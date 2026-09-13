#!/usr/bin/env python3
"""Render the approved investor-facing PCBA asset package.

Run after ``build_scene.py`` with ``deepreal.blend`` loaded in background mode.
Both high-resolution masters and lighter website images are deterministic.
"""

import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pcba_kicad_data import load as load_kicad_export, public_ready  # noqa: E402


REPO_ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(
    REPO_ROOT, "hardware", "electronics", "deepreal-main-pcba", "renders")
MANIFEST = os.path.join(os.path.dirname(OUTPUT), "public-assets.json")
DESIGN_STATUS = os.path.join(os.path.dirname(OUTPUT), "design-status.json")

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
    with open(MANIFEST, encoding="utf-8") as stream:
        manifest = json.load(stream)
    with open(DESIGN_STATUS, encoding="utf-8") as stream:
        status = json.load(stream)
    if (manifest.get("public_visual_allowed") is not True
            or status.get("public_visual_allowed") is not True
            or not public_ready(load_kicad_export())):
        raise RuntimeError(
            "PCBA public rendering is paused until the manifest, design status, "
            "and canonical KiCad export all pass the release gate")
    if any(obj.get("PCBA_Visual_Copper") for obj in bpy.data.objects):
        raise RuntimeError(
            "superseded handmade visual copper exists in the scene; rebuild "
            "from the canonical KiCad export before public rendering")
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
