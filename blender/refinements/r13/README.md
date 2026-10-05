# DeepReal enclosure refinement R13 — drum center gap

Open [the R13 Blender model](deepreal-exterior-refinement-r13.blend). This revision changes only the center ends of the two drums and their flat visual end faces. The enclosure, USB socket, main PCB and R12 source file are unchanged.

The R12 drum bodies met at the center with **0 mm gap**. A thin circular face had been placed on each end to hide the hollow tube. Each face projected 0.24 mm toward the other drum, so the two faces overlapped by 0.48 mm inside the model. These were appearance parts, not physical caps with a designed attachment.

R13 pulls each drum's inner edge back 0.5 mm without moving its optical openings or lenses. The resulting nominal **body gap is 1.0 mm**. Each flat face now follows its own drum end, leaving **0.52 mm between the visible faces**. The faces no longer intersect each other or the opposite drum. These clearances are appearance choices; running clearance, bearing play, thermal expansion and manufacturing tolerances still require mechanical design.

## Review views

- [Close view of the new center seam](renders/r13-drum-gap-front.png)
- [Angled view of both drums](renders/r13-drum-gap-angle.png)
- [Exterior front with housing visible](renders/r13-exterior-front.png)

The [verification report](r13-verification.json) checks the measured gaps, absence of face collisions, ten lens openings, unchanged PCB/housing/socket, saved housing visibility, and preservation of R12 and the native PCB. Engineering readiness remains **blocked**.

From the DeepReal root, run `blender -b -t 4 --python blender/refinements/r13/build_r13.py`, then `blender -b -t 4 --python blender/refinements/r13/verify_r13.py` and `blender -b -t 4 --python blender/refinements/r13/render_r13.py` to rebuild and check the revision.
