#!/usr/bin/env python3
"""Verify the R16 opening shift preserves the R15 optics and assembly."""

import bmesh
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import bounds_mm, signature, tree  # noqa: E402
sys.path.insert(0, str(HERE.parent / "r13"))
from verify_r13 import lens_results  # noqa: E402
sys.path.insert(0, str(HERE.parent / "r15"))
from verify_r15 import travel_check  # noqa: E402

BEFORE = HERE.parent / "r15/deepreal-exterior-refinement-r15.blend"
AFTER = HERE / "deepreal-exterior-refinement-r16.blend"
REPORT = HERE / "r16-verification.json"


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def capture_unchanged():
    names = ["Main_Housing", "Thermal_Spreader", "Shield_Rear_Tray",
             "Face_Sensor_Head", "Face_Rear_Access_Cover_REMOVABLE_CONCEPT",
             "Face_Head_PCBA_Carrier_CONCEPT",
             "Interaction_Head_PCBA_Carrier_CONCEPT"]
    names += [side + "_Drum_Lens_" + aperture
              for side in ("Face", "Interaction")
              for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole")]
    return {name: (signature(bpy.data.objects[name]),
                   tuple(round(v, 9)
                         for row in bpy.data.objects[name].matrix_world
                         for v in row)) for name in names}


def topology(obj):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    row = {"faces": len(mesh.faces),
           "non_manifold_edges": sum(not edge.is_manifold
                                     for edge in mesh.edges)}
    mesh.free()
    return row


def cover_angle(obj):
    # Angle relative to the straight rear (+Y) direction in the saved pose.
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mean = sum(points, Vector()) / len(points)
    return round(math.degrees(math.atan2(
        mean.z - .020, mean.y + .0015)), 2)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BEFORE))
    before = capture_unchanged()
    source_hash = sha256(BEFORE)
    bpy.ops.wm.open_mainfile(filepath=str(AFTER))
    checks = []

    def check(label, passed, evidence):
        checks.append({"check": label, "pass": bool(passed),
                       "evidence": evidence})

    after = capture_unchanged()
    preserved = {name: before[name] == after[name] for name in before}
    check("R15 housing, face drum, boards and all lens positions unchanged",
          all(preserved.values()), preserved)

    shell = bpy.data.objects["Interaction_Sensor_Head"]
    cover = bpy.data.objects[
        "Interaction_Rear_Access_Cover_REMOVABLE_CONCEPT"]
    angles = {side: cover_angle(bpy.data.objects[
        side + "_Rear_Access_Cover_REMOVABLE_CONCEPT"])
        for side in ("Face", "Interaction")}
    check("interaction cover is lower at saved pose",
          angles["Interaction"] < angles["Face"] - 20
          and shell["R15_Opening_Angle_At_Saved_Pose_deg"] == -25.0,
          {"cover_center_angles_deg": angles,
           "interaction_cutter_angle_deg":
           shell["R15_Opening_Angle_At_Saved_Pose_deg"]})

    topo = {obj.name: topology(obj) for obj in (
        bpy.data.objects["Face_Sensor_Head"],
        bpy.data.objects["Face_Rear_Access_Cover_REMOVABLE_CONCEPT"],
        shell, cover)}
    check("both shells and covers remain closed meshes",
          all(row["faces"] > 0 and row["non_manifold_edges"] == 0
              for row in topo.values()), topo)
    overlaps = {"shell_cover": len(tree(shell).overlap(tree(cover)))}
    for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole"):
        lens = bpy.data.objects["Interaction_Drum_Lens_" + aperture]
        overlaps["cover_" + aperture] = len(tree(cover).overlap(tree(lens)))
    check("shifted cover clears interaction optics and shell",
          not any(overlaps.values()), overlaps)
    lens_rays = lens_results()
    check("all ten lens-center passages remain open",
          all(lens_rays.values()), lens_rays)

    travel = travel_check()
    check("sampled drum travel clears fixed parts and housing",
          all(not row["fixed_part_or_housing_intersections"] and
              not row["housing_blocked_lens_center_rays"]
              for row in travel.values()), travel)
    face_end = bounds_mm(bpy.data.objects["Face_Sensor_Head"])[0][1]
    interaction_start = bounds_mm(shell)[0][0]
    check("one-millimeter drum gap remains",
          abs(interaction_start - face_end - 1) < .001,
          {"face_end_mm": face_end,
           "interaction_start_mm": interaction_start})

    current_hash = sha256(BEFORE)
    check("R15 source file remains unchanged", current_hash == source_hash,
          {"before_sha256": source_hash, "after_sha256": current_hash})
    report = {"model": str(AFTER),
              "result": "PASS" if all(row["pass"] for row in checks)
              else "FAIL", "checks": checks,
              "visual_review": (
                  "At the tested 75-degree-down high-front camera, the "
                  "interaction opening and seam are hidden. This is not "
                  "a guarantee for every viewpoint or future travel range."),
              "engineering_readiness": "BLOCKED"}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(report["result"], REPORT)
    for row in checks:
        print("PASS" if row["pass"] else "FAIL", row["check"])
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
