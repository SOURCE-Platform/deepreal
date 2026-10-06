#!/usr/bin/env python3
"""Show the R16 access-cover position at rest and maximum down study."""

import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r16.blend"
OUT = HERE / "renders"


def camera(name, location, target, scale, collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = .001
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    collection.objects.link(obj)
    return obj


def save(scene, cam, name):
    scene.camera = cam
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    print("R16 REVIEW", scene.render.filepath)


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
    housing = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    covers = bpy.data.collections[
        "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS"]
    housing.hide_render = covers.hide_render = False
    save(scene, bpy.data.objects["Camera_R05_Front"],
         "r16-saved-front-covers-installed.png")
    covers.hide_render = True
    save(scene, bpy.data.objects["Camera_R05_Front"],
         "r16-saved-front-covers-removed.png")
    covers.hide_render = False

    housing.hide_render = True
    rear = camera("Camera_R16_Rest_Rear", (.10, .16, .065),
                  (0, .004, .009), .16, studio)
    save(scene, rear, "r16-saved-rear-covers-installed.png")
    covers.hide_render = True
    save(scene, rear, "r16-saved-rear-covers-removed.png")

    housing.hide_render = False
    bpy.data.collections[
        "07C — MOTOR + HEAD ROUTES — CONCEPT"].hide_render = True
    for side, rest in (("Face", 0), ("Interaction", 45)):
        bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"].rotation_euler.x = (
            math.radians(75 - rest))
    bpy.context.view_layer.update()
    high = camera("Camera_R16_Down_Stop_High_Front",
                  (.010, -.12, .115), (0, 0, .012), .145, studio)
    for installed in (False, True):
        covers.hide_render = not installed
        label = "installed" if installed else "removed"
        save(scene, high, "r16-down75-high-front-covers-%s.png" % label)


if __name__ == "__main__":
    main()
