# DeepReal Main PCBA — Preliminary Engineering Layout / Packaging Study

> **Historical geometry notice (12 September 2026):** This study describes the
> existing one-FPGA/four-camera-connector Blender layout. It remains useful as a
> packaging record, but the current schematic-entry baseline is
> `../electrical/main-pcba-schematic-entry-spec-v0.1.md` and Mechanical BOM v0.2.
> Do not use the rendered trace-free layout as the current electrical design.

Status: packaging study, not a released schematic, routed PCB, or production
design. Model date: 2026-09-10.

## Decision summary

The current one-board 90 × 28 × 1.6 mm concept is still physically plausible.
The model now contains the named major devices, real/candidate package bodies,
four camera connectors, motor and emitter interfaces, representative power
magnetics, bulk energy storage, more than 100 support passives, BGA/QFN land
patterns, ground-via fields, silkscreen, and two-sided population.

The mechanical validator reports:

- 185 modeled component bodies: 133 top and 52 bottom
- tallest top-side body: 3.16 mm
- tallest bottom-side body: 1.30 mm
- total populated stack: 6.06 mm, versus the 15 mm electronics allocation
- body-projected area: 960 mm² top and 355 mm² bottom
- raw projection not covered by bodies: 1,560 mm² top and 2,165 mm² bottom

The raw free-area numbers are not routable-area claims. BGA escape, impedance
control, copper pours, thermal vias, courtyards, test access, flex mating, and
assembly tolerances will consume much of that apparent space.

![Preliminary Main PCBA top assembly](../../blender/renders/presentation-06-pcba-top.png)

![Preliminary Main PCBA bottom assembly](../../blender/renders/presentation-07-pcba-bottom.png)

![Dimensioned Main PCBA packaging view](../../blender/renders/presentation-08-pcba-dimensioned.png)

## What the model proves—and does not prove

It proves that this candidate population can be arranged inside the current
board outline without enlarging it, while respecting the modeled mounting-hole
keep-outs and a 15 mm gross component stack allocation. It also demonstrates a
credible visual density and the mechanical consequence of four 13 mm camera
connectors by placing each drum's pair on opposite PCB faces.

It does not prove that the board can be electrically routed, powered, cooled,
manufactured at acceptable yield, or qualified for signal integrity, EMC, eye
safety, or reliability. There are deliberately no invented copper traces. The
visible lands, vias, reference designators, and support parts communicate the
required physical density without pretending that a schematic or netlist is
frozen.

## Important remaining problems

1. The proposed board-edge USB-C receptacle is 41.1 mm away in X from the
   existing housing USB opening. Either the enclosure opening must move, or the
   design needs a short internal high-speed/power interconnect to a separate
   port board. The current model flags this rather than hiding it.
2. The one-FPGA, four-camera topology is provisional. A Lattice Radiant compile,
   complete lane map, I/O-bank allocation, bandwidth calculation, and timing
   result are required before U2 is an electrically defensible choice.
3. The paired top/bottom camera-connector arrangement fits the edge, but real
   flex drawings, insertion access, bend radius, motion life, and assembly order
   are not yet proven.
4. The USB input buck, eFuse, motor drivers, emitter drivers, second PF53, exact
   inductors, and bulk capacitors remain candidate or reserved selections until
   measured current and power requirements are frozen.
5. The 6.06 mm populated stack fits the 15 mm gross allocation, but the modeled
   shield cavity leaves only roughly 0.35–0.38 mm local clearance at the tallest
   front and rear bodies. That is a packaging warning, not production tolerance.
6. The microphone acoustic path, tamper actuator, thermal interface pressure,
   shield contacts, test access, and service clearances need real mechanical
   drawings and tolerance stacks.
7. No layer stack, BGA escape study, DDR/MIPI/USB routing, SI/PI analysis, or
   thermal simulation has been completed.

![Camera connector packaging comparison](../../blender/renders/presentation-10-camera-flex-study.png)

## Confidence statement

Confidence that the candidate parts can be physically placed in the present
90 × 28 mm outline is now approximately 60–70%. Confidence that this exact
architecture is complete and electrically routable is still only approximately
35–45%. Those numbers should not be combined into a claim that the production
PCB is finished.

The next confidence jump comes from a preliminary schematic and power tree,
exact orderable component choices, an FPGA compile/pinout proof, and an EDA
placement-and-escape study. A routed board reviewed for SI/PI and DFM can raise
confidence toward 80–85%; production confidence requires an EVT build and
measurement.

## Artifact set

- Blender source: `blender/deepreal.blend`
- Mechanical placement contract: `blender/pcba_bom.py`
- Mechanical BOM/source record: `docs/design/main-pcba-mechanical-bom-v0.1.csv`
- Manufacturer USB-C CAD record: `blender/vendor_cad/hirose/README.md`
- Dedicated scenes: PCBA Top, PCBA Bottom, Dimensioned, Identification, and
  Camera Flex Study
