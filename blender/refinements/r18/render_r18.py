#!/usr/bin/env python3
"""Show the rear-arm openings at neutral and travel-limit poses."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-rear-support-study-r18.blend"
OUT = HERE / "renders"


def camera(name, location, target, scale, collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = .001
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    return obj


def render(scene, cam, filename):
    scene.camera = cam
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    print("R18 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 950
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    housing = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    housing.hide_render = False
    front = bpy.data.objects["Camera_R05_Front"]
    below = camera("Camera_R18_Low_Front", (-.068, -.140, -.017),
                   (-.027, 0, .020), .095, studio)
    rear = camera("Camera_R18_Rear_Access", (-.072, .110, .055),
                  (-.027, .005, .020), .095, studio)
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    for angle in (-75, 0, 75):
        face.rotation_euler.x = math.radians(angle)
        interaction.rotation_euler.x = 0
        bpy.context.view_layer.update()
        label = "minus75" if angle < 0 else "plus75" if angle else "zero"
        render(scene, front, "r18-face-" + label + "-front.png")
        render(scene, below, "r18-face-" + label + "-low-front.png")
    face.rotation_euler.x = 0
    interaction.rotation_euler.x = math.radians(75 - 45)
    bpy.context.view_layer.update()
    render(scene, front, "r18-interaction-75-front.png")
    housing.hide_render = True
    render(scene, rear, "r18-rear-support-access.png")


if __name__ == "__main__":
    main()
