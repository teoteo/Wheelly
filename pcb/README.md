<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# The electronics board

How Wheelly's circuit is built, and **why** it is built that way. The choice of
components and their sizing are in [`../hardware.md`](../hardware.md); the
construction is here. The parts list is in [`BOM.md`](BOM.md).

## Constraints that must not be broken

These are the three things that, done wrong, do not give an error but a
malfunction that looks as if it had another cause.

**C1 is soldered across the VM and GND pins of the driver's socket, with its
leads cut short.** The VM → bridge → GND loop is where the current switches with
the steepest edges, and the area of that loop matters more than any shielding
downstream: a centimetre gained there is worth more than half a metre of braid.
It is a constraint that **comes before the size**: laying C1 down away from the
pins to make everything fit in height trades an electrical guarantee for half a
centimetre of room, and it is not worth it.

**One single ground node**, physically on the negative lead of C1. From there a
separate wire goes to each branch: 12 V return, driver power ground, logic
ground. No branch connects to another branch. The typical mistake on perfboard is
to run one ground wire along the whole board and tap it wherever convenient: that
is a chain, not a star, and it puts the logic ground in series with the power
ground. Two distinct mechanisms to avoid — **common impedance** (a shared run has
~1 nH/mm; five centimetres are 50 nH, and with the chopper's edges that is enough
to produce tens of mV that the logic reads as ground) and **loop** (if the two
grounds touch at two points, part of the motor's return goes through the USB
braid and ends up in the camera).

**R1 is a pull-up, not a series resistor.** It holds EN high — driver disabled —
in the first milliseconds after power-up, when the GPIO is still high impedance.
Fitted in series it would keep the driver disabled for good.

## Known traps

**R2 on TX only.** The driver's UART is single-wire: TX goes through 1 kΩ, RX
arrives straight on the same hole. ⚠️ Some driver modules **already** have 1 kΩ in
series on the board: measure the continuity between the header pin and the chip
pin, and if you read ~1 kΩ **leave R2 out**, otherwise 2 kΩ in total stop the
communication.

**C3 sits on the sensor module, not on the board.** The sensor is at the end of
half a metre of cable, which has inductance: the capacitor must be where the
instantaneous charge is needed, on the chip's pins, not before the cable.

**On the AS5600 module in use, pins 1 (VDD5V) and 2 (VDD3V3) of the chip are not
connected**: a bridge is needed to run it at 3.3 V. After the bridge the internal
regulator is bypassed and **the module can no longer be powered at 5 V** — label
it `3V3` on the board or on the cable.

**5.08 mm terminal blocks are ~10 mm wide, that is four holes, not two**: the
pins are two holes apart but the body sticks out by one on each side.

**SOIC-8 numbering**: start from the dot and go anticlockwise seen from above.
With the dot at top left, 1-2-3-4 go down the left side and 5-6-7-8 go **back
up** the right side: the top right pin is 8, not 5.

## The pin table lives in one place

**The board decides which XIAO pin does what, and the firmware follows.** The
single source is [`../mechanics/wheelly-cad/src/wiring.py`](../mechanics/wheelly-cad/src/wiring.py),
the same file that draws the layout and the diagrams in [`schemi/`](schemi/).

| signal | XIAO pin | note |
|---|---|---|
| STEP | D0 | one pulse, one microstep |
| DIR | D1 | direction |
| EN | D3 | active low; 10 kΩ pull-up to VIO |
| UART TX | D8 | through R2, 1 kΩ: the single wire |
| UART RX | D9 | straight onto the same hole |
| SDA | D4 | AS5600 |
| SCL | D5 | AS5600 |
| LED | D10 | through R3 |

⚠️ **Two pin tables drift apart silently.** A firmware table written apart from
the layout can disagree with it on most signals while each half stays
self-consistent, and the symptoms look like unrelated faults: `diag` reports the
driver silent over UART (the firmware talking on D6/D7 while the single wire is
on D8/D9), and EN sits at 0 V (the firmware driving the LED low on D3, which is
EN). Neither half can notice on its own.

So `firmware/test/test_pins.py` reads this drawing and the firmware's
table and fails when they drift. It runs first in `firmware/test/run_all.sh`,
before anything else: until both halves are talking about the same hardware, the
other tests pass and mean nothing.

## Power — decided, not provisional

**12 V in for the motor, logic from USB**, which goes to the camera's built-in
hub. No converter on the board, no diode, and the XIAO's 5V pad stays
unconnected.

A buck was evaluated and **rejected precisely on the criterion that made it
attractive**, interference: an LM2596 switches at ~150 kHz through an inductor
that radiates, and putting it in the same enclosure as the AS5600 adds a noise
source a few centimetres from the sensor. The hub's 5 V are already filtered DC.
It is a trade, not a net gain: a clean sensor and a coupled camera, instead of an
isolated camera and switching on board.

⚠️ **Sequence rule, for convenience: USB first, then 12 V.** It is no longer
needed for the driver's safety (see [`../hardware.md`](../hardware.md), section 3),
but it is the habit the rest of this page assumes.

**WiFi stays off in operation.** With WiFi on, the XIAO rises to 80–120 mA
average with peaks above 300 mA, and those peaks on a hub inside the camera can
drop the camera's own enumeration.

## The driver, and why VREF is no longer a problem

**The module is a TMC2208**, not a TMC2209: read on the silicon with the module
pulled out (`TMC2208-LA`) and confirmed over UART by the `version` field of
IOIN, which is `0x20`. The two sense resistors are marked `R110`: **Rsense =
0.110 Ω, measured on the part**. The parts list says the rest, in
[`BOM.md`](BOM.md).

**The current is set in milliampere, and VREF plays no part any more.** The
firmware turns off `i_scale_analog`, which is on at reset: with that bit on the
trimmer scales the full scale, and the whole current chain hangs on a quarter of
a volt read with a probe. Off, the current comes only from Rsense and IRUN, and
`rms_current(150)` means 150 mA on this board as on one built by someone else.

So: **the trimmer is not adjusted, and does not matter.** Leave it where it is.

### The price, measured with the motor running

⚠️ **It is not a net gain: it is a trade, and the price shows in CS.**
`firmware/motor_test` measured, asking for 150 mA:

| quantity | value |
|---|---|
| current read back from the driver | **122 mA**, not 150 |
| `CS_ACTUAL` while running | **3 / 31** |

The sums add up: with the TMC2208 at `vsense = 1` and Rsense 0.110 the full scale
is (CS+1)/32 × 0.979 A, so CS = 3 gives 122 mA and CS = 4 would give 153.
**There is nothing in between**, and the library rounds down.

At CS = 3 the microstep sine has four levels instead of sixteen: rougher and
noisier motion. **It is not a fault**: the wheel closes the loop on the AS5600
and retries, so it does not need a printer's microstep fidelity. But it is a
choice to make with open eyes — and the next section is what resolved it.

### Decided: 350 mA, and the clutch said so

**Found by trying instead of calculating.**
`firmware/torque_test` climbs in steps from 150 mA to the
motor's rated value, and at each step keeps the motor running for eight seconds
so that a hand can oppose the clutch. The motor itself says which step it is on,
with as many clicks as the step number: whoever tests stays at the wheel, not at
the terminal.

| step | asked | the driver does | `CS_ACTUAL` |
|---|---|---|---|
| 1 | 150 mA | 122 mA | 3 / 31 |
| 2 | 200 mA | 183 mA | 5 / 31 |
| 3 | 250 mA | 244 mA | 7 / 31 |
| 4 | 300 mA | 275 mA | 8 / 31 |
| **5** | **350 mA** | **336 mA** | **10 / 31** |

**At 350 mA the clutch stopped slipping** against the hand, and it is the
firmware's factory value. It was not taken higher: the 14HS10-0404S is rated
400 mA per phase, and fifty are left as margin.

It also cures the low CS, without turning `i_scale_analog` back on: **10 out of
31 instead of 3**, eleven levels of sine instead of four. Smoother and quieter
motion, which is exactly what VREF was after.

**The heat, which must be known**: at 350 mA the motor dissipates
2 × 0.35² × 30 = **7.4 W**. In operation it lasts **the two seconds of a move**,
because the holding current is zero and the motor is released. ⚠️ The sums change
completely for whoever turns the holding current on: there it would be 7.4 W
**forever** a few centimetres from the sensor, which is why the recommended
holding current is **150 mA** (`RECOMMENDED_HOLD_MA`) and not 350.

### How a faulty trimmer is recognised

Still useful even though the trimmer no longer matters: with the board off and the
driver out of its socket, between the two ends you read the nominal value (about
ten kΩ) CONSTANT while turning, and between each end and the wiper a value that
varies and adds up to the nominal. Powered, a wiper reading **outside the range
of its ends** is impossible in a passive divider: it means an open track or a pad
not making contact, and the VREF pin is floating. It also shows because the value
**changes depending on what is powered** — a floating node has no value, it has
whatever it happens to get. And beware of ohm readings in circuit: the meter
finds a path through the chip's silicon and reads kΩ that change with the
trimmer even when the divider hangs off the internal 5 V.

The firmware must handle the **echo** of the single-wire UART: it receives 12
bytes of which the first 4 are its own, only the last 8 are the reply.
`TMCStepper` does it by looking for the sync byte instead of counting bytes.

## Assembly order

1. Female sockets.
2. The power branch only: driver socket, C1, terminal blocks.
3. **Power at 12 V without motor and without XIAO** and check the distribution,
   right up to the VM and GND pins of the driver's socket — solder joints shifted
   by one column give 0 V there, and this is the moment to find them. No
   VREF adjustment: it is no longer needed, see above.
4. Logic: XIAO, resistors, headers, signal wires.
5. Star ground last, checking that every branch starts from the single node.

The two mistakes that burn something — 12 V on the 3V3, motor disconnected while
powered — both belong to the power branch: checking it on its own risks the
driver, not the XIAO as well.

⚠️ **Never unplug the motor with the 12 V on**: it kills the driver instantly.

⚠️ **When switching off the order is reversed: 12 V first, then USB.**

### Checks on the sensor module, before connecting it

| Measurement | Expected |
|---|---|
| chip pin 1 ↔ pin 2 | beeps — the bridge is there |
| pin 2 ↔ pin 3 | silent — the bridge has not spread |
| pin 1 ↔ pin 4 | silent — no supply-to-ground short |
| pad 6 ↔ pads 1, 7, 8 | silent |
| brown ↔ white-brown, with the cable fitted | silent |
| module pad 1 (GND) ↔ pad 7 (GND) | **beeps** — pad 1 is a real ground. On the reference build's module it does. Check yours: if it does NOT beep, pad 1 is not tied to the other grounds on that board, and the DIR jumper below needs a wire from pad 1-2 to pad 7-8 |
| pad 2 (DIR) ↔ pad 7 (GND), after the jumper | beeps — DIR is tied to ground |

C3 goes on **after** the bridge and after the checks, otherwise it falsifies the
continuity readings.

**DIR is tied to GND on the module, not through the cable.** DIR
only sets which way the angle grows, and must not float. A jumper from pad 2
(DIR) to pad 1 (GND) does it at the chip. The cable is then four wires: brown
3V3, white-brown GND, blue SDA, green SCL. The spare conductors (white-green,
white-blue, orange, white-orange) are cut back and insulated at the board end;
white-green may stay soldered to pad 2 at the module end, where the jumper
already ties it to ground. Using the spare whites as extra grounds paired with
SDA and SCL was rejected: small gain on a metre of cable, and three
wires in one crimp contact is a poor joint.

## External cables

| Cable | Rule |
|---|---|
| USB | the XIAO's connector, to the camera's hub. A cable with a **90° side elbow**, plugged and unplugged at every session: the socket must come **flush with the wall**, and on a curved wall the plug's shell does not seat — it goes on a flat wall |
| Sensor | 4 conductors, a cable separate from the motor's; if they cross, **at right angles**; GND paired with the signals |
| Motor | twisted pairs per phase (black+green, red+blue), shielded cable, **braid grounded at one end only**, the board's |
| 12 V | out and return **twisted together** all the way to the supply |
| LED | 2 conductors |

**Clip-on ferrites** on the motor cable where it leaves the box and on the USB
cable at Wheelly's end, two or three turns of cable inside the clip: the
impedance grows with the square of the number of turns. And an **LC EMI filter**
on the 12 V input: if the cooled camera and Wheelly draw from the same
distribution, there is a conduction path independent of USB and of any ground.

The four cables leave from **different edges**. On a smaller board keeping them
apart is harder: it is a cost of shrinking, not a detail.

## Diagrams

The connections are in [`schemi/`](schemi/): they say which pin goes where, not
where the component sits.

Every generated drawing comes in two languages: `en_`, the one the documentation
points at, and `it_`, for an Italian reader with the booklet in hand. The texts
are keys in `mechanics/wheelly-cad/src/texts_drawings_en.py` and
`texts_drawings_it.py`, and the build stops if a word of the other language ends
up in a drawing.

| File | What it shows |
|---|---|
| [`en_wiring-xiao-tmc2209.svg`](schemi/en_wiring-xiao-tmc2209.svg) | MCU ↔ driver, single-wire UART |
| [`en_wiring-xiao-as5600-led.svg`](schemi/en_wiring-xiao-as5600-led.svg) | MCU ↔ sensor and LED, with the sensor cable's colours |
| [`en_wiring-motor-power.svg`](schemi/en_wiring-motor-power.svg) | power branch and phases |

The printed booklet: [`en_wheelly-wiring-diagrams.pdf`](en_wheelly-wiring-diagrams.pdf)
(Italian: `it_wheelly-schemi-montaggio.pdf`).

## The layout on the board

[`en_board-layout.svg`](en_board-layout.svg) (Italian: `it_disposizione-basetta.svg`)
has **two views of the same board**: where each component sits, hole by hole,
and the same components with the **wires**, coloured by net, with the star ground
highlighted and the from→to list of every connection.

**It is not drawn by hand**: the build generates it from
`mechanics/wheelly-cad/src/electronics.py` (where each component sits, the same
source as the envelopes in the mechanical model) and from `src/wiring.py` (the
modules' pinouts and the wires). If a component moves there, both views move with
it, and so does the check that it does not touch the box.

**The XIAO's orientation is verified on the part** (on a photo of the
solder side): the D0–D6 row is on row R8, that is on the side of the wheel's
axis, as the maker's pinout says (USB at the top, D0–D6 on the left) turned with
the USB to the left. The reasoning is at the top of `src/wiring.py`.

The board is a **30 × 70 with 10 × 24 holes**, and it sits in the motor bay.
Columns C0–C23 from the head end (the USB), rows R0–R9 counted from the
**back**: R0 is the printed row "10", R9 is "01", which is on the axis side. The model
counts the way the printed labels do: counted from the axis, a board built
following the labels comes out mirrored, and the USB socket falls one hole off
its slot.
The layout drawing is a true top view, with the head on the left and the axis at
the bottom.

**It is cut on the head side.** The XIAO has its pins on the grid (C0–C6) and its
USB socket must come flush with the outer face of the head: with the whole board,
whose first column is 5.8 mm from the edge (an assumption, not measured), the
socket would stay inside. Cut, the board ends 1.38 mm beyond column C0. The two
fixing holes at that end go with the cut.

**One hole to drill: B05.** That end is held by a third M2.5 socket-head screw,
which bites into a standoff of the board panel. Drill the hole Ø2.7 on the
board's printed grid, at **B05** — second column from the head, row 05, that is
between the XIAO's two rows of pins. It is not a place chosen by eye: it is the
free hole farthest from everything already there, 4.93 mm from the nearest wire
(D0 → STEP) and 7.62 from the nearest pin. Above it, the screw head has 11 mm
before the underside of the XIAO, so it touches nothing. At the sides of the board
two guides of the panel square it; **they do not cover it**, so the board drops in
from above instead of sliding. Two teeth with a lip over the edge were rejected:
the lip printed on supports, a tooth broke in hand, and the board went in
stiffly there.

| zone | holes | why there |
|---|---|---|
| **XIAO** | C0–C6, rows R2 and R8 | the USB socket comes out flush with the head |
| **driver** | C8–C15, rows R2 and R8, power on R8 | above there is room up to the ceiling of the bay: with its heatsink it stands 26.9 mm above the panel |
| **C1** | C17, R8–R9 | just past the driver's end, on the VM and GND side; beside it, it would pass under the driver's board |
| **terminals and headers** | C17–C23 | at the far end, towards the motor; under the arm the room drops to 22 mm |

The pins of every component and every wire are listed in the drawing. R1 has one
end directly above the EN pin and R2 one above D8; the sensor header is under the
I²C pins and the LED's at the very end of the head, where the LED really arrives.

The diagrams in [`schemi/`](schemi/) come from `src/drawing_wiring.py`, which
reads the same holes as `src/wiring.py`: the coordinates they carry are those of
this layout, and can no longer drift from it.

**The driver sets the height**, not the capacitors: laying them down gains
nothing, and C1 stays upright because of the switching-loop constraint.
