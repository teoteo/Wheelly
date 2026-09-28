# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Box with two compartments: mechanical (motor, arm, spring, clutch) and electronic.

HOW IT GOES ON THE MACHINE: **as it is modelled**, that is with the floor of
the mechanical compartment (z -38, the one under the motor) on the bed. With
the electronics in the compartment, the shorter box and the opening of the
panel, the first layer measures 4,723 mm2; the numbers below are for the
earlier shape. Measured on the solid, overhangs beyond 45 degrees and contact
with the bed, in the four orientations tried:

    as modelled         12,072 mm2 of overhangs, 7,399 mm2 on the bed
    upside down         18,853 mm2, 488 mm2 on the bed
    on its side, back   13,457 mm2, ZERO contact (it touches along a line)
    on its side, open   20,231 mm2, ZERO contact

It is not only the total: as modelled the first layer is a full sector of
7,400 mm2, whereas upside down the box stands on its six ears. And the
overhangs that remain are almost all just two pieces - the roof of the
mechanical compartment (6,979 mm2) and that of the electronic compartment
(3,014), 83% of the total - which are INNER surfaces: nobody sees the marks of
the supports there and they seal nothing. It is exactly the place where
breakaway supports are fine, and indeed it prints without soluble.

The chamfers on the outer edges were REMOVED to make way for a different
edge treatment: for now the edges are sharp. The overhang count above
is the one without chamfers.

THE SHOULDER ABOVE z 16 HAS BEEN HOLLOWED OUT, and the real saving is much
smaller than a first estimate suggested: **from 126 to 120 g, that is 5.3 cm3
and 6 grams**, not 25. The estimate counted the material up
there (27.5 cm3 above z 16, of which 23.3 beyond r 96) as if it disappeared:
the roof of the compartment does not disappear, it is LOWERED. What really
goes is only the band of wall between the old roof and the new one - outer
back and two heads, measured 8.3 cm3 - less what is put back on top to carry
the ears. The right number is only obtained by building the variant and
weighing it.

The gain that remains is real all the same, and it is not the weight: the
roof to be supported - 6,881 mm2, the largest island of the part - has come
down from z 26 to z 16, so the supports under it are ten millimetres
shorter, and the solid part of the box is ten millimetres lower. The overhang
numbers above are from before the hollowing; after it they are 12,089 and
18,791, and the island of the roof is the same, only ten millimetres lower."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
import cadquery as cq
from parameters import D

# The inner face of the shell GOES INTO the collar, it leaves it no clearance:
# the two are the same part, and two solids that just touch fuse into a
# compound of two pieces instead of into one solid (see Weld_box_collar).
Ri = D["R_out_collar"] - D["Weld_box_collar"]
Ro = D["R_out_box"]          # 130
W  = D["Th_walls_box"]      # 2.5
import electronics as E
# AM0, the end of the lobe away from the pivot, is set further down: it is
# derived from the arc around the motor.
# The other end is no longer an angle: it is the HEAD WALL, a plane
# perpendicular to the board with its outer face flush with the USB socket
# (electronics.py). The electronic compartment of before, 63..108, is gone:
# the electronics sit in here. The sector is built out to beyond the head and
# then cut on the plane.
AM1 = E.head_angle(Ri, "out") + 1.0
# ZT IS NO LONGER A NUMBER. It was -38 written by hand, and when the motor
# moved - turning the clutch over - it would not have followed
# it: the floor would have stayed where it was and the millimetres gained
# would have become empty space instead of height removed.
ZT, ZB   = D["Z_floor_box"], 28.5    # ends of the mechanical compartment

# ---------------- the arc around the motor ----------------
# Beyond the shaft the back does not run on at r 130: it turns into an arc
# CENTRED ON THE MOTOR AXIS, tangent to the back on the line from the wheel
# centre through the shaft, and it runs round the motor down to the collar
# (drawn from a sketch on the top view). It replaces the old
# setback, which came back to the back at -8 degrees along a curve centred on
# nothing in particular: the box now wraps only what it holds.
#
# HOW IT IS BUILT, and why not as a radius that varies with the angle, which is
# how the setback was done. Rays from the wheel centre beyond -19.5 degrees
# miss the arc altogether, so "the radius of the back at this angle" has no
# answer there; and a radius sampled every half degree is a polyline, not an
# arc. So every region that used to reach "the back minus an offset" is now the
# sector up to Ro - offset INTERSECTED with what the arc keeps at that same
# offset (_keep): the half plane on the pivot side, plus the disc about the
# shaft of radius R_arc_back_box - offset. Both boundaries are true arcs, and
# because the arc is tangent to the back, every offset is tangent too - the
# wall is born with its thickness, like the setback's was.
MX, MY = D["Cd_motor"], 0.0
RA = D["R_arc_back_box"]
# where the arc meets a circle of radius r about the wheel centre, on the side
# away from the pivot: the angle at which the lobe ends at that radius
def arc_angle(r, off=0.0):
    _ra = RA - off
    _x = (r*r - _ra*_ra + MX*MX) / (2*MX)
    return -math.degrees(math.acos(max(-1.0, min(1.0, _x / r))))


def _keep(off, z0=-100.0, h=200.0):
    """What the arc keeps, at `off` inside the outer skin: the half plane on the
    pivot side (y >= 0) plus the disc about the shaft of radius RA - off."""
    _half = cq.Solid.makeBox(400.0, 200.0, h, cq.Vector(-200.0, 0.0, z0))
    _disc = cq.Solid.makeCylinder(RA - off, h, cq.Vector(MX, MY, z0))
    return cq.Workplane(obj=_half.fuse(_disc))


def back_radius(a):
    """The radius of the back at that angle: 130, or the far point of the arc.
    Only meaningful from arc_angle(Ri) upwards - below it the lobe has ended.
    Used by the grip, which lives within a few degrees of the shaft line."""
    if a >= 0.0:
        return Ro
    _c = MX*math.cos(math.radians(a))
    _d = RA*RA - MX*MX + _c*_c
    return _c + math.sqrt(_d) if _d > 0 else Ri


# The sectors are built from AM0 and then cut by the arc, so AM0 is only a
# construction bound: it must lie beyond the point where the arc reaches the
# innermost radius any region starts from (Ri - 2, the void), plus a margin.
# It used to be -30, the radial end wall of the lobe; that wall is gone.
AM0 = arc_angle(Ri - 2.0) - 3.0


def inside(a0, a1, r0, off, z, h):
    """The sector from r0 out to `off` inside the outer skin, back AND arc."""
    return sett(a0, a1, r0, Ro - off, z, h).intersect(_keep(off))


def _pxy(r, a):
    return (r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))


def _arc(wp, r, a0, a1):
    """Runs along the arc of radius r from a0 to a1 with TRUE ARCS, broken into
    stretches of no more than ninety degrees because beyond half a turn an arc
    through three points is no longer determined."""
    n = max(1, int(math.ceil(abs(a1 - a0)/90.0)))
    for i in range(n):
        b0 = a0 + (a1 - a0)*i/n
        b1 = a0 + (a1 - a0)*(i + 1)/n
        wp = wp.threePointArc(_pxy(r, (b0 + b1)/2), _pxy(r, b1))
    return wp


def sett(a0, a1, r0, r1, z, h, step=0.5):
    """Sector between two radii. r0 and r1 can be numbers or functions of the
    angle: that is how the back steps in without needing cuts."""
    if not (callable(r0) or callable(r1)):
        # constant radii: TRUE ARCS, so the curved face is one face instead
        # of a fan of flat faces. The same reason written next to the
        # collar's sett() applies.
        wp = cq.Workplane("XY").workplane(offset=z).moveTo(*_pxy(r1, a0))
        wp = _arc(wp, r1, a0, a1)
        if abs(r0) < 1e-9:
            wp = wp.lineTo(0.0, 0.0)
        else:
            wp = wp.lineTo(*_pxy(r0, a1))
            wp = _arc(wp, r0, a1, a0)
        return wp.close().extrude(h)
    n = max(2, int((a1-a0)/step)+1)
    A = [a0 + (a1-a0)*i/(n-1) for i in range(n)]
    f1 = r1 if callable(r1) else (lambda a: r1)
    f0 = r0 if callable(r0) else (lambda a: r0)
    p = [(f1(a)*math.cos(math.radians(a)), f1(a)*math.sin(math.radians(a))) for a in A]
    p += [(f0(a)*math.cos(math.radians(a)), f0(a)*math.sin(math.radians(a))) for a in reversed(A)]
    return cq.Workplane("XY").workplane(offset=z).polyline(p).close().extrude(h)

def beyond_head(t, z0=-60.0, h=120.0):
    """Everything that lies beyond the plane t of the head."""
    return cq.Workplane(obj=cq.Solid.makeBox(400.0, 200.0, h, cq.Vector(-100.0, t, z0))
                        .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))


def slot_st(s_c, width, z0, z1, t0, t1, r):
    """A slot in the board frame, ROUNDED at the top and open at the bottom:
    it is the profile of the USB-C socket, which has no sharp corners
    (the opening follows the connector's outline). The radius is half the height of the SOCKET, not of
    the slot, which at the bottom runs on down to the floor because the socket
    goes into it rising together with the panel."""
    body = cq.Solid.makeBox(width, t1-t0, (z1-r)-z0, cq.Vector(s_c-width/2, t0, z0))
    body = body.fuse(cq.Solid.makeBox(width - 2*r, t1-t0, z1-z0,
                                        cq.Vector(s_c-width/2+r, t0, z0)))
    for _sg in (-1, 1):
        body = body.fuse(cq.Solid.makeCylinder(
            r, t1-t0, cq.Vector(s_c + _sg*(width/2 - r), t0, z1-r), cq.Vector(0, 1, 0)))
    return cq.Workplane(obj=body.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))


def rect_st(s0, s1, t0, t1, z, h):
    """A rectangular prism in the board frame."""
    return cq.Workplane(obj=cq.Solid.makeBox(s1-s0, t1-t0, h, cq.Vector(s0, t0, z))
                        .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))


def cyl(r, h, pnt, dirv):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, h, cq.Vector(*pnt), cq.Vector(*dirv)))

def pol(r, a):
    return (r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))

# ---------------- shell ----------------
# The mechanical compartment no longer rises all the way to the top: it closes
# at Z_shoulder_box and above it there is only a low wall carrying the three
# rear ears.
#
# Why it can. Inside the compartment the tallest thing is the hub of the
# clutch, which ends at z 13; above it, measured on the assembly body by body,
# there was nothing else but the walls of the box. The shoulder above z 16
# weighed 27.5 cm3, of which 23.3 beyond r 96 held up nothing.
#
# And it can also because that volume faces the CLUTCH compartment, not the
# electronic one: the electronic compartment ends at z 2, fourteen millimetres
# lower, and that of the electronic compartment is the only envelope the model
# does not know everything about - the perfboard and the modules are not in
# it. Here instead the model is complete (motor, arm, clutch, spring, spring
# cup, washer, collar) and the measurement holds. Measured by sector: 99.5% of
# the material above z 16 lies in the mechanical sector, and the rest is a
# rear ear, which stays.
#
# Why the ears cannot come down with the shoulder: it is the three at the
# front AGAINST the three at the back, 29 mm apart, that make the couple that
# takes the moment of the spring. Lowering them would mean shortening the arm
# of the couple, that is increasing the pull on the screws.
# And why above the shoulder there remain three small PILLARS and not a
# continuous wall: because the roof of the compartment does not disappear, it
# is lowered. What is really saved is the band of wall between the old roof
# and the new one - the outer back and the two heads, measured 8.3 cm3 - and a
# continuous wall six millimetres wide weighs as much: done that way, the part
# would not have lost a gram. The pillars stand only where they are needed,
# under the three ears.
Qsp = D["Z_shoulder_box"]


# ---------------- the chamfer along the top outer edge ----------------
# Once the roof is flush with the collar, the 3.5 mm it
# rose make room inside, and a Ch_roof_box x Ch_roof_box chamfer along the
# whole edge where the outer wall meets the roof saves material and looks
# better. "The whole edge" is three stretches, one shape each: the back (a
# cone about the wheel axis), the arc round the motor (a cone about the shaft)
# and the head (an inclined plane). All three at 45 degrees.
#
# IT IS A WALL, NOT A CUT. Like the arc, the chamfer is applied at two
# offsets: the outer skin at 0, the void at W. The inclined face inside is
# parallel to the one outside and one wall thickness from it, so the corner
# is born as a 2.5 mm sloping wall. Cutting the outside only would have left
# the corner solid - no material saved - or, cut deeper, a wall thinning to
# nothing along the crease.
#
# Why the two cones stay tangent at every height: the arc is tangent to the
# back because Ro - RA equals the distance between the two centres. Both cones
# lose the same radius per millimetre of height, so that difference - and the
# tangency - holds at every z.
#
# A 45 degree slope facing up prints without supports: the box prints roof up.
CH = D["Ch_roof_box"]
Z_ROOF = Qsp + W


def chamfer(off):
    """What the chamfer keeps, `off` inside the outer skin: below the start of
    the slope everything, above it the three 45 degree faces moved in by off.

    Moving a 45 degree face in by `off` along its normal is the same as moving
    its start down by off*(sqrt(2) - 1) while also moving the vertical face in
    by off: that is the z0 below."""
    z0 = Z_ROOF - CH + off - off*math.sqrt(2.0)
    zt = 80.0                                          # well above anything
    def _cone(cx, cy, r):
        # a cylinder up to z0, then a cone losing one mm of radius per mm;
        # stopped half a millimetre short of its apex for the small one
        h = min(zt - z0, r - 0.5)
        return (cq.Solid.makeCylinder(r, z0 + 100.0, cq.Vector(cx, cy, -100.0))
                .fuse(cq.Solid.makeCone(r, r - h, h, cq.Vector(cx, cy, z0))))
    back = _cone(0.0, 0.0, Ro - off)
    arc = (cq.Solid.makeBox(400.0, 200.0, 200.0, cq.Vector(-200.0, 0.0, -100.0))
            .fuse(_cone(MX, MY, RA - off)))
    # the head, in the board frame (s along U, t along V), extruded along s
    t1 = E.T_HEAD_OUT - off
    prof = [(-300.0, -100.0), (t1, -100.0), (t1, z0), (t1 - (zt - z0), zt), (-300.0, zt)]
    head = (cq.Workplane("YZ").workplane(offset=-300.0).polyline(prof).close()
             .extrude(600.0).val()
             .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))
    return cq.Workplane(obj=back.intersect(arc).intersect(head))

from parameters import EARS_FRONT, EARS_REAR

# ---------------- the void of the compartment ----------------
# The void starts two millimetres FURTHER IN than the inner face of the shell,
# where there is no material to remove. Starting from the same radius, the two
# faces coincided and the subtraction left 197 laminae of zero volume at
# r 86.2: any part passing through that radius - the clutch, the collar -
# turned out to touch them, and the audit found interpenetrations of a
# hundredth of a cubic millimetre that did not exist.
_void = (inside(AM0+2, AM1+1, Ri - 2.0, W, ZT+W, Qsp-(ZT+W)).intersect(chamfer(W))
          .cut(beyond_head(E.T_HEAD_IN)))
mech = inside(AM0, AM1, Ri, 0.0, ZT, (Qsp+W)-ZT).cut(_void)
# The three pillars that carried the rear ears up to z 28.5 are gone:
# the ears went with the one-piece part, and with the roof now
# flush with the collar the pillars were three 4 mm bumps on a flat top.
box = mech.cut(beyond_head(E.T_HEAD_OUT))

# ---------------- the inner wall under the wheel ----------------
# The side of the box towards the wheel axis is no longer the INNER SKIRT at r 86 but a
# wall at r 74.4..76.9, from the floor up into the collar flange - with the
# floor strip between it and the old shell (green), the two ends closed
# (orange) and a 10 mm chamfer in the inside corner.
#
# WHY THE SKIRT WENT. It rose under the arm to half a millimetre from it and
# carved three steps round the pivot for the bearing flange, the washer and the
# screw head: the two F695ZZ sat in it as in a cup, with the pivot column 0.2
# mm above them. check_assembly_paths found the arm could not be put in, and
# no straight path (62 directions, then 162 around the best), and no path in
# two segments (162), got it home: the best still met 503 mm3. With the wall
# moved in, the arm tilted pivot-end-down on the edge of the motor face is free
# up to 8 degrees, and the box does not touch it up to 18.
#
# THE RADIUS IS DERIVED (electronics.R_INNER_WALL): the outer face stands
# Cl_wall_inner_motor inside the motor, which is what comes nearest to the
# axis below the collar. Only below the collar: above z 0 the same ring is the
# body of the wheel.
#
# HOW IT IS BUILT: the same shell and void as the bay, only starting from the
# new wall instead of from the collar, and stopping at the collar flange. The
# void stays W inside the arc round the motor and W inside the head plane, so
# the arc wall and the head wall run on inwards to meet the new wall by
# themselves: the two orange end walls are not drawn, they are the arc and the
# head continued. The shell goes Weld_box_collar into the flange, like the rest
# of the box, and the void 1 mm into it, so that no face of the void lies on
# the underside of the flange.
RP0, RP1 = E.R_INNER_WALL
_z_flange = -D["Th_flange_collar"]
_shell_in = (sett(AM0, AM1, RP0, Ri + 0.5, ZT, (_z_flange + D["Weld_box_collar"]) - ZT)
              .intersect(_keep(0.0)).cut(beyond_head(E.T_HEAD_OUT)))
_void_in = (sett(AM0 + 2, AM1 + 1, RP1, Ri + 1.0, ZT + W, (_z_flange + 1.0) - (ZT + W))
             .intersect(_keep(W)).cut(beyond_head(E.T_HEAD_IN)))
box = box.union(_shell_in.cut(_void_in))

from outline_motor import silhouette as _motor_silhouette
MOTOR_SILHOUETTE = _motor_silhouette(D["Cl_entry_motor"])
# (the chamfers of the inner wall are built further down, after the panel's
# cuts: they end at the ear of the panel, and have to know where it is)

# ---------------- the slot for the iron that plants the M4 insert ----------
# The M4 insert of the preload goes in from INSIDE the box, along its own axis,
# and the iron comes in along that same axis from the other side of the
# compartment. Lowering the spring axis to Z_axis_spring took the iron under the collar's front flange; what still stood in
# its way was the inner skirt, 18.5 mm3 of it at r 87.6, which rises to just
# under the arm. So the skirt gets a U slot there - a slit for the iron - as
# wide as the channel of the iron
# (D_tip_iron + Cl_tip_iron) and only across the skirt, where the axis crosses
# the band R_SKIRT: the channel itself, not a hand-drawn rectangle, so it
# follows the axis if the axis moves. Open at the top, it prints with nothing
# overhanging.
from parameters import spring_axis as _spring_axis_f
_Qxf, _Qyf, _nxf, _nyf, _zmf = _spring_axis_f()
def _s_at_r(r):
    """Where along the spring axis the axis is at radius r, on the crossing
    NEAR Q - Q itself sits at r 89, inside the skirt band. The other root is
    on the far side of the wheel, 180 mm away, and the first version took it."""
    _b = _Qxf*_nxf + _Qyf*_nyf
    _c = _Qxf*_Qxf + _Qyf*_Qyf - r*r
    return -_b + math.sqrt(max(_b*_b - _c, 0.0))
# The skirt is gone and what the axis crosses is now the INNER
# WALL under the wheel, which runs up into the collar: the U open at the top
# would be a slit up to the flange, open to the camera side. So it is the
# channel alone, a round hole through the wall - short, 2.5 mm, and it prints
# as a bridge of a few millimetres.
_s_g0, _s_g1 = _s_at_r(E.R_INNER_WALL[1] + 1.5), _s_at_r(E.R_INNER_WALL[0] - 1.5)
_r_chan = (D["D_tip_iron"] + D["Cl_tip_iron"])/2
_slit = cq.Workplane(obj=cq.Solid.makeCylinder(_r_chan, _s_g0 - _s_g1,
                              cq.Vector(_Qxf + _nxf*_s_g1, _Qyf + _nyf*_s_g1, _zmf),
                              cq.Vector(_nxf, _nyf, 0)))
box = box.cut(_slit)

# ---------------- seat of the spring ----------------
from parameters import spring_axis, s_spring_axis
Qx, Qy, nx, ny, _zm_spring = spring_axis()
# The fixed end sits at R_seat_spring_box, that is exactly one fitted spring
# beyond the side of the arm. It used to be at r 107.5, which left 1.3 mm to a
# spring 12.8 long; and the boss, 26 long, stuck three and a half millimetres
# out of the outer wall. Now the seat is close to the wall and the boss is
# short: it starts from the seat and just reaches it.
s_along_axis = s_spring_axis

S0 = s_along_axis(D["R_seat_spring_box"])
# The spring axis lies on the mid-plane of the arm plate, not at -6. That -6
# was the mid-plane of a thickening on the arm that served no purpose (see
# solids_arm.py) and has been removed; centred on the plate, the spring pushes
# in line with the section instead of two millimetres off it.
zm = _zm_spring

p0 = (Qx+nx*S0, Qy+ny*S0, zm)
travel, th_cup = D["Travel_preload"], D["Th_cup_spring"]
# The boss starts one travel BEFORE the nominal seat. Starting it at the seat,
# the pocket dug further back found no material to dig and the mouth stayed
# where the boss was: the spring cup, pushed in to increase the preload, came
# out of the guide instead of sliding in it. Measured: towards the arm there
# was zero travel.
pb = (Qx+nx*(S0-travel), Qy+ny*(S0-travel), zm)
# The boss is no longer just long enough to reach the wall: it must hold, in a
# row, the pocket of the spring cup, a bottom of ASA, and the seat of the
# grub's heat-set insert. Measured: between the bottom of the pocket and the
# outer wall there were 5.91 mm and the insert wants 8.6, so the seat would
# have broken into the pocket by two point seven millimetres. Now the boss is
# the longer of the two - the one that reaches the wall and the one that holds
# the row - so if one day the spring seat moves inwards the boss comes back in
# by itself instead of staying proud for ever.
L_row = (2*travel+th_cup) + D["Dp_seat_insert_M4"] + D["Th_retain_insert_M4"]
L_boss = max(s_along_axis(Ro) - (S0-travel) + 1.0, L_row)
R_BOSS = 7.5
box = box.union(cyl(R_BOSS, L_boss, pb, (nx, ny, 0)))           # boss out to the wall

# ---------------- the rib of the spring boss ----------------
# The boss is a cylinder LYING in the middle of the compartment, and the box
# prints with its floor on the bed: its lower half is an overhanging roof that
# wants supports, and under it there is nothing for them to grow from but the
# floor, twenty-seven millimetres lower.
#
# Instead of supporting it, it is filled. Under the cylinder two 45 degree
# faces - tangent to it, closed to a point - carry the material down to a
# vertical rib that goes down to the floor; above the cylinder the same rib
# rises up to the roof of the compartment. No face goes below 45 degrees, so
# in that orientation everything prints from solid.
#
# And it is not only a matter of printing: the boss is the point on which the
# spring presses permanently with 22.3 N, and it was attached to the box only
# by the end that touches the outer wall. Now it is tied to the floor and to
# the vault too, that is it unloads onto the whole section of the shell
# instead of onto one end. The sliced part shows the room for it: below and
# above there is space and nothing else passes there.
_ang_spring = math.degrees(math.atan2(ny, nx))
_sn = D["Th_rib_boss_spring"]/2
_sa_n, _sb_n = S0 - travel, (S0 - travel) + L_boss
_c45 = R_BOSS/math.sqrt(2.0)                 # where the 45 degree tangent touches
_prof_n = [(-_c45, zm - _c45), (_c45, zm - _c45), (0.0, zm - R_BOSS*math.sqrt(2.0))]
_flat = [(-_sn, ZT), (_sn, ZT), (_sn, Qsp + W), (-_sn, Qsp + W)]


def _along_spring(sol):
    """From the local frame of the spring (x along the axis, y across) to the
    plane of the design. Written once: hand-written angles have already cost a
    boss placed five degrees out of position, on the bracket."""
    return (sol.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _ang_spring)
            .translate(cq.Vector(Qx, Qy, 0)))


_rib = (cq.Workplane("YZ").workplane(offset=_sa_n).polyline(_flat).close()
         .extrude(_sb_n - _sa_n))
_rib = _rib.union(cq.Workplane("YZ").workplane(offset=_sa_n).polyline(_prof_n)
                    .close().extrude(_sb_n - _sa_n))
box = box.union(_along_spring(_rib)
                .intersect(inside(AM0, AM1, Ri, 0.0, ZT, (Qsp + W) - ZT)))


# The pocket is no longer just the guide of the spring: the spring cup slides
# in it. The grub pushed with its Ø4 tip directly on the last coil, which is a
# one-millimetre wire: it would have dug into it, and at every turn of
# adjustment it would have rubbed it and loaded it in torsion instead of in
# compression. Now the grub pushes on the back of the spring cup, and the
# spring sees a flat face and a spigot that keeps it on axis, as on the other
# side on the arm.
#
# The pocket starts one travel BEFORE the nominal position: so the preload can
# be increased beyond the nominal, not only slackened. As long as the travel,
# plus the spring cup, plus the travel on the other side.
pt = (Qx+nx*(S0-travel), Qy+ny*(S0-travel), zm)
box = box.cut(cyl(D["D_seat_spring_box"]/2, 2*travel+th_cup, pt, (nx, ny, 0)))
box = box.cut(cyl(2.05, L_boss+2, p0, (nx, ny, 0)))              # M4 hole of the grub

# ---------------- seat of the grub's heat-set insert ----------------
# The 4.1 hole is a clearance, not a thread: the grub would just slide in
# there, while the spring pushes against it with 22.3 N. The thread is in an
# M4 heat-set insert, planted at the mouth of the boss, on the side the grub
# is screwed in from. Beyond the insert the hole stays a clearance: the grub
# screws into the insert and then runs on free up to the spring cup.
#
# The two dimensions that matter are of the inserts of the reference build,
# measured with the caliper: 6.3 outside and 8.1 long. They are bigger than the
# most common M4,
# which is around 5.6 - whoever has different ones changes D_out_insert_M4 and
# L_insert_M4 and all the rest follows.
#
# The hole is narrower than the insert ON PURPOSE, by three and a half tenths:
# melting, it must plant itself in the plastic, not slip into it. And the seat
# is deeper than the insert ON PURPOSE, by half a millimetre: flush, the
# insert would push the molten plastic to the bottom instead of letting it
# flow back.
# THE INSERT IS PLANTED FROM INSIDE, not from outside. The direction is not
# indifferent: the spring pushes the spring cup, the spring cup pushes the
# grub and the grub unloads onto the insert TOWARDS THE OUTSIDE, that is in
# the direction in which the brass comes out of the wall it was put into.
# Planted from outside, those 22.3 N pulled for the whole life of the machine
# in the direction of pull-out. Planted from inside, the same force presses it
# against the outer wall, which stays whole except for the passage of the
# grub: it works in compression.
#
# The iron gets there through the pocket of the spring cup, which is Ø9.6
# coaxial: that is why between the pocket and the seat there is no longer any
# bottom: a bottom there would be the wall that blocks the tool's way. The
# plastic that used to be around it now lies all on the outer side.
s_end = (S0-travel) + L_boss                      # outer face of the boss
_s_mouth = s_end - D["Th_retain_insert_M4"]      # outer face of the insert
p_mouth = cq.Vector(Qx+nx*_s_mouth, Qy+ny*_s_mouth, zm)
towards = cq.Vector(-nx, -ny, 0)                    # towards the inside of the box
box = box.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
    D["D_hole_insert_M4"]/2, D["Dp_seat_insert_M4"], p_mouth, towards)))
# The lead-in looks INWARDS, because that is where the insert comes from. It
# starts half a millimetre beyond the mouth, in the air: a coplanar cone leaves
# splinters.
_s_entry = _s_mouth - D["Dp_seat_insert_M4"]        # inner mouth of the seat
p_entry = cq.Vector(Qx+nx*_s_entry, Qy+ny*_s_entry, zm)
box = box.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_leadin_insert_M4"]/2 + 0.5, D["D_hole_insert_M4"]/2,
    D["Dp_leadin_insert_M4"] + 0.5, p_entry + towards*0.5, -towards)))

# ---------------- the slot of the sensor cable in the roof ----------------
# The sensor cable enters the compartment through the roof. It used to be a
# hole at r 110, and it wanted the bare cable: an already crimped connector did
# not go through. Now it is an OPEN SLOT on the inner edge of the roof, at
# r 86: the cable slips into it sideways, connector included. The open
# edge faces the collar, so the cable is put in the slot BEFORE bringing the
# box up, and with the box fitted the collar closes the slot and holds it.
#
# It is long, and not by choice: the cable arrives from the bracket almost
# flat, and to go down into the compartment without bending below its minimum
# radius it crosses the roof obliquely. The bottom of the slot is where the
# cable leaves the roof.
#
# Countersunk above and below, along the whole edge: a cable resting on a
# sharp edge of printed ASA gets stripped there, after months. The countersink
# is made with a row of cones along the slot, which together make a
# continuous chamfer.
_av = D["Ang_opening_cable_box"]
_rv, _smv = D["D_opening_cable_box"]/2, D["Ch_opening_cable"]
_r_slot = (Ri - 2.0, D["R_opening_cable_box"])
_ua = (math.cos(math.radians(_av)), math.sin(math.radians(_av)))
_na = (-_ua[1], _ua[0])
_p_sl = [(_ua[0]*_r_slot[0] + _na[0]*sg*_rv, _ua[1]*_r_slot[0] + _na[1]*sg*_rv) for sg in (-1, 1)]
_p_sl += [(_ua[0]*_r_slot[1] + _na[0]*sg*_rv, _ua[1]*_r_slot[1] + _na[1]*sg*_rv) for sg in (1, -1)]
box = box.cut(cq.Workplane("XY").workplane(offset=Qsp-1).polyline(_p_sl).close().extrude(W+2))
box = box.cut(cq.Workplane("XY").workplane(offset=Qsp-1).center(*pol(_r_slot[1], _av))
              .circle(_rv).extrude(W+2))
_n_cones = int((_r_slot[1] - _r_slot[0])/0.5) + 1
for _k in range(_n_cones):
    _rk = _r_slot[0] + (_r_slot[1] - _r_slot[0])*_k/(_n_cones - 1)
    _pk = pol(_rk, _av)
    for _z0, _r0, _r1 in ((Qsp+W-_smv, _rv, _rv+_smv), (Qsp, _rv+_smv, _rv)):
        box = box.cut(cq.Workplane(obj=cq.Solid.makeCone(
            _r0, _r1, _smv, cq.Vector(_pk[0], _pk[1], _z0), cq.Vector(0, 0, 1))))

# ---------------- the head: USB and GX12 ----------------
# The USB socket of the XIAO comes flush with the outer face. The slot is OPEN
# TOWARDS THE FLOOR: the board goes in from the floor together with the panel,
# and the socket must be able to rise inside the wall instead of having to go
# through it. Below the socket the slot is closed by a tab of the panel.
_gu = D["Cl_usb"]
# The slot carries the panel's extra clearance too: the TAB rises into it,
# which is the last fit the panel makes going in, and its clearance was
# Cl_panel like all the others. Measuring after widening the outline and the
# ears, the narrowest point had moved right here.
box = box.cut(slot_st(E.S_USB, E.USB_L + 2*_gu + 2*D["Cl_panel_box"],
                       ZT - 1.0, E.Z_USB[1] + _gu,
                       E.T_HEAD_IN - 1.0, E.T_HEAD_OUT + 1.0,
                       (E.USB_H + 2*_gu + 2*D["Cl_panel_box"])/2))
# and below the socket one pitch more towards the back, for the arm going in
# (electronics.EXT_SLOT_BACK, the why is there): up to the top of the
# panel's tongue plus the clearance it rises with
_w_slot = E.USB_L + 2*_gu + 2*D["Cl_panel_box"]
box = box.cut(cq.Workplane(obj=cq.Solid.makeBox(
    E.EXT_SLOT_BACK + 1.0, E.T_HEAD_OUT - E.T_HEAD_IN + 2.0,
    (E.Z_USB[0] - _gu + D["Cl_panel_box"]) - (ZT - 1.0),
    cq.Vector(E.S_USB + _w_slot/2 - 1.0, E.T_HEAD_IN - 1.0, ZT - 1.0)
).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD)))
# Here was the GROOVE FOR THE XIAO'S BOARD: the board went into the head by
# 0.97 mm - as much as the socket sticks out beyond the edge, less the
# thickness of the wall - and a niche as wide as it was dug, open towards the
# floor. 18.58 wide against the 9.74 of the socket's slot, it left two 4.4 mm
# recesses at the sides of the panel's tower.
#
# REMOVED: the board of the reference build is sanded down on purpose in that
# area and no longer goes into the wall. The head is solid again at the sides of the socket, which is also
# the face the shell of the right-angle plug rests on. To be put back only if
# the board is changed or no longer sanded: the sign to watch is the
# interpenetration between the head and the envelope of the XIAO, which the
# maker's model draws whole.

# The GX12, above the XIAO. The hole runs along t, that is perpendicular to
# the head.
#
# It is NOT a plain round hole, and the reason showed up screwing it on: the
# connector TURNED behind the ring nut. The threaded barrel has two
# anti-rotation flats, one per side at 180 degrees, 11.75 from one to the
# other (measured with the caliper). In a round hole they have nothing to bear
# against.
#
# The flats of the hole are ABOVE AND BELOW, not at the sides: in the head the
# tight space is in height - below is the XIAO, above the LED - and two
# horizontal chords remove material exactly where it is least needed. The
# connector goes in both ways, so the orientation is free and is chosen for
# the box.
_gx = E.xy(E.GX12_S, E.T_HEAD_IN - 1.0)
_w_gx = D["W_flats_gx12"] + D["Cl_flats_gx12"] + D["Comp_hole_printing"]
_round_gx = cyl(D["D_hole_gx12"]/2, W + 2.0,
                (_gx[0], _gx[1], E.GX12_Z), (E.V[0], E.V[1], 0))
_slice_gx = (cq.Workplane("XY").workplane(offset=E.GX12_Z - _w_gx/2)
             .center(_gx[0], _gx[1]).rect(60.0, 60.0).extrude(_w_gx))
box = box.cut(_round_gx.intersect(_slice_gx))

# The tab for the tie of the wires, beside the GX12. Profile in the (t, z)
# plane: free edge vertical, H_tab high; lower edge at 45 degrees up to the
# head, so it prints without support. The slot crosses it transversely.
_la, _sa = D["L_tab_tie"], D["Th_tab_tie"]
_z0a, _z1a = E.TAB_Z
_prof = [(E.T_HEAD_IN + 0.5, _z0a - _la - 0.5), (E.T_HEAD_IN - _la, _z0a),
         (E.T_HEAD_IN - _la, _z1a), (E.T_HEAD_IN + 0.5, _z1a)]
_tie_tab = (cq.Workplane("YZ").workplane(offset=E.TAB_S - _sa/2)
           .polyline(_prof).close().extrude(_sa).val()
           .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))
_slot = cq.Workplane(obj=cq.Solid.makeBox(
    _sa + 2.0, D["H_slot_tie_head"], D["W_slot_tie_head"],
    cq.Vector(E.TAB_S - _sa/2 - 1.0, E.TAB_SLOT_T - D["H_slot_tie_head"]/2,
              E.TAB_SLOT_Z - D["W_slot_tie_head"]/2))
    .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD))
box = box.union(cq.Workplane(obj=_tie_tab)).cut(_slot)

# The status LED, above the GX12.
_led = E.xy(E.LED_S, E.T_HEAD_IN - 1.0)
box = box.cut(cyl(D["D_hole_led"]/2, W + 2.0, (_led[0], _led[1], E.LED_Z), (E.V[0], E.V[1], 0)))

# ---------------- the opening of the panel ----------------
# The panel closes an opening in the floor and carries the board: it is the
# service opening the compartment lacked. The whole floor is not removed,
# because the box prints right on it (assessment on the branch
# vano-elettronica-motore-3: without the floor 831 mm2 of first layer would
# remain).
#
# Flush with the floor, with a STOP on the outer half of the thickness: the
# panel cannot go into the compartment, and the screws hold it from the other
# side. The stop is not there on the side of the skirt, where there is no
# floor, and it must not eat into the back: everything stops at its inner
# face.
_bt = D["Stop_panel"]
_inside_back = inside(AM0, AM1, 0.5, W, ZT - 2.0, 14.0)
_rb = D["D_boss_panel"]/2

# The RAISES of the two ears. In the zones of the screws the panel is
# Th_panel_screws thick and not half a wall, so its step in the box is as deep:
# and there the floor was 2.5, all of it. So the box must RAISE its own floor
# in those zones, otherwise the step becomes a hole and the bosses of the
# screws are left without a roof to grow from.
#
# The raise is the outline of the ear widened by a wall on the sides that
# border material of the box - they are the ones that hold up the roof - and
# not widened on the one facing the opening, where beyond there is nothing to
# grow from. It is cut inside the skirt: further in than it there is the
# collar, and a raise ending up in it would be an interpenetration.
_inside_skirt = cq.Workplane("XY").workplane(offset=ZT - 2.0).circle(E.R_SKIRT[0]).extrude(20.0)
for _s0, _s1, _t0, _t1, _side, _ovl in E.panel_ears():
    # on the free sides the raise widens by a wall, which is the low wall that
    # holds up the roof; on the inner side instead it DRAWS BACK by the
    # overlap, because that millimetre lies inside the opening and no raise
    # belongs there: the guides of the board pass there, and at the first try
    # they ran into it for 23 mm3
    _e = {"s0": -W, "s1": +W, "t0": -W, "t1": +W}
    _e[_side] = -_ovl if _side in ("s1", "t1") else +_ovl
    box = box.union(rect_st(_s0 + _e["s0"], _s1 + _e["s1"],
                                  _t0 + _e["t0"], _t1 + _e["t1"],
                                  E.Z_FLOOR_TOP, (E.Z_SCREWS + W) - E.Z_FLOOR_TOP)
                    .intersect(_inside_back).cut(_inside_skirt)
                    .cut(beyond_head(E.T_HEAD_OUT)))


# The cuts of the opening are kept aside: the column of the front ear at 71.1
# degrees, which comes down right above here, has to redo them too. The ears
# are joined AFTERWARDS, and a cut already made does not cut what comes after:
# without this list the column closed again 109 mm3 of the panel's place, and
# the panel would no longer have come out of the floor.
# The opening is dug WIDER than the panel by Cl_panel_box per side, and the
# clearance is all added on this side: the panel stays the one of before, so
# that a panel already printed still fits. Two tenths per side were right on
# paper - measured on the solids they made 0.199, that is the nominal - and
# nil in the hand: over eighty-five millimetres of part that tenth and a half
# is eaten by the shrinkage. The panel centres nothing: what holds it in
# position is the three screws in their inserts.
_cb = D["Cl_panel_box"]
# The cut-out of the back must be widened too, otherwise on that side the
# extra clearance does not arrive: the panel is cut at Ro - W - Cl_panel and
# the opening at Ro - W, so there the clearance IS Cl_panel and widening the
# rectangle changes nothing - the back trims the cut. Measured: after widening
# only the rectangles, the minimum distance was still 0.199 in three points,
# all on the back. The wall stays W - Cl_panel_box thick in that band.
_inside_back_pan = inside(AM0, AM1, 0.5, W - _cb, ZT - 2.0, 14.0)
PANEL_CUTS = [
    rect_st(E.OP_S[0] - _cb, E.OP_S[1] + _cb, E.OP_T[0] - _cb, E.OP_T[1] + _cb,
                  ZT - 1.0, W + 2.0).intersect(_inside_back_pan),
    rect_st(E.OP_S[0] - _cb, E.OP_S[1] + _bt + _cb,
                  E.OP_T[0] - _bt - _cb, E.OP_T[1] + _bt + _cb,
                  ZT - 1.0, E.Z_STOP - (ZT - 1.0)).intersect(_inside_back_pan),
]
# the two ears, dug down to Z_SCREWS and not to half thickness. Here too the
# extra clearance is dug on the FREE sides - the same ones on which the panel
# had already been made smaller - and not on the one with which the ear is
# welded to the body of the panel, where there is no fit to widen.
for _s0, _s1, _t0, _t1, _side, _ovl in E.panel_ears():
    _e = {"s0": -_cb, "s1": +_cb, "t0": -_cb, "t1": +_cb}
    _e[_side] = 0.0
    _tg = rect_st(_s0 + _e["s0"], _s1 + _e["s1"],
                        _t0 + _e["t0"], _t1 + _e["t1"],
                        ZT - 1.0, E.Z_SCREWS - (ZT - 1.0))
    PANEL_CUTS.append(_tg.intersect(_inside_back_pan) if _side == "t1" else _tg)
# THE CHANNEL OF THE IRON to the three panel inserts, from the floor up to the
# face the insert is planted from (Z_SCREWS). The M3 insert n.2 sits at r 124.4
# and the pocket of its ear is cut back by the back wall, whose inner face is
# at Ro - (W - Cl_panel_box): the foot of that wall stood 3.1 mm from the axis
# for the 4.6 mm between the floor and the mouth, and the tip - Ø8, 8.5 with
# its clearance - met 16 mm3 of it (check_insert_access). The panel
# was never in the way: the insert is planted with the panel off, and the wall
# is part of the box itself. The panel is NOT changed - one already printed
# must keep fitting - so the channel is scooped into the wall from inside, leaving it
# Ro - r_insert - (D_tip_iron + Cl_tip_iron)/2 thick there (1.35 mm) with the
# outer face untouched. It is cut for all three screws and not for "the one
# near the wall": at n.1 and n.3 it removes nothing today, and if a screw
# moves, its channel moves with it.
for _s, _t in E.panel_screws():
    _xv, _yv = E.xy(_s, _t)
    PANEL_CUTS.append(
        cq.Workplane("XY").workplane(offset=ZT - 1.0).center(_xv, _yv)
        .circle((D["D_tip_iron"] + D["Cl_tip_iron"])/2)
        .extrude(E.Z_SCREWS - (ZT - 1.0)))
# ---------------- the web at the head, between the skirt and the wheel ------
# A wall here stiffens the structure. Beside the head, between the outer face of
# the skirt and the wheel body, the box had a gap from the floor up to the
# collar flange: the head wall stopped at the skirt, and the skirt was the
# only thing tying the head to the collar. The web fills that corner: along
# the head plane from the wheel to the skirt, back along the skirt for
# L_rib_head_skirt, and a straight edge from there to the wheel. Radially it
# stops Cl_rib_head_body short of the wheel body; it goes half a millimetre
# into the skirt, and up to the underside of the collar flange.
# Built before the panel cuts, so the panel opening is carved out of it too.
def _on_head(r, t):
    return E.xy(math.sqrt(r*r - t*t), t)
_rw0 = D["D_body"]/2 + D["Cl_rib_head_body"]
_rw1 = E.R_SKIRT[0] + 0.5
_tw0, _tw1 = E.T_HEAD_OUT, E.T_HEAD_OUT - D["L_rib_head_skirt"]
# up to the underside of the collar flange and not into it: half a millimetre
# of overlap there was counted by the audit as box and collar welding outside
# the skin of the shell. Touching is enough - the count of solids below says
# whether it fused.
_zw1 = -D["Th_flange_collar"]
_head_web = (cq.Workplane("XY").workplane(offset=ZT)
          .moveTo(*_on_head(_rw0, _tw0)).lineTo(*_on_head(_rw1, _tw0))
          .threePointArc(_on_head(_rw1, (_tw0 + _tw1)/2), _on_head(_rw1, _tw1))
          .close().extrude(_zw1 - ZT)
          .cut(cq.Workplane("XY").workplane(offset=ZT - 1.0).circle(_rw0).extrude(_zw1 - ZT + 2.0)))
box = box.union(_head_web)
print("web between head, skirt and wheel: r %.1f..%.1f, t %.1f..%.1f, z %.1f..%.1f, %.2f cm3"
      % (_rw0, _rw1, _tw1, _tw0, ZT, _zw1, _head_web.val().Volume()/1000))

# ---------------- the chamfers of the inner wall ----------------
# INSIDE: a ring of 45 degree fillet material on the floor against the wall,
# Chamfer high and wide. OUTSIDE: the same chamfer taken off, parallel to the
# inside one, so that round the corner the wall keeps its thickness: the outer
# leg is C + (2 - sqrt 2) W, which puts the outer slope exactly W from the
# inner one.
#
# WHERE THEY RUN: only between the motor and the ear of the panel by the head
# (they stop a little before the motor, and leave no points by the panel
# insert). Following the motor's outline, the first version left
# the chamfer notched into its silhouette and, at the head, running into the
# pocket of the ear, where it left thin points. Both ends are READ FROM THE
# SOLIDS: the motor end is the furthest the motor's exclusion reaches into the
# band of the chamfers, the other the nearest the ear's cuts reach into it.
#
# HOW THEY END: not square, but fading out on a ramp at the chamfer's own
# angle. At a distance s along the wall from the end the chamfer stands s
# high; the outer ramp runs W*sqrt(2) lower than the inner one, so that on the
# ramp too the wall is W thick across.
_C = D["L_chamfer_wall_inner_floor"]
_L_out = _C + (2.0 - math.sqrt(2.0))*W
_ZTf = ZT + W
# the motor's exclusion: past the outer face of the wall, and down through the
# floor - the silhouette starts at the bottom of the motor, above the floor
_excl = _motor_silhouette(max(D["Cl_entry_motor"] + W*math.sqrt(2.0),
                           D["Cl_wall_inner_motor"] + W) + 0.5)
_excl = _excl.union(_excl.translate((0, 0, -20.0)))
# the band the chamfers live in, short of the inner chamfer's foot by 1 mm:
# the panel opening grazes the foot along its middle, and that is not an end
_band = sett(AM0, AM1, RP0 - 1.0, RP1 + _C - 1.0, ZT - 1.0, _L_out + 3.0)
def _angles(w):
    return [math.degrees(math.atan2(v.Y, v.X)) for v in w.val().Vertices()]
_a_lo = max(_angles(_excl.intersect(_band)))
_ears = PANEL_CUTS[2]
for _tg in PANEL_CUTS[3:]:
    _ears = _ears.union(_tg)
_a_hi = min(a for a in _angles(_ears.intersect(_band)) if a > _a_lo)


def _ramp(a, towards, z0):
    """Keep what is s ahead of the end at angle `a` (on the side `towards`,
    +1 or -1) and at most s above z0: a half-space bounded by a plane at 45
    degrees."""
    ar = math.radians(a)
    t = cq.Vector(-math.sin(ar)*towards, math.cos(ar)*towards, 0.0)
    rad = cq.Vector(math.cos(ar), math.sin(ar), 0.0)
    p0 = cq.Vector(RP1*math.cos(ar), RP1*math.sin(ar), z0)
    n = (t + cq.Vector(0, 0, -1)).normalized()
    return cq.Workplane(cq.Plane(origin=p0, xDir=rad, normal=n)).rect(600, 600).extrude(300)


_sector_ch = sett(_a_lo, _a_hi, RP0 - 1.0, RP0 + _L_out + 2.0, ZT - 2.0, _L_out + 4.0)
_chamfer_in = (cq.Workplane(obj=cq.Solid.makeCone(RP1 + _C, RP1, _C, cq.Vector(0, 0, _ZTf)))
              .cut(cq.Workplane(obj=cq.Solid.makeCylinder(RP1 - 0.5, _C + 1.0, cq.Vector(0, 0, _ZTf - 0.5))))
              .intersect(_sector_ch).intersect(_keep(W)).cut(beyond_head(E.T_HEAD_IN))
              .intersect(_ramp(_a_lo, +1, _ZTf)).intersect(_ramp(_a_hi, -1, _ZTf)))
_z_out = _ZTf - W*math.sqrt(2.0)
_chamfer_out = (cq.Workplane(obj=cq.Solid.makeCone(RP0 + _L_out + 0.5, RP0, _L_out + 0.5, cq.Vector(0, 0, ZT - 0.5)))
               .cut(cq.Workplane(obj=cq.Solid.makeCylinder(RP0 - 0.5, _L_out + 2.0, cq.Vector(0, 0, ZT - 1.0))))
               .intersect(_sector_ch).intersect(_keep(W)).cut(beyond_head(E.T_HEAD_IN))
               .intersect(_ramp(_a_lo, +1, _z_out)).intersect(_ramp(_a_hi, -1, _z_out)))
box = box.union(_chamfer_in).cut(_chamfer_out)
print("chamfers of the inner wall: from %.1f to %.1f degrees, %.0f inside and %.1f outside, ramps at 45 degrees"
      % (_a_lo, _a_hi, _C, _L_out))

for _tg in PANEL_CUTS:
    box = box.cut(_tg)

# ...AND FROM THE RAMP TO THE HEAD, A STRAIGHT CUT. Past the ramp at
# the panel end the floor ran on as a tongue to the head: a triangle in plan
# between the ramp's foot on the wall, the wall's corner at the head and the
# head's corner by the ear. It goes, on a 45 degree plane through the line
# - from the ramp's foot on the wall to the head's corner by the ear, on
# the floor - rising towards the wheel axis: nothing at the ramp, the width
# of the tongue at the head. Both ends are read from the solid, at the floor:
# the ramp's foot is the floor vertex on the wall's face nearest _a_hi from
# below, the head's corner the floor vertex on the head plane outside the wall.
def _on_head(v):
    a = math.radians(E.A_BOARD)
    return abs(-math.sin(a)*v.X + math.cos(a)*v.Y - E.T_HEAD_OUT) < 0.05


_vf = [v for v in box.val().Vertices() if abs(v.Z - ZT) < 1e-3]
_foot = [v for v in _vf if abs(math.hypot(v.X, v.Y) - RP0) < 0.05
          and _a_hi - 5.0 < math.degrees(math.atan2(v.Y, v.X)) < _a_hi + 0.5]
_corner_t = [v for v in _vf if _on_head(v) and math.hypot(v.X, v.Y) > RP0 + 1.0]
if not _foot or not _corner_t:
    raise SystemExit("tongue at the head: cannot find the foot of the ramp (%d) or the corner "
                     "of the head (%d) on the floor" % (len(_foot), len(_corner_t)))
_P3 = max(_foot, key=lambda v: math.atan2(v.Y, v.X))
_H2 = min(_corner_t, key=lambda v: math.hypot(v.X, v.Y))
_d = cq.Vector(_H2.X - _P3.X, _H2.Y - _P3.Y, 0.0).normalized()
_m = cq.Vector(-_d.y, _d.x, 0.0)
if _m.dot(cq.Vector(-_P3.X, -_P3.Y, 0.0)) < 0:
    _m = _m.multiply(-1.0)                             # towards the wheel axis
_nn = (_m - cq.Vector(0, 0, 1)).normalized()
_tongue = (cq.Workplane(cq.Plane(origin=(_P3.X, _P3.Y, ZT), xDir=_d, normal=_nn))
           .rect(200.0, 200.0).extrude(60.0)
           .intersect(sett(math.degrees(math.atan2(_P3.Y, _P3.X)), AM1 + 5.0, RP0 - 10.0,
                           RP0 + 10.0, ZT - 1.0, 15.0))
           .cut(beyond_head(E.T_HEAD_OUT)))
box = box.cut(_tongue)
print("tongue at the head: removed along the line from (%.1f, %.1f) to (%.1f, %.1f), plane at 45 degrees"
      % (_P3.X, _P3.Y, _H2.X, _H2.Y))


# The bosses of the screws, with the M3 insert. The insert is planted FROM
# OUTSIDE, from the face of the stop, and not from inside: from inside it
# cannot be reached, because above the bosses the compartment is closed and the
# mouth of the panel is too narrow for the iron (the section shows it). The
# price is the hold: the screw pulls the insert towards its
# mouth, that is in the direction in which it pulls out, instead of pressing it
# onto the bottom of the hole. For a panel carrying a board it is enough.
# Above the insert the narrow hole remains, for the tip of the screw.
# The bosses grow from the roof of the step, which now sits at Z_SCREWS and no
# longer at half wall: the dimension is one, and boss, seat and lead-in follow
# it.
Z_PANEL_BOSSES = E.Z_SCREWS + D["L_insert_M3"] + 1.0
for _s, _t in E.panel_screws():
    _x, _y = E.xy(_s, _t)
    box = box.union(cq.Workplane("XY").workplane(offset=E.Z_SCREWS).center(_x, _y)
                    .circle(_rb).extrude(Z_PANEL_BOSSES - E.Z_SCREWS)
                    .intersect(inside(AM0, AM1, 0.5, 0.01, ZT, 60.0)))
    box = box.cut(cq.Workplane("XY").workplane(offset=E.Z_SCREWS - 0.01).center(_x, _y)
                  .circle(D["D_hole_insert_M3"]/2).extrude(D["L_insert_M3"] + 0.5))
    box = box.cut(cq.Workplane("XY").workplane(offset=ZT - 1.0).center(_x, _y)
                  .circle(1.7).extrude(Z_PANEL_BOSSES - 0.8 - (ZT - 1.0)))
    # the lead-in, born half a millimetre outside the face as for the other seats
    box = box.cut(cq.Workplane(obj=cq.Solid.makeCone(
        D["D_leadin_insert_M3"]/2 + 0.5, D["D_hole_insert_M3"]/2,
        D["Dp_leadin_insert_M3"] + 0.5,
        cq.Vector(_x, _y, E.Z_SCREWS - 0.5), cq.Vector(0, 0, 1))))


# ---------------- ears fastening to the collar: THEY NO LONGER EXIST --------
# Here stood the six ears - three at the front and three at the back - that
# went over the flanges of the collar and screwed into them, plus the columns
# that carried the front ones down to the floor and the fillets to the wall.
# They took the 22.3 N of the spring and the 680 N mm moment that followed.
#
# Now there is nothing left to fasten: box and collar are the
# same part and the material carries that load. With them three defects go at
# once - the box that did not pass over the screw of the pivot (it was a
# PATH defect, and without sliding it on there is no path), the ear of the
# collar that snapped while sliding it on, and the ten chances of getting a
# screw wrong in assembly (5 M3 screws + 5 heat-set inserts).

# ---------------- spring cup ----------------
# It sits between the grub and the spring, and does three jobs the grub alone
# did not do. It spreads: the Ø4 tip pressed on the last coil, a one-millimetre
# wire, and on ASA it would have dug in until the preload was lost. It
# decouples: turning, the grub rubbed the coil and gave it torsion instead of
# compression, that is it screwed and unscrewed the spring while being
# adjusted. And it centres: the spigot goes into the inner diameter of the
# spring exactly like the spigot on the arm, so the spring is held on axis at
# both ends instead of at one only.
#
# The dish on the back is narrower than the grub: it is the tip that finds the
# centre, not the assembler. And it is a cone, not a flat bottom, because on a
# flat bottom the spring cup could still wander sideways.
_rs, _rc = D["D_cup_spring"]/2, D["D_dish_grub"]/2
_axis = cq.Vector(nx, ny, 0)
_orig = cq.Vector(Qx+nx*S0, Qy+ny*S0, zm)
cup = cq.Solid.makeCylinder(_rs, th_cup, _orig, _axis)
cup = cup.fuse(cq.Solid.makeCylinder(D["D_spigot_spring"]/2, D["Proj_spigot_spring"],
                                       _orig, -_axis))
cup = cup.cut(cq.Solid.makeCone(_rc, 0.0, _rc,
                                  _orig + _axis*th_cup, -_axis))
cup = cq.Workplane(obj=cup.clean())
cq.exporters.export(cup, OUT+"spring_cup.step")

# ---------------- the outer edges: sharp for now ----------------
# Here there was a 45 degree, 1.5 mm chamfer on the six exposed outer edges.
# Removed to make way for a different way of taking the edges off, still to
# be drawn. It was not
# removed because it was not needed - the reasons it was there all remain, all
# three: the hands, the eye and the printing - so when the new shape arrives
# the job must be put back, not only the line.
#
# One thing the chamfer cost and that now comes back, and it is worth knowing
# before redrawing it: at the height of the floor of the electronic
# compartment the material stopped at r 128.5 instead of 130, and that
# millimetre and a half was exactly what was missing to fit a Ø11 boss for the
# M3 insert of the panel.
#
# ---------------- fillets on the VERTICAL edges ----------------
# Those are the corners the hand really meets: picking up the instrument from
# the side you touch the edge of the outline in plan, not the rim of the back.
#
# The ears of the collar are left sharp on purpose: behind them there are the
# M3 inserts and a fillet would remove the material that holds them.
#
# The back is a polyline at half a degree, not a cylinder - that is how sett()
# builds the sectors - so there are hundreds of vertical edges, almost all
# junctions between two consecutive faces that turn by very little: picking
# them by proximity would fillet the faces of the discretisation.
Rr = D["R_fillet_edges_box"]

# ONLY ONE is filleted, the corner between the head and the back: it is the
# end of the shell on the pivot side, where the end of the electronic lobe
# used to be.
# On the opposite side there is no corner to round: the arc
# around the motor runs into the collar, and meets it in a RE-ENTRANT corner
# (about 80 degrees measured outside the part), which nothing can bump into.
#
# The head is a plane, not a sector, so the edge does not lie at an exact
# angle: it lies where the plane meets the polyline of the back. It is looked
# for on the PLANE, that is at t = outer face and at the radius of the back.
# Exactly one is demanded: a fillet put on the wrong face does not show in the
# volume and is found out in the hand.
def _head_edges(sol):
    found = []
    for e in sol.Edges():
        p0, p1 = e.startPoint(), e.endPoint()
        if abs(p0.x-p1.x) > 1e-6 or abs(p0.y-p1.y) > 1e-6 or abs(p1.z-p0.z) < 10.0:
            continue
        _s, _t = E.st(p0.x, p0.y)
        if abs(_t - E.T_HEAD_OUT) < 0.01 and math.hypot(p0.x, p0.y) > Ro - 1.0:
            found.append(e)
    return found


_to_fillet = _head_edges(box.val())
if len(_to_fillet) != 1:
    raise SystemExit("expected 1 vertical edge between head and back, found %d"
                     % len(_to_fillet))
box = cq.Workplane(obj=box.val().fillet(Rr, _to_fillet))
print("filleted the vertical edge between head and back (r %.1f); "
      "on the opposite side the arc over the motor reaches the collar in a "
      "re-entrant corner, which has no sharp edge" % Rr)

# ---------------- the grip for turning the wheel by hand ----------------
# Assembled, the knurled rim of the wheel sits under this box and the disc can
# no longer be turned by hand - found with the printed parts in hand, while
# the assembly guide asked for exactly that gesture.
# The grip gives the gesture back: the wall steps in until it passes below the
# radius of the clutch tread, and the tread stands out of the opening. The
# thumb rolls on it, and a little over half a turn moves one filter along.
#
# THE SHAPE IS MATTEO'S, and it is the only one the measurements leave: the
# tread is the one part of the clutch that reaches out this far - r 122.5
# against the r 127.5 of the inner face of the wall - so either the wall comes
# in under it or there is nothing to hold on to. The counter-proposal, a wider
# knurled hub below the tread, was measured out: Ø57 wants 28.5 mm of radius
# about the motor axis and the window in the wheel body leaves 27.
#
# NOTHING HERE IS DRAWN IN Z BY HAND. The opening is the sector that clears the
# clutch by Cl_grip_clutch (Halfw_grip_slot, cosine rule), and its two levels
# are the top and bottom of the clutch hub plus that same clearance: if the
# clutch moves or changes size, the opening follows.
#
# THE THREE SURFACES THAT WOULD HAVE WANTED SUPPORTS, and what was done to each
# - the box prints with the floor of the mechanical compartment on the bed, so
# every downward-facing surface inside it is an overhang nobody can reach to
# clean off:
#   1. the ceiling of the recess. Not built: the recess runs up THROUGH the top
#      of the wall, so there is no ceiling at all. What closes the compartment
#      up there is the stepped-in wall itself, which carries on to the top;
#   2. the floor the stepped-in wall would start from. The wall does not begin
#      in mid air: below Z_grip_box it SPLAYS back out at Ang_overhang_printing
#      until it meets the ordinary wall, nine and a half millimetres lower. The
#      splay is a cone about the wheel axis, so it is one face and not a stair;
#   3. the roof of the opening, the only genuine overhang left, two and a half
#      millimetres of wall thickness. It is cut with a cone and not with a flat
#      top, so the opening is taller on the outside than on the inside and the
#      roof leans at the same angle as the splay.
AG   = D["Halfw_grip_box"]
ASL  = D["Halfw_grip_slot"]
RG   = D["R_grip_box"]
RGi  = RG - W                            # inner face of the stepped-in wall
ZG   = D["Z_grip_box"]
ZTOP = Qsp + W                           # the recess reaches the top: no ceiling
# tangent of the overhang angle, measured from the VERTICAL: how far the
# surface moves horizontally for every millimetre it goes down
TSB  = math.tan(math.radians(D["Ang_overhang_printing"]))

# The splay ends where it meets the inner face of the normal wall again. The
# FARTHEST back of the window is taken: so the splay reaches all the way down
# on the side where the back has already stepped in too, and what is left
# over falls outside the part instead of leaving a step.
_rd_max = max(back_radius(AG*i/20.0) for i in range(-20, 21))
_h_splay = (_rd_max - W - RGi) / TSB
# The DIG goes down lower than the new wall does, by one wall thickness plus a
# millimetre. The reason: the dig reaches out to back_radius + 1, so until the
# cone has reached the BACK - not the inner face - its bottom still cuts
# something, and the bottom plane of the dig splits the back leaving a face for
# each stretch of the polyline with which sett() discretises it. Measured:
# thirty-eight faces of zero area in the solid. With the bottom brought to
# where the cone has already gone past the back, the dig no longer removes
# anything there and those faces are not born. Below _z_dish the new wall and
# the old one overlap and the part does not change: the same material is
# removed and put back.
_z_dish = ZG - _h_splay                       # where the new wall meets the old one again
_z_bottom = ZG - (_rd_max - RGi)/TSB - 1.0
_r_bottom = RGi + (ZG - _z_bottom)*TSB


def _cone(r_low, r_high, z0, z1):
    """A truncated cone about the wheel axis, from z0 to z1.
    With equal radii OCCT does not make a cone - "cone with two identic radii" -
    and wants a cylinder: both cases are needed, because above the recess the
    wall is straight and below it opens out."""
    o, d = cq.Vector(0, 0, z0), cq.Vector(0, 0, 1)
    if abs(r_high - r_low) < 1e-9:
        return cq.Solid.makeCylinder(r_low, z1 - z0, o, d)
    return cq.Solid.makeCone(r_low, r_high, z1 - z0, o, d)


# The core: everything that lies FURTHER IN than the inner face of the
# stepped-in wall, splay included. What is dug is the sector minus it.
_core = (_cone(_r_bottom, RGi, _z_bottom, ZG)
           .fuse(_cone(RGi, RGi, ZG, ZTOP + 1.0)))
_core_out = (_cone(_r_bottom + (RG - RGi), RG, _z_bottom, ZG)
               .fuse(_cone(RG, RG, ZG, ZTOP + 1.0)))

# The slices do NOT start from the axis: sett() with r0 = 0 and an outer radius
# that depends on the angle ends up in the polyline branch and puts n
# coincident points at the origin, that is edges of zero length which OCCT
# rejects. It is enough for the slice to start further in than the core,
# which lies at RGi.
_r_slice = RGi - 8.0
# TRUE ARCS: "the back plus one" and "the back" are inside() at
# offsets -1 and 0, sector cut by the arc about the motor. They were
# sett(... lambda a: back_radius(a) + 1.0), a polyline every half degree, and
# the splay under the cover came out as a fan of vertical facets.
_slice_wide = inside(-AG, AG, _r_slice, -1.0, _z_bottom, (ZTOP + 1.0) - _z_bottom)
_slice_exact = inside(-AG, AG, _r_slice, 0.0, _z_bottom, ZTOP - _z_bottom)

box = box.cut(_slice_wide.cut(cq.Workplane(obj=_core)))
box = box.union(_slice_exact.intersect(cq.Workplane(obj=_core_out))
                .cut(cq.Workplane(obj=_core)))

# The opening the tread stands out of, and its sloping roof.
_z_ap0 = D["Z_top_clutch"] - D["Cl_grip_clutch"]
_z_ap1 = D["Z_top_clutch"] + D["H_hub_clutch"] + D["Cl_grip_clutch"]
box = box.cut(inside(-ASL, ASL, _r_slice, -1.0, _z_ap0, _z_ap1 - _z_ap0))
box = box.cut(inside(-ASL, ASL, _r_slice, -1.0, _z_ap1, W)
              .cut(cq.Workplane(obj=_cone(RGi, RGi + W*TSB, _z_ap1, _z_ap1 + W))))

# ---------------- the cover of the grip, and its two grooves ----------------
# An opening next to the friction pair invites dust exactly where it must not
# land: the TPU ring carries the whole torque of the motor on 22.3 N, and every
# point of it becomes the contact point sooner or later. The cover closes the
# recess whenever the wheel is not being turned by hand, and from outside the
# box goes back to being the box it was - the cover remakes the profile of the
# back, flush.
#
# IT CANNOT BE A PLUG IN THE OPENING, and this was measured before it was
# drawn. The opening is a sector about the WHEEL axis while the clutch it
# clears is a cylinder about the MOTOR axis, so the hole comes out wider on the
# inside than on the outside: a plug that filled it would go in from inside the
# box and would need the machine taken apart to come off. Useless for a part
# whose whole purpose is to be lifted every time the filters are cleaned. So
# the cover is a lid over the recess instead, and it goes on and off with the
# box closed.
#
# HOW IT IS HELD. It slides DOWN two grooves, one in each end wall of the
# recess, and wedges on the splay at the bottom - the same 45 degree cone that
# keeps the stepped-in wall from starting in mid air does duty here as a seat,
# and it centres the cover radially for free. The tongues stop it coming out
# radially; a detent bead on each tongue, dropping into its dimple, stops it
# sliding back up. Nothing here needs supports: the grooves run vertically in
# vertical faces, and the beads are spheres on those same faces.
#
# HOW IT PRINTS: standing on its top face, which is the one flat plane it has.
# Every other face is then vertical or is the 45 degree seat, which points up.
_cl_t    = D["Cl_cover_grip"]
_th_t    = D["Th_cover_grip"]


def _ang_of(mm, r=Ro):
    """The angle that at radius r is worth those millimetres of arc. The
    dimensions of the cover are declared in millimetres - they are thicknesses
    and clearances, and in degrees they would not be understood - but the box
    is made of sectors, so here they are converted once only."""
    return math.degrees(mm / r)


_rd_min = min(back_radius(AG*i/20.0) for i in range(-20, 21))
_ag_t = AG - _ang_of(_cl_t)                    # half-width of the cover

# THE COVER FOLLOWS THE ROOF CHAMFER (the better of two ways tried). The
# chamfer is at r 120 by the time it reaches the roof, and the
# recess starts at r 120.1: the cover has no flat top left. So it is a plate
# of Th_cover_grip that follows the chamfered envelope - vertical below the
# slope, at 45 degrees along it - and the 45 degree plate is what closes the
# recess from above, which used to be the job of a flat flap on top. Built
# like the box: sectors up to an offset, cut by the arc and by the chamfer at
# the same offset, so every curved face is a TRUE ARC. The old plate followed
# back_radius() sampled every half degree, and came out as forty flat facets.
#
# IT PRINTS STANDING, as mounted, and that is why its bottom is now flat. It
# used to print upside down on its flat top, and its bottom was a 45 degree
# knife edge sitting on the splay, which centred it radially. Standing, that
# edge would be the face on the bed. The foot is flat, at the height where
# the splay cone meets the INNER face of the plate at its farthest: from
# there down there is nothing of the cover, and the whole foot clears the
# cone. Where the back is closer in - the arc side - the cone still clips the
# inner corner of the foot, and the cut below is what does it. Radially the
# lips keep it in place, as they did before.
def _envelope(a0, a1, r0, off, z, h):
    return inside(a0, a1, r0, off, z, h).intersect(chamfer(off))


_rd_max_in = max(back_radius(AG*i/20.0) for i in range(-20, 21)) - _th_t
_z_t0 = ZG - (_rd_max_in - RG - _cl_t)
_splay_cl = cq.Workplane(obj=_cone(_r_bottom + (RG - RGi) + _cl_t, RG + _cl_t, _z_bottom, ZG)
                         .fuse(_cone(RG + _cl_t, RG + _cl_t, ZG, ZTOP + 1.0)))

# the plate
_cover = (_envelope(-_ag_t, _ag_t, RG + _cl_t, 0.0, _z_t0, ZTOP - _z_t0)
          .cut(_envelope(-_ag_t - 1.0, _ag_t + 1.0, 0.5, _th_t, _z_t0 - 1.0, ZTOP + 2.0 - _z_t0)))
# NO LIPS AND NO DETENTS any more. The lip at +y
# ran down a groove that left a slit in the end wall of the recess, the lip at
# -y had gone with the arc about the motor, and the dimples of the detents were
# holes left in the box. The cover is now held by the L-section guides at the
# two ends of the recess and by the screw in the collar (the guides were later
# replaced by tabs, see how the cover is held, below).

# THE NOTCH FOR THE FINGERNAIL: a cover flush with the
# back cannot be gripped. It is a groove across the outer face,
# L_notch_cover_grip wide and centred on the axis of the clutch - where the
# grip is, so it can be found in the dark too.
#
# It sits on the VERTICAL face, just under the start of the
# chamfer: where it used to be, under the flat flap, the outer face now slopes
# in and the groove would have cut air. And it is turned upside down for the
# same reason the cover is: printed standing, the face that looks down is the
# CEILING of the groove, so that is the one that slopes at 45 degrees and
# closes towards the top, and the floor, which looks up, is flat. The nail
# pushes up into the wedge, which is the way the cover comes off.
_a_notch = _ang_of(D["L_notch_cover_grip"]/2)
_dp_notch = D["Dp_notch_cover_grip"]
_z_notch1 = Z_ROOF - CH - 0.5                   # the top, half a mm under the slope
_z_notch = _z_notch1 - D["H_notch_cover_grip"]     # the floor
_groove = sett(-_a_notch, _a_notch, _rd_max - _dp_notch, Ro + 2.0,
             _z_notch, D["H_notch_cover_grip"])
# TURNED OVER AGAIN with the cover: it now prints upside down,
# so the face that looks down on the bed side is the FLOOR of the groove. The
# floor slopes at 45 degrees and the ceiling is flat - which is also the face
# the nail pulls up on.
_groove = _groove.cut(cq.Workplane(obj=_cone(_rd_max, _rd_max - _dp_notch,
                                         _z_notch, _z_notch + _dp_notch)))
_cover = _cover.cut(_groove)
_cover = _cover.cut(_splay_cl)

# ---------------- how the cover is held ----------------------------------
# The L-section guides were rejected: too delicate, and right where the finger
# rubs. Of the three ways sketched, the one built: THICK TABS at the foot of the
# cover dropping into pockets in the box, plus, at +y only, a TONGUE at the
# end of the cover in a groove of the end wall. The rim under the door plate
# of the sketch was not built: measured, under the roof slab there is no wall
# for it to bear on (the arc wall is 1 mm outside the opening, the collar lip
# 1 mm below it), so it added nothing to the grip the plate already has.
#
# THE TABS are thick because of how the cover prints - upside down, so a tab
# hanging from its foot is the last thing printed, its layers across its
# length, and it breaks between layers if it is thin. Th_tab_cover_grip
# radially, W_tab_cover_grip wide, and a root that runs up the inner face of
# the cover. They stand where the back is the circle about the wheel: there
# the splay meets the back below the foot of the cover, and there is material
# to cut a pocket in. Towards -y the back becomes the arc about the motor and
# the splay meets it higher than the foot: the -y tab goes as far that way as
# the back stays within W/2 of the circle, and that is measured here, not chosen.
_tt, _wt, _lt = D["Th_tab_cover_grip"], D["W_tab_cover_grip"], D["L_tab_cover_grip"]
_pw = D["Wall_pad_cover_grip"]
_h_root = _tt + 1.0                   # the root of the tab, above the foot


def _band(a0, a1, off0, off1, z0, z1):
    """The band between two offsets from the back, off0 outside, off1 inside."""
    return (inside(a0, a1, _r_slice, off0, z0, z1 - z0)
            .cut(inside(a0 - 1.0, a1 + 1.0, _r_slice, off1, z0 - 1.0, z1 - z0 + 2.0)))


_da_t = _ang_of(_wt/2, RG + 5.0)
_da_p = _da_t + _ang_of(_cl_t + _pw, RG + 5.0)
_a_minus = None
_a = 0.0
while _a > -AG:
    # within half a wall of the circle: for a < 0 the back is already the arc
    # about the motor, which leaves the circle at 0 and comes in by tenths.
    # The pad and the pocket are built as offsets from the REAL back, so they
    # follow it; what limits them is the splay meeting the back higher up.
    if all(back_radius(_a + _da_p*k/5.0) >= Ro - W/2 for k in range(-5, 6)):
        _a_minus = _a
    _a -= 0.25
if _a_minus is None:
    raise SystemExit("cover: there is no round back for the tab towards -y")
TAB_ANGLES = (_a_minus, D["Ang_tab_cover_grip"])
_z_pocket0 = _z_t0 - _lt - _cl_t                      # bottom of the pocket
_z_pad_back = _z_pocket0 - _pw - (_tt + _cl_t + 0.5)  # underside of the pad, at the back
for _a in TAB_ANGLES:
    # the root runs up the inner face of the cover by Ht_root: where the back
    # is the arc, the cover ends higher than its flat foot (it follows the
    # splay), and a root that stopped at the foot would hang from nothing
    # and the top of the root slopes at 45 degrees, highest against the cover:
    # the cover prints upside down, and a flat top there is a 30 mm2 ceiling
    _R_root = Ro - _th_t + 0.5
    _z_root = _z_t0 + _h_root
    _chamfer_root = cq.Workplane(obj=_cone(_R_root - _tt - 1.0, _R_root + 5.0,
                                         _z_root - _tt - 1.0, _z_root + 5.0))
    _cover = _cover.union(_band(_a - _da_t, _a + _da_t, _th_t - 0.5, _th_t + _tt,
                                  _z_t0 - _lt, _z_root).cut(_chamfer_root))
print("cover tabs at %s degrees: %.1f x %.1f, %.1f long"
      % (", ".join("%+.2f" % a for a in TAB_ANGLES), _tt, _wt, _lt))

# THE TONGUE at +y: a radial fin at the end of the cover, from its inner face
# in towards the stepped-in wall, whose tip goes Dp_groove_cover_grip into a
# groove of the end wall. The end wall is made thicker to take it.
_r_tongue0 = (RG + (Ro - W))/2 - D["W_groove_cover_grip"]/2 + _cl_t
_r_tongue1 = _r_tongue0 + D["W_groove_cover_grip"] - 2*_cl_t
_a_tongue1 = AG + _ang_of(D["Dp_groove_cover_grip"], _r_tongue1)
_tongue_fin = (sett(_ag_t - _ang_of(2.0, _r_tongue0), _ag_t, _r_tongue0, Ro + 2.0, _z_t0, ZTOP - _z_t0)
          .union(sett(_ag_t - _ang_of(1.0, _r_tongue0), _a_tongue1, _r_tongue0, _r_tongue1,
                      _z_t0, ZTOP - _z_t0))
          .intersect(inside(-AG - 1.0, AG + 5.0, _r_slice, _th_t - 0.5, _z_t0, ZTOP - _z_t0)
                     .union(sett(AG - 1.0, AG + 5.0, _r_tongue0, _r_tongue1, _z_t0, ZTOP - _z_t0)))
          .intersect(chamfer(0.0))
          # and it stops above the splay, like the rest of the cover
          .cut(_splay_cl))
_cover = _cover.union(_tongue_fin)
_cover = cq.Workplane(obj=_cover.val().clean())

# ---------------- the end wall of the recess, on the side of the pivot ------
# This wall is closed. At the +y
# end of the recess there was nothing between the stepped-in wall and the back
# - the lip of the cover runs down there, behind the back, and past the lip
# groove the compartment was open: with the cover off, the arm and the spring
# could be seen and reached from outside. Only the lip closed it, and only
# while the cover was on. The -y end did not have the defect: there the
# stepped-in wall meets the arc about the motor.
#
# The wall stands just past the lip groove, W thick at the inner face of the
# stepped-in wall, from that face out to the back and up to the roof, so the
# groove becomes a blind slot. Its underside is a cone at 45 degrees about the
# wheel axis, lowest against the back: the box prints on its floor, and a flat
# underside here would be an overhang with nothing below it.
# FROM THE EDGE OF THE RECESS since the lips went: the lip groove between the
# stepped-in wall and this wall was a slit through the wall, so the wall is
# joined to the body. A tenth of a
# millimetre INTO the recess, so it overlaps the end of the stepped-in wall
# instead of touching it; the cover ends Cl_cover_grip short of that plane.
_a_end = AG - _ang_of(0.1, RGi)
# thicker by the depth of the groove the cover's tongue runs in
_a_endwall = _a_end + _ang_of(W + D["Dp_groove_cover_grip"], RGi)
_z_endwall = _z_dish - (_rd_max - RGi)
# Its outer face stops HALF A WALL inside the back, not on it: inside the
# recess that face lay on the outer skin of the back, which the recess had
# cut away, and the union came out as an invalid solid (measured: valid before
# the union, invalid after, fixed by this and nothing else). Past the edge of
# the recess the back is there and covers the other half.
_endwall = inside(_a_end, _a_endwall, RGi, W/2, _z_endwall, ZTOP - _z_endwall)
_endwall = _endwall.cut(cq.Workplane(obj=_cone(_rd_max, RGi, _z_endwall, _z_dish)))
box = box.union(_endwall)
print("end wall of the recess on the pivot side: %.2f..%.2f degrees, from r %.1f, bottom at 45 degrees from z %.2f"
      % (_a_end, _a_endwall, RGi, _z_dish))

# the groove for the tongue of the cover, open at the top: the cover drops in
box = box.cut(sett(AG - 0.5, _a_tongue1 + _ang_of(_cl_t, _r_tongue1),
                   _r_tongue0 - _cl_t, _r_tongue1 + _cl_t,
                   _z_t0 - _cl_t, ZTOP + 1.0 - (_z_t0 - _cl_t)))
# the pads under the tabs, and the pockets in them. The pad fills the wedge
# under the foot of the cover and hangs inside the box below the splay; its
# underside is a cone at 45 degrees, lowest against the back, so the box still
# prints on its floor without supports. Its top is the seat of the cover.
_R_in = Ro - W
_below_pad = cq.Workplane(obj=_cone(_R_in + 30.0, _R_in - 15.0, _z_pad_back - 30.0, _z_pad_back + 15.0))
# THE POCKET CROSSES THE SPLAY, and at both its faces it left a sliver
# (check_thin). Above the pad the pocket runs up through the 45
# degree splay: its inner face cuts the splay's underside and leaves a wedge
# hanging off it, 0 to 0.8 mm over z -3.6..-2.8, with nothing under it; its
# outer face, 0.3 outside the pad, meets the splay's outer face and leaves a
# skin tapering to nothing over z -6.0..-5.2. Two different cures, because
# the two slivers are different:
# - the INNER wall of the pad goes on up until it meets the splay's
#   underside (what it fills is inside _core, the void under the splay):
#   the wedge becomes the top of a 2 mm wall, and the pad top that is the
#   seat of the cover is not touched - it is outside this wall;
# - the OUTER skin is taken away from where it is Th_min_wall_printing thick
#   up, as wide as the pocket: that stretch of skin held nothing (the tab is
#   located by the pocket's faces below it), and the level is derived from the
#   splay, at the largest back radius, which is where the skin is thinnest.
_tm = D["Th_min_wall_printing"]
_off_pocket_out = _th_t - 0.5 - _cl_t               # outer face of the pocket, from the back
_z_skin = ZG - ((Ro - _off_pocket_out + _tm) - RG)/TSB
for _a in TAB_ANGLES:
    _pad = (_band(_a - _da_p, _a + _da_p, W - 0.5, _th_t + _tt + _cl_t + _pw,
                    _z_pad_back - 30.0, _z_t0 - _cl_t)
            .cut(_below_pad))
    box = box.union(_pad)
    box = box.union(_band(_a - _da_p, _a + _da_p, _th_t + _tt + _cl_t - 0.01,
                            _th_t + _tt + _cl_t + _pw, _z_t0 - _cl_t - 0.01, ZG)
                    .intersect(cq.Workplane(obj=_core)))
    _da_pocket = _da_t + _ang_of(_cl_t, RG + 5.0)
    box = box.cut(_band(_a - _da_pocket, _a + _da_pocket,
                          _th_t - 0.5 - _cl_t, _th_t + _tt + _cl_t, _z_pocket0, _z_t0 + _h_root + _cl_t))
    box = box.cut(_band(_a - _da_pocket, _a + _da_pocket, -1.0, _off_pocket_out + 0.01,
                          _z_skin, _z_t0 + _h_root + _cl_t))
print("cover pockets: inner wall up to the splay, outer skin taken away above z %.2f"
      % _z_skin)

# THE CHAMFER, on the outside: the last cut on the box, so that nothing added
# after the shell - the grip, its cover grooves - can stand proud of the
# sloping face. The inside was chamfered with the void, above.
#
# ONLY ABOVE THE START OF THE SLOPE, and that is not a detail. The first
# version intersected the whole box with the chamfered envelope, which below
# the slope is just the outer skin - and it trimmed flush the one thing that
# stands out of the back ON PURPOSE: the end of the spring boss, a millimetre
# proud of r 130 so that the M4 insert and the wall that retains it fit in
# full. 0.08 mm of ASA were left between the insert and the outside; the
# audit said so.
_above_slope = cq.Workplane(obj=cq.Solid.makeBox(
    400.0, 400.0, 100.0, cq.Vector(-200.0, -200.0, Z_ROOF - CH)))
box = box.cut(_above_slope.cut(chamfer(0.0)))
box = cq.Workplane(obj=box.val().clean())

# (the cover is finished and written after the door over the motor, below:
# it also closes that door)

# THE SOLID MUST BE CHECKED BEFORE WRITING IT. Once, breaking the box on
# purpose to test the new checks, the generator wrote without a murmur an
# INVALID box.step - zero solids, volume 70 cm3 instead of 97 - and the defect
# came out only thirty minutes later, inside the audit, in the form of "Null
# TopoDS_Shape object" in a check that had nothing to do with it. An hour of
# build to find out that the part did not exist. Here it costs a tenth of a
# second and says so at once, with the right name.
if not box.val().isValid() or len(box.val().Solids()) != 1:
    raise SystemExit("box: the solid is not valid - %d solids, %.1f cm3. "
                     "It is not written: downstream no boolean operation "
                     "would hold, and the error would come out elsewhere."
                     % (len(box.val().Solids()), box.val().Volume()/1000))
from parameters import out_subdir
cq.exporters.export(box, OUT + out_subdir("box") + "box.step")

print("shell of the box %.1f cm3 | spring cup %.2f cm3"
      % (box.val().Volume()/1000, cup.val().Volume()/1000))


# ==========================================================================
# THE ONE-PIECE PART: box + collar
# ==========================================================================
# Why it exists. They used to be two parts screwed together, and the printed
# parts showed that joint cost three defects: the box
# did not pass over the screw of the pivot while it was being slid on, an ear
# of the collar snapped while sliding it on, and the ten pieces of hardware of
# the joint were ten chances of getting it wrong. Joined, two defects out of
# three disappear by
# construction - there is no longer a sliding on to get wrong.
#
# THE COLLAR IS READ BACK FROM DISK, it is not rebuilt here. Its geometry -
# bore, flanges, small window, gasket grooves - is tied to the wheel and lives
# in solids_body_collar.py, which runs first. Reading it back is what
# solids_assembly.py already does, and it is the only way not to keep two
# thousand lines of geometry in two copies that diverge at the first touch-up.
_shell = cq.importers.importStep(OUT + out_subdir("collar") + "collar.step")
part = box.union(_shell)

# --- the door over the motor -----------------------------------------------
# One opening only for two jobs, and it is the price of the union: with the
# compartment closed on all sides the motor no longer goes in from the side.
# It must let it drop in from above - 35.2 x 53.2 in plan, measured on the
# maker's STEP - and give the screwdriver the column above its four screws,
# which without a door stops 13 mm from the roof.
#
# THE EDGE AT 121 AND NOT AT 119.5, and it is not a rounding: at 119.5 a 0.6 mm
# flake - 26 mm3 - was left attached, detached from the rest of the part. It
# was not the shell cut in two, but in a printed part a flake is stuff that
# comes off in the bag. The count of solids below showed it, which is the
# reason that count is there.
DOOR_X = (D["Edge_opening_motor_box"], 121.0)
DOOR_Y = (-30.0, 30.0)
# THE HEIGHT THE CUT STARTS FROM IS Z_shoulder_box, NOT ZB. At the first go it
# was ZB (28.5), which is the upper end of the SECTOR the compartment is built
# with, not its roof: the roof is the slab at Z_shoulder_box..+Th_walls_box,
# that is 16..18.5, and a cut starting at 28.5 passes over the slab without
# touching it. The part came out without a door and looked right - it showed
# only in the STEP, because the arm no longer went in.
_z_door = D["Z_shoulder_box"] - 1.0
_door = (cq.Workplane("XY")
          .box(DOOR_X[1]-DOOR_X[0], DOOR_Y[1]-DOOR_Y[0], 60)
          .translate(((DOOR_X[0]+DOOR_X[1])/2, (DOOR_Y[0]+DOOR_Y[1])/2,
                      _z_door + 30))).val()
# ON THE ARC SIDE the door stops one millimetre short of the inner face of the
# arc wall. The rectangle reached y -30, and the arc wall now
# stands at 30 from the shaft: the door would have notched the wall. Stopping
# exactly ON the inner face would put two faces on the same cylinder, which is
# how this part once got 197 empty laminae (see _void). The motor still drops
# in: its widest point, the connector, is 26.6 from the shaft.
_door = _door.intersect(cq.Solid.makeCylinder(RA - W - 1.0, 200.0,
                                                cq.Vector(MX, MY, -100.0)))
part = part.cut(cq.Workplane(obj=_door))
# THE MOTOR'S WAY DOWN (the motor goes in first, straight down from the
# top). The door above stops at z 24.5, and below it the collar
# ring - r 79.5..86.5, from z 14 - stood across the motor's path over 6 mm:
# 1009 mm3, measured by sliding the maker's motor down. (The 24 mm3 it seemed
# to meet in the roof outside the door were its leads, which the maker's STEP
# draws as rigid bars: they bend, and the silhouette leaves them out - see
# outline_motor.py.) So the cut is the motor's own
# silhouette plus Cl_entry_motor (outline_motor.py), from the bottom of the
# motor up through the roof: only what its way down takes, and it follows the
# motor if the motor moves. Dropping it shifted out and sliding it in was
# measured too: it saves collar only by notching the outer arc wall.
part = part.cut(MOTOR_SILHOUETTE)
# ...AND ACROSS THE COLLAR RING, ALL THE WAY THROUGH. The silhouette is cut by
# a straight line (its square face) and the inside of the ring is a cylinder:
# where the two nearly meet, the ring was left as a blade 0.27 mm thick, at r
# 79.5, +-8 degrees, z 14..21 - found by check_thin.py. A straight
# cut crossing a cylinder always leaves a point where the rest goes to zero. So
# over the angles where the silhouette crosses the ring, the ring goes whole,
# from the wheel body out, with radial ends: a band derived from the
# silhouette, not drawn by hand. Only
# from the face of the wheel up (z 0): below is the new floor.
_r_ring = (D["D_body"]/2 - 0.5, D["R_out_collar"] + 0.5)
_ang_sil = [math.degrees(math.atan2(v.Y, v.X)) for v in
            MOTOR_SILHOUETTE.intersect(sett(-60, 60, _r_ring[0], _r_ring[1], 0.0, 30.0)).val().Vertices()]
# ...AND WIDE ENOUGH FOR THE CLUTCH TO COME IN FROM THE WHEEL SIDE (assembly
# strategy C). On the shaft the clutch is caged - it touches the
# roof after 1 mm of the 13 it needs to leave the shaft - so it goes in first,
# sliding radially out from the middle of the collar, before the wheel is in.
# Slid that way through the ring cut for the motor alone, it met the two
# corners of the ring at y +-22..25 for 52 mm3 each: the tread is 50 wide,
# the motor 35. So the ring goes over the angles of the clutch's radial sweep
# too - the clutch's own width, read from its STEP, plus Cl_entry_clutch -
# and the cut follows the clutch if it grows.
_clutch = (cq.importers.importStep(OUT + "clutch_hub.step").val()
       .fuse(cq.importers.importStep(OUT + "clutch_tyre.step").val()))
_bcl = _clutch.BoundingBox()
_ycl = max(abs(_bcl.ymin), abs(_bcl.ymax)) + D["Cl_entry_clutch"]
_clutch_sweep = (cq.Workplane("XY").workplane(offset=_bcl.zmin - 1.0)
                .center((_bcl.xmax + 0.0)/2, 0.0).rect(_bcl.xmax, 2*_ycl)
                .extrude(_bcl.zlen + 2.0))
_ang_sil += [math.degrees(math.atan2(v.Y, v.X)) for v in
             _clutch_sweep.intersect(sett(-60, 60, _r_ring[0], _r_ring[1], 0.0, 30.0)).val().Vertices()]
_ring_before = part.intersect(sett(min(_ang_sil), max(_ang_sil), _r_ring[0], _r_ring[1], 0.0, 40.0))
part = part.cut(sett(min(_ang_sil), max(_ang_sil), _r_ring[0], _r_ring[1], 0.0, 40.0))
print("collar ring cut for the motor from %.1f to %.1f degrees" % (min(_ang_sil), max(_ang_sil)))

# ---- THE FILLET BETWEEN THE COLLAR AND THE ARC ROUND THE MOTOR, -y side ----
# The ring cut that
# lets the clutch in from the middle of the collar runs to -19.3 degrees, and
# on the -y side that is past the arc round the motor: at r 79.5..86.5 it
# left the ring open to the outside, a slot where the collar meets the arc.
# Closed from outside with a concave fillet between the two circles - the
# collar's outer face (R_out_collar about the wheel axis) and the arc wall
# (RA about the motor axis) - tangent to both, R_fillet_collar_arc. What the
# clutch sweeps on its way in is cut out of it again: the clutch must still
# pass.
_Rf = D["R_fillet_collar_arc"]
_R1, _R2 = D["R_out_collar"], RA
_d = MX
# centre of the fillet circle: |C| = R1 + Rf, |C - M| = R2 + Rf, on -y
from parameters import collar_arc_fillet as _collar_arc_fillet
_cx, _cy, _t1, _t2 = _collar_arc_fillet()          # centre; tangency on the collar, on the arc
# up to where the roof chamfer of the arc starts: the fillet is outside the
# box's chamfered envelope (that envelope is the lobe's), and cut by it, as
# in the first try, nothing of it was left
# and from the bottom of the collar, not of the box: below it there is no
# collar face for the fillet to meet
_zf0, _zf1 = -D["Th_flange_collar"], Z_ROOF - CH
_quad = (cq.Workplane("XY").workplane(offset=_zf0)
         .polyline([(0.0, 0.0), _t1, (_cx, _cy), _t2, (MX, MY)]).close()
         .extrude(_zf1 - _zf0))
_web = (_quad.cut(cq.Workplane("XY").workplane(offset=_zf0 - 1).center(_cx, _cy)
                  .circle(_Rf).extrude(_zf1 - _zf0 + 2))
        .cut(cq.Workplane("XY").workplane(offset=_zf0 - 1).circle(_R1 - 0.5)
             .extrude(_zf1 - _zf0 + 2))
        .cut(cq.Workplane("XY").workplane(offset=_zf0 - 1).center(MX, MY).circle(_R2 - 0.5)
             .extrude(_zf1 - _zf0 + 2)))
_web = _web.cut(_clutch_sweep) if "_clutch_sweep" in globals() else _web
# ...AND THE RING PUT BACK where nothing passes. The fillet alone closed only
# the outer mouth: the slot was the ring cut itself, which on its outer angles
# runs past the arc round the motor and takes away the foot of the arc wall
# too - material neither the motor nor the clutch needs. So over the angles of
# the ring cut, in the ring band and above the wheel face, the ring comes back
# except inside the compartment round the motor (RA - W about the motor axis)
# and except the clutch's own way in. Seen from outside nothing is open.
# The ring as it WAS before the cut, not a band rebuilt by hand (a band
# lost the collar's own top and, outside the lobe's chamfered envelope, left
# a hole seen from above), less what the cut is for: the
# compartment round the motor, the clutch's way in, the motor's silhouette,
# and the room of the cover's piece that closes the cut from above - that
# piece lies inside the lobe's envelope, and the ring keeps Cl_cover_grip
# from it above the roof's underside (at first it met it for 67 mm3).
_cover_above = (chamfer(-D["Cl_cover_grip"])
                 .union(cq.Workplane(obj=cq.Solid.makeCylinder(
                     _r_ring[1] + D["Cl_cover_grip"], 200.0, cq.Vector(0, 0, -100.0))))
                 .intersect(cq.Workplane("XY").workplane(offset=Qsp - D["Cl_cover_grip"])
                            .rect(600, 600).extrude(40.0)))
# the compartment round the motor is left open only BELOW the roof: in the
# roof's thickness the ring comes back wherever the cover's piece is not.
# Cutting the compartment at every height left the roof open at x 78,
# y -14..-22, where the cover's piece stops at the lobe's envelope - a hole
# through the top since strategy C widened the ring cut
_ring_back = (cq.Workplane(obj=_ring_before.val())
              .cut(cq.Workplane("XY").workplane(offset=-1.0).center(MX, MY)
                   .circle(RA - W).extrude(Qsp + 1.0))
              .cut(_clutch_sweep)
              .cut(MOTOR_SILHOUETTE)
              .cut(_cover_above))
_web = _web.union(_ring_back)
# ...AND RAISED TO THE ROOF on the collar's side of the ring cut, up to where
# the insert has to go, and enlarged as needed. The cover's second screw is there, vertical,
# its tab in a pocket at the top of the collar, and that pocket reaches past
# the collar's outer face: the fillet is its outer wall. On the arc's side of
# the cut the fillet keeps stopping at the chamfer's foot - above it is the
# chamfer band, which is the cover's.
from parameters import fillet_screw as _fillet_screw
_xv2, _yv2, _a_cut2 = _fillet_screw()
if abs(math.degrees(_a_cut2) - min(_ang_sil)) > 0.05:
    raise SystemExit("second screw of the cover: the ring cut is at %.2f degrees, "
                     "parameters.fillet_screw puts it at %.2f - has the clutch changed?"
                     % (min(_ang_sil), math.degrees(_a_cut2)))
_web_top = (cq.Workplane("XY").workplane(offset=_zf1)
           .polyline([(0.0, 0.0), _t1, (_cx, _cy), _t2, (MX, MY)]).close()
           .extrude(Z_ROOF - _zf1)
           .cut(cq.Workplane("XY").workplane(offset=_zf1 - 1).center(_cx, _cy)
                .circle(_Rf).extrude(Z_ROOF - _zf1 + 2))
           # the quad runs to the wheel axis: without the collar's cylinder
           # taken off, as below the foot, it was a slab across the wheel
           .cut(cq.Workplane("XY").workplane(offset=_zf1 - 1).circle(_R1 - 0.5)
                .extrude(Z_ROOF - _zf1 + 2))
           # inwards it runs on to the inside of the arc's chamfer, not to the
           # arc's outer face: stopped there, between it and the chamfer band
           # it stood as a horn, joined to the wall only at its foot, with a
           # V open from above and a point at the chamfer's foot, with
           # nothing to keep it from joining the wall
           .cut(chamfer(W).union(cq.Workplane("XY").workplane(offset=_zf1 - 1).center(MX, MY)
                                .circle(RA - W).extrude(Z_ROOF - _zf1 + 2)))
           .cut(_clutch_sweep))
# ...WITH THE ARC'S OWN CHAMFER, except round the pocket. The arc round the
# motor has a 45 degree chamfer from the foot at z _zf1 inwards; the fillet
# gets the same, measured from ITS outer face - a cone about the fillet's
# axis, z = _zf1 + (distance from that face) - and at the tangency on the arc
# the two chamfers are one surface. Round the pocket it keeps full height out
# to the pocket's wall, and comes down from there at 45 degrees too (a cone
# about the insert's axis). Tried and rejected: full height up to
# the ring cut ended on a vertical face ten millimetres tall beside the chamfer
# band, with a V under it; the cone about the insert alone left a sharp spike
# where it met the fillet's face.
_s0_w = D["R_tab_cover"] + D["Cl_cover_grip"] + 2*D["Th_min_wall_printing"]
_h_w = Z_ROOF - _zf1
_fillet_chamfer = cq.Workplane(obj=cq.Solid.makeCone(
    _Rf, _Rf + _h_w + 2.0, _h_w + 2.0, cq.Vector(_cx, _cy, _zf1)))
_pocket_top = cq.Workplane(obj=cq.Solid.makeCone(
    _s0_w + _h_w + 1.0, _s0_w - 1.0, _h_w + 2.0, cq.Vector(_xv2, _yv2, _zf1 - 1.0)))
# the top is the higher of the fillet's chamfer and the arc's own (inside the
# lobe's chamfered envelope): filled in to the arc, the fillet's chamfer alone
# would have left the inner part standing full height over the arc's slope
_web_top = _web_top.cut(_fillet_chamfer.cut(_pocket_top).cut(chamfer(0.0)))
# over the ring cut it leaves the cover's room, as the ring put back does: the
# door's plate runs out to r 86.2 there, and met it for 0.08 mm3
_web_top = _web_top.cut(_cover_above.intersect(
    sett(math.degrees(_a_cut2), 60.0, 0.0, 200.0, -50.0, 100.0)))
_web = _web.union(_web_top)
part = part.union(_web)
print("collar-arc fillet at -y: R %.1f, tangent to the collar at (%.1f, %.1f) and to the arc at (%.1f, %.1f), %.2f cm3"
      % (_Rf, _t1[0], _t1[1], _t2[0], _t2[1], _web.val().Volume()/1000))

# ---- THE CHAMFER UNDER THE COLLAR FLANGE, towards the wheel axis ----------
# The inside corner between the underside of the flange and the outer face of the
# inner wall gets a 45 degree chamfer, L_chamfer_below_flange, and it runs on
# round the -y corner along the arc round the motor. The part prints on its
# floor, and that corner was a flat ceiling. Three pieces, since the corner of
# the lower box in plan is convex: a wedge along the inner wall (about the
# wheel axis) up to the corner's angle, a wedge along the arc (about the motor
# axis) beyond it, and a cone about the corner's vertical edge between them -
# together, every point within (z - z_bottom) of the lower box's outline.
# Kept only UNDER MATERIAL: the footprint of the part just above the flange's
# underside, read from the solid, so the wedge never hangs under nothing and
# follows the collar-arc fillet where that overhangs too.
_Cf = D["L_chamfer_below_flange"]
_zfl = -D["Th_flange_collar"]
_zfb = _zfl - _Cf                                     # where the chamfer meets the walls
_xc = (RP0*RP0 - RA*RA + MX*MX)/(2.0*MX)
_yc = -math.sqrt(RP0*RP0 - _xc*_xc)                   # the lower box's corner, -y side
_th_c = math.degrees(math.atan2(_yc, _xc))
_wedge_in = (cq.Workplane(obj=cq.Solid.makeCylinder(RP0 + 0.3, _Cf + 0.3, cq.Vector(0, 0, _zfb - 0.3)))
             .cut(cq.Workplane(obj=cq.Solid.makeCone(RP0 + 0.3, RP0 - _Cf, _Cf + 0.3,
                                                     cq.Vector(0, 0, _zfb - 0.3))))
             .intersect(sett(_th_c, AM1 + 5.0, 0.0, 200.0, _zfb - 1.0, _Cf + 2.0))
             .cut(beyond_head(E.T_HEAD_OUT)))
_wedge_arc = (cq.Workplane(obj=cq.Solid.makeCone(RA - 0.3, RA + _Cf, _Cf + 0.3,
                                                  cq.Vector(MX, MY, _zfb - 0.3)))
               .cut(cq.Workplane(obj=cq.Solid.makeCylinder(RA - 0.3, _Cf + 2.0,
                                                           cq.Vector(MX, MY, _zfb - 1.0))))
               # beyond the corner, on the -y side only
               .intersect(cq.Workplane(obj=cq.Solid.makeBox(200.0, 200.0, _Cf + 2.0,
                                                            cq.Vector(-50.0, -200.0, _zfb - 1.0))))
               .cut(sett(_th_c, 180.0, 0.0, 300.0, _zfb - 2.0, _Cf + 4.0)))
_cone_c = cq.Workplane(obj=cq.Solid.makeCone(0.0, _Cf + 0.3, _Cf + 0.3,
                                             cq.Vector(_xc, _yc, _zfb - 0.3)))
_wedge = _wedge_in.union(_wedge_arc).union(_cone_c)
# under material only: the faces of the part that look down at the flange's
# underside, pushed down through the chamfer's height
_slice = part.intersect(cq.Workplane("XY").workplane(offset=_zfl).rect(600, 600).extrude(0.1)).val()
_below = None
for _f in _slice.Faces():
    if _f.geomType() == "PLANE" and _f.normalAt().z < -0.99 and abs(_f.Center().z - _zfl) < 1e-3:
        _pr = cq.Solid.extrudeLinear(_f, cq.Vector(0, 0, -(_Cf + 1.0)))
        _below = _pr if _below is None else _below.fuse(_pr)
_wedge = _wedge.intersect(cq.Workplane(obj=_below))
# the reading window stays open, and readable at a slant: its outline at the
# flange, widening at 45 degrees downwards (a trapezoid in section)
_rw0, _rw1 = D["R_in_window_numbers"], D["R_out_window_numbers"]
_lw = D["L_window_numbers"]
_win = (cq.Workplane("XY").workplane(offset=_zfl + 0.01).center((_rw0 + _rw1)/2, 0.0)
        .rect(_rw1 - _rw0, _lw)
        .workplane(offset=-(_Cf + 1.5)).rect(_rw1 - _rw0 + 2*(_Cf + 1.5), _lw + 2*(_Cf + 1.5))
        .loft()
        .rotate((0, 0, 0), (0, 0, 1), D["Ang_window_numbers"]))
_wedge = _wedge.cut(_win)
# and the iron's channel runs on through it, along its own axis, from where it
# crosses the wall to past the chamfer's foot
_s_c1 = _s_at_r(RP0 - _Cf - 1.5)
_wedge = _wedge.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
    _r_chan, _s_g0 - _s_c1, cq.Vector(_Qxf + _nxf*_s_c1, _Qyf + _nyf*_s_c1, _zmf),
    cq.Vector(_nxf, _nyf, 0))))
part = part.union(_wedge)
print("chamfer under the flange: %.0f mm at 45 degrees, from the head to the corner at %.1f degrees and along "
      "the arc, %.2f cm3" % (_Cf, _th_c, _wedge.val().Volume()/1000))

# ---------------- the hatch under the motor, and its cover ----------------
# ASSEMBLY STRATEGY B: the arm goes in first, then the
# motor comes UP from below, through a hatch in the floor, and the cover closes
# it. Motor first and arm after is impossible: over the pivot half of the arm
# the pivot column and the collar ring are solid up to the sky, and with the
# shaft in its hole the arm has no way out (path search, src/study_paths).
#
# THE OUTLINE (outline_motor.hatch): the motor's silhouette swept over the
# whole travel of the arm, grown by Cl_hatch_motor - Cl_entry_motor plus one
# lead, because the leads bend down along the body on the way up and a hatch
# wider all round is simpler than a slot for them - and boxed
# into a rounded rectangle. On the side of the wheel axis it stops at the
# outer face of the inner wall: it must not bite its foot, and there is no
# stop on that side, as for the panel by the skirt.
#
# LIKE THE PANEL: flush with the floor, a stop Stop_panel wide on the outer
# half of the floor thickness, two ears Th_panel_screws thick sunk into the
# floor, the floor raised over them, M3 countersunk screws from below into
# inserts planted from below with the cover off.
import outline_motor as _OM
_B = _OM.hatch()
_Z_BOSSES_B = E.Z_SCREWS + D["L_insert_M3"] + 1.0
_G_B = D["Cl_panel"] + D["Cl_panel_box"]
_z_mot = _OM.motor_bottom()


def _hatch(d, z0, z1):
    """The hatch outline grown by d, from z0 to z1."""
    w = (cq.Workplane("XY").workplane(offset=z0).center(_B["xc"], _B["yc"])
         .rect(_B["lx"] + 2*d, _B["ly"] + 2*d).extrude(z1 - z0))
    return w.edges("|Z").fillet(_B["r"] + d) if _B["r"] + d > 0.01 else w


def _outside_wall(extra=0.0):
    return (cq.Workplane("XY").workplane(offset=-100.0)
            .circle(E.R_INNER_WALL[1] + extra).extrude(200.0))


def _ear(xv, yv, side, g, widen):
    """The ear of the screw at (xv, yv): outline_motor.hatch_ears, which
    check_arc_back reads too."""
    return _OM.hatch_ears(g, widen)[[v[:2] for v in _B["screws"]].index((xv, yv))]


def _rect(r, z0, z1):
    x0, x1, y0, y1 = r
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


_inside_arc = (cq.Workplane("XY").workplane(offset=ZT - 5.0).center(MX, MY)
                .circle(RA - 0.5).extrude(40.0))
for _xv, _yv, _l in _B["screws"]:
    # the raised floor over the ear, one wall wider on its free sides
    part = part.union(_rect(_ear(_xv, _yv, _l, 0.0, W), ZT + W, E.Z_SCREWS + W)
                        .intersect(_inside_arc))
    part = part.union(cq.Workplane("XY").workplane(offset=E.Z_SCREWS).center(_xv, _yv)
                        .circle(D["D_boss_panel"]/2).extrude(_Z_BOSSES_B - E.Z_SCREWS))
part = part.cut(_hatch(0.0, ZT - 1.0, _z_mot + 1.0).cut(_outside_wall()))
part = part.cut(_hatch(D["Stop_panel"], ZT - 1.0, ZT + W/2).cut(_outside_wall()))
for _xv, _yv, _l in _B["screws"]:
    part = part.cut(_rect(_ear(_xv, _yv, _l, -D["Cl_panel_box"], 0.0), ZT - 1.0, E.Z_SCREWS))
    part = part.cut(cq.Workplane("XY").workplane(offset=E.Z_SCREWS - 0.01).center(_xv, _yv)
                      .circle(D["D_hole_insert_M3"]/2).extrude(D["L_insert_M3"] + 0.5))
    part = part.cut(cq.Workplane("XY").workplane(offset=ZT - 1.0).center(_xv, _yv)
                      .circle(1.7).extrude(_Z_BOSSES_B - 0.8 - (ZT - 1.0)))
    part = part.cut(cq.Workplane(obj=cq.Solid.makeCone(
        D["D_leadin_insert_M3"]/2 + 0.5, D["D_hole_insert_M3"]/2, D["Dp_leadin_insert_M3"] + 0.5,
        cq.Vector(_xv, _yv, E.Z_SCREWS - 0.5), cq.Vector(0, 0, 1))))

# THE COVER, a part of its own (hatch_cover). It PRINTS ON ITS OUTER FACE, the
# one flush with the floor: that face is the one in sight, and it comes off
# the bed flat; the ears rise 5 mm straight up, and the countersinks open on
# the bed as 45 degree cones, which print without supports.
_hcover = (_hatch(-_G_B, ZT + W/2, ZT + W)
        .union(_hatch(D["Stop_panel"] - _G_B, ZT, ZT + W/2))
        .cut(_outside_wall(_G_B)))
for _xv, _yv, _l in _B["screws"]:
    _hcover = _hcover.union(_rect(_ear(_xv, _yv, _l, _G_B, 0.0), ZT, E.Z_SCREWS))
    _hcover = _hcover.cut(cq.Workplane("XY").workplane(offset=ZT - 1.0).center(_xv, _yv)
                    .circle(D["D_holes_M3_printed"]/2).extrude(20.0))
    _r1 = D["D_head_countersunk_M3"]/2 + 0.3
    _hcover = _hcover.cut(cq.Workplane(obj=cq.Solid.makeCone(
        _r1, 0.0, _r1, cq.Vector(_xv, _yv, ZT - 0.3), cq.Vector(0, 0, 1))))
_hcover = cq.Workplane(obj=_hcover.val().clean())
if not _hcover.val().isValid() or len(_hcover.val().Solids()) != 1:
    raise SystemExit("cover of the hatch: invalid solid")

# MEASURED, NOT ASSUMED. (1) The motor, moved with the arm to both ends of
# its travel and to the middle, touches neither the part nor the cover: the
# first hatch, cut on the motor at rest, met it for 55 mm3 in the ears.
# (2) The motor comes up from 60 mm below to home without touching the part.
# (3) Each insert keeps a wall all round, probed on the solid.
import arm_travel as _AT
_mot = _OM.body()
_P = cq.Vector(D["R_disc"], D["Off_pivot"], 0.0)
_pz, _cp = part.val(), _hcover.val()
for _g in (_AT.limits(D)[0], 0.0, _AT.limits(D)[1]):
    _m = _mot.rotate(_P, _P + cq.Vector(0, 0, 1), _g)
    _v1, _v2 = _m.intersect(_pz).Volume(), _m.intersect(_cp).Volume()
    if _v1 > 0.01 or _v2 > 0.01:
        raise SystemExit("hatch: with the arm at %.2f degrees the motor touches the part for "
                         "%.2f mm3 and the cover for %.2f" % (_g, _v1, _v2))
for _dz in range(2, 62, 4):
    _v = _mot.translate(cq.Vector(0, 0, -_dz)).intersect(_pz).Volume()
    if _v > 0.01:
        raise SystemExit("hatch: the motor coming up from below touches the part for %.2f mm3 "
                         "%d mm from home" % (_v, _dz))
_v = _cp.intersect(_pz).Volume()
if _v > 0.01:
    raise SystemExit("the cover of the hatch interpenetrates the part for %.2f mm3" % _v)
for _xv, _yv, _l in _B["screws"]:
    for _k in range(16):
        _t = 2*math.pi*_k/16
        for _dz in (0.3, 1.5, 2.7):
            _q = cq.Vector(_xv + (D["D_out_insert_M3"]/2 + 0.6)*math.cos(_t),
                           _yv + (D["D_out_insert_M3"]/2 + 0.6)*math.sin(_t), E.Z_SCREWS + _dz)
            if not _pz.isInside(_q):
                raise SystemExit("hatch: insert at (%.1f, %.1f) with less than 0.6 mm of wall "
                                 "at %.0f degrees, z %.1f" % (_xv, _yv, math.degrees(_t), _q.z))
cq.exporters.export(_hcover, OUT + "hatch_cover.step")
print("hatch under the motor: %.1f x %.1f, R %.1f; cover %.2f cm3 -> %.1f g in ASA, "
      "prints on its outer face" % (_B["lx"], _B["ly"], _B["r"], _cp.Volume()/1000,
                                    _cp.Volume()*1.07e-3))

# --- the pivot screw is turned over ------------------------------------------
# It goes in from the telescope side instead of from below. From below the
# screwdriver finds 24 mm of part in front of it; from above it finds 2.5,
# which is only the wall of the roof. It is a hole in the roof of the
# mechanical compartment, not on a face in sight: it cannot be seen with the
# machine assembled.
_pxp, _pyp = pol(D["R_pivot"], D["Ang_pivot"])
# THROUGH THE ROOF GOES THE IRON, not the screw. The pivot screw has its head
# at the bottom, under the washer, and goes up into the insert at the top of
# the hub: nothing of it goes in from above. What must pass here is the tip
# that plants the insert, and before the union it did so on the bare collar,
# when there was nothing above.
part = part.cut(cq.Workplane("XY").center(_pxp, _pyp)
                  .circle(D["D_access_iron_pivot"]/2).extrude(60)
                  .translate((0, 0, _z_door)))
# ...AND THROUGH THE FLOOR GOES THE SCREWDRIVER, which is the way that was
# missing: with the box closed the head of the screw could no longer be reached
# from anywhere. The hole stays open and a snap-in plug closes it.
part = part.cut(cq.Workplane("XY").center(_pxp, _pyp)
                  .circle(D["D_access_driver_pivot"]/2).extrude(30)
                  .translate((0, 0, D["Z_floor_box"] - 1.0)))

# --- the cover closes the door too, and a screw holds it -------------------
# The cover did not fill the roof: a big hole was left above the clutch. So
# the cover covers it, and an insert in the collar with an M3 screw keeps it
# shut. The hole was this door: it
# has to stay - the motor drops in through it - but it has no reason to stay
# OPEN, and above it there was nothing.
#
# So the cover of the grip carries a PLATE that fills the door flush with the
# roof, Cl_cover_grip short of every edge, and a TAB that goes over the collar
# into a pocket as deep as the tab. The whole cover still goes on and off the
# way it did: straight down, the lips in their grooves, the plate into the
# door and the tab into its pocket, all vertical.
#
# THE INSERT IS NOT ON THE AXIS OF THE CLUTCH, and that was measured, not
# chosen. Between the gasket groove under the collar (r 67..70, up to z 24.5)
# and the edge of the door (x = DOOR_X[0]) the collar is 5.5 mm wide at y 0:
# an insert of Ø5 would be left with a quarter of a millimetre on each side.
# The strip widens away from the axis, and at Off_insert_cover there is a wall on
# both sides; the check below measures it on the solid.
#
# HOW THE COVER PRINTS NOW: upside down, on the top face. It used to print
# standing, as mounted; with a 45 x 60 mm plate on top, standing would make the
# plate one big overhang. Upside down the plate and the tab are the first
# layer, the sloping plate of the grip rises at 45 degrees, the lips rise
# vertically, and the countersink opens on the bed.
_cl_l = D["Cl_cover_grip"]
_xi = DOOR_X[0] - D["D_out_insert_M3"]/2 - D["Wall_insert_cover"]
_yi = D["Off_insert_cover"]
_z_pocket = Z_ROOF - D["Th_tab_cover"] - _cl_l        # floor of the pocket = top of the insert


def _tab(clearance, z0, h):
    """The tab over the collar: round about the insert, straight into the door."""
    r = D["R_tab_cover"] + clearance
    x1 = DOOR_X[0] + 2.0
    return (cq.Workplane("XY").workplane(offset=z0).center(_xi, _yi).circle(r).extrude(h)
            .union(cq.Workplane("XY").workplane(offset=z0).center((_xi + x1)/2, _yi)
                   .rect(x1 - _xi, 2*r).extrude(h)))


part = part.cut(_tab(_cl_l, _z_pocket, Z_ROOF + 1.0 - _z_pocket))
part = part.cut(cq.Workplane("XY").workplane(offset=_z_pocket - D["L_insert_M3"] - 1.5)
                  .center(_xi, _yi).circle(D["D_hole_insert_M3"]/2)
                  .extrude(D["L_insert_M3"] + 2.0))
part = part.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_leadin_insert_M3"]/2 + 0.5, D["D_hole_insert_M3"]/2, D["Dp_leadin_insert_M3"] + 0.5,
    cq.Vector(_xi, _yi, _z_pocket + 0.5), cq.Vector(0, 0, -1))))
# The wall round the insert, on the solid: a ring of probes just outside the
# insert, through its whole length, must all be in material.
_exposed = []
for _k in range(16):
    _t = 2*math.pi*_k/16
    for _dz in (0.3, 1.5, 2.7):
        _p = cq.Vector(_xi + (D["D_out_insert_M3"]/2 + 0.6)*math.cos(_t),
                       _yi + (D["D_out_insert_M3"]/2 + 0.6)*math.sin(_t), _z_pocket - _dz)
        if part.val().intersect(cq.Solid.makeSphere(0.1, _p)).Volume() < 1e-12:
            _exposed.append("%.0f degrees at z %.1f" % (math.degrees(_t), _p.z))
if _exposed:
    raise SystemExit("insert of the cover: less than 0.6 mm of wall at %d points (%s)"
                     % (len(_exposed), ", ".join(_exposed[:6])))
print("insert of the cover at (%.2f, %.2f), mouth at z %.2f: wall >= 0.6 all round"
      % (_xi, _yi, _z_pocket))

# WHERE THE COVER MEETS THE COLLAR IT STAYS FULL HEIGHT. The
# plates were cut by the lobe's chamfered envelope everywhere, and the lobe's
# roof chamfer is some ten millimetres: next to the door's edge on the collar
# side, where the box roof is flat up to the edge, the plate sloped away and
# left a V, 1..6 mm wide, open from above into the compartment (dark beside
# the round plate in the render). Within the collar's outer radius the plates
# keep the roof's full height, as the collar next to them does.
_env_cover = chamfer(0.0).union(
    cq.Workplane(obj=cq.Solid.makeCylinder(_r_ring[1], 200.0, cq.Vector(0, 0, -100.0))))
_door_in = (cq.Workplane("XY")
             .box(DOOR_X[1] - DOOR_X[0] - _cl_l, DOOR_Y[1] - DOOR_Y[0] - 2*_cl_l, W)
             .translate(((DOOR_X[0] + _cl_l + DOOR_X[1])/2, (DOOR_Y[0] + DOOR_Y[1])/2,
                         Qsp + W/2))
             .intersect(cq.Workplane(obj=cq.Solid.makeCylinder(
                 RA - W - 1.0 - _cl_l, 200.0, cq.Vector(MX, MY, -100.0))))
             .intersect(_env_cover))
# the plate also covers whatever the motor's silhouette opens in the roof
# outside the door, Cl_cover_grip inside that cut. With the leads left out of
# the silhouette that is nothing today; it was a tab on the plate while the
# leads were in it, and it had no reason to be there
_door_in = _door_in.union(
    _motor_silhouette(D["Cl_entry_motor"] - D["Cl_cover_grip"])
    .intersect(cq.Workplane("XY").workplane(offset=Qsp).rect(400, 400).extrude(W))
    .intersect(_env_cover))
# and the ring cut right through over the motor's angles
_dcl = math.degrees(D["Cl_cover_grip"]/_r_ring[0])
_door_in = _door_in.union(
    sett(min(_ang_sil) + _dcl, max(_ang_sil) - _dcl, _r_ring[0] + D["Cl_cover_grip"],
         _r_ring[1] - D["Cl_cover_grip"], Qsp, W)
    .intersect(_env_cover))
_cover = _cover.union(_door_in).union(_tab(0.0, Z_ROOF - D["Th_tab_cover"], D["Th_tab_cover"]))
# THE KNIFE ALONG THE TOP OF THE SLOPING PLATE (check_thin). The
# plate of the grip is the chamfered envelope from outside and the cylinder
# Cl_cover_grip outside the stepped-in wall from inside, and the two meet 0.4
# below the top in a knife edge. Where the door plate lies against it, the
# knife is inside the door plate and is not a knife at all; past the door
# plate, from 9.3 to 11.5 degrees on the +y side, it stood alone - printed
# upside down it is the first thing off the bed, 0 to 0.8 mm wide. So above
# the level where the sloping plate is Th_min_wall_printing thick, whatever
# is NOT door plate goes: the plate ends there on a flat, at full thickness.
_r_i_cover = RG + _cl_t                           # inner face of the sloping plate
_z_knife = (Z_ROOF - CH) + (Ro - _r_i_cover) - D["Th_min_wall_printing"]
# ...CUT AT 45 DEGREES, NOT FLAT. Cut flat at _z_knife
# the plate kept a level ring there, and printed upside down that ring faced
# the bed from 1.2 mm up: an overhang of 4 mm2, the one incongruence left in
# the build (check_grip). The cut now rises outwards at 45 degrees from the
# inner face - a cone about the wheel axis - so the section ends on a 90
# degree edge: no knife, and nothing the printer has to bridge.
_H_knife = (Z_ROOF + 1.0) - _z_knife
_cone_knife = cq.Solid.makeCone(_r_i_cover, _r_i_cover + _H_knife, _H_knife,
                               cq.Vector(0, 0, _z_knife))
_cover = _cover.cut(sett(-AG - 1.0, AG + 1.0, _r_i_cover - 1.0, Ro + 1.0,
                         _z_knife, _H_knife).intersect(cq.Workplane(obj=_cone_knife))
                    .cut(_door_in))
# a plain hole: the screws are socket head, knurled, and sit on the tab
# (they are undone by hand to clean the filters). They were
# countersunk, and the tab carried the cone
_cover = _cover.cut(cq.Workplane("XY").workplane(offset=Z_ROOF - 5.0).center(_xi, _yi)
                    .circle(D["D_holes_M3_printed"]/2).extrude(10.0))
# ---- THE COVER TAKES THE CHAMFER BAND ON THE -y SIDE, with a second screw ---
# The roof chamfer of the arc round the motor, on the -y side, from the fillet at the
# collar to the grip, goes from the box to the cover. The cover's edge then
# follows the foot of the chamfer, one line, and the step where the round
# plate met the chamfer goes inside the cover. The band held the top of the
# arc wall to the collar, so the cover now carries a SECOND SCREW, in the
# chamfer, into an insert in a boss behind it: where the chamfer has too
# little material, it is thickened until the insert fits with enough wall
# round it.
#
# Where the band runs, about the motor axis: from the fillet's tangency on
# the arc (_t2) to the point of the arc at the grip's edge (wheel angle -AG).
from parameters import chamfer_band as _chamfer_band
_a0, _a1 = _chamfer_band()
_zc = Z_ROOF - CH                                   # foot of the chamfer


def _fan(a0, a1, z0, z1):
    """A fan about the motor axis between two angles (radians)."""
    n = 24
    pts = [(MX, MY)] + [(MX + 3*RA*math.cos(a0 + (a1 - a0)*k/n),
                         MY + 3*RA*math.sin(a0 + (a1 - a0)*k/n)) for k in range(n + 1)]
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


_collar_cyl = cq.Workplane(obj=cq.Solid.makeCylinder(_r_ring[1], 200.0, cq.Vector(0, 0, -100.0)))
_skin = chamfer(0.0).cut(chamfer(W))
# the chamfered envelope does not stop at the roof - above it the cone runs
# on to its apex - so the band is capped at Z_ROOF; uncapped, it stood up
# over the roof and check_grip saw a 2071 mm2 overhang
_roof = chamfer(0.0).intersect(cq.Workplane("XY").workplane(offset=Qsp).rect(600, 600).extrude(Z_ROOF - Qsp))
# the band ends on the grip's own plane, the radius at -AG from the WHEEL
# axis, not on a radius from the motor axis: cut that way, at the inner radii
# it reached into the grip's sector and met the stepped-in wall (9.6 mm3)
# ...but only from the grip's stepped-in wall outwards (RGi): inside it, in
# the grip's sector, the arc's chamfer was left to the box, and between the
# round plate, the band and the grip's plate it showed as a yellow triangle
# The band takes it; the stepped-in wall stays the box's.
# (and the stepped-in wall's own top, above the chamfer's foot and only
# there, goes to the band too: left to the box it still showed as a narrow
# yellow strip between the band and the grip's plate. The band reaches the
# plate's inner face, RG + Cl_cover_grip, and the two merge.)
_grip_sector = sett(-AG, AG, RG + D["Cl_cover_grip"], 300.0, _zc - 1.0, 20.0)
_band_box = ((chamfer(-1.0).cut(chamfer(W)).union(_roof))
               .intersect(_fan(_a0, _a1 + math.radians(25.0), _zc, Z_ROOF))
               .cut(_collar_cyl).cut(_grip_sector))
_dcl_f = D["Cl_cover_grip"]/RA
# the band floats Cl_cover_grip over the wall's top and over the boss behind
# it, like the rest of the cover: the screws pull it down onto its seats, and
# check_grip wants air between cover and part everywhere in the model
_band_cover = ((_skin.union(_roof))
               # and Cl_cover_grip short of where the box's cut ends, inside
               # the grip's sector: ending on the same plane, the band lay
               # face to face with the box left beyond it (at -33.8 degrees)
               .intersect(_fan(_a0 + _dcl_f, _a1 + math.radians(25.0) - _dcl_f*1.5,
                                     _zc + D["Cl_cover_grip"], Z_ROOF))
               # Cl_cover_grip short of the grip's plane, at r 80 and more: on
               # that plane the box goes on (the grip's sector) and the band
               # touched it, 0.003 mm at (110.2, -22.7, 24.5)
               .cut(sett(-AG - math.degrees(D["Cl_cover_grip"]/80.0), AG,
                         RG + D["Cl_cover_grip"], 300.0, _zc - 1.0, 20.0))
               .cut(cq.Workplane(obj=cq.Solid.makeCylinder(_r_ring[1] + D["Cl_cover_grip"], 200.0,
                                                         cq.Vector(0, 0, -100.0)))))
part = part.cut(_band_box)
_band_cover_raw = _band_cover
print("chamfer band to the cover: from %.1f to %.1f degrees about the motor, from the foot at z %.1f"
      % (math.degrees(_a0), math.degrees(_a1), _zc))

# THE SECOND SCREW, VERTICAL, AT THE CORNER WHERE THE COLLAR MEETS THE ARC
# It was first square to the 45
# degree chamfer, into a boss hanging inside the arc: that boss and the tab of
# box chamfer beside it were two fins in the compartment, and the tilted
# countersink was the one overhang the cover had to be forgiven. Now it is the
# first screw again, mirrored: a round tab of the cover lies in a pocket at the
# top of the collar, Th_tab_cover deep, the M3 goes down through it
# into an insert in the collar. The tab runs on straight into the ring cut,
# where the door's plate is, and that is what joins it to the cover. Where it
# is comes from parameters.fillet_screw, which purchased.py and the audit read.
_zt2 = Z_ROOF - D["Th_tab_cover"] - _cl_l            # floor of the pocket = top of the insert
_ac2 = math.atan2(_yv2, _xv2)
_rc2 = math.hypot(_xv2, _yv2)
_ae2 = _a_cut2 + math.asin(2.0/_rc2)                    # 2 mm into the ring cut


def _tab2(clearance, z0, h):
    """The tab over the collar at -y: round about the insert, straight into the
    ring cut along the circle through the insert."""
    r = D["R_tab_cover"] + clearance
    ux, uy = math.cos(_ae2) - math.cos(_ac2), math.sin(_ae2) - math.sin(_ac2)
    L = math.hypot(ux, uy)
    ux, uy = ux/L, uy/L
    # the pocket is longer by the same clearance at the far end: without it
    # the tab's end face lay on the pocket's, on the collar's lip (check_grip,
    # distance 0.000)
    ex, ey = _rc2*math.cos(_ae2) + ux*clearance, _rc2*math.sin(_ae2) + uy*clearance
    return (cq.Workplane("XY").workplane(offset=z0).center(_xv2, _yv2).circle(r).extrude(h)
            .union(cq.Workplane("XY").workplane(offset=z0)
                   .polyline([(_xv2 - uy*r, _yv2 + ux*r), (ex - uy*r, ey + ux*r),
                              (ex + uy*r, ey - ux*r), (_xv2 + uy*r, _yv2 - ux*r)]).close()
                   .extrude(h)))


part = part.cut(_tab2(_cl_l, _zt2, Z_ROOF + 1.0 - _zt2))
part = part.cut(cq.Workplane("XY").workplane(offset=_zt2 - D["L_insert_M3"] - 1.5)
                  .center(_xv2, _yv2).circle(D["D_hole_insert_M3"]/2)
                  .extrude(D["L_insert_M3"] + 2.0))
part = part.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_leadin_insert_M3"]/2 + 0.5, D["D_hole_insert_M3"]/2, D["Dp_leadin_insert_M3"] + 0.5,
    cq.Vector(_xv2, _yv2, _zt2 + 0.5), cq.Vector(0, 0, -1))))
# the wall round the insert, on the solid, as for the first
_exposed2 = []
for _k in range(16):
    _t = 2*math.pi*_k/16
    for _dz in (0.3, 1.5, 2.7):
        _p = cq.Vector(_xv2 + (D["D_out_insert_M3"]/2 + 0.6)*math.cos(_t),
                       _yv2 + (D["D_out_insert_M3"]/2 + 0.6)*math.sin(_t), _zt2 - _dz)
        if part.val().intersect(cq.Solid.makeSphere(0.1, _p)).Volume() < 1e-12:
            _exposed2.append("%.0f degrees at z %.1f" % (math.degrees(_t), _p.z))
if _exposed2:
    raise SystemExit("second screw of the cover: less than 0.6 mm of wall round the insert "
                     "at %d points (%s)" % (len(_exposed2), ", ".join(_exposed2[:6])))
# ...and the wall round the POCKET on the outside, where only the fillet is:
# probes 2 * Th_min_wall_printing outside the pocket's edge, over the half
# that faces outwards, must all be in material - short of the side towards
# the ring cut, where the tab runs on straight and there is no wall to have.
# This is what sets R_fillet_collar_arc: at 10 the wall was a quarter of a
# millimetre
_rp2 = D["R_tab_cover"] + _cl_l + 2*D["Th_min_wall_printing"]
_exposed3 = []
for _k in range(13):
    _t = _ac2 - math.pi/2 + math.pi*_k/12          # the outer half, from the -y side
    for _dz in (0.3, 1.0, 1.9):
        _p = cq.Vector(_xv2 + _rp2*math.cos(_t), _yv2 + _rp2*math.sin(_t), Z_ROOF - _dz)
        if math.atan2(_p.y, _p.x) > _a_cut2:
            continue                                # in the ring cut: the door's plate is there
        if part.val().intersect(cq.Solid.makeSphere(0.1, _p)).Volume() < 1e-12:
            _exposed3.append("%.0f degrees at z %.1f" % (math.degrees(_t), _p.z))
if _exposed3:
    raise SystemExit("second screw of the cover: the pocket of the tab has less than %.1f mm "
                     "of wall at %d points (%s) - widen R_fillet_collar_arc"
                     % (2*D["Th_min_wall_printing"], len(_exposed3), ", ".join(_exposed3[:6])))
print("second screw of the cover at (%.2f, %.2f), mouth at z %.2f: wall >= 0.6 round "
      "the insert, >= %.1f round the pocket" % (_xv2, _yv2, _zt2, 2*D["Th_min_wall_printing"]))
# THE BAND KEEPS Cl_cover_grip FROM THE PART EVERYWHERE, taken from the part
# itself: the band less the finished part moved by the clearance in the 26
# directions of a cube's faces, edges and corners (a Minkowski sum, as the
# motor's silhouette does in the plane with eight). Cleared by hand it still
# touched in nine places; with the six axis directions alone it touched at
# the part's convex edges, where a point just off the edge diagonally falls
# in none of the six copies.
_fc = _band_cover_raw
_cl6 = D["Cl_cover_grip"]
for _i in (-1, 0, 1):
    for _j in (-1, 0, 1):
        for _k in (-1, 0, 1):
            if (_i, _j, _k) == (0, 0, 0):
                continue
            _nn = math.sqrt(_i*_i + _j*_j + _k*_k)
            _fc = _fc.cut(part.translate((_cl6*_i/_nn, _cl6*_j/_nn, _cl6*_k/_nn)))
_cover = _cover.union(_fc)
_cover = _cover.union(_tab2(0.0, Z_ROOF - D["Th_tab_cover"], D["Th_tab_cover"]))
_cover = _cover.cut(cq.Workplane("XY").workplane(offset=Z_ROOF - 5.0).center(_xv2, _yv2)
                    .circle(D["D_holes_M3_printed"]/2).extrude(10.0))

_cover = cq.Workplane(obj=_cover.val().clean())
if not _cover.val().isValid() or len(_cover.val().Solids()) != 1:
    raise SystemExit("cover of the grip: the solid is not valid - %d solids"
                     % len(_cover.val().Solids()))
_v_ur = _cover.val().intersect(part.val()).Volume()
if _v_ur > 0.01:
    for _so in _cover.val().intersect(part.val()).Solids():
        _b = _so.BoundingBox()
        print("  interpenetration %.2f mm3 in x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
              % (_so.Volume(), _b.xmin, _b.xmax, _b.ymin, _b.ymax, _b.zmin, _b.zmax))
    raise SystemExit("the cover interpenetrates the one-piece part for %.2f mm3" % _v_ur)
cq.exporters.export(_cover, OUT+"grip_cover.step")
print("cover (grip + door) %.2f cm3 -> %.1f g in ASA; prints upside down"
      % (_cover.val().Volume()/1000, _cover.val().Volume()*1.07e-3))

# DID THE DOOR REALLY CUT? Measured, not taken as done: a cut that passes over
# the roof without touching it removes nothing and nobody notices - the part
# comes out valid, of a single solid, and closed. It happened once, and a
# wrong STEP went out to be printed. It is probed in the middle of
# the door, at the height of the roof slab: there must be nothing left there.
_probe = cq.Solid.makeSphere(0.2, cq.Vector((DOOR_X[0]+DOOR_X[1])/2,
                                          (DOOR_Y[0]+DOOR_Y[1])/2,
                                          D["Z_shoulder_box"] + 1.0))
if part.val().intersect(_probe).Volume() > 1e-12:
    raise SystemExit("the door did not cut the roof of the compartment: there is "
                     "still material at z %.1f in the middle of the door. The cut "
                     "starts from %.1f and the roof is at %.1f."
                     % (D["Z_shoulder_box"] + 1.0, _z_door, D["Z_shoulder_box"]))

# THE COUNT OF SOLIDS, and it is not a formality: it is the check that found
# the 26 mm3 flake. Two solids mean either that an opening has detached a
# piece, or that box and collar did not weld - and in that case the culprit is
# Weld_box_collar, which must be an interpenetration and not a clearance.
_p = part.val()
if not _p.isValid() or len(_p.Solids()) != 1:
    raise SystemExit(
        "one-piece part: %d solids, valid=%s. If they are two, either an opening "
        "detached a flake, or the shell does not touch the collar "
        "(Weld_box_collar must interpenetrate, not leave clearance)."
        % (len(_p.Solids()), _p.isValid()))

_bb = _p.BoundingBox()
cq.exporters.export(part, OUT + "box_collar.step")
print("ONE-PIECE PART box_collar: %.1f cm3 -> %.0f g in ASA"
      % (_p.Volume()/1000, _p.Volume()*1.07e-3))
print("   envelope %.1f x %.1f x %.1f - wants a 200 x 200 bed"
      % (_bb.xlen, _bb.ylen, _bb.zlen))

# --- the CO-PRINTED part, for the two-material machine ---------------------
# It lived in solids_body_collar.py when the collar was a part of its own. Now
# the ASA the gaskets rest on is the whole one-piece part, so the file for the
# IDEX is written by whoever holds the whole part.
#
# The three bodies stay SEPARATE and named by material: that is how a slicer
# takes them, one body per extruder. A single solid would make them
# indistinguishable.
_gf = cq.importers.importStep(OUT + "front_gasket.step")
_gr = cq.importers.importStep(OUT + "rear_gasket.step")
_coprinted = cq.Assembly(name="box_collar_coprinted")
_coprinted.add(part, name="box_collar_ASA",
          color=cq.Color(0.85, 0.85, 0.88))
_coprinted.add(_gf, name="front_gasket_TPU", color=cq.Color(0.20, 0.55, 0.35))
_coprinted.add(_gr, name="rear_gasket_TPU", color=cq.Color(0.20, 0.55, 0.35))
_coprinted.save(OUT + "box_collar_coprinted.step")
print("   co-printed: 3 bodies, ASA %.1f cm3 + TPU %.1f cm3"
      % (_p.Volume()/1000.0,
         (_gf.val().Volume() + _gr.val().Volume())/1000.0))
