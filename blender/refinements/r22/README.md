# R22 curved canopy study

This is a visual study of the cover drawn over the drums in the user's
markup. Two removable curved panels span between the outer cheeks and the
center divider. Matching crowns on those three supports complete the arc.
The front remains open for both cameras; the cover bends over the top and
joins the rear housing spine. The R21 side bearings, motors, encoders, and
hollow outer cable pivots remain in place.

The canopy is 1 mm clear of the nominal 12 mm drum radius. Its leading edge
begins 75° behind the forward direction. At the face camera's provisional
45° upward bore, that is about 9.5° beyond its 20.5° vertical half field of
view. Actual lens rays and manufacturing tolerance remain to be checked.

`r22-canopy-clearance.json` reports no mesh triangle intersections between
the canopy and sampled moving shells, end rings, or lens elements at face
45° up / forward / 45° down and interaction forward / 22.5° down / 45° down.
This is a dust shield, not a sealed enclosure: dust can still enter through
the front slot and unsealed panel joints.

The inner-end lip inherited from R21 is still a separate visual mesh over a
solid shell end cap. Its outer surface is inset to remove the stepped
viewport artifact, while the actual bearing seat remains unresolved.
The next mechanical revision needs a genuinely hollow shell, an integrated
inner bearing seat, and a defined side assembly sequence. The wide
interaction lens envelope also still intersects the older optical carrier.

Files:

- `deepreal-curved-drum-canopy-r22.blend`: editable Blender study.
- `r22-exterior-preview.png`, `r22-above-preview.png`,
  `r22-side-preview.png`, `r22-low-pose-preview.png`: review images.
- `r22-canopy-manifest.json`: canopy dimensions and parts.
- `r22-canopy-clearance.json`: sampled overlap check.

Regenerate from the repository root:

```sh
blender -b -t 4 --python blender/refinements/r22/build_r22.py
blender -b -t 4 --python blender/refinements/r22/check_r22.py
blender -b -t 4 --python blender/refinements/r22/render_r22.py
```
