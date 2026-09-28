# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

import math, cadquery as cq
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
from parameters import D
import outline_arm as SB
# same frame as the other STEPs: origin = centre of the disc, z 0 = camera-side face
Rd=D["R_disc"]; Ia=D["Cd_motor"]; off=D["Off_pivot"]
Px,Py = Rd, off; Mx,My = Ia, 0.0
Lb=D["L_arm"]; th=D["Th_arm"]
# THE PLATE IS STEPPED, and before it was not. As long as the
# motor had its face on the bottom of the plate, Z_face_motor and Th_arm were
# both 8 and a single z0 was enough for two different things. Turning the
# clutch upside down raised the grub, the shaft has to reach above it, and the
# motor face rose with it: now the two dimensions differ and must be kept
# apart.
#   z0 = the bottom of the plate, where the pivot bearings sit
#   zf = the face the motor rests on, higher up
z0 = D["Z_bottom_arm"]           # -6 .. 2, the solid where the pivot hub sits
# (it was -th, i.e. the top face pinned at z 0: the arm is now
# raised to Z_top_arm, and a literal here would have left the arm behind)
zf = -D["Z_face_motor"]          # -2.5, the motor face
# Under the motor the plate stays Z_face_motor thick, and this is the price
# that turning the clutch upside down carries with it: every millimetre the
# motor rises is a millimetre the plate loses. If it gets too thin one does not
# find out when printing - one finds out when it gives way - so here it stops.
if D["Th_plate_motor"] < D["Th_min_plate_motor"]:
    raise SystemExit(
        "the plate under the motor would be %.2f mm thick, and the minimum is\n"
        "%.2f (Th_min_plate_motor). It is Z_face_motor (%.2f) plus what the\n"
        "plate grows above the plane, Th_more_plate_motor (%.2f): to\n"
        "gain some back it grows UPWARDS, which costs the machine no height."
        % (D["Th_plate_motor"], D["Th_min_plate_motor"], D["Z_face_motor"],
           D["Th_more_plate_motor"]))
ux,uy = (Mx-Px)/Lb, (My-Py)/Lb          # unit vector pivot -> motor
nx,ny = -uy, ux                          # perpendicular
if nx*Px+ny*Py < 0: nx,ny = -nx,-ny      # pointing outwards
half=D["Side_motor"]/2; hh=D["Cd_holes_motor"]/2
w=D["L_band_arm"]/2                 # the band is narrower than the hub

def box_at(x,y,dx,dy,z,h):
    return cq.Workplane("XY").workplane(offset=z).center(x,y).rect(dx,dy).extrude(h)

def s_along_axis(qx, qy, dx, dy, radius):
    """How far to run along the spring axis to find oneself at that radius."""
    lo, hi = 0.0, 100.0
    for _ in range(60):
        mid = (lo+hi)/2
        if math.hypot(qx+dx*mid, qy+dy*mid) < radius: lo = mid
        else: hi = mid
    return (lo+hi)/2

# --- plate: pivot hub + band + motor plate, then the cut on the inner radius ---
# The two corners of the plate that look downwards (negative global y) are the
# ones that on the fitted part stick out and get knocked when handling it:
# they must be filleted. The arcs are taken from the same piece of code that
# draws the plan, because the 2D outline and this solid must tell the same
# part - but they remain TWO distinct constructions, and check_audit compares
# the outline with the section of this STEP: if they diverge, it is heard.
_q = [(Mx-half, My-half), (Mx+half, My-half), (Mx+half, My+half), (Mx-half, My+half)]
_Rsp = D["R_edges_plate_motor"]
_arc_left = SB._corner_arc(_q[3], _q[0], _q[1], _Rsp)   # corner towards the pivot
_arc_right = SB._corner_arc(_q[0], _q[1], _q[2], _Rsp)   # far corner
_square = _arc_left + _arc_right + [_q[2], _q[3]]

pts=[(Px-w*nx, Py-w*ny)] + _arc_left + _arc_right + [_q[2], (Px+w*nx, Py+w*ny)]
arm = cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(th)
arm = arm.union(cq.Workplane("XY").workplane(offset=z0).center(Px,Py)
              .circle(D["D_hub_pivot"]/2).extrude(th))
arm = arm.union(cq.Workplane("XY").workplane(offset=z0).polyline(_square).close().extrude(th))

# --- the wide part carries on towards the pivot ---
# The motor square is 35.2 wide, the band at the pivot 18: between the two the
# arm is a wedge, and the section thins right where the spring's moment is
# greatest. L_plate_solid says how far to keep the full width. Only the outer
# side is lengthened: the inner one is already cut by R_rim_inner and would
# gain nothing.
sp = Lb - D["L_plate_solid"]
def on_arm(s, t):
    return (Px+ux*s+nx*t, Py+uy*s+ny*t)
# Where the solid plate reaches the pivot, the two sides no longer jump to it
# with a 7.1 mm step (hub r 10.5 against plate 17.6): they climb to it with an
# ogive of two tangent arcs, L_nose_arm long. The length is dictated by the
# spring - the ogive closes before the spring starts resting - not by taste: a
# spring resting on the curve would go back to pressing on an edge, which is
# the defect the plate had been lengthened for.
_rm, _xb = D["D_hub_pivot"]/2, D["L_nose_arm"]
if sp <= 1e-9 and _xb > 1e-9:
    _n = max(2, int(_xb/0.25) + 1)
    _xs = [_xb*i/(_n-1) for i in range(_n)]
    _plus  = [on_arm(x, SB.ogive(x,  _rm,  half, _xb)) for x in _xs]
    _minus = [on_arm(x, SB.ogive(x, -_rm, -half, _xb)) for x in _xs]
    _wide = _plus + [on_arm(Lb, half), on_arm(Lb, -half)] + _minus[::-1]
else:
    _wide = [on_arm(sp, half), on_arm(Lb, half),
              on_arm(Lb, -half), on_arm(sp, -half)]
arm = arm.union(cq.Workplane("XY").workplane(offset=z0).polyline(_wide).close().extrude(th))

arm = arm.cut(cq.Workplane("XY").workplane(offset=z0-1)
            .circle(D["R_rim_inner"]).extrude(th+2))          # inner rim r80

# --- where the spring washer went ---
# Here there was a Ø14 cylinder centred on Q, the spring's attachment on the
# arm, twelve millimetres tall: born from the Ø10 construction circle that the
# drawing puts at Q, taken for a real washer. But the spring never reaches Q:
# its force passes through Q, its end stops seventeen millimetres before,
# against the side of the plate. That cylinder touched nothing - just four
# millimetres of material hanging under the motor face, which on top of that
# brought the spring axis to -6 instead of the mid-plane of the plate, two
# millimetres off centre and so with a free twist on the arm. Removed: the
# spring rests on the solid side of the 8 mm.
Qx,Qy = Px+ux*D["Att_spring"], Py+uy*D["Att_spring"]

# --- the pocket under the motor, which makes the step ------------------------
# The motor rests at zf, not on the bottom of the plate: under it the material
# is taken away up to there.
#
# THE POCKET TAKES THE TRUE OUTLINE OF THE PLATE, not a larger square. At the
# first attempt it was the motor footprint plus a millimetre a side, and that
# millimetre came out OF THE PLATE: the plate at the motor is exactly as wide
# as the motor, so the pocket ate its filleted corners instead of just
# thinning it. The fillet check and the one on the material around the M3
# holes showed it - forty-eight uncovered points. Using _square, which is the
# same outline the plate was built with, the step falls exactly on its edge:
# under the motor the plate is Z_face_motor thick, and nothing sticks out or
# is missing.
arm = arm.cut(cq.Workplane("XY").workplane(offset=z0-1)
            .polyline(_square).close().extrude(zf - z0 + 1))
# --- the two thin walls on the wheel side of the motor -----------------------
# Between the edge of the motor square (x = Mx - half) and the inner rim cut
# (R_rim_inner) two slivers of the arm stood below the plate, from the arm's
# underside up to the motor face, tapering to nothing where the rim circle
# crosses the square edge: 0 to 0.8 mm on the side away from the pivot, 0 to
# 1.9 on the side of the pivot. The far one is taken away.
#
# THE NEAR ONE STAYS AS IT IS, without the 45 degree step that was once grown
# under it: rejected, the step was removed. Do not put it back as a way of
# thickening that wall.
_x_q = Mx - half                                   # the edge of the motor square
_y_far = (-half - 1.0, 0.0)                        # the far wall: y < 0
arm = arm.cut(cq.Workplane("XY").workplane(offset=z0 - 1.0)
            .center(_x_q - 2.0, (_y_far[0] + _y_far[1])/2)
            .rect(4.0, _y_far[1] - _y_far[0]).extrude(zf - (z0 - 1.0)))

# ...and it grows UPWARDS by Th_more_plate_motor. Above the plane z 0, at the
# motor, there is no collar - it is at r 86 and the motor at 97.5 - so the
# material can be taken from there instead of bringing the motor down, which
# would raise the floor and with it the whole machine.
_z_top_plate = zf + D["Th_plate_motor"]
if _z_top_plate > z0 + th + 1e-9:
    # from the top face of the body, not from z 0: with the arm raised the
    # body already reaches the top of the plate, and nothing is added
    arm = arm.union(cq.Workplane("XY").workplane(offset=z0 + th)
                  .polyline(_square).close().extrude(_z_top_plate - (z0 + th)))

# --- machining ---
# The seat of the two flanged F695ZZ is drawn with the COMPENSATED diameter,
# not the catalogue one. It was 13.0 net, i.e. the diameter of the outer ring,
# and printed it measured two tenths less: the bearings went in by force. A
# light interference is needed - the outer ring must not turn in the plastic -
# but two tenths on thirteen is ten times as much and jams the balls, and a
# bearing that turns hard cancels the reason it is there.
arm = arm.cut(cq.Workplane("XY").workplane(offset=z0-1).center(Px,Py)
            .circle(D["D_seat_bearings_printed"]/2).extrude(th+2))
# The 45 degree lead-in goes on BOTH faces: the bearings go in one per face,
# with the flanges staying outside as the axial reference. The cone starts
# half a millimetre outside the face, in the air, for the same reason as the
# lead-in of the centring seat: coplanar leaves chips on the edge.
_rbc, _ric = D["D_mouth_seat_bearings"]/2, D["D_seat_bearings_printed"]/2
_hic = D["H_leadin_seat_bearings"]
for _zf, _vs in ((z0, 1.0), (z0+th, -1.0)):
    arm = arm.cut(cq.Workplane(obj=cq.Solid.makeCone(
        _rbc+0.5, _ric, _hic+0.5,
        cq.Vector(Px, Py, _zf - _vs*0.5), cq.Vector(0, 0, _vs))))
# The centring seat must be dug in the face WHERE THE MOTOR RESTS, i.e.
# z0 = -Z_face_motor, not in the other one. It was at -H_seat_centring, i.e. on
# the face towards the body: a pocket on the wrong side, and the Ø22 hub of the
# motor ran into the solid of the plate. Measured on the assembly: 682.2 mm3
# of interpenetration between z -8 and -6, which is exactly the hub. The motor
# would have stayed two millimetres raised, resting on the hub instead of on
# the flange, and centred by nothing - precisely the job that D_circle_motor
# says is its own and not the screws'.
# THE CENTRING SEAT WENT THROUGH for a while, no longer blind. It was a
# pocket H_seat_centring (2.2) deep dug in the motor face, and it worked as
# long as the plate was eight thick. Stepping it to Z_face_motor - 2.68 -
# above that pocket FOUR TENTHS of material were left: that is not a plate, it
# is a membrane, and it would have broken when driving in the motor screws.
# Through-going, the Ø22 hub of the motor crosses the plate and the flange
# rests on the ring left around it: the centring is done by the wall of the
# hole on the two millimetres of hub, which are the ones there have always
# been.
#
# ...AND BLIND AGAIN: there is room now to put back about 1.5 mm of material
# and support the motor better. The plate has grown
# back to Th_plate_motor = 3.5 while the hub of the motor is still
# H_circle_motor = 2 tall: through the plate, the 1.5 mm above the hub were
# empty. So the seat is H_seat_centring deep - the hub plus two tenths - and
# above it a floor of Th_plate_motor - H_seat_centring is left, crossed only by
# the shaft clearance hole. The rule that made it through-going still holds:
# if the floor would come out thinner than Th_min_floor_seat_centring, it is a
# membrane, and the seat goes through again.
_floor_seat = D["Th_plate_motor"] - D["H_seat_centring"]
_h_seat = (D["H_seat_centring"] if _floor_seat >= D["Th_min_floor_seat_centring"]
           else D["Th_plate_motor"] + 1.0)
arm = arm.cut(cq.Workplane("XY").workplane(offset=zf-1).center(Mx,My)
            .circle(D["D_seat_centring"]/2).extrude(_h_seat + 1.0))
print("centring seat: %.2f deep, floor of %.2f above the motor hub"
      % (min(_h_seat, D["Th_plate_motor"]), max(D["Th_plate_motor"] - _h_seat, 0.0)))
# 45 degree lead-in on the mouth of the seat. It is not a finish: the motor hub
# is not a clean cylinder, at the root it has a fillet that widens to
# D_fillet_hub_motor in the first half millimetre. Without a lead-in the seat
# at 22.2 runs into it - 1.7 mm3, measured with the real motor in the
# assembly - and the motor rests two tenths raised, on the fillet instead of
# on the flange. The lead-in frees it, and on top of that it guides the hub
# while it goes down into the seat.
# The cone starts half a millimetre below the face, in the air: a cut with the
# face exactly coplanar to that of the part leaves chips.
_rb, _ri = D["D_mouth_seat_centring"]/2, D["D_seat_centring"]/2
arm = arm.cut(cq.Workplane(obj=cq.Solid.makeCone(
    _rb+0.5, _ri, D["H_leadin_seat_centring"]+0.5,
    cq.Vector(Mx, My, zf-0.5), cq.Vector(0,0,1))))
arm = arm.cut(cq.Workplane("XY").workplane(offset=z0-1).center(Mx,My)
            .circle(D["D_clear_shaft"]/2).extrude(th+2))
for sx in (-1,1):
    for sy in (-1,1):
        arm = arm.cut(cq.Workplane("XY").workplane(offset=z0-1)
                    .center(Mx+sx*hh, My+sy*hh).circle(D["D_holes_M3_printed"]/2).extrude(th+2))
# --- the spring's centring spigot ---
# The spring rests on the SIDE of the plate, at R_rest_spring_arm, not inside
# a dimple: here there was a pocket dug at s=5.5, buried eight millimetres
# inside the solid, which the spring would never have seen. The spigot instead
# goes into the inner diameter of the spring (6.9) and keeps it on axis; a
# pocket could not be made, because the spring is 8.9 outside and the plate is
# 8 thick.
#
# The axis is on the mid-plane of the plate, not two millimetres below: that
# way the spigot, Ø6.4 on a face 8 tall, is born entirely on the solid. Before,
# it was born at -6 and its round went down to -9.2, one millimetre two below
# the face of the arm: an eighth of the root started in the air, which on an
# FDM print means a cantilevered cylinder resting on nothing.
#
# And the spigot does not start on the side: it starts Dp_spigot_spring inside
# the solid and crosses it. Before, the cylinder started exactly on the side,
# and the union shared with the plate only the base face - measured, zero
# cubic millimetres in common: a butt joint, not a weld.
# THE AXIS IS NO LONGER THE MID-PLANE of the arm: it is
# Z_axis_spring, low enough for the iron that plants the M4 insert to pass
# under the collar flange - and that is below the arm. So the arm carries a TAB
# under it where the spring rests: as wide as the spring plus a millimetre a
# side, reaching H_tab_spring_arm below the axis, Th_tab_spring_arm deep into
# the arm from the face the spring rests on. Its outer face IS that face, the
# flank at R_rest_spring_arm, so the spring sees one flat seat; and printed top
# face down, the tab grows up from the body with vertical walls and needs no
# support.
zc = D["Z_axis_spring"]
sa = s_along_axis(Qx, Qy, nx, ny, D["R_rest_spring_arm"])
_z_tab0 = zc - D["H_tab_spring_arm"]
if _z_tab0 < z0:
    _wl = D["D_spring_out"]/2 + 1.0
    _tl = D["Th_tab_spring_arm"]
    _c = (Qx + nx*(sa - _tl/2), Qy + ny*(sa - _tl/2))
    _tab = (cq.Workplane("XY").workplane(offset=_z_tab0).center(*_c)
            .rect(_tl, 2*_wl).extrude(z0 + 1.0 - _z_tab0)
            .rotate((_c[0], _c[1], 0), (_c[0], _c[1], 1), math.degrees(math.atan2(ny, nx))))
    arm = arm.union(_tab)
    print("spring tab under the arm: z %.2f..%.2f, %.1f wide, %.1f thick"
          % (_z_tab0, z0, 2*_wl, _tl))
    # THE GUSSET (the thickness is fine, but a chamfer on the side away from
    # the spring joins the tab to the arm). The tab is
    # a cantilever hanging under the arm, and the spring pushes it outwards,
    # along +n: the root that takes the tension is the face away from the
    # spring. A 45 degree wedge there, as wide as the tab, with legs of
    # L_chamfer_tab_spring_arm along the underside of the arm and down the tab.
    # Printed top face down, the tab grows upwards from the body and the sloping
    # face of the wedge looks up: it supports itself.
    _g = D["L_chamfer_tab_spring_arm"]
    _s_in = sa - _tl                               # the face away from the spring
    _cg = (Qx + nx*_s_in, Qy + ny*_s_in)
    _sq = (cq.Workplane("XZ").polyline([(0.0, z0 + 0.5), (-_g - 0.5, z0 + 0.5),
                                         (-_g - 0.5, z0), (0.0, z0 - _g)])
           .close().extrude(_wl, both=True))
    # built about the origin with its own axis along X, then turned so that X
    # becomes n and moved onto the face: the same frame the tab was built in
    _sq = (_sq.rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(ny, nx)))
           .translate((_cg[0], _cg[1], 0)))
    _v_sq = arm.val().intersect(_sq.val()).Volume()
    arm = arm.union(_sq)
    print("tab chamfer: legs %.2f, new volume %.1f mm3 (%.1f already in the arm)"
          % (_g, _sq.val().Volume() - _v_sq, _v_sq))
r_spigot = D["D_spigot_spring"]/2
s_root = sa - D["Dp_spigot_spring"]
spigot = cq.Solid.makeCylinder(r_spigot, D["Dp_spigot_spring"]+D["Proj_spigot_spring"],
                              cq.Vector(Qx+nx*s_root, Qy+ny*s_root, zc), cq.Vector(nx,ny,0))
# The interpenetration is measured, not hoped for: if R_rest_spring_arm falls
# outside the true side, the spigot is born detached and the part comes out in
# two.
_inside = arm.val().intersect(spigot).Volume()
_expected = math.pi*r_spigot**2*D["Dp_spigot_spring"]
# Two thresholds, not one. The first says the solid is there where it was
# asked for; the second that what was asked for is enough - at least one radius
# of depth - because with Dp_spigot_spring at zero the first threshold would be
# zero and would let through exactly the defect it is looking for.
_minimum = math.pi*r_spigot**3
assert _inside > max(0.8*_expected, _minimum), \
    "the spring spigot is not inside the solid: %.1f mm3, at least %.1f are needed" \
    % (_inside, max(0.8*_expected, _minimum))
print("spring spigot: interpenetrating the arm by %.1f mm3 of %.1f" % (_inside, _expected))
arm = arm.union(cq.Workplane(obj=spigot))
print("spring axis: point (%.2f, %.2f, %.2f)  direction (%.4f, %.4f, 0)" % (Qx,Qy,zc,nx,ny))
print("spring rest on the arm at s=%.2f -> r %.2f" % (sa, D["R_rest_spring_arm"]))

cq.exporters.export(arm, OUT + "arm.step")
print("arm %.1f cm3 -> %.0f g in ASA" % (arm.val().Volume()/1000, arm.val().Volume()*1.07e-3))
print("pivot (%.2f, %.2f)  motor (%.2f, %.2f)  spring pad (%.2f, %.2f)" % (Px,Py,Mx,My,Qx,Qy))
