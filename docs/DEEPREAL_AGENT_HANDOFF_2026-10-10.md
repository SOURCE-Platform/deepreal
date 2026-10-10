# DeepReal agent handoff — 10 October 2026

This is the working handoff for continuing the DeepReal device and its SOURCE website presentation. Read the status distinctions carefully: the exterior is a strong visual concept, the assembly review is a working demonstration, and the internal electronics and moving mechanism are **not** released engineering designs. No board or cable is fabrication ready.

## Where the work lives

- Device repository: `/Users/adam/Documents/deepreal`, branch `main`. The R38 exterior and USB appearance study was committed and pushed as `4bff15f`; earlier device commits include `3cc2988` internal web wiring/groups and `0b866e0` website GLB exports.
- Website repository: `/Users/adam/Documents/source-public-site`, branch `main`. The R38 site asset and viewer changes were committed and pushed as `3865734`. **Many unrelated files in this repo are modified or untracked.** Preserve them; stage only DeepReal files when committing site changes.
- Local links: `http://localhost:3001/deepreal` (exterior) and `http://localhost:3001/deepreal/assembly-review` (development review). Both responded on 10 October. Port 3001 belongs to SOURCE public site per `~/.agents/ports.md`; use the site's `.agents/skills/restart-app/SKILL.md` before restarting. The assembly route deliberately returns 404 in production.
- Device model authority: Blender source and its manifests/checks, especially `blender/refinements/r38/` (current exterior/mount/USB appearance), `r30/` (base enclosure), `r21/` (side-supported mechanism envelopes), and `r34/`–`r37/` (interface and cable studies). R38 is the current website exterior export source; R37 only adds hidden volume reservations to the earlier R36 study.
- Electrical authority: `hardware/electronics/deepreal-main-pcba/` plus `hardware/electronics/deepreal-optical-head/`. `hardware/electronics/deepreal-main-pcba/design-status.json` is the gate register. Product requirements live in `docs/system-architecture/system-architecture.md`, but its older camera count, motion travel, and packaging language can lag the dated electrical/optical decisions; use the more recent specific studies when they conflict.

## What the user wants next

The immediate goal is an investor-facing Three.js device presentation. Milestone 1, the exterior model with USB cable on `/deepreal`, is deployed at `https://sourceovcourse.com/deepreal` and remains a reviewable visual, not an engineered mount or cable. Milestone 2 is an intact-to-transparent-to-exploded assembly animation with the three boards, major internal parts, and visible wiring. A useful **development-only** review already exists, including stage controls, scrub/play, board focus, orbit/zoom, and responsive/mobile framing. It is not yet a public polished release. The user explicitly accepts a visually accurate **conceptual** PCB representation for the website; exact copper traces and fabrication readiness are later goals. Keep that distinction visible in any investor copy.

## Completion vocabulary

Use **reviewable visual**, **concept/specification**, **blocked**, or **not started** for each subsystem. A rendered part or a footprint on a KiCad board is not a completed engineering subsystem. Avoid invented percent-complete scores. The three physical PCB assemblies intended for the product are one stationary main board plus two instances of a common rotating optical-head board design; small stationary cheek angle-sensor daughterboards are a possible additional board type and are not decided.

## Physical architecture and current status

| Part | What exists now | What remains |
| --- | --- | --- |
| Exterior enclosure | **Reviewable visual.** R30 has one continuous visual shell, flat rear top, exposed crowns of two cylindrical drums, fixed left/right cheeks and center divider, curved rear/leg, and monitor-top ledge. R30 checks a closed shell and six sampled drum poses. | Engineering wall thickness, shell split/seams, fastening, tolerance and print/mold method, dust strategy, thermal path, structural loads. One visual mesh does not imply one manufacturable piece. |
| Face drum | **Reviewable visual / mechanism concept.** True cylindrical shell, inner rotating ring, outer hub, optical apertures. R34–R36 study its inner cable opening and centered angle magnet. | Select bearings, shaft coupling, ring gear, stops, carrier/window clearance and a complete moving flex path. |
| Interaction drum | **Reviewable visual / earlier mechanism concept.** Separate drum with wide RGB lens envelope; current R21 interfaces are older than the face-drum R34–R36 studies. | Repeat axial encoder, bearing, flex and full travel study for this drum; redesign carrier around wide lens. |
| Side supports and center divider | **Reviewable geometry.** Fixed cheeks and center island connect visually to the enclosure and support each drum from both ends; the earlier rear-entry arms are gone. | Load path, bearing seats, retention, actual cable windows, assembly sequence. R37's proposed divider passage hits a bearing web. |
| Drive per drum | **Envelope concept.** Stationary center-fed motor/pinion drives an internal ring gear fixed to the rotating drum. R35 sketches a rotating outer web/hub connection. | Exact motor/gear/bearing selection, torque/inertia, gear teeth/backlash, fastening, vibration/settle and strength. No mechanism is released. |
| Motion and optics | **Provisional coverage decision.** Face standard RGB assembly: 66° H × 41° V FoV, nominal +45° up to −45° down. Interaction wide RGB: 102° H × 67° V, nominal straight to −45° down. | Real mounting geometry, RGB/IR/projector overlap, lens windows, calibration, physical hard stops and cable-life-limited travel. These are review poses, not proven motion limits. At −45°, interaction wide RGB reaches about 78.5° down, not straight below. |
| Monitor/laptop mount | **Visual stack.** R38 absorbs R30's old 40 × 13 mm housing-colored pad into a continuous inner leg and adds a distinct 112 × 26 × 0.9 mm device-side magnetic face matching R32's 112 × 26 × 0.35 mm laptop-side target plate visually. The nominal stack remains 0.90 mm face, 0.35 mm gap, 0.35 mm plate and 0.40 mm tape; the inner ledge depth is now 5.0 mm. | Choose actual magnet material/construction, retention/removal force, hinge load, adhesive aging, enclosure structure and laptop fit. Matching face dimensions and a metal finish do **not** validate magnetic holding force. Logo tooling and 430 ferritic stainless are candidates, not production selections. |
| USB exterior | **Reviewable visual.** The site GLB shows a 3.2 mm visual cable, longer V-tapered molded plug handle, separate sleeve and small DeepReal wordmark; the viewer fades the artificial free end. | Reconcile actual cable specification, receptacle, bracket, board position and strain relief. Existing board receptacle is 41.1 mm from modeled housing opening, and candidate CX90M3-24P's recommended board thickness conflicts with the 1.6 mm board candidate. |
| Shields/thermal | **Presentation envelopes** in exploded view. | Shield grounding, vent/heat path, mechanical attachment and thermal proof. |

## Electrical connection map (intended, not yet a verified netlist)

```text
Laptop/monitor host ←USB-C data + input power→ stationary MAIN PCBA
  USB-C/PD/protection → 5 V system and conditional 6 V motor rail
  i.MX95 + LPDDR4X + eMMC + PMIC + FPGA camera bridge candidate(s)
  J2 ⇄ 51-contact face flex ⇄ J1 on rotating FACE head PCBA
  J3 ⇄ 51-contact interaction flex ⇄ J1 on rotating INTERACTION head PCBA
  J4 ⇄ fixed face motor + motor quadrature encoder harness
  J5 ⇄ fixed interaction motor + motor quadrature encoder harness
  fixed cheek angle-sensor board(s) ⇄ main board (connector/pins TBD)

Each head: local RGB camera + IR camera + structured-light projector/driver
  RGB CSI-2 clock/2 data pairs + IR CSI-2 clock/2 data pairs → flex → bridge(s)
  3.3 V, returns, separate RGB/IR clocks, control, trigger, interlock/fault
  ← main board through flex; high projector output pulse is generated locally
Rotating magnet on each drum → stationary cheek absolute-angle sensor
  (separate from motor quadrature feedback)
```

The face and interaction boards are two *populations* of the same planned head design. The face uses SA31VA30P standard RGB; interaction uses SA36VA30P wide RGB. Both also need Mira220 IR/depth and local structured-light projection. The main board holds computation, trust/capture functions, USB, input/power conversion, motor drivers and audio. The host is outside the trust boundary; i.MX95/EdgeLock plus a camera-ingress bridge is the **reference architecture**, not a proven proof chain. No secure capture firmware/protocol is implemented by the Blender/website work.

## Board-by-board status

### 1. Stationary main PCBA

**State: detailed placement concept and circuit plan; complete schematic/routing blocked.** `hardware/electronics/deepreal-main-pcba/README.md`, `circuit-specification.md`, `design-status.json` and the KiCad project are the source. Candidate outline is 90 × 28 × 1.6 mm with a 10-layer HDI *working assumption*. The inherited board has 238 footprints and 2,313 pads, but zero routed tracks/named-net completion; its 14 functional schematic pages are note-only. It is not a publishable realistic board or a fabrication candidate (`fabrication_allowed:false`, `public_visual_allowed:false`). An earlier audit reported hundreds of DRC and schematic parity issues; do not interpret a populated board view as successful layout.

- **Compute/storage — concept placement:** U1 i.MX95, U4 LPDDR4X, eMMC, PF09/PF53 power tree and other major bodies have proposed placement. DDR escape and sequencing require real pin maps, reference circuits, analysis and routing.
- **Camera ingress — architecture blocked:** inherited U2 face and U3 interaction CrossLink-NX topology is a candidate. Zero-, one-, and two-FPGA alternatives need legal I/O, timing, margin, power and trusted-ingress review. Lattice Radiant work requires a supported Windows/Linux host; no successful target compile is recorded. Do not freeze bridge count or FPGA pins.
- **USB and power — concept:** USB 3.x over USB-C, PD sink, ESD/TVS, eFuse, 5 V system, conditional 6 V motor, independently switched/monitored 3.3 V feeds to the two heads. Motor rail should stay disabled from a plain 5 V contract. Connector location and PCB thickness are mechanically inconsistent with the enclosure today. One-cable power/thermal budget remains unmeasured.
- **Motors and position — concept:** U13/U14 H-bridge candidates drive motors via J4/J5; these connectors also carry motor encoder quadrature A/B and supply/returns. U18/U19 AS5600L absolute-angle sensors are registered on the main board but R21/R34 geometry requires a *stationary sensor beside each rotating cheek magnet*. Decide cheek daughterboards and fixed harness before changing board ownership. Startup absolute angle and motor quadrature serve different purposes.
- **Audio/tamper/temperature — concept:** one PDM microphone and tamper/temperature functions planned. SW1 tamper switch is in the register but missing from inherited board placement.
- **Gates:** G0/G1 pass (classification/requirements); G2 parts evidence in progress; G3 camera architecture blocked; G4 mechanical/flex blocked; G5 head interface in progress; G6 full schematic blocked; G7 stack/constraints in progress; G8 placement blocked; G9 critical routes and G10 complete routing not started; G11 KiCad-derived public PCB visualization blocked. Audit status before editing the KiCad design.

### 2. Face optical-head PCBA

**State: functional circuit specification and Blender carrier proxy; native KiCad board/schematic not captured.** The intended common head board holds SA31VA30P standard RGB, Mira220 IR, local AS1170/Belago1.2-class structured-light driver and pulse capacitors, rail conversion/sequencing, connector J1, and hardware-default-off lens-integrity/interlock circuit. RGB and IR each return two-lane CSI-2. Mira220 needs a separate 38.4 MHz clock; the older shared 24 MHz idea is wrong. Sensor supply, sequencing and pulsed illumination current need actual component calculations and bench proof. The 700 mA projector output pulse is **not** a claim that 700 mA must cross the flex. The optical aperture, carrier and lens geometry remain concept models. See `hardware/electronics/deepreal-optical-head/README.md` and `circuit-specification.md`.

### 3. Interaction optical-head PCBA

**State: same unbuilt electrical design, with a different RGB population and worse packaging risk.** SA36VA30P wide RGB has a larger lens envelope and autofocus/support compatibility to verify. Its envelope currently intersects the old optical carrier proxy; redesign the carrier and front window. Mira220 and the local projector/safety circuit are intended as for the face head. Neither head has a tested camera, safe projector circuit, actual PCB outline, complete BOM, or routed copper. Do not silently assume the two RGB assemblies are electrically identical.

### Possible cheek angle boards

**State: preferred physical partition, not finalized.** R34 places a rotating Ø6 × 2.5 mm reference magnet on the face drum axis and a stationary sensor/board envelope inside the outer cheek with a modeled 0.55 mm axial surface gap. Field strength, orientation, air-gap tolerance, motor interference, power/addressing and a fixed cable to the main board are unverified. Interaction still has older off-axis R21 placeholders. Resolve this partition before moving U18/U19 out of the main-board design. These are *additional small stationary boards*, not replacements for the three primary board assemblies.

## Cable and connector status (the biggest mechanical/electrical gap)

| Path | Current representation | Next proof needed |
| --- | --- | --- |
| Face head J1 → main J2 | 51-contact, 0.3 mm-pitch Hirose FH26W-51S-0.3SHW(97) interface concept. Connector-end flex width is 15.6 mm. R34/R36 pass a **straight strip** through a 16.9 mm nominal inner-bearing bore in sampled face poses. Website shows a visual path. | Numbered end-to-end pinout; flex contact side/orientation, retention, power/return and six CSI differential pairs; a deforming loop and fixed termination that clear **all** parts from −45° to +45°; vendor bend, fatigue and SI review. R35's eight full-width twist routes failed. R36's simple narrow/offset twists also failed. R37's proposed rear chamber crosses a bearing web and is too shallow for its cited dynamic-flex example. No working moving route exists. |
| Interaction head J1 → main J3 | Same planned 51-contact functional grouping; visual path in website GLB is a rest-pose proxy. | Repeat the mechanism/cable study for its different range, wide lens and carrier; complete the same electrical and fatigue work. No motion-cleared route exists. |
| Fixed motor/quad harnesses → J4/J5 | Separate visual motor leads; intended motor power plus quadrature A/B. | Exact motor and connector, pin assignments, current, shielding/EMI, strain relief and clearance through actual fixed supports. |
| Fixed cheek angle-sensor harnesses → main | Separate visual angle leads. | Decide daughterboard ownership, connector and pins, voltage/I²C addressing, sensor grounding and routing. |
| USB-C to main | Visible exterior cable/plug, proposed main-board USB circuit. | Locate a real receptacle at the opening or design a verified daughter/rigid-flex solution; support insertion loads and reconcile PCB thickness. |

The head connector has **51 positions**, not an approved 51-wire cable. Current allocation lists functional groups but no validated contact-by-contact map. The 15.6 mm dimension is the **connector end**, not permission to neck down the moving section. `docs/electrical/head-interface-checkpoint-2026-09-14.md` records preliminary current arithmetic (eight 3.3 V and eight return contacts), but actual current, voltage drop, SI, contact orientation and cycle life remain open. The three-dimensional wires in `blender/web_assembly_cables.py` merely connect visual endpoints; their paths have not passed clearance, bend, or electrical checks.

## Website presentation status and files

- **Exterior milestone — deployed reviewable visual:** `/deepreal` uses `source-public-site/public/models/deepreal.glb` and `deepreal-exterior-manifest.json`. It includes the R38 continuous inner leg, separate conceptual magnetic face, both drums/optics, and the revised USB plug and cable. Source exporter is `deepreal/blender/export_web_exterior.py`; rebuild from the R38 `.blend` with the command in `docs/website-visualization-milestones.md`. The production GLB checksum matched the committed asset on 10 October 2026, and the live Three.js model rendered. Test full orbit and phone framing after further visual edits.
- **Exploded milestone — useful review, not public release:** `/deepreal/assembly-review` loads the exterior and `deepreal-assembly-review.glb` with its manifest. It fades the shell, reveals the main board, stationary supports/drives, each moving head, optics, shields/thermal proxies, optical flex concepts and separate motor/angle harness concepts, then spreads groups. It has controls and a pauseable/reversible scrub; desktop and narrow phone viewport were checked. Source exporter is `deepreal/blender/export_web_assembly.py` and cable concepts are in `blender/web_assembly_cables.py`. Site implementation is `source-public-site/src/components/public/deepreal/assembly-review-*.tsx` plus camera helper and the route. Production route is intentionally hidden via `notFound()`.
- **Publication limitation:** the assembly's main board and head boards are visual envelopes with named major functions, not an export of the unrouted KiCad board. The review page explicitly says cable bends and clearances need review. The site-wide `npx tsc --noEmit` currently fails on unrelated pre-existing errors; targeted DeepReal lint and the two HTTP routes were checked during the previous pass. Re-run relevant checks when editing and do not claim a global clean typecheck without fixing the unrelated failures.
- **Next visual work:** improve the exploded staging and mobile legibility, label/sequence board functions so the internal architecture reads clearly, inspect any exterior feedback from the user, and promote the sequence into a production-facing page only when the story, model, and caveat are accepted. The website need not wait for routed copper, but must not imply that the displayed cables are validated.

## Practical next sequence for the next agent

1. Open both local pages and the existing GLBs/manifests. Preserve the approved exposed-drum silhouette, partial rear top cover, center island, side cheeks, ledge and visible USB lead. Review with the user if their new exterior feedback arrives.
2. Finish the **website assembly presentation**: check start/reveal/explosion/return, camera framing and focus on a phone; make the three board assemblies and separated stationary versus rotating parts understandable. Keep concept labels honest. Production publication is a separate decision from the development review route.
3. In parallel, produce one **shared interface drawing/table** for the face drum: fixed/rotating boundary, bearings, motor/pinion/ring load path, cheek absolute-angle board, head connector, moving flex, fixed termination and main-board endpoint. Base it on R30 + R34–R37, explicitly marking the R37 collision and absent loop. Then repeat for interaction with its actual optics and travel.
4. Choose a viable cable/bearing/carrier architecture together; sweep the *whole* moving path and both travel limits in front/above/end views. Do not cut a rear cavity or narrow the flex from visual guesswork. Ask a flex fabricator to assess dynamic stack, bend and differential-pair routing once a geometric candidate exists.
5. Complete the numbered J1↔J2/J3 contacts, motor J4/J5 pinout and cheek-board link; review head current/voltage drop, separate RGB/Mira clocks, local projector hardware interlock and both heads' BOM. Capture one real head KiCad design and populate it twice only after wide-RGB compatibility is verified.
6. Close main-board FPGA topology, USB mating, power budget and exact parts. Then populate actual KiCad functional sheets, run ERC, get a stackup, constrain/place critical nets, route, DRC and prototype. These steps are **later than the website milestone** but necessary for a working device.

## Read-first evidence index

- `docs/website-visualization-milestones.md` — two milestones, acceptance, export instructions and limitations.
- `docs/system-architecture/device-integration-workplan-2026-10-09.md` — current integrated engineering work order and connection map.
- `hardware/electronics/deepreal-main-pcba/design-status.json` and `README.md` — exact board gates and artifact classification.
- `hardware/electronics/deepreal-main-pcba/circuit-specification.md` and `hardware/electronics/deepreal-optical-head/circuit-specification.md` — intended functional pages/parts.
- `docs/electrical/head-interface-checkpoint-2026-09-14.md` and `hardware/electronics/deepreal-main-pcba/connector-allocation.csv` — flex grouping, caveats and unresolved pinout.
- `docs/electrical/pcb-progress-2026-09-14.md` — unrouted board audit.
- `docs/design/main-pcba-usb-mechanical-options-v0.1.md` and `docs/research/main-pcba-fpga-topology-study-v0.2.md` — major electrical/mechanical blockers.
- `docs/optics/interaction-wide-rgb-decision-2026-10-06.md` — FOV, provisional travel and wide-lens conflicts.
- `blender/refinements/r21/README.md`, `r30/README.md`, and `r34/`–`r37/README.md` — mechanism evolution and measured pass/fail boundaries.
- `blender/refinements/r31/README.md`, `r32/README.md` — laptop plate and softly pressed logo visual study.

When reporting progress, state exactly what the evidence proves. A passed static Blender intersection sweep, a placed KiCad footprint, and a good looking website animation answer different questions; none closes the others.
