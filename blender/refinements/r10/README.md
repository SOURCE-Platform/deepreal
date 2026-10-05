# DeepReal enclosure refinement R10 — continuous board tab review

Open `deepreal-exterior-refinement-r10.blend` in Blender. This is an unbuilt
packaging study. It does not approve the main PCB, connector, shield, enclosure,
or thermal design for manufacture.

## Correction to R09

The R09 green USB tab was a **separate, overlapping Blender slab**. Its
intersection with the imported board did not make it an extended PCB. In R10,
the visible board substrate is **one connected mesh** with a stepped right-hand
tab. The original imported board artwork is retained as a hidden reference;
its component objects remain visible in the review scene. Four existing board
mounting holes are carried into the new substrate. The separate tab object is
gone.

The USB socket envelope now contains its four illustrative seating feet as
part of the **same socket mesh**. They enter the board-top surface, making the
visual mounting relationship clear when the socket is selected. These feet
are **not** a verified land pattern, connector pins, solder joints, or a
retention design. An exact receptacle and matching cable must be selected
before those features can be drawn accurately.

`native-outline-study-NOT-FOR-FAB.kicad_pcb` is a separate copy of the main
board with only its `Edge.Cuts` changed to a closed, one-piece outline. The
source KiCad board is untouched. In the copy, J1 still occupies its original
position and retains the existing Amphenol-footprint/Hirose-value mismatch.
The copy is an **outline study**, not a corrected electrical PCB or a valid
USB connector placement. The board has no routed USB power or data connection.
Do not fabricate or substitute it into the project.

## Geometry and evidence

- Original board outline: KiCad X 20–110 mm, Y 20–48 mm.
- Proposed right tab: KiCad X 110–122.5 mm, Y 32.5–45 mm, corresponding to
  Blender X 45–57.5 mm, Z −10 to −22.5 mm.
- USB socket envelope: Blender X 46.25–56.75 mm. Its nominal lateral gap to
  the spreader is 8.25 mm; this says nothing about operating temperature.
- `renders/r10-port-tab-exposed.png` shows the tab joined to the board and
  socket position with the shield and spreader hidden for inspection.
- `renders/r10-internal-rear.png` shows the proposed right-side path with the
  spreader and shield visible.
- `renders/r10-exterior-front.png` shows the outer cable position.

`r10-verification.json` checks that the new board and socket are each one
manifold mesh, that their seating surfaces intersect, that the separate tab
is absent, that the outline copy is closed, and that protected files retain
their baseline hashes. Mesh overlap is only a geometry check. It cannot prove
solderability, electrical continuity, assembly strength, USB performance, EMI,
safe temperatures, or the absence of every possible clash.

Reproduce using Blender 5.2.0 LTS:

```sh
/opt/homebrew/bin/blender --background --python blender/refinements/r10/build_r10.py
python3 blender/refinements/r10/make_outline_study.py
/opt/homebrew/bin/blender --background --python blender/refinements/r10/verify_r10.py
/opt/homebrew/bin/blender --background --python blender/refinements/r10/render_r10.py
```

The standalone KiCad executable was not available in this environment, so
the outline copy has not had KiCad DRC or a native editor visual review. The
next design step is to select and audit one real connector, then place its
correct footprint on the extended PCB, route power/data, and check mechanical
and thermal loads. R10 does not claim that work is complete.
