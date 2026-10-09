#!/usr/bin/env python3
"""Render the R36 fixed-bearing support and cable-window study."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-inner-bearing-window-r36.blend"


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


def render(name, view, visible):
    selected = set(visible)
    for obj in bpy.data.objects:
        if obj.type != "CAMERA":
            obj.hide_render = obj.name not in selected
    scene = bpy.context.scene
    scene.camera = view
    scene.render.filepath = str(HERE / name)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("R36 RENDER", scene.render.filepath)


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

    end = camera("R36_Bearing_Window_End_View", (.06, -.025, .044),
                 (-.003, -.0015, .020), .046)
    side = camera("R36_Bearing_Window_Side_View", (.025, -.07, .047),
                  (-.006, -.0015, .020), .053)
    support = (
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "Face_Inner_Bearing_Rotating_Race_ENV_R21",
        "Face_Open_Inner_End_Ring_R21",
        "R36_Face_Fixed_Bearing_Axial_Neck_ENV",
        "R36_Face_Inner_Race_Rear_Side_Web_ENV",
        "R36_Face_Inner_Race_Front_Side_Web_ENV",
        "R36_Face_Full_Width_Straight_Exit_ENV",
    )
    render("r36-bearing-window-end.png", end, support)
    render("r36-bearing-window-side.png", side, support + (
        "Face_Motor_Cantilever_R21",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
        "Face_Internal_Optical_Carrier",
    ))


if __name__ == "__main__":
    main()
