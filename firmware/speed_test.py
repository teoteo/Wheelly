#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT
"""Speed and precision test of a real wheel: for each setting of current,
speed and acceleration, a tour of all the slots, and a table of what came out.

A method kept on purpose: it may become a button in the calibration tab. It
found the working range of the reference wheel without its detent - every setting from 100 to 1000 full steps/s arrived,
precision under 0.15 deg on four slots out of five - and the factory setting
350 mA, 300/1200, shortest way.

It talks to the wheel's own firmware over its serial port, so it must run on
the computer the wheel is plugged into, with Ekos DISCONNECTED from the wheel
(one program at a time on the port). What the wheel has saved is not touched:
the settings of the test are sent without `save`, and at the end the ones
read at the start are sent back.

    python3 speed_test.py                       /dev/ttyACM0 (Linux) or the
                                                first /dev/cu.usbmodem* (Mac)
    python3 speed_test.py --port /dev/ttyACM0 --configs "400/100/400 350/300/1200"
    python3 speed_test.py --out ~/Documents     where the CSV goes (dated name)

A config is MA/SPEED/ACCEL, speed and acceleration in FULL steps per second.
The CSV has one row per move: config, slot, target, verdict, error, legs,
boosts, seconds.
"""
import argparse
import datetime
import glob
import os
import re
import sys
import termios
import time

DEFAULT_CONFIGS = ("400/100/400 400/150/600 400/200/800 400/300/1200 350/300/1200 "
                   "400/400/1600 400/600/2400 400/800/3200 400/1000/4000")


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
        os.write(self.fd, (command + "\n").encode())
        return [l for l in self.lines(wait) if l.startswith(("ok", "error"))]

    def fields(self, reply):
        return dict(x.split("=", 1) for x in reply[3:].split() if "=" in x)


def slots_of(wheel):
    for r in wheel.ask("angles"):
        if r.startswith("ok a1="):
            return len([k for k in wheel.fields(r) if re.fullmatch(r"a\d+", k)])
    return 5


def move(wheel, slot, timeout):
    """One move: until its event, or the timeout. Returns a dict."""
    t0 = time.time()
    os.write(wheel.fd, ("go %d\n" % slot).encode())
    res = {"slot": slot, "verdict": "timeout", "err": None, "legs": 0, "boosts": 0}
    while time.time() - t0 < timeout:
        os.write(wheel.fd, b"status\n")
        for l in wheel.lines(0.25):
            if l.startswith("ok target="):
                res["target"] = wheel.fields(l).get("target")
            elif l.startswith("ok pos="):
                f = wheel.fields(l)
                res["legs"] = max(res["legs"], int(f.get("legs", f.get("retries", 0))))
                res["boosts"] = max(res["boosts"], int(f.get("boosts", 0)))
            elif l.startswith("!") and l.split()[1] in ("arrived", "warning", "failed"):
                res["verdict"] = l.split()[1]
                res["err"] = float(re.search(r"err=([-\d.]+)", l).group(1))
                res["seconds"] = round(time.time() - t0, 2)
                return res
    res["seconds"] = round(time.time() - t0, 2)
    wheel.ask("stop")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port")
    ap.add_argument("--configs", default=DEFAULT_CONFIGS)
    ap.add_argument("--out", default=os.path.expanduser("~/Documents"),
                    help="folder of the CSV (its name carries date and time)")
    ap.add_argument("--timeout", type=float, default=20.0, help="seconds per move")
    a = ap.parse_args()
    port = a.port or (["/dev/ttyACM0"] if os.path.exists("/dev/ttyACM0")
                      else sorted(glob.glob("/dev/cu.usbmodem*")))[0]
    wheel = Wheel(port)
    wheel.lines(0.5)
    before = [r for r in wheel.ask("motor") + wheel.ask("direction") if r.startswith("ok")]
    saved_motor = wheel.fields(before[0]) if before else None
    n = slots_of(wheel)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs(a.out, exist_ok=True)
    csv_path = os.path.join(a.out, "wheelly_speed_test_%s.csv" % stamp)
    rows = []
    print("%-14s %-6s %-34s %-10s %-5s %s" % ("mA/speed/acc", "ok", "error per slot (deg)",
                                             "seconds", "legs", "boosts"))
    for cfg in a.configs.split():
        ma, sp, ac = cfg.split("/")
        wheel.ask("motor %s %s %s" % (ma, sp, ac))
        res = [move(wheel, s, a.timeout) for s in range(1, n + 1)]
        for r in res:
            rows.append([cfg, r["slot"], r.get("target", ""), r["verdict"],
                         "" if r["err"] is None else r["err"], r["legs"], r["boosts"], r["seconds"]])
        good = sum(r["verdict"] in ("arrived", "warning") for r in res)
        errs = " ".join("--" if r["err"] is None else "%.2f" % abs(r["err"]) for r in res)
        secs = [r["seconds"] for r in res]
        print("%-14s %d/%-4d %-34s %4.1f-%-5.1f %-5d %d" % (
            cfg, good, len(res), errs, min(secs), max(secs),
            max(r["legs"] for r in res), max(r["boosts"] for r in res)))
    # what the wheel had before the test, back - without saving anything
    if saved_motor:
        wheel.ask("motor %s %s %s" % (saved_motor["ma"], saved_motor["speed"], saved_motor["accel"]))
    with open(csv_path, "w") as f:
        f.write("config,slot,target,verdict,error_deg,legs,boosts,seconds\n")
        f.writelines(",".join(str(x) for x in r) + "\n" for r in rows)
    print("written %s" % csv_path)


if __name__ == "__main__":
    sys.exit(main())
