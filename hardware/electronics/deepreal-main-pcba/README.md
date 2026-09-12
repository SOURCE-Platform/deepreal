# DeepReal Main PCBA Electrical Capture v0.2

| Field | Value |
| --- | --- |
| Board | Main PCBA |
| Target outline | 90 x 28 x 1.6 mm |
| Assembly | Two-sided, 10-layer HDI working assumption |
| KiCad | 10.0.6 project created and verified |
| Schematic | 15-page hierarchy and page contracts; circuits not yet captured |
| PCB | 90 x 28 mm, 10-layer preliminary placement; canonical board has no routed copper |
| Visual derivative | Production-intent KiCad/Blender artwork; illustrative copper only |
| Status | Investor-facing visualization complete; electrical capture and routing not complete |
| Architecture baseline | `../../../docs/electrical/main-pcba-schematic-entry-spec-v0.1.md` |

## Current KiCad artifacts

- `deepreal-main-pcba.kicad_pro` - KiCad project settings.
- `deepreal-main-pcba.kicad_sch` plus pages `02` through `15` - navigable
  schematic hierarchy. Each page states its references and closure gate.
- `deepreal-main-pcba-capture-map.pdf` - verified 15-page review export.
- `deepreal-main-pcba.kicad_pcb` - placement-only board study generated from
  `blender/pcba_bom.py`; it has the exact working outline and mount locations.
- `deepreal-main-pcba-visual.kicad_pcb` - non-fabrication website derivative
  containing the shared illustrative copper artwork.
- `visual-layout-summary.json` - machine-readable visual status, disclaimer and
  KiCad/Blender geometry counts.
- `public-assets.json` - approved caption, non-fabrication status and the six
  master/web image pairs intended for publication.
- `renders/preliminary-placement-top.png` and `-bottom.png` - KiCad 3D previews.
- `renders/production-intent-visual-top.png` and `-bottom.png` - KiCad views of
  the non-fabrication presentation board.
- `renders/deepreal-*-master.png` and `-web.png` - approved high-resolution and
  website-sized Blender presentation assets: top, bottom, dimensioned,
  exploded, shield cutaway and installed assembly.
- `scripts/generate_schematic_hierarchy.py` and
  `scripts/generate_preliminary_board.py` - deterministic regeneration tools.
- `scripts/generate_visual_board.py` - regenerates both the honest placement
  board and its separately named visualization derivative.

The placement currently contains the registered major packages plus U21/U22,
six camera-interface ESD arrays, nine power-inductor envelopes, 144 capacitor
proxies and 44 resistor proxies. Unconnected support parts are space claims,
not finished circuit values.

## Capture sequence

1. Import manufacturer symbols and footprints listed in `pinmap-gates.csv`.
2. Capture pages 2-4 and 13-15 from `circuit-specification.md` first.
3. Apply the net names and ownership in `net-registry.csv`.
4. Capture pages 5-12 after their vendor/tool gates close.
5. Annotate, run ERC and export an independently reviewed PDF and netlist.
6. Perform the Lattice pin compile and NXP DDR-tool pass before placement is
   treated as routeable.

Regenerate the current work with:

```sh
python3 scripts/generate_schematic_hierarchy.py
/Users/adam/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
  scripts/generate_preliminary_board.py
/Users/adam/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
  scripts/generate_visual_board.py
```

The visual route contract is `../../../blender/pcba_visual_layout.py`. Blender
and KiCad consume the same coordinates. The derivative contains 99 visual trace
paths, 81 visual vias, 10 test pads and four masked copper regions. These counts
describe artwork, not connected electrical nets.

Rebuild the public render package after `blender/build_scene.py` with:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python blender/render_pcba_public.py
```

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
- Marketing may use the caption **DeepReal Main PCBA — production-intent
  engineering visualization**. It must not describe the illustrative surface
  tracks as electrically routed or fabrication-ready copper.

## Current completion definition

This package closes the KiCad project structure, preliminary placement and the
separate investor-facing visualization. It does not close circuit or manufacturing
routing work.
Pin-level closure remains blocked where the official i.MX95, LPDDR4X, eMMC or FPGA
package data has not been imported and verified. See `pinmap-gates.csv` for the
exact blockers.
