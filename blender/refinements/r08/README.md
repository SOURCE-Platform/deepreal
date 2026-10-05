# DeepReal enclosure refinement R08

Open `deepreal-exterior-refinement-r08.blend` in Blender. This is a packaging
study kept inside the DeepReal folder. It is not an electrical, thermal, EMI,
or fabrication approval.

## Changes from R07

- The USB cable still enters at the bottom center of the exterior.
- The previously hidden original main-board J1 remains a reference to the
  current PCB. A separate, visibly modeled USB-C female **envelope** now sits
  on a centered daughterboard placeholder. No exact receptacle is selected.
- The internal amber path runs from that placeholder toward the product's
  right side, around the edge of the spreader, through a small rear-shield
  feedthrough, and to a proposed main-board connector location. In rear views,
  the product's right side appears on the image's left. The path represents
  intended power **and** data packaging. It is not routed electrical wiring.
- The thermal spreader and front shield lid use their original uncut meshes.
  The rear shield has one provisional 5 × 4 mm feedthrough at its right side
  instead of the 18 × 15 mm center channel.
- The housing has a socket clearance pocket and retains the centered plug
  chute. Saved Blender viewports use a 0.14 m orbit distance for close framing.
- No vents were added. The present model does not contain a defensible heat
  budget or validated path to ambient air, so vent size and placement cannot
  yet be chosen.

## How to inspect

The Outliner collection `00 — HOUSING MODE — CLICK EYE: SOLID ↔ WIREFRAME`
controls the solid housing. Turn its eye off to see the wireframe housing and
internal parts; turn it on to restore the solid housing. Keep `00A — WIREFRAME
FALLBACK — KEEP VISIBLE` enabled. This does not delete the housing.

Review images in `renders/`:

- `r08-exterior-front.png`: centered outside USB entry.
- `r08-internal-rear.png`: continuous spreader and side route.
- `r08-usb-side-route.png`: close view with the spreader visible.
- `r08-usb-path-exposed.png`: diagnostic view with the spreader and rear shield
  hidden **for that render only**, exposing the proposed route and PCB region.

## Unresolved engineering

The original PCB, schematic, and components were not edited. The daughterboard,
USB-C female envelope, internal flex path, and proposed main-board connector
have no selected parts, pin assignment, schematic, PCB routing, impedance
stackup, power-delivery design, ESD protection, shield termination, retention,
or bend-life validation. The female shell is a visual mating volume, not a
manufacturer package model. The native project currently has no verified
electrical connection from this new centered socket to the main PCB.

The 2.12 mm modeled PCB-to-spreader gap has no defined thermal interface.
The two thermal links and housing pads are still conceptual. Chip heat loads,
actual contact area, material, compression, chassis material, touch temperature,
monitor clearance, and ambient cooling remain unknown. A continuous spreader
improves the *geometry* of a possible heat path but does not prove cooling.
The rear shield feedthrough also requires an actual EMI and grounding design.

## Rebuild and verify

From `/Users/adam/Documents/deepreal`:

```sh
/opt/homebrew/bin/blender --background --python blender/refinements/r08/build_r08.py
/opt/homebrew/bin/blender --background blender/refinements/r08/deepreal-exterior-refinement-r08.blend --python blender/refinements/r08/verify_r08.py
/opt/homebrew/bin/blender --background --python blender/refinements/r08/render_r08.py
```

`r08-verification.json` records mesh comparisons, center placement, specific
intersection checks, viewport framing, and protected source hashes. Its `PASS`
means the listed geometric checks passed. `engineering_readiness` remains
`BLOCKED` by design.
