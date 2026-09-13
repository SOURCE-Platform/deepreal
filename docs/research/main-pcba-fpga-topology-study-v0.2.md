# DeepReal Camera / FPGA Topology Study v0.2

| Field | Value |
| --- | --- |
| Status | Provisional analysis; Radiant compile required |
| Requirement | Four simultaneous streams from two identical RGB/IR heads |
| Processor baseline | NXP i.MX95 with two CSI-2 receiver interfaces |
| Decision state | Zero-FPGA rejected; one versus two FPGAs remains open |

## Bandwidth baseline

| Stream | Active payload | With 25% margin |
| --- | ---: | ---: |
| One 1920 x 1080 x 50 fps RAW10 RGB | 1.037 Gbit/s | 1.296 Gbit/s |
| One 1600 x 1400 x 60 fps RAW10 IR | 1.344 Gbit/s | 1.680 Gbit/s |
| One RGB/IR head | 2.381 Gbit/s | 2.976 Gbit/s |
| Both heads | 4.762 Gbit/s | 5.952 Gbit/s |

The margin is an engineering allowance, not a substitute for the final CSI-2 packet,
blanking and clock-mode calculation.

## Option A — no FPGA

Four independent sensor transmitters cannot be passively wired onto the i.MX95's
two physical camera receivers. Virtual channels help a receiver distinguish streams
that already share one legal transmitter, but do not electrically combine unrelated
sensor D-PHY outputs. Time-multiplexing would violate the simultaneous-stream
requirement.

**Disposition:** rejected unless a selected sensor/head device performs documented
aggregation before the dynamic flex.

## Option B — one CrossLink-NX

A single device could aggregate all four streams and deliver one four-lane output at
about 1.49 Gbit/s per lane after the present margin. Lattice publishes an N-to-1
virtual-channel aggregation design and CrossLink-NX supports hard and soft D-PHY
interfaces. This does not prove that the LIFCL-17 csfBGA121 has enough legal pins,
soft receivers, logic, clocking and timing margin for DeepReal.

Advantages:

- one programmable device, bitstream and configuration circuit;
- lower major-package count;
- potential use of one processor camera receiver.

Risks:

- four sensor inputs converge on one board location;
- longer MIPI routes from at least one drum;
- package/I/O growth may erase the component-area saving;
- concentrated power/thermal load and one failure domain;
- a one-output topology reduces independent receiver isolation.

## Option C — two CrossLink-NX devices

Each device handles one RGB/IR head and drives one dedicated i.MX95 receiver at
about 0.75 Gbit/s per output lane after the present margin.

Advantages:

- short connector-to-FPGA routes and a natural one-head-per-receiver partition;
- lower per-device bandwidth and I/O concentration;
- independent reset, status and failure containment.

Risks:

- duplicated FPGA power, configuration and decoupling support;
- two packages and bitstreams;
- still requires at least one soft D-PHY path per device unless a different lane
  allocation is proven legal.

## Compile matrix required for decision

| Candidate | Required proof | Current state |
| --- | --- | --- |
| One LIFCL-17 csfBGA121 | Four RX plus one/two TX legal pins, timing and margin | BLOCKED |
| One larger CrossLink-NX | Same proof plus package/route/power comparison | BLOCKED |
| Two LIFCL-17 csfBGA121 | Per-head two RX plus one TX compile and timing | BLOCKED |

For each viable build, archive the source project, exact device/package/speed grade,
pin report, timing report, utilization, generated clocks and power estimate. Require
20% implementation-resource margin and 25% link-bandwidth margin.

## Provisional recommendation

Retain two LIFCL-17 devices only as the routing baseline because it offers the clearest
physical partition. Do not freeze or publicly claim that topology until the compile
matrix closes. Choose one FPGA if it passes all hard requirements with margin and its
package plus routing is simpler; otherwise choose two.

## Official sources

- NXP i.MX95 product and camera interface: https://www.nxp.com/products/i.MX95
- Lattice CrossLink-NX family and pin resources: https://www.latticesemi.com/CrossLinkNX
- Lattice virtual-channel aggregation reference: https://www.latticesemi.com/Products/DesignSoftwareAndIP/IntellectualProperty/ReferenceDesigns/ReferenceDesign04/Nto1
- Lattice Radiant download and platform requirements: https://www.latticesemi.com/Radiant

## Toolchain execution blocker

Lattice's current Radiant 2026.1 release supports Windows 11 and selected 64-bit
Linux distributions; it does not list macOS. CrossLink-NX device use is available
under Lattice's free license, but the compile must run on a supported Windows/Linux
host with the required account/license setup. The present macOS workstation cannot
produce the required legal pin, timing, resource, or power evidence natively.
