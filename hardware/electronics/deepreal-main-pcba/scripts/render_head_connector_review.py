#!/usr/bin/env python3
"""Plot actual KiCad courtyards and explicitly unapproved rotation trials.

This diagnostic figure is not a PCB render or an alternative placement authority.
Requires Pillow; no CAD source is modified.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "generated-review"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", default="/System/Library/Fonts/Supplemental/Arial.ttf")
    args = parser.parse_args()
    layout = json.loads((PROJECT/"engineering-layout-export.json").read_text())
    report = json.loads((OUT/"head-interface-audit.json").read_text())
    for name, key in (("head-interface-evidence.json", "source_evidence_sha256"),
                      ("connector-allocation.csv", "source_allocation_sha256")):
        if hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() != report[key]:
            raise RuntimeError("Stale interface evidence: "+name)
    source_hash = hashlib.sha256((PROJECT/"deepreal-main-pcba.kicad_pcb").read_bytes()).hexdigest()
    if source_hash != report["source_board_sha256"] or source_hash != layout["metadata"]["source_board_sha256"]:
        raise RuntimeError("Stale review: regenerate the export and interface audit")
    image = Image.new("RGB", (1680, 1390), "#f5f7fa")
    draw = ImageDraw.Draw(image)
    fonts = {size: ImageFont.truetype(args.font, size) for size in (18, 21, 24, 30, 42)}

    def text(x, y, value, size=24, color="#172334"):
        draw.text((x, y), value, font=fonts[size], fill=color)

    text(70, 35, "Two drum connectors: why a quarter-turn is not enough", 42)
    text(70, 95, "Internal engineering diagnosis | Main board unchanged | NOT FOR PUBLICATION", 24)
    text(70, 138, "Shapes are component courtyards (assembly-clearance outlines), not chip bodies or copper.", 21)
    edge = layout["board"]["bounds_mm"]
    scale = 15.6
    red, amber, muted = "#b62b37", "#876000", "#83929f"

    def panel(top, title, subtitle, trials):
        text(70, top, title, 30)
        text(70, top+43, subtitle, 21)
        origin = [135, top+87]

        def xy(p):
            return (origin[0]+(p[0]-edge[0])*scale,
                    origin[1]+(p[1]-32)*scale)

        # Lower portion only; the shared crop does not imply a new board outline.
        draw.rectangle([xy([edge[0], 32]), xy([edge[2], edge[3]])],
                       fill="#e4efea", outline="#355746", width=3)
        moved = {r["ref"]: r for r in trials}
        highlighted = {"J2", "J3", "U2", "U3", "U21", "U22"}
        for component in layout["components"]:
            if component["side"] != "TOP":
                continue
            ref = component["ref"]
            polygons = moved.get(ref, component)["courtyard_polygons_mm"]
            for polygon in polygons:
                if max(p[1] for p in polygon) < 32:
                    continue
                # Clip the figure at Y=32 for this rectangle-courtyard review.
                # This is a view crop only; screening used complete polygons.
                points = [xy([x, max(32, y)]) for x, y in polygon]
                color = red if ref in moved else amber if ref in highlighted else muted
                draw.line(points+[points[0]], fill=color, width=4 if ref in moved else 2)
                if ref in highlighted:
                    x = sum(p[0] for p in points)/len(points)
                    y = sum(p[1] for p in points)/len(points)
                    box = draw.textbbox((0, 0), ref, font=fonts[21])
                    draw.rectangle((x-(box[2]+10)/2, y-13, x+(box[2]+10)/2, y+14), fill="#f5f7fa")
                    text(x-box[2]/2, y-12, ref, 21, color)
        for x in range(20, 111, 10):
            px, py = xy([x, 56])
            draw.line((px, py-5, px, py), fill=muted, width=2)
            text(px-12, py+8, str(x), 18)
        text(1390, top+500, "X (KiCad mm)", 18)
        for y in (32, 40, 48, 56):
            px, py = xy([20, y])
            text(px-43, py-11, str(y), 18)
        text(74, top+280, "Y mm", 18)
        text(140, top+354, "Board edge at Y = 48 mm", 18, "#355746")

    panel(192, "CURRENT  |  J2 and J3 at 0 degrees",
          "Both clearance outlines overhang the lower edge by 6.895 mm; other overlap candidates also exist.",
          report["current_placements"])
    trials = [r for r in report["quarter_turn_trials_not_applied"] if r["rotation_deg"] == 90]
    panel(755, "TRIAL ONLY  |  Rotate 90 degrees and shift inward 1 mm",
          "Edge overhang disappears, but both connectors still overlap neighboring clearance outlines.", trials)
    text(70, 1325, "Red: drum connectors   |   Amber: camera FPGA / head power parts   |   Gray: other top-side courtyards", 21)
    image.save(OUT/"head-connector-review.png")
    print(OUT/"head-connector-review.png")


if __name__ == "__main__":
    main()
