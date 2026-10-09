# R36 inner-bearing cable window study

R36 continues the [R35 motion study](../r35/README.md). It keeps the exposed
drum exterior and the R35 outer-shaft web. This revision changes only the
**face drum's fixed inner-bearing support**; the interaction drum is unchanged.

## What changed

The R21 upper and lower bearing tabs crossed a full-width cable even at the
straight-ahead pose. R36 replaces them with a thin fixed **axial neck** that
extends toward the center divider beyond the rotating inner lip. Two short
side webs connect that neck to the enclosure from the left and right of the
cable opening. The moving straight strip remains 15.6 mm wide, matching the
documented connector-end width.

The R36 model's sampled −45° to +45° face-drum sweep, every 5°, records:

- Intended mesh contacts from each side web to the axial neck and enclosure,
  and from the neck to the fixed bearing envelope.
- Zero mesh intersections of the new fixed supports with the rotating inner
  race, rotating lip or drum shell.
- Zero mesh intersections of the **straight** full-width exit segment with
  the modeled bearing, supports, motor, housing, drum shell and optical
  carriers at those sampled poses.

The neck's nominal outer radius is 8.9 mm, while the rotating lip's nominal
inner radius is 9.15 mm: just 0.25 mm radial space before tolerances. The
flex's corner radius is about 7.8 mm inside an 8.45 mm bore. These are
packaging measurements, not bearing or cable clearances approved for manufacture.

## What still blocks a moving cable

The straight strip stops before it connects to a fixed harness. The R35
full-width axial-twist route still crosses the optical carrier. As a separate
screen, `probe_r36.py` tested 6–8 mm trunk widths at three moving-anchor
positions. `probe_offset_r36.py` tested 6 and 7 mm trunks with up to 3 mm of
offset toward the motor. **None of these simple twist routes was collision
free.** Width reduction cleared the old bearing tabs, but did not resolve the
carrier conflict; moving the strip toward the motor traded carrier contacts
for motor contacts. `map_conflict_r36.py` localizes representative contacts
along the inner optical carrier rather than assuming a small end relief would
fix them.

The 15.6 mm number is the **mating end width** of the 51-contact connector.
It does not approve a narrower dynamic trunk, a multilayer flex, split tails
or changes to the six differential-pair routes. Those need a real electrical
stack-up and signal-integrity review before selection.

The next mechanical study should reserve a service-loop chamber outside the
current optical-carrier and motor envelopes, with a protected route through
the fixed center divider. It must retain bearing support and the visible
exterior. Then a cable vendor or electrical designer must validate bend
radius, copper strain, terminations, impedance and cycle life.

## Files and reproduction

- `deepreal-inner-bearing-window-r36.blend`: editable support study.
- `r36-bearing-window-end.png` and `r36-bearing-window-side.png`: internal
  support views with the drum skin hidden.
- `r36-support-check.json`: sampled fixed/moving geometry checks.
- `r36-width-screen.json` and `r36-offset-screen.json`: exploratory moving
  cable screens against the unchanged R35 carrier and motor layout.
- `r36-support-manifest.json`: changed objects and remaining open work.

Run from the repository root with Blender 5.2:

```sh
blender -b -t 4 --python blender/refinements/r36/probe_r36.py
blender -b -t 4 --python blender/refinements/r36/probe_offset_r36.py
blender -b -t 4 --python blender/refinements/r36/map_conflict_r36.py
blender -b -t 4 --python blender/refinements/r36/build_r36.py
blender -b -t 4 --python blender/refinements/r36/check_r36.py
blender -b -t 4 --python blender/refinements/r36/render_r36.py
```
