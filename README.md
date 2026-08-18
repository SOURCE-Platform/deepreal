# DeepReal

**Open-source trusted sensing for private AI.** The first SOURCE reference device.

> **Status: architecture + hardware design in progress.** DeepReal is in active architecture, hardware-design, and prototype-planning work. Nothing here is production-ready, and no sensor configuration is final.

Project page: https://sourceovcourse.com/deepreal

---

## What DeepReal is

DeepReal is an open-source desktop sensing device and reference architecture designed to give AI systems authenticated, privacy-preserving observations of the physical world around a computer. It combines multimodal sensing, hardware-rooted device trust, encrypted transport, protected host-side processing, and verifiable outputs — designed to remain inspectable and user-controlled.

It is the first reference implementation of **SOURCE**, a broader open architecture for connecting trusted devices and physical-world observations to digital and AI systems with stronger guarantees about origin, integrity, and privacy.

## Two sensing systems

DeepReal is not one general-purpose camera. It has two sensing systems, each aimed at a specific physical domain:

- **Face / presence sensing** — short-range RGB + structured-light depth. Captures the person at the computer (RGB imagery, facial geometry, depth) to support presence, liveness, and future identity-related research.
- **Interaction sensing** — wide-angle RGB aimed at the workspace. Observes hands, fingers on the keyboard, and mouse interaction to build stronger evidence that a real human produced a given computer action.

## Trust architecture (intended)

Two sensing paths converge into one trusted pipeline:

Physical world → face/presence + interaction sensing → **device trust boundary** (secure boot, hardware root of trust, secure element, device credentials, sequence-aware capture) → authenticated + encrypted device–host channel → **host trust boundary** (Trusted Execution Environment, protected processing, local AI, attestation/proof logic) → **verifiable output** (attestations, selective disclosure, provenance).

Later layers (attestation formats, provenance) are part of the design, not yet implemented.

## Hardware configurations (under evaluation)

DeepReal is being developed through several reference configurations that trade cost against assurance. These are engineering configurations, not products for sale, and carry no prices here.

| Config | Face sensing | Interaction sensing | Research question |
|---|---|---|---|
| A — Cost optimized (baseline) | RGB + depth | Rolling-shutter RGB | Can a cost-optimized system reliably observe physical interaction? |
| B — Motion optimized | RGB + depth | Global-shutter RGB | Does cleaner fast-motion capture materially improve verification? |
| C — Full 3D interaction | RGB + depth | RGB + depth | Does 3D interaction geometry give substantially stronger evidence? |
| C+ — Full 3D + motion | RGB + depth | Global shutter + depth | What is achievable with maximum interaction evidence? |

## Prototype → production

Today's off-the-shelf modules are experimental instruments, not permanent dependencies:

Off-the-shelf modules → validate requirements → measure what actually helps → custom open reference hardware.

## Candidate components

Parts are candidates under evaluation, **not** final production specifications:

- **Face / depth module — Orbbec Astra Mini S Pro** *(prototype candidate).* Its short-range operating envelope suits someone sitting at a laptop. Final facial-identity performance must still be tested.
- **Secure-boot-capable MCU** *(under evaluation)*
- **Discrete secure element / hardware root of trust** *(under evaluation)*
- **Common architecture:** USB-C power and data, one microphone, device cryptographic identity, common PCB / interface architecture, authenticated communication with the host.

## Privacy by architecture

The design asks not only what *can* be sensed but what actually *needs* to be sensed — minimizing hardware sensing capability alongside retention and disclosure. Intended properties, under development: local / host-side processing, cloud inference not required, encrypted device–host link, data minimization, selective disclosure, user-controlled retention, and attestations that can expose less information than raw sensor streams. These are design goals, not finished guarantees.

## Roadmap

Discrete statuses — no completion percentages.

1. System architecture — **Current**
2. Mechanical + sensing design — **Current**
3. Sensor configuration evaluation — **Next**
4. Prototype electronics — **Next**
5. Trusted sensor pipeline — **Planned**
6. Protected host processing — **Planned**
7. Production reference architecture — **Planned**
8. SOURCE reference implementation — **Planned**

## Relationship to SOURCE

DeepReal provides the physical sensing endpoint; SOURCE is the broader open protocol and trust architecture (attestation + provenance) that applications and AI agents build on. The goal is an open architecture others can implement — future SOURCE-compatible hardware need not be built by the DeepReal project.

## Repository layout

This repository is being set up. Planned structure, added as material lands:

```
deepreal/
├── docs/         # architecture, threat model, sensor evaluation notes
├── hardware/     # CAD, enclosure, sensor carrier, PCB (schematics / layout)
├── firmware/     # device firmware / secure-boot MCU
├── renders/      # product and exploded renders
└── README.md
```

## Contributing

DeepReal is developed in the open. We are interested in collaboration around open hardware, embedded security, confidential computing, privacy-preserving AI, cryptography, and trustworthy sensing.

Contact: adam@sourceovcourse.com

## License

Open-source licensing under final review.
