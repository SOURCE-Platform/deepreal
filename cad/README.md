# DeepReal CAD

Parametric FreeCAD model driven entirely by Python. The Python source is
the single source of truth; `deepreal.FCStd` is a generated artifact that
can be rebuilt at any time.

## Layout

- `parameters.py` — every dimension/placement parameter (edit this file)
- `parts.py` — Phase 1 builders (display reference, main housing)
- `sensor_heads.py` — Phase 2 builders (two X-axis barrels + debug orientation marks)
- `rear_arm.py` — Phase 3 builder: Main_Housing as one coherent Y-Z side
  profile (body + full-width quarter-circle arm + laptop-lid pocket)
  extruded along X
- `document.py` — assembles the FreeCAD document (import-safe module);
  `rebuild_in_place()` swaps generated geometry inside an open document.
  Generated objects carry a `DeepRealGenerated` stamp; rebuilds delete
  stamped objects that are no longer registered in the source, and never
  delete objects you created manually
- `build.py` — script: rebuilds `deepreal.FCStd` from scratch
- `validate.py` — script: perturbs parameters, rebuilds in memory, checks
  bounding boxes plus the live-reload architecture
- `live_reload.py` — file watcher + debounce + module reload + `DevSession`
- `start_dev.py` / `dev.sh` — start the interactive development session
- `review_camera.py` — capture/restore the review camera via normal
  FreeCADGui API (`getCamera()`/`setCamera()`)
- `capture_review_view.py` — GUI helper: save the current camera as the
  review preset (`cad/review_view_preset.py`)
- `review_view.py` — GUI helper: force visibility + restore the review
  camera once, manually

`build.py` and `validate.py` are scripts, not modules: freecadcmd runs them
with `__name__` set to the module name, so they execute their `main()`
unconditionally at import time. Import `document.py` instead.

Headless builds are saved only through FreeCAD's normal save API and
intentionally contain **no GUI view state** (no `GuiDocument.xml`): an
earlier injection mechanism caused `Reading failed from embedded file:
GuiDocument.xml` errors on open and was removed. Camera/visibility setup
is a GUI-side concern handled by `review_camera.py` / `review_view.py` /
the live-reload session. Nothing in `cad/` ever reads, synthesizes, or
writes FCStd archive members.

## Rebuild (headless, deterministic)

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/build.py
```

## Validate (headless)

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/validate.py
```

## Develop (live reload)

```sh
cad/dev.sh
```

This opens `deepreal.FCStd` in FreeCAD (building it first if missing),
rebuilds the geometry from the current Python source inside the open
document, makes all generated objects visible, restores the review camera,
and starts watching the geometry sources (`parameters.py`, `parts.py`,
`sensor_heads.py`, `rear_arm.py`, `document.py` — anything in `cad/*.py`
not on the exclusion list).

Then just edit and save any watched file: after a 400 ms quiet period the
model is rebuilt **in place** — same document, no close/reopen, no
duplicated objects, visibility re-forced, camera restored. If a half-saved
edit breaks a module, the last valid model stays on screen and the error
is printed to FreeCAD's report view; saving a fix rebuilds again.

One-time camera setup (optional): arrange the view you like, then run in
FreeCAD's Python console:

```python
exec(open("cad/capture_review_view.py").read())
```

This stores the camera in `cad/review_view_preset.py` (a normal repo file;
inspect/edit/delete freely). Every reload then restores exactly that view.
Without the preset, reloads fall back to isometric + Fit All. To stop the
watcher: `start_dev.SESSION.stop()` in the Python console.

No global FreeCAD configuration is installed or modified, and the session
never saves the FCStd — `deepreal.FCStd` on disk stays exactly what the
last headless `build.py` run produced.

## Coordinate system

Millimetres throughout. The Y axis is defined physically, not abstractly:

- **X** — left/right across the laptop display (+X to the user's right)
- **-Y = FRONT / USER SIDE** — the side of the display with the visible
  screen/pixels, where the seated user sits. The sensor heads live here.
- **+Y = REAR / MOUNT SIDE** — the back of the laptop lid. The integrated
  arm and magnetic mounting system will live here.
- **Z** — vertical (+Z up)
- **Origin** — centre of the display lid's top edge, on the lid mid-plane

This matches FreeCAD's viewing convention: the standard front view looks
at the -Y (user) face.

## Phases

**Phase 1:** MacBook Air M2 display reference slab + DeepReal main housing
envelope.

**Phase 2:** two horizontal cylindrical sensor heads
(`Face_Sensor_Head`, `Interaction_Sensor_Head`) with axes along X on the
user side (-Y) of the housing, independent pitch rotation parameters, and
temporary thin orientation marks lying flush on the barrels (debug
geometry in `References`).

**Phase 2.5:** interactive development infrastructure —
live-reload session (`dev.sh`), in-place rebuilds, review camera
capture/restore. No new product geometry.

**Phase 3 (current):** `Main_Housing` is built from ONE coherent Y-Z
side profile — rectangular sensor body + full-width quarter-circle rear
arm + laptop-lid pocket — extruded along X across the full device width
into a single connected solid (there is no separate `Rear_Arm` product
object and no boolean union, so no splitter seams or crossover
artifacts). Per the annotated review screenshots, the arm hangs BELOW
the body in its corrected lower position: the arc centre sits exactly on
the housing bottom plane and the arc meets the housing exactly at the
bottom-rear corner, tangent to the rear face, so the silhouette runs
rear face → arc → mounting face → pocket ceiling as one continuous
outline. The intentional **laptop-lid pocket**: the housing front
(user-side) face is flush with the lid's front plane
(`MAIN_BODY_LID_FRONT_OFFSET = 0`; the housing extends rearward and is
not centred on the lid), the housing bottom floats
`MAIN_BODY_LID_TOP_CLEARANCE` (5 mm, provisional) above the lid top edge,
and the arm's vertical mounting face stands
`LAPTOP_LID_POCKET_CLEARANCE` (2 mm, provisional) behind the lid rear
face — so the lid's top edge inserts upward into the pocket without
touching anything, captured between the pocket ceiling and the arm wall.
The Phase 4 magnet/plate/foam-tape stack will secure the device in this
region; the long thin line in the original sketches is the USB-C cable,
which is NOT modelled yet.

`REAR_ARM_RADIUS = None` derives the radius so the arc lands exactly on
the bottom-rear corner (radius = the housing depth behind the mounting
face, currently 19 mm); set a number to override — a smaller arc tucks
under the housing and leaves a flat bottom strip behind it. The arm
position is fully derived from the housing/lid/pocket parameters, so the
body and arm can never drift apart. `resolve()` rejects parameter sets
that break the pocket: housing touching the lid top, sub-0.5 mm pocket
clearance, mounting face outside the housing span, sensor heads dipping
below the pocket ceiling, an arc reaching past the rear face, or an arm
tip that fails to descend below the lid top edge.

Also per the specification, the interaction drum is nominally pitched
down (`INTERACTION_HEAD_ROTATION_DEG = 45`, provisional) while the face
drum looks forward at the user.

Still intentionally absent: USB-C cable routing, magnetic mounting stack,
PCB/motor keep-outs, USB-C connector geometry, wall thickness, optical
openings.
