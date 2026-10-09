#!/usr/bin/env python3
"""Match each fixed divider's front edge to the circular drum profile."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21",
             HERE.parent / "r23", HERE.parent / "r24",
             HERE.parent / "r25", HERE.parent / "r26"):
    sys.path.insert(0, str(path))

from build_r23 import ccw, union_into  # noqa: E402
from build_r24 import lower_profile  # noqa: E402
from build_r25 import rear_arc  # noqa: E402
from build_r26 import (DRUM_CENTER_Y_MM, DRUM_CENTER_Z_MM,
                       DRUM_RADIUS_MM, add_finish, roof_profile)  # noqa: E402
from r21_chassis import yz_prism  # noqa: E402

SOURCE = HERE.parent / "r26/deepreal-contoured-roof-edge-r26.blend"
OUTPUT = HERE / "deepreal-circular-divider-enclosure-r29.blend"
ARC_SEGMENTS = 96


def divider_profile():
    # The front edge is concentric with, and has the same radius as, a drum.
    # Divider thickness lies in the axial gaps between rotating shells.
    outline = [(13.2, 32)]
    outline.extend(rear_arc(9.3, True))
    outline.extend([(22.5, 5.5), (0, 5.5), (-1.4, 6.6),
                    (DRUM_CENTER_Y_MM, DRUM_CENTER_Z_MM - DRUM_RADIUS_MM)])
    for i in range(1, ARC_SEGMENTS + 1):
        angle = -math.pi / 2 - math.pi * i / ARC_SEGMENTS
        outline.append((DRUM_CENTER_Y_MM + DRUM_RADIUS_MM * math.cos(angle),
                        DRUM_CENTER_Z_MM + DRUM_RADIUS_MM * math.sin(angle)))
    return ccw(outline)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R26_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("20 — R29 CIRCULAR DRUM DIVIDERS")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    material = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R29_One_Piece_Enclosure", lower_profile(),
                     0, 120, material, collection)
    profile = divider_profile()
    for label, x, width in (("Left", -58.8, 2.4),
                            ("Center", 0, 3.0),
                            ("Right", 58.8, 2.4)):
        divider = yz_prism("R29_Temporary_" + label + "_Divider",
                           profile, x, width, material, collection)
        union_into(shell, divider)
    roof = yz_prism("R29_Temporary_Contoured_Roof", roof_profile(),
                    0, 120, material, collection)
    union_into(shell, roof)
    add_finish(shell)
    shell["R29_Design_Intent"] = (
        "three dividers with true drum-concentric front arcs; outer faces "
        "flush with the main enclosure; integrated roof and lower body")
    shell["R29_Scope"] = "exterior concept; print seams and fastening deferred"
    scene.name = "DeepReal Circular Divider Enclosure R29"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r29-exterior-manifest.json").write_text(json.dumps({
        "source": str(SOURCE), "model": str(OUTPUT),
        "enclosure": shell.name,
        "drum_and_divider_arc_radius_mm": DRUM_RADIUS_MM,
        "drum_and_divider_arc_center_yz_mm": [DRUM_CENTER_Y_MM,
                                               DRUM_CENTER_Z_MM],
        "divider_arc_segments": ARC_SEGMENTS,
        "outer_supports_flush_with_housing_x_mm": [-60, 60],
        "scope": "appearance concept; assembly details deferred",
    }, indent=2) + "\n")
    print("R29 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
