"""
DeepReal review camera preset, using only normal FreeCADGui APIs.

Capture: read the active 3D view's camera as FreeCAD's own Inventor-format
string (View3DInventor.getCamera()) and store it in
cad/review_view_preset.py -- a normal, human-inspectable repo-side Python
file.

Restore: after every live-reload rebuild, reapply the captured camera with
View3DInventor.setCamera(). If no preset exists, fall back to View
Isometric + Fit All. Reapplying a fixed string cannot drift.

Nothing is ever written into or read from the FCStd archive.
"""

import importlib.util
import os

CAD_DIR = os.path.dirname(os.path.abspath(__file__))
PRESET_PATH = os.path.join(CAD_DIR, "review_view_preset.py")

PRESET_TEMPLATE = '''"""
DeepReal review camera preset.

Captured by cad/capture_review_view.py from a manually positioned FreeCAD
camera. Human-inspectable; delete this file to fall back to
"isometric view + fit all" after each rebuild.

The string is FreeCAD's own Inventor camera representation as returned by
View3DInventor.getCamera(); it is applied with View3DInventor.setCamera().
"""

CAMERA_SETTINGS = {settings!r}
'''


def load_preset(path=None):
    """Return the captured camera settings string, or None when no usable
    preset exists (callers then fall back to isometric + fit all)."""
    path = path or PRESET_PATH
    if not os.path.exists(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("review_view_preset",
                                                      path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        settings = getattr(module, "CAMERA_SETTINGS", None)
        if isinstance(settings, str) and settings.strip():
            return settings
    except Exception:
        pass
    return None


def save_preset(settings, path=None):
    """Write the captured camera string as a repo-side Python module."""
    path = path or PRESET_PATH
    with open(path, "w") as handle:
        handle.write(PRESET_TEMPLATE.format(settings=settings))
    return path


def capture_from_active_view():
    """Read the active 3D view's camera as an Inventor-format string."""
    import FreeCADGui as Gui

    if Gui.ActiveDocument is None or Gui.ActiveDocument.ActiveView is None:
        raise RuntimeError("no active 3D view to capture from")
    return Gui.ActiveDocument.ActiveView.getCamera()


def apply_to_view(view):
    """Apply the captured preset to a view, or isometric + fit all.

    Returns which mode was applied ("preset" or "isometric+fitAll").
    """
    settings = load_preset()
    if settings:
        try:
            view.setCamera(settings)
            return "preset"
        except Exception:
            pass  # fall through to the default view
    view.viewIsometric()
    view.fitAll()
    return "isometric+fitAll"


def apply_to_active_view():
    """No-op-safe wrapper used by the live-reload session."""
    import FreeCAD as App

    if not App.GuiUp:
        return "headless (skipped)"
    import FreeCADGui as Gui

    if Gui.ActiveDocument is None or Gui.ActiveDocument.ActiveView is None:
        return "no active view (skipped)"
    return apply_to_view(Gui.ActiveDocument.ActiveView)
