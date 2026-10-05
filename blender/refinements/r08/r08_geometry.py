#!/usr/bin/env python3
"""R08 enclosure study: a centered USB entry with a lateral internal route."""

from pathlib import Path

import bpy
from mathutils import Vector

import macbook
from r07_geometry import difference

MM = 0.001


def restore_meshes(source: Path, names):
    """Use the uncut native R04 meshes at their already aligned transforms."""
    with bpy.data.libraries.load(str(source), link=False) as (src, dst):
        missing = set(names) - set(src.objects)
        if missing:
            raise RuntimeError(f"R04 restoration source missing: {missing}")
        dst.objects = list(names)
    for name, donor in zip(names, dst.objects):
        target = bpy.data.objects[name]
        if any(abs(target.matrix_basis[i][j] - donor.matrix_basis[i][j]) > 1e-8
               for i in range(4) for j in range(4)):
            raise RuntimeError(
                f"R04/R07 transform mismatch: {name}: "
                f"target={list(target.matrix_basis.translation)} "
                f"donor={list(donor.matrix_basis.translation)}")
        target.data = donor.data
        for key in list(target.keys()):
            if key.startswith(("R05_Service", "R07_Service")):
                del target[key]
        target["R08_Status"] = "uncut R04 mesh restored; engineering status provisional"
        bpy.data.objects.remove(donor, do_unlink=True)


def rear_shield_feedthrough():
    tray = bpy.data.objects["Shield_Rear_Tray"]
    cutter = macbook.slab(
        "_R08_Rear_Shield_Side_Feedthrough_Cutter",
        Vector((39.0 * MM, 11.0 * MM, -17.5 * MM)), macbook.X, macbook.Z,
        (5.0 * MM, 4.0 * MM), 0.5 * MM, 10.0 * MM, None)
    bpy.context.scene.collection.objects.link(cutter)
    difference(tray, cutter, "R08_Side_Feedthrough")
    tray["R08_Feedthrough_Envelope_mm"] = [5.0, 4.0]
    tray["R08_Feedthrough_Center_mm"] = [39.0, -17.5]
    tray["R08_Status"] = (
        "small right-side concept feedthrough; shield bonding and cable stackup unverified")


def restore_housing(source: Path):
    restore_meshes(source, ("Main_Housing",))
    housing = bpy.data.objects["Main_Housing"]
    chute = macbook.prism(
        "_R08_USB_Overmold_Chute",
        macbook._rounded_rect_2d(9.4 * MM, 5.4 * MM, 2.3 * MM, seg=12),
        Vector((0.0, 18.0 * MM, -27.5 * MM)), macbook.X, macbook.Y,
        15.0 * MM, None)
    bpy.context.scene.collection.objects.link(chute)
    difference(housing, chute, "R08_USB_Overmold_Chute")
    pocket = macbook.slab(
        "_R08_Daughterboard_Clearance_Pocket",
        Vector((0.0, 18.0 * MM, -12.0 * MM)), macbook.X, macbook.Z,
        (18.0 * MM, 8.0 * MM), 0.6 * MM, 4.0 * MM, None)
    bpy.context.scene.collection.objects.link(pocket)
    difference(housing, pocket, "R08_Daughterboard_Pocket")
    socket_pocket = macbook.prism(
        "_R08_Socket_Clearance_Pocket",
        macbook._rounded_rect_2d(11.5 * MM, 5.1 * MM, 1.8 * MM, seg=12),
        Vector((0.0, 18.0 * MM, -17.6 * MM)), macbook.X, macbook.Y,
        6.2 * MM, None)
    bpy.context.scene.collection.objects.link(socket_pocket)
    difference(housing, socket_pocket, "R08_Socket_Pocket")
    bpy.data.objects["Main_Housing_Inspection_Wireframe"].data = housing.data
    housing["R08_USB_Chute_mm"] = [9.4, 5.4, 15.0]
    housing["R08_Daughterboard_Pocket_mm"] = [18.0, 4.0, 8.0]
    housing["R08_Socket_Pocket_mm"] = [11.5, 5.1, 6.2]


def _curve(name, points, material, target):
    data = bpy.data.curves.new(name + "_Path", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = 0.35 * MM
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (*tuple(Vector(coords) * MM), 1.0)
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj["DeepReal_Status"] = (
        "illustrative USB power/data route only; no pinout, impedance or power approval")
    obj["R08_Route_Points_mm"] = [v for point in points for v in point]
    return obj


def study_material(name, color, metallic=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = 0.48
    return material


def usb_socket_and_side_route():
    routes = bpy.data.collections["05 — POWER AND DATA ROUTES — PROVISIONAL"]
    routes.name = "05 — USB POWER + DATA PATH — DIAGRAM ONLY"
    old = bpy.data.objects["USB3_PD_Internal_Flex_CONCEPT"]
    bpy.data.objects.remove(old, do_unlink=True)
    old_board = bpy.data.objects["Centered_USB_Daughterboard"]
    board_mat = old_board.data.materials[0]
    bpy.data.objects.remove(old_board, do_unlink=True)
    board = macbook.slab(
        "Centered_USB_Daughterboard", Vector((0.0, 18.0 * MM, -12.0 * MM)),
        macbook.X, macbook.Z, (16.0 * MM, 6.0 * MM), 0.5 * MM,
        1.0 * MM, board_mat)
    routes.objects.link(board)
    board["DeepReal_Status"] = (
        "packaging placeholder; exact USB-C receptacle, schematic and PCB absent")

    metal = study_material("R08_Socket_Envelope_Metal",
                           (0.16, 0.19, 0.22, 1.0), 0.72)
    socket = macbook.prism(
        "USB_C_Female_Socket_ENVELOPE_NOT_PART_SELECTED",
        macbook._rounded_rect_2d(10.5 * MM, 4.3 * MM, 1.6 * MM, seg=12),
        Vector((0.0, 18.0 * MM, -17.6 * MM)), macbook.X, macbook.Y,
        5.2 * MM, metal)
    routes.objects.link(socket)
    cavity = macbook.prism(
        "_R08_Socket_Mating_Void",
        macbook._rounded_rect_2d(9.3 * MM, 3.3 * MM, 1.1 * MM, seg=12),
        Vector((0.0, 18.0 * MM, -19.0 * MM)), macbook.X, macbook.Y,
        3.4 * MM, None)
    bpy.context.scene.collection.objects.link(cavity)
    difference(socket, cavity, "R08_Mating_Void")
    socket["DeepReal_Status"] = (
        "illustrative mating envelope; exact USB-C female connector not selected")

    main = bpy.data.objects["Mainboard_USB_Flex_Connector_CONCEPT"]
    main.location.x = 39.0 * MM
    main.location.z = -2.5 * MM
    main["DeepReal_Status"] = (
        "new main-board connector location is a proposal; current PCB unchanged")
    points = ((7.0, 18.0, -12.5), (8.8, 18.0, -15.8),
              (10.0, 18.0, -17.5), (35.0, 18.0, -17.5),
              (39.0, 17.0, -17.5), (39.0, 14.5, -17.5),
              (39.0, 13.0, -17.5), (39.0, 12.7, -17.5))
    amber = study_material("R08_Route_Amber_CONCEPT",
                           (0.58, 0.17, 0.025, 1.0), 0.1)
    route = _curve("USB_Power_Data_Side_Route_CONCEPT", points,
                   amber, routes)
    return board, socket, main, route


def tag_scene():
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R08"
    scene["DeepReal_Status"] = "R08 geometric packaging study; no electrical or thermal approval"
    scene["R08_USB_Status"] = (
        "centered external entry with right-side diagram route; exact socket,"
        " daughterboard, flex, connector and USB/power engineering unresolved")
    scene["R08_Thermal_Status"] = (
        "spreader continuous; PCB-to-spreader interface, heat budget, materials and"
        " housing rejection unverified; vents undecided")
    scene["R08_Shield_Status"] = (
        "front lid restored; rear side feedthrough provisional; EMI not measured")
