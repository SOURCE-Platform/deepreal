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
- `electronics.py` — populated main PCBA, proof-engine parts, one realistic
  board-mounted EMI shield can, thermal spreader/pad, microphone, and tamper
  switch.
- `motion.py` — two offset gearmotors, pinions, ring gears, axles, four
  bearings, encoder boards/magnets, brackets, and travel stops.
- `interconnect.py` — four camera flex service loops and two projector
  power/control harnesses.
- `mounting_stack.py`, `usb_port.py`, `usb_cable.py` — display attachment and
  external connection concepts.
- `build_scene.py` — deterministic complete-scene build.
- `validate_model.py` — named-subsystem and legacy-variant checks.
- `review_renders.py` — website/review exterior, profile, assembly, and EMI
  shield renders.
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
- High-emission compute parts sit under one shallow grounded shield can: one
  lid plus four perimeter walls meeting the PCBA ground. There is no invented
  second full-width barrier between electronics and drums.
- Camera flex connectors remain outside the can. Signals enter the chips
  through controlled PCB traces; no harness is routed through a metal wall.
- A separate copper spreader and compliant pad show the intended heat path
  from the compute area into the rear housing surface.

## What remains open

The model includes every architecture-level BOM function, but many items are
still reference envelopes. Production work still needs selected lenses,
projector and eye-safety hardware, final PCB layout, confirmed motor and
bearing parts, fastening/sealing details, flex fatigue data, thermal testing,
EMC testing, mass/hinge testing, and tolerance-driven CAD. Those unresolved
items are visible in the model and documentation rather than silently treated
as finished engineering.
