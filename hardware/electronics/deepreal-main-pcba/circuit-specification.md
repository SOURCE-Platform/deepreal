# Main PCBA Circuit Specification v0.1

This file describes what must appear on each electrical sheet. It is a capture
contract, not a substitute for the checked EDA pages.

## Page 2 - USB-C, PD and protected VBUS

J1 carries USB 3.x data, USB 2, CC and power. Place D1 and D2 directly behind the
receptacle. SuperSpeed enters U12 after D1, then reaches U1 USB1. USB 2 reaches U1
through D2 and does not pass through U11. CC1/CC2 terminate at U11 using the exact
Infineon configuration network.

VBUS reaches D9 and U10 before any converter. U10 must provide reverse blocking,
controlled inrush, current limiting and current monitoring. Its fault/current status
is observable by trusted control. J1 shell connects to `CHASSIS_SHELL`, not directly
to the digital ground symbol; the final RC/capacitive join is selected by EMC review.

Acceptance: a wrong cable orientation cannot alter data function; a 5 V source boots
in service mode; motor power cannot turn on until the accepted contract permits it.

## Page 3 - 5 V system and 6 V motor converters

U8 converts `VBUS_PROTECTED` to `SYS_5V`. U9 converts it to `MOTOR_6V`. Each circuit
must copy the selected regulator's data-sheet topology with a calculated inductor,
feedback divider, bootstrap capacitor and input/output network. U9 enable is the AND
of power-good policy and a hardware-safe control state. It must be off at 5 V input.

Reserve thermal-via arrays under exposed pads and keep both hot loops away from U4,
U2/U3, J2/J3, Y1/Y2 and MK1. Converter values cannot be frozen until minimum input,
load transient, ripple and temperature calculations are attached.

## Page 4 - PF09/PF53 power tree

U5 generates system I/O, analog and DDR rails using the industrial LPDDR4X OTP
variant. U6 is the 15 A-class `VDD_SOC` converter and U7 the 8 A-class `VDD_ARM`
converter. Their enable, power-good and sequencing connections follow the i.MX95
reference design and PF09 OTP behavior; firmware is not the primary sequencer.

Every rail gets a named test point and rail-specific bulk/decoupling values. Exposed
pads, current return, remote-sense requirements and power-good pull domains must be
checked from the official package data before ERC waiver.

## Pages 5-8 - compute, memory, boot and storage

U1 is split into logical EDA units: power/ground, DDR, two CSI receivers, USB,
eMMC, M7/M33 control, clocks/reset/boot and unused pins. Every supply ball must map
to exactly one named rail and its local capacitor field. Unused pins receive an
explicit N/C decision from the hardware guide, never a blanket no-connect marker.

U4 sits adjacent to the correct DDR escape edge. `LPDDR4X_BUS` topology, grouping,
length limits and vias come from the NXP DDR tool. No connector, switch node, plane
split or unrelated via field enters that corridor.

U15 is the signed primary boot store. U16 contains only non-secret board identity,
revision and calibration selection. Recovery uses U1 USB serial download. Reserve
an unpopulated compact serial-NOR option only if the boot review finds a real need.

## Pages 9-10 - one camera bridge per drum

U2 and U3 use the same circuit block. Each accepts a two-lane RGB CSI stream and a
two-lane IR CSI stream, then emits a four-lane CSI stream to its dedicated U1 receiver.
Both devices have separate core regulation, bank decoupling, reset, PROGRAMN, INITN,
DONE and chip select. Shared configuration data/clock is allowed only if independent
fault containment and status remain possible.

Pin names are assigned only by a successful Lattice Radiant build targeting
LIFCL-17 csfBGA121. The build must prove hard/soft D-PHY allocation, all lane pins,
the 1.8 V bank plan, configuration pins, timing and resource margin.

## Pages 11-12 - optical-head interfaces

J2 and J3 use the allocation in `connector-allocation.csv`. U21/U22 independently
switch and monitor each 3.3 V feed. MIPI receives low-capacitance protection at the
stationary connector. Sideband signals use small series damping/filter footprints;
projector enable has a hardware pull-down on both sides of the flex.

An open flex, missing head, invalid head identity, open lens-integrity loop or head
fault must make projector emission impossible. The exact contact numbering remains
open until the flex orientation and stack-up are frozen.

## Page 13 - motors and absolute angle

U13/U14 are independent DRV8213 bridges. Each has local motor bulk capacitance,
charge-pump capacitor, hardware current regulation, IPROPI telemetry, nSTALL and
nFAULT. J4/J5 carry motor leads, encoder supply, encoder ground and quadrature A/B.

U18/U19 are stationary absolute-angle sensors at the drum axes. Magnets rotate with
the drums. They provide trusted position after power-up; motor quadrature is used for
velocity and incremental motion. Their programmable addresses and supply behavior
must be confirmed before sharing `BOARD_I2C`.

## Page 14 - audio, tamper and temperature

MK1 connects to U1 MICFIL with its supply filter and source damping. Its bottom port
has a copper/component keep-out and no motor or converter return current nearby.

SW1 is normally closed in the assembled state. Open-circuit wiring, connector loss
or enclosure opening must be distinguishable from normal closed state. U20 sits in
the i.MX95 thermal path and asserts an always-readable alert.

## Page 15 - test and manufacturing

Provide accessible test points for input power, every generated rail, ground, reset,
PD fault, both FPGA status groups, both head interlocks, both motor faults and the
recovery/debug interface. Test pads cannot violate DDR/MIPI/USB stubs. Document all
do-not-fit components and the reason for each option.

## Review gates before layout

The schematic is not layout-released until: vendor pin maps are audited; ERC has no
unexplained violations; the FPGA design compiles; the first DDR-tool pass exists;
the 51-position flex stack-up is reviewed; and power component values have attached
calculations. A preliminary placement study may run in parallel to expose space
conflicts, but it is not routing closure.
