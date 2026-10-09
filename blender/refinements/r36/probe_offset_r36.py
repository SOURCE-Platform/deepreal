#!/usr/bin/env python3
"""Screen offset narrow tails against the unchanged R35 mechanisms."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "r08"))
from offset_flex_geometry import set_pose  # noqa: E402
from verify_r08 import tree  # noqa: E402

SOURCE = HERE.parent / "r35/deepreal-face-motion-study-r35.blend"
REPORT = HERE / "r36-offset-screen.json"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
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
    parts = {name: bpy.data.objects[name] for name in names}
    results = []
    for width in (6.0, 7.0):
        flex["R35_Width_mm"] = width
        for start in (-22.0, -12.0, -8.5):
            flex["R35_Moving_Anchor_X_mm"] = start
            flex["R35_Fixed_Anchor_X_mm"] = -2.2
            for offset in (0.0, 1.0, 2.0, 3.0):
                counts = {name: 0 for name in parts}
                for angle in range(-45, 46, 5):
                    pivot.rotation_euler.x = math.radians(angle)
                    set_pose(flex, angle, offset)
                    bpy.context.view_layer.update()
                    flex_tree = tree(flex)
                    for name, part in parts.items():
                        if flex_tree.overlap(tree(part)):
                            counts[name] += 1
                hits = {name: count for name, count in counts.items() if count}
                result = {"width_mm": width, "start_x_mm": start,
                          "end_x_mm": -2.2, "moving_offset_y_mm": offset,
                          "collision_pose_counts": hits,
                          "zero_hit_sweep": not hits}
                results.append(result)
                print("OFFSET", width, start, offset, "PASS", not hits, hits)
    REPORT.write_text(json.dumps({"source": str(SOURCE),
                                  "status": "GEOMETRY_SCREEN_ONLY",
                                  "candidates": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
