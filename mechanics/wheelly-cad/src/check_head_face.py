# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The head face is one flat face, box and collar together.

Why it exists. The collar is cut on the plane of the outer face of the box
head - the flat face that carries the USB and the GX12 - because that face is
a candidate to put on the print bed. A face to print on is only a face if it is ONE plane: a collar that ran a
few tenths past it would lift the part off the bed on a ridge, one that
stopped short would leave a step. Neither shows as an interference, and both
can come back the day the head or the collar moves.

What it measures, on box_collar.step and the two gaskets: nothing stands past
the plane, and on the plane there is exactly one flat face, which reaches both
into the collar (inside R_out_collar) and into the box (outside it).

Outside the audit, so that breaking it on purpose costs seconds.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D
import electronics as E

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
PART = OUT + "box_collar.step"

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


part = cq.importers.importStep(PART).val()
beyond = (cq.Solid.makeBox(300.0, 200.0, 200.0, cq.Vector(0.0, E.T_HEAD_OUT + 0.01, -100.0))
         .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))
protruding = {n: s.intersect(beyond).Volume() for n, s in
          (("box_collar", part),
           ("front_gasket", cq.importers.importStep(OUT + "front_gasket.step").val()),
           ("rear_gasket", cq.importers.importStep(OUT + "rear_gasket.step").val()))}
T("head face: nothing stands past the plane of the head",
  all(v < 1e-3 for v in protruding.values()),
  ", ".join("%s %.3f mm3" % (n, v) for n, v in protruding.items() if v >= 1e-3))

V = cq.Vector(E.V[0], E.V[1], 0)
faces = [f for f in part.Faces()
         if f.geomType() == "PLANE" and abs(f.normalAt(f.Center()).dot(V)) > 0.9999
         and abs(f.Center().x*E.V[0] + f.Center().y*E.V[1] - E.T_HEAD_OUT) < 0.01]


def on_plane(r, z):
    """A point of the plane at radius r from the wheel axis, height z."""
    s = math.sqrt(r*r - E.T_HEAD_OUT**2)
    x, y = E.xy(s, E.T_HEAD_OUT)
    return cq.Vertex.makeVertex(x, y, z)


# one point in the collar (mid-height of the collar band), one in the box
Rc = D["R_out_collar"]
in_collar = on_plane(Rc - 3.0, D["H_body"]/2)
in_box = on_plane(Rc + 15.0, D["Z_floor_box"] + 10.0)
touches = lambda f, v: f.distance(v) < 1e-4
T("head face: one flat face across the box and the collar",
  len(faces) == 1 and touches(faces[0], in_collar) and touches(faces[0], in_box),
  "%d faces on the plane%s" % (len(faces), "" if not faces else
                               "; collar %s, box %s" % (any(touches(f, in_collar) for f in faces),
                                                        any(touches(f, in_box) for f in faces))))

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
