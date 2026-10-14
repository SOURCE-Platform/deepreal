"""Combine the scoped sleeve correction with the private NXP footprint proposal."""

import argparse
import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcb_candidate_review_data import ROOT, digest
from pcba_native_import import _owner, _join, _envelope
from pcba_bom import ALL_PARTS
from build_pcb_candidate_review import box, camera, light
from build_pcb_package_review import (
    BOARD_COLLECTION, CONTRACT_PATH, configure_studio, frame_viewports,
    register_board, excluded, descendant, classify_pairs,
)
from audit_pcb_candidate_transport import capture, distance_to
from pcb_fit_geometry import positive_box_overlap
from pcb_solid_fit import snapshot, self_test
from build_optical_clearance_candidate import geometry_hash, opening_audit, rgb_cone_audit, center


WORK = ROOT / "tmp/assembly-corrections-2026-10-14"
CHANGED = {"U1": [15, 15, 1.584], "U6": [3.6, 4.6, 0.8], "U7": [3.6, 4.6, 0.8]}


def inputs(directory, optical):
    layout = json.loads((directory / "engineering-layout-export.json").read_text())
    manifest = json.loads((directory / "native-review-manifest.json").read_text())
    audit = json.loads((directory / "package-audit.json").read_text())
    if layout["metadata"]["design_revision"] != "MECH-FIT-05" or manifest["revision"] != "MECH-FIT-05":
        raise ValueError("MECH-FIT-05 input required")
    for name, sha in (
        (layout["metadata"]["source_board"], manifest["source_board_sha256"]),
        ("engineering-layout-export.json", manifest["source_export_sha256"]),
        ("package-audit.json", manifest["package_audit_sha256"]),
        (manifest["glb"], manifest["glb_sha256"]),
    ):
        if digest(directory / name) != sha:
            raise ValueError("stale candidate artifact: " + name)
    if set(audit["changed_footprint_refs"]) != set(CHANGED) or len(layout["components"]) != 238:
        raise ValueError("unexpected package scope")
    for source in manifest["model_sources"]:
        path = Path(source["resolved"])
        actual = digest(path) if path.is_file() else None
        if actual != source["sha256"]:
            raise ValueError("changed native model")
    for record in (layout["metadata"], manifest, audit):
        if any(record.get(flag) is not False for flag in
               ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
            raise ValueError("release locks required")
    optical_audit = json.loads((optical / "optical-clearance-audit.json").read_text())
    if optical_audit["changed_geometry_objects"] != ["R35_Face_Outer_Drum_Wall_Sleeve_ENV"]:
        raise ValueError("unexpected optical predecessor scope")
    blend = optical / "deepreal-optical-clearance-candidate.blend"
    if digest(blend) != optical_audit["output_sha256"][blend.name]:
        raise ValueError("changed optical predecessor")
    return layout, manifest, optical_audit


def standalone(layout, manifest, directory, output, render):
    refs = {c["ref"]: c for c in layout["components"]}
    metadata = {c["ref"]: c for c in ALL_PARTS}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "MECH-FIT-05 Private package proposal"
    collection = bpy.data.collections.new(BOARD_COLLECTION)
    scene.collection.children.link(collection)
    bpy.ops.import_scene.gltf(filepath=str(directory / manifest["glb"]))
    bpy.context.view_layer.update()
    imported = list(scene.objects)
    empties = [o for o in imported if o.type == "EMPTY"]
    groups, anchors, surfaces = {}, {}, []
    for obj in imported:
        if obj.name in refs:
            anchors[obj.name] = obj.matrix_world.copy()
        if obj.type == "MESH":
            ref = _owner(obj, refs)
            if ref:
                groups.setdefault(ref, []).append(obj)
            else:
                surfaces.append(obj)
    if set(groups) != set(manifest["native_model_refs"]):
        raise ValueError("native inventory mismatch")
    substrates = [o for o in surfaces if o.data.name.endswith("_PCB")]
    if len(substrates) != 1:
        raise ValueError("ambiguous native substrate")
    substrate = substrates[0]
    high = box(substrate)["max_mm"][2] * .001
    models = {}
    native_vertices = sum(len(o.data.vertices) for group in groups.values() for o in group)
    join_error = 0
    for ref, meshes in sorted(groups.items()):
        original = [box(o) for o in meshes]
        obj = _join(meshes)
        matrix = obj.matrix_world.copy()
        obj.parent, obj.matrix_world = None, matrix
        obj.name = "Candidate_" + ref
        obj["PCBA_ModelStatus"] = "MANUFACTURER_MAXIMUM_BOUNDING_ENVELOPE_NOT_DETAILED_MODEL" \
            if ref in CHANGED else "INHERITED_PACKAGE_OR_REPRESENTATIVE_NOT_ELECTRICAL_RELEASE"
        for key, op in (("min_mm", min), ("max_mm", max)):
            expected = [op(b[key][i] for b in original) for i in range(3)]
            join_error = max(join_error, *(abs(a-b) for a, b in zip(box(obj)[key], expected)))
        models[ref] = obj
    if sum(len(o.data.vertices) for o in models.values()) != native_vertices or join_error > .00005:
        raise ValueError("native join changed geometry")
    for ref in manifest["missing_model_refs"]:
        obj = _envelope(refs[ref], metadata[ref], [65, 34], high + .000085, collection)
        obj.name = "Representative_" + ref
        models[ref], anchors[ref] = obj, obj.matrix_world.copy()
    anchor_error = 0
    for ref, obj in models.items():
        part = refs[ref]
        expected = Vector(((part["position_mm"][0]-65)*.001, (34-part["position_mm"][1])*.001))
        anchor_error = max(anchor_error, (anchors[ref].translation.xy-expected).length*1000)
        for key, value in {
            "PCBA_Ref": ref, "PCBA_UUID": part["uuid"], "PCBA_Value": part["value"],
            "PCBA_Side": part["side"], "PCBA_Footprint": part["footprint"],
        }.items():
            obj[key] = value
    if anchor_error > .01 or set(models) | set(manifest["pad_or_hole_only_refs"]) != set(refs):
        raise ValueError("native anchor/population mismatch")
    for obj in surfaces + list(models.values()):
        matrix = obj.matrix_world.copy()
        obj.parent, obj.matrix_world = None, matrix
        for parent in list(obj.users_collection):
            parent.objects.unlink(obj)
        collection.objects.link(obj)
        obj["PCBA_PublicAllowed"] = False
        obj["PCBA_SourceBoardHash"] = manifest["source_board_sha256"]
    for obj in empties:
        bpy.data.objects.remove(obj, do_unlink=True)
    bounds = {ref: box(obj) for ref, obj in models.items()}
    substrate_bounds = box(substrate)
    for ref, dimensions in CHANGED.items():
        actual = [b-a for a, b in zip(bounds[ref]["min_mm"], bounds[ref]["max_mm"])]
        if max(abs(a-b) for a, b in zip(actual, dimensions)) > .00005:
            raise ValueError("native envelope scale/axes wrong: " + ref + " " + str(actual))
    overlaps = [{"refs": [a, b], "overlap_mm": widths}
                for a, b in itertools.combinations(sorted(bounds), 2)
                if (widths := positive_box_overlap(bounds[a], bounds[b]))]
    if overlaps:
        raise ValueError("new component-body box overlaps: " + str(overlaps))
    for obj in surfaces:
        for mat in obj.data.materials:
            shader = mat.node_tree.nodes.get("Principled BSDF") if mat and mat.use_nodes else None
            if shader:
                shader.inputs["Alpha"].default_value = 1
                if "soldermask" in obj.data.name:
                    shader.inputs["Base Color"].default_value = (.008, .065, .023, 1)
                    shader.inputs["Roughness"].default_value = .42
                    shader.inputs["Metallic"].default_value = 0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = substrate
    bpy.ops.export_scene.gltf(filepath=str(output / "candidate-board.glb"), export_format="GLB",
        use_selection=True, export_extras=True, export_materials="EXPORT", export_yup=True)
    configure_studio(scene)
    for name, pos, energy in (
        ("Board key", (.015, -.025, .095), .05), ("Board edge", (.015, .065, .055), .067),
        ("Board fill", (-.075, -.035, .025), .017), ("Board bottom", (.01, -.035, -.080), .04),
    ):
        light(scene, name, pos, energy, .08)
    top = camera(scene, "Board top", (.064, -.092, .09), (.006, 0, .001))
    bottom = camera(scene, "Board bottom", (.064, -.092, -.085), (.006, 0, 0))
    scene.render.stamp_note_text = "MECH-FIT-05 | UNROUTED PACKAGE PROPOSAL | U1/PF53 MAX ENVELOPES | LANDS/STENCIL NOT RELEASED"
    if render:
        for stem, view in (("board-top", top), ("board-bottom", bottom)):
            scene.camera, scene.render.filepath = view, str(output / (stem + ".png"))
            bpy.ops.render.render(write_still=True)
    scene.camera = top
    for obj in scene.objects:
        if obj.name not in collection.objects:
            obj.hide_set(True)
    frame_viewports(scene, top, (.006, 0, .001), .16)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "deepreal-mech-fit-05-board.blend"))
    before = capture(collection.objects)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output / "candidate-board.glb"))
    after = capture(bpy.context.scene.objects)
    if before.keys() != after.keys():
        raise ValueError("transport lost native mesh identities")
    error = max(max(distance_to(v, after[k]), distance_to(after[k], v)) for k, v in before.items())
    if error > .00005:
        raise ValueError("native transport vertex drift")
    return {
        "body_bounds_native_mm": bounds, "substrate_bounds_native_mm": substrate_bounds,
        "native_body_vertices_preserved": native_vertices,
        "max_native_join_bound_error_mm": join_error, "max_anchor_error_mm": anchor_error,
        "component_body_box_overlaps": overlaps,
        "transport": {
            "status": "PASS", "mesh_identities": len(before),
            "source_vertices": sum(map(len, before.values())),
            "exported_vertices": sum(map(len, after.values())),
            "max_bidirectional_vertex_error_mm": error,
        },
    }


def installed(layout, manifest, optical, output, board_audit, render):
    bpy.ops.wm.open_mainfile(filepath=str(optical / "deepreal-optical-clearance-candidate.blend"))
    scene = bpy.context.scene
    old = bpy.data.collections[BOARD_COLLECTION]
    old_objects = list(old.objects)
    retained = [o for o in scene.objects if o.type in ("MESH", "CURVE") and o not in old_objects]
    hashes = {o.name: geometry_hash(o) for o in retained}
    for obj in old_objects:
        if obj.get("PCBA_PublicAllowed") is not False:
            raise ValueError("unexpected board-removal scope")
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
    with bpy.data.libraries.load(str(output / "deepreal-mech-fit-05-board.blend"), link=False) as (available, imported):
        imported.collections = [BOARD_COLLECTION]
    collection = imported.collections[0]
    scene.collection.children.link(collection)
    objects = list(collection.objects)
    contract = json.loads(CONTRACT_PATH.read_text())
    center_z = sum(board_audit["substrate_bounds_native_mm"][k][2]
                   for k in ("min_mm", "max_mm")) / 2 * .001
    cs = contract["coordinate_system"]
    transform = Matrix.Translation((0, -cs["board_center_web_depth_mm"]*.001 + center_z,
                                    cs["board_center_height_mm"]*.001)) @ Matrix.Rotation(math.pi/2, 4, "X")
    registration = register_board(objects, transform, board_audit)
    if hashes != {o.name: geometry_hash(o) for o in retained}:
        raise ValueError("retained mechanics changed while replacing board")
    physical = [o for o in retained if not excluded(o)]
    candidates = [snapshot(o) for o in objects if o.get("PCBA_Ref") or o.data.name.endswith("_PCB")]
    mechanics = [snapshot(o) for o in physical]
    findings, pairs = classify_pairs(candidates, mechanics)
    refs = {o.name: o.get("PCBA_Ref", "BOARD_SUBSTRATE") for o in objects}
    sweep = {}
    matrices = {o.name: o.matrix_world.copy() for o in physical}
    for head, base, angles in (("Face", 0, range(-45, 46, 5)), ("Interaction", 45, range(0, 46, 5))):
        pivot = bpy.data.objects[head + "_Rotating_Drum_Pivot_R15"]
        saved = pivot.rotation_euler.copy()
        moving = [o for o in physical if descendant(o, pivot)]
        events, checked = [], 0
        for angle in angles:
            pivot.rotation_euler.x = math.radians(angle-base)
            bpy.context.view_layer.update()
            result, count = classify_pairs(candidates, [snapshot(o) for o in moving])
            checked += count
            events.extend({"angle_deg": angle, **r} for r in result)
        pivot.rotation_euler = saved
        bpy.context.view_layer.update()
        sweep[head] = {"angles_deg": list(angles), "rigid_objects": len(moving),
                       "box_candidates": checked, "events": events}
    matrix_error = max(abs(a-b) for o in physical for old_row, new_row in
                       zip(matrices[o.name], o.matrix_world) for a, b in zip(old_row, new_row))
    if matrix_error > 1e-8 or hashes != {o.name: geometry_hash(o) for o in retained}:
        raise ValueError("mechanics not preserved after rigid pose samples")
    all_solids = [snapshot(o) for o in scene.objects if o.type == "MESH"]
    openings, cones = opening_audit(all_solids), rgb_cone_audit(all_solids)
    if any(o["unexpected_blockers"] for o in openings) or any(c["blocked_rays"] for c in cones):
        raise ValueError("new sampled structural optical obstruction")
    if render:
        scene.render.stamp_note_text = "PRIVATE CORRECTION REVIEW | SLEEVE BORE CORRECTED | NXP PACKAGE PROPOSALS | USB FIT STILL BLOCKED"
        scene.render.filepath = str(output / "installed-cutaway.png")
        bpy.ops.render.render(write_still=True)
        view = scene.camera
        saved_location, saved_scale = view.location.copy(), view.data.ortho_scale
        view.location += center(bpy.data.objects["Face_Drum_Lens_Depth_Element"]) - Vector((.004, .004, -.004))
        view.data.ortho_scale = .025
        scene.render.stamp_note_text = "DEPTH WINDOW | SLEEVE OBSTRUCTION REMOVED | NOT STRENGTH OR OPTICAL APPROVAL"
        scene.render.filepath = str(output / "depth-window-detail.png")
        bpy.ops.render.render(write_still=True)
        view.location, view.data.ortho_scale = saved_location, saved_scale
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "deepreal-assembly-corrections-review.blend"))
    return {
        "rigid_registration": registration, "retained_geometry_objects": len(retained),
        "retained_geometry_hashes": hashes, "retained_geometry_preserved": True,
        "candidate_solids": len(candidates), "mechanical_solids": len(mechanics),
        "rest_box_candidate_pairs": pairs,
        "rest_status_counts": dict(Counter(r["status"] for r in findings)),
        "rest_findings": [{"ref": refs[r["candidate"]], **r} for r in findings],
        "rigid_pose_samples": sweep, "restored_matrix_error": matrix_error,
        "opening_audit": openings, "rgb_cone_audit": cones, "solid_self_tests": self_test(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "optical", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    if any(not p.is_absolute() or not p.resolve().is_relative_to(WORK)
           for p in (args.candidate, args.optical, args.output)):
        raise ValueError("absolute private-workspace paths required")
    layout, manifest, optical_audit = inputs(args.candidate, args.optical)
    args.output.mkdir(parents=True, exist_ok=False)
    board = standalone(layout, manifest, args.candidate, args.output, args.render)
    fit = installed(layout, manifest, args.optical, args.output, board, args.render)
    report = {
        "schema": "deepreal.assembly-corrections-review.v1", "revision": "MECH-FIT-05",
        "status": "CORRECTIONS_REVIEW_COMPLETE_ASSEMBLY_FIT_BLOCKED",
        "builder_sha256": digest(Path(__file__)),
        "source_board_sha256": manifest["source_board_sha256"],
        "optical_predecessor_sha256": optical_audit["output_sha256"]["deepreal-optical-clearance-candidate.blend"],
        "board": board, "fit": fit,
        "limits": [
            "U1/PF53B are source-corrected private footprint proposals, not production-qualified libraries",
            "U1 land definition, AF22 source conflict, PF53 mask and all three stencils remain unresolved",
            "Three IC models are conservative maximum bounding envelopes, not detailed manufacturer CAD",
            "Existing USB positives and open mechanical geometry are not cleared by normal materials",
            "Normal and placeholder-pupil RGB rays are sampled structural screens, not optical qualification",
            "5-degree rigid pose samples are not continuous sweeps or dynamic-flex qualification",
            "Only four local PF53 PGND/LX alias nets; no system circuits, stackup, routing, manufacturing, website sync or deployment",
        ],
        "fabrication_allowed": False, "public_visual_allowed": False, "viewer_integration_allowed": False,
    }
    report["output_sha256"] = {p.name: digest(p) for p in args.output.iterdir() if p.is_file()}
    (args.output / "corrections-review-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("CORRECTIONS REVIEW", fit["rest_status_counts"], board["transport"], flush=True)


if __name__ == "__main__":
    main()
