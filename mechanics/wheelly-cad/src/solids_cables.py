# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The cables, as solids.

Why as solids and not as lines: a cable must be able to INTERPENETRATE
something and show it. As long as the model had only the cable passages and
not the cables, no check could say whether those passages were any use - and
it is the same blindness as the body drawn without its little window and the
electronics compartment without the perfboard.

The route is DECLARED, not optimistic. A cable does not pass through the
corner, is not born already bent at the exit of a connector, and to turn it
wants room AROUND the bend and not only in front of it. So here we write the
points it passes through, build the tube, and then MEASURE: the bend radius
along the whole length, and the interpenetration with everything else.

The constraint that rules is not the diameter but the bend radius. A cable
that fits but must be bent tighter than it can take is a cable that does not
fit: it gets stripped, breaks by fatigue, or pushes back and misaligns what it
is attached to.

WHEN THE CABLE IS THREADED IN, because a route that exists with the machine
assembled but cannot be followed while assembling is no use at all. The roof
has an OPEN SLOT on its inner edge: the cable goes in from the side, with the
connector already wired, BEFORE bringing the box up to the collar. The box
arrives from the side, stepping over the flanges, and carries the cable with
it; with the box fitted the collar closes the open edge of the slot and the
cable stays retained. To remove it, the box comes off first. Then the panel
with the board: the sensor wires come down through the opening and are
attached to the board OUTSIDE the box, with the panel in hand, so a connector
and a little slack are needed - inside the compartment there is room for the
loop, between the board and the roof. The panel is closed last. To take it
apart, the reverse: panel, connector, cable pulled out from above, box.

THE LIGHT. The opening is a new aperture and it must be said where it faces,
but it does not open a new path to the optics: it is at r 110, while the body
of the wheel ends at r 79. Above it faces the air between the collar and the
sensor bracket, below the motor compartment. And the motor compartment
already communicates with the body through the clutch aperture, which is
there by necessity because the friction wheel has to reach the disc - besides
already having the GX12 hole and the USB-C slot. That compartment is not
light-tight by design: the opening adds a hole to it, not the first one. The
true barrier towards the filters remains the collar gasket, at r 67-70, and
the opening is forty millimetres outside it.
"""
import math, os, sys
import os
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT + "references", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
from parameters import D, out_subdir
import electronics as E


def pol(r, ang, z):
    a = math.radians(ang)
    return (r*math.cos(a), r*math.sin(a), z)


# --------------------------------------------------------------------------
# THE SENSOR CABLE, from the cable clamp on the bracket to above the board.
#
# The points, and why they are where they are:
#   1. it leaves the cable clamp on the bracket, at r 49 on the cable arm,
#      which points at 50 degrees. The first stretch is STRAIGHT and radial: a
#      cable just out of a cable clamp cannot bend straight away.
#   2. it steps over the rear flange of the collar, which ends at z 26: it
#      passes over it with half its cross-section of clearance.
#   3. it crosses the roof of the compartment in the open slot, OBLIQUELY,
#      staying in the plane of the bracket's arm (no sideways bends):
#      arriving almost flat over the paddle, to become vertical right after
#      the edge of the roof it would have to bend tighter than its minimum
#      radius. The slot is long on purpose.
#   4. inside the compartment it stops ABOVE the board: from there down only
#      the four stripped wires go, which do not pull and have no minimum
#      radius. With the earlier electronics compartment the cable had to cross
#      a passage between the two compartments that did not close; now the
#      electronics is in the same compartment, and below the slot there is the
#      board.
# The stretch that goes down is not written by hand: it is an ARC of radius
# R_ARC, tangent to the flat stretch, which starts at R_ARC_START. The two
# numbers follow from the two edges to step over with half the cable's
# cross-section of clearance - the tip of the bracket's paddle (r 85.3,
# z 31.1) and the edge of the collar (r 86, z 28) - and from the cable's
# minimum radius, with a little margin: a spline passed through the points of
# a circle wobbles below the true radius. With the points written by hand the
# minimum radius came out 15.2; with the arc of 26 sampled every 15 degrees,
# 21.5. The arc is sampled densely.
R_ARC, R_ARC_START, Z_PLANE = 28.0, 80.0, 34.6
# WHERE THE SHEATH ENDS. They were the numbers 4.0 and 1.0 written by hand,
# and the day the floor rose by six and a half millimetres - with the whole
# electronics stack behind it - the sheath found itself inside the driver's
# heatsink, by 68 mm3. Now it follows from it: the sheath stops above the
# tallest thing on the board, and below go the stripped wires, which do not
# pull.
_Z_END = E.Z_DRIVER_TOP + D["Cl_cable_driver"]
_ANG_DESCENT = D["Ang_opening_cable_box"]


def _arc(phi):
    return pol(R_ARC_START + R_ARC*math.sin(math.radians(phi)), _ANG_DESCENT,
               Z_PLANE - R_ARC*(1 - math.cos(math.radians(phi))))


SENSOR_ROUTE = [
    pol(49.0, _ANG_DESCENT, 35.7),   # cable clamp on the bracket: it leaves straight
    pol(62.0, _ANG_DESCENT, 35.2),
    pol(72.0, _ANG_DESCENT, 34.8),   # almost flat over the bracket's paddle
    _arc(0.0)] + [_arc(7.5*k) for k in range(1, 13)] + [
]
# THE SHEATH ENDS WHERE THE ARC ENDS, and not one point lower. Before, there
# were two points written by hand here, z 4.0 and 1.0: they brought the sheath
# lower when the floor was at -38 and the board was far away. Once the floor
# rose by six and a half millimetres, those two points ended up INSIDE the
# driver's heatsink (68 mm3) - and replacing them with two derived points was
# not enough: the arc already goes below them, so the cable went down, came
# back up and went down again, and the bend radius collapsed from 22 to 0.1. A
# zigzag the radius check saw straight away.
#
# The tail is not needed: the arc already ends above the driver, and below go
# the stripped wires, which do not pull and have no minimum radius.
_Z_SHEATH = _arc(90.0)[2]
if _Z_SHEATH < E.Z_DRIVER_TOP + D["Cl_cable_driver"]:
    raise SystemExit(
        "the cable's sheath ends at z %.2f and the driver's heatsink reaches\n"
        "%.2f: the sheath would run into it. The descending arc must stop\n"
        "higher - R_ARC or Z_PLANE - or else the electronics stack has\n"
        "risen too much."
        % (_Z_SHEATH, E.Z_DRIVER_TOP))


def tube(points, diameter):
    """The cable: a tube along the spline through the declared points."""
    vs = [cq.Vector(*p) for p in points]
    spine = cq.Edge.makeSpline(vs)
    wire = cq.Wire.assembleEdges([spine])
    d0 = (vs[1] - vs[0]).normalized()
    # any vector perpendicular to the start
    u = cq.Vector(0, 0, 1).cross(d0)
    if u.Length < 1e-6:
        u = cq.Vector(1, 0, 0).cross(d0)
    u = u.normalized()
    plane = cq.Plane(origin=vs[0], xDir=u, normal=d0)
    prof = cq.Workplane(plane).circle(diameter/2).val()
    return cq.Workplane(obj=cq.Solid.sweep(prof, [], wire, True)), wire


def min_radius(wire, steps=400, margin=0.04):
    """The tightest bend radius along the wire, measured on three sliding
    points: it is the number that decides whether the route can be followed.

    The first and the last `margin` of the route are not counted, and it is
    not to make the numbers come out right. A spline passed through points
    curls a little at its ends because of how it is made, not because of how
    the cable is made; and on the real part the two ends are held straight by
    what the cable is attached to - a connector, a cable clamp, a terminal
    block. Faults tried: a route point pulled off in the middle is seen all
    the same, because it falls inside the measured stretch.
    """
    pts = [wire.positionAt(i/steps) for i in range(steps+1)]
    worst, where = 1e9, 0.0
    i0, i1 = int(steps*margin), int(steps*(1-margin))
    for i in range(max(1, i0), min(len(pts)-1, i1)):
        a = (pts[i]-pts[i-1]).Length
        b = (pts[i+1]-pts[i]).Length
        c = (pts[i+1]-pts[i-1]).Length
        s = (pts[i]-pts[i-1]).cross(pts[i+1]-pts[i]).Length/2
        if s > 1e-12:
            R = a*b*c/(4*s)
            if R < worst: worst, where = R, i/steps
    return worst, where


# --------------------------------------------------------------------------
# THE MOTOR CABLE AND THE SUPPLY CABLE ARE NOT HERE. Before, they did not
# close: they had to cross a passage between the mechanical compartment and
# the electronics one that pointed the wrong way. With the electronics in the
# motor compartment that passage no longer exists: the motor cable reaches the
# driver inside the same compartment, and the supply one comes down from the
# GX12, on the head, to the board just below it. They are short and have not
# been modelled.

_d = D["D_cable_sensor_measured"]
cable, axis = tube(SENSOR_ROUTE, _d)
cq.exporters.export(cable, OUT + out_subdir("sensor_cable") + "sensor_cable.step")
cq.exporters.export(cq.Workplane(obj=axis), OUT + out_subdir("sensor_cable_axis") + "sensor_cable_axis.step")
_rmin, _where = min_radius(axis)
print("sensor cable: Ø%.1f, %.0f mm long, minimum radius %.1f mm at %.0f%% of the route"
      % (_d, axis.Length(), _rmin, 100*_where))
print("   minimum allowed %.1f (4 x the diameter, TO BE CONFIRMED on the datasheet)"
      % D["R_curvature_min_cable"])
