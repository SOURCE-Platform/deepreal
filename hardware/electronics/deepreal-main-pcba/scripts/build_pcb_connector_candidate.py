#!/usr/bin/env python3
"""Branch an unrouted optical-connector placement and stencil study."""

import argparse
import copy
import itertools
import json
import math
import re
import uuid
from pathlib import Path

from build_pcb_fit_candidate import (
    PROJECT, ROOT, courtyard_candidates, digest, top_level_blocks, validate_inputs,
)
from head_interface_audit import bounds, land_pattern_screen, placement_screen, rotate
from pcb_fit_geometry import positive_box_overlap


REFS = ("J2", "J3")
LIBRARY_PART = "Hirose_FH26-51S-0.3SHW_2Rows-51Pins-1MP_P0.60mm_Horizontal"
PASTE = {
    (0.8, 0.3): ((0.65, 0.23), 26),
    (0.65, 0.3): ((0.55, 0.23), 25),
    (0.95, 0.4): ((0.7, 0.3), 2),
}


def children(text, kind):
    """Reuse the quoted-string parser for footprint and pad root children."""
    if not re.match(r"\(" + re.escape(kind) + r"\b", text):
        raise ValueError("unexpected S-expression root")
    delta = len("kicad_pcb") - len(kind)
    wrapped = "(kicad_pcb" + text[len(kind) + 1:]
    blocks, _ = top_level_blocks(wrapped)
    return [(start - delta, end - delta, block) for start, end, block in blocks]


def child(text, kind, name):
    found = [(start, end, block) for start, end, block in children(text, kind)
             if re.match(r"\(" + re.escape(name) + r"\b", block)]
    if len(found) != 1:
        raise ValueError("expected exactly one " + name)
    return found[0]


def coordinates(block, name):
    match = re.fullmatch(r"\(" + name + r"\s+([^()]*)\)", block)
    if not match:
        raise ValueError("unexpected coordinate expression")
    values = [float(v) for v in match[1].split()]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("nonfinite coordinate")
    return values


def replace_ranges(text, edits):
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def turn_child_at(text, kind, angle):
    start, end, block = child(text, kind, "at")
    values = coordinates(block, "at")
    if len(values) not in (2, 3):
        raise ValueError("unexpected placement dimensions")
    current = values[2] if len(values) == 3 else 0
    return replace_ranges(text, [(start, end, "(at {:g} {:g} {:g})".format(
        *values[:2], current + angle))])


def correct_footprint(text, ref, position):
    if not text.startswith('(footprint "' + LIBRARY_PART + '"'):
        raise ValueError("unexpected optical connector library part")
    reference = child(text, "footprint", "layer")[2]
    if reference != '(layer "F.Cu")':
        raise ValueError("optical connector must retain its top mounting side")
    at_start, at_end, at = child(text, "footprint", "at")
    old = coordinates(at, "at")
    if len(old) not in (2, 3) or (len(old) == 3 and old[2] != 0):
        raise ValueError("expected inherited zero-degree connector")
    edits = [(at_start, at_end, "(at {:g} {:g} 90)".format(*position))]
    additions, counts = [], {size: 0 for size in PASTE}
    for start, end, block in children(text, "footprint"):
        if block.startswith("(property ") or block.startswith("(fp_text "):
            kind = "property" if block.startswith("(property ") else "fp_text"
            edits.append((start, end, turn_child_at(block, kind, 90)))
        elif block.startswith("(pad "):
            if not re.match(r'\(pad "(?:\d+|MP)" smd rect\b', block):
                raise ValueError("unexpected contact type")
            size = tuple(coordinates(child(block, "pad", "size")[2], "size"))
            if size not in PASTE:
                raise ValueError("unexpected optical copper pad size")
            counts[size] += 1
            layer_start, layer_end, layers = child(block, "pad", "layers")
            if layers != '(layers "F.Cu" "F.Mask" "F.Paste")' or "solder_paste" in block:
                raise ValueError("unexpected existing paste configuration")
            updated = replace_ranges(block, [
                (layer_start, layer_end, '(layers "F.Cu" "F.Mask")')])
            edits.append((start, end, turn_child_at(updated, "pad", 90)))
            point = coordinates(child(block, "pad", "at")[2], "at")
            if len(point) not in (2, 3) or (len(point) == 3 and point[2] != 0):
                raise ValueError("unexpected contact angle")
            identity = child(block, "pad", "uuid")[2]
            paste_id = uuid.uuid5(uuid.NAMESPACE_URL,
                                 "deepreal:MECH-FIT-02:paste:" + ref + identity)
            aperture = PASTE[size][0]
            additions.append(
                '\n\t\t(pad "" smd rect (at {:g} {:g} 90) (size {:g} {:g}) '
                '(layers "F.Paste") (uuid "{}"))'.format(
                    *point[:2], *aperture, paste_id))
    if counts != {size: spec[1] for size, spec in PASTE.items()}:
        raise ValueError("unexpected optical connector contact counts")
    result = replace_ranges(text, edits)
    # Append paste-only primitives before the footprint terminator. Copper
    # numbers, UUIDs, land patterns, mask openings and models remain intact.
    end = result.rfind(")")
    return result[:end] + "".join(additions) + "\n\t" + result[end:]


def connector_candidate_text(source, positions):
    if set(positions) != set(REFS) or any(
            len(p) != 2 or not all(math.isfinite(v) for v in p)
            for p in positions.values()):
        raise ValueError("exactly two finite optical placements required")
    blocks, _ = top_level_blocks(source)
    edits, changed = [], []
    for start, end, block in blocks:
        if not block.startswith("(footprint "):
            continue
        references = [b for _, _, b in children(block, "footprint")
                      if b.startswith('(property "Reference" ')]
        if len(references) != 1:
            raise ValueError("missing or ambiguous footprint reference")
        ref = next((r for r in REFS if references[0].startswith(
            '(property "Reference" "' + r + '"')), None)
        if ref is not None:
            if ref in changed:
                raise ValueError("duplicate optical reference")
            edits.append((start, end, correct_footprint(block, ref, positions[ref])))
            changed.append(ref)
    if set(changed) != set(REFS):
        raise ValueError("missing optical connector")
    result = replace_ranges(source, edits)
    new_blocks, _ = top_level_blocks(result)
    if len(blocks) != len(new_blocks) or any(
            before != after for (start, end, before), (_, _, after)
            in zip(blocks, new_blocks) if (start, end) not in {
                (a, b) for a, b, _ in edits}):
        raise ValueError("connector edit changed unrelated source blocks")
    return result


def validate_predecessor(path, layout, contract, root=ROOT):
    root = root.resolve()
    if not path.resolve().is_relative_to(root / "tmp"):
        raise ValueError("predecessor must be an internal candidate")
    meta = layout["metadata"]
    if meta.get("design_revision") != "MECH-FIT-01" or meta.get("is_canonical") is not False:
        raise ValueError("expected outline-only predecessor")
    if any(meta.get(k) is not False for k in (
            "fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
        raise ValueError("predecessor permissions must be explicitly false")
    if digest(path) != meta["source_board_sha256"] or path.name != meta["source_board"]:
        raise ValueError("changed predecessor PCB")
    if meta["fixed_origin_mm"] != contract["coordinate_system"]["kicad_origin_mm"]:
        raise ValueError("changed fixed datum")
    if layout["tracks"] or layout["vias"] or layout["zones"]:
        raise ValueError("connector study requires an unrouted predecessor")
    if any(p["net"] or p["net_code"] for p in layout["pads"]):
        raise ValueError("do not move connected circuits with this study")


def inset_positions(layout):
    """Reserve 0.30 mm between the rotated courtyard and the core lower edge."""
    by_ref = {c["ref"]: c for c in layout["components"]}
    positions = {}
    for ref in REFS:
        c = by_ref[ref]
        if c["rotation_deg"] != 0 or c["side"] != "TOP":
            raise ValueError("unexpected inherited optical pose")
        rotated = rotate(c["courtyard_polygons_mm"], c["position_mm"], [0, 0], 90)
        lower_offset = bounds(rotated)[3]
        positions[ref] = [c["position_mm"][0],
                          round(layout["board"]["bounds_mm"][3] - 0.30 - lower_offset, 6)]
    return positions


def transform_bodies(contract, old_components, new_components):
    bodies = copy.deepcopy(contract["retained_component_bodies"])
    datum = contract["coordinate_system"]["kicad_origin_mm"]
    height = contract["coordinate_system"]["board_center_height_mm"]
    for ref in REFS:
        item, old, new = bodies[ref], old_components[ref], new_components[ref]
        lo, hi = item["min_mm"], item["max_mm"]
        points = [[datum[0] + x, datum[1] - (y - height)]
                  for x, y in itertools.product((lo[0], hi[0]), (lo[1], hi[1]))]
        points = rotate([points], old["position_mm"], new["position_mm"], 90)[0]
        web = [[x - datum[0], height - (y - datum[1])] for x, y in points]
        item["min_mm"] = [min(p[0] for p in web), min(p[1] for p in web), lo[2]]
        item["max_mm"] = [max(p[0] for p in web), max(p[1] for p in web), hi[2]]
        item["center_mm"] = [(a + b) / 2 for a, b in zip(item["min_mm"], item["max_mm"])]
        item["size_mm"] = [b - a for a, b in zip(item["min_mm"], item["max_mm"])]
        item["model_status"] += "_RIGID_CANDIDATE_TRANSFORM_NOT_REIMPORTED"
    return bodies


def verify_layout(before, after):
    old_parts = {c["ref"]: c for c in before["components"]}
    new_parts = {c["ref"]: c for c in after["components"]}
    if set(old_parts) != set(new_parts):
        raise ValueError("component population changed")
    for ref, old in old_parts.items():
        new = new_parts[ref]
        if ref not in REFS:
            if old != new:
                raise ValueError("unrelated component changed: " + ref)
        elif any(old[k] != new[k] for k in (
                "uuid", "ref", "value", "footprint", "side", "models", "model_transforms")):
            raise ValueError("optical part identity or model changed")
    old_pads = {p["uuid"]: p for p in before["pads"]}
    new_pads = {p["uuid"]: p for p in after["pads"]}
    if len(new_pads) != len(old_pads) + 106 or len(after["pads"]) != len(new_pads):
        raise ValueError("unexpected paste primitive inventory")
    for identity, old in old_pads.items():
        if identity not in new_pads:
            raise ValueError("original contact removed")
        expected = dict(old)
        ref = old["ref"]
        if ref in REFS:
            expected["position_mm"] = rotate(
                [[old["position_mm"]]], old_parts[ref]["position_mm"],
                new_parts[ref]["position_mm"], 90)[0][0]
            expected["rotation_deg"] = old["rotation_deg"] + 90
        if new_pads[identity] != expected:
            raise ValueError("unexpected original pad mutation: " + identity)
    additions = [p for identity, p in new_pads.items() if identity not in old_pads]
    if any(p["ref"] not in REFS or p["number"] or p["net"] or p["net_code"] or
           p["copper_top"] or p["copper_bottom"] or p["mask_open_top"] or
           p["mask_open_bottom"] for p in additions):
        raise ValueError("paste additions acquired copper, mask or connectivity")
    if before["board"] != after["board"] or before["holes"] != after["holes"]:
        raise ValueError("outline, thickness or drills changed")
    if after["tracks"] or after["vias"] or after["zones"]:
        raise ValueError("connector study acquired routed copper")


def paste_screen(board):
    """Check the effective KiCad paste inventory, not just added source text."""
    import pcbnew
    result = []
    for fp in board.GetFootprints():
        if fp.GetReference() not in REFS:
            continue
        pads = list(fp.Pads())
        paste = [p for p in pads if p.IsOnLayer(pcbnew.F_Paste)]
        copper = [p for p in pads if p.IsOnLayer(pcbnew.F_Cu)]
        sizes = {}
        for pad in paste:
            size = pad.GetSize()
            key = tuple(round(pcbnew.ToMM(v), 6) for v in (size.x, size.y))
            sizes[key] = sizes.get(key, 0) + 1
        if sizes != {spec[0]: spec[1] for spec in PASTE.values()} or any(
                p.IsOnLayer(pcbnew.F_Paste) for p in copper):
            raise ValueError("effective KiCad paste inventory mismatch")
        for contact in copper:
            same_center = [p for p in paste if p.GetPosition() == contact.GetPosition()]
            if len(same_center) != 1:
                raise ValueError("paste aperture centre mismatch")
            size = contact.GetSize()
            key = tuple(round(pcbnew.ToMM(v), 6) for v in (size.x, size.y))
            aperture = same_center[0]
            actual = aperture.GetSize()
            if tuple(round(pcbnew.ToMM(v), 6) for v in (actual.x, actual.y)) != PASTE[key][0]:
                raise ValueError("paste size/row mismatch")
            if contact.GetOrientationDegrees() != aperture.GetOrientationDegrees():
                raise ValueError("paste aperture angle mismatch")
        result.append({"ref": fp.GetReference(), "copper_contacts_and_tabs": len(copper),
                       "separate_paste_apertures": len(paste),
                       "catalog_dimension_and_center_screen": "PASS",
                       "exact_numbered_drawing_and_stencil_approval": False})
    if len(result) != 2:
        raise ValueError("missing optical paste audit")
    return sorted(result, key=lambda r: r["ref"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--predecessor-dir", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    status = json.loads((PROJECT / "design-status.json").read_text())
    validate_inputs(contract, status, args.output_dir)
    evidence = json.loads(args.evidence.read_text())
    if evidence.get("schema") != "deepreal.connector-correction-evidence.v1" or any(
            evidence.get(k) is not False for k in (
                "fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
        raise ValueError("unsupported or unlocked evidence")
    for path, sha in evidence["sources_sha256"].items():
        source = (ROOT / path).resolve()
        if not source.is_relative_to(ROOT) or digest(source) != sha:
            raise ValueError("changed manufacturer evidence")
    before = json.loads((args.predecessor_dir / "engineering-layout-export.json").read_text())
    source = args.predecessor_dir / before["metadata"]["source_board"]
    validate_predecessor(source, before, contract)
    if before["metadata"]["mechanical_contract_sha256"] != digest(args.contract):
        raise ValueError("changed predecessor contract")
    positions = inset_positions(before)
    text = connector_candidate_text(source.read_text(), positions)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    target = output / "deepreal-main-pcba-mech-fit-02.kicad_pcb"
    with target.open("x") as stream:
        stream.write(text)
    import export_kicad_design as cad
    import pcbnew
    board = pcbnew.LoadBoard(str(target))
    tracks, vias = cad.copper(board)
    layout = {
        "metadata": {
            **before["metadata"], "design_revision": "MECH-FIT-02",
            "design_status": "OPTICAL_CONNECTOR_STUDY_FULL_FIT_BLOCKED",
            "source_board": target.name, "source_board_sha256": digest(target),
            "predecessor_board_sha256": digest(source),
            "connector_evidence_sha256": digest(args.evidence),
        },
        "board": cad.board_outline(board), "components": cad.components(board),
        "pads": cad.pads(board), "holes": cad.holes(board), "tracks": tracks,
        "vias": vias, "zones": cad.zones(board),
        "validation_status": before["validation_status"],
    }
    verify_layout(before, layout)
    old_parts = {c["ref"]: c for c in before["components"]}
    new_parts = {c["ref"]: c for c in layout["components"]}
    bodies = transform_bodies(contract, old_parts, new_parts)
    body_pairs = []
    for a, b in itertools.combinations(sorted(bodies), 2):
        widths = positive_box_overlap(bodies[a], bodies[b])
        if widths:
            body_pairs.append({"refs": [a, b], "box_overlap_mm": widths})
    copper_layout = dict(layout, pads=[p for p in layout["pads"]
                                      if p["copper_top"] or p["copper_bottom"]])
    head_evidence = json.loads((PROJECT / "head-interface-evidence.json").read_text())
    report = {
        "schema": "deepreal.pcb-connector-candidate.v1", "revision": "MECH-FIT-02",
        "status": "LIMITED_SOURCE_CORRECTIONS_PASS_FULL_FIT_BLOCKED",
        "candidate_board_sha256": digest(target), "predecessor_board_sha256": digest(source),
        "mechanical_contract_sha256": digest(args.contract),
        "connector_evidence_sha256": digest(args.evidence),
        "fixed_origin_mm": layout["metadata"]["fixed_origin_mm"],
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
        "footprints_preserved": len(layout["components"]),
        "original_pad_identities_preserved": len(before["pads"]),
        "paste_only_primitives_added": 106, "unrelated_source_blocks_byte_identical": True,
        "changes": [{
            "ref": ref, "old_position_mm": old_parts[ref]["position_mm"],
            "new_position_mm": new_parts[ref]["position_mm"], "rotation_deg": 90,
            "screened_body_center_web_mm": bodies[ref]["center_mm"],
            "mechanical_target_center_web_mm": contract["interfaces"][ref]["center_mm"],
            "reason": "Horizontal long axis and 0.30 mm lower courtyard inset; no contact renumbering",
            "electrical_or_cable_orientation_approved": False,
        } for ref in REFS],
        "J2_J3_copper_dimension_screens": [
            land_pattern_screen(copper_layout, ref, head_evidence) for ref in REFS],
        "J2_J3_effective_paste_screens": paste_screen(board),
        "current_optical_placement_screens": [placement_screen(layout, ref) for ref in REFS],
        "retained_component_bodies": bodies, "component_bodies_screened": len(bodies),
        "body_aabb_overlap_candidates": body_pairs,
        "same_side_courtyard_aabb_candidates": courtyard_candidates(layout["components"]),
        "missing_courtyard_refs": [c["ref"] for c in layout["components"]
                                   if not c["courtyard_polygons_mm"]],
        "blocking_reasons": contract["open"] + [
            "Optical connectors still overlap neighbor courtyards; no circuit-driven neighbor moves",
            "Exact FH26W model, numbered pin drawing and cable orientation are not approved",
            "USB and motor/encoder selections remain unresolved and unchanged",
        ],
        "screen_limits": [
            "Retained AABBs rigidly transformed for two connectors, not a fresh CAD solid import",
            "Courtyard AABBs are conservative; standalone native DRC is reported separately",
            "Paste dimension/centre correction is not stencil, assembly or fabrication approval",
        ],
    }
    for name, data in (("engineering-layout-export.json", layout), ("fit-screen.json", report)):
        with (output / name).open("x") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
    validate_predecessor(source, before, contract)
    print("CANDIDATE", target)
    print("Preserved footprints/original pads:", len(layout["components"]), len(before["pads"]))
    print("Added paste-only primitives:", 106)
    print("Body/courtyard candidates:", len(body_pairs),
          len(report["same_side_courtyard_aabb_candidates"]))
    print("Viewer integration BLOCKED; no connector or electrical approval")


if __name__ == "__main__":
    main()
