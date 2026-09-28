# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""How much print bed a part needs, measured on its STEP.

The box-collar's print orientation used to say "wants a 200 x 200 bed", a
number written by hand. Now there is a second way to lay it - on the face of
the GX12 connector - and the bed is worked out for both. Measured, not written: the part changes and the number must follow it.

For a face on the bed (given by its outward normal), the part is projected
onto the bed and turned on it degree by degree until the square that holds
it is smallest - a bed is square, and a part turned 45 degrees often fits a
bed its straight footprint does not. Returned: the side of that square, the
turn, and the height of the print.
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
_CACHE = {}


def _points(part):
    if part not in _CACHE:
        import cadquery as cq
        solid = cq.importers.importStep(os.path.join(OUT, part + ".step")).val()
        vertices, _t = solid.tessellate(0.05)
        _CACHE[part] = [(v.x, v.y, v.z) for v in vertices]
    return _CACHE[part]


def footprint(part, normal, u, w):
    """(side of the smallest square, turn in degrees, height), in mm, of the
    part with the face of `normal` on the bed; u and w span the bed."""
    pts = _points(part)
    dot = lambda a, b: a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
    heights = [dot(q, normal) for q in pts]
    height = max(heights) - min(heights)
    best = None
    for degrees in range(180):
        a = math.radians(degrees)
        e1 = [math.cos(a)*u[i] + math.sin(a)*w[i] for i in range(3)]
        e2 = [-math.sin(a)*u[i] + math.cos(a)*w[i] for i in range(3)]
        p1 = [dot(q, e1) for q in pts]
        p2 = [dot(q, e2) for q in pts]
        side = max(max(p1) - min(p1), max(p2) - min(p2))
        if best is None or side < best[0]:
            best = (side, degrees)
    return best[0], best[1], height


def measures():
    """The numbers the print orientations quote, as placeholders.

    The keys are the placeholder names of the texts in guide/palette.py, in
    both the English and the Italian catalogue ("piatto" = bed, "giro" = turn,
    "alto" = height; "sportello" = laid on the door, "testa" = laid on the
    head): they are left as they are, with the catalogues."""
    import electronics as E
    side_d, turn_d, height_d = footprint("box_collar", (0, 0, 1), (1, 0, 0), (0, 1, 0))
    V = (E.V[0], E.V[1], 0.0)
    side_h, turn_h, height_h = footprint("box_collar", V, (-E.V[1], E.V[0], 0.0), (0, 0, 1))
    # the side rounded UP to the millimetre: a bed a tenth too small is too small
    return {"piatto_sportello": math.ceil(side_d), "giro_sportello": turn_d,
            "alto_sportello": "%.0f" % height_d,
            "piatto_testa": math.ceil(side_h), "giro_testa": turn_h,
            "alto_testa": "%.0f" % height_h}
