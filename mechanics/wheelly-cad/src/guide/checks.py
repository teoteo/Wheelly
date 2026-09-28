# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The checks of the assembly guide.

A wrong guide does not look wrong: the pictures are pretty all the same, the
text reads all the same, and the defect turns up in the hands of whoever
assembles, which is the worst place. These four checks look at the finished
product - the bodies of the assembly, the pixels of the pictures, the text
already filled in - and not at the intentions of whoever wrote the chapters.

1. **coverage**: every body of the assembly is in **exactly one** step. These
   are the two ways a guide lies without looking wrong: a part that is never
   mounted and a part that is mounted twice.
2. **really framed**: the part the step talks about must leave pixels in the
   picture. They are counted by redrawing the scene in flat shades, one per
   body: that the PNG exists proves nothing, a part out of frame or covered
   by another gives a file identical to a good one.
3. **placeholders**: no braces must be left in the finished text. A `{gioco}`
   that survives means the measure was never put in.
4. **sequence**: a step cannot show, move, cut or frame a part that has not
   arrived yet in the steps before.
"""
from . import chapters, scene, palette

# below this fraction of the picture the part is there but cannot be seen: it
# is not an error - an insert driven into its seat is almost all inside - but
# it has to be said, because it nearly always means the framing is to be redone
SCANT = 0.001


def names(raw_chapters, assembly_bodies):
    """The body names, checked BEFORE drawing.

    It is not pedantry about order: a wrong name makes the render die at the
    first step that names it, and from there only one error shows - the
    first - while the others stay hidden until that one is fixed. Here instead
    they all come out together, which is what is needed while a new chapter is
    being written.
    """
    problems = []
    for cap in raw_chapters:
        for i, step in enumerate(cap["steps"], 1):
            # A step without a `view` names no bodies: there is nothing to
            # check, and demanding a view from a step that installs a program
            # would mean putting a fake key in the data to keep the check happy.
            v = step.get("view")
            if v is None:
                continue
            # The context may be a SENTINEL - "PURCHASED" - that write.py
            # expands from the assembly. Here it is not expanded yet, and
            # iterating it would give its letters one by one as if they were
            # body names.
            if isinstance(step.get("context"), str):
                continue
            cited = (list(step["mounts"]) + list(step.get("context", []))
                     + list(step.get("backdrop", [])) + list(v.get("explode", {}))
                     + list(v.get("cut", [])) + list(v.get("frame") or [])
                     + [f[0] for f in v.get("arrows", [])])
            for body in cited:
                if body not in assembly_bodies:
                    problems.append("chapter %d step %d: the assembly has no "
                                    "body '%s'" % (cap["num"], i, body))
    return problems


def coverage(prepared, assembly_bodies):
    """Every body in exactly one step."""
    problems, where = [], {}
    for cap in prepared:
        for step in cap["steps"]:
            for body in step["mounts"]:
                if body not in assembly_bodies:
                    problems.append("chapter %d step %d: the assembly has no "
                                    "body '%s'" % (cap["num"], step["n"], body))
                where.setdefault(body, []).append((cap["num"], step["n"]))
    for body, places in sorted(where.items()):
        if len(places) > 1:
            problems.append("'%s' is mounted %d times: %s"
                            % (body, len(places),
                               ", ".join("ch %d step %d" % p for p in places)))
    # The bodies not mounted yet are an error only when the guide is
    # complete: while chapters are missing, their parts are missing too.
    some_chapter_missing = len(prepared) < len(chapters.PLAN)
    uncovered = sorted(set(assembly_bodies) - set(where) - set(NOT_MOUNTED))
    if uncovered and not some_chapter_missing:
        problems.append("these bodies are mounted in no step: %s"
                        % ", ".join(uncovered))
    return problems, uncovered


# The bodies of the assembly that are not parts to mount: the starting wheel
# and its disc are there as a reference, the envelopes of the electronics are
# estimates of what the board will take. The guide shows them but does not
# "mount" them.
NOT_MOUNTED = ("filter_wheel_body", "filter_disc")


def framed(prepared):
    """Does the part the step talks about leave pixels in the picture?

    The counts are not redone here: whoever drew the picture already took
    them, redrawing the same scene in flat shades right after. It is the only
    way to be sure one is counting exactly the picture that ends up in the
    page, and not a similar one."""
    problems, scant = [], []
    for cap in prepared:
        for step in cap["steps"]:
            counts = step["counts"]
            total = float(sum(counts.values())) or 1.0
            for body in step["mounts"]:
                n = counts.get(body, 0)
                if n == 0:
                    problems.append("chapter %d step %d: '%s' is mounted here but "
                                    "not one pixel of it shows in the picture"
                                    % (cap["num"], step["n"], body))
                elif n / total < SCANT:
                    scant.append("chapter %d step %d: '%s' shows only %d pixels"
                                 % (cap["num"], step["n"], body, n))
    return problems, scant


def placeholders(prepared):
    """Braces left in the text already filled in."""
    problems = []
    for cap in prepared:
        if "{" in cap["intro"] or "}" in cap["intro"]:
            problems.append("chapter %d, introduction: placeholder not "
                            "replaced" % cap["num"])
        for text in cap["tools"]:
            if "{" in text or "}" in text:
                problems.append("chapter %d, tools: placeholder not "
                                "replaced in \"%s\"" % (cap["num"], text))
        for step in cap["steps"]:
            for text, _careful in step["points"]:
                if "{" in text or "}" in text:
                    problems.append("chapter %d step %d: placeholder not "
                                    "replaced in \"%s\"" % (cap["num"], step["n"], text))
    return problems


def sequence(prepared):
    """No step brings in a part that has not arrived yet.

    With one exemption, and one only: **a chapter that mounts nothing** cannot
    break the sequence, because for it there is no "after". It is the case of
    the opening chapter, which shows the finished machine before starting -
    and that is exactly what it must do. The exemption is not asked for with a
    flag in the data: it is earned by mounting nothing, so it cannot be used
    to silence the check in a real chapter.
    """
    problems, mounted = [], set()
    for cap in sorted(prepared, key=lambda c: c["num"]):
        if not any(step["mounts"] for step in cap["steps"]):
            continue
        for step in cap["steps"]:
            arriving = set(step["mounts"])
            cited = set(step["cited"]) - arriving
            unknown = sorted(cited - mounted - set(NOT_MOUNTED))
            if unknown:
                problems.append("chapter %d step %d: brings in parts that "
                                "have not arrived yet: %s"
                                % (cap["num"], step["n"], ", ".join(unknown)))
            mounted |= arriving
    return problems


def all_checks(prepared, assembly_bodies):
    """All four, and returns the list of problems plus the list of notes."""
    problems, notes = [], []
    p, uncovered = coverage(prepared, assembly_bodies)
    problems += p
    if uncovered:
        notes.append("still to be mounted in a chapter: %d bodies (%s)"
                     % (len(uncovered), ", ".join(uncovered[:6]) + ("..." if len(uncovered) > 6 else "")))
    p, scant = framed(prepared)
    problems += p
    notes += scant
    problems += placeholders(prepared)
    problems += sequence(prepared)
    return problems, notes


# --------------------------------------------------------------- two languages
# 5. **bilingual**: checked on the FILES written, not on the data they come
#    from. English in docs/assembly/, Italian in docs/assembly/it/; the checks
#    are the ways a two-language site goes wrong without looking wrong - a page
#    with no twin (the toggle leads to a 404), a toggle that points to the
#    wrong file, an Italian page with "Next" or "Step 3" left in it, a page
#    that says it is English and is not.

def _visible_text(source):
    """What a reader sees of a page: no script, no style, no tags."""
    import html as _h
    import re
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", source)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return _h.unescape(t)


def _words_of(lang):
    """The fixed words that belong to `lang` and must not show up in a page
    of the other one: the UI texts that differ between the two, the part and
    item names, the electronics parts, the chapter titles and their notes."""
    import bom_electronics
    from . import interface, language as languages
    other = "it" if lang == "en" else "en"
    words = set()
    if lang == "en":
        words |= set(interface.english_left())
    else:
        import re
        for text_key, texts in interface.TEXTS.items():
            if text_key == "md_other_language" or texts["it"] == texts["en"]:
                continue
            piece = re.split(r"%|<|\*\*|\[|`", texts["it"])[0].strip(" —:")
            if len(piece) >= 4:
                words.add(piece)
    pairs = []
    for name, (_c, en) in palette.PARTS.items():
        pairs.append((en, palette.NAMES_IT.get(name, en)))
    for name, en in palette.ITEMS.items():
        pairs.append((en, palette.ITEMS_IT.get(name, en)))
    for it_en in bom_electronics.ITEMS:
        it_it = bom_electronics.ITEMS_IT.get(bom_electronics._key(it_en))
        if it_it:
            pairs.append((it_en[2], it_it[1]))
    for (n, ten, nen), (_n, tit, nit) in zip(languages.plan("en"), languages.plan("it")):
        pairs += [(ten, tit), (nen, nit)]
    for en, it in pairs:
        mine, theirs = (en, it) if lang == "en" else (it, en)
        # a name that is the same in both (XIAO ESP32-S3, "magnet" inside
        # "magnete" is not a match anyway: the search is by whole words)
        if mine and mine != theirs and len(mine) >= 4:
            words.add(mine)
    return sorted(words)


def bilingual(destination, languages_=("en", "it")):
    import os
    import re
    problems = []
    folders = {l: destination if l == languages_[0] else os.path.join(destination, l)
               for l in languages_}

    def pages(l):
        c = folders[l]
        if not os.path.isdir(c):
            return set()
        return {f for f in os.listdir(c) if f.endswith((".html", ".md"))}

    # (a) every page has its twin, both ways
    for l in languages_:
        for other in languages_:
            if other == l:
                continue
            for f in sorted(pages(l) - pages(other)):
                problems.append("bilingual: %s/%s has no twin in %s" % (l, f, other))

    for l in languages_:
        foreign = _words_of("it" if l == "en" else "en")
        for f in sorted(pages(l)):
            path = os.path.join(folders[l], f)
            src = open(path, encoding="utf-8").read()
            where = "%s/%s" % (l, f)
            if f.endswith(".html"):
                # (b) the page says the language it is in
                m = re.search(r'<html lang="([a-z-]+)"', src)
                if not m or m.group(1) != l:
                    problems.append("bilingual: %s declares lang=%s"
                                    % (where, m.group(1) if m else "nothing"))
                # (c) the switch: there, one link per language, each to an
                #     existing file that is THIS page in that language, the
                #     page's own language the active one
                nav = re.search(r'(?s)<nav class="lang-switch"[^>]*>(.*?)</nav>', src)
                if not nav:
                    problems.append("bilingual: %s has no language switch" % where)
                else:
                    links = re.findall(r'<a class="lang-btn( is-active)?"[^>]*?'
                                       r'href="([^"]+)" hreflang="([a-z]+)"', nav.group(1))
                    if sorted(h for _a, _r, h in links) != sorted(languages_):
                        problems.append("bilingual: %s, the switch has %s"
                                        % (where, [h for _a, _r, h in links]))
                    for active, href, h in links:
                        lands = os.path.normpath(os.path.join(folders[l], href))
                        expected = os.path.normpath(os.path.join(folders.get(h, "?"), f))
                        if not os.path.exists(lands):
                            problems.append("bilingual: %s, %s leads to %s, which does "
                                            "not exist" % (where, h.upper(), href))
                        elif lands != expected:
                            problems.append("bilingual: %s, %s leads to %s and not to "
                                            "the same page" % (where, h.upper(), href))
                        if bool(active) != (h == l):
                            problems.append("bilingual: %s, %s is%s marked active"
                                            % (where, h.upper(), "" if active else " not"))
                    if nav.group(1).count('aria-current="page"') != 1:
                        problems.append("bilingual: %s, the switch has not one "
                                        "aria-current" % where)
                # canonical and alternates, when relative, lead to THIS page in
                # the language they name (canonical: this very page)
                for rel, h, href in re.findall(r'<link rel="(canonical|alternate)"'
                                               r'(?: hreflang="([a-z-]+)")? href="([^"]+)"', src):
                    if "://" in href:
                        continue
                    h = {"": l, "x-default": languages_[0]}.get(h, h)
                    lands = os.path.normpath(os.path.join(folders[l], href))
                    if not os.path.exists(lands):
                        problems.append("bilingual: %s, %s %s does not exist" % (where, rel, href))
                    elif lands != os.path.normpath(os.path.join(folders.get(h, "?"), f)):
                        problems.append("bilingual: %s, %s (%s) %s is not the same page"
                                        % (where, rel, h, href))
                text = _visible_text(src)
            else:
                # the Markdown: its link to the other language leads to a file
                for href in re.findall(r"^\*\[[^\]]+\]\(([^)]+)\)\*$", src, re.M)[:1]:
                    if not os.path.exists(os.path.join(folders[l], href)):
                        problems.append("bilingual: %s, the language link %s does "
                                        "not exist" % (where, href))
                if not re.search(r"^\*\[[^\]]+\]\(([^)]+)\)\*$", src, re.M):
                    problems.append("bilingual: %s has no link to the other language" % where)
                text = re.sub(r"(?s)<!--.*?-->", " ", src)
                # file names are not words of the page: the drawing of the
                # magnet is magnet-magnetisation.svg in both languages
                text = re.sub(r'(?:src|href)="[^"]*"', " ", text)
                text = re.sub(r"\]\([^)]*\)", "]", text)
            # (d) no word of the other language left in the page
            for p in foreign:
                if re.search(r"(?<!\w)%s(?!\w)" % re.escape(p), text):
                    problems.append("bilingual: %s still says \"%s\" (%s)"
                                    % (where, p, "en" if l != "en" else "it"))
    return problems
