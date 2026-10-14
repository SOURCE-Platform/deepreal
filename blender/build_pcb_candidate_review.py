"""Build and render a source-bound private board, without canonical integration."""

import argparse
import itertools
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pcb_candidate_review_data import checked_inputs, digest
from pcba_native_import import _owner, _join, _envelope
from pcba_bom import ALL_PARTS
from pcb_fit_geometry import positive_box_overlap


def box(obj):
    points = [obj.matrix_world @ Vector(p) * 1000 for p in obj.bound_box]
    return {"min_mm": [min(p[i] for p in points) for i in range(3)],
            "max_mm": [max(p[i] for p in points) for i in range(3)]}


def material(name, color, metallic=0, roughness=0.5):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return result


def camera(scene, name, position, target):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = 0.126
    data.clip_start = 0.0001
    data.clip_end = 10
    return obj


def light(scene, name, position, power, size):
    data = bpy.data.lights.new(name, "AREA")
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0.006, 0, 0)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    data.energy, data.shape, data.size = power, "DISK", size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    layout, manifest = checked_inputs(args.candidate_dir, args.output_dir)
    output = args.output_dir.resolve()
    refs = {c["ref"]: c for c in layout["components"]}
    metadata = {c["ref"]: c for c in ALL_PARTS}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "MECH-FIT-03 Private Board Review"
    electronics = bpy.data.collections.new("Complete Candidate PCBA")
    scene.collection.children.link(electronics)
    bpy.ops.import_scene.gltf(filepath=str(args.candidate_dir / manifest["glb"]))
    imported = list(bpy.data.objects)
    empties = [o for o in imported if o.type == "EMPTY"]
    groups, surfaces, anchors = {}, [], {}
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
        raise ValueError("imported native inventory differs from manifest")
    substrates = [o for o in surfaces if o.data.name.endswith("_PCB")]
    if len(substrates) != 1:
        raise ValueError("ambiguous substrate")
    substrate = substrates[0]
    substrate_box = box(substrate)
    low, high = substrate_box["min_mm"][2] * .001, substrate_box["max_mm"][2] * .001
    models, max_anchor_error, max_join_error = {}, 0.0, 0.0
    native_vertices_before = sum(len(o.data.vertices) for meshes in groups.values() for o in meshes)
    for ref, meshes in sorted(groups.items()):
        old_boxes = [box(o) for o in meshes]
        original = {k: [op(b[k][i] for b in old_boxes) for i in range(3)]
                    for k, op in (("min_mm", min), ("max_mm", max))}
        obj = _join(meshes)
        matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix
        obj.name = "Candidate_" + ref
        models[ref] = obj
        new_box = box(obj)
        max_join_error = max(max_join_error, *(abs(a - b) for k in original
                            for a, b in zip(original[k], new_box[k])))
        obj["PCBA_ModelStatus"] = "NATIVE_INHERITED_UNVERIFIED_PACKAGE"
    if native_vertices_before != sum(len(o.data.vertices) for o in models.values()) or max_join_error > .00005:
        raise ValueError("native join lost vertices or moved geometry")
    for ref in manifest["missing_model_refs"]:
        if ref not in metadata:
            raise ValueError("no documented envelope: " + ref)
        obj = _envelope(refs[ref], metadata[ref], [65, 34], high + .000085, electronics)
        obj.name = "Representative_" + ref
        models[ref] = obj
        obj["PCBA_EnvelopeSource"] = metadata[ref]["source"]
        # This is an explicit body envelope, not invented pin geometry.
        anchors[ref] = obj.matrix_world.copy()
        anchors[ref].translation.x = (refs[ref]["position_mm"][0] - 65) * .001
        anchors[ref].translation.y = (34 - refs[ref]["position_mm"][1]) * .001
    for ref, obj in models.items():
        item = refs[ref]
        expected = Vector(((item["position_mm"][0] - 65) * .001,
                           (34 - item["position_mm"][1]) * .001))
        actual = anchors[ref].translation
        error = (Vector((actual.x, actual.y)) - expected).length * 1000
        max_anchor_error = max(max_anchor_error, error)
        if error > .01:
            raise ValueError("native anchor disagreement: " + ref)
        for key, value in {"PCBA_Ref": ref, "PCBA_UUID": item["uuid"],
                           "PCBA_Side": item["side"], "PCBA_Footprint": item["footprint"],
                           "PCBA_Value": item["value"], "PCBA_PublicAllowed": False,
                           "PCBA_SourceBoardHash": manifest["source_board_sha256"]}.items():
            obj[key] = value
    if set(models) | set(manifest["pad_or_hole_only_refs"]) != set(refs):
        raise ValueError("population lost before modeling")
    for obj in surfaces + list(models.values()):
        matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        electronics.objects.link(obj)
        obj["PCBA_PublicAllowed"] = False
    for obj in empties:
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    bodies = {ref: box(obj) for ref, obj in models.items()}
    overlaps = [{"refs": [a, b], "overlap_mm": widths}
                for a, b in itertools.combinations(sorted(bodies), 2)
                if (widths := positive_box_overlap(bodies[a], bodies[b]))]
    if overlaps:
        raise ValueError("fresh model body-box overlaps: " + str(overlaps))
    for obj in surfaces:
        for mat in obj.data.materials:
            shader = mat.node_tree.nodes.get("Principled BSDF")
            if shader:
                shader.inputs["Alpha"].default_value = 1
                if "soldermask" in obj.data.name:
                    shader.inputs["Base Color"].default_value = (.008, .065, .023, 1)
                    shader.inputs["Metallic"].default_value = 0
                    shader.inputs["Roughness"].default_value = .42
    nonmetal_roles = {
        "mat_1": "capacitor ceramic", "mat_2": "insulator and inductor core",
        "mat_4": "FPC housing",
        "mat_5": "FPC latch", "mat_9": "resistor ceramic", "mat_10": "resistor coating",
    }
    for name in nonmetal_roles:
        mat = bpy.data.materials.get(name)
        if mat:
            shader = mat.node_tree.nodes.get("Principled BSDF")
            shader.inputs["Metallic"].default_value = 0
            shader.inputs["Roughness"].default_value = .6
    output.mkdir(parents=True, exist_ok=False)
    audit = {
        "schema": "deepreal.private-pcb-model-audit.v1",
        "status": "PRIVATE_UNROUTED_REVIEW_NOT_INTERFACE_OR_ELECTRICAL_APPROVAL",
        "source_board_sha256": manifest["source_board_sha256"],
        "source_export_sha256": manifest["source_export_sha256"],
        "native_glb_sha256": manifest["glb_sha256"],
        "builder_script_sha256": digest(Path(__file__)),
        "representative_metadata_sha256": digest(HERE / "pcba_bom.py"),
        "footprints_preserved": len(refs), "body_objects": len(models),
        "native_body_refs": manifest["native_model_refs"],
        "representative_body_refs": manifest["missing_model_refs"],
        "hole_pad_only_refs": manifest["pad_or_hole_only_refs"],
        "native_body_vertex_count_preserved": native_vertices_before,
        "max_native_join_bound_error_mm": max_join_error,
        "max_anchor_error_mm": max_anchor_error,
        "body_aabb_overlap_candidates": overlaps,
        "substrate_bounds_native_mm": substrate_box,
        "nominal_board_thickness_mm": layout["board"]["thickness_mm"],
        "native_substrate_thickness_mm": (high - low) * 1000,
        "board_surface_bounds_native_mm": {obj.name: box(obj) for obj in surfaces},
        "body_bounds_native_mm": bodies,
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
        "limits": [
            "18 explicitly representative package bodies; inherited land patterns still unverified",
            "No netlist or routing; no invented traces, vias or component deletions",
            "Tall J4/J5 headers are inherited placeholders, not low-profile motor selections",
            "No housing, plugged USB, latch-sweep or dynamic-flex fit approval",
        ],
        "appearance_changes": "Opaque substrate, matte green mask and nonmetallic ceramic/plastic/core shaders. "
                              "Native component base colours and all geometry retained.",
        "nonmetal_material_roles": nonmetal_roles,
    }
    (output / "model-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in electronics.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = substrate
    bpy.ops.export_scene.gltf(filepath=str(output / "candidate-board.glb"),
        export_format="GLB", use_selection=True, export_extras=True,
        export_materials="EXPORT", export_yup=True)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == "METAL"
        if any(d.use for d in prefs.devices):
            scene.cycles.device = "GPU"
    except (TypeError, AttributeError):
        pass
    scene.world = bpy.data.worlds.new("Review Studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.35, .40, .46, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
    light(scene, "Broad key", (.015, -.025, .095), .05, .09)
    light(scene, "Edge strip", (.015, .065, .055), .067, .08)
    light(scene, "Front fill", (-.075, -.035, .025), .017, .07)
    light(scene, "Bottom fill", (.01, -.035, -.080), .04, .08)
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -.009))
    floor = bpy.context.object
    floor.name = "Studio_Backdrop_Not_PCB"
    floor.data.materials.append(material("Studio Grey", (.16, .18, .21), roughness=.7))
    top = camera(scene, "Top review", (.064, -.092, .09), (.006, 0, .001))
    bottom = camera(scene, "Bottom review", (.064, -.092, -.085), (.006, 0, 0))
    scene.render.resolution_x = 2400
    scene.render.resolution_y = 1360
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.render.use_stamp = True
    scene.render.use_stamp_note = True
    scene.render.stamp_note_text = "MECH-FIT-03 | PRIVATE UNROUTED STUDY | 18 REPRESENTATIVE BODIES | MOTOR HEADERS UNSELECTED"
    for key in ("use_stamp_date", "use_stamp_time", "use_stamp_frame", "use_stamp_filename",
                "use_stamp_scene", "use_stamp_camera", "use_stamp_render_time"):
        setattr(scene.render, key, False)
    scene.render.stamp_font_size = 18
    scene.render.stamp_foreground = (1, 1, 1, 1)
    scene.render.stamp_background = (.015, .018, .022, .85)
    for stem, view in (("board-top", top), ("board-bottom", bottom)):
        scene.camera = view
        floor.hide_render = view == bottom
        scene.render.filepath = str(output / (stem + ".png"))
        bpy.ops.render.render(write_still=True)
    floor.hide_render = False
    scene.camera = top
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    for obj in scene.objects:
        if obj.name not in electronics.objects:
            obj.hide_set(True)
    bpy.ops.object.select_all(action="DESELECT")
    substrate.select_set(True)
    bpy.context.view_layer.objects.active = substrate
    framed_viewports = 0
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.clip_start = .00001
                space.clip_end = 10
                space.shading.type = "MATERIAL"
                space.overlay.show_floor = False
                space.overlay.show_axis_x = False
                space.overlay.show_axis_y = False
                space.region_3d.view_location = Vector((.006, 0, .001))
                space.region_3d.view_rotation = top.rotation_euler.to_quaternion()
                space.region_3d.view_distance = .16
                space.region_3d.view_perspective = "ORTHO"
                framed_viewports += 1
    if not framed_viewports or any(obj.hide_get() for obj in electronics.objects):
        raise ValueError("interactive board review is not visible and framed")
    audit["interactive_review"] = {
        "display_units": "MILLIMETERS", "framed_viewports": framed_viewports,
        "shading": "MATERIAL", "board_meshes_visible": len(electronics.objects),
        "studio_helpers_hidden": all(obj.hide_get() for obj in scene.objects
                                     if obj.name not in electronics.objects),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "deepreal-mech-fit-03-review.blend"))
    # Recheck every input after the export/render process without relaxing any
    # canonical import guard or modifying the publication manifest.
    checked_inputs(args.candidate_dir, output / "unused-next-review")
    audit["output_sha256"] = {name: digest(output / name) for name in
        ("candidate-board.glb", "board-top.png", "board-bottom.png", "deepreal-mech-fit-03-review.blend")}
    (output / "model-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print("PRIVATE MODEL:", output, "Body overlaps:", len(overlaps), flush=True)


if __name__ == "__main__":
    main()
