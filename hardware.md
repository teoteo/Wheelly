<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Wheelly — hardware decisions

The reference for the electronics: which parts, why, and the constraints the
circuit must respect. The mechanical dimensions live in the parameters
(`mechanics/wheelly-cad/src/parameters.py`); the construction of the board is in
[`pcb/README.md`](pcb/README.md).

---

## 1. Chosen components

| Function | Component | Notes |
|---|---|---|
| MCU | **Seeed XIAO ESP32-S3** | 3.3 V · native USB-C · 11 GPIO · connectorised FPC antenna |
| Motor driver | **TMC2208** | UART mode. The reference build's module is a 2208, identified from the marking on the chip: the two modules look alike, check yours. The firmware accepts both |
| Motor | **StepperOnline 14HS10-0404S** | NEMA14, bipolar, 4 wires |
| Position sensor | **AS5600 gimbal module** | round Ø16.85 flattened to 15 · chip centred · Ø2.0 holes 11.5 apart, on the axis of the flats |
| Magnet | **Ø8 × 1, diametrically magnetised** | bought separately, not included with the module · Ø8 chosen equal to the Ø7.95 hub: it centres by eye |
| Preload spring | wire 0.9 × Ø6.7 outside × 13.5 free (measured with a calliper; the prototype's comes from a clothes peg) | 5.7 N/mm measured on a scale · **13.5 N** (`Force_spring_N`) at 11.1 mm fitted. It replaces the 0.039" × 0.350" × 0.78" of the first design, ~22.3 N at 12.8 mm |
| Pivot bearings | **2 × F695ZZ, flanged** | Ø13 × Ø5 × 4 · flanges outward, they give the axial reference · Ø5 pivot, Ø21 hub · the 608ZZ was rejected (Ø22 → Ø30 hub, which would end up inside the wheel body) |

---

## 2. Motor — data for the electrical sizing

| | |
|---|---|
| Rated current | 0.40 A/phase |
| Resistance | 30.0 Ω/phase @ 25 °C |
| Inductance | 30.0 mH/phase |
| Rated voltage (0.4 A × 30 Ω) | **12 V** |
| Holding torque | 14 N·cm (140 mN·m) |
| Step | 1.8° — 200 steps/turn |
| Shaft | Ø5 × 20.5 from the mounting face, flat 4.5 over 16.5 |
| Spigot | Ø22 h × 2 mm |
| Fixing holes | 4 × M3 on 26 mm centres |

**Running current: 350 mA** (the factory value in
`firmware/wheelly/wheelly_protocol.h`). It was found by raising it in
steps until the clutch stopped slipping: the test and its table are in
`pcb/README.md`, "Decided: 350 mA". The project started from ~150 mA because of
heat: at 0.4 A the motor would dissipate 9.6 W in a 35 × 26 mm body, that is
+80 °C a few centimetres from the sensor. At 350 mA it dissipates 7.4 W, but only
for the two seconds of a move, because at rest the driver is disabled (below).

**No holding current at rest, by default.** The driver is **disabled** as soon as
a move is over — no heat, no consumption, no chopper noise during an exposure.
The wheel's detent could hold the position (285 mN·m the hard way), but it is
**always** removed when the magnet is fitted (assembly guide, chapter 10): the
motor turns the disc by friction and cannot climb out of the notches. Without the detent the disc, held between the clutch and the body,
may well stay put by itself; if it does not, the firmware sees it (the `drift`
event) and the driver suggests turning the holding current on (`hold`, 150 mA
recommended).

---

## 3. Power

**Decided: 12 V in, and the logic powered from USB.**

**12 V** from the telescope's powerbox, straight to the driver's VM. The driver
would take up to 29 V and 24 V would give more chopper headroom, but at these
speeds it is not needed: the wheel makes five moves a night, not a continuous
motion, and 12 V is already the motor's rated voltage (0.4 A × 30 Ω). In return
the wheel stays on the voltage the powerbox already distributes to everything
else, with no second rail to manage.

**The XIAO is powered over USB from the Raspberry Pi**, the same cable that
carries the data. So **there is no regulator on the board**: no buck, no
dissipation, one component less that can fail in the field and one chance less
to inject noise a few centimetres from the sensor. The two rejected routes were
an MP1584 / LM2596 buck for 12 → 5 V (useless, since USB is there anyway) and a
linear AMS1117, which from 12 to 5 V at 200 mA would dissipate 1.4 W.

A consequence to keep in mind when wiring: **logic and power come from two
different sources**, USB from the Raspberry and 12 V from the powerbox. The
grounds are joined **at a single point**, on the board, near the driver.

**The two sources do not have to be switched on in any order for the driver's
sake: everything can be switched on together.** (For convenience `pcb/README.md`
still prescribes USB first and then 12 V. The firmware does not depend on it: a
driver configured at boot, before the 12 V are there, does not keep the
configuration, so the firmware checks it and **redoes** it when the 12 V arrive
— merely asking whether it had taken would answer no forever.) What makes it safe is a **10 kΩ pull-up between EN
and VIO**, the driver's logic rail. EN is active low, so held high the driver is
off, and it is off whenever the XIAO is not driving that pin: during reset,
during boot, and whenever its GPIOs are high-impedance. The firmware pulls EN
low only to move and raises it again as soon as the move is over — which is what
the project wants anyway, no holding current at rest. The pull-up goes to
**VIO** and not to any 3.3 V: this way, with the powerbox on and the Raspberry
off, the driver's logic stays unpowered and its outputs still.

Without that pull-up the trouble is not a kick to the motor, it is sneakier: the
driver enables itself with STEP and DIR still undefined and starts running a
**holding current nobody asked for**, that is heat and chopper hum a few
centimetres from the cooled sensor. A spurious step from a random edge on STEP is
possible but matters little: it moves the wheel by 1.8° and the AS5600 gives the
reference back.

EN goes on a **GPIO with no boot constraint**: pins with a strapping function
can be forced at power-up.

A fuse, a reverse-polarity diode (the wheel is connected in the dark, in the
field) and a **100 µF** electrolytic at the driver's VM/GND were planned on the
12 V input. **As decided** (`pcb/README.md` and `pcb/BOM.md`): no series diode;
the bulk capacitor is **C1, 47 µF 63 V**, soldered across VM and GND of the
driver's socket, plus an identical, optional **C2** at the input; the Schottky
**D2** is not fitted, it is only for the buck variant. **The fuse does not go on
the board: the powerbox's is enough.** The wheel takes its
12 V from an output of the telescope's powerbox, which is already protected; a
second fuse in series on the perfboard would be one more part to solder and to
fit in the bay, to protect a few centimetres of track. Whoever powers the wheel
from an unprotected source puts one on the cable.

---

## 4. The AS5600 sensor

- I²C address **0x36**, bus up to 1 MHz, 4.7 kΩ pull-ups.
- **Power it at 3.3 V**, not 5 V: at 5 V the logic input threshold is
  0.7 × VDD = 3.5 V, above what the ESP32 can drive. Check with a meter that pins
  1 (VDD5V) and 2 (VDD3V3) are bridged on the module; if they are not, bridge
  them.
- Read **RAW ANGLE** (0x0C–0x0D) and map the positions in software. Do not use
  the BURN commands: they are irreversible and can be repeated only three times.
- Free diagnostics: the MD / ML / MH bits in the STATUS register, the AGC value
  and above all the **magnitude** (see *How the air gap was chosen*).

### Finding the air gap, in practice

`Gap_nominal` = **1.2 mm**, chosen by measurement and not from the datasheet: see
*How the air gap was chosen*, below. What is really adjusted is **the height the
module rests at**, `H_rest_module`; the air gap follows from it,
`H − Th_spacer_magnet − Th_magnet − Th_glue_stack_magnet − H_body_chip`, that is
`H − 0.8 − 1 − 0.5 − 1.63` = `H − 3.93`.

That **0.5** of glue is not theoretical: the spacer + magnet stack is 1.8 by
design, but glued on the hub it **measures 2.3 above the face**. Half a
millimetre goes into the two joints and the printing tolerance of the spacer.
Without counting it the bracket comes out half a millimetre too low: with the
4.0 foot the real air gap was **0.07 mm**, the magnet brushing the chip.

1. Print the **test feet** (`out/tools/gap_gauges.step`; the build prints their
   heights and air gaps on the "gap gauges" line of `solids_tools.py`, derived
   from `H_min_foot_test`, `Pitch_foot_test` and `N_foot_test` — by default
   4.6 → 5.8, that is air gaps from 0.67 to 1.87 glue included; the
   height is engraved on the tab) and the **spacers** (`out/magnet_spacer.step`).
   The feet have the ring over the magnet, the pads and the holes of the real
   bracket, but the outer disc is Ø20: wider than the real hub, which at 14.9
   would be a fragile part to handle. On the side away from the tab they are
   cut straight at r 6.2 and lowered to 0.4 in the band that is left: under the
   module there sits the **104 capacitor**, the tallest component of the module,
   which does not fit in the three tenths the recess leaves — without the relief
   the module rests on it instead of on the pads, and the air gap you measure is
   not the real one. The magnet hole is drawn **8.45** and not 8.15: two tenths
   are the printing compensation (an FDM hole comes out undersize) and one tenth
   is extra play, because the foot has to turn freely on the magnet even if the
   compensation is off. It cannot be widened further: at 8.55 the possible
   off-centre would reach 0.275 and exceed the 0.25 the AS5600 allows — if the
   hole comes out tight, correct `Comp_hole_printing`, not the play. At the
   bottom of the hole there is a 0.3 lead-in cone against the first layer's
   elephant foot, which is exactly where the magnet rests. The two M2 holes are
   also a tenth wider than on the real bracket, **1.9 instead of 1.8**: the same
   screw goes in and out seven times, once per height, and at 1.8 every turn
   recuts the thread in a hole already tapped until the plastic crumbles. In
   the slicer **do not turn on hole compensation as well**, or the two add up.
   After printing, measure the hole with the calliper: `Comp_hole_printing` is a
   number of your printer, not of the project, and from then on it also applies
   to the real bracket, which wants the fit tight.

   **Check the VDD5V–VDD3V3 bridge before trusting any reading.** It is what
   lets the chip run at 3.3 V, and it sits on two small pads that the air-gap
   test strains over and over: the module is screwed and unscrewed once per
   foot, and one pulled solder joint is enough to lift it. With that bridge
   broken the symptom is not silence, and that is what misleads: I²C keeps
   answering, the registers read, the angle follows the magnet — but the Hall
   front end runs under-voltage, the magnitude collapses, the AGC stays wide
   open at 128 and ML lights up. It looks in every way like a magnet too weak,
   and sends you looking on the wrong side. Check: **continuity between pin 1 and
   pin 2**, and 3.3 V between pin 2 and GND with the module powered. Worth doing
   every time a reading gets worse for no reason.

   **The test that tells "no power" from "weak magnet", without a meter:
   disconnect the power wire only** and leave SDA, SCL and GND attached. If the
   readings keep coming unchanged, the chip is powering itself sideways from
   the pull-ups of the data lines through the protection diodes of its pins —
   enough to keep the I²C logic alive, which draws nothing, but not the Hall
   front end, which does. In that case the power is not arriving, however good
   the wires look. If instead `# ! the AS5600 does not answer` appears, the volts
   really are there and the suspicion moves to the magnet. Ten seconds, and it
   halves the tree of hypotheses: without this test, a phantom supply imitates
   a weak magnet perfectly.

   Two **M2 × 4** screws with a parallel thread are needed, countersunk ones
   too: they tap themselves in the 1.8 hole. Longer ones poke out underneath and
   lift the foot off the face. If the hole comes out tight, one pass of a 1.8
   drill. A countersunk head on a module hole without a countersink rests on the
   hole's edge and centres itself: fine, but do not tighten hard.
2. Flash `firmware/air_gap_test/air_gap_test.ino` on an ESP32 — a WROOM-32 will
   do, the XIAO is not needed: `cd firmware && ./flash.sh`, which compiles,
   uploads and opens the monitor. Power the module at **3.3 V**, SDA on GPIO 21,
   SCL on GPIO 22, DIR to ground.
3. **With the wheel already closed**, glue the spacer + magnet stack on the hub,
   on the telescope side, and wait for a full cure before going on: see *Gluing
   the magnet*, below. The hub is aluminium, the magnet does not stay there by
   itself, and once glued it no longer passes through the hole of the cover: it
   is the last thing to be fitted.
4. For each foot: wheel resting telescope side up, foot on the face with its
   ring around the magnet — it centres itself and stays there by gravity —
   module screwed on top, `r` on the serial monitor, **one full turn** of the
   disc by hand (take it by the knurled rim, through the side opening), `s` for
   the summary. More comfortable: `cd firmware && ./gap_page.sh`, which opens
   the test bench in Chrome — live AGC, the sectors of the turn lighting up, and
   the table of the measurements with the recommended air gap already in it.
5. Keep the height with **the highest magnitude** among those with MD on for the
   whole turn and little excursion. Then in the parameter editor:
   `Gap_nominal` = chosen height − 3.93, and `.venv/bin/python build.py` in
   `mechanics/wheelly-cad`.

### How the air gap was chosen

The AGC-at-64 criterion was **rejected**: it does not work, and why is worth
knowing before trying it again. With this magnet and this module, at 3.3 V,
**the AGC stays pinned at 128 — full scale — at any height**, and ML stays on:
the chip says "field below the 30 mT I recommend", and says it always, so it
discriminates nothing. The useful criterion is the **magnitude**, which responds
to the distance monotonically.

Seven tests with the module **screwed down** (merely resting, it lifts, and then
the foot no longer sets the air gap):

| real air gap | mean magnitude | excursion over the turn |
|---|---|---|
| 0.07 mm | 893 | 5.8 % |
| 0.67 mm | 847 | 7.1 % |
| 1.27 mm | 759 | 4.1 % |

Over the whole range the magnitude drops by **15 %**: there is no optimum to hit,
there is a plateau. And every point lies between **2.2 and 2.6 times** the
threshold below which MD goes off, observed around **350**. So the field is not
the constraint, and the air gap is chosen for mechanical reasons: there is a
magnet spinning flush with a fixed chip, and half a millimetre of clearance is
worth more than 5 % of field. Hence **1.2 mm**.

Two things learnt by measuring, which also apply to the final assembly. The
**magnitude along the turn is the measure of the centring**: a modulation that
repeats once per turn is eccentricity. And mind where it is measured — **the
wider the air gap, the less the off-centre shows**, because the far field is
more uniform: measuring the centring at a wide air gap makes it look better than
it is.

If not even the lowest foot gives a magnitude well above the MD threshold, the
Ø8 × 1 magnet is too weak as it is: a thicker one is needed (Ø8 × 2, or a
Ø6 × 2.5).

### Gluing the magnet

**It is glued last, with the wheel already closed.** The magnet is Ø8 and the
hole of the cover the hub turns in is narrower: once it is glued, the wheel no
longer closes. It is the last gesture of the assembly, and from then on the
wheel can only be reopened by unsticking it.

**The hub is aluminium, so the magnet is simply glued.** Not being ferrous, it
does not hold it: there is no way to do the air-gap test dry, you glue first and
test afterwards, once cured. Aluminium is however the right choice for the
AS5600: a ferrous hub would bend the field lines and falsify the reading, while
aluminium is transparent to the field. Since there is no dry run, the centring
must be right the first time: use the gluing cap and check the rim all around
before the glue sets — with slow epoxy there are at least twenty minutes to
adjust.

**Between hub and magnet goes the Ø7.6 × 0.8 spacer** (`out/magnet_spacer.step`).
The hub is flush with the face and the magnet is wider than it: without the
spacer the magnet would rest on the cover, which stands still while it turns.
The friction itself would be negligible — half a gram on a ring 0.025 wide — but
the bead of glue squeezed out of the edge would catch there, and if the disc
hits its axial stop the glue joint becomes the thrust bearing. The spacer is
**deliberately narrower than the hub**, so it cannot touch the cover even if
fitted off centre, and it is plastic: it sits inside the magnet's field.

**Glue: slow two-part epoxy**, 30 minutes or more. Not cyanoacrylate: it grabs
instantly and leaves no time to centre, it is brittle under thermal cycling, and
its vapours fog the optics next to it. Not hot glue, which creeps over time.
Nothing structural is needed: the magnet weighs half a gram and takes no load,
the glue only has to keep it still.

1. Degrease with isopropyl alcohol the top of the hub, both faces of the spacer
   and the face of the magnet.
2. Magnet at the bottom of the cap's seat, **with the face to be glued facing
   out**; ease it down by pushing through the Ø3 hole. The seat is 4 mm deep,
   much more than the stack it holds: the tall wall is needed, or the slightest
   thing tilts it.
3. **Very little glue**, a film, on the exposed face of the magnet; the spacer on
   top; another film on the exposed face of the spacer. The whole stack is glued
   in one go. If there is too much glue it is squeezed out and glues the cap to
   the body: a film of wax or a bit of tape on the face of the cap makes that
   harmless.
4. Rest the cap on the telescope-side face, **centre it on the hub by eye**,
   press and leave it there until cured.
5. Lift the cap off. If the magnet stays in the seat, push it out through the
   Ø3 hole.

**The centring.** The magnet is Ø8.0 and the hub Ø7.95: the magnet is **wider by
0.025 mm each side**. It is not a matter of measuring, but of checking that
nowhere **does the face of the hub show**: centred, the magnet overhangs all
round and the aluminium cannot be seen. As soon as a shiny crescent appears on
one side, the eccentricity has passed 0.025 mm — which is still a tenth of what
the AS5600 allows. It is a yes/no check, not an estimate: nobody judges
0.025 mm by eye even magnified, but the crescent is either there or not, and the
shiny aluminium against the dark nickel of the magnet makes it readable. A 10×
loupe shows it well; even handier is a macro photo with the phone, enlarged at
leisure while the glue is still workable.

**The orientation does not matter**: the magnet is diametral and the zero is set
in software. And **do not heat** to speed up the cure: above roughly 80 °C the
magnet loses strength for good.

**The check comes afterwards, and the sensor does it.** A magnet off centre or
tilted shows as a magnitude that swings along the turn: the test page shows the
excursion. The air gap has nothing to do with it and does not fix it.

- Field required 30–90 mT at the die surface; air gap 0.5–3 mm; maximum offset
  of the rotation axis from the chip centre **0.25 mm**.
- Module dimensions, taken with the calliper: board **round Ø16.85 flattened to
  15**, holes **Ø2.0** on **11.5** centres on the axis of the flats, chip body
  under the board **1.63**, tallest component **0.93**.
- The sensor sits on the **telescope-side face**, and the magnet is right under
  it, on the same face: they are not two different sides. It is glued on top of
  the disc's hub (Ø7.95, flush with the face), with the Ø7.6 × 0.8 spacer in
  between. The printed **gluing cap** keeps the stack flat, square and still
  while the glue sets. The bracket then centres itself, because its ring is
  dimensioned on the magnet (8.15 over 8.0).

---

## 5. Pin budget — XIAO ESP32-S3

Eleven GPIOs available.

| Function | Pins |
|---|---|
| Driver STEP, DIR, EN | 3 |
| Driver UART (single wire through a 1 kΩ resistor) | 1 |
| I²C to the AS5600 (SDA, SCL) | 2 |
| External diagnostic LED | 1 |
| **Total** | **7** |
| Free for DIAG/StallGuard, a button, expansions | 4 |

Avoid the pins with boot constraints. The on-board user LED is on GPIO21, active
low; the diagnostic LED is kept **external** anyway, so that it can be placed and
shielded from the optics. The pin table itself lives in one place, see
`pcb/README.md`.

---

## 6. Connectors and wiring

- **Motor**: 4 poles. The wires leave the box radially, downwards, on the
  telescope side — away from the camera's cable bundle, which leaves on the
  opposite side.
- **Sensor**: 4-pole JST-SH on the module (its lead has one already), but the run
  to the box is **a whole length of CAT5, Ø5–6**, not four wires pulled out of
  the sheath.

  **The reason is electrical, not mechanical.** The AS5600 talks I²C, and over a
  cable I²C is sensitive: what helps is the twisting, and pulling the wires out
  throws it away exactly on the two signals that need it. So the pairs are used
  **coupling each signal with a ground return** — SDA with one ground, SCL with
  the other — instead of taking four wires at random. The price is the bulk: Ø6
  instead of Ø2–3, and the channel is sized on 6, because a cable squashes but
  does not get thinner.

  **The route** leaves the sensor cover along one arm of the bracket, climbs over
  the rear flange of the collar and enters the mechanics bay through the free
  gap between 40° and 56°, on the ring r 86–92 between z 23 and 26 — measured on
  the solids, there is neither box nor collar there. From there it reaches the
  electronics bay the way the motor cable does.

  **A cable clamp is needed at the entry**: the module's pads are the weak link
  of the whole chain, and a cable pulling on the solder joints tears them off
  sooner or later. For the same reason the sensor cover rests **on the arms of
  the bracket and never on the module**: anything pressing on the module from
  above moves `H_rest_module`, that is it **changes the air gap**, the number
  the whole sensor setup is built around.

| pad on the module | goes to | note |
|---|---|---|
| GND | GND | |
| 5V | **3.3 V** | it is the supply pad: it is called 5V, but here the chip runs at 3.3 |
| SDA | I²C data GPIO | |
| SCL | I²C clock GPIO | silk-screened `SOL`, it is SCL |
| DIR | GND | counting direction; tied to ground it is fixed |
| PGO | nothing | the AS5600's programming pin: not connected |
| PWM, GND, 5V (opposite edge) | nothing | three large pads for the analogue output, not needed: it is read over I²C |

**The module is mounted aligned with the arms**, that is turned by 45°, and the
rest of the bracket follows from that. The **104 capacitor** — which sticks out
**4.2 mm** under the board and is also where the cable leaves — goes **in line with
the cable's arm**. There the arm is **widened from 8 to 15 mm** and holed: the
hole does two jobs, room for the capacitor and exit for the cable, and the two
ribs left at the sides, 2.9 wide, bridge over it. Without the widening the hole,
9.2 wide on an 8-wide arm, would cut the arm in two (tried and rejected: the
bracket comes out in two pieces).

The **three large unused pads** (PWM, GND, 5V) then fall on the **opposite arm**,
which is solid material at full height: there a support as tall as the screw
pads is left, and it is the **third point** the module rests on, because on two
pads in a row it could rock and every rock is air gap that changes. The support
**comes out of the hub**: the pads fall at r 7.50 and 7.92 while the hub ends at
7.45, so a pad stopped there would touch none of them. The **six pads in use**
are on the opposite edge, and the wires reach the exit through the capacitor's
hole.

In the bracket the capacitor's hole goes **right through**: the capacitor slips
into it and still stays 0.93 mm from the face of the body.

- **Power**: 12 V.
- **Data**: the XIAO's USB-C to the Raspberry Pi. The firmware exposes a serial
  protocol ([`firmware.md`](firmware.md)); the `indi-wheelly` driver on the host
  only relays it.

---

## 7. Constraints the circuit must respect

**It is built on perfboard**, with point-to-point wiring and strips of
connectors: a printed circuit board may come later, once the prototype has
worked in the field. The constraints below apply to both — they are functional
constraints, not layout ones. On perfboard, however, the ways of failing change:
cold joints, a jumper that lifts, a Dupont crimp that makes contact for the logic
but not for the analogue. They are the first suspects when a measurement gets
worse for no apparent reason — the sensor module's VDD5V–VDD3V3 bridge is the
typical case (section 4).

- **No LED lit in operation.** The unit sits a few centimetres from the cooled
  sensor and inside the optical cone. The diagnostic LED stays off while the
  wheel works and lights only to signal a fault, and can be disabled altogether.
- **No light sources inside the box**: no power LED, no steady indicator.
- Available room: the box spans radius 86 to 122 from the disc centre, over a
  sector of about 114°, with a usable height equal to the 23 mm of the wheel body
  plus what grows towards the camera side.
- The motor is 26 mm tall and sticks out on the camera side; above it there are
  54 mm free up to the camera body.
