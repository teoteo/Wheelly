# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The two catalogues of the parameters editor, and the language to use.

The editor page, the names of the dimension chains it lists and the callouts
of the assembly plan it shows all go through keys, because a screenshot of
the editor appears in the assembly guide, which is in English. The language is WHEELLY_LINGUA, English by default - the same
switch the wiring drawings use.
"""
import os
import texts_editor_en as _en, texts_editor_it as _it

LANGUAGES = ("en", "it")
CATALOGUES = {"en": _en.TEXTS, "it": _it.TEXTS}


def check(catalogues=CATALOGUES):
    """The two catalogues must hold the same keys: a key in one only is a text
    that shows up as its key in the other language."""
    only = sorted(set(catalogues["en"]) ^ set(catalogues["it"]))
    if only:
        raise SystemExit("the two catalogues of the editor do not hold the same keys: %s"
                         % ", ".join(only))


check()


def language():
    l = os.environ.get("WHEELLY_LINGUA", "en")
    return l if l in LANGUAGES else "en"


def tr(key, language_=None, **fields):
    t = CATALOGUES[language_ or language()][key]
    return t.format(**fields) if fields else t


# --------------------------------------------------------------------------
# The parameters: their description and their "drawings" label
# --------------------------------------------------------------------------
# parameters.py holds them in English, and that is the source every tool reads
# (the Fusion CSV, the links from a parameter to its drawings). The Italian is
# a translation kept aside in texts_parameters_it.py, keyed by parameter name,
# the same way the page texts are, so the editor running in English shows no
# Italian. A parameter the Italian catalogue
# does not know - every new one, since they are written in English only -
# shows its English text instead of a key or a blank.
#
# A name that appears twice in P (it happens: Cl_head_screw_clutch) is keyed
# "name#2" for its second row, so each row keeps its own translation.
PARAMETER_FIELDS = ("group", "description")
_PARAMETERS = {}


def parameter_texts(language_):
    """The catalogue of the parameters for a language ({} for English)."""
    if language_ not in _PARAMETERS:
        if language_ == "it":
            import texts_parameters_it
            _PARAMETERS[language_] = texts_parameters_it.TEXTS
        else:
            _PARAMETERS[language_] = {}
    return _PARAMETERS[language_]


def parameter_text(key, field, english, language_=None):
    """The description or the drawings label of a parameter, in the language
    of the editor; `english` is what parameters.py says, and is the fallback."""
    entry = parameter_texts(language_ or language()).get(key) or {}
    return entry.get(field) or english


def check_parameters(keys, language_="it"):
    """Keys of the parameters catalogue that match no row of parameters.py,
    or carry a field the editor does not read. A parameter renamed or removed
    leaves its translation behind and the Italian silently stops showing, so
    this is checked (check_editor.py) instead of trusted. `keys` are the
    keys the rows answer to (name, or name#2 for a repeated name)."""
    keys = set(keys)
    return sorted(k for k, v in parameter_texts(language_).items()
                  if k not in keys or set(v) - set(PARAMETER_FIELDS))
