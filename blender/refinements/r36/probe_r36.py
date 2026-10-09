#!/usr/bin/env python3
"""Screen narrower trunk widths before changing the R35 housing model."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r35"))
from check_r35 import scan_candidate  # noqa: E402

SOURCE = HERE.parent / "r35/deepreal-face-motion-study-r35.blend"
REPORT = HERE / "r36-width-screen.json"


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
    obstacles = {name: bpy.data.objects[name] for name in names}
    results = []
    for width in (6.0, 6.5, 7.0, 7.5, 8.0):
        flex["R35_Width_mm"] = width
        for x in (-22.0, -12.0, -8.5):
            result = scan_candidate(flex, pivot, x, -2.2, obstacles)
            results.append({
                "trunk_width_mm": width,
                "moving_anchor_x_mm": x,
                "fixed_anchor_x_mm": -2.2,
                "collision_angles_by_part_deg":
                    result["collision_angles_by_part_deg"],
                "zero_hit_sweep": result["zero_hit_sweep"],
            })
            print("WIDTH", width, "START", x,
                  "PASS", result["zero_hit_sweep"],
                  "HITS", {key: len(value) for key, value in
                           result["collision_angles_by_part_deg"].items()})
    REPORT.write_text(json.dumps({"source": str(SOURCE),
                                  "status": "GEOMETRY_SCREEN_ONLY",
                                  "candidates": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
