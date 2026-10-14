# Optical-module mounting and interface checkpoint, 13 October 2026

Status: **stage 1 audit delivered; mounting and electrical approvals remain open.**

This is the evidence-only phase of the
[optical-head roadmap](../system-architecture/device-integration-workplan-2026-10-09.md).
It does not approve the displayed supports, connectors, a common PCB or a
moving flex. No geometry, connector position, schematic, PCB or gate record
changes are part of this pass. Stage 2 has not started.

## Result and limit

The retained sources establish RGB variant envelopes, a standard-assembly
drawing's 30-pin definition and handling-bend note, the Mira220 CSP package
and pin definitions, the Belago1.2 reflow package and sense contacts, and the
FH26 catalog's conductors-down insertion direction.

They do **not** establish current standard/wide electrical interchangeability,
the selected RGB mating stack, approved rear bond sites, a complete IR
receiver, end-to-end 51-contact continuity or a qualified moving-flex
construction. The installed web supports remain proposals.

These inputs support only a conditional space-reservation study, if separately
authorized and labeled with its assumptions. They are insufficient for a
specified housed dynamic flex, mechanical interface freeze or fabrication.
Review the questions below before starting that study.

## Retained manufacturer evidence

Page numbers below are PDF pages. “Verified” means the retained document states
the fact, not that the ordered part or installed geometry has been qualified.
The standard assembly drawing is image-only; its table and notes were read
from enlarged page renders.

| ID | Archived source | Version and scope |
| --- | --- | --- |
| S1 | [RGB sensor-assembly product brief](../../references/components/datasheets/rpi-camera-module-3-sensor-assembly-product-brief.pdf) | July 2025, 7 pages; includes SA31VA30P standard and SA36VA30P wide visible variants. |
| S2 | [Standard sensor-assembly drawing](../../references/components/datasheets/rpi-camera-module-3-sensor-assembly-standard-datasheet.pdf) | TNBA1392, A0, revision 0 dated 20211210, 1 page; current applicability to the ordered variants needs confirmation. |
| S3 | [Standard Camera Module 3 mechanical drawing](../../references/components/datasheets/rpi-camera-module-3-standard-mechanical-drawing.pdf) | 1 page; complete camera PCB, not the separate sensor assembly's mounting interface. |
| S4 | [Mira220 datasheet](../../references/components/datasheets/ams-mira220-ds000642-v9.pdf) | DS000642 v9-00, 2025-Sep-26, 91 pages; Q65114A0087 / Mira220-2QM1WA monochrome CSP with AR glass and protective film, p6. |
| S5 | [Belago1.2 datasheet](../../references/components/datasheets/ams-belago1-2-datasheet.pdf) | DS001002 v1-00, 2025-Apr-22, 19 pages; Q65114A0198 component baseline. |
| S6 | [Hirose FH26 series catalog](../../references/components/datasheets/hirose-fh26-D49355-en.pdf) | Cover May 2017 revision 3; footer Aug.1.2026, 18 pages. The footer is not proof of a new technical revision. |

Exact archived-file SHA-256 values:

| Source | SHA-256 |
| --- | --- |
| S1 | `7627926f7f5ebf6aa19b7b8fe17b8720734541a1f26e762e4b5fe9139603d45c` |
| S2 | `92cb659c2f825326ad7de5f962aadc8342b82da92624c3a11ad18e623e50ac9c` |
| S3 | `bde27f5ab38dd46aa05713bbb17c6e8acc4cb1d48ff9109df511256f6fbc66ac` |
| S4 | `cc0048e8c5137516a9e47917112d23b11402253f6d95cef9b298d60c5e80efd5` |
| S5 | `f4f6149b8e7f8647316a653112103713fd90f84e81b346f52958becefcb91bf6` |
| S6 | `38e5c3c1278d7843146da4eb44c1a360f847659dd8d758143c5d55407148a40c` |

S1 pp2–3 identify reference schematic and BOM links. The existing
[source register](../../hardware/electronics/deepreal-main-pcba/source-evidence-register.csv)
also identifies the reference schematic URL. No local schematic/BOM archive,
wide-specific electrical drawing, DF37 mating drawing or AS1170 datasheet was
found in `references/`; those references were not reviewed in this pass.
An identified URL is not electrical approval.

## Mounting and mating findings

| Interface | Verified source fact | Display assumption or evidence still missing |
| --- | --- | --- |
| Face RGB, SA31VA30P | S1 pp4–5: 10.8 × 10.8 mm assembly, Ø5.75 mm lens, 6.98 mm depth, 66° × 41° field axes; focus 10 cm–infinity. | The displayed 0.6 mm sensor plate and retained lens-nose datum are not a manufacturer tolerance stack. S2 p1 instead shows a 0.4 ± 0.05 mm PCB and focus-dependent side-view dimensions of 5.97 ± 0.15 mm at infinity and 6.21 ± 0.15 mm at 10 cm. Reconcile datums and revisions, rather than substituting one height for another. |
| Interaction RGB, SA36VA30P | S1 pp4–5: same 10.8 × 10.8 mm outline, Ø6.95 mm lens, 8.3 mm depth, 102° × 67° field axes; focus 5 cm–infinity. Both selected visible variants include IR cut. | Equal outlines do not prove equal plug/pinout, autofocus circuit, rear surface or formed-tail geometry. S2 is not a wide-specific drawing. |
| RGB retention | S1 p6 says the product should be firmly secured or placed on a stable, flat, nonconductive surface, without contacting conductive items. | No source approves the four rear bond sites, saddle, anchor load path, adhesive or lens/VCM clamping. S3's full-camera PCB mounting holes cannot be transferred to the sensor assembly. |
| Short RGB tail | S2 p1: 8.9 ± 0.15 mm tail width, marked bending area, 0.13 ± 0.05 mm FPC+EMI thickness; technical requirement 3 permits 180° bending 20 times at R0.8 mm without failure. | The web centerline/terminal simplifications and radii of 1.565 mm face / 1.205 mm interaction do not prove a formed assembly. This handling-bend requirement does not qualify wide-tail equivalence or repeated drum motion. S6's long-flex requirements concern a different interface. |
| RGB plug to head J2 | S2 p1 names HLM-033M-3002-76 and marks pin 1 in its bottom view. | DF37NC-30DS-0.4V is only the electrical baseline. No retained drawing proves that it mates with HLM, or specifies the exact wide plug/socket, stack height and insertion/withdrawal clearance. The displayed 7.6 × 2.6 × 0.98 mm J2 is a keepout, not mating CAD. |
| IR receiver | S4 pp6, 81–84: 87-ball, 0.5 mm-pitch CSP. Table 41 nominal body is 5.4476 × 5.4448 × 0.7395 mm; maxima are 5.4726 × 5.4698 × 0.7995 mm. Underfill is recommended, strongly so on p81. | The register's “5.4 × 5.4” is shorthand, not a maximum envelope. This is a sensor package, not the displayed complete lens/body. Lens, filter, holder, optical/back-focus datum, assembly process and permitted support surfaces are unselected. Underfill guidance is not approval for bonding a receiver body to a rear seat. |
| Projector | S5 pp6, 9, 11–13: rear electrical contacts on a reflow-compatible nominal 4.2 × 3.6 × 3.325 mm package; Figure 8 defines a 2 × 2 mm optical aperture. Portrait field of illumination is typically 60° horizontal × 78° vertical at the 700 mA / 1 ms / 30 fps reference condition (pp7–9). Page 13's solder-mask/pad recommendation is a guide, not a firm specification. | The larger web body/two-opening depiction and rear bond seat are not the selected package/footprint. A direct-reflow component needs its electrical contact and thermal path defined; a bond across the contact face is not authorized by this drawing. Package/field axes still need an assembled coordinate drawing. |
| Projector handling and retention | S5 p15 identifies a ventilation hole and prohibits ultrasonic cleaning. Page 16, Figure 14 recommends pickup directly on the glass within the green area. | Pickup permission is not permission for a permanent structural clamp or adhesive on that glass. Allowed bond sites, vent keepout, support loads, thermal path and service method need manufacturer evidence. |
| Head J1 / main J2–J3 | S6 pp6–9: FH26W-51S-0.3SHW(97), 51 positions, 0.3 mm contact pitch; body 16.8 × 3.2 × 1.0 mm, recommended end 15.6 ± 0.05 mm wide and 0.2 ± 0.03 mm thick. Page 14 requires parallel insertion with exposed conductors facing down. | Catalog contact side is established. Physical pin-one direction, top/bottom placement, reflected footprints, cable-end orientation, paste/mask/retention and end-to-end continuity remain unapproved. The catalog subset is not the selected-part drawing/product specification. |
| FH26 strain relief | S6 pp17–18 require insertion space and securing flex under continuous load; do not bend close to the actuator and consult the FPC manufacturer for bend specifications. | No straight-entry reservation, strain-relief part, moving-section construction, dynamic bend limit or life test has been approved. Page 12's rear-copper caution concerns the connector-end construction, not a blanket ban on multilayer dynamic flex. Ten mating cycles are not drum-fatigue life. |

The existing
[web proposal record](../website-visualization-milestones.md#two-head-camera-support-and-common-board-proposal)
separates nominal contact checks from mounting approval. The two 47.3 × 12 ×
0.6 mm boards are proxy instances of one intended controlled design, not
native routed PCBs. Neither the displayed 0.1 mm bond layers nor sampled
clearance checks establish strength, retention, tolerances or optical function.

## Pinout and autofocus evidence

### Standard RGB drawing, not an approved socket netlist

S2 p1 gives the following numbered definition. Names are transcribed from the
source, including the unresolved combined label on pin 3.

| Source pins | Source definition |
| --- | --- |
| 1 / 2 | AFVDD2.8V / AF-GND |
| 3 | DOVDD1.8V+AVDD1.8V |
| 4, 11 / 10 | DVDD1.1V / AVDD2.8V |
| 5 / 7 / 9 | Sensor_PWDN / MCLK / AGND |
| 6, 8, 12, 15, 16, 19, 22, 25, 28 | DGND |
| 13 / 14 | MIPI-D3P / MIPI-D3N |
| 17 / 18 | MIPI-D2N / MIPI-D2P |
| 20 / 21 | MIPI-D1N / MIPI-D1P |
| 23 / 24 | MIPI-D0N / MIPI-D0P |
| 26 / 27 | MIPI-CLKN / MIPI-CLKP |
| 29 / 30 | SCL(1.8V) / SDA(1.8V) |

This preserves source polarity/numbering, not a top-view mating-socket map.
Confirm current-part applicability and derive the socket mapping from the
selected connector drawings. Do not assign these contacts to the 51-pin flex.
S2 exposes four data-pair labels; the intended two-lane RGB mode still needs
its reference circuit and configuration checked.

S2's module specification says DVDD 1.1 V, AVDD 2.8 V and DOVDD 1.8 V,
“PWDN Low effective” and “Reset NA.” Its pin-3 AVDD1.8V label therefore needs
manufacturer clarification. The
[head net registry](../../hardware/electronics/deepreal-optical-head/net-registry.csv)
uses `RGB_RESET_N`; the PWDN/reset function and default-state mapping must be
reconciled, not silently treated as the same signal.

S2 identifies an open-loop VCM, DW9800W driver and BL24SA64D-CS EEPROM;
starting current is unspecified. S1 pp2–3 describes autofocus/PDAF and
libcamera support. This does not establish the wide assembly's exact driver,
addresses, calibration, power-on behavior or DeepReal software support.
The existing 600 mA/50 mA reference rail figures are not measured total RGB
loads or an approved autofocus/startup budget.

### Mira220 selected CSP

S4 pp83–84, Table 42 defines these CSP balls, distinct from its bare-die pin
numbers. This subset is not a complete schematic/package audit:

| Signal | CSP ball(s) |
| --- | --- |
| CLK_IN / ARST_N | G10 / F8 |
| CCI_SDA / CCI_SCL | H8 / H7 |
| CCI_ADDR0 / CCI_ADDR1 | H4 / J8 |
| MIPI_CLK_P / MIPI_CLK_N | A8 / B8 |
| MIPI_D0_P / MIPI_D0_N | C7 / C8 |
| MIPI_D1_P / MIPI_D1_N | A9 / B9 |
| REQ_FRAME / REQ_EXP | G9 / G8 |
| ILLUM_TRIGGER / READ_TRIGGER | H5 / J10 |
| R_EXT / C_EXT | E8 / C6 |

Package top-view orientation is shown on S4 p82; image/pixel orientation and
lens inversion are shown on p45. Neither establishes the assembled receiver's
image axes. The proposed 180° RGB orientation also needs software/calibration
review; retaining horizontal/vertical field axes is not image-orientation proof.

S4 p9 specifies a 38.4 MHz reference, ±50 ppm, 45–55% duty and at most
200 ps cycle-to-cycle jitter. Page 21's 350 mA VDD25 source capability is a
startup minimum, not a maximum input draw. Page 12's 168 mW example is
typical at 30 fps, not a 60 fps/head maximum. The
[power/clock evidence](../../hardware/electronics/deepreal-optical-head/power-clock-evidence.json)
still leaves mode profiles, regulators, AF, pulse recharge, faults and
simultaneous-head transients open.

### Belago and the main-to-head connection

S5 p6 defines **1 Sense1, 2 Anode, 3 Sense2, 4 Cathode**. Its lens-integrity
loop is specified at 10.8–21 kΩ, 15 kΩ typical at room temperature (pp7–9); “continuity” alone
does not prove a valid sense state. The 700 mA / 1 ms / 30 fps optical
reference condition is not a safe-system operating approval or head-input
current. AS1170 Q65113A7129 remains a driver baseline without a reviewed
datasheet, pin mapping or implemented safety circuit in this pass.

Main J2 → face-head J1 and main J3 → interaction-head J1 remain the intended
connections. The
[earlier interface checkpoint](head-interface-checkpoint-2026-09-14.md)
records six candidate differential pairs per head and 51 contacts in 16
groups, without numbered continuity approval. Its 1.12 A/contact-allocation
screen is not a load budget or approved flex capacity.

The hardware permission requirement remains local valid power, an intact
qualified sense loop and no thermal/fault condition; absent, open or unknown
states must disable emission. S5 p17 says the component is not classified
under IEC 60825-1:2014. Qualified system safety review and hardware-default-off
evidence are still required before powered projector testing.

## Questions to close before later design work

These are evidence requests and engineering decisions, not sent vendor queries
or approved selections.

| Owner | Required answer or evidence |
| --- | --- |
| RGB manufacturer/supplier | Current released drawings for both exact assemblies; confirm S2 applicability, pin 3, PWDN/reset polarity, numbered plug/socket, compatible orderable mate, tail stack/bend/formed geometry and mounting/adhesive keepouts. Supply the reference schematic/BOM and wide AF driver, address, calibration and load/startup information. |
| IR optics/electrical design | Choose direct Mira220 CSP plus a controlled lens/filter/holder design, or an exact complete receiver assembly. Obtain package, optical datum/back focus, spectral performance, field/image orientation, thermal and mounting evidence for that choice. The current lens body cannot supply these facts. |
| Projector manufacturer and mechanical/electrical design | Confirm the exact component's released footprint, contact/heat path, vent and optical keepouts, permitted support surfaces and handling limits. Define how its reflow interface relates to the carrier; review lens-sense thresholds/faults and the driver/default-off circuit. |
| Connector manufacturer and PCB design | Archive the exact FH26 and RGB mating-pair drawings/product specifications. Derive physical pin-one, pad numbering and both cable-end/contact-side views; reserve latch, insertion, withdrawal and strain-relief access. |
| Flex supplier and electrical design | Propose construction for six differential pairs, returns, power and controls, with impedance/drop/current review, end stiffeners, free lengths, static/dynamic bend limits, minimum straight entry, temperature and intended cycle life. Do not use the RGB tail's 20 bends or FH26's ten mating cycles as moving-flex qualification. |
| Mechanical/optics design | Decide travel, hard stops, fixed/moving endpoints, retention loads, cable torque and reserved loop/service volume for one reference drum. The head circuit specification still says “160-degree motion”; the current studies sample face −45° to +45° and interaction 0° to 45°. Resolve that conflict explicitly before a fatigue/route requirement is frozen. |
| Electrical/system design | Close pin mapping, RGB lane/AF/control compatibility, Mira clocks/sequencing, mode/startup/recharge/fault budgets and hardware inhibition. Only then can one controlled common-board design and per-head configuration be approved. |

## Checks for this pass

- Six archived PDF hashes, byte sizes and page counts match the source inventory.
- All 25 local links/anchors across this checkpoint and the roadmap resolve.
  The RGB transcription covers all 30 source pins once; the 18 listed Mira
  signal-to-ball assignments match the extracted Table 42.
- All 167 files in the before-pass protected snapshot remain byte-identical.
  This covers the electronics, source model, installed review assets and viewer
  files. Both installed assembly GLBs retain SHA-256
  `fee55af0d30db02b063da30bad8aaa623ffc2aa04243b936750122384538d004`.
- Both repositories pass `git diff --check`. Prose scans find no banned phrases
  or structural flags. Soft readability/outline warnings are retained for the
  technical tables, repeated component terms and scope restrictions.
- Blender/viewer unit and browser checks were not rerun: this phase changes
  documentation only. Prior geometry results are linked evidence, not new tests.

## Checkpoint boundary

The governing
[main-PCBA design status](../../hardware/electronics/deepreal-main-pcba/design-status.json)
remains unchanged: `ENGINEERING_REBUILD_IN_PROGRESS`, fabrication and public
visual permission false. The closure fields in
[head-interface evidence](../../hardware/electronics/deepreal-main-pcba/head-interface-evidence.json)
remain open. No source inspection here passes a schematic, PCB, safety or
mechanical gate.

This phase adds this checkpoint and updates the roadmap status only. Temporary
extractions/renders are working evidence, not new manufacturer documents.
Do not start stage 2, alter housed-flex geometry or change connector positions
without the next bounded authorization. No order, fabrication, commit, push,
publication or deployment is included.
