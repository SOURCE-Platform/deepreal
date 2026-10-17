#!/usr/bin/env python3
"""Polish presentation metadata without modifying any native engineering board."""

import hashlib
import json
from pathlib import Path
import sys

import wx

APP = wx.App(False)
import pcbnew

ROOT = Path(__file__).resolve().parents[4]
OLD = ROOT / "blender/review-output/web/pcb-visual-demo-01/visual-routing-demo.json"
BASE = ROOT / "blender/review-output/web/pcb-visual-05-aon01"
SOURCE = ROOT / "tmp/usb-pd-interface-2026-10-16/mainboard-aon-07.kicad_pcb"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(position):
    return [round(pcbnew.ToMM(position.x), 6), round(pcbnew.ToMM(position.y), 6)]


def main():
    output = Path(sys.argv[1]).resolve()
    if output.exists() or output.parent != ROOT / "blender/review-output/web":
        raise ValueError("Choose a new local presentation asset directory")
    demo = json.loads(OLD.read_text())
    manifest = json.loads((BASE / "main-pcba-review.json").read_text())
    if sha(SOURCE) != demo["source_board_sha256"] or sha(BASE / "main-pcba-review.glb") != demo["base_asset_sha256"]:
        raise ValueError("Protected engineering inputs changed")
    board = pcbnew.LoadBoard(str(SOURCE))
    components = {c["reference"]: c for c in manifest["components"]}
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    packages = []
    omitted_marker_pads = 0
    for ref, component in components.items():
        if not ref.startswith("U") or not any(s in component["model_status"] for s in
                ("ENVELOPE", "REPRESENTATIVE_SOURCE_DIMENSION")):
            continue
        footprint = footprints[ref]
        smd = [p for p in footprint.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        pads = [p for p in smd if min(pcbnew.ToMM(p.GetBoundingBox().GetWidth()),
                                    pcbnew.ToMM(p.GetBoundingBox().GetHeight())) >= .04]
        omitted_marker_pads += len(smd) - len(pads)
        pin_one = next((p for p in pads if p.GetNumber() in ("A1", "1")), None)
        if not pads or pin_one is None:
            raise ValueError("Missing presentation contact geometry: " + ref)
        packages.append({
            "ref": ref, "object": component["object"],
            "kind": "bga" if any(s in component["footprint"] for s in ("BGA", "WLCSP")) else "leadless",
            "layer": 0 if footprint.GetLayer() == pcbnew.F_Cu else 1,
            "pin_one_mm": point(pin_one.GetPosition()),
            "contacts": [{
                "pad": p.GetNumber(), "position_mm": point(p.GetPosition()),
                "size_mm": [round(pcbnew.ToMM(p.GetBoundingBox().GetWidth()), 6),
                            round(pcbnew.ToMM(p.GetBoundingBox().GetHeight()), 6)],
            } for p in pads],
        })
    endpoint_pads = {}
    for connection in demo["connections"]:
        for endpoint in connection["endpoints"]:
            if endpoint["ref"] == "VISUAL_VIA":
                continue
            fp = footprints[endpoint["ref"]]
            candidates = [p for p in fp.Pads() if p.GetNumber() == endpoint["pad"]
                          and max(abs(a-b) for a, b in zip(point(p.GetPosition()), endpoint["position"])) < .00001]
            if not candidates:
                raise ValueError("Demo endpoint does not match a physical source pad")
            layers = sorted({i for p in candidates for i, layer in enumerate((pcbnew.F_Cu, pcbnew.B_Cu))
                             if p.IsOnLayer(layer)})
            key = (endpoint["ref"], endpoint["pad"], *endpoint["position"])
            endpoint_pads[key] = {**endpoint, "layers": layers}
    exclusions = []
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetText().startswith(
                ("Support placeholders:", "UNROUTED:", "PRELIMINARY PLACEMENT", "DEEPREAL MAIN PCBA")):
            box = item.GetBoundingBox()
            exclusions.append({
                "layer": 0 if item.GetLayer() == pcbnew.F_SilkS else 1,
                "bounds_mm": [pcbnew.ToMM(box.GetX())-.15, pcbnew.ToMM(box.GetY())-.15,
                              pcbnew.ToMM(box.GetRight())+.15, pcbnew.ToMM(box.GetBottom())+.15],
            })
    demo.update({
        "schema": "deepreal.pcb-visual-demo.v2",
        "visual_revision": "PRESENTATION_POLISH_02",
        # Source F.Cu is next to TOP component bodies at higher glTF Z.
        "surface_z_m": [-.010531, -.012169],
        "pad_surface_z_m": [-.01056, -.01214],
        "focus_bounds_mm": [30, 22, 84, 43],
        "packages": sorted(packages, key=lambda p: p["ref"]),
        "endpoint_pads": list(endpoint_pads.values()),
        "silkscreen_exclusions": exclusions,
        "presentation_package_geometry_changed": True,
        "package_models_manufacturer_qualified": False,
    })
    demo["limits"][2] = (
        "Default traces represent mask-covered copper; inspection highlights them for readability, not a mask fabrication definition.")
    demo["limits"].extend([
        "Generic presentation package bodies and contacts follow existing body envelopes and footprint pads, not manufacturer-qualified CAD.",
        "Large layout annotations that overlap parts are hidden only in presentation mode; the persistent nonworking disclosure and original engineering silkscreen remain unchanged.",
        "Fan-out vias and geometric pad pairs do not establish complete or functional circuit connections.",
    ])
    output.mkdir()
    data_path = output / "visual-routing-demo.json"
    data_path.write_text(json.dumps(demo, separators=(",", ":")) + "\n")
    report = {
        "status": "PRESENTATION_POLISH_REQUIRES_RENDERED_REVIEW",
        "source_board_sha256": sha(SOURCE), "base_glb_sha256": sha(BASE / "main-pcba-review.glb"),
        "previous_demo_data_sha256": sha(OLD), "data_sha256": sha(data_path),
        "generic_presentation_packages": len(packages),
        "presentation_contacts": sum(len(p["contacts"]) for p in packages),
        "tiny_source_marker_pads_not_rendered_as_contacts": omitted_marker_pads,
        "source_endpoint_pads": len(endpoint_pads), "hidden_diagnostic_annotations": len(exclusions),
        "illustrative_segments": demo["illustrative_segment_count"],
        "illustrative_vias": demo["illustrative_via_count"],
        "engineering_files_modified": False, "electrical_qualification_claimed": False,
    }
    (output / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
