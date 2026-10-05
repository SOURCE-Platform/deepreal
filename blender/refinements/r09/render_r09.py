#!/usr/bin/env python3
"""Render R09 review views from the saved native Blender file."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r09.blend"
OUT = HERE / "renders"


def review_camera(name, position, target, scale, studio):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = 0.001
    obj = bpy.data.objects.new(name, data)
    obj.location = position
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    studio.objects.link(obj)
    return obj


def save(scene, camera, filename):
    scene.camera = camera
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    print("R09 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    housing = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    bpy.data.collections["00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    housing.hide_render = False
    save(scene, bpy.data.objects["Camera_R05_Front"], "r09-exterior-front.png")

    housing.hide_render = True
    scene.view_settings.exposure = -0.8
    rear = review_camera("Camera_R09_Rear_Layout",
                         (0.025, 0.155, -0.009),
                         (0.004, 0.014, -0.009), 0.14, studio)
    save(scene, rear, "r09-internal-rear.png")

    detail = review_camera("Camera_R09_Right_USB_Detail",
                           (0.086, 0.095, -0.017),
                           (0.050, 0.014, -0.017), 0.055, studio)
    save(scene, detail, "r09-right-usb-detail.png")

    bpy.data.objects["Thermal_Spreader"].hide_render = True
    bpy.data.objects["Shield_Rear_Tray"].hide_render = True
    bpy.data.collections["04 — THERMAL LINKS + PADS — UNVALIDATED"].hide_render = True
    save(scene, detail, "r09-port-tab-exposed.png")


if __name__ == "__main__":
    main()
