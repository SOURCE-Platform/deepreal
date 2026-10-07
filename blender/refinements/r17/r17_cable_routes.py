"""Place head, motor and encoder paths within the fixed end chambers."""

import math

import bpy
from mathutils import Vector

from assembly_primitives import routed_wire
from r14_assembly import rotated_point


def head_point(side, x, y, z):
    point = (x, y, z)
    return rotated_point(point) if side == "Interaction" else point


def build():
    collection = bpy.data.collections[
        "07C — MOTOR + HEAD ROUTES — CONCEPT"]
    colors = {
        "head": bpy.data.materials["R14_Head_Flex_Amber"],
        "motor": bpy.data.materials["R14_Motor_Power_Red"],
        "encoder": bpy.data.materials["R14_Encoder_Feedback_Yellow"],
    }
    created = []
    for side, sign in (("Face", -1), ("Interaction", 1)):
        for suffix in ("Head_Power_Data_Flex_ROUTE_CONCEPT",
                       "Motor_Power_Harness_ROUTE_CONCEPT",
                       "Encoder_Feedback_ROUTE_CONCEPT"):
            old = bpy.data.objects.get(side + "_" + suffix)
            if old:
                bpy.data.objects.remove(old, do_unlink=True)
        connector = bpy.data.objects[side + "_Head_Flex_Connector_PROXY"]
        position = connector.matrix_world.copy()
        position.translation += Vector((sign * .0035, 0, 0))
        connector.matrix_world = position
        connector["R17_Position"] = (
            "moved outward 3.5 mm to clear optical module cable departure")

        moving_points = [head_point(side, sign * x, y, z)
                         for x, y, z in ((37.5, -5.4, 20),
                                         (38.5, -6.0, 26.8),
                                         (40.0, -1.5, 27.0),
                                         (41.0, -1.5, 25.8),
                                         (50.8, -1.5, 25.8),
                                         (51.3, -3.0, 25.60),
                                         (51.8, -4.4, 25.02),
                                         (52.4, -5.94, 23.73),
                                         (53.0, -6.95, 21.98),
                                         (53.5, -7.3, 20.0),
                                         (54.6, -7.3, 20.0))]
        moving = routed_wire(
            side + "_Head_Flex_Rotating_Pigtail_R17",
            moving_points, .32, 2.0, colors["head"], collection)
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        moving.parent = pivot
        moving.matrix_parent_inverse = pivot.matrix_world.inverted()
        moving["R17_Route_Status"] = (
            "moves with the drum into the near-axis arc; final flex stack, "
            "strain relief and bend life unverified")

        # One saved-pose shape illustrates where the dynamic loop can live.
        # It does not claim to model the loop's deformation during motion.
        start = 0 if side == "Face" else 45
        loop = [head_point(side, sign * 54.6, -7.3, 20.0)]
        for angle in range(start, 121, 15):
            theta = math.radians(angle)
            loop.append((sign * 55.15,
                         -1.5 - 5.8 * math.cos(theta),
                         20.0 - 5.8 * math.sin(theta)))
        service = routed_wire(
            side + "_Head_Flex_Service_Loop_REST_POSE_ONLY_R17",
            loop, .32, 1.5, colors["head"], collection)
        service["R17_Route_Status"] = (
            "protected chamber keepout concept shown only at saved pose; "
            "must be designed for full flex sweep and fatigue")

        main_head = routed_wire(
            side + "_Head_Power_Data_Flex_ROUTE_CONCEPT",
            ((sign * 55.15, 1.4, 14.98),
             (sign * 55.6, 1.0, 13.5),
             (sign * 56.7, 7.5, 13.2),
             (sign * 57.0, 10.5, 12.5),
             (sign * 57.0, 11.0, -10.0),
             (sign * 45.0, 10.0, -22.5),
             (sign * 22.0, 10.1, -23.5)),
            .32, 2.0, colors["head"], collection)
        main_head["R17_Route_Status"] = (
            "fixed head power/data tail through rear outlet to J2/J3 area; "
            "electrical nets and connector still unverified")

        motor = routed_wire(
            side + "_Motor_Power_Harness_ROUTE_CONCEPT",
            ((sign * 55.45, 6.7, 20.0),
             (sign * 56.6, 6.7, 15.0),
             (sign * 57.0, 7.8, 12.8),
             (sign * 57.0, 10.5, 12.0),
             (sign * 57.0, 11.0, -10.0),
             (sign * 45.0, 10.0, -22.8),
             (sign * 34.0, 10.0, -23.5)),
            .28, 1.5, colors["motor"], collection)
        motor["R17_Route_Status"] = (
            "fixed motor lead through rear outlet; termination unselected")

        encoder = routed_wire(
            side + "_Encoder_Feedback_ROUTE_CONCEPT",
            ((sign * 56.9, -1.5, 20.0),
             (sign * 57.3, -1.5, 15.0),
             (sign * 57.0, 7.5, 13.2),
             (sign * 57.0, 10.5, 12.5),
             (sign * 56.0, 11.0, -10.0),
             (sign * 44.0, 10.0, -22.4),
             (sign * 34.0, 10.0, -23.5)),
            .22, 1.5, colors["encoder"], collection)
        encoder["R17_Route_Status"] = (
            "fixed magnetic encoder feedback through rear outlet; "
            "sensor part, pinout and shielding unselected")
        created.extend((moving, service, main_head, motor, encoder))
    return created
