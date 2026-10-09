#!/usr/bin/env python3
"""Check moving drum surfaces and optics against the fixed R22 canopy."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-curved-drum-canopy-r22.blend"
REPORT = HERE / "r22-canopy-clearance.json"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    roof = [obj for obj in bpy.data.objects if obj.name.startswith("R22_")
            and obj.type == "MESH"]
    results = {}
    for side, base, poses in (("Face", 0, (-45, 0, 45)),
                              ("Interaction", 45, (0, 22.5, 45))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        moving = [bpy.data.objects[side + "_" + suffix] for suffix in (
            "Sensor_Head", "Open_Inner_End_Ring_R21",
            "Flat_Outer_End_R21")]
        moving.extend(obj for obj in bpy.data.objects
                      if obj.name.startswith(side + "_Drum_Lens_")
                      and obj.type == "MESH")
        for direction in poses:
            pivot.rotation_euler.x = math.radians(direction - base)
            bpy.context.view_layer.update()
            clashes = {}
            for part in moving:
                counts = {cover.name: len(tree(part).overlap(tree(cover)))
                          for cover in roof}
                counts = {name: count for name, count in counts.items() if count}
                if counts:
                    clashes[part.name] = counts
            results[f"{side}_{direction:+g}_deg"] = clashes
        pivot.rotation_euler.x = 0
    report = {
        "model": str(MODEL),
        "canopy_to_nominal_drum_radial_gap_mm": 1.0,
        "moving_part_triangle_overlaps_by_pose": results,
        "status": "sampled visual geometry only; minimum tolerance and optical ray envelopes unverified",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print("R22 CLEARANCE", REPORT)
    print("R22 OVERLAPS", {pose: clashes for pose, clashes in results.items()
                           if clashes})


if __name__ == "__main__":
    main()
