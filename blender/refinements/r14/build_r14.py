#!/usr/bin/env python3
"""Restore separate motor/optical parts and route concepts to R13."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO / "blender") not in sys.path:
    sys.path.insert(0, str(REPO / "blender"))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from r14_assembly import add_routes, head_boards, hierarchy, remove_old_routes
from r14_restore import restore

SOURCE = HERE.parent / "r13" / "deepreal-exterior-refinement-r13.blend"
DONOR = REPO / "blender/deepreal.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r14.blend"
MANIFEST = HERE / "r14-assembly-manifest.json"


def bounds_mm(obj):
    if obj.type != "MESH":
        return None
    return [[round(min((obj.matrix_world @ Vector(v))[i]
                       for v in obj.bound_box) * 1000, 2),
             round(max((obj.matrix_world @ Vector(v))[i]
                       for v in obj.bound_box) * 1000, 2)]
            for i in range(3)]


def inventory(groups):
    entries = []
    for key, collection in groups.items():
        if key == "routes":
            side, role = "both", "routes"
        else:
            side, role = key
        for obj in sorted(collection.objects, key=lambda x: x.name):
            if obj.type not in {"MESH", "CURVE"}:
                continue
            entries.append({
                "name": obj.name, "side": side, "role": role,
                "geometry_type": obj.type,
                "bounds_mm": bounds_mm(obj),
                "origin": obj.get("R14_Origin", "R14 proxy or route concept"),
                "status": (obj.get("R14_Electrical_Status") or
                           obj.get("R14_Route_Status") or
                           obj.get("R14_Validation") or "concept geometry"),
            })
    return entries


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    groups = hierarchy(bpy.context.scene)
    restored = restore(DONOR, groups)
    board_set = head_boards(groups)
    remove_old_routes()
    routes = add_routes(groups)
    shell_collection = bpy.data.collections["01 — R05 SOLID EXTERIOR"]
    shell_collection.name = "01 — DRUM SHELLS — CLICK EYE FOR INTERNALS"
    scene = bpy.context.scene
    scene.name = "DeepReal Enclosure Refinement R14"
    scene["DeepReal_Status"] = (
        "complete visual assembly concept with drive and head electronics; "
        "engineering readiness BLOCKED")
    scene["R14_Drum_Internals"] = (
        "original motion/component envelopes restored; one provisional "
        "head-PCBA envelope per drum; routes conceptual")
    scene["R14_View_Control"] = (
        "toggle collection 00 for housing; toggle collection 01 for "
        "drum shells while inspecting internal parts")
    scene["R14_Limits"] = (
        "motor, gearbox, bearing, PCB, flex, feedthrough, thermal, optical "
        "and mounting details unvalidated")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    rows = inventory(groups)
    MANIFEST.write_text(json.dumps({
        "model": str(OUTPUT), "donor": str(DONOR),
        "restored_source_parts": len(restored),
        "head_board_count": len(board_set),
        "route_sets": len(routes),
        "assembly_parts": rows,
        "engineering_readiness": "BLOCKED",
    }, indent=2) + "\n")
    print("R14 SAVED", OUTPUT, "restored", len(restored),
          "total new", len(rows))


if __name__ == "__main__":
    main()
