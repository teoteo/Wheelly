<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# Wheelly - bill of materials

**Generated** by `mechanics/wheelly-cad/src/bom_global.py` at every build:
do not edit it by hand. Masses come from the solids, quantities from the
assembly, screw lengths from what the model needs under the head, and the
electronics from `src/bom_electronics.py`. The reasons behind the
electronic parts are in [`pcb/BOM.md`](pcb/BOM.md) and
[`hardware.md`](hardware.md); the assembly guide is in
[`docs/assembly/`](docs/assembly/README.md).

Dimensions marked **M** were measured with a caliper on a real part.

## 1. Printed parts

| Qty | Part | Material | Mass | How it prints |
|---:|---|---|---:|---|
| 1 | box and collar | ASA | 124.9 g | the electronics door on the plate: a 143 × 143 mm bed, the part turned 46° on it, 60 mm tall; or the face of the GX12 connector on the plate: 133 × 133 mm, turned 145°, 140 mm tall |
| 1 | arm | ASA | 14.5 g | top face on the plate - body and motor plate end on the same plane |
| 1 | clutch hub | ASA | 11.8 g | axis vertical, collar face on the plate |
| 1 | clutch tyre | TPU 87A-95A | 1.7 g | co-printed with the hub |
| 1 | sensor bracket | ASA | 10.4 g | the flat underside, with the pad, on the plate |
| 1 | sensor cover | ASA | 3.2 g | outer face on the plate |
| 1 | board panel | ASA | 9.9 g | outer face on the plate |
| 1 | spring cup | ASA | 0.3 g | flat back on the plate, dish up |
| 1 | grip cover | ASA | 11.7 g | upside down, top face on the plate |
| 1 | motor hatch cover | ASA | 5.2 g | outer face on the plate - the face in sight, flush with the floor |
| 1 | pivot washer | ASA | 0.2 g | flange on the plate, sleeve up |
| 4 | magnet spacer | ASA | 0.6 g | four of them - it is a part that gets lost |
| 1 | front gasket | TPU 87A-95A | 0.7 g | flat on the bed, lip up (co-print it with the collar if you have a multi-material printer) |
| 1 | rear gasket | TPU 87A-95A | 0.7 g | flat on the bed, lip up (co-print it with the collar if you have a multi-material printer) |

In all: **193 g** of ASA, **3 g** of TPU 87A-95A.

## 2. Bought: mechanics

| Qty | Part | What exactly |
|---:|---|---|
| 2 | F695ZZ bearing | F695ZZ flanged, 5 × 13 × 4 |
| 1 | M3 grub screw · clutch | M3 × 10 headless hex GRUB SCREW (10.0 mm from the shaft flat to the insert) |
| 1 | M4 grub screw · preload | M4 × 14 headless hex GRUB SCREW (12.1 mm from the back of the spring cup to the mouth of the boss) |
| 2 | M2.5 insert · sensor cover | M2.5 heat-set insert, Ø4.6 × 4.0 mm **M** |
| 1 | M2.5 insert · board post, head end | M2.5 heat-set insert, Ø4.6 × 4.0 mm **M** |
| 2 | M2 insert · board post | M2 heat-set insert, Ø3.6 × 4.0 mm **M** |
| 2 | M3 insert · grip cover | M3 heat-set insert, Ø5.0 × 3.0 mm **M** |
| 1 | M3 insert · clutch grub screw | M3 heat-set insert, Ø5.0 × 3.0 mm **M** |
| 2 | M3 insert · hatch cover | M3 heat-set insert, Ø5.0 × 3.0 mm **M** |
| 3 | M3 insert · panel screw | M3 heat-set insert, Ø5.0 × 3.0 mm **M** |
| 1 | M3 insert · pivot | M3 heat-set insert, Ø5.0 × 3.0 mm **M** |
| 1 | M4 insert · preload screw | M4 heat-set insert, Ø6.3 × 8.1 mm **M** |
| 1 | magnet | Ø8 × 1, **DIAMETRICALLY MAGNETISED** |
| 1 | stepper motor | NEMA 14 14HS10-0404S |
| 1 | preload spring | compression spring, wire 0.9, Ø6.7 outside, 13.5 mm free, 11.1 mm fitted, 5.7 N/mm (the prototype's came from a clothes peg) |
| 1 | M2.5 screw · board | M2.5 × 6, hex socket head (5.5 mm needed under the head) |
| 2 | M2.5 screw · sensor cover | M2.5 × 8, hex socket head (7.0 mm needed under the head) |
| 2 | M2 screw · board | M2 × 6, countersunk head (5.5 mm needed under the head) |
| 2 | M2 screw · AS5600 module | M2 × 4, countersunk head (4.0 mm needed under the head) |
| 2 | M3 screw · collar clamp | M3 × 14, hex socket head (12.4 mm needed under the head) |
| 2 | M3 screw · grip cover, knurled head | M3 × 6, hex socket head (6.0 mm needed under the head) |
| 2 | M3 screw · hatch cover | M3 × 8, countersunk head (8.0 mm needed under the head) |
| 4 | M3 screw · motor | M3 × 8, hex socket head (8.0 mm needed under the head) |
| 3 | M3 screw · panel | M3 × 8, countersunk head (8.0 mm needed under the head) |
| 1 | M3 screw · pivot | M3 × 20, hex socket head (20.0 mm needed under the head) |

## 3. Bought: electronics

### On the board

| Qty | Ref | Part | What exactly |
|---:|---|---|---|
| 1 | U1 | Seeed XIAO ESP32-S3 | native USB-C; FPC antenna on U.FL |
| 1 | U2 | TMC2208 stepstick driver, with its heatsink | 8+8 pin module, Rsense 0.110 Ω (M, marked R110). A TMC2208, not a TMC2209: see pcb/BOM.md |
| 1 | C1 | electrolytic capacitor | 47 µF 63 V, Ø6.35 × 13 mm (M) - bulk at the driver's VM, required, and its place on the board matters |
| 1 | C2 | electrolytic capacitor | 47 µF 63 V - optional, bulk at the 12 V input |
| 1 | R1 | resistor | 10 kΩ ¼ W - pull-up on EN, not in series |
| 1 | R2 | resistor | 1 kΩ ¼ W - in series on TX; leave it out if the driver module already has one |
| 1 | R3 | resistor | 1 kΩ ¼ W - in series with the LED |
| 1 | J1 | JST XH socket, 4 ways | pitch 2.5 - motor phases A± B±, one connector; with its plug |
| 1 | J3 | screw terminal block, 2 ways | pitch 5.08 - 12 V in |
| 1 | J4 | JST XH socket, 4 ways | pitch 2.5 - sensor: SDA, SCL, VCC, GND; with its plug |
| 1 | J5 | JST XH socket, 2 ways | pitch 2.5 - status LED; with its plug |
| 2 |  | female pin strip, 1 × 7 | round pins through both sides, body 3.0 mm - the XIAO's socket |
| 2 |  | female pin strip, 1 × 8 | the driver's socket |
| 1 |  | perfboard | double-sided, pitch 2.54, cut to 70 × 30.3 (24 × 10 holes) |

### Off the board

| Qty | Ref | Part | What exactly |
|---:|---|---|---|
| 1 | U3 | AS5600 magnetic encoder module | round Ø16.85 flattened to 15, a row of 8 pads; needs the VDD5V-VDD3V3 bridge, after which it no longer takes 5 V |
| 1 | C3 | ceramic capacitor | 100 nF (104), 16 V or more - on the module's pads, not on the board |
| 1 | D1 | red LED, 3 mm | outside the board; if it comes pre-wired for 12 V, take its resistor off |
| 1 |  | GX12 connector, 2 pins | panel socket with its nut, and the matching plug for the 12 V lead |

### Cables

| Qty | Ref | Part | What exactly |
|---:|---|---|---|
| 1 |  | CAT5 cable | solid, Ø5.6 - sensor to board |
| 1 |  | USB cable, USB-A to USB-C | 90 degree side elbow at both ends: it goes on and off at every session |
| 2 |  | clip-on ferrites | on the motor lead and the USB cable, two or three turns through each |
