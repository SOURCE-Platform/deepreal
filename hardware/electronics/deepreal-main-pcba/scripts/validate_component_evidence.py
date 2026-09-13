#!/usr/bin/env python3
"""Validate coverage and closure truth in the major-component evidence register."""

import csv
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REGISTER_PATH = PROJECT / "component-register.csv"
EVIDENCE_PATH = PROJECT / "component-evidence.csv"

MAJOR_PREFIXES = ("U", "J", "D", "MK", "SW")
CLOSED_STATES = {"AUDITED", "APPROVED"}


def _expand_ref_group(value):
    """Expand forms such as U2-U3 while preserving compound prefixes."""
    match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)?(\d+)", value)
    if not match:
        return {value}
    prefix_a, start, prefix_b, end = match.groups()
    if prefix_b and prefix_b != prefix_a:
        return {value}
    return {"{}{}".format(prefix_a, number)
            for number in range(int(start), int(end) + 1)}


def _refs(value):
    result = set()
    for token in re.split(r"[ ,/]+", value.strip()):
        if token:
            result.update(_expand_ref_group(token))
    return result


def _is_major(ref):
    return ref.startswith(MAJOR_PREFIXES)


def main():
    failures = []
    with REGISTER_PATH.open(newline="", encoding="utf-8") as stream:
        registered = list(csv.DictReader(stream))
    with EVIDENCE_PATH.open(newline="", encoding="utf-8") as stream:
        evidence = list(csv.DictReader(stream))

    required_refs = set()
    for row in registered:
        required_refs.update(ref for ref in _refs(row["Ref"]) if _is_major(ref))
    covered_refs = set()
    for row in evidence:
        covered_refs.update(ref for ref in _refs(row["Ref"]) if _is_major(ref))
        if not row.get("Selected_part") or not row.get("Required_evidence"):
            failures.append("incomplete evidence row {}".format(row.get("Ref", "?")))
        state = row.get("Audit_state", "")
        if state in CLOSED_STATES and row.get("Blocking_issue"):
            failures.append("{} is closed but still has a blocker".format(row["Ref"]))

    missing = sorted(required_refs - covered_refs)
    if missing:
        failures.append("major references lack evidence rows: " + ", ".join(missing))

    states = {}
    for row in evidence:
        states[row["Audit_state"]] = states.get(row["Audit_state"], 0) + 1
    closed = sum(count for state, count in states.items() if state in CLOSED_STATES)

    if failures:
        raise RuntimeError("\n".join(failures))
    print("COMPONENT EVIDENCE")
    print("  registered major refs:", len(required_refs))
    print("  evidence-covered refs:", len(covered_refs))
    print("  closed evidence rows: {} / {}".format(closed, len(evidence)))
    for state in sorted(states):
        print("  {:<24} {}".format(state, states[state]))
    print("PASS: evidence coverage is complete and open audit states remain explicit")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL:", error, file=sys.stderr)
        raise
