#!/usr/bin/env python3
"""Render exterior and mechanism review angles for the R21 drum concept."""

from pathlib import Path
from math import radians

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-side-supported-drums-r21.blend"
OUT = HERE / "renders"


def make_camera(name, location, target, scale, collection):
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


def render(scene, camera, name):
    scene.camera = camera
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    print("R21 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= .16
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    render(scene, bpy.data.objects["Camera_R21_Exterior_Review"],
           "r21-exterior-three-quarter.png")
    front = make_camera("Camera_R21_Front", (0, -.24, .025),
                        (0, .004, .002), .15, studio)
    render(scene, front, "r21-exterior-front.png")
    high = make_camera("Camera_R21_High", (.035, -.15, .17),
                       (0, .002, .016), .14, studio)
    render(scene, high, "r21-exterior-above.png")
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    for name, face_angle, interaction_angle in (
            ("r21-sweep-high.png", -45, 0),
            ("r21-sweep-middle.png", 0, 22.5),
            ("r21-sweep-low.png", 45, 45)):
        face.rotation_euler.x = radians(face_angle)
        interaction.rotation_euler.x = radians(interaction_angle - 45)
        bpy.context.view_layer.update()
        render(scene, high, name)
    face.rotation_euler.x = 0
    interaction.rotation_euler.x = 0
    bpy.context.view_layer.update()

    # Inspection view only: expose the stationary motor support and optics.
    for side in ("Face", "Interaction"):
        for suffix in ("Sensor_Head", "Rear_Access_Cover_REMOVABLE_CONCEPT",
                       "Flat_Outer_End_R21", "Open_Inner_End_Ring_R21"):
            obj = bpy.data.objects.get(side + "_" + suffix)
            if obj:
                obj.hide_render = True
    for name in ("07A — FACE ROTATING DRUM + OPTICS — CONCEPT",
                 "07B — INTERACTION ROTATING DRUM + OPTICS — CONCEPT",
                 "01A — EXTERIOR OPTICS — CONCEPT"):
        bpy.data.collections[name].hide_render = True
    for side in ("Face", "Interaction"):
        for suffix in ("RGB_Wide_Lens_6p95mm_ENVELOPE_R20",
                       "RGB_Wide_Assembly_10p8mm_ENVELOPE_R20"):
            obj = bpy.data.objects.get(side + "_" + suffix)
            if obj:
                obj.hide_render = True
    bpy.data.objects["R21_Lower_Housing_And_Rear_Spine"].hide_render = True
    rear = make_camera("Camera_R21_Mechanism_Review",
                       (.095, .14, .087), (0, .002, .013), .15, studio)
    render(scene, rear, "r21-mechanism-inspection.png")
    bpy.data.objects["R21_Center_Gap_Fairing"].hide_render = True
    detail = make_camera("Camera_R21_Drive_Detail",
                         (.045, -.10, .095), (0, .004, .020), .085, studio)
    render(scene, detail, "r21-drive-detail.png")


if __name__ == "__main__":
    main()
