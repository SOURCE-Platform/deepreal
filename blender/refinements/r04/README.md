# DeepReal exterior refinement R04

This folder contains the restored R04 Blender review model and all files needed
to rebuild and verify it. It lives inside the DeepReal repository so the model,
renders, scripts, and evidence remain together.

## Open this file

`deepreal-exterior-refinement-r04.blend`

The saved Blender viewports use a 0.19 m orbit distance so the product opens at
a useful review scale.

## R04 changes

- The panel USB-C assembly and cable are horizontally centered at `X = 0`.
- Both drum surfaces meet at the centerline with zero visible modeled gap.
- The cable includes a male metal shell, internal insert, contact tongue, seated
  overmold, and vertical cable.
- The thermal interface is split left and right around a 15 mm center USB
  channel. Each pad touches the copper spreader and a provisional housing boss.
- The stationary PCB assembly remains shifted 5 mm toward the monitor.
- The straight rear wall and broad lower enclosure curve are retained.

These are review geometries. Real drums need controlled running clearance. The
thermal pads and housing bosses need material selection, compression analysis,
thermal analysis, tolerance work, and physical testing. The USB assembly still
needs an exact connector, sealing, retention, bend-radius, and internal
electrical-interconnect design.

The main PCB and populated envelope still intersect the lower curved cavity;
R04 does not correct that electronics packaging conflict.

## Rebuild

From the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python blender/refinements/r04/build_r04.py -- --render
```

## Verify the saved native file

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/refinements/r04/deepreal-exterior-refinement-r04.blend \
  --python blender/refinements/r04/verify_r04.py
```

The verifier writes `reports/r04-geometry-audit.json`. The generated source
`blender/deepreal.blend` is Git-ignored, so the report checks its recorded SHA-256
and September 14 modification time rather than claiming a Git comparison.
