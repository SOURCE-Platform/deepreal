#!/usr/bin/env python3
"""Compile a drawing-bound comparison, not a selected connector or footprint."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


DRAWINGS = {
    "usb4230": "7e8c58eee83ce4cd827b20c8065dd46e89dd81449186b1850a0d2c10c8c57014",
    "usb4065": "20568c46e9f74b9d9f42b5ec85faaeb29f65ad95b2198c1f8efe786b3617b3a5",
    "usb4745": "ff1efa813f3ed801a479372aa7c267df1dabe72c54a7666ba243b050c5ece435",
    "usb4056": "5335ce832995d59e1e3ede9365e61f2bf90ddace5009f9950cf41ddb506aeeeb",
    "usb4910": "77affdf57f8f9833f608f05997e4db3326ac99192a9078b779674c23bd1acf7a",
}

# Manual transcriptions from the drawing images. These are not land patterns.
FACTS = {
    "usb4230": {
        "drawing_revision": "A",
        "mount": "horizontal hybrid top mount",
        "pcb_thickness_mm": None,
        "status": "UNRESOLVED_THICKNESS_AND_ATTACHMENT",
        "reason": "No PCB thickness range established from the inspected drawing.",
        "drawing_pages": [1, 2],
    },
    "usb4065": {
        "drawing_revision": "X",
        "mount": "horizontal hybrid top mount",
        "pcb_thickness_mm": [1.2, 1.2],
        "status": "REJECTED",
        "reason": "Drawing is marked OBSOLETE; page 2 recommends 1.20 mm PCB.",
        "drawing_pages": [1, 2],
    },
    "usb4745": {
        "drawing_revision": None,
        "mount": "horizontal mid mount",
        "pcb_thickness_mm": [0.5, 0.7],
        "status": "REJECTED",
        "reason": "Drawing specifies 0.6 +/- 0.1 mm PCB, not retained thickness.",
        "drawing_pages": [1, 2],
    },
    "usb4056": {
        "drawing_revision": "A5",
        "mount": "horizontal hybrid top mount",
        "pcb_thickness_mm": [1.0, 1.2],
        "status": "REJECTED",
        "reason": "Page 2 recommended PCB thickness is 1.00 to 1.20 mm.",
        "drawing_pages": [1, 2],
    },
    "usb4910": {
        "drawing_revision": "A",
        "mount": "horizontal dual-row SMT top mount",
        "pcb_thickness_mm": None,
        "status": "INVESTIGATE_ONLY",
        "reason": "No PCB thickness range established; short shell stakes require attachment evidence.",
        "drawing_pages": [1, 2],
        "observed_product_variant_not_selected": "USB4910-00-A",
        "profile_mm": 3.16,
        "body_length_mm": 7.90,
        "shell_stake_length_mm": 0.50,
        "locating_peg_diameter_mm": [0.40, 0.50],
        "recommended_locating_hole_diameter_mm": 0.55,
        "signal_lands_count_and_size_mm": [24, 0.85, 0.30],
        "signal_pitch_mm": 0.50,
        "layout_tolerance_mm": 0.05,
        "mask_stencil_note": (
            "Page 2 says 'Recommended Solder mask / Thickness = 0.12mm'. "
            "Meaning unresolved; do not assign this to board, mask or stencil thickness."
        ),
    },
}


def compile_audit(sources):
    candidates = []
    for name, expected in DRAWINGS.items():
        path = sources / (name + ".pdf")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Manufacturer drawing hash mismatch: " + name)
        candidates.append({
            "family": name.upper(),
            "source": str(path.resolve()),
            "sha256": actual,
            "official_url": "https://gct.co/files/drawings/" + name + ".pdf",
            "contact_count": 24,
            "superspeed_contacts_present": True,
            "pin_map_basis": "Inspected A1-A12/B1-B12 manufacturer drawing table.",
            "ordering_variant_selected": None,
            "thickness_compatible": False,
            "approved": False,
            **copy.deepcopy(FACTS[name]),
        })
    return {
        "status": "COMPARISON_ONLY_NO_APPROVED_REPLACEMENT",
        "method": "Manual drawing-image transcription with enforced PDF hashes.",
        "retained_thickness_definitions_mm": {
            "mechanical_nominal": 1.5,
            "native_measured_approx": 1.509994,
            "kicad_design_setting": 1.6,
        },
        "thickness_definition_reconciled": False,
        "candidates": candidates,
        "selected_part": None,
        "manufacturer_cad_retrieved": False,
        "manufacturer_specification_retrieved": False,
        "cad_access_note": (
            "Public GCT product/resources page was readable. Model Generator click "
            "was blocked by its cookie overlay; no model downloaded or inferred."
        ),
        "open_gates": [
            "Reconcile nominal, native-measured and KiCad thickness definitions.",
            "Confirm exact ordering variant and manufacturer thickness acceptance.",
            "Obtain manufacturer CAD/specification and mounting-plane/mouth datums.",
            "Verify shell stakes, peg holes, solder attachment and insertion loads.",
            "Check retained plug/overmold, insertion corridor and tolerance stack.",
            "Validate all lands, drills, mask and paste; no footprint created here.",
            "Resolve shielding, retention and full USB 3.x electrical design.",
        ],
        "release_permissions": {
            "canonical_replacement": False, "manufacturing": False,
            "public_export": False, "deployment": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = compile_audit(args.sources)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2) + "\n")
    print(payload["status"])


if __name__ == "__main__":
    main()
