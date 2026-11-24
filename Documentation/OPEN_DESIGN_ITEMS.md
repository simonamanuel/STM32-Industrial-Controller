# Open design items and limitations

This is a CAD-stage design portfolio, not a product qualification record. The following items were identified in previous design review and are **not claimed as fixed by the Revision D files**.

## 1. Q1/Q2 low-voltage gate-drive margin

The STM32 uses approximately 3.3 V GPIO drive and the output devices are IRLML0060. The previously reviewed published guaranteed on-resistance values were specified at gate-drive conditions above 3.3 V. Without a guaranteed operating-point check or an appropriate driver, it is not defensible to claim the full 1.5 A output rating has been validated. The optional UCC27524A driver proposal is **not included** in the original Revision D layout.

## 2. Mechanical outline and courtyard verification

The Phoenix Contact connector pads were revised in Revision D, but accurate PCB-plane housing outlines, courtyards, and assembly clearances have not been independently established. The prior independent audit raised courtyard-size concerns.

## 3. U2 exposed-pad thermal-via process

The six thermal vias at U2's exposed pad are present in the CAD, but assembly via filling/plugging/tenting and stencil-paste treatment have not been qualified. This matters to assembly reliability if physical fabrication is ever pursued.

## 4. High-current-path thermal and voltage-drop review

Some `VIN_FUSED` traces in the reviewed design were narrower than long adjacent power runs. A full path-based thermal and voltage-drop analysis for the intended continuous actuator current has not been completed or documented as verified.

## 5. Firmware status

Revision D is a KiCad-focused archive and includes no verified build, executable firmware image, or tests. Do not describe this as a programmed, working embedded controller.

## Portfolio position

It is appropriate to present Revision D as a **designed, documented, CAD-rule-checked mixed-signal PCB project with disclosed open engineering review items**. It is not appropriate to call it physically verified, safety-certified, production-ready, or electrically validated at full rated actuator loads.
