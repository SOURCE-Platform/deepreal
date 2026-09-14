# DeepReal Optical Head Electrical Capture v0.1

| Field | Value |
| --- | --- |
| Design | One reusable rotating optical-head carrier |
| Product quantity | 2 identical assemblies |
| Contains | RGB sensor assembly, IR sensor, projector, driver, local rails and safety interlock |
| Status | Capture source; optical, flex, safety and exact regulator selections open |

The two drums do not use two independently designed head PCBs. H1 and H2 are the
same controlled design populated twice, with identity/configuration selecting face
or interaction use. This reduces layout, firmware and test divergence.

This is the intended partition, not an existing completed pair of PCBs. No native
KiCad head schematic or board has been captured yet. Main-board J2 goes to the
face head's J1; J3 goes to the interaction head's J1. See the
[two-drum interface checkpoint](../../../docs/electrical/head-interface-checkpoint-2026-09-14.md)
for connector dimensions, placement conflicts, power and dynamic-flex blockers.

## Electrical partition

The head receives filtered/switched 3.3 V, MCLKs, control and triggers over the
51-contact dynamic flex. RGB and IR each return two-lane CSI-2. The AS1170,
Belago1.2 and projector pulse capacitor stay local so the 700 mA-class pulse loop
does not traverse the rotating flex.

## Safety rule

`PROJECTOR_ENABLE` is necessary but not sufficient for emission. The driver must
also see a valid local lens-integrity loop, valid local power and no thermal/fault
condition. Removal of power, an open flex or an open Sense1/Sense2 loop defaults to
off. This is a design intent pending the required system-level eye-safety assessment.

## Closure order

1. Freeze the RGB assembly and Mira220 orientation from the optical baseline.
2. Select and calculate the RGB and IR local regulators.
3. Capture the manufacturer reference circuits and full sensor pin maps.
4. Freeze the 51-contact flex numbering and dynamic-flex stack-up.
5. Run ERC, power-up sequencing review and projector single-fault review.
6. In a separately authorized future fabrication program, prototype one head and
   measure rails, timing, thermal behavior and optical output. No fabrication is
   authorized by this digital-review phase.
