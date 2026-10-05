#!/usr/bin/env python3
"""Validate visible optics against drum bores and check end closures."""

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, tree  # noqa: E402

SOURCE = HERE.parent / "r10" / "deepreal-exterior-refinement-r10.blend"
OUTPUT = HERE / "deepreal-exterior-refinement-r11.blend"
REPORT = HERE / "r11-verification.json"
APERTURES = ("Depth", "RGB", "ProjA", "ProjB", "Pinhole")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def center(obj):
    return sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices),
               Vector()) / len(obj.data.vertices)


def ray_results():
    outcomes = {}
    for prefix, drum_name, angle in (
            ("Face", "Face_Sensor_Head", 0),
            ("Interaction", "Interaction_Sensor_Head", 45)):
        axis = Vector((0, -math.cos(math.radians(angle)),
                       -math.sin(math.radians(angle))))
        shell = tree(bpy.data.objects[drum_name])
        for aperture in APERTURES:
            obj = bpy.data.objects[prefix + "_Drum_Lens_" + aperture]
            origin = center(obj) - axis * 0.005
            hit = shell.ray_cast(origin, axis, 0.008)[0]
            outcomes[prefix + "_" + aperture] = hit is not None
    return outcomes


def manifold(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    bad = sum(not edge.is_manifold for edge in mesh.edges)
    mesh.free()
    return bad == 0


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    before = ray_results()
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    after = ray_results()
    checks = []

    def record(label, okay, evidence):
        checks.append({"check": label, "pass": bool(okay),
                       "evidence": evidence})

    record("R10 baseline reproduces five misaligned interaction windows",
           all(before["Interaction_" + name] for name in APERTURES)
           and not any(before["Face_" + name] for name in APERTURES), before)
    record("all five interaction lens centers now ray through their openings",
           not any(after.values()), after)

    lens_objs = [obj for obj in bpy.data.objects
                 if obj.name.startswith("Interaction_Drum_Lens_")
                 and obj.type == "MESH"]
    angles = {obj.name: round(math.degrees(
        obj.matrix_world.to_euler().x), 3) for obj in lens_objs}
    record("every retained interaction lens component rotates with its window",
           len(lens_objs) >= 10 and all(abs(v - 45) < 0.01
                                        for v in angles.values()), angles)

    cap_results = {}
    for drum_name in ("Face_Sensor_Head", "Interaction_Sensor_Head"):
        drum = bpy.data.objects[drum_name]
        drum_x = bounds_mm(drum)[0]
        for side, expected_x, sign in (
                ("Left", drum_x[0], 1), ("Right", drum_x[1], -1)):
            name = drum_name + "_Closed_End_" + side
            cap = bpy.data.objects[name]
            cap_x = bounds_mm(cap)[0]
            origin = Vector(((expected_x - sign) * 0.001, -0.0015, 0.020))
            hit = tree(cap).ray_cast(origin, Vector((sign, 0, 0)), 0.005)[0]
            cap_results[name] = {
                "manifold": manifold(cap),
                "flush_with_drum_end_mm": abs(
                    (cap_x[0] if sign == 1 else cap_x[1]) - expected_x),
                "axial_center_ray_hits_cap": hit is not None}
    record("both drums have opaque faces at both ends",
           len(cap_results) == 4 and all(
               c["manifold"] and c["flush_with_drum_end_mm"] < 0.02
               and c["axial_center_ray_hits_cap"]
               for c in cap_results.values()), cap_results)

    board = bpy.data.objects["Main_PCBA_Continuous_Right_USB_Tab_PROPOSAL"]
    record("R10 continuous board retained",
           manifold(board) and bpy.data.objects.get(
               "Main_PCBA_Right_USB_Tab_GEOMETRY_PROPOSAL") is None,
           {"manifold": manifold(board), "bounds_mm": bounds_mm(board)})

    baseline = json.loads((HERE / "baseline.json").read_text())
    protected = {name: {"expected": expected,
                        "actual": sha256(REPO / name)}
                 for name, expected in baseline[
                     "protected_files_sha256"].items()}
    record("R10 and source KiCad files unchanged",
           all(item["expected"] == item["actual"]
               for item in protected.values()), protected)
    status = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    # The refinement directory is expected to change from untracked to
    # committed; compare only unrelated pre-existing worktree changes.
    unrelated = lambda rows: [row for row in rows
                              if not row[3:].startswith("blender/refinements/")]
    record("unrelated prework Git changes are preserved",
           unrelated(status) == unrelated(baseline["git_status_before"]),
           {"before": unrelated(baseline["git_status_before"]),
            "after": unrelated(status)})

    report = {"file": str(OUTPUT),
              "result": "PASS" if all(c["pass"] for c in checks) else "FAIL",
              "checks": checks, "engineering_readiness": "BLOCKED",
              "limits": [
                  "Lens alignment is visual geometry, not optical calibration.",
                  "Drum end caps are visual closures, not bearing or seal designs.",
                  "Website exterior views remain draft renders.",
                  "USB, PCB, thermal and motor engineering remain unresolved."]}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
