# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The Italian catalogue of the assembly guide: every chapter's module in
guide/it/, gathered. See guide/language.py for what the keys and fingerprints are."""
import importlib
import pkgutil

from . import it as _package

CATALOGUE = {}
for _m in pkgutil.iter_modules(_package.__path__):
    CATALOGUE.update(importlib.import_module("guide.it." + _m.name).CATALOGUE)
