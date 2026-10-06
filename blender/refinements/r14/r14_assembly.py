"""Organize restored drum parts and add provisional head boards and routes."""

import math

import bpy
from mathutils import Matrix, Vector

import macbook
from assembly_primitives import routed_wire

MM = 0.001


def material(name, rgba, metallic=0.0, roughness=0.48):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = rgba
    return mat


def turn_interaction(obj):
    center = Vector((0, -1.5 * MM, 20 * MM))
    rotation = (Matrix.Translation(center)
                @ Matrix.Rotation(math.radians(45), 4, "X")
                @ Matrix.Translation(-center))
    obj.matrix_world = rotation @ obj.matrix_world


def rotated_point(point_mm):
    center = Vector((0, -1.5, 20))
    relative = Vector(point_mm) - center
    rotated = Matrix.Rotation(math.radians(45), 3, "X") @ relative
    return tuple(center + rotated)


def hierarchy(scene):
    root = bpy.data.collections.new("07 — DRUM SYSTEMS — ASSEMBLY REVIEW")
    scene.collection.children.link(root)
    root.color_tag = "COLOR_04"
    groups = {}
    for side, letter in (("Face", "A"), ("Interaction", "B")):
        for role, title in (("motion", "FIXED DRIVE + SUPPORT"),
                            ("optical", "ROTATING DRUM + OPTICS")):
            col = bpy.data.collections.new(
                "07%s — %s %s — CONCEPT" % (letter, side.upper(), title))
            root.children.link(col)
            col.color_tag = "COLOR_02" if role == "motion" else "COLOR_05"
            groups[(side, role)] = col
    routes = bpy.data.collections.new(
        "07C — MOTOR + HEAD ROUTES — CONCEPT")
    root.children.link(routes)
    routes.color_tag = "COLOR_03"
    groups["routes"] = routes
    return groups


def head_boards(groups):
    green = material("R14_Head_PCBA_Concept_Green",
                     (0.035, 0.29, 0.19, 1.0), roughness=0.43)
    dark = material("R14_Head_Connector_Concept_Dark",
                    (0.055, 0.065, 0.075, 1.0), roughness=0.5)
    result = {}
    for side, sign in (("Face", -1), ("Interaction", 1)):
        target = groups[(side, "optical")]
        board = macbook.slab(
            side + "_Head_PCBA_Carrier_CONCEPT",
            Vector((sign * 26.75 * MM, -4.7 * MM, 20 * MM)),
            macbook.X, macbook.Z,
            (46.5 * MM, 12 * MM), 1.0 * MM, 0.6 * MM, green)
        target.objects.link(board)
        if side == "Interaction":
            turn_interaction(board)
        board["R14_Electrical_Status"] = (
            "one reusable head-PCB envelope populated twice; no native "
            "schematic, copper, stackup, mounting or pin map")
        board["R14_Assembly"] = side + " rotating drum assembly"
        connector = macbook.slab(
            side + "_Head_Flex_Connector_PROXY",
            Vector((sign * 34 * MM, -5.4 * MM, 20 * MM)),
            macbook.X, macbook.Z,
            (5 * MM, 2 * MM), 0.25 * MM, 0.8 * MM, dark)
        target.objects.link(connector)
        if side == "Interaction":
            turn_interaction(connector)
        connector["R14_Electrical_Status"] = (
            "visual connector location only; 51-contact part/pinout open")
        connector["R14_Assembly"] = side + " rotating drum assembly"
        result[side] = {"board": board, "connector": connector}
    return result


def remove_old_routes():
    for side in ("Face", "Interaction"):
        for suffix in ("Head_Power_Data_Flex_CONCEPT",
                       "Head_Flex_Interface_CONCEPT"):
            obj = bpy.data.objects.get(side + "_" + suffix)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)


def add_routes(groups):
    route_col = groups["routes"]
    orange = material("R14_Head_Flex_Amber", (0.85, 0.37, 0.045, 1.0),
                      roughness=0.5)
    red = material("R14_Motor_Power_Red", (0.6, 0.045, 0.03, 1.0),
                   roughness=0.6)
    yellow = material("R14_Encoder_Feedback_Yellow",
                      (0.8, 0.57, 0.07, 1.0), roughness=0.6)
    dark = bpy.data.materials["R14_Head_Connector_Concept_Dark"]
    routes = {}
    for side, sign, jref in (("Face", -1, "J4"),
                             ("Interaction", 1, "J5")):
        board_connector = macbook.slab(
            jref + "_" + side + "_Motor_Encoder_Connector_PROXY",
            Vector((sign * 34 * MM, 10.0 * MM, -23.5 * MM)),
            macbook.X, macbook.Z,
            (5.0 * MM, 2.0 * MM), 0.25 * MM, 1.2 * MM, dark)
        route_col.objects.link(board_connector)
        board_connector["R14_Electrical_Status"] = (
            "proposed J4/J5 envelope on main-PCB front face; no selected "
            "connector, footprint or routed nets")

        optical_start = (sign * 34, -5.4, 20)
        optical_second = (sign * 35, -6.5, 26)
        if side == "Interaction":
            optical_start = rotated_point(optical_start)
            optical_second = rotated_point(optical_second)
        optical = routed_wire(
            side + "_Head_Power_Data_Flex_ROUTE_CONCEPT",
            (optical_start, optical_second,
             (sign * 44, -2.0, 27), (sign * 50, 7.0, 24),
             (sign * 51, 10.5, 12), (sign * 51, 9.0, -10),
             (sign * 45, 9.0, -22.5),
             (sign * 22, 10.1, -23.5)),
            0.55, 2.0, orange, route_col)
        optical["R14_Route_Status"] = (
            "visible continuous concept from head-board proxy to J2/J3; "
            "rotating feedthrough, flex stackup and shell passage unresolved")

        motor = routed_wire(
            side + "_Motor_Power_Harness_ROUTE_CONCEPT",
            ((sign * 45, 13.6, 20), (sign * 51, 13.0, 14),
             (sign * 52, 12.8, -10), (sign * 45, 10.3, -22.8),
             (sign * 34, 10.0, -23.5)),
            0.34, 2.0, red, route_col)
        encoder = routed_wire(
            side + "_Encoder_Feedback_ROUTE_CONCEPT",
            ((sign * 46, 7.0, 20), (sign * 50, 10.0, 13),
             (sign * 50.8, 12.2, -9.5), (sign * 44, 10.0, -22.4),
             (sign * 34, 10.0, -23.5)),
            0.25, 2.0, yellow, route_col)
        for obj in (motor, encoder):
            obj["R14_Route_Status"] = (
                "visual power/feedback path to proposed J4/J5; pinout, "
                "suppression, strain relief and enclosure passage unresolved")
        routes[side] = (optical, motor, encoder, board_connector)
    return routes
