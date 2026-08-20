"""Build cad/feasibility/drum_internals.FCStd.

Gate 1 deliverable + Gate 1.5B depth-architecture layouts.

Headless:
    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD --console \\
        cad/feasibility/build.py

Contents:
  * EXT_*  approved exterior + laptop reference (copied read-only from
           cad/deepreal.FCStd, which is never written)
  * Ctx_*  drum shells / assumed interiors / travel markers
  * ENV_*  one true-size envelope per registry component, in a library row
  * LA_* / AP_* / KO_*  in-drum layout studies SL-A / SL-B / ToF-A
  * G00..G18 visibility groups
Review presets are view-only and live in review_presets.py.
"""

import os
import sys

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import drum_context
import envelopes
import exterior_reference
import groups
import layouts

DOC_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "drum_internals.FCStd"))


def build():
    # FreeCAD raises instead of returning None for an unknown document.
    if "drum_internals" in App.listDocuments():
        App.closeDocument("drum_internals")
    if os.path.exists(DOC_PATH):
        os.remove(DOC_PATH)

    doc = App.newDocument("drum_internals")
    exterior = exterior_reference.import_exterior_reference(doc)
    context = drum_context.build(doc)
    envs = envelopes.build_all(doc)
    layout_objs = layouts.build(doc)
    groups.build(doc, exterior, context, envs, layout_objs)
    doc.recompute()
    doc.saveAs(DOC_PATH)

    n_groups = len([o for o in doc.Objects
                    if o.TypeId == "App::DocumentObjectGroup"])
    print("BUILD-OK %s | objects=%d groups=%d"
          % (DOC_PATH, len(doc.Objects), n_groups))


# FreeCAD --console does not guarantee __name__ == "__main__"; run
# unconditionally when the file is executed as a script.
build()
