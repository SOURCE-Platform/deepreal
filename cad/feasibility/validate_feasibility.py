"""Validation for cad/feasibility/drum_internals.FCStd.

Gate 1 checks:
  1. every registry component has an ENV_* object whose bounding box
     matches the published registry dimensions (tol 0.05 mm; multi-part
     components compare against the union of their registry parts)
  2. drum context geometry matches the approved model positions
  3. all visibility groups exist
  4. the exterior reference matches the approved Main_Housing bounds
  5. cad/deepreal.FCStd is untouched: its SHA1 equals the main-branch
     blob (git show main:cad/deepreal.FCStd)

Gate 1.5B checks (in-drum layouts SL-A / SL-B / ToF-A):
  6. every LA_* part bounding box matches its registry part dims
  7. per-layout pairwise collision: common() volume ~ 0 for all LA_/KO_
     pairs (AP_* markers live in the wall and are excluded)
  8. containment: every LA_/KO_ part lies fully inside the assumed
     interior (dia 21, X -54.5..-3.5) of the UNCHANGED face drum
  9. both RGB results: the full CM3 board has NO axis-aligned
     orientation inside dia 21 (expected no-fit), while the CM3 Sensor
     Assembly fits (min enclosing circle reported)
 10. per-layout X span used / remaining and minimum radial clearance are
     computed and printed for the report

Run headless:
    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console \\
        cad/feasibility/validate_feasibility.py
"""

import hashlib
import math
import os
import subprocess
import sys

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelopes
import layouts
import registry
from groups import GROUP_DEFS

DOC_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "drum_internals.FCStd"))
APPROVED = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "deepreal.FCStd"))

TOL = 0.05
COLLISION_TOL_MM3 = 1e-3
_failures = []
_layout_metrics = {}


def check(ok, label, detail=""):
    print("%s %s%s" % ("PASS" if ok else "FAIL", label,
                       (" | " + detail) if detail else ""), flush=True)
    if not ok:
        _failures.append(label)


def dims_of(obj):
    bb = obj.Shape.BoundBox
    return sorted([bb.XLength, bb.YLength, bb.ZLength])


# ---------------------------------------------------------------- Gate 1
def check_envelopes(doc):
    for key, entry in registry.COMPONENTS.items():
        obj = doc.getObject("ENV_" + key)
        if obj is None:
            check(False, "envelope %s" % key, "object missing")
            continue
        got = dims_of(obj)
        want = envelopes.expected_union_dims(key)
        ok = all(abs(g - w) <= TOL for g, w in zip(got, want))
        check(ok, "envelope %s dims" % key,
              "got %s want %s" % (["%.2f" % v for v in got],
                                  ["%.2f" % v for v in want]))


def check_drum_context(doc):
    r = registry.DRUM_SHELL_DIAMETER / 2.0
    cases = [
        ("Ctx_Face_Drum_Shell", registry.DRUM_FACE_X_MIN,
         registry.DRUM_FACE_X_MAX),
        ("Ctx_Interaction_Drum_Shell", registry.DRUM_INTERACTION_X_MIN,
         registry.DRUM_INTERACTION_X_MAX),
    ]
    for name, x_min, x_max in cases:
        obj = doc.getObject(name)
        if obj is None:
            check(False, "drum %s" % name, "object missing")
            continue
        bb = obj.Shape.BoundBox
        ok = (abs(bb.XMin - x_min) <= TOL and abs(bb.XMax - x_max) <= TOL
              and abs(bb.YMin - (registry.DRUM_AXIS_Y - r)) <= TOL
              and abs(bb.YMax - (registry.DRUM_AXIS_Y + r)) <= TOL
              and abs(bb.ZMin - (registry.DRUM_AXIS_Z - r)) <= TOL
              and abs(bb.ZMax - (registry.DRUM_AXIS_Z + r)) <= TOL)
        check(ok, "drum %s bounds" % name,
              "X %.2f..%.2f Y %.2f..%.2f Z %.2f..%.2f"
              % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    interior = doc.getObject("Ctx_Face_Interior_Assumed")
    if interior is None:
        check(False, "assumed interior", "object missing")
    else:
        bb = interior.Shape.BoundBox
        ri = registry.ASSUMED_INNER_DIAMETER / 2.0
        ok = (abs(bb.YLength - 2 * ri) <= TOL
              and abs(bb.XLength - registry.ASSUMED_INNER_LENGTH) <= TOL)
        check(ok, "assumed interior dims",
              "dia %.2f len %.2f" % (bb.YLength, bb.XLength))
    n_ctx = len([o for o in doc.Objects if o.Name.startswith("Ctx_")])
    check(n_ctx == 8, "drum context object count",
          "got %d, want 8 (2 shells + 2 interiors + 4 travel plates)"
          % n_ctx)
    # Travel plates rotate about the drum axis with radial reach equal to
    # the shell radius; their bounds must stay within axis +/- (radius +
    # plate half-thickness 0.25) in Y and Z.
    r = registry.DRUM_SHELL_DIAMETER / 2.0 + 0.25
    n_plates = 0
    for obj in doc.Objects:
        if not obj.Name.startswith("Ctx_") or "_Travel_" not in obj.Name:
            continue
        n_plates += 1
        bb = obj.Shape.BoundBox
        ok = (bb.YMin >= registry.DRUM_AXIS_Y - r - TOL
              and bb.YMax <= registry.DRUM_AXIS_Y + r + TOL
              and bb.ZMin >= registry.DRUM_AXIS_Z - r - TOL
              and bb.ZMax <= registry.DRUM_AXIS_Z + r + TOL)
        check(ok, "travel plate %s within drum region" % obj.Name,
              "Y %.2f..%.2f Z %.2f..%.2f"
              % (bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    check(n_plates == 4, "travel plate count", "got %d, want 4" % n_plates)


def check_groups(doc):
    for name, _desc in GROUP_DEFS:
        check(doc.getObject(name) is not None, "group %s" % name)


def check_exterior(doc):
    obj = doc.getObject("EXT_Main_Housing")
    if obj is None:
        check(False, "exterior reference", "EXT_Main_Housing missing")
        return
    bb = obj.Shape.BoundBox
    want = (-60.0, 60.0, -1.5, 22.5, -14.0, 35.0)
    got = (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)
    ok = all(abs(g - w) <= TOL for g, w in zip(got, want))
    check(ok, "exterior reference bounds",
          "X %.1f..%.1f Y %.1f..%.1f Z %.1f..%.1f"
          % (got[0], got[1], got[2], got[3], got[4], got[5]))


def check_approved_untouched():
    disk = hashlib.sha1(open(APPROVED, "rb").read()).hexdigest()
    blob = subprocess.run(
        ["git", "show", "main:cad/deepreal.FCStd"],
        capture_output=True,
        cwd=os.path.dirname(os.path.dirname(APPROVED)))
    committed = hashlib.sha1(blob.stdout).hexdigest()
    check(blob.returncode == 0 and disk == committed,
          "cad/deepreal.FCStd untouched",
          "disk %s vs main %s" % (disk[:12], committed[:12]))


# ------------------------------------------------------------ Gate 1.5B
def _max_corner_radius(bb):
    """Max radial distance from the drum axis over the 4 YZ BB corners."""
    r = 0.0
    for y in (bb.YMin, bb.YMax):
        for z in (bb.ZMin, bb.ZMax):
            r = max(r, math.hypot(y - registry.DRUM_AXIS_Y,
                                  z - registry.DRUM_AXIS_Z))
    return r


def check_layouts(doc):
    r_int = registry.ASSUMED_INNER_DIAMETER / 2.0
    x_lo = registry.FACE_INTERIOR_X_MIN
    x_hi = registry.FACE_INTERIOR_X_MAX
    for lname, ldef in layouts.LAYOUTS.items():
        ltag = lname.replace("-", "")
        parts = [o for o in doc.Objects
                 if o.Name.startswith("LA_%s_" % ltag)
                 or o.Name.startswith("KO_%s_" % ltag)]
        markers = [o for o in doc.Objects
                   if o.Name.startswith("AP_%s_" % ltag)]
        if not parts:
            check(False, "layout %s parts" % lname, "no objects found")
            continue

        # (6) dims vs registry -----------------------------------------
        for obj in parts:
            if obj.Name.startswith("KO_"):
                continue   # keep-outs are labelled assumptions
            ckey = obj.Component
            pname = obj.PartName
            entry = registry.COMPONENTS[ckey]
            if entry["shape"] == "multipart":
                reg = [p for p in entry["parts"] if p["name"] == pname]
            else:
                reg = [{"shape": entry["shape"],
                        "dims_mm": entry["dims_mm"]}]
            if not reg:
                check(False, "layout %s part %s" % (lname, obj.Name),
                      "not in registry")
                continue
            dims = reg[0]["dims_mm"]
            if reg[0]["shape"] == "cylinder":
                want = sorted([dims[0], dims[0], dims[1]])
            else:
                want = sorted(dims)
            got = dims_of(obj)
            ok = all(abs(g - w) <= TOL for g, w in zip(got, want))
            check(ok, "layout %s part %s dims" % (lname, obj.Name),
                  "got %s want %s" % (["%.2f" % v for v in got],
                                      ["%.2f" % v for v in want]))

        # (7) pairwise collisions --------------------------------------
        n_coll = 0
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                common = parts[i].Shape.common(parts[j].Shape)
                if common.Volume > COLLISION_TOL_MM3:
                    n_coll += 1
                    check(False, "layout %s collision" % lname,
                          "%s vs %s: %.4f mm^3"
                          % (parts[i].Name, parts[j].Name, common.Volume))
        if n_coll == 0:
            check(True, "layout %s collision-free" % lname,
                  "%d parts checked pairwise" % len(parts))

        # (8) containment ----------------------------------------------
        worst_r = 0.0
        all_in = True
        for obj in parts:
            bb = obj.Shape.BoundBox
            r = _max_corner_radius(bb)
            worst_r = max(worst_r, r)
            ok = (r <= r_int + TOL
                  and bb.XMin >= x_lo - TOL and bb.XMax <= x_hi + TOL)
            if not ok:
                all_in = False
                check(False, "layout %s containment" % lname,
                      "%s corner radius %.2f (limit %.2f), X %.2f..%.2f"
                      % (obj.Name, r, r_int, bb.XMin, bb.XMax))
        if all_in:
            check(True, "layout %s contained in dia %.1f interior"
                  % (lname, 2 * r_int),
                  "worst corner radius %.2f mm" % worst_r)
        for mk in markers:
            bb = mk.Shape.BoundBox
            ok = (bb.XMin >= x_lo - TOL and bb.XMax <= x_hi + TOL
                  and _max_corner_radius(bb) <= r_int + TOL)
            check(ok, "layout %s aperture %s at wall" % (lname, mk.Name),
                  "X %.2f..%.2f" % (bb.XMin, bb.XMax))

        # (10) metrics for the report ----------------------------------
        x_min = min(o.Shape.BoundBox.XMin for o in parts)
        x_max = max(o.Shape.BoundBox.XMax for o in parts)
        span = x_max - x_min
        remaining = registry.ASSUMED_INNER_LENGTH - span
        clearance = r_int - worst_r
        _layout_metrics[lname] = {
            "x_span_mm": span, "x_min": x_min, "x_max": x_max,
            "x_remaining_mm": remaining,
            "worst_corner_radius_mm": worst_r,
            "min_radial_clearance_mm": clearance,
            "n_parts": len(parts), "n_markers": len(markers),
        }
        print("METRIC %s | X span %.1f mm (%.1f..%.1f), remaining %.1f "
              "mm of %.0f | worst corner r=%.2f | min radial clearance "
              "%.2f mm" % (lname, span, x_min, x_max, remaining,
                           registry.ASSUMED_INNER_LENGTH, worst_r,
                           clearance), flush=True)


def _min_cross_section_radius(dims):
    """Min over axis choices of the centred cross-section half-diagonal.

    A box inside a cylinder (axis X) needs, in the best case (centred),
    a circle of radius = half the diagonal of its cross-section face.
    """
    best = None
    for i in range(3):
        cross = [d for j, d in enumerate(dims) if j != i]
        r = math.hypot(cross[0], cross[1]) / 2.0
        if best is None or r < best[1]:
            best = (dims[i], r, cross)
    return best


def check_rgb_both_results():
    r_int = registry.ASSUMED_INNER_DIAMETER / 2.0
    r_shell = registry.DRUM_SHELL_DIAMETER / 2.0
    board = registry.COMPONENTS["rpi_camera_module_3"]["dims_mm"]
    sa = registry.COMPONENTS["rpi_cm3_sensor_assembly"]["dims_mm"]

    ax_b, r_b, cross_b = _min_cross_section_radius(board)
    check(r_b > r_int,
          "RGB option 1 (full CM3 board) has NO in-drum orientation",
          "best axis-aligned case: %.1f mm axial, cross %s needs dia "
          "%.1f mm (interior dia %.1f; even the dia %.0f shell is "
          "exceeded)" % (ax_b, ["%.1f" % c for c in cross_b], 2 * r_b,
                         2 * r_int, 2 * r_shell))
    check(2 * r_b > registry.DRUM_SHELL_DIAMETER,
          "CM3 board exceeds even the drum shell",
          "min enclosing dia %.2f > shell dia %.1f"
          % (2 * r_b, registry.DRUM_SHELL_DIAMETER))

    ax_s, r_s, cross_s = _min_cross_section_radius(sa)
    check(r_s <= r_int,
          "RGB option 2 (CM3 Sensor Assembly) fits in-drum",
          "best case: %.1f mm axial, cross %s needs dia %.1f mm; "
          "radial-optical placement (depth %.2f) verified in layouts"
          % (ax_s, ["%.1f" % c for c in cross_s], 2 * r_s, sa[2]))


def main():
    print("VALIDATE-BEGIN", flush=True)
    if not os.path.exists(DOC_PATH):
        print("FAIL document missing: %s (run build.py first)" % DOC_PATH,
              flush=True)
        sys.exit(1)
    doc = App.openDocument(DOC_PATH)
    print("VALIDATE-DOC-OPEN objects=%d" % len(doc.Objects), flush=True)
    check_envelopes(doc)
    check_drum_context(doc)
    check_groups(doc)
    check_exterior(doc)
    check_layouts(doc)
    check_rgb_both_results()
    check_approved_untouched()
    total = len(_failures)
    print("----", flush=True)
    if total:
        print("RESULT: %d FAIL" % total, flush=True)
        sys.exit(1)
    print("RESULT: ALL PASS", flush=True)
    sys.exit(0)


main()
