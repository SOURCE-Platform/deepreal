# DeepReal Main PCBA - Schematic Entry Specification v0.1

> **Superseded architecture note (13 September 2026):** Use this document as source
> evidence, not as permission to freeze two FPGAs or begin pin-driven layout. The
> authoritative requirements are in `main-pcba-engineering-requirements-v0.2.md`;
> FPGA count remains open in the v0.2 topology study until compile evidence exists.

| Field | Value |
| --- | --- |
| Date | 12 September 2026 |
| Status | Pre-schematic engineering baseline; not manufacturing-ready |
| Main board target | 90 x 28 x 1.6 mm, two-sided assembly |
| Populated envelope | Approximately 90 x 28 x 15 mm including shield/thermal stack |
| Purpose | Prevent the schematic and 3D model from being built on generic blocks |

> **Capture status (12 September 2026):** The tool-neutral schematic source package
> now exists at `../../hardware/electronics/`. It defines the 15 main-board sheets,
> the reusable optical-head design, reference ownership, named nets, connector groups
> and pin-map gates. A checked EDA schematic/netlist still requires vendor symbol
> import, FPGA pin compilation, the first DDR-tool pass and ERC.

## Outcome

The 90 x 28 mm main board remains plausible enough to continue, but it is not yet
proven. The architecture now has a credible schematic entry point and three material
changes from the current visual model:

1. Use two 6 x 6 mm LIFCL-17 camera bridges, one per drum, rather than one generic
   9.5 mm FPGA.
2. Use one 51-position high-speed flex connector per drum as the compact baseline,
   with the current four 22-position camera connectors retained as a lower-risk SI
   fallback.
3. Put each AS1170 projector driver, its inductor, pulse capacitor, local camera
   regulators and interlock circuit on a small rotating head carrier. These are
   internal product electronics, not external development boards. Shortening the
   projector pulse loop is more credible than sending the switched 700 mA pulse
   through the rotating flex.

The i.MX 95 and LPDDR packages must not touch. Their bodies need an assembly gap,
while the DDR routing must remain short. The final gap and relative orientation come
from BGA escape and DDR routing, not from visual preference.

### First board-space sanity check

- The raw projected area of all current main-board package and connector bodies in
  Mechanical BOM v0.2 is approximately 1,044 mm2. That is 41.4% of one 90 x 28 mm
  board face, before support passives, courtyards, routing and keep-outs.
- The board has two assembly faces, so package body area alone does not force a size
  increase. The controlling constraints are DDR escape, six MIPI corridors, USB,
  power-loop copper, flex access and the thermal contact zone.
- Two 51-position drum connectors occupy 31.2 mm of body length in total versus
  approximately 52 mm for the older four-connector concept.
- A 15 mm i.MX body, a 1.5 mm assembly gap and the 10 mm LPDDR body consume 26.5 mm
  along the long axis while staying about 15 mm deep. That geometry fits on paper;
  fan-out and length matching still decide whether it fits electrically.

This is enough evidence to keep 90 x 28 mm as the working target, but not enough to
claim that routing will close at that size.

## 1. Locked schematic baseline

| Function | Baseline part | Package / body | Confidence | Status |
| --- | --- | --- | ---: | --- |
| Application processor | NXP MIMX9596CVTXNAC | 548-ball FC-PBGA, 15 x 15 mm, 0.5 mm pitch | 85% | Exact industrial six-core 15 mm SKU |
| LPDDR4X | Micron MT53E1G32D2FW-046 AAT:B | 200-ball, 10 x 14.5 mm | 65% | 4 GB baseline; NXP DDR validation required |
| eMMC | Micron MTFC32GBCAQTC-AAT | 153-ball, 11.5 x 13 mm | 85% | 32 GB, eMMC 5.1 |
| Camera bridges | 2 x Lattice LIFCL-17, csfBGA121 | 6 x 6 mm, 0.5 mm pitch | 70% | Exact speed grade/order suffix after Radiant compile |
| Main PMIC | NXP MPF0900AVNA2ES | HVQFN56, 8 x 8 mm | 90% | Industrial QM OTP for i.MX 95 + LPDDR4X |
| SoC regulator | NXP MPF5302BVNAAEP | H-FC-PQFN24, 15 A class | 85% | VDD_SOC baseline |
| CPU regulator | NXP MPF5301BVNABEP | H-FC-PQFN24, 8 A class | 85% | VDD_ARM baseline |
| Protected 5 V buck | TI TPS56637RPAR | VQFN-HR10, 3 x 3 mm | 80% | 15 V to system rail; validate 5 V fallback dropout |
| Motor 6 V buck | TI TPS56637RPAR | VQFN-HR10, 3 x 3 mm | 75% | Enabled only when USB contract is at least 9 V |
| Input eFuse | TI TPS259472LRPWR | WQFN10, 2 x 2 mm | 80% | 23 V, reverse blocking, current monitoring |
| USB-PD sink | Infineon CYPD3177-24LQXQ | QFN24, 4 x 4 mm | 90% | 15 V / 3 A preferred contract |
| USB orientation mux | TI HD3SS3212IRKSR | VQFN20, 2.5 x 4.5 mm | 90% | Industrial USB SuperSpeed mux |
| Motor drivers | 2 x TI DRV8213RTER | WQFN16, 3 x 3 mm | 90% | Current sense/regulation and hardware stall detection |
| Motor | 2 x Pololu item 5137 | 6 V micro gearmotor | 90% electrical | 0.67 A theoretical stall each |
| Absolute drum angle | 2 x AS5600L-AWLM | WLCSP15, 2.07 x 2.63 x 0.6 mm | 70% | Programmable I2C addresses; supply-transition check required |
| Shared sensor clock buffer | TI LMK1C1104DQFR | WSON8, 2 x 2 mm | 75% | Four low-skew LVCMOS outputs |
| Board EEPROM | Microchip AT24C64D-MAHM-T | UDFN8, 2 x 3 mm | 90% | Non-secret board revision/calibration selection |
| Main board temperature | TI TMP117AIDRVR | WSON6, 2 x 2 mm | 90% | Place near i.MX thermal path |
| Digital microphone | TDK MMICT3902-00-012 | LGA, 3.5 x 2.65 mm | 90% | PDM, bottom port |
| Case tamper | Omron D3SK-B1R | Surface-mount NC switch, 3 x 3.5 x 0.9 mm | 70% | Exact lever direction still enclosure-dependent |
| Drum connector baseline | 2 x Hirose FH26W-51S-0.3SHW(97) | 51 pos, 15.6 x 3.2 x 1.0 mm | 65% | Dynamic-flex and SI validation required |
| RGB sensors | 2 x Raspberry Pi SA31VA30P | 10.8 x 10.8 mm sensor assembly | 70% | Located on head carrier |
| IR sensors | 2 x ams OSRAM Mira220 Q65114A0087 | CSP, 5.4 x 5.4 x 0.74 mm | 80% | Located on head carrier |
| Projectors | 2 x ams OSRAM Belago1.2 Q65114A0198 | 4.2 x 3.6 x 3.325 mm | 75% | Located on head carrier |
| Projector drivers | 2 x ams OSRAM AS1170 Q65113A7129 | WLCSP13, 2.25 x 1.5 x 0.6 mm | 75% | Located on head carrier |

Exact orderable suffixes above are a purchasing baseline, not blanket approval for
production. Availability, lifecycle and alternates must be checked again at design
release.

## 2. Board partition

```text
USB-C
  |-- CC1/CC2 --> CYPD3177 PD sink
  |-- VBUS ----> eFuse ----> protected VBUS
  |                         |-- 5 V system buck --> PF09 + two PF53 --> i.MX95/DDR
  |                         |                    --> local FPGA rails
  |                         |                    --> two optical-head flexes
  |                         `-- 6 V motor buck --> two DRV8213 --> stationary motors
  `-- USB 3.x --> ESD --> orientation mux --> i.MX95 USB1

Main PCBA                 Face head carrier       Interaction head carrier
i.MX95 + memory           IMX708 assembly         IMX708 assembly
2 x LIFCL-17              Mira220                 Mira220
USB and power             AS1170 + Belago         AS1170 + Belago
motor drivers             local sensor rails      local sensor rails
clock/reset/control       local interlock         local interlock
```

The absolute drum-angle sensors should be stationary at the drum axes with their
magnets on the rotating shafts. They therefore do not require a rotating flex. The
motor's incremental encoder can be used for velocity and commutation feedback, but it
does not replace the absolute angle sensor required for trusted pose after power-up.
AS5600L is preferred over the fixed-address AS5600 so both axes can share a controlled
bus if desired. Reconfirm the manufacturer/order code before release because this
sensor family is in a supplier-ownership transition.

## 3. Power contract and operating modes

| USB input | Allowed behavior |
| --- | --- |
| 15 V / 3 A | Full design mode; 45 W input ceiling, not 45 W dissipation |
| 9 V / 3 A | Normal or moderately derated mode after measured power validation |
| 5 V / 3 A | Boot, enumerate and service mode; motor 6 V rail disabled; capture duty and compute capped |
| Less than 5 V / 3 A equivalent | Do not begin a capture session; report insufficient source power |

The CYPD3177 advertises and negotiates sink voltages; it does not replace the DC/DC
converters. Firmware must read or infer the accepted contract before enabling the
motor and projector state machines.

The current rail budget is maintained in
`main-pcba-rail-budget-v0.1.csv`. Important design limits are:

- 5 V system converter: 6 A continuous class, with thermal design based on measured
  sustained load rather than the nameplate current.
- 6 V motor converter: at least 1.5 A short-duration combined load and 2 A design
  capacity; both motors may not remain stalled.
- Each RGB head needs a 1.1 V rail capable of 600 mA plus 1.8 V and 2.8 V rails.
- Each Mira220 head needs sequenced 2.5 V, 1.35 V and 1.8 V rails; the 2.5 V rail
  must tolerate the documented 350 mA startup interval.
- Only one projector is intentionally active at a time. Local energy storage must
  keep its pulse out of the camera and SoC rails.

## 4. Camera topology and lane budget

Per drum, the initial operating point is:

| Stream | Mode | Active payload | FPGA input |
| --- | --- | ---: | --- |
| RGB | 1920 x 1080, 50 fps, RAW10 | 1.04 Gbit/s | 2-lane CSI-2 hard D-PHY |
| IR | 1600 x 1400, 60 fps, RAW10 | 1.34 Gbit/s | 2-lane CSI-2 soft D-PHY |
| Aggregated output | Both streams + 25% allowance | 2.98 Gbit/s | 4-lane CSI-2 hard TX |

Each LIFCL-17 assigns fixed virtual-channel IDs, validates packet structure, adds a
frame counter and reports stream errors. Face output goes only to i.MX CSI-0;
interaction output goes only to i.MX CSI-1. Full-rate frame hashing remains in
protected i.MX memory unless an FPGA benchmark later proves a stronger boundary.

The exact FPGA pin map is not considered closed until the same two-input/one-output
project compiles and meets timing for the 121-ball package. The published resource
count is encouraging but is not a pinout proof.

## 5. Drum flex definition

The 51-pin connector is allocated by signal group rather than final pin number until
the flex vendor confirms contact orientation and stack-up:

| Group | Contacts | Notes |
| --- | ---: | --- |
| Head 3.3 V feed | 8 | Parallel contacts; nominal 1.6 A before system derating |
| Dedicated power returns | 8 | In addition to high-speed return contacts |
| RGB CSI clock/data | 6 signal + 3 return | Clock plus two data lanes |
| IR CSI clock/data | 6 signal + 3 return | Clock plus two data lanes |
| RGB MCLK + return | 2 | 24 MHz from clock buffer |
| IR MCLK + return | 2 | 24 MHz from clock buffer |
| Shared I2C/CCI | 2 | Confirm non-conflicting addresses; add mux only if required |
| RGB reset and IR reset | 2 | Independent trusted control |
| IR trigger and illumination trigger | 2 | Exposure/projector synchronization |
| Projector enable and fault | 2 | Hardware default-off |
| Interlock status | 1 | Must fail safe on open flex or open lens loop |
| Head temperature alert | 1 | Local sensor/driver thermal protection |
| Head identity | 1 | Local carrier revision/calibration identification |
| Shield / reserved | 2 | Assigned after SI and flex review |
| **Total** | **51** | Includes two uncommitted contacts before SI review |

This compact interface is mechanically attractive but electrically aggressive. The
fallback remains two separate camera flexes plus a power/control flex per drum if the
51-conductor dynamic flex cannot meet impedance, crosstalk or fatigue requirements.

## 6. Clock, reset and boot plan

- i.MX95 uses its manufacturer-required 24 MHz system reference and the required
  power-on reset network. Add a 32.768 kHz RTC reference only if holdover behavior
  justifies it.
- A separate 24 MHz oscillator drives LMK1C1104. Its four outputs feed RGB and IR
  sensor clocks. The exact oscillator is chosen during schematic capture after the
  sensor input-swing and jitter limits are checked together.
- PF09 and both PF53 devices own the i.MX power sequence. Do not create an unrelated
  discrete sequence.
- Each FPGA gets independent PROGRAMN, INITN, DONE, reset and chip select. i.MX loads
  authenticated bitstreams after boot; camera capture remains disabled until both
  configurations are measured and accepted.
- Primary boot is signed software from eMMC. Recovery uses i.MX USB serial download.
  A 6 x 8 mm optional Octal-SPI footprint may be reserved, but no NOR device is
  required in the first schematic merely to make the board look complete.
- Board identity/calibration EEPROM is separate from device signing keys. Device keys
  remain in EdgeLock; the EEPROM stores non-secret board revision and calibration
  selection data.

## 7. USB-C data path

- USB1 is the recovery and product data port.
- Route SuperSpeed pairs through external ESD protection and the industrial
  HD3SS3212 orientation mux. Keep the connector, ESD and mux in one short corridor.
- Route USB 2 D+/D- with its own low-capacitance protection. Do not route USB data
  through the CYPD3177; that part controls Type-C/PD power behavior.
- Baseline protection population is one TPD4EUSB30-class four-channel array for USB
  SuperSpeed, one TPD2EUSB30A-class device for USB 2 and three TPD4E05U06 arrays at
  each drum connector for the twelve MIPI conductors. Final capacitance and placement
  require an eye-diagram review; these parts cannot be decorative blocks.
- CYPD3177 HPI/I2C and fault outputs connect to trusted control so accepted source
  power becomes part of the capture enable policy.
- The USB-C shell needs a chassis/EMI strategy distinct from digital ground, joined
  only through the final EMC network.

## 8. Physical layout rules before aesthetic routing

- Working assumption: 10-layer HDI, controlled-impedance stack, laser microvias and
  via-in-pad where the 0.5 mm BGAs require it. Final stack-up comes from the chosen
  fabricator.
- LPDDR sits in the i.MX DDR escape direction with no connector or switching node in
  the DDR corridor.
- One FPGA sits near each drum connector and its associated i.MX CSI receiver.
- Keep inductors, motor current loops and projector power entry away from MIPI, DDR,
  microphone port and clock routing.
- Put decoupling on both sides where allowed, directly at BGA power fields. The 3D
  model must show the capacitor fields, inductors, crystals, ESD arrays, test pads and
  courtyards rather than only major IC bodies.
- Reserve a rear-housing thermal contact over the i.MX95 through a compliant pad and
  copper spreader. Do not place tall components in that compression zone.
- Keep all dynamic flex bend volumes and connector actuator access outside the EMI-can
  wall. The can is not allowed to trap serviceable flexes.

## 9. Schematic page plan

1. Cover, revision, variants and design constraints
2. USB-C receptacle, ESD, PD negotiation and protected VBUS
3. 5 V system and 6 V motor conversion
4. PF09/PF53 power tree and sequence
5. i.MX95 power and decoupling units
6. i.MX95 boot straps, reset, clocks, debug and recovery
7. LPDDR4X
8. eMMC and board EEPROM
9. Face LIFCL-17, CSI input/output, config and sideband
10. Interaction LIFCL-17, CSI input/output, config and sideband
11. Face drum flex interface and protection
12. Interaction drum flex interface and protection
13. Motor drivers, absolute encoders and connectors
14. Microphone, tamper, temperature and miscellaneous I/O
15. Test points, manufacturing options and no-fit parts

## 10. Gates that cannot be closed by documentation alone

| Gate | Required evidence | What it can change |
| --- | --- | --- |
| DDR | NXP DDR tool settings, length rules and memory bring-up | LPDDR part, orientation, board layers |
| FPGA | Radiant compile, legal pin assignment and timing closure in csfBGA121 | FPGA package/count and connector placement |
| Dynamic flex | Vendor stack-up, impedance model and 160-degree cycle test | One 51-pin vs multiple flexes per drum |
| Optical head | RGB/IR/projector bench with real lens and baseline | Sensor choice, aperture spacing, head PCB size |
| Eye safety | IEC 60825-1 system assessment including single faults | Projector current, interlock and public claims |
| Motor | Measured torque, inrush, stall, settling and acoustic data | Gear ratio, driver limit, 6 V rail size |
| USB source | Tests on target laptops/docks at 5/9/15 V contracts | Full single-cable claim and derating policy |
| Thermal | Sealed-enclosure sustained workload test | SoC power cap, shield/spreader and enclosure vents |
| SI/PI | DDR/MIPI/USB simulation and power-rail impedance review | Stack-up, spacing, passives and board size |
| Security | Protected-DMA and fault-injection demonstration | Hash boundary and marketing language |

## 11. Entry decision

The preliminary schematic may now begin using this document as its baseline. It must
not be called final, and PCB routing should not begin until at least the DDR rules,
FPGA pin compile and drum-flex topology have passed their first engineering reviews.
The 3D model can be updated immediately to show the corrected packages, carrier-board
partition and realistic support-component density, while clearly labeling unverified
routes as illustrative rather than copper derived from a netlist.

## Primary manufacturer sources

- [NXP i.MX 95 industrial data sheet](https://www.nxp.com/docs/en/data-sheet/IMX95IEC.pdf)
- [NXP PF09 data sheet](https://www.nxp.com/docs/en/data-sheet/PF09.pdf)
- [NXP PF53 product and ordering table](https://www.nxp.com/products/PF53)
- [Lattice CrossLink-NX family](https://www.latticesemi.com/CrossLinkNX)
- [Raspberry Pi Camera Module 3 reference schematic](https://pip-assets.raspberrypi.com/categories/1207-design-files/documents/RP-008969-SD-3-Raspberry%20Pi%20Camera%20Module%203%20Reference%20Schematic.pdf)
- [ams OSRAM Mira220](https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-mira220)
- [ams OSRAM Belago1.2](https://ams-osram.com/products/lasers/ir-lasers-vcsel/ams-belago1-2-dot-pattern-illuminator-vcsel)
- [ams OSRAM AS1170](https://ams-osram.com/products/drivers/led-drivers/ams-as1170-2-channel-led-and-vcsel-driver-ic)
- [TI DRV8213](https://www.ti.com/product/DRV8213)
- [TI high-speed ESD array](https://www.ti.com/product/TPD4E05U06)
- [TI TMP117](https://www.ti.com/product/TMP117)
- [AS5600L data sheet](https://look.ams-osram.com/m/657fca3b775890b7/original/AS5600L-DS000545.pdf)
- [Pololu item 5137](https://www.pololu.com/product/5137/specs)
- [Infineon CYPD3177](https://www.infineon.com/part/CYPD3177-24LQXQ)
- [Hirose FH26 series connector catalog](https://www.hirose.com/en/product/document?clcode=CL0580-2413-0-60&documentid=D49355_en&documenttype=Catalog&lang=en&series=FH26)
