#!/usr/bin/env python3
"""Render front and side checks of the enclosed R17 drum modules."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-exterior-refinement-r17.blend"
OUT = HERE / "renders"


def view(name, location, target, scale, collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = .001
    cam = bpy.data.objects.new(name, data)
    collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    return cam


def save(scene, camera, name):
    scene.camera = camera
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    print("R17 RENDER", scene.render.filepath)


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
    save(scene, front, "r17-front-enclosed.png")
    for side, sign in (("face", -1), ("interaction", 1)):
        cam = view("Camera_R17_" + side + "_side",
                   (sign * .18, -.035, .022),
                   (sign * .055, -.0015, .020), .075, studio)
        save(scene, cam, "r17-" + side + "-side-enclosed.png")
    bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"].hide_render = True
    cam = view("Camera_R17_Internal_Module_Review",
               (.095, .080, .075), (.048, .001, .020), .075, studio)
    save(scene, cam, "r17-internal-module.png")
    # Diagnostic access view: the saved assembly remains closed.
    for name in ("Face_Smooth_Outer_End_Cap_R17",
                 "Face_Fixed_End_Chamber_Sleeve_R17"):
        bpy.data.objects[name].hide_render = True
    cam = view("Camera_R17_Face_Access_Review",
               (-.092, -.055, .045), (-.054, -.0015, .020), .055, studio)
    save(scene, cam, "r17-face-access-review.png")


if __name__ == "__main__":
    main()
