#!/usr/bin/env python3
"""Show all three enclosure dividers with and without the drums."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
from render_r24 import camera  # noqa: E402

MODEL = HERE / "deepreal-circular-divider-enclosure-r29.blend"
PRESENTATION = HERE / "deepreal-circular-divider-review-r29.blend"
SHELL = "R29_One_Piece_Enclosure"


def render(scene, view, filename):
    scene.camera = view
    scene.render.filepath = str(HERE / filename)
    bpy.ops.render.render(write_still=True)
    print("R29 RENDER", scene.render.filepath)


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
    fill_data = bpy.data.lights.new("R29_Front_Fill", "AREA")
    fill_data.energy = 1.2
    fill_data.shape = "DISK"
    fill_data.size = .20
    fill = bpy.data.objects.new("R29_Front_Fill", fill_data)
    studio.objects.link(fill)
    fill.location = (0, -.16, .055)
    fill.rotation_euler = (Vector((0, 0, .014)) - fill.location).to_track_quat(
        "-Z", "Y").to_euler()
    hero = camera("Camera_R29_Assembled", (.105, -.22, .085),
                  (0, .003, .008), .158, studio)
    scene.camera = hero
    bpy.context.preferences.filepaths.save_version = 0
    render(scene, hero, "r29-assembled-preview.png")
    center_detail = camera("Camera_R29_Center_Detail", (.042, -.13, .047),
                           (0, -.0015, .020), .052, studio)
    render(scene, center_detail, "r29-center-divider-detail.png")
    right_detail = camera("Camera_R29_Right_Detail", (.16, -.12, .05),
                          (.058, -.0015, .020), .052, studio)
    render(scene, right_detail, "r29-right-side-detail.png")
    scene.camera = hero
    bpy.ops.wm.save_as_mainfile(filepath=str(PRESENTATION))
    front = camera("Camera_R29_Three_Dividers", (0, -.22, .09),
                   (0, .003, .011), .155, studio)
    render(scene, front, "r29-three-dividers-assembled.png")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            obj.hide_render = obj.name != SHELL
    render(scene, hero, "r29-connected-shell.png")
    render(scene, front, "r29-three-dividers-shell.png")
    low = camera("Camera_R29_Shell_Low", (.03, -.17, -.025),
                 (0, .004, .014), .138, studio)
    render(scene, low, "r29-connected-shell-low.png")


if __name__ == "__main__":
    main()
