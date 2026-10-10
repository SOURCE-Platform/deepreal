# DeepReal website visualization milestones

The near-term deliverable is an investor-facing view of the device on the
SOURCE public site. Fabrication readiness is a later engineering milestone.
The site model must stay traceable to this repository's Blender source.

## 1. Exterior model

The `/deepreal` Three.js viewer loads `public/models/deepreal.glb`. Its current
export uses the R36 assembly because R37 changes only hidden cable-space
reservations. The visible export includes the R30 enclosure, both exposed-top
drums, lens details, and the USB plug and cable descending from the right
underside. It does not include the temporary monitor or laptop references.

Rebuild from the DeepReal repository root with Blender 5.2:

```sh
blender -b -t 4 blender/refinements/r36/deepreal-inner-bearing-window-r36.blend \
  --python-exit-code 1 --python blender/export_web_exterior.py
```

Set `DEEPREAL_WEB_OUT` to override the default sibling
`source-public-site/public/models/deepreal.glb` destination. The exporter
writes a SHA-256 provenance manifest beside the GLB. Review the model at
`http://localhost:3001/deepreal` on desktop and mobile before publishing.

Acceptance: the model loads, can be orbited, shows the front optics, exposed
drum tops, integrated center and side supports, monitor ledge, and USB cable.
The cable remains visible through a full orbit and the model fits its viewer.

## 2. Internal reveal and exploded sequence

Use the same coordinate system as the exterior GLB. The animation should:

1. Start at the intact exterior.
2. Fade the enclosure skin while preserving the drum and optic positions.
3. Show the internal assembly at rest: main board in the leg, one optical
   carrier board in each drum, optics, motors, bearings, angle sensing, USB
   entry, and the two head-to-main electrical paths.
4. Spread those assemblies apart enough to identify them, then return to the
   intact device. Group each drum's moving parts with its own board and optics;
   keep its stationary motor, bearing race, and angle sensor in the housing
   group. Distinguish moving head flex from stationary motor/encoder wiring.

The present Blender file has a proposed main-board outline, two conceptual
head-carrier boards and optical components. The KiCad main board is an
engineering review import marked `PCBA_PublicAllowed=False`: it has no routed
tracks, and some footprints and package models are unverified. Do not export
that import to the public site as if it were a finished PCB. The display board
can show the planned major functions without decorative or invented traces.

The wiring geometry needs another mechanical pass before the internal view is
ready. R36 has a straight face-drum exit but no collision-free moving loop or
fixed termination. R37 demonstrates that the proposed rear chamber is too
small for its cited dynamic-flex example and would cut through the existing
bearing support. The interaction drum's current flex and fixed harness are
rest-pose proxies only. Model both complete paths as explicit visual concepts,
then check their endpoints and motion envelopes. The site must identify this
assembly view as a concept until these connections are resolved.

An initial grouped internal GLB is available for local review. Generate it
with `blender/export_web_assembly.py`, then copy the resulting GLB and manifest
from `blender/review-output/web/` into the site's `public/models/` directory.
The site's development-only `/deepreal/assembly-review` route fades the shell
and separates the main, stationary, face and interaction groups. For review it
adds two optical ribbons, two stationary motor leads and two stationary angle
sensor leads. Those six paths connect visual endpoints, but have not passed
geometry or electrical checks; they are not approved cable designs. This route
is a composition and pacing test, not the accepted second milestone.

Acceptance: three board assemblies and their major functional components are
present, each depicted head cable visibly reaches the main-board area, and
motor/angle-sensor wiring is distinguishable. The reveal and explosion can be
paused, reversed, and viewed on mobile. The presentation does not claim that
the PCB layout, cable bend life, or manufacturability is validated.
