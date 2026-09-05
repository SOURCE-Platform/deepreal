"""Concept-level drum drive, support, sensing, and travel-stop hardware."""

from mathutils import Vector

from assembly_primitives import box, cylinder, material, tag, tube, wire


AXIS_Y = -1.5
AXIS_Z = 20.0


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
    gear_x = sign * 53.0
    motor_x = sign * 44.5
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
                9.8, 12.8, 3.2, mats["gear"], collection, segments=64)
    objects.append(tag(ring, "Drum drive", "CONCEPT GEAR ENVELOPE"))

    motor = cylinder("{}_Geared_Motor".format(label),
                     (motor_x, motor_y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                     4.2, 12.0, mats["motor"], collection)
    objects.append(tag(motor, "Drum drive", "REFERENCE GEARMOTOR"))
    pinion = cylinder("{}_Motor_Pinion".format(label),
                      (gear_x, motor_y, AXIS_Z), Vector((1.0, 0.0, 0.0)),
                      3.4, 3.2, mats["gear"], collection, segments=32)
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

    connector_x = -38.0 if sign < 0 else 39.0
    harness = wire("{}_Motor_Encoder_Harness".format(label), (
        (motor_x, 18.8, AXIS_Z),
        (sign * 37.0, 20.0, 10.0),
        (sign * 32.0, 18.0, 4.0),
        (connector_x, 16.2, 0.5),
    ), 0.45, mats["wire"], collection)
    objects.append(tag(harness, "Motor interconnect", "ROUTING CONCEPT"))
    return objects


def build(collection):
    mats = _materials()
    objects = []
    objects += _side(-1.0, "Face", mats, collection)
    objects += _side(1.0, "Interaction", mats, collection)
    return objects
