#!/usr/bin/env python3
"""Render the R20 wide-RGB envelope against the current carrier proxy."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-wide-interaction-optics-r20.blend"
IMAGE = HERE / "r20-wide-envelope-vs-carrier.png"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    keep = {
        "Interaction_Internal_Optical_Carrier",
        "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20",
        "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20",
    }
    for collection in bpy.data.collections:
        collection.hide_render = False
    for obj in bpy.data.objects:
        if obj.type != "CAMERA":
            obj.hide_render = obj.name not in keep
            if obj.name in keep:
                obj.display_type = "TEXTURED"
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera_data = bpy.data.cameras.new("Camera_R20_Envelope_Review")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = .040
    camera_data.clip_start = .001
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    camera.location = (.085, -.040, .055)
    camera.rotation_euler = (Vector((.044, -.006, .016)) - camera.location
                             ).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    scene.render.filepath = str(IMAGE)
    bpy.ops.render.render(write_still=True)
    print("R20 RENDER", IMAGE)


if __name__ == "__main__":
    main()
