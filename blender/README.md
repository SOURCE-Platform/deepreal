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

- `materials.py` — deterministic Principled BSDF library (near-black
  satin anodized device, reference-component optics, nickel/steel/
  foam-tape mount, MacBook alu/screen/keycaps, debug red)
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
  open angle), materials, 3-point lighting, four cameras; saves
  `deepreal.blend`
- `animate_drum_travel.py` — renders a looping clip of both drums
  sweeping their full travel (re-parents the shells under the optics
  pivots in-memory so each drum spins as one rigid body, adds witness
  marks so the rotation is visible)
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

## Electronics packaging comparison

`build_packaging_comparison.py` creates a separate architecture study with
two labeled laptops staggered diagonally (behind and to the right), so a
side view of one variant is never blocked by the other:

- current 120 × 30 × 24 mm housing, showing component conflicts;
- compact 120 × 34 × 18 mm housing — same width as today, electronics as
  a tight vertical sandwich directly below the drums.

All three use the selected drum drive: an offset micro-gearmotor behind
each drum whose pinion meshes a gear ring on the drum's outboard end
(r4 + r13 = 17 mm center distance, ≈3.25:1 reduction). The drum rotates
about its own centerline on its bearings; the gears only deliver torque,
and the motors are fully internal. A coaxial end-pod variant was
evaluated in an earlier pass of this study and rejected: direct drive
needed larger motors in pods extending ~16 mm past each housing end
(~32 mm wider device).

The compact growth extends downward behind the laptop lid,
never upward: the extension clears the lid rear face and hangs below the
lid top edge, so the visible top profile stays the current device's. The
electronics form one tight vertical sandwich (EMI shield | chips | PCBA |
heat spreader, sub-mm gaps) placed at the top of the belly directly below
the drums, so the wire drops stay short; the motors stay at drum height.

The study includes provisional volumes for the 90 × 28 × 15 mm main PCBA
keep-out, i.MX 95, CrossLink-NX FPGA, memory, power devices, two motors,
EMI shield, heat spreader, MIPI links, and motor wiring. These are
packaging envelopes, not production PCB or harness geometry. Keep-out
envelopes use wireframe viewport display so they never hide the parts
inside them.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --factory-startup --python blender/build_packaging_comparison.py
```

Outputs are saved under `blender/renders/`:

- `packaging-comparison.blend` — saved in the exterior state
- `packaging-comparison-cutaway.blend` — saved in the cutaway state for
  interactive inspection: ghosted see-through shells, internals visible,
  laptops and keep-outs hidden. Each variant's enclosure (housing + both
  drums) lives in its own `<Size>_Enclosure` collection, so the shell can
  be toggled with one click on the collection's eye/camera icons in the
  outliner. The ghost tint is kept visible in the viewport (renders stay
  nearly fully transparent)
- `drum-travel-extremes.mp4` — 4 s loop of both drums sweeping their full
  ±80° travel (from `animate_drum_travel.py`)
- `packaging-comparison-exterior.png`
- `packaging-comparison-cutaway.png`
- `packaging-comparison-drive-gear.png` — oblique orthographic close-up
  of the gear mesh at one drum end: ring gear fixed to the drum, pinion
  and the red gearmotor beside it

Expanded housings are boolean-unioned with the original housing bar, so
each expanded variant is one solid shell rather than two overlapping boxes.

The labels use red for a collision study, amber for tight packaging, and
green for serviceable reserve. In the technical view, orange is the
i.MX 95, blue is the camera FPGA, copper is the heat spreader, silver is
the EMI shield, green is the PCBA, and red cylinders are motors.

Coordinate system: identical to the CAD (mm scaled to m, Z up, -Y user
side, origin at the lid top-edge centre). Everything that swings with
the lid is parented to `Lid_Pivot` at the hinge with
`matrix_parent_inverse` captured before rotation; the open angle is
`OPEN_ANGLE_DEG` in `build_scene.py`.

## Next up (not built yet)

- USB-C cable as a render-side curve
- Feasibility drum internals (SL-A layout, travel limits, vendor STEPs)
  for cutaway/technical shots
- Animations as `bpy` scripts (exploded view, assembly)
- Backdrop/studio environment, hero renders
