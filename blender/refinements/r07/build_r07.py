#!/usr/bin/env python3
"""Build R07 from the preserved R06 enclosure review model."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
R04 = HERE.parent / "r04"
for path in (REPO / "blender", R04, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r04_geometry import frame_viewports  # noqa: E402
from r07_geometry import (  # noqa: E402
    clear_housing_for_usb, configure_housing_mode, enlarge_service_path,
    mark_conditional_thermal_path, reshape_daughterboard, tag_scene)

SOURCE = HERE.parent / "r06" / "deepreal-exterior-refinement-r06.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r07.blend"
RENDERS = HERE / "renders"


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()


def clearance_camera(studio):
    data = bpy.data.cameras.new("Camera_R07_USB_Clearance")
    data.type = "ORTHO"
    data.ortho_scale = 0.040
    obj = bpy.data.objects.new("Camera_R07_USB_Clearance", data)
    obj.location = (0.0, -0.100, -0.017)
    studio.objects.link(obj)
    aim(obj, (0.0, 0.015, -0.017))
    return obj


def render(scene, camera, filename):
    scene.camera = camera
    scene.render.filepath = str(RENDERS / filename)
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=True)


def build():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    tag_scene()
    housing, wire, solid_collection, wire_collection = configure_housing_mode()
    reshape_daughterboard()
    enlarge_service_path()
    clear_housing_for_usb(housing, wire)
    mark_conditional_thermal_path()

    electronics = bpy.data.collections["02 — STATIONARY ELECTRONICS — PROVISIONAL"]
    thermal = bpy.data.collections["04 — SPLIT THERMAL PATH — UNVALIDATED OPTION"]
    routes = bpy.data.collections["05 — POWER AND DATA ROUTES — PROVISIONAL"]
    studio = bpy.data.collections["STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"]
    obstacles = [bpy.data.objects[name] for name in (
        "Thermal_Spreader", "Shield_Rear_Tray", "Shield_Front_Lid")]
    camera = clearance_camera(studio)

    if "--render" in sys.argv:
        RENDERS.mkdir(parents=True, exist_ok=True)
        studio.hide_render = False
        wire_collection.hide_render = True
        solid_collection.hide_render = True
        electronics.hide_render = False
        saved_visibility = {obj: obj.hide_render for obj in electronics.all_objects}
        allowed = {"Thermal_Spreader", "Shield_Rear_Tray", "Shield_Front_Lid"}
        for obj in electronics.all_objects:
            obj.hide_render = obj.name not in allowed
        thermal.hide_render = True
        routes.hide_render = False
        render(scene, camera, "r07-usb-clearance.png")
        for obj, hidden in saved_visibility.items():
            obj.hide_render = hidden

        solid_collection.hide_render = False
        electronics.hide_render = True
        thermal.hide_render = True
        routes.hide_render = True
        render(scene, bpy.data.objects["Camera_R05_USB_Cutaway"],
               "r07-usb-seated.png")

    solid_collection.hide_viewport = solid_collection.hide_render = False
    wire_collection.hide_viewport = False
    wire_collection.hide_render = True
    studio.hide_viewport = studio.hide_render = True
    for target in (electronics, thermal, routes):
        target.hide_render = False
    for obj in obstacles:
        obj.hide_render = False
    housing.display_type = "SOLID"
    wire.display_type = "WIRE"
    frame_viewports()
    scene.camera = bpy.data.objects["Camera_R05_Front"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R07 saved", OUTPUT)


if __name__ == "__main__":
    build()
