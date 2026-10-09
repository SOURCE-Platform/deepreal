# R23 integrated flat-roof enclosure

This revision follows the user's corrected side-profile drawing. The top is
flat over both drums, turns through a rounded rear corner, and continues
down the back. The lower body, flat top, center island, two outer supports,
and center fairing are Boolean-unioned into **one connected, manifold mesh**.
It is a single-piece appearance and packaging concept rather than an
assemblable manufacturing design.

The nominal roof underside is 32.8 mm above the model datum. The drum axis
is at 20 mm and the shell radius is 12 mm, leaving 0.8 mm nominal radial
clearance at the top. The front roof edge is at Y = -6 mm, behind the
camera-facing windows. The back corner has an 11.5 mm outer radius.

The R23 check found one connected mesh component, no non-manifold edges,
and no mesh intersections with the sampled rotating shell, end rings, or
lens elements at face 45° up / forward / 45° down and interaction forward /
22.5° down / 45° down. This does not verify manufacturing tolerance,
optical ray clearance, dust sealing, heat flow, fastening or assembly.

The one-piece shell creates an important assembly question: the drums and
bearings must be installed between fixed side and center supports. Bearing
bores, removable bearing retainers, and an insertion path are not modeled.
The R21 inner drum end is still solid beneath a provisional ring, and the
interaction wide lens envelope still conflicts with the inherited optical
carrier. Those details should be resolved before preparing a website render.

Files:

- `deepreal-integrated-flat-roof-r23.blend`: editable Blender model.
- `r23-exterior-preview.png`, `r23-side-preview.png`,
  `r23-above-preview.png`, `r23-low-pose-preview.png`: review images.
- `r23-enclosure-manifest.json`: dimensions and source.
- `r23-enclosure-check.json`: topology and sampled travel check.

Regenerate from the repository root:

```sh
blender -b -t 4 --python blender/refinements/r23/build_r23.py
blender -b -t 4 --python blender/refinements/r23/check_r23.py
blender -b -t 4 --python blender/refinements/r23/render_r23.py
```
