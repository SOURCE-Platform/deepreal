# R34 face-drum interface study

This Blender revision tests one packaging direction against the R30 exterior:
a centered angle encoder at the **outer cheek** and an optical flex exit through
the **inner bearing**. It changes only the face drum. The interaction drum
retains its R30/R21 interface.

The [R35 motion study](../r35/README.md) extends this check and finds that a
full-width moving twist collides with the existing bearing supports and optical
carrier. Treat the straight-aperture result below as a limited check.

## Files

- `deepreal-face-interface-study-r34.blend` is the editable assembly study.
- `r34-mechanism-study.png`, `r34-outer-encoder-detail.png` and
  `r34-inner-flex-detail.png` are internal review views. The enclosure and
  drum skin are hidden in these views to reveal the interfaces.
- `r34-interface-manifest.json` records the placed envelopes and open items.
- `r34-interface-check.json` records the current geometric sweep.
- `build_r34.py`, `check_r34.py` and `render_r34.py` reproduce those artifacts
  from the R30 model using Blender 5.2.

Run the scripts in build, check, render order from the repository root:

```sh
blender -b -t 4 --python blender/refinements/r34/build_r34.py
blender -b -t 4 --python blender/refinements/r34/check_r34.py
blender -b -t 4 --python blender/refinements/r34/render_r34.py
```

## What this pass establishes

The moving magnet and stationary sensor-package proxies share the face-drum
axis. Their modeled axial surface gap is 0.55 mm. The sensor board sits in an
internal pocket in the fixed outer cheek; the exterior cheek remains skinned.
The magnet is a Ø6 × 2.5 mm **reference envelope**, not a selected magnet.
The [AS5600L adapter-board guide](https://look.ams-osram.com/m/b03a90ea3dea434a/original/AS5600L_UG000345_2-00.pdf)
gives 0.5–3 mm for its reference magnet setup;
field strength, datum and errors for this assembly have not been measured.

The inner flex strip uses the documented 15.6 mm connector-end width from
`head-interface-evidence.json`. A clearance slot is cut through the inherited
solid drum cap. At sampled face-drum angles from −45° to +45° in 5° steps,
the straight strip has zero triangle intersections with the fixed inner bearing,
motor, motor bracket, housing and drum shell. At zero it also has zero triangle
intersections with the modeled optical carrier, head PCBA carrier, RGB/IR/
projector bodies and rotating inner bearing. The strip's maximum corner radius
is 7.80 mm against an 8.45 mm fixed-bearing opening radius: approximately
0.65 mm **nominal radial** margin. This is a geometry check, with no tolerance
or manufacturing allowance.

## Open before the mechanism can be released

1. Design and sweep the **deforming flex service loop** between the rotating
   head and fixed divider; select flex construction, end terminations, strain
   relief, minimum bend radius and cycle-life target. The current strip ends
   before that transition.
2. Connect the outer rotating shaft structurally to the rotating hub and drum.
   The bearing, shaft and hub are envelopes, with no load or fastener design.
3. Redesign the outer cheek pocket with a validated wall and board mount. The
   study leaves a very thin outer skin solely to preserve exterior appearance.
4. Validate the magnet, sensor datum, polarity, air gap across tolerances,
   motor-field interference and stationary electrical harness.
5. Reconcile the second drum, motor drive, hard stops and assembly sequence.

The present `straight_envelope_pass` field describes only the tested straight
segment and static overlaps. It does not indicate that a moving cable or
manufacturable bearing assembly passes.
