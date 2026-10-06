# DeepReal R14 — drum systems assembly study

Open [the R14 Blender model](deepreal-exterior-refinement-r14.blend). It starts
with the exterior visible and the close viewport framing inherited from R13.
The complete model and all review images are inside this DeepReal folder.

R14 restores **44 separate concept parts** from the original
`blender/deepreal.blend`: an axle, two bearings, a ring gear, a geared motor,
pinion, bracket, encoder board, encoder magnet, rotation-stop envelope and
12 optical carrier/module/projector parts **for each drum**. R04 had omitted
their source collections, so they disappeared from later revisions. The parts
are grouped by drum in the Outliner for inspection and eventual exploded views.
R13's exterior shell, lens windows, main PCB, thermal stack and USB arrangement
remain intact.

## Boards and wiring shown

- Each drum has one green **head PCBA carrier**: a visible placeholder for the
  board that would hold its sensor electronics. It is shown twice because the
  intended architecture is one reusable board design in both drums. The
  optical module bodies sit against these board envelopes.
- Amber paths show where head power and data would travel from each rotating
  head toward the main board's J2/J3 area. Red paths show proposed motor
  power, and yellow paths show proposed encoder feedback (the position signal
  from the drum). Small dark J4/J5 blocks on the main board show possible
  motor/encoder connector locations.
- These lines are **route concepts**, not designed copper traces or approved
  cable assemblies. The passage from a moving drum to the fixed body, cable
  fatigue, connector parts, pinout and actual PCB layout remain open.

## Viewing the assembly

In Blender's Outliner, click the eye on
`00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME` to switch the housing
between solid and its wireframe fallback. Click the eye on
`01 — DRUM SHELLS — CLICK EYE FOR INTERNALS` to expose or cover the drum
internals. The new parts are in `07 — DRUM SYSTEMS — ASSEMBLY REVIEW`, with
separate collections for each drum's fixed drive, rotating optical parts and
routes. Objects remain individually named and selectable.

Review images: [assembled front](renders/r14-assembled-front.png),
[internals front](renders/r14-internals-front.png),
[internals rear](renders/r14-internals-rear.png), and
[drive detail](renders/r14-drive-detail.png).

## What was checked and what remains open

[The R14 verification report](r14-verification.json) confirms the 44 restored
parts, both head-board envelopes, continuous drawn routes to the main-board
areas, clearance of restored hard parts against the newer housing and drum
shell meshes, preserved R13 geometry, the 1 mm drum-body gap, all ten optical
openings and saved close viewport framing. The old drive units were shifted
outward to clear the current solid drums; the rotation-stop blocks were moved
to clearance-only positions.

**This is an assembly model, not a fabrication-ready mechanism.** In
particular, the gear-to-drum coupling, gear teeth and torque, bearing seats,
actual rotation-stop mounts, a physical rotating power/data feedthrough,
head-PCB schematic/footprints, motor connections, cable bend life and thermal
performance still require engineering. The two visual head boards do not
represent a completed electronic design. The model deliberately labels these
limits on the objects and scene.

To rebuild from the DeepReal root, run
`blender -b -t 4 --python blender/refinements/r14/build_r14.py`, then
`blender -b -t 4 --python blender/refinements/r14/verify_r14.py` and
`blender -b -t 4 --python blender/refinements/r14/render_r14.py`.
