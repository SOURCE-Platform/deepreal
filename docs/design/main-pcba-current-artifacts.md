# DeepReal PCBA - Current Artifact Index

| Field | Value |
| --- | --- |
| Updated | 13 September 2026 |
| Purpose | Separate current engineering inputs from historical visual studies |

## Current engineering inputs

These files should be used for the next schematic and 3D packaging pass:

1. `../electrical/main-pcba-schematic-entry-spec-v0.1.md` - authoritative
   pre-schematic architecture, exact baseline parts, partitions and validation gates.
2. `../electrical/main-pcba-rail-budget-v0.1.csv` - preliminary rail and peak-current
   requirements. Estimated rows must be replaced with measured or calculated values.
3. `../electrical/main-pcba-interface-map-v0.1.csv` - logical interfaces and routing
   classes.
4. `main-pcba-mechanical-bom-v0.2.csv` - historical dimensional and presentation
   metadata. It is no longer an engineering placement authority.
5. `../research/main-pcba-architecture-input-decisions-v0.1.md` - research rationale;
   retained for traceability but superseded where the entry spec differs.
6. `../../hardware/electronics/deepreal-main-pcba/` - current tool-neutral electrical
   capture source: 15-sheet plan, component register, named-net registry, connector
   allocation, circuit requirements and explicit vendor pin-map gates.
7. `../../hardware/electronics/deepreal-optical-head/` - reusable optical-head
   electrical capture source for the two identical rotating carrier assemblies.
8. `../electrical/main-pcba-schematic-capture-status-v0.1.md` - exact record of
   what the capture pass and synchronized Blender rebuild did and did not produce.
9. `../../hardware/electronics/deepreal-main-pcba/deepreal-main-pcba.kicad_pcb` -
   canonical 90 x 28 mm placement board; intentionally contains no decorative copper.
10. `../../hardware/electronics/deepreal-main-pcba/engineering-layout-export.json` -
    deterministic KiCad-to-Blender export containing current components, 2,313 pads,
    holes, and the presently empty real-copper categories.
11. `../../hardware/electronics/deepreal-main-pcba/design-status.json` and
    `engineering-review-manifest.json` - machine-readable gates, ownership, evidence,
    blockers, and publication/fabrication locks.
12. `main-pcba-usb-mechanical-options-v0.1.md` - measured 41.1 mm USB mismatch and
    the three mechanical closure options.

## Superseded presentation artifacts

Publication is paused. The listed renders and illustrative-copper KiCad board are
historical concept artifacts and are not approved for new investor, grant or website
use. Their copper does not come from a complete schematic or netlist.

1. `../../hardware/electronics/deepreal-main-pcba/deepreal-main-pcba-visual.kicad_pcb`
   - explicitly non-fabrication visualization derivative.
2. `../../blender/pcba_visual_layout.py` - tool-neutral visual trace, via, test-pad
   and masked-pour coordinates shared by KiCad and Blender.
3. `../../blender/deepreal.blend` and `../../blender/renders/` - generated Blender
   model and public render masters; rebuild from the source scripts.
4. `../../hardware/electronics/deepreal-main-pcba/renders/` - historical packaged
   KiCad and Blender PCBA views; none are currently approved for publication.

Replacement caption after the engineering release gate: **DeepReal Main PCBA —
engineering development visualization based on a pre-fabrication PCB layout**.

## Historical or visual-study inputs

These files remain useful as evidence of previous work, but are not the current
electrical baseline:

- `main-pcba-mechanical-bom-v0.1.csv` - the older one-FPGA/four-camera-connector BOM.
- `main-pcba-packaging-study-v0.1.md` - packaging study based on v0.1 mechanical
  assumptions.
- `../research/main-pcba-feasibility-v0.1.md` - early feasibility research.
- Superseded Blender renders without the shared visual-copper layer - historical
  presentation geometry, not a routed board derived from a schematic/netlist.

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

Until those items exist, the superseded board images remain paused. They must not be
shown as a current engineering visualization or described as final, electrically
routed or production-ready.
