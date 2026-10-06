#!/usr/bin/env python3
"""Render both drums at the down stop from beneath the sensor opening."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r15.blend"
OUT = HERE / "renders"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    studio = bpy.data.collections[
        "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    studio.hide_render = False
    bpy.data.collections[
        "00A — WIREFRAME FALLBACK — KEEP VISIBLE"].hide_render = True
    bpy.data.collections[
        "07C — MOTOR + HEAD ROUTES — CONCEPT"].hide_render = True
    covers = bpy.data.collections[
        "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS"]
    for side, rest in (("Face", 0), ("Interaction", 45)):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        pivot.rotation_euler.x = math.radians(75 - rest)
    bpy.context.view_layer.update()

    data = bpy.data.cameras.new("Camera_R15_Down_Stop_From_Below")
    data.type = "ORTHO"
    data.ortho_scale = .145
    data.clip_start = .001
    camera = bpy.data.objects.new(data.name, data)
    camera.location = (.012, -.115, -.060)
    camera.rotation_euler = (Vector((0, 0, .020)) -
                             camera.location).to_track_quat("-Z", "Y").to_euler()
    studio.objects.link(camera)
    scene.camera = camera
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for installed in (False, True):
        covers.hide_render = not installed
        label = "installed" if installed else "removed"
        scene.render.filepath = str(
            OUT / ("r15-down75-from-below-covers-%s.png" % label))
        bpy.ops.render.render(write_still=True)
        print("R15 UNDERSIDE", scene.render.filepath)


if __name__ == "__main__":
    main()
