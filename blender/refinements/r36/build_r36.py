#!/usr/bin/env python3
"""Replace obstructing inner-bearing tabs with side support envelopes."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(HERE.parent / "r21"))

import macbook  # noqa: E402
from assembly_primitives import box, material, tube  # noqa: E402
from r21_mechanism import AXIS  # noqa: E402

SOURCE = HERE.parent / "r35/deepreal-face-motion-study-r35.blend"
OUTPUT = HERE / "deepreal-inner-bearing-window-r36.blend"
HEAD_INTERFACE = ROOT / "hardware/electronics/deepreal-main-pcba/head-interface-evidence.json"
FPC_WIDTH_MM = json.loads(HEAD_INTERFACE.read_text())["connector"]["fpc_end_width_mm"]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    pivot = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    collection = bpy.data.collections.new("26 — R36 INNER BEARING SIDE SUPPORT STUDY")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_06"
    for name in (
        "Face_Inner_Race_Upper_Web_R21",
        "Face_Inner_Race_Lower_Web_R21",
        "Face_Inner_Race_Upper_Tab_R21",
        "Face_Inner_Race_Lower_Tab_R21",
        "R35_Face_Full_Width_Torsion_Candidate_ENV",
    ):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    steel = material("R36_Fixed_Bearing_Side_Web_ENV", (.4, .52, .58), .65, .3)
    flex_mat = material("R36_Full_Width_Exit_Clearance_ENV", (.73, .45, .1), .1, .4)
    neck = tube("R36_Face_Fixed_Bearing_Axial_Neck_ENV",
                (-2.05, *AXIS), macbook.X, 8.45, 8.9, 2.1,
                steel, collection, 96)
    neck["R36_Role"] = "fixed bearing extension beyond rotating lip"
    neck["R36_Status"] = "concept clearance neck, bearing not selected"
    supports = []
    for label, y in (("Rear", AXIS[0] + 9.3),
                     ("Front", AXIS[0] - 9.3)):
        web = box("R36_Face_Inner_Race_" + label + "_Side_Web_ENV",
                  (-.8, y, AXIS[1]), (1.4, 1.6, 2.0),
                  .2, steel, collection)
        web["R36_Role"] = "stationary bearing-to-center-support concept"
        web["R36_Status"] = "contact, strength and fasteners unverified"
        supports.append(web)

    flex = box("R36_Face_Full_Width_Straight_Exit_ENV",
               (-5.35, *AXIS), (6.3, .2, FPC_WIDTH_MM),
               .03, flex_mat, collection)
    flex.parent = pivot
    flex.matrix_parent_inverse = pivot.matrix_world.inverted()
    flex["R36_Status"] = (
        "straight moving segment only; optical-carrier and dynamic-loop "
        "clearance unverified")
    flex["R36_Width_mm"] = FPC_WIDTH_MM

    scene.name = "DeepReal Inner Bearing Side Support Study R36"
    scene["R36_Engineering_Status"] = (
        "fixed bearing side webs replace obstructing upper/lower tabs; "
        "full moving cable route remains unproven")
    bpy.context.view_layer.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r36-support-manifest.json").write_text(json.dumps({
        "source": str(SOURCE), "model": str(OUTPUT),
        "fixed_bearing_axial_neck": neck.name,
        "new_side_supports": [web.name for web in supports],
        "moving_straight_flex": flex.name,
        "connector_end_width_mm": FPC_WIDTH_MM,
        "status": "BEARING_SUPPORT_GEOMETRY_STUDY_ONLY",
        "open": ["stationary bearing-support joints and loads",
                 "moving cable path around optical carrier",
                 "center-divider cable opening and fixed termination",
                 "flex electrical stackup and fatigue"],
    }, indent=2) + "\n")
    print("R36 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
