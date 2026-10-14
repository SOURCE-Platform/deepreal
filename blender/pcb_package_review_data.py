"""Strict provenance for the scoped MECH-FIT-04 package candidate."""

import json
from pathlib import Path

from pcb_candidate_review_data import ROOT, digest


def checked_inputs(directory, output, root=ROOT):
    root, directory, output = root.resolve(), directory.resolve(), output.resolve()
    if not directory.is_relative_to(root / "tmp") or \
            not output.is_relative_to(root / "tmp") or output.exists():
        raise ValueError("new private output and private candidate required")
    layout_path = directory / "engineering-layout-export.json"
    layout = json.loads(layout_path.read_text())
    manifest = json.loads((directory / "native-review-manifest.json").read_text())
    audit_path = directory / "package-audit.json"
    audit = json.loads(audit_path.read_text())
    meta = layout["metadata"]
    if meta.get("design_revision") != "MECH-FIT-04" or meta.get("is_canonical") is not False or \
            manifest.get("schema") != "deepreal.private-candidate-native.v1" or \
            manifest.get("revision") != "MECH-FIT-04" or \
            audit.get("schema") != "deepreal.pcb-package-candidate.v1" or \
            audit.get("revision") != "MECH-FIT-04":
        raise ValueError("unsupported package candidate")
    for document in (meta, manifest, audit):
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
            digest(board) != audit["source_board_sha256"] or \
            digest(layout_path) != manifest["source_export_sha256"] or \
            digest(glb) != manifest["glb_sha256"] or \
            digest(audit_path) != manifest["package_audit_sha256"]:
        raise ValueError("stale package candidate")
    status = root / "hardware/electronics/deepreal-main-pcba/design-status.json"
    if digest(status) != meta["source_status_sha256"] or \
            digest(status) != manifest["source_status_sha256"]:
        raise ValueError("design status changed")
    for path, key in (("datasheet", "datasheet_sha256"), ("library_footprint", "library_sha256")):
        if digest(Path(audit["D2"][path])) != audit["D2"][key]:
            raise ValueError("D2 evidence changed")
    for model in manifest["model_sources"]:
        path = Path(model["resolved"])
        if (digest(path) if path.is_file() else None) != model["sha256"]:
            raise ValueError("model library changed")
    refs = {c["ref"] for c in layout["components"]}
    groups = [set(manifest[k]) for k in
              ("native_model_refs", "missing_model_refs", "pad_or_hole_only_refs")]
    if len(refs) != 238 or set.union(*groups) != refs or sum(map(len, groups)) != len(refs):
        raise ValueError("incomplete or duplicated population")
    if audit["changed_footprint_refs"] != ["D2"] or len(layout["pads"]) != 2412:
        raise ValueError("package scope changed")
    if layout["tracks"] or layout["vias"] or layout["zones"] or any(p["net"] for p in layout["pads"]):
        raise ValueError("unrouted classification changed")
    return layout, manifest
