#!/usr/bin/env python3
"""Expose the drum crowns and retain only a rear partial enclosure roof."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21",
             HERE.parent / "r23", HERE.parent / "r24"):
    sys.path.insert(0, str(path))

import macbook  # noqa: E402
from build_r23 import ccw, union_into  # noqa: E402
from build_r24 import add_finish, lower_profile  # noqa: E402
from r21_chassis import yz_prism  # noqa: E402

SOURCE = HERE.parent / "r24/deepreal-finished-exterior-r24.blend"
OUTPUT = HERE / "deepreal-exposed-drum-top-r25.blend"
DRUM_TOP_MM = 32.0
ROOF_FRONT_Y_MM = 5.0
REAR_TANGENT_Y_MM = 13.2
REAR_TANGENT_Z_MM = 22.7


def rear_arc(radius, descending):
    for i in range(1, 25):
        angle = math.radians((90 - 90 * i / 24) if descending
                             else 90 * i / 24)
        yield (REAR_TANGENT_Y_MM + radius * math.cos(angle),
               REAR_TANGENT_Z_MM + radius * math.sin(angle))


def roof_profile():
    outer = [(ROOF_FRONT_Y_MM, DRUM_TOP_MM),
             (REAR_TANGENT_Y_MM, DRUM_TOP_MM)]
    outer.extend(rear_arc(9.3, True))
    inner = [(22.5, 13), (21.3, 13), (21.3, REAR_TANGENT_Z_MM)]
    inner.extend(rear_arc(8.1, False))
    inner.append((ROOF_FRONT_Y_MM, 30.8))
    return ccw(outer + inner)


def support_profile():
    upper = [(-4.2, 17), (-4.2, 23), (0.5, 27.5),
             (ROOF_FRONT_Y_MM, DRUM_TOP_MM),
             (REAR_TANGENT_Y_MM, DRUM_TOP_MM)]
    upper.extend(rear_arc(9.3, True))
    upper.extend([(22.5, 5.5), (6, 5.5), (6, 10), (2, 14)])
    return ccw(upper)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R24_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("16 — R25 EXPOSED DRUM TOP")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    shell_mat = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R25_One_Piece_Enclosure", lower_profile(),
                     0, 120, shell_mat, collection)
    for label, x, width in (("Left", -58.3, 2.2),
                            ("Center", 0, 3.0),
                            ("Right", 58.3, 2.2)):
        cheek = yz_prism("R25_Temporary_" + label,
                         support_profile(), x, width,
                         shell_mat, collection)
        union_into(shell, cheek)
    top = yz_prism("R25_Temporary_Rear_Partial_Roof",
                   roof_profile(), 0, 120, shell_mat, collection)
    union_into(shell, top)
    center = macbook.cylinder(
        "R25_Temporary_Center_Island", Vector((0, -.0015, .020)),
        macbook.X, .012, .003, shell_mat, seg=96)
    collection.objects.link(center)
    union_into(shell, center)
    add_finish(shell)
    shell["R25_Design_Intent"] = (
        "drum crowns and upper rear arcs exposed; flat enclosure top "
        "level with the drum crowns; roof protects the rear only")
    shell["R25_Scope"] = "website exterior study; parting seams deferred"
    scene.name = "DeepReal Exposed Drum Top Study R25"
    scene["R25_Render_Intent"] = (
        "enclosure silhouette aligned with drum crowns, partial rear roof")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    manifest = {"source": str(SOURCE), "model": str(OUTPUT),
                "enclosure": shell.name,
                "drum_crown_z_mm": DRUM_TOP_MM,
                "enclosure_top_z_mm": DRUM_TOP_MM,
                "rear_roof_front_y_mm": ROOF_FRONT_Y_MM,
                "rear_roof_thickness_mm": 1.2,
                "scope": "exterior visual study"}
    (HERE / "r25-exterior-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print("R25 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
