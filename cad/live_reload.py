"""
Live-reload infrastructure for interactive DeepReal CAD development.

GUI-independent core (watched-file discovery, change detection, debounce,
module reload) plus the GUI-side DevSession that ties it into FreeCAD's Qt
event loop. The core is import-safe without a GUI so validate.py can test
it headlessly.

Only normal FreeCAD/FreeCADGui APIs are used at runtime. No FCStd archive
member is ever read, synthesized, or written by this module.
"""

import importlib
import os
import sys
import time
import traceback

CAD_DIR = os.path.dirname(os.path.abspath(__file__))

# cad/*.py files that do NOT participate in geometry generation and
# therefore never trigger a rebuild. Everything else in cad/*.py is
# watched, so future geometry modules are picked up automatically.
EXCLUDED_FILES = {
    "build.py",
    "validate.py",
    "live_reload.py",
    "start_dev.py",
    "review_camera.py",
    "review_view.py",
    "capture_review_view.py",
    "review_view_preset.py",
}

# Reload order: parameters first (other modules read it), document last
# (it ties the builders together), everything else alphabetically between.
RELOAD_PRIORITY = {"parameters": 0, "document": 99}

POLL_MS = 250     # QTimer poll interval for file mtimes (cheap stat calls)
DEBOUNCE_S = 0.4  # quiet period after the last save before rebuilding


def _qt_core():
    """QtCore from whichever Qt binding this FreeCAD ships.

    Prefers FreeCAD's binding-agnostic PySide shim, then PySide6
    (FreeCAD 1.1 macOS bundle), then PySide2 (older releases).
    """
    try:
        from PySide import QtCore
        return QtCore
    except ImportError:
        pass
    try:
        from PySide6 import QtCore
        return QtCore
    except ImportError:
        pass
    from PySide2 import QtCore
    return QtCore


def watched_files():
    """All cad/*.py geometry sources. deepreal.FCStd is deliberately NOT
    watched: the Python sources are the source of truth."""
    return sorted(
        os.path.join(CAD_DIR, name)
        for name in os.listdir(CAD_DIR)
        if name.endswith(".py") and name not in EXCLUDED_FILES
    )


def snapshot(paths):
    """{path: mtime} for existing files."""
    return {path: os.path.getmtime(path)
            for path in paths if os.path.exists(path)}


def detect_changes(paths, old_snapshot):
    """Return (changed, new_snapshot). Detects edits, additions, removals."""
    new_snapshot = snapshot(paths)
    return new_snapshot != old_snapshot, new_snapshot


class Debouncer:
    """Collapses a burst of file-system events into one rebuild.

    note_change() marks activity; due() becomes True only once the burst
    has been quiet for `delay_s`; fire() resets. Pure Python with an
    injected clock, so it is unit-testable headless.
    """

    def __init__(self, delay_s=DEBOUNCE_S):
        self.delay_s = delay_s
        self._last_change = None

    def note_change(self, now):
        self._last_change = now

    def due(self, now):
        return (self._last_change is not None
                and (now - self._last_change) >= self.delay_s)

    def fire(self):
        self._last_change = None


def reload_modules(names):
    """Re-execute each named module's source into its existing module object.

    Deliberately bypasses importlib.reload: its timestamp/size-based
    bytecode cache can silently reuse stale code when two same-size edits
    land within the same second (common with debounced live reload, e.g.
    FACE_HEAD_DIAMETER 24.0 -> 27.0). Reading and compiling the source
    directly is immune to that, and a compile error raises BEFORE the
    module's previous working state is touched, so the last valid model
    stays on screen.

    Re-execution happens in the SAME module object, so other modules
    holding `import x` references see the new code automatically.
    """
    reloaded = []
    for name in names:
        module = sys.modules.get(name)
        if module is None:
            importlib.import_module(name)
            reloaded.append(name)
            continue
        path = getattr(module, "__file__", None)
        if path is None or not os.path.exists(path):
            importlib.reload(module)  # fallback for non-file modules
            reloaded.append(name)
            continue
        with open(path, "r") as handle:
            source = handle.read()
        code = compile(source, path, "exec")  # SyntaxError -> module untouched
        exec(code, module.__dict__)
        reloaded.append(name)
    return reloaded


def reload_geometry_modules():
    """Reload all watched geometry modules in dependency order."""
    names = [os.path.splitext(os.path.basename(path))[0]
             for path in watched_files()]
    names.sort(key=lambda n: (RELOAD_PRIORITY.get(n, 50), n))
    return reload_modules(names)


class DevSession:
    """Live-reload session running inside the FreeCAD GUI.

    Polls the watched CAD sources on a QTimer, debounces bursts, reloads
    the geometry modules, rebuilds the geometry inside the already-open
    document (no close/reopen), forces visibility, and restores the review
    camera. A failure keeps the last valid model on screen and is retried
    automatically on the next save.
    """

    def __init__(self, doc_name="deepreal"):
        self.doc_name = doc_name
        self.watched = watched_files()
        self.file_state = snapshot(self.watched)
        self.debouncer = Debouncer(DEBOUNCE_S)
        self.reload_count = 0   # successful reloads, including the initial one
        self.last_error = None
        self._timer = None

    def start(self):
        QtCore = _qt_core()

        self.reload_once(reason="session start")
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(POLL_MS)
        # The 3D view may not exist yet during startup; re-apply view and
        # visibility once the event loop has settled.
        QtCore.QTimer.singleShot(1000, self._settle_view)

        print("DeepReal live reload watching {} file(s):".format(
            len(self.watched)))
        for path in self.watched:
            print("  " + os.path.basename(path))
        print("Edit any of them; the open model rebuilds automatically.")

    def stop(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
            print("DeepReal live reload stopped.")

    def _tick(self):
        now = time.monotonic()
        changed, self.file_state = detect_changes(self.watched,
                                                  self.file_state)
        if changed:
            self.debouncer.note_change(now)
        if self.debouncer.due(now):
            self.debouncer.fire()
            self.reload_once(reason="source change")

    def reload_once(self, reason):
        """One reload + rebuild + view restore cycle. Never raises."""
        import FreeCAD as App
        import document
        import review_camera

        try:
            reloaded = reload_geometry_modules()
            doc = App.getDocument(self.doc_name)
            document.rebuild_in_place(doc)
            self._force_visibility(doc)
            view_mode = review_camera.apply_to_active_view()
            self.reload_count += 1
            self.last_error = None
            msg = ("DeepReal live reload #{} ({}): OK "
                   "[reloaded: {}; view: {}]".format(
                       self.reload_count, reason,
                       ", ".join(reloaded), view_mode))
            print(msg)
            App.Console.PrintMessage(msg + "\n")
        except Exception:
            self.last_error = traceback.format_exc()
            print("DeepReal live reload FAILED ({}); keeping the last "
                  "valid model. Fix the file and save again.".format(reason))
            print(self.last_error)
            sys.stdout.flush()
            App.Console.PrintError(
                "DeepReal live reload FAILED ({}):\n{}\n".format(
                    reason, self.last_error))

    def _settle_view(self):
        """One-shot deferred visibility/camera re-apply after startup."""
        import FreeCAD as App
        import review_camera
        try:
            doc = App.getDocument(self.doc_name)
            self._force_visibility(doc)
            review_camera.apply_to_active_view()
        except Exception:
            pass  # the next reload cycle applies them anyway

    def _force_visibility(self, doc):
        """Every generated object (anything in the two generated groups,
        plus the groups themselves) is visible. Later phases participate
        automatically by adding their objects to the groups."""
        import FreeCAD as App
        import document

        if not App.GuiUp:
            return
        for group_name in (document.GROUP_REFERENCES, document.GROUP_PRODUCT):
            group = doc.getObject(group_name)
            if group is None or not hasattr(group, "ViewObject"):
                continue
            group.ViewObject.Visibility = True
            for obj in group.Group:
                if hasattr(obj, "ViewObject"):
                    obj.ViewObject.Visibility = True
