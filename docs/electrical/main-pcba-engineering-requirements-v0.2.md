# DeepReal Main PCBA Engineering Requirements v0.2

| Field | Value |
| --- | --- |
| Status | Approved digital-design baseline |
| Immediate endpoint | Pre-fabrication engineering review draft and website visualization |
| Physical fabrication | Explicitly out of scope |
| Size policy | 90 x 28 mm preferred target; evidence may change it |
| Priority | Correctness and margin, then minimum practical size, then cost |

## Capture and data requirements

- Support face RGB, face IR, interaction RGB and interaction IR concurrently.
- Initial RGB mode is 1920 x 1080 at 50 fps, RAW10.
- Initial IR mode is 1600 x 1400 at 60 fps, RAW10.
- Retain at least 25% camera-link bandwidth margin after active-pixel payload.
- Give every stream a deterministic identity, frame sequence and error indication.
- Detect missing, duplicated and malformed frames before a capture is accepted.
- Keep full-rate frame hashing in protected i.MX95 memory unless a measured FPGA
  implementation proves a stronger and simpler trust boundary.
- Treat FPGA configuration as untrusted until authenticated and measured by the
  i.MX95 secure-boot path. Capture remains disabled until configuration succeeds.

## Power and operating requirements

- Accept USB-C 5 V, 9 V and 15 V Power Delivery contracts up to 3 A.
- Prefer 15 V / 3 A for unrestricted operation; treat 45 W as an input ceiling,
  not expected device dissipation.
- At 5 V / 3 A, allow boot, enumeration and service operation only; keep MOTOR_6V
  disabled and cap camera/compute activity.
- Enable the motor rail only after a contract of at least 9 V is confirmed.
- Support two 6 V motor channels and survive a 1.5 A combined short transient;
  firmware and hardware must prevent sustained stall.
- Power both optical heads, but intentionally enable no more than one projector
  pulse at a time in the baseline mode.
- Sequence processor, memory, FPGA and sensor rails according to their official
  manufacturer requirements. Unverified rail timing is a blocking issue.

## Safety, sensing and service requirements

- Projector emission defaults off after reset, brownout, open flex, configuration
  failure, overtemperature, driver fault or open lens-integrity loop.
- Firmware permission alone cannot complete the projector-enable path.
- Provide absolute position for each drum after startup, plus incremental motor
  encoder inputs for motion control.
- Provide board temperature, PDM microphone and enclosure-tamper inputs.
- Provide recovery, debug and production-test access without requiring a permanent
  product connector.
- No claim of eye safety, EMC compliance or physical validation is permitted in
  this digital-design phase.

## Mechanical and presentation requirements

- Use one reusable optical-head electrical design populated twice.
- Preserve the established enclosure and external USB-C opening by default.
- Align the receptacle, plug mating volume and cable bend to that opening before
  placement is approved.
- Respect mounting holes, shield boundary, connector-latch access, flex bend,
  microphone aperture, tamper actuator and processor thermal-contact keep-outs.
- Keep the preferred 90 x 28 x 1.6 mm board only if critical routing and mechanical
  integration pass without undocumented waivers.
- Generate all future presentation geometry from the canonical KiCad board.
- Public wording is: **DeepReal Main PCBA — engineering development visualization
  based on a pre-fabrication PCB layout.**

## Change-control triggers

Reopen affected gates after a change to any camera mode, sensor, processor, memory,
FPGA count/package, flex topology, power contract, board outline, stack-up,
connector location, shield or thermal interface.
