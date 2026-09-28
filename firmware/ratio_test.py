#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT
"""Drive ratio test of a real wheel: how many degrees of motor make one degree
of disc, measured on the wheel instead of declared from the model.

Why. The motor drives the disc by friction, a TPU tyre on the
clutch pressing on the disc's knurled rim, and the ratio is the rim's
diameter over the diameter the tyre REALLY rolls on - squashed by the spring,
sunk in the knurl - not the drawing's 145/50 = 2.90. The firmware estimates
every leg with it (the verdict is always the angle read), and legs on the
reference wheel moved 0.84-0.92 of the estimate: the true ratio is higher.
The ratio is a setting of each wheel (`ratio`, saved with
`save`), and this script measures it.

THE METHOD. Every leg of a move sends a number of motor steps, and the wheel,
after `legs on`, reports each one: steps, motor degrees, the disc angle
before and after (`! leg`). The ratio is motor degrees over disc degrees -
but not leg by leg, because of the PLAY: the clutch's TPU tyre swallows some
steps (about 0.6 degrees of disc, 1.7 of motor, on the reference wheel) before
the disc moves, and with the motor released at rest it gives them back, so
EVERY leg pays it again. On one leg that is an error of 1-3 %; so the legs
are of two lengths, and a straight line through (disc degrees, motor
degrees) gives the ratio as its SLOPE and the play as its intercept.

Why LONG legs, in the SAME direction, at LOW speed:
  - long (60 and 150 degrees by default), so the play and the sensor's
    resolution (one AS5600 count is 0.09 degrees) weigh little, and only the
    FIRST leg of each move is used: the approach legs after it are short
    and start from a disc that has just stopped;
  - the same direction, N moves in a row, after a first move that takes up
    the backlash: a reversal adds the play on the other side of the tyre,
    and a leg after a reversal would carry both; then the same the other
    way, to see whether the two directions agree (a clutch that rolls on a
    different diameter one way than the other would show here);
  - slow (200 full steps/s by default, 800/s^2), where the friction drive
    does not slip: a slipping leg reads as a higher ratio.
The moves are `jog`s, relative and closed loop like `go`: the wheel ends each
one where it was asked, and a jog is never learnt from by the wheel itself
(Wheel::judge), so the test does not disturb the ratio the wheel is learning.

It talks to the wheel's own firmware over its serial port, so it must run on
the computer the wheel is plugged into, with Ekos DISCONNECTED from the wheel
(one program at a time on the port). NOTHING IS SAVED unless --apply is
given: speed and the leg report are set without `save`, and at the end the
ones read at the start are sent back (also after Ctrl-C). With --apply the
suggested ratio is sent with `ratio <value>` and then `save` - which writes
EVERYTHING the wheel holds, as the panel's "Save to the wheel" does: if the
calibration was changed and not saved, it is saved too.

    python3 ratio_test.py                       /dev/ttyACM0 (Linux) or the
                                                first /dev/cu.usbmodem* (Mac)
    python3 ratio_test.py --port /dev/ttyACM0 --legs 6 --degrees 60,150
    python3 ratio_test.py --speed 150           slower still
    python3 ratio_test.py --apply               and set and save the result
    python3 ratio_test.py --out ~/Documents     where the CSV goes (dated name)

The CSV has one row per move: direction, number, degrees asked, the first
leg's steps, motor degrees, aim, disc angles before and after, disc degrees
moved, its ratio with and without the play, whether it was used, verdict.
"""
import argparse
import datetime
import glob
import os
import re
import statistics
import sys
import termios
import time

# the wheel's protocol words, from the shared header like the simulator does:
# one list, not a copy that drifts
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator"))
import protocol as P  # noqa: E402

TERMINAL = (P.EV_ARRIVED, P.EV_WARNING, P.EV_FAILED)
# A leg whose ratio is further than this from the median of its direction is
# not used: a slip, a stall, a knock. Said in the table, not hidden.
OUTLIER = 0.10


def open_port(path):
    fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    a = termios.tcgetattr(fd)
    a[0] = 0
    a[1] = 0
    a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    a[3] = 0
    a[4] = a[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, a)
    return fd


class Wheel:
    def __init__(self, path):
        self.fd = open_port(path)
        self.buf = b""

    def lines(self, wait):
        """Every line that arrives within `wait` seconds."""
        end, out = time.time() + wait, []
        while time.time() < end:
            try:
                self.buf += os.read(self.fd, 4096)
            except BlockingIOError:
                time.sleep(0.01)
            *done, self.buf = self.buf.split(b"\n")
            out += [d.decode(errors="replace").strip() for d in done]
        return out

    def ask(self, command, wait=0.4):
        """The reply line (ok or error) of one command, or None."""
        os.write(self.fd, (command + "\n").encode())
        end = time.time() + max(wait, 3.0)
        while time.time() < end:
            for line in self.lines(0.05):
                if line.startswith((P.PREFIX_OK, P.PREFIX_ERROR)):
                    return line
        return None

    @staticmethod
    def fields(reply):
        return dict(x.split("=", 1) for x in (reply or "").split()[1:] if "=" in x)


def jog(wheel, degrees, timeout):
    """One jog: its leg reports until the verdict. Returns (verdict, legs)."""
    os.write(wheel.fd, ("%s %.2f\n" % (P.CMD_JOG, degrees)).encode())
    t0, legs = time.time(), []
    while time.time() - t0 < timeout:
        for line in wheel.lines(0.1):
            if line.startswith(P.PREFIX_ERROR):
                return line, legs
            if not line.startswith(P.PREFIX_EVENT):
                continue
            name = line[1:].split()[0]
            if name == P.EV_LEG:
                legs.append(Wheel.fields(line))
            elif name in TERMINAL:
                return name, legs
    wheel.ask(P.CMD_STOP)
    return "timeout", legs


def fit(points):
    """Least squares motor = slope * disc + intercept. None with fewer than
    two distinct lengths: the slope would be undetermined."""
    if len(points) < 2 or max(d for d, _ in points) - min(d for d, _ in points) < 10.0:
        return None
    n = len(points)
    mx = sum(d for d, _ in points) / n
    my = sum(m for _, m in points) / n
    sxx = sum((d - mx) ** 2 for d, _ in points)
    sxy = sum((d - mx) * (m - my) for d, m in points)
    slope = sxy / sxx
    return slope, my - slope * mx


def measure(wheel, sign, sizes, legs, timeout, rows):
    """Takes up the play with a first move, then `legs` moves `sign` way."""
    verdict, _ = jog(wheel, sign * 20.0, timeout)
    print("  %s: play taken up (%s)" % ("up" if sign > 0 else "down", verdict))
    points = []
    for i in range(legs):
        size = sizes[i % len(sizes)]
        verdict, reported = jog(wheel, sign * size, timeout)
        first = next((x for x in reported if x.get(P.F_N) == "1"), None)
        row = {"direction": "up" if sign > 0 else "down", "n": i + 1, "asked": size,
               "verdict": verdict}
        if first is not None:
            motor = abs(float(first[P.F_MOTOR]))
            moved = float(first[P.F_MOVED])
            row.update(steps=int(first[P.F_STEPS]), motor=motor, aim=float(first[P.F_AIM]),
                       frm=float(first[P.F_FROM]), to=float(first[P.F_TO]), moved=moved,
                       long=first.get(P.F_LONG), wheel_ratio=float(first[P.F_RATIO]))
            if moved > 0 and first.get(P.F_LONG) == P.V_YES:
                points.append((moved, motor, row))
        rows.append(row)
        print("    %-5s %3d  %6.1f deg  first leg %s" % (
            row["direction"], i + 1, size,
            "moved %.2f for %.2f motor deg" % (row["moved"], row["motor"])
            if "moved" in row else "NOT reported (%s)" % verdict))
    # outliers: a leg far from the others' raw ratio (motor / disc)
    if points:
        median = statistics.median(m / d for d, m, _ in points)
        kept = []
        for d, m, row in points:
            row["raw_ratio"] = m / d
            if abs((m / d) / median - 1.0) <= OUTLIER:
                kept.append((d, m, row))
                row["used"] = "yes"
            else:
                row["used"] = "no (outlier)"
        points = kept
    line = fit([(d, m) for d, m, _ in points])
    if line is None:
        return None
    slope, play = line
    for d, m, row in points:
        row["ratio"] = (m - play) / d
    return {"slope": slope, "play_motor": play, "n": len(points),
            "each": [row["ratio"] for _, _, row in points]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port")
    ap.add_argument("--legs", type=int, default=6, help="moves per direction (default 6)")
    ap.add_argument("--degrees", default="60,150",
                    help="the lengths of the moves, alternated, at most %d (default 60,150)"
                         % P.JOG_MAX_DEG)
    ap.add_argument("--speed", type=int, default=200, help="full steps/s (default 200)")
    ap.add_argument("--accel", type=int, help="full steps/s^2 (default 4 x speed)")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds per move")
    ap.add_argument("--apply", action="store_true",
                    help="send the suggested ratio with `ratio` and `save` it")
    ap.add_argument("--out", default=os.path.expanduser("~/Documents"),
                    help="folder of the CSV (its name carries date and time)")
    a = ap.parse_args()
    sizes = [float(x) for x in a.degrees.split(",")]
    if not all(0 < s <= P.JOG_MAX_DEG for s in sizes) or a.legs < 2:
        ap.error("--degrees between 0 and %d, --legs at least 2" % P.JOG_MAX_DEG)
    port = a.port or (["/dev/ttyACM0"] if os.path.exists("/dev/ttyACM0")
                      else sorted(glob.glob("/dev/cu.usbmodem*")))[0]
    wheel = Wheel(port)
    wheel.lines(0.5)
    who = Wheel.fields(wheel.ask(P.CMD_VERSION))
    if who.get(P.F_NAME) != "wheelly":
        sys.exit("no Wheelly on %s (is Ekos still connected?)" % port)
    before_ratio = Wheel.fields(wheel.ask(P.CMD_RATIO))
    if P.F_RATIO not in before_ratio:
        sys.exit("this firmware (%s) has no `ratio`: flash a newer one"
                 % who.get(P.F_FW))
    before_motor = Wheel.fields(wheel.ask(P.CMD_MOTOR))
    before_legs = Wheel.fields(wheel.ask(P.CMD_LEGS)).get(P.F_REPORT, P.ARG_OFF)
    print("wheel %s, fw %s: ratio in use %s (base %s, factory %s, learning %s, %s legs learnt)"
          % (who.get(P.F_SERIAL), who.get(P.F_FW), before_ratio.get(P.F_RATIO),
             before_ratio.get(P.F_BASE), before_ratio.get(P.F_FACTORY),
             before_ratio.get(P.F_LEARN), before_ratio.get(P.F_LEARNT)))

    rows, result = [], {}
    try:
        wheel.ask("%s %s" % (P.CMD_LEGS, P.ARG_ON))
        reply = wheel.ask("%s %s %d %d" % (P.CMD_MOTOR, before_motor.get(P.F_MA, P.FACTORY_RUN_MA),
                                           a.speed, a.accel or 4 * a.speed))
        if not (reply or "").startswith(P.PREFIX_OK):
            sys.exit("speed refused: %s" % reply)
        for sign in (1, -1):
            result[sign] = measure(wheel, sign, sizes, a.legs, a.timeout, rows)
    finally:
        # what the wheel had before the test, back - without saving anything
        if P.F_SPEED in before_motor:
            wheel.ask("%s %s %s %s" % (P.CMD_MOTOR, before_motor[P.F_MA],
                                       before_motor[P.F_SPEED], before_motor[P.F_ACCEL]))
        wheel.ask("%s %s" % (P.CMD_LEGS, before_legs))

    print("\n%-6s %-4s %-9s %-16s %-14s" % ("way", "legs", "ratio", "spread (1 sd)", "play"))
    good = []
    for sign in (1, -1):
        r = result.get(sign)
        name = "up" if sign > 0 else "down"
        if r is None:
            print("%-6s  -- not enough good legs of two lengths" % name)
            continue
        sd = statistics.stdev(r["each"]) if len(r["each"]) > 1 else 0.0
        print("%-6s %-4d %-9.4f %-16s %.2f motor deg = %.2f disc deg" % (
            name, r["n"], r["slope"], "%.4f (%.2f %%)" % (sd, 100 * sd / r["slope"]),
            r["play_motor"], r["play_motor"] / r["slope"]))
        good.append(r)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(a.out, exist_ok=True)
    csv_path = os.path.join(a.out, "wheelly_ratio_test_%s.csv" % stamp)
    keys = ("direction", "n", "asked", "steps", "motor", "aim", "frm", "to", "moved",
            "raw_ratio", "ratio", "used", "verdict", "wheel_ratio")
    with open(csv_path, "w") as f:
        f.write("direction,n,asked_deg,steps,motor_deg,aim_deg,from_deg,to_deg,moved_deg,"
                "ratio_with_play,ratio,used,verdict,ratio_in_use\n")
        for row in rows:
            f.write(",".join("" if row.get(k) is None else
                             ("%.4f" % row[k] if isinstance(row[k], float) else str(row[k]))
                             for k in keys) + "\n")
    print("written %s" % csv_path)
    if not good:
        return 1
    suggested = round(sum(r["slope"] for r in good) / len(good), 4)
    if len(good) == 2:
        apart = abs(good[0]["slope"] - good[1]["slope"]) / suggested
        print("the two directions differ by %.2f %%" % (100 * apart))
    after = Wheel.fields(wheel.ask(P.CMD_RATIO))
    print("\nSUGGESTED: ratio %.4f   (factory %s; the wheel is using %s, learnt from %s legs)"
          % (suggested, after.get(P.F_FACTORY), after.get(P.F_RATIO), after.get(P.F_LEARNT)))
    if a.apply:
        r1 = wheel.ask("%s %.4f" % (P.CMD_RATIO, suggested))
        r2 = wheel.ask(P.CMD_SAVE, wait=2.0)
        print("applied: %s / %s" % (r1, r2))
    else:
        print("nothing saved: run again with --apply, or send `ratio %.4f` and `save`" % suggested)
    return 0


if __name__ == "__main__":
    sys.exit(main())
