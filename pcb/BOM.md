<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# Electronics parts

The **why** of each choice is in [`../hardware.md`](../hardware.md); the
construction in [`README.md`](README.md).

**The list to buy from is the global bill of materials, [`../BOM.md`](../BOM.md)**:
mechanics and electronics together, generated at every build by
`mechanics/wheelly-cad/src/bom_electronics.py`. This file keeps the reasons. The
references in the tables below (U1, C1, ...) must be the same as in that list.

Dimensions marked **M** are measured with the calliper on a real part. The others
are declared by the maker or assumed, and must be confirmed before anything is
sized on them: in this project four defects came from numbers assumed and never
checked.

## On the board

| Ref. | Component | Value / spec | Size | Notes |
|---|---|---|---|---|
| U1 | Seeed XIAO ESP32-S3 | native USB-C, FPC antenna on U.FL | 21 × 17.8 mm | in a socket, 2 × 7-way 2.54 female strips. Model: see [`../mechanics/others/`](../mechanics/others/README.md) |
| U2 | **TMC2208** stepstick | 8+8 pin format, Rsense **110 mΩ (M)** | to be measured | ⚠️ **not a TMC2209**: see below. **With its heatsink**, in a socket, 2 × 8-way female strips. Model: see [`../mechanics/others/`](../mechanics/others/README.md) |
| C1 | Electrolytic | **47 µF 63 V** | **Ø6.35 × 13 mm (M)** | bulk at the driver's VM — **mandatory**, and its position is a constraint: see README |
| C2 | Electrolytic | 47 µF 63 V | Ø6.35 × 13 mm (M) | optional, bulk at the 12 V input |
| R1 | Resistor | **10 kΩ** 1/4 W | — | EN **pull-up**, *not* in series |
| R2 | Resistor | **1 kΩ** 1/4 W | — | in series on TX. Leave it out if the driver module already has one |
| R3 | Resistor | **1 kΩ** 1/4 W | — | in series with the LED |
| J1 | Phase connector, **4 poles** | JST XH, 2.5 pitch | holes (23,3)…(23,6) | phases A± and B±: **one connector**, not two terminal blocks |
| J3 | 2-pole screw terminal | **5.08 mm** pitch | body ~10 mm, four holes | 12 V input |
| J4 | Sensor connector, 4 poles | JST XH, 2.5 pitch | holes (10,9)…(13,9) | SDA, SCL, VCC, GND |
| J5 | LED connector, 2 poles | JST XH, 2.5 pitch | holes (3,0), (4,0) | LED cable |
| — | Female strip | 1 × 7, round pins through on both sides | insulating body **3.0 mm** | the XIAO's sockets |
| — | Perfboard | double sided, 2.54 pitch | cut to **70 × 30.3 mm** (24 × 10 holes) | cut on the head side so that the USB socket comes flush: see [README](README.md#the-layout-on-the-board) |
| D2 | Schottky 1N5819 | — | — | **not fitted**: only for the buck variant |

### The driver is a TMC2208, not a TMC2209

**Identified on the part**, pulling the module out of its socket and reading
the silicon: the chip is marked **`TMC2208-LA`**, and the two sense resistors are
marked `R110`, that is **0.11 Ω confirmed on the part**. The two modules look
alike: read the chip before trusting the listing, because a 2208 taken for a
2209 shows up as a silent UART.

What changes, and they are not details of naming:

- **a TMC2209-only library rejects the part** — hence `TMCStepper`, see
  `firmware.md`. Rejected: janelia's
  `TMC2209.h` has `const static uint8_t VERSION = 0x21`, and `isCommunicating()`
  compares the `version` field of IOIN with it. A TMC2208 answers **0x20**: even
  wired perfectly and fully alive, that library declares it mute;
- **MS1 and MS2 are not an address.** On the TMC2209 they choose the UART node,
  which is why the wiring ties both to ground; on the TMC2208 they choose the
  microstepping, and the UART has no node address. The ground on MS1/MS2 does no
  harm, but it does not do what it was put there for either;
- **PDN_UART** is not brought out to the header on many 2208 modules, and has to
  be wired by hand to the chip's pad. Check it on your module;
- **no StallGuard.** Wheelly does not use it — the clutch slips by design and the
  AS5600 gives the reference — so it is no loss, but it is written here because
  one day it will look like an available route and it is not;
- **1.4 A maximum** instead of the 2209's 2. Wheelly runs at 0.35 A, so nothing
  changes.

## Off the board

| Ref. | Component | Spec | Notes |
|---|---|---|---|
| U3 | AS5600 module | round Ø16.85 flattened to 15, row of 8 pads | on the wheel's axis, at the end of the cable. Needs the **VDD5V–VDD3V3 bridge**, after which it no longer tolerates 5 V |
| C3 | 100 nF ceramic (`104`), ≥ 16 V | — | **on the module's pads**, not on the board |
| M1 | StepperOnline 14HS10-0404S motor | NEMA14, 0.4 A/phase, 30 Ω, 30 mH, 0.14 N·m | body **26 mm** below the mounting face (M, from the maker's model) |
| — | Magnet | Ø8 × 1 diametral, N42 | centres itself on the Ø7.95 hub; nominal air gap `Gap_nominal`, by default 1.2 mm |
| D1 | 3 mm red LED | off the board | if pre-wired for 12 V, remove its built-in resistor. **Off in operation** |
| — | USB cable | USB-A → USB-C, **90° side elbow** at both ends | plugged and unplugged at every session |
| — | Sensor cable | whole CAT5, Ø5.6 | minimum bend radius assumed 4 × Ø = 22.4 mm — **to be confirmed on the cable's datasheet** |
| — | Clip-on ferrites | — | on the motor cable and on the USB, two or three turns inside the clip |

## Heat-set inserts

Which, how many and where is in the global bill of materials,
[`../BOM.md`](../BOM.md), section 2: the build generates it from the assembly, and
this file does not repeat it. Only what that list does not say is here.

The label convention is **M(thread) × (length) × (outer diameter)**: the length
is in the middle. On the electronics side: the perfboard's standoffs in the
board panel take **2 M2 inserts** (Ø3.6 × 4.0, M) and **1 M2.5** (Ø4.6 × 4.0, M,
at the head end); the sensor cover takes **2 M2.5**.

⚠️ The M3 inserts used are **Ø5.0 × 3.0**. Three millimetres of grip on an M3 are
**barely one diameter**, the practical minimum: it holds, but there is no margin
to spend. A screwed box–collar joint, which would be the most loaded one, was
rejected: box and collar are one part, and the spring pushes with
`Force_spring_N`, by default 13.5 N.

## To be measured or confirmed

- **The height of the JST XH connectors with the cable plugged in**: the model
  holds them at **8.5 mm** (J4, J5) and `H_terminals` = 10 mm (J1, J3), which are
  estimates; the ceiling of the bay and the walls follow from there. The 2.5
  pitch on the 2.54 perfboard is off by 0.12 mm over four ways, which the holes
  absorb;
- **connector bodies** of the GX12, USB-C and antenna: only their **holes** exist
  in the mechanical model, so any "it fits" in that bay holds for the bare board;
- **the driver's size** with its heatsink, split between board, heatsink, socket
  and pins: it tells which one sets the height;
- **the minimum radius of the CAT5**: today it is a rule of the category, not the
  datasheet of the cable in use;
- **how many capacitors** are really fitted: it changes the footprint, especially
  if they are laid down.
