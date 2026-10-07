#!/usr/bin/env python3
"""Check the user-proposed face and interaction optical poses."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODEL = HERE / "deepreal-role-specific-sweep-r19.blend"
REPORT = HERE / "r19-sweep-check.json"
for path in (HERE.parent / "r08", HERE.parent / "r18"):
    sys.path.insert(0, str(path))
from verify_r08 import tree  # noqa: E402
from check_r18 import front_overlap_deg  # noqa: E402


def blocked_lenses(side, angle, housing):
    axis = Vector((0, -math.cos(math.radians(angle)),
                   -math.sin(math.radians(angle))))
    blocked = []
    for aperture in ("Depth", "RGB", "ProjA", "ProjB", "Pinhole"):
        lens = bpy.data.objects[side + "_Drum_Lens_" + aperture]
        center = sum((lens.matrix_world @ vertex.co
                      for vertex in lens.data.vertices), Vector())
        center /= len(lens.data.vertices)
        if housing.ray_cast(center + axis * .0005, axis, .08)[0] is not None:
            blocked.append(aperture)
    return blocked


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    report = {"model": str(MODEL), "samples": {}, "limits": [
        "These are provisional user-proposed angles, not finalized hard stops.",
        "Front-facing slot angle is a geometric exposure estimate; consult renders for actual enclosure occlusion.",
        "Arm-shell triangle overlap is a rough collision check, not a tolerance check.",
        "Bearing load path, motor, encoder, cable and assembly are not designed in this model.",
    ]}
    housing = tree(bpy.data.objects["Main_Housing"])
    for side, base, slot_width, angles in (
            ("Face", 0, 114, (-45, 0, 45)),
            ("Interaction", 45, 102, (0, 45, 90))):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        arms = [bpy.data.objects[side + "_Rear_Arm_" + label + "_R19"]
                for label in ("Inner", "Outer")]
        rows = {}
        for angle in angles:
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            rotating = [tree(bpy.data.objects[side + "_" + suffix])
                        for suffix in ("Sensor_Head",
                                       "Rear_Access_Cover_REMOVABLE_CONCEPT")]
            rows[str(angle)] = {
                "arm_shell_triangle_hits": {
                    arm.name: sum(len(tree(arm).overlap(part))
                                  for part in rotating) for arm in arms},
                "potential_front_facing_slot_deg": front_overlap_deg(
                    180 - (angle - base), slot_width),
                "housing_blocked_lens_centers": blocked_lenses(
                    side, angle, housing),
            }
        pivot.rotation_euler.x = 0
        bpy.context.view_layer.update()
        report["samples"][side] = rows
    report["arm_shell_clear_at_samples"] = all(
        not any(row["arm_shell_triangle_hits"].values())
        for rows in report["samples"].values() for row in rows.values())
    report["lens_centers_clear_at_samples"] = all(
        not row["housing_blocked_lens_centers"]
        for rows in report["samples"].values() for row in rows.values())
    report["slots_never_face_front_at_samples"] = all(
        row["potential_front_facing_slot_deg"] == 0
        for rows in report["samples"].values() for row in rows.values())
    interaction = bpy.data.objects["Interaction_Rotating_Drum_Pivot_R15"]
    blockage = {}
    for angle in range(91):
        interaction.rotation_euler.x = math.radians(angle - 45)
        bpy.context.view_layer.update()
        blocked = blocked_lenses("Interaction", angle, housing)
        if blocked:
            blockage[str(angle)] = blocked
    interaction.rotation_euler.x = 0
    bpy.context.view_layer.update()
    report["interaction_first_center_ray_blocked_deg"] = (
        min(map(int, blockage)) if blockage else None)
    report["interaction_center_ray_blockages_by_degree"] = blockage
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print("R19 CHECK", REPORT)
    for side, rows in report["samples"].items():
        print(side, [(angle, data["potential_front_facing_slot_deg"],
                      data["housing_blocked_lens_centers"])
                     for angle, data in rows.items()])
    print("arm-shell clear", report["arm_shell_clear_at_samples"])
    print("lens centers clear", report["lens_centers_clear_at_samples"])
    print("interaction first center ray blocked at",
          report["interaction_first_center_ray_blocked_deg"])


if __name__ == "__main__":
    main()
