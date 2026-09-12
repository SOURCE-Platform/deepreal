# DeepReal Main PCBA Feasibility Study — Architecture and Packaging v0.1

> Research baseline written before the dimensioned placement model. For the
> current mechanical-fit result and updated confidence, see
> `docs/design/main-pcba-packaging-study-v0.1.md`.

## Executive conclusion

The present `Main_PCBA` is an architecture placeholder, not a credible production-board model. Its 90 × 28 mm outline may still be achievable, but the current Blender representation materially understates the component count, connector area, power circuitry, routing difficulty, and thermal constraints.

The most important conclusion is not “the board is too small.” It is:

> **There is not yet enough engineering evidence to know whether 90 × 28 mm is the right size.**

A single 90 × 28 mm board is a plausible but aggressive target if it uses dense multilayer/HDI construction, components on both sides, and a carefully consolidated connector strategy. A 100 × 32 mm board is a safer single-board starting envelope. A two-board 90 × 28 mm stack offers the most placement area inside the existing shield volume, but adds high-speed interconnect, cost, and thermal complexity.

Current confidence levels are:

- **About 30%** that the component architecture is complete enough for an investor-facing internal model.
- **About 40–50%** that the entire production architecture can fit on one 90 × 28 mm PCB.
- **About 60–70%** that it can fit on one 100 × 32 mm PCB.
- **About 70–80%** that it can fit in the existing 90 × 28 × 15 mm electronics volume as a two-board stack.

These are engineering estimates, not simulation results. Web research alone cannot raise confidence much beyond roughly 50–60%. The next decisive work is a preliminary schematic, exact component selection, an FPGA pin-and-throughput proof, and a placement-only study in KiCad or Altium.

## What is wrong with the current model

The Blender model contains the intended major functions, but it does not represent the physical population of a real PCB. It currently depicts a 90 × 28 × 1.6 mm board with simplified blocks for an i.MX95, CrossLink-NX, memory, storage, PMICs, USB-PD, ESD, motor drivers, emitter drivers, microphone, tamper switch, and connectors.

It is visually and physically incomplete in five important ways:

1. **Packages are approximate.** Several modeled bodies do not match a selected orderable package.
2. **Support circuitry is absent.** Regulators, inductors, MOSFETs, clocks, boot memory, pull-ups, decoupling, bulk capacitors, filters, protection, and test points are mostly missing.
3. **Connectors are understated.** Four modeled camera connectors occupy much less edge length and area than a representative MIPI-capable FPC connector.
4. **Routing volume is invisible.** BGA escape, DDR length matching, MIPI differential lanes, return paths, vias, keep-outs, and copper pours have not been designed.
5. **The shield volume has not been proven against a real assembly.** Top and bottom component heights, thermal hardware, assembly clearances, and connector mating envelopes remain approximate.

Visible surface traces are not the main measure of realism. On a real high-speed board, much of the DDR and MIPI routing may be under soldermask or on internal layers. The visual cues that are currently missing are exact footprints and pads, dense passives, vias, reference designators, copper/ground features, real connectors, test pads, and believable component-height variation.

## Reference architecture under evaluation

This study assumes the full two-drum, four-camera DeepReal device described in the current architecture documents:

- One NXP i.MX95 application processor
- One or two Lattice CrossLink-NX FPGAs, depending on the validated camera topology
- 4 GB LPDDR4X or LPDDR5 working memory
- 16–32 GB or greater eMMC storage
- NXP PF09 plus the number of PF53 companion regulators established by the power tree
- One USB-C port for power and SuperSpeed data
- Two motor channels, two structured-light/emitter channels, four camera links, microphone, tamper sensing, and production/debug access

The i.MX95 itself is available in 15 × 15 mm and 19 × 19 mm packages. It provides two four-lane MIPI CSI-2 interfaces and supports multiple virtual channels.[^1] NXP’s current FRDM-i.MX95 reference shows the 15 mm processor with 8 GB LPDDR4X, 32 GB eMMC, one PF09, and two PF53 devices.[^2]

The smaller i.MX95 package is attractive for DeepReal, but NXP notes that its denser ball pitch makes signal and power integrity more demanding and limits the maximum supported DDR data rate compared with the 19 mm package.[^3] Package choice therefore cannot be made from body size alone.

## Major corrections to the modeled parts

### FPGA size and topology

The current model gives the CrossLink-NX a roughly 13 × 13 mm body. Lattice offers the family in several packages, but its published four-to-one image aggregation reference targets the LIFCL-40 in a 17 × 17 mm, 400-ball package.[^4] That reference demonstrates four-input aggregation, but it does **not** prove DeepReal’s exact resolution, frame rate, lane rate, output topology, or full-rate cryptographic hashing requirement.

The FPGA decision is the largest unresolved architectural gate:

- One 17 mm FPGA may aggregate all four cameras if lane count, bandwidth, I/O banking, and timing close.
- Two smaller FPGAs may make routing and camera grouping easier, but consume more total support area and power.
- A different camera topology may allow direct use of the i.MX95’s two CSI-2 receivers and eliminate or reduce FPGA scope.

Lattice’s hardware checklist also shows that the FPGA needs multiple filtered rails, local decoupling, configuration support, clocking, and programming provisions beyond the single visible package.[^5]

### Memory and storage

The current pair of 8 × 6 mm memory placeholders is not representative of a selected 4 GB solution. One production Micron 32 Gb ×32 LPDDR4X device is approximately 10 × 14.5 mm and can supply 4 GB by itself.[^6] A one-package x32 topology may save area, but its compatibility, speed, placement, and routing must be verified against the chosen i.MX95 package and NXP design guidance.

The modeled 10 × 7 mm eMMC is also smaller than a representative Micron 32 GB production package at approximately 11.5 × 13 mm.[^7] Smaller eMMC packages exist, but an exact part must be chosen before the board can be dimensioned honestly.

### Power architecture

The modeled PF09 and PF53 bodies are approximate. PF09 is an 8 × 8 mm QFN power-management IC; its bucks require nearby inductors, switching capacitors, controlled high-current loops, and thermal vias.[^8] PF53 is a 3.5 × 4.5 mm companion regulator.[^9] NXP’s current reference uses two PF53 devices, although NXP states the three-PMIC arrangement is not mandatory for every configuration.[^3]

The current model also appears to be missing the largest conceptual power block: **USB-PD input conversion**. The CYPD3177 is only a 4 × 4 mm USB-PD sink controller. It negotiates a power contract and controls external power-path components; it does not convert a 9 V, 15 V, or 20 V USB-PD input into the approximately 5 V system input needed by the downstream PMIC architecture.[^10]

If DeepReal needs more than the 15 W available from 5 V at 3 A, the board likely needs:

- External VBUS MOSFET and gate/control support
- Overvoltage, overcurrent, reverse-current, and transient protection
- A synchronous input buck converter sized for the selected PD voltage and peak load
- A power inductor, current sense/protection parts, and substantial input/output capacitance
- Bulk energy storage and separated/noise-managed motor and emitter power paths

This subsystem can occupy more useful board area than the CYPD3177, PF09, and PF53 packages combined. A representative USB-PD power reference includes the controller, power-path protection, DC/DC conversion, magnetics, and supporting passives rather than a single IC.[^11]

### USB-C data path

USB-C receptacle orientation means the SuperSpeed pairs must be switched or otherwise handled for plug reversal. A USB 3 orientation switch/mux or a suitable integrated redriver/mux is therefore likely required in addition to ESD protection.[^12] The final design also needs a deliberate connector-shell/chassis bond and an impedance-controlled route from the receptacle to the i.MX95.

### Camera connectors

The existing four camera blocks are each about 6 × 2.4 mm. A representative 22-position, 0.5 mm-pitch Hirose FH34 MIPI-capable FPC connector is approximately 13 × 3.8 mm and 1 mm high.[^13] Four such bodies alone would occupy about 198 mm² and 52 mm of edge length before mating, latch, cable-bend, spacing, and routing clearances.

DeepReal may use a smaller 0.3 mm-pitch connector or consolidate signals into one connector per drum. That must be treated as a mechanical and electrical architecture choice, not corrected cosmetically in Blender.

## Realistic subsystem inventory

The following is the minimum credible population to reserve in an early placement study. Exact quantities remain open.

### Compute, memory, and trust

- i.MX95 processor and BGA escape field
- One or two CrossLink-NX FPGAs
- One 4 GB x32 LPDDR package or validated alternative
- eMMC storage
- Optional QSPI/Octal-SPI boot or recovery flash
- Board-identity/configuration EEPROM
- Main and low-frequency clock sources, load components, reset, watchdog, and boot straps
- JTAG/UART/programming pads and production test points

### Power

- USB-PD sink controller and configuration resistors
- VBUS power-path MOSFET(s), surge/ESD protection, and current/voltage monitoring
- High-voltage-to-system-rail buck converter if accepting more than 5 V
- PF09 and one or two PF53 regulators, subject to load analysis
- Regulator inductors, input/output capacitors, compensation parts, ferrite beads, and thermal-via fields
- Local camera/FPGA/analog LDOs or load switches as required
- Bulk motor and emitter capacitance, rail segmentation, and NTC/temperature sensing

### Camera and high-speed I/O

- Four camera FPC connectors or a consolidated connector topology
- MIPI lane/clock routing and reference-ground continuity
- Camera clock, reset, trigger, synchronization, I²C, and rail-enable wiring
- I²C pull-ups and possibly bus switches/multiplexers
- USB-C receptacle, SuperSpeed orientation mux/redriver, ESD, and shell bonding

### Motion, illumination, sensing, and safety

- Two motor-driver ICs, suppression components, local bulk capacitance, and motor/encoder connectors
- Two emitter/VCSEL-driver ICs with their inductors and local capacitance
- Hardware emitter enable, fault monitoring, temperature sensing, and eye-safety interlock path
- PDM microphone and acoustic keep-out
- Tamper switch and protected signal path
- Status LED(s), service input if required, and manufacturing test access

A realistic board of this complexity will likely contain on the order of **100–250 or more mounted components**, most of them small capacitors, resistors, inductors, protection parts, and test provisions. This range is an early density estimate, not a preliminary bill of materials.

## Spatial feasibility

### Current 90 × 28 mm outline

The raw area is 2,520 mm². A simple first-order allowance for a 1.5 mm perimeter keep-out, four 3 mm-radius mounting keep-outs, and a 5 mm connector corridor leaves about 1,610 mm² of nominal top-side placement area. This is not the same as routable area: BGA escape, high-current loops, thermal copper, cable access, component height, and assembly spacing remove additional freedom.

For comparison, Variscite packages the i.MX95, LPDDR, eMMC, power, and clocks on a 30 × 55 × 4.25 mm system-on-module, or 1,650 mm² of raw board area.[^14] That module does not include DeepReal’s FPGA aggregation, four camera connectors, USB-PD input conversion, motor and emitter drivers, or product-specific I/O. Digi’s comparable i.MX95 module is 40 × 45 × 3.5 mm.[^15]

This comparison does not prove that 90 × 28 mm fails; commercial modules include connectors and design margins not applicable to a soldered custom board. It does show that the current outline demands a very dense, product-specific implementation rather than a conventional single-sided layout.

### Preliminary reservation zones

These rectangles are conservative planning allowances, not final component courtyards:

| Zone | Initial reservation | Reason |
|---|---:|---|
| i.MX95, escape, local decoupling | 22 × 22 mm | 15 mm BGA plus escape and high-frequency support |
| LPDDR and matched routing | 16 × 18 mm | Package plus close-coupled routing zone |
| eMMC and support | 15 × 16 mm | Representative 11.5 × 13 mm package |
| CrossLink-NX and support | 22 × 22 mm | 17 mm reference package plus rails/configuration |
| PF09/PF53 power island | 27 × 20 mm | PMICs, inductors, capacitors, thermal loops |
| USB-PD, input buck, mux, ESD | 24 × 18 mm | Controller is a small part of the subsystem |
| Motion and emitter channels | 24 × 12 mm | Drivers, inductors, suppression, bulk capacitance |
| Clocks, boot, debug, tamper, mic | 20 × 10 mm | Distributed support functions |
| Four representative camera connectors | 52 × 3.8 mm | Connector bodies only |

Several routing zones can overlap and many small parts can move to the back side, but the reservation set cannot be packed cleanly on one side of the current outline. A credible 90 × 28 mm solution therefore assumes two-sided assembly and advanced routing.

### Options to carry forward

**Option A — 90 × 28 mm single PCB.** Preserve the enclosure concept. Treat this as the high-density challenge case. It likely requires 10 or more layers, microvias/via-in-pad or comparable HDI techniques, bottom-side population, and tightly controlled flex exits. Estimated spatial confidence: 40–50%.

**Option B — approximately 100 × 32 mm single PCB.** Adds 27% raw area and materially improves edge length, connector spacing, power layout, and BGA escape. This is the recommended single-board feasibility baseline if the mechanical assembly can absorb 10 mm of added width and 4 mm of added depth. Estimated spatial confidence: 60–70%.

**Option C — two 90 × 28 mm PCBs inside the existing shield volume.** Place the i.MX95, DDR, eMMC, PMICs, and clocks on a core board; place camera aggregation, connectors, USB input, and actuator interfaces on an I/O board. This offers the most placement area but introduces a high-speed board-to-board connector, extra cost, service/assembly complexity, and another thermal interface. Estimated volume confidence: 70–80%.

These options should remain open until the same exact component set is placed in EDA for all three.

## Path to a defensible production-board model

### Gate 1 — Freeze the electrical requirements

Define the four camera sensors and their exact active resolution, frame rate, bit depth, MIPI lane count/rate, virtual-channel behavior, clocking, and synchronization. Establish motor stall current, emitter pulse/continuous current, compute power states, USB data requirement, and desired single-cable power budget.

**Deliverable:** one-page interface and power-budget table with nominal, peak, and fault values.

### Gate 2 — Prove the camera/FPGA topology

Create a real Lattice Radiant project for the candidate CrossLink-NX package. Compile the four-stream pipeline, allocate all D-PHY lanes and I/O banks, prove output bandwidth into the i.MX95, and determine whether the proposed trusted hash path can operate at full rate. Compare one-FPGA, two-FPGA, and reduced-FPGA architectures.

**Deliverable:** selected FPGA part/package, pin map, utilization/timing report, lane map, bandwidth calculation, power estimate, and explicit disposition of the hash requirement.

### Gate 3 — Build the preliminary schematic and power tree

Obtain NXP’s controlled i.MX95 reference-design package and hardware guide. Select orderable memory, eMMC, PMIC, input buck, USB switch, connectors, drivers, clocks, and protection components. Calculate every rail and determine whether one or two PF53 devices are required.

**Deliverable:** reviewable schematic v0.1, power tree, exact preliminary BOM, and package-height table.

### Gate 4 — Run a three-option EDA placement study

Create exact footprints and mechanical keep-outs for 90 × 28, 100 × 32, and the 90 × 28 stack. Place every IC, connector, inductor, bulk capacitor, mounting hole, shield contact, flex bend, thermal interface, test point region, and a representative decoupling population. Reserve BGA escape and controlled-impedance routing corridors.

**Deliverable:** top/bottom assembly drawings and measured occupied/free-area comparison for all three options.

### Gate 5 — Review manufacturability and signal/power integrity

Engage an engineer or design house with shipped i.MX8/i.MX9, LPDDR, MIPI CSI-2, USB 3, and dense BGA experience. Define the PCB stack-up and fabrication class with the intended manufacturer. Review DDR topology, MIPI and USB impedance, power-distribution impedance, switch-node containment, thermal paths, EMC, assembly yield, and test access.

**Deliverable:** reviewed placement, preliminary layer stack, via technology, routing constraints, SI/PI risk register, and a written go/no-go on each board outline.

### Gate 6 — Replace the Blender fiction with EDA-derived geometry

Export the chosen EDA board outline and component placement, use manufacturer STEP models for visible packages and connectors, and model the real shield, spreader, pad stack, fasteners, flex exits, and cable bends. Surface copper can be selectively rendered for communication, but component density, pads, vias, silkscreen, and reference designators should come from the actual board data.

**Deliverable:** investor-safe mechanical visualization explicitly labeled “preliminary engineering layout,” not “production PCB.”

### Gate 7 — Build and measure EVT hardware

Fabricate an engineering validation board and test power sequencing, brownout/fault behavior, DDR stress, all four camera streams, USB throughput, motor noise coupling, emitter safety shutdown, thermals, radiated/conducted emissions, and sustained workload stability.

**Deliverable:** measured EVT report and revised production layout.

## Recommended immediate decision

Do not spend the next effort adding decorative traces and capacitors to the current Blender board. That would make the model look more convincing without making it more true.

The immediate engineering package should be:

1. Requirements and power-budget freeze
2. CrossLink-NX topology/pinout proof
3. Preliminary schematic with exact packages
4. Comparative placement study for 90 × 28, 100 × 32, and a 90 × 28 stack

At the end of those four items, the board outline can be selected with roughly 70% confidence and the Blender model can be rebuilt from real engineering data. After routing and SI/PI review, confidence can rise to roughly 85%. It should not be represented as production-feasible with high confidence until an EVT board has been built and measured.

## Sources

[^1]: NXP Semiconductors, “i.MX 95 Applications Processors,” product page and feature table, including package and MIPI CSI-2 information. https://www.nxp.com/products/i.MX95
[^2]: NXP Semiconductors, “FRDM-i.MX95 Block Diagram,” showing i.MX95, LPDDR4X, eMMC, PF09, and two PF53 regulators. https://www.nxp.com/assets/block-diagram/en/FRDM-IMX95.pdf
[^3]: NXP Technical Support, “i.MX95 DDR MT/s difference between packages,” package-density, DDR-rate, and PMIC-topology clarification. https://community.nxp.com/t5/i-MX-Processors/i-MX95-DDR-MT-s-difference-between-packages/m-p/2369534
[^4]: Lattice Semiconductor, “4 to 1 Image Aggregation with CrossLink-NX,” LIFCL-40-7BG400I target and four-input reference architecture; the page currently identifies this reference as discontinued and for reference only. https://www.latticesemi.com/products/designsoftwareandip/intellectualproperty/referencedesigns/referencedesign04/4to1
[^5]: Lattice Semiconductor, “CrossLink-NX Hardware Checklist,” power, decoupling, configuration, clock, and programming guidance. https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/AD2/FPGA-TN-02149-1-7-CrossLink-NX-Hardware-Checklist.ashx?document_id=52782
[^6]: Micron Technology, “LPDDR4 Part Catalog,” MT53E1G32D2FW production 32 Gb ×32 device and package dimensions. https://sg.micron.com/products/memory/lpddr-components/lpddr4/part-catalog
[^7]: Micron Technology, “e.MMC Part Catalog,” production 32 GB device package dimensions. https://www.micron.com/products/storage/managed-nand/emmc/part-catalog
[^8]: NXP Semiconductors, “PF09: Power Management Integrated Circuit,” package information; see also the PF09 hardware design guide for switching-loop and thermal guidance. https://www.nxp.com/products/PF09 and https://www.nxp.com/docs/en/application-note/AN14910.pdf
[^9]: NXP Semiconductors, “PF53: 12 A Core Supply Regulator,” package information. https://www.nxp.com/products/PF53
[^10]: Infineon Technologies, “CYPD3177 EZ-PD BCR USB Type-C Port Controller,” package, power-contract, and external power-path information. https://www.infineon.com/assets/row/public/documents/24/49/infineon-cypd3177-24lqxq-datasheet-en.pdf
[^11]: Texas Instruments, “PMP23300 USB Type-C Power Delivery reference design,” illustrating controller, protection, switching conversion, magnetics, and supporting power components. https://www.ti.com/tool/PMP23300
[^12]: Texas Instruments, “How to Implement USB Type-C and USB Type-C Power Delivery,” explanation of reversible SuperSpeed routing and signal switching. https://www.ti.com/document-viewer/lit/html/SSZT765/GUID-E2A58524-B9DF-4C85-8572-E26B66671E97
[^13]: Hirose Electric, “FH34SRJ Series,” MIPI-capable 0.5 mm-pitch FPC connectors and 22-position dimensional data. https://www.hirose.com/en/product/series/FH34SRJ
[^14]: Variscite, “DART-MX95 System on Module Datasheet,” 30 × 55 × 4.25 mm module with i.MX95, memory, storage, clocks, and power. https://variscite.com/wp-content/uploads/2024/06/DART-MX95_Datasheet.pdf
[^15]: Digi International, “ConnectCore 95 SOM,” 40 × 45 × 3.5 mm i.MX95 module with memory, storage, and power. https://www.digi.com/products/embedded-systems/digi-connectcore/system-on-modules/digi-connectcore-95-som-nxp-i-mx-95
