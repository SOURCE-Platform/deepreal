#!/usr/bin/env python3
"""Build an open-top, side-supported drum concept from the R20 optics study."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r15", HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r21_chassis import add_chassis, material  # noqa: E402
from r21_mechanism import add_mechanisms, remove_superseded  # noqa: E402

SOURCE = HERE.parent / "r20/deepreal-wide-interaction-optics-r20.blend"
PRE_ACCESS = HERE.parent / "r14/deepreal-exterior-refinement-r14.blend"
OUTPUT = HERE / "deepreal-side-supported-drums-r21.blend"


def close_legacy_rear_openings():
    names = tuple(side + "_Sensor_Head" for side in ("Face", "Interaction"))
    with bpy.data.libraries.load(str(PRE_ACCESS), link=False) as (source, loaded):
        loaded.objects = list(names)
    removed = []
    for name, original in zip(names, loaded.objects):
        shell = bpy.data.objects[name]
        shell.data = original.data.copy()
        shell["R21_Shell_Access"] = (
            "rear access cut removed; inner end cap still solid under the "
            "provisional ring and must be opened for assembly")
        bpy.data.objects.remove(original, do_unlink=True)
        cover = bpy.data.objects.get(name.replace("Sensor_Head", "Rear_Access_Cover_REMOVABLE_CONCEPT"))
        if cover:
            removed.append(cover.name)
            bpy.data.objects.remove(cover, do_unlink=True)
    return removed


def camera(scene):
    data = bpy.data.cameras.new("Camera_R21_Exterior_Review")
    data.type = "ORTHO"
    data.ortho_scale = .155
    data.clip_start = .001
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = (.12, -.19, .105)
    target = Vector((0, .003, .004))
    obj.rotation_euler = (target - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    scene.camera = obj
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        obj.hide_set(False)
    for name in ("98 — UNVERIFIED PCB BODY EVIDENCE — HIDDEN",
                 "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"):
        bpy.data.collections[name].hide_viewport = True
    removed = remove_superseded()
    removed.extend(close_legacy_rear_openings())
    body, supports = add_chassis(scene)
    parts = add_mechanisms(scene)
    for suffix in ("RGB_Module_Body", "RGB_Module_Barrel"):
        obj = bpy.data.objects.get("Interaction_" + suffix)
        if obj:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    lens = bpy.data.objects[
        "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20"]
    assembly = bpy.data.objects[
        "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20"]
    lens.data.materials.clear()
    lens.data.materials.append(material("R21_Wide_Lens_Dark",
                                        (.075, .09, .095, 1), .25, .18))
    assembly.data.materials.clear()
    assembly.data.materials.append(material("R21_Wide_RGB_Board_Green",
                                            (.035, .24, .16, 1), .05, .48))
    for obj in (lens, assembly):
        obj.hide_render = False
        obj["R21_Status"] = (
            "wide RGB size envelope only; old carrier still conflicts; "
            "mounting, optical datum and board clearance open")
    scene.name = "DeepReal Side-Supported Drum Concept R21"
    scene["R21_Design_Intent"] = (
        "open top; left/center/right fixed supports; bearings at both "
        "drum ends; closed rear shell; no fixed arms through rear shell")
    scene["R21_Engineering_Status"] = (
        "visual/mechanism envelope only; not fabrication-ready")
    scene["R21_Open_Issues"] = (
        "wide lens/carrier overlap; bearing and motor selection; ring gear "
        "teeth/torque; real hollow drum and inner-end access; dynamic flex; "
        "enclosure fasteners and full sweep")
    review_camera = camera(scene)
    target = Vector((0, .003, .004))
    eye = Vector((.12, -.19, .105))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.region_3d.view_location = target
                space.region_3d.view_distance = .19
                space.region_3d.view_rotation = (
                    target - eye).to_track_quat("-Z", "Y")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {
        "model": str(OUTPUT), "source": str(SOURCE),
        "closed_shell_source": str(PRE_ACCESS),
        "camera": review_camera.name,
        "drum_outward_shift_mm_each": 2.0,
        "approximate_end_gap_mm": 5.0,
        "center_support_thickness_mm": 3.0,
        "outer_support_thickness_mm": 2.2,
        "fixed_supports": [obj.name for obj in supports],
        "lower_housing": body.name,
        "mechanism_envelopes": [obj.name for obj in parts],
        "superseded_objects_removed": removed,
        "readiness": "CONCEPT_ONLY",
    }
    (HERE / "r21-assembly-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R21 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
