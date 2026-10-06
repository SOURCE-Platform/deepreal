# DeepReal enclosure refinement R16

Open [deepreal-exterior-refinement-r16.blend](deepreal-exterior-refinement-r16.blend) in Blender. The complete file is in the DeepReal folder and opens with the same drum and sensor pose as R15.

## Change made

The **interaction drum's** rear assembly opening and matching cover were moved lower around the cylinder. Their center is now about **25° below straight rear** in the saved pose. In R15, that center was 45° above straight rear, so this is a 70° downward change. The face drum opening remains where it was.

The shell rotation, sensor windows, internal head board, gear, motor, housing, and main electronics stayed in their R15 positions. This is an opening and cover placement change.

## What the views show

- [Saved rear view, covers installed](renders/r16-saved-rear-covers-installed.png): the interaction cover on the left sits lower than the face cover on the right.
- [Saved front view, covers installed](renders/r16-saved-front-covers-installed.png)
- [Saved front view, covers removed](renders/r16-saved-front-covers-removed.png)
- [75° down, covers removed](renders/r16-down75-high-front-covers-removed.png): the interaction opening is hidden from this high front camera; the unchanged face opening remains visible.
- [75° down, covers installed](renders/r16-down75-high-front-covers-installed.png)

In Blender, hide or show collection `01A — REAR ACCESS COVERS — CLICK EYE TO INSPECT OPENINGS` to inspect the openings. The two objects in collection `08 — DRUM TRAVEL PIVOTS — 150 DEGREE STUDY` can be rotated about local X for a movement review. Those pivot names remain from R15. R16 marks the interaction drum's final travel limits as **pending**; only its saved 45°-down pose and the 75°-down study position are specified.

## Limits

The view check covers selected camera angles and the modeled 75° down position. It does not establish that the seam is invisible from every viewpoint or through a final interaction-drum travel range. The access covers still need attachment, sealing, stiffness, and assembly design. The moving head flex cable, motor gearing, hard stops, and final optical field of view remain unresolved.

[r16-verification.json](r16-verification.json) checks that the face drum, lens positions, housing, and boards are unchanged; the interaction cover is lower; the meshes stay closed; the lens centers remain open; and sampled drum positions show no triangle intersections with fixed parts or housing. These checks are geometry review only.
