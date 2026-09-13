# DeepReal Blender reference model

Blender contains the mechanical concept and presentation scenes. KiCad is the
authority for the main PCB footprint placement and copper geometry.
The canonical design is one curved 120 mm-wide assembly; the obsolete
"Current" collision study and boxy "Compact" comparison are no longer part of
the build. FreeCAD is not required.

The electronics are an incomplete engineering rebuild, **not approved for
website use**. The native KiCad import preserves the current placement defects;
it does not make the footprint selections, circuits or layout correct. The two
rotating head-board designs and flex interfaces remain unresolved concepts.
This model must not be used to manufacture or certify hardware.

See [the current implementation checkpoint](../docs/electrical/native-pcba-import-checkpoint.md)
for measured progress, reproducible commands and remaining blockers.

## Source files

- `design_spec.py` — Blender-native dimensions and the approved curved housing
  profile.
- `device.py` — hollow curved enclosure, drum and motor pockets, bounded side
  cable passages, and two cylindrical 24 × 54 mm drum shells.
- `optics.py` — bored apertures plus architecture-stage RGB, IR, projector,
  carrier, PCB, and optical keep-out geometry.
- `electronics.py` — native main-PCB import, concept shield and thermal stack.
  The missing KiCad tamper switch is no longer silently added in Blender.
- `motion.py` — two offset gearmotors, pinions, ring gears, axles, four
  bearings, encoder boards/magnets, brackets, and travel stops. Each ring gear
  occupies the final 2 mm drum-end band, clear of the outer camera window.
- `interconnect.py` — two combined 51-conductor optical-head flex routes;
  projector drivers and pulse loops remain local to the rotating heads.
- `support_hardware.py` — removable PCBA mounts, bearing carriers, grounded
  cable channels, boundary clamps, and strain relief.
- `presentation_views.py` and `pcba_presentation.py` — full-device views plus
  five dedicated PCBA scenes made from linked canonical geometry.
- `pcba_bom.py` — presentation names and explicitly representative envelopes
  for 18 missing native chip models; not an independent placement authority.
- `pcba_kicad_data.py` and `pcba_native_import.py` — hash-checked JSON/GLB
  interface from KiCad, including native components, pads, mask and holes.
- `mounting_stack.py`, `usb_port.py`, `usb_cable.py` — display attachment and
  external connection concepts.
- `build_scene.py` — deterministic complete-scene build.
- `validate_model.py` — legacy assembly checks; still fails missing required
  hardware and does not approve electronics.
- `validate_pcba.py`, `validate_pcba_native.py`, `test_pcba_native.py` — geometry
  transport and provenance checks, explicitly separate from engineering approval.
- `render_native_review.py` — six stamped internal review images; no publication.
- `review_renders.py` — legacy general-device review views, not a release gate.
- `render_pcba_public.py` — gated public packaging; currently refuses release.
- `deepreal.blend` and `renders/` — generated outputs; rebuild rather than
  treating manual edits as authoritative.

Handmade copper, decorative vias, fake connector-apron boards and the separate
Blender support-population generator are no longer active. Removed source is
recoverable from Git history. No traces have been invented to fill this board.

## Build and validate

From the repository root:

```sh
# Refresh the JSON and native GLB first; see the checkpoint for KiCad commands.
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --factory-startup --python-exit-code 1 --python blender/build_scene.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python-exit-code 1 --python blender/validate_pcba.py

/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python-exit-code 1 --python blender/test_pcba_native.py
```

The build uses millimetres in source and converts to Blender metres. Product
X runs across the display, Y runs front-to-back, and Z runs vertically.

## Enclosure and shielding decisions

- The electronics compartment follows the approved curved/tapered lower
  profile instead of a rectangular chin.
- The housing contains real drum, motor, electronics, and side-route cavities.
- A two-piece shield concept surrounds the main board. Actual connector,
  component, thermal-contact and tolerance clearances remain open.
- The head interfaces are two candidate combined flex connectors plus two
  motor/encoder interfaces. Their native placement currently overhangs the
  board incorrectly; no grounded connector apron has been implemented.
- Side cable passages are closely bounded, and data and power/motion routes
  remain in separate fitted channels.
- A separate copper spreader and compliant pad show the intended heat path
  from the rear tray into the rear housing surface. The spreader and pad sit
  behind the enclosure rather than inside the protected electronics chamber.

## Presentation scenes and navigation

The generated `.blend` opens to **00 Four View Overview**, where all four
versions are arranged together and labeled. You do not need to know Blender's
navigation to find them. For a larger individual view, use the scene selector
in the upper-right corner of Blender and choose a numbered detail
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
4. **04 Electronics Exploded** — the PCBA, tray, lid, components, thermal
   stack, connector banks, routes, and supports separated for inspection.
5. **05 Shield Cutaway** — the front lid removed to expose the shield
   boundary, populated field, connector apron, and cable passages.
6. **06 PCBA Top** — orthographic top/front assembly view.
7. **07 PCBA Bottom** — orthographic bottom/rear assembly view.
8. **08 PCBA Dimensioned** — board and populated-stack dimensions.
9. **09 PCBA Identification** — top/bottom reference-designator index.
10. **10 Camera Flex Study** — current two-connector drum interface beside the
    four-camera-flex signal-integrity fallback.

## What remains open

The model includes every architecture-level BOM function, but many items are
still reference envelopes. Production work still needs selected lenses,
projector and eye-safety hardware, final PCB layout, confirmed motor and
bearing parts, fastening/sealing details, flex fatigue data, thermal testing,
EMC testing, mass/hinge testing, and tolerance-driven CAD. Those unresolved
items are visible in the model and documentation rather than silently treated
as finished engineering.
