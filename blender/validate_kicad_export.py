#!/usr/bin/env python3
"""Validate the KiCad-to-Blender data boundary and release lock."""

from pcba_bom import ALL_PARTS
from pcba_kicad_data import (blender_to_board, board_to_blender, load,
                             public_ready)


def main():
    payload = load()
    board = payload["board"]
    bounds = board["bounds_mm"]
    width = bounds[2] - bounds[0]
    depth = bounds[3] - bounds[1]
    failures = []
    open_issues = []
    gates = payload.get("validation_status", {})
    placement_passed = gates.get("G8") == "PASS"
    if abs(width - 90.0) > 0.001 or abs(depth - 28.0) > 0.001:
        failures.append("outline is not exactly 90 x 28 mm")
    if abs(board["thickness_mm"] - 1.6) > 0.001:
        failures.append("board thickness is not 1.6 mm")
    refs = [item["ref"] for item in payload["components"]]
    if len(refs) != len(set(refs)):
        failures.append("duplicate component references")
    for item in payload["components"]:
        x, y = item["position_mm"]
        bx, bz = board_to_blender(x, y, bounds)
        if not (-45.01 <= bx <= 45.01 and -25.51 <= bz <= 2.51):
            failures.append(item["ref"] + " origin leaves board")
        rx, ry = blender_to_board(bx, bz, bounds)
        if abs(rx - x) > 0.001 or abs(ry - y) > 0.001:
            failures.append(item["ref"] + " fails coordinate round trip")
    by_ref = {item["ref"]: item for item in payload["components"]}
    for part in ALL_PARTS:
        item = by_ref.get(part["ref"])
        if item is None:
            message = part["ref"] + " missing from canonical KiCad board"
            (failures if placement_passed else open_issues).append(message)
            continue
        bx, bz = board_to_blender(*item["position_mm"], bounds)
        if not placement_passed and (
                abs(bx - part["x"]) > 0.1 or abs(bz - part["z"]) > 0.1):
            open_issues.append(part["ref"] + " differs from concept metadata")
        if not placement_passed and item["side"] != part["side"]:
            open_issues.append(part["ref"] + " side differs from concept metadata")
    if public_ready(payload) and (gates.get("G10") != "PASS"
                                  or not payload["tracks"]):
        failures.append("public-ready export lacks a passed routed-review gate")
    if failures:
        raise RuntimeError("\n".join(failures))
    print("KICAD EXPORT METRICS")
    print("  board: {:.2f} x {:.2f} x {:.2f} mm".format(
        width, depth, board["thickness_mm"]))
    print("  components / pads / holes: {} / {} / {}".format(
        len(payload["components"]), len(payload["pads"]),
        len(payload["holes"])))
    print("  tracks / vias / zones: {} / {} / {}".format(
        len(payload["tracks"]), len(payload["vias"]), len(payload["zones"])))
    for issue in open_issues:
        print("  OPEN:", issue)
    print("PASS: coordinate conversion, canonical export, and release lock are truthful")


if __name__ == "__main__":
    main()
