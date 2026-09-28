# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""Reads the protocol constants straight from wheelly_protocol.h.

The whole point of the exercise is that commands, fields and events are
defined ONCE. The firmware and the INDI driver manage it by including the same
header; the simulator, being Python, would have to copy them by hand - and then
there would be two lists that can drift apart in silence, which is exactly the
trouble the shared header was meant to remove.

So here the header is really read, and the constants are extracted from it.
If someone renames a command in the header and does not update the simulator,
the simulator does not start: `check_complete()` fails at start-up with the
list of what is missing. Ten seconds of annoyance instead of an evening spent
wondering why the driver does not answer.
"""

import pathlib
import re

HEADER = pathlib.Path(__file__).resolve().parent.parent / "wheelly" / "wheelly_protocol.h"

# `const char NAME[] = "value";`
_STRING = re.compile(r'^\s*const\s+char\s+(\w+)\s*\[\]\s*=\s*"([^"]*)"\s*;', re.M)
# `const char NAME = 'c';`
_CHAR = re.compile(r"^\s*const\s+char\s+(\w+)\s*=\s*'(.)'\s*;", re.M)
# `const int NAME = 12;` or `const size_t NAME = 12;`
# (and the unsigned ones: the limits of the motor settings;
# uint16_t for the recommended holding current, that the drift advice quotes)
_NUMBER = re.compile(r"^\s*const\s+(?:int|size_t|uint16_t|unsigned(?:\s+long)?)\s+(\w+)\s*=\s*(\d+)\s*;", re.M)
# `const float NAME = 0.5f;` - the factory tolerances
_FLOAT = re.compile(r"^\s*const\s+(?:float|double)\s+(\w+)\s*=\s*(\d+\.\d*)f?\s*;", re.M)
# `const float NAME = OTHER / ANOTHER;` - a value DERIVED in the header from
# others (the factory drive ratio, from the model's diameters).
# Evaluated here from the names already read, so the formula is written once.
_FLOAT_EXPR = re.compile(r"^\s*const\s+float\s+(\w+)\s*=\s*([A-Za-z_][^;]*)\s*;", re.M)
# `const bool NAME = true;` - none in the header since the detent flag went
#; the reader stays, it costs one line
_BOOL = re.compile(r"^\s*const\s+bool\s+(\w+)\s*=\s*(true|false)\s*;", re.M)
# enum entries: `NAME = 3,` or `NAME = 3`
_ENUM = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(\d+)\s*,?\s*(?://.*)?$", re.M)


def _read():
    text = HEADER.read_text(encoding="utf-8")
    values = {}
    for name, value in _STRING.findall(text):
        values[name] = value
    for name, value in _CHAR.findall(text):
        values[name] = value
    for name, value in _NUMBER.findall(text):
        values[name] = int(value)
    for name, value in _FLOAT.findall(text):
        values[name] = float(value)
    for name, expr in _FLOAT_EXPR.findall(text):
        # only names already read, numbers and arithmetic: nothing else runs
        if not re.fullmatch(r"[\w\s.+\-*/()]+", expr):
            continue
        values[name] = float(eval(re.sub(r"(\d)f\b", r"\1", expr),
                                  {"__builtins__": {}}, dict(values)))
    for name, value in _BOOL.findall(text):
        values[name] = value == "true"
    for name, value in _ENUM.findall(text):
        values.setdefault(name, int(value))
    return values


# Everything the simulator expects to find. The list is written by hand on
# purpose: it is the contract between this file and the header, and if the
# header changes somebody should notice.
# (The names are the header's own, Italian ones included: they are shared
# identifiers and are renamed there, not here.)
EXPECTED = [
    "PROTOCOL_VERSION", "MAX_SLOTS", "MIN_SLOTS", "FACTORY_SLOTS", "FILTER_NAME_MAX",
    "WHEELLY_LINE_MAX",
    "PREFIX_OK", "PREFIX_ERROR", "PREFIX_COMMENT", "PREFIX_EVENT",
    "CMD_VERSION", "CMD_STATUS", "CMD_GO", "CMD_STOP", "CMD_JOG", "JOG_MAX_DEG", "CMD_ANGLES",
    "CMD_ANGLE", "ANGLE_MAX_DEG", "CMD_NAMES", "CMD_NAME", "CMD_TEACH",
    "CMD_SAVE", "CMD_TOLERANCE", "CMD_MOTOR", "CMD_HOLD",
    "CMD_LED", "CMD_DIAG", "CMD_SLOTS", "RECOMMENDED_HOLD_MA",
    "CMD_DIRECTION", "ARG_SHORTEST", "ARG_UP", "ARG_DOWN", "FACTORY_DIRECTION",
    "F_DIRECTION", "F_CEILING", "EKOS_FILTER_TIMEOUT_MS",
    "MOTOR_MA_MAX", "MOTOR_SPEED_MAX", "MOTOR_ACCEL_MAX", "FACTORY_SPEED", "FACTORY_ACCEL", "FACTORY_RUN_MA", "BOOST_SPEED_MAX",
    "TOLERANCE_MAX_DEG", "RETRIES_MAX", "FACTORY_GOOD_DEG", "FACTORY_WARN_DEG",
    "MODEL_DISC_DIAMETER_MM", "MODEL_CLUTCH_DIAMETER_MM", "FACTORY_DRIVE_RATIO",
    "CMD_RATIO", "ARG_LEARN", "DRIVE_RATIO_MIN", "DRIVE_RATIO_MAX", "CMD_LEGS", "F_REPORT",
    "CMD_SETTLE", "FACTORY_SETTLE_MS", "SETTLE_MS_MAX", "F_MS",
    "F_RATIO", "F_BASE", "F_FACTORY", "F_LEARN", "F_LEARNT",
    "F_N", "F_KIND", "KIND_FIRST", "KIND_APPROACH", "KIND_RETRY", "F_JOG", "F_STEPS",
    "F_MOTOR", "F_AIM", "F_TO", "F_MOVED", "F_LONG", "EV_LEG",
    "ARG_ON", "ARG_OFF", "ARG_TEST", "ARG_PULSE", "F_MODE",
    "F_POS", "F_ANGLE", "F_TARGET", "F_ERR", "F_MOTION", "F_RETRIES", "F_LEGS", "F_BOOSTS",
    "F_FROM", "F_DIR", "F_AGC", "F_MAG", "F_MD", "F_ML", "F_MH",
    "F_NAME", "F_FW", "F_PROTO", "F_SERIAL", "F_SLOTS", "F_GOOD", "F_WARN", "F_MA",
    "F_SPEED", "F_ACCEL", "F_STATE", "F_ENABLED", "F_SAVED",
    "F_DURATION", "F_EXPECTED", "F_GOT", "F_REASON", "F_OUTCOME",
    "OUTCOME_NONE",
    "V_YES", "V_NO",
    "MOTION_IDLE", "MOTION_MOVING", "MOTION_SETTLING", "MOTION_FAILED",
    "EV_ARRIVED", "EV_WARNING", "EV_FAILED", "EV_SENSOR",
    "ERR_UNKNOWN_COMMAND", "ERR_BAD_ARGUMENTS", "ERR_OUT_OF_RANGE",
    "ERR_SENSOR_SILENT", "ERR_NO_MAGNET", "ERR_DRIVER_SILENT", "ERR_NOT_NOW",
    "ERR_NVS_WRITE", "ERR_BAD_FILTER_NAME",
    "NAME_OK", "NAME_EMPTY", "NAME_TOO_LONG", "NAME_BAD_EDGE",
    "NAME_BAD_CHAR", "NAME_RESERVED",
]


def check_complete(values):
    missing = [n for n in EXPECTED if n not in values]
    if missing:
        raise RuntimeError(
            "wheelly_protocol.h does not contain: " + ", ".join(missing) +
            "\nSomebody renamed or removed something in the header without "
            "updating the simulator."
        )
    return values


_VALUES = check_complete(_read())
globals().update(_VALUES)

# names of the refusal reasons, for the reason= field of the error lines
REASON_NAME = {
    _VALUES["NAME_EMPTY"]: "empty",
    _VALUES["NAME_TOO_LONG"]: "too-long",
    _VALUES["NAME_BAD_EDGE"]: "bad-edge",
    _VALUES["NAME_BAD_CHAR"]: "bad-char",
    _VALUES["NAME_RESERVED"]: "reserved",
}


# --------------------------------------------------------------------------
# The filter-name rule, translated from the header.
#
# Here the duplication exists, and on purpose: Python cannot include a C++
# header. So the test puts it against the real implementation, running both on
# hundreds of inputs and demanding the same verdict. If they diverge, the test
# fails.

_RESERVED = {"CON", "PRN", "AUX", "NUL"}
_RESERVED |= {f"COM{i}" for i in range(1, 10)}
_RESERVED |= {f"LPT{i}" for i in range(1, 10)}


def _alnum(c):
    return ("A" <= c <= "Z") or ("a" <= c <= "z") or ("0" <= c <= "9")


def _allowed(c):
    return _alnum(c) or c in "_-."


def _reserved(s):
    stem = s.split(".", 1)[0]
    return len(stem) <= 15 and stem.upper() in _RESERVED


def check_name(s):
    """Returns NAME_OK or the reason for the refusal."""
    if not s:
        return _VALUES["NAME_EMPTY"]
    if len(s) > _VALUES["FILTER_NAME_MAX"]:
        return _VALUES["NAME_TOO_LONG"]
    for c in s:
        if not _allowed(c):
            return _VALUES["NAME_BAD_CHAR"]
    if not _alnum(s[0]) or not _alnum(s[-1]):
        return _VALUES["NAME_BAD_EDGE"]
    if _reserved(s):
        return _VALUES["NAME_RESERVED"]
    return _VALUES["NAME_OK"]
