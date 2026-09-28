# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Where a dimension sits inside the drawing, and how to draw it on top.

The "drawings" field of parameters.py says in which figure a parameter
appears, not at which point. The point is found in two ways, and the first is
the good one.

**The signature.** While it draws, `drawings.py` records which parameters it
has read and writes them onto the entity as XDATA (see `_Msp` in there). A
circle that carries `L_groove_gasket` written on it IS that dimension, and
there is nothing to guess: that parameter had six matches in the collar
section, and with the signature it has one.

**The measurement**, for everything else: the DXF is searched for the
geometries worth that number. It is the earlier way, and on its own it is not
enough - 219 parameters out of 336 share their value with another one, so
ambiguity is the rule, not the exception. Selecting `Cd_holes_board_w`, which
is worth 26, the editor showed the MOTOR holes, which are 26 as well, and
showed them with the same confidence with which it would have shown the right
one. On an editor used with the calipers in hand, this is the worst defect it
could have.

So: if some candidate carries the parameter's signature, ONLY those are kept.
If none carries it, all are kept and it is DECLARED that there is more than
one, instead of picking one and giving it as certain.

**Where the signature does not reach**, and it is better to know it than to
expect it: when the dimension is read far from the entity that comes out of it
- the four motor holes are placed from `Cd_holes_motor` read at the top of the
function, and the signature ends up on the entity written right after that
read - and in the assembly views, which pile up the drawing in closures and
write it all at the end. And there is the worst case, which no signature can
solve: a dimension whose geometry is in NO drawing the editor knows how to
show, like `Cd_holes_board_w` itself - the board's holes are in the SVG of the
perfboard, not in a DXF. There the right answer is the declared one: these
points are worth that number, which one is its own is not known.
"""
import math, os, ezdxf

TOLERANCE = 0.06        # the values in the file are rounded to 2 decimals

# From the most specific to the most generic: a diameter that matches says far
# more than two parallel segments at the right distance.
# (the keys are also the editor's catalogue keys, ui.kind_<key>: they stay)
PRIORITY = {"diametro": 0, "raggio": 1, "interasse": 2, "lunghezza": 3,
            "distanza": 4, "ascissa": 5, "ordinata": 5, "spessore": 6}

MAX_SHOWN = 4              # beyond that, the drawing becomes unreadable

# Beyond this number of matches the search by value says nothing any more:
# L_cavity_gasket is worth 0.50 and in an assembly view it comes back at 363
# points, because half a millimetre is the distance between an infinity of
# things. Pointing at four of them at random, with the air of knowing which, is
# worse than saying it is not known: whoever looks believes it and goes looking
# with the calipers for a point chosen by chance.
TOO_MANY = 12

# The pairwise tests are quadratic, and on a circle discretised into three
# hundred sides every pair of opposite sides is one diameter apart: one ends
# up with thousands of true and useless matches. Only the longest segments are
# looked at, which are the ones that stand for walls and shoulders.
MAX_PAIRS = 120
MIN_LENGTH = 1.5       # mm: below it, it is the discretisation of a curve

_cache = {}


def features(path):
    """Circles and segments of the drawing, with the polylines already broken up.

    The polylines of drawings.py carry bulges: without breaking them into real
    arcs every curve would look like a straight chord, and half the radii would
    not be found.
    """
    key_ = (path, os.path.getmtime(path))
    if key_ in _cache:
        return _cache[key_]
    msp = ezdxf.readfile(path).modelspace()
    circles, segments = [], []
    signature = [()]        # the signature of the entity being broken up

    def collect(e):
        t = e.dxftype()
        if t == "CIRCLE":
            circles.append((e.dxf.center.x, e.dxf.center.y, e.dxf.radius, True, signature[0]))
        elif t == "ARC":
            circles.append((e.dxf.center.x, e.dxf.center.y, e.dxf.radius, False, signature[0]))
        elif t == "LINE":
            segments.append((e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y,
                             signature[0]))

    for e in msp:
        signature[0] = _signature(e)
        # The leader lines of the assembly views are not geometry: if they
        # came in here, a leader as long as it happens to be would offer
        # itself as a match for any dimension at all. (ETICHETTE is the DXF
        # layer name written by drawings_assembly.py: an output, it stays.)
        if e.dxf.layer == "ETICHETTE":
            continue
        if e.dxftype() == "LWPOLYLINE":
            for v in e.virtual_entities():
                collect(v)
            circles.extend(_implicit_arcs([(p[0], p[1]) for p in e.get_points("xy")],
                                          signature=signature[0]))
        else:
            collect(e)

    _cache.clear()
    _cache[key_] = (circles, segments)
    return circles, segments


APPID_DIMENSIONS = "WHEELLY"          # the same one drawings.py signs with


def _signature(e):
    """The parameters that entity was drawn with, if it carries them.

    An old drawing, generated before the signature existed, has none: here it
    comes back empty and one falls back on the measurement, the earlier way.
    """
    try:
        data = e.get_xdata(APPID_DIMENSIONS)
    except Exception:
        return ()
    return tuple(v for code, v in data if code == 1000)


def matches(value, data, name=None):
    """The geometries that measure that value, most significant first.

    With `name`, that is with the parameter's name, the candidates carrying its
    signature win over all the others: it is the only way to tell apart two
    dimensions worth the same number, and two parameters out of three in this
    project are worth as much as some other one.
    """
    circles, segments = data
    found = []
    if value <= 0:
        return found

    for c in circles:
        cx, cy, rad = c[0], c[1], c[2]
        if abs(2 * rad - value) < TOLERANCE:
            found.append(("diametro", c))
        elif abs(rad - value) < TOLERANCE:
            found.append(("raggio", c))
        d = math.hypot(cx, cy)
        if abs(d - value) < TOLERANCE and d > 0.1:
            found.append(("distanza", c))
        elif abs(abs(cx) - value) < TOLERANCE and abs(cx) > 0.1:
            found.append(("ascissa", c))
        elif abs(abs(cy) - value) < TOLERANCE and abs(cy) > 0.1:
            found.append(("ordinata", c))

    holes = circles[:MAX_PAIRS]
    for i in range(len(holes)):                       # centre distances between equal holes
        for j in range(i + 1, len(holes)):
            a, b = holes[i], holes[j]
            if abs(a[2] - b[2]) > 0.01:
                continue
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            if abs(d - value) < TOLERANCE and d > 0.1:
                found.append(("interasse", (a, b)))

    for s in segments:
        if abs(math.hypot(s[2] - s[0], s[3] - s[1]) - value) < TOLERANCE:
            found.append(("lunghezza", s))

    # The segments compared are the longest ones - they are the ones that
    # stand for walls and shoulders - PLUS those signed WITH THIS parameter,
    # however short. Without the second half the plane of the flat, which is
    # a three-millimetre chord in an assembly drawing two hundred wide, did
    # not enter the comparison: the dimension that comes from it could not be
    # found and the editor fell back on any pair worth the same number. And
    # only those of the parameter searched for, not all the signed ones:
    # admitting them all multiplies the pairs and the noise with them - tried,
    # the "too many matches" parameters went from 7 to 16.
    _ord = sorted((s for s in segments
                   if math.hypot(s[2] - s[0], s[3] - s[1]) >= MIN_LENGTH),
                  key=lambda s: -math.hypot(s[2] - s[0], s[3] - s[1]))
    long_ = _ord[:MAX_PAIRS] + [s for s in _ord[MAX_PAIRS:]
                                if name and name in (s[-1] or ())]
    for i in range(len(long_)):                     # thicknesses between parallels
        for j in range(i + 1, len(long_)):
            a, b = long_[i], long_[j]
            ax, ay = a[2] - a[0], a[3] - a[1]
            bx, by = b[2] - b[0], b[3] - b[1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if abs(ax * by - ay * bx) / (la * lb) > 0.02:
                continue
            # they must face each other: projected on the first one's
            # direction, they overlap
            ux, uy = ax / la, ay / la
            t0 = (b[0] - a[0]) * ux + (b[1] - a[1]) * uy
            t1 = (b[2] - a[0]) * ux + (b[3] - a[1]) * uy
            if min(t0, t1) > la or max(t0, t1) < 0:
                continue
            d = abs((b[0] - a[0]) * ay - (b[1] - a[1]) * ax) / la
            if abs(d - value) < TOLERANCE and d > 0.05:
                found.append(("spessore", (a, b)))

    found = _without_duplicates(found)
    if not found:
        return found
    # THE SIGNATURE WINS. If even a single candidate carries the parameter's
    # name written on it, the others are no longer candidates: they are worth
    # that number by coincidence. It is what tells the board holes from the
    # motor ones, which have the same centre distance and no other measurable
    # difference.
    if name:
        signed = [t for t in found if _bears_signature(t[1], name)]
        if signed:
            found = signed
        else:
            # THE NAME SAYS WHAT KIND OF DIMENSION IT IS. In this project the
            # names are systematic - Th_ a thickness, D_ a diameter, R_ a
            # radius, Cd_ a centre distance - and that convention is worth as
            # much as a measurement: for Th_flange_collar, a thickness of
            # 3.00, the editor showed FIFTEEN diameters of 3.00, that is the
            # M3 screws of the assembly view, because among the kinds the
            # diameter has precedence. The kind the name announces is
            # preferred, but only if some candidate has it: if none does, one
            # goes back to all of them, because a convention is not a proof.
            expected = kind_from_name(name)
            right = [t for t in found if t[0] == expected]
            if right:
                found = right
    # A common value - 3.00 mm in a section - comes back on many geometries.
    # Only the most specific kind of match among those present is kept: better
    # two right diameters than two diameters drowned in twelve thicknesses.
    best = min(PRIORITY[t[0]] for t in found)
    found = [t for t in found if PRIORITY[t[0]] == best]
    found.sort(key=lambda t: PRIORITY[t[0]])
    return found


# The prefix of the name and the kind of match expected. They are only the four
# prefixes that have no exceptions in this project: H_ and L_ not, because a
# height can be a length as much as a thickness between two faces as much as a
# dimension from the datum plane, and an uncertain convention would hide the
# right match instead of finding it.
# The prefixes followed the parameters into English (the table is in
# `rename_en.py`). The renaming does NOT touch this one, because here the
# prefixes are pieces of string and not whole names: left behind, the editor
# would have stopped recognising the kind of every dimension without saying
# so, and would have gone back to showing fifteen diameters of 3.00 to whoever
# looks for a thickness.
KIND_FROM_NAME = (("Th_", "spessore"), ("D_", "diametro"),
                  ("R_", "raggio"), ("Cd_", "interasse"))


def kind_from_name(name):
    """The kind of match the parameter's name announces, if it announces one."""
    for prefix, kind in KIND_FROM_NAME:
        if name.startswith(prefix):
            return kind
    return None


def signed(found, name):
    """How many of the matches carry the parameter's signature.

    The page needs it to tell the truth about what it shows: a signed match is
    the right point, three unsigned matches are three places worth the same
    number and the editor does not know which one it is.
    """
    return sum(1 for t in found if _bears_signature(t[1], name))


def _bears_signature(item, name):
    """Whether the item - a geometry, or the pair of a centre distance or of a
    thickness - was drawn reading that parameter.

    For a pair it is enough that ONE of the two carries it: the centre
    distance between two holes comes from a single read, and what signs it is
    the entity written right after."""
    if item and isinstance(item[0], tuple):          # pair
        return any(_bears_signature(d, name) for d in item)
    return name in (item[-1] if item and isinstance(item[-1], tuple) else ())


def _without_duplicates(found):
    """Removes the matches that fall at the same point.

    A discretised curve produces dozens of nearly coincident sides: without
    this the same dimension would be counted once per side.
    """
    seen, clean = set(), []
    for kind, item in found:
        if kind in ("diametro", "raggio", "distanza", "ascissa", "ordinata"):
            key_ = (kind, round(item[0], 1), round(item[1], 1), round(item[2], 1))
        elif kind == "interasse":
            a, b = item
            key_ = (kind, round(a[0], 1), round(a[1], 1), round(b[0], 1), round(b[1], 1))
        elif kind == "lunghezza":
            key_ = (kind, round((item[0] + item[2]) / 2), round((item[1] + item[3]) / 2))
        else:
            a, b = item
            key_ = (kind, round((a[0] + a[2] + b[0] + b[2]) / 4),
                   round((a[1] + a[3] + b[1] + b[3]) / 4))
        if key_ in seen:
            continue
        seen.add(key_)
        clean.append((kind, item))
    return clean


def _implicit_arcs(points, minimum=6, signature=()):
    """Stretches of polyline at constant radius from the origin.

    In the assembly views the circles and the sectors are polylines, not arcs:
    without this the body's diameter would not be found, and the same circle
    would show up as hundreds of pairs of opposite sides one diameter apart.
    The centre of the disc is the origin of all the drawings, so looking at
    the radius is enough.
    """
    found, start = [], 0
    radii = [math.hypot(x, y) for x, y in points]
    for i in range(1, len(radii) + 1):
        end = i == len(radii) or abs(radii[i] - radii[start]) > 0.02
        if end:
            if i - start >= minimum and radii[start] > 0.5:
                found.append((0.0, 0.0, radii[start], False, signature))
            start = i
    return found
