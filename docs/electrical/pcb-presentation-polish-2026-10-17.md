# PCB presentation correction

Status: `PCB_PRESENTATION_POLISH_REVIEWED_LOCAL_ONLY`

This is a nonworking presentation model. The electrical design remains
incomplete. Generic package geometry, illustrative routing and presentation
cleanup do not establish a working or manufacturable circuit.

## Corrections

- Corrected the illustrative F.Cu/B.Cu display surfaces. Front traces now sit
  next to front-side components; back traces sit next to U15 and other back-side
  components. The original rendering incorrectly reversed those surfaces.
- Checked the mapping against actual solder-mask geometry in the protected
  engineering GLB, independently of the demo constants. The old swapped mapping
  is explicitly rejected.
- Added 17 generic beveled package bodies, 1,404 footprint-derived contacts and
  pin-one markers. BGA contacts sit under bodies; leadless-package contacts use
  the source pad locations. Body XY envelopes and outer heights remain fixed.
- Omitted 16 tiny source marker pads from rendered solder contacts rather than
  depicting them as real package terminals.
- Gave normal views a mask-covered trace appearance. The inspection view
  highlights illustrative copper without changing the installed view.
- Hid four large board annotations that crossed parts or described internal
  layout bookkeeping. This is presentation-only filtering. The persistent
  nonworking disclosure remains visible; engineering mode restores the
  original silkscreen and original component bodies.
- Expanded the inspection region to include the processor, storage and nearby
  camera-bridge area together.

## Scope and evidence

The illustration retains 272 geometric connections, 1,728 segments and 255 vias.
Of those connections, 81 are chip-to-via escape paths, not complete connections
to another component. No extra electrical completion is claimed.

The data is `blender/review-output/web/pcb-visual-demo-02-r2/visual-routing-demo.json`,
SHA-256 `497e060fb2e7b7b5400e612a5637efa29553e3f6fc4154c13f133fb389b5b331`.
Build and browser evidence is in `tmp/pcb-presentation-polish-2026-10-17/`.
The source builder is
`hardware/electronics/deepreal-main-pcba/scripts/build_pcb_presentation_demo.py`.

The earlier checkpoint is marked superseded. Its passing tests did not
establish physical chip-to-trace side correspondence.

## Validation

- 62 viewer, PCB, USB, camera and control tests passed, including four new
  tests for endpoint termination, physical side registration, presentation
  contacts/toggle behavior and nondestructive silkscreen filtering.
- The actual engineering GLB passed side checks for 138 component references
  used by single-sided demo endpoints. All 463 source endpoint-pad records
  passed geometry validation. Path ends require a source pad on the same layer
  or a via, rather than an unexplained free endpoint.
- Checked 548 original rendered mesh position buffers for preservation.
  Presentation-mode replacement does not edit those buffers or the original GLB.
- Reviewed ten final desktop/mobile front/back/installed captures, with
  additional normal and oblique inspections. The disclosure and control bounds
  were checked in the DOM. Captures are direct WebGL canvas exports, not
  whole-page screenshots.
- A trusted pointer click successfully switched from inspection to whole-board
  view. Mouse orbit, flip, engineering restore and independent installed-view
  materials/visibility were also checked. Browser errors were empty.
- Changed-file ESLint, scoped viewer TypeScript and Python syntax checks passed.
  The broader site TypeScript check was not rerun; earlier unrelated marked,
  Leva, thoughts and scroll-area failures are not fixed by this work.
- Actual local API/hash checks and isolated production no-read/404 guards
  passed. Production was not deployed or exercised as a server.
- Copy scans found no hard, structural or silhouette defects. Readability
  advisories were retained for short control labels and necessary repeated
  technical disclosure terms.

The canonical schematic, engineering board, prior demo data and protected v7
GLB remain unchanged. No commit, deployment or fabrication submission occurred.

## Remaining limits

These are representative package models, not qualified manufacturer CAD.
Part selection, complete signal assignments, electrical behavior, timing,
power, clearances and fabrication remain engineering work. This pass corrects
the known visual contradictions; it is not independent hardware-advisor
approval or a guarantee that further review will find no issues.
