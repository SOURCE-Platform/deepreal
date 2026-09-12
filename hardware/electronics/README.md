# DeepReal Electronics Design Source

This directory is the controlled handoff between the system architecture, future
EDA capture, PCB layout and Blender packaging model.

## Designs

- `deepreal-main-pcba/` - stationary 90 x 28 mm compute, power, camera bridge,
  USB and motor-control board.
- `deepreal-optical-head/` - one rotating RGB/IR/projector carrier design. The
  identical design is populated twice, once for each drum.

## What exists at v0.1

The files define the sheet hierarchy, component/reference-designator ownership,
named power and signal nets, drum-connector allocation, circuit intent and the
vendor pin maps that must be imported before an ERC-clean EDA schematic can be
claimed. They are deliberately tool-neutral because KiCad is not installed in the
current workspace and several authoritative BGA pin maps are not stored locally.

This is electrical design source, but it is **not yet** a checked KiCad schematic,
PCB layout, routed netlist or manufacturing package. `TBD_PINMAP` is an explicit
gate, never a guessed connection.

## Release rule

Blender geometry may use the component packages and support-population counts in
this directory. Copper traces shown before an EDA router produces them must be
labelled `ILLUSTRATIVE ROUTING - NOT NETLIST DERIVED`.
