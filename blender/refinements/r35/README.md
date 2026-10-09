# R35 face-drum motion feasibility study

R35 follows [R34](../r34/README.md). It studies the two remaining face-drum
interfaces: how the outer axle reaches the drum wall, and how a moving optical
cable might reach the fixed center divider. This is **not** a release model.

## Outer end: a geometric load path exists

The new rotating disk/web overlaps the shaft, the rotating hub and a thin
sleeve at the drum sidewall. The sleeve also overlaps the rotating drum shell.
Together these envelopes show a continuous *intended* load path from drum wall
to shaft, while the stationary bearing stays separate. The sweep script finds
zero triangle intersections between these rotating envelopes and the fixed
bearing or enclosure at the rest pose. The web has only 0.3 mm **nominal axial**
space to the fixed bearing. That is a packaging observation, not a tolerance
or strength allowance. Separate meshes deliberately overlap where joints
would be needed; fits, fasteners, bearing retention and loads remain unproven.

## Inner end: the full-width twist route fails this layout

The red ribbon represents the existing 15.6 mm connector-end width at 0.2 mm
illustrative thickness. It twists from a rotating anchor to a fixed anchor.
`check_r35.py` tests four moving-anchor positions and two fixed-anchor
positions at 5° increments over −45° to +45°. **None of the eight candidate
routes clears the modeled parts.**

- The R21 upper/lower fixed-bearing webs and tabs intersect the ribbon at
  every pose, even when the fixed end stops before the enclosure.
- When the fixed end reaches into the center divider, the current enclosure
  intersects the ribbon at every pose; no fixed cable opening exists there.
- Longer torsion spans cross the moving optical carrier and, at some angles,
  the RGB or projector body. Shortening the span reduces those collisions but
  leaves the fixed support conflict and offers very little length for twist.

This corrects an easy overreading of R34: its 0.65 mm figure measured the
straight strip *inside the circular bearing opening*. R34 did not demonstrate
a routed moving cable past the bearing supports, optical payload and divider.
The R35 collision study does not prove every possible flex geometry fails; it
shows that a simple full-width axial twist cannot be dropped into this layout.
No bend-radius, copper-strain or life model has been claimed.

## Review artifacts

- `deepreal-face-motion-study-r35.blend`: editable study, with the failed
  cable candidate visibly red.
- `r35-outer-load-path.png`: isolated rotating web, hub, shaft and bearing.
- `r35-flex-center-conflict.png` and `r35-flex-up45-conflict.png`: internal
  conflict views. The drum shell is hidden so the contacts are visible.
- `r35-motion-check.json`: all sampled triangle-intersection results.
- `r35-motion-manifest.json`: objects and provisional anchor locations.

Regenerate from the repository root with Blender 5.2:

```sh
blender -b -t 4 --python blender/refinements/r35/build_r35.py
blender -b -t 4 --python blender/refinements/r35/check_r35.py
blender -b -t 4 --python blender/refinements/r35/render_r35.py
```

## Next design pass

1. Rebuild the fixed inner-bearing supports around an intentional cable
   window and add a protected path through the center divider.
2. Change the moving cable architecture or optical-carrier layout so the
   required contacts can traverse that window through the full face-drum
   travel. Candidate directions include a split harness from the head PCBA
   or a packaged flex loop; neither has been validated yet.
3. Re-sweep the exact new cable envelope, then check termination, minimum
   bend radius, strain relief, signal integrity and cycle life.
4. Turn the outer web overlaps into a specified rotating joint with selected
   bearing, loads, fastening and tolerances.
