#!/usr/bin/env python3
"""Render the R13 center gap with and without the exterior housing."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r13.blend"
OUT = HERE / "renders"


def camera(name, position, target, scale, collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = 0.001
    obj = bpy.data.objects.new(name, data)
    obj.location = position
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    collection.objects.link(obj)
    return obj


def save(scene, cam, filename):
    scene.camera = cam
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    print("R13 RENDER", scene.render.filepath)


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
    bpy.data.collections["00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    housing = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    housing.hide_render = False
    save(scene, bpy.data.objects["Camera_R05_Front"],
         "r13-exterior-front.png")

    housing.hide_render = True
    scene.view_settings.exposure = -0.8
    front = camera("Camera_R13_Center_Seam",
                   (0, -0.12, 0.020), (0, -0.0015, 0.020),
                   0.045, studio)
    save(scene, front, "r13-drum-gap-front.png")

    angle = camera("Camera_R13_Center_Seam_Angle",
                   (0.060, -0.105, 0.051),
                   (0, -0.0015, 0.020), 0.085, studio)
    save(scene, angle, "r13-drum-gap-angle.png")


if __name__ == "__main__":
    main()
