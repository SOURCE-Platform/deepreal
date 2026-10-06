#!/usr/bin/env python3
"""Render R14 assembled and internal review views."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r14.blend"
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
    print("R14 RENDER", scene.render.filepath)


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
    shells = bpy.data.collections[
        "01 — DRUM SHELLS — CLICK EYE FOR INTERNALS"]
    housing.hide_render = shells.hide_render = False
    save(scene, bpy.data.objects["Camera_R05_Front"],
         "r14-assembled-front.png")

    housing.hide_render = shells.hide_render = True
    scene.view_settings.exposure = -0.6
    front = camera("Camera_R14_Internal_Front",
                   (0, -0.14, 0.075), (0, 0.003, 0.009),
                   0.15, studio)
    save(scene, front, "r14-internals-front.png")
    rear = camera("Camera_R14_Internal_Rear",
                  (0, 0.15, 0.077), (0, 0.005, 0.008),
                  0.15, studio)
    save(scene, rear, "r14-internals-rear.png")
    face = camera("Camera_R14_Face_Drive_Detail",
                  (-0.115, 0.075, 0.060),
                  (-0.044, 0.006, 0.015), 0.078, studio)
    save(scene, face, "r14-drive-detail.png")


if __name__ == "__main__":
    main()
