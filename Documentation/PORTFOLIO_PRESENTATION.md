
# Engineering Portfolio Overview

## Project Description

A four-layer STM32F103C8T6 industrial controller PCB
developed in KiCad, incorporating mixed-signal sensor
interfaces, industrial communications, regulated power
distribution, and DC actuator-control circuitry.

## Engineering Scope

- STM32F103C8T6 embedded hardware architecture.
- Four-layer PCB schematic capture and layout.
- 5 V buck conversion and 3.3 V LDO regulation.
- Dual 0–10 V analog input signal conditioning.
- Reverse-polarity and transient-voltage protection.
- RS-485, I2C, SPI, UART, and SWD interfaces.
- Low-side MOSFET switching and inductive-load protection.
- Ground and power plane implementation.
- Electrical and PCB design-rule verification.

## Engineering Deliverables

- Native KiCad schematic and PCB files.
- Gerber and drill files.
- Bill of materials with manufacturer part numbers.
- Component placement files.
- IPC netlist.
- PCB fabrication documentation.
- Electrical Rules Check (ERC) report.
- Design Rules Check (DRC) report.

## Design Verification

The Revision D reports document:

- Zero reported ERC errors and warnings,
  with four check categories excluded.
- Zero reported DRC violations.
- Zero unconnected pads.
- Zero reported footprint errors.

The project remains at the CAD design stage.
Automated rule checks do not establish physical
electrical performance or production readiness.

## Future Development

- Resolve outstanding MOSFET gate-drive limitations.
- Complete electrical and thermal design reviews.
- Fabricate and assemble the PCB.
- Perform hardware bring-up and peripheral testing.
- Develop and validate embedded firmware.
- Characterize analog acquisition accuracy.
- Verify actuator switching and current-handling capability.
