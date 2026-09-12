# Optical Head Circuit Specification v0.1

## Input and rail sequence

J1 receives eight parallel 3.3 V contacts and eight dedicated power returns. Input
bulk capacitance is sized against flex inductance and the main-board load-switch
stability limit. U2/U3/U4 reproduce the published RGB reference rail arrangement.
U5/U6/U7 generate the Mira220 rails and enforce its manufacturer sequence, including
the 2.5 V startup interval. Sensors remain in reset until all rails are valid.

The final schematic must show every supply pin, bypass capacitor, regulator feedback
network, enable pull and discharge path. A single generic `CAMERA_POWER` arrow is not
acceptable.

## RGB channel

S1 is the 10.8 mm IMX708-based sensor assembly, not the complete Raspberry Pi camera
module PCB. J2 and the support circuit follow the published Camera Module 3 reference
design. Its two-lane CSI, MCLK, CCI/control, reset/power-down and autofocus support
are retained. Assembly availability and software enablement remain EVT risks.

## IR channel

S2 is Mira220 Q65114A0087. Capture all sensor pins from the current manufacturer data,
including its 12 kilohm 0.1% bias resistor, internal-regulator capacitors, three input
rails, external trigger and illumination-trigger output. MIPI lane polarity cannot
be swapped casually; any swap must be supported by both sensor and FPGA configuration.

## Projector and fail-safe control

U1, L1, P1 and the pulse capacitors form one compact switching island. Use the AS1170
reference topology and calculate current programming for the selected Belago pulse,
initially bounded by the 700 mA, 1 ms, 30 fps reference point. Only one head is
intentionally allowed to emit at a time.

U9 implements the local hardware permission chain:

```text
main enable AND valid head power AND closed lens loop AND no local fault
    -> AS1170 hardware enable
```

Every absent/open/unknown input resolves to disabled. The schematic must expose a
fault signal to the main board and provide physical measurement points for pulse
current and the Sense1/Sense2 loop. This circuit is still subject to IEC 60825-1
system assessment; it is not a certification claim.

## Layout-derived schematic requirements

- Keep P1/U1/L1/pulse capacitors together and away from both MIPI lane groups.
- Give S1 and S2 uninterrupted ground reference and separate local rail filtering.
- Keep switching inductors outside each sensor's optical and thermal keep-out.
- Put J1 where the 160-degree motion does not fold the flex over tall components.
- Keep all components below the drum's verified radial/axial envelopes.
- Expose small test pads without creating MIPI stubs.

## Prototype acceptance

One assembled head must demonstrate power sequencing, both live CSI streams, trigger
timing, a forced-open lens loop, flex removal, thermal inhibit and measured optical
pulse behavior before the design is cloned into both drums for EVT.
