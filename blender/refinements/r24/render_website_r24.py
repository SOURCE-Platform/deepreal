#!/usr/bin/env python3
"""Render the finished exterior for use on the website."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_r24 import camera  # noqa: E402

MODEL = HERE / "deepreal-finished-exterior-r24.blend"
PRESENTATION = HERE / "deepreal-website-presentation-r24.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= .08
    fill_data = bpy.data.lights.new("R24_Front_Lens_Fill", "AREA")
    fill_data.energy = 1.2
    fill_data.shape = "DISK"
    fill_data.size = .20
    fill = bpy.data.objects.new("R24_Front_Lens_Fill", fill_data)
    studio.objects.link(fill)
    fill.location = (0, -.16, .055)
    fill.rotation_euler = (Vector((0, 0, .014)) - fill.location).to_track_quat(
        "-Z", "Y").to_euler()
    hero = camera("Camera_R24_Website_Hero", (.105, -.22, .072),
                  (0, .003, .008), .158, studio)
    scene.camera = hero
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1125
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(PRESENTATION))
    for name, transparent in (("r24-website-hero-dark.png", False),
                              ("r24-website-hero-transparent.png", True)):
        scene.render.film_transparent = transparent
        scene.render.filepath = str(HERE / name)
        bpy.ops.render.render(write_still=True)
        print("R24 WEBSITE RENDER", scene.render.filepath)


if __name__ == "__main__":
    main()
