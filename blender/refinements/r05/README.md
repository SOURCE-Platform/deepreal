# DeepReal enclosure refinement R05

R05 corrects the R04 internal presentation model. It remains a packaging and
interconnect proposal, not an approved electrical or mechanical design.

## What changed

- All imported KiCad objects now move with `Main_PCBA`. In R04, changing object
  parents while iterating the collection caused some small capacitor models,
  including `PCBA_C101` and `PCBA_C107`, to be skipped and left floating.
- The large `Housing_Thermal_Boss_*` blocks are removed. They were unsourced
  provisional housing protrusions, not real DeepReal parts.
- Two smaller `Thermal_Link_*` plates and compressible
  `Housing_Thermal_Pad_*` interfaces show a possible heat path. Their material,
  thickness, compression, contact pressure, and performance remain unverified.
- A centered USB daughterboard and internal flex are shown. A 15 mm service
  opening is modeled through the shield lid, shield tray, and thermal spreader.
- The current right-edge main-board `J1` object is retained as a hidden legacy
  reference. The centered arrangement needs a main-board connector and PCB
  revision; the model does not pretend the current J1 already supports it.
- Candidate paths connect the main-board region to both sensor drums. They show
  routing intent only. The 51-contact connector choice, contact assignment,
  cable construction, signal integrity, and motion envelope are still open.
- `Main_Housing` opens as a solid object. An optional hidden
  `Main_Housing_Inspection_Wireframe` copy is available for cutaway inspection.

## Proposed power and data path

The centered receptacle feeds `Centered_USB_Daughterboard`. The orange
`USB3_PD_Internal_Flex_CONCEPT` passes through the three centered service
openings to `Mainboard_USB_Flex_Connector_CONCEPT` on the main-board region.
From there the board would distribute power and data to its existing J2 and J3
head-connector locations. The two orange head-flex centerlines begin inside
those modeled connector bodies and end inside visible interface blocks at the
lower rear of each drum.

This only makes the packaging path explicit. The current PCB has no approved
centered USB daughterboard connector or routing, and this Blender file contains
no circuit connectivity. Exact connector parts, USB/PD pin mapping, impedance,
return paths, shielding bonds, flex construction, bend life, strain relief, and
drum feedthrough geometry must be engineered in the native electrical and
mechanical designs before this arrangement can be accepted.

## Object naming

`PCBA_C101`, `PCBA_C107`, and similar names are KiCad component reference
designators. In this model they are imported 0201 capacitor bodies. Their value
is recorded as `TBD_BY_RAIL`, and their native model/footprint is not yet vendor
verified. A visible 3D body does not prove the component selection or pin map.

`Housing_Thermal_Pad_*` represents a soft thermal interface material between a
thermal link and housing. `Thermal_Link_*` represents a possible thin copper or
graphite link. R05 contains no `Housing_Thermal_Boss_*` objects.

## View controls

The saved default shows the solid housing and frames the product to fill the
viewport. For internal inspection, hide `Main_Housing`, then enable
`Main_Housing_Inspection_Wireframe` in collection
`06 — HOUSING WIREFRAME — HIDDEN INSPECTION`. To repair this manually in Blender,
select an object, open **Object Properties → Viewport Display**, and set
**Display As** to **Solid** or **Wire**.

## Rebuild and verification

Run with the existing Blender 5.2 LTS installation:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python \
  blender/refinements/r05/build_r05.py -- --render

/Applications/Blender.app/Contents/MacOS/Blender --background --python \
  blender/refinements/r05/verify_r05.py
```

The authoritative source remains `blender/deepreal.blend`; the build script does
not save over it. Verification records the expected source SHA-256 and fails if
that file changes.
