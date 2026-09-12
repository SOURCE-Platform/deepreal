"""Concept-level drum drive, support, sensing, and travel-stop hardware."""

from mathutils import Vector

from assembly_primitives import (
    box, cylinder, material, routed_wire, tag, tube,
)


AXIS_Y = -1.5
AXIS_Z = 20.0
OUTER_GEAR_X = 54.8
RING_GEAR_WIDTH = 2.0
MOTOR_X = 47.0
MOTOR_LENGTH = 14.0


def _materials():
    return {
        "steel": material("Motion_Steel", (0.32, 0.34, 0.37),
                          metallic=0.92, roughness=0.28),
        "gear": material("Motion_Gear", (0.16, 0.18, 0.21),
                         metallic=0.78, roughness=0.36),
        "motor": material("Motion_Motor", (0.17, 0.19, 0.21),
                          metallic=0.70, roughness=0.32),
        "bearing": material("Motion_Bearing", (0.58, 0.60, 0.63),
                            metallic=0.98, roughness=0.20),
        "bracket": material("Motion_Bracket", (0.08, 0.09, 0.10),
                            metallic=0.72, roughness=0.42),
        "encoder": material("Motion_Encoder_PCBA", (0.03, 0.24, 0.09),
                            roughness=0.55),
        "magnet": material("Motion_Encoder_Magnet", (0.44, 0.10, 0.08),
                           metallic=0.55, roughness=0.38),
        "wire": material("Motion_Wiring", (0.72, 0.08, 0.035),
                         roughness=0.65),
    }


def _side(sign, label, mats, collection):
    objects = []
    drum_inner_x = sign * 1.0
    drum_outer_x = sign * 55.0
    # Keep the ring gear in the final 2 mm end band of the 54 mm drum.
    # The outer camera windows reach to X +/-52.38 mm; the former 3.2 mm
    # gear at X +/-53 mm overlapped those windows by about 1 mm.
    gear_x = sign * OUTER_GEAR_X
    motor_x = sign * MOTOR_X
    motor_y = 13.6

    shaft = cylinder("{}_Drum_Axle".format(label),
                     ((drum_inner_x + drum_outer_x) / 2.0, AXIS_Y, AXIS_Z),
                     Vector((sign, 0.0, 0.0)), 2.2,
                     abs(drum_outer_x - drum_inner_x), mats["steel"],
                     collection)
    objects.append(tag(shaft, "Drum support", "CONCEPT AXLE"))

    for suffix, x in (("Inner", sign * 2.2), ("Outer", sign * 54.2)):
        bearing = tube("{}_Bearing_{}".format(label, suffix),
                       (x, AXIS_Y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                       2.3, 4.2, 2.6, mats["bearing"], collection)
        objects.append(tag(bearing, "Drum support", "REFERENCE ENVELOPE"))

    ring = tube("{}_Ring_Gear".format(label),
                (gear_x, AXIS_Y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                9.8, 12.8, RING_GEAR_WIDTH, mats["gear"], collection,
                segments=64)
    objects.append(tag(ring, "Drum drive", "CONCEPT GEAR ENVELOPE"))

    motor = cylinder("{}_Geared_Motor".format(label),
                     (motor_x, motor_y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                     4.2, MOTOR_LENGTH, mats["motor"], collection)
    objects.append(tag(motor, "Drum drive", "REFERENCE GEARMOTOR"))
    pinion = cylinder("{}_Motor_Pinion".format(label),
                      (gear_x, motor_y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                      3.4, RING_GEAR_WIDTH, mats["gear"], collection,
                      segments=32)
    objects.append(tag(pinion, "Drum drive", "CONCEPT GEAR ENVELOPE"))

    bracket = box("{}_Motor_Bracket".format(label),
                  (motor_x, 18.0, AXIS_Z), (16.0, 1.6, 12.0), 1.0,
                  mats["bracket"], collection)
    objects.append(tag(bracket, "Drum drive", "CONCEPT BRACKET"))

    encoder_board_x = sign * 48.0
    encoder = box("{}_Encoder_Board".format(label),
                  (encoder_board_x, 7.0, AXIS_Z), (8.0, 1.0, 8.0), 0.5,
                  mats["encoder"], collection)
    objects.append(tag(encoder, "Position sensing", "AS5600-CLASS CONCEPT"))
    magnet = cylinder("{}_Encoder_Magnet".format(label),
                      (encoder_board_x, 5.8, AXIS_Z), Vector((0.0, 1.0, 0.0)),
                      2.5, 1.5, mats["magnet"], collection, segments=32)
    objects.append(tag(magnet, "Position sensing", "REFERENCE MAGNET"))

    stop = box("{}_Rotation_Stop".format(label),
               (sign * 56.0, 5.2, 7.0), (5.0, 4.0, 3.0), 0.6,
               mats["bracket"], collection)
    objects.append(tag(stop, "Travel limit", "150 DEG CONCEPT"))

    connector_x = -34.0 if sign < 0 else 34.0
    lane_x = sign * 54.0
    harness = routed_wire("{}_Motor_Encoder_Harness".format(label), (
        (sign * 40.0, motor_y, AXIS_Z),
        (sign * 46.0, 13.0, 15.0),
        (lane_x, 13.0, 10.0),
        (lane_x, 13.0, -10.0),
        (lane_x, 13.0, -25.0),
        (sign * 44.0, 13.0, -25.0),
        (sign * 40.0, 14.2, -24.2),
        (connector_x, 14.95, -24.2),
    ), 0.45, 3.0, mats["wire"], collection)
    harness["Cable_Lane"] = (
        "Face_Power_Motion_Lane" if sign < 0
        else "Interaction_Power_Motion_Lane")
    harness["Physical_Intent"] = (
        "Tightly coupled supply and return with motor suppression provision")
    objects.append(tag(harness, "Motor interconnect", "ROUTING CONCEPT"))
    return objects


def build(collection):
    mats = _materials()
    objects = []
    objects += _side(-1.0, "Face", mats, collection)
    objects += _side(1.0, "Interaction", mats, collection)
    return objects
