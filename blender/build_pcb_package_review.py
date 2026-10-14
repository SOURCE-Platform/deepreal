"""Build a private source-bound board and diagnose its retained enclosure fit."""

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
from pcb_package_review_data import checked_inputs
from pcb_candidate_review_data import ROOT, digest
from pcba_native_import import _owner, _join, _envelope
from pcba_bom import ALL_PARTS
from pcb_fit_geometry import positive_box_overlap
from build_pcb_candidate_review import box, camera, light, material
from audit_pcb_candidate_transport import capture, distance_to
from pcb_solid_fit import snapshot, screen, self_test, WELD_MM, VOLUME_MM3
from export_web_assembly import MAIN


MECHANICAL_SOURCE = ROOT / "blender/refinements/r38/deepreal-exterior-mount-r38.blend"
CONTRACT_PATH = ROOT / "docs/design/pcb-mechanical-interface-2026-10-13.json"
BOARD_COLLECTION = "Complete Candidate PCBA"
EXCLUDE = set(MAIN) | {
    "Main_PCBA_Populated_Keepout", "Main_PCBA_Imported_Artwork_HIDDEN_REFERENCE",
    "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED", "J1_SOURCE_BOARD_POSITION_HIDDEN_REFERENCE",
    "Monitor_Lid_Reference", "Mount_Foam_Tape_Reference", "Mount_Steel_Plate_Reference",
}


def configure_studio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples, scene.cycles.use_denoising = 48, True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == "METAL"
        if any(d.use for d in prefs.devices):
            scene.cycles.device = "GPU"
    except (AttributeError, TypeError):
        pass
    scene.world = bpy.data.worlds.new("Private Fit Studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.35, .40, .46, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1360
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.render.use_stamp = True
    scene.render.use_stamp_note = True
    scene.render.stamp_font_size = 18
    scene.render.stamp_foreground = (1, 1, 1, 1)
    scene.render.stamp_background = (.015, .018, .022, .85)
    for key in ("use_stamp_date", "use_stamp_time", "use_stamp_frame", "use_stamp_filename",
                "use_stamp_scene", "use_stamp_camera", "use_stamp_render_time"):
        setattr(scene.render, key, False)


def frame_viewports(scene, view, target, distance):
    scene.unit_settings.system, scene.unit_settings.length_unit = "METRIC", "MILLIMETERS"
    count = 0
    for screen_data in bpy.data.screens:
        for area in screen_data.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.clip_start, space.clip_end = .00001, 10
                space.shading.type = "MATERIAL"
                space.overlay.show_floor = False
                space.region_3d.view_location = Vector(target)
                space.region_3d.view_rotation = view.rotation_euler.to_quaternion()
                space.region_3d.view_distance, space.region_3d.view_perspective = distance, "ORTHO"
                count += 1
    if not count:
        raise ValueError("no framed interactive viewport")
    return count


def standalone(layout, manifest, directory, output):
    refs = {c["ref"]: c for c in layout["components"]}
    metadata = {c["ref"]: c for c in ALL_PARTS}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "MECH-FIT-04 Private Board"
    collection = bpy.data.collections.new(BOARD_COLLECTION)
    scene.collection.children.link(collection)
    bpy.ops.import_scene.gltf(filepath=str(directory / manifest["glb"]))
    imported = list(bpy.data.objects)
    empties = [obj for obj in imported if obj.type == "EMPTY"]
    groups, anchors, surfaces = {}, {}, []
    for obj in imported:
        if obj.name in refs:
            anchors[obj.name] = obj.matrix_world.copy()
        if obj.type != "MESH":
            continue
        ref = _owner(obj, refs)
        if ref:
            groups.setdefault(ref, []).append(obj)
        else:
            surfaces.append(obj)
    if set(groups) != set(manifest["native_model_refs"]):
        raise ValueError("native inventory disagrees")
    substrates = [o for o in surfaces if o.data.name.endswith("_PCB")]
    if len(substrates) != 1:
        raise ValueError("ambiguous substrate")
    substrate = substrates[0]
    low, high = [box(substrate)[k][2] * .001 for k in ("min_mm", "max_mm")]
    native_vertices = sum(len(o.data.vertices) for parts in groups.values() for o in parts)
    models, bound_error = {}, 0
    for ref, meshes in sorted(groups.items()):
        original = [box(obj) for obj in meshes]
        joined = _join(meshes)
        matrix = joined.matrix_world.copy()
        joined.parent, joined.matrix_world = None, matrix
        joined.name = "Candidate_" + ref
        joined["PCBA_ModelStatus"] = "LIBRARY_DRT_PACKAGE_CHECKED_NOT_ELECTRICAL_RELEASE" \
            if ref == "D2" else "NATIVE_INHERITED_UNVERIFIED_PACKAGE"
        for key, op in (("min_mm", min), ("max_mm", max)):
            expected = [op(b[key][i] for b in original) for i in range(3)]
            bound_error = max(bound_error, *(abs(a - b) for a, b in zip(expected, box(joined)[key])))
        models[ref] = joined
    if native_vertices != sum(len(o.data.vertices) for o in models.values()) or bound_error > .00005:
        raise ValueError("native join changed geometry")
    for ref in manifest["missing_model_refs"]:
        obj = _envelope(refs[ref], metadata[ref], [65, 34], high + .000085, collection)
        obj.name = "Representative_" + ref
        models[ref] = obj
        anchors[ref] = obj.matrix_world.copy()
    max_anchor = 0
    for ref, obj in models.items():
        item = refs[ref]
        expected = Vector(((item["position_mm"][0] - 65) * .001,
                           (34 - item["position_mm"][1]) * .001))
        max_anchor = max(max_anchor, (anchors[ref].translation.xy - expected).length * 1000)
        for key, value in {"PCBA_Ref": ref, "PCBA_UUID": item["uuid"],
                           "PCBA_Side": item["side"], "PCBA_Footprint": item["footprint"],
                           "PCBA_Value": item["value"]}.items():
            obj[key] = value
    if max_anchor > .01 or set(models) | set(manifest["pad_or_hole_only_refs"]) != set(refs):
        raise ValueError("anchor/population disagreement")
    for obj in surfaces + list(models.values()):
        matrix = obj.matrix_world.copy()
        obj.parent, obj.matrix_world = None, matrix
        for parent in list(obj.users_collection):
            parent.objects.unlink(obj)
        collection.objects.link(obj)
        obj["PCBA_PublicAllowed"] = False
        obj["PCBA_SourceBoardHash"] = manifest["source_board_sha256"]
    for obj in empties:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    bounds = {ref: box(obj) for ref, obj in models.items()}
    overlaps = [{"refs": [a, b], "overlap_mm": widths}
                for a, b in itertools.combinations(sorted(bounds), 2)
                if (widths := positive_box_overlap(bounds[a], bounds[b]))]
    if overlaps:
        raise ValueError("fresh component body-box overlaps: " + str(overlaps))
    for obj in surfaces:
        for mat in obj.data.materials:
            shader = mat.node_tree.nodes.get("Principled BSDF")
            if shader:
                shader.inputs["Alpha"].default_value = 1
                if "soldermask" in obj.data.name:
                    shader.inputs["Base Color"].default_value = (.008, .065, .023, 1)
                    shader.inputs["Metallic"].default_value = 0
                    shader.inputs["Roughness"].default_value = .42
    for name in ("mat_1", "mat_2", "mat_4", "mat_5", "mat_9", "mat_10"):
        mat = bpy.data.materials.get(name)
        if mat:
            shader = mat.node_tree.nodes.get("Principled BSDF")
            shader.inputs["Metallic"].default_value = 0
            shader.inputs["Roughness"].default_value = .6
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = substrate
    bpy.ops.export_scene.gltf(filepath=str(output / "candidate-board.glb"), export_format="GLB",
        use_selection=True, export_extras=True, export_materials="EXPORT", export_yup=True)
    configure_studio(scene)
    light(scene, "Board key", (.015, -.025, .095), .05, .09)
    light(scene, "Board edge", (.015, .065, .055), .067, .08)
    light(scene, "Board fill", (-.075, -.035, .025), .017, .07)
    light(scene, "Board bottom", (.01, -.035, -.080), .04, .08)
    top = camera(scene, "Board top", (.064, -.092, .09), (.006, 0, .001))
    bottom = camera(scene, "Board bottom", (.064, -.092, -.085), (.006, 0, 0))
    scene.render.stamp_note_text = "MECH-FIT-04 | PRIVATE UNROUTED BOARD | D2 PACKAGE CORRECTED | OTHER SUBSTITUTIONS OPEN"
    for stem, view in (("board-top", top), ("board-bottom", bottom)):
        scene.camera, scene.render.filepath = view, str(output / (stem + ".png"))
        bpy.ops.render.render(write_still=True)
    scene.camera = top
    for obj in scene.objects:
        if obj.name not in collection.objects:
            obj.hide_set(True)
    viewports = frame_viewports(scene, top, (.006, 0, .001), .16)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "deepreal-mech-fit-04-board.blend"))
    return {
        "native_body_vertex_count_preserved": native_vertices,
        "max_native_join_bound_error_mm": bound_error, "max_anchor_error_mm": max_anchor,
        "body_aabb_overlap_candidates": overlaps, "body_bounds_native_mm": bounds,
        "substrate_bounds_native_mm": box(substrate),
        "native_substrate_thickness_mm": (high - low) * 1000,
        "nominal_board_thickness_mm": layout["board"]["thickness_mm"],
        "interactive_board_viewports": viewports,
    }


def excluded(obj):
    return obj.name in EXCLUDE or obj.get("PCBA_Component") or obj.get("PCBA_NativeSurface") or \
        obj.name.startswith(("PCBA_", "SOURCE_UNVERIFIED_", "Main_PCBA_"))


def descendant(obj, pivot):
    while obj.parent:
        obj = obj.parent
        if obj == pivot:
            return True
    return False


def classify_pairs(candidates, mechanics):
    results, count = [], 0
    for first in candidates:
        for second in mechanics:
            if not positive_box_overlap(first["box"], second["box"]):
                continue
            count += 1
            result = screen(first, second)
            if result:
                results.append({"candidate": first["name"], "mechanical": second["name"], **result})
    return results, count


def register_board(objects, transform, board_audit):
    # Appended datablocks do not have evaluated world matrices until the
    # view layer updates. Capture all source matrices before changing any.
    bpy.context.view_layer.update()
    source_matrices = {o.name: o.matrix_world.copy() for o in objects}
    source_bounds = {o.name: box(o) for o in objects}
    if any(o.parent for o in objects):
        raise ValueError("standalone board must have no transform parents")
    source_error = 0
    for obj in objects:
        ref = obj.get("PCBA_Ref")
        expected = board_audit["body_bounds_native_mm"].get(ref)
        if obj.data.name.endswith("_PCB"):
            expected = board_audit["substrate_bounds_native_mm"]
        if expected:
            source_error = max(source_error, *(abs(a - b)
                for key in ("min_mm", "max_mm")
                for a, b in zip(source_bounds[obj.name][key], expected[key])))
    if source_error > .00005:
        raise ValueError("appended board disagrees with standalone bounds")
    for obj in objects:
        obj.matrix_world = transform @ source_matrices[obj.name]
        obj.hide_render = False
        obj.hide_set(False)
    bpy.context.view_layer.update()
    vertex_error = max(
        (obj.matrix_world @ v.co - transform @ source_matrices[obj.name] @ v.co).length * 1000
        for obj in objects for v in obj.data.vertices)
    bound_error = 0
    for obj in objects:
        corners = [transform @ (Vector(p) * .001) * 1000
                   for p in itertools.product(*zip(
                       source_bounds[obj.name]["min_mm"], source_bounds[obj.name]["max_mm"]))]
        actual = box(obj)
        for key, op in (("min_mm", min), ("max_mm", max)):
            expected = [op(p[i] for p in corners) for i in range(3)]
            bound_error = max(bound_error, *(abs(a - b) for a, b in zip(actual[key], expected)))
    if max(vertex_error, bound_error) > .00005:
        raise ValueError("installed registration changed relative board geometry")
    return {
        "status": "PASS", "objects_checked": len(objects),
        "vertices_checked": sum(len(o.data.vertices) for o in objects),
        "max_appended_source_bound_error_mm": source_error,
        "max_rigid_transform_vertex_error_mm": vertex_error,
        "max_rigid_transform_bound_error_mm": bound_error,
    }


def enclosure(layout, manifest, output, board_audit):
    contract = json.loads(CONTRACT_PATH.read_text())
    for path, sha in contract["sources_sha256"].items():
        if digest(ROOT / path) != sha:
            raise ValueError("retained mechanical source changed")
    bpy.ops.wm.open_mainfile(filepath=str(MECHANICAL_SOURCE))
    scene = bpy.context.scene
    source_objects = list(scene.objects)
    physical = [o for o in source_objects if o.type in ("MESH", "CURVE") and not excluded(o)]
    excluded_names = [o.name for o in source_objects if o.type in ("MESH", "CURVE") and excluded(o)]
    for obj in source_objects:
        if obj.type in ("LIGHT", "CAMERA") or excluded(obj):
            obj.hide_render = True
            obj.hide_set(True)
    board_path = output / "deepreal-mech-fit-04-board.blend"
    with bpy.data.libraries.load(str(board_path), link=False) as (available, imported):
        imported.collections = [BOARD_COLLECTION]
    board_collection = imported.collections[0]
    scene.collection.children.link(board_collection)
    board_objects = list(board_collection.objects)
    center_z = sum(board_audit["substrate_bounds_native_mm"][k][2]
                   for k in ("min_mm", "max_mm")) / 2 * .001
    cs = contract["coordinate_system"]
    transform = Matrix.Translation((0, -cs["board_center_web_depth_mm"] * .001 + center_z,
                                    cs["board_center_height_mm"] * .001)) @ \
        Matrix.Rotation(math.pi / 2, 4, "X")
    registration_audit = register_board(board_objects, transform, board_audit)
    substrate = next(o for o in board_objects if o.data.name.endswith("_PCB"))
    candidates = [snapshot(o) for o in board_objects if o.get("PCBA_Ref") or o == substrate]
    baseline_matrices = {o.name: o.matrix_world.copy() for o in physical}
    mechanical = [snapshot(o) for o in physical]
    tests = self_test()
    rest_results, rest_candidates = classify_pairs(candidates, mechanical)
    print("REST FIT", Counter(r["status"] for r in rest_results), flush=True)
    sweep = {}
    for head, base, angles in (("Face", 0, range(-45, 46, 5)),
                                ("Interaction", 45, range(0, 46, 5))):
        pivot = bpy.data.objects[head + "_Rotating_Drum_Pivot_R15"]
        saved = pivot.rotation_euler.copy()
        moving = [o for o in physical if descendant(o, pivot)]
        events, checked = [], 0
        for angle in angles:
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            result, count = classify_pairs(candidates, [snapshot(o) for o in moving])
            checked += count
            events.extend({"optical_direction_deg": angle, **r} for r in result)
        pivot.rotation_euler = saved
        bpy.context.view_layer.update()
        sweep[head] = {"optical_directions_deg": list(angles), "base_direction_deg": base,
                       "rigid_objects": [o.name for o in moving], "events": events,
                       "box_candidate_pairs_checked": checked}
        print("SWEEP", head, Counter(r["status"] for r in events), flush=True)
    matrix_error = max(abs(a - b) for o in physical
                       for old, new in zip(baseline_matrices[o.name], o.matrix_world)
                       for a, b in zip(old, new))
    if matrix_error > 1e-8:
        raise ValueError("mechanical matrices not restored after sampling")
    refs = {o.name: o.get("PCBA_Ref", "BOARD_SUBSTRATE") for o in board_objects}
    plug_names = {"USB_C_Male_Metal_Shell", "USB_C_Male_Internal_Insert",
                  "USB_C_Male_Contact_Tongue", "USB_C_Plug_Overmold"}
    j1 = next(c for c in candidates if refs[c["name"]] == "J1")
    plug = next(m for m in mechanical if m["name"] == "USB_C_Male_Metal_Shell")
    # The mouth datum remains unverified. These are actual body bounds,
    # useful to reject gross displacement, not an invented mating anchor.
    def center(bounds):
        return [(a + b) / 2 for a, b in zip(bounds["min_mm"], bounds["max_mm"])]
    j1_center, plug_center = center(j1["box"]), center(plug["box"])
    report = {
        "schema": "deepreal.private-pcb-enclosure-fit.v1", "revision": "MECH-FIT-04",
        "status": "NOMINAL_FIT_DIAGNOSIS_NOT_ASSEMBLY_APPROVAL",
        "source_board_sha256": manifest["source_board_sha256"],
        "mechanical_source": str(MECHANICAL_SOURCE), "mechanical_source_sha256": digest(MECHANICAL_SOURCE),
        "mechanical_contract_sha256": digest(CONTRACT_PATH),
        "fixed_origin_mm": [65, 34], "registration_matrix_blender_metres": [list(row) for row in transform],
        "rigid_registration": registration_audit,
        "substrate_bounds_device_mm": box(substrate), "mechanical_board_target_web_mm": contract["board"],
        "candidate_solids_screened": len(candidates), "mechanical_objects_screened": len(mechanical),
        "excluded_nonphysical_or_superseded_objects": excluded_names,
        "inspection_weld_mm": WELD_MM, "positive_volume_threshold_mm3": VOLUME_MM3,
        "solid_screen_self_tests": tests, "rest_box_candidate_pairs_checked": rest_candidates,
        "rest_findings": [{**r, "ref": refs[r["candidate"]]} for r in rest_results],
        "rigid_sweep": sweep, "restored_mechanical_matrix_error": matrix_error,
        "source_mesh_boundary_counts": {m["name"]: m["nonmanifold_edges"] for m in mechanical},
        "candidate_mesh_boundary_counts": {c["name"]: c["nonmanifold_edges"] for c in candidates},
        "usb": {"J1_body_bounds_blender_mm": j1["box"], "retained_plug_shell_bounds_blender_mm": plug["box"],
                "body_center_offset_blender_mm": [a - b for a, b in zip(j1_center, plug_center)],
                "rest_plug_findings": [r for r in rest_results if r["mechanical"] in plug_names],
                "mating_axis_and_mouth_status": "UNVERIFIED; centres are not mouth/footprint datums"},
        "limits": [
            "Nominal inherited solids/envelopes only, no manufacturing or assembly tolerance budget",
            "Positive intersections are fit failures, including any intended contact that has no compression/load specification",
            "Open geometry, contacts and subthreshold intersections remain unresolved, not counted as clearance passes",
            "Rigid poses sampled every 5 degrees, not a continuous swept-volume proof",
            "No selected USB plug/receptacle pair, plug insertion-force or retention qualification",
            "No connector latch geometry or service/tool sweep; no latch-access approval",
            "Retained flex strips are rigid illustrations, not deforming routes or dynamic-fatigue evidence",
            "Thermal compression, electrical insulation, PCB mounts and microphone ports are unqualified",
            "Wrong U1/PF53 and other inherited packages still prevent a final package fit conclusion",
        ],
        "fabrication_allowed": False, "public_visual_allowed": False, "viewer_integration_allowed": False,
    }
    (output / "enclosure-fit-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return scene, board_collection, physical, report


def render_enclosure(scene, board_collection, physical, report, output):
    configure_studio(scene)
    # The cutaway is visibility-only: no mechanical body is cut, moved or
    # resized. The installed intersections remain in the saved model.
    removed = {"R30_One_Piece_Enclosure", "Shield_Front_Lid", "Shield_Rear_Tray",
               "Thermal_Spreader", "R38_Device_Magnet_Face_CONCEPT"}
    for obj in physical:
        obj.hide_render = obj.name in removed or obj.hide_render
    key = bpy.data.lights.new("Fit key", "AREA")
    key_obj = bpy.data.objects.new(key.name, key)
    scene.collection.objects.link(key_obj)
    key_obj.location = (.02, -.12, .14)
    key_obj.rotation_euler = (Vector((.004, .004, -.01)) - key_obj.location).to_track_quat("-Z", "Y").to_euler()
    key.energy, key.shape, key.size = .8, "DISK", .15
    fill = bpy.data.lights.new("Fit fill", "AREA")
    fill_obj = bpy.data.objects.new(fill.name, fill)
    scene.collection.objects.link(fill_obj)
    fill_obj.location = (-.08, -.06, .05)
    fill_obj.rotation_euler = (Vector((0, .01, -.01)) - fill_obj.location).to_track_quat("-Z", "Y").to_euler()
    fill.energy, fill.shape, fill.size = .4, "DISK", .12
    view = camera(scene, "Installed cutaway review", (.105, -.17, .10), (.004, .004, -.004))
    view.data.ortho_scale = .175
    scene.camera = view
    scene.render.stamp_note_text = "MECH-FIT-04 | INSTALLED CUTAWAY | HOUSING + SHIELDS + SPREADER + MOUNT FACE HIDDEN | FIT NOT APPROVED"
    scene.render.filepath = str(output / "installed-cutaway.png")
    bpy.ops.render.render(write_still=True)
    for obj in physical:
        if obj.name in removed:
            obj.hide_render = False
    failures = [r for r in report["rest_findings"] if r["status"] == "POSITIVE_NOMINAL_SOLID_INTERSECTION"]
    failed_refs = {r["ref"] for r in failures}
    highlight = material("Measured collision red", (.65, .018, .007), roughness=.45)
    for obj in board_collection.objects:
        ref = obj.get("PCBA_Ref", "BOARD_SUBSTRATE" if obj.data.name.endswith("_PCB") else None)
        if ref in failed_refs:
            obj.data.materials.clear()
            obj.data.materials.append(highlight)
    # Use a rear-side view to expose the retained shield/USB relationships,
    # with the housing hidden but the thermal stack installed.
    bpy.data.objects["R30_One_Piece_Enclosure"].hide_render = True
    if "Shield_Rear_Tray" in bpy.data.objects:
        bpy.data.objects["Shield_Rear_Tray"].hide_render = True
    diagnostic = camera(scene, "Installed diagnostic", (.11, .14, .09), (.004, .01, -.012))
    diagnostic.data.ortho_scale = .17
    scene.camera = diagnostic
    scene.render.stamp_note_text = "INSTALLED FIT DIAGNOSIS | RED = MEASURED BODY INTERSECTIONS | HOUSING + REAR SHIELD HIDDEN | NO FIT APPROVAL"
    scene.render.filepath = str(output / "installed-diagnostic.png")
    bpy.ops.render.render(write_still=True)
    usb = camera(scene, "USB nominal intersection detail", (.075, .057, -.006), (.0515, .013, -.021))
    usb.data.ortho_scale = .034
    scene.camera = usb
    scene.render.stamp_note_text = "USB MODEL INTERSECTIONS | SOCKET + SUBSTRATE EDGES RED | RETAINED PLUG | NO MATING APPROVAL"
    scene.render.filepath = str(output / "installed-usb-detail.png")
    bpy.ops.render.render(write_still=True)
    report["diagnostic_red_refs"] = sorted(failed_refs)
    report["cutaway_hidden_objects"] = sorted(removed)
    report["diagnostic_hidden_objects"] = ["R30_One_Piece_Enclosure", "Shield_Rear_Tray"]
    report["diagnostic_visibility_only"] = True
    for obj in scene.objects:
        if obj.type in ("LIGHT", "CAMERA"):
            obj.hide_set(True)
    for obj in physical:
        if obj.name in removed:
            obj.hide_render = True
        obj.hide_set(obj.name in removed or obj.hide_render)
    scene.camera = view
    framed = frame_viewports(scene, view, (.004, .004, -.01), .20)
    scene.name = "MECH-FIT-04 Installed Fit Diagnosis"
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "deepreal-mech-fit-04-installed-review.blend"))
    report["interactive_viewports"] = framed
    (output / "enclosure-fit-audit.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    layout, manifest = checked_inputs(args.candidate_dir, args.output_dir)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    board_audit = standalone(layout, manifest, args.candidate_dir, output)
    scene, board_collection, physical, fit = enclosure(layout, manifest, output, board_audit)
    render_enclosure(scene, board_collection, physical, fit, output)
    bpy.ops.wm.open_mainfile(filepath=str(output / "deepreal-mech-fit-04-board.blend"))
    before = capture(bpy.data.collections[BOARD_COLLECTION].objects)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(output / "candidate-board.glb"))
    after = capture(bpy.context.scene.objects)
    if before.keys() != after.keys():
        raise ValueError("mesh transport lost identities")
    error = max(max(distance_to(points, after[key]), distance_to(after[key], points))
                for key, points in before.items())
    if error > .00005:
        raise ValueError("mesh transport difference exceeds 50 nm")
    audit = {
        "schema": "deepreal.private-package-model-audit.v1", "revision": "MECH-FIT-04",
        "source_board_sha256": manifest["source_board_sha256"],
        "source_export_sha256": manifest["source_export_sha256"], "native_glb_sha256": manifest["glb_sha256"],
        "builder_sha256": digest(Path(__file__)), "solid_screen_sha256": digest(HERE / "pcb_solid_fit.py"),
        "native_body_refs": manifest["native_model_refs"],
        "representative_body_refs": manifest["missing_model_refs"],
        "hole_pad_only_refs": manifest["pad_or_hole_only_refs"], **board_audit,
        "transport": {"status": "PASS", "mesh_identities_preserved": len(before),
                      "max_bidirectional_vertex_difference_mm": error,
                      "source_vertices_checked": sum(map(len, before.values())),
                      "export_vertices_checked": sum(map(len, after.values()))},
        "fabrication_allowed": False, "public_visual_allowed": False, "viewer_integration_allowed": False,
    }
    names = ("candidate-board.glb", "deepreal-mech-fit-04-board.blend",
             "deepreal-mech-fit-04-installed-review.blend", "board-top.png", "board-bottom.png",
             "installed-cutaway.png", "installed-diagnostic.png", "installed-usb-detail.png",
             "enclosure-fit-audit.json")
    audit["output_sha256"] = {name: digest(output / name) for name in names}
    (output / "model-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    checked_inputs(args.candidate_dir, output / "unused-next-review")
    print("PRIVATE FIT REVIEW", output, "transport error mm", error, flush=True)


if __name__ == "__main__":
    main()
