#!/usr/bin/env python3
"""R07 clearance geometry and viewport mode controls."""

import bpy
from mathutils import Matrix, Vector

import macbook

MM = 0.001


def collection(name):
    value = bpy.data.collections.get(name)
    if value is None:
        value = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(value)
    return value


def move_object(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def difference(target, cutter, label):
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    modifier = target.modifiers.new(label, "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    target.modifiers.move(len(target.modifiers) - 1, 0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    target.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def configure_housing_mode():
    solid = bpy.data.objects["Main_Housing"]
    solid_collection = bpy.data.collections[
        "00 — HOUSING SHELL — CLICK EYE OR CAMERA"]
    solid_collection.name = "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"
    wire = bpy.data.objects["Main_Housing_Inspection_Wireframe"]
    wire_collection = collection("00A — WIREFRAME FALLBACK — KEEP VISIBLE")
    move_object(wire, wire_collection)
    wire.display_type = "WIRE"
    wire.scale = (0.997, 0.997, 0.997)
    wire.hide_viewport = False
    wire.hide_render = True
    wire.hide_set(False)
    wire_collection.hide_viewport = False
    wire_collection.hide_render = True
    solid.display_type = "SOLID"
    solid.hide_viewport = solid.hide_render = False
    solid_collection["R07_Toggle"] = (
        "Eye on: solid hides inset wire; eye off: inset wire remains visible")
    return solid, wire, solid_collection, wire_collection


def reshape_daughterboard():
    old = bpy.data.objects["Centered_USB_Daughterboard"]
    owners = list(old.users_collection)
    material = old.data.materials[0]
    bpy.data.objects.remove(old, do_unlink=True)
    board = macbook.slab(
        "Centered_USB_Daughterboard", Vector((0.0, 14.5 * MM, -15.5 * MM)),
        macbook.X, macbook.Z, (16.0 * MM, 9.0 * MM), 0.6 * MM,
        1.0 * MM, material)
    owners[0].objects.link(board)
    board["DeepReal_Status"] = (
        "conditional USB daughterboard concept; exact connector and stackup unselected")
    board["R07_Clearance_mm"] = {
        "overmold_y": 0.5, "service_slot_x_each_side": 1.0,
        "service_slot_z_each_end": 1.0}
    flex = bpy.data.objects["USB3_PD_Internal_Flex_CONCEPT"]
    points = flex.data.splines[0].points
    points[0].co = (0.0, 15.0 * MM, -17.0 * MM, 1.0)
    points[1].co = (0.0, 14.0 * MM, -17.0 * MM, 1.0)
    return board


def _slot_cutter(name, width, low_z, high_z, depth):
    return macbook.slab(
        name, Vector((0.0, 11.0 * MM, (low_z + high_z) / 2 * MM)),
        macbook.X, macbook.Z, (width * MM, (high_z - low_z) * MM),
        1.0 * MM, depth * MM, None)


def enlarge_service_path():
    values = (("Thermal_Spreader", 12.0), ("Shield_Rear_Tray", 18.0),
              ("Shield_Front_Lid", 12.0))
    for name, depth in values:
        obj = bpy.data.objects[name]
        cutter = _slot_cutter("_R07_" + name + "_Clearance", 18.0,
                              -25.0, -10.0, depth)
        bpy.context.scene.collection.objects.link(cutter)
        difference(obj, cutter, "R07_Centered_USB_Clearance")
        obj["R07_Service_Slot_Width_mm"] = 18.0
        obj["R07_Service_Slot_Z_mm"] = [-25.0, -10.0]


def clear_housing_for_usb(housing, wire):
    housing.data = housing.data.copy()
    chute = macbook.prism(
        "_R07_USB_Overmold_Chute", macbook._rounded_rect_2d(
            9.4 * MM, 5.4 * MM, 2.3 * MM, seg=12),
        Vector((0.0, 18.0 * MM, -27.5 * MM)), macbook.X, macbook.Y,
        15.0 * MM, None)
    bpy.context.scene.collection.objects.link(chute)
    difference(housing, chute, "R07_USB_Overmold_Chute")

    pocket = macbook.slab(
        "_R07_Daughterboard_Pocket", Vector((0.0, 14.5 * MM, -15.5 * MM)),
        macbook.X, macbook.Z, (18.0 * MM, 11.0 * MM), 0.8 * MM,
        2.4 * MM, None)
    bpy.context.scene.collection.objects.link(pocket)
    difference(housing, pocket, "R07_Daughterboard_Clearance_Pocket")
    wire.data = housing.data
    housing["R07_USB_Chute_mm"] = [9.4, 5.4, 15.0]
    housing["R07_Daughterboard_Pocket_mm"] = [18.0, 2.4, 11.0]


def mark_conditional_thermal_path():
    target = bpy.data.collections["04 — BOUNDED THERMAL LINKS — PROVISIONAL"]
    target.name = "04 — SPLIT THERMAL PATH — UNVALIDATED OPTION"
    target["R07_Status"] = (
        "clearance workaround only; requires thermal and compression validation")
    for name in ("Housing_Thermal_Pad_Left", "Housing_Thermal_Pad_Right",
                 "Thermal_Link_Left", "Thermal_Link_Right"):
        bpy.data.objects[name]["R07_Status"] = (
            "not a best-practice claim; material, compression and heat path unverified")


def tag_scene():
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R07"
    scene["DeepReal_Status"] = "R07 packaging review; no engineering approval"
    scene["R07_USB_Daughterboard_Decision"] = (
        "conditional option; validate SI, PD, ESD, shield bond and service loads")
