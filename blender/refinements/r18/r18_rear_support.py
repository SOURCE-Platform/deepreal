"""Two narrow rear support penetrations per drum for a visibility study."""

import math

import bpy
from mathutils import Vector

import macbook
from assembly_primitives import cylinder, tube
from r15_drive import cuboid
from r15_shell import _boolean

MM = 0.001
AXIS_Y = -1.5
AXIS_Z = 20.0
FACE_SLOT_DEG = 186.0  # 150-degree motion plus conservative end-arm clearance.
INTERACTION_SLOT_DEG = 42.0  # 30-degree study plus the same clearance.


def swept_slot(side, sign, x_mm, center_deg, width_deg, collection):
    # Short convex sectors avoid ambiguous triangulation of a >180-degree ngon.
    segment_count = math.ceil(width_deg / 45.0)
    for segment in range(segment_count):
        start = center_deg - width_deg / 2 + width_deg * segment / segment_count
        end = center_deg - width_deg / 2 + width_deg * (segment + 1) / segment_count
        angles = [math.radians(start + (end - start) * index / 16)
                  for index in range(17)]
        outline = [(0.0, 0.0)]
        outline.extend((-20 * math.cos(angle) * MM,
                        20 * math.sin(angle) * MM) for angle in angles)
        cutter = macbook.prism(
            side + "_Rear_Arm_Sweep_CUTTER",
            outline, Vector((sign * x_mm * MM,
                             AXIS_Y * MM, AXIS_Z * MM)),
            macbook.Y, macbook.Z, 3.2 * MM)
        bpy.context.scene.collection.objects.link(cutter)
        for suffix in ("Sensor_Head", "Rear_Access_Cover_REMOVABLE_CONCEPT"):
            target = bpy.data.objects[side + "_" + suffix]
            # r15_shell._boolean consumes its cutter.
            copied = cutter.copy()
            copied.data = cutter.data.copy()
            collection.objects.link(copied)
            _boolean(target, copied, "DIFFERENCE")
        bpy.data.objects.remove(cutter, do_unlink=True)


def remove_old_side_drive(side, sign):
    suffixes = ("Geared_Motor", "Motor_Pinion", "Motor_Bracket",
                "Motor_Output_Shaft_CONCEPT", "Ring_Gear", "Rotation_Stop",
                "Motor_Mount_Arm_Low_CONCEPT",
                "Motor_Mount_Arm_High_CONCEPT",
                "Motor_Mount_Standoff_Low_CONCEPT",
                "Motor_Mount_Standoff_High_CONCEPT", "Encoder_Board",
                "Encoder_Magnet", "Bearing_Outer", "Bearing_Inner",
                "Drum_Axle", "Head_Power_Data_Flex_ROUTE_CONCEPT",
                "Motor_Power_Harness_ROUTE_CONCEPT",
                "Encoder_Feedback_ROUTE_CONCEPT")
    for suffix in suffixes:
        obj = bpy.data.objects.get(side + "_" + suffix)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    exposed_end = ("Left" if sign < 0 else "Right")
    bpy.data.objects.remove(
        bpy.data.objects[side + "_Sensor_Head_Flat_End_" + exposed_end],
        do_unlink=True)


def build(scene, specs=None, revision="R18"):
    if specs is None:
        specs = (("Face", -1, 180.0, FACE_SLOT_DEG),
                 ("Interaction", 1, 195.0, INTERACTION_SLOT_DEG))
    collection = bpy.data.collections.new(
        "09 — " + revision + " REAR YOKE AND ARM-SWEEP STUDY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    created = []
    for side, sign, center, width in specs:
        shell = bpy.data.objects[side + "_Sensor_Head"]
        shell_material = shell.data.materials[0]
        support_material = bpy.data.materials["Motion_Bracket"]
        bearing_material = bpy.data.materials["Motion_Steel"]
        remove_old_side_drive(side, sign)
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        for x_mm in (6.0, 44.0):
            swept_slot(side, sign, x_mm, center, width, collection)

        end = cylinder(side + "_Plain_Rotating_Outer_Face_" + revision,
                       (sign * 54.12, AXIS_Y, AXIS_Z), macbook.X,
                       12.0, .24, shell_material, collection, 96)
        end.parent = pivot
        end.matrix_parent_inverse = pivot.matrix_world.inverted()
        end[revision + "_Status"] = (
            "visual rotating end face; shell fastening and seal unselected")
        created.append(end)

        rail = cuboid(side + "_Rear_Support_Yoke_" + revision,
                      (sign * 25.0, 17.2, AXIS_Z),
                      (42.0, 2.2, 3.4), support_material, collection)
        rail[revision + "_Status"] = (
            "fixed rear yoke envelope; connection to enclosure and "
            "stiffness unverified")
        created.append(rail)
        for label, x_mm in (("Inner", 6.0), ("Outer", 44.0)):
            arm = cuboid(side + "_Rear_Arm_" + label + "_" + revision,
                         (sign * x_mm, 7.9, AXIS_Z),
                         (1.6, 19.0, 1.6), support_material, collection)
            arm[revision + "_Status"] = (
                "fixed arm through drum sweep slot; bearing mount concept")
            bearing = tube(side + "_Bearing_" + label + "_ENVELOPE_" + revision,
                           (sign * x_mm, AXIS_Y, AXIS_Z), macbook.X,
                           1.2, 3.2, 1.6, bearing_material, collection, 48)
            bearing[revision + "_Status"] = (
                "bearing envelope only; inner/outer race attachment open")
            created.extend((arm, bearing))
        shell[revision + "_Rear_Arm_Sweep"] = (
            "two 3.2 mm axial slots, each %g degrees around drum; "
            "witness openings for the stated trial travel range" % width)
    return created
