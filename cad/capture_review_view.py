"""
Capture the current FreeCAD camera as the DeepReal review view.

Position the camera exactly how you like it in the active 3D view, then
run this once inside the FreeCAD GUI (from the repository root), either
via Macro -> Macros... or from the Python console:

    exec(open("cad/capture_review_view.py").read())

The camera is stored in cad/review_view_preset.py -- a normal repo-side
Python file you can inspect, edit, or delete. From then on, every
live-reload rebuild restores this exact view. Delete the preset file to go
back to the default "isometric + fit all" behavior.

Only normal FreeCADGui APIs are used; nothing is written into the FCStd.
"""

import os
import sys

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
    if not os.path.exists(os.path.join(HERE, "review_camera.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import review_camera  # noqa: E402

settings = review_camera.capture_from_active_view()
path = review_camera.save_preset(settings)
print("DeepReal review view captured ->", path)
print("Live-reload rebuilds will restore this camera. "
      "Delete review_view_preset.py to return to isometric + fit all.")
