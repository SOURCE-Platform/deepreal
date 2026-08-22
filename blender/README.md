# DeepReal Blender scene

Parametric Blender scene for renders/animations of the DeepReal device,
driven by meshes exported from the FreeCAD CAD. Same philosophy as
`cad/`: Python is the source of truth; `deepreal.blend` and everything
under `assets/`/`renders/` are generated artifacts, rebuilt on demand.

## Architecture

Two sources of truth, cleanly split:

- **`../cad/` (FreeCAD)** owns the engineered product geometry.
- **`blender/`** owns render-side assets: the MacBook model, materials,
  lighting, cameras, and the provisional mounting stack. None of it is
  engineering data.

`assets/manifest.json` is the contract between the two sides: per-part
mesh files plus every resolved CAD parameter, so render-side code sizes
things from the same numbers the CAD uses (e.g. the MacBook lid locks
to the CAD reference slab, the mounting stack spans the pocket exactly).

## Files

- `materials.py` — deterministic Principled BSDF library (smooth
  3D-print nylon, nickel/steel/foam-tape mount, MacBook alu/screen/
  keycaps, debug red)
- `macbook.py` — parametric MacBook Air (M2-generation chassis, silver;
  lid locked to the CAD slab cross-section so the pocket fits)
- `device.py` — native quad/n-gon rebuild of the device from the CAD
  profile + bboxes, volume-verified against the CAD solids (<0.1%)
- `optics.py` — sensor-drum optical treatment: five apertures per drum
  (large depth lens | projector cluster | large RGB lens) bored through
  the curved skin as live boolean modifiers, parallel optic axes on a
  hidden internal carrier, per-aperture X/Z/diameter/depth/bezel
  constants, per-drum optics pivots rotated per the CAD drum-pitch
  params (spin a pivot = spin the turret)
- `mounting_stack.py` — PROVISIONAL Phase-4 preview (magnet plate /
  steel plate / foam tape); delete when CAD Phase 4 models the real
  stack
- `build_scene.py` — headless scene assembly: imports the CAD meshes,
  builds MacBook + mount, parents everything to the lid pivot (105°
  open angle), materials, 3-point lighting, three cameras; saves
  `deepreal.blend`
- `assets/` — generated: `parts/*.stl` + `manifest.json`
- `renders/` — generated verification stills
- `deepreal.blend` — generated; open it interactively any time

## Pipeline

After any CAD change (from the repository root):

```sh
# 1. export meshes + params from FreeCAD
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/export_blender.py

# 2. rebuild the scene (and optionally render)
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --factory-startup --python blender/build_scene.py -- [--render] \
    [--camera hero|device|laptop] [--samples 96]
```

Scene rebuilds are total: manual `.blend` edits do not survive a
rebuild, so change the scripts instead. (Iterating on looks inside the
Blender GUI is fine — just port the result back into the scripts.)

Coordinate system: identical to the CAD (mm scaled to m, Z up, -Y user
side, origin at the lid top-edge centre). Everything that swings with
the lid is parented to `Lid_Pivot` at the hinge with
`matrix_parent_inverse` captured before rotation; the open angle is
`OPEN_ANGLE_DEG` in `build_scene.py`.

## Next up (not built yet)

- USB-C cable as a render-side curve
- Feasibility drum internals (SL-A layout, travel limits, vendor STEPs)
  for cutaway/technical shots
- Animations as `bpy` scripts (drum rotation, exploded view, assembly)
- Backdrop/studio environment, hero renders
