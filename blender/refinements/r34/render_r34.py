#!/usr/bin/env python3
"""Render internal review views from the R34 interface study."""

from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-face-interface-study-r34.blend"


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


def visible_only(names):
    selected = set(names)
    for obj in bpy.data.objects:
        if obj.type != "CAMERA":
            obj.hide_render = obj.name not in selected


def render(name, camera_obj, visible):
    scene = bpy.context.scene
    visible_only(visible)
    scene.camera = camera_obj
    scene.render.filepath = str(HERE / name)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("R34 RENDER", scene.render.filepath)


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

    overview = camera("R34_Internal_Review", (-.100, -.125, .075),
                      (-.030, -.001, .020), .105)
    outer = camera("R34_Outer_Encoder_Detail", (-.106, -.065, .048),
                   (-.056, -.001, .020), .043)
    inner = camera("R34_Inner_Flex_Detail", (.038, -.065, .052),
                   (-.005, -.001, .020), .05)

    common = {
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "Face_Inner_Bearing_Rotating_Race_ENV_R21",
        "Face_Outer_Rotating_Hub_R21",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
        "Face_Motor_Cantilever_R21",
        "Face_Motor_Pinion_ENV_R21",
        "Face_Internal_Ring_Gear_ENV_R21",
    }
    study = {obj.name for obj in bpy.data.objects
             if obj.name.startswith("R34_Face_") and obj.type == "MESH"}
    render("r34-mechanism-study.png", overview, common | study)
    render("r34-outer-encoder-detail.png", outer,
           {"R34_Face_Outer_Rotating_Shaft_ENV", "R34_Face_Outer_Bearing_ENV",
            "R34_Face_Outer_Rotating_Hub_ENV", "R34_Face_Axial_Magnet_ENV",
            "R34_Face_Axial_Sensor_IC_ENV", "R34_Face_Axial_Sensor_PCB_ENV"})
    render("r34-inner-flex-detail.png", inner,
           {"Face_Inner_Bearing_Fixed_Race_ENV_R21",
            "Face_Inner_Bearing_Rotating_Race_ENV_R21",
            "Face_Center_Fed_Motor_Stator_ENV_R21",
            "Face_Motor_Cantilever_R21", "R34_Face_Inner_Flex_Width_ENV"})


if __name__ == "__main__":
    main()
