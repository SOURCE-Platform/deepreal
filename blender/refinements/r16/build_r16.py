#!/usr/bin/env python3
"""Build a lower interaction-drum access opening without moving its optics."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r14", HERE.parent / "r15"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r15_drive import build as drive_build  # noqa: E402
from r15_pivots import build as pivot_build  # noqa: E402
from r15_routes import build as route_build  # noqa: E402
from r15_shell import build as shell_build  # noqa: E402

SOURCE = HERE.parent / "r14/deepreal-exterior-refinement-r14.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r16.blend"
INTERACTION_OPENING_DEG = -25.0


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    _, covers = shell_build(
        scene, interaction_opening_deg=INTERACTION_OPENING_DEG)
    drive = drive_build(scene)
    routes = route_build()
    pivots = pivot_build(scene)
    interaction_pivot = bpy.data.objects[
        "Interaction_Rotating_Drum_Pivot_R15"]
    del interaction_pivot["R15_Allowed_Optical_Direction_deg"]
    del interaction_pivot["R15_Pivot_X_Range_deg"]
    interaction_pivot["R16_Studied_Optical_Directions_deg"] = [45.0, 75.0]
    interaction_pivot["R16_Final_Travel_Range"] = (
        "not selected; intended to remain downward")
    scene.name = "DeepReal Enclosure Refinement R16"
    scene["DeepReal_Status"] = (
        "interaction access opening moved lower at saved pose; "
        "engineering readiness BLOCKED")
    scene["R16_Face_Access_Center_Saved_deg"] = 0.0
    scene["R16_Interaction_Access_Center_Saved_deg"] = (
        INTERACTION_OPENING_DEG)
    scene["R16_Interaction_Optics_Saved_deg"] = 45.0
    scene["R16_Interaction_Optics_Down_Stop_Study_deg"] = 75.0
    scene["R16_Interaction_Travel_Status"] = (
        "45 to 75 degrees downward reviewed; full operating limits pending")
    scene["R16_Opening_Design_Note"] = (
        "The interaction service opening and cover were clocked lower on "
        "the same drum. Sensor windows and saved drum pose are unchanged.")
    scene["R16_Review_Limit"] = (
        "Cover visibility tested in chosen rendered views at 45 and 75 "
        "degrees optical down direction; full viewing envelope, fasteners, "
        "sealing, cable motion and mechanical stops unverified")
    scene["R16_View_Control"] = (
        "toggle 00 housing solid/wire; toggle 01 drum shells; "
        "toggle 01A rear access covers")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r16-assembly-manifest.json").write_text(json.dumps({
        "model": str(OUTPUT), "source": str(SOURCE),
        "interaction_opening_angle_saved_deg": INTERACTION_OPENING_DEG,
        "face_opening_angle_saved_deg": 0.0,
        "interaction_optics_angle_saved_deg": 45.0,
        "covers": [obj.name for obj in covers],
        "drive_parts": [obj.name for obj in drive],
        "neutral_pose_routes": [obj.name for obj in routes],
        "pivots": [obj.name for obj in pivots],
        "engineering_readiness": "BLOCKED",
    }, indent=2) + "\n")
    print("R16 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
