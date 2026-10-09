#!/usr/bin/env python3
"""Check the connected shell and sampled drum clearances."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
sys.path.insert(0, str(HERE.parent / "r08"))
sys.path.insert(0, str(HERE.parent / "r26"))
from check_r24 import topology  # noqa: E402
from verify_r08 import tree  # noqa: E402
from build_r26 import (DRUM_CENTER_Y_MM, DRUM_CENTER_Z_MM,
                       DRUM_RADIUS_MM, RUNNING_CLEARANCE_MM,
                       CURVE_END_Y_MM, TIP_Y_MM, inner_arc_height)  # noqa: E402

MODEL = HERE / "deepreal-circular-divider-enclosure-r29.blend"
REPORT = HERE / "r29-enclosure-check.json"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    shell = bpy.data.objects["R29_One_Piece_Enclosure"]
    shell_topology = topology(shell)
    shell_tree = tree(shell)
    poses = {}
    for side, base, directions in (("Face", 0, (-45, 0, 45)),
                                   ("Interaction", 45, (0, 22.5, 45))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        saved_rotation = pivot.rotation_euler.x
        moving = [bpy.data.objects[side + "_" + suffix] for suffix in (
            "Sensor_Head", "Open_Inner_End_Ring_R21",
            "Flat_Outer_End_R21")]
        moving += [obj for obj in bpy.data.objects
                   if obj.name.startswith(side + "_Drum_Lens_")
                   and obj.type == "MESH"]
        for direction in directions:
            pivot.rotation_euler.x = math.radians(direction - base)
            bpy.context.view_layer.update()
            hits = {obj.name: len(tree(obj).overlap(shell_tree))
                    for obj in moving}
            poses[f"{side}_{direction:+g}_deg"] = {
                name: count for name, count in hits.items() if count}
        pivot.rotation_euler.x = saved_rotation
    radial_gaps = []
    for i in range(65):
        y = TIP_Y_MM + (CURVE_END_Y_MM - TIP_Y_MM) * i / 64
        z = inner_arc_height(y)
        radial_gaps.append(math.hypot(y - DRUM_CENTER_Y_MM,
                                      z - DRUM_CENTER_Z_MM) -
                           DRUM_RADIUS_MM)
    result = {"model": str(MODEL), "enclosure_topology": shell_topology,
              "moving_part_intersections_by_pose": poses,
              "nominal_radial_gap_mm": RUNNING_CLEARANCE_MM,
              "profile_radial_gap_range_mm": [min(radial_gaps), max(radial_gaps)],
              "limits": "Nominal mesh geometry only; production tolerances and dust sealing unverified."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R29 TOPOLOGY", shell_topology)
    print("R29 OVERLAPS", {pose: hit for pose, hit in poses.items() if hit})
    print("R29 RADIAL GAP", min(radial_gaps), max(radial_gaps))


if __name__ == "__main__":
    main()
