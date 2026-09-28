# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The TRUE SHAPE of the parts on the 2D pages of the parameter editor.

WHY IT EXISTS. The pages of the editor (collar_plan, arm_plan,
clutch_section, collar_section) draw the parts again, by hand, from the
parameters - and once the box and the collar became one part nobody followed
them: the collar page still showed the old collar with its ears, the clutch
section a rectangle across the disc, the arm page no spring tab. Drawings
redrawn by hand fall behind the parts they show.

WHAT IT DOES. Each page gets, on a layer of its own (VERA_FORMA - a layer
name, part of the DXF output, and so left as it is), the section of the
solids as the last build exported them - the same STEP files the checks
measure - with a line saying so. The lines drawn from the
parameters stay: they are what the editor moves while a value is being
tried, and the true shape is what the model IS until the next build. The two
disagreeing on a page is information, not noise.

WHERE THE STEP FILES ARE. In out/ - or, inside the editor's sandbox, in the
real project's out/, which ui_build passes as WHEELLY_OUT_SOLIDI: the
sandbox builds no solids.

SPEED. A section of the one-part box costs seconds, and the editor redraws
at every change. The sections are cached next to the drawings, keyed by the
STEP file's time: they are computed again only after a build.
"""
import json
import os
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("WHEELLY_OUT_SOLIDI", os.path.join(HERE, "out")) + os.sep
CACHE = os.path.join(HERE, "out", "drawings", ".true_shape.json")


def _load_cache():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(c):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w") as f:
            json.dump(c, f)
    except Exception:
        pass


def _polylines(step, plane):
    """The section of a STEP by a plane, as polylines in the plane's own 2D
    coordinates. plane: ("z", z0) for a plan at height z0, (x, y) kept;
    ("y", y0) for an upright section at y0, (x, z) kept."""
    import cadquery as cq
    sol = cq.importers.importStep(step).val()
    axis, q = plane
    if axis == "z":
        f = cq.Face.makePlane(1000, 1000, cq.Vector(0, 0, q), cq.Vector(0, 0, 1))
        uv = lambda p: (p.x, p.y)
    else:
        f = cq.Face.makePlane(1000, 1000, cq.Vector(0, q, 0), cq.Vector(0, 1, 0))
        uv = lambda p: (p.x, p.z)
    out = []
    try:
        sec = sol.intersect(f)
    except Exception:
        return out
    for fc in sec.Faces():
        for w in [fc.outerWire()] + fc.innerWires():
            n = max(24, int(w.Length() / 0.5))
            pts = [uv(w.positionAt(k / n)) for k in range(n + 1)]
            out.append([(round(a, 3), round(b, 3)) for a, b in pts])
    return out


def sections(step_name, plane):
    """The polylines of one STEP cut by one plane, from the cache when the STEP
    has not changed since. None when the STEP is not there (no build yet)."""
    step = OUT + step_name
    if not os.path.exists(step):
        return None
    key = "%s|%s|%s" % (step_name, plane[0], plane[1])
    t = os.path.getmtime(step)
    c = _load_cache()
    if key in c and c[key]["t"] == t:
        return c[key]["pl"]
    pl = _polylines(step, plane)
    c[key] = {"t": t, "pl": pl}
    _save_cache(c)
    return pl


def draw(m, parts, where, height=2.0, x_min=None):
    """Draw the true shape on msp `m`: parts = [(step, plane), ...]. The note
    goes at `where` and says what the layer is and from which build. x_min
    drops what lies wholly on the far side of the axis: the sections of the
    pages draw one radius, the plane cuts the whole wheel."""
    doc = m.doc if hasattr(m, "doc") else None
    try:
        (doc or m).layers.add("VERA_FORMA", color=3)
    except Exception:
        pass
    when, drawn = None, 0
    for step, plane in parts:
        pl = sections(step, plane)
        if pl is None:
            continue
        when = max(when or 0, os.path.getmtime(OUT + step))
        for p in pl:
            if x_min is not None and max(a for a, _b in p) < x_min:
                continue
            m.add_lwpolyline(p, dxfattribs={"layer": "VERA_FORMA"})
            drawn += 1
    if drawn:
        text = ("green: TRUE SHAPE, section of the solids of the last build (%s); "
                 "white: drawn from the parameters"
                 % time.strftime("%d/%m/%Y %H:%M", time.localtime(when)))
    else:
        text = "true shape not available: no solids built yet"
    m.add_text(text, height=height, dxfattribs={"layer": "VERA_FORMA"}).set_placement(where)
    return drawn
