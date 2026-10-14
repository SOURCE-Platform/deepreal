# MECH-FIT-05 optical and NXP package corrections

The private review removes the sleeve obstruction at the Face depth window,
restores normal board and USB materials, and replaces the inherited U1/U6/U7
packages with source-backed footprint proposals. **The assembly still fails
USB fit, and the PCB is not electrically or manufacturing complete.** These
corrections have not been applied to the canonical CAD or website.

## Sleeve correction

The pale crescent was real geometry:
`R35_Face_Outer_Drum_Wall_Sleeve_ENV`, not a lens or reflection. A 9 mm bore
matching the existing depth opening now passes through that sleeve. Only the
sleeve geometry changes from the retained MECH-FIT-04 installed model; the
other 601 geometry objects remain unchanged in the optical candidate.

The corrected sleeve is closed and connected. It retains 95.200593% of its
nominal volume and the measured nominal overlaps with its support objects.
Those overlaps do not prove an attachment method, adequate stiffness or
strength. Removing the obstruction does not qualify the sleeve's load path.

Each of the ten nominal openings was screened with 197 normal rays. No
unexpected structural blockers remain. The four camera openings each retain
12 hits at their existing retaining-baffle edges; the six other openings have
zero hits. Separate 221-ray RGB cone screens at 66° × 41° for Face and
102° × 67° for Interaction find no unexpected structure. These use placeholder
pupils and explicitly excluded optical surfaces, not selected lens prescriptions.
They do not establish actual field of view, IR performance or projector safety.

The latest depth-window render shows the obstructing crescent removed.
J1 and the substrate now use their source materials, not collision red.
Changing those materials does not clear any recorded USB intersection.

## Manufacturer evidence and private footprints

Official NXP China downloads recovered the selected package evidence missing
from the earlier checkpoint. The source PDFs, embedded workbook and compiled
evidence are hash-bound in `nxp-proposal-04/nxp-package-evidence.json`.

| Reference | Selected part and package | Checked source geometry |
| --- | --- | --- |
| U1 | MIMX9596CVTXNAC, SOT2251-1 | 548 balls, 0.5 mm pitch, 15 × 15 mm body, 1.584 mm maximum height |
| U6 | MPF5302BVNAAEP, SOT2283-1 | 24 terminals in 16 copper regions, 3.6 × 4.6 × 0.8 mm maximum body |
| U7 | MPF5301BVNABEP, SOT2283-1 | Same selected B-variant package as U6 |

U1 uses IMX95IEC Rev 8, page 115, drawing 98ASA02029D revision A, and the
embedded 15 mm ball-map workbook. All 548 coordinates agree with its independent
board grid. Functions agree at 547 balls. At AF22, the coordinate list says
`VDD_EARC_1P8` and the grid says `VDD_AUD_1P8`. The proposal records
`UNRESOLVED_AF22` and assigns no net. SOT2021-1 is a different package and is
not used as evidence for the selected processor.

The PF53 Rev 7 ordering table selects SOT2283-1 for these B variants, not
SOT2090-1. Its page 156 figure caption disagrees with the ordering table and
drawing title block; that discrepancy remains recorded. The SOT2283-1 drawing
supplies the transported copper contours and terminal positions.

These are **private footprint proposals, not qualified production libraries**:

- U1's 0.28 mm copper and 0.33 mm mask diameters interpret the embedded
  `FC_BGA_330_280` name. Its vendor land definition remains unverified.
- PF53 uses a provisional 0.05 mm isotropic mask opening, not the separately
  dimensioned vendor mask pattern.
- No F.Paste apertures were generated for these three replacements. Stencil
  design and assembly-process qualification remain open.
- The three new 3D bodies are maximum bounding envelopes, not detailed
  manufacturer CAD. Other inherited package substitutions remain unqualified.

MECH-FIT-05 changes only U1/U6/U7 source footprint blocks. Reference, value,
UUID and placement remain fixed. All other root blocks and 2,030 pad
primitives outside those packages are unchanged. The board retains
238 footprints and now has 2,626 pad primitives. Package-07 and package-08
produce byte-identical PCB files.

Four local nets record manufacturer-defined shared copper functions:
`PACKAGE_U6_PGND`, `PACKAGE_U6_LX`, `PACKAGE_U7_PGND` and `PACKAGE_U7_LX`.
They cover 22 pads, with no inter-package or external circuit assignment.
The board is therefore no longer net-free, but it still has no system
netlist, tracks, vias or zones. These aliases do not establish circuitry.

## Checks and unresolved fit

The regression suites pass 109 tests: 50 CAD, 23 geometry/provenance guards,
four registration, nine optical, 14 NXP and nine independent saved-assembly
tests. Four nominal-solid self-tests also pass. Seven new Python files parse.
All 291 protected input hashes remain unchanged, and both repositories pass
`git diff --check`.

The saved standalone and installed models preserve all 240 board mesh
identities and the 231 component bodies outside U1/U6/U7. The final board has
391,441 source vertices. Maximum rigid-registration error is 0.000004657 mm;
the GLB round-trip error is 0.000003824 mm. The assembly retains the corrected
optical predecessor's 365 non-candidate geometry objects. There are zero
positive component-body box overlaps on the standalone board.

The nominal rest screen compares 235 candidate solids with 115 mechanical
objects. It retains the same four positive intersections as MECH-FIT-04:

| Candidate | Retained model | Intersection, mm³ |
| --- | --- | ---: |
| Substrate | USB plug overmold | 7.874741 |
| J1 | USB male shell | 34.602028 |
| J1 | USB male insert | 56.725520 |
| J1 | USB male tongue | 3.313073 |

There are also 445 open-geometry pair results and one unresolved Boolean
topology result. These are neither proven clashes nor clearance passes.
Open enclosure/rear-tray surfaces and the fixed harness proxy still prevent
a complete occupied-volume conclusion.

Face was sampled at 19 rigid poses from −45° to 45°; Interaction at ten poses
from 0° to 45°, both in 5° increments. Neither sampled group produced positive
board/body box candidates, and all matrices restored exactly. This is not a
continuous sweep, minimum-clearance analysis or dynamic-flex qualification.

Package-07 DRC **fails**, exit code 5, with **496 total findings:
373 errors and 123 warnings**. The report contains 494 violations
(371 errors, 123 warnings), plus two unconnected-item errors. The latter are
U6 pad 20 to pad 24 and U7 pad 20 to pad 24, the separate local PGND regions
that still require circuit routing. Five inherited ignored checks remain
identical to MECH-FIT-04; no new suppression was added. `--severity-all`
does not enable ignored checks.

## Next engineering gates

1. Resolve USB part, board thickness and true mating datums together. J1
   remains the inherited Amphenol, not the intended Hirose CX90M3-24P.
   Hirose recommends at most 0.8 mm PCB thickness; KiCad declares 1.6 mm,
   the native substrate measures 1.509994 mm and mechanics propose 1.5 mm.
   A supported local treatment, compatible part or separate connector board
   requires engineering evidence, not a cosmetic relocation.
2. Resolve AF22, vendor lands/mask/stencils and the remaining package and
   connector selections, including AS5600L, FH26/FH26W and the tall headers.
3. Engineer closed enclosure/shield solids, harness routing, insulation,
   latch/tool access, support attachments and dynamic flex. Qualify real
   optics and structural loads.
4. Capture system circuits, power sequencing, FPGA/DDR constraints and clock
   distribution; then establish stack-up, routing and fabrication checks.

## Review files

All paths below are relative to
`tmp/assembly-corrections-2026-10-14/` in the repository root:

- PCB: `package-07/deepreal-main-pcba-mech-fit-05.kicad_pcb`
- Source evidence: `nxp-proposal-04/nxp-package-evidence.json`
- Optical audit: `optical-04/optical-clearance-audit.json`
- Standalone: `model-03/deepreal-mech-fit-05-board.blend`
- Installed: `model-03/deepreal-assembly-corrections-review.blend`
- Fit/transport audit: `model-03/corrections-review-audit.json`
- Renders: `model-03/board-top.png`, `model-03/board-bottom.png`,
  `model-03/installed-cutaway.png`, `model-03/depth-window-detail.png`
- Final integrity record: `validation-model-03-final.json`

Earlier attempts remain as history. Optical-03 images precede the complete
normal-material fix; optical-04 and final model-03 supersede them.
The installed cutaway hides enclosing parts for inspection without moving or
resizing them. Fabrication, public visual release and viewer integration
permissions remain false. No website update, commit, push or deployment was made.
