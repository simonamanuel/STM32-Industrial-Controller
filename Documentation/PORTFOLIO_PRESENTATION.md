# Portfolio presentation and resume wording

## GitHub short description

> AI-assisted four-layer STM32 mixed-signal controller PCB design in KiCad 10, with analog sensor inputs, RS-485, 5 V/3.3 V regulation, protected power distribution, and dual MOSFET output stages. CAD-stage design only; includes native files, supplied ERC/DRC reports, BOM, and disclosed unresolved design-review items.

## Short portfolio paragraph

> Created and reviewed a four-layer KiCad design study for a low-voltage STM32 industrial controller with two conditioned analog inputs, RS-485 communications, low-side actuator channels, and regulated power distribution. Organized the editable schematic/PCB, BOM, and fabrication outputs, and used design reviews to identify limitations that automated rule checks alone do not verify. The project was AI-assisted and has not been fabricated or physically tested.

## Resume bullet — use only if it accurately reflects your work

> Developed and reviewed an AI-assisted four-layer STM32 controller PCB in KiCad, integrating analog sensor front ends, RS-485, regulated power supplies, and MOSFET outputs; evaluated schematic/PCB rule-check results and documented electrical design risks.

A more conservative option if your primary contribution was audit/review rather than design authoring:

> Reviewed and iterated an AI-generated four-layer STM32 controller design in KiCad, investigating component pinouts, power-routing constraints, protection circuitry, and ERC/DRC evidence; documented unresolved hardware limitations.

## What to avoid claiming

- Do not say you **fabricated, assembled, commissioned, or bench-validated** this board.
- Do not claim output-current ratings, thermal margins, or gate-drive performance were verified.
- Do not claim embedded C firmware is implemented/tested as part of the Revision D ZIP.
- Do not imply CAD checker results are equivalent to actual physical validation.
- Be able to explain the design decisions and identify your actual contribution, including AI assistance when relevant.

## Interview prompts to practise

1. Explain the power path from input protection to the 5 V and 3.3 V rails.
2. Explain the input scaling/protection for two 0–10 V channels.
3. Explain half-duplex RS-485 and selectable termination/bias.
4. Explain why the low-side inductive output needs flyback suppression.
5. Explain the difference between an ERC/DRC pass and design validation.
6. Explain the MOSFET 3.3 V gate-drive limitation and proposed improvements.
