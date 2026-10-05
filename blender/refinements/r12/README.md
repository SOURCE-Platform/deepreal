# DeepReal enclosure refinement R12

R12 is the current **review model**, saved entirely inside the DeepReal folder. Open [the Blender file](deepreal-exterior-refinement-r12.blend). The [verification report](r12-verification.json) records eight geometry and source-preservation checks. Engineering readiness remains **blocked**.

## What changed

- The USB area is now part of one continuous main-PCB mesh. The right wing spans 26.5 mm of the original board's 28 mm height. A 1.5 mm step along its lower edge clears the existing housing; extending the full rectangle intersected that housing in the geometry study.
- The top and bottom imported board-finish surfaces continue over the wing. This removes the previous green-color seam, which came from the finish stopping at the original edge. The R12 substrate and finish remain visual representations, not a released stackup.
- A proposed H5 mounting hole was added to the wing, with an integral support boss and blind pilot in the housing beneath it. This shows a possible load path for plugging and unplugging USB. Its screw, insert, wall, tooling, and strength have not been engineered.
- The visible drum ends use thin flat disks over their original hollow rims. This gives the requested minimal side appearance. The disks are presentation skins; the bearing, sealing, and manufactured end construction remain unresolved.
- A separate [KiCad outline and H5 placement study](native-outline-H5-study-NOT-FOR-FAB.kicad_pcb) mirrors the wider board shape. It is clearly marked **not for fabrication**. The original native PCB and R11 model are unchanged.

## Review views

- [USB wing with spreader and rear shield hidden](renders/r12-port-tab-exposed.png)
- [USB wing in the surrounding layout](renders/r12-right-usb-detail.png)
- [Flat drum side](renders/r12-closed-drum-ends.png)
- [Exterior front](renders/r12-exterior-front.png)

## What the model does not establish

The USB socket remains an unselected illustrative envelope. Its seating geometry intersects the board in the model, but no actual connector footprint, solder joints, copper routing, power/data path, or retention design has been completed. The KiCad study adds an outline and H5 only; its original J1 placement is retained. It has not passed KiCad DRC. The boss has not been checked for plug insertion forces, torque, vibration, or manufacturing feasibility. Drum closure and optics have not been mechanically or optically validated. This is not a fabrication release.

Rebuild with `blender -b -t 4 --python blender/refinements/r12/build_r12.py`, generate the native copy with `python3 blender/refinements/r12/make_outline_study.py`, render with `blender -b -t 4 --python blender/refinements/r12/render_r12.py`, and verify with `blender -b -t 4 --python blender/refinements/r12/verify_r12.py` from the DeepReal root.
