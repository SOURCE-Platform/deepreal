#!/usr/bin/env python3
"""Render the overview and four linked scenes for review and web use.

Run after build_scene.py:
    Blender --background blender/deepreal.blend --python blender/review_renders.py
"""

import os

import bpy


HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "renders")

PRESENTATION_RENDERS = (
    ("00 Four View Overview", "presentation-00-four-view-overview"),
    ("01 Fully Assembled", "presentation-01-fully-assembled"),
    ("02 Housing Removed", "presentation-02-housing-removed"),
    ("03 Functional Core", "presentation-03-functional-core"),
    ("04 Electronics Exploded", "presentation-04-electronics-exploded"),
)


def main():
    os.makedirs(OUTPUT, exist_ok=True)
    window = bpy.context.window
    for scene_name, filename in PRESENTATION_RENDERS:
        scene = bpy.data.scenes.get(scene_name)
        if scene is None:
            raise RuntimeError("missing presentation scene: " + scene_name)
        if window:
            window.scene = scene
        scene.render.filepath = os.path.join(OUTPUT, filename + ".png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        print("presentation render:", scene.render.filepath)


if __name__ == "__main__":
    main()
