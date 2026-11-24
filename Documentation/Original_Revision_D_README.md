# STM32 Industrial Sensor, Data Acquisition and Actuator Controller

Revision D is a four-layer engineering demonstration board built around the STM32F103C8T6. It accepts a protected 9-30 V supply, creates 5 V and 3.3 V rails, measures two 0-10 V sensor inputs, exposes I2C/SPI/UART/SWD, provides a protected half-duplex RS-485 port, and switches two low-side DC actuator channels.

> **Verification status:** the Revision D native schematic passes ERC with 0 violations. The PCB passes the full KiCad check with 0 DRC violations, 0 unconnected items, and 0 schematic-parity issues. Firmware and physical hardware validation are separate from this KiCad-focused revision. This remains a design-review package, **not a production release**, until independent review and physical validation are complete.

## Key design limits

- Logic-only input: 9-30 VDC steady state.
- Actuator operation: nominal 12 V, 9-18 V allowed, 1.5 A per channel, 3 A combined.
- Analog inputs: 0-10 V, approximately 0-3.115 V at the ADC.
- Auxiliary outputs: 5 V at 250 mA and 3.3 V at 25 mA maximum, subject to thermal verification.
- RS-485: 3.3 V THVD1450, 115200 bit/s default, selectable 120 ohm termination and 680 ohm bias pair.
- This is not a safety controller and has no industrial certification.

## Repository map

- `KiCad/`: native editable KiCad 10 project and schematic, legacy import source, project-local symbol/footprint libraries, four-layer board, and custom rules.
- `Firmware/STM32_Project/`: register-level C11 firmware, protocol tests, and ARM compile output.
- `Manufacturing/`: BOM, placement, fabrication notes, Gerbers, and drill outputs.
- `Documentation/`: requirements, calculations, design report, verification plan, pin map, and actual check reports.
- `Images/`: schematic, PCB, and 3D exports generated from the design.

## Firmware protocol

Frames are `A5 | command | length | payload | CRC-8/ATM`. Commands read status (0x01), read an ADC channel (0x02), set an actuator output (0x10), and clear a fault (0x20). A five-second command timeout forces active outputs off. Hardware gate pull-downs and early GPIO initialization keep both MOSFETs off during reset and startup.

## Reproducing checks

Open `KiCad/STM32_Industrial_Controller.kicad_pro` in KiCad 10. The native `.kicad_sch` was produced in the KiCad 10.0.8 desktop Schematic Editor. The included ERC and DRC reports record zero violations; the DRC also records zero unconnected items and zero schematic-parity issues. From the firmware folder, `make host-test` runs the protocol tests. `arm-none-eabi-gcc` is needed for the complete linked firmware image; the supplied environment only supported verified Cortex-M3 object compilation with Clang.

## Primary component references

- [STM32F103C8 and STM32F103 documentation](https://www.st.com/en/microcontrollers-microprocessors/stm32f103c8.html)
- [LMR36510 65 V, 1 A buck regulator](https://www.ti.com/product/LMR36510)
- [TLV755P 500 mA LDO](https://www.ti.com/product/TLV755P)
- [THVD1450 RS-485 transceiver](https://www.ti.com/product/THVD1450)

## License and use

The project is intended for education, portfolio review, and engineering discussion. A qualified engineer must independently review the schematic, land patterns, current-carrying copper, thermal design, and protection strategy, then execute the verification plan before field use.
