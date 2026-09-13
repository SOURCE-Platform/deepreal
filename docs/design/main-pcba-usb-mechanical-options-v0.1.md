# DeepReal Main PCBA USB-C Mechanical Closure v0.1

| Field | Value |
| --- | --- |
| Status | Blocking option study; no geometry selected |
| Board candidate | 90 x 28 x 1.6 mm |
| Review date | 13 September 2026 |
| Fabrication | Not allowed |

## Measured contradiction

The current models describe two USB-C locations that cannot mate:

- The enclosure opening is centered at device X = 0 mm in `blender/usb_port.py`.
- Main-board receptacle J1 is centered at board/device X = 41.075 mm in
  `blender/pcba_bom.py`, near the right board edge.
- The resulting X offset is 41.075 mm, reported as 41.1 mm by
  `blender/validate_pcba.py`.

This is a real blocking issue, not a cosmetic discrepancy. A plug cannot pass through
the enclosure opening and enter the modeled board receptacle. The current opening and
J1 placement are concept coordinates; neither is approved engineering geometry.

There is also a board-thickness conflict. Hirose currently lists 0.8 mm maximum as
the recommended PCB thickness for CX90M3-24P, while the main-board candidate is
1.6 mm. The connector cannot remain selected merely because its 3D body looks right.
The electrical/mechanical team must either prove a supported local board treatment,
select a receptacle compatible with the final board construction, or move the
receptacle onto a separately designed connector board.

## Mechanical rules that any solution must pass

1. The receptacle shell must meet the enclosure boundary and have a controlled
   chassis/EMI bond.
2. A normal USB-C plug must insert fully without colliding with the housing, shield,
   board, thermal stack, drums, or flex cables.
3. SuperSpeed routing from the receptacle through ESD and the orientation mux must
   be short, continuous, and reviewable.
4. The connector must tolerate insertion force without loading the PCB or housing
   beyond their mounting assumptions.
5. Assembly, inspection, rework, and cable removal must remain possible.
6. The solution must preserve the microphone acoustic path and moving-flex envelopes.
7. The receptacle land pattern and mid-mount geometry must support the actual local
   PCB thickness without an undocumented milling or assembly process.

## Candidate A — Move the enclosure opening to the board edge

The main board retains a board-edge J1 corridor and the enclosure opening moves to
match it.

Advantages:

- shortest and simplest USB SuperSpeed path;
- no extra high-speed connector or interconnect;
- connector loads can transfer directly into the main-board mounting structure.

Costs and risks:

- changes the visible industrial design;
- requires a new housing opening, internal boss, cable-clearance, and shield study;
- may conflict with the curved housing surface or other internal structures.

## Candidate B — Preserve the opening and relocate the main board/receptacle

The opening stays at X = 0 mm, and J1 must be placed on a main-board edge that can
physically meet it. This may require shifting, rotating, notching, or reshaping the
board and relocating the processor/memory and other components.

Advantages:

- preserves the current external appearance;
- retains one rigid PCB and avoids another high-speed connector.

Costs and risks:

- the present rectangular 90 x 28 mm board and central compute region do not prove a
  valid mating edge at X = 0 mm;
- a notch or board shift could remove routing area and disturb the thermal interface;
- all mounting, shield, flex, and critical-route assumptions would need reevaluation.

## Candidate C — Preserve the opening with a small connector board or rigid-flex

A mechanically supported USB-C receptacle sits at the enclosure opening and connects
to the main board through a controlled-impedance rigid-flex or short board-to-board
interconnect.

Advantages:

- preserves the external opening without forcing the main board through the curved
  housing boundary;
- isolates insertion loads from the dense main board;
- permits independent adjustment of the external connector geometry.

Costs and risks:

- adds a PCB/interconnect, assembly steps, cost, and failure points;
- USB SuperSpeed signal integrity must be demonstrated across the interconnect;
- shield continuity, ground-reference transitions, and connector retention become
  explicit design problems.

## Current recommendation and decision gate

No candidate is selected yet. Candidate A is electrically simplest. If preserving the
centered industrial-design opening is mandatory, Candidate C is presently more
credible than visually moving J1 into the middle of the existing board, but it must
pass a USB 3.x interconnect and mechanical-retention review.

The mechanical lead must compare the three candidates in the enclosure coordinate
system and provide:

- receptacle, plug, and cable sweep geometry;
- board and shield mounting reactions under insertion/removal;
- a collision-free assembly sequence;
- a continuous USB reference-path concept;
- the exact selected receptacle location and orientation.

Until that evidence exists, J1 placement and the 90 x 28 mm outline remain
provisional, the mechanical gate remains blocked, and pin-driven placement must not
begin.

## Official source records

- Hirose CX90M3-24P product record, detailed specifications updated 19 June 2026:
  https://www.hirose.com/product/p/CL0480-0919-0-00
- Local manufacturer STEP provenance: `blender/vendor_cad/hirose/README.md`
