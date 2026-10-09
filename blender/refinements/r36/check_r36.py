#!/usr/bin/env python3
"""Check side bearing supports and the straight full-width exit at face poses."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-inner-bearing-window-r36.blend"
REPORT = HERE / "r36-support-check.json"


def hits(first, second):
    return len(tree(first).overlap(tree(second)))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    flex = bpy.data.objects["R36_Face_Full_Width_Straight_Exit_ENV"]
    bearing = bpy.data.objects["Face_Inner_Bearing_Fixed_Race_ENV_R21"]
    neck = bpy.data.objects["R36_Face_Fixed_Bearing_Axial_Neck_ENV"]
    moving_race = bpy.data.objects["Face_Inner_Bearing_Rotating_Race_ENV_R21"]
    housing = bpy.data.objects["R30_One_Piece_Enclosure"]
    supports = {side: bpy.data.objects[
        "R36_Face_Inner_Race_" + side + "_Side_Web_ENV"]
        for side in ("Rear", "Front")}
    obstacle_names = (
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "R36_Face_Fixed_Bearing_Axial_Neck_ENV",
        "Face_Inner_Bearing_Rotating_Race_ENV_R21",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
        "Face_Motor_Cantilever_R21",
        "R30_One_Piece_Enclosure",
        "Face_Sensor_Head",
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Internal_Optical_Carrier",
        "Face_RGB_Module_Body",
    ) + tuple(web.name for web in supports.values())
    obstacles = {name: bpy.data.objects[name] for name in obstacle_names}
    poses = {}
    support_poses = {}
    for angle in range(-45, 46, 5):
        pivot.rotation_euler.x = math.radians(angle)
        bpy.context.view_layer.update()
        poses[str(angle)] = {name: hits(flex, part)
                             for name, part in obstacles.items()}
        support_poses[str(angle)] = {
            side: {"moving_race": hits(web, moving_race),
                   "rotating_inner_ring": hits(web, bpy.data.objects[
                       "Face_Open_Inner_End_Ring_R21"]),
                   "drum_shell": hits(web, bpy.data.objects[
                       "Face_Sensor_Head"])}
            for side, web in supports.items()}
        support_poses[str(angle)]["Neck"] = {
            "moving_race": hits(neck, moving_race),
            "rotating_inner_ring": hits(neck, bpy.data.objects[
                "Face_Open_Inner_End_Ring_R21"]),
            "drum_shell": hits(neck, bpy.data.objects["Face_Sensor_Head"]),
        }
    pivot.rotation_euler.x = 0
    bpy.context.view_layer.update()
    fixed_contacts = {side: {"axial_neck": hits(web, neck),
                             "housing": hits(web, housing)}
                      for side, web in supports.items()}
    neck_to_bearing = hits(neck, bearing)
    result = {
        "model": str(MODEL),
        "full_width_flex_mm": flex["R36_Width_mm"],
        "support_fixed_contact_triangle_hits": fixed_contacts,
        "neck_to_fixed_bearing_triangle_hits": neck_to_bearing,
        "support_vs_rotating_parts_at_5_degree_poses": support_poses,
        "straight_flex_triangle_hits_at_5_degree_poses": poses,
        "support_to_bearing_and_housing_contact": (
            neck_to_bearing > 0 and all(
                row["axial_neck"] > 0 and row["housing"] > 0
                for row in fixed_contacts.values())),
        "support_vs_rotating_parts_clear": not any(
            count for pose in support_poses.values()
            for row in pose.values() for count in row.values()),
        "straight_flex_clear": not any(
            count for pose in poses.values() for count in pose.values()),
        "limits": [
            "This is a straight rotating strip; no deforming service loop or fixed terminal is modeled.",
            "Triangle contacts at the side webs are only an intended attachment envelope.",
            "Fastening, bearing load and tolerance are not assessed.",
        ],
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R36 FIXED SUPPORT CONTACTS", fixed_contacts)
    print("R36 SUPPORT ROTATING CLEAR", result["support_vs_rotating_parts_clear"])
    print("R36 STRAIGHT FLEX CLEAR", result["straight_flex_clear"])
    print("R36 SUPPORT COLLISIONS", {
        angle: row for angle, row in support_poses.items()
        if any(value for part in row.values() for value in part.values())})
    print("R36 FLEX COLLISION PARTS", {name: sum(pose[name] > 0 for pose in poses.values())
                                       for name in obstacles
                                       if any(pose[name] > 0 for pose in poses.values())})


if __name__ == "__main__":
    main()
