#!/usr/bin/env python3
"""Create a separate NONWORKING illustrative PCB, never an engineering release."""

import hashlib
import json
import math
from pathlib import Path
import sys

import wx

WX_APP = wx.App(False)
import pcbnew

from demo_pcb_router import design_demo

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "tmp/usb-pd-interface-2026-10-16/mainboard-aon-07.kicad_pcb"
SOURCE_SHA = "51f3bec8d1b0885a5ee136b3b1fc5c9391d1f12ed878cb9be424826a71864c7a"
BASE_ASSET_SHA = "d9675b1317e6e4db468a751ab4fca5fe21e01bbe8af47591feca6b6e62cbc686"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm_point(point):
    return [round(pcbnew.ToMM(point.x), 6), round(pcbnew.ToMM(point.y), 6)]


def geometry(board):
    edges = []
    for item in board.GetDrawings():
        if item.GetLayer() == pcbnew.Edge_Cuts:
            edges.append((mm_point(item.GetStart()), mm_point(item.GetEnd())))
    loops = []
    while edges:
        start, end = edges.pop(0)
        loop = [start, end]
        while math.dist(loop[-1], loop[0]) > .001:
            found = next((i for i, edge in enumerate(edges)
                          if min(math.dist(loop[-1], edge[0]), math.dist(loop[-1], edge[1])) < .001), None)
            if found is None:
                raise ValueError("Native board outline is not closed")
            a, b = edges.pop(found)
            loop.append(b if math.dist(loop[-1], a) < .001 else a)
        loops.append(loop[:-1])
    pads, centers = [], {}
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        centers[ref] = mm_point(footprint.GetPosition())
        for pad in footprint.Pads():
            layers = [i for i, layer in enumerate((pcbnew.F_Cu, pcbnew.B_Cu)) if pad.IsOnLayer(layer)]
            if not layers:
                continue
            bbox = pad.GetBoundingBox()
            pads.append({"ref": ref, "pad": pad.GetNumber(), "position": mm_point(pad.GetPosition()),
                         "aabb_size": [pcbnew.ToMM(bbox.GetWidth()), pcbnew.ToMM(bbox.GetHeight())],
                         "net": pad.GetNetname(), "layers": layers})
    tracks = []
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_VIA) and item.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            tracks.append({"start": mm_point(item.GetStart()), "end": mm_point(item.GetEnd()),
                           "width": pcbnew.ToMM(item.GetWidth()),
                           "layer": 0 if item.GetLayer() == pcbnew.F_Cu else 1})
    return {"outlines": loops, "pads": pads, "centers": centers, "existing_surface_tracks": tracks}


def main():
    if len(sys.argv) != 2:
        raise ValueError("Pass a new output directory below repository tmp")
    output = Path(sys.argv[1]).resolve()
    if ROOT / "tmp" not in output.parents or output.exists():
        raise ValueError("Refusing to overwrite an output or write outside private tmp")
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError("Protected engineering board changed")
    board = pcbnew.LoadBoard(str(SOURCE))
    source_track_ids = {item.m_Uuid.AsString() for item in board.GetTracks()}
    before_geometry = [(fp.m_Uuid.AsString(), mm_point(fp.GetPosition()), fp.GetOrientationDegrees())
                       for fp in board.GetFootprints()]
    data = geometry(board)
    output.mkdir(parents=True)
    (output / "source-geometry.json").write_text(json.dumps(data, indent=2) + "\n")
    print("Routing a geometry-only visual demo; no circuit connectivity is implied", flush=True)
    demo = design_demo(data)
    segments = []
    for connection in demo["connections"]:
        for route in connection["paths"]:
            for start, end in zip(route["points"], route["points"][1:]):
                track = pcbnew.PCB_TRACK(board)
                track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1])))
                track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1])))
                track.SetWidth(pcbnew.FromMM(connection["width_mm"]))
                track.SetLayer(pcbnew.F_Cu if route["layer"] == 0 else pcbnew.B_Cu)
                # Start unassigned. KiCad may infer labels on save; none are verified signals.
                track.SetNetCode(0)
                board.Add(track)
                segments.append((route["layer"], start, end, connection["width_mm"]))
    for entry in demo["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in entry["position_mm"]]))
        via.SetWidth(pcbnew.FromMM(entry["diameter_mm"]))
        via.SetDrill(pcbnew.FromMM(entry["drill_mm"]))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetNetCode(0)
        board.Add(via)
    board.SetTitleBlock(board.GetTitleBlock())
    title = board.GetTitleBlock()
    title.SetTitle("NONWORKING VISUAL DEMO - ILLUSTRATIVE COPPER ONLY")
    title.SetComment(0, "NOT ELECTRICALLY VALIDATED. NOT FOR FABRICATION.")
    board.SetTitleBlock(title)
    native = output / "nonworking-visual-routing-demo.kicad_pcb"
    pcbnew.SaveBoard(str(native), board)
    inferred_labels = {
        "segments": sum(bool(t.GetNetname()) for t in board.GetTracks()
                        if t.m_Uuid.AsString() not in source_track_ids and not isinstance(t, pcbnew.PCB_VIA)),
        "vias": sum(bool(t.GetNetname()) for t in board.GetTracks()
                    if t.m_Uuid.AsString() not in source_track_ids and isinstance(t, pcbnew.PCB_VIA)),
    }
    if before_geometry != [(fp.m_Uuid.AsString(), mm_point(fp.GetPosition()), fp.GetOrientationDegrees())
                           for fp in board.GetFootprints()] or sha(SOURCE) != SOURCE_SHA:
        raise ValueError("Source component placement changed")
    demo.update({
        "schema": "deepreal.pcb-visual-demo.v1", "status": "NONWORKING_VISUAL_DEMO",
        "source_board_sha256": SOURCE_SHA, "base_asset_sha256": BASE_ASSET_SHA,
        "demo_board_sha256": sha(native),
        "disclosure": "Nonworking PCB demo. Illustrative routing, not electrically validated.",
        "coordinate_system": "KICAD_MM_ORIGIN_65_22P5_GLTF_Z_SURFACES",
        "surface_z_m": [-.012169, -.010531],
        "focus_bounds_mm": [48, 23, 82, 38],
        "outlines_mm": data["outlines"], "illustrative_connection_count": len(demo["connections"]),
        "illustrative_segment_count": len(segments), "illustrative_via_count": len(demo["vias"]),
        "electrical_connectivity_verified": False, "signal_pin_mapping_verified": False,
        "manufacturing_rules_verified": False, "fabrication_allowed": False,
        "public_visual_allowed": False, "source_component_placement_changed": False,
        "usb_geometry_changed": False,
        "native_inferred_net_labels_not_verified": inferred_labels,
        "limits": [
            "Endpoint pairs are selected geometrically for a disclosed visual demo, not from a circuit netlist.",
            "Illustrative traces are native copper on a separate private board; any KiCad-inferred net labels are not verified signal assignments.",
            "Copper is shown exposed above the mask for readability; this is not a solder-mask manufacturing definition.",
            "No electrical function, impedance, length matching, current capacity, clearance or manufacturing approval is established.",
            "The existing engineering board, schematic and protected GLB remain separate and unchanged.",
        ],
    })
    (output / "visual-routing-demo.json").write_text(json.dumps(demo, separators=(",", ":")) + "\n")
    (output / "build-report.json").write_text(json.dumps({
        "source_board_sha256": SOURCE_SHA, "demo_board_sha256": sha(native),
        "data_sha256": sha(output / "visual-routing-demo.json"),
        "illustrative_connections": len(demo["connections"]),
        "illustrative_segments": len(segments), "illustrative_vias": len(demo["vias"]),
        "unrouted_visual_attempts": demo["unrouted_visual_attempts"],
        "source_placement_unchanged": True, "engineering_design_changed": False,
        "electrical_qualification_claimed": False,
        "native_inferred_net_labels_not_verified": inferred_labels,
    }, indent=2) + "\n")
    print("VISUAL_DEMO", len(demo["connections"]), "illustrative connections",
          len(segments), "segments", len(demo["vias"]), "vias", flush=True)


if __name__ == "__main__":
    main()
