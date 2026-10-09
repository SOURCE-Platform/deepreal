#!/usr/bin/env python3
"""Render exterior review of the unified flat-roof enclosure."""

from math import radians
from pathlib import Path
from shutil import copy2

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-integrated-flat-roof-r23.blend"
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


def render(scene, view, filename, preview):
    scene.camera = view
    path = OUT / filename
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    copy2(path, HERE / preview)
    print("R23 RENDER", path)


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
           "r23-exterior-three-quarter.png", "r23-exterior-preview.png")
    side = camera("Camera_R23_Side", (.24, 0, .002),
                  (0, 0, .002), .13, studio)
    render(scene, side, "r23-side-profile.png", "r23-side-preview.png")
    high = camera("Camera_R23_High", (.035, -.15, .17),
                  (0, .002, .016), .14, studio)
    render(scene, high, "r23-above.png", "r23-above-preview.png")
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    face.rotation_euler.x = radians(45)
    interaction.rotation_euler.x = 0
    bpy.context.view_layer.update()
    render(scene, high, "r23-low-pose.png", "r23-low-pose-preview.png")


if __name__ == "__main__":
    main()
