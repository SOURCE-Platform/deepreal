#!/usr/bin/env python3
"""Sample RGB sightlines against the existing R16 outer housing."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "r08"))
from verify_r08 import tree  # noqa: E402

SOURCE = HERE / "deepreal-wide-interaction-optics-r20.blend"
REPORT = HERE / "r20-rgb-cone-check.json"


def center(obj):
    return sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices),
               Vector()) / len(obj.data.vertices)


def direction(tilt_deg, horizontal_deg, vertical_deg):
    horizontal = math.radians(horizontal_deg)
    down = math.radians(tilt_deg + vertical_deg)
    return Vector((math.sin(horizontal),
                   -math.cos(horizontal) * math.cos(down),
                   -math.cos(horizontal) * math.sin(down))).normalized()


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    housing = tree(bpy.data.objects["Main_Housing"])
    rows = {}
    for side, base, vfov, hfov, poses in (
        ("Face", 0, 41, 66, (-45, 0, 45)),
        ("Interaction", 45, 67, 102, (0, 22.5, 45)),
    ):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        lens = bpy.data.objects[side + "_Drum_Lens_RGB_Element"]
        for angle in poses:
            pivot.rotation_euler.x = math.radians(angle - base)
            bpy.context.view_layer.update()
            shell = tree(bpy.data.objects[side + "_Sensor_Head"])
            origin = center(lens)
            housing_samples = {}
            shell_samples = {}
            for horizontal in (-hfov / 2, 0, hfov / 2):
                for vertical in (-vfov / 2, 0, vfov / 2):
                    ray = direction(angle, horizontal, vertical)
                    hit = housing.ray_cast(origin + ray * .0005, ray, .25)
                    key = f"h{horizontal:+g}_v{vertical:+g}"
                    housing_samples[key] = hit[0] is not None
                    shell_samples[key] = (shell.ray_cast(
                        origin + ray * .0005, ray, .25)[0] is not None)
            rows[f"{side}_{angle:+g}"] = {
                "optical_down_deg": angle,
                "fov_h_deg": hfov,
                "fov_v_deg": vfov,
                "housing_blocked_samples": [key for key, blocked
                                            in housing_samples.items()
                                            if blocked],
                "shell_blocked_samples": [key for key, blocked
                                          in shell_samples.items() if blocked],
                "sample_count": len(housing_samples),
            }
        pivot.rotation_euler.x = 0
    report = {
        "source": str(SOURCE),
        "method": "Nine rays from the modeled RGB cover center to the existing shell and housing at each pose; this is not a full aperture or field clearance proof.",
        "limits": [
            "The retained R16 housing and lens windows predate the wide-lens choice.",
            "The modeled RGB modules are visual proxies, not true sensor assembly CAD.",
            "Full entrance-pupil rays, window edge clearance and depth/IR overlap remain unverified.",
        ],
        "poses": rows,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print("R20 RGB CONE", REPORT)
    for name, value in rows.items():
        print(name, "housing", value["housing_blocked_samples"],
              "shell", value["shell_blocked_samples"])


if __name__ == "__main__":
    main()
