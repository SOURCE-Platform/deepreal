# DeepReal Blender reference model

Blender is the current mechanical and visual design authority for DeepReal.
The canonical design is one curved 120 mm-wide assembly; the obsolete
"Current" collision study and boxy "Compact" comparison are no longer part of
the build. FreeCAD is not required.

This is an architecture-complete concept model for communication, packaging,
and website imagery. Named parts distinguish verified/reference component
envelopes from concept geometry. It is not production CAD and must not be used
to manufacture tooling or certify optical, thermal, EMC, or safety behavior.

## Source files

- `design_spec.py` — Blender-native dimensions and the approved curved housing
  profile.
- `device.py` — hollow curved enclosure, drum channel, motor pocket, and two
  cylindrical 24 × 54 mm drum shells.
- `optics.py` — bored apertures plus architecture-stage RGB, IR, projector,
  carrier, PCB, and optical keep-out geometry.
- `electronics.py` — populated main PCBA, proof-engine parts, one formed
  board-covering EMI shield can, a separate external connector strip,
  thermal spreader/pad, microphone, and tamper switch.
- `motion.py` — two offset gearmotors, pinions, ring gears, axles, four
  bearings, encoder boards/magnets, brackets, and travel stops. Each ring gear
  occupies the final 2 mm drum-end band, clear of the outer camera window.
- `interconnect.py` — four camera flex service loops and two projector
  power/control harnesses.
- `support_hardware.py` — removable PCBA standoffs, fasteners, and bearing
  carriers that connect the functional core to the enclosure.
- `presentation_views.py` — a labeled four-view overview plus four detail
  scenes made from linked instances of the canonical geometry.
- `mounting_stack.py`, `usb_port.py`, `usb_cable.py` — display attachment and
  external connection concepts.
- `build_scene.py` — deterministic complete-scene build.
- `validate_model.py` — named-subsystem and legacy-variant checks.
- `review_renders.py` — renders the overview and all four detail scenes for
  review and website use.
- `deepreal.blend` and `renders/` — generated outputs; rebuild rather than
  treating manual edits as authoritative.

## Build and validate

From the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --factory-startup --python blender/build_scene.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python blender/validate_model.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python blender/review_renders.py
```

The build uses millimetres in source and converts to Blender metres. Product
X runs across the display, Y runs front-to-back, and Z runs vertically.

## Enclosure and shielding decisions

- The electronics compartment follows the approved curved/tapered lower
  profile instead of a rectangular chin.
- The housing contains real drum, motor, and electronics cavities.
- The populated area of the PCBA sits under one shallow grounded shield can:
  one lid plus four perimeter walls meeting the PCBA ground. A narrow board-
  edge strip remains outside the perimeter for cable connectors.
- The can deliberately does not cover every visible millimetre of green PCB.
  Bare board perimeter and the physical connector-mating strip remain outside;
  all processor, FPGA, memory, power, USB, and driver packages remain inside.
  Production design must bond connector shields/grounds and control the traces
  where they pass beneath the can wall.
- Four camera, two projector, and two motor connectors remain outside the can.
  Every external harness terminates at that strip; signals continue beneath
  the shield only as controlled PCB traces.
- A separate copper spreader and compliant pad show the intended heat path
  behind the PCBA into the rear housing surface. Neither thermal part is
  enclosed by the front-side EMI can.

## Presentation scenes and navigation

The generated `.blend` opens to **00 Four View Overview**, where all four
versions are arranged together and labeled. You do not need to know Blender's
navigation to find them. For a larger individual view, use the scene selector
in the upper-right corner of Blender and choose one of the four numbered detail
scenes. The canonical source scene is also retained for modeling work.

Presentation objects are linked duplicates: they have independent positions
for composition, but share the source mesh or curve datablock. Geometry is
modeled once and updates in every view.

0. **00 Four View Overview** — all four labeled arrangements on one canvas.
1. **01 Fully Assembled** — complete enclosed DeepReal hardware.
2. **02 Housing Removed** — enclosure and drum shells removed; mounting
   brackets, carriers, and standoffs remain. The enclosure-mounted USB-C
   receptacle and external cable are removed with the housing.
3. **03 Functional Core** — the same internals with removable support hardware
   omitted.
4. **04 Electronics Exploded** — the PCBA, every component, the five can
   pieces, heat spreader, pad, and connector strip separated for inspection.

## What remains open

The model includes every architecture-level BOM function, but many items are
still reference envelopes. Production work still needs selected lenses,
projector and eye-safety hardware, final PCB layout, confirmed motor and
bearing parts, fastening/sealing details, flex fatigue data, thermal testing,
EMC testing, mass/hinge testing, and tolerance-driven CAD. Those unresolved
items are visible in the model and documentation rather than silently treated
as finished engineering.
