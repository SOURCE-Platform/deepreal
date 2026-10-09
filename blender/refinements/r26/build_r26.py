#!/usr/bin/env python3
"""Shape a tapered rear roof whose inner edge follows the drum arc."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21",
             HERE.parent / "r23", HERE.parent / "r24",
             HERE.parent / "r25"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from build_r23 import ccw, union_into  # noqa: E402
from build_r24 import lower_profile  # noqa: E402
from build_r25 import rear_arc  # noqa: E402
from r21_chassis import yz_prism  # noqa: E402

SOURCE = HERE.parent / "r25/deepreal-exposed-drum-top-r25.blend"
OUTPUT = HERE / "deepreal-contoured-roof-edge-r26.blend"
TIP_Y_MM = 2.8
CURVE_END_Y_MM = 9.5
DRUM_CENTER_Y_MM = -1.5
DRUM_CENTER_Z_MM = 20.0
DRUM_RADIUS_MM = 12.0
RUNNING_CLEARANCE_MM = .5


def inner_arc_height(y):
    radial_y = y - DRUM_CENTER_Y_MM
    return (DRUM_CENTER_Z_MM +
            math.sqrt((DRUM_RADIUS_MM + RUNNING_CLEARANCE_MM) ** 2 -
                      radial_y ** 2))


def roof_profile():
    outer = [(TIP_Y_MM, 32), (13.2, 32)]
    outer.extend(rear_arc(9.3, True))
    inner = [(22.5, 13), (11.7, 13), (11.7, 20),
             (CURVE_END_Y_MM, inner_arc_height(CURVE_END_Y_MM))]
    for i in range(1, 33):
        y = CURVE_END_Y_MM + (TIP_Y_MM - CURVE_END_Y_MM) * i / 32
        inner.append((y, inner_arc_height(y)))
    return ccw(outer + inner)


def support_profile():
    outline = [(TIP_Y_MM, 32), (13.2, 32)]
    outline.extend(rear_arc(9.3, True))
    outline.extend([(22.5, 5.5), (6, 5.5), (6, 10), (2, 14),
                    (-4.2, 17), (-4.2, 23), (-1, 24), (2, 24.4),
                    (5, 24.8), (8, 25.5),
                    (CURVE_END_Y_MM, inner_arc_height(CURVE_END_Y_MM))])
    for i in range(1, 33):
        y = CURVE_END_Y_MM + (TIP_Y_MM - CURVE_END_Y_MM) * i / 32
        outline.append((y, inner_arc_height(y)))
    return ccw(outline)


def add_finish(shell):
    bevel = shell.modifiers.new("R26_Subtle_Enclosure_Edges", "BEVEL")
    bevel.width = .0001
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(36)
    bevel.harden_normals = True
    normals = shell.modifiers.new("R26_Weighted_Normals", "WEIGHTED_NORMAL")
    normals.keep_sharp = True
    normals.weight = 50


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R25_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("17 — R26 CONTOURED ROOF EDGE")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    shell_mat = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R26_One_Piece_Enclosure", lower_profile(),
                     0, 120, shell_mat, collection)
    for label, x, width in (("Left", -58.3, 2.2),
                            ("Center", 0, 3.0),
                            ("Right", 58.3, 2.2)):
        cheek = yz_prism("R26_Temporary_" + label,
                         support_profile(), x, width,
                         shell_mat, collection)
        union_into(shell, cheek)
    roof = yz_prism("R26_Temporary_Arc_Following_Roof",
                    roof_profile(), 0, 120, shell_mat, collection)
    union_into(shell, roof)
    center = macbook.cylinder(
        "R26_Temporary_Center_Island", Vector((0, -.0015, .020)),
        macbook.X, .012, .003, shell_mat, seg=96)
    collection.objects.link(center)
    union_into(shell, center)
    add_finish(shell)
    shell["R26_Design_Intent"] = (
        "thin forward roof edge; concave underside follows rotating drum "
        "rear arc with visible clearance")
    shell["R26_Scope"] = "visual enclosure; production seal deferred"
    scene.name = "DeepReal Contoured Rear Roof Study R26"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {"source": str(SOURCE), "model": str(OUTPUT),
                "enclosure": shell.name, "tip_y_mm": TIP_Y_MM,
                "inner_curve_end_y_mm": CURVE_END_Y_MM,
                "nominal_running_clearance_mm": RUNNING_CLEARANCE_MM,
                "drum_crown_and_roof_top_z_mm": 32.0,
                "scope": "appearance concept, not a validated dust seal"}
    (HERE / "r26-exterior-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R26 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
