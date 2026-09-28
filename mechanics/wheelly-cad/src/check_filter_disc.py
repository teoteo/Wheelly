# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The filter disc of reference: closed holes, on the optical axis.

Why it exists. The modelled disc used to have five holes of 51 mm at
48 mm from the centre, both numbers written by hand: 48 + 25.5 = 73.5 against
a rim radius of 72.5, so every hole cut 1 mm into the rim and the disc was
five petals held by the hub. It showed next to a photo of the real disc,
whose holes are closed with about 3 mm of material to the rim. No check had
seen it, because nothing measured the disc: it is not printed, it is only a
reference - but the optical axis, and everything placed on it, comes from it.

What it measures, on the STEP files and not on the parameters:
- the holes, found as the off-centre cylindrical faces of filter_disc.step:
  their number, their diameter, the radius of their circle;
- the material between each hole and the rim, as the distance between the
  hole's face and the outer cylindrical face of the disc: a hole that cuts
  the rim shares an edge with it and measures 0;
- the web between each pair of adjacent holes, face to face;
- that the first hole is coaxial with the optical hole of the wheel body
  (filter_wheel_body.step): a filter in position is on the optical axis, and
  the body and the disc are two solids drawn by the same number only as long
  as nobody writes another one.

The web is compared with W_web_filter because that is an OBSERVATION of
the real disc (estimated by hand from a photo), not a number the check
rereads to watch itself; the rim is compared with a fixed floor.

Outside the audit, so that breaking it on purpose costs seconds.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GeomAbs import GeomAbs_SurfaceType
from parameters import D, out_subdir

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep

# Material left between a filter hole and the rim, at least. The real disc
# has about 3.2 (photo); 2 mm is the floor under which the model would no
# longer be that disc - and zero is the defect this check was born for.
RIM_MIN = 2.0
# How far the modelled web may be from the observed one. The observation is
# ±0.3 by hand; the model has to reproduce it exactly, since it is derived
# from it, so the tolerance only absorbs the STEP round trip.
WEB_TOL = 0.05

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


def cylinders(solid):
    """(face, radius, (x, y) of the axis) for every cylindrical face with a
    vertical axis."""
    found = []
    for f in solid.Faces():
        s = BRepAdaptor_Surface(f.wrapped)
        if s.GetType() != GeomAbs_SurfaceType.GeomAbs_Cylinder:
            continue
        c = s.Cylinder()
        if abs(abs(c.Axis().Direction().Z()) - 1.0) > 1e-6:
            continue
        p = c.Location()
        found.append((f, c.Radius(), (p.X(), p.Y())))
    return found


def distance(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


def grouped(cyls):
    """The faces of one hole together: OCC may split a cylinder at its seam."""
    groups = {}
    for f, r, (x, y) in cyls:
        key = (round(x, 2), round(y, 2), round(r, 3))
        groups.setdefault(key, []).append(f)
    return [((x, y), r, cq.Compound.makeCompound(fs)) for (x, y, r), fs in groups.items()]


disc = cq.importers.importStep(OUT + out_subdir("filter_disc") + "filter_disc.step").val()
body = cq.importers.importStep(OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step").val()

cyl_disc = cylinders(disc)
centred = [c for c in cyl_disc if math.hypot(*c[2]) < 0.01]
outer_r = max(r for _, r, _ in centred)
outer = cq.Compound.makeCompound([f for f, r, _ in centred if abs(r - outer_r) < 1e-6])
holes = grouped([c for c in cyl_disc if math.hypot(*c[2]) > 10.0])
holes.sort(key=lambda h: math.atan2(h[0][1], h[0][0]) % (2*math.pi))

n = len(holes)
T("filter disc: the holes are there", n >= 2, "%d holes found" % n)
if n >= 2:
    radii = [math.hypot(*c) for c, _, _ in holes]
    diam = [2*r for _, r, _ in holes]
    T("filter disc: the holes are on one circle",
      max(radii) - min(radii) < 0.01,
      "circle radius %.3f..%.3f mm, holes Ø%.3f..Ø%.3f" % (min(radii), max(radii), min(diam), max(diam)))

    rims = [distance(f, outer) for _, _, f in holes]
    T("filter disc: every hole is closed towards the rim",
      min(rims) >= RIM_MIN,
      "rim material %s mm (floor %.1f; photo of the real disc ~3.2)"
      % ("/".join("%.2f" % v for v in rims), RIM_MIN))

    webs = [distance(holes[i][2], holes[(i + 1) % n][2]) for i in range(n)]
    T("filter disc: the web between holes is the one observed",
      all(abs(w - D["W_web_filter"]) <= WEB_TOL for w in webs),
      "webs %s mm, observed %.2f (estimated by hand)"
      % ("/".join("%.2f" % w for w in webs), D["W_web_filter"]))

    # the optical hole of the body: the off-centre cylinder of the body
    # nearest to the first filter hole, which is the one in position
    first = min(holes, key=lambda h: math.hypot(h[0][0] + 100.0, h[0][1]))
    body_off = [(r, c) for _, r, c in cylinders(body) if math.hypot(*c) > 10.0 and r > 15.0]
    if body_off:
        rb, cb = min(body_off, key=lambda rc: math.hypot(rc[1][0] - first[0][0], rc[1][1] - first[0][1]))
        dc = math.hypot(cb[0] - first[0][0], cb[1] - first[0][1])
        T("filter disc: the filter in position is on the body's optical hole",
          dc < 0.01,
          "filter hole at (%.3f, %.3f), body optical hole Ø%.2f at (%.3f, %.3f), %.3f mm apart"
          % (first[0][0], first[0][1], 2*rb, cb[0], cb[1], dc))
    else:
        T("filter disc: the filter in position is on the body's optical hole", False,
          "no off-centre hole found in filter_wheel_body.step")

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
