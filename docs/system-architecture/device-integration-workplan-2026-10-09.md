# DeepReal device integration workplan — 9 October 2026

Status: engineering work order. The exterior study can support appearance review;
the internal hardware is still an unverified concept. This plan does not approve a
board, flex, actuator, optical output or fabrication release.

The first [measured drum-interface audit](../electrical/drum-interface-finding-2026-10-09.md)
found two geometry blockers: the encoder magnet/sensor envelopes sit 6 mm off
the rotation axis, and the specified optical flex end is 15.6 mm wide while
the modeled outer spindle bore is 2 mm. Resolve these together before treating
the R21 mechanism as a cable or encoder layout.

## Working assembly

The current exterior is the R30 housing with two exposed-top drums, fixed left
and right cheeks, a fixed center divider, and a monitor-top ledge. R21 supplies
the internal motion *envelopes*. One reusable optical-head electrical design is
intended to populate both drums, with different RGB assembly variants. These
pieces have not yet been reconciled into a buildable assembly.

```text
                            stationary housing and center divider
              ┌──────────────────────────────────────────────────┐
face drum     │ fixed motor/drive → rotating ring → drum          │
              │ inner bearing                       outer bearing │
              │ moving optical head → dynamic flex → fixed harness
              │ rotating magnet → fixed angle sensor at cheek    │
interaction   │ same mechanism; different optical population     │
drum          │ and separately chosen travel stops               │
              └──────────────────┬───────────────────────────────┘
                                 │ power, CSI, control, motor and angle wiring
                       main PCBA ↔ USB-C ↔ host
```

The outer cheeks and center divider should react bearing and motor loads into
the same housing. The moving optical flex must have its own controlled path and
life test; the motor and stationary angle sensor use fixed wiring to the main
board. A render showing these paths is not evidence of clearance or fatigue life.

| Interface | Drum or actuator side | Housing/main-board side | Current status |
| --- | --- | --- | --- |
| Drum support | Rotating inner ring and outer hub | Center-divider bearing seat and outer-cheek spindle | Envelopes only; bearing/coupling unselected |
| Drum drive | Internal ring gear attached to drum | Center-fed motor, bracket and pinion | Envelope only; torque, teeth and fastening open |
| Optical data and power | Reusable RGB/IR/projector head in each drum | Main-board J2/J3 through an outer-axis exit | 51-contact grouping exists; pinout, bend and current unapproved |
| Absolute drum angle | Magnet rotates with end face | Hall sensor/board at outer cheek | Physical location conflicts with main-board register |
| Motor position and power | Motor quadrature encoder and motor terminals | Main-board J4/J5 and U13/U14 | Harness concept exists; exact motor and connector pending |

## First integration conflict to close

R21 places each rotating encoder magnet next to a **stationary angle-sensor
board at the outer cheek**. The main-board component register still lists
U18/U19 AS5600L as **main-PCBA top-side components**, and the circuit plan
groups them with the motor harnesses. Those two physical locations cannot both
describe the same sensor. R21 also labels its Hall IC as unselected, so the
AS5600L choice and magnetic geometry need confirmation.

Preferred layout direction for evaluation: keep a small stationary sensor
daughterboard at each cheek, close to the rotating magnet; carry power,
ground and angle-data signals to the main PCBA by a fixed harness. This avoids
requiring the sensor to read a magnet across the device from the main board.
Before updating KiCad, verify sensor-to-magnet orientation, air gap, angular
error, cheek thickness, motor-field interference, address/voltage compatibility
and service access. Then move the physical U18/U19 placement ownership from the
main board to those cheek boards, or document a different proven geometry.
Keep the motor quadrature encoder separate from this absolute-angle function.

## Execution sequence and exit evidence

| Order | Work package | Deliverable that closes it |
| --- | --- | --- |
| 1 | Freeze one reference drum's physical interface | Coordinate drawing with center/outer bearing seats, fixed vs rotating parts, magnet and sensor datum, motor/pinion/ring coupling, head-board envelope, cable exit, hard stops and service clearances. Repeat with the second drum's optical and travel differences. |
| 2 | Prove motion and wiring envelopes | Selected bearing and motor candidates, torque/inertia/gear calculation, backlash target, full pose collision sweep, hard stops, moving-flex bend radius and cycle-life plan. Travel limits follow optical coverage and wire life; existing R21 poses are provisional. |
| 3 | Resolve stationary and moving interconnects | Numbered end-to-end 51-contact head flex; mating side and contact orientation; six camera differential pairs per head; power/return allocation; motor/quad harness and cheek sensor harness. Provide continuity drawing and current, voltage-drop, signal-integrity and fatigue review. |
| 4 | Complete head power, clocks and safety | Mode-specific RGB/IR load and startup budget, local conversion losses, projector capacitor recharge, 38.4 MHz Mira220 reference-clock implementation, power sequencing and hardware-default-off projector interlock. Then capture the reusable head schematic and outline. |
| 5 | Close compute and external connection | Compile one- versus two-FPGA alternatives on supported tools with legal pins/timing; define simultaneous capture and USB output/encoding policy; select a USB-C mating solution at the housing opening, including compatible board thickness and insertion support. |
| 6 | Design the actual main board | Audit exact parts and footprints, populate the functional KiCad sheets, run ERC, select stack-up, place from pin and enclosure constraints, prove critical routes, then complete routing/DRC, thermal and specialist review. Board size remains a candidate until this is done. |
| 7 | Prototype and validate | Bench one drum/head first: startup absolute-angle and quadrature correlation, motion under cable load, flex life, sensor/clock behavior, power transients, projector safety and thermal behavior. Integrate the second drum and full USB capture after the reference module passes. |

Packages 1, 3 and 4 can advance together. Package 5 can run in parallel once
its camera and mechanical connector assumptions are explicitly recorded.
Packages 6 and 7 depend on the interface and electrical evidence above.

## Next concrete engineering pass

The [R34 face-drum interface study](../../blender/refinements/r34/README.md)
now places a rotating magnet on the outer drum axis opposite a stationary
cheek-board envelope and passes a 15.6 mm straight flex envelope through the
inner bearing. Its sampled straight-segment sweep clears the current fixed
geometry. The study leaves the deforming service loop, shaft/hub coupling,
cheek wall, selected bearing and interaction drum unresolved; it is evidence
for packaging direction, not a fabrication-ready mechanism.

The follow-on [R35 motion study](../../blender/refinements/r35/README.md) adds
an outer rotating web from shaft and hub to drum wall. Its concept geometry
clears the fixed bearing and enclosure, but the joints and loads are open.
The moving cable route is blocked in the current package: all eight sampled
full-width axial-twist candidates intersect the existing bearing supports;
longer routes also intersect the optical carrier. The immediate integration
task is to redesign the inner bearing support and cable architecture together
before assigning a final drum flex or freezing the head-board connectors.

The [R36 bearing-window study](../../blender/refinements/r36/README.md)
resolves the first geometric obstruction at concept level: an axial fixed
bearing neck and side webs clear the rotating ring and straight 15.6 mm strip
over sampled face-drum poses. The service loop and fixed cable exit remain
unmodeled. A 6–8 mm trunk-width screen and offset screen did not find a
collision-free simple twist through the current optical-carrier layout, so
the next pass must reserve a separate moving-cable volume and verify the
electrical construction before changing the 51-contact interface.

The [R37 rear-space study](../../blender/refinements/r37/README.md) places a
test passage through the center divider and a test chamber within the rear
housing. The passage intersects the current rear bearing support web, while
the chamber is occupied by the solid visual enclosure. The cable also needs
a change of orientation to reach that chamber without bending edgewise.
These are volume reservations, not cutouts or a complete cable path. Design
the support, flex loop, and fixed termination together before cutting the
housing or treating the R37 view as an assembly solution.

1. Make a shared coordinate and connection drawing for **one drum** using the
   R30 housing and R21 motion envelopes. Mark every fixed support, rotating
   part, cable and board. Include the cheek angle-sensor board option.
2. Write the per-drum interface table from head connector to main board, plus
   separate motor/quad and angle-sensor harnesses. Number contacts only after
   checking both connector ends and flex orientation.
3. Reconcile the schematic/component register with that physical partition.
   Do not move U18/U19 in the PCB file until the cheek geometry and electrical
   interface are reviewed.
4. Run the full pose sweep with transparent housing and three views per pose:
   front, above and end-on. Inspect lens clearances, top opening, flex path,
   bearing support and wire exposure at both travel limits.

The monitor attachment and decorative plate remain a separate mount-validation
track: retention/release force, laptop hinge load, adhesive aging and the
selected magnet or clip mechanism. They do not set the internal PCB pinout.

## Evidence behind this work order

- `blender/refinements/r21/r21_mechanism.py`: bearing, motor, gear, magnet and
  flex envelopes; no selected hard stops or fatigue proof.
- `blender/refinements/r30/r30-mount-manifest.json`: current exterior/ledge study.
- `hardware/electronics/deepreal-main-pcba/component-register.csv` and
  `circuit-specification.md`: current U18/U19 and J4/J5 ownership.
- `hardware/electronics/deepreal-main-pcba/design-status.json`: G3/G4 blocked,
  G5 in progress, G6 blocked, routing not started.
- `docs/electrical/head-interface-checkpoint-2026-09-14.md`: 51-contact flex,
  connector orientation and current constraints.
- `docs/electrical/pcb-progress-2026-09-14.md`: board and circuit status.
- `docs/design/main-pcba-usb-mechanical-options-v0.1.md`: USB opening/port
  mismatch and board-thickness conflict.
- `docs/research/main-pcba-fpga-topology-study-v0.2.md`: topology decision gate.
