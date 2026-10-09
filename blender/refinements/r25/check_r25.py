#!/usr/bin/env python3
"""Check the exposed-top shell and sampled drum travel."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r24"))
sys.path.insert(0, str(HERE.parent / "r08"))
from check_r24 import topology  # noqa: E402
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-exposed-drum-top-r25.blend"
REPORT = HERE / "r25-enclosure-check.json"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    shell = bpy.data.objects["R25_One_Piece_Enclosure"]
    shell_topology = topology(shell)
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
            shell_tree = tree(shell)
            hits = {obj.name: len(tree(obj).overlap(shell_tree))
                    for obj in moving}
            poses[f"{side}_{direction:+g}_deg"] = {
                name: count for name, count in hits.items() if count}
        pivot.rotation_euler.x = saved_rotation
    result = {"model": str(MODEL), "enclosure_topology": shell_topology,
              "moving_part_intersections_by_pose": poses,
              "limits": "Triangle intersections only; production tolerance and assembly path unverified."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R25 TOPOLOGY", shell_topology)
    print("R25 OVERLAPS", {pose: hit for pose, hit in poses.items() if hit})


if __name__ == "__main__":
    main()
