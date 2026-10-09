#!/usr/bin/env python3
"""Check R23 enclosure connectivity and drum travel intersections."""

import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

MODEL = HERE / "deepreal-integrated-flat-roof-r23.blend"
REPORT = HERE / "r23-enclosure-check.json"


def mesh_topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    result = {"vertex_components": components,
              "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
              "faces": len(bm.faces)}
    bm.free()
    return result


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    shell = bpy.data.objects["R23_Unified_Enclosure"]
    topology = mesh_topology(shell)
    poses = {}
    for side, base, directions in (("Face", 0, (-45, 0, 45)),
                                   ("Interaction", 45, (0, 22.5, 45))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        moving = [bpy.data.objects[side + "_" + suffix] for suffix in (
            "Sensor_Head", "Open_Inner_End_Ring_R21",
            "Flat_Outer_End_R21")]
        moving += [obj for obj in bpy.data.objects
                   if obj.name.startswith(side + "_Drum_Lens_")
                   and obj.type == "MESH"]
        for direction in directions:
            pivot.rotation_euler.x = math.radians(direction - base)
            bpy.context.view_layer.update()
            hits = {obj.name: len(tree(obj).overlap(tree(shell)))
                    for obj in moving}
            poses[f"{side}_{direction:+g}_deg"] = {
                name: count for name, count in hits.items() if count}
        pivot.rotation_euler.x = 0
    result = {"model": str(MODEL), "enclosure_topology": topology,
              "moving_part_intersections_by_pose": poses,
              "limits": "Triangle intersections only; tolerance, optical rays, fasteners and assembly path unverified."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("R23 TOPOLOGY", topology)
    print("R23 OVERLAPS", {pose: hit for pose, hit in poses.items() if hit})


if __name__ == "__main__":
    main()
