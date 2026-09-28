# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Eleven detail points of a design review, measured on the solids.

Why this is a file of its own. Two of those points - the bearings drawn
4.5 mm above their seat, the motor screws drawn inside the arm plate - went
through a full build that PASSED: the audit exempts every fixing from the
parts it fixes, so a fixing in the wrong place is invisible to it. The others
are shapes that are easy to lose in the next rework: a gusset, a blind seat,
a wall, a web. Outside the audit, each of these costs seconds, so each one can
be broken on purpose and seen to sound - which is the only way a check here
earns its keep.

Breaking on purpose: WHEELLY_BREAK=<name> damages the solid read from out/
the way the defect would, before measuring. Every name in BREAKS must make
exactly its own check fail.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D
import purchased as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
BREAK = os.environ.get("WHEELLY_BREAK", "")
BREAKS = ("bearings", "motor_screws", "recess", "step", "chamfer", "seat",
          "end_wall", "rib", "cover_plate", "tabs", "tab_minus", "tongue", "bushing", "pin",
          "inner_wall", "inner_top", "inner_chamfer", "outer_chamfer", "motor_entry")

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-58s %s" % (name, det))


def load(name):
    return cq.importers.importStep(OUT + name).val()


def solid_at(sol, x, y, z):
    return sol.intersect(cq.Solid.makeSphere(0.1, cq.Vector(x, y, z))).Volume() > 1e-12


arm, hub = load("arm.step"), load("clutch_hub.step")
part, cover = load("box_collar.step"), load("grip_cover.step")
items = C.purchased_parts()
z0, th = D["Z_bottom_arm"], D["Th_arm"]
zf = -D["Z_face_motor"]
Px, Py = D["R_disc"], D["Off_pivot"]
Mx = D["Cd_motor"]

# --- point 4: the bearings sit in the seat of the arm ------------------------
# Probed just outside the mouth of the seat, at both ends of each bearing: the
# arm must be there. Drawn from the motor face, the upper bearing ended at 6.5
# against an arm ending at 2.
if BREAK == "bearings":
    items = [dict(v, z=(v["z"][0] + 4.5, v["z"][1] + 4.5)) if v["name"] == "bearing_F695ZZ"
            else v for v in items]
_r = D["D_mouth_seat_bearings"]/2 + 0.3
_outside = []
for v in items:
    if v["name"] != "bearing_F695ZZ":
        continue
    for zz in (v["z"][0] + 0.2, v["z"][1] - 0.2):
        n = sum(solid_at(arm, Px + _r*math.cos(2*math.pi*k/8), Py + _r*math.sin(2*math.pi*k/8), zz)
                for k in range(8))
        if n < 8:
            _outside.append("z %.1f: %d/8" % (zz, n))
T("4. the two F695ZZ sit inside the seat of the arm", not _outside,
  "; ".join(_outside) or "both, both ends")

# --- point 11: the heads of the motor screws stand on the plate --------------
# Head drawn as the socket head it is; it must touch neither the arm nor the
# clutch, and the arm must be right under it - a head in the air is as wrong
# as a head in the plate.
_heads = []
for v in items:
    if v["name"] != "screw_M3_motor":
        continue
    x, y = v["xy"]
    zt = v["z"][1] + (-1.0 if BREAK == "motor_screws" else 0.0)
    head = cq.Solid.makeCylinder(D["D_head_screw_M3"]/2, D["H_head_screw_M3"],
                                  cq.Vector(x, y, zt))
    va, vh = head.intersect(arm).Volume(), head.intersect(hub).Volume()
    under = sum(solid_at(arm, x + 2.3*math.cos(k*math.pi/2), y + 2.3*math.sin(k*math.pi/2), zt - 0.2)
                for k in range(4))
    if va > 0.01 or vh > 0.01 or under < 4:
        _heads.append("(%.1f, %.1f): in the arm %.2f mm3, in the clutch %.2f, arm under %d/4"
                      % (x, y, va, vh, under))
T("11. the motor screw heads stand on the plate, clear of the clutch",
  not _heads, "; ".join(_heads) or "four of four")

# --- point 9: no recess in the top shoulder of the clutch -------------------
# The ring between the collar of the grub and the rim must be full at the top
# of the shoulder: the recess left the retaining ring over the tread joined by
# one edge.
if BREAK == "recess":
    hub = hub.cut(cq.Solid.makeCylinder(D["D_hub_clutch"]/2 - 1.0, 1.0,
                                        cq.Vector(Mx, 0, D["Z_base_collar_grub"] - 1.0))
                  .cut(cq.Solid.makeCylinder(D["D_collar_grub"]/2, 1.0,
                                             cq.Vector(Mx, 0, D["Z_base_collar_grub"] - 1.0))))
_voids = []
for rr in (D["D_collar_grub"]/2 + 0.5, (D["D_collar_grub"] + D["D_hub_clutch"])/4,
           D["D_hub_clutch"]/2 - 1.3):
    for k in range(12):
        t = 2*math.pi*k/12
        if not solid_at(hub, Mx + rr*math.cos(t), rr*math.sin(t), D["Z_base_collar_grub"] - 0.3):
            _voids.append("r %.1f at %d degrees" % (rr, 30*k))
T("9. the top shoulder of the clutch is full, no recess", not _voids,
  "; ".join(_voids[:4]) or "36 of 36 probes in material")

# --- point 2: no step under the near wall ------------------------------------
# The step grew inside R_rim_inner, where the arm has nothing to do: nothing of
# the arm may be inside that circle.
if BREAK == "step":
    arm = arm.fuse(cq.Solid.makeBox(1.5, 10.0, 2.0,
                                    cq.Vector(Mx - D["Side_motor"]/2 - 2.5, 8.0, z0)))
_inside = arm.intersect(cq.Solid.makeCylinder(D["R_rim_inner"] - 0.05, 40.0,
                                              cq.Vector(0, 0, -20.0))).Volume()
T("2. nothing of the arm inside R_rim_inner (the step is gone)", _inside < 0.01,
  "%.2f mm3" % _inside)

# --- point 1: the chamfer under the spring tab -------------------------------
_ux, _uy = (Mx - Px)/D["L_arm"], (0.0 - Py)/D["L_arm"]
_nx, _ny = -_uy, _ux
if _nx*Px + _ny*Py < 0:
    _nx, _ny = -_nx, -_ny
_Qx, _Qy = Px + _ux*D["Att_spring"], Py + _uy*D["Att_spring"]
_lo, _hi = 0.0, 100.0
for _ in range(60):
    _m = (_lo + _hi)/2
    if math.hypot(_Qx + _nx*_m, _Qy + _ny*_m) < D["R_rest_spring_arm"]:
        _lo = _m
    else:
        _hi = _m
_s_in = _lo - D["Th_tab_spring_arm"]
_g = D["L_chamfer_tab_spring_arm"]
_pt = (_Qx + _nx*(_s_in - _g/3), _Qy + _ny*(_s_in - _g/3), z0 - _g/3)
if BREAK == "chamfer":
    arm = arm.cut(cq.Solid.makeSphere(1.0, cq.Vector(*_pt)))
_past_chamfer = (_Qx + _nx*(_s_in - _g/2 - 0.8), _Qy + _ny*(_s_in - _g/2 - 0.8), z0 - _g/2 - 0.8)
T("1. the chamfer joins the spring tab to the arm",
  solid_at(arm, *_pt) and not solid_at(arm, *_past_chamfer),
  "inside the wedge %s, past its slope %s" % (solid_at(arm, *_pt), solid_at(arm, *_past_chamfer)))

# --- point 10: the centring seat is blind, with a floor over the hub --------
_rs = (D["D_clear_shaft"] + D["D_seat_centring"])/4
_z_floor = zf + (D["H_seat_centring"] + D["Th_plate_motor"])/2
_z_seat = zf + D["H_seat_centring"] - 0.2
if BREAK == "seat":
    arm = arm.cut(cq.Solid.makeCylinder(D["D_seat_centring"]/2, 10.0, cq.Vector(Mx, 0, zf - 1.0)))
_f = sum(solid_at(arm, Mx + _rs*math.cos(k*math.pi/4), _rs*math.sin(k*math.pi/4), _z_floor)
         for k in range(8))
_s = sum(solid_at(arm, Mx + _rs*math.cos(k*math.pi/4), _rs*math.sin(k*math.pi/4), _z_seat)
         for k in range(8))
T("10. the centring seat is blind: a floor over the motor hub",
  _f == 8 and _s == 0, "floor %d/8 at z %.2f, seat free %d/8 at z %.2f"
  % (_f, _z_floor, 8 - _s, _z_seat))

# --- point 8: the end wall of the recess on the pivot side -------------------
_Ro, _W = D["R_out_box"], D["Th_walls_box"]
_RGi = D["R_grip_box"] - _W
# from the very edge of the recess: since the lips went the wall is joined to
# the body there, and a slit between the two would leave these probes in air
_a0 = D["Halfw_grip_box"]
_a1 = _a0 + math.degrees(_W/_RGi)
_am = math.radians((_a0 + _a1)/2)
if BREAK == "end_wall":
    part = part.cut(cq.Solid.makeBox(10.0, 10.0, 40.0, cq.Vector(112.0, 22.0, -15.0))
                      .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 0.0))
_missing = []
for rr in (_RGi + 1.0, _RGi + 4.0):
    for zz in (D["Z_grip_box"], D["Z_top_clutch"] + D["H_hub_clutch"], D["Z_shoulder_box"] - 2.0):
        if not solid_at(part, rr*math.cos(_am), rr*math.sin(_am), zz):
            _missing.append("r %.1f z %.1f" % (rr, zz))
T("8. the end of the recess is one wall with the body, no slit", not _missing,
  "; ".join(_missing) or "6 of 6 probes in material")

# --- point 7: the rib between the head, the skirt and the wheel -------------
import electronics as E
_t = E.T_HEAD_OUT - D["L_rib_head_skirt"]/3
_r = (D["D_body"]/2 + D["Cl_rib_head_body"] + E.R_SKIRT[0])/2 + 1.0
_pr = E.xy(math.sqrt(_r*_r - _t*_t), _t)
if BREAK == "rib":
    part = part.cut(cq.Solid.makeCylinder(3.0, 60.0, cq.Vector(_pr[0], _pr[1], -40.0)))
_no_rib = [zz for zz in (-28.0, -15.0, -5.0) if not solid_at(part, _pr[0], _pr[1], zz)]
# "Clear of the wheel body" used to be measured here too - no material of the
# part inside the wheel's radius below the collar. That space is now INSIDE
# the box by design: the inner wall runs at r 74.4..76.9 under the wheel
# (there is nothing on the camera side there, checked on the reference
# wheel), and
# the wheel body itself is above z 0, where the part does not go. The rib is
# checked for being there; that the bay is closed is W1 below.
T("7. the rib fills the corner at the head",
  not _no_rib, "missing at z %s" % (_no_rib or "none"))

# --- point 5: the cover closes the door over the motor ----------------------
# Probed in the plane of the roof over the whole door, on a grid: every probe
# that is not box must be cover. Nothing may be left open above the clutch.
if BREAK == "cover_plate":
    cover = cover.cut(cq.Solid.makeBox(20.0, 20.0, 10.0, cq.Vector(88.0, -10.0, 20.0)))
_zr = D["Z_shoulder_box"] + D["Th_walls_box"]/2
_holes = []
for i in range(9):
    for j in range(9):
        x = D["Edge_opening_motor_box"] + 1.0 + (121.0 - 2.0 - D["Edge_opening_motor_box"])*i/8
        y = -28.0 + 56.0*j/8
        # past the roof chamfer the probe is outside the part, and the chamfer
        # runs round BOTH backs: the arc about the motor and the back about
        # the wheel. At the height of the probe each one has come in by
        # (probe - start of the slope); the first version measured only the
        # back about the wheel and called the air past the arc "open".
        _setback = _zr - (D["Z_shoulder_box"] + D["Th_walls_box"] - D["Ch_roof_box"])
        if math.hypot(x - Mx, y) > D["R_arc_back_box"] - _setback - 1.0:
            continue
        if math.hypot(x, y) > D["R_out_box"] - _setback - 1.0:
            continue
        if not (solid_at(part, x, y, _zr) or solid_at(cover, x, y, _zr)):
            _holes.append("(%.0f, %.0f)" % (x, y))
_ur = cover.intersect(part).Volume()
T("5. the cover closes the door over the motor, flush with the roof",
  not _holes and _ur < 0.01, "open at %s; cover in the part %.2f mm3"
  % (", ".join(_holes[:5]) or "nowhere", _ur))

# --- the cover is held by thick tabs in pockets, and a tongue at +y ---------
# (the L guides were rejected as too delicate.) Probed at the
# middle of each tab, half way down its pocket: the tab must be there, and the
# box must be there on both sides of it radially - the pad inside, the back
# outside. And at +y the tongue must be inside the end wall's groove, with the
# end wall on both sides of it.
_zf = D["Z_grip_box"] - (D["R_out_box"] - D["Th_cover_grip"] - D["R_grip_box"] - D["Cl_cover_grip"])
_zt = _zf - D["L_tab_cover_grip"]/2
_Ro, _thc, _tt, _cl = D["R_out_box"], D["Th_cover_grip"], D["Th_tab_cover_grip"], D["Cl_cover_grip"]
_rt = _Ro - _thc - _tt/2                         # middle of the tab, on the round back
if BREAK == "tabs":
    cover = cover.cut(cq.Solid.makeBox(8, 30, 6, cq.Vector(_rt - 4, 5, _zt - 3)))
if BREAK == "tab_minus":
    cover = cover.cut(cq.Solid.makeBox(8, 30, 6, cq.Vector(_rt - 4, -25, _zt - 3)))
_tabs = []
for _deg in (D["Ang_tab_cover_grip"],):
    _a = math.radians(_deg)
    _t = solid_at(cover, _rt*math.cos(_a), _rt*math.sin(_a), _zt)
    _inside = solid_at(part, (_rt - _tt/2 - _cl - 1.0)*math.cos(_a), (_rt - _tt/2 - _cl - 1.0)*math.sin(_a), _zt)
    _outside = solid_at(part, (_Ro - 0.5)*math.cos(_a), (_Ro - 0.5)*math.sin(_a), _zt)
    if not (_t and _inside and _outside):
        _tabs.append("%+.1f deg: tab %s, pad %s, back %s" % (_deg, _t, _inside, _outside))
# the -y tab: wherever the generator put it, there must be one - some cover
# below the foot on the -y half of the recess
_minus = any(solid_at(cover, _rt*math.cos(math.radians(d/4.0)), _rt*math.sin(math.radians(d/4.0)), _zt)
            for d in range(-40, 1))
if not _minus:
    _tabs.append("no tab under the foot between -10 and 0 deg")
T("5b. the cover sits on thick tabs in pockets of the box", not _tabs,
  "; ".join(_tabs) or "+y tab in its pocket, -y tab present")
_RG = D["R_grip_box"]
_rl = (_RG + (_Ro - D["Th_walls_box"]))/2
_al = math.radians(D["Halfw_grip_box"]) + (D["Dp_groove_cover_grip"]/2)/_rl
if BREAK == "tongue":
    cover = cover.cut(cq.Solid.makeSphere(2.0, cq.Vector(_rl*math.cos(_al), _rl*math.sin(_al), 12.0)))
_tongue = [solid_at(cover, _rl*math.cos(_al), _rl*math.sin(_al), zz) for zz in (4.0, 12.0)]
_sides = [solid_at(part, (_rl + s_*(D["W_groove_cover_grip"]/2 + 0.6))*math.cos(_al),
               (_rl + s_*(D["W_groove_cover_grip"]/2 + 0.6))*math.sin(_al), 12.0) for s_ in (-1, 1)]
T("5c. at +y the cover's tongue runs in a groove of the end wall", all(_tongue) and all(_sides),
  "tongue %s, groove sides %s" % (_tongue, _sides))

# --- the bushing is on the washer, and the collar has no pin -----------------
washer = load("pivot_washer.step")
if BREAK == "bushing":
    washer = washer.cut(cq.Solid.makeCylinder(4.0, 20.0, cq.Vector(Px, Py, z0 + 1.0)))
if BREAK == "pin":
    part = part.fuse(cq.Solid.makeCylinder(D["D_pivot_arm"]/2, 9.0, cq.Vector(Px, Py, z0)))
_rbush = (D["D_pivot_arm"] + D["D_hole_washer_pivot"])/4
_ztop = D["Z_top_arm"] + D["Th_flange_bearing"]
_bush = [solid_at(washer, Px + _rbush*math.cos(k*math.pi/2), Py + _rbush*math.sin(k*math.pi/2), zz)
       for k in range(4) for zz in (z0 + 0.5, (z0 + _ztop)/2, _ztop - D["Ch_bushing_pivot"] - 0.2)]
_pin = [zz for zz in (z0 + 0.5, (z0 + _ztop)/2)
          if solid_at(part, Px + _rbush, Py, zz)]
T("7b. the bushing is printed on the washer, the collar has no pin",
  all(_bush) and not _pin,
  "bushing %d/12 in material; collar material at the pin at z %s"
  % (sum(_bush), _pin or "none"))

# --- the inner wall under the wheel, and the motor's way in ----------------
# The wall, the floor strip, the closed ends and the 10 mm chamfer, and the motor
# dropped straight in from the top. Measured on the solids, and NOT from
# R_INNER_WALL: the rays below go out from inside the wheel and ask only
# whether they meet material before the collar radius, wherever the wall is.
import electronics as _E
panel = load("board_panel.step")
_ZTf = D["Z_floor_box"] + D["Th_walls_box"]            # top of the floor
_zfl = -D["Th_flange_collar"]                          # underside of the collar flange
if BREAK == "inner_wall":      # the wall gone, as before
    part = part.cut(cq.Solid.makeCylinder(78.5, 40.0, cq.Vector(0, 0, _ZTf + 12.0))
                      .cut(cq.Solid.makeCylinder(70.0, 40.0, cq.Vector(0, 0, _ZTf + 12.0))))
if BREAK == "inner_top":       # the wall stopping 3 mm short of the collar
    part = part.cut(cq.Solid.makeCylinder(78.5, 3.0, cq.Vector(0, 0, _zfl - 3.0))
                      .cut(cq.Solid.makeCylinder(70.0, 3.0, cq.Vector(0, 0, _zfl - 3.0))))


def _ray_closed(a, z):
    """A radial ray at angle a and height z, from r 60 (inside the wheel) out to
    the collar radius: does it meet box, panel or collar?"""
    c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
    r0, r1 = 60.0, D["R_out_collar"]
    ray = cq.Solid.makeBox(r1 - r0, 0.2, 0.2).translate(cq.Vector(r0, -0.1, z - 0.1)) \
        .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)
    return part.intersect(ray).Volume() > 1e-6 or panel.intersect(ray).Volume() > 1e-6


# the span: from where the arc round the motor meets the wall region to the
# head plane, both at r 76 - bounds only, the property is what the rays find
_a_lo = math.degrees(math.atan2(-17.0, 73.5)) + 1.0
_a_hi = _E.head_angle(76.0, "in") - 1.0
_open = []
for _k in range(15):
    _a = _a_lo + (_a_hi - _a_lo)*_k/14
    for _z in (_ZTf + 1.0, _ZTf + 10.0, (_ZTf + _zfl)/2, _zfl - 1.0, _zfl - 0.3):
        if not _ray_closed(_a, _z):
            _open.append("%.0f deg z %.1f" % (_a, _z))
T("W1. the bay is closed towards the wheel axis, floor to collar", not _open,
  "; ".join(_open[:6]) or "75 rays, all closed")

# the chamfers: the corner between the inner wall and the
# floor is a SLOPED WALL - a 10 mm chamfer inside, the same taken off outside,
# parallel, so the wall keeps its thickness. Found on the solid: the wall's
# outer face by a ray at mid height, the top of the floor by a vertical ray
# past the chamfer. Then across the 45 degree diagonal from that corner: void
# inside the slope, material in the band of the wall, void outside the outer
# slope. At two angles well inside the run of the chamfers.
if BREAK == "inner_chamfer":   # the inside chamfer gone: a square corner again
    part = part.cut(cq.Solid.makeCylinder(90.0, 9.0, cq.Vector(0, 0, _ZTf + 0.01))
                      .cut(cq.Solid.makeCylinder(76.95, 9.0, cq.Vector(0, 0, _ZTf + 0.01))))
if BREAK == "outer_chamfer":   # the outside chamfer filled back in
    part = part.fuse(cq.Solid.makeCylinder(88.0, 12.0, cq.Vector(0, 0, D["Z_floor_box"]))
                       .cut(cq.Solid.makeCylinder(74.45, 12.0, cq.Vector(0, 0, D["Z_floor_box"])))
                       .intersect(cq.Solid.makeBox(200, 200, 12, cq.Vector(0, 0, D["Z_floor_box"]))))
_C = D["L_chamfer_wall_inner_floor"]
_Wp = D["Th_walls_box"]
_chamfers = []
for _a_s in (30.0, 50.0):
    _cs, _sn = math.cos(math.radians(_a_s)), math.sin(math.radians(_a_s))
    _P = lambda r, z: solid_at(part, r*_cs, r*_sn, z)
    # FOUND WITH A RAY, not by stepping a probe: stepping 0.05 at a time, the
    # probe at r 74.50 exactly came back empty on a solid wall - an OCCT
    # boolean that fails on a coincidence - and the check measured the wall as
    # half a tenth thick. A thin bar through the part, and the
    # extent of the pieces it cuts, do not depend on hitting a lucky number.
    def _segments(p0, p1):
        v = cq.Vector(*p1) - cq.Vector(*p0)
        bar = cq.Solid.makeBox(v.Length, 0.1, 0.1, cq.Vector(0, -0.05, -0.05))
        bar = bar.transformShape(cq.Matrix())
        u = v.normalized()
        # the bar along u from p0: rotate x onto u, then move
        ax = cq.Vector(1, 0, 0).cross(u)
        if ax.Length > 1e-9:
            bar = bar.rotate(cq.Vector(0, 0, 0), ax, math.degrees(math.acos(max(-1, min(1, u.x)))))
        bar = bar.translate(cq.Vector(*p0))
        pieces = part.intersect(bar).Solids()
        return sorted(((cq.Vector(*p0) - q.Center()).Length - q.BoundingBox().DiagonalLength/2,
                       (cq.Vector(*p0) - q.Center()).Length + q.BoundingBox().DiagonalLength/2)
                      for q in pieces)
    _t = _segments((60.0*_cs, 60.0*_sn, _zfl - 4.0), (90.0*_cs, 90.0*_sn, _zfl - 4.0))
    _face = 60.0 + _t[0][1] if _t else 0.0      # outer face of the wall
    # Vertical rays across the sloped wall, at k mm out from the wall face: each
    # meets one piece of material, from the outer slope up to the inner one.
    # The floor is no reference: past the chamfer, along most of its run, is
    # the opening of the panel. So the slope is measured on itself: the piece
    # must be W*sqrt(2) tall (a wall W thick at 45 degrees), its top must fall
    # 1 mm for every mm out (45 degrees), and inside the wall the material must
    # start the outer leg above the bottom of the part.
    _zb = part.BoundingBox().zmin
    def _piece_v(k):
        r = _face + k
        t = _segments((r*_cs, r*_sn, _zb - 1.0), (r*_cs, r*_sn, _zb + 25.0))
        return (_zb - 1.0 + t[0][0], _zb - 1.0 + t[0][1]) if t else (None, None)
    _k1, _k2 = 3.0, 7.0
    (_lo1, _hi1), (_lo2, _hi2) = _piece_v(_k1), _piece_v(_k2)
    _lo0, _ = _piece_v(-_Wp/2)                    # inside the wall
    _expected_L = _C + (2.0 - math.sqrt(2.0))*_Wp
    _err = []
    if None in (_lo1, _hi1, _lo2, _hi2, _lo0):
        _err.append("a ray met nothing")
    else:
        for _lo, _hi, _k in ((_lo1, _hi1, _k1), (_lo2, _hi2, _k2)):
            if abs((_hi - _lo) - _Wp*math.sqrt(2.0)) > 0.3:
                _err.append("at %.0f mm out the wall is %.2f tall, not %.2f" % (_k, _hi - _lo, _Wp*math.sqrt(2.0)))
        _slope = (_hi2 - _hi1)/(_k2 - _k1)
        if abs(_slope + 1.0) > 0.1:
            _err.append("the slope falls %.2f per mm, not 1" % -_slope)
        _L = (_lo0 - _zb) + _Wp/2
        if abs(_L - _expected_L) > 0.4:
            _err.append("outer leg %.2f, not %.2f" % (_L, _expected_L))
    if _err:
        _chamfers.append("%.0f deg (face r %.2f): %s" % (_a_s, _face, "; ".join(_err)))
T("W2. the corner of the inner wall is a sloped wall: %.0f mm chamfer in and out" % _C,
  not _chamfers, "; ".join(_chamfers) or "at 30 and 50 deg: void, wall %.1f thick, void" % _Wp)

# the motor straight UP FROM BELOW, through the hatch - strategy C: the motor
# no longer comes in from the top, the clutch sits over it by then. This used
# to read "straight down from the top", and
# failed only when the boss of the cover's second screw grew behind the
# chamfer, on a way the motor no longer takes. The maker's motor, lowered 60
# mm and raised home every millimetre, must not meet the part. What it shares with
# the part at home is the audit's business (it is 0.64 mm3 of the maker's
# model on the arm's seat), so only what is met ON THE WAY counts.
import outline_motor as _SM
_mot = _SM.body()      # without its leads: they are wires, they bend
if BREAK == "motor_entry":     # a plate across the hatch, on the motor's way up
    part = part.fuse(cq.Solid.makeBox(6.0, 30.0, 2.0).translate(cq.Vector(95.0, -15.0, -45.0)))
_bm = _mot.BoundingBox()
_col = cq.Solid.makeBox(_bm.xlen + 4, _bm.ylen + 4, 120.0).translate(cq.Vector(_bm.xmin - 2, _bm.ymin - 2, _bm.zmin - 62))
_loc = part.intersect(_col)
_home = _loc.intersect(_mot).Volume()
_worst, _where = 0.0, 0.0
for _dz in range(1, 61):
    _v = _loc.intersect(_mot.translate(cq.Vector(0, 0, -_dz))).Volume() - _home
    if _v > _worst:
        _worst, _where = _v, _dz
T("W3. the motor comes up straight from below, through the hatch", _worst <= 0.5,
  "worst %.1f mm3 at %d mm below home" % (_worst, _where) if _worst > 0.5 else "free all the way")

if BREAK:
    print("!! BROKEN ON PURPOSE: %s" % BREAK)
print("--- OK (%d) ---" % len(ok)); [print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko)); [print("  !", r) for r in ko]
sys.exit(1 if ko else 0)
