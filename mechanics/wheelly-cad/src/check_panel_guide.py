# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The guide to the INDI panel (docs/driver) follows the driver.

The guide must update itself when a command is added or removed, and a build check must fail when a property has no entry or the
guide describes one that is gone. The rules are panel_guide.problems(), in
driver/indi-wheelly/doc, next to what they check: the captured panel, its
texts, and the properties wheelly.cpp declares. Seconds, and no solid read:
outside the audit, so it can be broken on purpose in seconds.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "..", "..", "..", "driver", "indi-wheelly", "doc")
sys.path.insert(0, os.path.abspath(DOC))
import panel_guide  # noqa: E402

problems = panel_guide.problems()
print("--- OK (%d) ---" % (0 if problems else 1))
if not problems:
    print("   the panel guide covers every property of the driver, and nothing else")
print("--- TO FIX (%d) ---" % len(problems))
for p in problems:
    print("  ! panel guide: " + p)
