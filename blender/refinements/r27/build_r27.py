#!/usr/bin/env python3
"""Bring the three roof-to-body support junctions forward visibly."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21",
             HERE.parent / "r23", HERE.parent / "r24",
             HERE.parent / "r25", HERE.parent / "r26"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from build_r23 import ccw, union_into  # noqa: E402
from build_r24 import lower_profile  # noqa: E402
from build_r25 import rear_arc  # noqa: E402
from build_r26 import add_finish, inner_arc_height, roof_profile  # noqa: E402
from r21_chassis import yz_prism  # noqa: E402

SOURCE = HERE.parent / "r26/deepreal-contoured-roof-edge-r26.blend"
OUTPUT = HERE / "deepreal-integrated-three-supports-r27.blend"
JOIN_Y_MM = 6.8
TIP_Y_MM = 2.8


def connected_support_profile():
    outline = [(TIP_Y_MM, 32), (13.2, 32)]
    outline.extend(rear_arc(9.3, True))
    outline.extend([(22.5, 5.5), (6, 5.5), (6, 10), (2, 14),
                    (-4.2, 17), (-4.2, 23), (-1, 24),
                    (2, 24.4), (4.2, 25.5), (5.6, 27.2),
                    (JOIN_Y_MM, inner_arc_height(JOIN_Y_MM))])
    for i in range(1, 33):
        y = JOIN_Y_MM + (TIP_Y_MM - JOIN_Y_MM) * i / 32
        outline.append((y, inner_arc_height(y)))
    return ccw(outline)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R26_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("18 — R27 INTEGRATED THREE SUPPORTS")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    shell_mat = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R27_One_Piece_Enclosure", lower_profile(),
                     0, 120, shell_mat, collection)
    support = connected_support_profile()
    for label, x, width in (("Left", -58.3, 2.2),
                            ("Center", 0, 3.0),
                            ("Right", 58.3, 2.2)):
        cheek = yz_prism("R27_Temporary_" + label, support,
                         x, width, shell_mat, collection)
        union_into(shell, cheek)
    roof = yz_prism("R27_Temporary_Contoured_Roof", roof_profile(),
                    0, 120, shell_mat, collection)
    union_into(shell, roof)
    center = macbook.cylinder(
        "R27_Temporary_Center_Island", Vector((0, -.0015, .020)),
        macbook.X, .012, .003, shell_mat, seg=96)
    collection.objects.link(center)
    union_into(shell, center)
    add_finish(shell)
    shell["R27_Design_Intent"] = (
        "one integrated roof, three curved supports, center island, "
        "and lower enclosure; forward-visible roof junctions")
    shell["R27_Scope"] = "appearance and packaging concept"
    scene.name = "DeepReal Integrated Three-Support Enclosure R27"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {"source": str(SOURCE), "model": str(OUTPUT),
                "enclosure": shell.name,
                "roof_support_join_y_mm": JOIN_Y_MM,
                "three_supports": ["left", "center", "right"],
                "scope": "appearance concept; assembly details deferred"}
    (HERE / "r27-exterior-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R27 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
