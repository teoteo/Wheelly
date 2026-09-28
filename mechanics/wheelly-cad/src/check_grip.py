# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The grip for turning the wheel by hand, and its cover.

Four questions, and none of them is answered by rereading the parameters the
grip was built from: the overhangs to print, the clearance from the clutch,
whether the tread really stands out, and whether the cover closes.

IT LIVES IN A MODULE OF ITS OWN and not inside check_audit for a practical
reason: these checks read only two STEP files and cost half a minute, while
the audit costs twelve. Breaking a check on purpose to see whether it can fail
- which in this project is not optional - cost an hour for four faults with
the audit in the way, and a check one is reluctant to test is a check that
does not get tested.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D, out_subdir
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Pnt, gp_Vec
from OCP.TopAbs import TopAbs_REVERSED, TopAbs_IN, TopAbs_ON
from OCP.BRepTopAdaptor import BRepTopAdaptor_FClass2d
from OCP.gp import gp_Pnt2d

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


_box_solid = cq.importers.importStep(OUT + out_subdir("box") + "box.step").val()

# ---------------- the grip for turning the wheel by hand ----------------
# Three questions, and none of them is answered by rereading the parameters
# the grip was built from: the clearance from the clutch, the overhangs to
# print, and whether the tread really stands out. The first two are what the
# grip promises - no supports needed in there - and the
# third is the reason the grip exists.

_cover_step = OUT + "grip_cover.step"
_cover = cq.importers.importStep(_cover_step).val() if os.path.exists(_cover_step) else None
_tpu = cq.importers.importStep(OUT + "clutch_tyre.step").val()
_clutch_hub_asa = cq.importers.importStep(OUT + "clutch_hub.step").val()


def _overhangs(f, up, inside, n=9):
    """How much AREA of this face, inside the zone of interest, faces down
    steeper than the overhang angle. Returns (estimated area, worst angle,
    worst point).

    BY SAMPLES AND NOT BY WHOLE FACE, and the difference is not academic: the
    first draft took the normal at the centre of the face and kept or
    discarded the whole face at once. Breaking the roof of the opening on
    purpose - the check that was supposed to notice it - did not sound,
    because the new overhang merged with the ROOF OF THE COMPARTMENT, which is
    a single face of 6,262 mm2 already known and accepted, and its centre
    falls forty degrees from here. A face half inside the zone and half
    outside can be neither kept nor discarded: it must be measured for the
    part that lies inside.

    `up` says which way is up in the PRINT orientation of the part, which for
    the cover is not the assembly's: it prints upside down, on its flat
    face."""
    ad = BRepAdaptor_Surface(f.wrapped)
    u0, u1 = ad.FirstUParameter(), ad.LastUParameter()
    v0, v1 = ad.FirstVParameter(), ad.LastVParameter()
    if any(abs(x) > 1e8 for x in (u0, u1, v0, v1)):
        return 0.0, None, None
    sign = -1.0 if f.wrapped.Orientation() == TopAbs_REVERSED else 1.0
    lim = D["Ang_overhang_printing"]
    # The parameter rectangle is NOT the face: a flat face like the roof of
    # the compartment has an arbitrary outline, and sampling the rectangle
    # ends up in its holes. It happened: the check reported an overhang of
    # 228 mm2 at r 121.6, which is in the middle of the void of the recess.
    # Every sample must therefore be classified against the true outline.
    in_face = BRepTopAdaptor_FClass2d(f.wrapped, 1e-6)
    hits, valid, worst, where = 0, 0, -1.0, None
    for i in range(n):
        for j in range(n):
            u = u0 + (u1 - u0)*(i + 0.5)/n
            v = v0 + (v1 - v0)*(j + 0.5)/n
            if in_face.Perform(gp_Pnt2d(u, v)) not in (TopAbs_IN, TopAbs_ON):
                continue
            valid += 1
            pnt, du, dv = gp_Pnt(), gp_Vec(), gp_Vec()
            ad.D1(u, v, pnt, du, dv)
            nv = du.Crossed(dv)
            if nv.Magnitude() < 1e-12:
                continue
            nv.Normalize(); nv.Multiply(sign*up)
            if nv.Z() >= -1e-9:
                continue
            th = math.degrees(math.asin(min(1.0, -nv.Z())))
            q = (pnt.X(), pnt.Y(), pnt.Z())
            if th <= lim + 0.5 or not inside(q):
                continue
            hits += 1
            if th > worst:
                worst, where = th, q
    # the area is estimated on the samples that fall INSIDE the face, or else
    # a narrow face inside a wide rectangle would count for nothing
    return (f.Area()*hits/float(valid) if valid else 0.0), worst, where


def _to_support(solid, up, inside):
    """The faces that want a support: facing down beyond the overhang angle,
    inside the zone, and wide enough for a support to fit under them. The
    BED PLANE is discarded: it faces down by necessity and is not an
    overhang."""
    a_min = D["L_min_support_printing"]**2
    zs = [v.Z for v in solid.Vertices()]
    z_bed = max(zs) if up < 0 else min(zs)
    out = []
    for f in solid.Faces():
        if f.Area() < a_min:
            continue
        if abs(f.Center().z - z_bed) < 1e-6:
            continue                      # it is the face resting on the bed
        area, th, pnt = _overhangs(f, up, inside)
        if area < a_min:
            continue
        out.append("%.0f mm2 at %.0f degrees (z %.1f, r %.1f, ang %.1f)"
                     % (area, th, pnt[2], math.hypot(pnt[0], pnt[1]),
                        math.degrees(math.atan2(pnt[1], pnt[0]))))
    return out


# The zone of the grip: everything that lies FURTHER OUT than the inner face of
# the recessed wall, inside the window of the recess and above the bottom of
# the flare. Taken this way it does not contain the roof of the mechanical
# compartment, which does not face in there: between the recess and the roof
# there is the recessed wall, which rises to the top. If one day that wall
# disappeared, the roof would widen as far as here - and that is exactly the
# fault this check must hear.
_R_IN = D["R_grip_box"] - D["Th_walls_box"] - 0.5
_A_IN = D["Halfw_grip_box"] + 2.0
_Z_IN = D["Z_grip_box"] - (D["R_out_box"] - D["R_grip_box"] + D["Th_walls_box"]) - 1.0


def _in_grip(p):
    return (math.hypot(p[0], p[1]) >= _R_IN
            and abs(math.degrees(math.atan2(p[1], p[0]))) <= _A_IN
            and p[2] >= _Z_IN)


_ov_box = _to_support(_box_solid, +1, _in_grip)
T("grip: no overhang to support in the box", not _ov_box,
  "; ".join(_ov_box))
if _cover is not None:
    # -1: the cover prints UPSIDE DOWN, on its top face. It printed standing
    # at first; then it took on the plate that closes the
    # door over the motor, and standing, that plate is a 45 x 60 overhang.
    # Nothing accepted: the second screw's countersink was tilted, square to
    # the chamfer band, and its 10 mm2 were briefly forgiven here; the screw
    # is vertical now, like the first, and its
    # countersink opens on the bed.
    _ov_cover = _to_support(_cover, -1, lambda p: True)
    T("grip: no overhang to support in the cover", not _ov_cover, "; ".join(_ov_cover))

# 2) the clearance from the clutch, measured between the solids
_dmin = []
for _n, _o in (("TPU ring", _tpu), ("ASA hub", _clutch_hub_asa)):
    _d = BRepExtrema_DistShapeShape(_box_solid.wrapped, _o.wrapped)
    _d.Perform()
    _dmin.append((_n, _d.Value()))
_tight = ["%s %.3f" % (n, v) for n, v in _dmin if v < D["Cl_grip_clutch"] - 0.01]
T("grip: the wall does not touch the clutch", not _tight,
  "; ".join(_tight) or "min %.3f mm" % min(v for _, v in _dmin))

# 3) the tread really stands out, and by as much as is written
# Measured on the SOLID: the largest radius at which the box has material on
# the clutch axis, against the radius of the tread there. Deriving it from
# R_grip_box would mean asking the parameter whether the parameter has been
# respected.
def _r_max_material(sol, ang, z, r0, r1, step=0.005):
    """The largest radius at which that solid has material, along that ray and
    at that height. A coarse scan to find the last full point, then bisection
    down to the wanted step: isInside on a solid like the box costs quite a
    lot, and reading it one hundredth at a time the check took two minutes
    instead of two seconds."""
    a = math.radians(ang)
    def full(r):
        return sol.isInside(cq.Vector(r*math.cos(a), r*math.sin(a), z), 1e-9)
    n = max(2, int(abs(r1 - r0)/0.25))
    last = None
    for i in range(n + 1):
        r = r0 + (r1 - r0)*i/n
        if full(r):
            last = r
    if last is None:
        return None
    lo, hi = last, min(r1, last + abs(r1 - r0)/n)
    while hi - lo > step:
        mid = (lo + hi)/2.0
        if full(mid):
            lo = mid
        else:
            hi = mid
    return lo


_z_tread = D["Z_plane_mid_disc"]
_r_tpu = _r_max_material(_tpu, 0.0, _z_tread, 110.0, 126.0)
_r_par = _r_max_material(_box_solid, 0.0, _z_tread, D["R_grip_box"] - 4.0, 132.0)
if _r_tpu is None:
    T("grip: the tread stands out of the wall", False, "tread not found")
elif _r_par is not None and _r_par > _r_tpu:
    T("grip: the tread stands out of the wall", False,
      "the box reaches %.2f, the tread %.2f" % (_r_par, _r_tpu))
else:
    # With no material in front, the reference wall is the recess's.
    # The tread is measured on the solid, which sits where the CAD draws it:
    # in the machine the arm keeps it squashed against the disc, so what the
    # thumb finds lies Squash_clutch further in. That is why R_grip_box has
    # that term, and why here the expected value is Proj_tread_grip PLUS the
    # squash: measuring as drawn one sees the projection when new, in the
    # hand one finds one squash less.
    _proj = _r_tpu - D["R_grip_box"]
    _expected = D["Proj_tread_grip"] + D["Squash_clutch"]
    T("grip: the tread stands out of the wall",
      abs(_proj - _expected) < 0.05,
      "stands out %.2f as drawn (%.2f in use), expected %.2f"
      % (_proj, _proj - D["Squash_clutch"], _expected))

# 4) with the cover fitted the clutch can no longer be seen
if _cover is not None:
    _open = []
    for _a in (0.0, D["Halfw_grip_slot"]/2, D["Halfw_grip_slot"] - 0.3):
        for _z in (D["Z_top_clutch"] + 1.0, _z_tread, D["Z_top_clutch"] + D["H_hub_clutch"] - 1.0):
            _c = math.cos(math.radians(_a)), math.sin(math.radians(_a))
            _full_here = False
            _r = D["R_grip_box"]
            while _r <= 131.0:
                _p = cq.Vector(_r*_c[0], _r*_c[1], _z)
                if _box_solid.isInside(_p, 1e-9) or _cover.isInside(_p, 1e-9):
                    _full_here = True
                    break
                _r += 0.25
            if not _full_here:
                _open.append("ang %.1f z %.1f" % (_a, _z))
    T("grip: with the cover fitted the clutch is not visible", not _open,
      "; ".join(_open))


# 5) THE COVER AND THE ROOF CHAMFER. Since the roof got its
#    Ch_roof_box chamfer the cover has no flat flap on top: its own 45 degree
#    plate closes the recess from above, and it prints standing on a flat
#    foot. Four things follow, and none of them was checked before, because
#    none of them could go wrong with a flat-topped cover: that it is flush
#    with the slope, that nothing is open from above, that it stays clear of
#    the part it closes, and that the foot it prints on is there. Measured on
#    box_collar.step, the part that is printed.
if _cover is not None:
    _pz = cq.importers.importStep(OUT + "box_collar.step").val()
    _W, _CH = D["Th_walls_box"], D["Ch_roof_box"]
    _Z_T = D["Z_shoulder_box"] + _W
    _z_ch = _Z_T - _CH                                  # where the slope starts
    _MX, _RA, _Ro = D["Cd_motor"], D["R_arc_back_box"], D["R_out_box"]
    _AG = D["Halfw_grip_box"]

    def _skin(a):
        """The horizontal distance of the vertical outer face, and the centre it
        is measured from: the wheel axis on the back, the shaft on the arc."""
        return ((0.0, 0.0), _Ro) if a >= 0 else ((_MX, 0.0), _RA)

    def _on_skin(a, z, d):
        """A point at signed distance d INSIDE the outer skin, at angle a about
        the wheel and height z, on the sloped part (z above _z_ch)."""
        (cx, cy), R = _skin(a)
        # the direction from the skin centre towards the point of the skin
        # that lies on the ray from the wheel axis at angle a
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        if a < 0:
            c = _MX*ux; far = c + math.sqrt(_RA*_RA - _MX*_MX + c*c)
            px, py = far*ux - cx, far*uy - cy
            L = math.hypot(px, py); ux, uy = px/L, py/L
        # d along the normal of a 45 degree face is d*sqrt(2) across; below
        # the start of the slope the face is vertical and d is d
        if z > _z_ch:
            h = R - (z - _z_ch) - d*math.sqrt(2.0)
        else:
            h = R - d
        return cq.Vector(cx + ux*h, cy + uy*h, z)

    _inside = lambda sol, p: sol.isInside(p, 1e-6)
    _off_flush, _holes_on_top = [], []
    for _a in (-0.6*_AG, -0.3*_AG, 0.3*_AG, 0.6*_AG):
        for _z in (_z_ch + 3.0, _z_ch + 6.0):
            # flush: outside the slope is air, 0.6 inside it is the cover.
            # Outside at THREE depths, not one: breaking it on purpose with a
            # plate left unchamfered - 127.5 to 130 - the single probe 0.3 out
            # sat at r 127.4 and missed it; the plate starts further out.
            for _d in (-0.3, -1.5, -3.0):
                if _inside(_cover, _on_skin(_a, _z, _d)) or _inside(_pz, _on_skin(_a, _z, _d)):
                    _off_flush.append("stands out at %+.1f degrees z %.1f (%.1f out)" % (_a, _z, -_d))
            if not _inside(_cover, _on_skin(_a, _z, 0.6)):
                _off_flush.append("missing at %+.1f degrees z %.1f" % (_a, _z))
    T("grip: the cover is flush with the chamfer", not _off_flush, "; ".join(_off_flush[:4]))

    # closed from above: every vertical line over the recess, from the top of
    # the clutch hub up, meets the cover or the part - as long as it starts
    # inside the outer skin at that height (outside it is outside the box)
    # from the top of the clutch hub, MEASURED on the hub: Z_top_clutch +
    # H_hub_clutch is the top of the tread, eight millimetres lower, and the
    # first version started there and probed the side of the recess
    _z0 = _clutch_hub_asa.BoundingBox().zmax
    for _a in [-_AG + 0.5 + _k*(2*_AG - 1.0)/10 for _k in range(11)]:
        for _r in [D["R_grip_box"] + 0.5 + _k for _k in range(10)]:
            _x, _y = _r*math.cos(math.radians(_a)), _r*math.sin(math.radians(_a))
            _p_sk = _on_skin(_a, _z0 + 0.1, 0.4)
            if math.hypot(_x - _skin(_a)[0][0], _y - _skin(_a)[0][1]) > \
               math.hypot(_p_sk.x - _skin(_a)[0][0], _p_sk.y - _skin(_a)[0][1]):
                continue
            _ray = cq.Solid.makeCylinder(0.05, _Z_T + 5.0 - _z0, cq.Vector(_x, _y, _z0))
            if _ray.intersect(_cover).Volume() < 1e-6 and _ray.intersect(_pz).Volume() < 1e-6:
                _holes_on_top.append("%+.1f degrees r %.1f" % (_a, _r))
    T("grip: with the cover fitted the recess is closed from above", not _holes_on_top,
      "; ".join(_holes_on_top[:4]))

    _vi = _cover.intersect(_pz).Volume()
    _di = _cover.distance(_pz)
    T("grip: the cover does not touch the part it closes", _vi < 1e-3 and _di > 0.05,
      "interference %.3f mm3, distance %.3f mm" % (_vi, _di))

    # the foot it prints on: a flat face at the bottom, as big as a stripe of
    # plate along the whole cover - a knife edge has no area there
    _zb = _cover.BoundingBox().zmin
    _foot = sum(f.Area() for f in _cover.Faces()
                 if f.geomType() == "PLANE" and abs(f.Center().z - _zb) < 1e-4
                 and abs(f.normalAt(f.Center()).z) > 0.999)
    _minimum = D["Th_cover_grip"] * 20.0
    T("grip: the cover has the flat foot to print standing on",
      _foot >= _minimum, "%.0f mm2 at z %.2f (at least %.0f)" % (_foot, _zb, _minimum))

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
