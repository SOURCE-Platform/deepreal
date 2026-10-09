# DeepReal pressed logo target plate — R32

This separate Blender appearance study replaces the R31 dark surface mark
with actual shallow relief on a taller laptop-side magnetic target plate.

- Plate: 112 × 26 × 0.35 mm, centered at z = −14 mm below the laptop top.
- Foam sticker: 109 × 23 × 0.4 mm. The original R30 device-side magnet pad
  remains its earlier size; magnetic holding force has not been checked here.
- Artwork: original DeepReal SVG sampled to 103 mm wide. Each logo line is
  the bottom of a 0.15 mm deep trough with a 0.95 mm smooth shoulder.
- The plate back remains flat in this visual model. Material forming, tooling,
  local thickness, adhesive stack, and pull force require a physical prototype.

Build with:

```sh
/opt/homebrew/bin/blender -b --python blender/refinements/r32/build_pressed_plate.py
```

The saved file opens on the plate detail camera. The PNG renders show the
larger plate on a laptop lid and the light/shadow behavior of the logo.
