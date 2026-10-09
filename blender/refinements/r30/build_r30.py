#!/usr/bin/env python3
"""Restore a monitor-top ledge and the provisional magnetic mount pad."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r21", HERE.parent / "r23",
             HERE.parent / "r25", HERE.parent / "r26", HERE.parent / "r29"):
    sys.path.insert(0, str(path))

from build_r23 import ccw, union_into  # noqa: E402
from build_r26 import add_finish, roof_profile  # noqa: E402
from build_r29 import divider_profile  # noqa: E402
from r21_chassis import material as make_material, yz_prism  # noqa: E402

SOURCE = HERE.parent / "r29/deepreal-circular-divider-enclosure-r29.blend"
OUTPUT = HERE / "deepreal-monitor-ledge-enclosure-r30.blend"
LID_FRONT_Y_MM = -1.5
LID_REAR_Y_MM = 1.5
STACK_FACE_Y_MM = 3.5
POCKET_BACK_Y_MM = 5.5
SHELF_Z_MM = 0.0


def ledged_body_profile():
    # Seven millimetres from the lid's front face to the recessed pocket
    # back. The small pad farther forward preserves the earlier 2 mm stack.
    outline = [(POCKET_BACK_Y_MM, -29), (10, -29)]
    for i in range(1, 25):
        angle = math.radians(-90 + 90 * i / 24)
        outline.append((10 + 12.5 * math.cos(angle),
                        -16 + 13 * math.sin(angle)))
    outline.extend([(22.5, 20), (11.7, 20), (11.7, 6.8),
                    (LID_FRONT_Y_MM, 6.8),
                    (LID_FRONT_Y_MM, SHELF_Z_MM),
                    (POCKET_BACK_Y_MM, SHELF_Z_MM)])
    return ccw(outline)


def add_stack_references(scene):
    refs = bpy.data.collections.new("22 — R30 MOUNT STACK REFERENCES (HIDDEN)")
    scene.collection.children.link(refs)
    specs = (
        ("Monitor_Lid_Reference", -1.5, 1.5, -30, 0, 45,
         (.14, .27, .34, 1), "3.0 mm display lid"),
        ("Mount_Foam_Tape_Reference", 1.5, 1.9, -13, -1, 40,
         (.74, .55, .25, 1), "0.40 mm removable foam tape"),
        ("Mount_Steel_Plate_Reference", 1.9, 2.25, -13, -1, 40,
         (.34, .42, .46, 1), "0.35 mm passive steel target"),
        ("Mount_Magnet_Reference", 2.6, 3.5, -13, -1, 40,
         (.61, .30, .17, 1), "0.90 mm device magnet"),
    )
    for name, y0, y1, z0, z1, width, color, role in specs:
        mat = make_material("R30_" + name, color, .12, .55)
        obj = yz_prism(name, ccw([(y0, z0), (y1, z0),
                                  (y1, z1), (y0, z1)]),
                       0, width, mat, refs)
        obj["R30_Reference_Role"] = role
        obj["R30_Reference_Only"] = True
        obj.hide_render = True
        obj.hide_set(True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    bpy.data.objects.remove(
        bpy.data.objects["R29_One_Piece_Enclosure"], do_unlink=True)
    collection = bpy.data.collections.new("21 — R30 MONITOR TOP LEDGE")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_04"
    material = bpy.data.materials["R24_Satin_Mineral_Housing"]
    shell = yz_prism("R30_One_Piece_Enclosure", ledged_body_profile(),
                     0, 120, material, collection)
    for label, x, width in (("Left", -58.8, 2.4),
                            ("Center", 0, 3.0),
                            ("Right", 58.8, 2.4)):
        divider = yz_prism("R30_Temporary_" + label + "_Divider",
                           divider_profile(), x, width,
                           material, collection)
        union_into(shell, divider)
    roof = yz_prism("R30_Temporary_Contoured_Roof", roof_profile(),
                    0, 120, material, collection)
    union_into(shell, roof)
    # The 40 mm wide central pad carries the device magnet at the original
    # mounting plane, while the side silhouette gains a deeper 7 mm pocket.
    pad = yz_prism("R30_Temporary_Magnet_Pad",
                   ccw([(STACK_FACE_Y_MM, -14),
                        (POCKET_BACK_Y_MM + .2, -14),
                        (POCKET_BACK_Y_MM + .2, -1),
                        (STACK_FACE_Y_MM, -1)]),
                   0, 40, material, collection)
    union_into(shell, pad)
    add_finish(shell)
    shell["R30_Design_Intent"] = (
        "deeper seven-millimetre monitor-top shelf with a central magnet "
        "pad preserving the historic two-millimetre attachment stack")
    shell["R30_Scope"] = "appearance and stack envelope, not mount engineering"
    add_stack_references(scene)
    scene.name = "DeepReal Monitor Ledge Enclosure R30"
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r30-mount-manifest.json").write_text(json.dumps({
        "source": str(SOURCE), "model": str(OUTPUT), "enclosure": shell.name,
        "monitor_lid_thickness_mm": LID_REAR_Y_MM - LID_FRONT_Y_MM,
        "ledge_depth_from_lid_front_mm": POCKET_BACK_Y_MM - LID_FRONT_Y_MM,
        "mount_stack_space_behind_lid_mm": STACK_FACE_Y_MM - LID_REAR_Y_MM,
        "mounting_pad_recess_depth_mm": POCKET_BACK_Y_MM - STACK_FACE_Y_MM,
        "provisional_stack_mm": {"foam_tape": .4, "steel_plate": .35,
                                 "air_gap": .35, "magnet": .9},
        "shelf_underside_z_mm": SHELF_Z_MM,
        "scope": "appearance and packaging concept; magnet/adhesive selection open",
    }, indent=2) + "\n")
    print("R30 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
