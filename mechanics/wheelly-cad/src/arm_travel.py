# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The travel of the arm: how far it really turns, and why exactly that far.

The travel was once not a datum. In the checks there was
a sweep written by hand - four angles, `(-3, -1.5, 1.5, 3)` - that followed
from nothing, and the other things were checked AGAINST it; the sweep instead
was checked against nobody. Measuring the real part it turned out that at
-1.5 degrees the arm already touches the collar, and that no check noticed.

The sense of the mechanism, measured by turning the group about the pivot:

  - at 0 degrees the TPU ring is EXACTLY TANGENT to the disc. It is not by
    chance: Cd_motor is R_disc + D_clutch/2 to the thousandth, that is the
    tangency is written in the chain of dimensions. At 0 degrees therefore
    the clutch does not push: zero force;
  - going NEGATIVE the arm comes closer to the disc and squeezes the rubber.
    It is the direction the spring takes it, and also the direction the arm
    moves in as the TPU wears: less rubber, more rotation to keep the same
    push;
  - going POSITIVE the arm moves away from the disc and compresses the spring.

The ratio is steep: **one degree of arm is worth about one millimetre of
squeeze**. So degrees, here, are big, and the degree and a half that
separated the tangency from the collar was not margin: it was the whole
working, operating point included.

Nothing is chosen in here: it converts. The choices are in the parameters -
how much to squeeze the rubber, how much wear to follow, how much margin to
leave - and this module says which angle they correspond to, really turning
the motor axis about the pivot instead of trusting a linearisation.
"""
import math


def _motor_axis(D, degrees):
    """Where the motor axis is after turning the arm by `degrees`."""
    Px, Py = D["R_disc"], D["Off_pivot"]
    Mx, My = D["Cd_motor"], 0.0
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return (Px + (Mx-Px)*c - (My-Py)*s,
            Py + (Mx-Px)*s + (My-Py)*c)


def approach(D, degrees):
    """How far the clutch goes into the disc, in mm, at that angle.

    Positive = the rubber is squeezed; negative = the clutch is off the disc.
    """
    mx, my = _motor_axis(D, degrees)
    tangency = D["R_disc"] + D["D_clutch"]/2
    return tangency - math.hypot(mx, my)


def angle_for(D, mm):
    """The angle that produces that approach. It is searched, not linearised."""
    lo, hi = -20.0, 20.0
    for _ in range(60):
        mid = (lo+hi)/2
        if approach(D, mid) < mm: hi = mid
        else: lo = mid
    return (lo+hi)/2


def passage(D, samples=41):
    """The recess the collar must have for the arm to pass through it.

    Returns (angle0, angle1, inner_radius) about the centre of the disc.

    It is not a choice of shape: it is the envelope of what the arm really
    sweeps, widened by Cl_passage_arm. Before, there were three numbers here
    written by hand - `sett(-22, 54, Rc-0.5, ...)` - that did not follow from
    the travel, and in fact they were generous in angle while in radius they
    were a millimetre and a half short: the arm, turning towards the disc,
    dived under the edge of the recess and touched the flange. The defect was
    all in that millimetre and a half, not in the angles.

    It works on the outline in plan and not on the solid: so the function
    runs with --solo-dxf too, and the collar does not have to wait for the
    arm to be exported.
    """
    import outline_arm as _OA
    Px, Py = D["R_disc"], D["Off_pivot"]
    outl = _OA.outline(D)
    down, up = limits(D)
    Re, Rif = D["R_out_collar"], D["R_in_flange_collar"]
    rmin, amin, amax = 1e9, 1e9, -1e9
    for k in range(samples):
        g = down + (up-down)*k/(samples-1)
        a = math.radians(g); c, s = math.cos(a), math.sin(a)
        for x, y in outl:
            X = Px + (x-Px)*c - (y-Py)*s
            Y = Py + (x-Px)*s + (y-Py)*c
            r = math.hypot(X, Y)
            if r > Re + 2 or r < Rif:
                continue
            rmin = min(rmin, r)
            ang = math.degrees(math.atan2(Y, X))
            amin, amax = min(amin, ang), max(amax, ang)
    clearance = D["Cl_passage_arm"]
    dang = math.degrees(clearance/rmin)
    return (amin - dang, amax + dang, rmin - clearance)


def limits(D):
    """The two ends of the travel, in degrees: (towards the disc, towards the
    spring).

    The first is the one that matters for the working: the arm must be able
    to get there FREELY, because that is where the spring takes it as the
    rubber wears. It is not an end stop: it is the point beyond which there
    should be no need to go, and up to which there must be nothing.

    The second is a real end stop, which is to be made: on that side today
    the arm is free until the clutch hits the box.
    """
    down = angle_for(D, D["Approach_travel_arm"])
    up = angle_for(D, -D["Open_travel_arm"])
    return (down, up)
