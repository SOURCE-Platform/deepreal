#!/usr/bin/env python3
"""Rebuild the rear-arm visibility mockup for role-specific drum limits."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r15",
             HERE.parent / "r18"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r18_rear_support import build  # noqa: E402

SOURCE = HERE.parent / "r16/deepreal-exterior-refinement-r16.blend"
OUTPUT = HERE / "deepreal-role-specific-sweep-r19.blend"
SPECS = (("Face", -1, 180.0, 114.0),
         ("Interaction", 1, 180.0, 102.0))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    parts = build(scene, specs=SPECS, revision="R19")
    scene.name = "DeepReal Role-Specific Sweep R19"
    face = bpy.data.objects["Face_Rotating_Drum_Pivot_R15"]
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    face["R19_Optical_Directions_deg"] = [-45.0, 0.0, 45.0]
    interaction["R19_Optical_Directions_deg"] = [0.0, 45.0, 90.0]
    scene["R19_Status"] = (
        "rear-only support visibility mockup with user-proposed limits; "
        "bearing and shell load path, motor, encoder, cable and assembly open")
    scene["R19_Arm_Slots"] = (
        "two 3.2 mm axial openings per drum; 114-degree face and "
        "102-degree interaction arcs for 90-degree optical travel, "
        "with trial arm clearance")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r19-study-manifest.json").write_text(json.dumps({
        "model": str(OUTPUT), "source": str(SOURCE),
        "face_optical_directions_deg": [-45, 0, 45],
        "interaction_optical_directions_deg": [0, 45, 90],
        "study_parts": [part.name for part in parts],
        "engineering_readiness": "VISIBILITY_STUDY_ONLY",
    }, indent=2) + "\n")
    print("R19 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
