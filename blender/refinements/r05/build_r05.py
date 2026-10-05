#!/usr/bin/env python3
"""Build the DeepReal R05 internal architecture review model."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLENDER_DIR = REPO / "blender"
R04_DIR = HERE.parent / "r04"
for path in (BLENDER_DIR, R04_DIR, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import design_spec  # noqa: E402
import device  # noqa: E402
import materials  # noqa: E402
import optics  # noqa: E402
import usb_port  # noqa: E402
from r04_geometry import (  # noqa: E402
    add_usb_plug_and_cable, close_drum_gap, frame_viewports, hollow_housing,
    refinement_manifest, usb_frame)
from r05_architecture import (  # noqa: E402
    add_head_routes, add_housing_inspection_copy, add_thermal_straps,
    add_usb_daughterboard, append_shifted_electronics, mark_legacy_j1,
    open_usb_service_path, remove_r04_thermal_parts)

SOURCE_BLEND = BLENDER_DIR / "deepreal.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r05.blend"
FRONT_RENDER = HERE / "renders" / "r05-front.png"
ARCH_RENDER = HERE / "renders" / "r05-power-data-architecture.png"
USB_RENDER = HERE / "renders" / "r05-usb-cutaway.png"


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
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("R05 Review World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.012, 0.016, 0.024, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.28
    scene.world = world


def keep_exterior_optics(target):
    for obj in list(target.objects):
        visible = (obj.type == "MESH" and "_Lens_" in obj.name
                   and "Cutter" not in obj.name)
        if not visible:
            bpy.data.objects.remove(obj, do_unlink=True)


def show(target, visible):
    target.hide_render = not visible


def render(scene, camera_obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.camera = camera_obj
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R05"
    scene.unit_settings.system = "METRIC"
    configure_scene(scene)
    scene["DeepReal_Status"] = "R05 architecture review; no engineering approval"
    scene["DeepReal_Architecture"] = (
        "center USB daughterboard -> controlled-impedance flex -> main PCB -> J2/J3 head flexes")

    mats = materials.build_all()
    manifest = refinement_manifest(design_spec.manifest())
    exterior = collection("01 — R05 SOLID EXTERIOR")
    original_hollow = device._hollow_housing
    device._hollow_housing = lambda obj: hollow_housing(obj, manifest)
    try:
        product = device.build(manifest, mats, exterior)
    finally:
        device._hollow_housing = original_hollow
    housing = bpy.data.objects["Main_Housing"]
    housing.display_type = "SOLID"

    optics_collection = collection("01A — EXTERIOR OPTICS — CONCEPT")
    optics.apply_to_product(manifest, mats, optics_collection)
    keep_exterior_optics(optics_collection)
    close_drum_gap(exterior, optics_collection)

    electronics = append_shifted_electronics(
        SOURCE_BLEND, "02 — STATIONARY ELECTRONICS — PROVISIONAL")
    remove_r04_thermal_parts()
    spreader, tray, lid = open_usb_service_path()
    for obj in (spreader, tray, lid):
        obj["DeepReal_Status"] = "R05 centered USB service opening; unvalidated"
    keepout = bpy.data.objects.get("Main_PCBA_Populated_Keepout")
    if keepout:
        keepout.hide_render = True
        keepout.display_type = "WIRE"
    mark_legacy_j1()

    usb_collection = collection("03 — CENTERED USB — PROVISIONAL")
    original_frame = usb_port.port_frame
    original_angle = usb_port.PORT_ANGLE_DEG
    usb_port.port_frame = usb_frame
    usb_port.PORT_ANGLE_DEG = 90.0
    try:
        usb_port.build(manifest, mats, usb_collection)
    finally:
        usb_port.port_frame = original_frame
        usb_port.PORT_ANGLE_DEG = original_angle
    add_usb_plug_and_cable(manifest, mats, usb_collection)

    thermal = collection("04 — BOUNDED THERMAL LINKS — PROVISIONAL")
    add_thermal_straps(thermal)
    routes = collection("05 — POWER AND DATA ROUTES — PROVISIONAL")
    _, _, _, flex_material = add_usb_daughterboard(routes)
    add_head_routes(routes, flex_material)
    routes["DeepReal_Status"] = (
        "architecture centerlines only; connectors, pinout, SI, and motion unverified")

    inspection = collection("06 — HOUSING WIREFRAME — HIDDEN INSPECTION")
    add_housing_inspection_copy(housing, inspection)
    inspection.hide_render = True

    studio = collection("STUDIO — R05 REVIEW CAMERAS — HIDDEN IN VIEWPORT")
    studio.hide_viewport = True
    front = camera("Camera_R05_Front", (0.0, -0.24, 0.0),
                   (0.0, 0.005, 0.0), 0.145, studio)
    architecture = camera("Camera_R05_Architecture", (0.145, -0.18, 0.055),
                          (0.0, 0.012, -0.008), 0.125, studio)
    usb_camera = camera("Camera_R05_USB_Cutaway", (0.0, -0.14, -0.023),
                        (0.0, 0.018, -0.023), 0.045, studio)
    area("Key", (0.16, -0.12, 0.16), (0, 0, 0), 20, 0.16, studio)
    area("Fill", (-0.12, -0.05, 0.08), (0, 0, 0), 8, 0.13, studio)
    area("Rim", (0.0, 0.14, 0.10), (0, 0, 0), 16, 0.10, studio)

    if "--render" in sys.argv:
        show(electronics, False)
        show(thermal, False)
        show(routes, False)
        render(scene, front, FRONT_RENDER)

        # Keep the drums visible so the two candidate head-flex paths have
        # readable physical endpoints.  Only the housing shell is hidden.
        show(exterior, True)
        show(optics_collection, True)
        show(electronics, True)
        show(thermal, True)
        show(routes, True)
        housing.hide_render = True
        for obstacle in (spreader, tray, lid):
            obstacle.hide_render = True
        render(scene, architecture, ARCH_RENDER)
        for obstacle in (spreader, tray, lid):
            obstacle.hide_render = False

        show(electronics, False)
        show(thermal, False)
        show(routes, False)
        render(scene, usb_camera, USB_RENDER)

    for target in bpy.data.collections:
        target.hide_render = target in (inspection, studio)
    for obj in bpy.data.objects:
        if obj.name.endswith("Cutter"):
            obj.hide_render = True
    housing.hide_render = False
    housing.display_type = "SOLID"
    frame_viewports()
    scene.camera = front
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R05 saved", OUTPUT)


if __name__ == "__main__":
    build()
