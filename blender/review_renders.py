#!/usr/bin/env python3
"""Render the single Blender-authoritative design for review and web use.

Run after build_scene.py:
    Blender --background blender/deepreal.blend --python blender/review_renders.py
"""

import os

import bpy
from mathutils import Vector


HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "renders")


def _aim(camera, target):
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def _camera(name, local_eye_mm, local_target_mm, orthographic=False,
            ortho_mm=150.0):
    pivot = bpy.data.objects["Lid_Pivot"]
    rotation = pivot.matrix_world.to_quaternion()
    origin = bpy.data.objects["Device_Target"].matrix_world.translation
    eye = origin + rotation @ Vector(tuple(v * 0.001 for v in local_eye_mm))
    target = origin + rotation @ Vector(
        tuple(v * 0.001 for v in local_target_mm))
    data = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    data.type = 'ORTHO' if orthographic else 'PERSP'
    data.lens = 58
    data.ortho_scale = ortho_mm * 0.001
    camera = bpy.data.objects.get(name)
    if camera is None:
        camera = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(camera)
    camera.location = eye
    _aim(camera, target)
    return camera


def _hide_collection(name, hidden=True):
    collection = bpy.data.collections.get(name)
    if collection:
        for obj in list(collection.objects):
            obj.hide_render = hidden


def _show_product_only():
    for name in ("MacBook Lid", "MacBook Deck", "Mounting (provisional)",
                 "USB Port (provisional)"):
        _hide_collection(name, True)


def _hide_shells(hidden=True):
    for name in ("Main_Housing", "Face_Sensor_Head",
                 "Interaction_Sensor_Head"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = hidden


def _render(name, camera):
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.filepath = os.path.join(OUTPUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("review render:", scene.render.filepath)


def main():
    os.makedirs(OUTPUT, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    # Technical views use the product coordinate frame directly. The laptop
    # pose belongs in the hero render, not in mechanical review imagery.
    bpy.data.objects["Lid_Pivot"].rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    _show_product_only()

    _render("reference-exterior", _camera(
        "Camera_Reference_Exterior", (160.0, -150.0, 50.0),
        (0.0, 6.0, 2.0)))
    _render("reference-profile", _camera(
        "Camera_Reference_Profile", (220.0, 0.0, 4.0),
        (0.0, 4.0, 2.0), orthographic=True, ortho_mm=84.0))

    _hide_shells(True)
    _hide_collection("Drum Optics", True)
    _render("reference-internal-assembly", _camera(
        "Camera_Reference_Assembly", (145.0, -175.0, 45.0),
        (0.0, 7.0, 0.0)))
    _render("reference-electronics-shield", _camera(
        "Camera_Reference_Shield", (105.0, -135.0, -5.0),
        (0.0, 15.0, -11.0)))


if __name__ == "__main__":
    main()
