"""Enclose each fixed drive and encoder in a coaxial end chamber."""

import math

import bpy
from mathutils import Vector

import macbook
from assembly_primitives import cylinder, tube
from r15_drive import cuboid
from r15_shell import _boolean

MM = 0.001


def slot_in_inner_cap(side, sign):
    """A near-axis arc lets the moving head flex enter the fixed chamber."""
    name = (side + "_Sensor_Head_Flat_End_"
            + ("Left" if sign < 0 else "Right"))
    previous = bpy.data.objects[name]
    collection = previous.users_collection[0]
    material = previous.data.materials[0]
    bpy.data.objects.remove(previous, do_unlink=True)
    cap = tube(name, (sign * 54.24, -1.5, 20), macbook.X,
               2.35, 12.0, .24, material, collection, 96)
    angles = [math.radians(-82 + 164 * index / 48) for index in range(49)]
    outline = []
    for radius, order in ((6.9, angles), (4.85, angles[::-1])):
        outline.extend(((-radius * math.cos(a) * MM,
                         -radius * math.sin(a) * MM)) for a in order)
    cutter = macbook.prism(
        side + "_Head_Flex_Arc_Slot_CUTTER",
        outline, Vector((sign * 54.24 * MM, -1.5 * MM, 20 * MM)),
        macbook.Y, macbook.Z, 0.8 * MM)
    bpy.context.scene.collection.objects.link(cutter)
    _boolean(cap, cutter, "DIFFERENCE")
    cap["R17_Head_Flex_Passage"] = (
        "near-axis 164-degree arc for limited-rotation flex; "
        "strength and moving-cable sweep unverified")


def remove_legacy_drive(side):
    names = ("Geared_Motor", "Motor_Pinion", "Motor_Bracket",
             "Motor_Output_Shaft_CONCEPT", "Ring_Gear", "Rotation_Stop",
             "Motor_Mount_Arm_Low_CONCEPT",
             "Motor_Mount_Arm_High_CONCEPT",
             "Motor_Mount_Standoff_Low_CONCEPT",
             "Motor_Mount_Standoff_High_CONCEPT")
    for suffix in names:
        bpy.data.objects.remove(bpy.data.objects[side + "_" + suffix],
                                do_unlink=True)


def curved_housing_pocket(side, sign):
    housing = bpy.data.objects["Main_Housing"]
    if housing.data.users > 1:
        housing.data = housing.data.copy()
    cutter = macbook.cylinder(
        side + "_Curved_Side_Pocket_CUTTER",
        Vector((sign * 57.3 * MM, -1.5 * MM, 20 * MM)),
        macbook.X, 12.15 * MM, 7.0 * MM, None, seg=96)
    bpy.context.scene.collection.objects.link(cutter)
    _boolean(housing, cutter, "DIFFERENCE")
    housing["R17_Curved_Drum_Pocket"] = (
        "side wall relieved around fixed coaxial end chambers with "
        "nominal 0.35 mm radial visual clearance; structural review open")


def build(scene):
    collection = bpy.data.collections.new(
        "09 — R17 ENCLOSED OUTER DRUM MODULES — FIXED")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    created = []
    for side, sign in (("Face", -1), ("Interaction", 1)):
        curved_housing_pocket(side, sign)
        shell = bpy.data.objects[side + "_Sensor_Head"]
        body_material = shell.data.materials[0]
        support_material = bpy.data.materials["Motion_Bracket"]
        board_material = bpy.data.materials["Motion_Encoder_PCBA"]
        sensor_material = bpy.data.materials["Motion_Encoder_Magnet"]
        motor_material = bpy.data.materials["Motion_Motor"]
        rotor_material = bpy.data.materials["Motion_Gear"]
        remove_legacy_drive(side)
        slot_in_inner_cap(side, sign)

        sleeve = tube(side + "_Fixed_End_Chamber_Sleeve_R17",
                      (sign * 56.55, -1.5, 20), macbook.X,
                      10.55, 11.8, 4.3, body_material, collection, 96)
        # The cable outlet faces the rear/lower housing cavity, not the viewer.
        outlet = cuboid(side + "_Rear_Cable_Outlet_CUTTER",
                        (sign * 57.0, 9.2, 13.0),
                        (3.0, 7.4, 7.0), None, collection)
        _boolean(sleeve, outlet, "DIFFERENCE")
        sleeve["R17_Function"] = (
            "fixed coaxial side chamber, visibly continuous with the drum; "
            "rear cable outlet inside housing")
        outer_cap = cylinder(side + "_Smooth_Outer_End_Cap_R17",
                             (sign * 58.9, -1.5, 20), macbook.X,
                             11.8, 0.4, body_material, collection, 96)
        outer_cap["R17_Function"] = (
            "fixed clean side face covers the encoder, motor mount and cable")

        stator = tube(side + "_Axial_Motor_Stator_ENVELOPE_R17",
                      (sign * 55.45, -1.5, 20), macbook.X,
                      7.0, 9.5, 2.0, motor_material, collection, 96)
        stator["R17_Function"] = (
            "fixed annular motor envelope; torque, supplier, windings and "
            "controller are unselected")
        rotor = tube(side + "_Axial_Motor_Rotor_Hub_ENVELOPE_R17",
                     (sign * 54.9, -1.5, 20), macbook.X,
                     2.2, 4.8, .8, rotor_material, collection, 96)
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        rotor.parent = pivot
        rotor.matrix_parent_inverse = pivot.matrix_world.inverted()
        rotor["R17_Function"] = (
            "rotating shaft-coupled hub envelope; torque path unverified")
        for label, z in (("Top", 28.2), ("Bottom", 11.8)):
            mount = cylinder(side + "_Stator_Mount_" + label + "_R17",
                             (sign * 54.6, -1.5, z), macbook.X,
                             .36, .9, support_material, collection, 24)
            mount["R17_Function"] = "fixed stator support at inner cap"
            created.append(mount)

        old_board = bpy.data.objects[side + "_Encoder_Board"]
        board_collection = old_board.users_collection[0]
        bpy.data.objects.remove(old_board, do_unlink=True)
        board = cylinder(side + "_Encoder_Board",
                         (sign * 56.9, -1.5, 20), macbook.X,
                         2.75, 0.6, board_material, board_collection, 48)
        board["R17_Encoder_Status"] = (
            "compact fixed magnetic-angle PCB envelope; sensor and "
            "diametric magnet selection, calibration and accuracy open")
        sensor = cuboid(side + "_Encoder_Sensor_IC_PROXY_R17",
                        (sign * 56.45, -1.5, 20),
                        (0.3, 1.6, 1.6), sensor_material, collection)
        sensor["R17_Function"] = (
            "fixed magnetic angle sensor faces shaft-end rotating magnet")
        for label, y, z in (("A", -3.25, 18.25),
                            ("B", 0.25, 21.75)):
            post = cylinder(side + "_Encoder_Board_Mount_" + label + "_R17",
                            (sign * 57.95, y, z), macbook.X,
                            0.28, 1.8, support_material, collection, 24)
            post["R17_Function"] = "fixed board support from sealed end cap"
            created.append(post)
        created.extend((sleeve, outer_cap, stator, rotor, board, sensor))
    return collection, created
