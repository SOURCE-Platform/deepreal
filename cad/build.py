#!/usr/bin/env python3
"""
DeepReal CAD build entry point (Phase 1).

Rebuilds cad/deepreal.FCStd deterministically from parameters.py.

Run headless from the repository root:

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/build.py

Note: freecadcmd executes this file with __name__ set to the module name
("build"), not "__main__", so main() is invoked unconditionally at import
time. Do not import this module; import document.py instead.
"""

import os
import sys

# Make sibling modules importable whether this file is run by freecadcmd
# from the repo root, or exec'd from the FreeCAD GUI console.
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
    if not os.path.exists(os.path.join(HERE, "parameters.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import document  # noqa: E402

document.main()
