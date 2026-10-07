#!/usr/bin/env python3
"""Build enclosed outer drum modules from the R16 assembly study."""

import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for path in (REPO / "blender", HERE.parent / "r14",
             HERE.parent / "r15", HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from r17_cable_routes import build as route_build  # noqa: E402
from r17_side_modules import build as module_build  # noqa: E402

SOURCE = HERE.parent / "r16/deepreal-exterior-refinement-r16.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r17.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    _, module_parts = module_build(scene)
    routes = route_build()
    scene.name = "DeepReal Enclosure Refinement R17"
    scene["DeepReal_Status"] = (
        "outer drive and encoder enclosed in fixed coaxial drum-end "
        "modules; mechanical/electrical engineering readiness BLOCKED")
    scene["R17_Architecture"] = (
        "rotating shell and optics; fixed internal motor, encoder board, "
        "support and smooth outer cap; head flex exits near pivot through "
        "protected side chamber")
    scene["R17_Cable_Limit"] = (
        "neutral-pose flex loop illustration only; dynamic shape, cable "
        "selection, minimum bend radius, fatigue and signal integrity open")
    scene["R17_Encoder_Limit"] = (
        "magnet and sensor envelopes only; accuracy, part choice, "
        "field orientation, calibration and mount tolerances open")
    scene["R17_View_Control"] = (
        "toggle 00 housing solid/wire; toggle 01 drum shells; "
        "toggle 01A rear access covers; toggle 09 fixed end modules")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    (HERE / "r17-assembly-manifest.json").write_text(json.dumps({
        "model": str(OUTPUT), "source": str(SOURCE),
        "module_parts": [part.name for part in module_parts],
        "route_parts": [part.name for part in routes],
        "engineering_readiness": "BLOCKED",
    }, indent=2) + "\n")
    print("R17 SAVED", OUTPUT)


if __name__ == "__main__":
    main()
