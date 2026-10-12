# DeepReal website visualization milestones

The near-term deliverable is an investor-facing view of the device on the
SOURCE public site. Fabrication readiness is a later engineering milestone.
The site model must stay traceable to this repository's Blender source.

## 1. Exterior model

The `/deepreal` Three.js viewer loads `public/models/deepreal.glb`. Its current
export uses the R38 exterior mount study, based on R36 (R37 changes only
hidden cable-space reservations). The visible export includes the R30
enclosure with its old narrow pad absorbed into a continuous inner leg, a
separate 112 × 26 mm metal-finish magnetic face matching the R32 laptop-side
plate, both exposed-top
drums, lens details, and the USB plug with its longer molded handle, separate
cable sleeve, small logo mark and 3.2 mm visual cable descending from the
right underside. The website fades
the free cable end to hide the artificial cut. It does not include the
temporary monitor or laptop references.
The magnetic mount's actual material, retention and holding force are open.

Rebuild from the DeepReal repository root with Blender 5.2:

```sh
blender -b -t 4 --python-exit-code 1 --python blender/refinements/r38/build_r38.py
blender -b -t 4 blender/refinements/r38/deepreal-exterior-mount-r38.blend \
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
2. Retract the USB plug and pigtail together while the enclosure is opaque.
   Keep the unplugged lead visible and carry it rearward with the enclosure
   during the rest of the reveal, without ghosting the plug.
   The visual exterior does not establish a selected receptacle or tested
   insertion and removal loads.
3. Make the one-piece enclosure a low-opacity ghost before sliding it behind
   the drums. Keep the drums and internal assemblies in place. Do not show
   the conceptual cables while the enclosure still surrounds the device.
4. After the enclosure finishes sliding behind the drums, ghost the shield
   lid and rear tray together and move them behind the PCB as one assembly
   without separating the front panel. Move the ghosted thermal spreader
   behind them. Once those layers stop, fade in all six conceptual paths as
   an expanded cable study. These are not installed routes emerging from
   the housing or a simulated gravity release. From back to front, show the
   enclosure, spreader, shield assembly and PCB. The lid and tray remain
   separate Blender meshes; this animation does not establish how they are
   joined. Distinguish the moving head flex from stationary motor/encoder
   wiring.
5. Keep all six conceptual paths visible and attached to their endpoints.
   Ghost the drum exteriors before lifting them above the internals, then
   restore their solid appearance once clear. Leave the main board, head
   carriers, optics, motors and their wiring at rest during the lift.
6. Ghost the inner rings, bearing envelopes, ring gears, outer end plates and
   cheek angle-sensor proxies, then peel them outward to expose each head
   board. Restore their solid appearance once clear and keep them in the
   final view. Bend each angle-sensor lead so its cheek end follows the
   moving sensor board while its main-board end stays fixed. Leave the two
   separate fixed motor cantilevers at the center. This is not a validated
   physical assembly or teardown order.

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
bearing support. The interaction drum's flex and fixed harness are still
rest-pose concepts. The site must identify this assembly view as a concept
until the connector selection, moving paths and motion envelopes are resolved.

The grouped internal GLB is available for local review. Regenerate it from the
R36 source with Blender 5.2:

```sh
blender -b -t 4 blender/refinements/r36/deepreal-inner-bearing-window-r36.blend \
  --python-exit-code 1 --python blender/export_web_assembly.py
```

Copy the GLB and its SHA-256 provenance manifest from
`blender/review-output/web/` into the site's `public/models/` directory. The
amber color and normal-map images are generated by
`blender/web_assembly_cables.py` and embedded in the GLB, so no separate
texture files are needed.

The site's development-only `/deepreal/assembly-review` route retracts the USB
lead and keeps it alongside the retreating enclosure. All six concept cables
remain hidden until the shell, shield and spreader finish sliding backward,
then fade in as an expanded study with their current curves unchanged. This
is a change in presentation, not a stowed cable pose or a mechanical release.
The route ghosts and lifts the drum exteriors, then restores them to solid
while the concept cables remain visible. The axial hardware ghosts and peels
outward, keeping the head boards exposed and the sensor leads visually
attached to their moving cheek boards.

`blender/web_assembly_cables.py` now shows both head-to-J2/J3 optical links as
15.6 mm wide custom FPC concepts, matching the planned 51-contact mating-end
width without inventing a narrower trunk. The 0.16 mm body and 0.20 mm
connector-end thickness are illustration values, not a selected dynamic
stack-up or a bend-life claim. UV artwork gives the amber film translucent
spaces, opaque fine copper-colored lines at a 0.3 mm contact pitch, brighter
ends and a subtle light-reactive normal map. Those 51 lines convey contact
density; they do not define electrical continuity, impedance, shielding,
layer count or numbered pinout. Any actual copper plane or shield could make
the finished flex less translucent.

`blender/export_web_assembly.py` widens the two web-only head connector
envelopes from 5 mm to the proposed 16.8 × 3.2 × 1.0 mm body, seats them on
the underside of each conceptual head board and cuts a local pocket in each
web-only optical carrier proxy. This avoids overlap with the visible IR and
projector bodies without moving those optics or changing the R36 `.blend`.
The interaction-side J1 and ribbon start in the gap behind the IR and
projector bodies rather than inside the wide RGB camera. The conceptual
motor lead uses a separate lane. The carrier pockets keep the first short
arcs clear; the ribbon starts use each head board's actual transform,
including the interaction board's tilt. The 51-contact connector, its
footprint, retention, rear-side board access and carrier pocket are **not**
approved for assembly. Both ribbons leave the head boards above the shield,
pass behind the PCB and return below its lower edge toward the main-board
J2/J3 envelopes. The separate motor and angle-sensor leads approach the
J4/J5 proxy areas in distinct visual lanes; the angle-sensor ends follow the
cheek boards during the peel.

The green square on the interaction drum is the inherited R20 wide-angle
RGB assembly envelope. The face drum has a different, smaller RGB module
proxy. They are not two depictions of the same selected camera. A prior
rest-pose check omitted the wide RGB board and lens: in the older local GLB,
both crossed the interaction ribbon, head-board/carrier proxies and J1.
For this web export only, the interaction head-board and dark optical-carrier
proxies end before that camera, leaving a visible 2.5 mm lateral gap.
The camera envelope remains in its original location, visibly separate and
**without a demonstrated mount or connection to the head board**. The cutaway
removes the overlap; it does not solve the camera mount, shared PCB, electrical
connection or optical package. R36 and the public exterior GLB are unchanged.

The FPC mesh uses a 16 mm head departure arc, a short rearward stem above the
shield, a rounded rear sweep with quintic lateral easing, and a nominal 16 mm
lower return. Each cross section keeps the full width projected perpendicular
to the centerline, instead of fanning it around a tight turn in its own plane.
The exporter rejects reversed frames, ribbon edges that double back, and
interaction-side camera/J1/ring-gear rest-pose crossings.
Sampled minimum centerline curvature radii reconstructed from exported UV
sections are 11.311 mm for the face ribbon and 11.344 mm for the interaction
ribbon, rather than the prior 1.9–2.1 mm. This is a visual comparison,
**not** a specified DeepReal bend limit or a copper strain/life calculation.
The translucent film and contact-density artwork are preserved.

The main-board tips now end at y=9.85 mm. All four exported section corners
at each J1 and J2/J3 endpoint fall within the corresponding conceptual
connector's bounding box; this does not verify a mating contact or footprint.
Exported rest-pose triangle checks now include both wide RGB envelopes, IR
and projector bodies, the PCB, head boards, carriers, shield, spreader,
same-side motor and angle leads, other FPC, and bearing, ring, motor and
encoder parts. None of the 61 tested ribbon/obstacle pairs crossed. A
separate broad interaction-side audit found no crossings between the wide
RGB board, lens, J1 or ribbon and 32 nearby exported meshes (excluding
interactions among those four). J1 does not cross either camera envelope;
the ribbon does not cross either one or J1's neighboring optics.
Sampled vertex-to-surface gaps include approximately 1.15 mm at the
interaction ring gear, 2.685 mm at its optical carrier, 3.25 mm at its
head board, and 10 mm from the camera board to the ribbon. These samples
are **not** exact continuous minimum clearances. Rest-pose checks do not
establish a mounted camera, safe drum motion, enclosure clearance,
acceptable dynamic bends, fatigue life, electrical function or
manufacturability. The full-width motion studies in R35–R37 still block
an engineered moving loop. These are not approved cable designs. This
route is a composition and pacing test, not the accepted second milestone.

The larger loops **do not fit the current enclosure**. The exterior shell's
rest-pose bounds reach about 29 mm below the web origin and 22.5 mm rearward;
the ribbons reach about 45.93 mm below and 41.65 mm rearward. The animation
pulls the shell backward before showing the ribbons, so they do not appear
outside a still-occupied housing. It does not show where they would fit inside
the device. A new package envelope or a different cable architecture, along
with collision and motion studies, is required before depicting a working
head connection. The optical FPCs remain at rest while the reveal lifts drum
exteriors; that presentation is not a rotation or assembly test.

The reveal previously slid the lid and tray 24 mm rearward, cutting both
optical ribbons in the exploded pose; the spreader crossed them partway
through its 31 mm slide. Exported rest-pose checks did not cover those moving
positions. A first clear version withdrew the three rear layers 40 mm and
the shell 90 mm, but left only about 5 mm between the cables and shield and
about 21 mm between the spreader and shell. In the marked-up follow-up, the
development viewer now withdraws the lid, tray and spreader 50 mm and the
shell and USB lead 82 mm. In exported coordinates, the farthest ribbon
surface reaches 41.65 mm rearward, while the final lid starts at 56.58 mm,
tray at 56.8 mm, spreader at 64.22 mm and shell at 68.5 mm. The minimum
rear-axis separation is 14.93 mm between cable and lid and 2.92 mm between
spreader and shell. Triangle checks found no crossings among the six cable
meshes and the three rear layers, or between those layers and the shell, in
the displayed pose. The cables stay hidden while the layers pass through
their volume and appear from 0.49 to the Inside stage at 0.57. These are
viewer offsets, **not** longer thermal or shield parts or a larger housing:
they do not establish a valid assembly sequence, thermal contact in the
exploded pose, or an enclosure that can hold the loops.

Acceptance: three board assemblies and their major functional components are
present, each depicted head cable visibly reaches the main-board area, and
motor/angle-sensor wiring is distinguishable. The reveal and explosion can be
paused, reversed, and viewed on mobile. The presentation does not claim that
the PCB layout, cable bend life, or manufacturability is validated.
