#!/usr/bin/env python3
"""Scoped optical-opening correction on a copy of the installed review."""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from assembly_primitives import cylinder  # noqa: E402
from pcb_solid_fit import snapshot, screen  # noqa: E402

ROOT = HERE.parent
PREVIOUS = ROOT / "tmp/pcb-package-fit-2026-10-13"
SOURCE = PREVIOUS / "model-04/deepreal-mech-fit-04-installed-review.blend"
SOURCE_SHA = "34fb36619f61810eb9cdbd39bcb288631d1f9cd93687d0d0611c104095e32346"
BOARD = PREVIOUS / "model-04/deepreal-mech-fit-04-board.blend"
BOARD_SHA = "62986770003a42d13ed3f01cad949488b3738793016e0617bea8a386dc57f00a"
SLEEVE = "R35_Face_Outer_Drum_Wall_Sleeve_ENV"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_hash(obj):
    """Hash evaluated world geometry and the source matrix, not lighting."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        points = [tuple(evaluated.matrix_world @ v.co) for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        matrix = [tuple(row) for row in obj.matrix_world]
        return hashlib.sha256(repr((points, faces, matrix)).encode()).hexdigest()
    finally:
        evaluated.to_mesh_clear()


def center(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return sum((evaluated.matrix_world @ Vector(c) for c in evaluated.bound_box),
               Vector()) / 8


def window_frame(prefix, kind):
    name = prefix + "_Drum_Lens_" + kind
    window = bpy.data.objects[name + "_Element" if kind in ("RGB", "Depth") else name]
    midpoint = center(window)
    evaluated = window.evaluated_get(bpy.context.evaluated_depsgraph_get())
    if kind in ("RGB", "Depth"):
        outward = (midpoint - center(bpy.data.objects[name + "_Pupil"])).normalized()
    else:
        # Read the evaluated cylinder cap, including its baked/parent transforms.
        cap = max(evaluated.data.polygons, key=lambda p: p.area)
        outward = (evaluated.matrix_world.to_3x3().inverted().transposed() @ cap.normal).normalized()
        if outward.dot(midpoint - center(bpy.data.objects[prefix + "_Sensor_Head"])) < 0:
            outward.negate()
    horizontal = Vector((1, 0, 0))
    vertical = horizontal.cross(outward).normalized()
    vertices = [evaluated.matrix_world @ v.co for v in evaluated.data.vertices]
    axial = [(point - midpoint).dot(outward) for point in vertices]
    radius = max(((point - midpoint) - outward * (point - midpoint).dot(outward)).length
                 for point in vertices)
    return {
        "name": window.name, "center": midpoint, "outward": outward,
        "horizontal": horizontal, "vertical": vertical,
        "front": midpoint + outward * max(axial), "radius": radius,
    }


def nearest_hit(solids, origin_mm, direction, length_mm):
    found = None
    for solid in solids:
        point, normal, index, distance = solid["tree"].ray_cast(
            origin_mm, direction, length_mm)
        if point is not None and (found is None or distance < found["distance_mm"]):
            found = {"name": solid["name"], "distance_mm": distance}
    return found


def opening_audit(solids):
    """Sample nominal window discs, not an optical or tolerance qualification."""
    results = []
    for prefix in ("Face", "Interaction"):
        for kind in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole"):
            frame = window_frame(prefix, kind)
            failures, total = Counter(), 0
            for row in range(-8, 9):
                for column in range(-8, 9):
                    u, v = column / 8, row / 8
                    if u * u + v * v > 1:
                        continue
                    # Keep 0.1 mm inside the glass edge to avoid edge contacts.
                    radius = frame["radius"] - 0.0001
                    target = frame["front"] + radius * (
                        frame["horizontal"] * u + frame["vertical"] * v)
                    origin = (target + frame["outward"] * 0.025) * 1000
                    hit = nearest_hit(solids, origin, -frame["outward"], 25.1)
                    total += 1
                    if not hit or hit["name"] != frame["name"]:
                        failures[hit["name"] if hit else "NO_WINDOW_HIT"] += 1
            results.append({
                "aperture": prefix + "_" + kind, "target": frame["name"],
                "sampled_rays": total, "blocked_rays": sum(failures.values()),
                "blockers": dict(failures),
                "retaining_baffle_edge_hits": failures.get(prefix + "_Drum_Lens_" + kind, 0)
                if kind in ("Depth", "RGB") else 0,
                "unexpected_blockers": {
                    name: count for name, count in failures.items()
                    if kind not in ("Depth", "RGB") or name != prefix + "_Drum_Lens_" + kind
                },
                "qualification": "SAMPLED_NORMAL_RAYS_TO_NOMINAL_WINDOW_ONLY",
            })
    return results


def rgb_cone_audit(solids):
    """Published RGB angles at placeholder pupils, explicitly not real ray tracing."""
    results = []
    for prefix, horizontal_fov, vertical_fov in (("Face", 66, 41), ("Interaction", 102, 67)):
        frame = window_frame(prefix, "RGB")
        pupil = center(bpy.data.objects[prefix + "_Drum_Lens_RGB_Pupil"])
        excluded = {
            prefix + "_Drum_Lens_RGB_Element", prefix + "_Drum_Lens_RGB_Front_Element",
            prefix + "_Drum_Lens_RGB_Pupil",
        }
        if prefix == "Interaction":
            excluded.add("Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20")
        structural = [s for s in solids if s["name"] not in excluded]
        failures = Counter()
        for row in range(-6, 7):
            for column in range(-8, 9):
                direction = (frame["outward"]
                             + frame["horizontal"] * math.tan(math.radians(horizontal_fov / 2 * column / 8))
                             + frame["vertical"] * math.tan(math.radians(vertical_fov / 2 * row / 6))).normalized()
                hit = nearest_hit(structural, pupil * 1000, direction, 30)
                if hit:
                    failures[hit["name"]] += 1
        results.append({
            "aperture": prefix + "_RGB", "horizontal_fov_deg": horizontal_fov,
            "vertical_fov_deg": vertical_fov, "sampled_rays": 221,
            "blocked_rays": sum(failures.values()), "blockers": dict(failures),
            "excluded_optical_surfaces": sorted(excluded),
            "qualification": "PLACEHOLDER_PUPIL_SCREEN_NOT_OPTICAL_FOV_APPROVAL",
        })
    return results


def apply_matching_bore(sleeve, frame):
    """Copy the existing 9 mm through-bore into the later-added sleeve only."""
    if abs(frame["radius"] * 1000 - 4.38) > 0.00005:
        raise ValueError("unexpected depth window radius; do not infer a new bore")
    cutter = cylinder(
        "Optical correction inspection cutter",
        tuple((frame["front"] + frame["outward"] * 0.0003) * 1000),
        frame["outward"], 4.5, 3.6, None, bpy.context.scene.collection, 64)
    try:
        modifier = sleeve.modifiers.new("Match existing depth-camera through-bore", "BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "DIFFERENCE", "EXACT", cutter
        modifier.use_self = True
        with bpy.context.temp_override(object=sleeve, active_object=sleeve,
                                       selected_objects=[sleeve]):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    finally:
        mesh = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        bpy.data.meshes.remove(mesh)
    bpy.context.view_layer.update()


def volume_mm3(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.transform(evaluated.matrix_world)
        return abs(bm.calc_volume(signed=True)) * 1e9
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def restore_board_materials():
    """Normal views use original materials; red belongs only in diagnostics."""
    with bpy.data.libraries.load(str(BOARD), link=False) as (available, loaded):
        loaded.objects = available.objects
    for source in loaded.objects:
        if source is None or source.type != "MESH":
            continue
        destination = bpy.data.objects.get(source.name.removesuffix(".001"))
        if source.get("PCBA_Ref") != "J1" and not source.data.name.split(".")[0].endswith("_PCB"):
            continue
        if destination is None or destination.name not in bpy.context.scene.objects:
            raise ValueError("cannot restore board material identity")
        destination.data.materials.clear()
        for material in source.data.materials:
            destination.data.materials.append(material)
    for obj in loaded.objects:
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    output = args.output_dir.resolve()
    if output.exists():
        raise ValueError("retain previous candidates; output directory must be new")
    if sha(SOURCE) != SOURCE_SHA or sha(BOARD) != BOARD_SHA:
        raise ValueError("predecessor source changed")
    output.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    fit = json.loads((PREVIOUS / "model-04/enclosure-fit-audit.json").read_text())
    objects = [o for o in scene.objects if o.type == "MESH"]
    before_hashes = {o.name: geometry_hash(o) for o in objects}
    names = set(fit["source_mesh_boundary_counts"])
    names.update(o.name for o in objects if o.get("PCBA_Ref") or o.data.name.endswith("_PCB"))
    physical = [bpy.data.objects[name] for name in sorted(names)]
    solids = [snapshot(o) for o in physical]
    before_openings = opening_audit(solids)
    before_cones = rgb_cone_audit(solids)
    sleeve = bpy.data.objects[SLEEVE]
    original = snapshot(sleeve)
    original_volume = volume_mm3(sleeve)
    apply_matching_bore(sleeve, window_frame("Face", "Depth"))
    corrected = snapshot(sleeve)
    corrected_volume = volume_mm3(sleeve)
    if corrected["nonmanifold_edges"] or len(corrected["representatives"]) != 1:
        raise ValueError("correction must retain one closed connected sleeve")
    if not 0 < corrected_volume < original_volume:
        raise ValueError("invalid sleeve volume change")
    contacts = {}
    for name in ("R35_Face_Outer_Coupling_Web_ENV", "Face_Sensor_Head"):
        other = snapshot(bpy.data.objects[name])
        contacts[name] = {"before": screen(original, other), "after": screen(corrected, other)}
        if not contacts[name]["after"] or contacts[name]["after"]["status"] != "POSITIVE_NOMINAL_SOLID_INTERSECTION":
            raise ValueError("nominal sleeve load-path overlap was lost")
    solids = [corrected if s["name"] == SLEEVE else s for s in solids]
    after_openings = opening_audit(solids)
    after_cones = rgb_cone_audit(solids)
    target = next(a for a in after_openings if a["aperture"] == "Face_Depth")
    if target["unexpected_blockers"]:
        raise ValueError("depth opening still obstructed: " + repr(target))
    after_hashes = {o.name: geometry_hash(o) for o in objects}
    changed = [name for name in before_hashes if before_hashes[name] != after_hashes[name]]
    if changed != [SLEEVE]:
        raise ValueError("geometry change exceeded scope: " + repr(changed))
    restore_board_materials()
    if any(geometry_hash(o) != after_hashes[o.name] for o in objects):
        raise ValueError("material restoration changed geometry")
    scene.name = "Optical opening correction candidate, not engineering release"
    sleeve["Optical_Correction"] = "Matching existing 9mm depth through-bore; strength remains unqualified"
    bpy.context.preferences.filepaths.save_version = 0
    scene.camera = bpy.data.objects["Installed cutaway review"]
    report = {
        "schema": "deepreal.private-optical-clearance-candidate.v1",
        "status": "SCOPED_GEOMETRY_CORRECTION_NOT_ASSEMBLY_APPROVAL",
        "source": str(SOURCE), "source_sha256": SOURCE_SHA,
        "builder_sha256": sha(Path(__file__)),
        "changed_geometry_objects": changed,
        "unchanged_geometry_objects": len(objects) - len(changed),
        "geometry_hashes_before": before_hashes, "geometry_hashes_after": after_hashes,
        "sleeve_volume_before_mm3": original_volume, "sleeve_volume_after_mm3": corrected_volume,
        "removed_volume_mm3": original_volume - corrected_volume,
        "retained_volume_fraction": corrected_volume / original_volume,
        "corrected_nonmanifold_edges": corrected["nonmanifold_edges"],
        "corrected_connected_components": len(corrected["representatives"]),
        "nominal_load_path_overlaps": contacts,
        "opening_audit_before": before_openings, "opening_audit_after": after_openings,
        "rgb_cone_audit_before": before_cones, "rgb_cone_audit_after": after_cones,
        "pcb_source_unchanged": True,
        "limits": [
            "Cut matches the inherited aperture; no selected lens or strength claim",
            "Remaining sleeve is connected with nominal overlaps, not joint/load/tolerance approval",
            "Sampled normal rays do not certify continuous field of view or optical image quality",
            "RGB cone screen uses placeholder pupils, not measured entrance-pupil positions or focus travel",
            "IR lens/holder/filter and Belago aperture/window system remain unselected or unverified",
            "MECH-FIT-04 USB, shield, harness, circuit and manufacturing blockers remain",
        ],
        "fabrication_allowed": False, "public_visual_allowed": False, "viewer_integration_allowed": False,
    }
    if args.render:
        scene.render.stamp_note_text = "OPTICAL CORRECTION CANDIDATE | MATCHING SLEEVE BORE | NORMAL MATERIALS | FIT NOT APPROVED"
        scene.render.filepath = str(output / "installed-cutaway.png")
        bpy.ops.render.render(write_still=True)
        camera = scene.camera
        old_scale, old_location = camera.data.ortho_scale, camera.location.copy()
        camera.location += center(bpy.data.objects["Face_Drum_Lens_Depth_Element"]) - Vector((.004, .004, -.004))
        camera.data.ortho_scale = .025
        scene.render.stamp_note_text = "DEPTH WINDOW | SLEEVE OBSTRUCTION CORRECTED | SAMPLED NOMINAL CLEARANCE, NOT OPTICAL APPROVAL"
        scene.render.filepath = str(output / "depth-window-detail.png")
        bpy.ops.render.render(write_still=True)
        camera.data.ortho_scale, camera.location = old_scale, old_location
    blend = output / "deepreal-optical-clearance-candidate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report["output_sha256"] = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
    (output / "optical-clearance-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("SCOPED OPTICAL CORRECTION", json.dumps({
        "changed_objects": changed, "retained_volume_fraction": report["retained_volume_fraction"],
        "blocked_normal_rays_after": {r["aperture"]: r["blocked_rays"] for r in after_openings},
        "unexpected_normal_ray_blockers_after": {r["aperture"]: r["unexpected_blockers"] for r in after_openings},
        "rgb_cone_blockers_after": after_cones,
    }))


if __name__ == "__main__":
    main()
