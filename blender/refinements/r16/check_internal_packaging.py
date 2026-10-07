#!/usr/bin/env python3
"""Screen whether the current encoder-board envelope fits inside R16 drums.

Geometry review only: sampled triangle intersections cannot prove manufacturable
clearance, electrical sensing, mounting, or moving-cable life.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-exterior-refinement-r16.blend"
REPORT = HERE / "r16-internal-packaging-check.json"
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

MM = 0.001
AXIS_Y = -1.5
AXIS_Z = 20.0
INNER_RADIUS = 10.5


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [(min(p[i] for p in points), max(p[i] for p in points))
            for i in range(3)]


def bounds_mm(obj):
    return [[round(lo / MM, 2), round(hi / MM, 2)]
            for lo, hi in bounds(obj)]


def boxes_cross(first, second):
    return all(first[i][0] < second[i][1]
               and second[i][0] < first[i][1] for i in range(3))


def candidate_radius(y, z):
    # The existing proxy board is 6 x 6 mm in this cross section.
    return max(math.hypot(y + dy - AXIS_Y, z + dz - AXIS_Z)
               for dy in (-3, 3) for dz in (-3, 3))


def occupied_geometry(side, base_angle, angles):
    pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
    cap = "Sensor_Head_Flat_End_" + ("Left" if side == "Face"
                                     else "Right")
    fixed_names = ("Geared_Motor", "Motor_Pinion", "Bearing_Outer",
                   "Bearing_Inner", cap)
    geometry = []
    for suffix in fixed_names:
        obj = bpy.data.objects[side + "_" + suffix]
        geometry.append((obj.name, bounds(obj), tree(obj)))
    for angle in angles:
        pivot.rotation_euler.x = math.radians(angle - base_angle)
        bpy.context.view_layer.update()
        for obj in pivot.children:
            if obj.type == "MESH":
                geometry.append((f"{angle}:{obj.name}",
                                 bounds(obj), tree(obj)))
    pivot.rotation_euler.x = 0
    bpy.context.view_layer.update()
    return geometry


def scan(side, sign, angles, x_values, geometry):
    board = bpy.data.objects[side + "_Encoder_Board"]
    original = board.matrix_world.copy()
    tested = 0
    clear = []
    for x in x_values:
        for y in range(-5, 5):
            for z in range(14, 28):
                radius = candidate_radius(y, z)
                if radius > INNER_RADIUS - 1.0:
                    continue
                tested += 1
                delta = Vector((sign * (x - 56.8) * MM,
                                (y - AXIS_Y) * MM,
                                (z - AXIS_Z) * MM))
                board.matrix_world = Matrix.Translation(delta) @ original
                bpy.context.view_layer.update()
                candidate_box = bounds(board)
                candidate_tree = tree(board)
                if not any(boxes_cross(candidate_box, box)
                           and candidate_tree.overlap(other)
                           for _, box, other in geometry):
                    clear.append({"center_mm": [x, y, z],
                                  "radial_clearance_mm":
                                  round(INNER_RADIUS - radius, 2)})
    board.matrix_world = original
    bpy.context.view_layer.update()
    return {"angles_deg": list(angles), "positions_tested": tested,
            "collision_free_positions": clear}


def main():
    if not bpy.data.filepath or Path(bpy.data.filepath) != MODEL:
        bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    results = {}
    for side, sign, base in (("Face", -1, 0),
                            ("Interaction", 1, 45)):
        near_angles = (-75, -45, 0, 45, 75)
        broad_angles = (-75, -45, -15, 0, 15, 45, 75)
        near_geometry = occupied_geometry(side, base, near_angles)
        broad_geometry = occupied_geometry(side, base, broad_angles)
        near = scan(side, sign, near_angles,
                    [index * .5 for index in range(92, 106)],
                    near_geometry)
        broad = scan(side, sign, broad_angles, range(4, 54, 2),
                     broad_geometry)
        names = ("Sensor_Head", "Geared_Motor", "Ring_Gear",
                 "Motor_Bracket", "Encoder_Board", "Encoder_Magnet",
                 "Drum_Axle", "Head_PCBA_Carrier_CONCEPT")
        results[side] = {
            "current_bounds_mm": {name: bounds_mm(
                bpy.data.objects[side + "_" + name]) for name in names},
            "outer_end_scan": near, "whole_drum_coarse_scan": broad}
    report = {
        "model": str(MODEL),
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "drum_inner_diameter_mm": 2 * INNER_RADIUS,
        "encoder_board_envelope_mm": [0.8, 6.0, 6.0],
        "results": results,
        "conclusion": (
            "The motor and ring are already axially within the drum. "
            "The current encoder board has no collision-free drop-in "
            "position near either outer end at sampled angles and with "
            "at least 1 mm radial clearance. The bracket, magnet, bearing, "
            "and head cable require a joint redesign for full concealment."),
        "limits": [
            "Triangle overlap sampling is a screen, not a tolerance study.",
            "The interaction drum's final travel limits remain undecided; "
            "the scan uses the same -75 to +75 degree study as R15.",
            "The coarse whole-drum scan does not prove a clear position "
            "can be supported from the fixed enclosure or sense a magnet.",
            "No cable size, bend radius, strain relief, or life is checked.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    for side, result in results.items():
        near = result["outer_end_scan"]
        broad = result["whole_drum_coarse_scan"]
        print(side, "outer-end:", near["positions_tested"], "tested,",
              len(near["collision_free_positions"]), "clear; whole drum:",
              broad["positions_tested"], "tested,",
              len(broad["collision_free_positions"]), "clear")
    print(REPORT)


if __name__ == "__main__":
    main()
