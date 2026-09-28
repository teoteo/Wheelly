# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The arc around the motor: is it there, is it a wall, and does it stay clear?

Why it exists. The mechanical lobe of the box no longer ends in a radial end
wall with a setback in front of it, but in an arc centred on the motor axis, tangent to the back on the shaft line, running round
the motor down to the collar. Three things can go wrong with that, and none of
them shows as an interference between solids:

  - the arc is not there, or not where it should be (the lobe is still full);
  - the arc is there but it is a SKIN with nothing behind it, or a solid block
    with no compartment inside - the construction offsets outer face and void
    separately, and either can go missing without the part becoming invalid;
  - the arc is too tight, and the motor, the arm or the clutch rub on it at one
    end of the arm's travel. Clearances at rest say nothing about that.

What it measures, and on what. On box_collar.step, the part that gets printed
- not on the two halves in out/references/, which turned out to lack 9.3 cm3
of cuts made after the union. The outline and the wall are probed
on the solid; the clearance is the true distance between the arc wall and the
moving parts - the arm, the maker's motor, the clutch - rotated about the pivot
over their whole travel.

Runs outside check_audit.py on purpose: it takes seconds, so breaking it on
purpose to see it fail costs seconds too.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D
import arm_travel as CB

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out") + os.sep
MOTOR = os.path.join(os.path.dirname(HERE), "others", "14HS10-0404S.STEP")

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


MX, MY = D["Cd_motor"], 0.0
RA, W = D["R_arc_back_box"], D["Th_walls_box"]
Ro, Rc = D["R_out_box"], D["R_out_collar"]
ZT = D["Z_floor_box"]

part = cq.importers.importStep(OUT + "box_collar.step").val()


def solid_at(r, a, z):
    p = cq.Vector(r*math.cos(math.radians(a)), r*math.sin(math.radians(a)), z)
    return part.intersect(cq.Solid.makeSphere(0.08, p)).Volume() > 1e-12


def arc(a):
    """Where the arc is expected at angle a: its far point from the wheel centre."""
    c = MX*math.cos(math.radians(a))
    d = RA*RA - MX*MX + c*c
    return c + math.sqrt(d) if d > 0 else None


def edge(a, z):
    """The radius at which the material ends, measured on the solid. The inner
    end of the bisection starts INSIDE the wall, where there is material by
    construction: starting in the compartment, the bisection would begin in the
    void and report "nothing" on a sound part (the same trap found three times
    in this project)."""
    lo, hi = arc(a) - W/2, Ro + 10.0
    if not solid_at(lo, a, z):
        return None
    for _ in range(22):
        m = (lo + hi)/2
        if solid_at(m, a, z): lo = m
        else: hi = m
    return lo


# The angle at which the arc reaches the collar. Below it the lobe has ended.
_x = (Rc*Rc - RA*RA + MX*MX)/(2*MX)
A_END = -math.degrees(math.acos(_x/Rc))
# Sampled from two degrees past the collar to just short of the grip: around
# the shaft line the grip opens the wall at mid height, and its own check
# (check_grip.py) looks after it. Two heights, one low in the motor bay and
# one just under the roof, because the wall is built as a single extrusion and
# a construction fault would show at one height only if it came from one of
# the slabs.
A_GRIP = D["Halfw_grip_box"] + 2.0
ANGLES = [A_END + 2.0 + k*((-A_GRIP) - (A_END + 2.0))/6 for k in range(7)]
# The upper one sits a millimetre below the START of the roof chamfer, not
# under the roof: above it the outline slopes in by design (Ch_roof_box), and
# probing there the arc read "nothing" on a sound part.
HEIGHTS = (ZT + W + 2.0, D["Z_shoulder_box"] + W - D["Ch_roof_box"] - 1.0)

import outline_motor as _SMa
import electronics as _Ea
_SM_ears = _SMa.hatch_ears(0.0, W)
E_ZSCREWS_TOP = _Ea.Z_SCREWS + W + 0.01          # the top of the raised floor
off_arc, no_wall, no_compartment = [], [], []
for a in ANGLES:
    for z in HEIGHTS:
        e = arc(a)
        m = edge(a, z)
        if m is None or abs(m - e) > 0.3:
            off_arc.append("%+.1f deg z %.1f: %s instead of %.2f"
                         % (a, z, "nothing" if m is None else "%.2f" % m, e))
            continue
        if not solid_at(m - W/2, a, z):
            no_wall.append("%+.1f deg z %.1f" % (a, z))
        # the raised floor over the hatch-cover ears is there on purpose:
        # it carries the inserts, and it stands W high over the floor, where the low probe is. A probe over an ear, as the
        # generator raises it, is not asked for the compartment
        _r = (Rc + m - W)/2
        _px, _py = _r*math.cos(math.radians(a)), _r*math.sin(math.radians(a))
        if z < E_ZSCREWS_TOP and any(x0 - 0.5 <= _px <= x1 + 0.5 and y0 - 0.5 <= _py <= y1 + 0.5
                                  for x0, x1, y0, y1 in _SM_ears):
            continue
        if solid_at(_r, a, z):
            no_compartment.append("%+.1f deg z %.1f" % (a, z))
T("arc: the back follows the arc about the motor axis", not off_arc,
  "; ".join(off_arc[:3]))
T("arc: along the arc there is a wall, not a skin", not no_wall,
  "no wall at: " + ", ".join(no_wall))
T("arc: behind the wall the compartment is still there", not no_compartment,
  "solid at: " + ", ".join(no_compartment))

# Nothing left outside the arc: past the collar junction the whole lobe is
# gone, and between it and the grip nothing stands a millimetre beyond the arc.
# ...except the fillet between the collar and the arc on the -y side, there on
# purpose: a probe inside the fillet's corner - outside
# the collar and the arc, inside the fillet circle's outer side - is not asked
from parameters import collar_arc_fillet as _rca
_fcx, _fcy, _ft1, _ft2 = _rca()


def _in_fillet(r, a):
    """Inside the fillet's corner: the region the generator fills - within the
    polygon (axis, t1, fillet centre, t2, motor axis), outside the collar and
    the arc, outside the fillet circle."""
    from matplotlib.path import Path as _Path
    x, y = r*math.cos(math.radians(a)), r*math.sin(math.radians(a))
    quad = _Path([(0.0, 0.0), _ft1, (_fcx, _fcy), _ft2, (D["Cd_motor"], 0.0)])
    return (quad.contains_point((x, y))
            and math.hypot(x, y) >= D["R_out_collar"] - 0.5
            and math.hypot(x - D["Cd_motor"], y) >= D["R_arc_back_box"] - 0.5
            and math.hypot(x - _fcx, y - _fcy) >= D["R_fillet_collar_arc"] - 0.01)


left_over = []
for a in (A_END - 8.0, A_END - 4.0, A_END - 1.0):
    for r in (Rc + 2.0, (Rc + Ro)/2, Ro - 2.0):
        for z in HEIGHTS:
            if _in_fillet(r, a):
                continue
            if solid_at(r, a, z):
                left_over.append("%+.1f deg r %.1f z %.1f" % (a, r, z))
for a in ANGLES:
    for z in HEIGHTS:
        if solid_at(arc(a) + 1.0, a, z):
            left_over.append("%+.1f deg, 1 mm past the arc, z %.1f" % (a, z))
T("arc: nothing is left of the lobe beyond the arc", not left_over,
  "; ".join(left_over[:4]))

# The clearance, on the solid, over the whole travel of the arm. The band is
# the part of the box within reach of the arc wall: the lobe on the side away
# from the pivot, between the floor slab and the roof slab, and short of the
# grip. Floor, roof, grip and collar stay out of it, or the nearest thing
# would be the floor under the motor and the number would say nothing about
# the arc.
#
# The band is cut by HEIGHT and ANGLE, never by distance from the shaft. The
# first version took away the disc of the compartment, RA - W - 0.5 about the
# shaft - and so it could not see an arc that had moved in: breaking it on
# purpose with the wall three millimetres tighter, the clutch still measured
# 2.95 instead of 0.5, because the intruding material lay exactly inside the
# disc that had been removed.
#
# THREE MILLIMETRES, not the six the arc was sized with: six is at rest, and
# the arm swings the motor about the pivot by up to two millimetres at the
# shaft. The clutch is the one that comes closest - 3.5 measured - and its TPU tread is the one part of the three that can bulge.
CLEARANCE_MIN = 3.0


def _sector(a0, a1, r0, r1, z0, h):
    p = lambda r, a: (r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))
    return (cq.Workplane("XY").workplane(offset=z0).moveTo(*p(r1, a0))
            .threePointArc(p(r1, (a0 + a1)/2), p(r1, a1)).lineTo(*p(r0, a1))
            .threePointArc(p(r0, (a0 + a1)/2), p(r0, a0)).close().extrude(h).val())


_z0, _z1 = ZT + W + 0.2, D["Z_shoulder_box"] - 0.2
band = part.intersect(_sector(A_END - 10.0, -A_GRIP, Rc + 0.5, Ro + 5.0, _z0, _z1 - _z0))
down, up = CB.limits(D)
A0 = cq.Vector(D["R_disc"], D["Off_pivot"], 0)
A1 = cq.Vector(D["R_disc"], D["Off_pivot"], 1)
moving = {"arm": cq.importers.importStep(OUT + "arm.step").val(),
          "clutch": cq.importers.importStep(OUT + "clutch_assembly.step").val()}
if os.path.exists(MOTOR):
    moving["motor"] = (cq.importers.importStep(MOTOR).val()
                       .rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
                       .translate(cq.Vector(MX, MY, -D["Z_face_motor"])))
else:
    ko.append("%-52s %s" % ("arc: the maker's motor is in the model", "missing " + MOTOR))
for name, sol in moving.items():
    d = min(band.distance(sol.rotate(A0, A1, down + (up - down)*k/6)) for k in range(7))
    T("arc: the %s stays clear of the arc wall over its travel" % name,
      d >= CLEARANCE_MIN, "%.2f mm (at least %.1f)" % (d, CLEARANCE_MIN))

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
