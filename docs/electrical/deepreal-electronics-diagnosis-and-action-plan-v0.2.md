# DeepReal electronics diagnosis and action plan v0.2

Date: 13 September 2026. Inspected baseline: `main`, commit `50ea864`.
Scope: main PCBA, both rotating sensor heads, flexes, position sensing, USB integration, and the KiCad-to-Blender presentation pipeline.
Status: diagnosis and proposed execution plan; no electrical or mechanical design changes made during this audit. Complements the existing engineering-review plan with measured findings and corrected priorities. It does not grant a release approval.

Implementation note, 14 September: the pipeline findings below describe the
inspected baseline, not all current code. See the
[native-import checkpoint](native-pcba-import-checkpoint.md) for Stage A changes.
Electrical and mechanical blockers remain open.

## 1. Conclusion and intended result

The current files are an incomplete packaging study with a partially connected visualization pipeline. They are not a coherent electrical layout yet. Senior engineering review would find substantive problems in connectivity, footprints, board-to-board interfaces, moving flex geometry, and the correspondence between the schematic, PCB and render.

The useful foundation is the enclosure, named subsystem arrangement, candidate component register, 90 × 28 mm main-board envelope, two rotating optical payloads, and reproducible scene generation. Keep these as starting constraints. Exact fit and final board size remain unresolved.

The next deliverable should be a reviewable electronics assembly: an actual main-board design, a reusable head-board design installed twice, a documented position-sensor arrangement, real interconnect definitions, and renders generated from those designs. A polished render is an output of that work. It cannot establish electrical correctness by itself.

There are two review checkpoints: an internal geometry/interface review that makes the assembly understandable, followed by a routed electrical review that can support publication. Show progress at the first checkpoint, but do not label it finished or publish it under the routed-review caption.

## 2. Evidence gathered in this audit

Read the current KiCad sources/export, component/evidence registers, optical-head capture documents, requirements, topology study, Blender geometry/import code, interconnect and motion code, and validators. Re-ran the gate, flex-allocation, camera-bandwidth and export validators. Ran KiCad DRC with schematic parity and all report severities. Inspected the saved Blender scene with a read-only script; it was not saved or rebuilt.

| Measurement | Current evidence | Meaning |
| --- | --- | --- |
| Main-board outline | 90 × 28 × 1.6 mm | A candidate envelope, not routing-supported fit |
| KiCad footprints | 238, including four mounting-hole footprints | Does not mean 238 selected, electrically defined components |
| Capacitor/resistor proxies | 144 C references, 44 R references | Mostly reserved values and independent space claims |
| Exported pads | 2,313; every pad has an empty net name | Actual electrical connections are absent |
| Actual tracks / vias / copper zones | 0 / 0 / 0 | No routing feasibility has been demonstrated |
| Functional schematic sheets | 14 under the root sheet; 0 populated with circuitry | The 15-page structure is a document scaffold |
| KiCad DRC | 610 violations, plus 199 schematic-parity issues | Existing placement cannot pass review |
| DRC unconnected items | 0 | Meaningless as a completion metric when pads have no defined nets |
| Blender component bodies | 201 | Different inventory from KiCad; counts alone cannot prove parity |
| Handmade Blender ground vias | 40 | Remain visible even though KiCad has zero vias |
| Tamper switch SW1 | Appears in Blender; absent from KiCad | Missing parts are still silently represented from fallback data |
| Head-board KiCad files | None in `deepreal-optical-head/` | Only requirements, registers and circuit prose exist |
| Head-flex allocation | 51 contacts in 16 groups; every group awaits physical pin numbers | Arithmetic fits; the cable cannot yet be wired from this definition |

The DRC report is preserved in [review evidence](review-evidence/2026-09-13-main-layout-check.json). It reports 149 clearance, 56 courtyard-overlap, 126 solder-mask-bridge, 7 copper-edge, 4 hole-clearance, 4 plated-hole-inside-courtyard and 3 non-plated-hole-inside-courtyard violations; 261 further items concern silkscreen/text. The separate 199 parity issues are extra footprints relative to the schematic.

Examples: J2 pad 2 and C59 pad 1 have zero copper clearance; D9's courtyard overlaps U10 and mounting footprint H3. These are findings on the existing proxy footprints, not proof that a future corrected footprint will have the same conflict. Replace wrong footprints before treating each marker as an independent routing problem.

Five checks are disabled in the current project, including missing courtyards and footprint-type/filter checks. Audit their relevance and restore applicable checks. `--severity-all` does not enable disabled checks. A clean result must also establish that required circuits and rules exist.

Reproduction:

```sh
/Users/adam/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli pcb drc \
  --schematic-parity --severity-all --format json --output /tmp/deepreal-main-drc.json \
  hardware/electronics/deepreal-main-pcba/deepreal-main-pcba.kicad_pcb
```

Board SHA-256: `63739aa744a85b407b4784bacde8dd61b5b745cae19ed3499ce07cf85a1c31b5`.
Root schematic SHA-256: `df3893862b4aa8ce53c104299217cc40e541bd4ad6adaa6390dc58df595e9323`.

## 3. Main-board diagnosis and corrections

| ID | Finding | Correct response |
| --- | --- | --- |
| M01 | Processor U1 uses a generic 324-pad footprint while the register calls for a 548-ball device. Blender separately draws a 27 × 27 pad array. | Import the exact device's audited ball map and land pattern; derive both PCB and rendered pads from it. Matching the outer 15 mm square is insufficient. |
| M02 | DDR/eMMC pin maps are unaudited; processor/RAM proximity is only a neighborhood choice. | Audit memory variant, voltage, bus width, ball maps, boot compatibility and routing rules; select orientations from real connections. Keep the existing 2 mm body gap only if the resulting routing and assembly access support it. |
| M03 | PF53 footprints are 4 × 4 mm proxies versus the registered 3.5 × 4.5 mm bodies; angle sensors use 16-ball proxies for 15-ball parts; USB D2 has a wrong package proxy. | Complete symbol-to-pad audits for every major IC. Package names and appearance are not adequate evidence. |
| M04 | KiCad J1 uses an Amphenol footprint; Blender shows the selected Hirose shell. Its position is approximately 41.1 mm from the enclosure opening. | Solve receptacle, opening, insertion direction, plug clearance, retention and exact footprint together. Validate the recorded 0.8 mm recommended-board-thickness conflict against the final drawing before using it on a 1.6 mm board. |
| M05 | Load switches, TVS, oscillators, debug interface, motor connectors and several regulators/support parts remain unselected. | Choose orderable parts with documented requirements; include all external circuits, exposed-pad connections and test provisions in schematic and area budgeting. |
| M06 | Capacitors, resistors and inductors are reserved populations, not calculated circuits. | Calculate values, tolerance, effective capacitance under DC bias, ratings, inductor saturation/loss and converter compensation; place from actual power pins and switching loops. |
| M07 | Blender L3/L6 have zero nominal body-envelope gap; U5/L1 have 0.40 mm and D1/D2 0.05 mm. | Remove unintended body contact. Assess other gaps with exact courtyards, pads, manufacturing tolerances and rework access. A 0.40 mm body gap is not automatically unacceptable; the earlier blanket claim was too strong. |
| M08 | Upper-left space is unallocated; right side is congested. | Rebalance after USB, FPGA, head connectors, thermal contact and actual circuits are known. Do not fill the region decoratively or shrink the board based on projected body occupancy. |
| M09 | Ten layers are an unapproved intent model; the board has only generic rules and no critical net-class assignments. | Select a preliminary manufacturable stack with defined reference planes, impedance geometries, BGA escape and via rules. Encode DDR, camera, USB, clocks, memory and power constraints before routing. |
| M10 | The current layer intent places several signal/power layers together without an established reference-plane analysis. | Review return-current continuity, plane coupling and transitions; compare 8/10/12 layers using actual escape and routing demands. Layer count alone does not prove feasibility. |
| M11 | Cooling geometry connects tray → spreader → housing but does not establish processor → thermal interface. | Design and budget the entire heat path, including contact area, electrical isolation, compression and tolerances. Audit reads approximately 1.941 mm from U1's top to the inside of the front lid, with no modeled interface bridging it. A backside path would require its own board/thermal design. |
| M12 | The validator uses a 15 mm aggregate stack allowance while a separate populated reservation is 6 mm; heights are reported mainly from registered major parts. | Establish one local top/bottom height envelope from the actual enclosure. Check every body, solder joint, shield, pad, fastener, connector latch and tool-access volume against it. |
| M13 | Microphone port, switch actuation, ESD returns, shield ground contacts and assembly/test details are incomplete in KiCad. | Model these as explicit constraints and circuit features, then check them in installed and service configurations. |

Sources: [component evidence](../../hardware/electronics/deepreal-main-pcba/component-evidence.csv), [USB study](../design/main-pcba-usb-mechanical-options-v0.1.md), `blender/pcba_geometry.py`, `blender/electronics.py`, `blender/validate_pcba.py`, and the new DRC report. Manufacturer references: [NXP i.MX95](https://www.nxp.com/products/i.MX95), [Hirose receptacle](https://www.hirose.com/product/p/CL0480-0919-0-00).

## 4. Both drums and the actual board count

The intended head electronics are sensible as a partition: RGB assembly, IR sensor and lens, projector/driver, sensor regulators, decoupling, pulse storage, temperature sensing and a local emission interlock belong on the rotating head. Processor, RAM, storage and major system power stay stationary.

However, Blender currently creates an RGB PCB, an IR PCB and a projector PCB in each drum. These are bare geometric slabs, not three designed and interconnected boards. The electrical documents instead describe one reusable head-carrier design installed twice. Neither interpretation has been implemented as a head-board KiCad design.

Recommended starting architecture: one main board plus two copies of one head-carrier assembly. Evaluate a single rigid head carrier first; use multiple rigid islands or rigid-flex only if optics, assembly or the axle require them. A bought RGB assembly can contain its own substrate and short tail without becoming an independently designed DeepReal carrier board.

Two stationary angle-sensor boards may also be needed at the drum axes, and a small USB board may be needed at the external opening. That means three primary board assemblies, potentially five with angle boards, or six with a USB board, before counting supplier-internal substrates. These are candidates to reconcile, not a frozen BOM.

| ID | Finding | Correct response |
| --- | --- | --- |
| H01 | There is no real head-carrier PCB outline, schematic, pad layout, local rail layout or populated render. | Create one head KiCad project and a complete assembly definition; install it twice using explicit mechanical transforms and per-head identity/calibration. |
| H02 | The rendered RGB body is 8 × 8 mm with a 7 × 7 × 0.6 mm PCB; the selected Raspberry Pi assembly is 10.8 × 10.8 mm. | Replace generic body/lens/tail geometry with the selected assembly's drawing and connector. Redo axial and radial containment, focus travel, aperture and carrier checks. Never shrink the purchased assembly to fit the picture. |
| H03 | Mira220 is a bare sensor; the current generic camera body does not define the lens, holder, filter, focus spacing or complete sensor electronics. | Select a lens/holder/filter solution and package it with the exact sensor and required rails. Verify image circle, field of view, working distance and alignment tolerances. |
| H04 | Projector shape and three front apertures originate from concept geometry, not a demonstrated Belago optical path. | Check the actual emitting aperture, divergence, window transmission and clearance to housing. Any baffle/window arrangement needs optical justification. Keep or change the visible aperture pattern only from that evidence. |
| H05 | The 5 × 5.4 mm projector PCB placeholder carries none of the driver, inductor, pulse capacitor or interlock logic. | Place the full local switching circuit in the head budget, with a short current loop and separated camera routing. Do not assume its components fit on that slab. |
| H06 | Local regulator selections, rail sequence, reset logic, autofocus support and I²C address isolation are unfinished. | Capture the published sensor reference circuits, exact pin maps, local protection and test access. Check identical heads for address conflicts and back-powering through control signals. |
| H07 | Requirements call for IR capture at 60 fps, while the current illumination reference is 1 ms at 30 fps and only one projector active at a time. | Define the illumination/exposure schedule and required depth-output rate. Keep simultaneous sensor capture; establish whether every frame needs illumination, how pulses interleave, and how thermal/optical limits are met. Do not silently promise 60 illuminated depth frames per head. |
| H08 | RGB/IR/projector alignment, baseline, calibration and depth reconstruction are unproved. | Define target depth range/accuracy, optical overlap and calibration retention with temperature/motion. A dot projector and IR sensor alone do not demonstrate a working depth product. |
| H09 | Drum volume checks omit the complete electronics and do not establish service or assembly access. | Recheck full populated boards, axle, bearings, carrier, shell, windows, flex exits, latch access, fasteners and thermal paths through tolerances and travel. Freeze the head outline only then. |

Official basis: [Raspberry Pi sensor assembly drawing](https://datasheets.raspberrypi.com/camera/sensor-assembly-product-brief.pdf), [Mira220](https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-mira220), [AS1170](https://ams-osram.com/products/drivers/led-drivers/ams-as1170-2-channel-led-and-vcsel-driver-ic), [Belago1.2 datasheet](https://look.ams-osram.com/m/4971b838d6356daa/original/Belago1-2-Dot-pattern-infrared-illuminator.pdf). The pulse operating point is a reference condition, not a demonstrated safe product limit.

## 5. How the heads connect, and what is missing

Candidate signal flow, retaining two main-board FPGAs pending the architecture decision:

```text
Face rotating head: RGB + IR + local power/projector/interlock
  ⇅ one engineered dynamic flex ⇅ main J2 → FPGA A → processor CSI receiver A

Interaction rotating head: same carrier design and components
  ⇅ one engineered dynamic flex ⇅ main J3 → FPGA B → processor CSI receiver B

Main → head: switched power, ground, control, clocks, reset/permission
Head → main: RGB/IR image streams, faults/status; timing direction per sensor

Stationary drum-angle sensor + shaft magnet → stationary control harness → main
Motor → motor power/encoder harness → main driver/control
Processor → defined processing/encoding/transport → USB connection → host
```

Each head currently budgets four MIPI data pairs plus two MIPI clock pairs: **six differential pairs**, not four pairs total. They occupy 12 signal contacts, with other contacts allocated to returns, clocks, power and control. Two sensors cannot share an electrical output just because software assigns virtual-channel numbers.

| ID | Finding | Correct response |
| --- | --- | --- |
| I01 | All 51-contact groups lack real pin numbers and verified mating orientation. | Produce an end-to-end connector table: board reference, pad number, signal, voltage, direction, paired return, head pin and flex face. Check mirroring, latch direction, contact staggering and continuity. Use assembly-qualified names such as MAIN:J2 and HEAD_FACE:J1. |
| I02 | The flex is drawn as a round 1.44 mm diameter cable; a 51-position, 0.3 mm interface needs a much broader contact region. | Build the actual flat flexible circuit with specified width, thickness, conductor/reference layers, stiffeners and connector tails. The 50 contact intervals span about 15 mm; a necked flex requires its own routed fan-out and current analysis. |
| I03 | A 3 mm bend-radius number is attached as metadata; the validator does not measure a dynamic flex's surface strain or curvature. | Define a supported flex stack and rolling/service loop; calculate bend/strain limits and test a continuous travel envelope, including twist, length conservation and strain relief. Supplier fatigue data and later cycle tests remain required. |
| I04 | The flex is not attached to a modeled head connector; present sweep validation rotates optics at five angles against shield parts, not a deforming flex against all obstacles. | Add both real mating ends and model movement of the head end. Check shell exits, axle/bearings, gears, motor, shields and supports over the full motion range. Resolve 150° stop versus 160° flex assumptions. |
| I05 | Eight power contacts are assumed sufficient. | Use connector/contact derating, current sharing, flex resistance, voltage drop, ground bounce, sensor startup and pulse-capacitor recharge. FH26 lists 0.2 A/contact; 8 × 0.2 = 1.6 A is only nominal arithmetic, not approved harness current. |
| I06 | MIPI electrical integrity across connectors/flex is unverified. | Define actual transmitter lane rates, impedance, return paths, discontinuities, crosstalk, skew and protection capacitance. Split power/control and camera functions if a single flex cannot meet requirements; then revisit connector area. |
| I07 | Angle ICs U18/U19 are on the main board while Blender separately shows encoder boards/magnets near each drum. The depicted magnet axes are Y; the drums rotate about X. | Choose a coherent stationary sensor/rotating magnet assembly aligned to the measured shaft axis, gap and field. Likely use two small stationary sensor boards; remove duplicate main-board sensor claims and budget their wiring and connectors. |
| I08 | A six-contact motor/encoder connector is not proven to carry motor power, incremental encoder and absolute-angle functions. | Enumerate all wires, supply/return paths and logic levels. Split or enlarge connectors where necessary, and provide suppression/fault feedback. Stationary sensors and motors do not need to burden the rotating optical flex. |

Official basis: [Hirose FH26 catalog](https://www.hirose.com/product/document?clcode=CL0580-2401-1-60&documentid=D49355_en&documenttype=Catalog&lang=en&productname=FH26W-13S-0.3SHW%2860%29&series=FH26) and [AS5600L mounting guide](https://look.ams-osram.com/m/b03a90ea3dea434a/original/AS5600L_UG000345_2-00.pdf). The sensor must see the appropriate centered rotating magnetic field; the current two competing placements do not establish that relationship.

## 6. System decisions that can change the PCB

- **Camera aggregation:** one or two FPGAs remains undecided. Two devices near the corresponding head connectors are a reasonable study baseline. Prove the exact part/package, hard/soft PHY assignment, pins, lane rates, clocks, buffer capacity, timing, IP licensing, resource and power margins. A no-FPGA solution would still need documented aggregation hardware or changed sensor/processor connectivity. [NXP](https://www.nxp.com/products/i.MX95) lists two four-lane CSI interfaces; [Lattice](https://www.latticesemi.com/CrossLinkNX) documents configurable PHY resources whose availability depends on device/package. A reference design is not a DeepReal compile.
- **Camera budget:** the script calculates 4.7616 Gbit/s active pixels and 5.952 Gbit/s after multiplying by 1.25. It does not add actual protocol overhead first. Reconcile this with the requested 25% margin after overhead, define the margin convention, and budget each input/output using the sensors' actual modes and burst line rates. Average frame payload alone cannot size the PHY or aggregator buffers.
- **Host transport:** uncompressed pixels total 595.2 MB/s. A 5 Gbit/s USB link using 8b/10b coding has at most 500 MB/s before packet overhead. Continuous uncompressed four-stream transfer is therefore impossible on that link. Existing architecture prose allows encoded media and proof-only modes; choose exact operating profiles, required retention, buffering and overflow behavior. Validate processor/codec/DDR/storage throughput or change the transport architecture. Do not assume compression always meets a fixed ratio. [TI USB transceiver documentation](https://www.ti.com/lit/ds/symlink/tusb1310a.pdf) documents the physical coding; rates here are calculations from the project requirements.
- **Power from the host:** do not assume a target laptop port supplies the preferred 15 V/3 A contract. Verify power-source capabilities for supported hosts and choose useful 5 V operation, an external supply arrangement or changed performance requirements as appropriate. Preserve the one-cable goal explicitly when comparing alternatives. Check how a nominal 5 V system rail behaves with only 5 V input after cable/eFuse losses.
- **Power tree:** close the actual processor/FPGA/head/motor load matrix, efficiencies, inrush, brownout, discharge, sequencing and worst-case simultaneous loads. Rated converter current is not expected consumption, and 45 W input capability is not an acceptable heat budget by itself.
- **Trust/software:** select supported sensor modes/drivers, virtual-channel handling, timestamp/trigger ownership, protected capture buffers, hashing bandwidth and FPGA configuration/recovery. Clarify which bytes are committed before transformations. Security branding cannot substitute for this data path.
- **Requirements consistency:** the approved requirement file, older system-architecture stream table, FPGA hashing preference, optical-module references and motion limits disagree. Resolve them under one revision before treating G1 as closed for the complete system. The audit does not silently alter gate statuses.

## 7. Why Blender does not yet match KiCad

`pcba_placement.py` imports coordinates for references already present in its hand-maintained major-part list. It does not build the complete KiCad inventory. `pcba_geometry.py` still places small components and seven inductors independently; KiCad contains nine inductors. U21/U22 and D3–D8 are not covered by the major merge. SW1 falls back to historical coordinates when absent from KiCad.

The geometry builder reads rotation metadata but does not consistently apply it to bodies, marks or generated pads. BGA arrays and QFN pads are synthesized by package-family heuristics rather than imported pad geometry. Forty decorative through-board rings and a separate shielding ground ring remain handmade. The prior statement that every future visible via already came from KiCad was incorrect.

The exporter writes a Python object representation as the footprint ID, including a process memory address; it is not a stable library identifier. Its field named `courtyard_bbox_mm` is a general footprint bounding box, not the actual courtyard polygon. Model transforms/heights, complete board arc/slot geometry, stable object identifiers, source hashes and real silkscreen are missing. Copper export/import does not faithfully cover arc tracks, via spans, filled zones/voids and per-side mask detail. Exported pads, zones and holes are not used to reproduce the full Blender PCB.

Correct solution: implement one complete, versioned KiCad assembly export and a strict Blender importer. Include main/head/auxiliary board identity, part reference, exact footprint, side, rotation, body/model transform, actual pads and layers, outline/slots, vias/spans/tenting, filled zones, mask/paste, silkscreen and source revision/hash. Handle missing model files with recorded dimensionally accurate envelopes, never guessed pin grids. Missing required components should fail the parity check.

Geometry tests must compare the built meshes and object inventory to KiCad, including asymmetric rotations and mirrored bottoms, within 0.1 mm maximum positional deviation. The existing coordinate round-trip check tests an arithmetic conversion; it does not prove scene parity or deterministic exported bytes. Remove memory-address strings, sort by stable IDs and test regenerated geometry with hashes. Include negative tests that detect missing parts, a wrong pad map, zero body clearance, swapped connector ends, stale exports and empty schematics.

## 8. Action plan and dependencies

### Stage A — Repair the evidence and geometry pipeline

Start immediately. Preserve the diagnostic baseline and DRC report; add complete body/courtyard/pad/edge/height checks and assembly parity checks. Replace all Blender-only placement/pads/vias with the full canonical export, including smaller components and orientation. Keep missing/unaudited package status visible. Restore meaningful DRC checks and reject empty circuit sheets as completion evidence.

Deliverable: a reliable reference-designator map and discrepancy report showing what is in each board and what remains missing. This may initially look worse because it exposes real collisions. Acceptance: every modeled PCB feature is traceable to its source, and contacts cannot pass unnoticed. This stage can proceed while device data is being gathered.

### Stage B — Freeze system interfaces and operating profiles

Depends on requirements audit, not on render polish. Decide host transport/power modes, sensor modes and timing, depth/illumination schedule, main versus head partition, angle-sensor location, and USB mechanical approach. Study the centered USB opening with a supported daughterboard/interconnect alongside an integrated-board solution; do not choose merely by appearance. Compile viable FPGA candidates on a supported toolchain and compare pins, timing, power and placement needs.

Deliverable: one board/harness inventory, system diagram, operating-mode matrix, camera/USB bandwidth budgets, power budget, and justified architecture decisions. Acceptance: each interface can meet its requirement with stated margin; remaining unknowns are named and do not masquerade as frozen choices.

### Stage C — Design one head assembly and its complete connection

Begins alongside B; final connector/power details depend on B. Use actual RGB assembly, Mira220 lens/sensor, projector and full support circuits to establish the head board or rigid-flex geometry. Design stationary angle-sensor boards if selected. Derive the flex and motor/encoder pin tables from real circuits and verify both mating ends. Define the flat flex construction, current budget and motion envelope.

Deliverable: populated head schematic/PCB draft, exact connector tables, sectioned drum assembly, full-range flex animation and two installed copies. Acceptance: complete payload fits with tolerances; no free-floating connection; the same electrical design works in both roles without accidental left/right pin reversal. Optical design review and head thermal checks are required inputs.

### Stage D — Capture circuits and establish the manufacturable rules

Subsystem circuits may be developed as their own inputs close. Complete the main, head and any auxiliary-board schematics using audited symbols and land patterns. Include power/startup, clocks, memory, FPGA configuration, motors, local laser permission/fault logic, debug, protection and test access. Obtain preliminary PCB/flex manufacturing capability and impedance recommendations; translate them into design rules.

Deliverable: real schematics, BOMs, netlists, component audit, power/sequence diagrams, preliminary stack and rule files. Acceptance: expected circuits exist; pins and pad mappings reconcile; ERC errors are fixed and warnings individually reviewed. No invented BGA pins or footprint substitutions are accepted for placement release.

### Stage E — Place from pins and prove fit

Depends on B–D for affected circuitry. Place mechanical interfaces/thermal contacts first, then processor/memory and FPGA lanes, then power loops/decoupling and remaining support. Place protection at physical cable boundaries and make servicing possible. Start routing DDR, cameras/flex, USB, clocks, eMMC and main power early enough to expose blocked corridors. Iterate between placement and critical routing.

Deliverable: top/bottom placement and critical-route review for all boards, with explained empty areas, connector access and populated-height sections. Acceptance: package-specific spacing and actual pad clearances pass, return paths and impedance constraints work, and full assembly/flex checks pass. Keep 90 × 28 mm only if that evidence supports it. Compare a changed outline or split-board solution when necessary.

### Stage F — Complete routing and close engineering findings

Depends on E. Route remaining nets, fill planes, add real grounding/thermal structures and test points, finalize silkscreen and assembly notes. Review current/voltage-drop, power integrity, DDR constraints, MIPI/USB transitions, noise coupling, thermal estimates, BOM lifecycle and software feasibility. Include applicable simulations/tool reports and distinguish calculated from measured evidence.

Deliverable: routed digital review package with ERC/DRC/parity/length/skew/connectivity reports, pin audits, FPGA reports, stack-up, mechanical/flex assessment and open-risk list. Acceptance: no unexplained violations or unintended unrouted nets; every intentional exception has an owner and justification. A zero result without meaningful nets/rules is rejected.

### Stage G — Senior review and visual finish

Use an experienced PCB/high-speed reviewer plus mechanical/optical/FPGA input where appropriate. Track findings to closure against a named design revision. Their approval cannot be promised in advance; the package must make the review possible and expose uncertainty.

Once the engineering geometry is stable, refine mask, packages, pads, solder joints, component markings and lighting in Blender. Use real exposed-metal finishes, subtle copper relief beneath mask, readable component polarity and labels, and accurate substrate edges. Do not add decorative traces to achieve a busier image. Do not add solder geometry that obscures contacts or invents package leads.

### Stage H — Produce website and document assets

Depends on accepted review findings and exact geometry parity. Produce main-board top/bottom, head-board top/bottom, a labeled assembly map, drum cutaway, flex/connector detail, electronics exploded view, thermal/USB section, and complete installed-device view. Keep high-resolution masters and web derivatives, plus source revision and approved caption. Inspect full-resolution crops and actual website display sizes.

Acceptance: one coherent design in every view; no floating parts, unresolved contacts, invented copper, reversed connectors, masked text, z-fighting or missing small parts. A senior engineer can identify a component and trace it to the schematic, footprint, connection and assembly constraint. Publish only after the existing release gate and the review findings permit it.

## 9. Corrections to previous acceptance rules

- Do not prohibit every trace under a component or inside a courtyard. Legitimate pad connections, BGA escape and internal-layer routing occur there. Prohibit unintended same-layer copper contact, actual keep-out violations and inadequate spacing/return paths. Courtyards primarily describe assembly clearance; they are not universal routing bans.
- Do not apply a universal 0.5 mm or 1 mm component-body gap. Use audited package geometry and assembly requirements; dense local decoupling and regulator loops need short connections.
- Do not treat the current RGB and projector dummy envelopes, round flex, or coarse five-angle shield sweep as validated drum fit.
- Do not label current dimensions as final. Projected component area does not include routing, copper return paths, assembly access or thermal margin.
- Do not quote percentage completion as engineering evidence. Use concrete deliverables and their acceptance reports.
- Do not make visual approval stand in for physical validation. This work can produce a strong digital design and review package; prototype electrical, thermal, optical, EMI, flex-life and manufacturing tests remain future work before production claims.

## 10. Inputs and resources required to close the plan

Most immediate audit/pipeline work can proceed locally. Final closure requires exact vendor data and reference designs, a supported licensed FPGA tool environment, sensor/ISP/software support evidence, preliminary board/flex manufacturing input, and experienced hardware/optical review. Missing access or data should be recorded as a specific blocker with the required file/tool, not a generic claim that an entire subsystem is inaccessible.

Product decisions to bring back with concrete alternatives: required host output/retention, supported host power sources, required illuminated depth rate and working range, permitted USB-opening changes, and motion duty/lifetime. Research feasible alternatives and their size/performance consequences before asking for a selection.

First reviewable milestone: corrected import/validation, a complete board inventory, and a head/USB/encoder/flex interface study. Final milestone: reviewed routed electronics and matching website-quality renders. Do not spend another render-polish cycle before addressing the geometry and interface contradictions documented here.
