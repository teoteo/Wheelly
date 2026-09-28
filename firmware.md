<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Wheelly — firmware decisions

Reference document for the firmware of the XIAO ESP32-S3 and for the `indi-wheelly`
driver. The electronics decisions are in `hardware.md`. The per-property guide to the INDI
panel is in `docs/driver/`.

It describes `firmware/wheelly/` and `driver/indi-wheelly/`. Where this text and the code
disagree, the code wins and this text is the one to fix.

Measured values are marked as such; values taken from the model or a datasheet are marked
**declared**. "The reference wheel" is the specimen the project was developed on: a
manual StarDikor wheel, Ø158 mm, five slots.

---

## 1. The three pieces, and where they split

| piece | where it runs | what it does |
|---|---|---|
| **Firmware** | XIAO ESP32-S3 | closes the AS5600 → motor-driver loop, decides whether it has arrived, keeps the calibration |
| **Protocol** | on the USB cable | the contract between the two. One file, `firmware/wheelly/wheelly_protocol.h`, included by both |
| **`indi-wheelly` driver** | Raspberry Pi, under `indiserver` | translates the protocol into INDI properties. Decides nothing |

Across all three: **every user-facing text is multilingual through keys**, English and
Italian to start with — but not the protocol, which is an interface between machines
(section 13).

The dividing line: **the firmware decides, the driver reports.** The comparison with the
tolerances, the retries and the final verdict are on the XIAO. So the wheel behaves the
same when driven by hand from a serial monitor, and there are no two copies of the same
logic to drift apart.

---

## 2. The starting decisions, and what follows from them

### 2.1 No reduction between disc and magnet → no homing, ever

The AS5600 is an **absolute** encoder over one turn, and the turn it measures is exactly
the turn of the wheel. So at power-up the position is known **before moving**: no search
for zero, no limit switch, no blind start towards a reference.

- **Power can be cut at any moment**, even in the middle of a move, and at power-up the
  wheel knows where it is. If the disc moves while the motor is released, or is turned by
  hand while the wheel is off, it notices — at rest through the drift watch, at power-up by
  reading the angle.
- **The step count is never the truth.** It only estimates how many steps to send; whether
  the wheel has arrived is decided only by the angle read. It is needed anyway, because the
  friction drive can slip.
- **Calibration is a measurement of angles, not of steps**: bring the wheel to where the
  filter is centred, read the angle, store it.

### 2.2 The angles live in the XIAO's NVS, but Ekos sees them and can change them

The wheel is **self-describing**: it knows where its filters are and tells whoever
connects. A reinstalled Raspberry, or another computer, does not lose the calibration.

**One number per slot**: in NVS, for each slot, `angle[i]`, the calibration angle. The
target of `go i` is that angle and nothing else.

**Rejected: a rotation trim on top of the angle** (protocol 1: `offset[i]`, ±45°, NVS keys
`o1`…`o12`, commands `offset`, `offsets`, `clear-offsets`; the target was
`angle[i] + offset[i]`). It was meant to allow resetting to the original calibration and to
show, as diagnostics, a trim growing night after night. It was removed because:

- **the angle is editable in the panel, with a Set**, and a Set on the angle of the slot the
  wheel stands on moves it there at once — it *is* the live trim, done on the one number
  that counts, so two fields per slot did the same job twice;
- **an angle set and not saved is lost at a restart, as the trim was**: `angle` writes
  working memory and only `save` writes NVS, so experimenting without spoiling the good
  calibration still costs nothing;
- **the history is kept better by the driver**: every angle change is written in the log
  and in the movement register (`wheelly_movements.csv`), "slot 2: 122.87° → 123.10°", with
  its date — a single trim value showed only the last state, not whether it had been
  growing.

Removing it changed the protocol (version 2, `wheelly_protocol.h`). A wheel saved by a
protocol-1 firmware keeps its trims in NVS: **at the first start of the new firmware each
non-zero trim is added to its angle, the angle is written back and the trim's key erased**,
once (`Wheel::fold_old_trims()`), so every slot stays where it was. The bench tries it with
the keys of an older wheel, started one, two and three times.

The **filter names** are in NVS too: a few hundred bytes, and a wheel connected to a new
computer shows up with the right names. So are the **number of slots** (section 5.1, "The
wheel says how many slots it has"), the tolerances, the motor settings, the holding
current, the direction of travel, the settling wait, the drive ratio and the LED mode:
everything `save` writes (see `Wheel::save()`).

### 2.3 Out of position: two thresholds, not one

| residual error | what happens |
|---|---|
| ≤ `good` tolerance (0.30° by default, `FACTORY_GOOD_DEG`) | success, nothing to report |
| between `good` and `warn` (0.80° by default, `FACTORY_WARN_DEG`) | **warns in the log** and still declares success: the sequence goes on |
| > `warn` | **retries** on its own, up to `retries` times (3 by default) |
| still outside after the retries, or past the time cap | **declared failure**: the sequence stops, no exposure |

The two thresholds and the number of retries are editable in Ekos (`WHEELLY_TOLERANCE`),
not compiled constants. The firmware accepts `0 < good ≤ warn ≤ 45` and retries `0..20`.

**Why 0.30° and 0.80°.** A speed test on the reference wheel without its detent
(`firmware/speed_test.py`) measured final errors below 0.15° on four slots out of five at
every speed: 0.30° keeps twice that margin, and 0.80° still lets a leg the tyre swallowed
end as a warning. 1° of disc moves a filter about 0.9 mm at a filter circle radius of
~50 mm (estimated, not measured). Rejected: 0.10° / 0.50°, proposed before the wheel was
assembled — the TPU tyre absorbs the last ~0.6–1.0° of a leg (measured), so 0.10° chased an
error the drive cannot resolve. Wheels that already saved their tolerances keep them (NVS,
no migration). Tighter values remain an option once the movement log shows the real errors
in the field.

**Why this is enough to prevent the exposure.** It is the standard INDI mechanism, with no
private agreement with Ekos: `FILTER_SLOT` stays `Busy` for the whole move and Ekos waits
without exposing; at the end it becomes `Ok` if the wheel arrived, or `Alert` if it did not
— and on `Alert` Ekos aborts the capture sequence. The middle band becomes `Ok` plus a
warning line in the log: "report but proceed".

### 2.4 Holding current at rest: off by default, but not for every wheel

Once a move is over the motor driver is **disabled**: no current, no heat a few centimetres
from the cooled sensor, no chopper hum during the exposure, no consumption. **That is the
default.**

The manual wheel's own **detent** — the spring click stop, 285 mN·m in the hard direction
on the reference wheel (measured) — is **always removed** (assembly guide, chapter 10): the
motor drives the disc by friction, through the clutch, and cannot climb out of the notches;
on an asymmetric detent it stalls and hums against the steep flank. Without it, the disc
pressed between the clutch tyre and the body usually stays put by itself, but a cable
pulling, or the telescope's tilt changing during the night, can turn it. So holding is **an
option, not a compiled constant**, and whether a wheel needs it is seen on the wheel: the
drift watch says so.

| setting | what happens |
|---|---|
| `hold 0` (**default**) | the driver is disabled at the end of the move (EN high, coils freewheeling). Zero current |
| `hold N` (mA) | the driver stays enabled with a holding current of N mA |

**The chip already does it well.** The TMC2208 has two separate currents, run (`IRUN`) and
hold (`IHOLD`). The firmware sets the run current in milliamperes with
`rms_current(mA, ratio)` and derives `IHOLD` as the ratio hold/run, so a holding current
higher than the run current cannot be asked for by construction (the firmware also refuses
`hold` above the run current). The chip's own delay for dropping from run to hold current
(`TPOWERDOWN`) is left at its default.

The **recommended** value is `RECOMMENDED_HOLD_MA = 150` mA (`wheelly_protocol.h`). It is
not the 350 mA of the run current, because **a move lasts two seconds, holding lasts all
night**: at 350 mA it would be 7.4 W forever, a few centimetres from a magnetic sensor and a
cooled camera; at 150 mA it is 1.35 W.

**Whoever turns it on buys** continuous heat next to the sensor, a consumption that never
stops, and the chopper singing through the exposure — what `hardware.md` wanted to avoid.
The firmware prints a `#` warning line whenever a non-zero holding current is set, and the
driver passes it on.

A wheel that moves at rest by itself is reported (the `drift` event, section 4.6), and the
driver's log then suggests turning holding on, with the recommended value — or, if holding
is already on, says that it is not enough. That is the single guidance.

**Rejected: a `detent yes|no` setting** (`WHEELLY_DETENT`), with a warning for "no detent
and no holding current". With the detent always removed the setting had one right value,
and the warning would have sounded at every connection of every wheel — a warning that
always sounds is no longer read. A wheel that saved the flag keeps an NVS key `detent` that
nobody reads; a driver that still sends `detent` gets `ERR_UNKNOWN_COMMAND`, and its switch
goes to Alert — nothing else.

---

## 3. The positioning state machine

```
        ┌──────────┐
        │  IDLE    │  driver disabled, no current (or holding current, if set)
        └────┬─────┘
             │ command "go to slot i"
             ▼
      ┌─────────────┐
      │  ENABLE     │  EN low
      └──────┬──────┘
             ▼
   ┌────────────────────┐
   │  MOVE (estimate)   │◄──────────┐  steps = (target − read) × steps/degree
   └─────────┬──────────┘           │  the shortest way (default) or one way only
             ▼                      │
   ┌────────────────────┐           │
   │  SETTLE AND READ   │           │  `settle` wait (300 ms) at the run current,
   │                    │           │  then the mean of 8 readings
   └─────────┬──────────┘           │
             ▼                      │
        residual error?             │
             │                      │
   ≤ good ───┼── ≤ warn             │
      │      │      │               │
      │      │   warns              │
      ▼      ▼      ▼               │
   ┌────────────────────┐           │
   │  RELEASE           │           │  EN high, no current — or the
   └─────────┬──────────┘           │  holding current, if one is set
             ▼                      │
          SUCCESS                   │
                                    │
   > warn, retries left, within cap ┘

   > warn, no retries left or past the time cap → RELEASE → FAILED
```

In the code (`wheel.cpp`) the states are `IDLE`, `MOVING`, `SETTLING`, `FAILED`, reported
on the wire as `idle`, `moving`, `settling`, `failed`.

Two details that are paid for at the bench if they are missing:

- The **settling** wait before reading again (`settle`, 300 ms by default). The disc has
  inertia and the clutch's tyre gives back a little; reading right after the last step gives
  an angle that then changes on its own. **The motor stays energised at the run current for
  the whole wait**, and is released only after the verdict: see "The hold after arrival"
  below.
- The **mean of several readings** (`READINGS_PER_MEASURE = 8`), not one. The AS5600 has a
  few LSB of noise, and at 4096 counts per turn one LSB is 0.088°: the scale of the
  tolerances. The mean is taken on the circle (sine and cosine): between 359° and 1° an
  arithmetic mean would give 180°.

### Which way round

**The shortest way by default, one way as an option** (`direction`, kept by `save` under
its own NVS key). The backlash is not compensated, it is **measured and corrected**,
because the encoder is downstream of the friction drive — so the direction of arrival does
not matter to the precision, and the shortest way saves up to half a turn.

| setting | what happens |
|---|---|
| `up` | every move and every retry towards increasing angles |
| `down` | every move and every retry towards decreasing angles |
| `shortest` (**factory default**) | the shortest way round, either way |

The factory default is one constant, `FACTORY_DIRECTION` in `wheelly_protocol.h`, read by
the firmware, the simulator and the driver's panel.

**`up` and `down` exist for a mechanism that turns more stiffly one way than the other.**
With the reference wheel's asymmetric detent still fitted (285 mN·m on the steep flank,
section 2.4), going up the motor stalled at every notch (about 51°, 123°, 195°, 267° and
339°, measured) and going down it passed them all; going the shortest way, half the moves
climbed that flank. Without the detent the speed test (`firmware/speed_test.py`) arrived
every time, at every speed from 100 to 1000 full steps/s, in two legs the shortest way.
With nothing to stall against, one way only costs time: a move can be nearly a whole turn
instead of at most half, and the move time cap at the factory speed goes from 12.1 to
15.8 s.

**The DIR pin is inverted, by design** (`MechanicsEsp32::begin()`,
`setDirectionPin(dir, false)`). With J1 wired as in the assembly guide — black A+, green
A−, red B+, blue B− — and the sensor looking down on the magnet, positive steps turn the
disc towards **decreasing** angle: uninverted, every leg moves away from its target by about
0.9 of the length asked, and looks like a stall. It is a fact of the design, not of one
wheel, so the firmware inverts the pin. **Whoever wires J1 the other way round (one phase
swapped) must flip that `false` too**, or every move runs away from its target. The Mac
bench cannot see it: its fake mechanics has no pin.

**One way only, the retries go the same way too**: after an overshoot the wheel goes round
(360° − overshoot) instead of backing up the few degrees. A wheel already within the good
tolerance of its target does not move at all: a hair past the target would otherwise cost
a turn. The verdict, as always, is the angle read, not the steps counted.

**One way only, every leg aims short** (`Wheel::start_leg()`). Without it, the whole turn
after an overshoot overshoots again by the same few percent, round and round, and ends
"not reached". So each leg stops **12 %** of the distance short of the target (at least 1°),
and within 2° it goes 60 % of the way: the next legs creep in. The 12 % must be more than
the step estimate can be off: the factory ratio is declared from the model, so ±10 % is
allowed for (on the reference wheel legs moved 0.84–0.92 of the estimate, measured: short,
the safe side). The shortest way does not aim short: an overshoot there is a small step
back.

### The lost motion

**Every leg also sends the lost motion** (`m_lost`). With the aim short alone the disc
stopped 0.6–1.0° short of the target and the small creep legs did not close it: the
clutch's TPU tyre absorbs about 15 microsteps — 0.6° of disc (measured) — before the disc
turns, and with the motor released at rest it gives them back, so every leg loses them
again. Each leg sends that much more than it wants, and the amount is **learnt** from the
short legs (< 5°): what was sent minus what the disc did. A short leg that did not move at
all says only that the loss is larger than what it was sent: the next one sends 0.2° more
(at most half the good tolerance, so that it cannot land past it), up to 2°, and those legs
are taking up the play, not stalls (they are approach legs). It starts at zero, so a drive
without that play is never pushed past its target, and it is kept from one positioning to
the next, in RAM. The Mac bench and the simulator model the play (`--lost-motion`, 0.6° by
default) together with the ratio error (`--ratio-error`, −10 %).

### Approach legs, retries and the boost

**Approach legs are not retries.** A leg that moved towards the target and did not pass it
is followed by an *approach leg*, up to 10 of them, which do not use up the retries (also
inside the warning band: going on costs a fraction of a second). A **retry** is the leg
after one that made **no progress** (less than 20 % of what it aimed at: a stall, the clutch
slipping) or **went past the target**. Counted as retries, the approach legs made a wheel
that was converging end "failed" or "warning" at `retries=3`. Whether a leg went past or
back is judged on the distance still to go the way it turns: if it grew, the smaller of the
two movements (past the target, or back) is what happened. `status` reports every leg in
`legs`.

**The boost after a stall.** A leg that wanted to move and made no progress — less than
20 % of its aim, not while taking up the play, judged on the angle read because the TMC2208
has no StallGuard — has most likely stalled against a notch or a stiff point. The **next
leg**, whatever it is, runs at **twice the speed and the acceleration**, at most
`BOOST_SPEED_MAX` = 1000 steps/s (and never above the protocol's limits), to break out; the
legs after it go back to the set speed. It is still a retry. `status` counts the boosted
legs of the positioning in `boosts`. The bench and the simulator have a notch that stalls a
slow motor (`--notch-at`, `--notch-min-speed`) to test it.

### The steps

`steps_per_degree(ratio)` (`wheel.h`) counts **microsteps** of motor per degree of disc:
200 steps × 16 microsteps per motor turn, times the drive ratio in use (below).
`Mechanics::move()` takes microsteps, and `MechanicsEsp32::move()` must not multiply them by
16 again: a firmware that did made every move on the real wheel sixteen times its estimate,
and the Mac bench could not see it, because its fake mechanics turned steps back into
degrees with the same constant. So the bench has its own physics (motor, microstepping,
clutch and disc diameters written separately, then off by `--ratio-error`, −10 % by default
as on the reference wheel), a clean move must arrive with no retries — a wrong unit
overshoots or stalls, which is a retry — and `firmware/test/test_units.py` reads
`MechanicsEsp32::move()` to keep it from multiplying again.

### The drive ratio

How many degrees of motor make one degree of disc. The motor drives the disc by friction —
a TPU tyre on the clutch pressing on the knurled rim — so the ratio is the rim's diameter
over the diameter the tyre **really** rolls on, squashed by the spring and sunk in the
knurl: a fact of each wheel, not of the drawing. What depends on one wheel's mechanics is an
option with a default, so it is a **setting**:

- **the factory value is the model's**, `FACTORY_DRIVE_RATIO` = `MODEL_DISC_DIAMETER_MM /
  MODEL_CLUTCH_DIAMETER_MM` = 145 / 50 = **2.90**, derived in `wheelly_protocol.h`, not
  typed; the disc's 145 is a calliper reading (`Disc_rotating`, measured), the clutch's 50
  the design's (`D_clutch`, set). `test_units.py` reads the CAD's `parameters.py` and fails
  if the header's two diameters drift from it. **Status: DECLARED from the model, not
  measured** — on the reference wheel legs moved 0.84–0.92 of the estimate, so the true
  ratio is likely 3.1–3.4; it stays declared until `firmware/ratio_test.py` has been run on
  the wheel. As long as it is off by less than the 12 % the one-way legs aim short, it only
  affects how many legs a move takes, not where the wheel stops;
- `ratio <value>` sets the **base** the wheel starts from (range 1–10: it only catches a
  typo, a wheel with another clutch may be far from 2.9), in working memory until `save`,
  and restarts the learning from it; refused while moving;
- **it is learnt in use**, `ratio learn on|off`, on by default and kept by `save`; the base
  refined by the learning is the ratio **in use**.

**Measuring it: `firmware/ratio_test.py`**, modelled on `speed_test.py`: on the computer the
wheel is plugged into, Ekos disconnected, nothing saved unless `--apply`, the speed and the
leg report put back at the end. It turns on the `! leg` report (`legs on`), takes up the
play with a first move, then six jogs up of 60 and 150 degrees alternated at 200 full
steps/s, then the same down, and keeps each jog's **first** leg. The ratio is motor degrees
over disc degrees, but not leg by leg: every leg pays the tyre's play (about 0.6° of disc,
1.7° of motor) before the disc moves, 1–3 % of a leg; so the two lengths give a straight
line (disc, motor) whose **slope is the ratio and intercept the play**. One direction at a
time after taking up the backlash, because a leg after a reversal carries the play on both
sides of the tyre; slow, because a slipping leg reads as a higher ratio. It prints each
direction's ratio, spread and play, the suggested value (their mean), writes a dated CSV
(default `~/Documents`, `--out`), and with `--apply` sends `ratio <value>` and `save` —
which saves everything the wheel holds, as the panel's "Save to the wheel". On the simulator
(true ratio 2.9 / 0.9 = 3.2222) it read **3.2230** both ways, spread 0.04 %; on the Mac
bench with the disc 5 % long and 1° of play (true 2.7619) **2.7616**, play 2.90–3.02 motor
degrees against 2.90.

**Why it learns.** The ratio of a friction drive is not a constant even on one wheel — the
tyre wears, the spring settles, the TPU is stiffer cold than warm, and an observatory spans
30 °C in a year; a measured value is right the day it is measured. Every long leg is a free
measurement: with the disc 10 % short of the estimate a move takes three legs, learnt it
takes two, then one; fewer legs are fewer settling pauses and less wear on the tyre. It also
makes the measurement optional for whoever builds a wheel and never runs the script.

**The case against, and the guards that answer it.** A first version learnt from every long
leg without guards and was rejected: a leg cut short (by a notch of the detent) taught a
ratio 40 % low, and the next legs went past the target. A value that changes by itself also
makes the wheel's behaviour depend on its history; the aim short and the approach legs
already absorb ±10 %, so the gain is time, not arrival; and a wrong learnt value saved by
accident would be carried across restarts. So (`Wheel::judge()`, `LEARN_*` in `wheel.cpp`):

- a leg teaches only if it is the **first** leg of a **`go`** — not a jog (centring by
  hand), not an approach leg (short, from a disc just stopped), not a retry (after a stall
  or an overshoot);
- it wanted **at least 30°** (`LEARN_MIN_DEG`: the play is 2 % of that, one sensor count
  0.3 %);
- **the play is known**: a short leg that moved has been judged since the start; before
  that, what the leg sent on top of its aim was a guess;
- it **progressed**, and the **magnet was seen at every reading** while it ran;
- what it says is **within 15 %** of the ratio in use (`LEARN_OUTLIER`): a leg cut short by
  a third is thrown away, not averaged in;
- it goes in with **weight 0.25** (`LEARN_WEIGHT`: a leg 10 % off moves the ratio by 2.5 %),
  and the ratio in use is kept **within 15 % of the base** (`LEARN_CLAMP`): a wheel further
  off must be measured and set with `ratio`, because learning refines, it does not
  calibrate;
- the play (`m_lost`) is kept in steps when the ratio changes;
- **the learnt ratio is saved only by `save`**, never by itself: `save` is the explicit
  gesture for everything else, and a value that wrote itself to flash would change what the
  wheel does after a restart without anyone asking. A restart goes back to the base; `save`
  writes the ratio in use, which becomes the new base; `ratio` shows both, and how many legs
  it was learnt from (`learnt=`). `ratio learn off` drops the refinement (the base alone,
  one known number), it does not freeze it.

The tests put the simulator and the Mac bench, whose discs go 10 % short, through fifteen
moves: both learn 3.216 against the true 3.222 and the moves shrink from three legs to two,
then one; with learning off they stay at three. A leg cut short by a notch at 60 % and at
80 % of its way, a stalled first leg, a long jog, the first move (play unknown) and a leg
run while the magnet flickered all teach nothing, nor does a first leg under 30° or the long
retry after a cut; every guard removed on purpose, in the firmware and in the simulator,
made its test fail. What no bench can see: that `save` really writes the key — the benches
do not restart after a save; it is read in `Wheel::save()`, and the loading of a saved ratio
is tested from a seeded memory (`--nvs ratio=3.3,ratio_learn=0`).

### The time cap

The whole positioning, retries included, has a cap; past it the firmware stops retrying and
declares failure itself, under the 30 s after which Ekos gives up by itself (section 5.3).
A fixed number is either too short for a slow motor or pointlessly long for a fast one, and
one way round the longest path is nearly two turns instead of half of one, so the cap is
**derived** (`Wheel::ceiling_ms()`; rejected: a fixed 25 s, `CEILING_MS`): the longest path
— 180° the shortest way, 720° one way (just under a turn, then one retry round; the approach
legs share the same distance) — as one trapezoidal move at the set speed and acceleration,
plus each leg's own ramps and the settling wait (`settle`) for the first move, the up to 10
approach legs and every retry, times 1.25, plus 1 s.

It travels in the replies of `direction`, `motor`, `settle` and `ratio` as `ceiling=` (ms).
The path is counted at the **base** ratio, not the learnt one, so the number the driver
holds does not move by itself with every leg learnt (the learnt one stays within 15 % of the
base, and the 25 % margin covers it). The driver's own cap is the wheel's plus 3 s (28 s with
a firmware that does not say it), and the driver **warns in the log** when the wheel's cap is
past Ekos's 30 s — at connection, and when the direction or the motor speed is set.

### Speed

**Speed is in full steps per second.** 200 steps/s is one motor turn per second, which the
2.9 ratio makes about **124° of disc per second**. The factory value is **300 steps/s with
1200 steps/s²** (`FACTORY_SPEED`, `FACTORY_ACCEL` in `wheelly_protocol.h`), about 186°/s.

**Slower is not gentler.** On the reference wheel with its detent (measured, 400 mA, one way
down), at 50 steps/s (about 31°/s) the motor stalled and vibrated at some notches even the
easy way, while 100, 150, 200, 300, 400, 700 and 1000 all arrived — 1–2.5 s per slot in 2–4
legs, with no trend in the final error. The motor's datasheet pull-out curve (24 V, 0.4 A,
half step) starts only at 500 half steps/s, i.e. 75 rpm = 250 full steps/s: below that is a
weak zone the datasheet does not even draw. With 3 retries and up to 10 approach legs, the
caps are:

| speed / acceleration | shortest way | one way |
|---|---|---|
| 300 / 1200 (default) | 12.1 s | 15.8 s |
| 200 / 800 | 12.8 s | 18.2 s |
| 50 / 300 | 16.6 s | 38.4 s — past Ekos's 30 s, the driver warns |

These are worst cases, every approach leg and retry used: a clean one-way move takes five or
six legs.

### The hold after arrival

After every leg the motor stays energised **at the run current** for `settle` ms (300 by
default) before the angle is read and the motor released, **even with the holding current
at rest at 0**: the drive is by friction, and a stopped motor that is still energised holds
the TPU tyre, which brakes the disc; released at once, the disc's inertia could carry it on.

- the wait is a **setting**, `settle [ms]`, factory value `FACTORY_SETTLE_MS` = 300 in
  `wheelly_protocol.h`, range `0..SETTLE_MS_MAX` = 2000, kept by `save` under the NVS key
  `settle_ms` (a wheel saved without it gets the factory 300). A heavier disc or a softer
  tyre may want longer. **0** reads and releases at once — allowed, but the readings are then
  taken with the disc still ringing, and the approach legs pay for it;
- **the run current is guaranteed for the whole wait**, whatever its length:
  `Wheel::start_positioning()` sets the driver's hold current to the run current, and
  `release()` puts the real one back (disable first, then IHOLD 0, so the coils never
  freewheel with EN still low). Without it the TMC2208 itself drops to its hold current
  `TPOWERDOWN` after the last step — 20 × 2¹⁸ clocks at 12 MHz = **0.44 s** by default — so a
  300 ms wait held by accident, but a 500 ms wait with the hold at 0 would let the coils
  freewheel half way through (`freewheel` is on at IHOLD 0). **Why the run current and not
  the holding one**: the motor has just stopped at it, so there is no step in torque at the
  moment it matters; the hold current is chosen for a whole night (150 mA recommended, 0 by
  default), and at 0 it would hold nothing; the price is 300 ms of 350 mA per leg, a
  fraction of the move it ends;
- the **verdict is read at the end of the wait**: a disc that went on moving during it is
  judged where it stopped, and the normal approach legs and retries apply. What happens after
  the release is the drift watch's;
- **every leg** waits, not only the last: the firmware cannot know a leg is the last before
  reading where it ended. So a move takes `settle` × legs longer (a clean move is 2–4 legs:
  300 ms → +0.6–1.2 s against 0), and the **move time cap counts it** once per leg: at the
  factory speed, the shortest way, 6.9 s at 0 ms, 12.1 s at 300, 24.4 s at 1000, 41.9 s at
  2000 — past Ekos's 30 s, and the driver warns. The reply of `settle` carries `ceiling=`, so
  the driver's own cap follows it.

The benches model the disc's inertia (`--coast DEG`, `--coast-ms MS`): a disc let go — EN
high, or the current dropping below the run current, which the fake chip does by itself
0.44 s after the last step when the hold is lower — sooner than `coast-ms` after it stopped
slides on by `coast` degrees. With `--coast 1.5 --coast-ms 200` and the hold at 0, 300 ms
keep the disc on its slot, and 0 lets it slide past the warning tolerance (drift event);
with `--coast-ms 1000` a 1.2 s wait arrives with no retry. Each part was broken on purpose,
in the firmware and in the simulator — the run current not raised during the positioning,
the motor released at the stop, the wait fixed at 300, the cap without it, the saved value
not loaded, the range not checked — and the tests failed every time.

### The drift watch

**At rest the firmware keeps watching.** While idle it reads the angle continuously; if the
wheel moves beyond the `warn` tolerance without being asked, it sends a `drift` event, once
per episode (section 4.6). Nothing is watched before the first positioning: until someone
asks for a slot there is no target to drift from.

---

## 4. The protocol

### 4.1 What was learnt from frankenwheely

The abandoned project by Kari Brown (2017-18), firmware and INDI driver, was read in full.
Out of it come **an idea to take, a trap to avoid and a confirmation**.

**The idea: a single protocol definition file, compiled by both sides.** There, the list of
commands is in a header compiled identically on the microcontroller and in the Linux driver.
It removes *by construction* the most annoying class of bugs to chase, firmware and driver
disagreeing on what a message means. Here the same is done with `wheelly_protocol.h`.

**The trap: depending on unsolicited messages.** Its firmware sends a notification when a
move is over, and the driver *counts on it*. But before every command the driver did
`tcflush(TCIOFLUSH)`, throwing away input not yet read: a command sent at the wrong moment
erased the notification, and the host waited forever for something that had already arrived
and that it had thrown away itself. The rule here: **unsolicited events are a luxury, not the
truth.** The state can always be asked for, and asking always gives the right answer.

**The confirmation: the shortest way round.** It too, with five slots, chooses the direction
by which way round is shorter.

**What is not needed: the double forward/backward offset.** Frankenwheely keeps two
calibrations per filter, one per direction of arrival, to compensate for the belt's backlash.
It knows the position only roughly, from four Hall sensors that say only *which* filter, and
does the fine centring by **counting steps open-loop** — so it cannot see the backlash and
has to calibrate it. Wheelly has the true angle, downstream of the friction drive, with 4096
counts per turn: one angle per slot.

### 4.2 Text, not binary

Frankenwheely uses binary frames with a checksum. For a real serial line, with noise, that is
the right choice. **Not here**, for two reasons.

**The link is not a serial line**: it is USB CDC. USB already has its 16-bit CRC per packet and
automatic retransmission in hardware. An application checksum over a channel that is already
reliable protects against a fault that does not exist, and costs the ability to read what goes
through. Bandwidth is not an argument: the wheel changes filter a handful of times a night.

**This project is debugged by hand.** A fault behind the AS5600 module's VDD5V–VDD3V3 jumper
was found by opening a serial monitor and looking at the numbers; with a binary protocol it
would have stayed hidden. A text protocol can be read in the monitor, typed by hand to try
something, pasted into a message, kept in a log that is still readable in six months.
**Readability is a feature.**

### 4.3 Named fields, not positional ones

Answers are not lists of numbers in an order to remember, but `key=value`:

```
ok pos=3 angle=144.44 target=144.45 err=-0.01 motion=idle retries=0 ...
```

It costs a few bytes and buys two things. It can be read without the manual at hand. And
**adding a field breaks nothing**: an old driver that meets a field it does not know ignores
it, instead of shifting by one and misreading everything after. With firmware and driver
updated at different times, it is the property that matters most. That is also why adding a
field, a command or an event does not raise `PROTOCOL_VERSION` (currently 2), while changing
or removing a word does.

Numbers use **the decimal point**: it is a machine format.

### 4.4 Four kinds of line, told apart by the first characters

| starts with | what it is |
|---|---|
| `ok` | positive outcome of a command, with its fields |
| `error` | negative outcome, with code, fields and explanation |
| `#` | comment or diagnostics: informative, never required |
| `!` | **unsolicited event**, not asked for by any command |

Every command produces **exactly one** `ok` or `error` line, possibly preceded by `#` lines.
So the driver always knows when it has finished reading: it waits for the first line that
does not start with `#` or `!`. An empty line is not a command and gets no answer. A line
longer than `WHEELLY_LINE_MAX` (512 bytes) is not executed by halves: it is answered with
`error 2 ... line too long`.

### 4.5 The commands

One per line, terminated by `\n` (a `\r` is ignored). Words are separated by spaces.

**The words are in English**: they are identifiers, that is code, meant to be read by whoever
builds the wheel elsewhere and opens a serial monitor. They are defined once, in
`wheelly_protocol.h`, and executed in `dialog.cpp`.

| command | arguments | answer |
|---|---|---|
| `version` | — | `name fw proto serial slots` |
| `status` | — | the whole state, see below |
| `go` | `<slot>` | `target from dir` — asynchronous |
| `stop` | — | `ok` |
| `jog` | `<degrees>`, at most ±180 | `target from dir` — asynchronous, as `go` |
| `angles` · `names` | — | `a1=… a2=…` · `n1=…`, one per slot |
| `angle` | `<slot> <degrees>`, 0 … 360 | `a<slot>=…` — does not move the wheel |
| `name` | `<slot> <text>` | `n<slot>=…` |
| `teach` | `<slot>` | `a<slot>=…` |
| `save` | — | `saved=nvs` |
| `slots` | `[<n>]` | `slots=…` |
| `tolerance` | `[<good> <warn> <retries>]` | `good warn retries` |
| `motor` | `[<mA> [<speed> <accel>]]` | `ma speed accel ceiling` |
| `hold` | `[<mA>]` | `ma` |
| `settle` | `[<ms>]` | `ms ceiling` |
| `direction` | `[shortest\|up\|down]` | `direction ceiling` |
| `ratio` | `[<value>]` or `learn on\|off` | `ratio base factory learn learnt ceiling` |
| `legs` | `[on\|off]` | `report` — the `! leg` events, off at start |
| `led` | `[on\|pulse\|off\|test]` | `state enabled mode` (query) |
| `diag` | — | `#` lines, then `ok` |

#### Identification

```
> version
ok name=wheelly fw=0.1.0 proto=2 serial=0123456789AB slots=5
```

**The first command to implement, not the last.** Frankenwheely had the version number in the
firmware and no command to read it: the driver could not know what it was talking to. Here
`proto` is the number that counts — the driver refuses to connect if it does not know that
version, and says so clearly instead of behaving strangely.

It is also the **real handshake**: another device on the port does not answer `name=wheelly`
and the connection fails at once. Frankenwheely's `Handshake()` returned `true` in every case,
so connected to the wrong port its driver declared itself connected.

`serial` is the chip's MAC address (`ESP.getEfuseMac()`), unique and set at the factory: it is
how the driver tells two wheels apart (section 5.4). `slots` is how many slots this wheel has;
the driver does not assume it.

#### State

```
> status
ok pos=3 angle=144.44 target=144.45 err=-0.01 motion=idle retries=0 legs=5 boosts=0 outcome=arrived agc=128 mag=812 md=1 ml=1 mh=0 dir=-
```

| field | meaning |
|---|---|
| `pos` | current slot, 1 … number of slots, or `0` if the wheel is between slots **or moving** |
| `angle` | angle read from the AS5600, in degrees |
| `target` | target angle, that is `angle[pos]` (`angle[pos] + offset[pos]` in protocol 1) |
| `err` | residual error in degrees, signed |
| `motion` | `idle` · `moving` · `settling` · `failed` |
| `retries` | retries used in the last positioning: legs after a stall or an overshoot, not the approach legs |
| `legs` | every leg of the last (or current) positioning, the first included |
| `boosts` | legs of the last (or current) positioning run at the boosted speed after a stall |
| `outcome` | **the verdict** of the last completed positioning: `none` · `arrived` · `warning` · `failed` |
| `agc` `mag` | the sensor's gain and magnitude |
| `md` `ml` `mh` | the AS5600's STATUS flags: magnet detected · field too weak · field too strong |
| `dir` | the way the current (or last) leg was sent: `+` increasing angles, `-` decreasing |

**This command is the truth.** It can be called at any moment, even with the motor running,
and answers at once without disturbing the positioning.

**`md`, `ml` and `mh` are read from the chip**, every time (`magnetDetected()`,
`magnetTooWeak()`, `magnetTooStrong()` of the AS5600 library). Rejected: sending `ml=1 mh=0`
as constants — that is the usual reading with this magnet at 3.3 V, but ML also lights up when
the module's VDD5V–VDD3V3 bridge breaks (`hardware.md`), and a constant hides exactly that.
When the sensor does not answer on I2C, `agc`, `mag`, `md`, `ml` and `mh` are all sent as `0`.
`firmware/test/test_field.cpp` checks that the flags reach `status` and `diag` as the chip
reports them.

**`outcome` exists because `status` must be enough on its own.** Without it the driver would
have to compare the residual error with the tolerances to know whether the move succeeded or
was only passable — **redoing the decision that by design belongs to the firmware**, in a
second copy bound to diverge the first time a threshold changes. It uses the same vocabulary
as the events on purpose: one thing, said in two ways.

`pos` is never a valid slot during a move: that would be a lie while the wheel passes in front
of the slots, and an Alpaca bridge must be able to translate it into the −1 that ASCOM
requires (section 11).

#### Movement

```
> go 3
ok target=144.45 from=72.20 dir=+
> stop
ok
```

```
> jog -0.1
ok target=143.98 from=144.08 dir=-
```

`go` returns **at once**: the move is asynchronous. The answer says where the wheel is going,
where it starts from and which way it turns (`dir`, the one really commanded: one way round it
is not the shorter one), so the log shows what it decided. A slot outside `1..slots` is refused
with `error 3 expected=1..<slots> got=…`; a silent sensor or a missing magnet with `error 4` or
`error 5`, and the wheel does not move. `stop` interrupts and releases the motor.

`jog <degrees>` (for the jog buttons of the calibration tab) moves the disc **to the angle read
now plus `<degrees>`**, `|degrees| <= JOG_MAX_DEG` (180), with the same closed loop as `go`:
approach legs, the learnt play of the tyre, retries, and the usual `arrived` / `warning` /
`failed` events, which name the slot asked for last (jogging is how that slot is centred
before `teach`). It is a target and **not a number of steps** on purpose: the TPU tyre
swallows ~0.6° before the disc moves, so 0.05° of steps would move nothing. Its own choices:

- **the range is half a turn**: the panel's largest jog is one slot pitch, 360/slots, and the
  fewest slots are two. A jog of exactly half a turn has no shorter way: it goes the way its
  sign says;
- **the shortest way, whatever `direction` says.** One way only, a jog against it would go
  round the whole turn across the other filters, and so would a correction after an overshoot.
  On a mechanism stiffer one way a jog the stiff way may stall; it then ends `warning` or
  `failed`, honestly, and the jog the other way still works;
- **its own good tolerance**: half the jog, never below half an AS5600 count (0.044°,
  `JOG_GOOD_MIN_DEG`) and never above `good`. Judged by `good` (0.3°), a jog of 0.1° would
  "arrive" without moving; below one count (0.088°) the sensor cannot tell more, so a 0.05° jog
  may end `warning` a hair past its target — the driver reports that as information, not as a
  fault;
- **a jog that did not cover half of itself is never a warning**: the warning band of a `go`
  (0.8°) is wider than the small jogs, so a stalled +0.5° jog, the disc never moving, would end
  0.5° off its target, be reported as a warning and shown as done. It takes its retries and ends
  `failed`;
- refused with `error 7` while the wheel moves, `error 3 expected=-180..180 got=…` beyond the
  range, `error 4`/`5` without the sensor or the magnet, like `go`.

The hand stays the second way: turn the wheel, then `teach`.

#### Calibration

```
> angles
ok a1=0.00 a2=72.00 a3=144.00 a4=216.00 a5=288.00
> names
ok n1=Lum n2=Red n3=Green n4=Blue n5=Ha

> angle 3 144.05
ok a3=144.05
> go 3
ok target=144.05 from=143.98 dir=+
> jog 0.1
ok target=144.16 from=144.06 dir=+
> teach 3
ok a3=144.18
> name 3 Green
ok n3=Green
> save
ok saved=nvs
```

The lists are built in a loop over the wheel's slots, not with a fixed five-entry format: the
number of slots is a property of the wheel, not of the code.

`angle 3 …` sets the angle of slot 3, 0° … 360° (360 reads back as 0), in working memory; it is
refused with `error 7` while the wheel moves, because the move under way aims at the old angle.
It **does not move the wheel**: whoever sends it decides. The INDI driver sends `go 3` right
after it when one angle changed, which is the live centring of the star while watching the
screen; when several changed at once it moves nothing (section 5.1). It replaces protocol 1's
`offset`, `offsets` and `clear-offsets` (section 2.2).

`teach 3` takes the angle the wheel has **now** and makes it the calibration of slot 3. It is
the calibration procedure: bring the wheel to where the filter is centred, by hand if you like,
and say "this is three". Refused with `error 7` while the wheel is moving.

`name` checks the name against the rule of section 6 and refuses it with `error 9 reason=…`,
where the reason is one of `empty`, `too-long`, `bad-edge`, `bad-char`, `reserved`,
`duplicate`. A name with a space arrives split into several words and is refused as
`bad-char`.

**Saving is an explicit gesture.** Frankenwheely wrote to EEPROM at every single change of an
offset — two writes for every click on the Ekos slider. Here you experiment in volatile memory
and write only when you are happy: if you get it wrong, restart the wheel and the good
calibration is back. `save` writes everything the wheel keeps: the number of slots, angles,
names, tolerances, run and holding current, speed, acceleration, the settling wait, the
direction, the drive ratio and its learning switch, and the LED mode.

#### Number of slots

```
> slots
ok slots=5
> slots 7
ok slots=7
```

`slots <n>` accepts `MIN_SLOTS..MAX_SLOTS` (2 to 12: a wheel with one slot never changes
filter) and is refused with `error 7` while the wheel moves. Changing the number **throws the
calibration away**: see section 5.1, "The wheel says how many slots it has". Like everything
else, it reaches NVS only with `save`.

#### Settings

```
> tolerance
ok good=0.30 warn=0.80 retries=3
> tolerance 0.50 1.50 3
ok good=0.50 warn=1.50 retries=3

> motor
ok ma=350 speed=300 accel=1200 ceiling=15771
> motor 300
ok ma=300 speed=300 accel=1200 ceiling=15771
> motor 350 250 1000
ok ma=350 speed=250 accel=1000 ceiling=16738

> direction
ok direction=down ceiling=15771
> direction shortest
ok direction=shortest ceiling=12146

> hold
ok ma=0
> hold 150
# warning: holding current on - heat and chopper noise during exposures
ok ma=150

> settle
ok ms=300 ceiling=12146
> settle 1000
ok ms=1000 ceiling=24396
```

`motor <mA> [<speed> <accel>]` sets the run current, and optionally speed (steps/s) and
acceleration (steps/s²) **together**: the driver's panel sets the three at once, and a
half-applied pair makes no sense, so `motor <mA> <speed>` without the acceleration is refused
with `error 2`. The limits are in `wheelly_protocol.h`, shared by the wheel that checks them
and the panel that offers them, so the panel cannot offer what the wheel refuses: current
`1..MOTOR_MA_MAX` (800 mA), speed `1..MOTOR_SPEED_MAX` (5000), acceleration
`1..MOTOR_ACCEL_MAX` (50000). **A refused `motor` changes nothing**: every argument is checked
before any is applied — otherwise `motor 300 99999 1200` would answer an error with the current
already at 300.

The defaults are **350 mA, 300 steps/s, 1200 steps/s²** (`FACTORY_RUN_MA`, `FACTORY_SPEED`,
`FACTORY_ACCEL`, one source for the firmware, the simulator and the panel). The 350 mA was
**found on the part, not calculated** (measured): the friction drive was tried by hand from 150
to 350 mA in steps, and 350 is where it stopped slipping. The motor is rated 400 mA per phase,
which leaves 50 mA of margin (with the detent still fitted, the reference wheel needed the full
400 mA to climb out of one notch). Lowering the run current below the holding current lowers
the holding current with it.

`motor` exists for commissioning: the run current is found by raising it until the friction
stops slipping, and doing it live with the wheel mounted instead of recompiling is the
difference between an evening and ten minutes.

`hold` is **zero by default** — the motor is released at the end of the move. A wheel that
drifts at rest (the `drift` event says so) gets a reduced current (section 2.4); the firmware
accepts `0..` the run current.

`settle [ms]` is how long the motor stays energised at the run current after every leg, before
the verdict is read and the motor released (section 3, "The hold after arrival");
`0..SETTLE_MS_MAX` (2000), default `FACTORY_SETTLE_MS` (300), kept by `save`; the reply carries
the move time cap, which counts it once per leg. A command of its own and not a second argument
of `hold`, so that an older driver's `hold <mA>` keeps working unchanged; an older firmware
answers `settle` with `error 1` (unknown command), and the driver then keeps the field at 300,
which is what that firmware does. Anything else is `error 2` (`settle 1 2`, `settle soon`) or
`error 3 expected=0..2000 got=…`, and changes nothing.

`direction [shortest|up|down]` sets which way the wheel may turn (section 3; default
`FACTORY_DIRECTION`, `shortest`; kept by `save`). The reply carries the move time cap the wheel
derives from it, `ceiling=` in ms. Any other value is
`error 2 expected=shortest|up|down got=…`, and changes nothing.

#### The drive ratio

```
> ratio
ok ratio=2.9000 base=2.9000 factory=2.9000 learn=on learnt=0 ceiling=12146
> ratio 3.2230
ok ratio=3.2230 base=3.2230 factory=2.9000 learn=on learnt=0 ceiling=12280
> ratio learn off
ok ratio=3.2230 base=3.2230 factory=2.9000 learn=off learnt=0 ceiling=12280
> ratio 29
error 3 expected=1.0..10.0 got=29 ratio out of range

> legs on
ok report=on
```

`ratio` (section 3, "The drive ratio") reads the ratio **in use** (`ratio=`, the base refined
by the learning), the **base** it started from (`base=`: the factory value, the saved one, or
the last `ratio <value>`), the factory one, whether it learns and from how many legs since the
base was set. `ratio <value>` sets the base (1–10, refused while moving with `error 7`) and
restarts the learning from it; `ratio learn on|off` switches the learning, and off goes back to
the base. The reply carries the move time cap, counted at the base. `save` writes the ratio in
use and the switch (NVS keys `ratio`, `ratio_learn`), and the ratio in use becomes the base.
The INDI driver never sends `ratio`, and adding a command is not an incompatible change
(protocol stays 2).

`legs on|off` turns on the `! leg` event (section 4.6) after every leg. It is **off at every
start and never saved**: it is for a measuring tool like `firmware/ratio_test.py`, which turns
it on and back off.

#### The LED

```
> led
ok state=off enabled=yes mode=pulse
> led on
ok state=on
> led pulse
ok state=off mode=pulse
> led off
ok state=off
> led test
# W .--  H ....  E .  E .  L .-..  L .-..  Y -.--
ok duration=6.7
```

The LED has three **modes**, kept in NVS by `save`:

| mode | behaviour |
|---|---|
| `pulse` (**default**) | off at rest; **breathes** while the wheel goes to *another* slot; shows the alarm signals below |
| `on` | steady on; the alarm signals replace it while one is active |
| `off` | off **for good**: no pulse, no alarm signals, for whoever wants no light near the optics |

The pulse starts when `go` arrives and stops when the wheel is there, has failed, or has been
stopped. It does not start on a `go` to the slot the wheel is already on: that is a small
correction, not a change of filter, and a light that breathed at every correction would stop
meaning anything. The timing is a sine with a 1700 ms period that starts from the bottom; the
brightness goes from 5% to 30%, chosen by comparing ranges side by side on the real LED
(`firmware/led_test`), and it is raised to a gamma of 2.2 because a PWM duty is linear light,
not a colour already coded for the eye.

**The alarm signals.** The LED says what went wrong, one alarm at a time, the gravest first
(`Alarm` in `dialog.h`):

| alarm | signal | when it ends |
|---|---|---|
| slot not reached (`failed`) | **fast blinking**, 4 a second | when the wheel is sent again, or is found at rest on a slot within `warn` — turned there by hand too; the slot it was stuck on counts only once it has left it |
| drift at rest (`drift`) | **two short flashes every 2 s** | when the wheel is sent somewhere, or a positioning ends |
| magnet lost (`sensor`) | **three short flashes every 2 s** | when the sensor sees the magnet again without a break for `MAGNET_REARM_MS` (section 4.6) |

By gravity: magnet lost, then slot not reached, then drift. The flashes are at the top
brightness of the pulse. **With the LED in `off` mode none of them shows**: `off` is also the
mode for turning the wheel by hand with no current in the motor, and a wheel turned by hand
drifts by definition. The Morse test wins over all of them. `firmware/test/test_alarms.cpp`
checks the patterns and their silence in `off` mode.

`led test` blinks **`Wheelly` in Morse code** and then returns to what the mode says. It
answers "is the LED alive, or is it the wire that came off?" without taking anything apart and
without a multimeter. Spelling the name of the project instead of three random blinks makes the
test recognisable: a sensible sequence and not a flicker means the right LED, driven by the
right firmware.

**It never starts by itself.** It is done with the cover open or in daylight, never during a
session: the assembly is inside the optical path. The driver's log says so when the test
starts.

Standard Morse timing: dot 1 unit, dash 3, gap between symbols 1, between letters 3. At 100 ms
per unit the sequence lasts **6.7 seconds**. `firmware/test/test_morse.cpp` checks it unit by
unit.

The `enabled` field of the query is always `yes` (in the simulator too), and the driver does
not read it: the mode is in `mode`. It is a leftover of a design in which `off` was not a mode.

#### Diagnostics

```
> diag
# AS5600 at 0x36: responding
# STATUS md=1 ml=1 mh=0  AGC=128  MAG=812
# TMC2208 over UART: responding, run 350 mA, hold 0 mA
ok
```

It answers one question only: **is it really talking to the hardware?** A driver in UART mode
can be questioned, and a loose wire there would otherwise look like "the motor does not turn"
and send you looking in ten wrong places.

The motor driver's line carries **the name the chip reports**: the `version` field of the IOIN
register is `0x20` on a TMC2208 and `0x21` on a TMC2209, and the firmware accepts both
(section 9). The module in Wheelly is a **TMC2208**. When nothing answers, the line reads
`TMC2208/2209 over UART: SILENT - check VM at the driver, then the 1k on the single wire`,
because which chip is silent cannot be known. The driver line goes through **the same check every
leg of motor makes** (section 9, trap 3): a driver found reset or newly powered is set up again
here too, and reported with the `! driver` event. It used to be the only place that set the
driver up after boot, so after a power-up in the guide's order - USB, then 12 V - the wheel moved
on a driver at its reset values (a +10° jog moved +2.28° on the reference wheel) until someone
typed `diag`, and `diag` looked like the cure. When the sensor is silent the answer says so and
points at the wiring and the VDD5V–VDD3V3 jumper; when the magnitude is below 350 it adds that
the magnet is too far or off centre.

### 4.6 The events

Lines that arrive **without anyone asking for them**, recognisable by the `!`.

```
! arrived pos=3 err=0.01 retries=0
! warning pos=3 err=0.34 retries=1
! failed pos=3 err=1.87 retries=3
! drift pos=0 err=0.62
! sensor md=0
! driver reason=power
! leg n=1 kind=first jog=no steps=4125 motor=464.062 ratio=3.2230 aim=144.000 from=0.000 to=143.518 moved=143.518 long=yes learn=no
```

- `arrived` — success within the `good` tolerance.
- `warning` — success, but outside `good` and within `warn`. The driver writes it in the Ekos
  log and **lets the sequence go on**: "report but proceed".
- `failed` — outside `warn` even after all the retries, or past the time cap. The driver puts
  `FILTER_SLOT` in `Alert` and Ekos stops the capture, and after the error — as after its own
  time cap and a failed jog — logs a second line, `msg.hint.detent`: if the motor stalls or the
  clutch slips, check first that the wheel's detent was removed (assembly guide, chapter 10). A
  line of its own because an INDI message is cut at 255 characters.
- `drift` — the wheel moved **at rest**, beyond the `warn` tolerance, with nobody asking. Sent
  once per episode: it re-arms when the wheel comes back within tolerance or a new move starts,
  otherwise a drifting wheel would fill the log ten times a second. It is the sign that holding
  current is needed. Its `pos` is the slot the wheel is on when it is sent: beyond `warn` that
  is `0` (between slots), unless it has drifted all the way onto another one.
- `sensor` — the magnet is no longer detected. It is serious and must be said when it happens,
  not at the next question. **Once per loss, with hysteresis**: the next loss is reported only
  after the magnet has been seen **without a break** for `MAGNET_REARM_MS` (1 s, `wheel.h`), and
  the LED's magnet alarm ends on the same condition. Re-armed by a single "seen", a magnitude
  around the AS5600's detection threshold (314 on the reference wheel, measured) made the MD bit
  flicker and sent `! sensor md=0` tens of times a second. The fakes of both halves reproduce it
  with `--magnet-flicker MS`, and the tests want one event per episode.
- `driver` — the motor driver had to be **set up again** before a leg or in `diag`.
  `reason=power`: it had been silent and now answers - the 12 V arrived after the XIAO had
  started, which is the order the assembly guide gives, so at a normal power-up it comes once,
  before the first move; the INDI driver logs it as information. `reason=reset`: it answered
  with its setup gone - the 12 V dropped and came back with the wheel running; logged as a
  warning. Once per setup, never per check. The reasons, and how a reset is recognised, are in
  section 9, trap 3.
- `leg` — **only after `legs on`**: the end of one leg, sent before the verdict's event when it
  was the last. `n` its number in the positioning, `kind` `first`, `approach` or `retry`, `jog`
  whether the positioning is a jog, `steps` the microsteps sent (signed) and `motor` the same in
  motor degrees, `ratio` the ratio they were computed with, `aim` the disc degrees wanted (the
  play sent on top excluded), `from` and `to` the angles read before and after settling, `moved`
  the disc degrees the way it was sent (negative: back), `long` whether it was long enough to
  tell the ratio (30°), `learn` whether the wheel learnt its ratio from it. Opt-in because
  nobody but a measuring tool wants a line per leg: the INDI driver logs an event it does not
  know at debug level and ignores it (`Wheelly::handle_unsolicited_line`).

**No event is indispensable** — the rule frankenwheely got wrong. Events make the driver react
quickly, they do not inform it: everything they say can be found in `status`. The driver asks
`status` at every INDI polling period — 250 ms by default, adjustable in Options → Polling — and
every 100 ms during a magnet sweep; if an event is lost, the next poll notices.

### 4.7 The errors

```
error 3 expected=1..5 got=7 slot out of range
```

Three things on the same line, each for a different reader. The **code** is for the machine,
and it is also the **translation key** (section 13). The **named fields** are the parameters
with which the driver builds the sentence in the user's language. The **English text** at the
end is very short and serves only whoever is watching the raw serial: it is the note for the
developer, not the sentence the user sees.

| code | meaning |
|---|---|
| 1 | unknown command |
| 2 | missing, extra or non-numeric arguments; a line too long |
| 3 | value out of range, with `expected=` and `got=` |
| 4 | the sensor does not answer |
| 5 | magnet not detected |
| 6 | the motor driver does not answer: `go` and `jog` refuse to start (after the slot's range and the sensor), because steps sent to a driver without its 12 V go nowhere; the host's sentence asks whether the 12 V are on. A driver that goes silent **between two legs** ends the positioning `failed` at once, with no retries into nothing |
| 7 | not allowed now (for example `teach` or `slots` while the wheel is moving) |
| 8 | writing to NVS failed |
| 9 | invalid filter name, with `reason=` (see section 6) |

Frankenwheely had eight communication error codes, defined in an enum and then **thrown away**
inside a function whose body had been commented out: a corrupted frame vanished, and the host
could not tell "still working" from "the command was lost". Here **every command answers**,
always. If the driver receives no line within its timeout (3 s), the problem is the link — and
that is information, not ambiguity.

---

## 5. The INDI driver

### 5.1 The properties, and which tab they are in

Three tabs of our own, split by the real work.

**Main Control** — what you touch every night: which filter, what they are called, and where the
wheel is now. The sensor's magnitude and AGC are there too, because they are instrumentation to
keep an eye on *while* capturing: the magnitude's excursion is the measure of the magnet's
centring, and a loosening wire shows up there before it shows up in a spoiled exposure.

**Calibration and Diagnostics** — what you touch once and then rarely: number of slots, angles,
jog steps, saving, tolerances, the hardware check, the magnet sweep, the movement log. Things to
do with the cover open or during commissioning, not in the middle of a sequence. "and", not
"&", because a Qt tab label takes "&" as a shortcut marker.

**Options** — the settings of the machine (motor, holding current, LED), the firmware data and
the language, together with what INDI puts there itself: debug, polling period, configuration.
Right under INDI's *Configuration* sits *Wheel configuration* with the one button *Save to the
wheel*, the same as the calibration tab's: the settings of Options that live in the wheel are
saved without leaving it. A property of its own, `WHEELLY_CONFIG`: `CONFIG_PROCESS` is INDI's,
Ekos counts on its four elements, and five exclusive buttons KStars would draw as a drop-down
menu. It is placed there by registering it between INDI's own controls (the driver calls
`addConfigurationControl()` and `addPollPeriodControl()` itself instead of `addAuxControls()`),
since a client lays a tab out in the order the properties are defined.

The first two properties come from the `INDI::FilterWheel` base class and are the ones Ekos
expects; the others are ours. The full description of each, with pictures of the real panel, is
in `docs/driver/` (English) and `docs/driver/it/` (Italian), generated from the panel the driver
really declares.

| property | tab | type | access | what it holds |
|---|---|---|---|---|
| `FILTER_SLOT` | Main Control | number, 1 | R/W | current slot, from 1 to the wheel's number of slots. **Standard** |
| `FILTER_NAME` | Main Control | text | R/W | filter names, read from the wheel. **Standard** |
| `WHEELLY_POSITION` | Main Control | number, 3 | read-only | angle read, residual error, retries of the last move |
| `WHEELLY_SENSOR` | Main Control | number, 5 | read-only | AGC, magnitude, and the MD/ML/MH flags |
| `WHEELLY_SLOTS` | Calibration and Diagnostics | number, 1 | R/W | how many slots the wheel has. Sent to the wheel with `slots` |
| `WHEELLY_ANGLE_1` … `_n` | Calibration and Diagnostics | number, 1 each | R/W | the calibration angles, in degrees, **one property per slot** (not one vector) so that every row has its own Set. The current slot's label reads "▶ n"; after a jog its row shows the angle read now, "▶ n *", not taught yet. Set on that row unchanged teaches it with `angle n` and does not move; Set with another value, or on another row, sends `angle n` if the value changed and moves the wheel there as `FILTER_SLOT` would |
| `WHEELLY_JOG_DOWN` / `WHEELLY_JOG_UP` | Calibration and Diagnostics | switch | W | −360/slots · −10 · −1 · −0.1 and +0.1 · +1 · +10 · +360/slots degrees, sent with `jog <deg>`; the pitch buttons' labels follow the number of slots |
| `WHEELLY_SAVE` | Calibration and Diagnostics | switch | W | save to the wheel |
| `WHEELLY_TOLERANCE` | Calibration and Diagnostics | number, 3 | R/W | good tolerance, warn tolerance, retries |
| `WHEELLY_DIAG` | Calibration and Diagnostics | switch | W | ask the wheel: is it really talking to the sensor and the motor driver? |
| `WHEELLY_SWEEP` | Calibration and Diagnostics | switch | W | the sweep: a full turn measuring the magnet at every poll |
| `WHEELLY_SWEEP_PLOT` | Calibration and Diagnostics | BLOB | read-only | the plot of the last sweep, as PNG |
| `WHEELLY_SWEEP_DIR` | Calibration and Diagnostics | text, 1 | R/W | where sweeps are written. Default `~/Documents`, saved in the configuration |
| `WHEELLY_LOG` | Calibration and Diagnostics | switch | R/W | the CSV movement log: on or off. **Off by default** |
| `WHEELLY_FILES` | Calibration and Diagnostics | text, 2 | read-only | where the two files the driver leaves on disk are: the movement log and the last sweep |
| `WHEELLY_CONFIG` | Options | switch | W | "Wheel configuration": save to the wheel, right under INDI's Configuration |
| `WHEELLY_FIRMWARE` | Options | text, 3 | read-only | firmware version, protocol version, serial number |
| `WHEELLY_MOTOR` | Options | number, 3 | R/W | run current in mA, speed, acceleration — sent together with `motor` |
| `WHEELLY_HOLD` | Options | number, 2 | R/W | holding current at rest in mA. **0 = off**, the default. The field shows the wheel's value, 0 included; the 150 mA suggestion is in the drift message. Second field: the **hold after arrival** in ms, `settle`, read back from the wheel at connection and sent only when it changed (an older firmware then goes to Alert only if that field is changed) |
| `WHEELLY_DIRECTION` | Options | switch | R/W | shortest way (default) · increasing angles only · decreasing angles only — sent with `direction`, read at connection; warns in the log when the wheel's time cap is past Ekos's 30 s |
| `WHEELLY_LED` | Options | switch | R/W | steady on · pulses while moving (default) · off · test (blinks `WHEELLY` in Morse) |
| `WHEELLY_LANGUAGE` | Options | switch | R/W | from the system · English · Italian |

**The current slot is marked in the angles.** INDI cannot colour one element, only a whole
property, so the label of the slot the driver is on reads "▶ 2". A label reaches a client only
with a definition, so the driver takes the property down and defines it again — and every
property after it in the tab too, because KStars puts a property defined again at the end of its
group, and the angles would slide under the log. Only at the end of a jog, at a change of slot
and at a teach, never at a plain poll. The mark follows the driver's current filter: it stays on
while the wheel is jogged off the slot to centre it, and that row follows the jogs with an
asterisk until its Set confirms it; any other move gives it back its taught angle. There is no
separate "Save position" button (`teach` of the current slot): that Set does the same.

**Property and element names are identifiers**, so they are English and fixed forever, like the
words of the protocol. What the user reads in Ekos are the **labels**, which are free text and
come from the catalogue of their language.

**The tab names stay in English.** They sit in the same tab bar INDI creates by itself —
*Connection*, *Options* — which cannot be translated: a bar half in Italian and half in English
would look broken. Everything inside the tabs is ours, and is translated.

`FILTER_NAME` is read **from the wheel** at connection and fills the standard property; if the
user changes the names from Ekos, the driver writes them back to the wheel. The names are the
wheel's, always: a name saved in the INDI configuration does not override what the wheel says.

**The rejection of a name is said in two places, and they are the only two there are.** The
`FILTER_NAME` light goes to `Alert` — red — and the text **goes back to the good one**, so you
see it was not accepted instead of believing it saved; and in the **log pane**, at the bottom of
the panel, goes the sentence that explains: which slot, which name, what is wrong, **which name
to write instead**, and — always, even when the reason has nothing to do with them — **which
characters are allowed**.

```
Slot 1: "f_ fsd" refused - there is a space. A name that would be accepted here: "f_fsd".
[INFO] Allowed: letters without accents, digits, _ - and . ; 1 to 32 characters;
the first and the last must be a letter or a digit.
```

**Two lines, not one**: an INDI message is a `char[MAXINDIMESSAGE]` with
`MAXINDIMESSAGE = 255` (`indiapi.h`), and what does not fit is cut **silently**. With the rule
appended at the end, the rejection of `-Lum-` reached Ekos cut off mid-word. In two lines it
always fits, even with a 32-character name and an equally long proposal. The bench test checks
it — and the check goes **at the end**, after all the cases have run: in the middle it cannot
see the cases after it.

**`FILTER_SLOT`, on the other hand, must NOT turn red**: in Ekos `FILTER_SLOT` in `Alert` means
"filter change failed" and **stops the capture sequence**. A misspelt name is the writer's
mistake, not the wheel's, and must not throw a night away. The test checks it on purpose.

### Why there is no pop-up hint, nor a text box in the panel

The model is the tooltip of *Camera → Format* in Ekos, the one that lists the placeholders
`%f`, `%D`, `%T`. A driver cannot replicate it. Three ways of getting close were tried and
rejected; they stay written here because all three look like good ideas.

**That tooltip lives inside Ekos.** It is a single HTML string in the `.ui` file of the Capture
tab, compiled into the executable: `strings /usr/bin/kstars` pulls it out as is,
`<html><head/><body><p>Format is used to define…`. It is an Ekos widget with the text wired into
it, not data coming from the device.

**Rejected: a free text box between one field and another** — it does not exist. The INDI panel
builds widgets from the **properties**, and there are five types — number, text, switch, light,
BLOB. The closest to free text is a read-only text property, but it is rendered as a fixed-width
`QLineEdit` that **does not wrap and has no tooltip**: long text shows by half. Tried: four rows
of fields in the middle of the main panel, with the rule broken into fifty-character pieces.

**Rejected: the property's label as tooltip.** It is the only tooltip a driver can set — in
KStars `indi/indiproperty.cpp` does `setToolTip(label)`, while elements, in
`indi/indielement.cpp`, have none. The price is that the label is **also visible text**, in a
box 130 points wide: in the column it reads with an ellipsis in the middle. There is no way to
have the tooltip without the truncation. Two limits that remain true for any label:

- the label is a `char[MAXINDILABEL]` with `MAXINDILABEL = 64` (`indiapi.h`), and what does not
  fit is cut **silently**. **Bytes** are counted, not letters: accented letters take two;
- breaking it over several lines does not help: labels travel as XML attributes, and `lilxml` —
  INDI's parser, the one KStars uses too — drops newlines inside an attribute **without even
  leaving a space**. Tried with a small program compiled against the real `lilxml`:
  `"filters\nAllowed"` arrives as `"filtersAllowed"`.

So the log pane, which wraps by itself and holds all the text needed, is not a fallback: it is
the right place.

**The reason names the guilty character.** "Only letters, digits, `_ - .`" forces you to reread
the name character by character; "there is a space" is understood at once. An accented letter
has a sentence of its own, and **cannot be printed**: in UTF-8 it is two bytes, and sending back
only one is not valid UTF-8, hence not valid XML — with the check removed, the INDI client dies
with `not well-formed (invalid token)` on the whole stream, not on that message.

The proposed name is computed by `sanitize_filter_name()`, the same function that is the safety
net for names coming from outside: by construction what it produces passes
`check_filter_name()`, so the driver checks only the one thing the rule cannot know, that the
proposal is not already another slot's name. For duplicates nothing is proposed: the name is
valid in itself, and choosing another is up to whoever knows what that slot is for.

### The magnet sweep

`WHEELLY_SENSOR` gives the magnitude **now**, one number at a time. But the measure that counts
for the magnet's centring is its **excursion over the whole turn**, and that cannot be seen by
watching a changing number. The sweep shows it: the wheel makes a full turn going from slot to
slot, the driver records angle and magnitude at every poll, and a plot comes out at the end.

**No new firmware command.** The data it needs are all in `status`, which the driver polls
anyway: the sweep does not send a single extra byte on the serial line, it keeps the answers. A
`sweep` command would have meant touching the protocol for a diagnostic function.

**It does not block the driver.** A loop running for twenty seconds inside `ISNewSwitch` would
freeze the driver and with it the possibility of stopping it from Ekos. So it is a state machine
advancing inside `TimerHit`, one hop at a time, exactly like a normal filter change — and
`FILTER_SLOT` goes `Busy` while it runs, because the wheel is really moving. The turn ends
**where it started**: whoever was capturing finds the filter they had.

**During the turn it polls more often**, 100 ms instead of the polling period: every answer is a
sample, and at the normal rate a whole turn gives twenty — which over 360° draw a constellation,
not a curve. At 100 ms there are about forty on the simulator, more on the real wheel, which is
slower.

**The firmware reads the sensor during moves too**: `Wheel::step()` reads the angle at every
pass, moving too (one raw reading; the verdict still takes its own 8-reading mean after
settling). A firmware that kept the angle of the last stop until the verdict gave a sweep with
points **only at the five slots**, while the simulator — which interpolates the move — drew a
continuous curve, and nothing compared the two. A test now asks `status` during a move on both
halves and wants the angle to change. The I2C read does not disturb the motion: the pulses come
from a peripheral of the ESP32 and the ramp from FastAccelStepper's own task, not from `loop()`.

**How the plot treats the points.** Samples taken at the same angle (within 0.1°, about one
count) are **one point**, at their mean: the wheel rests at every slot for a while, and those
samples, sorted and joined, draw vertical lines that read as the field jumping where the wheel
stands still. The vertical window is **at least 200 counts**, centred on the data: stretched to
the data alone, the reference wheel's 390–424 (measured) filled the whole height and read as a
collapse of the field when it was an 8 % ripple. Both are checked on the Mac by
`firmware/test/test_plot.cpp`.

**The PNG is drawn by hand**, in `plot.cpp`: a palette canvas, a 5×7 font written row by row,
and a PNG writer that does not compress — deflate *stored* blocks, which is valid zlib and costs
twenty lines instead of a dependency. The driver has no external dependencies, and that is what,
by INDI's `CONTRIBUTING`, lets it go into the main repository instead of `indi-3rdparty`: adding
Qt or libpng for a diagnostic plot would be a disproportionate price. The file is about 269 kB,
because it is not compressed; for something asked for once in a while that is fine.

The font has **only unaccented capitals**, so the plot's words are chosen accordingly: a letter
it does not know becomes a space. The background is **solid black**, not a very dark grey: the
window that shows it is white, and next to white a near-black reads as a washed-out smudge.

**How the plot is seen, and why it does not open by itself.** It is a BLOB, and a BLOB in INDI is
not a widget: it is a file transfer. In the panel the property shows the words
`INDI DATA STREAM` and nothing else. On arrival KStars saves it in the FITS folder; and **if** the
extension is an image format Qt can read, it also opens its `ImageViewer` window. That window has
two defects, and neither can be fixed from here:

- **it is white.** KStars inverts its palette on purpose (`auxiliary/imageviewer.cpp`): it uses
  the text colour as background, so with a dark theme it comes out white. It is meant for
  astronomical images in negative. The *Invert colors* button is added in the same place;
- **closing it also makes the INDI panel disappear.** The panel is created as a **child window**
  of KStars' main one — `new GUIManager(Options::independentWindowINDI() ? nullptr :
  KStars::Instance())`, and the default is `false` — and so is the plot's window: when one
  closes, the window manager raises the parent and the other child goes behind it. The
  *Independent window* box in *Configure KStars → INDI* fixes it, but that is a setting of the
  machine, not something the driver can guarantee.

So the declared format is **`.wheelly.png`** and not `.png`: Qt does not recognise it as an
image, KStars just saves the file, and no window opens. The name still ends in `.png`, so any
viewer opens it.

**The driver says the path**, because the client's is not known: where KStars puts the BLOB is
KStars' business. So the driver writes **its own copy**, for example
`~/Documents/2026-09-15_18-23-34_wheelly_sweep.png`, and puts its path in `WHEELLY_FILES`, where
it stays written, and in the log.

**Each sweep its own file, in Documents.** Measuring the magnet means comparing a before and an
after — a touch to the air gap, a screw tightened — and a fixed name that is overwritten throws
away exactly the term of comparison. The time in the name is **local**, not UTC, unlike the one
in the movement log: that one is read by a spreadsheet, this one by someone who remembers
touching the wheel "last night around nine". And it is in `~/Documents`, not in the driver's
hidden folder, because a plot is something to look at.

The folder is **writable** (`WHEELLY_SWEEP_DIR`) and saved in the configuration: `~/Documents`
is a reasonable default, not a truth for every machine, and whoever keeps data on an external
disk points it there. Changing it creates it at once and tries to write in it: if that fails — a
disk not mounted yet — the property goes to `Alert` and **says so**, instead of letting it be
found out at the first lost sweep. A leading `~` is expanded by the driver, because it is
usually the shell that expands it, and there is no shell here.

The file is a **PNG** and not a JPEG: JPEG compresses lossily, and on a drawing made of thin
lines and six-point text that means halos around every stroke.

BLOBs do not arrive until the client asks for them: in KStars that is the little box next to the
property, on by default.

**`WHEELLY_SENSOR` is not a luxury.** It is the instrumentation that at the bench served to
choose the air gap, and bringing it into Ekos means watching it while the wheel really works.
The magnitude's excursion over the turn is the measure of the magnet's centring, and a power
jumper coming loose shows up here before it shows up in a wrong exposure. The ML flag, read from
the chip, is the other place where it shows.

### The wheel says how many slots it has

Five is the number of the reference wheel, not of the project. The real number is **in the
wheel's memory**, is read with the `slots` command and reaches the driver in the handshake; the
driver adapts to it at connection, and sizes `FILTER_SLOT`, the names, the angles and the pitch
of the largest jog accordingly.

**It can also be set from the INDI panel**, with `WHEELLY_SLOTS` in *Calibration and
Diagnostics*: the driver sends `slots <n>` to the wheel, then takes down and defines again every
property whose size follows it (a client does not notice elements added to a property it already
has), and the log says what to do next — teach each slot, name the filters, save. The panel
offers 2 to 12, as the firmware accepts (`MIN_SLOTS`, `MAX_SLOTS`). Nothing reaches NVS until
*Save to the wheel*: switching the wheel off brings back the previous number and calibration.

**Rejected: separate `Wheelly5` and `Wheelly7` drivers.** Every fix would have to be applied to
every variant; the KStars device list would fill with near-identical entries; and above all
**whoever installs would have to know how many slots their wheel has in order to choose the
right entry** — exactly the information the wheel can give by itself. The wrong entry would give
a driver offering seven slots on a five-slot wheel, failing on the sixth without explanation. A
single driver that asks cannot be got wrong.

In the firmware `MAX_SLOTS` (twelve) is the size of the arrays, not the number of slots.
Changing the number with `slots <n>` **throws the calibration away**, and it could not be
otherwise: the angles of a five-slot wheel mean nothing on a seven-slot one. It starts again from
evenly spaced angles and generic names (`Lum Red Green Blue Ha` on a five-slot wheel,
`Filter1`… otherwise), which is not the real calibration but is usable at once.

### ⚠ "Offset" in this project means rotation, and only rotation

The same word means **something else** in at least two places of the ecosystem this wheel has to
live with.

| where | what it means | unit |
|---|---|---|
| **`WHEELLY_OFFSET`, protocol 1 (removed)** | how many degrees to rotate more or less than the calibration angle, to centre the filter | degrees of rotation |
| **Ekos**, focus management | how much to move the **focuser** when that filter is chosen | focuser steps |
| **ASCOM**, `FocusOffsets` of `IFilterWheel` | the same: focus compensation per filter, relative values with at least one at zero | not specified by the standard |

The other two exist because **filters of different thickness move the focal plane**, so focus
has to be corrected at every filter change. They have **nothing** to do with the rotation of the
disc.

**The two values must never be mapped onto each other.** Doing it would make the focuser move by
a meaningless amount at every filter change — a fault that would show up as out-of-focus images
and send you looking in the wrong place. Until there are real focus offsets to declare, the
ASCOM side returns for `FocusOffsets` **a row of zeros**, as long as the list of names.

In documentation and interface always write **"rotation trim"** or "rotation offset", never
"offset" alone. The rotation trim is gone (section 2.2, one number per slot): the centring is
done on the angle itself, and the warning stands for the ASCOM side (section 11).

**A note on names.** Frankenwheely called its properties `offset1`, `of1`, `ob1`: it works but
jars in every client, because INDI by convention uses `UPPER_CASE_WITH_UNDERSCORES` like
`FILTER_SLOT`. Here the convention is followed.

---

### 5.2 Where it is meant to end up: core, not `indi-3rdparty`

**INDI's written criterion**, the same in the `CONTRIBUTING.md` of both repositories: if the
driver builds and runs with only the dependencies already in INDI Core, **it goes in INDI
Core**. `indi-3rdparty` is for camera drivers, for drivers that need SDKs or external
dependencies, or for whoever wants to stay out of the core's release cycle.

`indi-wheelly` has no external dependencies: it speaks a serial line and that is all. All
fifteen existing filter wheels are in the core, in `drivers/filter_wheel/`, including purely
serial ones such as `xagyl_wheel`, `quantum_wheel`, `ifwoptec` and `pegasus_indigo`.

The core is also much cheaper to integrate: **four lines of CMake and an entry in
`drivers.xml`** (prepared in `driver/indi-wheelly/upstream/`). A third-party driver instead
wants `config.h.cmake`, the `.xml.cmake` file, a `debian/` folder with changelog and build rules,
often an RPM `.spec`, and two changes to the top-level `CMakeLists.txt` without which CI never
builds it.

**One door stays open.** `indi-atik-efw` — a serial filter wheel, no SDK, recent and well written
— is in `indi-3rdparty` all the same, so the rule is not applied to the letter. Releasing
`indi-wheelly` on its own schedule, apart from the core's cycle, is a legitimate reason, and must
be stated in the merge request.

What holds either way:

- **Licence.** INDI's repositories are LGPL-2.1, and the driver's files carry
  `SPDX-License-Identifier: LGPL-2.1-or-later`, so it can be carried in INDI's tree unchanged;
  `wheelly_protocol.h` stays MIT, a copy of the firmware's header (see `LICENSING.md`).
- **CI builds with `-Werror`**, on Ubuntu, Debian, Fedora, Arch and macOS, warnings about unused
  parameters included. `CMakeLists.txt` already builds with `-Wall -Wextra
  -Werror=unused-parameter -Werror=unused-but-set-variable`: better to find out here.
- In the core, in addition: the tests really run, and there is an **automatic style check with
  astyle** on the lines added by the diff.

**A warning about sources.** The documentation on `docs.indilib.org` — both the best-practice
page and the one on submitting drivers — prescribes a folder structure that **matches no real
driver** in the repositories. The specification is the repository, not the site.

### 5.3 Two Ekos constraints the firmware must respect

Read in the KStars source, not inferred, and kept **in the firmware** because that is where the
decision is taken.

**Thirty seconds, and not one more.** Ekos sets a 30-second timeout on the filter change: if by
then `FILTER_SLOT` has not gone back to `Ok`, it considers the change failed anyway. The retries
must fit **all together**, with margin. Hence the firmware's cap on the total positioning time:
past it, it declares failure by itself instead of being declared failed from outside, so the
reason stays written in our log and not only in Ekos'. The driver has its own cap, 3 s past the
wheel's, for a wheel that stops answering altogether. The wheel's cap is derived from speed and
direction (section 3) and can go past Ekos's 30 s — one way round, at a slow speed: the driver
then says so in the log, when the setting is chosen and at connection, rather than letting Ekos
end the move with a bare "timeout".

**`Alert` stops the sequence at once.** As soon as `FILTER_SLOT` goes to `Alert` during a change,
Ekos emits the failure and **stops the capture immediately**. It is the effect wanted for a real
failure — no exposure with the wheel out of position — and it confirms, by contrast, that **the
middle band must never use `Alert`**: a recoverable warning that stopped the night would be worse
than the problem it reports.

### 5.4 Easy to debug, by construction

- **Every protocol line in the log, on demand.** In *Options → Debug*, the **Driver Debug** level
  makes the driver write every line exchanged with the XIAO, both ways, with nothing to rebuild.
  Rejected: a dedicated *Protocol Verbose* level — it does not work on libindi 2.2:
  `addDebugLevel()` writes into slot `DBG_EXTRA_2`, but the `DEBUG_LEVEL` property publishes only
  five levels and stops at `DBG_EXTRA_1`, which stays labelled *Alignment Subsystem*. The level
  exists, the switch to turn it on does not.
- **Log levels used for what they are.** `LOG_INFO` is visible by default, so only what the user
  must really see goes there: connection, filter changed, failure. The rest is `LOG_DEBUG` and
  stays quiet until needed. A `LOG_ERROR` already reaches the client by itself; no separate
  message is needed.
- **The wheel is found by itself, and recognised by what it answers.** The driver gives INDI the
  port pattern `303a|espressif|wheelly|usbmodem` (Espressif's USB vendor id, the vendor name used
  under `/dev/serial/by-id/` on Linux, the macOS port name), so the port is proposed without the
  user choosing it in the dark; with INDI's *Auto Search* on, the other ports are tried when the
  saved one does not answer. But the port name is not an identity — on macOS it encodes the USB
  socket — so the wheel is recognised by its `version` answer and by its **serial number**, which
  the driver saves in the profile. `Connect()` makes two passes: only the wheel of this profile
  first, so that with two wheels each profile finds its own; then, if that wheel is on no port,
  any Wheelly, saying so in the log and adopting the new serial.
- **A wheel unplugged is found again by itself.** Unplugged and plugged back, the wheel used to
  leave the driver "Connected" on a descriptor that could only fail: `Write Error: Input/output
  error` at every poll (25 lines in a few seconds), the last angle frozen in the panel, commands
  lost, until Disconnect/Connect by hand. Now an I/O error that means the port is gone - `EIO`,
  `ENXIO`, `ENODEV`, `EBADF`, `EPIPE`, or end of file on a read; not a timeout, which a busy wheel
  also gives - closes the descriptor **at once** (kept open, it also keeps the device node busy,
  and the kernel gives the returning wheel another `ttyACMn`), writes **one** line in the log, puts
  the position and the sensor in Alert, and ends as failed whatever was under way (a filter
  change, a jog, a sweep), so Ekos stops a sequence instead of waiting. `TimerHit` then stops
  polling and tries to open the wheel again, after 1 s and then with a pause that doubles up to
  10 s, never giving up: the port the user chose first, then the `/dev/serial/by-id/` link that
  led to it at connection - that link carries the USB serial number, so it follows the wheel onto
  any `ttyACMn`. No other port is opened (that is Auto Search's business), and the wheel must
  answer with this profile's serial number: a reconnection never adopts another wheel. Found
  again, **one** more line, and the panel is read again from the wheel, which restarted with the
  USB. `CONNECTION` stays On and Ok throughout: libindi's `isConnected()` is true only for On
  **and** Ok, so putting it in Alert made the driver itself stop its timer and look for nothing,
  and for Ekos the device simply stays. A user command while the link is down gets one line
  saying so; a Disconnect by hand stops the search and closes the descriptor the reconnection
  opened. The bench unplugs a fake wheel twice (`test_usb_unplugged`): once coming back on a new
  pty found through a by-id link in the bench's own folder (`WHEELLY_SERIAL_BY_ID`, so no test
  looks at the machine's real devices), once on the port the user chose.
- **The driver never blocks.** INDI is single-threaded: a long wait freezes the driver and every
  client. So a filter change fires the command and returns, and the periodic poll checks the
  state until it is over. The repository has counter-examples — a wheel driver spinning in a wait
  loop for up to thirty seconds — which serve as a warning, not a model.

The style model is `indi-atik-efw`: a filter wheel, serial, no SDK, recent, with the new APIs and
— a detail worth copying — an **injectable transport**, which lets the protocol parser be tested
automatically, with no `indiserver` and no hardware.

---

## 6. Filter names: which characters, and why

The name typed in Ekos does not stay a label. It ends up in two places, and in both it can do
damage silently.

### Where it ends up

**In the `FILTER` keyword of the FITS header.** The chain is
`FILTER_NAME` → `indiccd.cpp` → `fits_update_key_str` → cfitsio → file. Followed line by line,
**none of the steps checks anything**: what the user types reaches the header byte by byte.

**In the file name, and also in a folder name.** In Ekos the `%F` placeholder appears twice in the
default format: as a directory component and in the file name.

### The finding that changes things

**Ekos sanitises the name of the target, of the host, of the camera and of the optical train. Not
the filter name.** In the same function, `placeholderpath.cpp`, the other placeholders all go
through `KSUtils::sanitize()`, and the filter is substituted literally, raw.

The worst consequence is not an error, it is the absence of one: **a slash in the filter name does
not make the write fail, it creates one more subfolder.** The frames end up somewhere other than
expected, and nobody complains.

The same goes for non-ASCII characters. The FITS 4.0 standard, §4.2.1.1, allows in string values
**only** printable ASCII from `0x20` to `0x7E` — no accents, no Greek. But cfitsio checks nothing
and truncates at 68 characters without raising an error; and reading back a file with a Greek
alpha in the header, astropy returns **`H??`** with a mere warning, and `verify()` passes without
complaint. The file stays valid, the name has changed, and nobody notices.

**And the filter name is not a label: it is a key.** Siril, PixInsight and the others group frames
by the value of `FILTER` to pair lights and flats. A wrong label you notice at once; a wrong
grouping you find out six months later, when the flats are not applied.

### The rule

**1 to 32 characters**, only `A-Z a-z 0-9` plus `_`, `-` and `.`, and **the first and last
character must be a letter or a digit**.

```
^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,30}[A-Za-z0-9])?$
```

Plus two checks a regex does not express: names **unique ignoring case** (`Ha` and `ha` are two
names for FITS and one folder on Windows and macOS), and the rejection of **Windows device
names** — `CON`, `PRN`, `AUX`, `NUL`, `COM1`…`9`, `LPT1`…`9`, also with an extension — because
`%F` is also a folder.

| constraint | where it comes from |
|---|---|
| printable ASCII only | FITS 4.0 §4.2.1.1. Mandatory, not advice |
| no `/ \ : * ? " < > \|` | the union of what Windows, macOS and Linux forbid — and Ekos does not sanitise |
| no space | FITS drops trailing spaces but keeps leading ones; INDI's XML parser does the opposite; and **our protocol** separates arguments with spaces |
| no `=` | answers are `key=value`: `ok n3=Green` |
| no leading `-` or `.` | a leading dash is taken for a command-line option, a leading dot hides the file on Unix |
| no trailing `.` or space | explicitly forbidden by Microsoft |

**Why 32 and not 68.** The FITS ceiling is 68 and ASCOM chooses 64 for its descriptions, but the
constraint that really bites is the path: `%F` appears twice, so 2 × 32 = 64, plus prefix,
exposure, sequence number and extension makes about 104 characters — comfortably within Linux's
255 and Windows' 260 even with a long destination folder. With 64 it would reach 170 and on
Windows files would start to be lost. **32 fits every constraint with twice the margin**, and
also keeps the protocol line `name 3 <text>` under 40 bytes.

### Refuse, do not correct

A name outside the rule is **refused with a message**, not silently fixed.

Every downstream layer corrects in its own way: cfitsio truncates, astropy puts `?`, Ekos
sanitises some fields and not others, the filesystem does something else again. If our code
corrected too, the user would find **the same filter with three different names in three
places** with no way to know which is the good one. Refusing is the only way to guarantee that
the name seen in the interface is identical, byte for byte, to the one in the header and the one
in the path.

And the cost is asymmetric: the name is written once and used thousands of times. A refusal costs
five seconds, once.

**It is sanitised anyway on the way out, as a safety net**, where the file name is composed and
where the keyword is written: a third-party INDI client can write `FILTER_NAME` without going
through our interface, and NVS may hold names saved before the rule existed (at start-up the
firmware ignores a stored name that fails the rule and keeps the default). If validation on the
way in does its job, that code never fires.

**The rule lives in `wheelly_protocol.h`** (`check_filter_name()`, `sanitize_filter_name()`,
`first_duplicate_name()`) and is applied in three places: in the firmware on the `name` command,
in the INDI driver before accepting `FILTER_NAME`, and one day on the ASCOM side. It must be
compiled identically on both sides, for the same reason the commands are. The simulator has a
Python copy of it, and the tests compare the two.

### What this rule breaks

| you would like | outcome | what to write |
|---|---|---|
| `Hα` | refused | `Ha`, or `H_Alpha`, which is INDI's default |
| `Luminosità` | refused | `Luminance` or `Lum` |
| `Baader 7nm` | refused for the space | `Baader_7nm` |
| `1.25"` | refused | `1_25in` |
| `R (Astrodon)` | refused | `R_Astrodon` |
| `L/RGB` | refused — and luckily so | in Ekos it would create a folder instead of an error |
| `O-III`, `L-eXtreme`, `Ha_3nm`, `SII`, `Lum`, `7nm_Ha` | **accepted** | they cover almost every real case |

The space is the case the rule breaks most often, and **Ekos already does exactly this
substitution** for the target name: the rule introduces no new convention, it makes it explicit.
And no name of INDI's default set is refused — `Red`, `Green`, `Blue`, `H_Alpha`, `SII`, `OIII`,
`LPR`, `Luminance` all pass. That INDI itself writes `H_Alpha` and not `Hα` says the prudent choice
had already been made upstream.

### The line for the documentation

> **Filter name** — 1 to 32 characters, only unaccented letters, digits, `_`, `-` and `.`; it
> must start and end with a letter or a digit. The limit is not a whim: this name ends up as is
> in the `FILTER` keyword of the FITS header, which the standard allows only in printable ASCII,
> and in the file name of the frame, where `/ \ : * ? " < > |` and the space are forbidden or
> dangerous on at least one of Linux, Windows and macOS. If you type `Hα` or `Baader 7nm` the
> software downstream gives no error: it silently changes the name — `Hα` is read back as `H??`
> — and stacking no longer pairs lights and flats. Type `Ha` and `Baader_7nm`.

---

## 7. How the firmware is built

Five files, and the cut between them is what matters most.

| file | what it does | Arduino? |
|---|---|---|
| `wheelly.ino` | powers things up and loops; wires the pieces together | yes, a hundred lines, mostly comments |
| `wheel.cpp` | **decides**: calibration, positioning, retries, verdict, drift watch | **no** |
| `dialog.cpp` | the protocol: from lines to commands and back; the LED (pulse, alarms, Morse) | **no** |
| `mechanics_esp32.cpp` | touches the wires: AS5600, TMC2208 (a TMC2209 is recognised too), step pulses, LED PWM | yes |
| `storage_esp32.cpp` | the NVS, through `Preferences` | yes |

The boundary is `mechanics.h`: the abstract `Mechanics` (sensor, motor, LED, clock) and `Storage`
(NVS) interfaces. **The two parts that decide contain not one line of Arduino**: they are
compiled for the PC too and run there under the tests. The same `Wheel` and the same `Dialog`
that end up on the XIAO pass **the very same tests as the simulator**, with a fake mechanics in
place of sensor and motor (`firmware/test/firmware_bench.cpp`).

Without this cut the only way to test the firmware would be to mount the wheel — and the cases
that really matter cannot be produced on demand: the friction drive slipping three times in a
row, the sensor falling silent in the middle of a move, the magnet disappearing, the memory not
being written. With the cut they are all produced with a command-line option.

**The firmware and the simulator are set against each other**: if they behaved differently, one
of the two would be wrong — and without the same tests on both nobody would notice until the
wheel was mounted.

`mechanics_esp32.cpp` is the only piece that cannot be tested without the real part, and is kept
thin on purpose: it decides nothing, it reads an angle, sends steps, lights a LED.

**The wiring**, as the board is soldered (from `mechanics/wheelly-cad/src/wiring.py`, the
drawing the board is built from; `firmware/test/test_pins.py` fails if the two drift):

| signal | XIAO pin |
|---|---|
| AS5600 SDA · SCL | D4 · D5 (3.3 V supply) |
| TMC2208 STEP · DIR · EN | D0 · D1 · D3 (EN with a 10 k pull-up to VIO: the driver stays off whenever the XIAO is not driving the pin). DIR is **inverted in the firmware** for J1 wired black A+, green A−, red B+, blue B− (section 3) |
| TMC2208 single-wire UART | D8 (TX, through 1 kΩ) · D9 (RX) |
| LED | D10, external |

**The main loop never blocks.** It does not wait on a read and uses no delays: `status` must be
able to answer while the wheel moves, and the LED's pulse, alarms and Morse are generated by
looking at the clock instead of stopping everything for seven seconds.

**Flashing**: `cd firmware && ./flash.sh wheelly` builds with `arduino-cli` (the one inside the
Arduino IDE on the Mac, the system one on the Raspberry, both with esp32 core 3.3.11), flashes
and opens the serial monitor.

---

## 8. How it is tested without hardware

The piece that unlocks everything is a **simulator**, `firmware/simulator/wheelly_sim.py`: a
program on the Mac or the Raspberry that speaks this protocol on a fake pty. With it
`indi-wheelly` is developed and tested **end to end in Ekos without a gram of hardware** — the
wheel appears, changes filter, gets it wrong, times out, declares `Alert` and stops the sequence.

It also produces the cases that are hard to produce on demand with the real hardware: the
friction drive slipping three times in a row, the sensor that stops answering mid-move, a wheel
drifting at rest, a firmware with a protocol version the driver does not know. The simulator has
switches for each (`--slip`, `--sensor-silent`, `--no-magnet`, `--drift`, `--nvs-broken`,
`--protocol-version`, …).

**All the firmware tests run on the Mac with one command, no hardware:**

```sh
firmware/test/run_all.sh
```

In order: the firmware's pins against the real board drawing (`test_pins.py`); the texts of the
air-gap test page; the shared header (`test_protocol.cpp`, via `test_protocol.sh`); the Python
simulator (`test_simulator.py`); the LED's Morse unit by unit (`test_morse.cpp`), its pulse
(`test_pulse.cpp`) and its alarm signals (`test_alarms.cpp`); the AS5600 field flags
(`test_field.cpp`); and finally **the real firmware**, `Wheel` and `Dialog` compiled for the PC,
put through the same tests as the simulator. That last step matters most: if firmware and
simulator did not behave the same, one of them would be wrong.

### Why a fake pty and not "simulation mode"

INDI offers a built-in simulation mode, and many drivers use it: a switch that, when on, makes
the driver return invented answers without touching the serial line. It is even accepted as an
alternative to testing on real hardware when proposing a driver.

**Rejected here**, for a single but heavy reason: simulation mode tests an `if` branch that **is
not the real code**. The protocol parser, the part that will really break, is never exercised —
and over time that branch drifts from the real code without anyone noticing. INDI's repository
already has a filter-wheel driver that exposes the simulation switch and **then uses it
nowhere**.

With a pair of connected ptys, instead, the driver opens an ordinary serial port, really writes
and reads, and at the other end a Python program plays the firmware line by line. The real parser
is tested, on the real path.

INDI's automatic port search enumerates only system devices and **will never find a pty**, so in
tests the port is set by hand. In real use the opposite happens: the driver gives INDI a pattern
that recognises the ESP32-S3's port, and the user is not even asked for it.

### Three levels of testing, from the cheapest to the most complete

1. **The parser, alone.** The driver would receive its communication channel from outside instead
   of opening it itself, so a test could pass it a fake channel and check the dialogue line by
   line, without `indiserver`. It is the technique of `indi-atik-efw`. **Not built yet**: the
   driver opens its own port through INDI's serial connection.
2. **The driver under `indiserver`**, against the simulator on a pty:
   `driver/indi-wheelly/driver_bench.py` runs the real compiled driver and talks to it in INDI's
   XML, as Ekos does. It can also be pointed at the firmware compiled for the PC instead of the
   simulator, which sets the two halves against each other once more. See
   `driver/indi-wheelly/README.md`.
3. **Ekos in front**, for the last mile: that the wheel appears, that a capture sequence changes
   filter, and above all that a failure **stops** the sequence instead of letting it go on in the
   dark.

---

## 9. What it stands on

Survey of repositories, commit dates, licences and open issues, checked rather than recalled
(September 2026; the figures below are from that survey).

| needed for | library | version | licence |
|---|---|---|---|
| TMC2208/2209 over UART | **`teemuatlut/TMCStepper`** | 0.7.3 | MIT |
| ~~TMC2209 over UART~~ | ~~`janelia-arduino/TMC2209`~~ | ~~10.1.1~~ | rejected, see below |
| AS5600 | **`RobTillaart/AS5600`** | 0.6.7 | MIT |
| STEP pulses | **`gin66/FastAccelStepper`** | 1.3.0 | MIT |

### Why these and not the usual ones

**For the motor driver, `TMCStepper`, although it is unmaintained.**

*Against it.* It is the library everybody cites, inherited from Marlin, 604 stars — and it has had
**no commit since 17 October 2021**, with 180 open issues and no fork standing to succeed it.
Issue #302, open since June 2024, describes exactly this case: the hardware UART no longer works
on ESP32 because Arduino-ESP32 3.x changed the default pins of UART1 and UART2, and nobody updated
the examples or the documentation.

*Rejected: `janelia-arduino/TMC2209`*, although it is alive, its maintainer answers, and it treats
the single wire as a first-class case. It assumes the module is a **TMC2209**. The module is not:
the chip is printed `TMC2208-LA`, and the `version` field of IOIN read over UART confirms it, at
`0x20`. janelia's library compares that field with `0x21` and **declares everything else
silent**: a healthy TMC2208, well wired and well powered, reads as a driver that does not answer.

*Why issue #302 does not bite.* The library never opens the UART. `TMC2208Stepper` is built with a
`Stream *`, and the firmware passes it `Serial1` **already opened with explicit pins**:
`Serial1.begin(BAUD, SERIAL_8N1, rx, tx)` before `driver.begin()`. The pin defaults, the heart of
the issue, the library never touches. The objection stays real for whoever uses the constructor
with pin numbers.

*What is gained.* A single class — `TMC2208Stepper` — speaks the subset common to 2208 and 2209,
which is all Wheelly uses, so the firmware accepts both silicons and says in `diag` which one it
found. And the current is set in **real milliamperes**, with `rms_current(mA)` and Rsense
0.110 Ω, with `I_scale_analog` off: the current comes from Rsense and IRUN alone, which took VREF
and its trimmer out of the design.

*What is lost.* A maintained library: if `TMCStepper` broke on a new core, there is no maintainer
to write to. The containment is that the firmware uses it for **a handful of calls**, all inside
`configure_driver()`, `apply_currents()` and `driver_name()`: replacing it would mean rewriting
those functions, not the firmware.

**For the AS5600, `RobTillaart` without rivals.** It is the only one that exposes the diagnostics
this project needs: `readStatus()` with the MD/ML/MH bits, `readAGC()`, `readMagnitude()`, plus
the three ready-made booleans (`magnetDetected()`, `magnetTooWeak()`, `magnetTooStrong()`), which
are what `status` sends. Zero open issues on 193 stars, regular releases. The alternatives are
stuck in 2022 or born and abandoned on the same day.

**For the pulses, `FastAccelStepper` and not `AccelStepper`.** `AccelStepper` is not abandoned, as
you read around — upstream is not on GitHub but on airspayce.com, at 1.66 of January 2026 — but
it generates each pulse from a call inside `loop()`, and on an ESP32 with USB CDC and FreeRTOS
tasks in between jitter is unavoidable. `FastAccelStepper` uses the hardware peripherals (RMT or
MCPWM/PCNT), is the only maintained Arduino library that does it on the S3, and is **the only one
that names `ESP32S3` explicitly** among its targets, with commits up to the survey.

### Four traps to put in the code at once

The first is still open in the libraries' trackers; the other three were paid for at the bench.

1. **Always pass explicit RX/TX pins to the UART.** The defaults changed with Arduino-ESP32 3.x and
   relying on them leads to a silent failure.
2. **Do not accept a silicon that was not recognised, and do not refuse a healthy one.** The
   `version` field of IOIN is `0x20` on a TMC2208 and `0x21` on a TMC2209: both are accepted and
   anything else is discarded, instead of trusting a single constant. It lives in
   `configure_driver()`.
3. **Ask the driver before every leg, and set it up again when it has forgotten.** The TMC2208's
   registers live on VM, the 12 V, not on the XIAO's 3.3 V. `pcb/README.md` and the assembly
   guide prescribe USB first and 12 V second, so **at boot the driver normally has no VM**: the
   setup written then reaches nobody, and when the 12 V arrive the chip starts from its reset
   values - current from the VREF trimmer, microsteps from the MS1/MS2 pins. A 12 V plug that
   drops and comes back does the same with the XIAO running. On the reference wheel a +10° jog
   moved **+2.28°** that way, and +9.76° and +9.84° after `diag` - which mended it only because it
   happened to redo the setup of a driver it had seen silent at boot; the moves asked nothing.
   Now `Wheel::check_driver()` runs before `go`, before `jog`, before every approach leg and
   retry, and in `diag`, one path for all. It reads three registers back (`mechanics.h`,
   `judge_driver`): **IOIN**'s version, to know a TMC2208 or 2209 answered with a good CRC;
   **GSTAT.reset**, which the chip sets at every reset and the setup clears at its end, so finding
   it set again means a reset since; **GCONF**, whose bits the setup writes (`pdn_disable`,
   `mstep_reg_select` on, `i_scale_analog`, `en_spreadcycle` off) and which must read back as
   written - a second witness, should GSTAT have been cleared by someone else. Not **IFCNT**, the
   counter of good writes: it tells a reset only against a count kept on the XIAO, it wraps at 256,
   and every write of the library moves it. Not IHOLD_IRUN or TPWMTHRS: write-only. Silent means
   the move is refused (error 6); reset or newly powered means the same `configure_driver()` as at
   boot, the wheel's currents applied again, and the `! driver` event. The reading costs three
   rounds of UART before a leg, never during one. The rule is a pure function so the Mac bench runs
   it against a fake register file that loses its setup with the 12 V (`--vm-off-for`,
   `--vm-drop-after-moves`, `--vm-lost-after-moves`); `test_driver_check.cpp` tries each witness
   alone.
4. **Do not trust a `0` read from a driver register.** If a read times out the library returns 0,
   which for many registers is a legitimate value: false but plausible data. It must be
   cross-checked with the AS5600, which is the reference of truth anyway.

**Core constraint:** `FastAccelStepper` **does not build** with Arduino core 3.0.x. It needs
≥ 3.1.0. The Mac and the Raspberry have **3.3.11** — but a core pinned to a 3.0.x makes the build
fail with an unhelpful error.

**A diagnostic that circulates and does not apply here:** the AS5600 documentation and half the
Internet say to set the air gap by bringing the AGC to mid-scale. With this module at 3.3 V **it
does not work**: the AGC stays nailed at 128 at any height (measured). Calibration is done on the
**magnitude**, as measured at the bench and written in `hardware.md`. The same goes for the
firmware: `diag` warns below a magnitude of 350.

---

## 10. The road not taken: speaking Xagyl

The serious alternative, and it partly contradicts the criterion "start from standard things".

INDI has shipped for years the drivers of several serial wheels: **Xagyl**, Quantum, Trutek, Optec
IFW, Manual. If the firmware spoke one of those protocols — the best fit would be Xagyl, whose de
facto specification is the source `xagyl_wheel.cpp`, stable for over five years — **on the
Raspberry side there would not be a line to write or maintain**. There is even a third-party
Xagyl-compatible Arduino firmware (`chemistorge/…`, GPL-3.0, updated in January 2026), useful as a
reading of the protocol.

It would be the most rigorous reading of "standard and already maintained". **Rejected**, for a
single but decisive reason: the Xagyl vocabulary cannot say the things this wheel must say.

- It has no **explicit save** set against a live, volatile calibration.
- It has no **two tolerance thresholds** nor the "report but proceed" semantics.
- It has **nowhere to put magnitude, AGC and the MD/ML/MH bits** — the diagnostics that found the
  faults at the bench.
- It has fields of its own that mean nothing here (*Pulse Width*, *Jitter*), because they
  describe a different machine: a stepper with a Hall sensor and step counting.

So: our protocol and our driver — and **the "standard and maintained" constraint is respected
where it really counts**, in the three libraries of section 9 and in the `INDI::FilterWheel` base
class, which is the real piece of infrastructure.

### And one more reason

Pretending to be a Xagyl looks like it would give **the ASCOM driver too** for free. It does not.

**Xagyl as a company no longer exists.** Its site redirects to another brand, and Xagyl **no longer
appears** in ASCOM's list of filter-wheel drivers, where a single entry is left. The ASCOM driver is
closed-source, so **there is no way to know what checks it makes**: the INDI one is tolerant, the
other may not be, and it cannot be checked without the device in hand.

And the wheel would appear under another brand's name in its user's software, and whoever had a
problem would write to them. A home-printed Xagyl-compatible wheel has solved this by answering the
identification request with a name of its own — compatible with the protocol without passing for
someone else. It is the bare minimum, if this road were ever taken.

The right candidate to imitate would not be Xagyl but **Optec IFW**, whose protocol is documented by
the manufacturer and which is the only wheel driver still listed by ASCOM. But the basic objection
stands: the vocabulary cannot say what this wheel must say.

---

## 11. The road to ASCOM

The requirement: the wheel must be able to work with N.I.N.A. too. The decision is **that the road
exists, not that it is travelled now**: which it is, what it costs, and what must not be got wrong
today so as not to pay dearly tomorrow.

### The four roads, with numbers

| | lines to write | needs Windows to develop? | the user installs | can it be validated from the Mac? |
|---|---|---|---|---|
| Classic ASCOM COM driver | 2000–3000 in C# | **yes** | Platform + installer + signature | **no** |
| Alpaca inside the firmware | 300–500 in C++ | no | **nothing** | yes |
| A serial→Alpaca bridge | 800–1500 | no | one executable | yes |
| Pretending to be a supported wheel | ~200 | no | a third party's driver | only on the INDI side |

**Rejected: the classic COM driver**, and not because it is a lot of code. It must be built, tested
**and validated** on Windows with Visual Studio, and the official validation tool checks COM drivers
**only** on Windows. Add an installer, COM registration, and code signing: ASCOM does not require it,
but Windows does in practice, because an unsigned binary never builds reputation and shows the
security warning **at every version, forever**. Signing costs a few hundred euros a year and since
2023 wants the key on a hardware token. For a project maintained by one person it is a recipe for
abandonment — and the ASCOM driver of the most cited home-made wheel was archived in January 2026.

**Alpaca is the road ASCOM itself recommends**, and on Windows **nothing is installed**: no
installer, no COM registration, no signature, no security warning. N.I.N.A. speaks Alpaca natively;
users of older programs go through the Platform's chooser once and then find it as an ordinary
driver.

### The snag: Alpaca wants an IP address

And the XIAO connected over USB **does not have one**. Alpaca is HTTP: without a network there is
nothing to talk to. Three ways out.

**Rejected: the XIAO's WiFi.** It is the road of commercial Alpaca devices, but here it costs more
than it seems. The only maintained Alpaca library for ESP32 with the filter wheel already
implemented **is written for ESP-IDF, not Arduino**: adopting it would mean overturning the
firmware's foundations and giving up the three libraries of section 9. And there are three physical
problems: the ESP32-S3 does only 2.4 GHz and would sit twenty centimetres from USB 3 cameras that
interfere on that band; the radio's power saving is **on by default** and must be turned off
explicitly, or the radio goes off intermittently; and device discovery travels on packets many home
networks filter.

**Unexplored: Ethernet over USB.** The XIAO would present itself as a network card and take an IP on
a point-to-point link: no radio, no shared network, only the cable already there. Technically the
most elegant solution and ESP-IDF supports it — but **there is no precedent** of an Alpaca device
served this way in astronomy. Worth an afternoon of trial before committing to it.

### The chosen road: a bridge on the Raspberry

**A small program on the Raspberry that speaks our serial protocol on one side and exposes Alpaca on
the other.** The Raspberry is already on, already on the network, and already attached to the wheel:
it adds no piece.

On Windows nothing is installed. The firmware **stays Arduino** with the three chosen libraries. No
WiFi on the XIAO, so none of the three problems above. And the bridge is thin, because the Alpaca
interface of a filter wheel is **four things in all**: the position, the names, the focus offsets
and the connection state. All four our protocol can already say.

### What must not be got wrong, and concerns today

**Two rules the official validator checks**, which our protocol already respects:

- Writing the position must be **asynchronous** — the command returns at once and the move goes on.
  A driver that waits is failed. Our `go` already does so.
- During a move the position must be reported as **−1**, and never a valid slot number while the
  wheel is passing in front of the slots. Our `status` already has `pos=0` for "between slots or
  moving" and the `motion` field: the bridge translates, it does not have to invent.

**And a trap to mark in capital letters.** ASCOM has a property called `FocusOffsets`, and **it has
nothing to do with the rotation trim** of protocol 1 (section 5.1, "Offset"). That was an
**angular** correction, how much more to rotate to centre the filter. ASCOM's is how much to move
the **focuser** when that filter is chosen, because filters of different thickness move the focal
plane. Confusing them would make the focus move by a meaningless amount at every filter change.
Until there are real focus offsets, `FocusOffsets` returns **a row of zeros** — not an empty list,
not an error — and it must be **as long as the list of names**, which the validator really checks.

The validator **also runs on macOS** when the device is Alpaca. So the bridge can be certified
without a Windows machine.

---

## 12. How it notices being out of position, and how it says so

The warning comes out of three different doors, because they answer three different questions.

### Inside Ekos — the standard mechanism, and not optional

A message in the driver's log, plus the state of `FILTER_SLOT`: `Alert` when the positioning
failed, and the capture sequence stops by itself. In the middle band — outside the `good` tolerance
but within `warn` — the message is there all the same but the state stays `Ok`, so the sequence goes
on: "report but proceed". A drift at rest and a lost magnet are written in the log too, the drift
with the suggested remedy (section 2.4).

It answers: **is it happening now, and am I looking at the screen?**

### A LED on the wheel — off, except when it is needed

The external diagnostic LED foreseen in `hardware.md`. What is written there holds: **off while the
wheel works**, lit only on an anomaly, and **it can be switched off altogether** — as a real,
reachable option, not buried. The assembly is a few centimetres from the cooled sensor and inside
the optical path, so every photon it emits is a photon that ends up in the exposures.

It answers: **I am in the garden in the dark and have no computer in front of me.**

What it does (section 4.5, "The LED", for the details): in the default `pulse` mode it is off at
rest and breathes softly while the wheel changes filter — the one deliberate exception to "off while
it works", at 5–30% brightness; and it signals the
three anomalies with three distinct patterns — **fast blinking** for a slot not reached, **two
flashes every 2 s** for a drift at rest, **three flashes every 2 s** for a lost magnet. In `off` mode
it shows nothing at all, alarms included. The mode is chosen in *Options → LED* and kept in the
wheel with *Save to the wheel*.

A LED that stays off by definition is a LED you never know is working, so there is the **Test**
button, which blinks `Wheelly` in Morse (the `led test` command). It is used with the cover open or
in daylight, because it blinks at full brightness (as does the `on` mode, which is there for whoever
wants it), and the log says so when it starts.

### A log file — **optional, off by default**

Two separate things.

**INDI already has its own file log**, turned on from the driver's Options tab. It is for digging
into a problem, it is verbose, and it is turned on for the occasion.

The second is ours and answers another question: **one CSV line per move**, in
`~/.indi/wheelly_movements.csv`, with the columns
`timestamp,slot,target,angle,error,retries,outcome,agc,magnitude` (the timestamp in UTC). A file that
opens in a spreadsheet and is read in ten seconds — the same idea as the air-gap sketch, which
prints pasteable CSV, taken from the bench into service.

It answers: **is it getting worse night after night?** An angle that keeps being corrected (its
`angle-set` rows) or a magnitude that falls shows up there well before it shows up in a spoiled
exposure.

**It stays off unless it is turned on**, from a switch in Ekos (`WHEELLY_LOG`), and the choice is
remembered between sessions like the driver's other preferences. By default the wheel writes nothing
to disk.

---

## 13. Languages: everything through keys, English and Italian

No user-facing string is written inline in the code. Each one has a **key**, and the texts are in
separate catalogues, one per language. The starting languages are **English and Italian**. In the
driver the catalogues are `driver/indi-wheelly/translations.cpp` and `translations_it.cpp`.

It has to be set up before writing: introducing keys afterwards means going through every string
already written, one by one — the kind of work that never gets done.

### What is translated and what is not

**The protocol is not translated.** The words of the commands and the names of the fields are not
prose: they are **identifiers**, and they must stay the same forever, in one language. Translated,
a firmware and a driver of different languages would no longer talk to each other.

| | language |
|---|---|
| commands, fields, events on the wire; INDI property names | **one, English, fixed forever** |
| everything a human reads in Ekos or on a page | **theirs** |
| the `#` diagnostic lines and the English tail of `error` lines | English, always: they are for the developer |

The criterion to tell which side a string is on: **if a machine reads it, or whoever is watching the
raw serial, it is English and never changes. If the user reads it, it has a key and a translation.**

### Translations live on the host, not in the firmware

**The XIAO has no catalogues.** When something goes wrong the firmware sends the **error code**, the
**parameters** as named fields, and a very short English text for whoever is watching the raw
serial:

```
error 3 expected=1..5 got=7 slot out of range
```

The **code is the key**, and the fields are the parameters. The driver looks the code up in the
catalogue of the user's language and builds the sentence.

It pays twice. The wire **stays readable by hand**, the value this whole protocol is built on. And
adding a language, or fixing a translation, **does not require reflashing the wheel**: only the host
is touched. Catalogues in the firmware would use flash for texts someone reads once a year, and
need a reflash to add French.

### Three rules against the classic damage

**One key, one whole sentence.** Never build a sentence by gluing pieces translated separately: word
order changes from language to language, and the result is wrong grammar that nobody rereads. The
key carries the whole sentence, with placeholders inside for the parameters.

**English is the safety net.** If a key is missing from the Italian catalogue the English is shown,
never the bare key and never an empty string. A missing translation must be a small annoyance, not a
broken interface.

**Filter names stay ASCII anyway.** Multilingual concerns the interface, not the data: the interface
can be in Italian, but a filter cannot be called `Luminosità`, for the reasons of section 6. They are
two different questions and must be kept apart, or one ends up "widening" the name rule believing
oneself consistent.

### How it chooses the language, in practice

The choice is in **Options → Language**: *From the system* (the default), *English*, *Italian* —
because in an observatory the system may be in one language and the interface wanted in another.
*From the system* reads `LC_ALL`, `LC_MESSAGES` and `LANG`, in that order, and picks Italian when the
first one set starts with `it`, English otherwise. INDI has **no translation mechanism** of its own:
property names are fixed identifiers, but **labels** are free text, and that is where the translated
strings go, when the properties are created.

The labels are built once, when the driver starts, and INDI clients keep the labels they received.
So **changing the language takes effect when the driver is started again** (in Ekos: stop INDI and
start it), not at once and not at a mere reconnection. The driver says so in the log when the choice
changes, instead of letting it be taken for a bug.

The catalogue is compiled into the driver, not read from a separate file: one file fewer to install,
to find and to lose, and no external dependency. The Italian catalogue is a CMake option
(`WHEELLY_ITALIAN`), so a build carried in INDI's tree can be English only.

---

## 14. Still to decide

- **Proposing `indi-wheelly` to INDI's main repository**, as the criterion says, or keeping it out to
  have releases independent of the core's cycle (section 5.2; what would be handed over is in
  `driver/indi-wheelly/upstream/`). It is not a technical decision but one of commitment: proposing
  it upstream means taking on maintenance in public.
- **When to make the Alpaca bridge**, if it is ever really needed. Today it is documented, and that
  is all.
- **The tolerances** (section 2.3): tighter values once the movement log shows the real errors in
  the field.
- **The drive ratio** (section 3): declared from the model; to be measured on the part with
  `firmware/ratio_test.py`.
