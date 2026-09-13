# Main PCBA native-import checkpoint — 14 September 2026

Status: **internal review only; electrical placement and website release remain blocked.**

This implements the geometry-fidelity portion of Stage A in the
[diagnosis and action plan](deepreal-electronics-diagnosis-and-action-plan-v0.2.md).
It does not close the component-library, circuitry, head/flex, mechanical-fit,
placement or routing gates. The canonical KiCad board was not moved or routed.

## What changed

- Blender now imports KiCad's own GLB: the full population, actual footprint
  pads, drilled geometry, solder-mask openings and silkscreen, rather than a
  second handcrafted component population.
- Of 238 footprints, 216 supply native component models, 18 have broken model
  references, and four are mounting holes. The 18 missing models use clearly
  tagged selected-package body envelopes, with no invented pins or pad arrays.
  These are **not** verified package replacements. Existing incorrect footprint
  choices are deliberately exposed rather than silently corrected in Blender.
- All 2,313 pads are described by the KiCad export. The board contains no routed
  tracks, vias or zones; Blender therefore adds none.
- Decorative ground-ring bars, fake shielding vias, extra connector-bank board
  slabs and the separate support-part generator no longer appear in the build.
  Removed source remains recoverable in Git history.
- A missing tamper switch is reported as missing, not added at an old coordinate.
- Footprint identifiers are now readable and stable, and component/pad UUIDs,
  model transforms and actual courtyard polygons are exported. The former
  `courtyard_bbox_mm` was merely a graphics bounding box; it is no longer
  mislabeled as courtyard evidence.
- Board, JSON, GLB, design-status and native-library hashes prevent stale imports.
- Close-up scenes now update the source scene before cloning the geometry.
  This fixes an inherited laptop-hinge rotation in supposedly orthographic views.
- Ray-traced rendering resolves closely spaced native PCB layers without
  changing their geometry. Material transparency and colors are presentation-only.

## Checks and their meaning

| Check | Result | What it does not prove |
|---|---|---|
| Complete footprint accounting | 216 native models + 18 envelopes + 4 holes = 238 | Package selections are correct |
| Imported footprint-anchor comparison | Maximum observed X/Y error 0.0 mm | Pin-driven electrical placement |
| Top, bottom, dimensioned, exploded and cutaway population | All 234 component bodies accounted for | Clearances or manufacturing feasibility |
| Provenance regression tests | Six pass, including changed-file rejection | Electrical validation |
| Repeated JSON regeneration | Byte-identical output | Physical or electrical correctness |
| KiCad native DRC | 610 violations; 199 schematic-parity issues | A passing PCB review |
| Named pad nets | None | Zero unconnected items is meaningful |
| Functional schematic sheets | 14 note-only sheets beneath the root | A complete 15-page circuit schematic |
| Projected model near-contacts | 21 candidates for review | These are not exact courtyard/solid-intersection verdicts |

The 90 × 28 mm outline is unchanged. KiCad records 1.6 mm nominal board
thickness; its native GLB substrate alone is about 1.510 mm, excluding separate
surface layers. No stack-up approval or populated-height approval is inferred.
Five DRC rules are currently ignored in the source project; the audit lists
them explicitly. There are no broad new suppressions or waived electrical errors.

## What remains wrong and comes next

1. Audit and correct the exact footprints and 3D references. In particular,
   processor/FPGA/memory pin data cannot be replaced by a similar-looking BGA.
   The selected PF53, angle-sensor, USB-protection and receptacle packages need
   reconciliation with their current footprints.
2. Resolve the physical interfaces before moving the whole layout: USB opening,
   head connector orientation, connector overhang and latch access, board
   mounting, shield envelope and the missing processor thermal interface.
3. Develop the reusable rotating optical-head board, used once in each drum.
   Each needs RGB/IR sensor circuitry, local rails/decoupling, projector driver
   and pulse-current loop, default-off interlock, clock/reset/trigger and sensing.
   The existing blank sensor/projector PCB slabs are not those completed designs.
4. Resolve angle sensing near each drum's magnet and rotation axis. Determine
   whether the stationary encoder boards remain separate and remove inconsistent
   duplicate sensor representations only after that decision.
5. Define both head-to-main interfaces, including contact orientation, power
   and returns, six candidate camera differential pairs per head (four data
   plus two clocks), control lines, current capacity, flex geometry and motion.
   The drawn round cable is not evidence of a manufacturable dynamic flex.
6. Close simultaneous camera/FPGA bandwidth, legal pins and host-output strategy,
   then capture circuits, implement constraints and perform pin-driven placement.
   Do not make the current image attractive by concealing these defects.

The two head designs, main-board placement, routed connections and enclosure
integration are still unfinished. No senior-engineer approval is claimed.

## Reproduce from the repository root

```sh
'/Users/adam/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3' hardware/electronics/deepreal-main-pcba/scripts/export_kicad_design.py

python3 hardware/electronics/deepreal-main-pcba/scripts/export_native_review.py --kicad-cli '/Users/adam/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

python3 hardware/electronics/deepreal-main-pcba/scripts/run_layout_audit.py --kicad-cli '/Users/adam/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python blender/build_scene.py

/Applications/Blender.app/Contents/MacOS/Blender --background blender/deepreal.blend --python-exit-code 1 --python blender/validate_pcba_native.py --python blender/test_pcba_native.py

/Applications/Blender.app/Contents/MacOS/Blender --background blender/deepreal.blend --python-exit-code 1 --python blender/render_native_review.py
```

On another installation, provide its CLI path and optionally `--model-dir`.
No vendor libraries are downloaded, installed or committed by these scripts.
Generated GLB/logs/reports live in `hardware/electronics/deepreal-main-pcba/generated-review/`.
The rebuilt model is `blender/deepreal.blend`; internal images and transfer
report are in `blender/review-output/`. These directories are rebuildable and
ignored by Git. The existing publication manifest remains locked.

## Artifact inventory

- **Active source:** canonical KiCad board and schematic hierarchy; exporter,
  native importer and test scripts; existing mechanical assembly source.
- **New review evidence:** the diagnosis/action plan, this checkpoint, native
  DRC/readiness reports and native-import report.
- **Internal review only:** regenerated `.blend`, main top/bottom/dimensioned,
  exploded, shield-cutaway and installed-review images. These show defects.
- **Not generated:** head/encoder KiCad boards, completed schematic, routed
  layout, fabrication files, tested hardware or publication-approved images.
- **Superseded:** old illustrative population and preliminary website PCB
  renders. They must not be mistaken for this engineering rebuild.
