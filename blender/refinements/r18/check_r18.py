#!/usr/bin/env python3
"""Sample support clearance and front-facing aperture exposure."""

import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-rear-support-study-r18.blend"
REPORT = HERE / "r18-sweep-check.json"
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402


def angular_distance(left, right):
    return (left - right + 180.0) % 360.0 - 180.0


def front_overlap_deg(center, width):
    # The camera-facing half-cylinder is -90 to +90 degrees, where 0 is front.
    step = .25
    return round(sum(abs(angular_distance(-90 + i * step, center)) <
                     width / 2 for i in range(721)) * step, 2)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    report = {"model": str(MODEL), "samples": {}, "limits": [
        "Angular front exposure does not account for housing occlusion or side views.",
        "Triangle overlap tests are not tolerance or flexible-cable checks.",
        "Bearings, motor, encoder, load path and assembly are envelopes only.",
    ]}
    for side, base, center, width, angles in (
            ("Face", 0, 180, 186, range(-75, 76, 15)),
            ("Interaction", 45, 195, 42, range(45, 76, 15))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        arms = [bpy.data.objects[side + "_Rear_Arm_" + label + "_R18"]
                for label in ("Inner", "Outer")]
        rows = {}
        for angle in angles:
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            rotating = [tree(bpy.data.objects[side + "_" + suffix])
                        for suffix in ("Sensor_Head",
                                       "Rear_Access_Cover_REMOVABLE_CONCEPT")]
            hits = {arm.name: sum(len(tree(arm).overlap(part))
                                  for part in rotating) for arm in arms}
            rows[str(angle)] = {
                "arm_shell_triangle_hits": hits,
                "potential_front_facing_slot_deg": front_overlap_deg(
                    center - (angle - base), width),
            }
        pivot.rotation_euler.x = 0
        bpy.context.view_layer.update()
        report["samples"][side] = rows
    report["arm_shell_clear_at_samples"] = all(
        not any(row["arm_shell_triangle_hits"].values())
        for rows in report["samples"].values() for row in rows.values())
    report["slots_never_face_front_at_samples"] = all(
        row["potential_front_facing_slot_deg"] == 0
        for rows in report["samples"].values() for row in rows.values())
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print("R18 CHECK", REPORT)
    print("arm-shell clear", report["arm_shell_clear_at_samples"])
    print("slots never front-facing",
          report["slots_never_face_front_at_samples"])
    for side, rows in report["samples"].items():
        print(side, [(angle, value["potential_front_facing_slot_deg"])
                     for angle, value in rows.items()])


if __name__ == "__main__":
    main()
