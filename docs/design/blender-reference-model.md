# Blender reference model and visual bill of materials

**Status:** architecture-complete concept model, 7 September 2026
**Authority:** Blender Python in `blender/` and the generated
`blender/deepreal.blend`

DeepReal has one active mechanical concept: a curved, 120 mm-wide device with
two independently aimed sensor drums and a stationary electronics compartment.
Blender is the mechanical and visual design authority. FreeCAD and the former
comparison models are outside the current workflow.

This is packaging and architecture geometry, not production CAD. Reference
envelopes and concept parts remain subject to component selection, tolerance
analysis, thermal analysis, EMC development, and physical testing.

![Approved electronics architecture](./emi-full-enclosure-figma-reference-v1.png)

The approved illustration defines the packaging intent: a grounded enclosure
around the complete populated board area, a serviceable lower connector apron,
and separate cable routes down the left and right sides. It does not define
released dimensions or prove EMC performance.

## System architecture

| Section | Model content | Status |
| --- | --- | --- |
| Sensor drums | Face and interaction drums, each with RGB, IR, structured-light, carrier, and PCB envelopes | Drum packaging is established; final optical parts and calibration features remain open |
| Drum motion | Two motors, pinions, ring gears, axles, four bearings, encoders, brackets, and travel stops | Concept and reference envelopes; ring gears and routes are checked against the optical geometry |
| Main electronics | 90 × 28 mm PCBA with processor, FPGA, memory, storage, power, USB, motor, and projector-driver packages | Architecture-level placement |
| Electronics Shield Enclosure | Formed rear tray with integrated perimeter walls plus a removable front lid | Full-board conductive enclosure concept |
| Grounding | PCB perimeter ground ring, ten ground-via features, and three chassis-bond tabs | Visible grounding strategy; final contact pitch and impedance remain open |
| Connector apron | Separate face, auxiliary, and interaction banks below the shielded chamber | Service-accessible boundary concept |
| Cable routing | Left and right camera-data lanes plus separate left and right power/motion lanes | Routing concept with lane metadata, grounded separators, clamps, and strain relief |
| Thermal path | Shield rear tray, copper spreader, compliant housing pad, and rear housing contact | Continuous concept path; pressure and performance are unverified |
| External connection | USB-C receptacle and cable | Provisional mechanical integration |
| Display mount | Magnet, steel target, and replaceable foam | Provisional attachment stack |

## Electronics Shield Enclosure

The former local can and exposed upper connector strip are not part of the
active model. The populated PCBA field now sits inside a two-piece conductive
enclosure:

- `Shield_Front_Lid` is the removable service lid.
- `Shield_Rear_Tray` fuses the rear panel, left wall, right wall, top wall,
  and grounded connector-apron boundary into one formed part.
- Four PCB ground-ring segments, ten ground-via features, and three
  chassis-bond contacts show how the metal enclosure returns to board and
  chassis ground.

The tray clears the PCB substrate on its top and side edges, while a controlled
lower pass-through lets the board continue into the connector apron. The
shield remains inside the established housing envelope. Every protected
processor, memory, storage, power, motor-driver, and projector-driver package
is contained by the chamber. The model does not claim that the illustrated
seams, apertures, or contacts are ready for production.

## Connector apron and routing

Drum connectors sit below the primary shielded chamber rather than along its
upper edge. The lower apron has three zones:

- `Face_Connector_Bank` on the left.
- `Auxiliary_Connector_Bank` in the center.
- `Interaction_Connector_Bank` on the right.

Face-drum cables descend on the left. Interaction-drum cables descend on the
right. Each side has two distinct paths:

1. A camera-data lane for the two camera links.
2. A power/motion lane for projector and motor/encoder wiring.

Grounded lane dividers, boundary clamps, and strain-relief features preserve
the visible separation. Routes stay inside the housing silhouette and do not
cross the center of the electronics chamber.

The curves communicate path and service-loop intent only. They do not specify
production flex stack-up, impedance, shielding, conductor pairing, filtering,
or fatigue life. Camera links still require controlled-impedance,
ground-referenced construction. Switching-current supply and return
conductors must remain tightly coupled.

## Thermal continuity

The processor heat path remains continuous through the enclosure:

```text
processor region
  → Shield_Rear_Tray
  → Thermal_Spreader
  → Housing_Thermal_Pad
  → rear housing contact
```

The separate objects keep shielding, heat spreading, compliance, and housing
contact visible as different design concerns. Final materials, electrical
isolation, contact pressure, assembly tolerance, and thermal performance
require engineering analysis and test.

## Visual bill of materials

| Qty | Named model item | Purpose |
| ---: | --- | --- |
| 2 | 24 × 54 mm sensor drum | Independently aimed sensing payload |
| 2 each | RGB camera, IR camera, structured-light projector, optical carrier | Face and interaction sensing architecture |
| 2 | Geared motor, pinion, ring gear, axle, encoder, and travel-stop set | Drum movement and measured angle |
| 4 | Drum bearing | Supports both ends of both drums |
| 1 | Main PCBA | Stationary electronics substrate |
| 1 | NXP i.MX 95 | Main compute and hardware-rooted trust |
| 1 | CrossLink-NX FPGA | Camera ingress and aggregation |
| 1 | 4 GB-class LPDDR package | Working memory |
| 1 | eMMC package | Storage |
| 3 | One PF09 plus two PF53 footprints | Power sequencing and regulation; second PF53 provisional |
| 2 each | Motor driver and projector driver | Drum and emitter actuation |
| 1 each | USB PD controller, protection stage, input buck, and orientation mux | External power/data interface |
| 4 | 13 mm camera FPC connector | One front- and one rear-side connector per drum |
| 100+ | Representative passives, magnetics, and bulk capacitors | Density and package-height study; schematic not frozen |
| 1 set | Electronics Shield Enclosure | Full populated-field conductive boundary |
| 1 set | PCB ground ring, ten vias, three chassis-bond tabs | Shield grounding concept |
| 3 | Connector bank | Face, auxiliary, and interaction apron zones |
| 4 | Camera-data route | Two links per drum in side-specific data lanes |
| 2 | Projector power/control route | Side-specific power/motion routing |
| 2 | Motor/encoder harness | Side-specific power/motion routing |
| 1 set | Grounded dividers, clamps, clips, and eight strain-relief features | Route separation and support |
| 1 set | Shield rear tray, spreader, and housing pad | Thermal path |
| 1 each | PDM microphone and case-open tamper switch | Auxiliary interfaces |
| 1 | USB-C receptacle and cable | Host data and intended single-cable power |
| 1 set | Magnet, steel target, and foam | Display attachment |

## Eleven linked presentation scenes

The generated file opens to **00 Four View Overview**. Presentation objects
are linked instances of the canonical geometry: each scene has its own
composition, but every mesh or curve continues to share its source datablock.

1. **00 Four View Overview** presents assembled, housing-removed, functional
   core, and exploded arrangements together.
2. **01 Fully Assembled** shows the complete exterior.
3. **02 Housing Removed** removes the housing and drum shells while retaining
   brackets, carriers, standoffs, routing clips, and clamps.
4. **03 Functional Core** also removes enclosure-mounted support hardware.
5. **04 Electronics Exploded** separates the board, protected packages,
   enclosure pieces, connector banks, grounding features, thermal parts,
   routes, clips, clamps, and strain relief for inspection.
6. **05 Shield Cutaway** removes the front lid to expose the protected
   component field, shield boundary, lower apron, and side routes.
7. **06 PCBA Top** is the orthographic top/front assembly view.
8. **07 PCBA Bottom** is the orthographic bottom/rear assembly view.
9. **08 PCBA Dimensioned** records the 90 × 28 × 1.6 mm substrate and 6.06 mm
   modeled populated stack.
10. **09 PCBA Identification** indexes the top and bottom reference designators.
11. **10 Camera Flex Study** compares the four-connector baseline with an
    explicitly unproven two-interface alternative.

![Four-view overview](../../blender/renders/presentation-00-four-view-overview.png)

![Shield cutaway](../../blender/renders/presentation-05-shield-cutaway.png)

## Build, validate, and render

Run from the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --factory-startup --python blender/build_scene.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python blender/validate_model.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python blender/review_renders.py
```

The build uses millimetres in source and converts them to Blender metres.
Product X runs across the display, Y runs front-to-back, and Z runs vertically.
Rebuild generated outputs after changing Python. Do not treat an isolated
manual edit to `deepreal.blend` as the source of truth.

## Automated validation boundary

`blender/validate_model.py` checks:

- required shield, ground, apron, routing, support, thermal, and interface
  objects;
- absence of obsolete comparison and local-can objects;
- containment of protected packages with chamber clearance;
- connector placement below the shield boundary;
- exact cable clearance from the housing, shield, gears, neighboring cables,
  and fitted supports;
- data versus power/motion lane separation, bend-radius metadata, connector
  termination, and side-lane metadata;
- PCB mounting-hole clearance and standoff/fastener seating;
- contact through the shield rear tray, spreader, housing pad, and housing;
- ring-gear clearance from optical and cable geometry;
- protected-optics clearance through sampled −80° to +80° drum travel;
- all eleven presentation scenes, linked instances, exploded content, and
  cutaway content.

A passing script is an architecture-level consistency check. It does not
certify manufacturability, signal integrity, EMC, thermal performance, eye
safety, structural strength, cable life, or production tolerances.

## Intentionally absent and still open

- No battery: the concept uses host/USB power.
- No separate TPM or secure element: the baseline uses i.MX 95 EdgeLock.
- No slip ring: limited drum travel uses controlled service loops.
- No claim of emissions or immunity compliance.

Production work still needs final PCB stack-up and connector selection,
signal-integrity review, shield seam and contact design, motor suppression,
thermal and structural analysis, cable-flex testing through full drum travel,
near-field scanning, and emissions/immunity pre-compliance testing.
