# R17 enclosed drum-end packaging study

Open [the R17 Blender model](deepreal-exterior-refinement-r17.blend). This revision starts from R16 and leaves that file unchanged. It tests how to cover the encoder, drive, support, and head-cable exit at both outer drum ends.

## What moves and what stays fixed

- Each sensor drum, optical head, axle, shaft magnet, and motor rotor hub rotate together.
- A fixed chamber at each outer end contains a compact magnetic encoder board, an encoder sensor, motor stator envelope, and mounts. A smooth cap closes the side seen by a viewer. The chamber is part of the drum assembly but **does not rotate** with the drum.
- The previous exposed encoder board, motor bracket, pinion, and ring gear have been replaced in this concept. Curved pockets in the upper housing accommodate the closed end chambers.
- The head's power/data lead follows the rotating drum to a near-axis opening in the chamber. A protected loop is illustrated inside the chamber; fixed head, motor, and encoder leads then leave through a rear outlet inside the housing. The visible orange lead in the housing-hidden view is **behind** the enclosed side face.

The motor is a **coaxial annular envelope**: a ring-shaped motor concept around the axle. No purchasable motor, torque rating, driver, winding arrangement, or shaft coupling has been selected. The encoder PCB and sensor are also dimensional placeholders, not a completed electrical design.

## Review in Blender

In the Outliner, use `00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME` and `00A — WIREFRAME FALLBACK — KEEP VISIBLE` to swap the housing display. Collection `09 — R17 ENCLOSED OUTER DRUM MODULES — FIXED` contains the new end chambers and internal drive and encoder proxies. The saved model has its end caps closed. The separate [access review render](renders/r17-face-access-review.png) temporarily hides the left cap and sleeve for inspection; it does not alter the model.

Other review images: [front](renders/r17-front-enclosed.png), [face side](renders/r17-face-side-enclosed.png), [interaction side](renders/r17-interaction-side-enclosed.png), and [housing hidden](renders/r17-internal-module.png).

## Checks and remaining work

Run `blender -b -t 4 --python blender/refinements/r17/verify_r17.py` from the repository root. The [verification report](r17-verification.json) samples both drums from -75° through +75° in 15° increments. It checks side coverage, cable intersections with the modeled fixed shell, gross moving-part clearance, lens-center clearance, topology of the new shell pieces, and preservation of R16 optics and thermal parts. These are geometric checks, not proof of manufacturability.

Before a build, choose a real motor and encoder, confirm torque and thermal behavior, design shaft bearings and load path, choose the flexible cable and its connector, validate its entire moving shape and bend life, route actual power/data nets, and check housing strength, sealing, fasteners, and tolerances. The saved cable loop depicts one rest pose only. The interaction drum's final travel limits remain open.
