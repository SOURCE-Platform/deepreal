#!/usr/bin/env python3
"""Render the contoured roof and its drum clearance from review angles."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
from render_r24 import camera  # noqa: E402

MODEL = HERE / "deepreal-contoured-roof-edge-r26.blend"


def render(scene, view, name):
    scene.camera = view
    scene.render.filepath = str(HERE / name)
    bpy.ops.render.render(write_still=True)
    print("R26 REVIEW RENDER", scene.render.filepath)


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
        if obj.type == "LIGHT":
            obj.data.energy *= .08
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    fill_data = bpy.data.lights.new("R26_Front_Lens_Fill", "AREA")
    fill_data.energy = 1.2
    fill_data.shape = "DISK"
    fill_data.size = .20
    fill = bpy.data.objects.new("R26_Front_Lens_Fill", fill_data)
    studio.objects.link(fill)
    fill.location = (0, -.16, .055)
    fill.rotation_euler = (Vector((0, 0, .014)) - fill.location).to_track_quat(
        "-Z", "Y").to_euler()
    hero = camera("Camera_R26_Hero", (.105, -.22, .085),
                  (0, .003, .008), .158, studio)
    render(scene, hero, "r26-hero-preview.png")
    side = camera("Camera_R26_Side", (.24, 0, .003),
                  (0, 0, .003), .13, studio)
    render(scene, side, "r26-side-preview.png")
    detail = camera("Camera_R26_Roof_Detail", (.24, .003, .047),
                    (0, .003, .026), .032, studio)
    render(scene, detail, "r26-roof-detail.png")
    high = camera("Camera_R26_High", (.035, -.15, .17),
                  (0, .002, .016), .14, studio)
    render(scene, high, "r26-above-preview.png")


if __name__ == "__main__":
    main()
