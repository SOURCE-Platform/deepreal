#!/usr/bin/env python3
"""Build the DeepReal R04 review model inside the repository."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLENDER_DIR = REPO / "blender"
if str(BLENDER_DIR) not in sys.path:
    sys.path.insert(0, str(BLENDER_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import design_spec  # noqa: E402
import device  # noqa: E402
import materials  # noqa: E402
import optics  # noqa: E402
import usb_port  # noqa: E402
from r04_geometry import (  # noqa: E402
    add_thermal_interface, add_usb_plug_and_cable,
    append_and_shift_electronics, close_drum_gap, frame_viewports,
    hollow_housing, refinement_manifest, usb_frame)

SOURCE_BLEND = BLENDER_DIR / "deepreal.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r04.blend"
FRONT_RENDER = HERE / "renders" / "r04-front.png"
THERMAL_RENDER = HERE / "renders" / "r04-thermal-usb.png"
USB_RENDER = HERE / "renders" / "r04-usb-cutaway.png"


def collection(name):
    value = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(value)
    return value


def aim(obj, target):
    obj.rotation_euler = (
        Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, scale, target_collection):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    target_collection.objects.link(obj)
    aim(obj, target)
    return obj


def area(name, location, target, energy, size, target_collection):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    target_collection.objects.link(obj)
    aim(obj, target)


def configure_scene(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("R04 Review World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.012, 0.016, 0.024, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.28
    scene.world = world


def keep_exterior_optics(target_collection):
    for obj in list(target_collection.objects):
        visible = (obj.type == "MESH" and "_Lens_" in obj.name
                   and "Cutter" not in obj.name)
        if not visible:
            bpy.data.objects.remove(obj, do_unlink=True)


def set_collection_render(name, visible):
    target = bpy.data.collections.get(name)
    if target:
        target.hide_render = not visible


def set_product_render(product, visible):
    for obj in product:
        obj.hide_render = not visible


def render(scene, camera_obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.camera = camera_obj
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R04"
    scene.unit_settings.system = "METRIC"
    configure_scene(scene)
    scene["DeepReal_Status"] = "R04 review model; no engineering approval"
    scene["DeepReal_User_Direction"] = (
        "center USB; zero visible drum gap; inserted plug; split thermal path")

    mats = materials.build_all()
    manifest = refinement_manifest(design_spec.manifest())
    exterior = collection("01 — R04 EXTERIOR")
    baseline_hollow = device._hollow_housing
    device._hollow_housing = lambda obj: hollow_housing(obj, manifest)
    try:
        product = device.build(manifest, mats, exterior)
    finally:
        device._hollow_housing = baseline_hollow
    housing = bpy.data.objects["Main_Housing"]
    housing.display_type = "WIRE"

    optics_collection = collection("01A — EXTERIOR OPTICS — CONCEPT")
    optics.apply_to_product(manifest, mats, optics_collection)
    keep_exterior_optics(optics_collection)

    electronics_placeholder = collection("02 — STATIONARY ELECTRONICS — PROVISIONAL")
    electronics = append_and_shift_electronics(
        SOURCE_BLEND, electronics_placeholder)
    keepout = bpy.data.objects.get("Main_PCBA_Populated_Keepout")
    if keepout:
        keepout.display_type = "WIRE"
        keepout.hide_render = False

    usb_collection = collection("03 — CENTERED USB — PROVISIONAL")
    baseline_frame = usb_port.port_frame
    baseline_angle = usb_port.PORT_ANGLE_DEG
    usb_port.port_frame = usb_frame
    usb_port.PORT_ANGLE_DEG = 90.0
    try:
        usb_port.build(manifest, mats, usb_collection)
    finally:
        usb_port.port_frame = baseline_frame
        usb_port.PORT_ANGLE_DEG = baseline_angle
    add_usb_plug_and_cable(manifest, mats, usb_collection)

    thermal = collection("04 — SPLIT THERMAL INTERFACE — PROVISIONAL")
    add_thermal_interface(thermal, mats)
    moved = close_drum_gap(exterior, optics_collection)
    scene["R04_Drum_Objects_Shifted"] = len(moved)

    unresolved = collection("05 — UNRESOLVED HEAD ELECTRONICS — NO GEOMETRY")
    unresolved["DeepReal_Status"] = (
        "complete local head electronics and motion hardware remain unresolved")

    studio = collection("STUDIO — R04 REVIEW CAMERAS — HIDDEN IN VIEWPORT")
    studio.hide_viewport = True
    front = camera("Camera_R04_Front", (0.0, -0.24, 0.0),
                   (0.0, 0.005, 0.0), 0.145, studio)
    thermal_camera = camera(
        "Camera_R04_Thermal_USB", (0.0, 0.018, 0.12),
        (0.0, 0.018, -0.0115), 0.095, studio)
    usb_camera = camera(
        "Camera_R04_USB_Cutaway", (0.0, -0.14, -0.023),
        (0.0, 0.018, -0.023), 0.045, studio)
    area("Key", (0.16, -0.12, 0.16), (0, 0, 0), 20, 0.16, studio)
    area("Fill", (-0.12, -0.05, 0.08), (0, 0, 0), 8, 0.13, studio)
    area("Rim", (0.0, 0.14, 0.10), (0, 0, 0), 16, 0.10, studio)

    if "--render" in sys.argv:
        set_collection_render(electronics.name, False)
        set_collection_render(thermal.name, False)
        render(scene, front, FRONT_RENDER)

        set_collection_render(exterior.name, False)
        set_collection_render(optics_collection.name, False)
        set_collection_render(electronics.name, True)
        set_collection_render(thermal.name, True)
        for obj in electronics.all_objects:
            obj.hide_render = obj.name != "Thermal_Spreader"
        render(scene, thermal_camera, THERMAL_RENDER)

        set_collection_render(electronics.name, False)
        set_collection_render(thermal.name, False)
        render(scene, usb_camera, USB_RENDER)

    for target in bpy.data.collections:
        target.hide_render = False
    for obj in bpy.data.objects:
        obj.hide_render = obj.name.endswith("Cutter")
    housing.hide_render = False
    frame_viewports()
    scene.camera = front
    scene["DeepReal_Default_Viewport"] = (
        "front perspective; 0.19 m orbit distance; product fills wide viewport")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R04 saved", OUTPUT)


if __name__ == "__main__":
    build()
