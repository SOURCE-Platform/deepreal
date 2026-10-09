#!/usr/bin/env python3
"""Sample the R21 side supports and motor envelopes at proposed travel poses."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-side-supported-drums-r21.blend"
REPORT = HERE / "r21-clearance-check.json"


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(point[i] for point in points),
             max(point[i] for point in points)] for i in range(3)]


def triangle_pairs(a, b):
    return len(tree(a).overlap(tree(b)))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    fixed_names = ("R21_Lower_Housing_And_Rear_Spine",
                   "R21_Support_Left_Outer", "R21_Support_Center",
                   "R21_Support_Right_Outer", "R21_Center_Gap_Fairing")
    for side in ("Face", "Interaction"):
        fixed_names += tuple(
            side + "_Inner_Race_" + position + "_" + part + "_R21"
            for position in ("Upper", "Lower")
            for part in ("Web", "Tab"))
        fixed_names += tuple(side + "_" + suffix for suffix in (
            "Inner_Bearing_Fixed_Race_ENV_R21",
            "Outer_Hollow_Fixed_Spindle_ENV_R21",
            "Outer_Bearing_ENV_R21",
            "Center_Fed_Motor_Stator_ENV_R21",
            "Motor_Cantilever_R21",
            "End_Encoder_PCB_ENV_R21",
            "End_Encoder_IC_ENV_R21"))
    fixed = {name: bpy.data.objects[name] for name in fixed_names}
    travel = {}
    for side, base, poses in (("Face", 0, (-45, 0, 45)),
                              ("Interaction", 45, (0, 22.5, 45))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        moving_names = ("Sensor_Head", "Flat_Outer_End_R21",
                        "Open_Inner_End_Ring_R21",
                        "Inner_Bearing_Rotating_Race_ENV_R21",
                        "Outer_Rotating_Hub_R21", "End_Encoder_Magnet_R21",
                        "Internal_Ring_Gear_ENV_R21")
        for optical_angle in poses:
            pivot.rotation_euler.x = math.radians(optical_angle - base)
            bpy.context.view_layer.update()
            overlaps = {}
            for suffix in moving_names:
                obj = bpy.data.objects[side + "_" + suffix]
                hits = {name: triangle_pairs(obj, part)
                        for name, part in fixed.items()}
                overlaps[obj.name] = {name: count for name, count in hits.items()
                                      if count}
            travel[f"{side}_{optical_angle:+g}"] = overlaps
        pivot.rotation_euler.x = 0
    bpy.context.view_layer.update()

    packaging = {}
    for side in ("Face", "Interaction"):
        motor = bpy.data.objects[side + "_Center_Fed_Motor_Stator_ENV_R21"]
        neighbors = ("Internal_Optical_Carrier",
                     "Head_PCBA_Carrier_CONCEPT", "IR_Depth_Module_Body",
                     "SL_Projector_Body")
        if side == "Face":
            neighbors += ("RGB_Module_Body",)
        packaging[side] = {
            name: triangle_pairs(motor, bpy.data.objects[side + "_" + name])
            for name in neighbors}
    lens = bpy.data.objects[
        "Interaction_RGB_Wide_Lens_6p95mm_ENVELOPE_R20"]
    board = bpy.data.objects[
        "Interaction_RGB_Wide_Assembly_10p8mm_ENVELOPE_R20"]
    optical_carrier = bpy.data.objects["Interaction_Internal_Optical_Carrier"]
    packaging["wide_rgb_vs_old_carrier"] = {
        "lens": triangle_pairs(lens, optical_carrier),
        "assembly": triangle_pairs(board, optical_carrier),
    }

    face_bounds = world_bounds(bpy.data.objects["Face_Sensor_Head"])
    interaction_bounds = world_bounds(
        bpy.data.objects["Interaction_Sensor_Head"])
    gap_mm = round((interaction_bounds[0][0] - face_bounds[0][1]) * 1000, 3)
    report = {
        "model": str(MODEL), "drum_shell_end_gap_mm": gap_mm,
        "fixed_housing_and_support_triangle_overlaps_by_pose": travel,
        "motor_and_optical_proxy_triangle_overlaps": packaging,
        "limits": [
            "Triangle intersections only; minimum tolerance clearances are not certified.",
            "Bearing races, teeth, moving flex, stop tabs and mounts are envelopes.",
            "The RGB window and optical carrier still require redesign for the wide assembly.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print("R21 CLEARANCE", REPORT)
    print("R21 DRUM GAP MM", gap_mm)
    print("R21 POSE OVERLAPS", {key: value for key, value in travel.items()
                                 if any(value.values())})
    print("R21 PACKAGING", packaging)


if __name__ == "__main__":
    main()
