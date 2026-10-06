#!/usr/bin/env python3
"""Render the Face drum drive alone so its internal ring is inspectable."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r15.blend"
OUTPUT = HERE / "renders/r15-internal-ring-drive-study.png"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    OUTPUT.parent.mkdir(exist_ok=True)
    show = {"Face_Ring_Gear", "Face_Motor_Pinion", "Face_Geared_Motor",
            "Face_Motor_Output_Shaft_CONCEPT", "Face_Drum_Axle"}
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            obj.hide_render = obj.name not in show
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    for light in (obj for obj in bpy.data.objects if obj.type == "LIGHT"):
        light.data.energy *= .05
    for collection in bpy.data.collections:
        if collection.name.startswith("00A — WIREFRAME FALLBACK"):
            collection.hide_render = True
    data = bpy.data.cameras.new("Camera_R15_Internal_Ring_Drive")
    data.type = "ORTHO"
    data.ortho_scale = .037
    data.clip_start = .001
    camera = bpy.data.objects.new(data.name, data)
    camera.location = (-.105, .037, .050)
    camera.rotation_euler = (Vector((-.052, -.0015, .020)) -
                             camera.location).to_track_quat("-Z", "Y").to_euler()
    studio.objects.link(camera)
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT)
    bpy.ops.render.render(write_still=True)
    print("R15 INTERNAL RING", OUTPUT)


if __name__ == "__main__":
    main()
