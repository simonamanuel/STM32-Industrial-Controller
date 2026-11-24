# Minimal steps to publish the CAD-only portfolio

## Essential

- [ ] Use the **original Revision D** project for screenshots, with **no partially wired U6 added**.
- [ ] In KiCad 10 Schematic Editor, run **Inspect → Electrical Rules Checker** on this exact saved design and record the actual results.
- [ ] In PCB Editor, run **Inspect → Design Rules Checker**, enable refill and schematic-parity check, record actual results.
- [ ] Export one clean schematic view; export or capture one full-board top copper/layout view.
- [ ] Open **View → 3D Viewer** in the PCB Editor; capture top and angled views that reflect the actual project.
- [ ] Add those three or four exported PNG/SVG images to `Images/` and link them from the README.
- [ ] Review the disclaimer in `OPEN_DESIGN_ITEMS.md`; retain it when publishing.
- [ ] Publish source files and documentation to GitHub, with no claims of fabrication or testing.

## Optional, not prerequisites for the CAD portfolio

- [ ] Add a design-calculation appendix with explicit input/load assumptions.
- [ ] Add representative KiCad net and component review notes.
- [ ] Develop separate demonstrative STM32 firmware, with build and tests labelled accurately.
- [ ] Independently resolve gate drive, connector courtyards, thermal-via process, and continuous-current reviews if pursuing manufacture later.

## Not necessary for this portfolio milestone

Ordering boards, assembly, paste stencil qualification, hardware bring-up, load-temperature measurement, and product certification are not required to publish a clearly-labelled CAD-only design study.
