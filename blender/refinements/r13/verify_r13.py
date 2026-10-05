#!/usr/bin/env python3
"""Verify the visible drum gap, face clearance, and protected R12 model."""

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
from verify_r08 import bounds_mm, signature, tree  # noqa: E402

SOURCE = HERE.parent / "r12" / "deepreal-exterior-refinement-r12.blend"
BLEND = HERE / "deepreal-exterior-refinement-r13.blend"
REPORT = HERE / "r13-verification.json"
DRUMS = ("Face_Sensor_Head", "Interaction_Sensor_Head")
APERTURES = ("Depth", "RGB", "ProjA", "ProjB", "Pinhole")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifold(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bad = sum(not edge.is_manifold for edge in bm.edges)
    bm.free()
    return bad == 0


def center(obj):
    return sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices),
               Vector()) / len(obj.data.vertices)


def lens_results():
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
            outcomes[prefix + "_" + aperture] = (
                shell.ray_cast(origin, axis, 0.008)[0] is None)
    return outcomes


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    before = {
        name: signature(bpy.data.objects[name])
        for name in ("Main_PCBA_Near_Full_Height_Right_Wing_PROPOSAL",
                     "Main_Housing", "USB_C_Direct_Board_Socket_ENVELOPE_UNSELECTED")}
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    checks = []

    def record(label, okay, evidence):
        checks.append({"check": label, "pass": bool(okay),
                       "evidence": evidence})

    left = bpy.data.objects[DRUMS[0]]
    right = bpy.data.objects[DRUMS[1]]
    left_end = bounds_mm(left)[0][1]
    right_start = bounds_mm(right)[0][0]
    body_gap = round(right_start - left_end, 5)
    record("drum bodies have a 1.0 mm center gap",
           abs(body_gap - 1.0) < 0.001 and manifold(left)
           and manifold(right),
           {"left_end_x_mm": left_end, "right_start_x_mm": right_start,
            "body_gap_mm": body_gap,
            "shells_manifold": [manifold(left), manifold(right)]})

    face_left = bpy.data.objects["Face_Sensor_Head_Flat_End_Right"]
    face_right = bpy.data.objects["Interaction_Sensor_Head_Flat_End_Left"]
    cap_gap = round(bounds_mm(face_right)[0][0] -
                    bounds_mm(face_left)[0][1], 5)
    overlap_faces = len(tree(face_left).overlap(tree(face_right)))
    opposing = (len(tree(face_left).overlap(tree(right))) +
                len(tree(face_right).overlap(tree(left))))
    record("flat center faces have visible clearance and no intersection",
           abs(cap_gap - 0.52) < 0.001 and overlap_faces == 0
           and opposing == 0,
           {"visible_face_gap_mm": cap_gap,
            "face_to_face_triangle_intersections": overlap_faces,
            "face_to_opposing_shell_triangle_intersections": opposing})

    optics = lens_results()
    record("all ten lens centers still pass through their drum openings",
           all(optics.values()), optics)

    preserved = {name: signature(bpy.data.objects[name]) == sig
                 for name, sig in before.items()}
    record("PCB, housing and USB socket are unchanged from R12",
           all(preserved.values()), preserved)

    housing = bpy.data.collections[
        "00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME"]
    visible = not housing.hide_render and not bpy.data.objects[
        "Main_Housing"].hide_render
    record("outer enclosure is enabled in saved model",
           visible, {"housing_collection_renders": not housing.hide_render,
                     "main_housing_renders": not bpy.data.objects[
                         "Main_Housing"].hide_render})

    baseline = json.loads((HERE / "baseline.json").read_text())
    protected = {name: sha256(REPO / name) == expected
                 for name, expected in baseline[
                     "protected_files_sha256"].items()}
    record("R12 and native PCB sources remain unchanged",
           all(protected.values()), protected)
    status = subprocess.check_output(
        ["git", "status", "--short"], cwd=REPO, text=True).splitlines()
    # Committing this refinement removes its old untracked-directory entry.
    unrelated = lambda rows: [row for row in rows
                              if not row[3:].startswith("blender/refinements/")]
    record("unrelated prework Git changes are preserved",
           unrelated(status) == unrelated(baseline["git_status_before"]),
           {"before": unrelated(baseline["git_status_before"]),
            "after": unrelated(status)})

    report = {
        "file": str(BLEND),
        "result": "PASS" if all(c["pass"] for c in checks) else "FAIL",
        "checks": checks,
        "engineering_readiness": "BLOCKED",
        "limits": [
            "A 1.0 mm body gap is a visual layout choice, not validated running clearance.",
            "Thin end faces remain presentation skins, not manufacturable drum closures.",
            "Thermal expansion, bearing play, runout and assembly tolerances need engineering review.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for check in checks:
        print("PASS" if check["pass"] else "FAIL", check["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
