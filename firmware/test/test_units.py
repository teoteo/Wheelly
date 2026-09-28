#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""The units across the boundary between wheel.cpp and the XIAO's mechanics.

Why this exists. wheel.h's STEPS_PER_DEGREE counts MICROsteps, and
MechanicsEsp32::move() once multiplied them by 16 more: every move on the
real wheel was sixteen times its estimate. No test could see it: the ESP32
mechanics does not compile on the Mac, and the bench's fake mechanics turned
steps back into degrees with the same constant.

Two checks, declared for what they are:

  - a READING of mechanics_esp32.cpp, not an execution: move() hands its
    microsteps to the stepper as they are, while speed() does convert full
    steps into pulses. It is a text check because the file needs FastAccelStepper
    and the Arduino core; it is here because the alternative was no check.
  - the arithmetic of steps_per_degree() at the factory ratio against the
    wheel's physics, written here independently: a 200-step motor, 16
    microsteps, a 50 mm clutch on the rim of a 145 mm disc (DECLARED from the
    model, not measured);
  - the factory ratio's two diameters, in the shared header, against the
    CAD's parameters (the ratio is a setting whose default is the model's,
    derived and not typed).

    python3 test_units.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
FIRMWARE = HERE.parent / "wheelly"

failed = []


def ok(condition, what, detail=""):
    print(("  ok      " if condition else "  FAILED: ") + what +
          ("" if condition else f" -> {detail}"))
    if not condition:
        failed.append(what)


def body(source, signature):
    """The text of a function body, from its signature to the closing brace
    at column 0."""
    start = source.find(signature)
    if start < 0:
        return None
    end = source.find("\n}", start)
    return source[start:end]


def main():
    print("\nThe units between wheel.cpp and the XIAO's mechanics")
    print("====================================================\n")
    src = (FIRMWARE / "mechanics_esp32.cpp").read_text(encoding="utf-8")
    # comments out, so a comment that says "* MICROSTEPS" does not count
    code = re.sub(r"//[^\n]*", "", src)

    move = body(code, "void MechanicsEsp32::move(")
    ok(move is not None, "MechanicsEsp32::move() is there to read")
    if move is not None:
        calls = re.findall(r"m_stepper->move\(([^;]*)\);", move)
        ok(len(calls) == 1 and "MICROSTEPS" not in calls[0] and "*" not in calls[0],
           "move() passes the microsteps to the stepper as they are, not multiplied",
           str(calls))

    speed = body(code, "void MechanicsEsp32::speed(")
    ok(speed is not None and speed.count("* MICROSTEPS") == 2,
       "speed() turns FULL steps/s and steps/s^2 into pulses (x MICROSTEPS)",
       str(speed))

    ok("const uint16_t MICROSTEPS" not in code,
       "the ESP32 mechanics has no microstepping of its own: it is mechanics.h's")

    header = (FIRMWARE / "wheel.h").read_text(encoding="utf-8")
    shared = (FIRMWARE / "wheelly_protocol.h").read_text(encoding="utf-8")
    mech = (FIRMWARE / "mechanics.h").read_text(encoding="utf-8")
    micro = int(re.search(r"const uint16_t MICROSTEPS = (\d+);", mech).group(1))

    def floats(text):
        """The header's `const float NAME = <expr>;`, evaluated in order."""
        out = {}
        for name, expr in re.findall(r"const float (\w+) = ([^;]+);", text):
            out[name] = eval(re.sub(r"(\d)f\b", r"\1", expr), {}, dict(out))
        return out

    f = floats(shared)
    ratio = f["FACTORY_DRIVE_RATIO"]
    # the ratio is a setting, and steps_per_degree(ratio)
    # the arithmetic: read and evaluated at the factory ratio
    spd_expr = re.search(r"inline float steps_per_degree\(float ratio\)\s*\{\s*return ([^;]+);",
                         header).group(1)
    spd = eval(re.sub(r"(\d)f\b", r"\1", spd_expr).replace("MICROSTEPS", str(micro)),
               {}, {"ratio": ratio})
    physics = 200 * 16 / 360.0 * (145.0 / 50.0)
    ok(abs(spd - physics) < 1e-3,
       "steps_per_degree() at the factory ratio is the microsteps of motor per degree of disc",
       f"{spd:.4f} against {physics:.4f} from the wheel's own numbers")

    # THE FACTORY RATIO IS THE MODEL'S: the two diameters it is
    # derived from, in the shared header, must be the CAD's own - read from
    # the parameters the solids are built from (parameters.py and the local
    # overrides), so a clutch redrawn in the CAD cannot leave the firmware
    # estimating with the old one. Pure Python: the system python runs it.
    cad = HERE.parent.parent / "mechanics" / "wheelly-cad" / "src"
    sys.path.insert(0, str(cad))
    try:
        import parameters  # noqa: E402
        disc, clutch = parameters.D["Disc_rotating"], parameters.D["D_clutch"]
    except Exception as e:           # noqa: BLE001 - said, not hidden
        disc = clutch = None
        ok(False, "the CAD's parameters can be read", repr(e))
    finally:
        sys.path.remove(str(cad))
    if disc is not None:
        ok(abs(f["MODEL_DISC_DIAMETER_MM"] - disc) < 1e-6
           and abs(f["MODEL_CLUTCH_DIAMETER_MM"] - clutch) < 1e-6,
           "the factory ratio's diameters are the CAD's (Disc_rotating, D_clutch)",
           f"header {f['MODEL_DISC_DIAMETER_MM']}/{f['MODEL_CLUTCH_DIAMETER_MM']}, "
           f"CAD {disc}/{clutch}")
        ok(abs(ratio - disc / clutch) < 1e-6,
           "FACTORY_DRIVE_RATIO is the disc over the clutch, as the CAD's Ratio_reduction",
           f"{ratio} against {disc / clutch}")

    print(f"\n{'all passed' if not failed else f'{len(failed)} failed'}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
