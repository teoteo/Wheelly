# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The makers' models of the bought parts, which the project does not ship.

WHY THEY ARE NOT IN THE REPOSITORY: they are the
makers' files, downloaded from their sites, and none of them carries a licence
that allows redistributing it. The project is CERN-OHL-P / MIT and cannot
relicense them, so whoever regenerates the CAD downloads them (where from, in
mechanics/others/README.md) and saves them under the exact names below.

WHY THE BUILD STOPS instead of skipping: the motor's model is not decoration.
solids_box_collar.py and the assembly drawing take the hatch under the motor
and the motor's arc from it (outline_motor.py), so without it neither the box
nor the 2D assembly view can be generated, and
the electronics envelopes checked against the box come from the other two.
A build that went on without them would write a box that differs from the
published one, silently. Printing does not need any of this: the printable
files are attached to each release.

    python3 src/vendor_files.py     lists what is there and what is missing
"""
import os
import sys

OTHERS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "others")

# file name as the build opens it: (the part, what uses it)
REQUIRED = {
    "14HS10-0404S.STEP": ("StepperOnline 14HS10-0404S NEMA14 motor",
                          "the box (hatch and arc under the motor), the assembly, "
                          "the interpenetration checks"),
    "XIAO-ESP32S3 v2.step": ("Seeed Studio XIAO ESP32S3",
                             "the electronics envelopes and the USB slot checks"),
    "TMC2209.step": ("TMC2208/TMC2209 stepstick driver module",
                     "the electronics envelopes and the driver's pin rows"),
    "GX12-2P.step": ("GX12 2-pin aviation socket (the 12 V inlet)",
                     "the electronics envelopes in the box head"),
}


def missing():
    """The required files not found in mechanics/others/, in a stable order."""
    return [f for f in sorted(REQUIRED) if not os.path.isfile(os.path.join(OTHERS, f))]


def explain(names):
    """The message the build prints when files are missing."""
    lines = ["The makers' models of these bought parts are missing from %s:" % OTHERS]
    for f in names:
        part, used = REQUIRED[f]
        lines.append("  - %-24s %s (used by: %s)" % (f, part, used))
    lines += ["They are not redistributed with Wheelly: download them as described in",
              "mechanics/others/README.md and save them under exactly these names.",
              "Nothing can be generated without them - not even the printed parts or",
              "the 2D drawings, because the box takes its shape from the motor's model.",
              "To PRINT Wheelly you do not need them: take the STEP/STL files attached",
              "to the release."]
    return "\n".join(lines)


if __name__ == "__main__":
    gone = missing()
    for f in sorted(REQUIRED):
        print("%-8s %s" % ("MISSING" if f in gone else "ok", f))
    if gone:
        print()
        print(explain(gone))
    sys.exit(1 if gone else 0)
