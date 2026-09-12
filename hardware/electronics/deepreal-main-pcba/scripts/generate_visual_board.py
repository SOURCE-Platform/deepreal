#!/usr/bin/env python3
"""Generate the non-fabrication KiCad board used for website visualization.

The canonical engineering board stays placement-only.  This derivative adds
the shared illustrative copper from Blender's visual layout contract.
"""

import json
from pathlib import Path
import sys

import wx

WX_APP = wx.App(False)
import pcbnew  # noqa: E402


HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
REPO_ROOT = PROJECT_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT / "blender"))
sys.path.insert(0, str(HERE))

from generate_preliminary_board import build_board, mm, point  # noqa: E402
from pcba_visual_layout import (  # noqa: E402
    DISCLAIMER, POURS, TEST_PADS, TRACE_GROUPS, VIAS,
)


SOURCE = PROJECT_DIR / "deepreal-main-pcba.kicad_pcb"
OUTPUT = PROJECT_DIR / "deepreal-main-pcba-visual.kicad_pcb"
SUMMARY = PROJECT_DIR / "visual-layout-summary.json"
X_OFFSET = 65.0
Y_OFFSET = 22.5


def to_board_xy(x, z):
    return x + X_OFFSET, Y_OFFSET - z


def add_copper_segment(board, start, end, side, width):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetStart(point(*to_board_xy(*start)))
    shape.SetEnd(point(*to_board_xy(*end)))
    shape.SetLayer(pcbnew.F_Cu if side == "TOP" else pcbnew.B_Cu)
    shape.SetWidth(mm(width))
    board.Add(shape)


def add_copper_rect(board, center, size, side):
    x, y = to_board_xy(*center)
    width, height = size
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_RECT)
    shape.SetStart(point(x - width / 2, y - height / 2))
    shape.SetEnd(point(x + width / 2, y + height / 2))
    shape.SetLayer(pcbnew.F_Cu if side == "TOP" else pcbnew.B_Cu)
    shape.SetWidth(mm(0.05))
    shape.SetFilled(True)
    board.Add(shape)


def add_via(board, x, z, width=0.52, drill=0.24):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(point(*to_board_xy(x, z)))
    via.SetWidth(mm(width))
    via.SetDrill(mm(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def replace_board_labels(board):
    replacements = {
        "PRELIMINARY PLACEMENT — NOT FOR FABRICATION":
            "PRODUCTION-INTENT VISUALIZATION",
        "UNROUTED: vendor pin maps + FPGA + DDR gates open":
            "ILLUSTRATIVE COPPER - NOT FOR FABRICATION",
    }
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT):
            current = item.GetText()
            if current in replacements:
                item.SetText(replacements[current])


def write_summary(trace_count):
    payload = {
        "artifact": OUTPUT.name,
        "status": "production-intent engineering visualization",
        "fabrication_allowed": False,
        "disclaimer": DISCLAIMER,
        "board_mm": [90.0, 28.0, 1.6],
        "trace_groups": len(TRACE_GROUPS),
        "trace_paths": trace_count,
        "visual_vias": len(VIAS),
        "visual_pours": len(POURS),
        "test_pads": len(TEST_PADS),
        "source_of_placement": "blender/pcba_bom.py",
        "source_of_visual_copper": "blender/pcba_visual_layout.py",
    }
    SUMMARY.write_text(json.dumps(payload, indent=2) + "\n")


def build_visual_board():
    build_board()
    board = pcbnew.LoadBoard(str(SOURCE))
    board.SetFileName(str(OUTPUT))
    title = board.GetTitleBlock()
    title.SetTitle("DeepReal Main PCBA — PRODUCTION-INTENT VISUALIZATION")
    title.SetRevision("0.3-visual")
    title.SetComment(0, "90 x 28 mm; illustrative surface copper")
    title.SetComment(1, "NOT ELECTRICALLY ROUTED / NOT FOR FABRICATION")
    title.SetComment(2, "Website and investor presentation artifact only")
    board.SetTitleBlock(title)
    replace_board_labels(board)

    trace_count = 0
    for pour in POURS:
        add_copper_rect(board, pour["center"], pour["size"], pour["side"])
    for group in TRACE_GROUPS:
        for path in group["paths"]:
            trace_count += 1
            for start, end in zip(path, path[1:]):
                add_copper_segment(board, start, end, group["side"],
                                   group["width"])
    for via in VIAS:
        width = 0.62 if via["kind"] == "POWER_THERMAL" else 0.52
        add_via(board, via["x"], via["z"], width)
    for pad in TEST_PADS:
        add_via(board, pad["x"], pad["z"], 0.84, 0.28)

    pcbnew.SaveBoard(str(OUTPUT), board)
    write_summary(trace_count)
    return trace_count


if __name__ == "__main__":
    count = build_visual_board()
    print("Generated", OUTPUT)
    print("Visual copper paths:", count)
    print(DISCLAIMER)
