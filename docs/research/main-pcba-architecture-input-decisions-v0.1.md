# DeepReal Main PCBA - Architecture Input Decisions v0.1

> **Superseded status note (13 September 2026):** This record is preserved for
> traceability, but its two-FPGA decision has been reopened. Requirements v0.2 and
> `main-pcba-fpga-topology-study-v0.2.md` are authoritative. Zero FPGA is presently
> rejected; one versus two devices requires legal Radiant compile and timing data.

| Field | Value |
| --- | --- |
| Date | 12 September 2026 |
| Status | Schematic input baseline; prototype validation required |
| Applies to | DeepReal Main PCBA preliminary engineering layout |
| Board target | 90 x 28 x 1.6 mm; approximately 15 mm populated envelope |

## Executive decision
The schematic should not be drawn from the current Blender component arrangement.
Six upstream decisions change the rail count, connector pinout, BGA escape, FPGA
count, power path, safety circuit and trusted-data boundary. This review resolves
those decisions far enough to begin a preliminary schematic, while preserving the
90 x 28 mm board as a target rather than claiming it already fits.

The recommended EVT architecture is:

```text
FACE DRUM                              INTERACTION DRUM
IMX708 RGB --\                        IMX708 RGB --\
               >-- LIFCL-17 -- CSI-0                  >-- LIFCL-17 -- CSI-1
Mira220 IR ---/                        Mira220 IR ---/
Belago1.2 + AS1170                     Belago1.2 + AS1170
Pololu 5137 + DRV8213                  Pololu 5137 + DRV8213
                         \            /
                    NXP i.MX 95 + LPDDR
                  protected capture buffers
                              |
                  EdgeLock-backed signatures
                              |
                     USB 3.x + USB-C PD
```

The most important change is **two small camera-bridge FPGAs, one per drum**, not
one unproven 9.5 mm FPGA with two outputs. The current Lattice reference design
supports virtual-channel aggregation, but its supplied project targets the 17 x
17 mm, 400-ball LIFCL-40 package and produces one CSI-2 output. Two LIFCL-17
devices preserve the desired face/interaction split into the i.MX 95's two camera
ports, shorten routing, and avoid forcing a 17 mm FPGA into the center of the board.

## Decision register

| Gate | Schematic baseline | Confidence | What remains to prove |
| --- | --- | ---: | --- |
| RGB sensor | 2 x Raspberry Pi CM3 Sensor Assembly, standard FOV, SA31VA30P | 70% | i.MX 95 driver port, flex life, thermal/optical test |
| IR sensor | 2 x ams OSRAM Mira220 mono CSP with AR glass, Q65114A0087 | 80% | lens selection, samples, depth accuracy |
| Dot projector | 2 x ams OSRAM Belago1.2, Q65114A0198 | 75% | IEC 60825-1 system classification and optical bench |
| Projector driver | 2 x ams OSRAM AS1170-ZWLM, Q65113A7129 | 75% | interlock circuit review and flex pulse integrity |
| Motor | 2 x Pololu item 5137, 6 V, 0.67 A theoretical stall each | 90% electrical | torque/noise/life in the actual gear train |
| Motor driver | 2 x TI DRV8213RTE | 90% | set current limit and verify stall algorithm |
| USB-C power | 15 V at 3 A preferred PD contract; 45 W input ceiling | 80% board input | operation from low-power laptop ports |
| Camera bridge | 2 x CrossLink-NX LIFCL-17 in 6 x 6 mm csfBGA121, one per drum | 70% | pin assignment, Radiant compile, timing and SI |
| Hashing boundary | i.MX 95 protected capture memory; EdgeLock signs roots | 80% architecture | demonstrate DMA isolation and throughput |
Confidence percentages are engineering judgments, not statistical measurements.
They describe how safe each decision is as an input to the first schematic.

## 1. RGB sensor

### Decision

Use two **Raspberry Pi Camera Module 3 Sensor Assemblies, standard visible-light
variant SA31VA30P**, as the EVT schematic and packaging baseline.

The assembly is 10.8 x 10.8 mm with a 6.98 mm conservative optical depth. It uses
the Sony IMX708, outputs RAW10, offers common 1080p50 and 720p100 modes, and has a
published reference schematic and BOM. Raspberry Pi states production through at
least January 2030.[^1] This is the smallest documented IMX708 integration path;
the complete 25 x 24 mm Camera Module 3 board does not fit in the drum.

### Schematic effect

- Two 30-pin sensor-assembly connectors or equivalent drum flex terminations.
- 1.1 V digital, 1.8 V I/O and 2.8 V analog rails, with local filtering.
- Two-lane CSI-2, I2C/CCI, clock, reset/power-down and autofocus control.
- EEPROM/VCM support copied from the published reference design rather than
  invented from the bare Sony part.

### Limit

The 0 to 50 C rating and Raspberry Pi-oriented software make this an EVT choice,
not a guaranteed production choice. The board should keep the RGB rail and flex
interface replaceable. The full-resolution IMX708 mode is not the initial FPGA
throughput target; start with 1920 x 1080 at 50 fps RAW10 or lower.

## 2. IR structured-light sensor

### Decision

Replace the provisional OmniVision OV9281 with **two ams OSRAM Mira220 monochrome
CSP devices with AR glass, Q65114A0087**.

The reason is documentation risk, not a claim that OV9281 is a bad sensor. Its
public product brief omits the package outline and full pin-level integration
details. Mira220 has a current 91-page public datasheet with the pinout, a 5.4 x
5.4 x 0.74 mm CSP, 1600 x 1400 global-shutter array, 90 fps maximum, two-lane
MIPI CSI-2, external trigger support, a dedicated illumination-trigger output and
high sensitivity at 940 nm. It consumes about 168 mW at full resolution and 30
fps.[^2] These are exactly the details a real schematic needs.

### Schematic effect

- Three sequenced rails: 2.5 V, 1.35 V and 1.8 V.
- Local capacitors for each supply pin and the internal regulator outputs.
- A 12 kilohm, 0.1% bias resistor and the manufacturer-specified power sequence.
- A 2.5 V rail capable of the documented 350 mA startup interval per sensor.
- Two-lane CSI-2, CCI/I2C, external clock, reset and illumination trigger.

### Limit

The receiving lens is still an optical selection, not a main-PCBA schematic
selection. It must be chosen with the projector FOV and the drum window. Depth
quality cannot be established from package dimensions alone.

## 3. Projector and driver

### Decision

Use one **Belago1.2 Q65114A0198** dot projector and one **AS1170-ZWLM
Q65113A7129** driver per drum.

Belago1.2 is a 4.2 x 3.6 x 3.325 mm, 940 nm projector. At the reference short
pulse it uses 700 mA for 1 ms at 30 fps and operates at 1.65 to 2.25 V. It projects
roughly 12,000 dots in the stated camera FOV and exposes a resistive lens-integrity
interlock on Sense1/Sense2.[^3] AS1170 is a 2.25 x 1.5 x 0.6 mm production VCSEL
driver with a boost converter and up to 1 A per channel.[^4]

Two drivers are retained even though AS1170 has two channels. Independent drivers
reduce the length of each high-current loop and prevent one shared driver fault
from disabling both depth heads. They should remain stationary near the two drum
connector zones.

### Schematic effect

- Two AS1170 devices, two 1 uH-class inductors and their local input/output caps.
- Feed each AS1170 from a filtered 3.3 V rail within its 2.7 to 4.4 V range.
- Independent hardware enables, current programming and shutdown paths.
- The Belago Sense1/Sense2 loop must participate in a hardware cutoff; firmware
  alone is not an eye-safety mechanism.
- The projectors are time-multiplexed so only one is intentionally active.

### Safety gate

Belago1.2 is not itself a finished Class 1 product. The manufacturer explicitly
states that the incorporating product may need IEC 60825-1 evaluation. No public
or investor claim of eye safety is justified until an accredited system-level
assessment covers normal operation and single faults.[^3]

## 4. Motor electrical load

### Decision

Use two **Pololu 75:1 Micro Metal Gearmotor MP 6V with 12 CPR encoder, side
connector, item 5137** for the EVT baseline.

The official figures are 6 V nominal, 70 mA no-load, 170 mA at maximum efficiency,
and 670 mA theoretical stall per motor. Two motors therefore create:

| Condition | Per motor | Two motors |
| --- | ---: | ---: |
| No load | 0.42 W | 0.84 W |
| Maximum-efficiency electrical input | 1.02 W | 2.04 W |
| Theoretical stall | 4.02 W | 8.04 W |

Pololu warns that a stall can damage the motor or gearbox.[^5] The rail must
survive the transient, but firmware must not permit sustained stall.

Use **DRV8213RTE** instead of the current DRV8837C-class placeholder. It accepts
up to 11 V, has a 4 A peak rating, integrated current measurement/regulation and,
in the 3 x 3 mm RTE package, hardware stall detection.[^6]

### Schematic effect

- A separate 6 V motor rail designed for 1.5 A combined short transient load.
- Two DRV8213RTE drivers, motor-current telemetry into the M7 ADC, and hardware
  current limits initially set close to the measured mechanism requirement.
- Local bulk capacitance at the drivers and isolation from camera/SoC rails.
- Encoder supply, quadrature inputs, ESD/filtering and two motor/flex connectors.

## 5. USB-C power target

### Decision

Design the input for a **45 W ceiling with 15 V at 3 A as the preferred PD
contract**. Keep 9 V/3 A and 5 V/3 A as degraded-power modes.

This does not mean the product should dissipate 45 W. It means the connector,
protection, sink controller and first converter have enough transient margin.
NXP measured about 2.43 W on the i.MX 95/LPDDR rails for a dual-4K ISP use case and
about 5.15 W in a combined CPU/NPU/GPU stress case; those figures exclude the full
DeepReal peripheral and conversion budget.[^7] Motors alone can briefly request
8.04 W. A realistic early allocation is:

| Load group | Sustained design allowance | Short peak allowance |
| --- | ---: | ---: |
| i.MX 95 + LPDDR + PMIC losses | 7 W | 9 W |
| Two FPGAs + cameras | 3 W | 4 W |
| Projectors and drivers | 1 W average | 3 W pulse |
| Motors and drivers | 2.5 W typical motion | 9 W stall-limited |
| USB/eMMC/clock/miscellaneous | 3 W | 4 W |
| **Total** | **about 16.5 W** | **about 29 W** |
The Infineon CYPD3177 supports 5, 9, 12, 15 and 20 V PD sink contracts and up to
100 W, so a 45 W configuration is within its published capability.[^8] PF09 itself
expects 3.3 to 5.0 V, so 15 V VBUS must feed protected buck stages before PF09 and
the motor/emitter rails.[^9]

### Product caveat

A laptop USB-C data port is not guaranteed to source 45 W. Full operation from
one cable therefore requires one of these to prove true in EVT:

1. the sustained product is tuned to 15 W with capacitive energy for short peaks;
2. the connected host actually offers the higher PD contract; or
3. the customer uses a powered USB-C dock that carries data and supplies power.

The schematic should measure the negotiated power and enforce power modes. The
website should say "single USB-C connection" only after this behavior is tested,
not imply full performance from every laptop port.

## 6. FPGA topology

### Decision

Use **two LIFCL-17 devices in 6 x 6 mm csfBGA121**, one per drum. Each receives one
RGB stream and one IR stream, assigns stable virtual-channel IDs, checks CSI packet
integrity, adds frame/sequence metadata, and transmits one four-lane CSI-2 stream
to its dedicated i.MX 95 receiver.

Why not the current single 9.5 mm LIFCL-40:

- Lattice's current virtual-channel aggregation design supports two to eight RX
  channels and up to 2.5 Gbit/s per TX lane, but the supplied project targets the
  17 x 17 mm LIFCL-40 caBGA400.[^10]
- The published resource example for two RX channels is only 2,931 LUTs, 2,109
  flip-flops and 12 EBRs, which is compatible with the smaller LIFCL-17 resource
  class on paper.[^10]
- The two-device topology matches the product requirement of face drum to CSI-0
  and interaction drum to CSI-1 without inventing a two-output implementation.
- Two 6 x 6 mm bodies use less package area than one 9.5 x 9.5 mm body and can be
  placed near their associated connector pairs, although duplicate decoupling and
  configuration support consume some of that gain.

### Initial throughput target

Use 1080p50 RAW10 RGB plus 1600 x 1400 at 60 fps RAW10 IR per drum:

| Stream | Active payload |
| --- | ---: |
| RGB | 1.04 Gbit/s |
| IR | 1.34 Gbit/s |
| Per-drum sum | 2.38 Gbit/s |
| With 25% engineering overhead | 2.98 Gbit/s |
| Four-lane output requirement | about 0.75 Gbit/s/lane |

This is comfortably below the published 2.5 Gbit/s hard-TX limit. The IR input is
about 0.84 Gbit/s/lane after the same overhead, below the 1.5 Gbit/s soft-RX
limit. Full 11.9 MP RGB at high frame rate is not part of this first mode.

### Mandatory gate before layout freeze

Run the exact two-input/one-output design twice in Lattice Radiant against the
LIFCL-17 csfBGA121, perform pin assignment, and require timing closure. If the
package cannot expose the selected hard/soft D-PHY mapping, fall back to the
14 x 14 mm caBGA256 package or revisit a single 17 mm LIFCL-40. Blender must show
the two-FPGA baseline and retain a marked fallback keep-out until this compile is
complete.

## 7. Trusted hashing path

### Decision

Do **not** make full-frame SHA-256 inside CrossLink-NX a schematic requirement.
Use the FPGA for deterministic ingress, virtual-channel identity, packet checks,
frame counters and timing metadata. DMA the frames into i.MX 95 memory that is
inaccessible to normal-world Linux until hashing completes. Hash in the protected
i.MX 95 path, form a Merkle/rolling root for the capture window, and ask EdgeLock
to sign that root with the device key.

The distinction matters: CrossLink-NX's configuration security protects the FPGA
design, but public documentation does not demonstrate a user-accessible streaming
SHA implementation at DeepReal's camera rate. NXP publicly documents two 4-lane
CSI inputs, a camera domain with TRDC components, DDR inline encryption and an
isolated EdgeLock enclave with cryptographic services.[^11][^12] That provides a
more supportable first trust boundary.

### Schematic effect

- No extra TPM or secure element in the baseline.
- FPGA configuration must be authenticated and its version/digest included in
  the signed evidence metadata.
- Reserve authenticated boot/configuration storage and recovery access.
- Route FPGA frame-valid/error/sequence sideband into trusted i.MX GPIO/SPI.
- Keep camera reset, sensor I2C and projector enable under the M7/trusted-control
  domain rather than exposing unrestricted control to Linux.

### Claim limit

This is an architecture, not proof that the path is secure. EVT must demonstrate
that camera DMA lands only in protected buffers, Linux cannot read or modify them
before commitment, sustained hashing meets the stream rate, and error injection
breaks or invalidates the signed window. Until then, describe the product as
"designed for hardware-backed capture integrity," not as a completed secure
camera.

## Consequences for the current 3D PCBA

The current visual board should change after the schematic block pages are drawn:

- replace one central 9.5 mm FPGA with two 6 mm FPGA zones nearer the camera edge;
- separate the touching i.MX 95 and LPDDR packages and show assembly courtyard;
- replace two generic projector-driver blocks with AS1170 packages, inductors and
  local capacitors;
- replace generic motor drivers with two 3 x 3 mm DRV8213RTE packages;
- add the Mira220 rail regulators/sequencing and their larger-than-expected local
  capacitor population;
- size the USB input protection and buck stages for 15 V/3 A;
- reserve FPGA configuration/boot circuitry and trusted sideband connections;
- route four distinct MIPI input corridors and two four-lane output corridors.

The 90 x 28 mm target is still plausible, but not yet demonstrated. Two 6 mm
FPGAs are favorable for silicon area and routing locality; the added sensor rails,
power magnetics, bulk capacitors and connector escape are unfavorable. A real
placement can now answer the size question because the architecture inputs are no
longer generic placeholders.

## Schematic start/stop rule

The preliminary schematic may begin from this record. Do not call it complete
until these four gates close:

1. LIFCL-17 csfBGA121 pin assignment and timing compile for the exact camera modes.
2. NXP review of the 15 mm i.MX 95 + PF09/PF53 power tree and DDR topology.
3. ams OSRAM confirmation of Mira220 and Belago1.2 sample availability plus an
   eye-safety design review.
4. Bench measurement of one real motor/gear/drum axis for startup, running, jam
   current, torque, noise and settling time.
## Sources

[^1]: Raspberry Pi, [Camera Module 3 Sensor Assembly product brief](https://datasheets.raspberrypi.com/camera/sensor-assembly-product-brief.pdf) and [product page](https://www.raspberrypi.com/products/camera-module-3-sensor-assembly/).
[^2]: ams OSRAM, [Mira220 public datasheet](https://look.ams-osram.com/m/7591efdbe4af32dc/original/Mira220-1-2-7-2-2-MP-NIR-enhanced-global-shutter-image-sensor.pdf) and [product page](https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-mira220).
[^3]: ams OSRAM, [Belago1.2 public datasheet](https://look.ams-osram.com/m/4971b838d6356daa/original/Belago1-2-Dot-pattern-infrared-illuminator.pdf) and [product page](https://ams-osram.com/products/lasers/ir-lasers-vcsel/ams-belago1-2-dot-pattern-illuminator-vcsel).
[^4]: ams OSRAM, [AS1170 product page](https://ams-osram.com/products/drivers/led-drivers/ams-as1170-2-channel-led-and-vcsel-driver-ic).
[^5]: Pololu, [75:1 Micro Metal Gearmotor MP 6V with encoder, item 5137](https://www.pololu.com/product/5137/specs).
[^6]: Texas Instruments, [DRV8213 product page](https://www.ti.com/product/DRV8213) and [datasheet](https://www.ti.com/lit/ds/symlink/drv8213.pdf).
[^7]: NXP, [i.MX 95 Power Consumption Measurement, AN14449](https://www.nxp.com/docs/en/application-note/AN14449.pdf).
[^8]: Infineon, [CYPD3177 EZ-PD BCR product page](https://www.infineon.com/part/CYPD3177-24LQXQ).
[^9]: NXP, [PF09 data sheet](https://www.nxp.com/docs/en/data-sheet/PF09.pdf) and [PF09 hardware guidelines](https://www.nxp.com/docs/en/application-note/AN14910.pdf).
[^10]: Lattice Semiconductor, [MIPI CSI-2 Virtual Channel Aggregation reference design](https://www.latticesemi.com/en/Products/DesignSoftwareAndIP/IntellectualProperty/ReferenceDesigns/ReferenceDesign04/Nto1) and [CrossLink-NX reference-design guide, FPGA-RD-02148](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ReferenceDesigns/1D/FPGA-RD-02148-1-2-CSI-2-VC-Aggregation-CrossLink-NX.ashx?document_id=52867).
[^11]: NXP, [i.MX 95 product page](https://www.nxp.com/products/i.MX95), [industrial data sheet](https://www.nxp.com/docs/en/data-sheet/IMX95IEC.pdf), and [camera porting guide](https://www.nxp.com/docs/en/user-guide/UG10215.pdf).
[^12]: NXP, [EdgeLock Secure Enclave and Crypto Accelerators](https://www.nxp.com/products/nxp-product-information/nxp-product-programs/edgelock-secure-enclave%3AEDGELOCK-SECURE-ENCLAVE) and [EdgeLock HSM API](https://www.nxp.com/docs/en/reference-manual/RM00284.pdf).
