# R18 rear-only drum support visibility study

Open [the R18 Blender mockup](deepreal-rear-support-study-r18.blend). This file is an experiment based on R16. It is **not** the next validated device assembly.

Each drum has a fixed rear yoke with two arms reaching toward bearing envelopes near opposite ends. The old exposed outer drive and encoder proxies were removed for this visibility study. The outer circular faces rotate with the drums; there is no R17 fixed side sleeve or added outer cap. The bearings shown are placeholders and have **no designed load path into the rotating shell** yet. Motor, encoder, head-cable flex, enclosure fasteners and assembly order are not designed in this mockup.

## What the sweep shows

The arm openings are narrow along each drum's length: 3.2 mm around each arm. They must be long around its circumference because the arms stay still while the drum turns.

| Drum | Studied optical travel | Trial slot around circumference | Front view result |
| --- | --- | --- | --- |
| Face | -75° to +75° | 186° including rough arm clearance | The slots face forward near both travel ends and are visible in the renders. |
| Interaction | 45° to 75° downward | 42° including rough arm clearance | The slots remain rear-facing in the sampled front views. |

See the [neutral front view](renders/r18-face-zero-front.png), [face drum at +75°](renders/r18-face-plus75-front.png), [face drum at -75°](renders/r18-face-minus75-front.png), [interaction drum at 75°](renders/r18-interaction-75-front.png), and [rear support view with the housing hidden](renders/r18-rear-support-access.png). The [machine-readable sweep check](r18-sweep-check.json) records sampled arm-to-shell intersections as well as potential front-facing angular exposure. **The clearance check still reports intersections**, so the exact slot/arm shape is not approved even as a working mechanism.

## Decision from this study

Two simple fixed rear arms passing through the rotating face drum cannot preserve an unbroken cylinder from the front throughout a 150° sweep. Making the slots thinner along the drum reduces their visual size but does not stop them from turning toward the viewer. The smaller interaction-drum sweep is more promising, but its final range has not been selected.

The concept needs a deliberate tradeoff before detailed motor and encoder placement: accept visible narrow slots at some angles; reduce the face drum's required travel if the optics permit it; or change how its bearings are supported so no fixed arm crosses its rotating cylindrical surface. Do not infer bearing stiffness, fatigue life, cable life, or manufacturability from this visual study.
