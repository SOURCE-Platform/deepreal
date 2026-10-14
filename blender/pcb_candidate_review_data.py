"""Private-candidate provenance guards, separate from the canonical importer."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_inputs(directory, output, root=ROOT):
    root = root.resolve()
    directory, output = directory.resolve(), output.resolve()
    if not directory.is_relative_to(root / "tmp") or \
            not output.is_relative_to(root / "tmp") or output.exists():
        raise ValueError("use private tmp input and a new private output directory")
    layout_path = directory / "engineering-layout-export.json"
    layout = json.loads(layout_path.read_text())
    manifest = json.loads((directory / "native-review-manifest.json").read_text())
    meta = layout["metadata"]
    if meta.get("design_revision") != "MECH-FIT-03" or meta.get("is_canonical") is not False or \
            manifest.get("schema") != "deepreal.private-candidate-native.v1":
        raise ValueError("not a supported private candidate")
    for document in (meta, manifest):
        if any(document.get(k) is not False for k in
               ("fabrication_allowed", "public_visual_allowed", "viewer_integration_allowed")):
            raise ValueError("explicit release locks required")
    if meta["fixed_origin_mm"] != [65, 34] or manifest["origin_mm"] != [65, 34]:
        raise ValueError("fixed core datum changed")
    board, glb = directory / meta["source_board"], directory / manifest["glb"]
    if board.resolve().parent != directory or glb.resolve().parent != directory:
        raise ValueError("candidate path escaped")
    if digest(board) != meta["source_board_sha256"] or \
            digest(board) != manifest["source_board_sha256"] or \
            digest(layout_path) != manifest["source_export_sha256"] or \
            digest(glb) != manifest["glb_sha256"]:
        raise ValueError("stale private candidate geometry")
    status = root / "hardware/electronics/deepreal-main-pcba/design-status.json"
    if digest(status) != meta["source_status_sha256"] or \
            digest(status) != manifest["source_status_sha256"]:
        raise ValueError("design status changed")
    for model in manifest["model_sources"]:
        path = Path(model["resolved"])
        if (digest(path) if path.is_file() else None) != model["sha256"]:
            raise ValueError("model library changed")
    refs = {c["ref"] for c in layout["components"]}
    groups = [set(manifest[k]) for k in
              ("native_model_refs", "missing_model_refs", "pad_or_hole_only_refs")]
    if set.union(*groups) != refs or sum(map(len, groups)) != len(refs):
        raise ValueError("incomplete or duplicated population classification")
    if layout["tracks"] or layout["vias"] or layout["zones"] or any(p["net"] for p in layout["pads"]):
        raise ValueError("unrouted classification is no longer accurate")
    return layout, manifest
