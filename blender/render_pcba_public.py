#!/usr/bin/env python3
"""Render the approved investor-facing PCBA asset package.

Run after ``build_scene.py`` with ``deepreal.blend`` loaded in background mode.
Both high-resolution masters and lighter website images are deterministic.
"""

import os

import bpy


HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(
    REPO_ROOT, "hardware", "electronics", "deepreal-main-pcba", "renders")

ASSETS = (
    ("06 PCBA Top", "deepreal-pcba-top", 3200, 1440),
    ("07 PCBA Bottom", "deepreal-pcba-bottom", 3200, 1440),
    ("08 PCBA Dimensioned", "deepreal-pcba-dimensioned", 3200, 1760),
    ("04 Electronics Exploded", "deepreal-electronics-exploded", 3200, 2400),
    ("05 Shield Cutaway", "deepreal-shield-cutaway", 3200, 2400),
    ("03 Functional Core", "deepreal-pcba-installed", 3200, 2400),
)


def render_asset(scene, stem, width, height, suffix):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(OUTPUT, stem + "-" + suffix + ".png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
    print("public PCBA render:", scene.render.filepath)


def main():
    os.makedirs(OUTPUT, exist_ok=True)
    window = bpy.context.window
    for scene_name, stem, width, height in ASSETS:
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            raise RuntimeError("missing public scene: " + scene_name)
        if window:
            window.scene = scene
        render_asset(scene, stem, width, height, "master")
        render_asset(scene, stem, width // 2, height // 2, "web")


if __name__ == "__main__":
    main()
