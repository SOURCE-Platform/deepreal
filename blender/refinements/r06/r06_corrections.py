#!/usr/bin/env python3
"""Focused R06 packaging corrections applied to the R05 review model."""

import bpy
from mathutils import Vector

import macbook

MM = 0.001
HIROSE_URL = "https://www.hirose.com/product/p/CL0580-2415-6-97"
USB_SURFACE_Z_MM = -22.278


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


def create_housing_toggle():
    housing = bpy.data.objects["Main_Housing"]
    # R05's optional wireframe copy shares this mesh.  R06 needs an isolated
    # mesh datablock before applying the local USB recess Boolean.
    housing.data = housing.data.copy()
    target = collection("00 — HOUSING SHELL — CLICK EYE OR CAMERA")
    move_object(housing, target)
    housing.display_type = "SOLID"
    housing.hide_viewport = housing.hide_render = False
    target["R06_User_Control"] = (
        "Eye hides shell in viewport; camera icon excludes shell from render")
    return housing, target


def quarantine_unverified_bodies():
    target = collection("98 — UNVERIFIED PCB BODY EVIDENCE — HIDDEN")
    renames = {
        "PCBA_Native_Surface_00": "SOURCE_UNVERIFIED_PCBA_NATIVE_SURFACE_BAKED",
        "Face_Optical_Head_Connector": "SOURCE_UNVERIFIED_J2_WRONG_ORIENTATION",
        "Interaction_Optical_Head_Connector": "SOURCE_UNVERIFIED_J3_WRONG_ORIENTATION",
        "Face_Motor_Encoder": "SOURCE_UNVERIFIED_J4_NO_EXACT_PART",
        "Interaction_Motor_Encoder": "SOURCE_UNVERIFIED_J5_NO_EXACT_PART",
    }
    moved = []
    for old_name, new_name in renames.items():
        obj = bpy.data.objects[old_name]
        obj.name = new_name
        obj.hide_viewport = obj.hide_render = False
        move_object(obj, target)
        moved.append(new_name)
    target.hide_viewport = True
    target.hide_render = True
    target["R06_Status"] = (
        "Preserved evidence only; enable explicitly to inspect invalid or unresolved bodies")
    return target, moved


def add_verified_j2_j3_envelopes():
    target = bpy.data.collections["02 — STATIONARY ELECTRONICS — PROVISIONAL"]
    material = bpy.data.materials["R05_Connector_Dark"]
    proxies = []
    for ref, label, x in (("J2", "Face", -22.0),
                          ("J3", "Interaction", 22.0)):
        proxy = macbook.slab(
            f"{ref}_{label}_Optical_Head_Connector_ENVELOPE",
            Vector((x * MM, 10.095 * MM, -23.5 * MM)),
            macbook.X, macbook.Z, (16.8 * MM, 3.2 * MM), 0.4 * MM,
            1.0 * MM, material)
        target.objects.link(proxy)
        proxy["PCBA_Ref"] = ref
        proxy["Exact_Part"] = "FH26W-51S-0.3SHW(97)"
        proxy["Envelope_mm"] = [16.8, 3.2, 1.0]
        proxy["Envelope_Source"] = HIROSE_URL
        proxy["R06_Status"] = (
            "manufacturer-dimensioned envelope proxy; not imported STEP geometry")
        proxies.append(proxy)
    return proxies


def recess_and_seat_usb_overmold(housing):
    overmold = bpy.data.objects["USB_C_Plug_Overmold"]
    cable = bpy.data.objects["USB_C_Cable"]
    insertion_shift = 1.2 * MM
    overmold.location.z += insertion_shift
    cable.location.z += insertion_shift
    overmold["R06_Axial_Insertion_mm"] = 1.0
    overmold["R06_Recess_Clearance_Each_Side_mm"] = 0.2

    outline = macbook._rounded_rect_2d(
        9.4 * MM, 5.4 * MM, 2.3 * MM, seg=12)
    cutter = macbook.prism(
        "_R06_USB_Overmold_Recess_Cutter", outline,
        Vector((0.0, 18.0 * MM, -21.85 * MM)), macbook.X, macbook.Y,
        2.2 * MM, None)
    bpy.context.scene.collection.objects.link(cutter)
    bpy.context.view_layer.objects.active = housing
    housing.select_set(True)
    modifier = housing.modifiers.new("R06_USB_Overmold_Recess", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    housing.modifiers.move(len(housing.modifiers) - 1, 0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    housing.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)
    wire = bpy.data.objects.get("Main_Housing_Inspection_Wireframe")
    if wire:
        wire.data = housing.data
    housing["R06_USB_Overmold_Recess_mm"] = [9.4, 5.4, 2.2]
    housing["R06_USB_Surface_Z_mm"] = USB_SURFACE_Z_MM
    return overmold, cable


def tag_scene():
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R06"
    scene["DeepReal_Status"] = "R06 packaging review; no engineering approval"
    scene["R06_J2_J3_Source"] = HIROSE_URL
    scene["R06_J4_J5_Blocker"] = (
        "Exact manufacturer parts absent; physical bodies intentionally not guessed")
