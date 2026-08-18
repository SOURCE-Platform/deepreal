#!/usr/bin/env python3
"""
DeepReal CAD development session bootstrap (runs inside the FreeCAD GUI).

Start it with the launcher:

    cad/dev.sh

which simply runs:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecad cad/start_dev.py

What it does:
  1. opens cad/deepreal.FCStd (building it from source first if missing);
  2. rebuilds the generated geometry from the current Python source (the
     source of truth) inside the open document -- no close/reopen;
  3. makes all generated objects visible;
  4. restores the captured review camera (cad/review_view_preset.py) or
     falls back to isometric + fit all;
  5. starts the live-reload watcher on the cad/*.py geometry sources.

No global FreeCAD configuration is installed or modified, and nothing is
written into the FCStd archive. Stop the watcher from the Python console
with:  start_dev.SESSION.stop()
"""

import os
import sys

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
    if not os.path.exists(os.path.join(HERE, "parameters.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SESSION = None


def main():
    global SESSION
    import live_reload

    doc = _ensure_document()
    SESSION = live_reload.DevSession(doc_name=doc.Name)
    SESSION.start()
    print("DeepReal CAD development session running "
              "(document: {}).".format(doc.Name))
    print("Stop the watcher with: start_dev.SESSION.stop()")
    return SESSION


def _ensure_document():
    import FreeCAD as App
    import document

    try:
        return App.getDocument(document.DOC_NAME)
    except Exception:
        pass
    if os.path.exists(document.OUTPUT_PATH):
        return App.openDocument(document.OUTPUT_PATH)
    print("deepreal.FCStd not found; building from source.")
    return document.build_document()


# FreeCAD executes startup scripts with __name__ set to the module name,
# and importing this module (e.g. from the smoke test) should also start
# the session -- so main() runs unconditionally.
main()
