# DeepReal PCBA - Current Artifact Index

| Field | Value |
| --- | --- |
| Updated | 12 September 2026 |
| Purpose | Separate current engineering inputs from historical visual studies |

## Current engineering inputs

These files should be used for the next schematic and 3D packaging pass:

1. `../electrical/main-pcba-schematic-entry-spec-v0.1.md` - authoritative
   pre-schematic architecture, exact baseline parts, partitions and validation gates.
2. `../electrical/main-pcba-rail-budget-v0.1.csv` - preliminary rail and peak-current
   requirements. Estimated rows must be replaced with measured or calculated values.
3. `../electrical/main-pcba-interface-map-v0.1.csv` - logical interfaces and routing
   classes.
4. `main-pcba-mechanical-bom-v0.2.csv` - current package population for the main
   board and the two internal optical-head carriers.
5. `../research/main-pcba-architecture-input-decisions-v0.1.md` - research rationale;
   retained for traceability but superseded where the entry spec differs.
6. `../../hardware/electronics/deepreal-main-pcba/` - current tool-neutral electrical
   capture source: 15-sheet plan, component register, named-net registry, connector
   allocation, circuit requirements and explicit vendor pin-map gates.
7. `../../hardware/electronics/deepreal-optical-head/` - reusable optical-head
   electrical capture source for the two identical rotating carrier assemblies.
8. `../electrical/main-pcba-schematic-capture-status-v0.1.md` - exact record of
   what the capture pass and synchronized Blender rebuild did and did not produce.

## Historical or visual-study inputs

These files remain useful as evidence of previous work, but are not the current
electrical baseline:

- `main-pcba-mechanical-bom-v0.1.csv` - the older one-FPGA/four-camera-connector BOM.
- `main-pcba-packaging-study-v0.1.md` - packaging study based on v0.1 mechanical
  assumptions.
- `../research/main-pcba-feasibility-v0.1.md` - early feasibility research.
- Existing Blender renders and the current Blender board - presentation geometry,
  not a routed board derived from a schematic/netlist.

## Not generated yet

- Checked EDA schematic, audited symbol library and exported netlist. Tool-neutral
  capture source now exists under `hardware/electronics/`, but it has not passed ERC.
- PCB footprints verified against every land-pattern drawing
- Routed copper, planes, vias and impedance-controlled stack-up
- FPGA Radiant project, pin assignment, timing report and power report
- NXP DDR tool output and DDR length constraints
- Dynamic-flex drawings and flex-vendor impedance/cycle-life report
- SI/PI, thermal, EMC, USB compliance or eye-safety test results
- Gerbers, drill files, pick-and-place, assembly drawings or production BOM

Until those items exist, the board can be shown as a preliminary engineering layout,
not as a final or production-ready PCB.
