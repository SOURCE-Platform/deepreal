# DeepReal Electrical Capture Status v0.1

| Field | Value |
| --- | --- |
| Date | 12 September 2026 |
| Main board | 90 x 28 x 1.6 mm |
| Electrical designs | Main PCBA plus one reusable optical-head carrier |
| EDA state | KiCad project and 15-page hierarchy exist; circuits and vendor pin maps remain incomplete |
| 3D synchronization | Shared placement and visual-copper contract mechanically validated |
| Presentation state | Production-intent KiCad/Blender visualization complete; not for fabrication |

## Generated in this pass

The main-board package now contains a 15-page schematic plan, a 46-row component
register, 49 named net/power groups, the complete 51-contact-per-drum functional
allocation, page-level circuit requirements and a list of twelve pin-map/verification
gates. The optical-head package contains nineteen component groups, twenty-two named
nets and a separate circuit specification for sensors, rails, projector and local
fail-safe control.

The Blender population was then changed to match those decisions:

- two 6 x 6 mm LIFCL-17 devices, one per drum;
- two 51-position optical-head connectors rather than four camera connectors;
- separate TPS56637 system and motor converters;
- DRV8213 motor drivers and AS5600L absolute-angle sensors;
- no projector drivers on the stationary main board;
- a 2.0 mm visible assembly gap between the 15 mm i.MX95 body and LPDDR body;
- two combined optical-head flex routes plus two separate motor/encoder harnesses.

The updated model has 201 modeled component bodies. Automated checks report a
6.06 mm populated board stack inside the 15 mm target envelope, no major-package or
component-body overlap, correct seating on the board, no mounting-hole intrusion,
and collision-free shield, cable, support, thermal and sampled drum-travel geometry.

The presentation derivative adds 99 engineering-informed visual trace paths, 81
visual vias, 10 test pads and four masked copper regions. KiCad and Blender consume
the same tool-neutral coordinate data. This artwork is deliberately separated from
the canonical placement-only KiCad board.

## What is not generated

- No completed or independently checked circuit pages or audited symbol library.
- No vendor-audited 548-ball i.MX95, 200-ball LPDDR4X, 153-ball eMMC or 121-ball
  FPGA pin mapping.
- No ERC-clean exported netlist.
- No NXP DDR-tool output or Lattice Radiant pin/timing report.
- No fabricator stack-up, fully legal footprints, electrically connected vias,
  copper planes or netlist-derived routed traces. The visual derivative is not an
  exception to this manufacturing gate.
- No dynamic-flex impedance/fatigue report, SI/PI result, thermal test, EMC result,
  USB compliance result or eye-safety certification.
- No Gerbers, drills, pick-and-place, assembly drawing or production BOM.

## Current size conclusion

The 90 x 28 mm board is still credible enough to continue. The present 3D population
fits with substantial projected open area and the mechanical validators pass. This
does not prove routeability: the remaining decisive tests are BGA escape, DDR routing,
the two FPGA pin assignments and the six MIPI corridors. A board-size claim becomes
high confidence only after preliminary placement and routing in a real EDA tool.

## Known integration issue

The board-level validator still reports the modeled USB-C receptacle center 41.1 mm
away from the housing USB opening center. This is currently a model-integration
warning rather than a board-body collision, but it must be reconciled before the
housing/PCBA arrangement is presented as mechanically final.

## Presentation release status

The board may be published using the caption **DeepReal Main PCBA —
production-intent engineering visualization**. It must not be called final,
electrically routed, validated or manufacturing-ready. The visualization KiCad file
must never be exported as Gerbers.

## Next manufacturing gate

Install or select the project EDA environment, import the official manufacturer
symbols/footprints, and capture pages 2-4 and 13-15 first. In parallel, obtain the
restricted or vendor-controlled BGA pin data and run the FPGA and DDR tool passes.
Only then should the illustrative marketing copper be replaced by an actual
placement/routing export.
