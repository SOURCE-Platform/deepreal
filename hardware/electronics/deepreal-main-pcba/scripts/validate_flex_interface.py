#!/usr/bin/env python3
"""Validate the 51-contact head-flex allocation without inventing pin numbers."""

import csv
import argparse
import hashlib
import json
from pathlib import Path
import sys

from head_interface_audit import audit


PROJECT = Path(__file__).resolve().parent.parent
ALLOCATION = PROJECT / "connector-allocation.csv"
STATUS = PROJECT / "design-status.json"
REQUIRED_GROUPS = {
    "Head_3V3", "Power_returns", "RGB_CSI_signals", "RGB_CSI_returns",
    "IR_CSI_signals", "IR_CSI_returns", "RGB_clock", "IR_clock",
    "Control_bus", "Sensor_resets", "Timing_triggers", "Projector_control",
    "Safety_interlock", "Thermal_status", "Head_identity", "Shield_reserved",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-ready", action="store_true",
                        help="Fail while interface evidence remains incomplete")
    args = parser.parse_args()
    failures = []
    with ALLOCATION.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    gate = next(item for item in status["gates"] if item["id"] == "G5")
    groups = {row["Group"] for row in rows}
    total = sum(int(row["Contacts"]) for row in rows)
    if groups != REQUIRED_GROUPS:
        failures.append("head-flex group set is incomplete or unexpected")
    if len(groups) != len(rows) or any(int(row["Contacts"]) < 1 for row in rows):
        failures.append("groups must be unique and contact counts positive")
    if total != 51:
        failures.append("head-flex allocation is {} contacts, expected 51".format(total))
    if any(row["Connector"] != "J2/J3" for row in rows):
        failures.append("allocation must apply identically to J2 and J3")
    unnumbered = [row["Group"] for row in rows
                  if row["Pin_numbers"].startswith("TBD")]
    if gate["status"] == "PASS" and unnumbered:
        failures.append("G5 passed with unnumbered groups: " + ", ".join(unnumbered))
    if failures:
        raise RuntimeError("\n".join(failures))
    evidence = json.loads((PROJECT / "head-interface-evidence.json").read_text())
    layout = json.loads((PROJECT / "engineering-layout-export.json").read_text())
    board = PROJECT / "deepreal-main-pcba.kicad_pcb"
    if hashlib.sha256(board.read_bytes()).hexdigest() != layout["metadata"]["source_board_sha256"]:
        raise RuntimeError("Stale layout export; regenerate before interface screening")
    report = audit(rows, evidence, layout, PROJECT.parents[2])
    report["source_evidence_sha256"] = hashlib.sha256(
        (PROJECT / "head-interface-evidence.json").read_bytes()).hexdigest()
    report["source_allocation_sha256"] = hashlib.sha256(ALLOCATION.read_bytes()).hexdigest()
    report["groups_awaiting_pin_numbers"] = unnumbered
    output = PROJECT / "generated-review" / "head-interface-audit.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+"\n")
    print("HEAD FLEX INTERFACE")
    print("  reusable connectors: J2 and J3")
    print("  allocated contacts:", total)
    print("  signal/power groups:", len(groups))
    print("  groups awaiting physical pin numbers:", len(unnumbered))
    print("  camera differential pairs per head:",
          report["capacity_screen"]["camera_differential_pairs_per_head"])
    print("  conservative connector-only current screen: {} A; NOT approved ampacity".format(
        report["capacity_screen"]["conservative_70_percent_screen_a"]))
    print("  interface status:", report["interface_status"])
    print("  report:", output)
    if args.require_ready or gate["status"] == "PASS":
        raise RuntimeError("Interface is not approved: review evidence, numbered continuity, head circuitry and physical fit remain required")
    print("PASS: audit ran with truthful release locks. The interface itself remains BLOCKED.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL:", error, file=sys.stderr)
        raise
