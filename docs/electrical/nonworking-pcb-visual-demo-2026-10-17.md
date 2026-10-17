# Nonworking PCB visual demo

Status: `SUPERSEDED_FRONT_BACK_PRESENTATION_DEFECT`

The original readiness assessment was premature. Subsequent review found that
the illustrative front/back trace surfaces were swapped relative to the chip
bodies. The records below describe the original pass, not acceptance of its
visual correctness. The corrected presentation pass is recorded in
`pcb-presentation-polish-2026-10-17.md`. Original engineering assets were not damaged.

The user clarified that the 48-hour deliverable is a believable, explicitly
nonworking visual PCB demo, not a functional routed board. This checkpoint
records that separate demo. It does not advance electrical release gates.

## View it

Open `http://localhost:3001/deepreal/assembly-review`, select **Main board**, then
**Inspect demo routing**. **Flip board** shows the other surface.
**Show engineering board** hides the illustrative overlay and restores the
original partial-routing review.

The disclosure remains visible in both standalone and installed board views:

> Nonworking PCB demo. Illustrative routing, not electrically validated.

## Scope

- Added 272 geometry-selected illustrative connections, comprising 1,728 trace
  segments and 255 vias, to a separate private KiCad copy.
- Rendered matching front/back copper, via rings and hole discs as six merged
  Three.js meshes over the unchanged v7 engineering GLB.
- Kept existing component placement, USB geometry and the original engineering
  assets unchanged. The engineering review remains 163 segments, 41 vias and
  five zones. Canonical electrical routing is not completed by this demo.
- Left 426 unsuccessful visual-routing attempts in the build report. These are
  heuristic attempts, not an electrical unconnected-net count.
- Started additions unassigned. KiCad inferred existing net labels on 14
  illustrative segments and two vias during native serialization. Those labels
  are not verified signal assignments.
- Exposed demo copper above the rendered solder mask for visibility. This is
  not a manufacturing solder-mask definition.

No functional connectivity, pin mapping, DRC acceptance, signal integrity,
current capacity, fabrication readiness or complete pad coverage is claimed.
The demo remains development-only. No commit, deployment or release occurred.

## Artifacts and preservation

- Native copy: `tmp/pcb-visual-demo-2026-10-17/candidate-01/nonworking-visual-routing-demo.kicad_pcb`
- Viewer data: `blender/review-output/web/pcb-visual-demo-01/visual-routing-demo.json`
- Evidence: `tmp/pcb-visual-demo-2026-10-17/`
- Source board SHA-256: `51f3bec8d1b0885a5ee136b3b1fc5c9391d1f12ed878cb9be424826a71864c7a`
- Unchanged base GLB SHA-256: `d9675b1317e6e4db468a751ab4fca5fe21e01bbe8af47591feca6b6e62cbc686`
- Demo data SHA-256: `f5d19ca2ac9cdc8734144411bcb69abce3f076bc528f94dcd08f965e4ee15891`

Of 1,252 protected preexisting inputs, 1,251 are byte-identical. The sole
intended change is the website scene integration. No protected input is missing
and no unrelated protected input changed.

## Validation

- Seven Python geometry tests and 58 viewer/USB/camera/control tests passed.
- Changed-file ESLint, scoped viewer TypeScript and Python syntax checks passed.
- Native round-trip checks preserved all 263 footprint poses, pads and library
  IDs, plus every original track/via UUID, geometry and net name. Added geometry
  matches the JSON within 0.00000101 mm, allowing native coordinate truncation.
- Actual local API: HTTP 200, `private, no-store`, matching response data.
  Production denial and no-read behavior passed isolated tests, not a deployment.
- Ten actual WebGL canvas captures cover desktop, mobile, both board surfaces,
  installed views and the engineering toggle. Disclosure and control bounds
  were checked separately in the DOM; no viewport overflow or browser errors
  were reported.
- Embedded desktop CDP pointer clicks did not activate inspection reliably.
  Browser checks therefore used DOM button activation. Whole-page screenshot
  capture timed out; the recorded images are direct WebGL canvas exports.
- The visitor-copy audit found no hard, structural or silhouette defects.
  A repetition advisory was retained because repeated control labels and
  disclosure terms have specific meanings.
- A previous full-site TypeScript run failed in unrelated marked, Leva,
  thoughts and scroll-area code. Only the scoped viewer check is green.

Electrical DRC and fabrication checks were intentionally not run for this
geometry-only demo. All existing electrical integration blockers remain open.
