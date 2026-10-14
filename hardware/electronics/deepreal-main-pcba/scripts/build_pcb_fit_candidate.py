#!/usr/bin/env python3
"""Branch a measured PCB profile for internal fit diagnosis, never release."""

import argparse
import hashlib
import itertools
import json
import math
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / "blender"))
from pcb_fit_geometry import positive_box_overlap
from head_interface_audit import bounds, overlaps, placement_screen, land_pattern_screen


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_inputs(contract, status, output, root=ROOT, project=PROJECT):
    root, project = root.resolve(), project.resolve()
    output = output.resolve()
    if not output.is_relative_to(root / "tmp") or output.exists():
        raise ValueError("choose a new internal tmp directory, never baseline/public output")
    if contract.get("schema") != "deepreal.pcb-mechanical-interface.v1":
        raise ValueError("unsupported mechanical interface contract")
    for document in (contract, status):
        for name in ("fabrication_allowed", "public_visual_allowed"):
            if document.get(name) is not False:
                raise ValueError("release permissions must be explicitly false")
    if contract.get("viewer_integration_allowed") is not False:
        raise ValueError("initial candidate must remain integration-blocked")
    for path, expected in contract["sources_sha256"].items():
        source = (root / path).resolve()
        if not source.is_relative_to(root) or digest(source) != expected:
            raise ValueError("changed mechanical/native input: " + path)
    for name, field in (
            ("deepreal-main-pcba.kicad_pcb", "source_board_sha256"),
            ("engineering-layout-export.json", "source_export_sha256"),
            ("design-status.json", "source_status_sha256")):
        if digest(project / name) != contract[field]:
            raise ValueError("changed candidate input: " + name)
    loops = contract["profile_loops_kicad_mm"]
    if not loops or any(len(loop) < 3 or any(
            len(point) != 2 or not all(math.isfinite(v) for v in point)
            for point in loop) for loop in loops):
        raise ValueError("invalid measured profile")


def matching_drill(loop, holes, tolerance=0.0002):
    lo = [min(p[i] for p in loop) for i in range(2)]
    hi = [max(p[i] for p in loop) for i in range(2)]
    center = [(a + b) / 2 for a, b in zip(lo, hi)]
    size = [b - a for a, b in zip(lo, hi)]
    # Require a circular source cutout, not merely a matching rectangle.
    radius = size[0] / 2
    if abs(size[0] - size[1]) > tolerance or any(
            abs(math.dist(p, center) - radius) > tolerance for p in loop):
        return None
    for hole in holes:
        if math.dist(hole["position_mm"], center) <= tolerance and all(
                abs(a - b) <= tolerance for a, b in zip(hole["drill_mm"], size)):
            return hole["ref"]
    return None


def top_level_blocks(text):
    """Locate root children while respecting quoted strings and escapes."""
    if not text.lstrip().startswith("(kicad_pcb"):
        raise ValueError("not a KiCad PCB")
    depth, quoted, escaped = 0, False, False
    start = None
    result = []
    root_end = None
    for index, character in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "(":
            if depth == 1:
                start = index
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced PCB")
            if depth == 1 and start is not None:
                result.append((start, index + 1, text[start:index + 1]))
                start = None
            elif depth == 0:
                root_end = index
                if text[index + 1:].strip():
                    raise ValueError("unexpected data after PCB")
                break
    if quoted or depth or root_end is None:
        raise ValueError("unbalanced PCB")
    return result, root_end


def profile_candidate_text(source, loops, holes):
    """Replace board-edge blocks only, preserving every footprint byte-for-byte."""
    blocks, root_end = top_level_blocks(source)
    removed = []
    for start, end, block in blocks:
        if re.match(r'\(gr_\w+\b', block) and re.search(
                r'\(layer\s+"Edge\.Cuts"\)', block):
            removed.append((start, end))
    if not removed:
        raise ValueError("baseline has no board-edge drawings")
    cutouts, additions = [], []
    for index, loop in enumerate(loops):
        existing = matching_drill(loop, holes) if index else None
        if existing:
            cutouts.append({"profile_index": index, "existing_drill_ref": existing,
                            "action": "REUSE_EXISTING_DRILL_NO_DUPLICATE_EDGE_CUT"})
            continue
        for start, end in zip(loop, loop[1:] + loop[:1]):
            identity = uuid.uuid5(uuid.NAMESPACE_URL,
                                 "deepreal:MECH-FIT-01:" + repr([index, start, end]))
            additions.append(
                '\t(gr_line (start {:.6f} {:.6f}) (end {:.6f} {:.6f}) '
                '(stroke (width 0.05) (type default)) (layer "Edge.Cuts") '
                '(uuid "{}"))\n'.format(*start, *end, identity))
        if index:
            cutouts.append({"profile_index": index,
                            "action": "UNAPPROVED_MECHANICAL_CUTOUT_NO_ADDED_COPPER"})
    # Replace from the end so offsets remain valid. Inserting before the
    # original root terminator leaves all unrelated source blocks unchanged.
    result = source[:root_end] + "".join(additions) + source[root_end:]
    for start, end in reversed(removed):
        result = result[:start] + result[end:]
    old_other = [block for start, end, block in blocks if (start, end) not in removed]
    new_blocks, _ = top_level_blocks(result)
    new_other = [block for _, _, block in new_blocks if not (
        re.match(r'\(gr_\w+\b', block) and re.search(r'\(layer\s+"Edge\.Cuts"\)', block))]
    if old_other != new_other:
        raise ValueError("profile edit changed non-edge source data")
    return result, cutouts


def courtyard_candidates(components):
    result = []
    known = [c for c in components if c["courtyard_polygons_mm"]]
    for a, b in itertools.combinations(known, 2):
        if a["side"] == b["side"] and overlaps(bounds(a["courtyard_polygons_mm"]),
                                               bounds(b["courtyard_polygons_mm"])):
            result.append([a["ref"], b["ref"]])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    status = json.loads((PROJECT / "design-status.json").read_text())
    validate_inputs(contract, status, args.output_dir)
    # Reuse the canonical export's descriptive functions, not its write main().
    # Import initializes KiCad's wx runtime; no baseline export is regenerated.
    import export_kicad_design as cad
    import pcbnew

    baseline = json.loads((PROJECT / "engineering-layout-export.json").read_text())
    text, cutouts = profile_candidate_text(
        (PROJECT / "deepreal-main-pcba.kicad_pcb").read_text(),
        contract["profile_loops_kicad_mm"], baseline["holes"])
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    target = output / "deepreal-main-pcba-mech-fit-01.kicad_pcb"
    with target.open("x") as stream:
        stream.write(text)
    # Parse the actual file with KiCad. Avoid mutation/SaveBoard in this local
    # SWIG build; it loses typed pointers after creating new drawing objects.
    board = pcbnew.LoadBoard(str(target))
    components, pads = cad.components(board), cad.pads(board)
    if components != baseline["components"] or pads != baseline["pads"]:
        raise ValueError("profile edit changed component placement, footprint or pads")
    tracks, vias = cad.copper(board)
    zones = cad.zones(board)
    if tracks or vias or zones:
        raise ValueError("unrouted fit candidate acquired copper")
    layout = {
        "metadata": {
            "schema": "deepreal.pcba.kicad-export.v1",
            "design": status["design"], "design_revision": "MECH-FIT-01",
            "design_status": "PROFILE_CANDIDATE_NOT_PLACEMENT_APPROVED",
            "is_canonical": False, "fabrication_allowed": False,
            "public_visual_allowed": False, "viewer_integration_allowed": False,
            "source_board": target.name, "source_board_sha256": digest(target),
            "source_status_sha256": contract["source_status_sha256"],
            "mechanical_contract_sha256": digest(args.contract),
            "fixed_origin_mm": contract["coordinate_system"]["kicad_origin_mm"],
        },
        "board": cad.board_outline(board), "components": components,
        "pads": pads, "holes": cad.holes(board), "tracks": tracks,
        "vias": vias, "zones": zones,
        "validation_status": {g["id"]: g["status"] for g in status["gates"]},
    }
    bodies = contract["retained_component_bodies"]
    body_candidates = []
    for a, b in itertools.combinations(sorted(bodies), 2):
        widths = positive_box_overlap(bodies[a], bodies[b])
        if widths:
            body_candidates.append({"refs": [a, b], "box_overlap_mm": widths})
    evidence = json.loads((PROJECT / "head-interface-evidence.json").read_text())
    trials = []
    by_ref = {c["ref"]: c for c in components}
    for ref in ("J2", "J3"):
        for rotation in (90, -90):
            for inward in (0, 1):
                position = list(by_ref[ref]["position_mm"])
                position[1] -= inward
                trial = placement_screen(layout, ref, position, rotation)
                trial["applied_to_candidate"] = False
                trials.append(trial)
    report = {
        "schema": "deepreal.pcb-fit-candidate.v1",
        "revision": "MECH-FIT-01",
        "status": "OUTLINE_TRANSPORT_PASS_FULL_FIT_BLOCKED",
        "source_board_sha256": contract["source_board_sha256"],
        "candidate_board_sha256": digest(target),
        "mechanical_contract_sha256": digest(args.contract),
        "fixed_origin_mm": layout["metadata"]["fixed_origin_mm"],
        "outline_bounds_kicad_mm": layout["board"]["bounds_mm"],
        "board_thickness_mm": layout["board"]["thickness_mm"],
        "mechanical_envelope_thickness_mm": contract["board"]["size_mm"][2],
        "footprints_preserved": len(components), "pads_preserved": len(pads),
        "component_bodies_screened": len(bodies),
        "component_placements_and_pad_geometry_unchanged": True,
        "profile_cutouts": cutouts,
        "body_aabb_overlap_candidates": body_candidates,
        "same_side_courtyard_aabb_candidates": courtyard_candidates(components),
        "missing_courtyard_refs": [c["ref"] for c in components
                                   if not c["courtyard_polygons_mm"]],
        "J2_J3_land_pattern_dimension_screens": [
            land_pattern_screen(layout, ref, evidence) for ref in ("J2", "J3")],
        "connector_orientation_trials_not_applied": trials,
        "viewer_integration_allowed": False, "fabrication_allowed": False,
        "public_visual_allowed": False,
        "blocking_reasons": contract["open"],
        "screen_limits": [
            "Body/courtyard AABBs are conservative candidates, not exact solid or polygon collision verdicts",
            "Retained native bodies include 18 representative missing-model envelopes",
            "No individual placement, footprint substitution, pin numbering or connector selection was changed",
            "Existing schematic and electrical gates are unchanged; no final placement or routing is claimed",
        ],
    }
    for name, document in (("engineering-layout-export.json", layout),
                           ("fit-screen.json", report)):
        with (output / name).open("x") as stream:
            json.dump(document, stream, indent=2)
            stream.write("\n")
    # Validate the source bindings again after CAD serialization.
    if digest(PROJECT / "deepreal-main-pcba.kicad_pcb") != contract["source_board_sha256"]:
        raise ValueError("baseline changed during candidate build")
    print("CANDIDATE", target)
    print("Preserved footprints/pads:", len(components), len(pads))
    print("Body-box candidates:", len(body_candidates))
    print("Viewer integration BLOCKED; connector selection and full fit remain open")


if __name__ == "__main__":
    main()
