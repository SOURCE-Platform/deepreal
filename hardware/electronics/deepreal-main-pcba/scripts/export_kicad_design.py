#!/usr/bin/env python3
"""Export canonical KiCad geometry for downstream Blender use.

The export is descriptive only and inherits the design gate release locks.
"""

import json
import hashlib
from pathlib import Path

import wx

WX_APP = wx.App(False)
import pcbnew  # noqa: E402


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
BOARD_PATH = PROJECT / "deepreal-main-pcba.kicad_pcb"
STATUS_PATH = PROJECT / "design-status.json"
OUTPUT = PROJECT / "engineering-layout-export.json"


def mm(value):
    return pcbnew.ToMM(value)


def point(vector):
    return [round(mm(vector.x), 6), round(mm(vector.y), 6)]


def layer_name(board, item):
    return board.GetLayerName(item.GetLayer())


def board_outline(board):
    segments = []
    xs, ys = [], []
    for item in board.GetDrawings():
        if item.GetLayer() != pcbnew.Edge_Cuts:
            continue
        entry = {"shape": item.GetShapeStr(), "start_mm": point(item.GetStart()),
                 "end_mm": point(item.GetEnd())}
        segments.append(entry)
        xs.extend((entry["start_mm"][0], entry["end_mm"][0]))
        ys.extend((entry["start_mm"][1], entry["end_mm"][1]))
    return {
        "segments": segments,
        "bounds_mm": [min(xs), min(ys), max(xs), max(ys)] if xs else [],
        "thickness_mm": round(mm(board.GetDesignSettings().GetBoardThickness()), 6),
    }


def components(board):
    result = []
    for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
        bbox = fp.GetBoundingBox(False, False)
        models = []
        model_transforms = []
        for model in fp.Models():
            models.append(str(model.m_Filename))
            model_transforms.append({"path": str(model.m_Filename),
                "offset_mm": [model.m_Offset.x, model.m_Offset.y, model.m_Offset.z],
                "rotation_deg": [model.m_Rotation.x, model.m_Rotation.y, model.m_Rotation.z],
                "scale": [model.m_Scale.x, model.m_Scale.y, model.m_Scale.z]})
        fp.BuildCourtyardCaches()
        courtyard = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        polygons = []
        for index in range(courtyard.OutlineCount()):
            chain = courtyard.COutline(index)
            polygons.append([point(chain.CPoint(i)) for i in range(chain.PointCount())])
        result.append({
            "uuid": fp.m_Uuid.AsString(),
            "ref": fp.GetReference(),
            "value": fp.GetValue(),
            "footprint": str(fp.GetFPID().GetLibNickname()) + ":" + str(fp.GetFPID().GetLibItemName()),
            "side": "BOTTOM" if fp.IsFlipped() else "TOP",
            "position_mm": point(fp.GetPosition()),
            "rotation_deg": round(fp.GetOrientationDegrees(), 6),
            "graphics_bbox_mm": [
                round(mm(bbox.GetX()), 6), round(mm(bbox.GetY()), 6),
                round(mm(bbox.GetWidth()), 6), round(mm(bbox.GetHeight()), 6),
            ],
            "models": models,
            "model_transforms": model_transforms,
            "courtyard_polygons_mm": polygons,
        })
    return result


def copper(board):
    tracks, vias = [], []
    for item in board.GetTracks():
        common = {
            "net": item.GetNetname(),
            "net_code": item.GetNetCode(),
            "layer": layer_name(board, item),
        }
        if isinstance(item, pcbnew.PCB_VIA):
            common.update({
                "position_mm": point(item.GetPosition()),
                "diameter_mm": round(mm(item.GetWidth()), 6),
                "drill_mm": round(mm(item.GetDrillValue()), 6),
                "via_type": item.GetViaType(),
                "mask_open_top": not bool(item.IsTented(pcbnew.F_Cu)),
                "mask_open_bottom": not bool(item.IsTented(pcbnew.B_Cu)),
            })
            vias.append(common)
        else:
            common.update({
                "start_mm": point(item.GetStart()),
                "end_mm": point(item.GetEnd()),
                "width_mm": round(mm(item.GetWidth()), 6),
            })
            tracks.append(common)
    return tracks, vias


def holes(board):
    result = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if drill.x <= 0 and drill.y <= 0:
                continue
            result.append({
                "ref": fp.GetReference(),
                "pad": pad.GetNumber(),
                "position_mm": point(pad.GetPosition()),
                "drill_mm": [round(mm(drill.x), 6), round(mm(drill.y), 6)],
            })
    return result


def pads(board):
    result = []
    for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
        for pad in fp.Pads():
            size = pad.GetSize()
            result.append({
                "uuid": pad.m_Uuid.AsString(),
                "ref": fp.GetReference(),
                "number": pad.GetNumber(),
                "net": pad.GetNetname(),
                "net_code": pad.GetNetCode(),
                "position_mm": point(pad.GetPosition()),
                "size_mm": [round(mm(size.x), 6), round(mm(size.y), 6)],
                "rotation_deg": round(pad.GetOrientationDegrees(), 6),
                "shape_code": pad.GetShape(),
                "copper_top": bool(pad.IsOnLayer(pcbnew.F_Cu)),
                "copper_bottom": bool(pad.IsOnLayer(pcbnew.B_Cu)),
                "mask_open_top": bool(pad.IsOnLayer(pcbnew.F_Mask)),
                "mask_open_bottom": bool(pad.IsOnLayer(pcbnew.B_Mask)),
            })
    return result


def zones(board):
    result = []
    for zone in board.Zones():
        outline = zone.Outline()
        polygons = []
        for index in range(outline.OutlineCount()):
            chain = outline.COutline(index)
            polygons.append([point(chain.CPoint(i)) for i in range(chain.PointCount())])
        result.append({
            "net": zone.GetNetname(),
            "net_code": zone.GetNetCode(),
            "layers": [board.GetLayerName(layer) for layer in zone.GetLayerSet().Seq()],
            "polygons_mm": polygons,
        })
    return result


def main():
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    tracks, vias = copper(board)
    payload = {
        "metadata": {
            "schema": "deepreal.pcba.kicad-export.v1",
            "design": status["design"],
            "design_revision": status["design_revision"],
            "design_status": status["status"],
            "fabrication_allowed": status["fabrication_allowed"],
            "public_visual_allowed": status["public_visual_allowed"],
            "source_board": BOARD_PATH.name,
            "source_board_sha256": hashlib.sha256(BOARD_PATH.read_bytes()).hexdigest(),
            "source_status_sha256": hashlib.sha256(STATUS_PATH.read_bytes()).hexdigest(),
        },
        "board": board_outline(board),
        "components": components(board),
        "holes": holes(board),
        "pads": pads(board),
        "tracks": tracks,
        "vias": vias,
        "zones": zones(board),
        "validation_status": {gate["id"]: gate["status"]
                              for gate in status["gates"]},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Exported", OUTPUT)
    print("components / tracks / vias / zones:",
          len(payload["components"]), len(tracks), len(vias), len(payload["zones"]))


if __name__ == "__main__":
    main()
