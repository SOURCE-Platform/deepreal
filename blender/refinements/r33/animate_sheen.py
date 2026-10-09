#!/usr/bin/env python3
"""Sweep a soft strip light across the pressed logo without changing the model."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
PREVIEW = "--preview" in sys.argv
SETUP_ONLY = "--setup-only" in sys.argv
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 64
scene.render.resolution_x = 1440
scene.render.resolution_y = 840
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.frame_start = 1
scene.frame_end = 72
scene.render.fps = 24
scene.camera = bpy.data.objects["Camera_Tall_Plate_And_Logo"]
scene.camera.data.clip_start = .001

steel = bpy.data.materials["Pressed_Satin_Ferritic_Steel"]
steel.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .27

for obj in bpy.data.objects:
    if obj.type == "LIGHT":
        obj.data.energy *= .35

data = bpy.data.lights.new("Animated_Satin_Sheen", "AREA")
data.shape = "RECTANGLE"
data.size = .014
data.size_y = .05
data.energy = 2.8
data.color = (1.0, .96, .9)
light = bpy.data.objects.new("Animated_Satin_Sheen", data)
scene.collection.objects.link(light)
target = Vector((0, .0022, -.014))

for frame, x in ((1, -.145), (36, 0), (72, .145)):
    light.location = (x, .055, .018)
    light.rotation_euler = (target - light.location).to_track_quat(
        "-Z", "Y").to_euler()
    light.keyframe_insert(data_path="location", frame=frame)
    light.keyframe_insert(data_path="rotation_euler", frame=frame)

if SETUP_ONLY:
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    path = HERE / "deepreal-creased-logo-light-sweep-r33.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print("R33 ANIMATED BLEND", path)
elif PREVIEW:
    scene.render.image_settings.file_format = "PNG"
    for frame in (1, 36, 72):
        scene.frame_set(frame)
        scene.render.filepath = str(HERE / f"sheen-preview-{frame:02d}.png")
        bpy.ops.render.render(write_still=True)
        print("R33 PREVIEW", scene.render.filepath)
else:
    frames = HERE / "sheen-frames"
    frames.mkdir(exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(frames / "frame-")
    bpy.ops.render.render(animation=True)
    print("R33 FRAMES", frames)
