# MECH-FIT-03 private 3D board review

The separate KiCad candidate and Blender model now retain all 238 inherited
footprints: 234 component bodies and four mounting-hole footprints. The USB wing
is retained. J1 is on the underside of that wing in KiCad. J2/J3 keep their
horizontal orientation and the catalog-sized paste apertures from MECH-FIT-02.

82 footprints move in this preliminary mechanical study. Compute, DDR and eMMC
placement, J2/J3 and H1–H4 stay fixed. Power packages and inductors no longer
overlap. The bridge/protection groups remain beside their respective head
connectors. Passives move only as needed to clear nearby geometry, within 6 mm
of their previous anchors. This is spatial placement, **not approved
pin-driven decoupling or routing**.

No component, original pad identity, model selection or board-edge block was
deleted or substituted. The saved candidate preserves 2,419 pad primitives,
including the 106 paste-only apertures. Copper nets, tracks, vias and zones
remain absent. The intended population is not complete merely because the
inherited population is preserved; SW1 and other uncaptured circuitry remain
open.

## Checks and restrictions

- 54 candidate, geometry and provenance tests pass.
- Native KiCad DRC reports zero courtyard overlaps, PTH/NPTH-in-courtyard
  findings and hole-clearance findings. There are no non-silkscreen findings
  involving two different footprints.
- Full DRC **still fails**, with 508 findings and exit code 5. The remaining
  categories are 340 intra-footprint clearance findings, two internal J1
  copper-to-NPTH-edge findings, 29 drill-rule findings and 137 silkscreen/text
  findings. No exclusions or severity suppressions were added.
- The fresh imported model has zero positive component-body box overlaps.
  Every native body vertex is retained during mesh joining. Fixed-datum
  anchors match the KiCad export.
- The Blender/GLB round-trip audit checks every mesh in both directions. This
  validates transport, not component selection or housing fit.
- 131 protected baseline, historical candidate, Blender and site inputs stay
  unchanged. The canonical import guard and public assets were not modified.

The model contains 216 native inherited component models and **18 explicitly
representative package-body envelopes**. The envelopes have documented
dimensions but do not invent vendor pin or package detail. Source PCB pads and
silkscreen remain visible; no decorative copper routing was added.

The nominal board thickness is 1.6 mm. The native substrate alone measures about
1.51 mm. The model audit retains bounds for each board surface separately;
substrate thickness is not silently relabelled as total finished thickness.
The 1.5 mm mechanical proposal and the electrical stack-up remain unreconciled.

J1 remains the inherited Amphenol, not an approved replacement for the intended
Hirose. Plug/mouth alignment, retention and housing fit are open. J4/J5 visibly
retain their tall pin-header placeholders; no low-profile motor mating system
was selected. FH26/FH26W variant, numbered flex continuity, latch sweep and
moving-flex clearance remain open. Sensor ownership is unresolved.

All electrical gates remain unchanged. Circuit capture, package audits, the
FPGA tool build, DDR constraints, manufacturing stack-up and routing still need
closure. Fabrication, public visual release and assembly/viewer integration
permissions remain **false**.

## Inspect the result

Current private candidate:
`../../tmp/pcb-model-candidate-2026-10-13/placement-03/deepreal-main-pcba-mech-fit-03.kicad_pcb`

Current Blender review:
`../../tmp/pcb-model-candidate-2026-10-13/model-03/deepreal-mech-fit-03-review.blend`

The same directory contains `candidate-board.glb`, `board-top.png`,
`board-bottom.png`, `model-audit.json` and `transport-audit.json`. The candidate
directory retains native geometry, its source-bound manifest, native DRC and
the DRC classification. The parent holds the protected snapshot and final
validation report.

The first saved placement trial failed the pad-registration guard. The second
trial exposed cross-board microphone-hole and USB shell-tab conflicts in native
DRC. Both remain diagnostic history, not the current candidate. The third
placement resolves those findings. The first lighting trial is also retained;
the second uses readable lighting and nonmetallic ceramic/plastic/core shaders
without changing native component base colours or geometry. The current third
model keeps that appearance and opens with a framed millimetre-scale viewport;
studio helpers are hidden from interactive inspection.

This is now a visual review point, not a request for the user to approve
electrical rules. The useful feedback is on arrangement and access. No commit,
push, deployment or website update was made.
