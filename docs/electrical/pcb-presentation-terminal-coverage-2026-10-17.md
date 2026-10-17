# Presentation PCB terminal coverage, 2026-10-17

Status: `PCB_PRESENTATION_RC_COVERAGE_REVIEWED_LOCAL_ONLY`.

The presentation graph now accounts for both terminals of all 199 displayed
resistors and capacitors. This closes the previously reported R/C coverage gap,
not the complete board's electrical connectivity. IC functions, pin assignments,
voltages, values and circuit feasibility remain unverified.

## Connection map

| Scope | Parts | Terminals | Basis |
| --- | ---: | ---: | --- |
| Existing R/C study | 15 | 30 | Original native net and connected-track evidence |
| Proposed R/C presentation | 184 | 368 | Explicit, unverified visual networks |
| Additional inductors | 9 | 18 | Proposed filter-interface templates |
| Two-terminal TVS placeholder D9 | 1 | 2 | Proposed, unverified protected-node shunt |
| Total accounted two-terminal parts | 209 | 418 | Complete source-pad inventory for this scope |

The proposed R/C roles are generic bypass and bias templates based on placement.
They are not conclusions about the real parts' functions. Proposed IC interface
pads were selected for geometric access, not verified manufacturer pin functions.
The separate `CONCEPT_*` namespace does not modify the engineering net registry.

D9's source register identifies a VBUS TVS with part selection still open.
The final metadata corrects an earlier indicator label. Its proposed protected
node is not a verified connection to the actual `USB_VBUS` net.

Each proposed terminal records its real source footprint pad and side, outer
connection, via ID, through span, actual layer taps, target layer and connected
internal destination. The CSV includes the proposed interface pads and preserves
native-track evidence separately for the 15 original study parts.

Local artifacts:

- `blender/review-output/web/pcb-visual-demo-03-r2/visual-routing-demo.json`
- `blender/review-output/web/pcb-visual-demo-03-r2/connection-map.csv`
- `tmp/pcb-passive-coverage-2026-10-17/connection-plan-r3.json`
- `tmp/pcb-passive-coverage-2026-10-17/inputs.json`

## Routed representation

The v3 graph contains 514 outer connections, 917 outer segments, 243 internal
paths, 1,613 internal segments and 490 illustrative vias. It has two explicitly
modeled, connected return regions on layer indices 2 and 9. Each region comprises
2,658 raster rectangles, with clearance around unrelated source copper and
through barrels. These regions are diagram geometry, not KiCad zone fills.

Proposed internal paths:

| Layer index | Proposed use | Paths |
| --- | --- | ---: |
| 3 | Component interfaces | 10 |
| 4 | Local supply distribution | 105 |
| 7 | Local supply distribution | 88 |
| 8 | Bias interfaces | 40 |

All proposed terminals reach a declared interface through the path/return-region
graph. Return barrels join the two reference regions explicitly. The original
one-ended local routes and 81 unterminated package-escape stubs were retired.
Of 73 legacy illustrative bus connections, 44 passed the selected pad/copper
envelope check and were retained; 29 were retired. This is not a KiCad DRC result.

The display router uses a nominal 0.045 mm envelope gap. Its comparisons permit
numerical boundary contact at that minimum. This parameter, the proposed
0.30/0.15 mm via geometry and all routing widths are unapproved for manufacturing.
No drill aspect ratio, annular ring, impedance or fabrication rule is qualified.

## Viewer

The development viewer's **Show proposed inner layers** control opens a separate
diagram for indices 2 through 9. Layers 5 and 6 show existing study copper only;
no new connections are claimed there. Proposed connections use gold markers;
existing copper and pass-through markers are gray.

Layer indices follow the unapproved ten-layer intent. Diagram spacing is linear
and schematic, not a dielectric or fabrication stack. No stack definition was
added to a native board. The installed assembly remains a normal masked view,
independent of the standalone diagram and copper inspection.

The persistent disclosure remains:

> Nonworking PCB demo. Illustrative routing, not electrically validated.

The additional R/C caption explicitly says that proposed nets and IC pin
assignments are unverified. Engineering mode restores the original bodies,
silkscreen and scoped native routing.

## Verification

- 66 focused viewer tests and 11 Python geometry tests passed.
- Missing terminals, missing rendered parts, orphaned or falsely tapped vias,
  disconnected return regions, foreign-barrel plane contacts and false internal
  layer destinations are rejected.
- Independent source-inventory and graph audit covered all 418 accounted
  terminals, including the 398 R/C terminals.
- The presentation-envelope audit checked 2,530 trace segments and all 490 added
  barrels. It is not electrical or manufacturing DRC.
- Actual loaded GLB checks covered 227 component sides and independently matched
  all 199 R/C body references against the connection inventory.
- All 548 original mesh position buffers remained unchanged. The 17 inherited
  presentation packages retained their source XY extents and outer heights.
- Scoped TypeScript, changed-file ESLint, Python compilation and diff whitespace
  checks passed. Visitor-copy audit found no confirmed writing defects;
  technical-label repetition/readability advisories were retained deliberately.
- The 21-view desktop/mobile matrix covered both faces, all eight internal-layer
  diagrams, engineering restore and installed views. DOM control bounds and the
  disclosure were checked separately from actual WebGL canvas exports.
- The final `03-r2` revision changes metadata only. Its outer-route and layer-map
  position buffers were compared directly with the matrix's `03` geometry and
  are identical. D9's corrected TVS label and explicitly historical native
  annotations do not change the reviewed geometry.
- Trusted CDP clicks verified main-board, flip, inspection and the new layer
  control. Native select interaction changed layer 4 to 9 and returned to board
  surfaces. The MK1 passive-region crop retains its original canvas provenance.
- No browser runtime errors were observed.

Whole-site TypeScript and the earlier engineering suite were not rerun. This
scope uses the focused viewer checks; prior unrelated site errors and inherited
electrical/DRC limitations are not resolved by this work.

Evidence is under `tmp/pcb-passive-coverage-2026-10-17/`, including
`source-coverage-final.json`, `actual-model-validation.json`,
`browser-validation.json`, `live-api-validation.json`, `preservation-final.json`
and `final-validation.json`.

## Provenance and limits

- Data SHA-256:
  `2a8946514842553c47e36abb60fb8b8ae388de77621a8b6fd3c2020d08b8b570`
- Source engineering-review board SHA-256:
  `51f3bec8d1b0885a5ee136b3b1fc5c9391d1f12ed878cb9be424826a71864c7a`
- Unchanged base GLB SHA-256:
  `d9675b1317e6e4db468a751ab4fca5fe21e01bbe8af47591feca6b6e62cbc686`
- Serialized API response SHA-256:
  `471cbdfb9c77ff89e764ddf504eccc50e7a0112c17ab0a282d759a41e09488fc`

The response is reserialized JSON, so its byte hash can differ through newline
and number-format normalization. The endpoint checks the full
source hash, serves privately without caching and returns 404 without reading
the asset outside development.

There is **no matching native v3 PCB export**. The inherited `demo_board_sha256`
and native-inference annotation refer to the archived v1 illustrative study
only. V3 explicitly marks that hash historical and current native parity false.

The canonical schematic/PCB, engineering-review board and base GLB remain
unchanged. The preservation report separates the four intended existing viewer
file edits from unrelated concurrent SecureMonitor changes; those files were
not edited or reverted by this work.

This pass does not complete chip, connector, microphone or protection-array
pin coverage. It does not establish a working power tree, approved stack,
functional netlist, EMC/thermal performance, mechanical clearance or fabrication
readiness. No commit, deployment, public release or fabrication submission was
made.
