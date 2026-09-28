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
  - the Italian catalogue, translations_it.cpp, has exactly the keys of the
    English one, translations.cpp. They used to be one table with three
    columns; the Italian is a file of its own so that INDI's English-only build can leave it out (CMake WHEELLY_ITALIAN); what the
    table's shape guaranteed - every key translated, no translation of a key
    that no longer exists - is now checked here. The keys are read from the
    two arrays' text, which is plain enough: one `{"key",` per entry.

    python3 test_driver_standalone.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "firmware" / "wheelly" / "wheelly_protocol.h"
DRIVER = ROOT / "driver" / "indi-wheelly"
COPY = DRIVER / "wheelly_protocol.h"

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


def catalogue_keys(path, array):
    """The keys of one catalogue array, in order."""
    text = path.read_text(encoding="utf-8")
    # "ARRAY[] = {" on one line or, in INDI's style, the brace on the next
    m = re.search(r"\b" + array + r"\[\]\s*=\s*\{", text)
    if m is None:
        return []
    start = m.end()
    body = text[start:text.index("\n};", start)]
    # an entry may open on one line and carry its key on the next (INDI's
    # astyle breaks long entries that way): the key is the first string after
    # the brace, whitespace and newlines between them allowed
    return re.findall(r'\{\s*"([^"]+)"\s*,', body)


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

    en = catalogue_keys(DRIVER / "translations.cpp", "CATALOGUE")
    it = catalogue_keys(DRIVER / "translations_it.cpp", "ITALIAN_CATALOGUE")
    ok(len(en) > 100, "the English catalogue is read", f"{len(en)} keys")
    ok(len(set(en)) == len(en), "no key twice in the English catalogue",
       sorted({k for k in en if en.count(k) > 1}))
    ok(len(set(it)) == len(it), "no key twice in the Italian catalogue",
       sorted({k for k in it if it.count(k) > 1}))
    ok(not set(en) - set(it), "every English key has its Italian text",
       sorted(set(en) - set(it)))
    ok(not set(it) - set(en), "no Italian text for a key English does not have",
       sorted(set(it) - set(en)))

    print()
    if failed:
        print(f"{len(failed)} FAILED")
        sys.exit(1)
    print("all passed")


if __name__ == "__main__":
    main()
