#!/usr/bin/env python3
"""Measure the R30 drum/encoder interface without changing the Blender model."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT / "blender/refinements/r21"))
from r21_mechanism import (INNER_BEARING_BORE_RADIUS_MM,
                           OUTER_SPINDLE_BORE_RADIUS_MM)  # noqa: E402

MODEL = ROOT / "blender/refinements/r30/deepreal-monitor-ledge-enclosure-r30.blend"
REPORT = ROOT / "docs/electrical/drum-interface-measurement-2026-10-09.json"
HEAD_INTERFACE = ROOT / "hardware/electronics/deepreal-main-pcba/head-interface-evidence.json"
MM = 1000.0


def bounds_mm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(point[axis] for point in corners) * MM,
             max(point[axis] for point in corners) * MM]
            for axis in range(3)]


def center(bounds):
    return [(low + high) / 2 for low, high in bounds]


def axial_gap(first, second):
    a0, a1 = first[0]
    b0, b1 = second[0]
    return max(b0 - a1, a0 - b1, 0.0)


def measure(side):
    pivot = bpy.data.objects[f"{side}_Rotating_Drum_Pivot_R15"]
    pivot_mm = [value * MM for value in pivot.matrix_world.translation]
    objects = {
        "magnet": f"{side}_End_Encoder_Magnet_R21",
        "sensor_ic_envelope": f"{side}_End_Encoder_IC_ENV_R21",
        "sensor_board_envelope": f"{side}_End_Encoder_PCB_ENV_R21",
        "outer_fixed_spindle": f"{side}_Outer_Hollow_Fixed_Spindle_ENV_R21",
        "outer_bearing": f"{side}_Outer_Bearing_ENV_R21",
        "motor": f"{side}_Center_Fed_Motor_Stator_ENV_R21",
        "pinion": f"{side}_Motor_Pinion_ENV_R21",
        "ring_gear": f"{side}_Internal_Ring_Gear_ENV_R21",
    }
    boxes = {role: bounds_mm(bpy.data.objects[name])
             for role, name in objects.items()}
    magnet = center(boxes["magnet"])
    sensor = center(boxes["sensor_ic_envelope"])
    motor = center(boxes["motor"])
    pinion = center(boxes["pinion"])
    return {
        "pivot_center_xyz_mm": pivot_mm,
        "object_bounds_xyz_mm": boxes,
        "magnet_center_xyz_mm": magnet,
        "sensor_package_center_proxy_xyz_mm": sensor,
        "magnet_radial_offset_from_drum_axis_mm": math.dist(magnet[1:], pivot_mm[1:]),
        "sensor_radial_offset_from_drum_axis_mm": math.dist(sensor[1:], pivot_mm[1:]),
        "magnet_to_ic_axial_surface_gap_mm": axial_gap(
            boxes["magnet"], boxes["sensor_ic_envelope"]),
        "motor_radial_offset_from_drum_axis_mm": math.dist(motor[1:], pivot_mm[1:]),
        "pinion_radial_offset_from_drum_axis_mm": math.dist(pinion[1:], pivot_mm[1:]),
        "moving_flex_object": f"{side}_Moving_Head_Flex_PROXY_R21",
        "fixed_harness_object": f"{side}_Fixed_Harness_PROXY_R21",
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    bpy.context.view_layer.update()
    drums = {side: measure(side) for side in ("Face", "Interaction")}
    connector = json.loads(HEAD_INTERFACE.read_text())["connector"]
    fpc_end_width = connector["fpc_end_width_mm"]
    contact_span = ((connector["contacts"] - 1) *
                    connector["mating_contact_pitch_mm"])
    spindle_bore = 2 * OUTER_SPINDLE_BORE_RADIUS_MM
    inner_bearing_bore = 2 * INNER_BEARING_BORE_RADIUS_MM
    result = {
        "source_blend": str(MODEL),
        "units": "mm",
        "drums": drums,
        "outer_exit_screen": {
            "spindle_bore_diameter_mm": spindle_bore,
            "connector_fpc_end_width_mm": fpc_end_width,
            "minimum_contact_center_span_mm": contact_span,
            "minimum_width_deficit_mm": fpc_end_width - spindle_bore,
            "source": "R21 mechanism bore and head-interface-evidence.json",
            "finding": "The specified 15.6 mm FPC connector end cannot pass through the modeled 2 mm bore. A straight 0.3 mm-pitch contact run spans 15 mm. Any narrower moving section requires a new flex construction and verified assembly path.",
        },
        "inner_exit_screen": {
            "inner_bearing_bore_diameter_mm": inner_bearing_bore,
            "connector_fpc_end_width_mm": fpc_end_width,
            "nominal_diametral_width_margin_mm": inner_bearing_bore - fpc_end_width,
            "finding": "The large inner bearing has nominal straight width for the FPC end, but no bend allowance. The center divider remains solid and the motor bracket occupies part of the inner drum volume; this is not a routed cable path.",
        },
        "as5600l_adapter_guide": {
            "source": "ams OSRAM UG000345 v2-00, page 5",
            "url": "https://look.ams-osram.com/m/b03a90ea3dea434a/original/AS5600L_UG000345_2-00.pdf",
            "magnet_centering": "center over or under the Hall array",
            "reference_air_gap_mm": [0.5, 3.0],
            "reference_diametric_magnet_mm": [6.0, 2.5],
        },
        "assessment": (
            "BLOCKED: the magnet and sensor package envelopes are about 6 mm "
            "off the drum axis. Their nominal axial gap is about 0.05 mm, "
            "below the cited adapter-guide range. Hall-array offset inside "
            "the package and actual magnetic field remain unmeasured. Moving "
            "both parts onto the outer axis would conflict with the proposed "
            "hollow flex exit unless the architecture changes. The specified "
            "FPC end is also wider than the modeled spindle bore."
        ),
        "limitations": [
            "R21 parts are envelopes, not selected bearings, motor, magnet or PCB",
            "bounding-box center is a proxy for the sensor Hall-array center",
            "no magnetic simulation, interference test or flex-bend sweep",
            "no manufacturing tolerance or assembly clearance included",
        ],
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    for side, drum in drums.items():
        print(side, "magnet offset", round(drum["magnet_radial_offset_from_drum_axis_mm"], 3),
              "sensor offset", round(drum["sensor_radial_offset_from_drum_axis_mm"], 3),
              "axial gap", round(drum["magnet_to_ic_axial_surface_gap_mm"], 3))
    print("REPORT", REPORT)


if __name__ == "__main__":
    main()
