#!/usr/bin/env python3
"""Render both role-specific drum limits and their straight/center poses."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-role-specific-sweep-r19.blend"
OUT = HERE / "renders"


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


def save(scene, cam, filename):
    scene.camera = cam
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
    print("R19 RENDER", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 950
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"].hide_render = False
    front = bpy.data.objects["Camera_R05_Front"]
    pivots = {side: bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
              for side in ("Face", "Interaction")}
    poses = (("Face", 0, (("up45", -45), ("straight", 0),
                          ("down45", 45))),
             ("Interaction", 45, (("straight", 0), ("down45", 45),
                                  ("down90", 90))))
    for side, base, positions in poses:
        other = "Interaction" if side == "Face" else "Face"
        pivots[other].rotation_euler.x = 0
        for label, angle in positions:
            pivots[side].rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            save(scene, front, "r19-" + side.lower() + "-" + label +
                 "-front.png")
            if label in ("up45", "down45", "straight", "down90") and (
                    (side == "Face" and label != "straight") or
                    (side == "Interaction" and label != "down45")):
                sign = -1 if side == "Face" else 1
                high = angle > (0 if side == "Face" else 45)
                cam = camera("Camera_R19_" + side + "_" + label,
                             (sign * .075, -.135,
                              .105 if high else -.065),
                             (sign * .027, -.0015, .020), .105, studio)
                save(scene, cam, "r19-" + side.lower() + "-" + label +
                     "-oblique.png")
        pivots[side].rotation_euler.x = 0
    bpy.context.view_layer.update()


if __name__ == "__main__":
    main()
