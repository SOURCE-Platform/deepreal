#!/usr/bin/env python3
"""Create exterior previews and website assets for the finished enclosure."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-finished-exterior-r24.blend"


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


def render(scene, view, name, transparent=False):
    scene.camera = view
    scene.render.film_transparent = transparent
    scene.render.filepath = str(HERE / name)
    bpy.ops.render.render(write_still=True)
    print("R24 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1125
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.eevee.taa_render_samples = 128
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= .08
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
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
    render(scene, hero, "r24-review-hero-dark.png")
    render(scene, hero, "r24-review-hero-transparent.png", True)
    front = camera("Camera_R24_Front", (0, -.24, .015),
                   (0, .003, .012), .143, studio)
    render(scene, front, "r24-front-preview.png")
    side = camera("Camera_R24_Side", (.24, 0, .003),
                  (0, 0, .003), .13, studio)
    render(scene, side, "r24-side-preview.png")
    high = camera("Camera_R24_High", (.035, -.15, .17),
                  (0, .002, .016), .14, studio)
    render(scene, high, "r24-above-preview.png")


if __name__ == "__main__":
    main()
