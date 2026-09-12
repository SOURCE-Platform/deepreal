"""Blender concept geometry for the stationary DeepReal electronics."""

import bpy
from mathutils import Vector

from assembly_primitives import box, cylinder, material, tag
from pcba_bom import BOARD
import pcba_geometry
import pcba_visual_copper


BOARD_Y = BOARD["center_y"]
BOARD_Z = BOARD["center_z"]
BOARD_X0 = -45.0
BOARD_X1 = 45.0
BOARD_Z0 = -25.5
BOARD_Z1 = 2.5
MOUNT_POINTS = (
    (-42.0, -22.5), (-42.0, -0.5),
    (42.0, -22.5), (42.0, -0.5),
)
SHIELD_X0 = -46.0
SHIELD_X1 = 46.0
SHIELD_Z0 = -20.9
SHIELD_Z1 = 3.5
SHIELD_FRONT_Y = 11.8
SHIELD_REAR_Y = 19.05
CONNECTOR_Z = -25.5
SHIELD_SHEET = 0.45


def _materials():
    return {
        "board": material("Electronics_PCBA", (0.008, 0.075, 0.022),
                          roughness=0.48),
        "soc": material("Electronics_iMX95", (0.92, 0.48, 0.05),
                        metallic=0.18, roughness=0.32),
        "fpga": material("Electronics_FPGA", (0.02, 0.42, 0.68),
                         metallic=0.12, roughness=0.34),
        "memory": material("Electronics_Memory", (0.035, 0.045, 0.07),
                           roughness=0.30),
        "power": material("Electronics_Power", (0.44, 0.12, 0.52),
                          roughness=0.40),
        "driver": material("Electronics_Driver", (0.06, 0.46, 0.34),
                           roughness=0.38),
        "connector": material("Electronics_Connector", (0.72, 0.74, 0.76),
                              metallic=0.55, roughness=0.30),
        "shield": material("EMI_Shield_Can", (0.30, 0.34, 0.40),
                           metallic=0.92, roughness=0.30),
        "copper": material("Thermal_Spreader_Copper", (0.66, 0.24, 0.06),
                           metallic=0.95, roughness=0.25),
        "pad": material("Thermal_Pad", (0.12, 0.30, 0.36),
                        roughness=0.72),
        "mic": material("Electronics_Microphone", (0.12, 0.12, 0.13),
                        metallic=0.55, roughness=0.35),
        "keepout": material("Electronics_Keepout", (0.94, 0.55, 0.04),
                            roughness=0.45, alpha=0.10),
        "ground": material("Shield_Ground_Features", (0.72, 0.56, 0.18),
                           metallic=0.94, roughness=0.26),
        "bank": material("Connector_Apron_PCBA", (0.035, 0.25, 0.09),
                         roughness=0.58),
    }


def _apply_boolean(target, cutter, operation, label):
    """Apply one exact construction boolean and remove its temporary tool."""
    with bpy.context.temp_override(
            object=target, active_object=target, selected_objects=[target]):
        modifier = target.modifiers.new(label, "BOOLEAN")
        modifier.operation = operation
        modifier.solver = "EXACT"
        modifier.object = cutter
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _union_box(target, name, center, dims, radius, mat, collection):
    tool = box(name, center, dims, radius, mat, collection)
    _apply_boolean(target, tool, "UNION", "Join_" + name)


def _cut_mounting_holes(target, mat, collection, length, radius):
    for index, (x, z) in enumerate(MOUNT_POINTS, 1):
        cutter = cylinder(
            "_Mounting_Hole_Tool_{:02d}".format(index),
            (x, BOARD_Y, z), Vector((0.0, 1.0, 0.0)),
            radius, length, mat, collection, segments=32)
        _apply_boolean(
            target, cutter, "DIFFERENCE",
            "Mounting_Hole_{:02d}".format(index))


def _shield_enclosure(mats, collection):
    """Build a formed rear tray, removable lid, and grounded PCB boundary."""
    x0, x1 = SHIELD_X0, SHIELD_X1
    z0, z1 = SHIELD_Z0, SHIELD_Z1
    front_y, rear_y = SHIELD_FRONT_Y, SHIELD_REAR_Y
    sheet = SHIELD_SHEET
    depth = rear_y - front_y
    mid_y = (front_y + rear_y) / 2.0
    mid_z = (z0 + z1) / 2.0
    objects = []

    # Start with the rear panel and fuse the perimeter walls into it. The
    # lower wall is split around the PCB thickness, forming a controlled
    # pass-through rather than cutting through the board substrate.
    tray = box(
        "Shield_Rear_Tray", (0.0, rear_y, mid_z),
        (x1 - x0, sheet, z1 - z0), 0.8, mats["shield"], collection)
    wall_specs = (
        ("_Tray_Left_Wall", (x0 + sheet / 2.0, mid_y, mid_z),
         (sheet, depth, z1 - z0), 0.18),
        ("_Tray_Right_Wall", (x1 - sheet / 2.0, mid_y, mid_z),
         (sheet, depth, z1 - z0), 0.18),
        ("_Tray_Top_Wall", (0.0, mid_y, z1 - sheet / 2.0),
         (x1 - x0, depth, sheet), 0.18),
        ("_Tray_Apron_Lip_Front",
         (0.0, (front_y + 15.45) / 2.0, z0 + sheet / 2.0),
         (x1 - x0, 15.45 - front_y, sheet), 0.18),
        ("_Tray_Apron_Lip_Rear",
         (0.0, (17.25 + rear_y) / 2.0, z0 + sheet / 2.0),
         (x1 - x0, rear_y - 17.25, sheet), 0.18),
    )
    for name, center, dims, radius in wall_specs:
        _union_box(
            tray, name, center, dims, radius, mats["shield"], collection)
    _cut_mounting_holes(
        tray, mats["shield"], collection, depth + 2.0, 1.85)
    tag(tray, "Electronics Shield Enclosure", "FORMED REAR-TRAY CONCEPT")
    tray["Grounding_Intent"] = "PCB ground ring and three chassis bonds"
    tray["Coverage_Intent"] = "Complete populated electronics chamber"
    tray["Thermal_Path"] = (
        "Rear tray contacts the copper spreader and housing pad")
    tray["Integrated_Walls"] = "left, right, top, connector-apron boundary"
    objects.append(tray)

    lid = box(
        "Shield_Front_Lid", (0.0, front_y, mid_z),
        (x1 - x0, sheet, z1 - z0), 0.8, mats["shield"], collection)
    tag(lid, "Electronics Shield Enclosure", "REMOVABLE LID CONCEPT")
    lid["Grounding_Intent"] = "Perimeter contact to formed rear tray"
    lid["Coverage_Intent"] = "Complete populated electronics chamber"
    objects.append(lid)

    # The visible ring and via field communicate a continuous, controlled
    # shield termination. Exact via pitch and contact-finger geometry remain
    # PCB and EMC engineering work.
    ring_y = BOARD_Y - 0.93
    ring_specs = (
        ("PCB_Ground_Ring_Left", (BOARD_X0 + 0.45, ring_y, -10.1),
         (0.55, 0.22, 24.0)),
        ("PCB_Ground_Ring_Right", (BOARD_X1 - 0.45, ring_y, -10.1),
         (0.55, 0.22, 24.0)),
        ("PCB_Ground_Ring_Top", (0.0, ring_y, BOARD_Z1 - 0.45),
         (88.2, 0.22, 0.55)),
        ("PCB_Ground_Ring_Apron", (0.0, ring_y, SHIELD_Z0 + 0.70),
         (88.2, 0.22, 0.55)),
    )
    for name, center, dims in ring_specs:
        obj = box(name, center, dims, 0.12, mats["ground"], collection)
        objects.append(tag(obj, "Shield perimeter ground",
                           "GROUND-RING CONCEPT"))

    via_positions = (
        (-40.0, BOARD_Z1 - 0.45), (-20.0, BOARD_Z1 - 0.45),
        (0.0, BOARD_Z1 - 0.45), (20.0, BOARD_Z1 - 0.45),
        (40.0, BOARD_Z1 - 0.45),
        (-40.0, z0 + 0.7), (-20.0, z0 + 0.7), (0.0, z0 + 0.7),
        (20.0, z0 + 0.7), (40.0, z0 + 0.7),
    )
    for index, (x, z) in enumerate(via_positions, 1):
        via = cylinder("Shield_Ground_Via_{:02d}".format(index),
                       (x, ring_y - 0.02, z), Vector((0.0, 1.0, 0.0)),
                       0.32, 0.36, mats["ground"], collection, segments=20)
        objects.append(tag(via, "Shield perimeter ground",
                           "VIA-FENCE CONCEPT"))

    for label, x in (("Left", -34.0), ("Center", 0.0), ("Right", 34.0)):
        tab = box("Shield_Chassis_Bond_" + label,
                  (x, rear_y + 0.55, z1 - 1.6), (6.0, 1.5, 2.4), 0.25,
                  mats["ground"], collection)
        objects.append(tag(tab, "Shield chassis bond",
                           "GROUND-TAB CONCEPT"))
    return objects


def _connector_apron(mats, collection):
    """Mark the face/auxiliary/interaction service regions."""
    objects = []
    for name, x, width in (
        ("Face_Connector_Bank", -28.0, 36.0),
        ("Auxiliary_Connector_Bank", 0.0, 8.0),
        ("Interaction_Connector_Bank", 28.0, 36.0),
    ):
        bank = box(name, (x, BOARD_Y - 0.25, CONNECTOR_Z),
                   (width, 0.45, 4.2), 0.35, mats["bank"], collection)
        bank["Apron_Zone"] = "Below grounded shield boundary"
        objects.append(tag(bank, "Connector Apron",
                           "SERVICE-ACCESS CONCEPT"))

    return objects


def build(collection):
    mats = _materials()
    objects = []
    board = box("Main_PCBA", (0.0, BOARD_Y, BOARD_Z),
                (BOARD["width"], BOARD["thickness"], BOARD["depth"]),
                0.8, mats["board"], collection)
    _cut_mounting_holes(board, mats["board"], collection, 4.0, 1.35)
    board["EMI_Shield_Coverage"] = (
        "All populated ICs inside full enclosure; lower apron remains outside")
    objects.append(tag(board, "Main electronics", "REQUIRED ENVELOPE"))
    board["Study_Label"] = (
        "DeepReal Main PCBA - Preliminary Engineering Layout / Packaging Study")

    keepout = box("Main_PCBA_Populated_Keepout", (0.0, 15.425, BOARD_Z),
                  (90.0, 6.0, 28.0), 1.0, mats["keepout"], collection)
    keepout.display_type = "WIRE"
    keepout.hide_render = True
    objects.append(tag(keepout, "Main electronics", "REFERENCE RESERVE"))

    objects += pcba_geometry.build(collection)
    objects += pcba_visual_copper.build(collection)
    objects += _connector_apron(mats, collection)

    objects += _shield_enclosure(mats, collection)

    spreader = box("Thermal_Spreader", (0.0, 19.90, BOARD_Z),
                   (76.0, 1.35, 23.0), 0.8, mats["copper"], collection)
    spreader["Thermal_Path"] = "Shield rear tray to housing thermal pad"
    objects.append(tag(spreader, "Thermal", "CONCEPT HEAT PATH"))
    pad = box("Housing_Thermal_Pad", (0.0, 21.2, BOARD_Z),
              (60.0, 1.4, 18.0), 0.7, mats["pad"], collection)
    objects.append(tag(pad, "Thermal", "CONCEPT INTERFACE"))
    return objects
