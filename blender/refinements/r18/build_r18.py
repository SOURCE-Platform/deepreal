#!/usr/bin/env python3
"""Build a reversible rear-only support and aperture visibility mockup."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r15", HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r18_rear_support import build  # noqa: E402

SOURCE = HERE.parent / "r16/deepreal-exterior-refinement-r16.blend"
OUTPUT = HERE / "deepreal-rear-support-study-r18.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    parts = build(scene)
    scene.name = "DeepReal Rear Support Visibility Study R18"
    scene["R18_Purpose"] = (
        "rear-only twin-arm drum support sightline experiment; NOT a "
        "validated motor, bearing, cable or enclosure assembly")
    scene["R18_Sweep"] = (
        "two 3.2 mm axial arm openings per drum; face 186-degree slots "
        "for -75 to +75 degrees, interaction 42-degree slots for 45 to "
        "75 degrees, both including approximate arm clearance")
    scene["R18_Limits"] = (
        "arm-to-housing attachment, bearing race attachments, motor, "
        "encoder, flexible cable, slot strength and assembly unverified")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r18-study-manifest.json").write_text(json.dumps({
        "model": str(OUTPUT), "source": str(SOURCE),
        "study_parts": [item.name for item in parts],
        "engineering_readiness": "VISIBILITY_STUDY_ONLY",
    }, indent=2) + "\n")
    print("R18 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
