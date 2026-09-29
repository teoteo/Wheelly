#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""The driver folder stands on its own.

Why this exists. The INDI driver is meant for inclusion in INDI itself,
where driver/indi-wheelly/ is copied into INDI's source tree and nothing
else of this repository comes along. A driver that included the protocol
header as ../../firmware/wheelly/wheelly_protocol.h, which there would not
exist, would not build there.

The driver now has its own copy of the header. Two copies of the one file
whose whole purpose is that firmware and driver agree is exactly the drift the
header was invented to prevent, so the copy is checked here, BYTE FOR BYTE.

Why a checked copy and not a copy made by the build: the build that matters in
the end is INDI's, which knows nothing of firmware/, so the file has to be in
the folder, committed, as it is; a generator would only move the question to
"was it run?". A byte comparison has no opinion to get wrong: whitespace, a
comment, a constant - any difference fails. The firmware's copy is the source
of truth; the fix is always

    cp firmware/wheelly/wheelly_protocol.h driver/indi-wheelly/

Checks:
  - the two copies of wheelly_protocol.h are identical;
  - no source of the driver includes anything through "../", i.e. from
    outside its folder (the old include would fail here);
  - the driver is English only, with the texts written where they are
    used, as every INDI driver's: INDI's maintainers asked for the
    translation layer (tr("msg.key") and its catalogues) to be removed, so
    no tr(/trf( call, no translations.h and no key-shaped string
    ("msg.x", "prop.x", ...) may come back;
  - every C++ file of the driver is already in INDI's style: astyle with the
    options of INDI's README leaves it unchanged. INDI's own check
    (scripts/check-codestyle.sh) only looks at the lines a pull request
    changes, and on macOS's bash 3.2 its regex fails and it passes everything
    without looking; checking the whole file here, on every run, is what
    keeps the copy proposed to INDI clean. Skipped, and said so, when astyle
    is not installed (brew install astyle).

    python3 test_driver_standalone.py
"""

import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "firmware" / "wheelly" / "wheelly_protocol.h"
DRIVER = ROOT / "driver" / "indi-wheelly"
COPY = DRIVER / "wheelly_protocol.h"

# INDI's README, "Code Style", and its scripts/check-codestyle.sh
ASTYLE_OPTIONS = [
    "--style=allman", "--align-reference=name", "--indent-switches",
    "--indent-modifiers", "--indent-classes", "--pad-oper",
    "--indent-col1-comments", "--lineend=linux", "--max-code-length=124",
]

failed = []


def ok(condition, what, detail=""):
    print(("  ok      " if condition else "  FAILED: ") + what +
          ("" if condition else f" -> {detail}"))
    if not condition:
        failed.append(what)


def first_difference(a: bytes, b: bytes) -> str:
    """Where the two copies part, as a line number and the two lines: enough to
    see at a glance which side was edited."""
    la, lb = a.split(b"\n"), b.split(b"\n")
    for i, (x, y) in enumerate(zip(la, lb), start=1):
        if x != y:
            return (f"line {i}: firmware {x.decode(errors='replace')!r} / "
                    f"driver {y.decode(errors='replace')!r}")
    return f"one is longer: firmware {len(la)} lines, driver {len(lb)} lines"


def translation_traces(path):
    """Lines of a driver source that bring the translation layer back."""
    found = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        code = line.split("//")[0]
        if (re.search(r"\btrf?\(", code) or "translations.h" in code or
                re.search(r'"(msg|prop|nome|err|num)\.[a-z0-9.\-]+"', code)):
            found.append(f"{path.name}:{n}")
    return found


def main():
    print("\nThe driver folder stands on its own")
    print("===================================\n")

    ok(COPY.is_file(), "the driver has its own wheelly_protocol.h", str(COPY))
    if COPY.is_file():
        a, b = SOURCE.read_bytes(), COPY.read_bytes()
        ok(a == b, "driver/indi-wheelly/wheelly_protocol.h is byte for byte "
                   "firmware/wheelly/wheelly_protocol.h",
           first_difference(a, b) +
           " - copy the firmware's over the driver's")

    outside = []
    for path in sorted(DRIVER.rglob("*")):
        if path.suffix not in {".cpp", ".h", ".cmake"} or "build" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r'\s*#\s*include\s*[<"][^>"]*\.\./', line):
                outside.append(f"{path.relative_to(ROOT)}:{n}")
    ok(not outside, "no driver source includes from outside its folder",
       ", ".join(outside))

    traces = []
    for path in sorted(DRIVER.glob("*.cpp")) + sorted(DRIVER.glob("*.h")):
        traces += translation_traces(path)
    ok(not list(DRIVER.glob("translations*")), "no translation catalogue in the driver folder",
       ", ".join(p.name for p in DRIVER.glob("translations*")))
    ok(not traces, "no translation call or key in the driver sources", ", ".join(traces[:8]))

    astyle = shutil.which("astyle")
    if astyle is None:
        print("  skipped: INDI code style (astyle not installed)")
    else:
        unstyled = []
        for path in sorted(DRIVER.glob("*.cpp")) + sorted(DRIVER.glob("*.h")):
            text = path.read_bytes()
            styled = subprocess.run([astyle, *ASTYLE_OPTIONS], input=text,
                                    capture_output=True, check=True).stdout
            if styled != text:
                unstyled.append(path.name)
        ok(not unstyled, "every driver source is in INDI's code style (astyle)",
           ", ".join(unstyled) + " - run astyle with INDI's options on it")

    print()
    if failed:
        print(f"{len(failed)} FAILED")
        sys.exit(1)
    print("all passed")


if __name__ == "__main__":
    main()
