#!/usr/bin/env python3
"""Render exterior and internal review previews without modifying the blend."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r08.blend"
OUT = HERE / "renders"


def camera(name, location, target, scale, studio):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = 0.001
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    studio.objects.link(obj)
    return obj


def render(scene, view, filename):
    scene.camera = view
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    print("RENDER", scene.render.filepath)


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
    wire = bpy.data.collections["00A — WIREFRAME FALLBACK — KEEP VISIBLE"]
    wire.hide_render = True
    housing.hide_render = False
    render(scene, bpy.data.objects["Camera_R05_Front"], "r08-exterior-front.png")

    housing.hide_render = True
    scene.view_settings.exposure = -0.8
    rear = camera("Camera_R08_Inside_Rear", (0.025, 0.155, -0.008),
                  (0.0, 0.014, -0.008), 0.14, studio)
    render(scene, rear, "r08-internal-rear.png")

    detail = camera("Camera_R08_USB_Route_Detail", (0.025, 0.155, -0.017),
                    (0.016, 0.014, -0.017), 0.085, studio)
    render(scene, detail, "r08-usb-side-route.png")

    bpy.data.objects["Thermal_Spreader"].hide_render = True
    bpy.data.objects["Shield_Rear_Tray"].hide_render = True
    bpy.data.collections["04 — THERMAL LINKS + PADS — UNVALIDATED"].hide_render = True
    render(scene, detail, "r08-usb-path-exposed.png")


if __name__ == "__main__":
    main()
