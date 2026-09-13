#!/usr/bin/env python3
"""Validate the 51-contact head-flex allocation without inventing pin numbers."""

import csv
import json
from pathlib import Path
import sys


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
    failures = []
    with ALLOCATION.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    gate = next(item for item in status["gates"] if item["id"] == "G5")
    groups = {row["Group"] for row in rows}
    total = sum(int(row["Contacts"]) for row in rows)
    if groups != REQUIRED_GROUPS:
        failures.append("head-flex group set is incomplete or unexpected")
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
    print("HEAD FLEX INTERFACE")
    print("  reusable connectors: J2 and J3")
    print("  allocated contacts:", total)
    print("  signal/power groups:", len(groups))
    print("  groups awaiting physical pin numbers:", len(unnumbered))
    print("PASS: the logical allocation fits 51 contacts; physical numbering remains open")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL:", error, file=sys.stderr)
        raise
