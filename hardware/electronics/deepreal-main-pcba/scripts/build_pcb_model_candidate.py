#!/usr/bin/env python3
"""Make an internal, unrouted mechanical placement study, not a layout release."""

import argparse
from collections import Counter
import copy
import itertools
import json
import math
import re
from pathlib import Path

from build_pcb_fit_candidate import (
    ROOT, PROJECT, digest, top_level_blocks, validate_inputs, courtyard_candidates,
)
from build_pcb_connector_candidate import children
from head_interface_audit import bounds, rotate
from pcb_fit_geometry import positive_box_overlap


# Preserve compute/DDR placement. Separate the inherited power packages and
# keep the two bridge/protection groups next to their respective head strips.
# These are spatial proposals, not pin-driven placements or part selections.
PREFERRED = {
    "J1": ([116.5, 40.4], 0, "BOTTOM"),
    "J4": ([27, 45.5], 90, "TOP"),
    "J5": ([98, 45.5], 90, "TOP"),
    "U2": ([36.5, 37], 0, "TOP"),
    "U3": ([85.5, 38], 0, "TOP"),
    "D3": ([42, 40], 90, "TOP"),
    "D4": ([45.4, 40], 90, "TOP"),
    "D5": ([48.8, 40], 90, "TOP"),
    "D6": ([91.5, 41.5], 90, "TOP"),
    "D7": ([94.9, 41.5], 90, "TOP"),
    "D8": ([98.3, 41.5], 90, "TOP"),
    "U20": ([54, 42], 0, "TOP"),
    "U21": ([55, 45], 0, "TOP"),
    "U22": ([76.5, 43.5], 0, "TOP"),
    "U5": ([94.5, 27.5], 0, "TOP"),
    "U6": ([83.22, 25], 0, "TOP"),
    "U7": ([83.22, 30.8], 0, "TOP"),
    "L3": ([87.85, 25], 0, "TOP"),
    "L4": ([87.85, 30.8], 0, "TOP"),
    "L5": ([101.5, 21.9], 0, "TOP"),
    "L6": ([101.5, 25.8], 0, "TOP"),
    "L7": ([101.5, 29.7], 0, "TOP"),
    "L8": ([91.5, 34], 0, "TOP"),
    "L9": ([106.2, 32], 0, "TOP"),
    "U8": ([97.5, 34.25], 0, "TOP"),
    "L1": ([94.5, 38], 0, "TOP"),
    "U9": ([102.5, 37.5], 0, "TOP"),
    "L2": ([107, 37.5], 0, "TOP"),
    "U10": ([110, 41], 0, "TOP"),
    "U11": ([113, 33], 0, "TOP"),
    "U18": ([27.5, 27.5], 0, "TOP"),
    "U19": ([107, 28], 0, "TOP"),
    "U12": ([107.5, 34], 180, "BOTTOM"),
    "D1": ([112.5, 32.5], 90, "BOTTOM"),
    "D2": ([116, 32.5], 90, "BOTTOM"),
    "D9": ([116.5, 40.5], 0, "TOP"),
}
LOCKED = {"U1", "U4", "U15", "J2", "J3", "H1", "H2", "H3", "H4"}


def reference(block):
    matches = [b for _, _, b in children(block, "footprint")
               if b.startswith('(property "Reference" ')]
    if len(matches) != 1:
        raise ValueError("ambiguous footprint reference")
    match = re.match(r'\(property "Reference" "([^"]+)"', matches[0])
    if not match:
        raise ValueError("invalid reference")
    return match[1]


def merge_footprints(source, saved, refs):
    """Keep every other source block byte-identical, including Edge.Cuts."""
    blocks, _ = top_level_blocks(source)
    replacements = {}
    for _, _, block in top_level_blocks(saved)[0]:
        if block.startswith("(footprint "):
            ref = reference(block)
            if ref in replacements:
                raise ValueError("duplicate saved reference")
            replacements[ref] = block
    edits = []
    found = set()
    for start, end, block in blocks:
        if block.startswith("(footprint "):
            ref = reference(block)
            if ref in refs:
                edits.append((start, end, replacements[ref]))
                found.add(ref)
    if found != set(refs):
        raise ValueError("missing changed footprint")
    for start, end, block in reversed(edits):
        source = source[:start] + block + source[end:]
    return source


def moved_polygons(component, pose):
    position, angle, side = pose
    old = component["position_mm"]
    polygons = component["courtyard_polygons_mm"]
    original_angle = component["rotation_deg"]
    if side != component["side"]:
        polygons = [[[2 * old[0] - x, y] for x, y in p] for p in polygons]
        original_angle = 180 - original_angle
    return rotate(polygons, old, position, angle - original_angle)


def expanded_overlap(a, b, margin=0.10):
    return min(a[2], b[2]) > max(a[0], b[0]) - margin + 1e-6 and \
        min(a[3], b[3]) > max(a[1], b[1]) - margin + 1e-6


def in_profile(box):
    # Exact six-corner profile bounds for this measured candidate, with the
    # lower-right step retained. No component may bridge the missing corner.
    return box[0] >= 20.15 and box[1] >= 20.15 and box[2] <= 122.35 and \
        box[3] <= (46.35 if box[2] > 110 else 47.85)


def candidate_offsets(radius, step):
    n = round(radius / step)
    values = [(i * step, j * step) for i in range(-n, n + 1)
              for j in range(-n, n + 1) if math.hypot(i * step, j * step) <= radius + 1e-8]
    return sorted(values, key=lambda p: (round(p[0] ** 2 + p[1] ** 2, 8), p))


def plan_placements(layout):
    if layout["board"]["bounds_mm"] != [20, 20, 122.5, 48]:
        raise ValueError("unexpected measured profile")
    by_ref = {c["ref"]: c for c in layout["components"]}
    if not LOCKED <= set(by_ref) or not set(PREFERRED) <= set(by_ref):
        raise ValueError("unexpected population")
    chosen, boxes, hole_boxes = {}, {}, {}
    # Reserve the fifth, unapproved mechanical cutout on both sides. Its
    # keep-out is for this fit study, not a new mounting pad or electrical rule.
    wing_hole = [114.65, 25.15, 119.35, 29.85]

    def drilled_zones(ref, pose):
        result = []
        old = by_ref[ref]
        new = {"position_mm": pose[0], "rotation_deg": pose[1], "side": pose[2]}
        for hole in layout["holes"]:
            if hole["ref"] != ref:
                continue
            point = transformed_point(hole["position_mm"], old, new)
            # Include the annular land, where present, on either board face.
            pads = [p for p in layout["pads"] if p["ref"] == ref and
                    p["number"] == hole["pad"] and
                    math.dist(p["position_mm"], hole["position_mm"]) < 1e-6]
            radius = max(hole["drill_mm"] + [v for p in pads for v in p["size_mm"]]) / 2 + 0.25
            result.append([point[0] - radius, point[1] - radius,
                           point[0] + radius, point[1] + radius])
        return result

    def free(ref, pose):
        box = bounds(moved_polygons(by_ref[ref], pose))
        if not in_profile(box) or expanded_overlap(box, wing_hole):
            return False
        for other, (other_box, other_side) in boxes.items():
            if pose[2] == other_side or ref.startswith("H") or other.startswith("H"):
                margin = 0 if ref in LOCKED and other in LOCKED else 0.10
                if expanded_overlap(box, other_box, margin):
                    return False
        if any(expanded_overlap(box, zone, 0) for zones in hole_boxes.values() for zone in zones):
            return False
        own_zones = drilled_zones(ref, pose)
        if any(expanded_overlap(zone, other_box, 0)
               for zone in own_zones for other_box, _ in boxes.values()):
            return False
        return True

    def add(ref, pose):
        chosen[ref] = pose
        boxes[ref] = (bounds(moved_polygons(by_ref[ref], pose)), pose[2])
        hole_boxes[ref] = drilled_zones(ref, pose)

    for ref in sorted(LOCKED):
        c = by_ref[ref]
        pose = (c["position_mm"], c["rotation_deg"], c["side"])
        if not free(ref, pose):
            raise ValueError("locked placement conflicts: " + ref)
        add(ref, pose)
    # Major items go first; passives remain fixed wherever possible.
    for ref in list(PREFERRED) + sorted(set(by_ref) - LOCKED - set(PREFERRED),
                                      key=lambda r: (r.startswith(("C", "R")), r)):
        c = by_ref[ref]
        preferred = PREFERRED.get(ref, (c["position_mm"], c["rotation_deg"], c["side"]))
        radius = 3.0 if ref in PREFERRED else 6.0
        for dx, dy in candidate_offsets(radius, 0.2):
            pose = ([round(preferred[0][0] + dx, 6), round(preferred[0][1] + dy, 6)],
                    preferred[1], preferred[2])
            if free(ref, pose):
                add(ref, pose)
                break
        else:
            raise ValueError("no local mechanical placement found: " + ref)
    return chosen


def transformed_point(point, old, new):
    original_angle = old["rotation_deg"]
    if old["side"] != new["side"]:
        point = [2 * old["position_mm"][0] - point[0], point[1]]
        original_angle = 180 - original_angle
    return rotate([[point]], old["position_mm"], new["position_mm"],
                  new["rotation_deg"] - original_angle)[0][0]


def verify_layout(before, after):
    old_parts = {c["ref"]: c for c in before["components"]}
    new_parts = {c["ref"]: c for c in after["components"]}
    if old_parts.keys() != new_parts.keys():
        raise ValueError("population changed")
    for ref, old in old_parts.items():
        new = new_parts[ref]
        for key in ("uuid", "ref", "value", "footprint", "models", "model_transforms"):
            if old[key] != new[key]:
                raise ValueError("identity or package changed: " + ref + ":" + key)
        if ref in LOCKED and old != new:
            raise ValueError("locked part changed: " + ref)
    old_pads = {p["uuid"]: p for p in before["pads"]}
    new_pads = {p["uuid"]: p for p in after["pads"]}
    if len(new_pads) != len(after["pads"]) or old_pads.keys() != new_pads.keys():
        raise ValueError("pad identities changed")
    for identity, old in old_pads.items():
        new = new_pads[identity]
        for key in ("uuid", "ref", "number", "net", "net_code", "size_mm", "shape_code"):
            if old[key] != new[key]:
                raise ValueError("pad geometry or identity changed: " + identity)
        a, b = old_parts[old["ref"]], new_parts[old["ref"]]
        expected = transformed_point(old["position_mm"], a, b)
        if math.dist(expected, new["position_mm"]) > 0.000003:
            raise ValueError("pad is not rigidly registered: " + identity)
        if a["side"] != b["side"]:
            angle = 180 - old["rotation_deg"] + b["rotation_deg"] - (180 - a["rotation_deg"])
        else:
            angle = old["rotation_deg"] + b["rotation_deg"] - a["rotation_deg"]
        if abs((new["rotation_deg"] - angle + 180) % 360 - 180) > 1e-6:
            raise ValueError("pad angle is not rigidly registered: " + identity)
        for front, back in (("copper_top", "copper_bottom"),
                            ("mask_open_top", "mask_open_bottom")):
            expected = (old[back], old[front]) if a["side"] != b["side"] else (old[front], old[back])
            if (new[front], new[back]) != expected:
                raise ValueError("pad layers disagree with side: " + identity)
    if before["board"] != after["board"] or after["tracks"] or after["vias"] or after["zones"]:
        raise ValueError("outline/thickness changed or routing added")
    def hole_key(hole):
        return (hole["ref"], hole["pad"], tuple(hole["position_mm"]), tuple(hole["drill_mm"]))
    expected = []
    for hole in before["holes"]:
        moved = dict(hole)
        moved["position_mm"] = transformed_point(
            hole["position_mm"], old_parts[hole["ref"]], new_parts[hole["ref"]])
        expected.append(hole_key(moved))
    if Counter(expected) != Counter(hole_key(hole) for hole in after["holes"]):
        raise ValueError("drill identity, size or registration changed")


def transform_bodies(bodies, old_parts, new_parts, contract):
    result = copy.deepcopy(bodies)
    origin = contract["coordinate_system"]["kicad_origin_mm"]
    height = contract["coordinate_system"]["board_center_height_mm"]
    depth = contract["coordinate_system"]["board_center_web_depth_mm"]
    for ref, item in result.items():
        old, new = old_parts[ref], new_parts[ref]
        lo, hi = item["min_mm"], item["max_mm"]
        points = [[origin[0] + x, origin[1] - (y - height)]
                  for x, y in itertools.product((lo[0], hi[0]), (lo[1], hi[1]))]
        points = [transformed_point(p, old, new) for p in points]
        web = [[p[0] - origin[0], height - (p[1] - origin[1])] for p in points]
        depths = [lo[2], hi[2]]
        if old["side"] != new["side"]:
            depths = [2 * depth - z for z in depths]
        item.update(
            min_mm=[min(p[0] for p in web), min(p[1] for p in web), min(depths)],
            max_mm=[max(p[0] for p in web), max(p[1] for p in web), max(depths)],
            side=new["side"],
            model_status=item["model_status"] + "_MECHANICAL_STUDY_TRANSFORM",
        )
        item["center_mm"] = [(a + b) / 2 for a, b in zip(item["min_mm"], item["max_mm"])]
        item["size_mm"] = [b - a for a, b in zip(item["min_mm"], item["max_mm"])]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predecessor-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    status = json.loads((PROJECT / "design-status.json").read_text())
    validate_inputs(contract, status, args.output_dir)
    before = json.loads((args.predecessor_dir / "engineering-layout-export.json").read_text())
    meta = before["metadata"]
    source = args.predecessor_dir / meta["source_board"]
    if not source.resolve().is_relative_to(ROOT / "tmp") or \
            meta["design_revision"] != "MECH-FIT-02" or digest(source) != meta["source_board_sha256"]:
        raise ValueError("stale or unexpected predecessor")
    if any(meta.get(k) is not False for k in
           ("is_canonical", "fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
        raise ValueError("unlocked predecessor")
    if meta["mechanical_contract_sha256"] != digest(args.contract) or \
            before["tracks"] or before["vias"] or before["zones"] or any(p["net"] for p in before["pads"]):
        raise ValueError("changed contract or connected/routed predecessor")
    poses = plan_placements(before)
    import export_kicad_design as cad
    import pcbnew
    board = pcbnew.LoadBoard(str(source))
    changed = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        position, angle, side = poses[ref]
        old = next(c for c in before["components"] if c["ref"] == ref)
        if (position, angle, side) == (old["position_mm"], old["rotation_deg"], old["side"]):
            continue
        if side != old["side"]:
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(angle)
        fp.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in position]))
        changed.append(ref)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    serialized = output / "serialization-inspection.kicad_pcb"
    pcbnew.SaveBoard(str(serialized), board)
    target = output / "deepreal-main-pcba-mech-fit-03.kicad_pcb"
    target.write_text(merge_footprints(source.read_text(), serialized.read_text(), changed))
    board = pcbnew.LoadBoard(str(target))
    tracks, vias = cad.copper(board)
    layout = {
        "metadata": {**meta, "design_revision": "MECH-FIT-03",
                     "design_status": "INTERNAL_UNROUTED_MECHANICAL_STUDY",
                     "source_board": target.name, "source_board_sha256": digest(target),
                     "predecessor_board_sha256": digest(source)},
        "board": cad.board_outline(board), "components": cad.components(board),
        "pads": cad.pads(board), "holes": cad.holes(board),
        "tracks": tracks, "vias": vias, "zones": cad.zones(board),
        "validation_status": before["validation_status"],
    }
    verify_layout(before, layout)
    old_parts = {c["ref"]: c for c in before["components"]}
    new_parts = {c["ref"]: c for c in layout["components"]}
    retained = json.loads((args.predecessor_dir / "fit-screen.json").read_text())
    bodies = transform_bodies(retained["retained_component_bodies"], old_parts, new_parts, contract)
    body_pairs = [{"refs": [a, b], "overlap_mm": widths}
                  for a, b in itertools.combinations(sorted(bodies), 2)
                  if (widths := positive_box_overlap(bodies[a], bodies[b]))]
    courtyard_pairs = courtyard_candidates(layout["components"])
    if body_pairs or courtyard_pairs:
        raise ValueError("remaining conservative body/courtyard overlaps: " +
                         str(body_pairs + courtyard_pairs))
    report = {
        "schema": "deepreal.pcb-model-candidate.v1", "revision": "MECH-FIT-03",
        "status": "PRELIMINARY_MECHANICAL_PLACEMENT_NOT_ELECTRICAL_RELEASE",
        "source_board_sha256": digest(target), "predecessor_board_sha256": digest(source),
        "mechanical_contract_sha256": digest(args.contract),
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
        "population_preserved": len(layout["components"]),
        "pad_identities_preserved": len(layout["pads"]),
        "fixed_origin_mm": meta["fixed_origin_mm"],
        "body_aabb_overlap_candidates": body_pairs,
        "same_side_courtyard_aabb_candidates": courtyard_pairs,
        "retained_component_bodies": bodies,
        "changed_refs": sorted(changed),
        "moves": [{"ref": ref, "old_pose": {k: old_parts[ref][k] for k in
                   ("position_mm", "rotation_deg", "side")},
                  "new_pose": {k: new_parts[ref][k] for k in
                   ("position_mm", "rotation_deg", "side")}} for ref in sorted(changed)],
        "placement_basis": "Measured outline; unchanged compute/DDR datum; spatial grouping only. "
                           "Passive moves are nearest local clearance corrections, not net-driven decoupling.",
        "unresolved": [
            "All electrical/package/release gates remain unchanged; no circuit/netlist or routing added",
            "U1 generic 324-ball footprint is not the selected 548-ball processor land pattern",
            "Inherited package substitutions and missing-model envelopes remain explicitly unapproved",
            "J1 inherited Amphenol moved to bottom of wing; not selection of it over intended Hirose",
            "USB mating-axis, PCB thickness, retention and plugged housing fit remain unapproved",
            "J4/J5 retain actual tall pin-header placeholders, not approved low-profile motor connectors",
            "FH26/FH26W variant, latch sweep, head numbering and housed dynamic flex remain open",
            "U18/U19 main-board ownership is still unresolved; relocation here is spatial only",
            "SW1 and other intended but absent circuitry were not invented",
        ],
    }
    for name, document in (("engineering-layout-export.json", layout), ("fit-screen.json", report)):
        (output / name).write_text(json.dumps(document, indent=2) + "\n")
    print("Candidate:", target, "Moved:", len(changed))
    print("Conservative body/courtyard overlaps: 0 / 0")
    print("Electrical, enclosure-interface and release approval: BLOCKED")


if __name__ == "__main__":
    main()
