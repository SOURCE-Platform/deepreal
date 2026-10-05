"""R09 packaging proposal: right-hand board tab and direct USB-C entry.

This modifies only a copied Blender scene. The KiCad board and connector
footprint are unchanged; the socket remains an unselected envelope.
"""

import bmesh
import bpy
from mathutils import Vector

import macbook
from r07_geometry import difference
from r08_geometry import restore_meshes

MM = 0.001
PORT_X = 51.5 * MM
PORT_Y_SHIFT = -3.85 * MM


def _forget(names):
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def remove_centered_study():
    _forget((
        "Centered_USB_Daughterboard", "USB_Power_Data_Side_Route_CONCEPT",
        "Mainboard_USB_Flex_Connector_CONCEPT", "Main_Housing_USB_Back",
        "Main_Housing_USB_Cutter", "Main_Housing_USB_Shell",
        "Main_Housing_USB_Tongue"))
    old = bpy.data.objects["USB_C_Receptacle_J1_LEGACY_LOCATION"]
    old.name = "J1_SOURCE_BOARD_POSITION_HIDDEN_REFERENCE"
    old.hide_set(True)
    old.hide_render = True
    old["R09_Status"] = (
        "native board position retained for reference only; KiCad J1 is not moved")


def add_board_tab():
    substrate = bpy.data.materials["R05_USB_Daughterboard_Green"]
    tab = macbook.slab(
        "Main_PCBA_Right_USB_Tab_GEOMETRY_PROPOSAL",
        Vector((51.05 * MM, 11.35 * MM, -16.25 * MM)), macbook.X, macbook.Z,
        (12.9 * MM, 12.5 * MM), 0.8 * MM, 1.49 * MM, substrate)
    bpy.data.collections["02 — STATIONARY ELECTRONICS — PROVISIONAL"].objects.link(tab)
    tab["R09_Status"] = (
        "board-outline and connector-mount study only; no native PCB outline, "
        "pads, copper, or component placement changed")
    tab["R09_Nominal_Envelope_mm"] = [44.6, 57.5, 10.605, 12.095, -22.5, -10.0]
    return tab


def open_shield_side(uncut):
    restore_meshes(uncut, ("Shield_Rear_Tray",))
    tray = bpy.data.objects["Shield_Rear_Tray"]
    for key in list(tray.keys()):
        if key.startswith("R08_"):
            del tray[key]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(45.0 * MM, 11.35 * MM,
                                                      -16.25 * MM))
    cutter = bpy.context.object
    cutter.name = "_R09_Board_Tab_Shield_Clearance"
    cutter.dimensions = (3.2 * MM, 3.2 * MM, 14.0 * MM)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    difference(tray, cutter, "R09_Right_Tab_Feedthrough")
    # The imported tray has an open edge, so Blender's boolean leaves its
    # inner side-wall skin across the cut. Remove only that split skin.
    world = tray.matrix_world
    indices = [poly.index for poly in tray.data.polygons
               if 44.5 < (world @ poly.center).x / MM < 46.01
               and 9.7 < (world @ poly.center).y / MM < 13.0
               and -23.3 < (world @ poly.center).z / MM < -9.2]
    mesh = bmesh.new()
    mesh.from_mesh(tray.data)
    mesh.faces.ensure_lookup_table()
    bmesh.ops.delete(mesh, geom=[mesh.faces[i] for i in indices], context="FACES")
    mesh.to_mesh(tray.data)
    mesh.free()
    tray["R09_Removed_Side_Wall_Faces"] = len(indices)
    tray["R09_Status"] = (
        "local side opening for proposed board tab; EMI bond and aperture "
        "clearance require design review")


def move_socket_and_plug():
    socket = bpy.data.objects[
        "USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED"]
    socket.name = "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED"
    target = bpy.data.collections["05 — USB POWER + DATA PATH — DIAGRAM ONLY"]
    target.name = "05 — RIGHT BOARD-MOUNT USB — GEOMETRY ONLY"
    for name in (
            socket.name, "USB_C_Plug_Overmold", "USB_C_Male_Metal_Shell",
            "USB_C_Male_Internal_Insert", "USB_C_Male_Contact_Tongue",
            "USB_C_Cable"):
        obj = bpy.data.objects[name]
        obj.location.x += PORT_X
        obj.location.y += PORT_Y_SHIFT
        obj["R09_Status"] = (
            "right-side packaging envelope; connector and cable are not "
            "manufacturer-verified parts")
    socket["R09_Mounting"] = (
        "envelope touches visual PCB tab; solder pads and retention unverified")
    for name in ("USB_C_Plug_Overmold", "USB_C_Male_Metal_Shell",
                 "USB_C_Male_Internal_Insert", "USB_C_Male_Contact_Tongue",
                 "USB_C_Cable"):
        obj = bpy.data.objects[name]
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        target.objects.link(obj)
    return socket


def open_housing(uncut):
    restore_meshes(uncut, ("Main_Housing",))
    housing = bpy.data.objects["Main_Housing"]
    for key in list(housing.keys()):
        if key.startswith("R08_"):
            del housing[key]
    cutter = macbook.prism(
        "_R09_Right_USB_Plug_Chute",
        macbook._rounded_rect_2d(12.0 * MM, 7.0 * MM, 2.0 * MM, seg=16),
        Vector((PORT_X, 14.15 * MM, -24.5 * MM)), macbook.X, macbook.Y,
        22.0 * MM, None)
    bpy.context.scene.collection.objects.link(cutter)
    difference(housing, cutter, "R09_Right_USB_Chute")
    bpy.data.objects["Main_Housing_Inspection_Wireframe"].data = housing.data
    housing["R09_Status"] = (
        "right lower USB access pocket; wall thickness, retention and "
        "tooling not verified")
    housing["R09_Chute_Center_X_mm"] = 51.5


def tag_scene():
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R09"
    for key in list(scene.keys()):
        if key.startswith("R08_"):
            del scene[key]
    scene["DeepReal_Status"] = (
        "right-side direct-board USB packaging study; engineering readiness BLOCKED")
    scene["R09_Decision"] = (
        "test a bottom-entry USB-C socket on a right-hand main-PCB tab; "
        "retire centered daughterboard/flex concept")
    scene["R09_Limits"] = (
        "KiCad board unchanged; USB socket and cable are envelopes; no pad "
        "mapping, USB routing, SI, EMI, thermal or mechanical approval")
