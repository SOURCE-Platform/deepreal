#!/usr/bin/env python3
"""Audit the exported camera proposal, not a fabrication or full-motion approval.

Run in Blender with the R36 source loaded. DEEPREAL_WEB_ASSEMBLY_OUT selects
the candidate GLB; the report is written beside it. Surface crossings are
checked independently from the explicitly permitted mating contacts.
Set DEEPREAL_WEB_ASSEMBLY_BASELINE to a saved prior GLB to check preservation;
do not use the site's mutable installed asset as an implicit baseline.
"""

import hashlib
import itertools
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_camera_mount import HEADS, camera_frame, optical_support_contacts
from web_export_common import require_r36_source

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path(os.environ.get(
    "DEEPREAL_WEB_ASSEMBLY_OUT",
    str(ROOT / "blender/review-output/web/deepreal-assembly-review.glb"),
))
EXTERIOR = ROOT.parent / "source-public-site/public/models/deepreal.glb"
baseline_path = os.environ.get("DEEPREAL_WEB_ASSEMBLY_BASELINE")
BASELINE = Path(baseline_path).resolve() if baseline_path else None


def points(obj, transform=None):
    matrix = obj.matrix_world if transform is None else transform @ obj.matrix_world
    return [matrix @ v.co for v in obj.data.vertices]


def tree(obj, transform=None):
    # Millimetres keep the nearest-triangle calculations well conditioned
    # for thin PCB/contact surfaces. The imported mesh remains in metres.
    return BVHTree.FromPolygons(
        [p * 1000 for p in points(obj, transform)], [tuple(p.vertices) for p in obj.data.polygons],
        all_triangles=False)


def sampled_gap(a, b):
    ta, tb = tree(a), tree(b)
    return min(
        min(tb.find_nearest(p * 1000)[3] for p in points(a)),
        min(ta.find_nearest(p * 1000)[3] for p in points(b)))


def mesh_signature(obj):
    # World-space vertex positions allow comparison after a glTF round trip.
    return sorted(tuple(round(float(c), 8) for c in p) for p in points(obj))


def intended_contacts(objects):
    pairs = set()

    def add(a, b):
        pairs.add(frozenset((a, b)))

    for side, config in HEADS.items():
        prefix = f"WEB_{side}_RGB_"
        carrier = f"{side}_Internal_Optical_Carrier_WEB"
        saddle = prefix + "Rear_Saddle_PROPOSAL_WEB"
        tail = prefix + "Static_Sensor_Tail_PROPOSAL_WEB"
        j2 = prefix + "J2_Mated_Keepout_PROPOSAL_WEB"
        add(saddle, carrier)
        add(config["board"], f"{side}_Head_Flex_Connector_PROXY_WEB")
        add(config["board"], j2)
        add(tail, j2)
        add(tail, config["camera"])
        for name in objects:
            if name.startswith(prefix) and "_Bond_" in name:
                add(name, config["camera"])
                add(name, saddle)
            if name.startswith(f"WEB_{side}_Head_Board_Spacer_"):
                add(name, config["board"])
                add(name, carrier)
        for a, b in optical_support_contacts(side):
            add(a, b)
    return pairs


def inside(point, surface):
    """Odd/even ray test for solid proxy meshes, independent of normal winding."""
    direction = Vector((.811, .371, .453)).normalized()
    cursor = point.copy()
    hits = 0
    for _ in range(256):
        location, _, _, _ = surface.ray_cast(cursor, direction)
        if location is None:
            return bool(hits % 2)
        cursor = location + direction * 1e-4
        hits += 1
    raise RuntimeError("Ambiguous solid-proxy ray test")


def point_triangle_distance(point, a, b, c):
    """Double-precision distance avoids false depth on long, thin PCB faces."""
    def sub(x, y):
        return tuple(u - v for u, v in zip(x, y))

    def dot(x, y):
        return sum(u * v for u, v in zip(x, y))

    def cross(x, y):
        return (x[1]*y[2] - x[2]*y[1], x[2]*y[0] - x[0]*y[2],
                x[0]*y[1] - x[1]*y[0])

    normal = cross(sub(b, a), sub(c, a))
    squared = dot(normal, normal)
    edges = ((a, b), (b, c), (c, a))
    if squared > 1e-20 and all(
        dot(cross(sub(end, start), sub(point, start)), normal) >= -squared * 1e-12
        for start, end in edges
    ):
        return abs(dot(sub(point, a), normal)) / math.sqrt(squared)
    distances = []
    for start, end in edges:
        edge = sub(end, start)
        length = dot(edge, edge)
        t = max(0, min(1, dot(sub(point, start), edge) / length)) if length else 0
        closest = tuple(u + t * v for u, v in zip(start, edge))
        distances.append(math.dist(point, closest))
    return min(distances)


def nearest_contact_depth(a, b):
    """Sample vertices and triangle centres, not an exact volume certificate."""
    deepest = 0
    for first, second in ((a, b), (b, a)):
        other = tree(second)
        other_points = points(second)
        second.data.calc_loop_triangles()
        scaled = [tuple(float(c) * 1000 for c in p) for p in other_points]
        triangles = [tuple(scaled[i] for i in triangle.vertices)
                     for triangle in second.data.loop_triangles]
        bounds = [(min(p[i] for p in other_points), max(p[i] for p in other_points))
                  for i in range(3)]
        first_points = points(first)
        first.data.calc_loop_triangles()
        samples = first_points + [
            sum((first_points[i] for i in triangle.vertices), Vector()) / 3
            for triangle in first.data.loop_triangles]
        for point in samples:
            if not all(lo - 1e-7 <= point[i] <= hi + 1e-7
                       for i, (lo, hi) in enumerate(bounds)):
                continue
            distance = min(point_triangle_distance(
                tuple(float(c) * 1000 for c in point), *triangle)
                for triangle in triangles)
            if distance > 1e-4 and inside(point * 1000, other):
                deepest = max(deepest, distance)
    return deepest


def main():
    source = require_r36_source()
    pivots = {side: bpy.data.objects[f"{side}_Rotating_Drum_Pivot_R15"].matrix_world.translation.copy()
              for side in HEADS}
    # Hidden source objects are not selected by object.select_all().
    # Remove the in-memory inventory, never save or modify the source file.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(ASSET))
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    manifest = json.loads(ASSET.with_name("deepreal-assembly-review-manifest.json").read_text())
    names = [n for group in manifest["groups"].values() for n in group]
    assert len(names) == len(set(names)), "Repeated manifest membership"
    assert set(names) == set(objects), "Manifest/export inventory mismatch"
    assert manifest["asset_sha256"] == hashlib.sha256(ASSET.read_bytes()).hexdigest()
    assert manifest["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()

    unchanged_parts_checked = 0
    if BASELINE is not None:
        assert BASELINE != ASSET.resolve(), "Baseline must be a separate prior export"
        prior = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(BASELINE))
        baseline_objects = set(bpy.data.objects) - prior
        baseline_signatures = {
            o.name.removesuffix(".001"): mesh_signature(o)
            for o in baseline_objects if o.type == "MESH"
        }
        for obj in baseline_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        # Explicit scope against the saved preceding two-head mount export.
        # Optical modules, boards, cables and RGB supports must stay unchanged.
        changed = {
            "Face_Internal_Optical_Carrier_WEB",
            "Interaction_Internal_Optical_Carrier_WEB",
            "Face_SL_Projector_Bracket_WEB",
            "Interaction_SL_Projector_Bracket_WEB",
        }
        for name, signature in baseline_signatures.items():
            if name not in changed:
                assert mesh_signature(objects[name]) == signature, f"Moved baseline part: {name}"
                unchanged_parts_checked += 1

    bpy.ops.import_scene.gltf(filepath=str(EXTERIOR))
    exterior = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name not in objects]
    all_objects = {**objects, **{o.name: o for o in exterior}}
    additions = {
        side: [o for n, o in objects.items()
               if n.startswith((f"WEB_{side}_RGB_", f"WEB_{side}_Head_Board_Spacer_",
                                f"WEB_{side}_Optics_"))]
        for side in HEADS
    }
    targets = [o for parts in additions.values() for o in parts]
    for side, config in HEADS.items():
        targets += [objects[n] for n in (
            config["board"], config["camera"], config["lens"],
            f"{side}_Internal_Optical_Carrier_WEB",
            f"{side}_SL_Projector_Bracket_WEB",
            f"{side}_Head_Flex_Connector_PROXY_WEB")]
    contacts = intended_contacts(objects)
    trees = {name: tree(obj) for name, obj in all_objects.items()}
    tested = set()
    unintended = []
    # Conservative sensor/lens solids and the existing exterior pupil/front
    # detail are overlapping descriptions of the SAME optic, not independent
    # manufactured parts. Report only these named envelope/detail overlaps.
    envelope_pairs = set()
    for side, config in HEADS.items():
        envelope_pairs.add(frozenset((config["camera"], config["lens"])))
        for obj in exterior:
            if obj.name.startswith((f"{side}_Drum_Lens_RGB_Front_Element",
                                    f"{side}_Drum_Lens_RGB_Pupil",
                                    f"{side}_Drum_Lens_RGB_Barrel")):
                envelope_pairs.add(frozenset((config["lens"], obj.name)))
        envelope_pairs.add(frozenset((f"{side}_Head_Flex_Connector_PROXY_WEB",
                                     f"WEB_{side}_Optical_Flex_CONCEPT_WEB")))
    envelope_overlaps = []
    for first in targets:
        for second in all_objects.values():
            pair = frozenset((first.name, second.name))
            if first == second or pair in tested:
                continue
            tested.add(pair)
            overlap = len(trees[first.name].overlap(trees[second.name]))
            if overlap and pair not in contacts:
                entry = [first.name, second.name, overlap]
                if pair in envelope_pairs:
                    envelope_overlaps.append(entry)
                else:
                    unintended.append(entry)

    contact_report = []
    for pair in sorted(contacts, key=lambda p: sorted(p)):
        a, b = (objects[n] for n in sorted(pair))
        gap = sampled_gap(a, b)
        depth = nearest_contact_depth(a, b)
        contact_report.append({
            "parts": sorted(pair), "sampled_gap_mm": round(gap, 6),
            "sampled_intrusion_mm": round(depth, 6),
        })
        assert gap < .001, f"Disconnected proposed mating: {a.name} / {b.name}: {gap}"
        assert depth < .001, f"Penetrating proposed mating: {a.name} / {b.name}: {depth}"

    landing_report = []
    for side, main_ref in (("Face", "J2_Face"), ("Interaction", "J3_Interaction")):
        ribbon = objects[f"WEB_{side}_Optical_Flex_CONCEPT_WEB"]
        uv = ribbon.data.uv_layers.active
        for value, connector_name in (
            (0, f"{side}_Head_Flex_Connector_PROXY_WEB"),
            (1, f"{main_ref}_Optical_Head_Connector_ENVELOPE_WEB"),
        ):
            section = set()
            for loop_index, coord in enumerate(uv.data):
                if abs(coord.uv.y - value) < 1e-6:
                    vertex = ribbon.data.loops[loop_index].vertex_index
                    section.add(tuple(ribbon.matrix_world @ ribbon.data.vertices[vertex].co))
            connector_points = points(objects[connector_name])
            bounds = [(min(p[i] for p in connector_points), max(p[i] for p in connector_points))
                      for i in range(3)]
            contained = all(all(lo - 1e-5 <= point[i] <= hi + 1e-5
                                for i, (lo, hi) in enumerate(bounds)) for point in section)
            assert len(section) == 4 and contained, f"Missed conceptual landing: {connector_name}"
            landing_report.append({"connector": connector_name, "corners_in_concept_bbox": len(section)})

    # Rigid proposed hardware follows the retained pivot. Fixed outer bearings,
    # motor, main PCB and enclosure do not. Dynamic head cables are excluded:
    # their visible loops are an expanded study, not a housed swept route.
    fixed = [objects[n] for n in (manifest["groups"]["stationary"]
                                 + manifest["groups"]["main"]
                                 + manifest["groups"]["shields"])]
    fixed += [o for o in exterior if not o.name.startswith(("Interaction_Sensor_Head", "Interaction_Drum_Lens_",
                                                           "Face_Sensor_Head", "Face_Drum_Lens_"))]
    heads = {}
    canonical_boards = {}
    canonical_interfaces = {"J1": {}, "J2": {}}
    for side, config in HEADS.items():
        pivot = pivots[side]
        frame = camera_frame(objects, side)
        normal = frame.col[2].to_3d()
        rest_degrees = math.degrees(math.atan2(-normal.z, -normal.y))
        rigid = additions[side] + [objects[config[n]] for n in ("board", "camera", "lens")]
        rigid += [objects[f"{side}_{suffix}_WEB"] for suffix in (
            "Internal_Optical_Carrier", "Head_Flex_Connector_PROXY",
            "IR_Depth_Module_Body", "IR_Depth_Module_Barrel",
            "SL_Projector_Body", "SL_Projector_Bracket", "SL_Projector_DOE",
            "SL_Projector_Emitter", "SL_Projector_Barrel_Pinhole",
            "SL_Projector_Barrel_ProjA", "SL_Projector_Barrel_ProjB")]
        angles = (-45, -33.75, -22.5, -11.25, 0, 11.25, 22.5, 33.75, 45) if side == "Face" else (0, 11.25, 22.5, 33.75, 45)

        def pose(angle):
            return (Matrix.Translation(pivot)
                    @ Matrix.Rotation(math.radians(angle - rest_degrees), 4, "X")
                    @ Matrix.Translation(-pivot))

        swept = []
        for angle in angles:
            rotation = pose(angle)
            rotated = {o.name: tree(o, rotation) for o in rigid}
            crossings = []
            for first, second in itertools.product(rigid, fixed):
                count = len(rotated[first.name].overlap(trees[second.name]))
                if count:
                    crossings.append([first.name, second.name, count])
            swept.append({"optical_direction_down_deg": angle, "crossings": crossings})

        shell = next(o for o in exterior if o.name.startswith(f"{side}_Sensor_Head"))
        shell_gaps = [{"part": o.name, "sampled_shell_gap_mm": round(sampled_gap(o, shell), 3)}
                      for o in additions[side] + [objects[config["board"]], objects[config["camera"]], objects[config["lens"]]]]
        nose = frame @ Vector((0, 0, config["lens_depth_mm"] * .001))
        optical_obstacles = [o for o in exterior
                             if o.name.startswith((f"{side}_Sensor_Head", "R30_One_Piece_Enclosure"))]
        ray_results = []
        h, v = [fov / 2 for fov in config["fov_degrees"]]
        for angle in ((-45, -22.5, 0, 22.5, 45) if side == "Face" else (0, 22.5, 45)):
            rotation = pose(angle)
            pose_trees = {o.name: tree(o, rotation if o == shell else None) for o in optical_obstacles}
            for horizontal, vertical in itertools.product((-h, 0, h), (-v, 0, v)):
                local = Vector((math.tan(math.radians(horizontal)),
                                math.tan(math.radians(vertical)), 1)).normalized()
                direction = (rotation.to_3x3() @ frame.to_3x3() @ local).normalized()
                start = rotation @ nose
                hits = []
                for name, surface in pose_trees.items():
                    hit, _, _, distance = surface.ray_cast(start * 1000, direction, 250)
                    if hit is not None:
                        hits.append({"part": name, "distance_mm": round(distance, 3)})
                ray_results.append({"pose_deg": angle, "H_deg": horizontal, "V_deg": vertical, "hits": hits})
        heads[side.lower()] = {
            "rigid_hardware_sampled_poses": swept, "sampled_shell_gaps": shell_gaps,
            "ideal_chief_ray_fan": ray_results,
            "camera_origin_mm": [round(value * 1000, 5) for value in frame.translation],
            "optical_normal": list(normal),
        }
        board = objects[config["board"]]
        local_points = [frame.inverted() @ p * 1000 for p in points(board)]
        for p in local_points:
            p.z += config["board_offset_mm"]
        canonical_boards[side] = (local_points, [tuple(p.vertices) for p in board.data.polygons])
        for label, name in (
            ("J1", f"{side}_Head_Flex_Connector_PROXY_WEB"),
            ("J2", f"WEB_{side}_RGB_J2_Mated_Keepout_PROPOSAL_WEB"),
        ):
            obj = objects[name]
            coords = [frame.inverted() @ p * 1000 for p in points(obj)]
            for p in coords:
                p.z += config["board_offset_mm"]
            canonical_interfaces[label][side] = (coords, [tuple(p.vertices) for p in obj.data.polygons])

    def shared_surface_difference(meshes):
        surfaces = {side: BVHTree.FromPolygons(*mesh, all_triangles=False)
                    for side, mesh in meshes.items()}
        return max(surfaces[other].find_nearest(point)[3]
                   for side, other in (("Face", "Interaction"), ("Interaction", "Face"))
                   for point in meshes[side][0])

    shared_board_error = shared_surface_difference(canonical_boards)
    assert shared_board_error < .001, f"Different common board surfaces: {shared_board_error} mm"
    interface_errors = {label: shared_surface_difference(meshes)
                        for label, meshes in canonical_interfaces.items()}
    assert all(value < .001 for value in interface_errors.values()), f"Different common interfaces: {interface_errors}"

    report = {
        "asset": ASSET.name, "asset_sha256": manifest["asset_sha256"],
        "source_sha256": manifest["source_sha256"],
        "exterior_sha256": hashlib.sha256(EXTERIOR.read_bytes()).hexdigest(),
        "baseline_sha256": hashlib.sha256(BASELINE.read_bytes()).hexdigest() if BASELINE else None,
        "baseline_unchanged_parts_checked": unchanged_parts_checked,
        "rest_pairs_checked": len(tested),
        "unintended_rest_crossings": unintended,
        "inherited_carrier_proxy_contacts": [],
        "declared_envelope_overlaps": envelope_overlaps,
        "declared_mating_contacts": contact_report,
        "conceptual_connector_landings": landing_report,
        "common_board_max_sampled_surface_difference_mm": shared_board_error,
        "common_connector_max_sampled_surface_difference_mm": interface_errors,
        "heads": heads,
        "limits": [
            "BVH triangle checks and nearest-vertex gaps are not exact minimum-clearance or tolerance certification.",
            "Nine face and five interaction rigid poses are sampled, not continuous swept-volume validation.",
            "Expanded dynamic head, motor and encoder cables are excluded from rigid motion approval.",
            "Chief rays use a provisional lens nose, not the optical pupil; glazing, refraction and full window clipping untested.",
            "Carrier/projector overlaps have no legacy exemption; declared support contacts must pass sampled gap/intrusion checks.",
            "Shared board geometry is a conditional proxy fit, not a routed design or tolerance-approved common PCB.",
            "Sensor, lens and decorative pupil envelopes are not independent manufactured parts.",
            "Camera stack, connector mating, mounting sites, carrier strength and thermal paths remain engineering gates.",
        ],
    }
    output = ASSET.with_name("camera-mount-audit.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print("MOUNT AUDIT", output)
    print("REST UNINTENDED", unintended)
    print("COMMON BOARD DIFFERENCE MM", shared_board_error)
    for side, result in heads.items():
        print("RIGID SWEEP", side, result["rigid_hardware_sampled_poses"])
        print("IDEAL RAY HITS", side, sum(bool(r["hits"]) for r in result["ideal_chief_ray_fan"]))
    assert not unintended, "Unintended camera-proposal rest crossings"
    assert not any(p["crossings"] for head in heads.values()
                   for p in head["rigid_hardware_sampled_poses"]), "Rigid camera-proposal sweep crossings"


if __name__ == "__main__":
    main()
