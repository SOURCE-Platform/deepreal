#!/usr/bin/env python3
"""Render assembled and service-access views of the R15 study."""

from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BLEND = HERE / "deepreal-exterior-refinement-r15.blend"
OUT = HERE / "renders"


def camera(name, position, target, scale, collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = 0.001
    obj = bpy.data.objects.new(name, data)
    obj.location = position
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()
    collection.objects.link(obj)
    return obj


def save(scene, cam, name):
    scene.camera = cam
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    print("R15 RENDER", scene.render.filepath)


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
    shells = bpy.data.collections[
        "01 — DRUM SHELLS — CLICK EYE FOR INTERNALS"]
    covers = bpy.data.collections[
        "01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS"]
    housing.hide_render = shells.hide_render = covers.hide_render = False
    save(scene, bpy.data.objects["Camera_R05_Front"],
         "r15-assembled-front.png")
    side = camera("Camera_R15_End", (0.16, -0.04, 0.08),
                  (0.044, 0.0, 0.010), 0.105, studio)
    save(scene, side, "r15-flat-end-face.png")

    housing.hide_render = True
    rear = camera("Camera_R15_Rear", (0.10, 0.16, 0.065),
                  (0.0, 0.004, 0.009), 0.16, studio)
    save(scene, rear, "r15-rear-covers-closed.png")
    covers.hide_render = True
    save(scene, rear, "r15-rear-access-open.png")
    shells.hide_render = True
    interior = camera("Camera_R15_Internal", (0, 0.15, 0.077),
                      (0, 0.005, 0.008), 0.15, studio)
    save(scene, interior, "r15-internal-drive-layout.png")


if __name__ == "__main__":
    main()
