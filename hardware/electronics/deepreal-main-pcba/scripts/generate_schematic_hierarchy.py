#!/usr/bin/env python3
"""Generate the reviewable 15-page KiCad schematic hierarchy.

The generated pages are capture contracts, not finished circuits. They make the
scope and closure gates visible in KiCad without inventing vendor-controlled
BGA pin maps or claiming that unchecked nets are complete.
"""

import csv
from pathlib import Path
import re
import uuid


HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
PLAN = PROJECT_DIR / "sheet-plan.csv"
ROOT = PROJECT_DIR / "deepreal-main-pcba.kicad_sch"
PROJECT_NAME = "deepreal-main-pcba"
ROOT_UUID = "a5af7141-8753-4fd5-bf7c-a862c424a54e"
UUID_NAMESPACE = uuid.UUID("7dfd8c53-9e25-462c-a24a-64f2379a3215")


def uid(name):
    return str(uuid.uuid5(UUID_NAMESPACE, name))


def quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def slug(page, name):
    value = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{int(page):02d}_{value}.kicad_sch"


def text_item(text, x, y, size, item_uuid):
    return f'''\t(text {quote(text)}
\t\t(exclude_from_sim no)
\t\t(at {x} {y} 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size {size} {size})
\t\t\t)
\t\t\t(justify left bottom)
\t\t)
\t\t(uuid {quote(item_uuid)})
\t)'''


def child_sheet(row, filename):
    page = int(row["Page"])
    state = row["State"]
    warning = (
        "PIN-LEVEL CAPTURE BLOCKED — import and audit official package data"
        if "GATE" in state else
        "ARCHITECTURE DEFINED — component values and pin-level review still required"
    )
    sheet_uuid = uid(f"child-{page}-{row['Sheet_name']}")
    texts = [
        text_item(row["Sheet_name"].replace("_", " "), 25.4, 30.0, 2.5, uid(f"title-{page}")),
        text_item(f"STATUS: {state}", 25.4, 40.0, 1.5, uid(f"status-{page}")),
        text_item(f"PRIMARY REFERENCES: {row['Primary_refs']}", 25.4, 48.0, 1.27, uid(f"refs-{page}")),
        text_item(f"CLOSURE EVIDENCE: {row['Closure_evidence']}", 25.4, 58.0, 1.27, uid(f"closure-{page}")),
        text_item(warning, 25.4, 75.0, 1.27, uid(f"warning-{page}")),
        text_item(
            "See circuit-specification.md, net-registry.csv, component-register.csv and pinmap-gates.csv.\n"
            "Do not add copper or release fabrication data until this page is electrically captured and reviewed.",
            25.4, 95.0, 1.27, uid(f"sources-{page}"),
        ),
    ]
    return f'''(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid {quote(sheet_uuid)})
\t(paper "A4")
\t(title_block
\t\t(title {quote(row['Sheet_name'].replace('_', ' '))})
\t\t(rev "0.2-capture")
\t\t(company "DeepReal")
\t\t(comment 1 {quote(f"Page {page}/15 — {state}")})
\t\t(comment 2 "PRELIMINARY / NOT FOR FABRICATION")
\t)
\t(lib_symbols)
{chr(10).join(texts)}
\t(embedded_fonts no)
)\n'''


def sheet_block(row, index, filename):
    col = index % 3
    grid_row = index // 3
    x = 20.0 + col * 90.0
    y = 35.0 + grid_row * 35.0
    width = 72.0
    height = 20.0
    sheet_uuid = uid(f"root-sheet-{row['Page']}-{row['Sheet_name']}")
    return f'''\t(sheet
\t\t(at {x} {y})
\t\t(size {width} {height})
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(stroke (width 0.1524) (type solid))
\t\t(fill (color 0 0 0 0))
\t\t(uuid {quote(sheet_uuid)})
\t\t(property "Sheetname" {quote(row['Sheet_name'])}
\t\t\t(at {x} {y - 0.7116} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t)
\t\t(property "Sheetfile" {quote(filename)}
\t\t\t(at {x} {y + height + 0.5846} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects (font (size 1.27 1.27)) (justify left top))
\t\t)
\t\t(instances
\t\t\t(project {quote(PROJECT_NAME)}
\t\t\t\t(path {quote('/' + ROOT_UUID)} (page {quote(row['Page'])}))
\t\t\t)
\t\t)
\t)'''


def root_sheet(rows):
    children = rows[1:]
    blocks = [sheet_block(row, index, slug(row["Page"], row["Sheet_name"])) for index, row in enumerate(children)]
    notes = [
        text_item("DEEPREAL MAIN PCBA — ELECTRICAL CAPTURE MAP", 20.0, 18.0, 2.0, uid("root-title")),
        text_item(
            "15 pages total. This hierarchy defines what must be captured; it is not an ERC-clean production schematic.\n"
            "Red gates: i.MX95 / LPDDR4X / eMMC vendor pin maps, Lattice compile, flex orientation and power calculations.",
            20.0, 26.0, 1.1, uid("root-warning"),
        ),
    ]
    return f'''(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid {quote(ROOT_UUID)})
\t(paper "A3")
\t(title_block
\t\t(title "DeepReal Main PCBA — Cover and Constraints")
\t\t(rev "0.2-capture")
\t\t(company "DeepReal")
\t\t(comment 1 "90 x 28 mm / 10-layer HDI working assumption")
\t\t(comment 2 "PRELIMINARY / NOT FOR FABRICATION")
\t)
\t(lib_symbols)
{chr(10).join(notes)}
{chr(10).join(blocks)}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
\t(embedded_fonts no)
)\n'''


def main():
    with PLAN.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 15 or rows[0]["Page"] != "1":
        raise RuntimeError("sheet-plan.csv must contain pages 1 through 15")
    ROOT.write_text(root_sheet(rows))
    for row in rows[1:]:
        filename = slug(row["Page"], row["Sheet_name"])
        (PROJECT_DIR / filename).write_text(child_sheet(row, filename))
    print(f"Generated root plus {len(rows) - 1} child sheets in {PROJECT_DIR}")


if __name__ == "__main__":
    main()
