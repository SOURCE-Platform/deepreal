# MECH-FIT-04 package correction and installed-fit review

The private candidate fixes D2 and the two mirrored backside labels. It also
places the detailed board in the retained R38 mechanics using the measured
core datum. **The nominal installed assembly is not fit-approved.** The USB
models intersect, and the open rear-shield and housing meshes prevent a
complete solid-clearance conclusion.

## Source changes

D2 now uses `Package_TO_SOT_SMD:Texas_DRT-3` for the selected TI
TPD2EUSB30ADRTR. The retained official TI datasheet identifies the three-pin
DRT package, its 1.0 × 0.8 mm nominal body and 0.5 mm maximum seating height.
The package audit records the drawing, library hash, pad numbering and exact
bottom-side registration. Pin functions are evidence only; no nets were added.
The KiCad library lands are not a manufacturer-qualified stencil or assembly
release.

Only D2's source block and the mirror flags of the two root B.SilkS labels
change from MECH-FIT-03. All other root blocks remain byte-identical. The
candidate retains 238 footprints and 2,412 pad primitives: 2,409 unchanged
primitives outside D2, plus its three new pads. Placement and board outline
remain unchanged.

Both official NXP download attempts remain recorded as HTTP 404 failures.
U1's generic 324-ball footprint was not guessed into the selected 548-ball
package. U6/U7 retain the inherited 4 × 4 mm QFN rather than an invented PF53
3.5 × 4.5 mm pad pattern. These and the other inherited substitutions still
block final package-fit approval.

## Native checks

- 77 source, geometry, provenance and Blender registration tests pass.
- Four separate solid-screen self-tests check overlap, containment, touching
  and separation.
- Repeated package builds produce identical PCB bytes. A fresh native parse
  agrees with all seven exported sections.
- Unsuppressed package-02 DRC **fails**, exit code 5: 500 findings,
  371 errors and 129 warnings. Categories are 340 clearance,
  29 drill-out-of-range, two copper-edge-clearance, 58 silk-over-copper,
  51 text-height, 17 silk-overlap and three silk-edge-clearance findings.
- The two backside mirror warnings are gone. DRC's zero unconnected items
  does not establish circuit completeness: the board still has no assigned
  pad nets, tracks, vias or zones.
- All 256 protected source, historical-model and site files remain unchanged.

## Installed diagnosis

The model retains 216 inherited native component bodies, 18 explicitly
representative envelopes and four hole-only footprints. Native pads,
silkscreen, mask and substrate are retained. There are zero positive
component-body box overlaps on the standalone board.

All 240 board meshes receive one rigid transform from the fixed `[65, 34]`
core datum, not the extended outline centre. No component is nudged to make
the enclosure look clear. The registration guard checks every mesh and
367,215 vertices. Maximum transform error is below 0.000005 mm.

The nominal rest screen compares 235 candidate bodies/substrate with 115
retained mechanical objects. It finds four positive, closed-output Boolean
intersections:

| Candidate | Retained model | Nominal intersection, mm³ |
| --- | --- | ---: |
| Board substrate | USB plug overmold | 7.874741 |
| J1 | USB male metal shell | 34.602028 |
| J1 | USB male internal insert | 56.725520 |
| J1 | USB male contact tongue | 3.313073 |

These are intersections of the retained nominal models, not a verified
plug/receptacle mating analysis. J1 is still the inherited Amphenol, not the
intended Hirose. Body centres are not mating datums. The intended Hirose's
board-thickness requirement remains unresolved.

There are also 445 open-geometry pair results and one unresolved J1/overmold
Boolean topology result. These are **not 446 proven clashes or clearance
passes**. Fifteen candidate bodies cross the open rear-tray surface, including
underside passives, U20/U22, MK1 and U17. The fixed harness proxy also crosses
the substrate surface. Exact occupied volumes cannot be certified from these
open meshes.

The screen uses a 0.00001 mm inspection-copy weld and a 0.00001 mm³ positive
volume threshold. It never repairs or changes retained CAD. Its broad phase
examines positive box overlaps, not minimum clearances; omitted pairs do not
receive tolerance-qualified clearance approval.

Face samples cover −45° to 45° in 5° steps, with 38 retained rigid objects.
Interaction samples cover 0° to 45°, with 35 rigid objects. Neither sampled
group has positive board/body box candidates. Source mechanical matrices
restore exactly after sampling. This is not a continuous sweep or a dynamic
flex result. Latch/tool access, cable deformation and fatigue, mounts,
microphone ports, thermal compression and insulation remain unqualified.

The nominal KiCad board thickness is 1.6 mm; the native substrate measures
1.509994 mm against the 1.5 mm mechanical proposal. Finished stack-up and
tolerances are still open.

## Review files and rejected history

Candidate:
`../../tmp/pcb-package-fit-2026-10-13/package-02/deepreal-main-pcba-mech-fit-04.kicad_pcb`

Standalone Blender:
`../../tmp/pcb-package-fit-2026-10-13/model-04/deepreal-mech-fit-04-board.blend`

Installed Blender:
`../../tmp/pcb-package-fit-2026-10-13/model-04/deepreal-mech-fit-04-installed-review.blend`

The model directory contains top/bottom board renders, an installed cutaway,
an installed diagnostic and a USB closeup. Cutaway visibility hides the housing,
shields, spreader and magnetic mount face; it does not withdraw or resize them.
Diagnostic red identifies J1 and the substrate edges. Installed relationships,
including intersections, remain in the saved model.

The native-to-review GLB round trip preserves all 240 mesh identities, with
maximum bidirectional vertex difference below 0.000004 mm. This validates
transport, not package selection or assembly fit.

Model-01 stopped during imported-object cleanup. Model-02's installed
measurements and images are **rejected**: appended Blender objects were
transformed before their world matrices were evaluated. Its reported J4/J5
thermal intersections and 51.5 mm USB displacement must not guide design.
Model-03 adds evaluated-world-matrix and whole-board registration guards.
Model-04 keeps that verified geometry and improves cutaway visibility,
lighting and the USB detail view. Failed and superseded outputs are retained.

Circuit capture, vendor pin maps, FPGA allocation/tool builds, DDR constraints,
power design, stack-up and routing remain open. Fabrication, public visual
release and viewer integration permissions remain false. No website update,
commit, push or deployment was made.
