#!/usr/bin/env python3
"""Correct only evidence-supported D2 geometry and two back-silk flags."""

import argparse
import copy
import json
import re
import subprocess
import uuid
from pathlib import Path

from build_pcb_fit_candidate import ROOT, PROJECT, digest, top_level_blocks, validate_inputs
from build_pcb_connector_candidate import child, children, replace_ranges
from build_pcb_model_candidate import merge_footprints, reference
from export_native_review import read_glb


REVISION = "MECH-FIT-04"
PREDECESSOR_HASH = "4916678e77bba92dcd39d7df4ca86b164370df7a5fece5419f369917eda89c8f"
TI_HASH = "0598c5db22020f75981a25648f963d7065f76d9a3635c2bacb98cbfc49884d33"
LABELS = {
    "9d1d6b0b-086a-4341-a8d3-0294160a9837": "Support placeholders: 144 C / 44 R",
    "ee95f718-7daa-4999-87a4-598e15ebc603": "UNROUTED: vendor pin maps + FPGA + DDR gates open",
}
FOOTPRINT = "Texas_DRT-3"
LIBRARY = "Package_TO_SOT_SMD"


def fix_back_labels(text):
    edits, found = [], set()
    for start, end, block in top_level_blocks(text)[0]:
        if not block.startswith("(gr_text "):
            continue
        identity = re.search(r'\(uuid "([^"]+)"\)', block)[1]
        if identity not in LABELS:
            continue
        if not block.startswith('(gr_text "' + LABELS[identity] + '"') or \
                child(block, "gr_text", "layer")[2] != '(layer "B.SilkS")':
            raise ValueError("unexpected back-label identity")
        a, b, effects = child(block, "gr_text", "effects")
        if any(c.startswith("(justify ") for _, _, c in children(effects, "effects")):
            raise ValueError("back-label justification already changed")
        corrected = effects[:-1] + "\n\t\t(justify mirror)\n\t)"
        edits.append((start, end, replace_ranges(block, [(a, b, corrected)])))
        found.add(identity)
    if found != set(LABELS):
        raise ValueError("missing intended back labels")
    return replace_ranges(text, edits)


def deterministic_d2(text, footprint_uuid):
    blocks = [(a, b, c) for a, b, c in top_level_blocks(text)[0]
              if c.startswith("(footprint ") and reference(c) == "D2"]
    if len(blocks) != 1:
        raise ValueError("ambiguous D2")
    a, b, block = blocks[0]
    root_uuid = child(block, "footprint", "uuid")[2]
    index = 0

    def identity(match):
        nonlocal index
        old = match[0]
        if old == root_uuid:
            return '(uuid "{}")'.format(footprint_uuid)
        index += 1
        return '(uuid "{}")'.format(uuid.uuid5(
            uuid.NAMESPACE_URL, "deepreal:" + REVISION + ":D2:child:" + str(index)))

    block = re.sub(r'^\(footprint "[^"]+"',
                   '(footprint "' + LIBRARY + ":" + FOOTPRINT + '"', block)
    return replace_ranges(text, [(a, b, re.sub(r'\(uuid "[^"]+"\)', identity, block))])


def verify_scope(before, after):
    old = {c["ref"]: c for c in before["components"]}
    new = {c["ref"]: c for c in after["components"]}
    if old.keys() != new.keys() or len(old) != 238:
        raise ValueError("population changed")
    for ref in old:
        keys = ("uuid", "ref", "value", "position_mm", "rotation_deg", "side") \
            if ref == "D2" else tuple(old[ref])
        if any(old[ref][key] != new[ref][key] for key in keys):
            raise ValueError("unscoped component change: " + ref)
    for section in ("board", "holes", "tracks", "vias", "zones"):
        if before[section] != after[section]:
            raise ValueError("unscoped change: " + section)
    if [p for p in before["pads"] if p["ref"] != "D2"] != \
            [p for p in after["pads"] if p["ref"] != "D2"]:
        raise ValueError("other pads changed")
    pads = [p for p in after["pads"] if p["ref"] == "D2"]
    if len(pads) != 3 or {p["number"] for p in pads} != {"1", "2", "3"} or \
            any(p["net"] or p["size_mm"] != [0.3, 0.3] for p in pads):
        raise ValueError("incorrect DRT pad geometry")
    expected = {"1": [115.575, 32.85], "2": [115.575, 32.15], "3": [116.425, 32.5]}
    if any(p["position_mm"] != expected[p["number"]] or p["rotation_deg"] != 90 or
           p["copper_top"] or p["mask_open_top"] or not p["copper_bottom"] or
           not p["mask_open_bottom"] for p in pads):
        raise ValueError("incorrect bottom-side DRT registration")
    if not new["D2"]["footprint"].endswith(":" + FOOTPRINT) or \
            len(after["pads"]) != len(before["pads"]) - 7:
        raise ValueError("incorrect package correction")
    if new["D2"]["models"] != [
            "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/Texas_DRT-3.step"]:
        raise ValueError("incorrect DRT model")
    if after["tracks"] or after["vias"] or after["zones"] or any(p["net"] for p in after["pads"]):
        raise ValueError("unrouted classification changed")


def checked_predecessor(directory):
    data = json.loads((directory / "engineering-layout-export.json").read_text())
    meta = data["metadata"]
    board = directory / meta["source_board"]
    if directory.resolve().parent != ROOT / "tmp/pcb-model-candidate-2026-10-13" or \
            board.resolve().parent != directory.resolve() or \
            meta["design_revision"] != "MECH-FIT-03" or \
            digest(board) != PREDECESSOR_HASH or meta["source_board_sha256"] != PREDECESSOR_HASH:
        raise ValueError("unexpected or stale predecessor")
    if any(meta.get(k) is not False for k in
           ("is_canonical", "fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
        raise ValueError("predecessor release locks required")
    return data, board


def export_native(directory, layout, board, cli, models):
    glb = directory / "main-pcba-native.glb"
    command = [str(cli), "pcb", "export", "glb", "--output", str(glb),
               "--define-var", "KICAD10_3DMODEL_DIR=" + str(models),
               "--include-tracks", "--include-pads", "--include-zones",
               "--include-silkscreen", "--include-soldermask", "--cut-vias-in-body",
               "--no-extra-pad-thickness", "--user-origin", "65x34mm", str(board)]
    run = subprocess.run(command, capture_output=True, text=True)
    (directory / "native-export.log").write_text(run.stdout + run.stderr)
    run.check_returncode()
    names = {n.get("name") for n in read_glb(glb)["nodes"]}
    sources = []
    for name in sorted({m for c in layout["components"] for m in c["models"]}):
        path = Path(name.replace("${KICAD10_3DMODEL_DIR}", str(models)))
        sources.append({"declared": name, "resolved": str(path),
                        "sha256": digest(path) if path.is_file() else None})
    manifest = {
        "schema": "deepreal.private-candidate-native.v1", "revision": REVISION,
        "source_board_sha256": digest(board),
        "source_export_sha256": digest(directory / "engineering-layout-export.json"),
        "source_status_sha256": layout["metadata"]["source_status_sha256"],
        "glb_sha256": digest(glb), "glb": glb.name, "origin_mm": [65, 34],
        "native_model_refs": sorted(c["ref"] for c in layout["components"] if c["ref"] in names),
        "missing_model_refs": sorted(c["ref"] for c in layout["components"]
                                     if c["models"] and c["ref"] not in names),
        "pad_or_hole_only_refs": sorted(c["ref"] for c in layout["components"] if not c["models"]),
        "model_sources": sources, "fabrication_allowed": False,
        "public_visual_allowed": False, "viewer_integration_allowed": False,
        "status": "PRIVATE_UNROUTED_PACKAGE_AND_ENCLOSURE_STUDY",
        "warning": "D2 package corrected; other inherited substitutions remain unapproved",
        "package_audit_sha256": digest(directory / "package-audit.json"),
        "command": command,
    }
    (directory / "native-review-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("predecessor-dir", "contract", "output-dir", "footprint-dir",
                "ti-datasheet", "kicad-cli", "model-dir"):
        parser.add_argument("--" + arg, type=Path, required=True)
    args = parser.parse_args()
    if any(not p.is_absolute() for p in vars(args).values()):
        parser.error("absolute paths required")
    contract = json.loads(args.contract.read_text())
    validate_inputs(contract, json.loads((PROJECT / "design-status.json").read_text()), args.output_dir)
    before, source = checked_predecessor(args.predecessor_dir)
    if digest(args.ti_datasheet) != TI_HASH or \
            before["metadata"]["mechanical_contract_sha256"] != digest(args.contract):
        raise ValueError("datasheet or mechanical evidence changed")
    import export_kicad_design as cad
    import pcbnew
    part = next(c for c in before["components"] if c["ref"] == "D2")
    # Detached-footprint Flip segfaults in this SWIG build. Parent it to a
    # scratch board and merge only its serialized block into the candidate.
    board = pcbnew.BOARD()
    replacement = pcbnew.FootprintLoad(str(args.footprint_dir), FOOTPRINT)
    if not replacement:
        raise ValueError("missing audited library footprint")
    board.Add(replacement)
    replacement.SetReference("D2")
    replacement.SetValue(part["value"])
    if part["side"] == "BOTTOM":
        replacement.Flip(replacement.GetPosition(), False)
    replacement.SetOrientationDegrees(part["rotation_deg"])
    replacement.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in part["position_mm"]]))
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    serialized = output / "serialization-inspection.kicad_pcb"
    pcbnew.SaveBoard(str(serialized), board)
    saved = deterministic_d2(serialized.read_text(), part["uuid"])
    target = output / "deepreal-main-pcba-mech-fit-04.kicad_pcb"
    target.write_text(fix_back_labels(merge_footprints(source.read_text(), saved, {"D2"})))
    board = pcbnew.LoadBoard(str(target))
    tracks, vias = cad.copper(board)
    layout = {
        "metadata": {**copy.deepcopy(before["metadata"]), "design_revision": REVISION,
                     "design_status": "PRIVATE_UNROUTED_PACKAGE_AND_ENCLOSURE_STUDY",
                     "source_board": target.name, "source_board_sha256": digest(target),
                     "predecessor_board_sha256": digest(source)},
        "board": cad.board_outline(board), "components": cad.components(board),
        "pads": cad.pads(board), "holes": cad.holes(board),
        "tracks": tracks, "vias": vias, "zones": cad.zones(board),
        "validation_status": before["validation_status"],
    }
    verify_scope(before, layout)
    (output / "engineering-layout-export.json").write_text(json.dumps(layout, indent=2) + "\n")
    report = {
        "schema": "deepreal.pcb-package-candidate.v1", "revision": REVISION,
        "source_board_sha256": digest(target), "predecessor_board_sha256": digest(source),
        "builder_sha256": digest(Path(__file__)),
        "changed_footprint_refs": ["D2"], "mirrored_label_uuids": sorted(LABELS),
        "population_preserved": len(layout["components"]),
        "other_pad_identities_and_geometry_preserved": len(layout["pads"]) - 3,
        "D2": {
            "selected_part": "TI TPD2EUSB30ADRTR", "old_pad_count": 10, "new_pad_count": 3,
            "datasheet": str(args.ti_datasheet), "datasheet_sha256": TI_HASH,
            "package_drawing": "4206292-2/D, 06/2008, datasheet page 26",
            "pin_functions": {"1": "D+", "2": "D-", "3": "GND"},
            "body_nominal_mm": [1.0, 0.8], "seating_height_max_mm": 0.5,
            "library_footprint": str(args.footprint_dir / (FOOTPRINT + ".kicad_mod")),
            "library_sha256": digest(args.footprint_dir / (FOOTPRINT + ".kicad_mod")),
            "land_basis": "KiCad library 0.3 mm square lands, 0.7 mm pair pitch, 0.85 mm row spacing",
            "limit": "Package and numbering checked; library lands are not a manufacturer-qualified stencil/assembly release",
            "electrical_assignment": "UNCONNECTED; functions recorded only, no netlist invented",
        },
        "blocked_package_changes": {
            "U1": "Selected 548-ball processor still has generic 324-ball footprint; official drawing downloads returned 404",
            "U6_U7": "PF53 3.5 x 4.5 mm package still represented by inherited 4 x 4 mm QFN; official drawings unavailable",
            "J1": "Amphenol model/footprint does not select it over Hirose; intended Hirose PCB thickness conflict remains",
            "J2_J3": "Inherited FH26 does not verify FH26W variant, latch sweep or mated cable",
            "J4_J5": "Tall inherited headers remain placeholders, not selected motor connectors",
            "U18_U19": "Package and fixed cheek-board ownership remain unresolved",
        },
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
    }
    (output / "package-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    export_native(output, layout, target, args.kicad_cli, args.model_dir)
    if digest(source) != PREDECESSOR_HASH:
        raise ValueError("predecessor changed during build")
    print("PACKAGE CANDIDATE", target, "238 footprints;", len(layout["pads"]), "primitives")


if __name__ == "__main__":
    main()
