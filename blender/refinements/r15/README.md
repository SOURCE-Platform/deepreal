# DeepReal enclosure refinement R15

Open [deepreal-exterior-refinement-r15.blend](deepreal-exterior-refinement-r15.blend) in Blender. This version builds on R14. The R14, R13, and native PCB source files were left unchanged.

## What changed

- The dark drive ring at each outer drum end is now **inside** the drum's 21 mm inner cavity. Its 20.9 mm outside diameter leaves a nominal 0.05 mm radial gap to the shell. The outer end face is flat. The ring, axle, optical head parts, and rear cover move together using a drum pivot.
- Each drum has a **90° rear quarter opening** over 48.5 mm of its length. This is an assembly access opening for the optical head board and its wiring. A separate removable cover closes it during normal use. A small seam remains visible.
- The motors, pinions, brackets, and encoder boards have been repositioned as compact visual envelopes near the two outer ends. The motor and encoder are fixed; the shell, axle, gear, and magnet rotate.
- The head power/data path is shown through a slot in each fixed outer end cap to the J2/J3 area of the main board. Motor and encoder routes lead toward the J4/J5 area. These are visual paths, not electrically verified connections.
- Pivot controls show a **proposed 150° optical movement** from 75° up to 75° down. This is a review range, not a motor control or mechanical hard stop.

## Inspect in Blender

In the Outliner, use the eye beside these collections:

| Collection | What the eye does |
| --- | --- |
| `00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME` | Switches between the solid housing and its wireframe fallback. |
| `01 — DRUM SHELLS — CLICK EYE FOR INTERNALS` | Hides or shows the drum shells. |
| `01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS` | Removes or installs both access covers for inspection. |

To inspect movement, select `Face_Rotating_Drum_Pivot_R15` or `Interaction_Rotating_Drum_Pivot_R15` in collection `08 — DRUM TRAVEL PIVOTS — 150 DEGREE STUDY`, then change its local **X Rotation**:

| Drum | Up stop | Saved position | Down stop |
| --- | ---: | ---: | ---: |
| Face | −75° | 0° | +75° |
| Interaction | −120° | 0° (optics point 45° down) | +30° |

The amber head cable is drawn only in the saved position. Hide collection `07C — MOTOR + HEAD ROUTES — CONCEPT` when evaluating other angles; its moving service loop has not been designed.

## Review images

- [Assembled front](renders/r15-assembled-front.png)
- [Flat outer end face](renders/r15-flat-end-face.png)
- [Rear covers installed](renders/r15-rear-covers-closed.png)
- [Rear access open for assembly](renders/r15-rear-access-open.png)
- [Downward stop with covers installed](renders/r15-down75-covers-closed.png)
- [Downward stop with covers removed](renders/r15-down75-covers-removed.png)
- [Downward stop from below, covers removed](renders/r15-down75-from-below-covers-removed.png)
- [Downward stop from below, covers installed](renders/r15-down75-from-below-covers-installed.png)
- [Internal ring drive study](renders/r15-internal-ring-drive-study.png)

The downward stop images show why the opening needs a cover: without it, the cavity is visible from above and the front housing opening. From below, looking up toward the downward-pointing sensors, the opening is hidden behind the near side of the drum. The cover stays on the rotating drum in normal use.

## Engineering status

**Visual mechanical study. Not ready for fabrication or product claims.** The ring and pinion are smooth envelopes with no teeth, coupling, backlash, bearings, or torque analysis. The motor and encoder are unselected size studies. The cover still needs fastening, sealing, and structural checks. The head flex needs a moving service loop, a chosen cable, strain relief, and cycle testing. Stops, full optical field of view, shock, thermal behavior, and assembly sequence need review with a mechanical and electrical engineer.

Run `blender -b -t 4 --python blender/refinements/r15/verify_r15.py` from the DeepReal root to check manifold geometry, static source preservation, saved visibility, and **sampled** part intersections and lens center rays. The result is [r15-verification.json](r15-verification.json). The sampled checks do not prove real tolerances or full-field clearance.
