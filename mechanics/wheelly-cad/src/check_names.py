# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The parameter names are built from the glossary, and from nothing else.

Why this exists. The migration to English renamed 378 parameters in a single
run of `rename_en.py`; from that day on, every new name is written by hand.
A hand-written name is where the language creeps back in - `Sp_scatola` lands
next to `Th_box` - and where a synonym is invented for something that already
has a word: `boss` here, `hub` there. Neither moves the geometry by a
micrometre, so no measurement in the build has an opinion about it, and
`check_unchanged.py` least of all: its whole point is to ignore the names.

Two things are checked, and the second one is here because it failed silently
once already:

1. the PREFIX is one the project uses, and every word after it is a word the
   glossary knows on its English side. A word it does not know is either
   Italian left behind or a new synonym - both worth a sentence of thought;

2. every name `SPECIAL` promises actually EXISTS. `SPECIAL` is the short list
   of names a word-by-word translation gets wrong, and once twelve of
   its thirteen entries turned out never to have been applied: the rename
   script had rewritten its own glossary, so by the time it ran for real the
   left-hand column was already English and matched nothing. The model was
   left with `Trq_seal_mnm` for the holding torque of the detent - `tenuta`
   read as a gasket - and with `Force_spring_n`, where the unit of a force
   reads as a word. Nothing complained, because a wrong name builds.

Fixing an alarm from (1) means one of two things: translate the name, or - when
the word is genuinely new - add it to `WORDS` in `rename_en.py` TOGETHER WITH
its Italian, so the glossary stays the record of a choice and not just a
filter. An alarm from (2) means either applying that rename or, if the
parameter is gone for good, moving its line to `RETIRED`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # rename_en.py lives above src/

from parameters import D
import rename_en

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


# --- 1) every name is spelled out of the glossary ------------------------
# The vocabulary is the ENGLISH side: the values of the prefix table for the
# head, the values of WORDS for everything after it. Deliberately not the keys:
# a name is wrong precisely when it uses a word the glossary has not been asked
# about, and the keys would let every Italian word through.
PREFIXES = set(rename_en.PREFIXES.values())
VOCAB = set(w.lower() for w in rename_en.WORDS.values())
# a name SPECIAL decides as a whole does not have to be spellable word by word:
# that is what makes it special
WHOLE = set(rename_en.SPECIAL.values())

bad_prefix, bad_word = [], []
for name in sorted(D):
    if name in WHOLE:
        continue
    bits = name.split("_")
    if len(bits) == 1:
        # a name with no prefix at all: `rename_en.to_english` leaves those
        # alone, which is how `Interasse` survived the first run untouched and
        # unnoticed - a name left as it was looks exactly like a translated one
        bad_prefix.append("%s (no prefix)" % name)
        continue
    if bits[0] not in PREFIXES:
        bad_prefix.append("%s (prefix %s)" % (name, bits[0]))
    for w in bits[1:]:
        if w.lower() not in VOCAB:
            bad_word.append("%s (%s)" % (name, w))

T("every parameter prefix is one the project uses",
  not bad_prefix, "; ".join(bad_prefix))
T("every word in a parameter name is in the glossary",
  not bad_word, "; ".join(sorted(set(bad_word))))

# --- 2) the special cases were actually applied ---------------------------
# Cheap, and the only thing that can tell a rule that was applied from one that
# was written down and then missed. Both look identical in the file.
missing = [("%s -> %s" % (it, en)) for it, en in sorted(rename_en.SPECIAL.items())
           if en not in D]
T("every name SPECIAL promises exists", not missing, "; ".join(missing))

# The retired ones are the other half of the same accounting: they are kept so
# the choice stays on the record, and checked so that the list cannot quietly
# fill up with names that are simply back.
back = [("%s -> %s" % (it, en)) for it, en in sorted(rename_en.RETIRED.items())
        if en in D or it in D]
T("no RETIRED name has come back", not back, "; ".join(back))

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
