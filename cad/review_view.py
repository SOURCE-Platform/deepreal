"""
GUI-side review-view helper for DeepReal.

Makes every generated object visible and restores the review camera: the
captured preset from cad/review_view_preset.py if present, otherwise
isometric view + Fit All.

Run inside the FreeCAD GUI after opening the document, either via
Macro -> Macros... or from the Python console (from the repository root):

    exec(open("cad/review_view.py").read())

It changes no geometry. (The generated FCStd intentionally contains no GUI
view state; view/camera setup is a GUI-side concern. When the live-reload
session from cad/dev.sh is running, this helper is unnecessary -- the
session applies the same view automatically after every rebuild.)
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

import FreeCAD as App  # noqa: E402
import FreeCADGui as Gui  # noqa: E402

import document  # noqa: E402
import review_camera  # noqa: E402


def set_review_view(doc_name="deepreal"):
    doc = App.getDocument(doc_name)
    for group_name in (document.GROUP_REFERENCES, document.GROUP_PRODUCT):
        group = doc.getObject(group_name)
        if group is None:
            continue
        if hasattr(group, "ViewObject"):
            group.ViewObject.Visibility = True
        for obj in group.Group:
            if hasattr(obj, "ViewObject"):
                obj.ViewObject.Visibility = True

    gui_doc = Gui.getDocument(doc_name)
    view = gui_doc.ActiveView
    if view is None:
        print("No active 3D view; open one first "
              "(right-click the document -> Create new view).")
        return
    which = review_camera.apply_to_view(view)
    print("Review view applied ({}), all objects visible.".format(which))


set_review_view()
