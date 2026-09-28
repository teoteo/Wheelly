# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The assembly guide in more than one language: every guide with a
language toggle, English by default, for now English and Italian.

The English is written in chapters.py and stays the source. Every other
language is a catalogue, chapters_<lang>.py, keyed by WHERE the text is -
"heat-set-inserts/3/point2" - and each entry remembers a fingerprint of the
English it was translated from. problems() says what is wrong, and the build
fails on it:

  - a text with no translation;
  - a translation whose English has changed since (it is out of date, and
    would otherwise go on saying the old thing, unseen);
  - a translation whose {placeholders} are not the English ones (a number
    from the model would go missing, or a wrong one appear);
  - a translation for a text that no longer exists.

    python3 -m guide.language it      prints the missing and stale entries, as
                                    Python ready to fill in and paste
"""
import copy
import hashlib
import importlib
import re

from . import chapters

LANGUAGES = ("en", "it")          # the first is the source, and the default
PLACEHOLDER = re.compile(r"\{[a-zA-Z_0-9]+\}")


def fingerprint(text):
    """Eight hex digits of the English text: enough to see it has changed."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def texts(cap):
    """(key, English text) for every translatable text of a chapter."""
    c = cap["id"]
    yield "%s/title" % c, cap["title"]
    yield "%s/intro" % c, cap["intro"]
    if cap.get("skip"):
        yield "%s/skip" % c, cap["skip"]
    for k, a in enumerate(cap.get("tools", []), 1):
        yield "%s/tool%d" % (c, k), a
    for i, p in enumerate(cap["steps"], 1):
        yield "%s/%d/title" % (c, i), p["title"]
        for k, t in enumerate(p.get("points", []), 1):
            yield "%s/%d/point%d" % (c, i, k), t


def plan_texts():
    """(key, English text) for the plan of the chapters, which the index and
    the side contents show: the one-line note of every chapter, and the title
    of a chapter not written yet (a written one has its title in its own
    chapter, and the plan's must be the same - plan() takes it from there)."""
    written = {c["num"] for c in chapters.CHAPTERS}
    for num, title, note in chapters.PLAN:
        if num not in written:
            yield "plan/%d/title" % num, title
        if note:
            yield "plan/%d/note" % num, note


def all_texts():
    for cap in chapters.CHAPTERS:
        yield from texts(cap)
    yield from plan_texts()


def plan(language):
    """chapters.PLAN in that language: (num, title, note)."""
    if language == LANGUAGES[0]:
        return list(chapters.PLAN)
    cat = catalogue(language)
    written = {c["num"]: c for c in chapters.CHAPTERS}

    def t(key, en):
        h, text = cat[key]
        if h != fingerprint(en):
            raise SystemExit("guide, %s: %s is out of date" % (language, key))
        return text
    out = []
    for num, title, note in chapters.PLAN:
        if num in written:
            tit = translated(written[num], language)["title"]
        else:
            tit = t("plan/%d/title" % num, title)
        out.append((num, tit, t("plan/%d/note" % num, note) if note else ""))
    return out


def catalogue(language):
    mod = importlib.import_module("guide.chapters_%s" % language)
    return importlib.reload(mod).CATALOGUE


def problems(language="it"):
    try:
        cat = catalogue(language)
    except ModuleNotFoundError:
        return ["guide/chapters_%s.py does not exist: no text is translated" % language]
    out, seen = [], set()
    for key, en in all_texts():
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
    for key in sorted(set(cat) - seen):
        out.append("%s: %s is translated but the guide no longer has it" % (language, key))
    return out


def translated(cap, language):
    """The chapter with its texts in that language (the source, as it is, for
    English). A text without a valid translation stops here: problems() has
    already said which, and a page half in one language must not come out."""
    if language == LANGUAGES[0]:
        return cap
    cat = catalogue(language)
    c = copy.deepcopy(cap)

    def t(key, en):
        h, text = cat[key]
        if h != fingerprint(en):
            raise SystemExit("guide, %s: %s is out of date" % (language, key))
        return text

    i = cap["id"]
    c["title"] = t("%s/title" % i, cap["title"])
    c["intro"] = t("%s/intro" % i, cap["intro"])
    if cap.get("skip"):
        c["skip"] = t("%s/skip" % i, cap["skip"])
    c["tools"] = [t("%s/tool%d" % (i, k), a) for k, a in enumerate(cap.get("tools", []), 1)]
    for n, p in enumerate(c["steps"], 1):
        p["title"] = t("%s/%d/title" % (i, n), cap["steps"][n - 1]["title"])
        p["points"] = [t("%s/%d/point%d" % (i, n, k), x)
                       for k, x in enumerate(cap["steps"][n - 1].get("points", []), 1)]
    return c


def to_translate(language, chapter=None):
    """The entries to write: missing or out of date, as Python lines."""
    try:
        cat = catalogue(language)
    except ModuleNotFoundError:
        cat = {}
    lines = []
    for cap in chapters.CHAPTERS:
        if chapter and cap["id"] != chapter:
            continue
        for key, en in texts(cap):
            if key in cat and cat[key][0] == fingerprint(en):
                continue
            lines.append("    %r: (%r,\n        %r)," % (key, fingerprint(en), en))
    if not chapter:
        for key, en in plan_texts():
            if key in cat and cat[key][0] == fingerprint(en):
                continue
            lines.append("    %r: (%r,\n        %r)," % (key, fingerprint(en), en))
    return lines


if __name__ == "__main__":
    import sys
    l = sys.argv[1] if len(sys.argv) > 1 else "it"
    print("\n".join(to_translate(l, sys.argv[2] if len(sys.argv) > 2 else None)))
