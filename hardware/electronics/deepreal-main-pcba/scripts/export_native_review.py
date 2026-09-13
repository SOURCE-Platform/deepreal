#!/usr/bin/env python3
"""Build native KiCad review geometry, never fabrication outputs.

Run export_kicad_design.py first with KiCad's Python. Missing component models
are recorded, not substituted by visually similar vendor packages.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

PROJECT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT / "generated-review"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
    with path.open("rb") as stream:
        magic, version, total = struct.unpack("<4sII", stream.read(12))
        size, kind = struct.unpack("<I4s", stream.read(8))
        if magic != b"glTF" or version != 2 or kind != b"JSON":
            raise ValueError("not a GLB 2 JSON header")
        return json.loads(stream.read(size))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad-cli", default=shutil.which("kicad-cli"))
    parser.add_argument("--model-dir", type=Path,
                        help="override KICAD10_3DMODEL_DIR for portable builds")
    args = parser.parse_args()
    if not args.kicad_cli:
        parser.error("supply --kicad-cli with the installed CLI path")
    data_path = PROJECT / "engineering-layout-export.json"
    data = json.loads(data_path.read_text())
    board = PROJECT / data["metadata"]["source_board"]
    if digest(board) != data["metadata"].get("source_board_sha256"):
        raise ValueError("stale layout JSON: run export_kicad_design.py first")
    OUTPUT.mkdir(exist_ok=True)
    glb = OUTPUT / "main-pcba-native.glb"
    x0, y0, x1, y1 = data["board"]["bounds_mm"]
    origin = [(x0+x1)/2, (y0+y1)/2]
    command = [args.kicad_cli, "pcb", "export", "glb", "--force",
               "--output", str(glb), "--include-tracks", "--include-pads",
               "--include-zones", "--include-silkscreen", "--include-soldermask",
               "--cut-vias-in-body", "--no-extra-pad-thickness",
               "--user-origin", "{}x{}mm".format(*origin), str(board)]
    model_dir = args.model_dir or Path(os.environ.get("KICAD10_3DMODEL_DIR",
        str(Path(args.kicad_cli).resolve().parent.parent / "SharedSupport" / "3dmodels")))
    if not model_dir.is_dir():
        parser.error("supply --model-dir pointing to the installed KiCad 3D library")
    command[5:5] = ["--define-var", "KICAD10_3DMODEL_DIR="+str(model_dir)]
    model_sources = []
    for name in sorted({p for c in data["components"] for p in c["models"]}):
        resolved = Path(os.path.expandvars(name.replace("${KICAD10_3DMODEL_DIR}",
            str(model_dir)).replace("${KIPRJMOD}", str(PROJECT))))
        model_sources.append({"declared": name, "resolved": str(resolved),
                              "sha256": digest(resolved) if resolved.is_file() else None})
    run = subprocess.run(command, capture_output=True, text=True)
    (OUTPUT / "native-export.log").write_text(run.stdout + run.stderr)
    run.check_returncode()
    document = read_glb(glb)
    names = {node.get("name") for node in document["nodes"]}
    represented = sorted(c["ref"] for c in data["components"] if c["ref"] in names)
    missing = [c["ref"] for c in data["components"]
               if c["models"] and c["ref"] not in names]
    pad_only = [c["ref"] for c in data["components"] if not c["models"]]
    manifest = {
        "schema": "deepreal.native-review.v1", "source_board_sha256": digest(board),
        "source_export_sha256": digest(data_path), "glb_sha256": digest(glb),
        "glb": glb.name, "origin_mm": origin,
        "kicad_version": subprocess.check_output(
            [args.kicad_cli, "version"], text=True).strip(),
        "native_model_refs": represented, "missing_model_refs": missing,
        "model_sources": model_sources,
        "pad_or_hole_only_refs": pad_only,
        "fabrication_allowed": False, "public_visual_allowed": False,
        "status": "INTERNAL_REVIEW_ONLY_UNROUTED_UNVERIFIED_FOOTPRINTS",
        "warning": "Native import preserves existing footprint errors; it does not validate the design.",
    }
    (OUTPUT / "native-review-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({k:manifest[k] for k in (
        "status", "missing_model_refs", "pad_or_hole_only_refs")}, indent=2))
    print("Native component models:", len(represented))


if __name__ == "__main__":
    main()
