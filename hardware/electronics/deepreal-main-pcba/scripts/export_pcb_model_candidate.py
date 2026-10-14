#!/usr/bin/env python3
"""Export fresh KiCad geometry for a private, explicitly unreleased candidate."""

import argparse
import json
import subprocess
from pathlib import Path

from build_pcb_fit_candidate import ROOT, digest
from export_native_review import read_glb


def checked_layout(directory):
    if not directory.resolve().is_relative_to(ROOT / "tmp"):
        raise ValueError("private tmp candidate required")
    path = directory / "engineering-layout-export.json"
    data = json.loads(path.read_text())
    meta = data["metadata"]
    if meta.get("is_canonical") is not False or meta.get("design_revision") != "MECH-FIT-03":
        raise ValueError("unexpected candidate")
    if any(meta.get(k) is not False for k in
           ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
        raise ValueError("candidate release locks required")
    board = directory / meta["source_board"]
    if board.resolve().parent != directory.resolve() or digest(board) != meta["source_board_sha256"]:
        raise ValueError("stale or external board")
    if data["tracks"] or data["vias"] or data["zones"] or any(p["net"] for p in data["pads"]):
        raise ValueError("this private study must remain explicitly unrouted")
    return data, board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--kicad-cli", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    data, board = checked_layout(args.candidate_dir)
    output = args.candidate_dir
    glb = output / "main-pcba-native.glb"
    manifest_path = output / "native-review-manifest.json"
    if glb.exists() or manifest_path.exists() or not args.model_dir.is_dir():
        raise ValueError("choose unexported candidate and existing model library")
    if data["metadata"]["fixed_origin_mm"] != [65, 34]:
        raise ValueError("do not recenter the extended wing")
    command = [str(args.kicad_cli), "pcb", "export", "glb", "--output", str(glb),
               "--define-var", "KICAD10_3DMODEL_DIR=" + str(args.model_dir),
               "--include-tracks", "--include-pads", "--include-zones",
               "--include-silkscreen", "--include-soldermask", "--cut-vias-in-body",
               "--no-extra-pad-thickness", "--user-origin", "65x34mm", str(board)]
    sources = []
    for name in sorted({n for c in data["components"] for n in c["models"]}):
        path = Path(name.replace("${KICAD10_3DMODEL_DIR}", str(args.model_dir)))
        sources.append({"declared": name, "resolved": str(path),
                        "sha256": digest(path) if path.is_file() else None})
    run = subprocess.run(command, capture_output=True, text=True)
    (output / "native-export.log").write_text(run.stdout + run.stderr)
    run.check_returncode()
    document = read_glb(glb)
    names = {node.get("name") for node in document["nodes"]}
    represented = sorted(c["ref"] for c in data["components"] if c["ref"] in names)
    missing = sorted(c["ref"] for c in data["components"] if c["models"] and c["ref"] not in names)
    manifest = {
        "schema": "deepreal.private-candidate-native.v1",
        "source_board_sha256": digest(board),
        "source_export_sha256": digest(output / "engineering-layout-export.json"),
        "source_status_sha256": data["metadata"]["source_status_sha256"],
        "glb_sha256": digest(glb), "glb": glb.name, "origin_mm": [65, 34],
        "native_model_refs": represented, "missing_model_refs": missing,
        "pad_or_hole_only_refs": sorted(c["ref"] for c in data["components"] if not c["models"]),
        "model_sources": sources,
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
        "status": "PRIVATE_UNROUTED_MECHANICAL_STUDY",
        "warning": "Existing package substitutions remain; missing models require labelled body envelopes",
        "command": command,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Native models:", len(represented), "Representative bodies required:", missing)


if __name__ == "__main__":
    main()
