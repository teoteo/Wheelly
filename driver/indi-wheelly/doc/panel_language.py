# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""The panel guide in more than one language (every guide has a language
toggle, English by default; for now English and Italian).

The same scheme as the assembly guide's (mechanics/wheelly-cad/src/guide/
language.py): panel_texts.py is written in English and stays the source; every
other language is a catalogue, panel_texts_<lang>.py, keyed by WHERE the text
is - "FILTER_SLOT/notes/2" - and each entry remembers a fingerprint of the
English it was translated from. problems() says what is wrong, and the build
fails on it: a text with no translation, a translation whose English has
changed since, one whose {placeholders} differ, one for a text that is gone.

    python3 panel_language.py it      prints the missing and stale entries, as
                                    Python ready to fill in and paste
"""
import copy
import hashlib
import importlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LANGUAGES = ("en", "it")          # the first is the source, and the default
PLACEHOLDER = re.compile(r"\{[a-zA-Z_0-9]+\}")


def fingerprint(text):
    """Eight hex digits of the English text: enough to see it has changed."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def source():
    sys.path.insert(0, HERE)
    import panel_texts
    return importlib.reload(panel_texts)


def entries(T=None):
    """(key, English text) for every translatable text of the guide."""
    T = T or source()
    for n, t in T.TEXTS.items():
        if t.get("what"):
            yield "%s/what" % n, t["what"]
        for e, x in t.get("elements", {}).items():
            yield "%s/elements/%s" % (n, e), x
        if t.get("variable_elements"):
            yield "%s/variable_elements" % n, t["variable_elements"]
        if t.get("table"):
            for k, h in enumerate(t["table"]["header"], 1):
                yield "%s/table/header/%d" % (n, k), h
            for i, r in enumerate(t["table"]["rows"], 1):
                for j, c in enumerate(r, 1):
                    yield "%s/table/%d/%d" % (n, i, j), c
        for k, x in enumerate(t.get("notes", []), 1):
            yield "%s/notes/%d" % (n, k), x
        if t.get("figure"):
            yield "%s/figure/caption" % n, t["figure"]["caption"]
    for g, x in T.TABS.items():
        yield "tabs/%s" % g, x


def catalogue(language):
    sys.path.insert(0, HERE)
    mod = importlib.import_module("panel_texts_%s" % language)
    return importlib.reload(mod).CATALOGUE


def problems(language="it"):
    try:
        cat = catalogue(language)
    except ModuleNotFoundError:
        return ["panel_texts_%s.py does not exist: no text is translated" % language]
    out, seen = [], set()
    for key, en in entries():
        seen.add(key)
        if key not in cat:
            out.append("%s: %s has no translation" % (language, key))
            continue
        h, t = cat[key]
        if h != fingerprint(en):
            out.append("%s: %s is out of date - the English has changed since it was "
                       "translated" % (language, key))
        if sorted(PLACEHOLDER.findall(t)) != sorted(PLACEHOLDER.findall(en)):
            out.append("%s: %s has placeholders %s, the English %s"
                       % (language, key, sorted(PLACEHOLDER.findall(t)),
                          sorted(PLACEHOLDER.findall(en))))
        if "TODO" in t:
            out.append("%s: %s has a TODO left in it" % (language, key))
    for key in sorted(set(cat) - seen):
        out.append("%s: %s is translated but the guide no longer has it" % (language, key))
    return out


def translated(language):
    """(TEXTS, TABS) in that language: the source itself for English. A text
    without a valid translation stops here - problems() has already said
    which, and a page half in one language must not come out."""
    T = source()
    if language == LANGUAGES[0]:
        return T.TEXTS, T.TABS
    cat = catalogue(language)

    def t(key, en):
        if key not in cat or cat[key][0] != fingerprint(en):
            raise SystemExit("panel guide, %s: %s is missing or out of date" % (language, key))
        return cat[key][1]

    texts = copy.deepcopy(T.TEXTS)
    for n, x in texts.items():
        if x.get("what"):
            x["what"] = t("%s/what" % n, x["what"])
        x["elements"] = {e: t("%s/elements/%s" % (n, e), v) for e, v in x.get("elements", {}).items()}
        if x.get("variable_elements"):
            x["variable_elements"] = t("%s/variable_elements" % n, x["variable_elements"])
        if x.get("table"):
            x["table"]["header"] = [t("%s/table/header/%d" % (n, k), h)
                                    for k, h in enumerate(x["table"]["header"], 1)]
            x["table"]["rows"] = [[t("%s/table/%d/%d" % (n, i, j), c) for j, c in enumerate(r, 1)]
                                  for i, r in enumerate(x["table"]["rows"], 1)]
        x["notes"] = [t("%s/notes/%d" % (n, k), v) for k, v in enumerate(x.get("notes", []), 1)]
        if x.get("figure"):
            x["figure"]["caption"] = t("%s/figure/caption" % n, x["figure"]["caption"])
    tabs = {g: t("tabs/%s" % g, x) for g, x in T.TABS.items()}
    return texts, tabs


def to_translate(language):
    """The entries to write: missing or out of date, as Python lines."""
    try:
        cat = catalogue(language)
    except ModuleNotFoundError:
        cat = {}
    return ["    %r: (%r,\n        %r)," % (k, fingerprint(en), en)
            for k, en in entries() if not (k in cat and cat[k][0] == fingerprint(en))]


if __name__ == "__main__":
    print("\n".join(to_translate(sys.argv[1] if len(sys.argv) > 1 else "it")))
