#!/usr/bin/env python3
"""Locate the moving narrow ribbon's intersections along the drum axis."""

import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r35"))
sys.path.insert(0, str(HERE.parent / "r08"))
from flex_geometry import set_pose  # noqa: E402
from verify_r08 import tree  # noqa: E402

SOURCE = HERE.parent / "r35/deepreal-face-motion-study-r35.blend"


def x_range_mm(obj, indices):
    mesh = obj.data
    vertices = [obj.matrix_world @ mesh.vertices[index].co
                for face in indices for index in mesh.polygons[face].vertices]
    return (round(min(v.x for v in vertices) * 1000, 2),
            round(max(v.x for v in vertices) * 1000, 2))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    flex = bpy.data.objects["R35_Face_Full_Width_Torsion_Candidate_ENV"]
    flex["R35_Width_mm"] = 6.0
    flex["R35_Moving_Anchor_X_mm"] = -12.0
    flex["R35_Fixed_Anchor_X_mm"] = -2.2
    for angle in (-45, -30, -15, 0, 15, 30, 45):
        pivot.rotation_euler.x = math.radians(angle)
        set_pose(flex, angle)
        bpy.context.view_layer.update()
        for name in ("Face_Head_PCBA_Carrier_CONCEPT",
                     "Face_Internal_Optical_Carrier",
                     "Face_RGB_Module_Body"):
            obj = bpy.data.objects[name]
            pairs = tree(flex).overlap(tree(obj))
            if pairs:
                print("ANGLE", angle, "PART", name,
                      "FLEX_X", x_range_mm(flex, {a for a, _ in pairs}),
                      "PART_X", x_range_mm(obj, {b for _, b in pairs}),
                      "PAIRS", len(pairs))


if __name__ == "__main__":
    main()
