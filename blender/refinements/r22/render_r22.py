#!/usr/bin/env python3
"""Render the canopy from exterior, top, and low-pose review angles."""

from math import radians
from pathlib import Path
from shutil import copy2

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-curved-drum-canopy-r22.blend"
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


def render(scene, view, filename, preview=None):
    scene.camera = view
    path = OUT / filename
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    if preview:
        copy2(path, HERE / preview)
    print("R22 RENDER", path)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= .16
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    render(scene, bpy.data.objects["Camera_R21_Exterior_Review"],
           "r22-exterior-three-quarter.png", "r22-exterior-preview.png")
    side = camera("Camera_R22_Side", (.21, -.012, .075),
                  (0, .002, .012), .095, studio)
    render(scene, side, "r22-side-profile.png", "r22-side-preview.png")
    high = camera("Camera_R22_High", (.035, -.15, .17),
                  (0, .002, .016), .14, studio)
    render(scene, high, "r22-above.png", "r22-above-preview.png")
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    face.rotation_euler.x = radians(45)
    interaction.rotation_euler.x = 0
    bpy.context.view_layer.update()
    render(scene, high, "r22-low-pose.png", "r22-low-pose-preview.png")


if __name__ == "__main__":
    main()
