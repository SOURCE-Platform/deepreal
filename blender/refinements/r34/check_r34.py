#!/usr/bin/env python3
"""Measure centered encoder and straight inner-flex clearance in R34."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
for path in (HERE.parents[1], HERE.parent / "r08",
             HERE.parent / "r21", HERE.parent / "r24"):
    sys.path.insert(0, str(path))

from check_r24 import topology  # noqa: E402
from r21_mechanism import AXIS, INNER_BEARING_BORE_RADIUS_MM  # noqa: E402
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-face-interface-study-r34.blend"
REPORT = HERE / "r34-interface-check.json"
MM = 1000.0


def world_bounds_mm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(point[i] for point in points) * MM,
             max(point[i] for point in points) * MM] for i in range(3)]


def center(box):
    return [(low + high) / 2 for low, high in box]


def triangle_hits(first, second):
    return len(tree(first).overlap(tree(second)))


def flex_radius_mm(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return max(math.hypot(point.y * MM - AXIS[0],
                          point.z * MM - AXIS[1]) for point in points)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    magnet = bpy.data.objects["R34_Face_Axial_Magnet_ENV"]
    sensor = bpy.data.objects["R34_Face_Axial_Sensor_IC_ENV"]
    board = bpy.data.objects["R34_Face_Axial_Sensor_PCB_ENV"]
    flex = bpy.data.objects["R34_Face_Inner_Flex_Width_ENV"]
    bearing = bpy.data.objects["Face_Inner_Bearing_Fixed_Race_ENV_R21"]
    motor = bpy.data.objects["Face_Center_Fed_Motor_Stator_ENV_R21"]
    bracket = bpy.data.objects["Face_Motor_Cantilever_R21"]
    housing = bpy.data.objects["R30_One_Piece_Enclosure"]
    drum = bpy.data.objects["Face_Sensor_Head"]
    outer_bearing = bpy.data.objects["R34_Face_Outer_Bearing_ENV"]
    shaft = bpy.data.objects["R34_Face_Outer_Rotating_Shaft_ENV"]

    bpy.context.view_layer.update()
    magnet_box = world_bounds_mm(magnet)
    sensor_box = world_bounds_mm(sensor)
    magnet_center = center(magnet_box)
    sensor_center = center(sensor_box)
    gap_mm = magnet_box[0][0] - sensor_box[0][1]
    assert abs(magnet_center[1] - AXIS[0]) < .01
    assert abs(magnet_center[2] - AXIS[1]) < .01
    assert abs(sensor_center[1] - AXIS[0]) < .01
    assert abs(sensor_center[2] - AXIS[1]) < .01
    assert .5 <= gap_mm <= 3.0

    fixed = {"inner_bearing": bearing, "motor": motor,
             "motor_bracket": bracket, "housing": housing,
             "drum_shell": drum}
    poses = {}
    saved_angle = pivot.rotation_euler.x
    maximum_flex_radius = 0.0
    for angle in range(-45, 46, 5):
        pivot.rotation_euler.x = math.radians(angle)
        bpy.context.view_layer.update()
        maximum_flex_radius = max(maximum_flex_radius, flex_radius_mm(flex))
        poses[str(angle)] = {name: triangle_hits(flex, part)
                             for name, part in fixed.items()}
    pivot.rotation_euler.x = saved_angle
    bpy.context.view_layer.update()
    passage_margin = INNER_BEARING_BORE_RADIUS_MM - maximum_flex_radius

    static_hits = {
        "sensor_board_vs_housing": triangle_hits(board, housing),
        "sensor_ic_vs_housing": triangle_hits(sensor, housing),
        "magnet_vs_housing": triangle_hits(magnet, housing),
        "rotating_shaft_vs_fixed_bearing": triangle_hits(shaft, outer_bearing),
    }
    payload_names = (
        "Face_Head_PCBA_Carrier_CONCEPT",
        "Face_Internal_Optical_Carrier",
        "Face_IR_Depth_Module_Body",
        "Face_RGB_Module_Body",
        "Face_SL_Projector_Body",
        "Face_Inner_Bearing_Rotating_Race_ENV_R21",
    )
    payload_hits = {
        name: triangle_hits(flex, bpy.data.objects[name])
        for name in payload_names
    }
    face_topology = topology(drum)
    housing_topology = topology(housing)
    result = {
        "model": str(MODEL),
        "face_drum_axis_yz_mm": list(AXIS),
        "magnet_center_xyz_mm": magnet_center,
        "sensor_package_center_proxy_xyz_mm": sensor_center,
        "magnet_to_sensor_axial_surface_gap_mm": gap_mm,
        "flex_width_mm": flex["R34_Width_mm"],
        "flex_max_corner_radius_from_drum_axis_mm": maximum_flex_radius,
        "inner_fixed_bearing_opening_radius_mm": INNER_BEARING_BORE_RADIUS_MM,
        "nominal_straight_passage_radial_margin_mm": passage_margin,
        "flex_triangle_hits_at_5_degree_poses": poses,
        "other_triangle_hits": static_hits,
        "flex_vs_rotating_payload_triangle_hits_at_zero": payload_hits,
        "drum_shell_topology": face_topology,
        "housing_topology": housing_topology,
        "straight_envelope_pass": (
            passage_margin > 0 and
            not any(count for pose in poses.values() for count in pose.values()) and
            not any(static_hits.values()) and
            not any(payload_hits.values()) and
            face_topology["non_manifold_edges"] == 0 and
            housing_topology["non_manifold_edges"] == 0),
        "limits": [
            "This checks a rigid straight strip only, not a deforming flex service loop.",
            "Triangle intersection counts do not establish assembly, tolerances or bend life.",
            "The axial magnet and sensor board are concept envelopes; field strength and Hall-array datum are unverified.",
            "The outer cheek pocket leaves a thin skin; wall thickness and fastening are not approved.",
            "The outer rotating shaft has no modeled structural connection to the rotating hub.",
            "Only the face drum was redesigned; the interaction drum remains R30/R21.",
        ],
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R34 AXIAL GAP MM", round(gap_mm, 3))
    print("R34 STRAIGHT PASSAGE MARGIN MM", round(passage_margin, 3))
    print("R34 STATIC HITS", static_hits)
    print("R34 PAYLOAD HITS", payload_hits)
    print("R34 POSE HITS", {angle: hits for angle, hits in poses.items()
                              if any(hits.values())})
    print("R34 STRAIGHT ENVELOPE PASS", result["straight_envelope_pass"])


if __name__ == "__main__":
    main()
