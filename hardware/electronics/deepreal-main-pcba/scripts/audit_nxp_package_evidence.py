#!/usr/bin/env python3
"""Compile a private, net-free NXP package proposal from hash-bound evidence."""

import argparse
import hashlib
import json
import math
from pathlib import Path


SOURCES = {
    "imx95iec-official-cn.pdf": "1d1f5bb8cf06528d7e96ce94ec6a7b045fd691ef863a68ddb45804f29f073e9b",
    "pf53-official-cn.pdf": "4f2f73a1cf2cad9e179317b640f1a1b89f9ce3dbda29e28c784e3a5300d78804",
    "sot2283-1-official-cn.pdf": "1e895e5c3b71ee85ca8f41d0970599ea6885783a0834a439e41b73409b5ee5e2",
}
ROWS = "A B C D E F G H J K L M N P R T U V W Y AA AB AC AD AE AF AG AH AJ".split()
PF_FUNCTIONS = {
    **{str(i): "PGND" for i in (1, 2, 3, 17, 18, 19, 20, 24)},
    **{str(i): "LX" for i in (21, 22, 23)},
    "4": "PVIN", "5": "BOOT", "6": "VIN", "7": "STANDBY/SYNCIN",
    "8": "PGOOD", "9": "PWRON", "10": "AGND", "11": "FB-", "12": "FB+",
    "13": "VDDOTP/XFAILB", "14": "SCL", "15": "SDA", "16": "PVIN",
}
EXPECTED_GROUPS = {
    frozenset(("1", "2", "3", "24")), frozenset(("17", "18", "19", "20")),
    frozenset(("21", "22", "23")),
    *[frozenset((str(i),)) for i in range(4, 17)],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_sources(directory):
    for name, expected in SOURCES.items():
        if digest(directory / name) != expected:
            raise ValueError("changed manufacturer source: " + name)


def ball_map(source):
    import fitz
    import openpyxl
    from io import BytesIO

    document = fitz.open(source)
    filename = "i.mx95_15mm_ballmap.xlsx"
    content = document.embfile_get(filename)
    workbook = openpyxl.load_workbook(BytesIO(content), data_only=True)
    sheet = workbook["i.mx95_15mm_SPN_r0.6"]
    if list(next(sheet.values)) != [
        "REFDES", "PIN_NUMBER", "SYM_NAME", "COMP_DEVICE_TYPE",
        "PAD_STACK_NAME", "PIN_X", "PIN_Y", "NET_NAME",
    ]:
        raise ValueError("unknown manufacturer ball-map columns")
    result = []
    for ref, number, symbol, device, stack, x, y, function in list(sheet.values)[1:]:
        if ref != "BGA" or stack != "FC_BGA_330_280" or not function:
            raise ValueError("unexpected ball-map row")
        row = "".join(c for c in number if c.isalpha())
        column = int("".join(c for c in number if c.isdigit()))
        expected = [(column - 15) * 0.5, (ROWS.index(row) - 14) * 0.5]
        position = [x / 1000, -y / 1000]
        if position != expected:
            raise ValueError("ball coordinates disagree with row/column: " + number)
        result.append({"number": number, "position_mm": position, "function": function})
    if len(result) != 548 or len({r["number"] for r in result}) != 548:
        raise ValueError("548 unique balls required")
    board_map = workbook["Board Map r0.6"]
    positions = {r["number"]: r for r in result}
    counted = 0
    for row in list(board_map.values)[1:]:
        for column, function in enumerate(row[1:], 1):
            number = row[0] + str(column)
            if function is None:
                if number in positions:
                    raise ValueError("ball placed at a manufacturer no-ball location")
            else:
                listed = positions[number]["function"]
                if listed != function:
                    if (number, listed, function) != ("AF22", "VDD_EARC_1P8", "VDD_AUD_1P8"):
                        raise ValueError("unreviewed manufacturer map disagreement: " + number)
                    positions[number].update(
                        coordinate_list_function=listed, board_grid_function=function,
                        function="UNRESOLVED_AF22",
                        function_evidence_status="SOURCE_DISAGREEMENT_DO_NOT_CONNECT")
                counted += 1
    if counted != 548:
        raise ValueError("incomplete independent ball-map comparison")
    return result, content


def pf_positions():
    positions = {}
    for i in range(1, 8):
        positions[str(i)] = [-1.675, -0.078 if i == 4 else (i - 4) * 0.5]
    for i in range(8, 13):
        positions[str(i)] = [(i - 10) * 0.5, 2.175]
    for i in range(13, 20):
        positions[str(i)] = [1.675, -0.078 if i == 16 else (16 - i) * 0.5]
    for i in range(20, 25):
        positions[str(i)] = [(22 - i) * 0.5, -2.175]
    return positions


def inside(point, polygon):
    x, y = point
    odd = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y) and x < \
                (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            odd = not odd
    return odd


def copper_loops(source):
    """Transport the 16 copper contours, not the PDF's mask or dimension lines."""
    import fitz

    drawings = fitz.open(source)[5].get_drawings()
    segments = []
    for drawing in drawings[990:1036]:
        for item in drawing["items"]:
            if item[0] == "l":
                points = [tuple(item[1]), tuple(item[2])]
            elif item[0] == "c":
                a, b, c, d = item[1:]
                points = [tuple(
                    (1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * b[k]
                    + 3 * (1 - t) * t ** 2 * c[k] + t ** 3 * d[k]
                    for k in (0, 1)
                ) for t in (i / 16 for i in range(17))]
            else:
                raise ValueError("unexpected PDF copper primitive")
            segments.append(points)
    loops = []
    while segments:
        points = segments.pop(0)
        while math.dist(points[-1], points[0]) > 0.07:
            matches = []
            for i, segment in enumerate(segments):
                for reverse in (False, True):
                    if math.dist(points[-1], segment[-1 if reverse else 0]) < 0.07:
                        matches.append((i, reverse))
            if len(matches) != 1:
                raise ValueError("ambiguous/open source copper contour")
            i, reverse = matches[0]
            segment = segments.pop(i)
            points.extend((list(reversed(segment)) if reverse else segment)[1:])
        loops.append(points[:-1])
    if len(loops) != 16:
        raise ValueError("expected 16 connected source copper regions")
    # PDF vectors have about 0.00085 mm drafting quantization. Calibrate using
    # the explicitly dimensioned 0.5 mm terminal pitch, independently of pixels.
    scale = (404.053955078125 - 379.27398681640625) / 0.5
    origin = (302.89716, 379.27398681640625 - scale * 0.5)
    polygons = [[[round((x - origin[0]) / scale, 6),
                  round((y - origin[1]) / scale, 6)] for x, y in loop] for loop in loops]
    groups = []
    for polygon in polygons:
        numbers = [n for n, position in pf_positions().items() if inside(position, polygon)]
        if not numbers:
            raise ValueError("unassigned copper contour")
        if len({PF_FUNCTIONS[n] for n in numbers}) != 1:
            raise ValueError("manufacturer contour would short unlike functions")
        groups.append({"numbers": numbers, "polygon_mm": polygon})
    if {frozenset(g["numbers"]) for g in groups} != EXPECTED_GROUPS:
        raise ValueError("unexpected copper connectivity or reflected numbering")
    return groups, {
        "pdf_page": 6, "drawing_indices": [990, 1035], "points_per_pdf_unit_mm": 1 / scale,
        "pdf_origin": list(origin), "endpoint_join_tolerance_pdf_units": 0.07,
        "curve_segments_per_cubic": 16, "connected_copper_regions": len(groups),
        "qualification": "MANUFACTURER_GUIDELINE_VECTOR_TRANSPORT_NOT_PROCESS_APPROVAL",
    }


def fmt(value):
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def header(name, width, length, model):
    return [
        f'(footprint "{name}" (version 20241229) (generator "deepreal-private-evidence")',
        '  (layer "F.Cu") (attr smd)',
        '  (property "Reference" "REF**" (at 0 -3.5) (layer "F.Fab") '
        '(effects (font (size 0.8 0.8) (thickness 0.12))))',
        '  (property "Value" "' + name + '" (at 0 3.5) (layer "F.Fab") '
        '(effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'  (fp_rect (start {-width/2} {-length/2}) (end {width/2} {length/2}) '
        '(stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
        f'  (fp_rect (start {-width/2-0.3} {-length/2-0.3}) '
        f'(end {width/2+0.3} {length/2+0.3}) '
        '(stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
        f'  (model "{model}" (offset (xyz 0 0 0)) '
        '(scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))',
    ]


def vrml_envelope(path, dimensions):
    x, y, z = (v / 2.54 for v in dimensions)
    path.write_text(
        "#VRML V2.0 utf8\n# Conservative manufacturer maximum package envelope, not detailed CAD.\n"
        f"Transform {{ translation 0 0 {z/2} children [ Shape {{ "
        "appearance Appearance { material Material { diffuseColor 0.07 0.08 0.09 } } "
        f"geometry Box {{ size {x} {y} {z} }} }} ] }}\n")


def compile_evidence(sources, output):
    checked_sources(sources)
    balls, workbook = ball_map(sources / "imx95iec-official-cn.pdf")
    groups, vector_basis = copper_loops(sources / "sot2283-1-official-cn.pdf")
    output.mkdir(parents=True, exist_ok=False)
    library = output / "DeepReal_Evidence.pretty"
    library.mkdir()
    models = output / "models"
    models.mkdir()
    envelopes = {
        "NXP_IMX95_SOT2251-1": [15, 15, 1.584],
        "NXP_PF53B_SOT2283-1": [3.6, 4.6, 0.8],
    }
    for name, dimensions in envelopes.items():
        vrml_envelope(models / (name + "_MAX_ENVELOPE.wrl"), dimensions)
    name = "NXP_IMX95_SOT2251-1"
    text = header(name, 15, 15, models / (name + "_MAX_ENVELOPE.wrl"))
    for ball in balls:
        x, y = ball["position_mm"]
        text.append(
            f'  (pad "{ball["number"]}" smd circle (at {x} {y}) (size 0.28 0.28) '
            '(layers "F.Cu" "F.Mask") (solder_mask_margin 0.025) '
            f'(pinfunction "{ball["function"]}") (pintype "passive"))')
    (library / (name + ".kicad_mod")).write_text("\n".join(text + [")", ""]))
    name = "NXP_PF53B_SOT2283-1"
    text = header(name, 3.6, 4.6, models / (name + "_MAX_ENVELOPE.wrl"))
    positions = pf_positions()
    for group in groups:
        for index, number in enumerate(group["numbers"]):
            x, y = positions[number]
            if index == 0:
                pts = " ".join(f"(xy {fmt(a-x)} {fmt(b-y)})" for a, b in group["polygon_mm"])
                text.append(
                    f'  (pad "{number}" smd custom (at {x} {y}) (size 0.02 0.02) '
                    '(layers "F.Cu" "F.Mask") (solder_mask_margin 0.05) '
                    f'(pinfunction "{PF_FUNCTIONS[number]}") (pintype "passive") '
                    '(options (clearance outline) (anchor circle)) '
                    f'(primitives (gr_poly (pts {pts}) (width 0) (fill yes))))')
            else:
                text.append(
                    f'  (pad "{number}" smd circle (at {x} {y}) (size 0.02 0.02) '
                    '(layers "F.Cu" "F.Mask") '
                    f'(pinfunction "{PF_FUNCTIONS[number]}") (pintype "passive"))')
    (library / (name + ".kicad_mod")).write_text("\n".join(text + [")", ""]))
    (output / "imx95-15mm-embedded-ballmap.xlsx").write_bytes(workbook)
    report = {
        "schema": "deepreal.nxp-package-evidence.v1",
        "compiler_sha256": digest(Path(__file__)),
        "artifacts_sha256": {
            str(path.relative_to(output)): digest(path)
            for path in sorted(output.rglob("*")) if path.is_file()
        },
        "sources": SOURCES,
        "U1": {
            "selected_part": "MIMX9596CVTXNAC", "package": "SOT2251-1",
            "drawing": "98ASA02029D revision A, 06 March 2024; IMX95IEC Rev 8 page 115",
            "body_nominal_mm": [15, 15, 1.414], "height_max_mm": 1.584,
            "ball_count": 548, "pitch_mm": 0.5, "balls": balls,
            "embedded_map_sha256": hashlib.sha256(workbook).hexdigest(),
            "independent_board_map_cells_checked": 548,
            "independent_function_matches": 547,
            "function_conflicts": {
                "AF22": {
                    "coordinate_list": "VDD_EARC_1P8", "board_grid": "VDD_AUD_1P8",
                    "resolution": "UNRESOLVED; pad function explicitly marked, no net assigned",
                },
            },
            "land_proposal": {
                "copper_diameter_mm": 0.28, "mask_diameter_mm": 0.33,
                "basis": "Interpretation of embedded PAD_STACK_NAME FC_BGA_330_280, NOT a verified land-dimension definition",
                "vendor_land_definition_verified": False,
            },
            "rejected_package": "SOT2021-1: different 98ASA01401D drawing and 1.94 mm body; NOT the selected processor package",
            "stepping_and_pinmux_application_review_complete": False,
        },
        "U6_U7": {
            "selected_parts": ["MPF5302BVNAAEP", "MPF5301BVNABEP"],
            "package": "SOT2283-1",
            "drawing": "98ASA02280D revision O, 22 July 2025",
            "ordering_basis": "PF53 Rev 7 pages 4-5: industrial B suffix -> SOT2283-1, NOT SOT2090-1",
            "datasheet_caption_discrepancy": "PF53 page 156 figure 69 caption says SOT2090-1; title block and ordering table say SOT2283-1",
            "body_nominal_mm": [3.5, 4.5, 0.75], "body_max_mm": [3.6, 4.6, 0.8],
            "functions": PF_FUNCTIONS, "positions_mm": positions,
            "copper_groups": groups, "copper_vector_basis": vector_basis,
            "mask_proposal": "Provisional isotropic 0.05 mm opening, NOT the separately dimensioned vendor mask pattern",
            "mask_pattern_verified": False,
            "sequence_and_power_circuit_review_complete": False,
        },
        "common_limits": [
            "No F.Paste apertures generated. Vendor stencil and assembly-process design are still required.",
            "No external nets, circuits or routing generated. Only manufacturer-defined local PGND/LX aliases may be assigned by the board builder.",
            "3D bodies are conservative maximum bounding envelopes, NOT detailed manufacturer models.",
            "PGND and LX alias pads share source copper intentionally; local alias nets do not define a system circuit.",
            "These are private footprint proposals, not production libraries.",
        ],
        "fabrication_allowed": False, "public_visual_allowed": False,
        "viewer_integration_allowed": False,
    }
    (output / "nxp-package-evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print("NXP PACKAGE PROPOSAL: 548 independently checked U1 balls; 24 PF53 pins, 16 copper regions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.sources.is_absolute() or not args.output.is_absolute():
        parser.error("absolute paths required")
    compile_evidence(args.sources, args.output)
