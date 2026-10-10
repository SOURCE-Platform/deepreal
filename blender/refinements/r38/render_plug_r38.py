#!/usr/bin/env python3
"""Render a close review of the R38 molded USB handle and separate sleeve."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "deepreal-exterior-mount-r38.blend"
OUTPUT = HERE / "r38-usb-plug-detail.png"
PARTS = {
    "USB_C_Plug_Overmold",
    "USB_C_Male_Metal_Shell",
    "USB_C_Male_Internal_Insert",
    "USB_C_Male_Contact_Tongue",
    "USB_C_Cable",
    "R38_USB_Molded_Handle_Taper",
    "R38_USB_Cable_Sleeve",
    "R38_USB_DeepReal_Wordmark",
}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE"}:
            obj.hide_render = obj.name not in PARTS
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.render.film_transparent = False
    scene.world.color = (.045, .05, .06)
    camera_data = bpy.data.cameras.new("R38_Plug_Detail")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = .052
    camera = bpy.data.objects.new("R38_Plug_Detail", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (.078, -.09, -.024)
    target = Vector((.0515, .014, -.038))
    camera.rotation_euler = (target - camera.location).to_track_quat(
        "-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1300
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT)
    bpy.ops.render.render(write_still=True)
    print("R38 PLUG RENDER", OUTPUT)


if __name__ == "__main__":
    main()
