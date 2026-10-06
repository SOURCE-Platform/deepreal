#!/usr/bin/env python3
"""Render rear access exposure at the proposed 150-degree end stops."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r15.blend"
OUT = HERE / "renders"


def camera(collection):
    data = bpy.data.cameras.new("R15_Travel_Top_Front")
    data.type = "ORTHO"
    data.ortho_scale = 0.145
    obj = bpy.data.objects.new(data.name, data)
    obj.location = (0.010, -0.12, 0.115)
    obj.rotation_euler = (Vector((0, 0.0, 0.012)) - obj.location
                          ).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(obj)
    return obj


def pose(side, target_deg):
    base = 0 if side == "Face" else 45
    pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
    pivot.rotation_euler.x = math.radians(target_deg - base)


def render(scene, name):
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    print("R15 SWEEP", scene.render.filepath)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    bpy.data.collections[
        "07C — MOTOR + HEAD ROUTES — CONCEPT"].hide_render = True
    covers = bpy.data.collections[
        "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS"]
    scene.camera = camera(studio)
    for target in (-75, 75):
        for side in ("Face", "Interaction"):
            pose(side, target)
        bpy.context.view_layer.update()
        covers.hide_render = False
        render(scene, "r15-%s75-covers-closed.png" %
               ("up" if target < 0 else "down"))
        covers.hide_render = True
        render(scene, "r15-%s75-covers-removed.png" %
               ("up" if target < 0 else "down"))


if __name__ == "__main__":
    main()
