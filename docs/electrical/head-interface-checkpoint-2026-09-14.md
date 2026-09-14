# Two-drum interface checkpoint

Status: **internal engineering investigation; not interface approval or a website asset.**

This extends the [native import checkpoint](native-pcba-import-checkpoint.md).
It does not replace the canonical KiCad board. No connector was moved, no net
was assigned, no new head PCB was claimed, and no schematic gate was passed.

## What is now established

The selected Hirose FH26W-51S-0.3SHW(97) body is **16.8 x 3.2 x 1.0 mm**.
The **15.6 mm** dimension belongs to the recommended FPC end width. The old
Blender metadata and optical-head component register conflated the two; both
are corrected. Native KiCad models continue to control visible geometry.

The manufacturer catalog is archived at
`references/components/datasheets/hirose-fh26-D49355-en.pdf`, with the URL,
revision text, retrieval date and SHA-256 in `head-interface-evidence.json`.
The cover identifies May 2017 revision 3; the downloaded footer says August
2026. A regenerated website footer is not proof of a new technical revision.

Catalog pages 6-9 distinguish the body, PCB land pattern and flex end. The
inherited footprint's copper **dimension subset** matches the catalog:
26 longer lands, 25 shorter lands, staggered 0.6 mm rows, 15.0/14.4 mm row
spans, 2.875 mm row-center separation, and two retention lands. Its F.Fab
long-axis extent also measures 16.8 mm. Therefore the generic FH26 filename
alone is **not** evidence that all its copper geometry is wrong.

This is not a complete footprint approval. Exact pin-one numbering, reflection,
retention-land alignment, solder mask, stencil apertures, selected-part 3D
geometry and mating orientation remain to be audited. Page 8 specifies reduced
paste openings; an inherited pad with F.Paste enabled is not proof these exist.

Page 2 permits PCB patterns beneath the connector's molded body. Consequently
"any trace under a connector is illegal" would be an incorrect general rule.
Real pad clearance, net ownership, insulation, assembly and signal-integrity
rules govern routing. No illustrative copper is added here.

## Placement experiment: a quarter-turn is insufficient

The actual KiCad courtyard of each connector extends **6.895 mm** past the
board's lower edge. This is courtyard overhang, not a measurement of plastic.
At rotation zero, the footprint's long axis runs along KiCad Y.

The read-only experiment tries both +90 and -90 degrees, preserving each X
coordinate and moving Y from 46 to 45 mm. All four trial courtyards fit the
board outline, but still produce same-side overlap candidates:

| Trial | Nearby courtyard candidates at either rotation |
|---|---|
| Face J2 | U2, U21, C74, C81, C82, C93 |
| Interaction J3 | U3, U22, C79, C86, C87 |

These are conservative axis-aligned bounding-box checks, not native polygon
DRC or a full mechanical verdict. The footprint remains unapproved, and the
experiment omits shield, latch, flex insertion, drum movement and pin routing.
It establishes that simply turning the connectors cannot be accepted as the
completed fix. Camera FPGA, connector, protection, head-power parts and their
support components need a coordinated layout after the physical interfaces
and legal FPGA pins are known. Empty space alone is not an approved corridor.

The generated comparison image is
`hardware/electronics/deepreal-main-pcba/generated-review/head-connector-review.png`.
It shows current geometry and a labeled trial, not a new design revision.

## Two head boards and their connections

- Main-board J2 connects to J1 on the face head; main-board J3 connects to J1
  on the interaction head. The intention remains one reusable head design
  assembled twice. Reference J1 is local to each board, not a shared connector.
- Each head carries an RGB assembly, IR sensor, their local supply circuitry,
  and the projector driver, pulse storage, sensing and hardware interlock.
  Existing blank Blender slabs are not a completed head PCB design.
- Each flex needs six candidate CSI-2 differential pairs: RGB clock plus two
  RGB data pairs, and IR clock plus two IR data pairs. That is twelve signal
  contacts, before grounds, supply and control.
- The allocation totals 51 contacts, but all 16 groups still lack physical pin
  numbers and end-to-end continuity approval. No pins are assigned by this audit.
- The stationary angle-sensor/encoder-board question is separate. These are not
  automatically part of the rotating optical-head circuit; proximity to the
  magnet and full motion geometry still determine that architecture.

## Power and motion are still open

Page 4 rates a contact at 0.2 A and applies 70% when all contacts carry current.
For the present eight supply plus eight dedicated return contacts, the ideal
equal-sharing rating sum is 1.6 A. Conservatively applying the 70% factor gives
**1.12 A per head**, or 3.696 W at 3.3 V before losses. This is a numerical
screen, not approved cable capacity or proof the head fits its power budget.
Whether the all-contact condition applies to this mixed loading, additional
thermal derating, unequal sharing, contact faults, flex resistance and voltage
drop require review. The unknown load is never treated as zero.

The projector's 700 mA output pulse is not the head's 3.3 V input current.
Sensor startup, conversion efficiency, simultaneous RGB/IR activity, local
pulse storage and recharge current must enter the input budget. A local pulse
capacitor does not make the supply-current question disappear.

The specified 0.2 +/- 0.03 mm mating thickness refers to the connector end,
including its construction; it does not prescribe the flexible moving section.
The catalog's ten insertion/withdrawal cycles are **connector mating durability**,
not ten drum movements and not a flex-fatigue qualification.

The next decisions are the exact connector contact-side/orientation drawing,
flat-flex continuity and mechanical entry corridor, followed by a traceable head
load budget. If current capacity or dynamic-flex routing fails, compare separate
power/control and camera connections before committing the main-board layout.

## Implemented safeguards and reproduction

`validate_flex_interface.py` now archives a read-only interface report covering
both head instances, six camera pairs, connector current arithmetic, catalog
pad dimensions, actual courtyard overhang, rotation trials and nine explicitly
open evidence categories. Its normal success means the audit ran truthfully;
`--require-ready` fails while the interface is unapproved. Eleven regression
tests cover source tampering, omitted evidence, missing camera clocks, return
contact limits, wrong pads, rotation direction and non-mutating trials.

Run from the repository root:

```sh
python3 hardware/electronics/deepreal-main-pcba/scripts/validate_flex_interface.py
python3 hardware/electronics/deepreal-main-pcba/scripts/test_head_interface.py
# Use a Python environment with Pillow; provide --font on non-macOS hosts.
python3 hardware/electronics/deepreal-main-pcba/scripts/render_head_connector_review.py
```

The board, electrical netlist and native Blender assembly remain unchanged in
this checkpoint. No new presentation render, physical validation, specialist
sign-off, manufacturing data or approved public asset was generated.
