#!/usr/bin/env python3
"""Build R06 from the preserved R05 review model."""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
R04_DIR = HERE.parent / "r04"
R05_DIR = HERE.parent / "r05"
for path in (REPO / "blender", R04_DIR, R05_DIR, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r04_geometry import frame_viewports  # noqa: E402
from r06_corrections import (  # noqa: E402
    add_verified_j2_j3_envelopes, create_housing_toggle,
    quarantine_unverified_bodies, recess_and_seat_usb_overmold, tag_scene)

SOURCE = R05_DIR / "deepreal-exterior-refinement-r05.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r06.blend"
RENDERS = HERE / "renders"


def render(scene, camera_name, filename):
    scene.camera = bpy.data.objects[camera_name]
    scene.render.filepath = str(RENDERS / filename)
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=True)


def set_collection(name, visible):
    bpy.data.collections[name].hide_render = not visible


def build():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    tag_scene()
    housing, housing_collection = create_housing_toggle()
    unresolved, _ = quarantine_unverified_bodies()
    add_verified_j2_j3_envelopes()
    recess_and_seat_usb_overmold(housing)

    electronics_name = "02 — STATIONARY ELECTRONICS — PROVISIONAL"
    thermal_name = "04 — BOUNDED THERMAL LINKS — PROVISIONAL"
    routes_name = "05 — POWER AND DATA ROUTES — PROVISIONAL"
    inspection_name = "06 — HOUSING WIREFRAME — HIDDEN INSPECTION"
    studio_name = "STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT"
    obstacles = [bpy.data.objects[name] for name in (
        "Thermal_Spreader", "Shield_Rear_Tray", "Shield_Front_Lid")]

    if "--render" in sys.argv:
        RENDERS.mkdir(parents=True, exist_ok=True)
        bpy.data.collections[studio_name].hide_render = False
        set_collection(electronics_name, False)
        set_collection(thermal_name, False)
        set_collection(routes_name, False)
        housing_collection.hide_render = False
        render(scene, "Camera_R05_Front", "r06-front.png")

        set_collection(electronics_name, True)
        set_collection(thermal_name, True)
        set_collection(routes_name, True)
        housing_collection.hide_render = True
        for obj in obstacles:
            obj.hide_render = True
        render(scene, "Camera_R05_Architecture", "r06-internal-routing.png")
        for obj in obstacles:
            obj.hide_render = False

        set_collection(electronics_name, False)
        set_collection(thermal_name, False)
        set_collection(routes_name, False)
        housing_collection.hide_render = False
        render(scene, "Camera_R05_USB_Cutaway", "r06-usb-seated.png")

    for name in (electronics_name, thermal_name, routes_name):
        set_collection(name, True)
    housing_collection.hide_viewport = housing_collection.hide_render = False
    unresolved.hide_viewport = unresolved.hide_render = True
    bpy.data.collections[inspection_name].hide_render = True
    bpy.data.collections[studio_name].hide_viewport = True
    bpy.data.collections[studio_name].hide_render = True
    housing.display_type = "SOLID"
    frame_viewports()
    scene.camera = bpy.data.objects["Camera_R05_Front"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R06 saved", OUTPUT)


if __name__ == "__main__":
    build()
