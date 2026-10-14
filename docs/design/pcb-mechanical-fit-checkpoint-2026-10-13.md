# PCB mechanical reconciliation, first pass, 2026-10-13

## Result and scope

`MECH-FIT-01` is a separate **outline and interface diagnosis**, not a corrected
component layout. The measured R36/R38 USB-wing profile now exists in a KiCad
candidate with the complete inherited population. No component, footprint,
model reference, pin number or electrical connection was changed.

The candidate is not integrated into Blender or the website. Full fit failed
screening, and the actual connector selections and interfaces remain open.
The website still shows the earlier mechanical illustration in All parts and
the known-clashes native snapshot separately in Main board.

## Shared interface record

`pcb-mechanical-interface-2026-10-13.json` records source hashes, coordinate
mapping, the actual mesh section, connector body envelopes and all 234 retained
native component-body boxes. R36 and R38 agree on the measured board and port
interfaces. The measurement opens the sources without saving them.

| Item | Measured target or inherited candidate |
| --- | --- |
| Board envelope | 102.5 × 28 × 1.5 mm |
| Existing electrical board thickness | 1.6 mm, unchanged and unapproved |
| Device board depth plane | Web Z = −11.35 mm |
| Fixed KiCad datum | X = 65, Y = 34 mm, the original core datum |
| USB socket envelope centre | Device X = 51.5, height = −17.6, depth = −14.125 mm |
| J2/J3 body-envelope centres | Device X = −22/+22, height = −23.5 mm |
| J4/J5 body-envelope centres | Device X = −34/+34, height = −23.5 mm |

The wing makes the outline's bounding-box centre move 6.25 mm. Downstream
exports must **not recenter all components around that new box**. The fixed
core datum preserves component and housing coordinates.

Connector-envelope centres are not footprint anchors. The USB envelope is
explicitly named `UNSELECTED` in the mechanical source and lies below the board
plane. An actual receptacle needs its own land-pattern datum, body transform,
mounting side, plug mating plane, retention and insertion-access checks.
The old September USB study's centred enclosure opening is not the measured
R38 port datum.

The section contains one six-corner outer profile and five circular cutouts.
Four cutouts match the existing H1–H4 drills and reuse them. The fifth,
at device X = 52, height = −5 mm, is copied as an unapproved mechanical
edge cutout. No pad, copper ring, plated hole or fastener is invented there.

## Candidate and checks

The generated candidate is:

`../../tmp/pcb-fit-candidate-2026-10-13/profile-03/deepreal-main-pcba-mech-fit-01.kicad_pcb`

Its sibling `engineering-layout-export.json` and `fit-screen.json` retain
source hashes, release locks and a fixed-origin instruction. The candidate
replaces only root-level `Edge.Cuts` drawings. All other PCB source blocks
remain byte-identical. KiCad parses the saved file and reproduces all
238 footprint descriptions and 2,313 pads exactly.

| Check | Result | Meaning |
| --- | --- | --- |
| KiCad outline bounds | 20, 20 to 122.5, 48 mm | The measured wing exists in KiCad coordinates |
| Footprint/pad preservation | 238 / 2,313, unchanged | No parts omitted to conceal conflicts |
| Retained native body inventory | 234, including 18 model envelopes | Full population screened, not exact package verification |
| Positive 3D body-box overlaps | 19 candidates | Conservative screen, not exact solid intersections |
| Same-side courtyard-box overlaps | 56 candidates | Assembly-clearance concerns remain |
| J2/J3 catalog dimension subset | Pass for both | 26/25 contact rows and two tabs match the retained evidence |
| Connector numbering, paste, model and mating audit | Open | Dimension agreement alone cannot approve orientation |
| Native standalone DRC | **Failed: 995 violations**, 735 errors and 260 warnings | No clearance or fabrication approval |
| Invalid-outline DRC findings | None | A valid outline does not make the populated board valid |
| Named pad nets / tracks / vias / zones | 0 / 0 / 0 / 0 | Electrical capture and routing are unfinished |
| New geometry/boundary tests | 20 pass | Profile extraction, source preservation and output locks |

DRC includes 56 courtyard-overlap violations. This standalone candidate does
not inherit the canonical project's ignored checks or custom project settings,
so its total is not an apples-to-apples comparison with earlier canonical DRC
counts. No errors were suppressed. Zero reported unconnected items is not
meaningful when pads have no named nets.

U20/U21 still have only 0.02 mm nominal body-box separation. Diagnostic J2/J3
quarter-turn trials, at the inherited anchor and 1 mm inward, remain unapplied:
the inherited-anchor trials overhang by 0.295 or 0.645 mm, and inward trials
clear that edge screen but overlap nearby capacitor/FPGA/head-power courtyards.
They do not establish contact-side, pin-one, latch or cable continuity.

The retained native source was measured, not rebuilt. Its pre-existing stale
design-status fingerprint and native-import guard are unchanged. The new
candidate has its own current source bindings; it does not waive that guard.

An annotated top/bottom diagnostic is retained at
`../../tmp/pcb-fit-candidate-2026-10-13/profile-03/fit-review-final.png`.
It plots body boxes and mechanical targets, not routed copper or finished
component models.

## Work required before integration

1. Reconcile the USB part with the working board thickness and below-board
   mating target. The named Hirose CX90M3-24P has a 0.8 mm maximum recommended
   PCB thickness, incompatible with both present candidates. Prefer researching
   a thickness-compatible USB 3.x receptacle before changing the board stack.
   Do not silently promote the inherited Amphenol substitute.
2. Complete the exact FH26W footprint/model and numbered contact-orientation
   audit. Define latch and insertion keepouts, then decide the actual J2/J3
   anchors rather than rotating viewer models.
3. Select real low-profile J4/J5 parts and land patterns. The current vertical
   pin headers are placeholders and extend beyond the board.
4. Resolve the package/library issues and capture the circuits needed to justify
   power, camera and memory placement. Several passives remain unconnected
   space claims; they must not be redistributed as decorative board fill.
5. Produce a complete-population fit candidate with actual interface evidence,
   then export it through Blender into the development viewer. Housing,
   plug-insertion, latch, cable and exact component clearances still need checks.
6. Finish the remaining schematic, architecture and stack-up decisions before
   real routing. Material and PCB-edge polish remains separate work.

Fabrication, publication and viewer-integration permissions remain false.
The canonical board/schematic, design gates, source Blender files and installed
viewer assets are unchanged. No commit, push or deployment was made.

## Reproduce

From the repository root, use new output paths. Both generators reject existing
outputs:

```sh
blender -b -t 4 --factory-startup --python-exit-code 1 \
  --python blender/measure_pcb_fit_interfaces.py -- \
  --output "$PWD/tmp/new-mechanical-interface.json"

'/Users/adam/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3' \
  hardware/electronics/deepreal-main-pcba/scripts/build_pcb_fit_candidate.py \
  --contract "$PWD/tmp/new-mechanical-interface.json" \
  --output-dir "$PWD/tmp/new-pcb-fit-candidate"

python3 -m unittest discover -s blender -p test_pcb_fit_geometry.py -v
python3 -m unittest discover \
  -s hardware/electronics/deepreal-main-pcba/scripts \
  -p test_pcb_fit_candidate.py -v
```

This local KiCad SWIG build loses typed pointers after drawing mutation.
The generator therefore preserves the source's S-expression blocks, replaces
only board-edge drawings, and validates the resulting file with KiCad. It
does not edit the baseline through a broken in-memory mutation path.
