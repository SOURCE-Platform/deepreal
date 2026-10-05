#!/usr/bin/env python3
"""Build an isolated R09 Blender packaging study from saved R08."""

import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for folder in (REPO / "blender", HERE.parent / "r04",
               HERE.parent / "r07", HERE.parent / "r08", HERE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from r04_geometry import frame_viewports  # noqa: E402
from r09_geometry import (  # noqa: E402
    add_board_tab, move_socket_and_plug, open_housing, open_shield_side,
    remove_centered_study, tag_scene)

SOURCE = HERE.parent / "r08" / "deepreal-exterior-refinement-r08.blend"
UNCUT = HERE.parent / "r04" / "deepreal-exterior-refinement-r04.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r09.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    remove_centered_study()
    add_board_tab()
    open_shield_side(UNCUT)
    move_socket_and_plug()
    open_housing(UNCUT)
    tag_scene()
    frame_viewports(target=(0.0, 0.004, -0.005), distance=0.14)
    bpy.context.scene.camera = bpy.data.objects["Camera_R05_Front"]
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print("R09 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
