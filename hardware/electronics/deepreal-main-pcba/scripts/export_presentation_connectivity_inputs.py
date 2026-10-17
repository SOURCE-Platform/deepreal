#!/usr/bin/env python3
"""Read-only native evidence for the separate nonworking presentation graph."""

import hashlib
import json
from pathlib import Path
import sys

import wx

APP = wx.App(False)
import pcbnew

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "tmp/usb-pd-interface-2026-10-16/mainboard-aon-07.kicad_pcb"
GEOMETRY = ROOT / "tmp/pcb-visual-demo-2026-10-17/candidate-01/source-geometry.json"


def main():
    output = Path(sys.argv[1]).resolve()
    if output.exists():
        raise ValueError("Refusing to overwrite an input export")
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    board = pcbnew.LoadBoard(str(SOURCE))
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    layers = [board.GetLayerID(name) for name in
              ["F.Cu"] + [f"In{i}.Cu" for i in range(1, 9)] + ["B.Cu"]]

    def point(p):
        return [round(pcbnew.ToMM(p.x), 6), round(pcbnew.ToMM(p.y), 6)]

    def layer_id(layer):
        return layers.index(layer) + 1

    pads, tracks, vias = [], [], []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pads.append({
                "ref": fp.GetReference(), "pad": pad.GetNumber(),
                "position": point(pad.GetPosition()), "net": pad.GetNetname(),
                "layers": [i + 1 for i, layer in enumerate(layers) if pad.IsOnLayer(layer)],
                "connected_track_uuids": sorted(str(t.m_Uuid.AsString())
                                               for t in connectivity.GetConnectedTracks(pad)),
            })
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append({
                "id": str(item.m_Uuid.AsString()), "position_mm": point(item.GetPosition()),
                "diameter_mm": pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)),
                "drill_mm": pcbnew.ToMM(item.GetDrillValue()), "net": item.GetNetname(),
                "span": [layer_id(item.TopLayer()), layer_id(item.BottomLayer())],
            })
        else:
            tracks.append({
                "id": str(item.m_Uuid.AsString()), "layer": layer_id(item.GetLayer()),
                "start": point(item.GetStart()), "end": point(item.GetEnd()),
                "width_mm": pcbnew.ToMM(item.GetWidth()), "net": item.GetNetname(),
            })
    geometry = json.loads(GEOMETRY.read_text())
    geometry["native_evidence"] = {"source_sha256": before, "pads": pads, "tracks": tracks, "vias": vias}
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != before:
        raise ValueError("Source board changed during read-only export")
    output.write_text(json.dumps(geometry, separators=(",", ":")) + "\n")
    print(json.dumps({
        "pads": len(pads), "tracks": len(tracks), "vias": len(vias),
        "source_unchanged": True, "source_sha256": before,
        "named_passive_terminals": [
            {"ref": p["ref"], "pad": p["pad"], "net": p["net"],
             "connected_tracks": len(p["connected_track_uuids"])}
            for p in pads if p["ref"].startswith(("C", "R")) and p["net"]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
