#!/usr/bin/env python3
"""Render the proposed outer load path and the cable-route conflict."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from flex_geometry import set_pose  # noqa: E402

MODEL = HERE / "deepreal-face-motion-study-r35.blend"


def camera(name, eye, target, scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = .001
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = eye
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    return obj


def render(name, camera_obj, visible):
    selected = set(visible)
    for obj in bpy.data.objects:
        if obj.type != "CAMERA":
            obj.hide_render = obj.name not in selected
    scene = bpy.context.scene
    scene.camera = camera_obj
    scene.render.filepath = str(HERE / name)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("R35 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_shadows = True
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (.12, .14, .16)
    scene.render.film_transparent = False

    outer = camera("R35_Outer_Load_Path_Review", (-.095, -.065, .05),
                   (-.053, -.0015, .02), .055)
    inner = camera("R35_Inner_Flex_Conflict_Review", (.027, -.07, .053),
                   (-.010, -.0015, .02), .05)
    render("r35-outer-load-path.png", outer, (
        "R35_Face_Outer_Shaft_ENV", "R35_Face_Outer_Hub_ENV",
        "R35_Face_Outer_Coupling_Web_ENV",
        "R35_Face_Outer_Drum_Wall_Sleeve_ENV",
        "R34_Face_Outer_Bearing_ENV"))

    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    flex = bpy.data.objects["R35_Face_Full_Width_Torsion_Candidate_ENV"]
    visible = (
        flex.name,
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "Face_Inner_Race_Upper_Web_R21",
        "Face_Inner_Race_Lower_Web_R21",
        "Face_Inner_Race_Upper_Tab_R21",
        "Face_Inner_Race_Lower_Tab_R21",
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Internal_Optical_Carrier",
        "Face_RGB_Module_Body",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
    )
    for angle, label in ((0, "center"), (45, "up45")):
        pivot.rotation_euler.x = math.radians(angle)
        set_pose(flex, angle)
        render(f"r35-flex-{label}-conflict.png", inner, visible)


if __name__ == "__main__":
    main()
