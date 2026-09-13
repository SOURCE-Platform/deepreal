#!/usr/bin/env python3
"""Historical Blender-driven placement generator for the Main PCBA.

The canonical KiCad board superseded this source direction. Direct execution is
guarded because it would overwrite the engineering placement with concept data.
"""

from pathlib import Path
import sys

import wx

WX_APP = wx.App(False)
import pcbnew  # noqa: E402


HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
REPO_ROOT = PROJECT_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT / "blender"))

from pcba_bom import ALL_PARTS, PLANNING_ZONES  # noqa: E402
from pcba_visual_layout import visual_route_keepout  # noqa: E402


LIB_ROOT = Path(
    "/Users/adam/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
)
OUTPUT = PROJECT_DIR / "deepreal-main-pcba.kicad_pcb"
X_OFFSET = 65.0
Y_OFFSET = 22.5
MOUNT_POINTS = ((-42.0, -22.5), (-42.0, -0.5), (42.0, -22.5), (42.0, -0.5))


FOOTPRINTS = {
    "U1": ("Package_BGA", "BGA-324_15x15mm_Layout18x18_P0.8mm"),
    "U2": ("Package_BGA", "ST_UFBGA-121_6x6mm_Layout11x11_P0.5mm"),
    "U3": ("Package_BGA", "ST_UFBGA-121_6x6mm_Layout11x11_P0.5mm"),
    "U4": ("Package_BGA", "BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm"),
    "U5": ("Package_DFN_QFN", "QFN-56-1EP_8x8mm_P0.5mm_EP6.1x6.1mm_ThermalVias"),
    "U6": ("Package_DFN_QFN", "QFN-24-1EP_4x4mm_P0.5mm_EP2.8x2.8mm"),
    "U7": ("Package_DFN_QFN", "QFN-24-1EP_4x4mm_P0.5mm_EP2.8x2.8mm"),
    "U8": ("Package_DFN_QFN", "DFN-10-1EP_3x3mm_P0.5mm_EP1.7x2.5mm"),
    "U9": ("Package_DFN_QFN", "DFN-10-1EP_3x3mm_P0.5mm_EP1.7x2.5mm"),
    "U10": ("Package_DFN_QFN", "LQFN-10-1EP_2x2mm_P0.5mm_EP0.7x0.7mm"),
    "U11": ("Package_DFN_QFN", "QFN-24-1EP_4x4mm_P0.5mm_EP2.8x2.8mm"),
    "U12": ("Package_DFN_QFN", "WQFN-20-1EP_2.5x4.5mm_P0.5mm_EP1x2.9mm"),
    "U13": ("Package_DFN_QFN", "Texas_RTE0016D_WQFN-16-1EP_3x3mm_P0.5mm_EP0.8x0.8mm_ThermalVias"),
    "U14": ("Package_DFN_QFN", "Texas_RTE0016D_WQFN-16-1EP_3x3mm_P0.5mm_EP0.8x0.8mm_ThermalVias"),
    "U15": ("Package_BGA", "LFBGA-153_11.5x13mm_Layout14x14_P0.5mm"),
    "U16": ("Package_DFN_QFN", "DFN-8-1EP_2x3mm_P0.5mm_EP0.61x2.2mm"),
    "U17": ("Package_SON", "Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_ThermalVias"),
    "U18": ("Package_CSP", "WLCSP-16_2.225x2.17mm_Layout4x4_P0.5mm"),
    "U19": ("Package_CSP", "WLCSP-16_2.225x2.17mm_Layout4x4_P0.5mm"),
    "U20": ("Package_SON", "WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm"),
    "MK1": ("Sensor_Audio", "Knowles_LGA-5_3.5x2.65mm"),
    "D1": ("Package_SON", "USON-10_2.5x1.0mm_P0.5mm"),
    "D2": ("Package_SON", "USON-10_2.5x1.0mm_P0.5mm"),
    "D9": ("Diode_SMD", "D_SMA"),
    "J1": ("Connector_USB", "USB_C_Receptacle_Amphenol_12401610E4-2A"),
    "J2": ("Connector_FFC-FPC", "Hirose_FH26-51S-0.3SHW_2Rows-51Pins-1MP_P0.60mm_Horizontal"),
    "J3": ("Connector_FFC-FPC", "Hirose_FH26-51S-0.3SHW_2Rows-51Pins-1MP_P0.60mm_Horizontal"),
    "J4": ("Connector_PinHeader_1.00mm", "PinHeader_1x06_P1.00mm_Vertical"),
    "J5": ("Connector_PinHeader_1.00mm", "PinHeader_1x06_P1.00mm_Vertical"),
}


def mm(value):
    return pcbnew.FromMM(value)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_line(board, start, end, layer, width=0.15):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetStart(point(*start))
    shape.SetEnd(point(*end))
    shape.SetLayer(layer)
    shape.SetWidth(mm(width))
    board.Add(shape)


def add_rect(board, center, size, layer, width=0.15):
    x, y = center
    w, h = size
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_RECT)
    shape.SetStart(point(x - w / 2, y - h / 2))
    shape.SetEnd(point(x + w / 2, y + h / 2))
    shape.SetLayer(layer)
    shape.SetWidth(mm(width))
    board.Add(shape)


def add_text(board, text, position, layer, size=1.0):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(point(*position))
    item.SetLayer(layer)
    item.SetTextSize(point(size, size))
    item.SetTextThickness(mm(max(0.15, size * 0.14)))
    board.Add(item)


def load_footprint(library, name):
    footprint = pcbnew.FootprintLoad(str(LIB_ROOT / f"{library}.pretty"), name)
    if footprint is None:
        raise FileNotFoundError(f"Missing KiCad footprint: {library}:{name}")
    return footprint


def place_footprint(
    board, library, name, ref, value, xy, side="TOP", angle=0, show_reference=True
):
    footprint = load_footprint(library, name)
    footprint.SetReference(ref)
    footprint.SetValue(value)
    footprint.Reference().SetVisible(show_reference)
    footprint.Reference().SetTextSize(point(0.65, 0.65))
    footprint.Reference().SetTextThickness(mm(0.12))
    footprint.Value().SetVisible(False)
    footprint.SetPosition(point(*xy))
    footprint.SetOrientationDegrees(angle)
    board.Add(footprint)
    if side == "BOTTOM":
        footprint.Flip(point(*xy), False)
    return footprint


def to_board_xy(part):
    return part["x"] + X_OFFSET, Y_OFFSET - part["z"]


def blocked(x, y, side, parts):
    for part in parts:
        if part["side"] != side:
            continue
        px, py = to_board_xy(part)
        if abs(x - px) < part["width"] / 2 + 0.75 and abs(y - py) < part["depth"] / 2 + 0.75:
            return True
    for hx, hz in MOUNT_POINTS:
        px, py = hx + X_OFFSET, Y_OFFSET - hz
        if (x - px) ** 2 + (y - py) ** 2 < 2.2 ** 2:
            return True
    return visual_route_keepout(
        x - X_OFFSET, Y_OFFSET - y, side, 1.0, 0.5)


def place_passive_field(
    board, parts, side, count, prefix, footprint, value, phase=0, ref_start=1
):
    candidates = []
    for row, y in enumerate([21.3 + 1.3 * i for i in range(20)]):
        for col, x in enumerate([22.3 + 1.3 * i for i in range(66)]):
            if x > 107.7 or y > 46.7 or (row + col + phase) % 3:
                continue
            if not blocked(x, y, side, parts):
                candidates.append((x, y, 90 if (row + col) % 3 == 0 else 0))
    if len(candidates) < count:
        raise RuntimeError(f"Only {len(candidates)} legal {side} passive sites for {count} parts")
    selected = [candidates[(index * len(candidates)) // count] for index in range(count)]
    for index, (x, y, angle) in enumerate(selected, ref_start):
        place_footprint(
            board, footprint[0], footprint[1], f"{prefix}{index}", value,
            (x, y), side, angle, show_reference=False,
        )
    return count


def planning_part(ref, xy, size, side="TOP"):
    """Return a BOM-shaped exclusion entry for added placement-study parts."""
    return {
        "ref": ref, "x": xy[0] - X_OFFSET, "z": Y_OFFSET - xy[1],
        "width": size[0], "depth": size[1], "side": side,
    }


def build_board():
    board = pcbnew.BOARD()
    board.SetFileName(str(OUTPUT))
    board.SetCopperLayerCount(10)
    settings = board.GetDesignSettings()
    settings.m_MinClearance = mm(0.075)
    settings.m_CopperEdgeClearance = mm(0.15)
    settings.m_MinThroughDrill = mm(0.15)
    settings.m_ViasMinSize = mm(0.3)
    settings.m_ViasMinAnnularWidth = mm(0.075)
    title = board.GetTitleBlock()
    title.SetTitle("DeepReal Main PCBA — PRELIMINARY PLACEMENT")
    title.SetCompany("DeepReal")
    title.SetRevision("0.2-placement")
    title.SetComment(0, "90 x 28 mm; 10-layer HDI working assumption")
    title.SetComment(1, "NOT ROUTED / NOT FOR FABRICATION")
    board.SetTitleBlock(title)

    # Exact working outline and the four mechanical mount locations from Blender.
    for start, end in [((20, 20), (110, 20)), ((110, 20), (110, 48)),
                       ((110, 48), (20, 48)), ((20, 48), (20, 20))]:
        add_line(board, start, end, pcbnew.Edge_Cuts, 0.1)
    for index, (hx, hz) in enumerate(MOUNT_POINTS, 1):
        place_footprint(
            board, "MountingHole", "MountingHole_2.7mm_M2.5_ISO14580_Pad_TopBottom",
            f"H{index}", "M2.5 mount", (hx + X_OFFSET, Y_OFFSET - hz), "TOP"
        )

    # Planning corridors are documentation graphics, never copper.
    for label, x, z, width, depth, _side in PLANNING_ZONES:
        center = (x + X_OFFSET, Y_OFFSET - z)
        add_rect(board, center, (width, depth), pcbnew.Dwgs_User, 0.2)
        add_text(board, label.replace("_", " "), (center[0], center[1] - depth / 2 + 0.8), pcbnew.Dwgs_User, 0.65)

    placed_parts = []
    for part in ALL_PARTS:
        ref = part["ref"]
        mapping = FOOTPRINTS.get(ref)
        if mapping is None:
            continue
        status = part["status"]
        value = f"{part['part_number']} | {status}"
        place_footprint(board, mapping[0], mapping[1], ref, value, to_board_xy(part), part["side"])
        placed_parts.append(part)

    # U1 uses a 15 mm mechanical BGA proxy only. Its 324 visible pads are not the
    # i.MX95 ball assignment; the production 548-ball vendor footprint is gated.
    add_text(board, "U1 PROXY: 548-BALL MAP REQUIRED", (60.0, 30.5), pcbnew.F_Fab, 0.55)

    added_parts = [
        ("U21", (51.5, 42.0), (2.0, 2.0), "HEAD FACE SWITCH / TBD"),
        ("U22", (78.5, 42.0), (2.0, 2.0), "HEAD INTERACTION SWITCH / TBD"),
    ]
    for ref, xy, size, value in added_parts:
        place_footprint(board, "Package_SON", "WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm", ref, value, xy)
        placed_parts.append(planning_part(ref, xy, size))

    esd_positions = {
        "D3": (39.5, 39.5), "D4": (43.0, 39.5), "D5": (46.5, 39.5),
        "D6": (83.5, 39.5), "D7": (87.0, 39.5), "D8": (90.5, 39.5),
    }
    for ref, xy in esd_positions.items():
        place_footprint(board, "Package_SON", "USON-10_2.5x1.0mm_P0.5mm", ref, "TPD4E05U06 / SI REVIEW", xy)
        placed_parts.append(planning_part(ref, xy, (2.5, 1.0)))

    inductor_positions = {
        "L1": (92.0, 34.0), "L2": (92.0, 38.0), "L3": (86.0, 25.0),
        "L4": (86.0, 30.5), "L5": (93.0, 24.0), "L6": (97.0, 24.0),
        "L7": (101.0, 24.0), "L8": (89.0, 29.0), "L9": (101.0, 29.0),
    }
    for ref, xy in inductor_positions.items():
        place_footprint(board, "Inductor_SMD", "L_Sunlord_SWPA3010S", ref, "TBD POWER INDUCTOR", xy)
        placed_parts.append(planning_part(ref, xy, (3.0, 3.0)))

    # Mechanically representative support population. These are intentionally
    # unconnected until their parent schematic sheets are captured and reviewed.
    c_top = place_passive_field(
        board, placed_parts, "TOP", 96, "C", ("Capacitor_SMD", "C_0201_0603Metric"), "TBD_BY_RAIL"
    )
    c_bottom = place_passive_field(
        board, placed_parts, "BOTTOM", 48, "C", ("Capacitor_SMD", "C_0201_0603Metric"), "TBD_BY_RAIL", 0, 97
    )
    r_bottom = place_passive_field(
        board, placed_parts, "BOTTOM", 44, "R", ("Resistor_SMD", "R_0201_0603Metric"), "TBD_BY_CIRCUIT", 1
    )

    add_text(board, "DEEPREAL MAIN PCBA", (65, 21.4), pcbnew.F_SilkS, 1.0)
    add_text(board, "PRELIMINARY PLACEMENT — NOT FOR FABRICATION", (65, 46.6), pcbnew.F_SilkS, 0.8)
    add_text(board, "UNROUTED: vendor pin maps + FPGA + DDR gates open", (65, 46.6), pcbnew.B_SilkS, 0.75)
    add_text(board, f"Support placeholders: {c_top + c_bottom} C / {r_bottom} R", (65, 22.6), pcbnew.B_SilkS, 0.65)

    pcbnew.SaveBoard(str(OUTPUT), board)
    return len(placed_parts), c_top + c_bottom, r_bottom


if __name__ == "__main__":
    if "--allow-overwrite-canonical-concept" not in sys.argv:
        raise SystemExit(
            "REFUSED: this superseded generator would overwrite the canonical "
            "KiCad board. Pass --allow-overwrite-canonical-concept only when "
            "deliberately restoring the historical placement study."
        )
    major, capacitors, resistors = build_board()
    print(f"Generated {OUTPUT}")
    print(f"Placed {major} major/support packages, {capacitors} capacitor proxies, {resistors} resistor proxies")
