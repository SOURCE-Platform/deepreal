#!/usr/bin/env python3
"""Build internal drive and removable rear access panels on R14."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r14", HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r15_drive import build as drive_build  # noqa: E402
from r15_pivots import build as pivot_build  # noqa: E402
from r15_routes import build as route_build  # noqa: E402
from r15_shell import build as shell_build  # noqa: E402

SOURCE = HERE.parent / "r14/deepreal-exterior-refinement-r14.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r15.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    covers, panels = shell_build(scene)
    drive_parts = drive_build(scene)
    routes = route_build()
    pivots = pivot_build(scene)
    scene.name = "DeepReal Enclosure Refinement R15"
    scene["DeepReal_Status"] = (
        "internal gear and removable rear panel assembly study; "
        "engineering readiness BLOCKED")
    scene["R15_Travel_Concept_Deg"] = [-75.0, 75.0]
    scene["R15_Travel_Reference"] = (
        "absolute optical direction relative to straight forward; "
        "Face currently 0 deg, Interaction currently 45 deg downward")
    scene["R15_View_Control"] = (
        "toggle 00 housing solid/wire; toggle 01 drum shells; "
        "toggle 01A rear access covers")
    scene["R15_Animation_Control"] = (
        "rotate Face or Interaction R15 pivot around local X; "
        "target optical direction = pivot X + current rest direction")
    scene["R15_Limits"] = (
        "ring teeth and torque, keyed drum coupling, motor selection, "
        "encoder IC, fixed endcap mount, dynamic head-flex fatigue, "
        "sealing and structural stiffness unverified")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r15-assembly-manifest.json").write_text(json.dumps({
        "model": str(OUTPUT),
        "source": str(SOURCE),
        "rear_access_cover_objects": [obj.name for obj in panels],
        "revised_drive_objects": [obj.name for obj in drive_parts],
        "neutral_pose_routes": [obj.name for obj in routes],
        "travel_pivots": [obj.name for obj in pivots],
        "design_sweep_absolute_deg": [-75, 75],
        "engineering_readiness": "BLOCKED",
    }, indent=2) + "\n")
    print("R15 SAVED", OUTPUT, "covers", len(panels),
          "drive objects", len(drive_parts), "routes", len(routes))


if __name__ == "__main__":
    main()
