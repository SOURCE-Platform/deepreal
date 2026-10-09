#!/usr/bin/env python3
"""Show the already unified roof, three supports, and lower enclosure."""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
from render_r24 import camera  # noqa: E402

MODEL = HERE / "deepreal-website-presentation-r26.blend"


def render(scene, camera_obj, filename):
    scene.camera = camera_obj
    scene.render.filepath = str(HERE / filename)
    bpy.ops.render.render(write_still=True)
    print("R26 SHELL REVIEW", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 128
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1125
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            obj.hide_render = obj.name != "R26_One_Piece_Enclosure"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    front = camera("Camera_R26_Shell_Only_Front", (.105, -.22, .085),
                   (0, .003, .008), .158, studio)
    render(scene, front, "r26-shell-only-front.png")
    low = camera("Camera_R26_Shell_Only_Low", (.03, -.17, -.025),
                 (0, .004, .014), .138, studio)
    render(scene, low, "r26-shell-only-low.png")


if __name__ == "__main__":
    main()
