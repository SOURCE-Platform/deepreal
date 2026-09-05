# Blender reference model and visual bill of materials

**Status:** architecture-complete concept model, 5 September 2026
**Authority:** `blender/design_spec.py` and generated `blender/deepreal.blend`

DeepReal now has one active mechanical concept in Blender. The obsolete
"Current" model existed to demonstrate collisions and has been removed. The
rectangular "Compact" chin has also been replaced by the approved curved
electronics compartment, which turns the earlier empty lower curve into
usable packaging volume.

![Current curved Blender profile](./blender-reference-profile.png)

The profile view shows the curved lower compartment continuing behind the
drums. The flat internal stack does not dictate a box-shaped exterior.

## What the major sections do

| Section | What it does | Model status |
| --- | --- | --- |
| Face drum | Aims RGB, IR depth receiver, and structured-light projection at the user. | Shell and optical architecture present; exact optics remain reference/placeholder geometry. |
| Interaction drum | Aims the same sensing classes toward hands and workspace. | Shell and optical architecture present; exact optics remain reference/placeholder geometry. |
| Drum motion | Rotates each drum independently and measures its real angle. | Two motors, pinions, ring gears, axles, four bearings, encoders, brackets, and stops present as concept/reference envelopes. |
| Electronics compartment | Houses the stationary Proof Engine below/behind the drums. | Curved hollow enclosure and populated PCBA volume present. |
| EMI shield can | Contains emissions close to the i.MX 95, FPGA, and memory instead of trying to block radiation with a remote full-width wall. | One thin lid and four perimeter walls present; grounding fingers, seams, and apertures await PCB/EMC design. |
| Thermal path | Moves processor heat into the enclosure so the case can spread it. | Copper spreader and compliant housing pad present; dimensions and thermal performance remain unverified. |
| Interconnect | Carries four camera streams plus emitter/control power across limited drum rotation. | Four MIPI service loops and two power/control routes present; exact flex stack and fatigue radii are open. |
| USB-C | Carries host data and intended single-cable power. | Port and cable concept present; connector/mechanical integration remains provisional. |
| Mount | Attaches the device to the display without putting active electronics in the laptop-side plate. | Magnet, steel target plate, and replaceable foam concept present. |

## Visual BOM

![Internal assembly with enclosure and drum shells hidden](./blender-internal-assembly.png)

| Qty | Named model item | Purpose | Evidence/status |
| ---: | --- | --- | --- |
| 2 | 24 × 54 mm sensor drum | Independently aimed sensing payload | Locked exterior concept; 21 mm assumed usable ID |
| 2 | RGB camera package | Color/identity/interaction imagery | IMX708-class reference geometry |
| 2 | IR global-shutter camera | Structured-light receiver | OV9281-class; package/lens still incomplete |
| 2 | Structured-light projector assembly | Active depth pattern | Reference envelope; final part and eye-safety design open |
| 2 | Internal optical carrier | Holds calibrated drum optics | Concept geometry |
| 2 | Offset geared motor | Drum rotation | Reference gearmotor envelope |
| 2 | Pinion + ring gear pair | Transfers motor torque to drum | Concept gear envelopes, not tooth-level production gears |
| 2 | Drum axle | Defines rotation axis | Concept geometry |
| 4 | Drum bearing | Supports both ends of both drums | Reference envelopes; exact bearing selection open |
| 2 | Magnetic encoder + magnet | Reports measured drum angle | AS5600-class concept |
| 2 | Mechanical travel stop | Limits motion to the intended range | 150° concept; final stop geometry open |
| 1 | Main PCBA | Stationary electronics substrate | 90 × 28 mm architecture envelope |
| 1 | NXP i.MX 95 | Proof Engine compute and hardware-rooted trust | Reference package |
| 1 | CrossLink-NX FPGA | Trusted camera ingress/aggregation | Reference package |
| 2 | LPDDR package | Working memory | Reference package |
| 1 | eMMC package | System storage | Reference package |
| 2 | PF09/PF53 PMIC | Power sequencing and regulation | Reference packages |
| 1 | USB PD controller | Negotiates available USB-C power | Reference package |
| 1 | USB ESD/protection stage | Protects the external high-speed interface | Functional placeholder |
| 2 | Motor driver | Bidirectional motor control | DRV8212-class functional placeholder |
| 2 | Projector driver | Drives active depth emitters safely | Functional placeholder; exact part open |
| 1 | PDM MEMS microphone | Stationary audio observation | Reference package |
| 1 | Case-open tamper switch | Records enclosure-open state | Concept implementation |
| 1 | Five-piece EMI shield can | Local RF containment around noisy compute | Formed-sheet concept |
| 1 | Heat spreader + thermal pad | Conducts compute heat to rear shell | Concept heat path |
| 4 | Camera flex link | Moves MIPI camera data off rotating drums | Service-loop routing concept |
| 2 | Projector power/control harness | Feeds active depth hardware | Routing concept |
| 1 | USB-C receptacle and cable | Host data and power | Provisional mechanical concept |
| 1 set | Magnet/steel/foam mount | Display attachment | Provisional reference stack |

## Intentionally absent

![Local board-mounted shield can and routed interconnect](./blender-electronics-shield.png)

- No battery: DeepReal is host/USB powered.
- No separate TPM or secure element: the baseline uses i.MX 95 EdgeLock.
- No slip ring: limited 140–160° travel uses controlled flex loops.
- No second full-width EMI wall: the local grounded shield can is the baseline;
  EMC testing may change details later.

## Validation boundary

`blender/validate_model.py` confirms the named architecture-level subsystems
exist and that no `Current_` or `Compact_` comparison objects remain. Optical
containment checks also run during the scene build. This does **not** certify
manufacturability, signal integrity, EMC, thermal performance, eye safety,
structural strength, cable life, or production tolerances.
