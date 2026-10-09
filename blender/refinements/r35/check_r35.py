#!/usr/bin/env python3
"""Sweep R35 torsion candidates and check the outer rotating load path."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "r08"))

from flex_geometry import set_pose  # noqa: E402
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-face-motion-study-r35.blend"
REPORT = HERE / "r35-motion-check.json"


def triangle_hits(first, second):
    return len(tree(first).overlap(tree(second)))


def world_bounds_mm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[round(min(point[i] for point in points) * 1000, 3),
             round(max(point[i] for point in points) * 1000, 3)]
            for i in range(3)]


def scan_candidate(flex, pivot, moving_x, fixed_x, objects):
    flex["R35_Moving_Anchor_X_mm"] = moving_x
    flex["R35_Fixed_Anchor_X_mm"] = fixed_x
    poses = {}
    for angle in range(-45, 46, 5):
        pivot.rotation_euler.x = math.radians(angle)
        set_pose(flex, angle)
        bpy.context.view_layer.update()
        poses[str(angle)] = {
            name: triangle_hits(flex, part)
            for name, part in objects.items()
        }
    hits = {name: [int(angle) for angle, row in poses.items()
                   if row[name] > 0] for name in objects}
    return {"moving_anchor_x_mm": moving_x,
            "fixed_anchor_x_mm": fixed_x,
            "pose_triangle_hits": poses,
            "collision_angles_by_part_deg": {key: value for key, value
                                             in hits.items() if value},
            "zero_hit_sweep": not any(hits.values())}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    flex = bpy.data.objects["R35_Face_Full_Width_Torsion_Candidate_ENV"]
    names = (
        "R30_One_Piece_Enclosure",
        "Face_Inner_Bearing_Fixed_Race_ENV_R21",
        "Face_Inner_Race_Upper_Web_R21",
        "Face_Inner_Race_Lower_Web_R21",
        "Face_Inner_Race_Upper_Tab_R21",
        "Face_Inner_Race_Lower_Tab_R21",
        "Face_Center_Fed_Motor_Stator_ENV_R21",
        "Face_Motor_Cantilever_R21",
        "Face_Sensor_Head",
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Internal_Optical_Carrier",
        "Face_IR_Depth_Module_Body",
        "Face_RGB_Module_Body",
        "Face_SL_Projector_Body",
        "Face_Inner_Bearing_Rotating_Race_ENV_R21",
    )
    obstacles = {name: bpy.data.objects[name] for name in names}
    candidates = [scan_candidate(flex, pivot, x, end, obstacles)
                  for end in (-2.2, -1.2)
                  for x in (-22.0, -12.0, -8.5, -5.5)]

    pivot.rotation_euler.x = 0
    flex["R35_Moving_Anchor_X_mm"] = -22.0
    flex["R35_Fixed_Anchor_X_mm"] = -1.2
    set_pose(flex, 0)
    bpy.context.view_layer.update()
    shaft = bpy.data.objects["R35_Face_Outer_Shaft_ENV"]
    hub = bpy.data.objects["R35_Face_Outer_Hub_ENV"]
    web = bpy.data.objects["R35_Face_Outer_Coupling_Web_ENV"]
    sleeve = bpy.data.objects["R35_Face_Outer_Drum_Wall_Sleeve_ENV"]
    drum = bpy.data.objects["Face_Sensor_Head"]
    bearing = bpy.data.objects["R34_Face_Outer_Bearing_ENV"]
    housing = bpy.data.objects["R30_One_Piece_Enclosure"]
    outer = {
        "shaft_vs_fixed_bearing": triangle_hits(shaft, bearing),
        "web_vs_fixed_bearing": triangle_hits(web, bearing),
        "sleeve_vs_fixed_bearing": triangle_hits(sleeve, bearing),
        "web_vs_housing": triangle_hits(web, housing),
        "sleeve_vs_housing": triangle_hits(sleeve, housing),
        "web_vs_rotating_drum_shell_intended_contact": triangle_hits(web, drum),
        "sleeve_vs_rotating_drum_shell_intended_contact": triangle_hits(sleeve, drum),
        "web_vs_rotating_hub_intended_contact": triangle_hits(web, hub),
        "web_vs_rotating_shaft_intended_contact": triangle_hits(web, shaft),
    }
    result = {
        "model": str(MODEL),
        "candidate_flex_width_mm": flex["R35_Width_mm"],
        "candidate_flex_thickness_mm": flex["R35_Thickness_mm"],
        "candidate_routes": candidates,
        "outer_load_path": outer,
        "outer_part_bounds_xyz_mm": {
            name: world_bounds_mm(obj) for name, obj in
            (("shaft", shaft), ("hub", hub), ("web", web),
             ("sleeve", sleeve), ("fixed_bearing", bearing))},
        "outer_fixed_clearance_pass": not any(outer[key] for key in (
            "shaft_vs_fixed_bearing", "web_vs_fixed_bearing",
            "sleeve_vs_fixed_bearing", "web_vs_housing",
            "sleeve_vs_housing")),
        "outer_contact_path_present": all(outer[key] > 0 for key in (
            "web_vs_rotating_drum_shell_intended_contact",
            "sleeve_vs_rotating_drum_shell_intended_contact",
            "web_vs_rotating_hub_intended_contact",
            "web_vs_rotating_shaft_intended_contact")),
        "any_zero_hit_flex_route": any(c["zero_hit_sweep"] for c in candidates),
        "limits": [
            "The ribbon is a simple straight-axis twist candidate, not an engineered service loop.",
            "Triangle intersections are geometric checks, not tolerance, copper strain or fatigue proof.",
            "Overlaps between rotating web, hub, shaft, sleeve and drum are intended connection regions, not specified joints.",
            "The outer cheek pocket and magnet mounting remain unresolved.",
        ],
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R35 OUTER FIXED CLEARANCE", result["outer_fixed_clearance_pass"])
    print("R35 OUTER CONTACT PATH", result["outer_contact_path_present"])
    print("R35 OUTER CONTACT HITS", outer)
    for candidate in candidates:
        print("R35 FLEX", candidate["moving_anchor_x_mm"],
              "TO", candidate["fixed_anchor_x_mm"],
              "ZERO-HIT", candidate["zero_hit_sweep"],
              "COLLISION PARTS", {
                  key: len(angles) for key, angles in
                  candidate["collision_angles_by_part_deg"].items()})


if __name__ == "__main__":
    main()
