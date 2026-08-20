"""Gate 1 validation for cad/feasibility/drum_internals.FCStd.

Checks, all reported as PASS/FAIL lines with a summary and exit code:
  1. every registry component has an ENV_* object whose bounding box
     matches the published registry dimensions (tol 0.05 mm)
  2. drum context geometry matches the approved model positions
  3. all 13 visibility groups exist
  4. the exterior reference matches the approved Main_Housing bounds
  5. cad/deepreal.FCStd is untouched: its SHA1 equals the main-branch
     blob (git show main:cad/deepreal.FCStd)

Run headless:
    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console \\
        cad/feasibility/validate_feasibility.py
"""

import hashlib
import os
import subprocess
import sys

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry
from groups import GROUP_DEFS

DOC_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "drum_internals.FCStd"))
APPROVED = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "deepreal.FCStd"))

TOL = 0.05
_failures = []


def check(ok, label, detail=""):
    print("%s %s%s" % ("PASS" if ok else "FAIL", label,
                       (" | " + detail) if detail else ""), flush=True)
    if not ok:
        _failures.append(label)


def dims_of(obj):
    bb = obj.Shape.BoundBox
    return sorted([bb.XLength, bb.YLength, bb.ZLength])


def check_envelopes(doc):
    for key, entry in registry.COMPONENTS.items():
        obj = doc.getObject("ENV_" + key)
        if obj is None:
            check(False, "envelope %s" % key, "object missing")
            continue
        got = dims_of(obj)
        if entry["shape"] == "cylinder":
            d, length = entry["dims_mm"]
            want = sorted([d, d, length])
        else:
            want = sorted(entry["dims_mm"])
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
    check_approved_untouched()
    total = len(_failures)
    print("----", flush=True)
    if total:
        print("RESULT: %d FAIL" % total, flush=True)
        sys.exit(1)
    print("RESULT: ALL PASS", flush=True)
    sys.exit(0)


main()
