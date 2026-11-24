# Design summary — Revision D

## Intended system

A four-layer STM32F103C8T6-based design-stage controller for two analog channels, common embedded communication interfaces, RS-485, and two low-side switched actuators. Project requirements below are **design targets in the provided files**, not validated performance results.

## Subsystems

| Subsystem | Components documented in supplied BOM | Intended function |
| --- | --- | --- |
| Controller | U1 STM32F103C8T6 | MCU, ADC, GPIO and serial peripherals |
| Power input | F1, D2, U5, Q3, F4 | Input fuse, transient suppression and ideal-diode-style reverse-polarity scheme |
| 5 V and 3.3 V rails | U2 LMR36510ADDAR, U3 TLV75533PDBVR | Buck conversion then 3.3 V LDO |
| Analog | J6/J7, R14–R19, C20/C21, D3/D4 | 0–10 V input scaling and protection |
| Communications | U4 THVD1450DR, D5 SM712, J2–J5/J8 | RS-485 and MCU headers |
| Outputs | F2/F3, Q1/Q2 IRLML0060, R27–R30, D6/D7, J9/J10 | Two fused 1.5 A intended low-side output channels |

## Selected design constraints (from original README and fabrication notes)

- Logic input: 9–30 V DC, with actuator supply limited to the separately stated 9–18 V operating window.
- Two actuator channels: nominal 12 V and 1.5 A each, 3 A combined intended maximum. Performance is not bench-confirmed.
- External copper layers and inner copper layers: nominal 35 μm each.
- Four-layer stack: top signal/components, internal GND reference, internal protected-supply plane, bottom signal.
- Board size: 218.0 × 146.0 mm, 1.60 mm nominal thickness.
- Fabrication notes: minimum 0.15 mm conductor, 0.10 mm spacing; these are design-rule settings rather than thermal current-capacity proof.

## Design decisions to discuss in an interview

1. Why the MCU uses 3.3 V logic and why a separate 5 V regulator is required.
2. How a 0–10 V sensor signal is scaled and protected before the ADC.
3. What an RS-485 transceiver and optional termination/bias networks do.
4. Why inductive outputs use external flyback diodes and MOSFET pull-downs.
5. Why copper widths, return paths, heat dissipation, and footprint geometry require independent engineering review beyond ERC/DRC.
6. Why output MOSFET gate drive at 3.3 V remains a disclosed design gap in this revision.

## Claims not established

No physical boards, measurements, thermal tests, communication tests, actuator switching tests, embedded firmware execution, safety certification or independent fabrication authorization are evidenced by the Revision D ZIP.
