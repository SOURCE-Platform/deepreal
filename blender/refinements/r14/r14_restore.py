"""Recover selected concept hardware omitted from the R04 rebuild."""

import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MM = 0.001
SIDES = ("Face", "Interaction")
MOTION_SUFFIXES = (
    "Drum_Axle", "Bearing_Inner", "Bearing_Outer", "Ring_Gear",
    "Geared_Motor", "Motor_Pinion", "Motor_Bracket", "Encoder_Board",
    "Encoder_Magnet", "Rotation_Stop",
)
OPTICAL_SUFFIXES = (
    "Internal_Optical_Carrier", "IR_Depth_Module_Barrel",
    "IR_Depth_Module_Body", "RGB_Module_Barrel", "RGB_Module_Body",
    "SL_Projector_Body", "SL_Projector_DOE", "SL_Projector_Emitter",
    "SL_Projector_Bracket", "SL_Projector_Barrel_ProjA",
    "SL_Projector_Barrel_ProjB", "SL_Projector_Barrel_Pinhole",
)
ROTATING_MOTION_SUFFIXES = {
    "Drum_Axle", "Ring_Gear", "Encoder_Magnet",
}


def donor_names():
    return [side + "_" + suffix for side in SIDES
            for suffix in MOTION_SUFFIXES + OPTICAL_SUFFIXES]


def bounds(obj):
    return [(min((obj.matrix_world @ Vector(v))[i] for v in obj.bound_box),
             max((obj.matrix_world @ Vector(v))[i] for v in obj.bound_box))
            for i in range(3)]


def clamp_barrel_front(obj):
    # R13 already has exterior window/lens barrels. Retain only the inner
    # segment of the older tube to bridge that window to the module body.
    obj.data = obj.data.copy()
    for vertex in obj.data.vertices:
        vertex.co.y = max(vertex.co.y, -10.6 * MM)
    obj.data.update()
    obj["R14_Barrel_Trim"] = (
        "front trimmed at Y=-10.6 mm to avoid doubling R13 window barrel")


def shorten_axle(obj, side):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    changed = 0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        if (side == "Face" and world.x > 0) or (
                side == "Interaction" and world.x < 0):
            world.x = (-0.5 if side == "Face" else 0.5) * MM
            vertex.co = inverse @ world
            changed += 1
    assert changed > 0, obj.name
    obj.data.update()
    obj["R14_Axle_Trim"] = "inner end stops at own R13 drum face"


def restore(source_blend: Path, collections):
    names = donor_names()
    with bpy.data.libraries.load(str(source_blend), link=False) as (src, dst):
        missing = sorted(set(names) - set(src.objects))
        assert not missing, missing
        dst.objects = names
    restored = {}
    for obj in dst.objects:
        side = obj.name.split("_", 1)[0]
        suffix = obj.name[len(side) + 1:]
        optical = suffix in OPTICAL_SUFFIXES
        rotating = optical or suffix in ROTATING_MOTION_SUFFIXES
        target = collections[(side, "optical" if rotating else "motion")]
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        target.objects.link(obj)
        if "_Barrel" in suffix and optical:
            clamp_barrel_front(obj)
        shift = 2.0 if side == "Face" else -2.0
        transform = Matrix.Translation(Vector((shift * MM, 0, 0)))
        if optical and suffix == "Internal_Optical_Carrier":
            transform = Matrix.Translation(Vector((0, 1.0 * MM, 0))) @ transform
        if optical and side == "Interaction":
            axis_center = Vector((0, -1.5 * MM, 20 * MM))
            turn = (Matrix.Translation(axis_center)
                    @ Matrix.Rotation(math.radians(45), 4, "X")
                    @ Matrix.Translation(-axis_center))
            transform = turn @ transform
        obj.matrix_world = transform @ obj.matrix_world
        if suffix == "Bearing_Inner":
            offset = -1.6 if side == "Face" else 1.6
            obj.matrix_world = (Matrix.Translation(
                Vector((offset * MM, 0, 0))) @ obj.matrix_world)
        if suffix in {"Ring_Gear", "Geared_Motor", "Motor_Pinion",
                      "Motor_Bracket"}:
            # R13's solid barrel extends into the old drive's axial plane.
            # Seat the drive just beyond its outer flat face instead.
            outward = -2.44 if side == "Face" else 2.44
            rearward = 1.25 if suffix in {"Geared_Motor",
                                              "Motor_Pinion",
                                              "Motor_Bracket"} else 0.0
            obj.matrix_world = (Matrix.Translation(Vector(
                (outward * MM, rearward * MM, 0))) @ obj.matrix_world)
            obj["R14_Drive_Relocation"] = (
                "outer axial plane clears R13 drum shell; gear coupling "
                "and tooth engagement need mechanical design")
        if suffix == "Rotation_Stop":
            # Keep the legacy stop envelope while lifting it clear of the
            # revised housing wall. Its actual mount/stop face is open.
            obj.matrix_world = (Matrix.Translation(Vector(
                (0, 6.0 * MM, 4.0 * MM))) @ obj.matrix_world)
            obj["R14_Stop_Status"] = (
                "clearance-only location; stop geometry and mount unresolved")
        if suffix == "Drum_Axle":
            shorten_axle(obj, side)
        obj.hide_render = False
        obj.hide_set(False)
        obj["R14_Origin"] = "blender/deepreal.blend concept geometry"
        obj["R14_Assembly"] = side + (" rotating drum assembly" if rotating
                                        else " fixed drive/support hardware")
        obj["R14_Validation"] = (
            "geometry for assembly review; supplier, torque, bearing, fit "
            "and fabrication unverified")
        restored[obj.name] = obj
    return restored
