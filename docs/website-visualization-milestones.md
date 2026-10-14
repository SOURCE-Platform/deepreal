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
the underside of each conceptual head board. The web-only optical carriers
now have a separate service opening and recessed module seats. This avoids
overlap with the visible IR and
projector bodies without moving those optics or changing the R36 `.blend`.
The interaction-side J1 and ribbon start in the gap behind the IR and
projector bodies rather than inside the wide RGB camera. The conceptual
motor lead uses a separate lane. The rear board offsets keep the first short
arcs clear of the rebuilt carriers; the ribbon starts use each head board's
actual transform,
including the interaction board's tilt. The 51-contact connector, its
footprint, retention, rear-side board access and carrier pocket are **not**
approved for assembly. Both ribbons leave the head boards above the shield,
pass behind the PCB and return below its lower edge toward the main-board
J2/J3 envelopes. The separate motor and angle-sensor leads approach the
J4/J5 proxy areas in distinct visual lanes; the angle-sensor ends follow the
cheek boards during the peel.

The green camera squares are 10.8 × 10.8 mm sensor assembly envelopes,
not complete Raspberry Pi camera PCBs. The face head now uses the standard
SA31VA30P envelope (Ø5.75 × 6.98 mm lens, 66° × 41° field axes), replacing
its smaller placeholder at the retained visual lens-nose datum. The
interaction head retains the wide SA36VA30P envelope (Ø6.95 × 8.3 mm lens,
102° × 67° field axes). Their 0.6 mm sensor plates are display assumptions,
not complete manufacturer CAD. R36 and the public exterior GLB are
unchanged. This is not a released camera mount or PCB.

### Two-head camera support and common-board proposal

`blender/web_camera_mount.py` applies the proposal to evaluated web meshes,
without saving the R36 source. Each head has
an insulating rear saddle, four provisional bonded seats against the sensor
rear face, two carrier-contact anchors and four head-board spacers. Board
keepouts let the saddle posts pass without intersecting the board. No screw
holes are invented in the sensor, and no clamp touches the lens or autofocus
mechanism. The bond sites and carrier/board retention remain unapproved.

Both board proxies use one 47.3 × 12 × 0.6 mm outline and shared keepouts,
shortened from 48.05 mm to clear the face outer hub. They represent two
physical boards intended to share one controlled PCB design, not two
released layouts. The face board sits 1.72–2.32 mm behind its camera datum
to clear its optical carrier; the interaction board sits 1.0–1.6 mm behind
its datum. J1 uses the same staged mesh and local position on both boards.
The face long-FPC departure moves to that common J1 position and leaves
straight in world X; the interaction expanded route is unchanged.
A shared 7.6 × 2.6 × 0.98 mm rear J2 keepout represents a proposed
sensor-to-board mating stack, **not** manufacturer connector CAD.
DF37NC-30DS-0.4V remains the electrical baseline; the standard sensor
drawing names HLM-033M-3002-76. Compatibility with that plug and the exact
wide assembly is not established.

Each illustrated sensor tail uses the product brief's 8.9 mm width and
7.3 mm flat length as a centerline budget, with a 0.13 mm display thickness.
It exits the upper edge and folds behind the sensor toward rear J2, at
nominal radii of 1.565 mm for face and 1.205 mm for interaction. A proposed
180° sensor orientation around each optical axis retains its horizontal
and vertical field axes; a 90° turn would swap them. Image orientation
and calibration still need review. Both short tails now use physical-distance
UVs and the long FPCs' translucent amber color/normal artwork, with 30
illustrative conductor bands at a 0.28 mm display pitch. That artwork is
not an actual contact pitch, copper layout, pin map or shielding design.
The terminal notch, exact tail/plug geometry and formed stacks are omitted.
The standard drawing's 0.8 mm bend-radius / 20-assembly-bend note does not
qualify either illustrated formed stack, the wide tail or dynamic head flex.

#### Optical-carrier and module-seat proposal

Both black optical carriers are rebuilt as 33.85 × 12 × 1 mm envelopes
with a separate 14.1 × 7.8 mm service window between the depth module and
projector. The window stops before the projector footprint. The carrier
rear planes, PCB-spacer contacts and RGB-saddle anchors are retained.
No optical module, lens, aperture or optical direction moves.

The old projector bracket intersected the carrier while leaving a 0.3 mm
gap to the projector body. Its web mesh is now a 6.6 × 7 × 0.5 mm seat
in a matching 0.5 mm carrier recess, rather than a penetrating rear block.
Each depth module has an 8.15 × 8.8 × 1 mm rear seat in its own recess.
Separate 0.1 mm provisional bond layers meet the module rear faces and
seat fronts. No module screw holes or lens clamps are invented. The depth
body retains a 0.25 mm left overhang, supported by an inset rear bond area.
This is a nominal contact/layout proposal: seat retention, allowable bond
sites, adhesive, joint strength, loads, thermal paths, serviceability,
materials and tolerances remain unapproved.

The exported proposal was checked with
`blender/audit_web_camera_mount.py`. The GLB hash is
`fee55af0d30db02b063da30bad8aaa623ffc2aa04243b936750122384538d004`
(1,555,328 bytes), installed with its matching manifest in both repositories.
Against the immutable preceding `160ab430d25e10c1…` export, 108 retained
meshes have unchanged world-space vertex inventories. Only the two optical
carriers and two projector-bracket web meshes may change. All optical
modules, boards, cables and RGB supports are preserved. Six added seat/bond
meshes belong to their respective head groups. Checks found:

- No unintended surface crossings in 5,420 proposed-part/board/carrier
  pairs against the exported rest hardware and exterior.
- 54 declared mating pairs, sampled at vertices and triangle centers,
  with maximum gap 0.000009 mm and zero sampled intrusion. These are
  intentional contacts, not collision failures.
- No inherited carrier/bracket overlap exemption. Both seat/carrier
  interfaces must pass the same sampled contact checks as the new bonds.
  Seven named optical-envelope or conceptual connector-insertion overlaps
  remain classified separately.
- Common board, J1 and J2 local surfaces match within 0.001 mm after GLB
  roundtrip. This establishes conditional proxy fit, not electrical
  interchangeability or a routed common PCB.
- No surface crossings between the rigid proposal and tested fixed
  hardware/exterior at nine face poses from −45° to +45° in 11.25° steps
  and five interaction poses from 0° to 45° down. Dynamic head, motor and
  encoder cables are excluded from this pose study.
- Sampled rest gaps to the rotating shell for tail/board/saddle of
  3.056/4.278/4.575 mm (face) and 3.596/4.406/4.575 mm (interaction).
- No hits in 45 face and 27 interaction ideal chief rays. Rays start at
  the provisional lens noses, not optical pupils. This does **not** validate
  window clipping, glazing, refraction, focus or optical performance.

The audit uses millimetre-scale BVH triangle intersections, double-precision
point-to-triangle distances and bounded odd/even containment samples at
mating interfaces. Ten numerical regressions cover distances, thin
triangles, touching, intrusion, separation and both heads' six module-seat
interfaces, including unchanged module geometry. It does not compute exact
solid intersection volumes, continuous minimum clearance, full swept
volumes or tolerance stacks. All four conceptual cable landings passed.
The rest-pair checks include both rebuilt carriers and new seats against
the expanded cables. The prior sampled ribbon curvature and 50/82 mm final
reveal spacing remain applicable to the unchanged cables and rear layers;
they were not rerun for this carrier-only change.

Four material-aware Cycles JPEG views were reviewed, front and oblique for
each head. All are intact. They show the projector over a solid carrier
region, its separate seat margin, the depth-module rear seat and a service
window clear of either module footprint. The larger interaction lens,
RGB support and textured short tails remain visible. These offline renders
are not live WebGL or mobile visual verification.

Regenerate the four views in an empty Blender process:

```sh
DEEPREAL_WEB_ASSEMBLY_OUT=/absolute/path/deepreal-assembly-review.glb \
  blender -b -t 4 --python-exit-code 1 \
  --python blender/render_web_optical_support.py
```

Ten Blender regression tests and Python syntax checks passed for this
candidate, along with both repositories' diff checks. The installed
GLB/manifest hash was verified through the local server and embedded
browser. Both head filters show their titles and proposal badges with an
active WebGL context. At 390 × 844, viewport/toolbar/notch assertions passed
for both filters without document overflow. Both new mobile JPEG captures
are intact and show the separate module seats and service window; their
small scale does not supply detailed material or tolerance verification.

The preceding viewer version passed ten tests, focused
TypeScript, scoped ESLint, all stage/filter assertions and viewport checks
at 1600 × 900, 1280 × 800 and 390 × 844. No viewer code changes are needed
for the added head-group meshes. Its desktop captures repeated image
sections and were rejected as evidence; desktop visual signoff remains
open. The full-site typecheck was not repeated after earlier unrelated
failures. The route retains its production `notFound()` guard.

Run the audit with the same R36 file loaded as the exporter:

```sh
blender -b -t 4 blender/refinements/r36/deepreal-inner-bearing-window-r36.blend \
  --python-exit-code 1 --python blender/audit_web_camera_mount.py
```

`DEEPREAL_WEB_ASSEMBLY_OUT` selects an isolated candidate GLB. The audit
writes `camera-mount-audit.json` beside it. Optionally set
`DEEPREAL_WEB_ASSEMBLY_BASELINE` to a saved preceding GLB to check preservation;
it does not assume the site's installed asset is an immutable baseline.
The audit also reads the sibling site's unchanged public exterior GLB.

One common controlled head-PCB design/population remains the target.
The two-head shape proposal does not release a PCB architecture.
Native schematic/PCB routing, wide-camera
connector/pinout/autofocus support, allowable bond sites, materials,
adhesive loads, anchoring, service access and thermal paths remain gates.
So do full optical validation and a housed moving flex. The development
viewer identifies both heads' camera support as a proposal; its reveal choreography
does not rotate the head or demonstrate a physical teardown.

### Expanded head-flex study

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
These samples are **not** exact continuous minimum clearances.
Rest-pose checks do not
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

### Development-only detailed main-board view

All parts again uses the earlier R36 mechanical board proposal, including its
right-side USB wing and original connector envelopes. The attempted native
board overlay was withdrawn after component clashes and interface mismatches
were confirmed.

The Main board filter keeps the retained native layout separate: 234 component
bodies, native pads, solder mask and silkscreen, with 18 missing-model envelopes
identified. It is labeled **Native PCB layout, known clashes**, not shown as
the assembled device's board. Its component placement, footprints, connectors
and package fit need correction before reuse in the assembly. It adds no routing.
The detailed GLB
stays outside site `public/` and is served only in development, without
changing publication or fabrication permissions.

See the [PCB viewer detail checkpoint](design/pcb-viewer-detail-checkpoint-2026-10-13.md)
for source hashes, transport checks, accepted desktop/mobile captures,
browser-test limitations and the pre-existing native-import status mismatch.
