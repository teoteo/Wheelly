# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The little that the SVG wiring drawings have in common.

It stands apart because both the board layout and the wiring diagrams use it,
and two copies of the same function drift apart at the first touch-up: the
same reason the placement of the components lives in one place only.
"""
import math


def hole_label(c, r):
    """The hole as it is PRINTED on the board: A to X and 01 to 10.

    Inside the model the columns count from zero on the head side and the rows
    from zero on the back side; on the perfboard instead it says A..X and
    01..10, with row 01 towards the axis and row 10 on the back, as on the
    reference board (with row 10 towards the axis, a board built from the
    labels came out the mirror of the model). Whoever holds the board reads
    that one, not ours, and the drawings for them must speak their language:
    the verified layout of the reference board is in these coordinates.
    """
    return "%s%02d" % (chr(ord("A") + int(c)), 10 - int(r))


def hole_label_below(c, r, n_col):
    """The hole as it is printed ON THE UNDERSIDE of the board.

    The perfboard carries the silkscreen on both faces, and each reads from
    left to right: turning the board over to solder, the column on the left is
    no longer the A of the top side but the A of the underside. So the SAME
    physical hole has two names, one the mirror of the other, and whoever
    solders looking at the copper reads the second, as checked with the board
    in hand.

    The rows do not change: the board turns about its long axis, so only the
    direction of the columns is mirrored.
    """
    return "%s%02d" % (chr(ord("A") + (int(n_col) - 1 - int(c))), 10 - int(r))


def curve(p, bulge=0.045):
    """The path of a wire, smooth instead of broken.

    A real wire has no corners: it bends. With polylines a wire could not be
    told from a line of the drawing, so the vertices are rounded with a
    Catmull-Rom converted to Bezier, and the two-point wires get a slight
    bulge - a fraction of their length - enough to read them as wires without
    moving them over the components.
    """
    if len(p) == 2:
        (x0, y0), (x1, y1) = p
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        mx = (x0 + x1)/2 - dy*bulge
        my = (y0 + y1)/2 + dx*bulge
        return "M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" % (x0, y0, mx, my, x1, y1)
    d = "M%.1f,%.1f" % p[0]
    for i in range(len(p) - 1):
        p0 = p[i-1] if i > 0 else p[0]
        p1, p2 = p[i], p[i+1]
        p3 = p[i+2] if i + 2 < len(p) else p[-1]
        c1 = (p1[0] + (p2[0]-p0[0])/6.0, p1[1] + (p2[1]-p0[1])/6.0)
        c2 = (p2[0] - (p3[0]-p1[0])/6.0, p2[1] - (p3[1]-p1[1])/6.0)
        d += " C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    return d


# ---------------- the two languages of the drawings -------------------------
# Every drawing comes out twice, NAME_en.svg and NAME_it.svg: the
# documentation points at _en, and _it is for an Italian
# reader with the printed booklet. The texts are keys into two catalogues,
# texts_drawings_en.py and texts_drawings_it.py; the language being drawn is
# WHEELLY_LINGUA, and a generator run without it draws both.
import os as _os, re as _re
import texts_drawings_en as _en, texts_drawings_it as _it

LANGUAGES = ("en", "it")
_CATALOGUES = {"en": _en.TEXTS, "it": _it.TEXTS}
_only = sorted(set(_en.TEXTS) ^ set(_it.TEXTS))
if _only:
    raise SystemExit("the two catalogues of the drawings do not hold the same keys: %s" % ", ".join(_only))


def language():
    return _os.environ.get("WHEELLY_LINGUA", "en")


def tr(key, **fields):
    """The text of a key in the language being drawn."""
    return _CATALOGUES[language()][key].format(**fields) if fields else _CATALOGUES[language()][key]


# The names of the generated files, in the two languages: en_ or it_ at the
# start, then the name of what it is, in that language (the Italian ones are
# the historical names). The key is the Italian name.
# A name that is not here stops the generator: a new file must not come out
# with its name in one language only.
FILE_NAMES = {
    "wheelly-schemi-montaggio":     {"en": "wheelly-wiring-diagrams"},
    "disposizione-basetta":         {"en": "board-layout"},
    "collegamenti-xiao-tmc2209":    {"en": "wiring-xiao-tmc2209"},
    "collegamenti-xiao-as5600-led": {"en": "wiring-xiao-as5600-led"},
    "collegamenti-potenza-motore":  {"en": "wiring-motor-power"},
}


def name_in_language(name, language_=None):
    """The file's name in the language, without the prefix and extension."""
    l = language_ or language()
    if name not in FILE_NAMES:
        raise SystemExit("drawing_common: the file %r has no name in both languages "
                         "(FILE_NAMES)" % name)
    return name if l == "it" else FILE_NAMES[name][l]


def with_language(name, extension, language_=None):
    """NAME -> en_<English name>.ext / it_<Italian name>.ext. The language used
    to be a suffix on the Italian name (disposizione-basetta_en.svg); an English
    reader got a file named in Italian."""
    l = language_ or language()
    return "%s_%s.%s" % (l, name_in_language(name, l), extension)


def sections_of(svg_path):
    """The JSON of the sections that goes with a drawing, named in its language."""
    base = _os.path.splitext(svg_path)[0]
    return base + (".sections.json" if language() == "en" else ".sezioni.json")


# Words that only one of the two languages uses. A drawing in one language
# carrying a word of the other means a string that did not go through the
# catalogue - written in line, or left behind by a later edit - and it is the
# defect this whole arrangement exists to prevent. Checked on the finished SVG.
_ONLY_IT = {"della", "dello", "delle", "del", "dei", "degli", "il", "lo", "gli", "di", "dal",
            "dalla", "con", "che", "non", "è", "sulla", "sul", "fili", "filo", "massa",
            "morsetto", "foro", "fori", "basetta", "ramo", "nodo", "sotto", "sopra", "capo",
            "vista", "piedini", "cavo", "verso", "segnali", "fase", "ingresso"}
_ONLY_EN = {"the", "of", "and", "with", "from", "wire", "wires", "ground", "board", "cable",
            "hole", "holes", "pins", "side", "where", "which", "above", "below", "this"}


def check_language(svg, name):
    """Stop if the text of the drawing holds a word of the other language."""
    other = _ONLY_IT if language() == "en" else _ONLY_EN
    texts = _re.findall(r"<(?:text|title|desc)[^>]*>([^<]*)<", svg)
    found = [(p, t) for t in texts for p in _re.findall(r"[A-Za-zÀ-ú']+", t.lower()) if p in other]
    if found:
        raise SystemExit("%s: the '%s' version holds words of the other language:\n%s"
                         % (name, language(), "\n".join("  %s  in \"%s\"" % pt for pt in found[:8])))
