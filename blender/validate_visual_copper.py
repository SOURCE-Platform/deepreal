#!/usr/bin/env python3
"""Validate the shared investor-facing PCBA copper visualization."""

import json
import os
import sys

import bpy


HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pcba_bom import ALL_PARTS, BOARD  # noqa: E402
from pcba_visual_layout import (  # noqa: E402
    DISCLAIMER, POURS, TEST_PADS, TRACE_GROUPS, VIAS,
)


MOUNT_POINTS = ((-42, -22.5), (-42, -.5), (42, -22.5), (42, -.5))


def _inside_board(x, z, margin=0.15):
    return (-BOARD["width"] / 2 + margin <= x <= BOARD["width"] / 2 - margin
            and BOARD["center_z"] - BOARD["depth"] / 2 + margin <= z
            <= BOARD["center_z"] + BOARD["depth"] / 2 - margin)


def _clear_of_mounts(x, z, clearance=1.6):
    return all((x - hx) ** 2 + (z - hz) ** 2 >= clearance ** 2
               for hx, hz in MOUNT_POINTS)


def main():
    failures = []
    expected_paths = sum(len(group["paths"]) for group in TRACE_GROUPS)
    visual = [obj for obj in bpy.data.objects if obj.get("PCBA_Visual_Copper")]
    trace_objects = [obj for obj in visual if obj.name.startswith("Visual_")
                     and obj.get("PCBA_Trace_Class")]
    via_objects = [obj for obj in visual if obj.name.startswith("Visual_Via_")]
    test_objects = [obj for obj in visual if obj.name.startswith("Visual_TP")]
    if len(trace_objects) != expected_paths:
        failures.append("{} trace objects != {} shared paths".format(
            len(trace_objects), expected_paths))
    if len(via_objects) != len(VIAS):
        failures.append("{} via objects != {} shared vias".format(
            len(via_objects), len(VIAS)))
    if len(test_objects) != len(TEST_PADS):
        failures.append("{} test pads != {} shared pads".format(
            len(test_objects), len(TEST_PADS)))

    for group in TRACE_GROUPS:
        if group["side"] not in {"TOP", "BOTTOM"}:
            failures.append(group["name"] + " has invalid side")
        if group["class"] == "DIFF_PAIR" and len(group["paths"]) % 2:
            failures.append(group["name"] + " has unmatched differential lane")
        if "Power" in group["name"] and group["width"] < 0.30:
            failures.append(group["name"] + " power path is too narrow visually")
        for path in group["paths"]:
            if len(path) < 2:
                failures.append(group["name"] + " contains a one-point path")
            for x, z in path:
                if not _inside_board(x, z):
                    failures.append("{} point {:.2f},{:.2f} leaves board".format(
                        group["name"], x, z))
                if not _clear_of_mounts(x, z):
                    failures.append("{} enters a mounting keep-out".format(
                        group["name"]))
    for item in VIAS + TEST_PADS:
        if not _inside_board(item["x"], item["z"]):
            failures.append("via/pad leaves board")
        if not _clear_of_mounts(item["x"], item["z"]):
            failures.append("via/pad enters a mounting keep-out")
    for pour in POURS:
        x, z = pour["center"]
        width, depth = pour["size"]
        for corner in ((x - width / 2, z - depth / 2),
                       (x + width / 2, z + depth / 2)):
            if not _inside_board(*corner):
                failures.append(pour["name"] + " leaves board")

    parts = {part["ref"]: part for part in ALL_PARTS}
    u1, u4 = parts["U1"], parts["U4"]
    gap = ((u4["x"] - u4["width"] / 2)
           - (u1["x"] + u1["width"] / 2))
    if gap < 1.5:
        failures.append("U1/U4 visual body gap {:.2f} mm < 1.50 mm".format(gap))

    summary_path = os.path.join(
        os.path.dirname(HERE), "hardware", "electronics",
        "deepreal-main-pcba", "visual-layout-summary.json")
    if not os.path.exists(summary_path):
        failures.append("visual-layout-summary.json missing")
    else:
        with open(summary_path, encoding="utf-8") as stream:
            summary = json.load(stream)
        if summary.get("fabrication_allowed") is not False:
            failures.append("visual summary does not prohibit fabrication")
        if summary.get("disclaimer") != DISCLAIMER:
            failures.append("visual summary disclaimer drift")
        if summary.get("trace_paths") != expected_paths:
            failures.append("KiCad/Blender trace count mismatch")

    if failures:
        raise RuntimeError("\n".join(sorted(set(failures))))
    print("VISUAL COPPER METRICS")
    print("  trace groups / paths: {} / {}".format(
        len(TRACE_GROUPS), expected_paths))
    print("  visual vias / test pads / pours: {} / {} / {}".format(
        len(VIAS), len(TEST_PADS), len(POURS)))
    print("  U1-to-U4 package gap: {:.2f} mm".format(gap))
    print("PASS: shared KiCad/Blender production-intent visual contract")


if __name__ == "__main__":
    main()
