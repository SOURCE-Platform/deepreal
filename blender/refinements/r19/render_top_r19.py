#!/usr/bin/env python3
"""Render the four drum travel limits from above and in front."""

import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_r19 import MODEL, OUT, camera, save


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"].hide_render = False

    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    for side, pivot, base, poses, sign in (
        ("face", face, 0, (("up45", -45), ("down45", 45)), -1),
        ("interaction", interaction, 45,
         (("straight", 0), ("down90", 90)), 1),
    ):
        other = interaction if side == "face" else face
        other.rotation_euler.x = 0
        cam = camera("Camera_R19_" + side + "_above",
                     (sign * .055, -.085, .145),
                     (sign * .027, -.0015, .020), .075, studio)
        for label, angle in poses:
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            save(scene, cam, "r19-" + side + "-" + label + "-above.png")
        pivot.rotation_euler.x = 0


if __name__ == "__main__":
    main()
