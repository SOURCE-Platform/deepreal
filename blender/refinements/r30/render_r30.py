#!/usr/bin/env python3
"""Render the restored monitor-top ledge in side and assembled views."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
from render_r24 import camera  # noqa: E402

MODEL = HERE / "deepreal-monitor-ledge-enclosure-r30.blend"
PRESENTATION = HERE / "deepreal-monitor-ledge-review-r30.blend"


def render(scene, view, name):
    scene.camera = view
    scene.render.filepath = str(HERE / name)
    bpy.ops.render.render(write_still=True)
    print("R30 RENDER", scene.render.filepath)


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
    fill_data = bpy.data.lights.new("R30_Ledge_Fill", "AREA")
    fill_data.energy = 1.7
    fill_data.shape = "DISK"
    fill_data.size = .20
    fill = bpy.data.objects.new("R30_Ledge_Fill", fill_data)
    studio.objects.link(fill)
    fill.location = (.18, -.10, .07)
    fill.rotation_euler = (Vector((0, 0, 0)) - fill.location).to_track_quat(
        "-Z", "Y").to_euler()
    hero = camera("Camera_R30_Assembled", (.105, -.22, .085),
                  (0, .003, .008), .158, studio)
    side = camera("Camera_R30_Mount_Side", (-.20, 0, .015),
                  (0, .002, 0), .12, studio)
    detail = camera("Camera_R30_Ledge_Detail", (-.20, 0, .012),
                    (0, .002, -.006), .060, studio)
    scene.camera = side
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(PRESENTATION))
    render(scene, hero, "r30-assembled-preview.png")
    render(scene, side, "r30-side-profile.png")
    render(scene, detail, "r30-ledge-detail.png")


if __name__ == "__main__":
    main()
