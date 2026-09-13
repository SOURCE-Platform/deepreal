#!/usr/bin/env python3
"""Generate a truthful inventory for the pre-fabrication review package."""

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
REPO = PROJECT.parents[2]
STATUS_PATH = PROJECT / "design-status.json"
OUTPUT = PROJECT / "engineering-review-manifest.json"


def _resolve(value):
    return REPO / value if value.startswith("docs/") else PROJECT / value


def main():
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    evidence = []
    missing = []
    for gate in status["gates"]:
        for item in gate["evidence"]:
            entry = {
                "gate": gate["id"],
                "path": item,
                "exists": _resolve(item).exists(),
            }
            evidence.append(entry)
            if not entry["exists"]:
                missing.append(entry)
    payload = {
        "schema": "deepreal.pcba.engineering-review-manifest.v1",
        "design_revision": status["design_revision"],
        "design_status": status["status"],
        "fabrication_allowed": False,
        "public_visual_allowed": status["public_visual_allowed"],
        "approved_caption": (
            "DeepReal Main PCBA — engineering development visualization based "
            "on a pre-fabrication PCB layout."
        ),
        "gate_status": {gate["id"]: gate["status"] for gate in status["gates"]},
        "evidence_inventory": evidence,
        "missing_evidence_files": missing,
        "deferred_release_outputs": [
            "Gerbers", "drill files", "stencil", "pick-and-place",
            "assembly release drawing", "production BOM",
        ],
        "known_blockers": [
            {"gate": gate["id"], "items": gate["blockers"]}
            for gate in status["gates"] if gate["blockers"]
        ],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Generated", OUTPUT)
    print("evidence files / missing:", len(evidence), len(missing))


if __name__ == "__main__":
    main()
