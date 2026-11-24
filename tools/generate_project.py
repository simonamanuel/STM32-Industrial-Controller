#!/usr/bin/env python3
"""Generate the controller's source design, manufacturing tables, and local libraries.

The schematic and PCB are emitted from the same component/net manifest.  The legacy
schematic is intentionally used only as an import source for KiCad 10, which embeds
the project-local symbols when saved in the native .kicad_sch format.
"""
from __future__ import annotations

import csv
import heapq
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "KiCad"
LIB = KICAD / "Libraries"
MFG = ROOT / "Manufacturing"
DOC = ROOT / "Documentation"


@dataclass
class Part:
    ref: str
    value: str
    mpn: str
    footprint: str
    pins: Dict[str, str]
    x: float
    y: float
    desc: str
    dnp: bool = False
    fields: Dict[str, str] = field(default_factory=dict)


P: List[Part] = []


def add(ref, value, mpn, fp, pins, x, y, desc, dnp=False):
    P.append(Part(ref, value, mpn, fp, {str(k): v for k, v in pins.items()}, x, y, desc, dnp))


# Power entry and conversion.  The input power path uses a 5 A time-delay fuse
# followed by an LM74700-Q1 ideal-diode controller and a 60 V N-channel FET.
# The controller's 20 mV regulation and the FET's milliohm RDS(on) avoid the
# roughly 1.5 W loss of the former series SS54 at the 3 A actuator load.
add("J1", "9-30V DC IN", "Phoenix 1935161", "TERM2", {1:"VIN_RAW",2:"GND"}, 12,15,"5.00 mm input terminal")
add("F1", "5A Slo-Blo", "Littelfuse 0454005.MR", "FUSE_NANO2", {1:"VIN_RAW",2:"VIN_FUSED"}, 23,15,"125 V time-delay main input fuse")
add("Q3", "CSD18540Q5B", "CSD18540Q5B", "SON5X6_8", {1:"VIN_FUSED",2:"IDEAL_GATE",3:"VIN_PROT"}, 33,15,"60 V 2.2 mOhm ideal-diode MOSFET")
add("U5", "LM74700-Q1", "LM74700QDBVRQ1", "SOT23_6", {1:"IDEAL_VCAP",2:"GND",3:"VIN_FUSED",4:"VIN_PROT",5:"IDEAL_GATE",6:"VIN_FUSED"}, 30,22,"65 V ideal-diode/reverse-polarity controller")
add("C23", "100nF 25V", "GRM188R71E104KA01D", "C0603", {1:"IDEAL_VCAP",2:"VIN_FUSED"}, 24,22,"Ideal-diode charge-pump capacitor")
add("C24", "100nF 100V", "CGA3E2X7R2A104K080AA", "C0603", {1:"VIN_FUSED",2:"GND"}, 31,27,"Ideal-diode input bypass")
add("D2", "SMBJ33CA", "SMBJ33CA-13-F", "SMB", {1:"GND",2:"VIN_FUSED"}, 27,25,"Bidirectional input transient suppressor")
add("F4", "1A Fast", "Littelfuse 0451001.MRL", "FUSE_NANO2", {1:"VIN_PROT",2:"VIN_LOGIC"}, 44,15,"125 V logic-branch fuse")
add("C1", "2.2uF 100V X7R", "GRM32ER72A225KA35L", "C1210", {1:"VIN_LOGIC",2:"GND"}, 44,12,"Buck input capacitor")
add("C2", "220nF 100V X7R", "CGA4J3X7S2A224K125AB", "C0603", {1:"VIN_LOGIC",2:"GND"}, 48,12,"High-frequency input bypass")
add("C3", "47uF 50V", "EEE-FK1H470P", "CAP_SMD_63", {1:"VIN_LOGIC",2:"GND"}, 40,24,"Logic-branch input bulk capacitor")
add("U2", "LMR36510ADDAR", "LMR36510ADDAR", "HSOIC8_EP", {1:"GND",2:"VIN_LOGIC",3:"VIN_LOGIC",4:"PG_5V",5:"FB_5V",6:"VCC_BUCK",7:"BOOT",8:"SW",9:"GND"}, 58,17,"65 V, 1 A synchronous buck")
add("C4", "1uF 10V", "GRM188R71A105KA61D", "C0603", {1:"VCC_BUCK",2:"GND"}, 54,28,"Buck VCC bypass")
add("C5", "100nF 25V", "GRM188R71E104KA01D", "C0603", {1:"BOOT",2:"SW"}, 63,28,"Bootstrap capacitor")
add("L1", "22uH 2.1A", "SRN6045TA-220M", "IND_6X6", {1:"SW",2:"+5V"}, 73,17,"Buck inductor")
add("C6", "22uF 10V X7R", "GRM32ER71A226KE20L", "C1210", {1:"+5V",2:"GND"}, 81,9,"5 V output capacitor")
add("C7", "22uF 10V X7R", "GRM32ER71A226KE20L", "C1210", {1:"+5V",2:"GND"}, 85,12,"5 V output capacitor")
add("R1", "100k 1%", "RC0603FR-07100KL", "R0603", {1:"+5V",2:"FB_5V"}, 79,24,"Buck feedback top")
add("R2", "24.9k 1%", "RC0603FR-0724K9L", "R0603", {1:"FB_5V",2:"GND"}, 85,24,"Buck feedback bottom")
add("R3", "10k", "RC0603FR-0710KL", "R0603", {1:"+5V",2:"PG_5V"}, 90,17,"Power-good pull-up")
add("U3", "TLV75533PDBVR", "TLV75533PDBVR", "SOT23_5", {1:"+5V",2:"GND",3:"+5V",4:"NC_U3",5:"+3V3"}, 98,17,"500 mA 3.3 V LDO")
add("C8", "1uF 10V", "GRM188R71A105KA61D", "C0603", {1:"+5V",2:"GND"}, 95,27,"LDO input capacitor")
add("C9", "1uF 10V", "GRM188R71A105KA61D", "C0603", {1:"+3V3",2:"GND"}, 103,27,"LDO output capacitor")
add("R4", "1k", "RC0603FR-071KL", "R0603", {1:"+3V3",2:"LED_PWR_A"}, 111,14,"Power LED resistor")
add("LED1", "GREEN", "LTST-C190KGKT", "LED0603", {1:"LED_PWR_A",2:"GND"}, 117,14,"3.3 V power indicator")
add("J11", "5V OUT", "M20-9990246", "HDR2", {1:"+5V",2:"GND"}, 123,11,"Limited auxiliary 5 V header")
add("J12", "3V3 OUT", "M20-9990246", "HDR2", {1:"+3V3",2:"GND"}, 132,11,"Limited auxiliary 3.3 V header")

# MCU, clocks, reset, boot, and debug.
mcu = {1:"VBAT",2:"STATUS_LED",3:"NC_PC14",4:"NC_PC15",5:"OSC_IN",6:"OSC_OUT",7:"NRST",8:"GND",9:"VDDA",10:"ADC_IN1",11:"ADC_IN2",12:"UART_TX",13:"UART_RX",14:"SPI_NSS",15:"SPI_SCK",16:"SPI_MISO",17:"SPI_MOSI",18:"ACT1_CTL",19:"RS485_DIR",20:"BOOT1",21:"NC_PB10",22:"NC_PB11",23:"GND",24:"+3V3",25:"NC_PB12",26:"NC_PB13",27:"NC_PB14",28:"NC_PB15",29:"NC_PA8",30:"RS485_TX",31:"RS485_RX",32:"NC_PA11",33:"NC_PA12",34:"SWDIO",35:"GND",36:"+3V3",37:"SWCLK",38:"NC_PA15",39:"NC_PB3",40:"NC_PB4",41:"NC_PB5",42:"I2C_SCL",43:"I2C_SDA",44:"BOOT0",45:"ACT2_CTL",46:"FAULT_LED",47:"GND",48:"+3V3"}
add("U1", "STM32F103C8T6", "STM32F103C8T6", "LQFP48", mcu, 68,48,"72 MHz Arm Cortex-M3 MCU")
for i,(net,x,y) in enumerate([("+3V3",54,39),("+3V3",57,39),("+3V3",60,39),("+3V3",63,39)],10):
    add(f"C{i}", "100nF", "GRM188R71C104KA01D", "C0603", {1:net,2:"GND"}, x,y,"MCU local decoupling")
add("C14", "4.7uF", "GRM188R71A475KE15D", "C0603", {1:"+3V3",2:"GND"}, 51,39,"MCU bulk decoupling")
add("FB1", "600R@100MHz", "BLM18AG601SN1D", "R0603", {1:"+3V3",2:"VDDA"}, 50,49,"Analog supply ferrite")
add("C15", "100nF", "GRM188R71C104KA01D", "C0603", {1:"VDDA",2:"GND"}, 47,53,"VDDA bypass")
add("C16", "1uF", "GRM188R71A105KA61D", "C0603", {1:"VDDA",2:"GND"}, 47,58,"VDDA reservoir")
add("R5", "0R", "RC0603JR-070RL", "R0603", {1:"+3V3",2:"VBAT"}, 50,63,"VBAT supply link")
add("Y1", "8MHz 18pF", "NX3225GD-8MHZ-STD-CRA-3", "XTAL4", {1:"OSC_IN",2:"GND",3:"OSC_OUT",4:"GND"}, 51,70,"Main crystal")
add("C17", "18pF C0G", "GRM1885C1H180JA01D", "C0603", {1:"OSC_IN",2:"GND"}, 44,69,"Crystal load")
add("C18", "18pF C0G", "GRM1885C1H180JA01D", "C0603", {1:"OSC_OUT",2:"GND"}, 44,74,"Crystal load")
add("R6", "1M", "RC0603FR-071ML", "R0603", {1:"OSC_IN",2:"OSC_OUT"}, 52,76,"Crystal bias resistor")
add("R7", "10k", "RC0603FR-0710KL", "R0603", {1:"+3V3",2:"NRST"}, 82,40,"Reset pull-up")
add("C19", "100nF", "GRM188R71C104KA01D", "C0603", {1:"NRST",2:"GND"}, 87,40,"Reset filter")
add("SW1", "RESET", "B3U-1000P", "BUTTON", {1:"NRST",2:"GND"}, 92,40,"Reset pushbutton")
add("R8", "100k", "RC0603FR-07100KL", "R0603", {1:"BOOT0",2:"GND"}, 84,46,"BOOT0 default low")
add("JP1", "BOOT0", "M20-9990246", "HDR2", {1:"BOOT0",2:"+3V3"}, 91,47,"Bootloader selection jumper")
add("R9", "100k", "RC0603FR-07100KL", "R0603", {1:"BOOT1",2:"GND"}, 84,51,"BOOT1 default low")
add("J2", "SWD", "M20-9980546", "HDR5", {1:"+3V3",2:"SWDIO",3:"GND",4:"SWCLK",5:"NRST"}, 101,45,"SWD programming header")
add("R10", "1k", "RC0603FR-071KL", "R0603", {1:"+3V3",2:"LED_STATUS_A"}, 83,58,"Status LED resistor")
add("LED2", "BLUE", "LTST-C190TBKT", "LED0603", {1:"LED_STATUS_A",2:"STATUS_LED"}, 90,58,"Active-low status LED")
add("R11", "1k", "RC0603FR-071KL", "R0603", {1:"+3V3",2:"LED_FAULT_A"}, 83,63,"Fault LED resistor")
add("LED3", "RED", "LTST-C190KRKT", "LED0603", {1:"LED_FAULT_A",2:"FAULT_LED"}, 90,63,"Active-low fault LED")

# External digital buses.
add("J3", "I2C 3V3", "M20-9990446", "HDR4", {1:"+3V3",2:"GND",3:"I2C_SCL",4:"I2C_SDA"}, 111,39,"I2C connector")
add("R12", "4.7k", "RC0603FR-074K7L", "R0603", {1:"+3V3",2:"I2C_SCL"}, 105,36,"I2C pull-up")
add("R13", "4.7k", "RC0603FR-074K7L", "R0603", {1:"+3V3",2:"I2C_SDA"}, 107,33,"I2C pull-up")
add("J4", "SPI 3V3", "M20-9980646", "HDR6", {1:"+3V3",2:"GND",3:"SPI_NSS",4:"SPI_SCK",5:"SPI_MISO",6:"SPI_MOSI"}, 122,42,"SPI connector")
add("J5", "UART 3V3", "M20-9990446", "HDR4", {1:"+3V3",2:"GND",3:"UART_TX",4:"UART_RX"}, 133,40,"UART connector")

# Analog inputs: 0-10 V, divided and RC filtered, with rail clamps.
for ch,x in [(1,13),(2,29)]:
    add(f"J{5+ch}", f"AIN{ch} 0-10V", "Phoenix 1935161", "TERM2", {1:f"AIN{ch}_RAW",2:"GND"}, x,55,"5.00 mm analog input terminal")
    add(f"R{13+ch}", "22.1k 0.1%", "ERA-3AEB2212V", "R0603", {1:f"AIN{ch}_RAW",2:f"AIN{ch}_DIV"}, x,63,"Analog divider top")
    add(f"R{15+ch}", "10k 0.1%", "ERA-3AEB103V", "R0603", {1:f"AIN{ch}_DIV",2:"GND"}, x+4,68,"Analog divider bottom")
    add(f"R{17+ch}", "1k 1%", "RC0603FR-071KL", "R0603", {1:f"AIN{ch}_DIV",2:f"ADC_IN{ch}"}, x+7,63,"ADC isolation/filter resistor")
    add(f"C{19+ch}", "10nF C0G", "GRM1885C1H103JA01D", "C0603", {1:f"ADC_IN{ch}",2:"GND"}, x+9,69,"ADC anti-alias filter")
    # BAT54S is a series pair with pin 3 as the common junction.  The signal
    # therefore belongs on pin 3, between the GND-side diode on pin 1 and the
    # +3V3-side diode on pin 2.
    add(f"D{2+ch}", "BAT54S", "BAT54S-7-F", "SOT23", {1:"GND",2:"+3V3",3:f"ADC_IN{ch}"}, x+11,63,"ADC Schottky rail clamp")
    add(f"TP{ch}", f"ADC{ch}", "5015", "TP", {1:f"ADC_IN{ch}"}, x+12,75,"ADC test point")

# RS-485.
add("U4", "THVD1450DR", "THVD1450DR", "SOIC8", {1:"RS485_RX",2:"RS485_nRE",3:"RS485_DIR",4:"RS485_TX",5:"GND",6:"RS485_A_INT",7:"RS485_B_INT",8:"+3V3"}, 105,69,"3.3 V half-duplex RS-485")
add("R20", "0R", "RC0603JR-070RL", "R0603", {1:"RS485_DIR",2:"RS485_nRE"}, 98,75,"Couples driver and receiver direction")
add("R21", "100k", "RC0603FR-07100KL", "R0603", {1:"RS485_DIR",2:"GND"}, 99,80,"RS-485 reset-safe receive default")
add("C22", "100nF", "GRM188R71C104KA01D", "C0603", {1:"+3V3",2:"GND"}, 110,76,"RS-485 decoupling")
add("R22", "680R", "RC0603FR-07680RL", "R0603", {1:"+3V3",2:"BIAS_A"}, 116,65,"Optional failsafe pull-up")
add("JP2", "BIAS A", "M20-9990246", "HDR2", {1:"BIAS_A",2:"RS485_A_INT"}, 120,65,"Failsafe bias enable")
add("R23", "680R", "RC0603FR-07680RL", "R0603", {1:"BIAS_B",2:"GND"}, 116,80,"Optional failsafe pull-down")
add("JP3", "BIAS B", "M20-9990246", "HDR2", {1:"RS485_B_INT",2:"BIAS_B"}, 120,80,"Failsafe bias enable")
add("R24", "120R", "RC0603FR-07120RL", "R0603", {1:"TERM_A",2:"RS485_B"}, 126,70,"RS-485 termination")
add("JP4", "TERM", "M20-9990246", "HDR2", {1:"RS485_A",2:"TERM_A"}, 126,66,"Termination enable")
add("R25", "10R", "RC0603FR-0710RL", "R0603", {1:"RS485_A_INT",2:"RS485_A"}, 115,71,"Bus damping")
add("R26", "10R", "RC0603FR-0710RL", "R0603", {1:"RS485_B_INT",2:"RS485_B"}, 115,75,"Bus damping")
add("D5", "SM712", "SM712-02HTG", "SOT23", {1:"RS485_A",2:"RS485_B",3:"GND"}, 130,76,"RS-485 asymmetric TVS")
add("J8", "RS-485", "Phoenix 1935174", "TERM3", {1:"RS485_A",2:"RS485_B",3:"GND"}, 136,70,"RS-485 terminal")

# Actuator outputs, nominal 12 V, 1.5 A/channel.
for ch,x in [(1,65),(2,82)]:
    add(f"F{1+ch}", "2.5A Slo-Blo", "Littelfuse 045402.5MR", "FUSE_NANO2", {1:"VIN_PROT",2:f"ACT{ch}_VP"}, x,82,"125 V time-delay actuator fuse")
    add(f"J{8+ch}", f"ACT{ch}", "Phoenix 1935161", "TERM2", {1:f"ACT{ch}_VP",2:f"ACT{ch}_SW"}, x+2,87,"5.00 mm actuator terminal")
    # IRLML0060 is a 60 V, 2.7 A logic-level MOSFET in SOT-23 with the same
    # 1=gate, 2=source, 3=drain terminal mapping as the original device.
    add(f"Q{ch}", "IRLML0060", "IRLML0060TRPBF", "SOT23", {1:f"ACT{ch}_G",2:"GND",3:f"ACT{ch}_SW"}, x+8,82,"60 V logic-level actuator NMOS")
    add(f"R{26+ch}", "33R", "RC0603FR-0733RL", "R0603", {1:f"ACT{ch}_CTL",2:f"ACT{ch}_G"}, x+4,77,"MOSFET gate resistor")
    add(f"R{28+ch}", "100k", "RC0603FR-07100KL", "R0603", {1:f"ACT{ch}_G",2:"GND"}, x+10,77,"MOSFET reset-state pull-down")
    # SMA pin 1 is the banded cathode.  A low-side flyback diode therefore
    # connects pin 1 to +ACTx_VP and pin 2 (anode) to the switched node.
    add(f"D{5+ch}", "SS36", "SS36", "SMA_K_RIGHT", {1:f"ACT{ch}_VP",2:f"ACT{ch}_SW"}, x+12,84,"60 V inductive flyback diode")
    add(f"TP{2+ch}", f"ACT{ch}_SW", "5015", "TP", {1:f"ACT{ch}_SW"}, x+13,89,"Output test point")

for ref,x,y in [("TP5",43,18),("TP6",86,18),("TP7",104,18),("TP8",37,30)]:
    net={"TP5":"VIN_PROT","TP6":"+5V","TP7":"+3V3","TP8":"GND"}[ref]
    add(ref,net,"5015","TP",{1:net},x,y,"Power rail test point")
for ref,x,y in [("H1",5,5),("H2",135,5),("H3",5,85),("H4",135,85)]:
    add(ref,"M3","9774050360R","MOUNT",{},x,y,"M3 plated mounting hole")

# Expand the demonstrator board for clean hand-assembly access and generous routing.
for part in P:
    part.x=4+(part.x-4)*1.60
    part.y=4+(part.y-4)*1.60


FP_PADS = {
    "R0603":[("1",-0.8,0), ("2",0.8,0)], "C0603":[("1",-0.8,0),("2",0.8,0)],
    "LED0603":[("1",-0.8,0),("2",0.8,0)], "C1210":[("1",-1.5,0),("2",1.5,0)],
    "FUSE_NANO2":[("1",-2.455,0),("2",2.455,0)], "SMA":[("1",-2.2,0),("2",2.2,0)],
    # Same SMA land pattern, rotated 180 degrees so the banded pin-1 cathode
    # is on the positive-rail side of the already-proven actuator routing.
    "SMA_K_RIGHT":[("1",2.2,0),("2",-2.2,0)],
    "SMB":[("1",-2.7,0),("2",2.7,0)], "IND_6X6":[("1",-3.1,0),("2",3.1,0)],
    "CAP_SMD_63":[("1",-3.2,0),("2",3.2,0)], "SOT23":[("1",-1,-1),("2",1,-1),("3",0,1)],
    "SOT23_5":[("1",-1,-1),("2",0,-1),("3",1,-1),("4",1,1),("5",-1,1)],
    "SOT23_6":[("1",-1.05,-0.95),("2",-1.05,0),("3",-1.05,0.95),("4",1.05,0.95),("5",1.05,0),("6",1.05,-0.95)],
    "XTAL4":[("1",-1.2,0),("2",0,-1),("3",1.2,0),("4",0,1)], "BUTTON":[("1",-2.25,0),("2",2.25,0)],
    "TP":[("1",0,0)], "MOUNT":[],
}
# TI's Q5B package has three electrical terminals: three source fingers (pin 1),
# one gate finger (pin 2), and a large drain land plus four drain fingers (pin 3).
# The coordinates follow KiCad's verified VSONP-8-1EP_5x6_P1.27mm land pattern.
FP_PADS["SON5X6_8"]=[
    ("1",-2.80,-1.905),("1",-2.80,-0.635),("1",-2.80,0.635),("2",-2.80,1.905),
    ("3",0.33,0.0),("3",2.80,-1.905),("3",2.80,-0.635),("3",2.80,0.635),("3",2.80,1.905),
]
FP_PADS["SOIC8"]=[(str(i+1),-2.7,-1.905+1.27*i) for i in range(4)]+[(str(8-i),2.7,-1.905+1.27*i) for i in range(4)]
FP_PADS["HSOIC8_EP"]=FP_PADS["SOIC8"]+[("9",0,0)]
FP_PADS["LQFP48"]=[]
for i in range(12):
    FP_PADS["LQFP48"].append((str(1+i),-4.6,-2.75+0.5*i))
    FP_PADS["LQFP48"].append((str(13+i),-2.75+0.5*i,4.6))
    FP_PADS["LQFP48"].append((str(25+i),4.6,2.75-0.5*i))
    FP_PADS["LQFP48"].append((str(37+i),2.75-0.5*i,-4.6))
for n in (2,3,4,5,6):
    FP_PADS[f"HDR{n}"]=[(str(i+1),0,(i-(n-1)/2)*2.54) for i in range(n)]
for n in (2,3):
    FP_PADS[f"TERM{n}"]=[(str(i+1),0,(i-(n-1)/2)*5.00) for i in range(n)]


def ensure_dirs():
    for d in (KICAD,LIB,LIB/"Local.pretty",MFG,MFG/"Gerbers",MFG/"Drill_Files",MFG/"Fabrication_Notes",DOC,ROOT/"Images"/"Schematic",ROOT/"Images"/"PCB_Layout",ROOT/"Images"/"PCB_3D"):
        d.mkdir(parents=True, exist_ok=True)


def make_symbol(name: str, pins: Sequence[Tuple[str,str]]):
    n=max(2,len(pins)); left=pins[:(n+1)//2]; right=pins[(n+1)//2:]
    h=max(200,100*max(len(left),len(right)))
    lines=[f"#\n# {name}\n#\nDEF {name} U 0 30 Y Y 1 F N",f'F0 "U" 0 {h//2+100} 50 H V C CNN',f'F1 "{name}" 0 {-h//2-100} 50 H V C CNN',"DRAW",f"S -250 {h//2} 250 {-h//2} 0 1 10 f"]
    for idx,(num,pname) in enumerate(left):
        yy=h//2-50-100*idx; lines.append(f"X {pname} {num} -350 {yy} 100 R 35 35 1 1 P")
    for idx,(num,pname) in enumerate(right):
        yy=h//2-50-100*idx; lines.append(f"X {pname} {num} 350 {yy} 100 L 35 35 1 1 P")
    return "\n".join(lines+["ENDDRAW","ENDDEF"]), left, right, h


def write_legacy_schematic():
    cache=["EESchema-LIBRARY Version 2.4","#encoding utf-8"]
    sym_info={}
    shapes={}
    for part in P:
        key=part.ref
        pinlist=list(part.pins.items())
        block,left,right,h=make_symbol(key,pinlist)
        cache.append(block); sym_info[key]=(left,right,h)
    cache += ["#\n#End Library"]
    (KICAD/"STM32_Industrial_Controller-cache.lib").write_text("\n".join(cache)+"\n")
    out=["EESchema Schematic File Version 4","LIBS:STM32_Industrial_Controller-cache","EELAYER 29 0","EELAYER END","$Descr A3 16535 11693","Sheet 1 1",'Title "STM32 Industrial Sensor, DAQ and Actuator Controller"','Date "2026-11-19"','Rev "D"','Comp "Engineering Demonstration Platform"','Comment1 "Input 9-30 VDC; nominal 12 V; actuator outputs nominal 12 V, 1.5 A each"','Comment2 "NOT a certified safety controller"',"$EndDescr"]
    sections=[(800,600,"POWER INPUT / 5 V / 3.3 V"),(800,3500,"MCU / CLOCK / RESET / DEBUG"),(800,7100,"ANALOG / RS-485 / ACTUATORS")]
    for x,y,t in sections: out.append(f"Text Notes {x} {y} 0    100  ~ 20\n{t}")
    # Arrange by board X/Y scaled to page, retaining functional grouping.
    for idx,part in enumerate(P):
        # Lay the manifest out on an electrical grid independent of the PCB
        # coordinates.  This guarantees that no two generated pin/label
        # endpoints are co-located after native conversion.  The large MCU is
        # placed in its own column because its 48-pin symbol spans several
        # normal grid rows.
        if part.ref == "U1":
            sx,sy=16000,5800
        else:
            sx=850+(idx%12)*1300; sy=800+(idx//12)*1200
        left,right,h=sym_info[part.ref]
        out += ["$Comp",f"L {part.ref} {part.ref}",f"U 1 1 {abs(hash(part.ref)) & 0xFFFFFF:06X}",f"P {sx} {sy}",f'F 0 "{part.ref}" H {sx} {sy-h//2-80} 50  0000 C CNN',f'F 1 "{part.value}" H {sx} {sy+h//2+80} 50  0000 C CNN',f'F 2 "Local:{part.footprint}" H {sx} {sy} 50  0001 C CNN',f'F 3 "{part.mpn}" H {sx} {sy} 50  0001 C CNN',f"\t1    {sx} {sy}","\t1 0 0 -1","$EndComp"]
        for idx,(num,net) in enumerate(left):
            # The legacy symbol instance uses a vertically mirrored transform
            # (1 0 0 -1), so the sheet-space pin Y is the negative of the
            # library-space pin Y.
            yy=sy-(h//2-50-100*idx)
            if net.startswith("NC_"):
                out.append(f"NoConn ~ {sx-350} {yy}")
            else:
                out.append(f"Text GLabel {sx-350} {yy} 2    35   BiDi ~ 0\n{net}")
        for idx,(num,net) in enumerate(right):
            yy=sy-(h//2-50-100*idx)
            if net.startswith("NC_"):
                out.append(f"NoConn ~ {sx+350} {yy}")
            else:
                out.append(f"Text GLabel {sx+350} {yy} 0    35   BiDi ~ 0\n{net}")
    out += ["$EndSCHEMATC"]
    (KICAD/"STM32_Industrial_Controller.sch").write_text("\n".join(out)+"\n")


def fp_pad_size(fp):
    if fp in ("TERM2","TERM3"): return 2.50,2.50,"thru_hole"
    if fp in ("HDR2","HDR3","HDR4","HDR5","HDR6"): return 1.8,1.8,"thru_hole"
    if fp=="TP": return 2.0,2.0,"thru_hole"
    if fp=="LQFP48": return .55,1.5,"smd"
    if fp in ("SOIC8","HSOIC8_EP"): return 1.5,.65,"smd"
    if fp=="SOT23_5": return .60,1.20,"smd"
    if fp=="SOT23_6": return 1.325,.60,"smd"
    if fp=="SOT23": return 1.1,.9,"smd"
    if fp=="FUSE_NANO2": return 1.96,3.15,"smd"
    if fp=="SON5X6_8": return .70,.70,"smd"
    if fp in ("SMA","SMA_K_RIGHT","SMB","C1210","IND_6X6","CAP_SMD_63"): return 2.4,2.0,"smd"
    return 1.0,1.0,"smd"


def actual_pad_size(fp, num, dx, dy):
    """Return land dimensions, including package-specific exposed pads."""
    sx, sy, ptype = fp_pad_size(fp)
    if fp == "LQFP48":
        if 1 <= int(num) <= 12 or 25 <= int(num) <= 36:
            sx, sy = 1.5, .30
        else:
            sx, sy = .30, 1.5
    if fp == "SON5X6_8" and num == "3" and abs(dx-.33) < .001:
        sx, sy = 4.35, 4.51
    if fp == "HSOIC8_EP" and num == "9":
        # TI DDA land-pattern data specifies a 3.10 mm x 2.40 mm copper pad.
        sx, sy = 3.10, 2.40
    return sx, sy, ptype


def courtyard(fp, pads):
    """Conservative component courtyard around copper and the package body."""
    if fp == "MOUNT":
        return -1.85, -1.85, 1.85, 1.85
    extents=[]
    for num, dx, dy in pads:
        sx, sy, _ = actual_pad_size(fp, num, dx, dy)
        extents.append((dx-sx/2, dy-sy/2, dx+sx/2, dy+sy/2))
    xmin=min(e[0] for e in extents); ymin=min(e[1] for e in extents)
    xmax=max(e[2] for e in extents); ymax=max(e[3] for e in extents)
    body={"LQFP48":(7.25,7.25), "SON5X6_8":(6.0,5.0), "SOT23_6":(3.0,3.0),
          "SOIC8":(5.0,5.2), "HSOIC8_EP":(5.0,5.2), "IND_6X6":(6.6,6.6),
          "CAP_SMD_63":(6.6,6.6), "BUTTON":(4.5,3.2)}
    bx,by=body.get(fp,(0,0))
    xmin=min(xmin,-bx/2)-.25; xmax=max(xmax,bx/2)+.25
    ymin=min(ymin,-by/2)-.25; ymax=max(ymax,by/2)+.25
    return xmin,ymin,xmax,ymax


def courtyard_lines(fp, pads, indent="  "):
    xmin,ymin,xmax,ymax=courtyard(fp,pads)
    return [
        f'{indent}(fp_rect (start {xmin:.3f} {ymin:.3f}) (end {xmax:.3f} {ymax:.3f})',
        f'{indent}  (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))'
    ]


def write_local_footprints():
    """Emit the project-local library referenced by every schematic symbol."""
    for name, pads in FP_PADS.items():
        sx, sy, ptype = fp_pad_size(name)
        lines = [
            f'(footprint "{name}"',
            '  (version 20250114)',
            '  (generator "pcbnew")',
            '  (layer "F.Cu")',
            '  (fp_text reference "REF**" (at 0 -4) (layer "F.SilkS")',
            '    (effects (font (size 1 1) (thickness 0.15))))',
            f'  (fp_text value "{name}" (at 0 4) (layer "F.Fab")',
            '    (effects (font (size 1 1) (thickness 0.15))))',
        ]
        if name == "MOUNT":
            lines.append('  (attr board_only exclude_from_pos_files)')
        elif ptype == "thru_hole":
            lines.append('  (attr through_hole)')
        else:
            lines.append('  (attr smd)')
        lines.extend(courtyard_lines(name, pads))
        if name == "MOUNT":
            lines.append('  (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask"))')
        else:
            for num, dx, dy in pads:
                psx, psy, _ = actual_pad_size(name, num, dx, dy)
                if ptype == "thru_hole":
                    zc=' (zone_connect 2)' if name=="TP" else ''
                    drill=1.30 if name in {"TERM2","TERM3"} else 1.0
                    lines.append(f'  (pad "{num}" thru_hole circle (at {dx:.3f} {dy:.3f}) (size {psx:.3f} {psy:.3f}) (drill {drill:.2f}) (layers "*.Cu" "*.Mask"){zc})')
                else:
                    layers='"F.Cu" "F.Mask"' if name == "SON5X6_8" and num == "3" and abs(dx-.33)<.001 else '"F.Cu" "F.Paste" "F.Mask"'
                    shape="rect" if name == "SON5X6_8" and num == "3" and abs(dx-.33)<.001 else "roundrect"
                    rr="" if shape == "rect" else " (roundrect_rratio 0.2)"
                    zc=' (zone_connect 2)' if name in {"FUSE_NANO2","SON5X6_8"} else ''
                    lines.append(f'  (pad "{num}" smd {shape} (at {dx:.3f} {dy:.3f}) (size {psx:.3f} {psy:.3f}) (layers {layers}){rr}{zc})')
            if name == "SON5X6_8":
                for px,py,psx,psy in [(-.7975,-1.095,1.235,1.57),(-.7975,1.095,1.235,1.57),(1.1125,-1.095,1.585,1.57),(1.1125,1.095,1.585,1.57)]:
                    lines.append(f'  (pad "" smd rect (at {px:.4f} {py:.4f}) (size {psx:.3f} {psy:.3f}) (layers "F.Paste"))')
        lines.append(')')
        (LIB / "Local.pretty" / f"{name}.kicad_mod").write_text("\n".join(lines) + "\n")


def pad_escape(part, num, dx, dy):
    """Return a copper-clear point reached by a straight fan-out from a pad."""
    x,y=part.x+dx,part.y+dy
    fp=part.footprint; n=int(num)
    if fp=="LQFP48":
        if n<=12: return part.x-6.2,y
        if n<=24: return x,part.y+6.2
        if n<=36: return part.x+6.2,y
        return x,part.y-6.2
    if fp in ("SOIC8","HSOIC8_EP") and n!=9: return (part.x-4.2,y) if dx<0 else (part.x+4.2,y)
    if fp in ("SOT23","SOT23_5"): return (x,part.y-2.3) if dy<0 else (x,part.y+2.3)
    if fp in ("SOT23_6","SON5X6_8"): return (part.x-4.0,y) if dx<0 else (part.x+4.0,y)
    if fp in ("C1210","FUSE_NANO2","SMA","SMA_K_RIGHT","SMB","IND_6X6","CAP_SMD_63"):
        return (x-1.8,y) if dx<0 else (x+1.8,y)
    if fp in ("R0603","C0603","LED0603","BUTTON"):
        return (x-1.3,y) if dx<0 else (x+1.3,y)
    if fp=="XTAL4":
        if abs(dx)>=abs(dy): return (x-1.3,y) if dx<0 else (x+1.3,y)
        return (x,y-1.3) if dy<0 else (x,y+1.3)
    return x,y


def build_board():
    def pcb_net(part, num, name):
        if name.startswith("NC_"):
            return f"unconnected-({part.ref}-{name}-Pad{num})"
        return name
    nets=sorted({pcb_net(p,num,n) for p in P for num,n in p.pins.items()})
    netid={"":0}; netid.update({n:i+1 for i,n in enumerate(nets)})
    lines=["(kicad_pcb (version 20250114) (generator pcbnew)","  (general (thickness 1.6))",'  (paper "A4")',"  (layers",'    (0 "F.Cu" signal)','    (2 "In1.Cu" power "GND plane")','    (4 "In2.Cu" power "Power plane")','    (31 "B.Cu" signal)','    (34 "B.Paste" user)','    (35 "F.Paste" user)','    (36 "B.SilkS" user "b.silkscreen")','    (37 "F.SilkS" user "f.silkscreen")','    (38 "B.Mask" user)','    (39 "F.Mask" user)','    (44 "Edge.Cuts" user)','    (46 "B.CrtYd" user "b.courtyard")','    (47 "F.CrtYd" user "f.courtyard")','    (48 "B.Fab" user)','    (49 "F.Fab" user)',"  )",'  (setup (pad_to_mask_clearance 0))']
    for n,i in netid.items():
        if i: lines.append(f'  (net {i} "{n}")')
    padpoints=[]
    for part in P:
        pads=FP_PADS.get(part.footprint,[])
        lines += [f'  (footprint "Local:{part.footprint}" (layer "F.Cu") (at {part.x:.3f} {part.y:.3f})',f'    (property "Reference" "{part.ref}" (at 0 -3.5 0) (layer "F.Fab"))',f'    (property "Value" "{part.value}" (at 0 4 0) (layer "F.Fab") hide)',f'    (property "Datasheet" "{part.mpn}" (at 0 0 0) (layer "F.Fab") hide)']
        if part.footprint == "MOUNT": lines.append('    (attr board_only exclude_from_pos_files)')
        elif fp_pad_size(part.footprint)[2] == "thru_hole": lines.append('    (attr through_hole)')
        else: lines.append('    (attr smd)')
        lines.extend(courtyard_lines(part.footprint,pads,"    "))
        if part.footprint=="MOUNT":
            lines += ['    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask"))',"  )"]; continue
        sx,sy,ptype=fp_pad_size(part.footprint)
        for num,dx,dy in pads:
            psx,psy,_=actual_pad_size(part.footprint,num,dx,dy)
            raw_net=part.pins.get(num,"")
            net=pcb_net(part,num,raw_net) if raw_net else ""
            nid=netid.get(net,0)
            if ptype=="thru_hole":
                zc=' (zone_connect 2)' if part.footprint=="TP" else ''
                drill=1.30 if part.footprint in {"TERM2","TERM3"} else 1.0
                lines.append(f'    (pad "{num}" thru_hole circle (at {dx:.3f} {dy:.3f}) (size {psx:.3f} {psy:.3f}) (drill {drill:.2f}) (layers "*.Cu" "*.Mask") (net {nid} "{net}"){zc})')
            else:
                layers='"F.Cu" "F.Mask"' if part.footprint == "SON5X6_8" and num == "3" and abs(dx-.33)<.001 else '"F.Cu" "F.Paste" "F.Mask"'
                shape="rect" if part.footprint == "SON5X6_8" and num == "3" and abs(dx-.33)<.001 else "roundrect"
                rr="" if shape == "rect" else " (roundrect_rratio 0.2)"
                zc=' (zone_connect 2)' if part.footprint in {"FUSE_NANO2","SON5X6_8"} else ''
                lines.append(f'    (pad "{num}" smd {shape} (at {dx:.3f} {dy:.3f}) (size {psx:.3f} {psy:.3f}) (layers {layers}){rr} (net {nid} "{net}"){zc})')
            ex,ey=pad_escape(part,num,dx,dy)
            owner=net if net else f"__{part.ref}_{num}"
            # Keep the proven Rev-C escape topology around U2 while emitting
            # the full TI pad-9 copper land.  The final DRC checks the actual
            # 3.10 x 2.40 mm pad against the routed copper.
            obs_psx,obs_psy=(1.5,.65) if part.footprint=="HSOIC8_EP" and num=="9" else (psx,psy)
            padpoints.append((owner,net if net in netid else "",part.x+dx,part.y+dy,ex,ey,ptype,obs_psx,obs_psy,part.ref,part.footprint))
        if part.footprint == "SON5X6_8":
            for px,py,psx,psy in [(-.7975,-1.095,1.235,1.57),(-.7975,1.095,1.235,1.57),(1.1125,-1.095,1.585,1.57),(1.1125,1.095,1.585,1.57)]:
                lines.append(f'    (pad "" smd rect (at {px:.4f} {py:.4f}) (size {psx:.3f} {psy:.3f}) (layers "F.Paste"))')
        lines.append("  )")
    # Treat the actuator-source ground stitches as routing terminals from the
    # outset.  This makes the wide power routes keep away from the via arrays
    # instead of adding the return vias after routing and discovering a clash.
    ground_stitches=[]
    for ref in ("Q1","Q2"):
        q=next(p for p in P if p.ref==ref)
        sx=q.x+1.0; sy=q.y-1.0
        for idx,(vx,vy) in enumerate(((sx+1.6,sy-.55),(sx+1.6,sy+.55)),1):
            ground_stitches.append((vx,vy))
            padpoints.append((f"__{ref}_GND_STITCH_{idx}","GND",vx,vy,sx,sy,"via",.8,.8,ref,"GROUND_STITCH"))
    # Grid-based four-layer maze router. It uses all four signal-capable layers and
    # never occupies the same grid node with two nets, so crossings are made by vias.
    bynet={n:[] for n in nets}
    for owner,net,x,y,ex,ey,ptype,sx,sy,ref,fp in padpoints:
        if net: bynet[net].append((x,y,ex,ey,ptype,sx,sy,ref,fp))
    # Signals use the two outer layers only.  This keeps In1.Cu as an
    # uninterrupted ground reference and avoids the false assumption that a
    # standard through-via can independently connect arbitrary inner layers.
    step=.50; x0=2.5; y0=2.5; nx=435; ny=291; nl=2
    layer_names=["F.Cu","B.Cu"]
    def node(x,y,l=0): return (max(0,min(nx-1,round((x-x0)/step))),max(0,min(ny-1,round((y-y0)/step))),l)
    def xy(n): return (x0+n[0]*step,y0+n[1]*step)
    occupied={}
    via_sites=set()
    pad_track_owners={}
    via_forbidden_owners={}
    via_fanout_owners={}
    # Copper pads are obstacles to every other net on their copper layers.
    # Build every pad obstacle before reserving fan-outs so a fan-out can never
    # claim the connection point of a later component.
    pth_xy=set()
    for owner,net,x,y,ex,ey,ptype,sx,sy,ref,fp in padpoints:
        layers=range(4) if ptype in ("thru_hole","via") else (0,)
        obstacle_owner=net if fp=="GROUND_STITCH" else owner
        rx=max(0,int(math.floor((sx/2+.30)/step))); ry=max(0,int(math.floor((sy/2+.30)/step)))
        vrx=max(0,int(math.floor((sx/2+.30)/step))); vry=max(0,int(math.floor((sy/2+.30)/step)))
        c=node(x,y)
        for l in layers:
            for ix in range(c[0]-rx,c[0]+rx+1):
                for iy in range(c[1]-ry,c[1]+ry+1):
                    if 0<=ix<nx and 0<=iy<ny:
                        occupied.setdefault((ix,iy,l),obstacle_owner)
                        pad_track_owners.setdefault((ix,iy,l),set()).add(obstacle_owner)
            occupied[(c[0],c[1],l)]=obstacle_owner
        for ix in range(c[0]-vrx,c[0]+vrx+1):
            for iy in range(c[1]-vry,c[1]+vry+1):
                if 0<=ix<nx and 0<=iy<ny:
                    via_forbidden_owners.setdefault((ix,iy),set()).add(owner)
        if ptype in ("thru_hole","via"): pth_xy.add(node(x,y,0)[:2])
    # Reserve the fixed pad escape segments with the same 0.50 mm centre-line
    # keepout used by the maze router.  Exact pad centres remain owned by their
    # pad nets because they were installed in the first pass above.
    for owner,net,x,y,ex,ey,ptype,sx,sy,ref,fp in padpoints:
        distance=max(abs(ex-x),abs(ey-y)); samples=max(1,int(math.ceil(distance/.10)))
        fan_owner=net if fp=="GROUND_STITCH" else owner
        fan_width=.15
        if net in {"VIN_RAW","VIN_FUSED","VIN_PROT"}:
            fan_width=3.0 if fp in {"TERM2","FUSE_NANO2","SMB","TP"} else .30
            if fp == "SON5X6_8":
                q3_for_fan=next(p for p in P if p.ref=="Q3")
                fan_width=3.0 if net=="VIN_PROT" and sx>3.0 else .70
        elif net in {"ACT1_VP","ACT2_VP","ACT1_SW","ACT2_SW"}:
            if fp=="SON5X6_8": fan_width=2.0 if sx>3.0 else .70
            else: fan_width=1.20 if fp=="SOT23" else 2.0
        elif net == "GND" and fp=="SON5X6_8" and ref in {"Q1","Q2"}:
            fan_width=.70
        elif fp=="GROUND_STITCH": fan_width=.60
        fan_radius=max(0,int(math.ceil((fan_width/2+.10)/step))-1)
        for s in range(samples+1):
            xx=x+(ex-x)*s/samples; yy=y+(ey-y)*s/samples; nn=node(xx,yy,0)
            occupied[nn]=fan_owner
            for ox in range(-fan_radius,fan_radius+1):
                for oy in range(-fan_radius,fan_radius+1):
                    occupied.setdefault((nn[0]+ox,nn[1]+oy,0),fan_owner)
            for ox in (-1,0,1):
                for oy in (-1,0,1):
                    via_fanout_owners.setdefault((nn[0]+ox,nn[1]+oy),set()).add(owner)
        gx,gy=xy(node(ex,ey,0)); distance=max(abs(gx-ex),abs(gy-ey)); samples=max(1,int(math.ceil(distance/.05)))
        for s in range(samples+1):
            xx=ex+(gx-ex)*s/samples; yy=ey+(gy-ey)*s/samples; nn=node(xx,yy,0)
            occupied[nn]=fan_owner
            for ox in range(-fan_radius,fan_radius+1):
                for oy in range(-fan_radius,fan_radius+1):
                    occupied.setdefault((nn[0]+ox,nn[1]+oy,0),fan_owner)
            for ox in (-1,0,1):
                for oy in (-1,0,1):
                    via_fanout_owners.setdefault((nn[0]+ox,nn[1]+oy),set()).add(owner)
    main_power={"VIN_RAW","VIN_FUSED","VIN_PROT"}
    channel_power={"ACT1_VP","ACT2_VP","ACT1_SW","ACT2_SW"}
    logic_power={"VIN_LOGIC","+5V","+3V3"}
    q3=next(p for p in P if p.ref=="Q3")
    def route_width(net, fp=None, ref=None, sx=0, y=0):
        if net in main_power:
            if fp == "SON5X6_8":
                # One source finger carries the wide feed into the source
                # bank; the other fingers use short 0.70 mm parallel links.
                if net == "VIN_PROT" and sx > 3.0: return 3.0
                return .70
            return 3.0 if fp in {"TERM2","FUSE_NANO2","SON5X6_8","SMB","TP"} else .30
        if net in channel_power:
            return 1.20 if fp == "SOT23" else 2.0
        if net == "VIN_LOGIC": return .20
        if net in logic_power: return .15
        if net == "GND":
            if fp == "GROUND_STITCH": return .60
            return .20
        return .15
    def via_geometry(width):
        if width >= 1.0: return .80,.40
        if width >= .50: return .60,.30
        return .40,.20
    def astar(start,goals,net,width):
        if occupied.get(start) not in (None,net): return None
        q=[(0,0,start)]; prev={start:None}; score={start:0}; serial=0
        gx=sum(g[0] for g in goals)/len(goals); gy=sum(g[1] for g in goals)/len(goals)
        while q:
            _,_,cur=heapq.heappop(q)
            if cur in goals:
                path=[]
                while cur is not None: path.append(cur); cur=prev[cur]
                return list(reversed(path))
            x,y,l=cur
            nbr=[(x+1,y,l),(x-1,y,l),(x,y+1,l),(x,y-1,l)]
            nbr += [(x,y,ll) for ll in range(nl) if ll!=l]
            for nn in nbr:
                xx,yy,ll=nn
                if not (0<=xx<nx and 0<=yy<ny): continue
                owner=occupied.get(nn)
                if owner is not None and owner!=net and nn not in goals: continue
                radius=max(0,int(math.ceil((width/2+.10)/step))-1)
                if radius and nn not in goals:
                    blocked=False
                    for ox in range(-radius,radius+1):
                        for oy in range(-radius,radius+1):
                            other=occupied.get((xx+ox,yy+oy,ll))
                            if other not in (None,net): blocked=True; break
                        if blocked: break
                    if blocked: continue
                via=(ll!=l); cost=score[cur]+(9 if via else 1)+(2 if ll in (1,2) else 0)
                if via:
                    # All generated vias are ordinary through-vias.  A layer
                    # transition must therefore be clear on every copper
                    # layer, not merely on the two route layers.
                    # Existing tracks, pads and vias already expand their own
                    # clearance keepouts into ``occupied``.  Testing the via
                    # centre on every layer is therefore sufficient and keeps
                    # the A* inner loop inexpensive.
                    blocked=any(occupied.get((xx,yy,vl)) not in (None,net) for vl in range(nl))
                    if blocked or (xx,yy) in via_sites or (xx,yy) in via_forbidden_owners: continue
                if cost>=score.get(nn,10**12): continue
                score[nn]=cost; prev[nn]=cur; serial+=1
                h=abs(xx-gx)+abs(yy-gy)
                heapq.heappush(q,(cost+h,serial,nn))
        return None
    route_lines=[]; failures=[]
    # Route large/common nets first while the field is open.
    # The ideal-diode gate trace is physically surrounded by the wide input
    # path; establish it first, then let the power router keep clearance.
    route_first={"IDEAL_GATE","IDEAL_VCAP","BOOT1"} | main_power | channel_power
    def route_rank(item):
        net,pts=item
        tier=0 if net in {"IDEAL_GATE","IDEAL_VCAP"} else 1 if net in main_power else 2 if net in channel_power else 3 if net=="BOOT1" else 4
        return tier,-len(pts),net
    for net,pts in sorted(bynet.items(),key=route_rank):
        if len(pts)<2: continue
        nid=netid[net]
        terminals=[]
        for x,y,ex,ey,ptype,sx,sy,ref,fp in pts:
            layers=range(nl) if ptype=="thru_hole" else (0,)
            w=route_width(net,fp,ref,sx,y)
            terminals.append((x,y,ex,ey,[node(ex,ey,l) for l in layers],w,fp))
            if abs(x-ex)>.001 or abs(y-ey)>.001:
                route_lines.append(f'  (segment (start {x:.3f} {y:.3f}) (end {ex:.3f} {ey:.3f}) (width {w:.2f}) (layer "F.Cu") (net {nid}))')
            gx,gy=xy(node(ex,ey,0))
            if abs(ex-gx)>.001 or abs(ey-gy)>.001:
                route_lines.append(f'  (segment (start {ex:.3f} {ey:.3f}) (end {gx:.3f} {gy:.3f}) (width {w:.2f}) (layer "F.Cu") (net {nid}))')
        tree=set(terminals[0][4])
        for tx,ty,ex,ey,starts,w,fp in terminals[1:]:
            best=None
            for st in starts:
                pth=astar(st,tree,net,w)
                if pth is not None and (best is None or len(pth)<len(best)): best=pth
            if not best:
                failures.append((net,tx,ty)); continue
            new_vias=[]
            for a,b in zip(best,best[1:]):
                if a[2]!=b[2] and a[:2] not in new_vias:
                    new_vias.append(a[:2])
            # Compress consecutive same-layer collinear nodes.
            run=0
            while run<len(best)-1:
                a=best[run]; b=best[run+1]
                if a[2]!=b[2]:
                    vx,vy=xy(a)
                    if a[:2] not in pth_xy:
                        vs,vd=via_geometry(w)
                        route_lines.append(f'  (via (at {vx:.3f} {vy:.3f}) (size {vs:.2f}) (drill {vd:.2f}) (layers "{layer_names[min(a[2],b[2])]}" "{layer_names[max(a[2],b[2])]}") (net {nid}))')
                    run+=1; continue
                dx=b[0]-a[0]; dy=b[1]-a[1]; end=run+1
                while end<len(best)-1 and best[end][2]==best[end+1][2] and best[end+1][0]-best[end][0]==dx and best[end+1][1]-best[end][1]==dy: end+=1
                ax,ay=xy(a); bx,by=xy(best[end]); route_lines.append(f'  (segment (start {ax:.3f} {ay:.3f}) (end {bx:.3f} {by:.3f}) (width {w:.2f}) (layer "{layer_names[a[2]]}") (net {nid}))'); run=end
            radius=max(0,int(math.ceil((w/2+.10)/step))-1)
            for n in best:
                occupied[n]=net
                # A two-grid keepout gives 0.50 mm centre spacing.  This is
                # sufficient for a 0.40 mm via beside a 0.20 mm track with
                # the 0.10 mm Class-2 clearance rule.
                for ox in range(-radius,radius+1):
                    for oy in range(-radius,radius+1):
                        nn=(n[0]+ox,n[1]+oy,n[2])
                        if 0<=nn[0]<nx and 0<=nn[1]<ny: occupied.setdefault(nn,net)
            for vx,vy in new_vias:
                via_sites.add((vx,vy))
                for vl in range(nl):
                    for ox in range(-radius,radius+1):
                        for oy in range(-radius,radius+1):
                            nn=(vx+ox,vy+oy,vl)
                            if 0<=nn[0]<nx and 0<=nn[1]<ny: occupied[nn]=net
            tree.update(best)
    if failures:
        raise RuntimeError(f"Router could not connect {len(failures)} terminals: {failures[:8]}")
    # The 0.50 mm maze grid is deliberately coarse for deterministic runtime.
    # Nudge the few layer transitions that otherwise land just inside the
    # clearance envelope of adjacent fine-pitch fan-outs.  All connected
    # segment endpoints move with each via, preserving connectivity.
    via_adjustments={
        ("STATUS_LED",101.0,77.5):(101.0,78.0),
        ("STATUS_LED",100.5,77.5):(100.4,77.6),
        ("STATUS_LED",100.5,72.0):(100.5,72.1),
        ("OSC_OUT",100.5,74.0):(100.5,74.1),
        ("OSC_OUT",100.5,77.5):(100.5,77.6),
        ("OSC_OUT",79.5,111.5):(80.0,111.5),
        ("SPI_NSS",104.0,80.5):(104.1,80.4),
        ("SPI_SCK",104.5,80.5):(104.6,80.4),
        ("SPI_MISO",105.0,80.5):(105.1,80.4),
        ("RS485_TX",161.5,109.0):(161.5,109.1),
        ("ACT2_CTL",105.0,68.5):(105.2,68.4),
        ("ACT2_CTL",119.5,120.5):(120.0,120.5),
        ("FAULT_LED",104.5,68.5):(104.7,68.7),
        ("GND",38.0,32.5):(42.0,32.5),
    }
    for (net,ox,oy),(nxv,nyv) in via_adjustments.items():
        nid=netid[net]; old=f"{ox:.3f} {oy:.3f}"; new=f"{nxv:.3f} {nyv:.3f}"
        for idx,line in enumerate(route_lines):
            if f"(net {nid})" not in line: continue
            line=line.replace(f"(start {old})",f"(start {new})")
            line=line.replace(f"(end {old})",f"(end {new})")
            line=line.replace(f"(at {old})",f"(at {new})")
            route_lines[idx]=line
    # The corrected 3.10 x 2.40 mm U2 PowerPAD needs the nearby PG and VCC
    # paths moved around its copper boundary.  These local replacements keep
    # every other verified Rev-C route unchanged.
    remove_exact={
        '  (segment (start 89.000 21.500) (end 89.000 25.500) (width 0.15) (layer "B.Cu") (net 35))',
        '  (segment (start 89.500 21.500) (end 89.000 21.500) (width 0.15) (layer "B.Cu") (net 35))',
        '  (via (at 89.000 25.500) (size 0.40) (drill 0.20) (layers "F.Cu" "B.Cu") (net 35))',
        '  (segment (start 89.000 25.500) (end 89.000 26.500) (width 0.15) (layer "F.Cu") (net 35))',
        '  (segment (start 89.000 26.500) (end 86.000 26.500) (width 0.15) (layer "F.Cu") (net 35))',
        '  (segment (start 86.000 27.500) (end 91.500 27.500) (width 0.15) (layer "F.Cu") (net 56))',
        '  (segment (start 91.500 27.500) (end 91.500 26.000) (width 0.15) (layer "F.Cu") (net 56))',
        '  (segment (start 91.500 26.000) (end 94.500 26.000) (width 0.15) (layer "F.Cu") (net 56))',
        '  (segment (start 94.500 26.000) (end 94.500 25.500) (width 0.15) (layer "F.Cu") (net 56))',
        '  (via (at 86.000 27.500) (size 0.40) (drill 0.20) (layers "F.Cu" "B.Cu") (net 56))',
    }
    route_lines=[line for line in route_lines if line not in remove_exact]
    route_lines += [
        '  (via (at 86.000 26.500) (size 0.40) (drill 0.20) (layers "F.Cu" "B.Cu") (net 35))',
        '  (segment (start 86.000 26.500) (end 88.000 26.500) (width 0.15) (layer "B.Cu") (net 35))',
        '  (segment (start 88.000 26.500) (end 88.000 21.500) (width 0.15) (layer "B.Cu") (net 35))',
        '  (segment (start 88.000 21.500) (end 89.500 21.500) (width 0.15) (layer "B.Cu") (net 35))',
        '  (segment (start 86.000 27.500) (end 93.500 27.500) (width 0.15) (layer "B.Cu") (net 56))',
        '  (segment (start 93.500 27.500) (end 93.500 25.500) (width 0.15) (layer "B.Cu") (net 56))',
        '  (via (at 93.500 25.500) (size 0.40) (drill 0.20) (layers "F.Cu" "B.Cu") (net 56))',
        '  (segment (start 93.500 25.500) (end 94.500 25.500) (width 0.15) (layer "F.Cu") (net 56))',
    ]
    # Two 0.40 mm finished vias per actuator provide a redundant, low-impedance
    # connection from the wide source fan-out into the In1.Cu ground plane.
    for vx,vy in ground_stitches:
        route_lines.append(f'  (via (at {vx:.3f} {vy:.3f}) (size 0.80) (drill 0.40) (layers "F.Cu" "B.Cu") (net {netid["GND"]}))')
    u2=next(p for p in P if p.ref=="U2")
    for ox in (-1.0,0.0,1.0):
        for oy in (-0.6,0.6):
            route_lines.append(f'  (via (at {u2.x+ox:.3f} {u2.y+oy:.3f}) (size 0.60) (drill 0.30) (layers "F.Cu" "B.Cu") (net {netid["GND"]}))')
    route_lines.append(f'  (via (at 104.000 68.000) (size 0.40) (drill 0.20) (layers "F.Cu" "B.Cu") (net {netid["GND"]}))')
    lines.extend(route_lines)
    # Board outline and reference planes. Keepouts around signal tracks are handled by zone fill.
    for a,b in [((2,2),(220,2)),((220,2),(220,148)),((220,148),(2,148)),((2,148),(2,2))]:
        lines.append(f'  (gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.15) (type default)) (layer "Edge.Cuts"))')
    lines += [
      '  (gr_text "STM32 INDUSTRIAL CONTROLLER  REV D" (at 111 4) (layer "F.SilkS") (effects (font (size 1.3 1.3) (thickness 0.2))))',
      '  (gr_text "9-30V IN | OUTPUTS: 12V NOM, 1.5A MAX" (at 111 6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
      f'  (zone (net {netid["GND"]}) (net_name "GND") (layer "In1.Cu") (hatch edge 0.5) (connect_pads (clearance 0.3)) (min_thickness 0.25) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy 2.5 2.5) (xy 219.5 2.5) (xy 219.5 147.5) (xy 2.5 147.5))))',
      f'  (zone (net {netid["VIN_PROT"]}) (net_name "VIN_PROT") (layer "In2.Cu") (hatch edge 0.5) (connect_pads (clearance 0.3)) (min_thickness 0.25) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.5)) (polygon (pts (xy 2.5 2.5) (xy 219.5 2.5) (xy 219.5 147.5) (xy 2.5 147.5))))',
      f'  (zone (net {netid["VIN_FUSED"]}) (net_name "VIN_FUSED") (layer "F.Cu") (hatch edge 0.5) (connect_pads (clearance 0.1)) (min_thickness 0.25) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.5)) (polygon (pts (xy 36.0 18.8) (xy 48.0 18.8) (xy 48.0 22.6) (xy 36.0 22.6))))',
      ")"]
    (KICAD/"STM32_Industrial_Controller.kicad_pcb").write_text("\n".join(lines)+"\n")


def write_tables():
    with (MFG/"BOM.csv").open("w",newline="") as f:
        w=csv.writer(f); w.writerow(["Reference","Quantity","Value","Manufacturer Part Number","Footprint","Description","Populate"])
        groups={}
        for p in P:
            if p.footprint=="MOUNT": continue
            k=(p.value,p.mpn,p.footprint,p.desc,p.dnp); groups.setdefault(k,[]).append(p.ref)
        for (value,mpn,fp,desc,dnp),refs in sorted(groups.items(),key=lambda z:z[1][0]):
            w.writerow([" ".join(refs),len(refs),value,mpn,fp,desc,"NO" if dnp else "YES"])
    with (MFG/"Pick_and_Place.csv").open("w",newline="") as f:
        w=csv.writer(f); w.writerow(["Reference","Value","Footprint","PosX_mm","PosY_mm","Rotation_deg","Side"])
        for p in P:
            if p.footprint!="MOUNT": w.writerow([p.ref,p.value,p.footprint,f"{p.x:.3f}",f"{p.y:.3f}",0,"Top"])
    with (DOC/"Pin_Map.csv").open("w",newline="") as f:
        w=csv.writer(f); w.writerow(["MCU Pin","STM32 Signal","Board Net","Function","Startup state"])
        fn={"ADC_IN1":"ADC1_IN0 0-10V channel 1","ADC_IN2":"ADC1_IN1 0-10V channel 2","UART_TX":"USART2_TX","UART_RX":"USART2_RX","SPI_NSS":"SPI1_NSS","SPI_SCK":"SPI1_SCK","SPI_MISO":"SPI1_MISO","SPI_MOSI":"SPI1_MOSI","ACT1_CTL":"Actuator 1 low-side command","ACT2_CTL":"Actuator 2 low-side command","RS485_DIR":"RS-485 DE and /RE","RS485_TX":"USART1_TX","RS485_RX":"USART1_RX","I2C_SCL":"I2C1_SCL","I2C_SDA":"I2C1_SDA","STATUS_LED":"Active-low status LED","FAULT_LED":"Active-low fault LED","SWDIO":"SWD data","SWCLK":"SWD clock"}
        pinname={10:"PA0",11:"PA1",12:"PA2",13:"PA3",14:"PA4",15:"PA5",16:"PA6",17:"PA7",18:"PB0",19:"PB1",20:"PB2",30:"PA9",31:"PA10",34:"PA13",37:"PA14",42:"PB6",43:"PB7",44:"BOOT0",45:"PB8",46:"PB9",2:"PC13"}
        for pin,net in mcu.items():
            if net in fn: w.writerow([pin,pinname.get(pin,""),net,fn[net],"Low/output disabled" if "ACT" in net or net=="RS485_DIR" else "Input/Hi-Z until configured"])
    def netclass(name,width,via,drill):
        return {"bus_width":12.0,"clearance":0.10,"diff_pair_gap":0.20,"diff_pair_via_gap":0.25,"diff_pair_width":0.20,"line_style":0,"microvia_diameter":0.30,"microvia_drill":0.10,"name":name,"pcb_color":"rgba(0, 0, 0, 0.000)","schematic_color":"rgba(0, 0, 0, 0.000)","track_width":width,"via_diameter":via,"via_drill":drill,"wire_width":6.0}
    classes=[netclass("Default",.15,.40,.20),netclass("Power Main",3.0,.80,.40),netclass("Power Channel",2.0,.80,.40),netclass("Power Logic",.20,.60,.30),netclass("Ground",.20,.80,.40)]
    assignments={n:"Power Main" for n in ("VIN_RAW","VIN_FUSED","VIN_PROT")}
    assignments.update({n:"Power Channel" for n in ("ACT1_VP","ACT2_VP","ACT1_SW","ACT2_SW")})
    assignments.update({n:"Power Logic" for n in ("VIN_LOGIC","+5V","+3V3")})
    assignments["GND"]="Ground"
    severities={"courtyards_overlap":"error","missing_courtyard":"error","malformed_courtyard":"error","footprint_type_mismatch":"error","footprint_filters_mismatch":"warning","lib_footprint_issues":"warning","lib_footprint_mismatch":"warning","track_not_centered_on_via":"error","tuning_profile_track_geometries":"warning"}
    project={"meta":{"filename":"STM32_Industrial_Controller.kicad_pro","version":1},"board":{"design_settings":{"rule_severities":severities}},"cvpcb":{},"erc":{},"libraries":{},"net_settings":{"classes":classes,"meta":{"version":3},"net_colors":None,"netclass_assignments":assignments},"pcbnew":{},"schematic":{},"text_variables":{"PROJECT_TITLE":"STM32 Industrial Controller","REVISION":"D"}}
    (KICAD/"STM32_Industrial_Controller.kicad_pro").write_text(json.dumps(project,indent=2)+"\n")
    (KICAD/"STM32_Industrial_Controller.kicad_dru").write_text('''(version 1)\n(rule "Class 2 fabrication minimums"\n  (constraint clearance (min 0.10mm))\n  (constraint track_width (min 0.15mm))\n  (constraint via_diameter (min 0.40mm))\n  (constraint hole_size (min 0.20mm))\n  (constraint hole_clearance (min 0.10mm))\n  (constraint hole_to_hole (min 0.20mm))\n  (constraint edge_clearance (min 0.25mm))\n)\n''')
    (KICAD/"fp-lib-table").write_text('(fp_lib_table\n  (lib (name "Local")(type "KiCad")(uri "${KIPRJMOD}/Libraries/Local.pretty")(options "")(descr "Project-local generated footprints"))\n)\n')
    (KICAD/"sym-lib-table").write_text('(sym_lib_table\n\t(version 7)\n\t(lib (name "STM32_Industrial_Controller-rescue") (type "Legacy") (uri "${KIPRJMOD}/STM32_Industrial_Controller-rescue.lib") (options "") (descr ""))\n)\n')
    notes="""STM32 Industrial Controller - Fabrication Notes - Revision D

Board: 218.0 mm x 146.0 mm, 1.60 mm finished thickness, four copper layers.
Stackup: L1 signal/components, L2 solid GND reference, L3 VIN_PROT power plane, L4 signal.
Copper: 35 um finished outer and inner layers. FR-4, Tg >= 150 C.
Minimum design rule: 0.15 mm trace, 0.10 mm copper spacing; 0.20 mm finished via drill, 0.40 mm pad.
Finish: lead-free HASL or ENIG. Solder mask both sides, green. White legend both sides.
Controlled impedance is not required. Route A/B as a coupled pair in any manual layout revision.
Mounting holes H1-H4: 3.2 mm NPTH. Board outline tolerance +/-0.20 mm.
Assembly: IPC-A-610 Class 2 target. No-clean lead-free process. Observe polarity and pin 1.
Do not fit jumpers JP2, JP3, JP4 by default; fit shunts only at one bus endpoint as required.
This is an engineering demonstration platform and is not safety-certified.
"""
    (MFG/"Fabrication_Notes"/"Fabrication_Notes.txt").write_text(notes)


def main():
    ensure_dirs(); write_legacy_schematic(); write_local_footprints(); build_board(); write_tables()
    print(f"Generated {len(P)} placed components in {ROOT}")


if __name__ == "__main__": main()
