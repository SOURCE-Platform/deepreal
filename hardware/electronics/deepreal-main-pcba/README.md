# DeepReal Main PCBA Electrical Capture v0.1

| Field | Value |
| --- | --- |
| Board | Main PCBA |
| Target outline | 90 x 28 x 1.6 mm |
| Assembly | Two-sided, 10-layer HDI working assumption |
| Status | Capture source; vendor pin import and ERC not complete |
| Architecture baseline | `../../../docs/electrical/main-pcba-schematic-entry-spec-v0.1.md` |

## Capture sequence

1. Create the 15-sheet hierarchy in `sheet-plan.csv`.
2. Import manufacturer symbols and footprints listed in `pinmap-gates.csv`.
3. Apply the net names and ownership in `net-registry.csv`.
4. Capture the circuit requirements in `circuit-specification.md`.
5. Annotate, run ERC and export an independently reviewed PDF and netlist.
6. Perform the Lattice pin compile and NXP DDR-tool pass before placement is
   treated as routeable.

## Non-negotiable rules

- U1 and U4 package bodies cannot touch; keep a physical assembly gap and preserve
  an unobstructed DDR corridor.
- U2 belongs near J2 and U3 belongs near J3. Each FPGA feeds only its associated
  i.MX95 CSI receiver.
- Projector pulse drivers are not on this board. They are on the optical heads.
- `HEAD_*_3V3` is filtered and independently switchable for each head.
- `MOTOR_6V` remains disabled unless the accepted USB-PD contract is at least 9 V.
- Every projector-enable path is hardware-default-off and interrupted by the local
  lens-integrity loop.
- No marketing render may imply that illustrative surface tracks are routed copper.

## Current completion definition

This package closes architectural connectivity. Pin-level closure remains blocked
where the official i.MX95, LPDDR4X, eMMC or FPGA package data has not been imported
and verified in an EDA tool. See `pinmap-gates.csv` for the exact blockers.
