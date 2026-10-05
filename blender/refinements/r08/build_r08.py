#!/usr/bin/env python3
"""Build R08 from R07 while preserving all prior review revisions."""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for folder in (REPO / "blender", HERE.parent / "r04",
               HERE.parent / "r07", HERE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from r04_geometry import frame_viewports  # noqa: E402
from r08_geometry import (  # noqa: E402
    rear_shield_feedthrough, restore_housing, restore_meshes,
    tag_scene, usb_socket_and_side_route)

SOURCE = HERE.parent / "r07" / "deepreal-exterior-refinement-r07.blend"
UNCUT = HERE.parent / "r04" / "deepreal-exterior-refinement-r04.blend"
HOUSING = HERE.parent / "r06" / "deepreal-exterior-refinement-r06.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r08.blend"


def build():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    restore_meshes(UNCUT, ("Thermal_Spreader", "Shield_Rear_Tray",
                           "Shield_Front_Lid"))
    rear_shield_feedthrough()
    restore_housing(HOUSING)
    usb_socket_and_side_route()
    tag_scene()
    thermal = bpy.data.collections["04 — SPLIT THERMAL PATH — UNVALIDATED OPTION"]
    thermal.name = "04 — THERMAL LINKS + PADS — UNVALIDATED"
    thermal["R08_Status"] = (
        "continuous spreader restored; links, pads and contact pressures unverified")
    frame_viewports(target=(0.0, 0.004, -0.003), distance=0.14)
    bpy.context.scene.camera = bpy.data.objects["Camera_R05_Front"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R08 saved", OUTPUT)


if __name__ == "__main__":
    build()
