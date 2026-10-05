# DeepReal exterior refinement R11 — optics and drum ends

Open `deepreal-exterior-refinement-r11.blend` in Blender. It is the next
reviewable presentation model and keeps the R10 USB/board study unchanged.
It is not a validated mechanical or optical design.

## What was wrong

The interaction drum's five bores were baked at a 45° downward angle, but an
earlier refinement deleted the optics pivot while retaining only its visible
lens meshes. Their positions reverted to the forward-facing rest plane. In
R10, rays through all five interaction lens centers hit the drum shell instead
of passing through the intended openings. The face drum's five openings were
already aligned.

## What changed

- Rotated every visible interaction lens component 45° around the drum axis.
  The shell bores, face drum and overall enclosure shape were not moved.
- Added inset, opaque end faces to **both ends of both drums**. The previous
  shells were hollow tubes; looking along their axes revealed the interior.
  The new faces close that visual path and sit flush with the tube ends.
- Kept the saved whole-product Blender viewport framing inherited from R10.

The end faces represent an appearance study. They do not establish how the
drums are supported, how bearings or wiring pass through, whether the seams
seal, or whether the optical and rotating parts can be assembled. The lens
placement is also not a camera calibration or an optical performance claim.

## Review images

- `renders/r11-interaction-optics.png`: angled openings and visible lenses.
- `renders/r11-closed-drum-ends.png`: outer right drum end face.
- `renders/r11-exterior-front.png`: front view of both drums.
- `renders/r11-internal-rear.png`: inherited R10 board and thermal presentation.

## Reproduction and checks

```sh
/opt/homebrew/bin/blender --background --python blender/refinements/r11/build_r11.py
/opt/homebrew/bin/blender --background --python blender/refinements/r11/verify_r11.py
/opt/homebrew/bin/blender --background --python blender/refinements/r11/render_r11.py
```

`r11-verification.json` checks the R10 fault as a negative baseline (all five
interaction lens rays hit the shell), then checks the R11 correction (all five
pass through the openings). It also checks the four end faces, preservation of
the continuous R10 board, protected hashes and Git status. Geometry checks do
not prove manufacturing feasibility or website visual approval. Engineering
readiness remains **BLOCKED**.
