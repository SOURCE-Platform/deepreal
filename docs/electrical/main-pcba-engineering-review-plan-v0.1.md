# DeepReal Main PCBA Engineering Review Plan v0.1

| Field | Value |
| --- | --- |
| Status | Active implementation plan |
| Immediate deliverable | Complete digital engineering-review draft |
| Public deliverable | KiCad-derived pre-fabrication visualization |
| Fabrication | Prohibited in this phase |

## Implementation checkpoint — 13 September 2026

Completed controls and evidence:

- G0 and G1 are passed with the historical concepts frozen, public rendering
  blocked, and measurable requirements recorded.
- All 39 registered major references have evidence-tracker coverage; zero rows are
  falsely marked audited or approved.
- The four-camera payload and margin calculation is machine checked. It rejects a
  main-board no-FPGA topology unless aggregation moves elsewhere, but does not yet
  choose one versus two FPGAs.
- The 41.1 mm USB-C mismatch is measured and documented with three candidate
  mechanical solutions.
- A ten-layer intent model exists, but it deliberately contains no invented
  dielectric or impedance geometry and does not authorize routing.
- The canonical KiCad export contains the exact 90 x 28 x 1.6 mm outline, 238
  footprints, 2,313 pads, 52 drilled pads/holes, and zero real tracks, vias, or
  zones.
- Blender now consumes canonical KiCad placement data and will build visible
  tracks/vias only from that export. The handmade copper path is disconnected from
  the active scene build.
- Automated checks enforce gate dependencies, sheet completeness, release locks,
  evidence coverage, bandwidth arithmetic, coordinate round trips, and the absence
  of fabrication outputs.

Current blocking facts:

- the selected FPGA topology has no legal Radiant compile, pin assignment, timing,
  resource, or power report;
- the i.MX95, LPDDR4X, eMMC, and several other symbols/footprints are not audited;
- the USB/enclosure geometry and 51-contact dynamic flex are unresolved;
- all 14 functional child sheets remain note-only, so no approved netlist exists;
- the stack-up has not been reviewed by an HDI fabricator or PCB specialist;
- pin-driven placement and routing therefore have not started.

## Dependency order

```text
requirements -> verified sources -> camera/FPGA decision
             -> mechanical + head/flex closure
             -> schematic + netlist -> stack-up rules
             -> pin-driven placement -> critical routing
             -> size decision -> complete review layout
             -> KiCad export -> Blender QA -> publication
```

`design-status.json` is the authoritative gate record. A downstream gate cannot pass
until every listed dependency passes and its evidence exists.

## Gates

| Gate | Deliverable | Required exit evidence |
| --- | --- | --- |
| G0 | Superseded concept frozen | Publication lock and artifact classification |
| G1 | Requirements baseline | Approved camera, power, safety and mechanical requirements |
| G2 | Verified component library | Exact parts, symbols, footprints, pin sources and audit |
| G3 | Camera/FPGA architecture | Zero/one/two comparison plus legal compile/timing evidence |
| G4 | Mechanical geometry | USB, mounts, shield, thermal, flex and height closure |
| G5 | Head/flex interface | Head schematic, loads, pinout and flex feasibility |
| G6 | Schematic/netlist | Populated 15-sheet schematic, audit, ERC and netlist |
| G7 | Stack-up/rules | Fabricator-informed layers, vias, impedance and net classes |
| G8 | Placement | Pin-driven orientations, exact courtyards and mechanical review |
| G9 | Critical routing/size | DDR, MIPI, USB, storage and power routes plus size decision |
| G10 | Complete review draft | All intended nets routed; ERC/DRC and open-issue package |
| G11 | Visualization/release | Exact KiCad export, Blender QA and approved pre-fab wording |

## Work that may run in parallel

After G1, these can proceed together:

- official symbol, footprint and component evidence acquisition;
- FPGA topology projects and bandwidth analysis;
- enclosure/USB/thermal coordinate closure;
- optical-head and flex definition;
- low-risk USB, power, motor and miscellaneous schematic capture.

High-speed placement cannot start until those workstreams converge. Full routing
cannot start until the netlist, preliminary stack-up and critical constraints exist.

## Decision rules

- Support all four RGB/IR streams simultaneously with 25% link margin.
- Select the simplest FPGA topology that passes legal pin, timing, routing, power
  and failure-containment requirements; require 20% implementation margin.
- Treat 90 x 28 mm as the first candidate, not a promise.
- Correctness and margin outrank size; size outranks cost.
- Reopen the owning gate when a selected part, sensor mode, connector, flex,
  enclosure interface or stack-up changes.
- Never invent inaccessible pins, suppress unexplained rule errors, or use visual
  copper to conceal failed routing.

## Digital review completion

The immediate program is complete only when:

- all schematic sheets contain real circuits;
- official major-device pin maps and footprints are audited;
- the selected FPGA topology has compile and timing evidence;
- critical and remaining intended nets are routed in canonical KiCad;
- ERC/DRC and completeness checks have no unexplained failures;
- the board-size report explains every material empty or congested region;
- Blender consumes the canonical KiCad export without manual trace geometry;
- public assets are visually clean and explicitly pre-fabrication;
- no fabrication outputs exist.

Physical prototypes, bring-up, compliance and production release remain a later
program and require specialist approval.
