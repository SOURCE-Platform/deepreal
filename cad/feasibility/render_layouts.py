"""Render schematic SVG cross-sections of the Gate 1.5B layouts.

Reads the built drum_internals.FCStd (single source of truth for placed
geometry) and writes one SVG per layout into cad/feasibility/assets/
renders/:
  * side view:  X (drum axis) horizontal vs radial distance from axis
  * cross view: Y-Z cross-section at the layout's densest station
Pure stdlib SVG writing; run under freecadcmd for FreeCAD access.
"""

import math
import os
import sys

import FreeCAD as App

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import registry  # noqa: E402

DOC_PATH = os.path.join(HERE, "drum_internals.FCStd")
OUT_DIR = os.path.join(HERE, "assets", "renders")

AXIS_Y = registry.DRUM_AXIS_Y
AXIS_Z = registry.DRUM_AXIS_Z
R_INT = registry.ASSUMED_INNER_DIAMETER / 2.0
R_SHELL = registry.DRUM_SHELL_DIAMETER / 2.0
X_LO = registry.FACE_INTERIOR_X_MIN
X_HI = registry.FACE_INTERIOR_X_MAX

COLORS = {
    "rpi_cm3_sensor_assembly": "#4a90d9",
    "ov9281_ir_camera": "#50b06c",
    "ams_belice_850": "#d9853b",
    "ams_belago1_2": "#c9534f",
    "infineon_irs2877a": "#8b6cc1",
    "tof_illuminator_placeholder": "#b0a050",
    "keepout": "#999999",
    "aperture": "#ff2222",
}


class SVG:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, opacity=0.55, stroke="#222",
             dash=None):
        d = ' stroke-dasharray="4 3"' if dash else ""
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="%s" fill-opacity="%.2f" stroke="%s" '
                 'stroke-width="1"%s/>' % (x, y, w, h, fill, opacity,
                                           stroke, d))

    def circle(self, cx, cy, r, fill="none", stroke="#222", sw=1.2,
               dash=None, opacity=1.0):
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.add('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" '
                 'stroke="%s" stroke-width="%.1f"%s opacity="%.2f"/>'
                 % (cx, cy, r, fill, stroke, sw, d, opacity))

    def line(self, x1, y1, x2, y2, stroke="#888", sw=0.8, dash=True):
        d = ' stroke-dasharray="3 3"' if dash else ""
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="%s" stroke-width="%.1f"%s/>'
                 % (x1, y1, x2, y2, stroke, sw, d))

    def text(self, x, y, s, size=11, fill="#111", anchor="start",
             bold=False):
        b = ' font-weight="bold"' if bold else ""
        self.add('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" '
                 'text-anchor="%s" font-family="Menlo, monospace"%s>%s'
                 '</text>' % (x, y, size, fill, anchor, b, s))

    def save(self, path):
        with open(path, "w") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" '
                    'height="%d" viewBox="0 0 %d %d">\n'
                    % (self.w, self.h, self.w, self.h))
            f.write('<rect width="100%" height="100%" fill="#fafafa"/>\n')
            f.write("\n".join(self.parts))
            f.write("\n</svg>\n")
        print("WROTE %s" % path, flush=True)


def collect(doc, ltag):
    parts, keepouts, markers = [], [], []
    for o in doc.Objects:
        if o.Name.startswith("LA_%s_" % ltag):
            parts.append(o)
        elif o.Name.startswith("KO_%s_" % ltag):
            keepouts.append(o)
        elif o.Name.startswith("AP_%s_" % ltag):
            markers.append(o)
    return parts, keepouts, markers


def color_of(obj):
    if obj.Name.startswith("KO_"):
        return COLORS["keepout"]
    if obj.Name.startswith("AP_"):
        return COLORS["aperture"]
    return COLORS.get(getattr(obj, "Component", ""), "#666666")


def render_side(lname, parts, keepouts, markers, metrics):
    """X (horizontal) vs radial distance from drum axis (vertical)."""
    s = SVG(1180, 420)
    sc = 16.0                       # px per mm
    ox, oy = 60.0, 330.0            # px origin: x=X_LO, radial 0
    # drum wall + interior lines
    s.rect(ox, oy - R_SHELL * sc, (X_HI - X_LO) * sc, R_SHELL * sc,
           "#dddddd", 0.25, "#999", dash=True)
    s.line(ox, oy - R_INT * sc, ox + (X_HI - X_LO) * sc, oy - R_INT * sc,
           "#666", 1.2)
    s.line(ox, oy, ox + (X_HI - X_LO) * sc, oy, "#333", 1.4, dash=False)
    s.text(ox + (X_HI - X_LO) * sc + 6, oy - R_INT * sc + 4,
           "assumed interior r=10.5", 10, "#555")
    s.text(ox + (X_HI - X_LO) * sc + 6, oy - R_SHELL * sc + 4,
           "shell r=12.0", 10, "#555")
    s.text(ox + (X_HI - X_LO) * sc + 6, oy + 4, "drum axis (X)", 10,
           "#333")
    for o in parts + keepouts + markers:
        bb = o.Shape.BoundBox
        rmax = max(abs(bb.YMin - AXIS_Y), abs(bb.YMax - AXIS_Y))
        rmin = min(abs(bb.YMin - AXIS_Y), abs(bb.YMax - AXIS_Y))
        # AP markers are thin: give them a fixed visual thickness.
        if o.Name.startswith("AP_"):
            rmin, rmax = R_INT - 0.4, R_INT
        x = ox + (bb.XMin - X_LO) * sc
        w = (bb.XMax - bb.XMin) * sc
        y = oy - rmax * sc
        h = max(2.0, (rmax - rmin) * sc)
        s.rect(x, y, w, h, color_of(o), 0.35 if o.Name[:2] == "KO"
               else 0.65, dash=o.Name[:2] == "KO")
        s.text(x + 1, y - 3, o.Name.split("_", 2)[2][:34], 9, "#222")
    s.text(ox, 30, "%s — side view (X span used %.1f mm of 51; "
           "remaining %.1f mm; min radial clearance %.2f mm)"
           % (lname, metrics["x_span_mm"], metrics["x_remaining_mm"],
              metrics["min_radial_clearance_mm"]), 15, "#111", bold=True)
    s.text(ox, 50, "radial distance from drum axis upward; window side "
           "(user-facing -Y) at top", 10, "#555")
    return s


def render_cross(lname, parts, keepouts, markers):
    """Y-Z cross-section; drum axis at centre."""
    s = SVG(560, 520)
    sc = 16.0
    cx, cy = 280.0, 250.0
    s.circle(cx, cy, R_SHELL * sc, stroke="#999", dash=True)
    s.circle(cx, cy, R_INT * sc, stroke="#666", sw=1.4)
    s.line(cx - R_SHELL * sc - 10, cy, cx + R_SHELL * sc + 10, cy)
    s.line(cx, cy - R_SHELL * sc - 10, cx, cy + R_SHELL * sc + 10)
    s.text(cx, cy - R_INT * sc - 8, "user-facing (-Y), rest position",
           10, "#555", anchor="middle")
    s.text(cx + 4, cy - 4, "axis", 9, "#333")
    for o in parts + keepouts + markers:
        bb = o.Shape.BoundBox
        # project: horizontal = Z (tangential), vertical = Y (radial);
        # screen Y grows downward, -Y (user-facing) is up.
        x = cx + (bb.ZMin - AXIS_Z) * sc
        w = (bb.ZMax - bb.ZMin) * sc
        y = cy + (bb.YMin - AXIS_Y) * sc
        h = (bb.YMax - bb.YMin) * sc
        s.rect(x, y, w, h, color_of(o),
               0.30 if o.Name[:2] == "KO" else 0.60,
               dash=o.Name[:2] == "KO")
        s.text(x, y - 3, o.Name.split("_", 2)[2][:26], 8, "#222")
    s.text(30, 30, "%s — Y-Z cross-section (max-projection of all "
           "stations)" % lname, 15, "#111", bold=True)
    s.text(30, 48, "circles: assumed interior dia 21 / shell dia 24",
           10, "#555")
    return s


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    doc = App.openDocument(DOC_PATH)
    # recompute metrics here (same math as the validator)
    import layouts  # noqa: E402
    for lname in layouts.LAYOUTS:
        ltag = lname.replace("-", "")
        parts, keepouts, markers = collect(doc, ltag)
        objs = parts + keepouts
        x_min = min(o.Shape.BoundBox.XMin for o in objs)
        x_max = max(o.Shape.BoundBox.XMax for o in objs)
        worst = 0.0
        for o in objs:
            bb = o.Shape.BoundBox
            for y in (bb.YMin, bb.YMax):
                for z in (bb.ZMin, bb.ZMax):
                    worst = max(worst, math.hypot(y - AXIS_Y,
                                                  z - AXIS_Z))
        metrics = {
            "x_span_mm": x_max - x_min,
            "x_remaining_mm": registry.ASSUMED_INNER_LENGTH - (x_max - x_min),
            "min_radial_clearance_mm": R_INT - worst,
        }
        tag = lname.replace("-", "")
        render_side(lname, parts, keepouts, markers, metrics).save(
            os.path.join(OUT_DIR, "layout_%s_side.svg" % tag))
        render_cross(lname, parts, keepouts, markers).save(
            os.path.join(OUT_DIR, "layout_%s_cross.svg" % tag))
    print("RENDER-OK", flush=True)


main()
