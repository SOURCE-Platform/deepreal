# DeepReal Main PCBA Electrical Capture v0.2

| Field | Value |
| --- | --- |
| Board | Main PCBA |
| Target outline | 90 x 28 x 1.6 mm |
| Assembly | Two-sided, 10-layer HDI working assumption |
| KiCad | 10.0.6 project created and verified |
| Schematic | 15-page hierarchy and page contracts; circuits not yet captured |
| PCB | 90 x 28 mm, 10-layer preliminary placement; canonical board has no routed copper |
| Public visualization | Not generated; publication paused |
| Status | Engineering rebuild in progress; electrical capture and routing not complete |
| Architecture baseline | `../../../docs/electrical/main-pcba-schematic-entry-spec-v0.1.md` |

The active rebuild plan is
`../../../docs/electrical/main-pcba-engineering-review-plan-v0.1.md`; requirements
v0.2 and `design-status.json` supersede older release and FPGA assumptions.

## Current KiCad artifacts

- `deepreal-main-pcba.kicad_pro` - KiCad project settings.
- `deepreal-main-pcba.kicad_sch` plus pages `02` through `15` - navigable
  schematic hierarchy. Each page states its references and closure gate.
- `deepreal-main-pcba-capture-map.pdf` - verified 15-page review export.
- `deepreal-main-pcba.kicad_pcb` - canonical engineering board. Its present
  contents are the inherited placement study, but future placement and copper
  edits originate only in KiCad.
- `design-status.json` - authoritative gate state and release permissions.
- `component-evidence.csv` - exact-source and footprint audit register.
- `source-evidence-register.csv` - versioned official-source locations and the
  specific gate each source can close.
- `change-register.csv` - architecture and geometry changes plus required reruns.
- `preliminary-stackup.json` - unapproved ten-layer intent model with every
  fabricator-dependent field left explicitly open.
- `engineering-layout-export.json` - canonical geometry and pad/copper export for
  Blender; the current baseline contains 238 components and 2,313 pads but no
  routing.
- `engineering-review-manifest.json` - generated evidence, blocker, and release
  inventory for the current review checkpoint.
- `public-assets.json` - publication lock and the names reserved for future
  KiCad-derived output. No current PCBA image is approved for publication.
- `scripts/generate_schematic_hierarchy.py` - deterministic hierarchy generator.
- `scripts/export_kicad_design.py` - exports canonical KiCad geometry for Blender.
- `scripts/validate_design_gates.py` and the other validators - enforce release,
  evidence, completeness, bandwidth, and no-fabrication rules.

The inherited placement contains 238 footprints: most registered major packages,
U21/U22, six camera-interface ESD arrays, nine power-inductor envelopes, 144
capacitor proxies, and 44 resistor proxies. SW1 is registered but missing from the
KiCad board. Several other footprints are known substitutes. Unconnected support
parts are space claims, not finished circuit values.

## Capture sequence

1. Import manufacturer symbols and footprints listed in `pinmap-gates.csv`.
2. Capture pages 2-4 and 13-15 from `circuit-specification.md` first.
3. Apply the net names and ownership in `net-registry.csv`.
4. Capture pages 5-12 after their vendor/tool gates close.
5. Annotate, run ERC and export an independently reviewed PDF and netlist.
6. Perform the Lattice pin compile and NXP DDR-tool pass before placement is
   treated as routeable.

Regenerate the hierarchy with:

```sh
python3 scripts/generate_schematic_hierarchy.py
```

The superseded visual board, handmade trace contract, generators, and renders were
removed from the working tree. Git history is the historical record. Future Blender
geometry must come from the canonical routed KiCad review draft instead.

The active Blender build imports component positions through
`../../../blender/pcba_placement.py` and visible tracks/vias through
`../../../blender/pcba_kicad_geometry.py`. `../../../blender/pcba_bom.py` now
supplies presentation metadata and historical fallback coordinates only.

Public rendering is intentionally blocked until `public_visual_allowed` becomes
true after the engineering and visual gates pass. At that future point, rebuild with:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/deepreal.blend --python-exit-code 1 --python blender/render_pcba_public.py
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
- No PCBA image may be used for new marketing or investor materials until the
  replacement passes G11. Its caption is controlled by `public-assets.json`.

## Current completion definition

This package preserves the KiCad project structure and preliminary placement while
the engineering review draft is rebuilt. It does not close circuit or manufacturing
routing work.
Pin-level closure remains blocked where the official i.MX95, LPDDR4X, eMMC or FPGA
package data has not been imported and verified. See `pinmap-gates.csv` for the
exact blockers.
