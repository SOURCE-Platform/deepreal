#!/usr/bin/env python3
"""Validate DeepReal PCBA gate truth and release locks.

Run with the Python bundled by KiCad so pcbnew is available.
"""

import csv
import json
from pathlib import Path
import re
import sys

import wx

WX_APP = wx.App(False)
import pcbnew  # noqa: E402


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT.parents[2]
STATUS_PATH = PROJECT / "design-status.json"
PUBLIC_PATH = PROJECT / "public-assets.json"
BOARD_PATH = PROJECT / "deepreal-main-pcba.kicad_pcb"
EVIDENCE_PATH = PROJECT / "component-evidence.csv"
STACKUP_PATH = PROJECT / "preliminary-stackup.json"
SHEETS = tuple(sorted(PROJECT.glob("[0-9][0-9]_*.kicad_sch")))

ALLOWED_STATES = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "PASS", "SUPERSEDED"}
REQUIRED_GATE_FIELDS = {
    "id", "name", "status", "depends_on", "responsible_disciplines",
    "review_date", "reviewer_type", "required_evidence", "evidence", "blockers",
}


def _count_placed(text, kind):
    return len(re.findall(r"^\s*\(" + kind + r"\s*$", text, re.MULTILINE))


def _evidence_path(value):
    if value.startswith("docs/"):
        return REPO / value
    return PROJECT / value


def main():
    failures = []
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    public = json.loads(PUBLIC_PATH.read_text(encoding="utf-8"))
    gates = {gate["id"]: gate for gate in status["gates"]}

    if status.get("schema") != "deepreal.pcba.design-status.v1":
        failures.append("unsupported or missing design-status schema")
    if len(gates) != len(status["gates"]):
        failures.append("gate identifiers are not unique")
    for gate in status["gates"]:
        missing_fields = REQUIRED_GATE_FIELDS - set(gate)
        if missing_fields:
            failures.append("{} missing fields {}".format(
                gate.get("id", "?"), ", ".join(sorted(missing_fields))))
            continue
        if gate["status"] not in ALLOWED_STATES:
            failures.append("{} has invalid status {}".format(
                gate["id"], gate["status"]))
        if gate["status"] == "PASS" and gate["blockers"]:
            failures.append("{} passed with open blockers".format(gate["id"]))
        if gate["status"] == "PASS" and not gate["review_date"]:
            failures.append("{} passed without a review date".format(gate["id"]))
        if not gate["responsible_disciplines"] or not gate["required_evidence"]:
            failures.append("{} lacks ownership or exit evidence".format(gate["id"]))

    if status.get("fabrication_allowed") is not False:
        failures.append("fabrication release lock is not false")
    if public.get("fabrication_allowed") is not False:
        failures.append("public manifest permits fabrication")
    if gates["G11"]["status"] != "PASS":
        if status.get("public_visual_allowed") is not False:
            failures.append("status permits public visual before G11")
        if public.get("public_visual_allowed") is not False:
            failures.append("manifest permits public visual before G11")

    for gate in status["gates"]:
        if gate["status"] != "PASS":
            continue
        unknown = [item for item in gate["depends_on"] if item not in gates]
        if unknown:
            failures.append("{} has unknown dependencies {}".format(
                gate["id"], ", ".join(unknown)))
            continue
        missing = [item for item in gate["depends_on"]
                   if gates[item]["status"] != "PASS"]
        if missing:
            failures.append("{} passed before {}".format(
                gate["id"], ", ".join(missing)))
    for gate in status["gates"]:
        for evidence in gate["evidence"]:
            if not _evidence_path(evidence).exists():
                failures.append("{} missing evidence {}".format(
                    gate["id"], evidence))

    if len(SHEETS) != 14:
        failures.append("expected 14 functional sheets, found {}".format(len(SHEETS)))
    sheet_metrics = []
    for sheet in SHEETS:
        text = sheet.read_text(encoding="utf-8")
        symbols = _count_placed(text, "symbol")
        wires = _count_placed(text, "wire")
        sheet_metrics.append((sheet.name, symbols, wires))
    complete = all(symbols > 0 and wires > 0
                   for _, symbols, wires in sheet_metrics)
    if gates["G6"]["status"] == "PASS" and not complete:
        failures.append("G6 passed while one or more sheets are note-only")

    board = pcbnew.LoadBoard(str(BOARD_PATH))
    track_count = sum(not isinstance(item, pcbnew.PCB_VIA)
                      for item in board.GetTracks())
    via_count = sum(isinstance(item, pcbnew.PCB_VIA)
                    for item in board.GetTracks())
    if gates["G9"]["status"] == "PASS" and track_count == 0:
        failures.append("G9 passed but canonical board has no routed tracks")
    if gates["G10"]["status"] == "PASS" and board.GetConnectivity().GetUnconnectedCount():
        failures.append("G10 passed with unintended unconnected items")
    if gates["G2"]["status"] == "PASS":
        with EVIDENCE_PATH.open(newline="", encoding="utf-8") as stream:
            open_rows = [row["Ref"] for row in csv.DictReader(stream)
                         if row["Audit_state"] not in {"AUDITED", "APPROVED"}]
        if open_rows:
            failures.append("G2 passed with open component audits: " +
                            ", ".join(open_rows))
    stackup = json.loads(STACKUP_PATH.read_text(encoding="utf-8"))
    if gates["G7"]["status"] == "PASS" and (
            not stackup.get("fabricator_reviewed")
            or not stackup.get("routing_allowed")):
        failures.append("G7 passed without a reviewed routing-authorized stack-up")

    if failures:
        raise RuntimeError("\n".join(failures))

    print("DESIGN GATE STATUS")
    for gate in status["gates"]:
        print("  {} {:<12} {}".format(gate["id"], gate["status"], gate["name"]))
    print("SCHEMATIC CONTENT")
    print("  functional sheets: {}".format(len(sheet_metrics)))
    print("  populated sheets: {}".format(sum(
        symbols > 0 and wires > 0 for _, symbols, wires in sheet_metrics)))
    print("CANONICAL PCB")
    print("  footprints / tracks / vias: {} / {} / {}".format(
        len(board.GetFootprints()), track_count, via_count))
    print("  fabrication allowed: false")
    print("  public visual allowed: false")
    print("PASS: gate dependencies and release locks are truthful")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL:", error, file=sys.stderr)
        raise
