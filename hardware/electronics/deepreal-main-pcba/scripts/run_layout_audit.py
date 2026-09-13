#!/usr/bin/env python3
"""Collect native DRC and completeness evidence without altering the board."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

PROJECT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()
    output = PROJECT / "generated-review"
    output.mkdir(exist_ok=True)
    board = PROJECT / "deepreal-main-pcba.kicad_pcb"
    before = hashlib.sha256(board.read_bytes()).hexdigest()
    native = output / "native-drc.json"
    run = subprocess.run([args.kicad_cli, "pcb", "drc", "--schematic-parity",
        "--severity-all", "--format", "json", "--output", str(native), str(board)],
        text=True, capture_output=True)
    (output / "native-drc.log").write_text(run.stdout+run.stderr)
    run.check_returncode()
    if before != hashlib.sha256(board.read_bytes()).hexdigest():
        raise RuntimeError("audit unexpectedly changed the canonical board")
    drc = json.loads(native.read_text())
    layout = json.loads((PROJECT / "engineering-layout-export.json").read_text())
    if before != layout["metadata"]["source_board_sha256"]:
        raise RuntimeError("export is stale; refresh before auditing")
    project = json.loads(board.with_suffix(".kicad_pro").read_text())
    severities = project["board"]["design_settings"]["rule_severities"]
    sheets = []
    for sheet in sorted(PROJECT.glob("[0-9][0-9]_*.kicad_sch")):
        text = sheet.read_text()
        sheets.append({"file": sheet.name,
            "symbols": len(re.findall(r"^\s*\(symbol\s*$", text, re.MULTILINE)),
            "wires": len(re.findall(r"^\s*\(wire\s*$", text, re.MULTILINE))})
    report = {
        "schema": "deepreal.layout-readiness-audit.v1",
        "source_board_sha256": before, "engineering_status": "BLOCKED",
        "public_visual_allowed": False, "fabrication_allowed": False,
        "violations": len(drc.get("violations", [])),
        "violations_by_type": dict(sorted(Counter(
            v["type"] for v in drc.get("violations", [])).items())),
        "schematic_parity_issues": len(drc.get("schematic_parity", [])),
        "unconnected_items_reported": len(drc.get("unconnected_items", [])),
        "ignored_rules": sorted(k for k, v in severities.items() if v == "ignore"),
        "missing_courtyard_refs": [c["ref"] for c in layout["components"]
                                   if not c["courtyard_polygons_mm"]],
        "named_pad_nets": sorted({p["net"] for p in layout["pads"] if p["net"]}),
        "sheets": sheets,
        "warning": "Zero unconnected items does not prove connectivity: inspect named nets and sheet completeness.",
    }
    (output / "layout-readiness.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("engineering_status", "violations",
          "schematic_parity_issues", "ignored_rules", "named_pad_nets")}, indent=2))


if __name__ == "__main__":
    main()
