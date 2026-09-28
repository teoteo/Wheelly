# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The silhouette of the motor seen from above, as a prism: the room it needs
to come down into the box straight from the top.

WHY IT EXISTS. The motor goes in first, dropped straight down from the top,
then the arm, then the screws. The door in the roof was
a rectangle written by hand, and it let the motor down only to z 24.5: below,
the collar ring stood across its path over 6 mm. Nothing checked it, because
nothing checked the motor's way
in at all.

WHY FROM THE MAKER'S STEP. The motor is bought: reading it from the STEP
means the cut follows the motor that is really there - the same file, placed
the same way, as the assembly (solids_assembly.py).

BUT NOT ITS LEADS. The STEP draws the four motor leads as four straight rigid
bars, 1 mm square, sticking out 17.6 mm to one side at the bottom of the motor
(y 18..35.6). They are wires: they bend out of the way when the motor goes in.
Taken into the silhouette, they opened a notch in the roof beyond the door,
and the cover plate grew a tab to fill it - a tab with no reason to exist,
since the printed version closed well without it. So the
motor is first clipped to the column of its square flange, Side_motor wide,
plus half a millimetre: the body, the boss and the shaft, not the wires.

HOW. Horizontal sections of the solid every SLICE mm, each extruded one step
and fused: the union is the silhouette to within the step. Then the prism is
grown by `clearance` with eight shifted copies - on the axes and on the diagonals -
which is a Minkowski sum with an octagon: never less than `clearance` in any
direction, and a few hundredths more at the corners. It runs from the bottom
of the motor up to well above the roof.
"""
import functools
import math
import os

import cadquery as cq

from parameters import D

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTOR_STEP = os.path.join(os.path.dirname(HERE), "others", "14HS10-0404S.STEP")
SLICE = 1.0
TOP = 100.0             # the prism goes up to here: above everything


def motor():
    """The maker's motor in its place, as solids_assembly.py puts it: half a turn
    about X (in its file the flange is at z 0 with the shaft towards -z), then
    onto the motor face."""
    return (cq.importers.importStep(MOTOR_STEP)
            .rotate((0, 0, 0), (1, 0, 0), 180)
            .translate((D["Cd_motor"], 0.0, -D["Z_face_motor"]))).val()


def body():
    """The motor without its leads: clipped to the column of the square flange.

    WHERE THE COLUMN STOPS IS READ FROM THE STEP, on the side without leads:
    the body reaches 17.61 from the axis towards -y. The leads start right at
    the body face on the +y side (17.62), so any margin written by hand lets
    their roots in. With half a millimetre they grew, after Cl_entry_motor,
    into a notch 1.5 mm deep on the +y edge of the hatch under the motor, and
    the notch has no reason to exist: the leads bend. A thousandth past
    the -y face keeps the whole body and not the wires."""
    m = motor()
    h = (-m.BoundingBox().ymin) + 0.001
    column = cq.Solid.makeBox(2*h, 2*h, 400.0, cq.Vector(D["Cd_motor"] - h, -h, -200.0))
    return m.intersect(column)


@functools.lru_cache(maxsize=None)
def _base():
    m = body()
    b = m.BoundingBox()
    slices = None
    z = b.zmin + SLICE/2
    while z < b.zmax:
        for f in cq.Workplane(obj=m).section(z).faces().vals():
            p = (cq.Workplane(obj=f.translate(cq.Vector(0, 0, b.zmin - z)))
                 .wires().toPending().extrude(TOP - b.zmin).val())
            slices = p if slices is None else slices.fuse(p)
        z += SLICE
    if slices is None:
        raise SystemExit("motor silhouette: no section - is the STEP %s empty?" % MOTOR_STEP)
    return slices.clean(), b.zmin


def silhouette(clearance):
    """The prism of the silhouette grown by `clearance`, from the bottom of the
    motor up to TOP, as a Workplane ready to cut or to intersect."""
    base, _ = _base()
    s = base
    if clearance > 0:
        for k in range(8):
            t = 2*math.pi*k/8
            s = s.fuse(base.translate(cq.Vector(clearance*math.cos(t), clearance*math.sin(t), 0)))
        s = s.clean()
    return cq.Workplane(obj=s)


def motor_bottom():
    """The z of the bottom of the motor in its place."""
    return _base()[1]


def travel_envelope(clearance, z0, z1, samples=9):
    """The silhouette grown by `clearance`, swept over the whole travel of the
    arm (arm_travel.limits), as a prism from z0 to z1.

    WHY. The motor rides on the arm, and the arm turns about the pivot: at the
    two ends of its travel the motor has moved 1.5..1.8 mm sideways, more than
    Cl_entry_motor. The hatch under the motor was first cut on the motor at
    rest, and its screw ears - which start at the edge of the hatch and rise
    to z -26.5, above the bottom of the motor at -27.5 - met the moving motor
    for 55 mm3 in the box and 12 in the cover. That is the requirement: the
    hatch is fine only if the motor can still move when the arm moves. Cut on the envelope, whatever stands outside the hatch is outside
    the motor's way, at every angle of the travel, by construction.

    The prism is a straight extrusion of the silhouette, so a horizontal
    section is enough: it is taken, turned about the pivot at `samples`
    angles between the two ends, and the turned sections are fused. Between
    two samples the motor moves by a few hundredths off the chord."""
    import arm_travel as _AT
    down, up = _AT.limits(D)
    zs = motor_bottom() + SLICE
    faces = silhouette(clearance).section(zs).faces().vals()
    P = cq.Vector(D["R_disc"], D["Off_pivot"], 0.0)
    tot = None
    for k in range(samples):
        g = down + (up - down)*k/(samples - 1)
        for f in faces:
            fr = f.rotate(P, P + cq.Vector(0, 0, 1), g).translate(cq.Vector(0, 0, z0 - zs))
            p = cq.Solid.extrudeLinear(fr.outerWire(), fr.innerWires(), cq.Vector(0, 0, z1 - z0))
            tot = p if tot is None else tot.fuse(p)
    return cq.Workplane(obj=tot.clean())


@functools.lru_cache(maxsize=None)
def hatch():
    """The hatch under the motor, in plan: the rectangle round the travel
    envelope (travel_envelope) grown by Cl_hatch_motor, its corner radius, and
    the two screws of its cover. Read by the generator and by purchased.py, so
    the screws in the assembly are the ones in the part.

    A RECTANGLE AND NOT THE ENVELOPE ITSELF: the envelope is nine octagon-grown
    silhouettes fused, and its edge came out scalloped - an ugly slot, and the
    hatch should be clean. The rectangle is
    the envelope's bounding box, with the largest corner radius, in half
    millimetres, that still holds the whole envelope: the rounded corners are
    what keeps it off the arc wall round the motor.

    THE SCREWS: one beyond the outer side and one beyond the -y side, on the
    midlines. +y is where the motor leads come out, and towards the wheel axis
    the hatch runs into the inner wall. Each screw stands so that its insert
    keeps 1.2 mm of boss towards the hatch; the ear round it is sized on the
    countersunk head, not on the boss - boss-wide, with the hatch widened for
    the travel, the outer ear reached 0.6 mm from the outside of the box.

    Returns dict(xc, yc, lx, ly, r, re, screws=[(x, y, side)])."""
    inv = travel_envelope(D["Cl_hatch_motor"], 0.0, 1.0)
    b = inv.val().BoundingBox()
    xc, yc, lx, ly = (b.xmin + b.xmax)/2, (b.ymin + b.ymax)/2, b.xlen, b.ylen
    r = 0.0
    for k in range(1, 60):
        rk = 0.5*k
        if rk >= min(lx, ly)/2 - 0.5:
            break
        ret = (cq.Workplane("XY").workplane(offset=-1.0).center(xc, yc).rect(lx, ly)
               .extrude(3.0).edges("|Z").fillet(rk))
        if inv.cut(ret).val().Volume() > 1e-4:
            break
        r = rk
    re = D["D_head_countersunk_M3"]/2 + 0.3 + D["Th_min_wall_printing"]
    m = D["D_hole_insert_M3"]/2 + 1.2
    screws = [(b.xmax + m, yc, "x"), (D["Cd_motor"], b.ymin - m, "y")]
    return dict(xc=xc, yc=yc, lx=lx, ly=ly, r=r, re=re, screws=screws)


def hatch_ears(g=0.0, grow=0.0):
    """The ears of the two hatch-cover screws in plan, (x0, x1, y0, y1) each,
    in the order of hatch()["screws"]: from 1 mm inside the hatch out round the
    countersunk head. `g` shrinks them on their free sides (the cover's
    clearance), `grow` grows them (the raised floor over them, one wall
    wider). Written once: the generator cuts and raises them, and
    check_arc_back must know where the raised floor is on purpose."""
    B = hatch()
    re, x1b, y0b = B["re"], B["xc"] + B["lx"]/2, B["yc"] - B["ly"]/2
    out = []
    for xv, yv, side in B["screws"]:
        if side == "x":
            out.append((x1b - 1.0, xv + re + grow - g,
                        yv - re - grow + g, yv + re + grow - g))
        else:
            out.append((xv - re - grow + g, xv + re + grow - g,
                        yv - re - grow + g, y0b + 1.0))
    return out
