#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""Simulator of the Wheelly wheel: it mimics the firmware, with no hardware.

What it is for. The INDI driver can be written and tested in full before a
gram of electronics exists: the wheel shows up in Ekos, changes filter, gets it
wrong, retries, fails and stops the imaging sequence. It is also the only
comfortable way to try the cases that are hard to produce on demand with the
real hardware - the clutch slipping three times in a row, the sensor going
silent half-way through a move, the magnet disappearing.

Two ways to connect, the same engine behind:

    ./wheelly_sim.py --pty                prints the name of a fake serial port,
                                          and the INDI driver is pointed there
    ./wheelly_sim.py                      dialogue on stdin/stdout, for the
                                          automatic tests and for trying by hand

The knobs for breaking things on purpose are listed by --help; the most useful
are --slip, --stuck, --sensor-silent and --no-magnet.

Commands and fields are NOT written here: they are read from wheelly_protocol.h,
the same file the firmware and the driver compile. See protocol.py.
"""

import argparse
import fcntl
import math
import os
import random
import select
import sys
import termios
import threading
import time

import protocol as P


# ---------------------------------------------------------------- geometry

def normalise(degrees):
    """Brings an angle back into [0, 360)."""
    return degrees % 360.0


def difference(a, b):
    """Difference a - b along the shortest way, in (-180, +180]."""
    return (a - b + 180.0) % 360.0 - 180.0


# ------------------------------------------------------------ move time cap
#
# A copy of Wheel::ceiling_ms() in wheel.cpp, and of the numbers
# it uses from wheel.h and mechanics.h. Python cannot include them; the tests
# ask both halves for the cap at the same settings and demand the same number,
# so a copy that drifts from the original is heard.
MICROSTEPS = 16


def steps_per_degree(ratio):
    """wheel.h's steps_per_degree(): microsteps of motor per degree of disc at
    a drive ratio. The ratio is a setting, whose factory
    value comes from the header (FACTORY_DRIVE_RATIO, derived there)."""
    return 200.0 * MICROSTEPS / 360.0 * ratio


# The fake DISC's own physics, written apart from the firmware's estimate as
# the firmware bench does: a 50 mm clutch on the rim of a 145 mm
# disc, then off by --ratio-error. Not the header's numbers on purpose: a
# wrong ratio or unit in the estimate must show as a disc that goes elsewhere.
PHYSICS_RATIO = 145.0 / 50.0
# The settling wait is a setting (`settle`, the wheel's
# settle_ms; FACTORY_SETTLE_MS in the header): no copy of it here.
# The TMC2208's own drop from the run to the hold current, 0.44 s after the
# last step (TPOWERDOWN = 20 x 2^18 clocks at 12 MHz), for the coasting model
# (--coast): the same number as the firmware bench.
POWERDOWN_S = 0.437
CEILING_MARGIN = 1.25
CEILING_ALLOWANCE_S = 1.0
LONGEST_SHORTEST_DEG = 180.0
LONGEST_ONE_WAY_DEG = 720.0
# The aim short and the approach legs: copies of the constants
# in wheel.cpp, whose comments say why each is what it is.
UNDERSHOOT_FRACTION = 0.12
UNDERSHOOT_MIN_DEG = 1.0
LAST_LEGS_SHARE = 0.6
APPROACH_LEGS_MAX = 10
NO_PROGRESS_SHARE = 0.2
SHORT_LEG_DEG = 5.0
LOST_STEP_DEG = 0.2
LOST_MAX_DEG = 2.0
# a jog's own good tolerance: half its size, not below half an AS5600 count
# (see Wheel::jog() in wheel.cpp)
JOG_GOOD_MIN_DEG = 0.044
# a jog that did not cover half of itself is not a warning, and a half-turn
# jog goes the way its sign says (see wheel.cpp)
JOG_MOVED_SHARE = 0.5
JOG_TIE_DEG = 1.0
# The learning of the drive ratio: copies of the constants in
# wheel.cpp, whose comment says why each guard is there.
LEARN_MIN_DEG = 30.0
LEARN_OUTLIER = 0.15
LEARN_WEIGHT = 0.25
LEARN_CLAMP = 0.15
# The hysteresis on a lost magnet, a copy of MAGNET_REARM_MS in wheel.h
#: the next loss is reported only after the magnet has been seen
# without a break for this long.
MAGNET_REARM_S = 1.0
# --magnet-flicker: in the first FLICKER_BURST_S of every FLICKER_CYCLE_S the
# magnet-detected bit toggles every N ms, then it stays solid. The same
# pattern as the firmware bench, from the start of the process.
FLICKER_BURST_S = 1.5
FLICKER_CYCLE_S = 4.0


def ceiling_ms(speed, acceleration, retries, direction, ratio=P.FACTORY_DRIVE_RATIO,
               settle_ms=P.FACTORY_SETTLE_MS):
    """The cap on a whole positioning, as the firmware derives it: the path
    counted at the BASE ratio (see Wheel::ceiling_ms)."""
    v = speed * MICROSTEPS
    a = acceleration * MICROSTEPS
    path = (LONGEST_SHORTEST_DEG if direction == P.ARG_SHORTEST
            else LONGEST_ONE_WAY_DEG) * steps_per_degree(ratio)
    travel = 2.0 * math.sqrt(path / a) if path <= v * v / a else path / v + v / a
    per_leg = settle_ms / 1000.0 + v / a
    legs = 1 + APPROACH_LEGS_MAX + retries
    seconds = CEILING_MARGIN * (travel + legs * per_leg) + CEILING_ALLOWANCE_S
    return int(math.floor(seconds * 1000.0 + 0.5))   # lroundf, not banker's round


# ------------------------------------------------------------------- wheel

class Wheel:
    """The state of the wheel and its physics, with nothing of the protocol.

    The separation is deliberate and is the same the firmware has: in here
    nothing is known about lines of text, and the dialogue knows nothing about
    angles.
    """

    def __init__(self, options):
        self.o = options
        self.rng = random.Random(options.seed)

        # How many positions this wheel has is a fact of the wheel, not of
        # the code: a single firmware serves different wheels.
        self.slots = options.slots
        self.spread_evenly()
        # What the NVS holds, from --nvs: the keys of an older firmware. The
        # simulator keeps no other memory (`save` only counts), so this is only
        # the angles and the rotation trims of protocol 1, folded once into the
        # angles at every start as Wheel::fold_old_trims() does.
        self.nvs = {}
        for pair in filter(None, (options.nvs or "").split(",")):
            key, _, value = pair.partition("=")
            self.nvs[key.strip()] = float(value)
        for _ in range(max(1, options.boots)):
            self._load_angles()
        # the ratio's keys, as Wheel::load_or_default()
        saved = self.nvs.get("ratio")
        self._saved_ratio = saved if saved is not None and \
            P.DRIVE_RATIO_MIN <= saved <= P.DRIVE_RATIO_MAX else None
        self._saved_learn = self.nvs.get("ratio_learn")
        # the settling wait, as Wheel::load_or_default(): a
        # saved value out of range is a corrupted key, and not taken
        saved = self.nvs.get("settle_ms")
        self.settle_ms = int(saved) if saved is not None and \
            0 <= saved <= P.SETTLE_MS_MAX else P.FACTORY_SETTLE_MS
        # the disc's inertia (--coast): set when a leg stops, spent at release
        self._t_stopped = 0.0
        self._coast_sign = 1.0
        self._coast_pending = False

        self.angle = self.angles[0]
        self.motion = P.MOTION_IDLE
        self.wanted_slot = 1              # 1..SLOTS
        self.target = self.angles[0]
        self.retries = 0                  # corrections: after a stall or an overshoot
        self.legs = 0                     # every leg of the positioning
        self._approach_legs = 0           # the free ones, of the aim short
        self.boosts = 0                   # legs at the boosted speed, after a stall
        self._boost_next = False
        self._leg_speed = 0               # full steps/s of the leg under way
        self._leg_from = 0.0
        self._leg_distance = 0.0
        self._leg_commanded = 0.0
        self._leg_aim = 0.0
        self._lost = 0.0                  # learnt lost motion, kept across moves
        self._lost_known = False          # a short leg that moved was judged
        # the drive ratio: the base it starts from and the one
        # in use, refined by the learning; as Wheel in the firmware
        self.base_ratio = P.FACTORY_DRIVE_RATIO
        self.ratio = P.FACTORY_DRIVE_RATIO
        self.learn = True
        self.learnt = 0
        self._leg_ratio = self.ratio
        self._leg_steps = 0
        self._leg_kind = P.KIND_FIRST
        self._leg_magnet_ok = True
        self.report_legs = False          # `legs on|off`, never saved
        self._jogging = False             # the positioning is a jog: shortest way
        self._jog_from = 0.0              # where the jog started
        self._jog_degrees = 0.0           # and how far it was asked to go
        self._good_now = P.FACTORY_GOOD_DEG   # the good tolerance of this positioning
        self._leg_sign = 1
        self.outcome = P.OUTCOME_NONE     # verdict of the last positioning
        self._drift_out = False           # already out of tolerance right now
        self._magnet_lost = False         # "! sensor" already sent for this loss
        self._magnet_since = None         # seen without a break since then
        self._born = time.monotonic()     # the flicker's clock
        self._last_step = 0.0
        self.direction = "+"
        self.start = self.angle

        self.tolerance_good = P.FACTORY_GOOD_DEG   # from the header
        self.tolerance_warn = P.FACTORY_WARN_DEG
        self.max_retries = 3

        # the factory values, all from the header
        self.run_current = P.FACTORY_RUN_MA
        self.hold_current = 0             # 0 = released, and it is the default
        self.speed = P.FACTORY_SPEED
        self.acceleration = P.FACTORY_ACCEL
        # which way it may turn: the shortest way, see FACTORY_DIRECTION in
        # the header
        self.turn = P.FACTORY_DIRECTION

        self.led_lit = False
        self.led_enabled = True
        self.led_test_end = 0.0
        # on / pulse / off: pulse by default, as in the firmware (Wheel)
        self.led_mode = P.ARG_PULSE

        self.saves = 0
        self.moves_done = 0
        if self._saved_ratio is not None:
            self.base_ratio = self.ratio = self._saved_ratio
        if self._saved_learn is not None:
            self.learn = self._saved_learn != 0.0

        # animation in progress
        self._landing = self.angle        # where it will really land
        self._travel = 0.0                # signed degrees of the leg under way
        self._t_move_end = 0.0
        self._t_settle_end = 0.0
        self._deadline = 0.0              # overall ceiling, as in the firmware

        self.events = []                  # unsolicited lines to send
        self._lock = threading.Lock()

        # The motor driver and its 12 V (--vm-*): the firmware bench's model
        # (FakeMechanics::supply), read by the firmware's rule. Powered from
        # the start, it is found set up, as MechanicsEsp32::begin() leaves it.
        self._vm = self.o.vm_off_for <= 0
        self._driver_seen = self._vm
        self._driver_set_up = True
        self._vm_dropped = False

    def spread_evenly(self):
        """Angles split into equal parts and generic names: it is not the real
        calibration, but a sensible starting point, usable at once."""
        step = 360.0 / self.slots
        self.angles = [normalise(i * step) for i in range(self.slots)]
        factory = ["Lum", "Red", "Green", "Blue", "Ha"]
        if self.slots == P.FACTORY_SLOTS:
            self.names = list(factory)
        else:
            self.names = [f"Filter{i + 1}" for i in range(self.slots)]

    def _load_angles(self):
        """One start: the saved angles, then the old trims folded in and their
        keys erased, as Wheel::load_or_default() and fold_old_trims()."""
        for i in range(self.slots):
            if f"a{i + 1}" in self.nvs:
                self.angles[i] = normalise(self.nvs[f"a{i + 1}"])
        for i in range(P.MAX_SLOTS):
            trim = self.nvs.pop(f"o{i + 1}", None)
            if trim is not None and i < self.slots and trim != 0.0:
                self.angles[i] = normalise(self.angles[i] + trim)
                self.nvs[f"a{i + 1}"] = self.angles[i]

    # -- sensor -----------------------------------------------------------

    @property
    def sensor_silent(self):
        return self.o.sensor_silent or (
            0 <= self.o.sensor_silent_after <= self.moves_done
        )

    # -- motor driver -----------------------------------------------------

    def _supply(self):
        """The 12 V now, from --vm-*: their arrival, and every drop and
        return, put the driver at its reset values (mechanics.h)."""
        vm = (time.monotonic() - self._born) * 1000.0 >= self.o.vm_off_for
        if 0 <= self.o.vm_lost_after_moves <= self.moves_done:
            vm = False
        if vm and not self._vm:
            self._driver_set_up = False
        if vm and not self._vm_dropped and 0 <= self.o.vm_drop_after_moves <= self.moves_done:
            self._vm_dropped = True
            self._driver_set_up = False
        self._vm = vm

    @property
    def driver_responds(self):
        self._supply()
        return self._vm

    def check_driver(self):
        """Wheel::check_driver(): False if the driver is silent; set up
        again, with the `! driver` event, if it answers without its setup."""
        self._supply()
        if not self._vm:
            self._driver_seen = False
            return False
        if not self._driver_set_up:
            reason = P.V_RESET if self._driver_seen else P.V_POWER
            self._driver_set_up = True
            self.events.append(f"{P.PREFIX_EVENT} {P.EV_DRIVER} {P.F_REASON}={reason}")
        self._driver_seen = True
        return True

    @property
    def magnet_seen(self):
        if self.o.no_magnet:
            return False
        if self.o.magnet_flicker > 0:
            t = (time.monotonic() - self._born) % FLICKER_CYCLE_S
            if t < FLICKER_BURST_S:
                return int(t * 1000.0 / self.o.magnet_flicker) % 2 == 1
        return True

    def magnitude(self):
        """Drops by about 15% over the whole useful air-gap range, and has a
        once-per-turn modulation: the eccentricity of the magnet. Numbers
        taken from the real bench measurements, see hardware.md."""
        base = 810.0
        eccentricity = 25.0 * math.sin(math.radians(self.angle))
        return int(base + eccentricity + self.rng.uniform(-4, 4))

    def agc(self):
        # With this magnet at 3.3 V the AGC stays at full scale at any
        # height: the finding that made the AGC criterion be dropped in
        # favour of the magnitude. The simulator lies the same way.
        return 128

    # -- motion -----------------------------------------------------------

    def arrival_error(self, attempt):
        """How much the target is missed by, in degrees."""
        if self.o.stuck:
            # never converges: used to prove that the retries end and that
            # the driver declares the failure instead of waiting forever
            return self.o.slip_degrees

        error = self.rng.gauss(0.0, self.o.noise_degrees)
        if self.rng.random() < self.o.slip:
            error += self.rng.choice([-1.0, 1.0]) * self.o.slip_degrees
        # a correction starts already close: the residual error shrinks
        return error * (0.2 ** attempt)

    def go(self, slot, now):
        with self._lock:
            self.wanted_slot = slot
            self._jogging = False
            self._good_now = self.tolerance_good
            self.target = self.angles[slot - 1]
            return self._start_positioning(now)

    def jog(self, degrees, now):
        """The firmware's Wheel::jog(): to the angle read now plus `degrees`,
        closed loop, the shortest way whatever the direction setting, judged
        by half the jog's size (at least half an AS5600 count, at most the
        good tolerance). The slot asked for last stays the events' one."""
        with self._lock:
            self._jogging = True
            self._good_now = min(self.tolerance_good, max(JOG_GOOD_MIN_DEG, 0.5 * abs(degrees)))
            self._jog_from = self.angle
            self._jog_degrees = degrees
            self.target = normalise(self.angle + degrees)
            return self._start_positioning(now)

    def _start_positioning(self, now):
        """What go() and jog() share; called with the lock held."""
        self.retries = 0
        self.legs = 0
        self._approach_legs = 0
        self.boosts = 0
        self._boost_next = False
        self.outcome = P.OUTCOME_NONE
        self._drift_out = False
        self._deadline = now + self.ceiling_ms() / 1000.0
        self._leg_kind = P.KIND_FIRST
        self._start_leg(now)
        return self.target, self.start, self.direction

    def ceiling_ms(self):
        return ceiling_ms(self.speed, self.acceleration, self.max_retries, self.turn,
                          self.base_ratio, self.settle_ms)

    def set_ratio(self, ratio):
        """Wheel::set_ratio(): the base, and the learning restarts from it.
        The range and the motion are checked by the dialogue."""
        with self._lock:
            self._lost *= self.ratio / ratio      # the play, kept in steps
            self.base_ratio = self.ratio = ratio
            self.learnt = 0

    def set_learning(self, on):
        """Wheel::set_learning(): off drops the refinement, the base alone."""
        with self._lock:
            self.learn = on
            if not on and self.ratio != self.base_ratio:
                self._lost *= self.ratio / self.base_ratio
                self.ratio = self.base_ratio
                self.learnt = 0

    def save(self):
        """Wheel::save() for what the simulator keeps: the ratio in use
        becomes the base, and goes in the memory with the learning switch."""
        with self._lock:
            self.nvs["ratio"] = self.ratio
            self.nvs["ratio_learn"] = 1.0 if self.learn else 0.0
            self.nvs["settle_ms"] = float(self.settle_ms)
            self.base_ratio = self.ratio
            self.learnt = 0
            self.saves += 1

    def _start_leg(self, now):
        """The firmware's Wheel::start_leg(): the way round is chosen on the
        target, one way the leg aims short of it, and the fake mechanics adds
        its errors to the landing: the ratio error and the slip."""
        self.start = self.angle
        delta = difference(self.target, self.angle)
        if self.turn != P.ARG_SHORTEST and not self._jogging:
            # one way, retries included: after an overshoot, round the whole
            # turn; already within the good tolerance, no move at all
            if abs(delta) <= self.tolerance_good:
                delta = 0.0
            elif self.turn == P.ARG_UP:
                delta = normalise(self.target - self.angle)
            else:
                delta = -normalise(self.angle - self.target)
            self._leg_sign = 1 if self.turn == P.ARG_UP else -1
            self._leg_distance = d = abs(delta)
            # the aim short: see wheel.cpp
            aim = d
            if d > 2.0 * UNDERSHOOT_MIN_DEG:
                aim = d - max(UNDERSHOOT_FRACTION * d, UNDERSHOOT_MIN_DEG)
            elif d > self.tolerance_good:
                aim = LAST_LEGS_SHARE * d
            delta = -aim if delta < 0 else aim
        else:
            # half a turn has no shorter way: a jog goes the way it was asked
            if self._jogging and abs(delta) > 180.0 - JOG_TIE_DEG \
                    and (delta < 0) != (self._jog_degrees < 0):
                delta = -(360.0 - abs(delta)) if self._jog_degrees < 0 else 360.0 - abs(delta)
            self._leg_sign = 1 if delta >= 0 else -1
            self._leg_distance = abs(delta)
        self.direction = "+" if self._leg_sign > 0 else "-"
        self._leg_from = self.angle
        self._leg_aim = abs(delta)
        commanded = self._leg_aim + self._lost if self._leg_aim > 0 else 0.0
        self._leg_commanded = -commanded if delta < 0 else commanded
        self.legs += 1
        # the boost after a stall: this one leg at twice the speed, capped
        speed = self.speed
        if self._boost_next:
            speed = max(self.speed, min(2 * self.speed, P.BOOST_SPEED_MAX, P.MOTOR_SPEED_MAX))
            if speed > self.speed:
                self.boosts += 1
            self._boost_next = False
        self._leg_speed = speed
        # The asymmetric detent: the steep flank stalls the motor, which hums
        # for the time of the move while the disc stays where it is.
        commanded = self._leg_commanded
        stalled = (self.o.stall == P.ARG_UP and commanded > 0) or \
                  (self.o.stall == P.ARG_DOWN and commanded < 0)
        error = 0.0 if stalled else self.arrival_error(self.legs - 1)
        # The steps, at the ratio in use, as Wheel::start_leg().
        steps = int(math.floor(abs(commanded) * steps_per_degree(self.ratio) + 0.5))
        self._leg_steps = -steps if commanded < 0 else steps
        self._leg_ratio = self.ratio
        self._leg_magnet_ok = True
        # the fake drive, from the STEPS and its own physics: the degrees of
        # disc they are worth at the model's diameters, less --lost-motion
        # (the tyre's give), then off by --ratio-error
        nominal = steps / steps_per_degree(PHYSICS_RATIO)
        through = max(0.0, nominal - self.o.lost_motion) * (1.0 + self.o.ratio_error)
        through = self._notch(through, -1 if commanded < 0 else 1)
        through = -through if commanded < 0 else through
        self._travel = 0.0 if stalled else through + error
        self._landing = normalise(self.start + self._travel)
        # as long as the disc really travels, like the firmware bench; a
        # stalled leg hums for the time the steps take
        duration = (abs(commanded) if stalled else abs(self._travel)) \
            * self.o.ms_per_degree / 1000.0
        self._t_move_end = now + duration
        self._t_settle_end = self._t_move_end + self.settle_ms / 1000.0
        self.motion = P.MOTION_MOVING

    def _notch(self, through, sign):
        """The notch that stalls a slow motor (--notch-at, --notch-min-speed):
        a leg slower than that, crossing it, stops half a degree before it.
        The same model as the firmware bench."""
        if self.o.notch_at is None or self._leg_speed >= self.o.notch_min_speed:
            return through
        to_notch = normalise(sign * (self.o.notch_at - self.angle))
        if to_notch < through:
            return max(0.0, to_notch - 0.5)
        return through

    def stop(self, now):
        with self._lock:
            self.motion = P.MOTION_IDLE
            self._t_move_end = now
            self._t_settle_end = now
            self._release(now)

    def _release(self, now):
        """Wheel::release(): the end of a positioning, after the settling
        wait. Until here the firmware holds the motor at the RUN current,
        so the only moment the disc can be let go is this one:
        at once with no holding current, at the chip's own drop to a holding
        current lower than the run one. Let go sooner than --coast-ms after the
        leg stopped, the disc slides on by --coast degrees (the same model as
        the firmware bench)."""
        if not self._coast_pending:
            return
        self._coast_pending = False
        since = now - self._t_stopped
        if self.hold_current <= 0:
            let_go = since
        elif self.hold_current < self.run_current:
            let_go = max(since, POWERDOWN_S)
        else:
            return
        if let_go < self.o.coast_ms / 1000.0:
            self.angle = normalise(self.angle + self._coast_sign * self.o.coast)

    def current_slot(self):
        """1..SLOTS if we are within the warning tolerance of a position,
        otherwise 0 - meaning "between two positions". The Alpaca bridge will
        translate it into the -1 that ASCOM demands during motion."""
        if self.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
            return 0
        for i in range(self.slots):
            if abs(difference(self.angle, self.angles[i])) <= self.tolerance_warn:
                return i + 1
        return 0

    def residual_error(self):
        return difference(self.angle, self.target)

    def step(self, now):
        """Moves time forward. Called continuously by the heartbeat."""
        with self._lock:
            # The lost magnet is said when it happens, at rest too, once per
            # loss - as Wheel::step() in the firmware. When the simulator
            # said it only at the end of a move, and since a wheel
            # without the magnet refuses to move, in practice never, the
            # driver's handling of "! sensor" was tested against nothing.
            # Once per loss, and found again only after MAGNET_REARM_S seen
            # without a break, as the firmware.
            if self.motion in (P.MOTION_MOVING, P.MOTION_SETTLING) and \
                    (self.sensor_silent or not self.magnet_seen):
                self._leg_magnet_ok = False      # this leg teaches no ratio
            if not self.sensor_silent:
                if not self.magnet_seen:
                    self._magnet_since = None
                    if not self._magnet_lost:
                        self._magnet_lost = True
                        self.events.append(f"{P.PREFIX_EVENT} {P.EV_SENSOR} {P.F_MD}=0")
                else:
                    if self._magnet_since is None:
                        self._magnet_since = now
                    if self._magnet_lost and now - self._magnet_since >= MAGNET_REARM_S:
                        self._magnet_lost = False

            if self.led_test_end and now >= self.led_test_end:
                self.led_test_end = 0.0
                self.led_lit = False

            if self.motion == P.MOTION_MOVING:
                if now >= self._t_move_end:
                    self.angle = self._landing
                    self.motion = P.MOTION_SETTLING
                    self._t_stopped = now
                    self._coast_sign = -1.0 if self._travel < 0 else 1.0
                    self._coast_pending = self.o.coast > 0 and self._travel != 0
                else:
                    # linear interpolation along the way really taken, which
                    # one way round can be longer than half a turn
                    total = abs(self._travel) * self.o.ms_per_degree / 1000.0
                    if total > 0:
                        fraction = max(0.0, 1.0 - (self._t_move_end - now) / total)
                        self.angle = normalise(self.start + self._travel * fraction)

            elif self.motion == P.MOTION_SETTLING:
                if now >= self._t_settle_end:
                    self._judge(now)

            else:
                # At rest. The drift is simulated only when asked for, but the
                # WATCH always runs: a wheel can move by itself for reasons the
                # simulator does not model, and the firmware does not wait for
                # permission to notice.
                if self.o.drift and self._last_step:
                    self.angle = normalise(
                        self.angle + self.o.drift * (now - self._last_step))
                # Watched only at REST, not after a failure: whoever has just
                # received "failed" already knows the wheel is not where it
                # should be, and adding "and it has drifted" is noise. It is
                # also what the firmware does - wheel.cpp looks at Motion::IDLE
                # - and the two halves are compared against each other.
                if self.motion == P.MOTION_IDLE:
                    self._watch_drift()
            self._last_step = now

    def _judge(self, now):
        """The verdict is given by the firmware, not the driver: it is decided here."""
        self.moves_done += 1
        error = abs(self.residual_error())
        pos = self.wanted_slot
        timed_out = now >= self._deadline

        # what the leg did, the way it turned: as Wheel::judge()
        left = normalise(self._leg_sign * (self.target - self.angle))
        past = False
        if left <= self._leg_distance:
            moved = self._leg_distance - left
        elif 360.0 - left < left - self._leg_distance:
            past = True
            moved = self._leg_distance + (360.0 - left)
        else:
            moved = self._leg_distance - left
        sent = abs(self._leg_commanded)
        progressed = self._leg_aim > 0.0 and moved > NO_PROGRESS_SHARE * self._leg_aim
        short_leg = self._leg_aim > 0.0 and sent < SHORT_LEG_DEG
        lost_before = self._lost
        if short_leg and progressed:
            self._lost_known = True
        if short_leg:
            step = min(LOST_STEP_DEG, 0.5 * self.tolerance_good)
            lost = sent - moved if progressed else sent + step
            if not progressed:
                lost = max(lost, self._lost + step)
            self._lost = min(LOST_MAX_DEG, max(0.0, lost))
        taking_up_play = short_leg and not progressed and lost_before < LOST_MAX_DEG
        # a stall: the next leg gets the boost, as Wheel::judge()
        self._boost_next = self._leg_aim > 0.0 and not progressed and not past \
            and not taking_up_play

        # the ratio, learnt from this leg if it qualifies: as Wheel::judge()
        long_leg = self._leg_aim >= LEARN_MIN_DEG
        learnt = False
        if (self.learn and long_leg and not self._jogging and self._leg_kind == P.KIND_FIRST
                and self._lost_known and self._leg_magnet_ok and progressed and moved > 0.0):
            seen = self._leg_ratio * self._leg_aim / moved
            if abs(seen / self._leg_ratio - 1.0) <= LEARN_OUTLIER:
                r = self.ratio + LEARN_WEIGHT * (seen - self.ratio)
                r = min(self.base_ratio * (1.0 + LEARN_CLAMP),
                        max(self.base_ratio * (1.0 - LEARN_CLAMP), r))
                self._lost *= self.ratio / r
                self.ratio = r
                self.learnt += 1
                learnt = True
        if self.report_legs:
            yes = lambda b: P.V_YES if b else P.V_NO   # noqa: E731
            self.events.append(
                f"{P.PREFIX_EVENT} {P.EV_LEG} {P.F_N}={self.legs} {P.F_KIND}={self._leg_kind} "
                f"{P.F_JOG}={yes(self._jogging)} {P.F_STEPS}={self._leg_steps} "
                f"{P.F_MOTOR}={self._leg_steps * 360.0 / (200.0 * MICROSTEPS):.3f} "
                f"{P.F_RATIO}={self._leg_ratio:.4f} {P.F_AIM}={self._leg_aim:.3f} "
                f"{P.F_FROM}={self._leg_from:.3f} {P.F_TO}={self.angle:.3f} "
                f"{P.F_MOVED}={moved:.3f} {P.F_LONG}={yes(long_leg)} {P.F_LEARN}={yes(learnt)}")

        # a jog must have gone half of itself to be a warning (JOG_MOVED_SHARE)
        jog_went = True
        if self._jogging:
            along = normalise((-1.0 if self._jog_degrees < 0 else 1.0) * (self.angle - self._jog_from))
            if along > 270.0:
                along -= 360.0
            jog_went = along >= JOG_MOVED_SHARE * abs(self._jog_degrees)

        if error <= self._good_now:
            self.motion = P.MOTION_IDLE
            self.outcome = P.EV_ARRIVED
            self._release(now)
            self._event(P.EV_ARRIVED, pos, error)
        elif ((progressed or taking_up_play) and not past
              and self._approach_legs < APPROACH_LEGS_MAX and not timed_out):
            # an approach leg: free, it does not use up a retry
            self._approach_legs += 1
            self._leg_kind = P.KIND_APPROACH
            if self.check_driver():
                self._start_leg(now)
            else:
                self._driver_gone(now, pos, error)
        elif error <= self.tolerance_warn and jog_went:
            self.motion = P.MOTION_IDLE
            self.outcome = P.EV_WARNING
            self._release(now)
            self._event(P.EV_WARNING, pos, error)
        elif self.retries < self.max_retries and not timed_out:
            # a retry: after a leg that stalled or went past the target
            self.retries += 1
            self._leg_kind = P.KIND_RETRY
            if self.check_driver():
                self._start_leg(now)
            else:
                self._driver_gone(now, pos, error)
        else:
            self.motion = P.MOTION_FAILED
            self.outcome = P.EV_FAILED
            self._release(now)
            self._event(P.EV_FAILED, pos, error)

    def _driver_gone(self, now, pos, error):
        """The driver went silent between two legs: as Wheel::judge(), the
        positioning ends there, failed."""
        self.motion = P.MOTION_FAILED
        self.outcome = P.EV_FAILED
        self._release(now)
        self._event(P.EV_FAILED, pos, error)

    def _watch_drift(self):
        """Same criterion as wheel.cpp, watch_drift().

        The two halves are compared against each other in the tests, so this
        is not a rough imitation: the threshold, the "once per episode" and the
        fields of the event must match word for word.
        """
        if self.outcome == P.OUTCOME_NONE:
            return          # no target yet: there is no such thing as a drift
        deviation = self.residual_error()
        if abs(deviation) > self.tolerance_warn:
            if not self._drift_out:
                self._drift_out = True
                self.events.append(
                    f"{P.PREFIX_EVENT} {P.EV_DRIFT} "
                    f"{P.F_POS}={self.current_slot()} {P.F_ERR}={deviation:.2f}")
        else:
            self._drift_out = False

    def _event(self, name, pos, error):
        self.events.append(
            f"{P.PREFIX_EVENT} {name} {P.F_POS}={pos} "
            f"{P.F_ERR}={error:.2f} {P.F_RETRIES}={self.retries}")

    def collect_events(self):
        with self._lock:
            lines, self.events = self.events, []
            return lines


# ---------------------------------------------------------------- dialogue

class Dialogue:
    """Turns lines of text into actions on the wheel, and back."""

    def __init__(self, wheel, options):
        self.r = wheel
        self.o = options

    # -- helpers ----------------------------------------------------------

    def _ok(self, *fields):
        return P.PREFIX_OK + ("" if not fields else " " + " ".join(fields))

    def _error(self, code, text, **fields):
        parts = [f"{k}={v}" for k, v in fields.items()]
        return " ".join([P.PREFIX_ERROR, str(code)] + parts + [text])

    def _slot(self, text):
        """Turns an argument into a position number, or raises."""
        # as the firmware: a number, truncated, and got= quotes what arrived
        try:
            n = int(float(text))
        except (ValueError, OverflowError):
            raise ProtocolError(P.ERR_BAD_ARGUMENTS, "slot must be a number")
        if not 1 <= n <= self.r.slots:
            raise ProtocolError(P.ERR_OUT_OF_RANGE, "slot out of range",
                                **{P.F_EXPECTED: f"1..{self.r.slots}", P.F_GOT: text})
        return n

    def _number(self, text, name):
        try:
            return float(text)
        except ValueError:
            raise ProtocolError(P.ERR_BAD_ARGUMENTS, f"{name} must be a number")

    def _check_sensor(self):
        if self.r.sensor_silent:
            raise ProtocolError(P.ERR_SENSOR_SILENT, "AS5600 not responding")
        if not self.r.magnet_seen:
            raise ProtocolError(P.ERR_NO_MAGNET, "magnet not detected")

    def _check_driver(self):
        # after the sensor, as Wheel::go() and Wheel::jog()
        with self.r._lock:
            if not self.r.check_driver():
                raise ProtocolError(P.ERR_DRIVER_SILENT,
                                    "motor driver not responding - is the 12 V on?")

    # -- input ------------------------------------------------------------

    def line(self, text, now):
        text = text.strip()
        if not text:
            return []
        pieces = text.split()
        command, args = pieces[0], pieces[1:]
        try:
            return self._execute(command, args, text, now)
        except ProtocolError as e:
            return [self._error(e.code, e.text, **e.fields)]

    def _execute(self, command, args, whole_line, now):
        r = self.r

        if command == P.CMD_VERSION:
            return [self._ok(
                f"{P.F_NAME}=wheelly",
                f"{P.F_FW}={self.o.fw_version}",
                f"{P.F_PROTO}={self.o.protocol_version}",
                f"{P.F_SERIAL}={self.o.serial}",
                f"{P.F_SLOTS}={r.slots}")]

        if command == P.CMD_STATUS:
            silent = r.sensor_silent
            return [self._ok(
                f"{P.F_POS}={r.current_slot()}",
                f"{P.F_ANGLE}={r.angle:.2f}",
                f"{P.F_TARGET}={r.target:.2f}",
                f"{P.F_ERR}={r.residual_error():.2f}",
                f"{P.F_MOTION}={r.motion}",
                f"{P.F_RETRIES}={r.retries}",
                f"{P.F_LEGS}={r.legs}",
                f"{P.F_BOOSTS}={r.boosts}",
                f"{P.F_OUTCOME}={r.outcome}",
                f"{P.F_AGC}={0 if silent else r.agc()}",
                f"{P.F_MAG}={0 if silent else r.magnitude()}",
                f"{P.F_MD}={0 if (silent or not r.magnet_seen) else 1}",
                # The simulated magnet reads as weak (AGC at full scale, as on
                # the bench), but a silent sensor reports no flags at all, as
                # the firmware (ml=1 used to come out even then).
                f"{P.F_ML}={0 if silent else 1}",
                f"{P.F_MH}=0",
                # the way of the current (or last) leg, as the firmware
                f"{P.F_DIR}={r.direction}")]

        if command == P.CMD_GO:
            if not args:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "go needs a slot")
            # the firmware's order (Wheel::go): the slot first, then the
            # sensor - so "go 9" on a silent sensor is out of range, as there
            n = self._slot(args[0])
            self._check_sensor()
            self._check_driver()
            target, start, direction = r.go(n, now)
            return [self._ok(f"{P.F_TARGET}={target:.2f}",
                             f"{P.F_FROM}={start:.2f}",
                             f"{P.F_DIR}={direction}")]

        if command == P.CMD_JOG:
            if len(args) != 1:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "jog needs degrees")
            try:
                v = float(args[0])
            except ValueError:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "degrees must be a number")
            # the firmware's order (Wheel::jog): range, motion, sensor
            if not abs(v) <= P.JOG_MAX_DEG:
                raise ProtocolError(P.ERR_OUT_OF_RANGE, "jog out of range",
                                    **{P.F_EXPECTED: f"-{P.JOG_MAX_DEG}..{P.JOG_MAX_DEG}",
                                       P.F_GOT: args[0]})
            if r.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
                raise ProtocolError(P.ERR_NOT_NOW, "wheel is moving")
            self._check_sensor()
            self._check_driver()
            start = r.angle
            target, _, direction = r.jog(v, now)
            return [self._ok(f"{P.F_TARGET}={target:.2f}",
                             f"{P.F_FROM}={start:.2f}",
                             f"{P.F_DIR}={direction}")]

        if command == P.CMD_SLOTS:
            if args:
                # the firmware's order (Wheel::set_slots): range, then
                # motion - the two used to answer different codes
                n = int(self._number(args[0], "slots"))
                if not P.MIN_SLOTS <= n <= P.MAX_SLOTS:
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "slots out of range",
                                        **{P.F_EXPECTED: f"{P.MIN_SLOTS}..{P.MAX_SLOTS}",
                                           P.F_GOT: args[0]})
                if r.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
                    raise ProtocolError(P.ERR_NOT_NOW, "wheel is moving")
                if n != r.slots:
                    # Changing the number of positions throws the old
                    # calibration away: the angles of a five-slot wheel mean
                    # nothing on a seven-slot one.
                    r.slots = n
                    r.spread_evenly()
                    r.wanted_slot = 1
                    r.outcome = P.OUTCOME_NONE
            return [self._ok(f"{P.F_SLOTS}={r.slots}")]

        if command == P.CMD_STOP:
            r.stop(now)
            return [self._ok()]

        if command == P.CMD_ANGLES:
            return [self._ok(*[f"a{i+1}={a:.2f}" for i, a in enumerate(r.angles)])]

        if command == P.CMD_NAMES:
            return [self._ok(*[f"n{i+1}={n}" for i, n in enumerate(r.names)])]

        if command == P.CMD_ANGLE:
            # the firmware's order (Wheel::set_angle): slot, angle, motion
            if len(args) != 2:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "angle needs slot and degrees")
            try:
                float(args[0])
                v = float(args[1])
            except ValueError:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "angle takes two numbers")
            n = self._slot(args[0])
            if not 0.0 <= v <= P.ANGLE_MAX_DEG:
                raise ProtocolError(P.ERR_OUT_OF_RANGE, "angle out of range",
                                    **{P.F_EXPECTED: f"0..{P.ANGLE_MAX_DEG}", P.F_GOT: args[1]})
            if r.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
                raise ProtocolError(P.ERR_NOT_NOW, "wheel is moving")
            # it does not move the wheel: the driver sends `go`
            r.angles[n - 1] = normalise(v)
            return [self._ok(f"a{n}={r.angles[n - 1]:.2f}")]

        if command == P.CMD_NAME:
            if len(args) < 2:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "name needs slot and text")
            n = self._slot(args[0])
            # the name is the rest of the line, but it cannot contain spaces:
            # if there are any, it is already an invalid name and it is said
            new = whole_line.split(None, 2)[2]
            verdict = P.check_name(new)
            if verdict != P.NAME_OK:
                raise ProtocolError(P.ERR_BAD_FILTER_NAME, "invalid filter name",
                                    **{P.F_REASON: P.REASON_NAME[verdict]})
            others = [x for i, x in enumerate(r.names) if i != n - 1]
            if any(x.lower() == new.lower() for x in others):
                raise ProtocolError(P.ERR_BAD_FILTER_NAME, "duplicate filter name",
                                    **{P.F_REASON: "duplicate"})
            r.names[n - 1] = new
            return [self._ok(f"n{n}={new}")]

        if command == P.CMD_TEACH:
            if not args:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "teach needs a slot")
            # the firmware's order (Wheel::reteach): range, motion, sensor
            n = self._slot(args[0])
            if r.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
                raise ProtocolError(P.ERR_NOT_NOW, "wheel is moving")
            self._check_sensor()
            r.angles[n - 1] = r.angle
            r.target = r.angle
            return [self._ok(f"a{n}={r.angles[n-1]:.2f}")]

        if command == P.CMD_SAVE:
            if self.o.nvs_broken:
                raise ProtocolError(P.ERR_NVS_WRITE, "NVS write failed")
            r.save()
            return [self._ok(f"{P.F_SAVED}=nvs")]

        if command == P.CMD_TOLERANCE:
            if args:
                if len(args) != 3:
                    raise ProtocolError(P.ERR_BAD_ARGUMENTS, "tolerance needs good, warn, retries")
                good = self._number(args[0], "good")
                warn = self._number(args[1], "warn")
                attempts = int(self._number(args[2], "retries"))
                if not (0 < good <= warn <= P.TOLERANCE_MAX_DEG) \
                        or not (0 <= attempts <= P.RETRIES_MAX):
                    # the same expected= as the firmware, from the same header
                    # constants, and got= with what arrived (this one used to
                    # have a space in it, and neither sent got=)
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "tolerance out of range",
                                        **{P.F_EXPECTED: f"0<good<=warn<={P.TOLERANCE_MAX_DEG},"
                                                         f"retries=0..{P.RETRIES_MAX}",
                                           P.F_GOT: ",".join(args)})
                r.tolerance_good, r.tolerance_warn = good, warn
                r.max_retries = attempts
            return [self._ok(f"{P.F_GOOD}={r.tolerance_good:.2f}",
                             f"{P.F_WARN}={r.tolerance_warn:.2f}",
                             f"{P.F_RETRIES}={r.max_retries}")]

        if command == P.CMD_MOTOR:
            # All or nothing, as the firmware: every argument is checked before
            # any is applied (applying the current, then refusing the speed,
            # made the error answer hide a changed current).
            # motor <mA> <speed> <accel>, as the firmware
            if len(args) == 2:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS,
                                    "speed needs acceleration too: motor <mA> <speed> <accel>")
            if args:
                ma = self._number(args[0], "mA")
                if not 1 <= ma <= P.MOTOR_MA_MAX:
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "current out of range",
                                        **{P.F_EXPECTED: f"1..{P.MOTOR_MA_MAX}", P.F_GOT: args[0]})
            if len(args) >= 3:
                try:
                    v, a = float(args[1]), float(args[2])
                except ValueError:
                    raise ProtocolError(P.ERR_BAD_ARGUMENTS, "speed and acceleration must be numbers")
                if not (1 <= v <= P.MOTOR_SPEED_MAX and 1 <= a <= P.MOTOR_ACCEL_MAX):
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "speed or acceleration out of range",
                                        **{P.F_EXPECTED: f"1..{P.MOTOR_SPEED_MAX},1..{P.MOTOR_ACCEL_MAX}",
                                           P.F_GOT: f"{args[1]},{args[2]}"})
            if args:
                r.run_current = int(ma)
                if r.hold_current > r.run_current:
                    r.hold_current = r.run_current   # as Wheel::set_run_current
            if len(args) >= 3:
                r.speed, r.acceleration = int(v), int(a)
            return [self._ok(f"{P.F_MA}={r.run_current}",
                             f"{P.F_SPEED}={r.speed}",
                             f"{P.F_ACCEL}={r.acceleration}",
                             f"{P.F_CEILING}={r.ceiling_ms()}")]

        if command == P.CMD_HOLD:
            lines = []
            if args:
                ma = self._number(args[0], "mA")
                if not 0 <= ma <= r.run_current:
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "hold current out of range",
                                        **{P.F_EXPECTED: f"0..{r.run_current}",
                                           P.F_GOT: args[0]})
                r.hold_current = int(ma)
                if r.hold_current > 0:
                    lines.append(f"{P.PREFIX_COMMENT} warning: holding current on"
                                 " - heat and chopper noise during exposures")
                return lines + [self._ok(f"{P.F_MA}={r.hold_current}")]
            # no `detent=` any more, as the firmware
            return [self._ok(f"{P.F_MA}={r.hold_current}")]

        if command == P.CMD_SETTLE:
            # the settling wait after every leg, as the firmware
            if len(args) > 1:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "settle takes one number: settle <ms>")
            if args:
                ms = self._number(args[0], "ms")
                if not 0 <= ms <= P.SETTLE_MS_MAX:
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "settle out of range",
                                        **{P.F_EXPECTED: f"0..{P.SETTLE_MS_MAX}",
                                           P.F_GOT: args[0]})
                r.settle_ms = int(math.floor(ms + 0.5))   # lroundf
            return [self._ok(f"{P.F_MS}={r.settle_ms}", f"{P.F_CEILING}={r.ceiling_ms()}")]

        if command == P.CMD_DIRECTION:
            if args:
                if args[0] not in (P.ARG_SHORTEST, P.ARG_UP, P.ARG_DOWN):
                    raise ProtocolError(
                        P.ERR_BAD_ARGUMENTS, "direction must be shortest, up or down",
                        **{P.F_EXPECTED: f"{P.ARG_SHORTEST}|{P.ARG_UP}|{P.ARG_DOWN}",
                           P.F_GOT: args[0]})
                r.turn = args[0]
            return [self._ok(f"{P.F_DIRECTION}={r.turn}",
                             f"{P.F_CEILING}={r.ceiling_ms()}")]

        if command == P.CMD_RATIO:
            # as the firmware's Dialog: ratio, ratio <value>,
            # ratio learn on|off
            if len(args) == 2 and args[0] == P.ARG_LEARN:
                if args[1] not in (P.ARG_ON, P.ARG_OFF):
                    raise ProtocolError(P.ERR_BAD_ARGUMENTS, "ratio learn takes on or off",
                                        **{P.F_EXPECTED: f"{P.ARG_ON}|{P.ARG_OFF}",
                                           P.F_GOT: args[1]})
                r.set_learning(args[1] == P.ARG_ON)
            elif len(args) == 1:
                try:
                    value = float(args[0])
                except ValueError:
                    value = None
                if value is None or not math.isfinite(value):
                    raise ProtocolError(P.ERR_BAD_ARGUMENTS,
                                        "ratio must be a number, or learn on|off")
                if not P.DRIVE_RATIO_MIN <= value <= P.DRIVE_RATIO_MAX:
                    raise ProtocolError(P.ERR_OUT_OF_RANGE, "ratio out of range",
                                        **{P.F_EXPECTED: f"{P.DRIVE_RATIO_MIN:.1f}.."
                                                         f"{P.DRIVE_RATIO_MAX:.1f}",
                                           P.F_GOT: args[0]})
                if r.motion in (P.MOTION_MOVING, P.MOTION_SETTLING):
                    raise ProtocolError(P.ERR_NOT_NOW, "wheel is moving")
                r.set_ratio(value)
            elif args:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "ratio takes a number, or learn on|off")
            return [self._ok(f"{P.F_RATIO}={r.ratio:.4f}", f"{P.F_BASE}={r.base_ratio:.4f}",
                             f"{P.F_FACTORY}={P.FACTORY_DRIVE_RATIO:.4f}",
                             f"{P.F_LEARN}={P.ARG_ON if r.learn else P.ARG_OFF}",
                             f"{P.F_LEARNT}={r.learnt}",
                             f"{P.F_CEILING}={r.ceiling_ms()}")]

        if command == P.CMD_LEGS:
            if len(args) == 1 and args[0] in (P.ARG_ON, P.ARG_OFF):
                r.report_legs = args[0] == P.ARG_ON
            elif args:
                raise ProtocolError(P.ERR_BAD_ARGUMENTS, "legs takes on or off",
                                    **{P.F_EXPECTED: f"{P.ARG_ON}|{P.ARG_OFF}",
                                       P.F_GOT: args[0]})
            return [self._ok(f"{P.F_REPORT}={P.ARG_ON if r.report_legs else P.ARG_OFF}")]

        if command == P.CMD_LED:
            if not args:
                return [self._ok(
                    f"{P.F_STATE}={P.ARG_ON if r.led_lit else P.ARG_OFF}",
                    f"{P.F_ENABLED}={P.V_YES if r.led_enabled else P.V_NO}",
                    f"{P.F_MODE}={r.led_mode}")]
            arg = args[0]
            if arg == P.ARG_ON:
                r.led_enabled = True
                r.led_lit = True
                r.led_mode = P.ARG_ON
                return [self._ok(f"{P.F_STATE}={P.ARG_ON}")]
            if arg == P.ARG_OFF:
                r.led_lit = False
                r.led_mode = P.ARG_OFF
                return [self._ok(f"{P.F_STATE}={P.ARG_OFF}")]
            if arg == P.ARG_PULSE:
                r.led_lit = False
                r.led_mode = P.ARG_PULSE
                return [self._ok(f"{P.F_STATE}={P.ARG_OFF}", f"{P.F_MODE}={P.ARG_PULSE}")]
            if arg == P.ARG_TEST:
                duration = self._morse_duration()
                r.led_lit = True
                r.led_test_end = now + duration
                return [f"{P.PREFIX_COMMENT} W .--  H ....  E .  E .  "
                        f"L .-..  L .-..  Y -.--",
                        self._ok(f"{P.F_DURATION}={duration:.1f}")]
            raise ProtocolError(P.ERR_BAD_ARGUMENTS, "led takes on, pulse, off or test")

        if command == P.CMD_DIAG:
            lines = []
            if r.sensor_silent:
                lines.append(f"{P.PREFIX_COMMENT} AS5600 at 0x36: SILENT")
            else:
                lines.append(f"{P.PREFIX_COMMENT} AS5600 at 0x36: responding")
                lines.append(
                    f"{P.PREFIX_COMMENT} STATUS md={1 if r.magnet_seen else 0}"
                    f" ml=1 mh=0  AGC={r.agc()}  MAG={r.magnitude()}")
            # Word for word what the firmware prints, including "run" and not
            # "current": the two halves are compared against each other, and a
            # line that differs only in wording is a difference nobody notices
            # until it hides a real one. The simulated wheel has a TMC2208, like the real one.
            # through the check every leg makes, as the firmware's diag
            with r._lock:
                answers = r.check_driver()
            if answers:
                lines.append(f"{P.PREFIX_COMMENT} TMC2208 over UART: responding,"
                             f" run {r.run_current} mA,"
                             f" hold {r.hold_current} mA")
            else:
                lines.append(f"{P.PREFIX_COMMENT} TMC2208 over UART: SILENT - check VM"
                             f" at the driver, then the 1k on the single wire")
            lines.append(self._ok())
            return lines

        raise ProtocolError(P.ERR_UNKNOWN_COMMAND, "unknown command")

    @staticmethod
    def _morse_duration():
        """Wheelly in Morse: 67 units, the gaps between letters included."""
        signs = {"W": ".--", "H": "....", "E": ".", "L": ".-..", "Y": "-.--"}
        units = 0
        word = "WHEELLY"
        for i, letter in enumerate(word):
            code = signs[letter]
            units += sum(3 if s == "-" else 1 for s in code)
            units += len(code) - 1            # gaps between signs
            if i < len(word) - 1:
                units += 3                    # gap between letters
        return units * 0.1


class ProtocolError(Exception):
    def __init__(self, code, text, **fields):
        super().__init__(text)
        self.code = code
        self.text = text
        self.fields = fields


# ------------------------------------------------------------------ service

class Service:
    """Holds wheel, dialogue and any transport together."""

    def __init__(self, options):
        self.o = options
        self.wheel = Wheel(options)
        self.dialogue = Dialogue(self.wheel, options)
        self.rest = b""
        self.stopping = threading.Event()

    def heartbeat(self):
        """Keeps the wheel's time running while nobody talks."""
        while not self.stopping.is_set():
            self.wheel.step(time.monotonic())
            time.sleep(0.005)

    def to_send(self):
        return self.wheel.collect_events()

    def receive(self, data):
        """Accumulates bytes, and returns the reply lines that are ready."""
        self.rest += data
        out = []
        while b"\n" in self.rest:
            line, self.rest = self.rest.split(b"\n", 1)
            text = line.decode("utf-8", errors="replace").replace("\r", "")
            now = time.monotonic()
            self.wheel.step(now)
            if self.o.echo:
                print(f"  <- {text}", file=sys.stderr)
            replies = self.dialogue.line(text, now)
            if self.o.echo:
                for x in replies:
                    print(f"  -> {x}", file=sys.stderr)
            out.extend(replies)
        return out


def serve_stdio(service):
    threading.Thread(target=service.heartbeat, daemon=True).start()
    out = sys.stdout
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0.02)
        for line in service.to_send():
            out.write(line + "\n")
            out.flush()
        if ready:
            data = sys.stdin.buffer.raw.read(4096)
            if not data:
                break
            for line in service.receive(data):
                out.write(line + "\n")
                out.flush()
    service.stopping.set()


def give_up_exclusivity(fd):
    """Removes the exclusivity mark from the fake serial port.

    When INDI opens a serial port it marks it exclusive with TIOCEXCL, and
    rightly so: two drivers on the same port would be a disaster. On disconnect
    it closes its descriptor - but we keep ours open, otherwise the pty would
    vanish and the symbolic link would be left hanging over nothing. Result:
    the pty stays alive with the mark on it, and from then on nobody can open
    it. It connects the first time and never again, with an EBUSY the driver
    reports as "Port is already used by another driver or process" - a message
    that sends you looking for a process that does not exist.

    Here exclusivity is given up explicitly, continuously: it is a fake serial
    port for testing, it has nothing to protect.
    """
    try:
        fcntl.ioctl(fd, termios.TIOCNXCL)
    except OSError:
        pass


def serve_pty(service, link):
    import tty

    master, slave = os.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    name = os.ttyname(slave)

    if link:
        try:
            if os.path.islink(link) or os.path.exists(link):
                os.unlink(link)
            os.symlink(name, link)
        except OSError as e:
            print(f"# cannot create {link}: {e}", file=sys.stderr)
            link = None

    print(f"fake serial port ready: {name}")
    if link:
        print(f"stable link: {link}")
    print("point the INDI driver here. Ctrl-C to close.")
    sys.stdout.flush()

    threading.Thread(target=service.heartbeat, daemon=True).start()
    try:
        while True:
            give_up_exclusivity(slave)
            ready, _, _ = select.select([master], [], [], 0.02)
            for line in service.to_send():
                os.write(master, (line + "\n").encode())
            if ready:
                try:
                    data = os.read(master, 4096)
                except OSError:
                    break
                if not data:
                    break
                for line in service.receive(data):
                    os.write(master, (line + "\n").encode())
    except KeyboardInterrupt:
        pass
    finally:
        service.stopping.set()
        if link:
            try:
                os.unlink(link)
            except OSError:
                pass
        os.close(slave)
        os.close(master)


# --------------------------------------------------------------------- start

def parse_options(argv=None):
    # The option names stay as they are (Italian): the driver bench, the panel
    # capture, firmware_bench.cpp and the READMEs pass them. Only their help
    # is translated; dest= gives the code English attribute names.
    p = argparse.ArgumentParser(
        description="Simulator of the Wheelly filter wheel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  %(prog)s --pty --link /tmp/wheelly
      opens a fake serial port and puts a fixed name on it, so the INDI
      driver is always pointed at the same path

  %(prog)s --slip 0.5
      the clutch slips on half of the moves: to see the retries

  %(prog)s --stuck
      never arrives: to prove that the driver declares the failure and stops
      the imaging sequence instead of waiting forever

  echo 'go 3' | %(prog)s
      one question and done, for trying by hand
""")
    p.add_argument("--pty", action="store_true",
                   help="open a fake serial port instead of using stdin/stdout")
    p.add_argument("--link", dest="link", metavar="PATH",
                   help="create a stable symbolic link to the fake serial port")
    p.add_argument("--echo", dest="echo", action="store_true",
                   help="echo the whole dialogue on stderr, to watch it")
    p.add_argument("--slots", type=int, default=P.FACTORY_SLOTS,
                   help="how many positions the wheel has (default: %(default)s)")

    g = p.add_argument_group("how the wheel behaves")
    g.add_argument("--ms-per-degree", dest="ms_per_degree", type=float, default=8.0,
                   help="rotation speed, ms per degree (default: %(default)s)")
    g.add_argument("--noise-degrees", dest="noise_degrees", type=float, default=0.03,
                   help="reading noise of the AS5600, in degrees")

    g = p.add_argument_group("knobs for breaking things on purpose")
    g.add_argument("--slip", dest="slip", type=float, default=0.0, metavar="P",
                   help="probability that the clutch slips, from 0 to 1")
    g.add_argument("--slip-degrees", dest="slip_degrees", type=float, default=2.0,
                   help="how much it slips, in degrees")
    g.add_argument("--ratio-error", dest="ratio_error", type=float, default=-0.10,
                   metavar="F",
                   help="how far the disc really goes from the firmware's step "
                        "estimate, as a fraction: -0.10 (default) is 10%% short, "
                        "the side the real wheel is on")
    g.add_argument("--lost-motion", dest="lost_motion", type=float, default=0.6,
                   metavar="DEG",
                   help="degrees of disc every leg loses before the disc moves: "
                        "the give of the clutch's TPU tyre, about 0.6 (default) "
                        "on the real wheel")
    g.add_argument("--coast", dest="coast", type=float, default=0.0, metavar="DEG",
                   help="the disc's inertia: let go by the motor sooner than --coast-ms "
                        "after a leg stopped, it slides on by this many degrees "
                        "(default 0: it does not)")
    g.add_argument("--coast-ms", dest="coast_ms", type=float, default=200.0, metavar="MS",
                   help="how long the stopped motor must hold the disc at the run "
                        "current to damp its inertia (default: %(default)s)")
    g.add_argument("--notch-at", dest="notch_at", type=float, default=None,
                   metavar="DEG",
                   help="a notch of a detent left in place at this angle stalls a slow motor: "
                        "a leg slower than --notch-min-speed stops before it")
    g.add_argument("--notch-min-speed", dest="notch_min_speed", type=float, default=0.0,
                   metavar="STEPS",
                   help="full steps/s needed to get past --notch-at")
    g.add_argument("--stall", dest="stall", choices=(P.ARG_UP, P.ARG_DOWN), default=None,
                   help="an asymmetric detent left in place: moving this way climbs "
                        "the steep flank, the motor stalls and the disc stays put")
    g.add_argument("--stuck", dest="stuck", action="store_true",
                   help="never reaches the destination")
    g.add_argument("--sensor-silent", dest="sensor_silent", action="store_true",
                   help="the AS5600 does not respond")
    g.add_argument("--sensor-silent-after", dest="sensor_silent_after", type=int,
                   default=-1, metavar="N",
                   help="the AS5600 goes silent after N moves")
    g.add_argument("--no-magnet", dest="no_magnet", action="store_true",
                   help="the sensor responds but does not see the magnet")
    g.add_argument("--magnet-flicker", dest="magnet_flicker", type=float, default=0.0,
                   metavar="MS",
                   help="the magnet-detected bit flickers, toggling every MS ms, in "
                        "the first 1.5 s of every 4 s: the magnitude hovering around "
                        "the AS5600's threshold, as seen on the reference wheel")
    g.add_argument("--drift", dest="drift", type=float, default=0.0,
                   metavar="DEGREES_PER_SEC",
                   help="the wheel moves by itself when at rest, this many degrees "
                        "per second: the case in which holding current at rest is "
                        "really needed")
    g.add_argument("--vm-off-for", dest="vm_off_for", type=float, default=0.0,
                   metavar="MS",
                   help="the motor's 12 V arrive MS ms after the start (USB first, "
                        "as the assembly guide says): the driver is silent until "
                        "then, and at its reset values after")
    g.add_argument("--vm-drop-after-moves", dest="vm_drop_after_moves", type=int,
                   default=-1, metavar="N",
                   help="after N legs the 12 V drop and come back: the driver "
                        "answers, reset")
    g.add_argument("--vm-lost-after-moves", dest="vm_lost_after_moves", type=int,
                   default=-1, metavar="N",
                   help="after N legs the 12 V go for good: the driver is silent")
    g.add_argument("--nvs-broken", dest="nvs_broken", action="store_true",
                   help="saving always fails")
    g.add_argument("--nvs", dest="nvs", default="", metavar="KEY=VALUE,...",
                   help="numbers the memory holds at the first start, as an older "
                        "firmware left them: a1..a12 angles, o1..o12 rotation trims")
    g.add_argument("--boots", dest="boots", type=int, default=1, metavar="N",
                   help="start the wheel N times on the same memory before talking")
    # A firmware older or newer than the driver: the driver must refuse it
    # with a message that says which is which, not half-work with it. The
    # switch was promised by firmware.md before it existed.
    g.add_argument("--protocol-version", dest="protocol_version", type=int,
                   default=P.PROTOCOL_VERSION, metavar="N",
                   help="declare this protocol version instead of the header's "
                        "(default: %(default)s)")

    g = p.add_argument_group("miscellaneous")
    g.add_argument("--seed", dest="seed", type=int, default=1,
                   help="random seed: same seed, same run")
    g.add_argument("--fw-version", dest="fw_version", default="0.1.0-sim",
                   help="firmware version to declare (default: %(default)s)")
    g.add_argument("--serial", dest="serial", default="51MUL470",
                   help="serial number to declare (default: %(default)s)")
    return p.parse_args(argv)


def main():
    o = parse_options()
    service = Service(o)
    if o.pty:
        serve_pty(service, o.link)
    else:
        serve_stdio(service)


if __name__ == "__main__":
    main()
