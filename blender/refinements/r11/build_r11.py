#!/usr/bin/env python3
"""Align visible optics with the angled drum bores and close drum ends."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO / "blender") not in sys.path:
    sys.path.insert(0, str(REPO / "blender"))

import macbook  # noqa: E402

MM = 0.001
SOURCE = HERE.parent / "r10" / "deepreal-exterior-refinement-r10.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r11.blend"
DRUMS = ("Face_Sensor_Head", "Interaction_Sensor_Head")
AXIS_YZ = (-1.5 * MM, 20.0 * MM)


def rotate_interaction_optics():
    # R04 retained only lens meshes and removed their rotated parent pivot.
    # The bores were already baked at +45 degrees; their visible lens meshes
    # reverted to the forward-facing rest orientation when that pivot died.
    center = Vector((0, AXIS_YZ[0], AXIS_YZ[1]))
    turn = (Matrix.Translation(center)
            @ Matrix.Rotation(math.radians(45), 4, "X")
            @ Matrix.Translation(-center))
    lenses = [obj for obj in bpy.data.objects
              if obj.name.startswith("Interaction_Drum_Lens_")
              and obj.type == "MESH"]
    assert len(lenses) >= 10, f"expected interaction lens assembly, got {len(lenses)}"
    for obj in lenses:
        assert obj.parent is None, f"unexpected parent on {obj.name}"
        obj.matrix_world = turn @ obj.matrix_world
        obj["R11_Optical_Axis"] = (
            "45 degree downward presentation alignment to baked drum bores")
    return len(lenses)


def drum_end_caps():
    material = bpy.data.materials["Device_Sensor_Drum"]
    created = []
    for name in DRUMS:
        drum = bpy.data.objects[name]
        collection = drum.users_collection[0]
        x_min = min((drum.matrix_world @ Vector(c)).x for c in drum.bound_box)
        x_max = max((drum.matrix_world @ Vector(c)).x for c in drum.bound_box)
        for side, x in (("Left", x_min + 0.75 * MM),
                        ("Right", x_max - 0.75 * MM)):
            cap = macbook.cylinder(
                name + "_Closed_End_" + side,
                Vector((x, AXIS_YZ[0], AXIS_YZ[1])),
                macbook.X, 10.52 * MM, 1.5 * MM, material, seg=96)
            collection.objects.link(cap)
            cap["R11_Status"] = (
                "concept end closure for visual review; bearings, fasteners, "
                "rotation support, tolerances and sealing unresolved")
            cap["R11_Drum"] = name
            created.append(cap.name)
    return created


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    count = rotate_interaction_optics()
    caps = drum_end_caps()
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R11"
    scene["DeepReal_Status"] = (
        "optical alignment and closed-end visual study; "
        "engineering readiness BLOCKED")
    scene["R11_Visible_Lenses_Rotated"] = count
    scene["R11_End_Caps"] = len(caps)
    scene["R11_Limits"] = (
        "presentation geometry only; optical calibration, mechanical drum "
        "support, sealing and USB/PCB engineering not validated")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R11 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
