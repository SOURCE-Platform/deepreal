#!/usr/bin/env python3
"""Build visible left, center, and right enclosure dividers."""

import json
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
from build_r26 import add_finish, roof_profile  # noqa: E402
from r21_chassis import yz_prism  # noqa: E402

SOURCE = HERE.parent / "r26/deepreal-contoured-roof-edge-r26.blend"
OUTPUT = HERE / "deepreal-three-divider-enclosure-r28.blend"


def divider_profile():
    # The exposed front edge traces the rear half of a drum end face.
    # Each divider remains axially outside its neighboring rotating shell.
    outline = [(4.0, 31.9), (13.2, 32)]
    outline.extend(rear_arc(9.3, True))
    outline.extend([(22.5, 5.5), (0, 5.5),
                    (-4.0, 9.8), (-6.3, 13.0),
                    (-7.5, 16.5), (-7.5, 23.5),
                    (-6.3, 27.0), (-4.0, 30.0),
                    (-1.5, 31.5), (0, 31.8)])
    return ccw(outline)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R26_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("19 — R28 THREE DRUM DIVIDERS")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    material = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R28_One_Piece_Enclosure", lower_profile(),
                     0, 120, material, collection)
    profile = divider_profile()
    for label, x, width in (("Left", -58.3, 2.2),
                            ("Center", 0, 3.0),
                            ("Right", 58.3, 2.2)):
        divider = yz_prism("R28_Temporary_" + label + "_Divider",
                           profile, x, width, material, collection)
        union_into(shell, divider)
    roof = yz_prism("R28_Temporary_Contoured_Roof", roof_profile(),
                    0, 120, material, collection)
    union_into(shell, roof)
    add_finish(shell)
    shell["R28_Design_Intent"] = (
        "visible full-height left, center, and right dividers integrated "
        "with the partial roof and lower enclosure")
    shell["R28_Scope"] = "exterior concept; print seams and fastening deferred"
    scene.name = "DeepReal Three Divider Enclosure R28"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r28-exterior-manifest.json").write_text(json.dumps({
        "source": str(SOURCE), "model": str(OUTPUT),
        "enclosure": shell.name,
        "frontmost_divider_y_mm": -7.5,
        "dividers": ["left", "center", "right"],
        "scope": "appearance concept; assembly details deferred",
    }, indent=2) + "\n")
    print("R28 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
