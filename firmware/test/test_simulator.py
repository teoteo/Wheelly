#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""Tests on the wheel simulator, and on its agreement with the real firmware.

The simulator is launched as a separate process and spoken to over its own
text channel, exactly as the INDI driver will. So what is tested here is not an
imitation of the protocol: it is the protocol.

    cd firmware/test && python3 test_simulator.py

Two kinds of tests, and the second is the one that mattered most:

  - the dialogue: every command, the error cases, and above all the faults -
    the clutch that slips, the wheel that never arrives, the sensor that goes
    silent. These are the cases the real hardware does not produce on demand.

  - the agreement between the two copies of the filter-name rule. In C++ it
    lives in the shared header, in Python it is necessarily a copy. A copy that
    nobody compares with the original sooner or later diverges, and then the
    simulator would accept names the firmware refuses - passing as good a
    driver that does not work on the real thing. Here the C++ implementation is
    compiled and fed the same inputs, demanding the same verdict.
"""

import os
import pathlib
import random
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent

# The same tests run against two different things, and that is the point of
# the whole exercise: the Python SIMULATOR, and the real FIRMWARE compiled for
# the PC. If the two did not behave the same way, one of them would be wrong
# and nobody would notice until the wheel is assembled.
#
#     python3 test_simulator.py                      the simulator
#     python3 test_simulator.py /tmp/wheelly_bench   the real firmware
UNDER_TEST = sys.argv[1] if len(sys.argv) > 1 else None
SIMULATOR = pathlib.Path(UNDER_TEST) if UNDER_TEST else HERE.parent / "simulator" / "wheelly_sim.py"
IS_PYTHON = SIMULATOR.suffix == ".py"
sys.path.insert(0, str(HERE.parent / "simulator"))

import protocol as P  # noqa: E402

failed = []
passed = 0


def ok(condition, what, detail=""):
    global passed
    if condition:
        passed += 1
    else:
        failed.append(f"{what}{' -> ' + detail if detail else ''}")
        print(f"  FAILED: {what}" + (f" -> {detail}" if detail else ""))


# ---------------------------------------------------------------- the channel

class Wheel:
    """Talks to the simulator as the driver would."""

    def __init__(self, *knobs):
        launch = [sys.executable, str(SIMULATOR)] if IS_PYTHON else [str(SIMULATOR)]
        self.p = subprocess.Popen(
            [*launch, *knobs],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            bufsize=0)
        os.set_blocking(self.p.stdout.fileno(), False)
        self.rest = b""
        self.events = []
        self.comments = []

    def _line(self, deadline):
        while True:
            if b"\n" in self.rest:
                line, self.rest = self.rest.split(b"\n", 1)
                return line.decode().rstrip("\r")
            if time.monotonic() > deadline:
                return None
            chunk = self.p.stdout.read(4096)
            if chunk:
                self.rest += chunk
            else:
                time.sleep(0.005)

    def ask(self, command, wait=5.0):
        """Sends a command and returns the outcome line.

        The driver does exactly this: it reads until it meets a line that does
        not start with '#' or '!', because those are informative and close
        nothing.
        """
        self.p.stdin.write((command + "\n").encode())
        self.p.stdin.flush()
        deadline = time.monotonic() + wait
        while True:
            line = self._line(deadline)
            if line is None:
                return None
            if line.startswith(P.PREFIX_EVENT):
                self.events.append(line)
            elif line.startswith(P.PREFIX_COMMENT):
                self.comments.append(line)
            else:
                return line

    def wait_outcome(self, wait=15.0):
        """Waits for any outcome of the positioning.

        Needed because a move can end in three ways, and the test must not
        assume which: arrived, warning (within the warning tolerance: report
        but carry on) or failed.
        """
        terminal = (P.EV_ARRIVED, P.EV_WARNING, P.EV_FAILED)
        # An event already collected counts, but it must be CONSUMED: if it
        # stayed in the list, the next wait would return at once with the
        # outcome of the previous move and the test would go on with the wheel
        # still moving. It really happened, and it is why this comment exists.
        for e in list(self.events):
            if e.split()[1] in terminal:
                self.events.remove(e)
                return e
        deadline = time.monotonic() + wait
        while True:
            line = self._line(deadline)
            if line is None:
                return None
            if line.startswith(P.PREFIX_EVENT):
                if line.split()[1] in terminal:
                    return line
                self.events.append(line)
            elif line.startswith(P.PREFIX_COMMENT):
                self.comments.append(line)

    def wait_event(self, name, wait=8.0):
        deadline = time.monotonic() + wait
        while True:
            for e in list(self.events):
                if e.split()[1] == name:
                    self.events.remove(e)   # consumed, see wait_outcome
                    return e
            line = self._line(deadline)
            if line is None:
                return None
            if line.startswith(P.PREFIX_EVENT):
                self.events.append(line)
            elif line.startswith(P.PREFIX_COMMENT):
                self.comments.append(line)

    def fields(self, line):
        out = {}
        for piece in line.split()[1:]:
            if "=" in piece:
                k, v = piece.split("=", 1)
                out[k] = v
        return out

    def close(self):
        try:
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.p.kill()


# --------------------------------------------------------------- the dialogue

def test_identification():
    print("identification and handshake")
    r = Wheel()
    line = r.ask(P.CMD_VERSION)
    ok(line is not None and line.startswith(P.PREFIX_OK), "version answers", str(line))
    c = r.fields(line or "")
    ok(c.get(P.F_NAME) == "wheelly", "introduces itself as wheelly", str(c))
    ok(c.get(P.F_PROTO) == str(P.PROTOCOL_VERSION),
       "declares the header's protocol version", str(c))
    ok(P.F_FW in c and P.F_SERIAL in c, "declares firmware and serial number")
    # How many positions it has is said by the wheel, and the driver does not
    # take it for granted: a seven-slot wheel must show neither five nor twelve.
    ok(c.get(P.F_SLOTS) == str(P.FACTORY_SLOTS),
       "declares how many positions it has", str(c))
    r.close()


def test_status():
    print("status")
    r = Wheel()
    c = r.fields(r.ask(P.CMD_STATUS))
    expected = [P.F_POS, P.F_ANGLE, P.F_TARGET, P.F_ERR, P.F_MOTION, P.F_RETRIES,
                P.F_LEGS, P.F_BOOSTS, P.F_OUTCOME, P.F_AGC, P.F_MAG, P.F_MD, P.F_ML, P.F_MH, P.F_DIR]
    missing = [x for x in expected if x not in c]
    ok(not missing, "status has all the documented fields", str(missing))
    ok(c.get(P.F_MOTION) == P.MOTION_IDLE, "at rest motion=idle", str(c))
    ok(c.get(P.F_AGC) == "128",
       "the AGC stays at full scale, as on the real bench", str(c))
    ok(c.get(P.F_OUTCOME) == P.OUTCOME_NONE,
       "before moving there is no verdict", str(c))
    # the field flags go with the AGC at full scale: weak, not strong - and
    # the same from both halves (the bench once said ml=0, the sim 1)
    ok(c.get(P.F_ML) == "1" and c.get(P.F_MH) == "0",
       "status: weak field flagged, strong not, like the bench magnet", str(c))
    r.close()


def test_motion():
    print("motion")
    r = Wheel()
    line = r.ask(P.CMD_GO + " 3")
    c = r.fields(line)
    ok(line.startswith(P.PREFIX_OK), "go accepted", line)
    ok(P.F_TARGET in c and P.F_FROM in c and P.F_DIR in c,
       "go states target, start and direction", str(c))

    # right after, the wheel is moving: this is when INDI keeps FILTER_SLOT
    # Busy and Ekos must not shoot
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(c.get(P.F_MOTION) in (P.MOTION_MOVING, P.MOTION_SETTLING),
       "during the move motion says it is moving", str(c))
    ok(c.get(P.F_POS) == "0",
       "during the move pos=0, never a valid slot", str(c))
    # THE ANGLE IS READ WHILE MOVING: a firmware that showed the angle of
    # the last stop until the verdict gave a sweep on the real wheel with
    # points only at the slots, while the simulator's was
    # continuous. Sampled during the move, the angle must change, on both
    # halves; 144 degrees at the fakes' 8 ms/degree is over a second.
    moving_angles = []
    while c.get(P.F_MOTION) == P.MOTION_MOVING:
        moving_angles.append(c.get(P.F_ANGLE))
        time.sleep(0.02)
        c = r.fields(r.ask(P.CMD_STATUS))
    ok(len(set(moving_angles)) >= 5,
       "status during a move shows the angle changing, not the last stop",
       f"{len(set(moving_angles))} distinct of {len(moving_angles)}: {moving_angles[:8]}")

    e = r.wait_event(P.EV_ARRIVED)
    ok(e is not None, "the arrived event comes", str(e))
    if e:
        c = r.fields(e)
        ok(c.get(P.F_POS) == "3", "the event states the right position", e)
        ok(abs(float(c[P.F_ERR])) <= P.FACTORY_GOOD_DEG, "residual error within the good tolerance", e)
        # With no slip, no retries: the fake disc goes 10 % short of the
        # estimate (--ratio-error, as the real wheel), so the wheel creeps in
        # with approach legs, which are not retries. The fake
        # mechanics of the firmware bench turns microsteps into degrees with
        # its OWN physics, so a wrong STEPS_PER_DEGREE - a ratio missing, a
        # microstep counted twice - overshoots or stalls, and that IS a retry.
        ok(c.get(P.F_RETRIES) == "0",
           "a clean move needs no retries: the approach legs are not retries", e)

    c = r.fields(r.ask(P.CMD_STATUS))
    # 144 degrees the shortest way (the factory way; 216 one way down),
    # 10 % short: the approach legs and the learnt
    # lost motion get there in a few legs; more than eight means the
    # approach is not converging as designed, fewer than two that the bench
    # is exact again and nothing here tests the creep-in
    ok(2 <= int(c.get(P.F_LEGS, 0)) <= LEGS_BOUND,
       "and it creeps in: a few approach legs, within a bound", str(c))
    ok(c.get(P.F_POS) == "3", "move finished, pos=3", str(c))
    ok(c.get(P.F_MOTION) == P.MOTION_IDLE, "and motion goes back to idle", str(c))
    # The verdict is in the status and not only in the event: that is what
    # lets the driver not recompute it by comparing the error with the
    # tolerances, i.e. not redo the firmware's decision in a second copy.
    ok(c.get(P.F_OUTCOME) == P.EV_ARRIVED,
       "and the status carries the verdict, not only the event", str(c))
    r.close()


def test_shortest_way():
    print("the shortest way round the circle, the factory way")
    r = Wheel()
    # the factory way (the detent is always removed): nothing to ask for
    ok(r.fields(r.ask(P.CMD_DIRECTION)).get(P.F_DIRECTION)
       == P.ARG_SHORTEST, "the shortest way by default")
    r.ask(P.CMD_GO + " 1")
    r.wait_event(P.EV_ARRIVED)
    # from 0 degrees to position 5, which is at 288: the short way is backwards
    c = r.fields(r.ask(P.CMD_GO + " 5"))
    ok(c.get(P.F_DIR) == "-",
       "from 0 to 288 degrees it goes backwards, not forwards", str(c))
    r.close()


def near(text, value, slack=2):
    """The cap in ms, from float (firmware) and double (simulator) arithmetic:
    the same formula may differ by a unit in the last place."""
    try:
        return abs(int(text) - value) <= slack
    except (TypeError, ValueError):
        return False


# How many legs a clean positioning may take, the first included:
# with the aim short and the lost motion learnt, the fakes take five to
# seven; without learning it, fourteen and a failure. Not the firmware's own limit
# (1 + 10 approach legs), which is a safety net and not the design.
LEGS_BOUND = 8


def legs_while_moving(r, seconds, angles=None):
    """Samples 'status' while the wheel moves: returns the set of 'dir' values
    seen, and how long the positioning took. With a list in `angles`, every
    angle read is appended to it, the one at rest at the end included."""
    seen, start = set(), time.monotonic()
    end = start + seconds
    while time.monotonic() < end:
        c = r.fields(r.ask(P.CMD_STATUS) or "")
        if angles is not None and P.F_ANGLE in c:
            angles.append(float(c[P.F_ANGLE]))
        if c.get(P.F_MOTION) in (P.MOTION_IDLE, P.MOTION_FAILED) or not c:
            break
        if c.get(P.F_MOTION) == P.MOTION_MOVING:
            seen.add(c.get(P.F_DIR))
        time.sleep(0.01)
    return seen, time.monotonic() - start


def passed_target(start, target, sign, angles, good=P.FACTORY_GOOD_DEG):
    """The first angle that went PAST the target turning one way (sign +1
    up, -1 down), or None. Past means beyond the target by more than the
    good tolerance; the distance still to go that way must only shrink."""
    distance = (sign * (target - start)) % 360.0
    for a in angles:
        left = (sign * (target - a)) % 360.0
        if left > distance + 0.05 and 360.0 - left > good:
            return a
    return None


def test_direction():
    print("one way round: the asymmetric detent")
    r = Wheel()
    c = r.fields(r.ask(P.CMD_DIRECTION))
    # The shortest way: the detent is removed, and "down" (CONFIRMED on the
    # reference wheel while it had its detent, up stalled at every notch)
    # stays an option for a mechanism stiffer one way; the
    # detent itself is always removed now.
    ok(c.get(P.F_DIRECTION) == P.FACTORY_DIRECTION == P.ARG_SHORTEST,
       "the factory direction: the shortest way", str(c))
    # The cap is derived, and the same number from both halves: 300/1200
    # steps (the defaults), 3 retries and up to 10 approach
    # legs give 12.1 s the shortest way, 15.8 s one way - just under a turn,
    # then one retry round.
    ok(near(c.get(P.F_CEILING), 12146), "shortest way: the cap covers half a turn", str(c))
    c = r.fields(r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}"))
    ok(c.get(P.F_DIRECTION) == P.ARG_DOWN and near(c.get(P.F_CEILING), 15771),
       "one way: the cap covers two turns", str(c))
    # speed moves the cap: 50/300 one way is past Ekos's 30 s
    c = r.fields(r.ask(f"{P.CMD_MOTOR} 350 50 300"))
    ok(near(c.get(P.F_CEILING), 38375) and int(c[P.F_CEILING]) > P.EKOS_FILTER_TIMEOUT_MS,
       "the motor reply carries the cap: slow and one way, past Ekos's 30 s", str(c))
    c = r.fields(r.ask(f"{P.CMD_DIRECTION} {P.ARG_SHORTEST}"))
    ok(near(c.get(P.F_CEILING), 16625),
       "slow the shortest way the worst case stays under it", str(c))
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    line = r.ask(f"{P.CMD_DIRECTION} sideways")
    c = r.fields(line)
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} ")
       and c.get(P.F_EXPECTED) == f"{P.ARG_SHORTEST}|{P.ARG_UP}|{P.ARG_DOWN}"
       and c.get(P.F_GOT) == "sideways",
       "an unknown direction is refused, saying what it expects", line)
    ok(r.fields(r.ask(P.CMD_DIRECTION)).get(P.F_DIRECTION) == P.ARG_DOWN,
       "and the refusal changes nothing")
    ok(r.ask(f"{P.CMD_DIRECTION} {P.ARG_UP}").startswith(P.PREFIX_OK)
       and r.ask(P.CMD_SAVE).startswith(P.PREFIX_OK), "direction up, then saved")
    r.close()

    # The stall seen on the reference wheel: going up the motor climbs the steep flank
    # and the disc does not move. The shortest way from 0 to 72 is up...
    r = Wheel("--stall", P.ARG_UP, "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_SHORTEST}")
    r.ask(P.CMD_GO + " 2")
    e = r.wait_outcome(20.0)
    ok(e is not None and e.split()[1] == P.EV_FAILED,
       "the shortest way into the steep flank stalls and fails", str(e))
    r.close()
    # ...one way down the same move goes round the long way, and arrives
    r = Wheel("--stall", P.ARG_UP, "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    c = r.fields(r.ask(P.CMD_GO + " 2"))
    ok(c.get(P.F_DIR) == "-", "one way down, from 0 to 72 it goes backwards", str(c))
    e = r.wait_outcome(20.0)
    ok(e is not None and e.split()[1] == P.EV_ARRIVED,
       "and arrives: one way round avoids the stall", str(e))
    r.close()
    # and the mirror image: up, on a wheel whose steep flank is down
    r = Wheel("--stall", P.ARG_DOWN, "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_UP}")
    c = r.fields(r.ask(P.CMD_GO + " 5"))
    e = r.wait_outcome(20.0)
    ok(c.get(P.F_DIR) == "+" and e is not None and e.split()[1] == P.EV_ARRIVED,
       "one way up, from 0 to 288 it goes forwards and arrives", f"{c} {e}")
    r.close()

    # THE AIM SHORT. One way, a leg that passes the target
    # costs a whole turn, so every leg stops short and the next ones creep
    # in. The step estimate is tried at both ends of what the declared ratio
    # may be off by: the disc 10 % short (the real wheel's side) and 10 %
    # long, and 20 % short (the wheel's legs went 0.84-0.92 of the estimate);
    # the drive's lost motion (the TPU tyre's give, 0.6 degrees on the
    # wheel, the fakes' default) at none, the default, 0.65 and 1 degree.
    # (0.65 with the disc 10 % long is where a short leg that did not move,
    # followed by one sending 0.2 degrees more, went past the target: the
    # step is now kept to half the good tolerance.) Sampled
    # while it moves: the distance still to go only shrinks - never past the
    # target - and it arrives, with no retries and within a bound on the
    # legs. The last case moves TWICE: the lost motion learnt on the first
    # move is kept, and the second must not be pushed past its target by it.
    cases = [("-0.10", "0.6", P.ARG_DOWN, -1), ("-0.10", "0.6", P.ARG_UP, 1),
             ("+0.10", "0.6", P.ARG_DOWN, -1), ("+0.10", "0.6", P.ARG_UP, 1),
             ("+0.10", "0", P.ARG_DOWN, -1), ("+0.10", "0.65", P.ARG_DOWN, -1),
             ("-0.20", "0.6", P.ARG_DOWN, -1),
             ("-0.10", "1.0", P.ARG_DOWN, -1)]
    for n, (ratio, lost, way, sign) in enumerate(cases):
        r = Wheel("--ratio-error", ratio, "--lost-motion", lost, "--ms-per-degree", "2")
        r.ask(f"{P.CMD_DIRECTION} {way}")
        for slot in ((3, 5) if n == len(cases) - 1 else (3,)):
            what = f"estimate {ratio}, lost motion {lost}, {way}, to {slot}"
            c = r.fields(r.ask(f"{P.CMD_GO} {slot}"))
            angles = []
            legs_while_moving(r, 20.0, angles)
            e = r.wait_outcome(5.0)
            s = r.fields(r.ask(P.CMD_STATUS))
            gone = passed_target(float(c.get(P.F_FROM, 0)), float(c.get(P.F_TARGET, 0)),
                                 sign, angles)
            ok(gone is None and len(angles) > 10,
               f"aim short, {what}: never past the target",
               f"passed at {gone}, {len(angles)} samples")
            ok(e is not None and e.split()[1] == P.EV_ARRIVED
               and r.fields(e).get(P.F_RETRIES) == "0" and 2 <= int(s.get(P.F_LEGS, 0)) <= LEGS_BOUND,
               f"aim short, {what}: arrives, no retries, 2 to {LEGS_BOUND} legs",
               f"{e} legs={s.get(P.F_LEGS)}")
        r.close()

    # Already there, one way round: nothing to do. The wheel lands 0.03
    # degrees PAST the target (inside the good tolerance); sent there again
    # it must not go round a whole turn to arrive from behind (2.9 s at the
    # fake's 8 ms/deg) - it stays and says arrived. Exact estimate here:
    # the fixed slip is what puts it past the target.
    r = Wheel("--stuck", "--slip-degrees", "-0.03", "--ratio-error", "0")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    r.ask(P.CMD_GO + " 3")
    first = r.wait_outcome()
    t0 = time.monotonic()
    r.ask(P.CMD_GO + " 3")
    again = r.wait_outcome()
    took = time.monotonic() - t0
    ok(first is not None and again is not None and again.split()[1] == P.EV_ARRIVED
       and took < 1.5,
       "one way, already within tolerance past the target: no turn round",
       f"{first} / {again} after {took:.2f} s")
    r.close()

    # THE RETRIES GO THE SAME WAY. The wheel always lands 5 degrees beyond
    # where it was sent - more than the aim short leaves on the last legs -
    # so it passes the target; the retry must go round (355 degrees) rather
    # than back 5 into the detent. Sampled while it moves: every leg says
    # "-", and the retries take whole turns' time (0.7 s each at 2 ms/deg) -
    # backing up 5 degrees would take a hundredth of that.
    r = Wheel("--stall", P.ARG_UP, "--stuck", "--slip-degrees", "-5",
              "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    r.ask(P.CMD_GO + " 3")
    seen, took = legs_while_moving(r, 25.0)
    e = r.wait_outcome(25.0)
    ok(seen == {"-"}, "one way: every leg, retries included, goes down", str(seen))
    ok(took > 2.5, "a retry after an overshoot goes round the turn",
       f"the positioning took {took:.2f} s")
    ok(e is not None and e.split()[1] == P.EV_FAILED and r.fields(e).get(P.F_RETRIES) == "3",
       "and after the retries the verdict is still the angle read: failed", str(e))
    r.close()


def test_boost():
    print("the boost after a stall")
    # A leg that stalls against a notch - no
    # progress on the angle read, the TMC2208 has no StallGuard - is followed
    # by ONE leg at twice the speed, to break out; then the set speed again.
    # The fakes have a notch at 200 degrees that a leg slower than 400 full
    # steps/s cannot pass; the factory speed is 300, the boost 600.
    r = Wheel("--notch-at", "200", "--notch-min-speed", "400", "--ms-per-degree", "2")
    # slot 3 (144) from 0, one way down, crosses 200: stalls, boosts, arrives
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    r.ask(P.CMD_GO + " 3")
    e = r.wait_outcome(20.0)
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(e is not None and e.split()[1] == P.EV_ARRIVED,
       "a notch that stalls the set speed: the boosted leg gets past it, arrived", str(e))
    ok(c.get(P.F_BOOSTS) == "1" and c.get(P.F_RETRIES) == "1",
       "one stall, one boosted leg, and it counts as a retry", str(c))
    # to slot 4 (216) does not cross it: no boost
    r.ask(P.CMD_GO + " 4")
    e = r.wait_outcome(20.0)
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(e is not None and e.split()[1] == P.EV_ARRIVED and c.get(P.F_BOOSTS) == "0",
       "a move that does not cross the notch needs no boost", f"{e} {c.get(P.F_BOOSTS)}")
    # back to 3 crosses it again: the speed went back to the set one after
    # the boosted leg, so it stalls again and needs the boost again
    r.ask(P.CMD_GO + " 3")
    e = r.wait_outcome(20.0)
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(e is not None and e.split()[1] == P.EV_ARRIVED and c.get(P.F_BOOSTS) == "1",
       "the boost is for one leg: the next crossing stalls and boosts again",
       f"{e} boosts={c.get(P.F_BOOSTS)}")
    r.close()
    # a notch no boost can pass (the boost is 600): it ends failed, honestly
    r = Wheel("--notch-at", "200", "--notch-min-speed", "5000", "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    r.ask(P.CMD_GO + " 3")
    e = r.wait_outcome(25.0)
    ok(e is not None and e.split()[1] == P.EV_FAILED,
       "a notch even the boost cannot pass: failed after the retries", str(e))
    r.close()


def test_jog():
    print("jog: to the angle read now plus a few degrees, closed loop")
    # The calibration tab's jog buttons, -10 .. +10 degrees. A jog is a TARGET, reached by the legs of `go` with the tyre's
    # learnt play - not raw steps: the fakes' tyre swallows 0.6 degrees, as
    # the real one, so a jog of 0.1 degrees of steps would move nothing.
    r = Wheel()
    # a fresh wheel: the play is not learnt yet, and the smallest jogs first
    for delta, sign in (("0.1", 1), ("-0.05", -1)):
        before = float(r.fields(r.ask(P.CMD_STATUS))[P.F_ANGLE])
        line = r.ask(f"{P.CMD_JOG} {delta}")
        c = r.fields(line)
        ok(line.startswith(P.PREFIX_OK) and c.get(P.F_DIR) == ("+" if sign > 0 else "-")
           and abs((float(c.get(P.F_TARGET, -99)) - before - float(delta) + 180.0) % 360.0
                   - 180.0) < 0.011,
           f"jog {delta}: accepted, to the angle read plus {delta}, the right way", line)
        e = r.wait_outcome(10.0)
        s = r.fields(r.ask(P.CMD_STATUS))
        moved = (float(s.get(P.F_ANGLE, before)) - before + 180.0) % 360.0 - 180.0
        ok(sign * moved >= 0.5 * abs(float(delta)),
           f"jog {delta}: the disc REALLY moves, the tyre's play taken up",
           f"moved {moved:.3f}, {e}")
        # Below the sensor's count (0.088) and the fakes' noise (0.03) the
        # loop cannot promise the jog's own tolerance: it ends arrived, or a
        # warning a hair past it - never a failure, and close to the target.
        ok(e is not None and e.split()[1] in (P.EV_ARRIVED, P.EV_WARNING)
           and abs(float(s[P.F_ERR])) <= 0.15,
           f"jog {delta}: ends close to its target, well inside the good tolerance",
           f"{e} err={s.get(P.F_ERR)}")
    # a large one: judged like a `go`, and the events carry the slot
    r.ask(P.CMD_GO + " 2")
    r.wait_outcome()
    c = r.fields(r.ask(f"{P.CMD_JOG} 10"))
    e = r.wait_outcome(10.0)
    s = r.fields(r.ask(P.CMD_STATUS))
    ok(e is not None and e.split()[1] == P.EV_ARRIVED and r.fields(e).get(P.F_POS) == "2"
       and abs(float(s[P.F_ANGLE]) - float(c[P.F_TARGET])) <= P.FACTORY_GOOD_DEG,
       "jog 10: arrived within the good tolerance, the event names the slot", f"{e} {s}")
    ok(s.get(P.F_POS) == "0", "ten degrees off its slot the wheel is between slots", str(s))
    # "Save position": teach takes the angle the jogs left
    line = r.ask(f"{P.CMD_TEACH} 2")
    ok(r.fields(line).get("a2") == s[P.F_ANGLE],
       "teach after a jog takes the jogged angle ('Save position')", f"{line} vs {s[P.F_ANGLE]}")
    # one way only, a jog still goes its own way: no turn round the wheel
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_UP}")
    t0 = time.monotonic()
    c = r.fields(r.ask(f"{P.CMD_JOG} -10"))
    e = r.wait_outcome(10.0)
    took = time.monotonic() - t0
    ok(c.get(P.F_DIR) == "-" and e is not None and e.split()[1] == P.EV_ARRIVED and took < 2.0,
       "direction up, jog -10 goes down 10 degrees, not up round the turn",
       f"{c} {e} {took:.2f} s")
    # refusals: half a turn is the limit (was 30)
    line = r.ask(f"{P.CMD_JOG} 181")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} ")
       and r.fields(line).get(P.F_EXPECTED) == f"-{P.JOG_MAX_DEG}..{P.JOG_MAX_DEG}"
       and r.fields(line).get(P.F_GOT) == "181", "jog 181 refused, saying the range", line)
    ok(P.JOG_MAX_DEG == 360 // P.MIN_SLOTS,
       "the largest jog is the pitch of the wheel with the fewest slots",
       f"{P.JOG_MAX_DEG} vs 360/{P.MIN_SLOTS}")
    for bad in (P.CMD_JOG, f"{P.CMD_JOG} far", f"{P.CMD_JOG} 1 2"):
        line = r.ask(bad)
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "), f"'{bad}' refused", line)
    r.ask(P.CMD_GO + " 4")
    line = r.ask(f"{P.CMD_JOG} 1")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NOT_NOW} "), "jog refused while moving", line)
    r.wait_outcome()
    r.close()
    r = Wheel("--no-magnet")
    line = r.ask(f"{P.CMD_JOG} 1")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NO_MAGNET} "), "jog refused without the magnet", line)
    r.close()


def test_jog_pitch():
    print("jog by one slot pitch, 360/slots: to the next slot, the shortest way")
    # The largest jog button is 360/slots, and JOG_MAX_DEG is 180 for it
    # (30 was too small). On evenly spaced angles a pitch lands on
    # the next slot, either way, going the way the button says.
    r = Wheel()
    r.ask(P.CMD_GO + " 2")
    r.wait_outcome()
    pitch = 360.0 / P.FACTORY_SLOTS
    for delta, sign, slot in ((pitch, "+", "3"), (-pitch, "-", "2"), (-pitch, "-", "1"),
                              (-pitch, "-", "5")):
        t0 = time.monotonic()
        c = r.fields(r.ask(f"{P.CMD_JOG} {delta:.4f}"))
        e = r.wait_outcome(10.0)
        s = r.fields(r.ask(P.CMD_STATUS))
        ok(c.get(P.F_DIR) == sign and e is not None and e.split()[1] == P.EV_ARRIVED
           and s.get(P.F_POS) == slot and time.monotonic() - t0 < 3.0,
           f"jog {delta:+.0f}: {sign} way, lands on slot {slot}", f"{c} {e} {s}")
    r.close()
    # A two-slot wheel: the pitch is half a turn, the one jog with no shorter
    # way. It must go the way its sign says, not whichever way the rounding
    # of the target falls, and land on the other slot.
    r = Wheel("--slots", "2")
    r.ask(P.CMD_GO + " 1")
    r.wait_outcome()
    for delta, sign, slot in (("180", "+", "2"), ("-180", "-", "1"), ("180", "+", "2"),
                              ("180", "+", "1")):
        c = r.fields(r.ask(f"{P.CMD_JOG} {delta}"))
        e = r.wait_outcome(15.0)
        s = r.fields(r.ask(P.CMD_STATUS))
        ok(c.get(P.F_DIR) == sign and e is not None and e.split()[1] == P.EV_ARRIVED
           and s.get(P.F_POS) == slot,
           f"two slots, jog {delta}: the {sign} way as asked, lands on slot {slot}",
           f"{c} {e} {s}")
    r.close()


def test_jog_that_does_not_go():
    print("a jog that stalls is a failure, not a warning")
    # The defect guarded against: a +1 jog that stalled completely still
    # ended Ok. The jog was judged by its distance from its own target - right
    # - but with the warning band of a `go`, which is wider than the small
    # jogs: a stalled +0.5 ended 0.5 degrees off, inside the 0.8 of the band,
    # as a "warning", which the panel shows as a done jog. A jog must have
    # covered half of itself to be a warning (JOG_MOVED_SHARE in wheel.cpp).
    for delta in ("0.5", "0.1", "0.7"):
        r = Wheel("--stall", P.ARG_UP)
        before = float(r.fields(r.ask(P.CMD_STATUS))[P.F_ANGLE])
        r.ask(f"{P.CMD_JOG} {delta}")
        e = r.wait_outcome(20.0)
        s = r.fields(r.ask(P.CMD_STATUS))
        moved = (float(s[P.F_ANGLE]) - before + 180.0) % 360.0 - 180.0
        ok(e is not None and e.split()[1] == P.EV_FAILED and abs(moved) < 0.05
           and s.get(P.F_MOTION) == P.MOTION_FAILED,
           f"jog +{delta} that never moves ends failed, after its retries",
           f"{e} moved {moved:.3f}")
        # (the same jog on a wheel that turns is test_jog's: it arrives. Not
        # tried here the other way: after the stall the learnt play is at
        # its maximum, the jog down overshoots, and its correction goes up -
        # the stalled way.)
        r.close()


# ------------------------------------------------------- the drive ratio

def legs_of(r):
    """The `! leg` events collected so far, consumed, as field dicts."""
    out = [e for e in r.events if e.split()[1] == P.EV_LEG]
    for e in out:
        r.events.remove(e)
    return [r.fields(e) for e in out]


def ratio_of(r):
    return r.fields(r.ask(P.CMD_RATIO) or "")


def move(r, slot, wait=20.0):
    """go, and the verdict; returns (verdict line, status fields, leg events)."""
    r.ask(f"{P.CMD_GO} {slot}")
    e = r.wait_outcome(wait)
    s = r.fields(r.ask(P.CMD_STATUS))
    return e, s, legs_of(r)


def test_ratio_setting():
    # The drive ratio is a setting of the wheel, with the model's value as its factory default, and the `! leg` event opt-in
    print("the drive ratio: a setting with a default, and the leg report")
    r = Wheel()
    c = ratio_of(r)
    factory = f"{P.FACTORY_DRIVE_RATIO:.4f}"
    ok(c.get(P.F_RATIO) == factory and c.get(P.F_BASE) == factory
       and c.get(P.F_FACTORY) == factory,
       "a new wheel runs on the factory ratio, the model's 145/50", str(c))
    ok(abs(P.FACTORY_DRIVE_RATIO - 2.9) < 1e-6, "which is 2.9", str(P.FACTORY_DRIVE_RATIO))
    ok(c.get(P.F_LEARN) == P.ARG_ON and c.get(P.F_LEARNT) == "0",
       "learning on by default, nothing learnt yet", str(c))
    shortest = r.fields(r.ask(P.CMD_DIRECTION)).get(P.F_CEILING)
    ok(c.get(P.F_CEILING) == shortest, "the ratio's reply carries the same cap", f"{c} {shortest}")
    ok(r.fields(r.ask(P.CMD_LEGS)).get(P.F_REPORT) == P.ARG_OFF,
       "the leg report is off at start")
    c = ratio_of(r)
    c = r.fields(r.ask(f"{P.CMD_RATIO} 3.1"))
    ok(c.get(P.F_RATIO) == "3.1000" and c.get(P.F_BASE) == "3.1000"
       and c.get(P.F_FACTORY) == factory,
       "ratio 3.1 sets the base and the one in use", str(c))
    # more steps per degree, a longer worst case: the cap follows the base
    ok(int(c.get(P.F_CEILING, 0)) > int(shortest), "and the cap grows with it", str(c))
    for bad, code in (("0.5", P.ERR_OUT_OF_RANGE), ("29", P.ERR_OUT_OF_RANGE),
                      ("abc", P.ERR_BAD_ARGUMENTS), ("nan", P.ERR_BAD_ARGUMENTS)):
        line = r.ask(f"{P.CMD_RATIO} {bad}") or ""
        ok(line.startswith(f"{P.PREFIX_ERROR} {code} "), f"ratio {bad} refused, code {code}", line)
    line = r.ask(f"{P.CMD_RATIO} 29") or ""
    ok(r.fields(line).get(P.F_EXPECTED) == f"{P.DRIVE_RATIO_MIN:.1f}..{P.DRIVE_RATIO_MAX:.1f}"
       and r.fields(line).get(P.F_GOT) == "29", "the refusal says the range", line)
    line = r.ask(f"{P.CMD_RATIO} {P.ARG_LEARN} maybe") or ""
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "), "ratio learn maybe refused", line)
    ok(ratio_of(r).get(P.F_BASE) == "3.1000" and ratio_of(r).get(P.F_LEARN) == P.ARG_ON,
       "and the refusals change nothing")
    ok(ratio_of(r).get(P.F_LEARN) == P.ARG_ON
       and r.fields(r.ask(f"{P.CMD_RATIO} {P.ARG_LEARN} {P.ARG_OFF}")).get(P.F_LEARN) == P.ARG_OFF,
       "ratio learn off")
    ok(r.fields(r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")).get(P.F_REPORT) == P.ARG_ON,
       "legs on")
    line = r.ask(f"{P.CMD_LEGS} sometimes") or ""
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "), "legs sometimes refused", line)
    # while moving the ratio cannot change: the leg under way used the old one
    r.ask(f"{P.CMD_GO} 3")
    line = r.ask(f"{P.CMD_RATIO} 3.0") or ""
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NOT_NOW} "), "ratio refused while moving", line)
    e = r.wait_outcome(20.0)
    legs = legs_of(r)
    ok(e is not None and len(legs) >= 1 and all(P.F_STEPS in x and P.F_MOVED in x for x in legs),
       "with legs on, every leg is reported, before the verdict", f"{e} {legs}")
    if legs:
        x = legs[0]
        motor = float(x[P.F_MOTOR])
        steps = int(x[P.F_STEPS])
        ok(x[P.F_N] == "1" and x[P.F_KIND] == P.KIND_FIRST and x[P.F_JOG] == P.V_NO
           and x[P.F_RATIO] == "3.1000" and x[P.F_LONG] == P.V_YES,
           "the first leg: number 1, first, not a jog, at the ratio set, long", str(x))
        # the steps are the ratio's: (aim + play) x 200 x 16 / 360 x ratio,
        # and motor= is the same in degrees of motor
        ok(abs(motor - steps * 360.0 / (200 * 16)) < 0.01
           and abs(abs(steps) / (float(x[P.F_AIM]) * 200 * 16 / 360.0 * 3.1) - 1.0) < 0.02,
           "the steps are counted at the ratio in use", str(x))
        ok(all(y[P.F_LEARN] == P.V_NO for y in legs), "and with learning off nothing learnt",
           str([y[P.F_LEARN] for y in legs]))
    ok(r.fields(r.ask(f"{P.CMD_LEGS} {P.ARG_OFF}")).get(P.F_REPORT) == P.ARG_OFF, "legs off")
    e, s, legs = move(r, 1)
    ok(e is not None and not legs, "and with legs off no leg is reported", str(legs[:1]))
    r.close()

    # the memory: a saved ratio and switch come back; a corrupt one does not
    r = Wheel("--nvs", "ratio=3.3,ratio_learn=0")
    c = ratio_of(r)
    ok(c.get(P.F_RATIO) == "3.3000" and c.get(P.F_BASE) == "3.3000"
       and c.get(P.F_LEARN) == P.ARG_OFF, "a saved ratio and learning off come back", str(c))
    r.close()
    r = Wheel("--nvs", "ratio=50")
    ok(ratio_of(r).get(P.F_BASE) == factory, "a saved ratio out of range is not taken")
    r.close()


def test_ratio_learning():
    # The wheel LEARNS its ratio in use, the detent being gone; an unguarded
    # learning was REJECTED because a leg cut short by a notch taught it a
    # ratio 40 % low. The fake disc goes 10 % short of the factory
    # estimate, so the true ratio is 2.9 / 0.9 = 3.222.
    print("the drive ratio, learnt: it converges, and a bad leg does not pull it")
    true_ratio = P.FACTORY_DRIVE_RATIO / 0.9
    tour = (2, 3, 4, 5, 1, 3, 5, 2, 4, 1, 2, 3, 4, 5, 1)

    def run(learn):
        r = Wheel("--ratio-error", "-0.10", "--ms-per-degree", "2")
        r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")
        r.ask(f"{P.CMD_RATIO} {P.ARG_LEARN} {P.ARG_ON if learn else P.ARG_OFF}")
        counts, taught = [], []
        for slot in tour:
            e, s, legs = move(r, slot)
            counts.append(int(s.get(P.F_LEGS, 99)))
            taught += [x for x in legs if x.get(P.F_LEARN) == P.V_YES]
        c = ratio_of(r)
        r.close()
        return counts, taught, c

    counts, taught, c = run(True)
    learnt = float(c.get(P.F_RATIO, 0))
    ok(abs(learnt / true_ratio - 1.0) < 0.02,
       f"learning: the ratio converges to the disc's ({true_ratio:.3f})", str(c))
    ok(max(counts[-5:]) <= 2, "and the legs shrink to one or two a move", str(counts))
    ok(taught and all(x[P.F_KIND] == P.KIND_FIRST and x[P.F_JOG] == P.V_NO
                      and x[P.F_LONG] == P.V_YES for x in taught),
       "only the long first legs of a go teach it", str(taught[:2]))
    ok(c.get(P.F_BASE) == f"{P.FACTORY_DRIVE_RATIO:.4f}" and int(c.get(P.F_LEARNT, 0)) == len(taught),
       "the base stays until saved, and the count is the legs that taught", str(c))
    off_counts, off_taught, c_off = run(False)
    ok(not off_taught and c_off.get(P.F_RATIO) == f"{P.FACTORY_DRIVE_RATIO:.4f}",
       "learning off: nothing learnt, the factory ratio stays", str(c_off))
    ok(sum(off_counts[-5:]) > sum(counts[-5:]),
       "and without it the moves take more legs", f"{off_counts} against {counts}")

    # `save` keeps the ratio in use, which becomes the base. And the very
    # first move teaches nothing: the play of the tyre is not known yet, so
    # what its first leg sent on top of the aim was a guess (m_lost_known)
    r = Wheel("--ratio-error", "-0.10", "--ms-per-degree", "2")
    r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")
    e, s, legs = move(r, 2)
    ok(legs and legs[0].get(P.F_LONG) == P.V_YES and legs[0].get(P.F_LEARN) == P.V_NO,
       "before the play is known, a long first leg teaches nothing", str(legs[:1]))
    for slot in (3, 4, 5, 1):
        move(r, slot)
    # a first leg shorter than 30 degrees does not teach: slot 2 moved to 20
    r.ask(f"{P.CMD_ANGLE} 2 20")
    e, s, legs = move(r, 2)
    ok(legs and legs[0].get(P.F_KIND) == P.KIND_FIRST and legs[0].get(P.F_LONG) == P.V_NO
       and legs[0].get(P.F_LEARN) == P.V_NO,
       "a first leg under 30 degrees teaches nothing", str(legs[:1]))
    move(r, 1)
    before = ratio_of(r).get(P.F_RATIO)
    r.ask(P.CMD_SAVE)
    c = ratio_of(r)
    ok(before != f"{P.FACTORY_DRIVE_RATIO:.4f}" and c.get(P.F_BASE) == before
       and c.get(P.F_RATIO) == before and c.get(P.F_LEARNT) == "0",
       "save keeps the learnt ratio, and it becomes the base", f"{before} {c}")
    r.close()

    # learning off drops the refinement: the base alone, one known number
    r = Wheel("--ratio-error", "-0.10", "--ms-per-degree", "2")
    for slot in (2, 3, 4):
        move(r, slot)
    learnt_now = ratio_of(r)
    c = r.fields(r.ask(f"{P.CMD_RATIO} {P.ARG_LEARN} {P.ARG_OFF}"))
    ok(learnt_now.get(P.F_RATIO) != learnt_now.get(P.F_BASE)
       and c.get(P.F_RATIO) == c.get(P.F_BASE) == f"{P.FACTORY_DRIVE_RATIO:.4f}"
       and c.get(P.F_LEARNT) == "0",
       "learning off goes back to the base", f"{learnt_now} -> {c}")
    r.close()

    # A LEG CUT SHORT DOES NOT PULL IT. Exact estimate here, so the ratio
    # should stay 2.9. The control: the same moves, nothing in the way - the
    # second move's first leg must teach (else the guards below would be
    # proved against a wheel that was not learning anyway).
    def three(*knobs, slots=(2, 4)):
        r = Wheel("--ratio-error", "0", "--ms-per-degree", "2", *knobs)
        r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")
        out = []
        for slot in slots:
            e, s, legs = move(r, slot)
            out.append((e, legs, ratio_of(r).get(P.F_RATIO)))
        r.close()
        return out

    control = three()
    first = control[1][1][0] if control[1][1] else {}
    ok(first.get(P.F_LEARN) == P.V_YES, "control: from 72 to 216 the first leg teaches", str(first))
    # A notch stops the leg from 72 to 216 at 60 % (the case
    # seen on the wheel) or 80 %
    # of the way, slower than the notch lets through
    for share in (0.6, 0.8):
        notch = 72.0 + share * 144.0 + 0.5
        # 500: the set 300 steps/s stalls at the notch, the boosted retry
        # (600) passes it - a long retry leg, which must not teach either
        out = three("--notch-at", f"{notch:.2f}", "--notch-min-speed", "500")
        first = out[1][1][0] if out[1][1] else {}
        ok(first.get(P.F_LEARN) == P.V_NO and float(first.get(P.F_MOVED, 0)) < 0.85 * 144
           and out[1][2] == out[0][2],
           f"a leg cut short at {share:.0%} of the way does not teach, the ratio stays",
           f"{first} {out[0][2]} -> {out[1][2]}")
        after = [x for x in out[1][1][1:] if x.get(P.F_LONG) == P.V_YES]
        # at 60 % the retry is 57 degrees, long; at 80 % 29, short
        ok((after or share > 0.7) and all(x.get(P.F_LEARN) == P.V_NO for x in after),
           f"cut short at {share:.0%}: the long retry after it does not teach either",
           str(after[:1]))
    # A stalled first leg: the steep flank down, the move from 144 to 72
    out = three("--stall", P.ARG_DOWN, slots=(2, 3, 2))
    first = out[2][1][0] if out[2][1] else {}
    ok(out[1][1] and out[1][1][0].get(P.F_LEARN) == P.V_YES
       and first.get(P.F_LEARN) == P.V_NO and out[2][2] == out[1][2],
       "a stalled first leg does not teach, the ratio stays", f"{first} {out[1][2]} -> {out[2][2]}")
    # A jog does not teach, however long
    r = Wheel("--ratio-error", "-0.10", "--ms-per-degree", "2")
    r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")
    move(r, 2)
    r.ask(f"{P.CMD_JOG} 90")
    r.wait_outcome(20.0)
    legs = legs_of(r)
    ok(legs and legs[0].get(P.F_JOG) == P.V_YES and legs[0].get(P.F_LONG) == P.V_YES
       and all(x.get(P.F_LEARN) == P.V_NO for x in legs),
       "a long jog does not teach", str(legs[:1]))
    r.close()


def test_ratio_magnet_lost():
    # A leg during which the magnet was lost does not teach: its "to" may
    # mean nothing. The flicker is in the first 1.5 s of every 4 s from the
    # start of the process; a move is timed inside one, and a control outside.
    print("the drive ratio: not learnt from a leg that lost the magnet")
    t0 = time.monotonic()
    r = Wheel("--ratio-error", "-0.10", "--ms-per-degree", "3", "--magnet-flicker", "40")

    def at(phase):
        """Waits for the next moment `phase` s into a 4 s cycle, then sends
        go until the wheel takes it (it refuses while the magnet is out)."""
        now = time.monotonic() - t0
        wait = (phase - now) % 4.0
        time.sleep(wait)

    def go_when_seen(slot):
        for _ in range(100):
            if (r.ask(f"{P.CMD_GO} {slot}") or "").startswith(P.PREFIX_OK):
                return True
            time.sleep(0.01)
        return False

    r.ask(f"{P.CMD_LEGS} {P.ARG_ON}")
    at(1.7)
    move(r, 2)                       # outside the flicker: arms the play
    at(0.25)
    sent = go_when_seen(3)           # 72 degrees, ~0.2 s + settling, inside
    r.wait_outcome(20.0)
    inside = legs_of(r)
    at(1.7)
    e, s, outside = move(r, 4)       # the control, outside
    first_in = inside[0] if inside else {}
    first_out = outside[0] if outside else {}
    ok(sent and first_in.get(P.F_LONG) == P.V_YES and first_in.get(P.F_LEARN) == P.V_NO,
       "a long first leg run while the magnet flickered does not teach", str(first_in))
    ok(first_out.get(P.F_LEARN) == P.V_YES,
       "control: the same leg with the magnet steady does", str(first_out))
    r.close()


def test_errors():
    print("errors")
    r = Wheel()

    line = r.ask("gibberish")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_UNKNOWN_COMMAND} "),
       "unknown command", line)

    line = r.ask(P.CMD_GO + " 9")
    c = r.fields(line)
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "position out of range", line)
    ok(c.get(P.F_EXPECTED) == f"1..{P.FACTORY_SLOTS}" and c.get(P.F_GOT) == "9",
       "the error carries the parameters for the translation", line)

    line = r.ask(P.CMD_GO)
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "),
       "go without arguments", line)

    line = r.ask(P.CMD_GO + " tre")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "),
       "go with a non-numeric argument", line)

    # every command ALWAYS answers: the rule frankenwheely got wrong
    for command in ["", "   ", P.CMD_STATUS, "xyz", P.CMD_ANGLE + " 1"]:
        if not command.strip():
            continue
        line = r.ask(command)
        ok(line is not None and (line.startswith(P.PREFIX_OK) or
                                 line.startswith(P.PREFIX_ERROR)),
           f"'{command}' gets an outcome anyway", str(line))
    r.close()


def test_names():
    print("filter names")
    r = Wheel()

    line = r.ask(f"{P.CMD_NAME} 3 Green")
    ok(line.startswith(P.PREFIX_OK), "valid name accepted", line)

    line = r.ask(f"{P.CMD_NAME} 3 Baader 7nm")
    c = r.fields(line)
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_FILTER_NAME} "),
       "name with a space refused", line)
    ok(c.get(P.F_REASON) == "bad-char", "with the reason for the refusal", line)

    line = r.ask(f"{P.CMD_NAME} 3 NUL")
    ok(r.fields(line).get(P.F_REASON) == "reserved",
       "Windows device name refused", line)

    line = r.ask(f"{P.CMD_NAME} 3 -Ha")
    ok(r.fields(line).get(P.F_REASON) == "bad-edge",
       "leading hyphen refused", line)

    # duplicates checked case-insensitively: two positions collapsing into the
    # same folder are a silent disaster
    r.ask(f"{P.CMD_NAME} 1 Sii")
    line = r.ask(f"{P.CMD_NAME} 2 sii")
    ok(r.fields(line).get(P.F_REASON) == "duplicate",
       "Ha and ha recognised as the same name", line)

    c = r.fields(r.ask(P.CMD_NAMES))
    ok(c.get("n1") == "Sii", "the name set reads back", str(c))
    # and a name already used by another position does not pass, even identical
    line = r.ask(f"{P.CMD_NAME} 4 Green")
    ok(r.fields(line).get(P.F_REASON) == "duplicate",
       "a name already in use by another position is a duplicate", line)
    r.close()


def test_calibration():
    print("calibration, offsets and saving")
    r = Wheel()

    r.ask(P.CMD_GO + " 2")
    r.wait_outcome()

    # `angle n x` sets a slot's angle (it replaced the trim): it
    # reads back, it does NOT move the wheel, and the next `go` goes there
    line = r.ask(f"{P.CMD_ANGLE} 2 73.5")
    ok(line.startswith(P.PREFIX_OK) and r.fields(line).get("a2") == "73.50",
       "angle accepted, the reply says the new angle", line)
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(c.get(P.F_MOTION) == P.MOTION_IDLE, "angle does not move the wheel by itself", str(c))
    c = r.fields(r.ask(P.CMD_ANGLES))
    ok(c.get("a2") == "73.50" and c.get("a3") == "144.00",
       "the angle reads back, and only that slot's changed", str(c))
    c = r.fields(r.ask(P.CMD_GO + " 2"))
    e = r.wait_outcome()
    s = r.fields(r.ask(P.CMD_STATUS))
    ok(c.get(P.F_TARGET) == "73.50" and e is not None and e.split()[1] == P.EV_ARRIVED
       and s.get(P.F_POS) == "2" and s.get(P.F_TARGET) == "73.50",
       "go goes to the new angle: the target is the angle alone, no trim on top",
       f"{c} {e} {s}")
    # 360 is the same place as 0; both ends of 0..360 are taken
    for value, reads in (("360", "0.00"), ("0", "0.00"), ("359.99", "359.99")):
        line = r.ask(f"{P.CMD_ANGLE} 5 {value}")
        ok(r.fields(line).get("a5") == reads, f"angle 5 {value} reads {reads}", line)
    r.ask(f"{P.CMD_ANGLE} 5 288")
    # refusals, with the range for the translation
    for bad, expected in (("361", f"0..{P.ANGLE_MAX_DEG}"), ("-0.5", f"0..{P.ANGLE_MAX_DEG}")):
        line = r.ask(f"{P.CMD_ANGLE} 2 {bad}")
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} ")
           and r.fields(line).get(P.F_EXPECTED) == expected and r.fields(line).get(P.F_GOT) == bad,
           f"angle {bad} refused, saying the range", line)
    line = r.ask(f"{P.CMD_ANGLE} 9 10")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} ")
       and r.fields(line).get(P.F_EXPECTED) == f"1..{P.FACTORY_SLOTS}",
       "angle on a slot the wheel does not have refused", line)
    for bad in (P.CMD_ANGLE, f"{P.CMD_ANGLE} 2", f"{P.CMD_ANGLE} 2 far", f"{P.CMD_ANGLE} 2 3 4"):
        line = r.ask(bad)
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "), f"'{bad}' refused", line)
    c = r.fields(r.ask(P.CMD_ANGLES))
    ok(c.get("a2") == "73.50", "a refused angle changes nothing", str(c))
    # the rotation trim is gone, all three of its commands
    for gone in ("offset 2 1.5", "offsets", "clear-offsets"):
        line = r.ask(gone)
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_UNKNOWN_COMMAND} "),
           f"'{gone}' is an unknown command now", line)

    # teach takes the current angle
    before = r.fields(r.ask(P.CMD_STATUS))[P.F_ANGLE]
    line = r.ask(f"{P.CMD_TEACH} 2")
    ok(line.startswith(P.PREFIX_OK), "teach accepted at rest", line)
    ok(r.fields(line).get("a2") == before,
       "teach takes the current angle", f"{line} vs {before}")

    line = r.ask(P.CMD_SAVE)
    ok(line.startswith(P.PREFIX_OK), "save accepted", line)
    r.close()

    # teach while the wheel is moving is not allowed
    r = Wheel()
    r.ask(P.CMD_GO + " 4")
    line = r.ask(f"{P.CMD_TEACH} 4")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NOT_NOW} "),
       "teach refused while the wheel is moving", line)
    line = r.ask(f"{P.CMD_ANGLE} 4 200")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NOT_NOW} "),
       "angle refused while the wheel is moving: the move aims at the old one", line)
    r.close()


def test_old_trims_folded():
    print("the rotation trims of an older firmware, folded into the angles once")
    # A wheel saved by a protocol-1 firmware has o<n> keys in its memory, and
    # went to angle + trim. The first start of this firmware adds the trim to
    # the angle and erases the key: the slot stays where it was, and a second
    # start adds nothing more.
    for boots in (1, 2, 3):
        r = Wheel("--nvs", "a2=100,o2=1.5,a3=144,o3=0,o4=-2,o9=7", "--boots", str(boots))
        c = r.fields(r.ask(P.CMD_ANGLES))
        ok(c.get("a2") == "101.50" and c.get("a3") == "144.00" and c.get("a4") == "214.00"
           and c.get("a1") == "0.00" and c.get("a5") == "288.00",
           f"{boots} start(s): each trim folded ONCE into its own slot's angle, "
           "a zero trim and a trim beyond the slots change nothing", str(c))
        c = r.fields(r.ask(P.CMD_GO + " 2"))
        ok(c.get(P.F_TARGET) == "101.50", "and go 2 goes where the old firmware went", str(c))
        r.wait_outcome()
        r.close()


def test_preferences():
    print("preferences")
    r = Wheel()

    # A brand-new wheel starts from the factory tolerances of the shared
    # header (0.30 / 0.80), in the wheel as in the simulator: when each wrote
    # its own, nothing compared them.
    line = r.ask(P.CMD_TOLERANCE)
    c = r.fields(line)
    ok(c.get(P.F_GOOD) == f"{P.FACTORY_GOOD_DEG:.2f}"
       and c.get(P.F_WARN) == f"{P.FACTORY_WARN_DEG:.2f}",
       "a new wheel has the factory tolerances of the header", line)

    line = r.ask(f"{P.CMD_TOLERANCE} 0.20 0.80 5")
    c = r.fields(line)
    ok(c.get(P.F_GOOD) == "0.20" and c.get(P.F_WARN) == "0.80"
       and c.get(P.F_RETRIES) == "5", "tolerances set and read back", line)

    line = r.ask(f"{P.CMD_TOLERANCE} 1.0 0.1 3")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "good tolerance larger than warning refused", line)
    # The refusal carries BOTH parameters of the driver's "expected %1$s, got
    # %2$s", and the same expected= from both halves (a firmware that sent
    # no got= made the user read "got .", and a space in the simulator's
    # expected= cut it in two).
    c = r.fields(line)
    ok(c.get(P.F_EXPECTED) == f"0<good<=warn<={P.TOLERANCE_MAX_DEG},retries=0..{P.RETRIES_MAX}"
       and c.get(P.F_GOT) == "1.0,0.1,3",
       "the tolerance refusal says what it expected and what it got", line)

    # the factory motor settings, one source in the header (not a 350
    # written in each half and in the panel)
    c = r.fields(r.ask(P.CMD_MOTOR))
    ok(c.get(P.F_MA) == str(P.FACTORY_RUN_MA) and c.get(P.F_SPEED) == str(P.FACTORY_SPEED)
       and c.get(P.F_ACCEL) == str(P.FACTORY_ACCEL),
       "a new wheel has the factory motor settings of the header", str(c))
    line = r.ask(f"{P.CMD_MOTOR} 180")
    ok(r.fields(line).get(P.F_MA) == "180", "run current set", line)
    line = r.ask(f"{P.CMD_MOTOR} 5000")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "absurd current refused", line)

    # speed and acceleration reach the wheel (a panel that sent only the
    # current left the other two fields going nowhere)
    c = r.fields(r.ask(f"{P.CMD_MOTOR} 180 350 1200"))
    ok(c.get(P.F_SPEED) == "350" and c.get(P.F_ACCEL) == "1200",
       "speed and acceleration set and read back", str(c))
    c = r.fields(r.ask(P.CMD_MOTOR))
    ok(c.get(P.F_SPEED) == "350" and c.get(P.F_ACCEL) == "1200",
       "and they stay, on a query without arguments", str(c))
    line = r.ask(f"{P.CMD_MOTOR} 180 {P.MOTOR_SPEED_MAX + 1} 1200")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "speed over the limit refused", line)
    line = r.ask(f"{P.CMD_MOTOR} 180 350")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "),
       "speed without acceleration refused", line)
    c = r.fields(r.ask(P.CMD_MOTOR))
    ok(c.get(P.F_SPEED) == "350", "and a refused command changes nothing", str(c))
    # All or nothing, the CURRENT included: the current used to be
    # applied before the speed was checked, so a refused "motor" had already
    # changed it - the error said "nothing done" and the wheel ran hotter.
    r.ask(f"{P.CMD_MOTOR} 300 {P.MOTOR_SPEED_MAX + 1} 1200")
    c = r.fields(r.ask(P.CMD_MOTOR))
    ok(c.get(P.F_MA) == "180",
       "a refused speed does not leave the current changed", str(c))
    r.ask(f"{P.CMD_MOTOR} 300 350")
    c = r.fields(r.ask(P.CMD_MOTOR))
    ok(c.get(P.F_MA) == "180",
       "nor does a speed without acceleration", str(c))

    # holding is zero to start with: released at rest is the default, and the
    # drift watch says when a wheel needs more. No `detent=` in the reply any
    # more (the detent is always removed, the option went)
    c = r.fields(r.ask(P.CMD_HOLD))
    ok(c.get(P.F_MA) == "0", "holding off to start with", str(c))
    ok("detent" not in c, "and says nothing about a detent", str(c))

    before = len(r.comments)
    line = r.ask(f"{P.CMD_HOLD} 50")
    ok(line.startswith(P.PREFIX_OK), "holding on", line)
    ok(len(r.comments) > before,
       "turning holding on warns about the price", str(r.comments[-1:]))

    line = r.ask(f"{P.CMD_HOLD} 9999")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "holding above the run current refused", line)
    r.close()

    # THE DETENT OPTION IS GONE: the motor cannot climb out of
    # the notches, so the detent is always removed and there is nothing to
    # declare. An older driver that still sends `detent` gets the plain
    # "unknown command" - its switch goes to Alert, nothing else happens -
    # and no "no detent" warning is ever printed: with the detent always
    # gone it would sound at every connection.
    r = Wheel()
    before = len(r.comments)
    for asked in ("detent", "detent no", "detent yes"):
        line = r.ask(asked)
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_UNKNOWN_COMMAND} "),
           f"'{asked}' is an unknown command now", line)
    ok(not any("detent" in x for x in r.comments[before:]),
       "and no warning about a detent", str(r.comments[before:]))
    ok(r.fields(r.ask(P.CMD_HOLD)).get(P.F_MA) == "0",
       "and the holding current is left alone", "")
    r.close()


def test_settle():
    """The wait after every leg, energised at the run current, before the
    verdict is read and - on the last leg - the motor released: a setting with a factory value, even with no holding current
    at rest, because the stopped motor brakes the disc through the tyre."""
    print("the settling hold: a setting, energised, and the verdict after it")
    r = Wheel()
    c = r.fields(r.ask(P.CMD_SETTLE) or "")
    ok(c.get(P.F_MS) == str(P.FACTORY_SETTLE_MS),
       "a new wheel holds the factory 300 ms after every leg", str(c))
    shortest = r.fields(r.ask(P.CMD_DIRECTION)).get(P.F_CEILING)
    ok(c.get(P.F_CEILING) == shortest, "the reply carries the move time cap", f"{c} {shortest}")
    c = r.fields(r.ask(f"{P.CMD_SETTLE} 1500") or "")
    ok(c.get(P.F_MS) == "1500", "set to 1500 and read back", str(c))
    # the cap counts the wait once per leg: 1 + 10 approach + 3 retries,
    # times the 25 % margin - 1.2 s more each is 21 s more
    grown = int(c.get(P.F_CEILING, "0")) - int(shortest or 0)
    ok(abs(grown - 21000) <= 2, "and the cap grows by the wait of every leg", str(grown))
    ok(r.fields(r.ask(P.CMD_DIRECTION)).get(P.F_CEILING) == c.get(P.F_CEILING),
       "the same cap the other replies carry", "")
    for bad, code in ((str(P.SETTLE_MS_MAX + 1), P.ERR_OUT_OF_RANGE), ("-1", P.ERR_OUT_OF_RANGE),
                      ("soon", P.ERR_BAD_ARGUMENTS), ("100 200", P.ERR_BAD_ARGUMENTS)):
        line = r.ask(f"{P.CMD_SETTLE} {bad}") or ""
        ok(line.startswith(f"{P.PREFIX_ERROR} {code} "), f"'settle {bad}' refused", line)
    line = r.ask(f"{P.CMD_SETTLE} {P.SETTLE_MS_MAX + 1}") or ""
    c = r.fields(line)
    ok(c.get(P.F_EXPECTED) == f"0..{P.SETTLE_MS_MAX}" and c.get(P.F_GOT) == str(P.SETTLE_MS_MAX + 1),
       "the refusal says what it expected and what it got", line)
    ok(r.fields(r.ask(P.CMD_SETTLE)).get(P.F_MS) == "1500", "and a refusal changes nothing", "")
    ok(r.fields(r.ask(f"{P.CMD_SETTLE} 0")).get(P.F_MS) == "0",
       "0 is allowed: release at once", "")
    r.close()

    # The verdict is read at the END of the wait: the same move takes longer
    # by the wait of every leg it made.
    def timed(ms, *knobs):
        w = Wheel(*knobs)
        w.ask(f"{P.CMD_SETTLE} {ms}")
        t0 = time.monotonic()
        e, st, _ = move(w, 3)
        elapsed = time.monotonic() - t0
        w.close()
        return e, st, elapsed
    e0, s0, t0 = timed(0)
    e1, s1, t1 = timed(1200)
    legs = int(s1.get(P.F_LEGS, "0"))
    ok(e0 is not None and e1 is not None and s0.get(P.F_LEGS) == s1.get(P.F_LEGS),
       "the same move with and without the wait", f"{s0} {s1}")
    ok(t1 - t0 >= 0.9 * 1.2 * legs,
       "the verdict waits for the hold after every leg",
       f"{t1 - t0:.2f} s more for {legs} legs")

    # THE DISC'S INERTIA (--coast): let go sooner than 200 ms after it
    # stopped, the disc slides on 1.5 degrees. Held 300 ms at the run
    # current with NO holding current at rest, it stays where it arrived;
    # released at once (settle 0) it slides past the warning tolerance, and
    # only the drift watch sees it, after a verdict of "arrived".
    def coasting(ms, *more):
        w = Wheel("--coast", "1.5", "--coast-ms", "200", *more)
        w.ask(f"{P.CMD_SETTLE} {ms}")
        e, _, _ = move(w, 3)
        drift = w.wait_event(P.EV_DRIFT, 1.5)
        st = w.fields(w.ask(P.CMD_STATUS))
        w.close()
        return e, drift, st
    e, drift, st = coasting(P.FACTORY_SETTLE_MS)
    ok(e is not None and e.split()[1] == P.EV_ARRIVED and drift is None
       and abs(float(st.get(P.F_ERR, "99"))) <= P.FACTORY_GOOD_DEG,
       "held 300 ms with the hold at 0, the disc stays where it arrived", f"{e} {drift} {st}")
    e, drift, st = coasting(0)
    ok(drift is not None and abs(float(st.get(P.F_ERR, "0"))) > P.FACTORY_WARN_DEG,
       "released at once, the same disc coasts off its slot (the model can fail)",
       f"{e} {drift} {st}")

    # A WAIT LONGER THAN THE CHIP'S OWN POWER-DOWN (0.44 s): the TMC2208
    # drops to its hold current by itself, and at 0 it freewheels. The
    # firmware keeps the hold at the run current through the positioning,
    # so a disc that needs a second to settle is held for all of it: no leg
    # coasts, and no retry is spent chasing a coast.
    w = Wheel("--coast", "1.5", "--coast-ms", "1000")
    w.ask(f"{P.CMD_SETTLE} 1200")
    e, st, _ = move(w, 3, wait=40.0)
    drift = w.wait_event(P.EV_DRIFT, 1.0)
    w.close()
    ok(e is not None and e.split()[1] == P.EV_ARRIVED and st.get(P.F_RETRIES) == "0"
       and drift is None,
       "a 1.2 s hold holds for 1.2 s, past the chip's own power-down", f"{e} {st} {drift}")

    # kept by `save`: a wheel that saved it starts from it; a saved value out
    # of range is a corrupted key, and the factory value is taken
    w = Wheel("--nvs", "settle_ms=750")
    ok(w.fields(w.ask(P.CMD_SETTLE)).get(P.F_MS) == "750", "a saved wait is loaded", "")
    w.close()
    w = Wheel("--nvs", "settle_ms=99999")
    ok(w.fields(w.ask(P.CMD_SETTLE)).get(P.F_MS) == str(P.FACTORY_SETTLE_MS),
       "a corrupted one is not", "")
    w.close()


def test_led():
    print("the LED")
    r = Wheel()
    c = r.fields(r.ask(P.CMD_LED))
    ok(c.get(P.F_STATE) == P.ARG_OFF, "the LED starts off", str(c))
    ok(c.get(P.F_MODE) == P.ARG_PULSE,
       "and in 'pulse' mode: it pulses during changes, by default", str(c))
    for arg, state in ((P.ARG_OFF, P.ARG_OFF), (P.ARG_ON, P.ARG_ON), (P.ARG_PULSE, P.ARG_OFF)):
        r.ask(f"{P.CMD_LED} {arg}")
        c = r.fields(r.ask(P.CMD_LED))
        ok(c.get(P.F_MODE) == arg and c.get(P.F_STATE) == state,
           f"'led {arg}' sets mode {arg}, LED {state}", str(c))

    line = r.ask(f"{P.CMD_LED} {P.ARG_TEST}")
    c = r.fields(line)
    ok(line.startswith(P.PREFIX_OK), "LED test accepted", line)
    ok(c.get(P.F_DURATION) == "6.7",
       "Wheelly in Morse lasts 6.7 seconds as documented", line)
    ok(any(".--" in x for x in r.comments),
       "and it writes the sequence, so it can be read", str(r.comments[-1:]))

    line = r.ask(f"{P.CMD_LED} gibberish")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_BAD_ARGUMENTS} "),
       "unknown LED argument refused", line)
    r.close()


# ------------------------------------------------------------------- faults

def test_slip():
    print("fault: the clutch slips")
    # The shortest way and an exact estimate, so that the only thing that
    # makes a second leg necessary is the slip (one way the aim short would
    # need it anyway). Whether that leg is an approach leg or a retry depends
    # on which way it slipped: what counts is that it is taken.
    r = Wheel("--slip", "1.0", "--slip-degrees", "3", "--ratio-error", "0")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_SHORTEST}")
    r.ask(P.CMD_GO + " 3")
    e = r.wait_outcome()
    ok(e is not None, "with the clutch slipping the move ends", str(e))
    if e:
        outcome = e.split()[1]
        ok(outcome in (P.EV_ARRIVED, P.EV_WARNING),
           "and ends well: arrived, or within the warning tolerance", e)
        ok(int(r.fields(r.ask(P.CMD_STATUS)).get(P.F_LEGS, 0)) >= 2,
           "but takes at least one more leg", e)
    r.close()

    # The middle band is the "report but carry on" one: it must be seen at
    # least once, because it is the case in which Ekos must NOT stop the
    # sequence.
    #
    # The seed can NOT be fixed, and fixing it was the defect. The simulator
    # and the real firmware have two different fake mechanics, so the same
    # seed does not produce the same run: over thirty seeds the simulator
    # ended in a warning thirty times out of thirty (error always 0.320,
    # because there the noise is nil and the slip certain), the real firmware
    # thirteen times out of thirty, with errors between 0.110 and 0.170. With
    # seed 3, written here, the simulator got there and the firmware did not -
    # and the else branch did ok(True), i.e. passed without testing anything.
    # Result: against the real firmware this band, which the comment above
    # declares mandatory, was NEVER checked, and the bench still said
    # "all passed".
    #
    # The seeds were scanned until the band came out, and it FAILED instead of
    # acquitting itself if none did. That scan stopped working when the
    # factory tolerances went from 0.10 / 0.50 to 0.50 / 1.50: on
    # the firmware bench, whose slip is proportional to the leg, the approach
    # legs now always creep inside the good tolerance (errors 0.01-0.48 over
    # ten seeds), and forty seeds gave no warning. Random slip was never the
    # point: the band is reached by a leg that OVERSHOOTS into it - one way
    # the aim short prevents that, the shortest way does not aim short, and
    # an overshoot into the band ends as a warning (see judge() in
    # wheel.cpp). So now it is made on purpose, the same on both fakes: an
    # exact drive, no lost motion, and every leg landing past the target by
    # the middle of the band, derived from the factory values so it follows
    # them. If one day the firmware stopped reporting warnings, it would
    # still be heard here.
    overshoot = (P.FACTORY_GOOD_DEG + P.FACTORY_WARN_DEG) / 2.0
    r = Wheel("--stuck", "--slip-degrees", f"{overshoot:.2f}", "--ratio-error", "0",
              "--lost-motion", "0")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_SHORTEST}")
    r.ask(P.CMD_GO + " 3")
    e = r.wait_outcome()
    motion = r.fields(r.ask(P.CMD_STATUS)).get(P.F_MOTION)
    r.close()
    ok(e is not None and e.split()[1] == P.EV_WARNING,
       "the middle band is reached: the warning really exists", str(e))
    if e is not None and e.split()[1] == P.EV_WARNING:
        offset = abs(float(r.fields(e)[P.F_ERR]))
        ok(P.FACTORY_GOOD_DEG < offset <= P.FACTORY_WARN_DEG,
           "the warning comes with the error between the two tolerances",
           f"offset {offset}")
        ok(motion == P.MOTION_IDLE,
           "and the wheel stays usable: it is not a failure", str(motion))


def test_stuck():
    print("fault: the wheel never arrives")
    # fast fake motor: one way round (down), the wheel always lands 5
    # degrees further down than sent, so it overshoots; each retry after the
    # overshoot is a whole turn, and at the real speed three of them are
    # past the cap
    r = Wheel("--stuck", "--slip-degrees", "-5", "--ms-per-degree", "2")
    r.ask(f"{P.CMD_DIRECTION} {P.ARG_DOWN}")
    r.ask(P.CMD_GO + " 3")
    e = r.wait_event(P.EV_FAILED, wait=25.0)
    ok(e is not None, "declares the failure instead of waiting forever", str(e))
    if e:
        c = r.fields(e)
        ok(int(c[P.F_RETRIES]) == 3, "after using up the retries", e)
        ok(abs(float(c[P.F_ERR])) > P.FACTORY_WARN_DEG, "and with the real residual error", e)

    c = r.fields(r.ask(P.CMD_STATUS))
    ok(c.get(P.F_MOTION) == P.MOTION_FAILED,
       "the status stays failed: that is what puts FILTER_SLOT in Alert", str(c))
    ok(c.get(P.F_OUTCOME) == P.EV_FAILED,
       "and the verdict in the status agrees with the event", str(c))
    r.close()


def test_silent_sensor():
    print("fault: the wheel moves by itself at rest")
    # A wheel that drifts at rest. It is the case in which holding at rest is
    # really needed, and the firmware must notice it AT REST - i.e. when nobody
    # has asked it anything - rather than at the next question.
    # Slow: 0.3 degrees per second. It must ARRIVE and then slide, which is
    # the real case. With a fast drift it would never arrive and something
    # else would be tested - the positioning failure - instead of drift at rest.
    r = Wheel("--drift", "0.3")
    r.ask(P.CMD_GO + " 2")
    ok(r.wait_outcome() is not None, "first it arrives", "")
    event = r.wait_event(P.EV_DRIFT, 8.0)
    ok(event is not None, "then notices by itself that it has drifted", str(r.events))
    if event is not None:
        c = r.fields(event)
        # >= and not >: the event fires AS SOON AS the threshold is crossed,
        # and the offset comes out with two decimals - 1.5001 prints 1.50.
        # Demanding strictly greater would mean demanding the wheel drift a
        # bit more before saying so, which is the opposite of what is wanted.
        ok(P.F_ERR in c and abs(float(c[P.F_ERR])) >= P.FACTORY_WARN_DEG,
           "and says by how much, at least the warning tolerance", event)
    # ONCE PER EPISODE. The wheel keeps drifting, so it stays out of
    # tolerance: if the event repeated, it would fill the log ten times a
    # second, and a warning that always shouts is no longer read by anyone.
    ok(r.wait_event(P.EV_DRIFT, 3.0) is None,
       "and does not repeat it while it stays out", str(r.events))
    r.close()

    # And a wheel that does NOT drift must report nothing: a warning that
    # always sounds is not a warning.
    r = Wheel()
    r.ask(P.CMD_GO + " 2")
    r.wait_outcome()
    ok(r.wait_event(P.EV_DRIFT, 2.0) is None,
       "a wheel at rest reports no drift", str(r.events))
    r.close()

    print("fault: the sensor does not respond")
    r = Wheel("--sensor-silent")
    line = r.ask(P.CMD_GO + " 3")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_SENSOR_SILENT} "),
       "go refused if the sensor is silent", line)
    line = r.ask(P.CMD_DIAG)
    ok(any("SILENT" in x for x in r.comments), "and diag says so", str(r.comments))
    ok(line.startswith(P.PREFIX_OK), "but diag answers anyway", line)
    # A silent sensor has no flags to report: every field of the chip reads 0,
    # as in the firmware (the simulator once sent ml=1 regardless).
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(all(c.get(f) == "0" for f in (P.F_AGC, P.F_MAG, P.F_MD, P.F_ML, P.F_MH)),
       "with the sensor silent status does not invent the field flags", str(c))
    # The order of the checks is the firmware's: the slot's range before the
    # sensor, so a wrong slot is said as such even with the sensor silent
    # (the simulator once answered 4 where the firmware answers 3).
    for command in (P.CMD_GO, P.CMD_TEACH):
        line = r.ask(f"{command} 9")
        ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
           f"{command} 9 with the sensor silent: position out of range first", line)
    r.close()

    r = Wheel("--no-magnet")
    line = r.ask(P.CMD_GO + " 3")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NO_MAGNET} "),
       "go refused if the magnet is not seen", line)
    c = r.fields(r.ask(P.CMD_STATUS))
    ok(c.get(P.F_MD) == "0", "and status says so with md=0", str(c))
    r.close()

    # The lost magnet is announced AT ONCE, at rest, without anybody asking -
    # as the firmware does in Wheel::step(). A simulator that said it only at the end of a move, which a wheel without the magnet never
    # starts never sent the event, and the driver was tested against nothing.
    r = Wheel("--no-magnet")
    e = r.wait_event(P.EV_SENSOR, 3.0)
    ok(e is not None and r.fields(e).get(P.F_MD) == "0",
       "the lost magnet is announced at rest, unasked", str(e))
    ok(r.wait_event(P.EV_SENSOR, 1.5) is None,
       "and only once per loss", str(r.events))
    r.close()

    # A FLICKERING MAGNET (seen on the reference wheel): the
    # MD bit toggling every 20 ms sent "! sensor" tens of times a second. Now
    # one event per loss, and another only after the magnet was seen without
    # a break for a second: the fakes flicker for 1.5 s of every 4, so in
    # 5.5 s there are two episodes, and two events - not seventy.
    r = Wheel("--magnet-flicker", "20")
    deadline = time.monotonic() + 5.5
    sensor_events = 0
    while True:
        line = r._line(deadline)
        if line is None:
            break
        if line.startswith(P.PREFIX_EVENT) and line.split()[1] == P.EV_SENSOR:
            sensor_events += 1
    ok(sensor_events == 2,
       "a flickering magnet: one event per episode, not one per flicker",
       f"{sensor_events} events in 5.5 s")
    r.close()

    # While moving: a bad number of slots is out of range (3), a good one is
    # "not now" (7) - the firmware checks the range first (the simulator
    # once answered 7 to both).
    r = Wheel()
    r.ask(P.CMD_GO + " 3")
    line = r.ask(f"{P.CMD_SLOTS} {P.MAX_SLOTS + 1}")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "slots out of range while moving: out of range", line)
    line = r.ask(f"{P.CMD_SLOTS} {P.MIN_SLOTS}")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NOT_NOW} "),
       "valid slots while moving: not now", line)
    line = r.ask(f"{P.CMD_TEACH} 9")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "teach 9 while moving: position out of range first", line)
    r.wait_outcome()
    r.close()

    # the sensor going silent half-way through a session: the nasty case, the
    # one the real hardware does not produce on demand
    r = Wheel("--sensor-silent-after", "1")
    r.ask(P.CMD_GO + " 2")
    r.wait_event(P.EV_ARRIVED)
    line = r.ask(P.CMD_GO + " 4")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_SENSOR_SILENT} "),
       "the sensor dying after a move is noticed", line)
    r.close()


def test_nvs_broken():
    print("fault: the NVS cannot be written")
    r = Wheel("--nvs-broken")
    line = r.ask(P.CMD_SAVE)
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_NVS_WRITE} "),
       "the failed save is reported", line)
    r.close()


def test_other_wheel():
    print("a wheel with a different number of positions")
    # It is why the number of positions lives in the wheel and not in the
    # code: one firmware, and one driver, serve different wheels. Separate
    # "Wheelly5" and "Wheelly7" drivers would force whoever installs to know
    # how many positions their wheel has to pick the right entry - that is,
    # exactly the information the wheel can already tell.
    r = Wheel("--slots", "7")
    c = r.fields(r.ask(P.CMD_VERSION))
    ok(c.get(P.F_SLOTS) == "7", "a seven-slot wheel declares it", str(c))

    c = r.fields(r.ask(P.CMD_ANGLES))
    ok(len(c) == 7, "and has seven calibration angles", str(c))
    ok(abs(float(c["a2"]) - 360.0 / 7) < 0.01,
       "split into equal parts", str(c.get("a2")))

    c = r.fields(r.ask(P.CMD_NAMES))
    ok(len(c) == 7, "and seven names, all valid", str(c))

    line = r.ask(f"{P.CMD_GO} 7")
    ok(line.startswith(P.PREFIX_OK), "the seventh position exists", line)
    line = r.ask(f"{P.CMD_GO} 8")
    ok(r.fields(line).get(P.F_EXPECTED) == "1..7",
       "the eighth does not, and the error says so", line)
    r.close()

    # and it can be changed live, which is how a new wheel is configured
    r = Wheel()
    ok(r.fields(r.ask(P.CMD_SLOTS)).get(P.F_SLOTS) == str(P.FACTORY_SLOTS),
       "a factory wheel has five")
    line = r.ask(f"{P.CMD_SLOTS} 9")
    ok(r.fields(line).get(P.F_SLOTS) == "9", "they can be raised to nine", line)
    c = r.fields(r.ask(P.CMD_NAMES))
    ok(len(c) == 9, "and the names become nine", str(c))
    line = r.ask(f"{P.CMD_SLOTS} 99")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} "),
       "ninety-nine no", line)
    # one slot is not a filter wheel (a firmware that took 1 left a wheel the
    # panel, which starts from 2, could not show); the error says the range, from MIN_SLOTS
    line = r.ask(f"{P.CMD_SLOTS} 1")
    ok(line.startswith(f"{P.PREFIX_ERROR} {P.ERR_OUT_OF_RANGE} ")
       and r.fields(line).get(P.F_EXPECTED) == f"{P.MIN_SLOTS}..{P.MAX_SLOTS}",
       "a single position no, and the error says 2 to 12", line)
    line = r.ask(f"{P.CMD_SLOTS} {P.MIN_SLOTS}")
    ok(r.fields(line).get(P.F_SLOTS) == str(P.MIN_SLOTS), "two yes", line)
    r.close()


def test_determinism():
    print("same seed, same run")
    readings = []
    for _ in range(2):
        r = Wheel("--seed", "42", "--slip", "0.5")
        r.ask(P.CMD_GO + " 4")
        e = r.wait_outcome() or ""
        readings.append((e.split()[1] if e else None, r.fields(e).get(P.F_ERR)))
        r.close()
    ok(readings[0] == readings[1] and readings[0] is not None,
       "two runs with the same seed give the same residual error",
       str(readings))


# --------------------------------- the agreement between the two copies of the rule

def test_name_rule_agreement():
    print("agreement between the Python rule and the C++ one")

    executable = "/tmp/wheelly_name_rule"
    source = HERE / "name_rule.cpp"
    build = subprocess.run(
        [os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra",
         "-Werror", "-O1", "-o", executable, str(source)],
        capture_output=True, text=True)
    if build.returncode != 0:
        ok(False, "name_rule.cpp compiles", build.stderr.strip()[:400])
        return

    cases = [
        "", "Ha", "Lum", "Red", "Green", "Blue", "H_Alpha", "SII", "OIII",
        "O-III", "L-eXtreme", "Ha_3nm", "7nm_Ha", "1.25", "Baader 7nm",
        "R (Astrodon)", "L/RGB", "NUL", "nul", "con", "COM1", "com9", "LPT9",
        "COM0", "CONE", "NULL", "nul.fits", "-Ha", ".Ha", "_Ha", "Ha-", "Ha.",
        "Ha_", "A" * 32, "A" * 33, "A" * 200, "Hα", "Luminosità",
        "Ha=1", "Ha\tL", "Ha\nL", "Ha|L", "Ha<L", "1.25\"", "a", "Z9",
    ]
    # every single byte, then a handful of random strings: that is where the
    # differences nobody thinks of testing hide
    cases += [chr(b) for b in range(1, 256)]
    cases += ["A" + chr(b) + "B" for b in range(1, 256)]
    rng = random.Random(7)
    alphabet = "AZaz09_-. \t\"'/\\:*?<>|()àα"
    for _ in range(600):
        length = rng.randint(0, 40)
        cases.append("".join(rng.choice(alphabet) for _ in range(length)))

    stdin = "\n".join(c.encode("utf-8").hex() for c in cases) + "\n"
    result = subprocess.run([executable], input=stdin,
                            capture_output=True, text=True)
    answers = result.stdout.split()
    ok(len(answers) == len(cases), "the C++ program answers every case",
       f"{len(answers)} answers for {len(cases)} cases")
    if len(answers) != len(cases):
        return

    disagreements = []
    for text, from_cpp in zip(cases, answers):
        # the Python copy reasons on characters, the C++ on bytes: they are
        # compared on what really travels on the wire, i.e. the UTF-8 bytes
        raw = text.encode("utf-8")
        from_python = P.check_name(raw.decode("latin-1"))
        if from_python != int(from_cpp):
            disagreements.append((text, from_python, int(from_cpp)))

    ok(not disagreements, "the two copies of the rule say the same thing",
       f"{len(disagreements)} disagreements, for example {disagreements[:3]}")
    print(f"    ({len(cases)} inputs compared)")


# --------------------------------------------------------------------- start

def main():
    who = "the real firmware, compiled for the PC" if not IS_PYTHON \
          else "the Python simulator"
    print(f"\nTests on the wheel protocol - {who}")
    print("=" * (32 + len(who)) + "\n")

    test_identification()
    test_status()
    test_motion()
    test_shortest_way()
    test_direction()
    test_boost()
    test_jog()
    test_jog_pitch()
    test_jog_that_does_not_go()
    test_ratio_setting()
    test_ratio_learning()
    test_ratio_magnet_lost()
    test_errors()
    test_names()
    test_calibration()
    test_old_trims_folded()
    test_preferences()
    test_settle()
    test_led()
    test_slip()
    test_stuck()
    test_silent_sensor()
    test_nvs_broken()
    test_other_wheel()
    test_determinism()
    test_name_rule_agreement()

    print("\n--------------------------------")
    print(f"{passed} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
