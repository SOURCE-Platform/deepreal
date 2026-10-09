# PCB progress: 14 September 2026

## Bottom line

We have repaired how the existing design is represented and checked. We have
not yet converted that placement study into a complete electrical PCB design.
The main board and two drum boards are not ready for website publication or
senior-engineer design approval. A useful internal review package now exists.

This status follows the A-H stages in
[the diagnosis/action plan](deepreal-electronics-diagnosis-and-action-plan-v0.2.md).
They expand the original gated engineering plan; they do not replace its gates.

| Stage | Status | What that means |
|---|---|---|
| A: trustworthy model and checks | Native main-board transfer implemented; wider validation remains open | Blender reproduces the current KiCad geometry, including its defects. This does not validate the electronics or full mechanical assembly. |
| B: system connections and operating choices | In progress | Camera topology, USB/power modes, clock sources, timing and board/harness partition still need decisions and evidence. |
| C: both drum assemblies and flexes | In progress at requirements/interface audit | Connector dimensions and candidate placement conflicts are measured; no completed head schematic or PCB exists. |
| D: actual circuits and board rules | Early documents only | The 15-sheet hierarchy still contains no actual functional circuits. Preliminary layer/rule intent is not approved. |
| E: connection-driven placement and fit | Not complete; diagnostic trials only | No placement release or critical-routing proof. The 90 x 28 mm outline is still a candidate. |
| F: complete routing and engineering checks | Not started | Zero tracks, vias and zones; pads have no named electrical nets. |
| G-H: senior review, visual finish and website assets | Not reached | Internal diagnostic renders exist, not approved public renders. No specialist sign-off has been obtained. |

## Accomplished and solved

- Replaced independent Blender population/pad generation with KiCad-native geometry.
- Accounted for all 238 footprints: 216 native body models, 18 flagged missing-model
  envelopes and four mounting-hole footprints. Position comparison passes for the
  present export, but envelopes do not establish exact package correctness.
- Removed handmade copper/vias and stale fallback parts; a missing switch is now
  reported, rather than quietly drawn in a convenient place.
- Added provenance checks so changed CAD, export, status or model libraries cannot
  silently reuse stale geometry. Corrected presentation-view transform problems.
- Generated internal top, bottom, dimensioned, exploded, cutaway and installed views.
- Preserved native DRC evidence: 610 violations plus 199 schematic-parity issues.
  Counting zero unconnected items is explicitly not accepted when no nets exist.
- Corrected the connector-body metadata: 16.8 mm body versus 15.6 mm flex end.
  Audited a subset of actual copper-land dimensions against the manufacturer.
- Established six camera differential pairs per head and a connector-only current
  screen. Added 11 interface tests and rejected unsupported readiness claims.
- Tested connector rotations without changing the board. The experiment identifies
  the neighboring parts involved in a coordinated placement correction.

## Encountered but not solved

- Several processor/memory/power/protection footprints or pin maps remain wrong
  or unaudited. No verified schematic-to-footprint electrical relationship exists.
- Both drum connector courtyards extend 6.895 mm beyond the main board. Rotating
  and moving them inward removes overhang but leaves other overlap candidates.
- USB receptacle and housing opening are about 41.1 mm apart; the selected
  receptacle's board-thickness recommendation also conflicts with the candidate.
- Thermal contact, service clearances, dynamic flat-flex geometry, head lens/optical
  packaging and stationary angle-sensor placement remain unresolved.
- The drum documents describe one reusable carrier used twice, but actual head
  circuits and board outlines are not captured. Existing small slabs are concepts.
- The 51-contact flex has group allocations, not a numbered end-to-end pinout.
  Load current, voltage drop, contact sharing, signal integrity and bend life remain open.
- Four-camera aggregation is not compiled or timed. The current computer lacks
  the supported FPGA implementation environment; legal pins and timing require it.
- Raw camera payload exceeds the theoretical usable data rate of the assumed
  5 Gbit/s USB path. Encoding/output profiles or transport changes need a decision.
- No complete head/system power budget, manufacturable stack-up, routed board,
  physical prototype or independent specialist review exists.

These issues are coupled. Solving the USB or flex geometry may move connectors;
real pins may rotate major chips; support circuits may consume currently empty
space. Neither an attractive render nor component-body area proves the board fits.

## Work continued in this update: IR power and clock evidence

The official Mira220 DS000642 v9-00 was retrieved and visually inspected for
its power and clock tables. A source-hashed ledger now separates peak rail
currents, startup supply capability, and a typical 30 fps power example.
Full head totals stay unknown while RGB, conversion, projector, auxiliary and
flex loads remain unquantified; eleven new regression tests enforce that distinction.

A material clock error was found: the inherited records supplied both RGB and IR
from 24 MHz, while the reviewed IR sensor reference is 38.4 MHz. Main/head/flex
contracts are corrected and the shared-clock claim withdrawn. The actual source,
buffering, voltage levels and gating are still unselected; no extra part or trace
has been invented. This fixes the requirement record, not a finished clock circuit.

The sensor startup requirement is a minimum 350 mA source capability on its
2.5 V rail, not a maximum head-current figure. The typical 30 fps power example
is not accepted as a worst-case value at the required 60 fps mode.

See `hardware/electronics/deepreal-optical-head/power-clock-evidence.json` and
`hardware/electronics/deepreal-main-pcba/scripts/audit_head_power.py`. No KiCad
placement, circuit or Blender assembly geometry changed in this update.

## Next execution order

1. Obtain RGB/IR current profiles for the actual modes; quantify local conversion,
   startup and projector recharge. Choose clock sources/distribution and safe gating.
2. Resolve head connector contact orientation, actual numbered flex continuity,
   physical entry direction and current/return allocation together.
3. Close reusable head geometry and the USB/angle-sensor arrangement; choose legal
   FPGA camera pins using the supported implementation tools.
4. Capture audited circuits, then move components and test critical routing.
5. Freeze board size only after routing/fit evidence, then finish and review the
   electrical layout before generating publication assets.

No additional aesthetic choice is needed from the user now. Product trade-offs
such as required USB output mode or illuminated depth rate will need an explicit
decision once supported alternatives and consequences have been prepared.
