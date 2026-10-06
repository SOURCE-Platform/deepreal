"""Route neutral-pose head flex through each fixed outer end cap."""

import bpy

from assembly_primitives import routed_wire
from r14_assembly import rotated_point


def build():
    collection = bpy.data.collections[
        "07C — MOTOR + HEAD ROUTES — CONCEPT"]
    colors = {
        "optical": bpy.data.materials["R14_Head_Flex_Amber"],
        "motor": bpy.data.materials["R14_Motor_Power_Red"],
        "encoder": bpy.data.materials["R14_Encoder_Feedback_Yellow"],
    }
    created = []
    for side, sign in (("Face", -1), ("Interaction", 1)):
        for suffix in ("Head_Power_Data_Flex_ROUTE_CONCEPT",
                       "Motor_Power_Harness_ROUTE_CONCEPT",
                       "Encoder_Feedback_ROUTE_CONCEPT"):
            bpy.data.objects.remove(bpy.data.objects[side + "_" + suffix],
                                    do_unlink=True)
        if side == "Face":
            start = (-34, -5.4, 20)
            head_path = (start, (-41, -5.6, 22), (-48, -5.5, 24),
                         (-52, -5.3, 25), (-55.0, -5.3, 25),
                         (-57, -4.5, 25), (-57, 9.0, 18))
        else:
            start = rotated_point((34, -5.4, 20))
            head_path = (start, (41, -5.0, 17), (48, -5.3, 15),
                         (52, -5.3, 15), (55.0, -5.3, 15),
                         (57, -4.5, 15), (57, 9.0, 8))
        optical = routed_wire(
            side + "_Head_Power_Data_Flex_ROUTE_CONCEPT",
            head_path + ((sign * 56, 10, -10),
                         (sign * 45, 10, -22.5),
                         (sign * 22, 10.1, -23.5)),
            0.4, 1.8, colors["optical"], collection)
        optical["R15_Route_Status"] = (
            "neutral-pose visual path through fixed outer-cap slot to "
            "J2/J3 area; dynamic loop, flex bend and cable life unverified")
        motor = routed_wire(
            side + "_Motor_Power_Harness_ROUTE_CONCEPT",
            ((sign * 44.8, 4.8, 20), (sign * 49, 5.0, 22),
             (sign * 53, 4.8, 23.8), (sign * 55, 4.8, 23.8),
             (sign * 57, 10, 16), (sign * 56, 10, -10),
             (sign * 45, 10, -22.8), (sign * 34, 10, -23.5)),
            0.3, 1.5, colors["motor"], collection)
        motor["R15_Route_Status"] = (
            "fixed motor lead follows mount arm to J4/J5 envelope; "
            "connectors, strain relief and suppression unverified")
        encoder = routed_wire(
            side + "_Encoder_Feedback_ROUTE_CONCEPT",
            ((sign * 56.8, -1.5, 20), (sign * 57.2, 8, 12),
             (sign * 56, 11, -10), (sign * 44, 10, -22.4),
             (sign * 34, 10, -23.5)),
            0.24, 1.5, colors["encoder"], collection)
        encoder["R15_Route_Status"] = (
            "fixed encoder lead to J4/J5 envelope; nets and connector "
            "selection unverified")
        created.extend((optical, motor, encoder))
    return created
