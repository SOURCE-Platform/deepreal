#!/usr/bin/env python3
"""Add published wide RGB assembly envelopes to the R16 optics baseline."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "blender"))
sys.path.insert(0, str(HERE.parent / "r08"))
import macbook  # noqa: E402
from verify_r08 import tree  # noqa: E402

SOURCE = HERE.parent / "r16/deepreal-exterior-refinement-r16.blend"
OUTPUT = HERE / "deepreal-wide-interaction-optics-r20.blend"
REPORT = HERE / "r20-envelope-check.json"
MM = .001


def center(obj):
    return sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices),
               Vector()) / len(obj.data.vertices)


def attach(obj, pivot, collection, note):
    collection.objects.link(obj)
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    obj.display_type = "SOLID"
    obj.color = (.09, .77, .72, 1.0)
    obj.hide_render = True
    obj["R20_Status"] = note
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.name = "DeepReal Interaction Wide RGB Envelope R20"
    pivot = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    window = bpy.data.objects["Interaction_Drum_Lens_RGB_Element"]
    shell = bpy.data.objects["Interaction_Sensor_Head"]
    outward = Vector((0, -math.sqrt(.5), -math.sqrt(.5)))
    up = Vector((0, -math.sqrt(.5), math.sqrt(.5)))
    nose = center(window) - outward * (.35 * MM)
    board_center = nose - outward * (8.3 * MM)
    collection = bpy.data.collections.new("10 — R20 WIDE RGB PHYSICAL ENVELOPES")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_06"
    material = bpy.data.materials.new("R20_Wide_RGB_Envelope_Material")
    material.diffuse_color = (.09, .77, .72, .7)
    lens = attach(macbook.cylinder(
        "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20",
        (nose + board_center) / 2, outward, 6.95 * MM / 2,
        8.3 * MM, material, seg=64), pivot, collection,
        "Conservative lens envelope; exact manufacturer shape and optical datum unverified")
    board = attach(macbook.slab(
        "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20",
        board_center, macbook.X, up, (10.8 * MM, 10.8 * MM),
        .25 * MM, .6 * MM, material), pivot, collection,
        "Assembly XY outline; 0.6 mm display thickness is not a published stack")
    pivot["R20_Provisional_Optical_Directions_deg"] = [0.0, 22.5, 45.0]
    pivot["R20_Interaction_RGB"] = "SA36VA30P wide; 102 H x 67 V degrees"
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    face["R20_Provisional_Optical_Directions_deg"] = [-45.0, 0.0, 45.0]
    face["R20_Face_RGB"] = "SA31VA30P standard; 66 H x 41 V degrees"
    for old_key in ("R15_Allowed_Optical_Direction_deg",
                    "R15_Pivot_X_Range_deg"):
        if old_key in face:
            del face[old_key]
    for old_key in ("R16_Studied_Optical_Directions_deg",
                    "R16_Final_Travel_Range"):
        if old_key in pivot:
            del pivot[old_key]
    for old_key in ("R16_Interaction_Optics_Down_Stop_Study_deg",
                    "R16_Interaction_Travel_Status"):
        if old_key in scene:
            del scene[old_key]
    scene["R20_Status"] = (
        "wide RGB physical envelope and FOV study; old R16 housing and "
        "drive remain, open-top cradle and optical clearance unbuilt")
    bpy.context.view_layer.update()
    shell_tree = tree(shell)
    overlaps = {obj.name: len(tree(obj).overlap(shell_tree))
                for obj in (lens, board)}
    neighbors = ("Interaction_Internal_Optical_Carrier",
                 "Interaction_IR_Depth_Module_Body",
                 "Interaction_SL_Projector_Body")
    neighbor_overlaps = {
        obj.name: {name: len(tree(obj).overlap(tree(bpy.data.objects[name])))
                   for name in neighbors}
        for obj in (lens, board)}
    report = {
        "model": str(OUTPUT), "source": str(SOURCE),
        "part": "Raspberry Pi SA36VA30P wide RGB sensor assembly",
        "lens_diameter_mm": 6.95, "lens_depth_dimension_mm": 8.3,
        "assembly_outline_mm": [10.8, 10.8],
        "existing_visual_bore_diameter_mm": 9.0,
        "triangle_overlaps_with_rotating_shell": overlaps,
        "triangle_overlaps_with_neighbor_proxies": neighbor_overlaps,
        "limits": [
            "Envelope placement uses existing visual window as a provisional nose datum.",
            "Published 8.3 mm depth is represented as a conservative cylinder, not manufacturer CAD.",
            "Existing R16 RGB proxy and window are retained; fit to carrier and optical cone are unverified.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    # Save an inspection-first viewport: the full assembly remains in the
    # file but is hidden until Alt-H, so the new geometry is unmistakable.
    visible = {lens.name, board.name,
               "Interaction_Internal_Optical_Carrier"}
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            obj.hide_set(obj.name not in visible)
    target = Vector((.044, -.006, .016))
    eye = Vector((.085, -.040, .055))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            space.shading.type = "SOLID"
            space.shading.color_type = "MATERIAL"
            space.region_3d.view_location = target
            space.region_3d.view_distance = .055
            space.region_3d.view_rotation = (
                target - eye).to_track_quat("-Z", "Y")
            space.region_3d.view_perspective = "PERSP"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R20 SAVED", OUTPUT)
    print("R20 SHELL OVERLAPS", overlaps)
    print("R20 NEIGHBOR OVERLAPS", neighbor_overlaps)


if __name__ == "__main__":
    main()
