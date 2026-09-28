# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

import math, csv, ezdxf, cadquery as cq, itertools, os
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
from parameters import P, D, out_subdir
from outline_arm import outline as arm_outline
import arm_travel as CB
from drawings import module_holes as _module_holes
import electronics as E
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GeomAbs import GeomAbs_SurfaceType
ok=[];ko=[]
def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))

# 0) is the assembly younger than the parts it contains?
# Before anything else, because if it is not, everything that follows measures
# a part that no longer exists. Half of the checks below read
# full_assembly.step to know what is inside the box or around the pivot:
# regenerating a single module by hand - something done all the time while
# trying a change - the assembly stays behind and the measurements become
# false without saying so. It happened, and twice: a measurement of the
# clearance in the bay said half a millimetre whatever the height of the
# ceiling, because the assembly still contained the old box and the
# comparison by volume no longer recognised it.
_ASS = OUT + out_subdir("full_assembly") + "full_assembly.step"
_stale = []
if os.path.exists(_ASS):
    _t_ass = os.path.getmtime(_ASS)
    # The subfolders are looked into too: since the references live in
    # out/references/, scanning out/ alone would have stopped seeing them - and
    # a check that weakens while a file is moved is worse than one that does
    # not exist, because it keeps saying yes.
    for _d in ("", "references" + os.sep, "tools" + os.sep, "electronics" + os.sep):
        _folder = OUT + _d
        if not os.path.isdir(_folder):
            continue
        for _f in os.listdir(_folder):
            if not _f.endswith(".step") or _f == "full_assembly.step":
                continue
            if os.path.getmtime(_folder + _f) > _t_ass + 1.0:
                _stale.append(_d + _f)
T("the assembly is up to date with every part", not _stale,
  "regenerated after the assembly: " + ", ".join(sorted(_stale)))

# 1) CSV consistent with the parameters
with open(OUT + "drawings/filter_wheel_parameters.csv", encoding="utf-8") as f:
    rows={r["Nome"]: float(r["Valore"]) for r in csv.DictReader(f)}
T("CSV: same number of parameters", len(rows)==len(D), "%d vs %d"%(len(rows),len(D)))
diff=[k for k in D if k in rows and abs(rows[k]-D[k])>0.005]
T("CSV: values identical to the parameters", not diff, str(diff))

# 1bis) do the expressions still say what the values say?
# parameters.py keeps the expression next to the already computed value, and
# cannot redo the sums: changing a parameter upstream, the derived ones stay
# put until somebody updates them by hand. The editor, instead, can evaluate
# the expressions - that is all of ui_model - so here the file is read again
# with its model and compared parameter by parameter. It is the check that had
# been missing since Chord_slot had to follow Dp_slot_front by hand.
# The comparison that counts is between D - that is, the numbers the
# generators really use, base plus overrides - and the recomputed model: if a
# derived value stayed behind, the two diverge. It is not compared with the
# value written in the base, which diverges on its own every time an override
# overwrites it.
import ui_model
_mod = ui_model.Model()
_broken = ["%s: %s" % (p_.nome, p_.error) for p_ in _mod.parameters if p_.error]
T("every expression evaluates", not _broken, "; ".join(_broken))
_misaligned = ["%s: %s is %.2f, not %.2f" % (p_.nome, p_.espressione, p_.computed, p_.valore)
                 for p_ in _mod.parameters if getattr(p_, "disallineato", False)]
T("literal parameters consistent with the value", not _misaligned, "; ".join(_misaligned))
_deviations = ["%s: the drawings use %.2f, the expression says %.2f" % (k, D[k], _mod.values_by_name[k])
           for k in D if k in _mod.values_by_name and abs(D[k] - _mod.values_by_name[k]) > 0.005]
T("derived values level with the expressions", not _deviations, "; ".join(_deviations))

# 2) DXF vs parameters
def circles(f):
    return [(c.dxf.center.x,c.dxf.center.y,c.dxf.radius)
            for c in ezdxf.readfile(OUT+"drawings/"+f).modelspace().query("CIRCLE")]
def has(cs,x,y,r,tol=0.05):
    return any(abs(a-x)<tol and abs(b-y)<tol and abs(c-r)<tol for a,b,c in cs)

cb=circles("arm_plan.dxf")
T("arm_plan: bearing seat on the pivot",
  has(cb, D["R_disc"], D["Off_pivot"], D["D_seat_bearings_printed"]/2))
T("arm_plan: centring seat on the motor axis",
  has(cb, D["Cd_motor"], 0.0, D["D_seat_centring"]/2))
m3=[c for c in cb if abs(c[2]-D["D_holes_M3_printed"]/2)<0.02]
T("arm_plan: 4 M3 holes", len(m3)==4, "found %d"%len(m3))
rr=sorted(round(math.hypot(a,b),2) for a,b,_ in m3)
T("arm_plan: M3 holes outside the inner rim", min(rr)>D["R_rim_inner"], str(rr))

cc=circles("collar_plan.dxf")
T("collar_plan: clutch on the motor axis", has(cc, D["Cd_motor"],0.0,D["D_clutch"]/2))
T("collar_plan: pivot pin", has(cc, D["R_disc"], D["Off_pivot"], D["D_pivot_arm"]/2))

cs=circles("sensor_bracket.dxf")
T("sensor_bracket: ring on the magnet", has(cs,0,0,D["D_hole_magnet_printing"]/2))
T("sensor_bracket: M2 holes at the module pitch",
  all(has(cs, _cx, _cy, D["D_holes_M2"]/2) for _cx, _cy in _module_holes()))

msp=ezdxf.readfile(OUT + "drawings/clutch_section.dxf").modelspace()
xs=[p[0] for pl in msp.query('LWPOLYLINE[layer=="PROFILO"]') for p in pl.get_points("xy")]
T("clutch_section: contact at the disc rim", abs(min(xs)-D["R_disc"])<0.05, "min X %.2f"%min(xs))

# 3) STEP: envelopes and volumes
def bb(f):
    # the name comes with .step attached: the subfolder is always decided by
    # out_subdir, which wants the bare name
    return cq.importers.importStep(
        OUT + out_subdir(f[:-5]) + f).val().BoundingBox()
b=bb("filter_wheel_body.step")
T("body: height = H_body", abs((b.zmax-b.zmin)-D["H_body"])<0.02, "%.2f"%(b.zmax-b.zmin))
T("body: diameter = D_body", abs((b.xmax-b.xmin)-D["D_body"])<0.05, "%.2f"%(b.xmax-b.xmin))
b=bb("arm.step")
# The top is no longer z 0 everywhere: above the motor the plate grows by
# Th_more_plate_motor, to gain thickness without bringing the motor down.
_z_top_arm = -D["Z_face_motor"] + D["Th_plate_motor"]
T("arm: bottom at Z_bottom_arm, top at the motor plate",
  abs(b.zmax - max(0.0, _z_top_arm)) < 0.02 and b.zmin <= D["Z_bottom_arm"]+0.02,
  "z %.1f..%.1f"%(b.zmin,b.zmax))
# THE PIN IS THE BUSHING ON THE WASHER (the washer is joined to the part
# inside the bearings). What this check guarded - the pin
# ending flush with the outer face of the arm, so that the washer presses the
# inner ring - is now two things, both measured on pivot_washer.step: the face
# of the washer is at the outer face of the arm, and the bushing reaches the
# floor of the spot face in the collar, which is where the screw closes the
# stack instead of on the bearings.
_pivot_washer = cq.importers.importStep(OUT + "pivot_washer.step").val()
_r_pivot = D["R_pivot"]; _a_pivot = math.radians(D["Ang_pivot"])
_pxp, _pyp = _r_pivot*math.cos(_a_pivot), _r_pivot*math.sin(_a_pivot)
_r_bush = (D["D_clear_screw_pivot"]/2 + D["D_pivot_arm"]/2)/2
_r_washer = (D["D_pivot_arm"]/2 + D["D_washer_pivot"]/2)/2


def _top_of(r, a, b):
    """Where material ends going up, at radius r from the pivot axis."""
    for _ in range(24):
        _m = (a + b)/2
        if _pivot_washer.intersect(cq.Solid.makeSphere(0.06, cq.Vector(_pxp + r, _pyp, _m))).Volume() > 1e-12:
            a = _m
        else:
            b = _m
    return (a + b)/2


_washer_face = _top_of(_r_washer, D["Z_bottom_arm"] - 2.0, D["Z_bottom_arm"] + 2.0)
_bushing_top = _top_of(_r_bush, D["Z_top_arm"] - 2.0, D["Z_top_arm"] + D["Th_flange_bearing"] + 2.0)
_z_spotface = D["Z_top_arm"] + D["Th_flange_bearing"]
T("pivot: the washer sits at the arm face, the bushing at the collar",
  abs(_washer_face - D["Z_bottom_arm"]) < 0.1 and abs(_bushing_top - _z_spotface) < 0.1,
  "washer at z %.2f (arm %.2f), bushing up to %.2f (spot face %.2f)"
  % (_washer_face, D["Z_bottom_arm"], _bushing_top, _z_spotface))
b=bb("box.step")
T("box: outer wall at R_out_box", abs(b.xmax-D["R_out_box"])<0.05, "%.2f"%b.xmax)
T("box: covers the motor in height", b.zmin <= -(D["Z_face_motor"]+D["L_motor"]+2), "zmin %.1f"%b.zmin)
b=bb("clutch_tyre.step")
T("tread centred on the disc mid-plane",
  abs((b.zmin+b.zmax)/2 - D["Z_plane_mid_disc"])<0.02, "%.2f"%((b.zmin+b.zmax)/2))
T("tread reaches the disc rim", abs(b.xmin-D["R_disc"])<0.35, "xmin %.2f"%b.xmin)

# 3bis) does the spring fit?
# The flank the spring rests on is not a number to be trusted: it is looked
# for on the solid, probing it with a small ball along the spring axis until it
# leaves the material. It is the check that was missing when
# R_rest_spring_arm said 96.22 while the material of the arm reached 106.2 and
# the spring had nowhere to go. It is probed half a millimetre below the face
# on the chamber side, not at the height of the axis: on the axis it would meet
# the centring pin instead of the flank. The pin is Ø6.4 centred on the
# mid-plane of the plate, so it leaves just under a millimetre free below each
# face, and the probe fits in there. Nor can it be probed from the side
# averaging two points: the flank is no longer a single ramp since the full
# width reaches past the spring attachment, and the average of two points
# straddling the edge would give a radius that does not exist on the part.
_Lb = D["L_arm"]
_ux, _uy = (D["Cd_motor"]-D["R_disc"])/_Lb, -D["Off_pivot"]/_Lb
_nx, _ny = -_uy, _ux
_Qx, _Qy = D["R_disc"]+_ux*D["Att_spring"], D["Off_pivot"]+_uy*D["Att_spring"]
_arm_body = cq.importers.importStep(OUT+"arm.step").val()

# --- the travel of the arm, and its swept envelope --------------------------
# Here there were four angles written by hand, `(-3, -1.5, 1.5, 3)`, repeated
# in two places. They derived from nothing, and the trouble was not the
# approximation: it was that the other things were checked AGAINST this sweep
# while the sweep was checked against nobody. Measuring the real part, at -1.5
# degrees the arm already touches the collar - and at -3, the ones written
# here, it sits inside it by ninety cubic millimetres. Now the travel is a
# design datum: it derives from how much TPU is to be squeezed, how much wear
# to follow and how much margin to leave, and the sweep follows it.
_TRAVEL_DOWN, _TRAVEL_UP = CB.limits(D)
_PIVOT_AXIS = ((D["R_disc"], D["Off_pivot"], 0), (D["R_disc"], D["Off_pivot"], 1))


def _swept(solid, samples=9):
    """The solid rotated over the whole travel and fused: its true envelope."""
    fused = solid
    for _k in range(samples):
        _g = _TRAVEL_DOWN + (_TRAVEL_UP-_TRAVEL_DOWN)*_k/(samples-1)
        fused = fused.fuse(solid.rotate(_PIVOT_AXIS[0], _PIVOT_AXIS[1], _g))
    return fused


_Z0B, _THB = D["Z_bottom_arm"], D["Th_arm"]

def _full(s):
    p = cq.Vector(_Qx+_nx*s, _Qy+_ny*s, _Z0B+_THB-0.5)
    return _arm_body.intersect(cq.Solid.makeSphere(0.25, p)).Volume() > 1e-9

_lo, _hi = 5.0, 40.0
for _ in range(22):
    _mid = (_lo+_hi)/2
    if _full(_mid): _lo = _mid
    else: _hi = _mid
_r = math.hypot(_Qx+_nx*_lo, _Qy+_ny*_lo)
T("spring: the arm ends where R_rest_spring_arm says",
  abs(_r - D["R_rest_spring_arm"]) < 0.5, "flank measured at r %.2f" % _r)
_gap = D["R_seat_spring_box"] - _r
T("spring: gap between arm and seat = L_spring_fitted",
  abs(_gap - D["L_spring_fitted"]) < 0.5, "gap %.2f, spring %.2f" % (_gap, D["L_spring_fitted"]))

# 3bis-bis) the spring rests square, not on an edge
# The flank of the arm was the ramp of the wedge, inclined by 15 degrees to the
# spring axis: the spring pressed on it with an edge, and of the 22.3 N six
# pushed sideways, making it slide along the flank. Only the pin held it. The
# flank is measured at the two ends of the outer diameter of the spring, not at
# the centre: at the centre a ramp and a plane give the same reading, and it is
# precisely the difference between the two ends that matters here.
# The outer diameter of the spring was written by hand in here. Now it is a
# dimension, D_spring_out, because it decides more than this check: it also
# decides how far the flank must stay straight, that is L_nose_arm. Two copies
# of the same number are two numbers that sooner or later drift apart.
_D_SPRING = D["D_spring_out"]
def _flank_at(off):
    _ax, _ay = _Qx+_ux*off, _Qy+_uy*off
    _a, _b = 5.0, 40.0
    for _ in range(26):
        _m = (_a+_b)/2
        _p = cq.Vector(_ax+_nx*_m, _ay+_ny*_m, _Z0B+_THB-0.5)
        if _arm_body.intersect(cq.Solid.makeSphere(0.15, _p)).Volume() > 1e-9: _a = _m
        else: _b = _m
    return _a
_drop = _flank_at(_D_SPRING/2) - _flank_at(-_D_SPRING/2)
_incl = math.degrees(math.atan2(abs(_drop), _D_SPRING))
T("spring: rests square on the flank of the arm", _incl < 2.0,
  "flank inclined by %.1f degrees under the seat (step %.2f mm)" % (_incl, _drop))

# 3bis-ter) the cup does its job
# Before, the preload grub screw pushed with its Ø4 tip directly on the last
# coil - a one-millimetre wire - and turning it rubbed it, that is it twisted
# it while the preload was being adjusted. Now the cup sits in between. For it
# to be of any use it must do three things, and all three are measured: slide
# in the pocket without cocking, have travel on either side of the nominal
# position, and hold the spring in line with the spigot without hitting the
# pin of the arm.
_cup = cq.importers.importStep(OUT + "spring_cup.step").val()
_box_solid = cq.importers.importStep(OUT + out_subdir("box") + "box.step").val()
_ax = cq.Vector(_nx, _ny, 0)
# The spring axis is READ FROM THE MODEL, not assumed on the mid-plane of the
# arm: it is Z_axis_spring, below the arm, low enough for the
# iron to pass under the collar flange. Assumed on the mid-plane, every probe
# of cup, pocket and insert went looking six millimetres too high.
from parameters import spring_axis as _spring_axis0
_zm = _spring_axis0()[4]

def _s_at_radius(r):
    _a, _b = 0.0, 200.0
    for _ in range(60):
        _m = (_a+_b)/2
        if math.hypot(_Qx+_nx*_m, _Qy+_ny*_m) < r: _a = _m
        else: _b = _m
    return (_a+_b)/2

_S0sc = _s_at_radius(D["R_seat_spring_box"])

# The play is MEASURED on the two parts, not asked of the parameter. Looking
# whether they interpenetrate at nominal is no use: at zero play the two
# cylinders share a surface and no volume, so the interpenetration is zero and
# the check passes on the defect. Nor is it any use to move it by half the play
# and see whether it touches: if the displacement is taken from the parameter,
# the check moves together with the defect and always touches. Here the two
# diameters are read from the solids - the cup from its envelope, the pocket by
# probing it vertically on the axis - and the difference is looked at.
_d_cup = _cup.BoundingBox().zlen            # the axis is horizontal: z is a diameter
_ps = _Qx+_nx*(_S0sc+D["Th_cup_spring"]/2), _Qy+_ny*(_S0sc+D["Th_cup_spring"]/2)

def _box_void(dz):
    _p = cq.Vector(_ps[0], _ps[1], _zm + dz)
    return _box_solid.intersect(cq.Solid.makeSphere(0.02, _p)).Volume() <= 1e-12

_a, _b = 0.0, 12.0                            # from the centre of the pocket upwards
for _ in range(24):
    _m = (_a+_b)/2
    if _box_void(_m): _a = _m
    else: _b = _m
_d_pocket = 2*_a
_play = _d_pocket - _d_cup
T("cup: slides in the pocket with a play that is measured",
  0.2 <= _play <= 0.8,
  "pocket %.2f, cup %.2f -> play %.2f on the diameter" % (_d_pocket, _d_cup, _play))

# The travel is measured on the pocket, not asked of Travel_preload: moving the
# cup by what the parameter says, the check moves together with the defect and
# at zero travel does not move at all - it passed, and in fact it did pass.
# Here the solid is probed. The mouth of the pocket is where the wall acting
# as a guide ends, so material is looked for just OUTSIDE the diameter of the
# pocket; the floor is where material reappears in front of the cup, and it is
# looked for half-way between the grub screw hole and the wall, because on the
# axis the grub screw hole is empty all the way down.
_dz_guide = D["D_seat_spring_box"]/2 + 0.4
_dz_floor = (D["D_grub_spring"]/2 + D["D_seat_spring_box"]/2)/2

def _mat(s, dz):
    _p = cq.Vector(_Qx+_nx*s, _Qy+_ny*s, _zm + dz)
    return _box_solid.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() > 1e-12

_mouth = _S0sc
while _mouth > _S0sc - 12.0 and _mat(_mouth, _dz_guide):
    _mouth -= 0.1
_floor = _S0sc + D["Th_cup_spring"]
while _floor < _S0sc + 20.0 and not _mat(_floor, _dz_floor):
    _floor += 0.1
_travel_in = _S0sc - _mouth
_travel_out = _floor - (_S0sc + D["Th_cup_spring"])
T("cup: has travel on both sides",
  _travel_in >= 1.0 and 1.0 <= _travel_out <= 6.0,
  "towards the arm %.1f mm (guided up to there), towards the grub screw %.1f mm (then the floor)"
  % (_travel_in, _travel_out))

# the two spigots face each other inside the same spring: added up they must
# stay shorter than the fitted spring, otherwise they touch and the preload
# goes out of the window.
_spigots = 2*D["Proj_spigot_spring"]
T("spring: the two spigots do not meet", _spigots < D["L_spring_fitted"] - 2.0,
  "%.1f + %.1f = %.1f inside a spring of %.1f"
  % (D["Proj_spigot_spring"], D["Proj_spigot_spring"], _spigots, D["L_spring_fitted"]))

# 3bis-quater) the seat of the grub screw's heat-set insert
# The preload grub screw does not screw into the ASA: it screws into an M4
# heat-set insert set at the entrance of the boss. The one of the reference
# build is 6.3 x 8.1, measured with the calliper - bigger than the most common M4 - and from those
# two measurements derive hole, lead-in and length of the boss. Here the SOLID
# is looked at: the numbers that follow all come from probing the box, not from
# re-reading the parameters that generated it. The probe ball is Ø0.16, so every
# diameter read is about a tenth and a half narrower than the truth and every
# depth as much shorter: the thresholds take it into account.
_PROBE = 0.08
_s_end = _S0sc - D["Travel_preload"] + max(
    _s_at_radius(D["R_out_box"]) - (_S0sc - D["Travel_preload"]) + 1.0,
    (2*D["Travel_preload"] + D["Th_cup_spring"])
    + D["Dp_seat_insert_M4"] + D["Th_retain_insert_M4"])

def _mat_b(s, dz):
    _p = cq.Vector(_Qx+_nx*s, _Qy+_ny*s, _zm + dz)
    return _box_solid.intersect(cq.Solid.makeSphere(_PROBE, _p)).Volume() > 1e-12

def _boundary(f, a, b):
    """Where the answer changes between a and b, by bisection: twenty probes
    instead of three hundred. The fixed-step scans here cost forty seconds of
    build, and a boolean operation for every two hundredths of a millimetre."""
    for _ in range(20):
        _m = (a+b)/2
        if f(_m): b = _m
        else: a = _m
    return (a+b)/2

def _diam_at(s):
    # on the axis the seat is empty, at r 7 one is inside the wall of the boss
    return 2*(_boundary(lambda r: _mat_b(s, r), 0.0, 7.0) + _PROBE)

# THE INSERT IS SET FROM INSIDE, so it is probed from inside: what sits at the
# outer edge of the boss is no longer the mouth of the seat, it is the WALL that
# retains the insert, drilled only for the passage of the grub screw. The two
# checks of before went off as soon as the direction changed - seat depth -0.00
# and mouth 4.10 instead of 5.95 - and it was the right verdict on the wrong
# geometry: they described the old assembly.
_dz_between = (D["D_grub_spring"]/2 + D["D_hole_insert_M4"]/2)/2

# 1) the retaining wall: from the outer edge inwards, how much material there
# is at the radius between the grub screw and the seat. There the grub screw
# passes (Ø4.1 hole) and the insert does not (Ø6.3): it is exactly the ring the
# insert bottoms against.
_th_wall, _q = 0.0, 0.0
while _q < 6.0 and _mat_b(_s_end - _q, _dz_between):
    _th_wall = _q
    _q += 0.05
# The minimum is absolute and does not derive from Th_retain_insert_M4: taken
# from there, zeroing the parameter would zero the test as well.
T("preload: the wall retains the insert", _th_wall + _PROBE >= 1.0,
  "%.2f mm of ASA between the insert and the outside, minimum 1.00" % (_th_wall + _PROBE))

# 2) and it must be drilled, otherwise the grub screw does not go in
T("preload: the wall is drilled for the grub screw",
  not _mat_b(_s_end - 0.15, 0.0), "on the axis there is material at the outer edge")

# 3) the seat starts behind the wall and contains the whole insert: at the
# depth of the last millimetre of the insert the hole must still be the one of
# the seat, not the one of the cup's pocket
_s_insert_mouth = _s_end - _th_wall - 0.2
_d_seat = _diam_at(_s_insert_mouth - D["L_insert_M4"]/2)
_d_bottom = _diam_at(_s_insert_mouth - D["L_insert_M4"] + 0.2)
T("preload: the seat contains the whole insert",
  _d_bottom < D["D_seat_spring_box"] - 1.0,
  "at the last millimetre the hole is %.2f: it is already the pocket (%.2f)"
  % (_d_bottom, D["D_seat_spring_box"]))

T("grub screw insert: the hole is narrower than it and wider than the grub screw",
  D["D_grub_spring"] + 0.2 < _d_seat < D["D_out_insert_M4"],
  "hole %.2f between grub screw %.2f and insert %.2f"
  % (_d_seat, D["D_grub_spring"], D["D_out_insert_M4"]))

# 4) the lead-in is on the side the insert COMES FROM, that is inside
_s_seat_bottom = _s_end - _th_wall - D["Dp_seat_insert_M4"]
_d_lead_in = _diam_at(_s_seat_bottom + 0.15)
T("grub screw insert: the mouth has the lead-in, and it faces inwards",
  _d_lead_in > _d_seat + 0.4,
  "inner mouth %.2f against seat %.2f" % (_d_lead_in, _d_seat))

# the wall left around the melted-in insert: from the side of the seat to the
# skin of the boss, measured where the insert sits, not counted by hand on the Ø15.
_s_mid = _s_insert_mouth - D["L_insert_M4"]/2
_r_outer = _boundary(lambda r: not _mat_b(_s_mid, r),
                    D["D_hole_insert_M4"]/2 + 0.3, 20.0)
_wall = _r_outer - D["D_out_insert_M4"]/2
T("grub screw insert: it keeps a wall around it", _wall >= 2.5,
  "%.2f mm of ASA between insert and skin of the boss" % _wall)

# and past the seat the grub screw must pass freely up to the cup: it is a
# passage, not a second thread.
_obstructed = None
_s = _s_seat_bottom - 0.3
while _s > _S0sc + D["Travel_preload"] + D["Th_cup_spring"] + 0.3:
    if _mat_b(_s, D["D_grub_spring"]/2 - 0.3): _obstructed = _s; break
    _s -= 0.5
T("grub screw insert: past the seat the grub screw runs on freely", _obstructed is None,
  "" if _obstructed is None else "obstructed at s %.2f" % _obstructed)

# 3ter) the centring pin grows entirely from material
# Seen by eye first: a cylinder stuck to the flank, that might come off. It
# was two things together. The cylinder started
# exactly on the flank, so it shared with the plate only its base face -
# measured, zero mm3 in common: not a weld but a butt joint. And its axis was at
# -6, two millimetres below the mid-plane of the plate, so the Ø6.4 round went
# down to -9.2 while the arm ends at -8: an eighth of the root grew in the air,
# which printed means a cantilevered cylinder hanging from nothing. Here the
# visible consequence on the solid is measured - where the protruding part is
# and how high - because the interpenetration, once fused, can no longer be
# seen: that one is checked by solids_arm.py while it builds.
# The window is narrow on purpose: four millimetres either side of the spring
# axis. Ten wide, it caught the flank of the plate two centimetres further on,
# where it protrudes most, and the measurement said the pin reached z 0 - that
# is, it measured the plate, not the pin.
def _ang(s, t):
    return (_Qx+_nx*s+_ux*t, _Qy+_ny*s+_uy*t)
_outside = (cq.Workplane("XY").workplane(offset=_Z0B-20)
          .polyline([_ang(_lo+1.0, -4.0), _ang(_lo+10.0, -4.0),
                     _ang(_lo+10.0, 4.0), _ang(_lo+1.0, 4.0)]).close().extrude(40).val())
_protrusion = _arm_body.intersect(_outside)
_bs = _protrusion.BoundingBox()
# The spigot sits on the TAB under the arm, not on the
# plate: the face it stands on runs from the bottom of the tab to the top of
# the arm, and its axis is the spring axis, no longer the mid-plane.
_z_tab_bottom = min(_Z0B, _zm - D["H_tab_spring_arm"])
T("spring pin: the root sits entirely on the flank of the plate",
  _bs.zmin > _z_tab_bottom-0.01 and _bs.zmax < _Z0B+_THB+0.01,
  "pin z %.2f..%.2f, face %.1f..%.1f" % (_bs.zmin, _bs.zmax, _z_tab_bottom, _Z0B+_THB))
T("spring pin: centred on the spring axis",
  abs((_bs.zmin+_bs.zmax)/2 - _zm) < 0.05,
  "axis at %.2f, spring at %.2f" % ((_bs.zmin+_bs.zmax)/2, _zm))

# 3quater-0) the arm must be able to make its whole travel
# This is the check that was missing, and it is the most important of its
# neighbours: until now the audit checked the other things AGAINST the travel of
# the arm, and the travel against nobody. So the arm could touch the collar at
# -1.5 degrees - before even finishing its useful travel - without anything
# going off, because the defect was in the measuring stick itself.
#
# The part is not looked at at rest: at rest the arm is modelled in one
# position only and says nothing. It is rotated, one sample after the other,
# and one looks at whom it meets. The collar must NEVER meet it: on that side
# the arm must be free, because that is where the spring takes it when the TPU
# wears, and an arm that hits the collar is an arm that stops pushing.
_collar_travel = cq.importers.importStep(OUT + out_subdir("collar") + "collar.step").val()
# AND IT IS NOT ENOUGH THAT THEY DO NOT INTERPENETRATE: they must also not RUB.
# Two coplanar faces have zero interpenetration, so the check below, alone,
# passes even when the arm rests on the collar over a square centimetre - and
# that is exactly what happened once, over 159 mm2, and it showed only when
# the arm was moved with the part screwed on. The way to ask the right thing is to
# RAISE the arm by the declared clearance and demand that it still does not
# touch: that way a distance is measured and not an overlap. It is raised by
# the SMALLER of the two declared clearances, because at the pivot hub the two
# faces are at Setback_face_hub and beyond at Free_above_arm.
_arm_clearance = min(D["Free_above_arm"], D["Setback_face_hub"])
_hits, _rubs = [], []
for _k in range(13):
    _g = _TRAVEL_DOWN + (_TRAVEL_UP-_TRAVEL_DOWN)*_k/12.0
    _brg = _arm_body.rotate(_PIVOT_AXIS[0], _PIVOT_AXIS[1], _g)
    _vc = _brg.intersect(_collar_travel).Volume()
    if _vc > 0.01:
        _hits.append("%+.2f degrees: %.1f mm3 in the collar" % (_g, _vc))
    _vs = _brg.moved(cq.Location(cq.Vector(0, 0, _arm_clearance))).intersect(_collar_travel).Volume()
    if _vs > 0.01:
        _rubs.append("%+.2f degrees: %.0f mm2" % (_g, _vs/_arm_clearance))
T("arm travel: over the whole travel the arm does not touch the collar",
  not _hits, "; ".join(_hits[:4]))
T("arm travel: above the arm the collar leaves the clearance, does not rest on it",
  not _rubs, "raised by %.2f it still touches: %s" % (_arm_clearance, "; ".join(_rubs[:4])))


# And the recess in the collar must be the one needed, not just any: if
# somebody put the old dimensions back by hand, the check above would go off -
# but this one also says by HOW MUCH, which is the useful information to fix it.
_pa0, _pa1, _pri = CB.passage(D)
T("arm travel: the collar recess contains what the arm sweeps",
  True,
  "needs angles %+.1f..%+.1f and inner radius %.2f (travel %+.2f..%+.2f degrees)"
  % (_pa0, _pa1, _pri, _TRAVEL_DOWN, _TRAVEL_UP))

# On the spring side, instead, an end stop is needed, and today there is NONE:
# the arm is free until the clutch hits the box. Here it is measured where it
# hits, so that the day the end stop is drawn one knows how much margin is left
# to it.
_clutch_c = cq.importers.importStep(OUT + "clutch_assembly.step").val()
_box_c = cq.importers.importStep(OUT + out_subdir("box") + "box.step").val()
_where_hits = None
for _k in range(41):
    _g = _TRAVEL_UP + 0.25*_k
    if _clutch_c.rotate(_PIVOT_AXIS[0], _PIVOT_AXIS[1], _g).intersect(_box_c).Volume() > 0.01:
        _where_hits = _g
        break
T("arm travel: past the end of travel there is room before it hits",
  _where_hits is None or _where_hits > _TRAVEL_UP + 0.5,
  "the clutch touches the box at %s, the end of travel is at %+.2f"
  % ("never within +10 degrees" if _where_hits is None else "%+.2f degrees" % _where_hits,
     _TRAVEL_UP))

# 3quater-bis) between the hub and the plate there is no longer a step
# The pivot hub is r 10.5 and the plate is 17.6 wide: the two met edge-on,
# with a 7.1 mm step on both flanks. On the outer flank it showed completely;
# on the inner one the cut of R_rim_inner left its tip, and the tip is what was
# seen protruding in the plan view. Now an ogive of two tangent arcs rises there.
#
# The radius of the ogive is not measured, that would be re-reading the
# parameter: one walks along the arm and looks at how much the flank moves from
# one station to the next. An ogive moves a little at a time; a step jumps.
# Both flanks are looked at, and one stops before the spring pin, which
# protrudes on its own and would jump for a legitimate reason.
_r_bearing_seat = D["D_seat_bearings_printed"]/2

def _arm_flank(s, side):
    """How far from the axis the flank is, at station s.

    The bisection wants an inner end that is SOLID, and on the axis of the arm
    it is not: inside the hub there is the bearing seat, which is a through
    hole. Starting from zero the search fell into the central void at some
    stations and found the flank at others, and the two readings differed by
    ten millimetres: an invented jump, on a sound part. So it starts from just
    outside the seat, and if there is no material even there the measurement
    declares itself invalid instead of returning any number at all.
    """
    _bx, _by = D["R_disc"]+_ux*s, D["Off_pivot"]+_uy*s
    def _full_m(_m):
        _p = cq.Vector(_bx+side*_nx*_m, _by+side*_ny*_m, _Z0B+_THB/2)
        return _arm_body.intersect(cq.Solid.makeSphere(0.15, _p)).Volume() > 1e-9
    _a = math.sqrt(max(0.0, _r_bearing_seat*_r_bearing_seat - s*s)) + 0.4
    if not _full_m(_a):
        return float("nan")
    _b = 40.0
    for _ in range(22):
        _m = (_a+_b)/2
        if _full_m(_m): _a = _m
        else: _b = _m
    return _a

# The scan MUST start inside the hub, not from the pivot forwards: the step
# straddles zero - the hub is at x<0, the plate starts at x=0 - and between two
# stations that are both positive no jump is seen. Starting at zero this check
# passed even with the ogive removed altogether: tried, it said 0.00 mm of jump
# with the 7.1 step in its place.
# But it cannot start from the edge of the hub either: there the circle has a
# vertical tangent and jumps on its own, two and a half millimetres per
# station, and the check would fail on a sound curve. At half the radius the
# slope of the hub is 0.58, gentler than the ogive itself: from there on every
# jump is a defect.
_STEP_OGIVE = 0.25
_S0_OGIVE = -D["D_hub_pivot"]/4.0
_n_ogive = int((D["L_nose_arm"] - _S0_OGIVE)/_STEP_OGIVE) + 1
_jumps = {}
for _flank_sign, _name in ((1, "outer"), (-1, "inner")):
    _prev, _worst, _where = None, 0.0, 0.0
    for _i in range(_n_ogive+1):
        _s = _S0_OGIVE + _i*_STEP_OGIVE
        _f = _arm_flank(_s, _flank_sign)
        if _prev is not None and abs(_f-_prev) > _worst:
            _worst, _where = abs(_f-_prev), _s
        _prev = _f
    _jumps[_name] = (_worst, _where)
# The threshold is not random: the steepest ogive this geometry produces has a
# slope of 0.72, that is less than two tenths every quarter of a millimetre.
# Half a millimetre leaves the measurement room to breathe and catches the
# step, which is worth 7.1.
for _name, (_worst, _where) in _jumps.items():
    T("arm: the %s flank rises without steps from the hub to the plate" % _name,
      _worst < 0.5,
      "largest jump %.2f mm between two stations 0.25 apart, at station %.2f" % (_worst, _where))

# 3quater-ter) the two exposed edges of the plate are filleted
# They are the ones that stick out on the assembled part and that one bumps
# into. It is probed along the inward diagonal: near the sharp edge there must
# be no material, a little further in there must. With the sharp edge the first
# reading comes back solid, and that is how the check notices it.
_Rsp = D["R_edges_plate_motor"]
_arc_setback = _Rsp*(math.sqrt(2.0)-1.0)        # how far the arc sets back on the diagonal
for _sx, _name in ((-1, "towards the pivot"), (1, "away from the pivot")):
    _cx = D["Cd_motor"] + _sx*D["Side_motor"]/2
    _cy = -D["Side_motor"]/2
    _dx, _dy = -_sx/math.sqrt(2.0), 1/math.sqrt(2.0)   # diagonal pointing inwards
    def _full_at(_d):
        _p = cq.Vector(_cx+_dx*_d, _cy+_dy*_d, -D["Z_face_motor"]/2)
        return _arm_body.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() > 1e-9
    _empty_near = not _full_at(_arc_setback*0.5)
    _full_after = _full_at(_arc_setback + 1.0)
    T("arm: plate edge %s filleted" % _name,
      _empty_near and _full_after,
      "at %.2f from the tip %s, at %.2f %s"
      % (_arc_setback*0.5, "empty" if _empty_near else "SOLID",
         _arc_setback+1.0, "solid" if _full_after else "EMPTY"))

# 3quater-quater) the fillet has not eaten the motor holes
# The radius of the fillet is limited by the M3 holes, not by taste: the point
# of a hole nearest the edge is 3.47 mm from it along the diagonal. Here one
# parameter is not compared with another - one looks at whether the material
# around the hole is still all there.
_rf = D["D_holes_M3_printed"]/2
_hh = D["Cd_holes_motor"]/2
_uncovered = []
for _sx in (-1, 1):
    _fx, _fy = D["Cd_motor"]+_sx*_hh, -_hh
    for _k in range(24):
        _a = 2*math.pi*_k/24
        _p = cq.Vector(_fx+(_rf+0.6)*math.cos(_a), _fy+(_rf+0.6)*math.sin(_a), -D["Z_face_motor"]/2)
        if _arm_body.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() < 1e-9:
            _uncovered.append((round(_p.x,2), round(_p.y,2)))
T("arm: the M3 holes near the edges still have material around them",
  not _uncovered, "%d points uncovered, for example %s" % (len(_uncovered), _uncovered[:3]))

# 3quinquies) the drawing of the arm is the arm
# The two plan drawings rebuilt the outline on their own, and the solid on its
# own: three copies. As long as the arm was a wedge they looked alike; with the
# straight plate the drawings showed a part that no longer exists. Now the
# outline is one only, and here it is checked that it really is the one of the
# solid: the section is sampled at half thickness and there must be no
# material sticking out of the drawn outline. Half a millimetre of allowance
# because the outline is a polyline and cuts the arcs along the chord.
_outline_pts = arm_outline(D)
_section = _arm_body.intersect(cq.Workplane("XY").workplane(offset=_Z0B+_THB/2-0.05)
                          .rect(400, 400).extrude(0.1).val())

def _inside_outline(x, y):
    _c = False
    for _i in range(len(_outline_pts)):
        _x0, _y0 = _outline_pts[_i]; _x1, _y1 = _outline_pts[(_i+1) % len(_outline_pts)]
        if (_y0 > y) != (_y1 > y) and x < _x0 + (y-_y0)*(_x1-_x0)/(_y1-_y0):
            _c = not _c
    return _c

def _far_from_edge(x, y):
    _d = 1e9
    for _i in range(len(_outline_pts)):
        _x0, _y0 = _outline_pts[_i]; _x1, _y1 = _outline_pts[(_i+1) % len(_outline_pts)]
        _dx, _dy = _x1-_x0, _y1-_y0; _L2 = _dx*_dx + _dy*_dy
        _t = 0.0 if _L2 < 1e-12 else max(0.0, min(1.0, ((x-_x0)*_dx + (y-_y0)*_dy)/_L2))
        _d = min(_d, math.hypot(x-_x0-_t*_dx, y-_y0-_t*_dy))
    return _d > 0.5

# The EDGE of the section is sampled, not a grid over the whole area: the edge
# is where the drawing can lie, and it is a few hundred points instead of seven
# thousand boolean operations. The edges of the holes fall inside the outline
# and do no harm.
_escaped = []
for _e in _section.Edges():
    _n = max(3, int(_e.Length()/0.7) + 1)
    for _k in range(_n+1):
        _p = _e.positionAt(_k/_n)
        if not _inside_outline(_p.x, _p.y) and _far_from_edge(_p.x, _p.y):
            _escaped.append((_p.x, _p.y))
T("arm: the plan drawing is the part", len(_escaped) == 0,
  "%d points of the part's edge outside the drawn outline%s"
  % (len(_escaped),
     "" if not _escaped else ", the first at (%.1f, %.1f)" % _escaped[0]))

# 3quater) the arm is a plate, and that is all
# Nothing must protrude from its two faces: below is the face the motor rests
# on, above the one towards the chamber. Here the spring platter protruded, a
# Ø14 cylinder twelve high centred on the spring attachment, which went four
# millimetres below the motor face - and did not touch the spring, which stops
# seventeen millimetres earlier, against the flank.
# One thing protrudes ON PURPOSE above the face towards the
# chamber: the motor plate, which grows by Th_more_plate_motor to gain
# thickness without bringing the motor down. So the check no longer asks
# "nothing above z 0" - it asks two more precise things, and together they say
# the same thing as before: nothing above the TOP of the motor plate, and above
# z 0 nothing outside the motor square.
_down = cq.Workplane("XY").workplane(offset=_Z0B-40).rect(400, 400).extrude(40).val()
_up  = (cq.Workplane("XY").workplane(offset=-D["Z_face_motor"]+D["Th_plate_motor"])
        .rect(400, 400).extrude(40).val())
# The body of the arm itself reaches Z_top_arm: the limit
# is its top face, no longer z 0.
_outside_square = (cq.Workplane("XY").workplane(offset=D["Z_top_arm"]).rect(400, 400).extrude(40)
                 .cut(cq.Workplane("XY").workplane(offset=-1.0)
                      .center(D["Cd_motor"], 0.0)
                      .rect(D["Side_motor"]+0.4, D["Side_motor"]+0.4).extrude(42)).val())
# ...and BELOW the arm one thing hangs on purpose: the tab
# the preload spring rests on, now that the spring axis (Z_axis_spring) is
# below the arm. The check asks two things: that the tab is THERE - material
# below the arm at the spring seat - and that nothing ELSE hangs below.
from parameters import spring_axis as _am, s_spring_axis as _sam
_Qxl, _Qyl, _nxl, _nyl, _zml = _am()
_sal = _sam(D["R_rest_spring_arm"])
_ul = (-_nyl, _nxl)
_wl = D["D_spring_out"]/2 + 1.5
# the zone reaches past the tab by its chamfer (a 45 degree wedge joining the
# tab to the arm on the side away from the spring)
_s0l = _sal - D["Th_tab_spring_arm"] - D["L_chamfer_tab_spring_arm"] - 0.5
_s1l = _sal + D["Proj_spigot_spring"] + 0.5
_pts_l = [(_Qxl + _nxl*ss + _ul[0]*ww, _Qyl + _nyl*ss + _ul[1]*ww)
          for ss, ww in ((_s0l, -_wl), (_s1l, -_wl), (_s1l, _wl), (_s0l, _wl))]
_tab_zone = (cq.Workplane("XY").workplane(offset=_Z0B - 40).polyline(_pts_l).close()
                   .extrude(40).val())
_below = _arm_body.intersect(_down)
_vlin = _below.intersect(_tab_zone).Volume()
T("arm: below the arm there is the spring tab",
  _vlin > 0.5*D["Th_tab_spring_arm"]*2*(D["D_spring_out"]/2 + 1.0)*(_Z0B - (_zml - D["H_tab_spring_arm"]))
  if _zml - D["H_tab_spring_arm"] < _Z0B else True,
  "%.1f mm3 in the tab zone" % _vlin)
_vg, _vs = _below.cut(_tab_zone).Volume(), _arm_body.intersect(_up).Volume()
_vq = _arm_body.intersect(_outside_square).Volume()
T("arm: above the chamber face only the motor plate protrudes",
  _vq < 1.0, "%.1f mm3 outside the motor square" % _vq)
T("arm: nothing protrudes from the faces of the plate", _vg < 1.0 and _vs < 1.0,
  "below %.1f mm3, above %.1f mm3" % (_vg, _vs))

# 4) interpenetrations
parts={n:cq.importers.importStep(OUT + out_subdir(n) + n + ".step") for n in
       ("filter_wheel_body","filter_disc","collar","arm",
        "clutch_hub","clutch_tyre","box","board_panel",
        "sensor_bracket","spring_cup","pivot_washer",
        "front_gasket","rear_gasket","sensor_cable")}
# The gaskets DO interpenetrate the body, and rightly so: at rest the lip
# protrudes from the groove, and that volume is exactly the squeeze. The pair
# is not exempted silently - one checks that the volume is the expected one,
# neither zero (a gasket that does not touch) nor too much (a gasket that does
# not close): see the dedicated check further down.
EXPECTED_PAIRS = {("filter_wheel_body","front_gasket"),
          ("filter_wheel_body","rear_gasket"),
          # Box and collar interpenetrate ON PURPOSE: they are not two parts
          # placed side by side, they are the two regions of a single printed
          # part, and the inner face of the shell goes into the collar by
          # Weld_box_collar so that the fusion is one solid and not a compound
          # of two. It is not just put here and left, though: right below
          # there is a check that verifies that this interpenetration is
          # EXACTLY the weld and not something that slipped through.
          ("box","collar")}
bad=[]
for a,c in itertools.combinations(parts,2):
    if tuple(sorted((a,c))) in {tuple(sorted(p)) for p in EXPECTED_PAIRS}: continue
    try: v=parts[a].val().intersect(parts[c].val()).Volume()
    except Exception: v=0.0
    if v>1.0: bad.append((a,c,round(v)))
T("no interpenetration between the solids", not bad, str(bad))

# 3bis) THE WELD BETWEEN THE TWO REGIONS IS EXACTLY THE ONE WANTED.
# Putting ("box","collar") among the expected ones, and that is all, would
# mean no longer looking precisely where the part holds together: from there on
# any interpenetration - a boss breaking through, a wall going where it should
# not - would pass unnoticed. So it is measured.
#
# The threshold does not come from Weld_box_collar: deriving it from there would
# mean that zeroing the weld also zeroes the test, which is the trap written in
# CONTRIBUTING.md. Instead one checks that the interpenetration stays in a thin SKIN
# around the inner face of the shell - one millimetre - and that outside it
# there is none.
_bu = (cq.Workplane("XY").circle(D["R_out_collar"] + 1.0)
       .circle(D["R_out_collar"] - 1.0).extrude(300).val().translate((0, 0, -150)))
_weld = parts["box"].val().intersect(parts["collar"].val())
# ...and the column of the pivot, which runs into the roof on purpose: its
# top inside the roof slab is weld too, and is taken out
# with a cylinder round the pivot axis from the underside of the roof up.
_pxw, _pyw = D["R_disc"], D["Off_pivot"]
_pivot_column = cq.Solid.makeCylinder(D["D_hub_pivot"]/2 + 0.5, 20.0,
                                   cq.Vector(_pxw, _pyw, D["Z_shoulder_box"] - 0.5))
# ...and the TOP OF THE INNER WALL under the wheel: the wall runs
# from the floor up into the collar flange and goes Weld_box_collar into it,
# like the rest of the shell - on purpose. So the layer just under the
# flange, as thick as the weld, is weld too. Only that layer: a boss that
# pushed further into the flange would still come out.
_z_fl = -D["Th_flange_collar"]
_flange_layer = cq.Solid.makeCylinder(D["R_out_collar"], D["Weld_box_collar"] + 0.02,
                                   cq.Vector(0, 0, _z_fl - 0.01))
_outside_skin = _weld.cut(_bu).cut(_pivot_column).cut(_flange_layer).Volume()
T("the two regions weld only on the inner face of the shell",
  _outside_skin <= 1.0,
  "%.1f mm3 of interpenetration outside the skin (total weld %.0f mm3)"
  % (_outside_skin, _weld.Volume()))

# NOTE ON THE PROBE HEIGHTS. Many tests in here probe the solid at
# absolute heights. As long as the floor was the number -38 and the ceiling the
# number 16, those heights could be written by hand and nobody suffered for it.
# The day the two planes moved - the clutch turned upside down, the motor went
# up and the floor followed it - every probe written by hand started probing
# OUTSIDE the part, reading the void and going off through its own fault. Now
# they derive from Z_floor_box and Z_shoulder_box: a probe that moves with the
# part keeps looking at the same thing.

# 4bis) CAN THE BOX BE SLID ON? IT IS NO LONGER SLID ON.
# Here the box was brought back along its direction of entry, step by step,
# and at no step was it to meet the collar. It was the first trajectory check
# of the project, born from a defect found with the parts in hand.
#
# Now there is nothing left to slide on: box and collar are the
# same part. The check was not weakened, it became pointless - and the family
# it belonged to was not left uncovered: it is carried on by
# src/check_wheel_entry.py, which sweeps the Ø158 wheel along its entry
# trajectory, to which the single part must keep making way.

# 4ter) DOES THE PANEL GO IN WITHOUT FORCING?
#
# Measured on the solids and not on the parameters, because the parameter said
# the right thing: Cl_panel is 0.2 and on the solids the play was 0.199, that
# is exactly that. And yet the printed panel went in only with effort, and
# rightly so:
# two tenths per side, on a part eighty-five millimetres long and in ASA, are
# eaten by the shrinkage. The extra air was all added on the side of the BOX -
# the printed panel stays good - and it had to chase four different fits:
# outline, cut-out of the back, the ears of the screws and the USB slot. Every
# time one was widened the tight spot moved to the next, and that is why this
# check looks at the MINIMUM over the whole part and not at a chosen point.
#
# It is measured in a slice below the stop, where the panel does not rest: the
# minimum distance between the two whole parts would be zero, and rightly so -
# on the supports they touch.
#
# The threshold is a number chosen here, 0.30, and does NOT derive from
# Cl_panel_box: deriving it from there would mean that zeroing the play also
# zeroes the test, which is the trap this project has already fallen into five
# times.
_slice = cq.Workplane("XY").box(300, 300, 0.4).val().translate((70, 75, D["Z_floor_box"] + 0.6))
try:
    _pa = parts["board_panel"].val().intersect(_slice)
    _bo = parts["box"].val().intersect(_slice)
    _dd = BRepExtrema_DistShapeShape(_pa.wrapped, _bo.wrapped)
    _dd.Perform()
    _play_panel = _dd.Value()
except Exception:
    _play_panel = -1.0
# 4quater) DOES THE GX12 HOLE HAVE THE TWO FLATS?
#
# Found while screwing it on: the connector turned behind the ring nut. Its
# barrel has two anti-rotation flats, one per side, and the hole was a plain
# round - in the model the GX12 is a simplified cylinder, so those flats do not
# exist and no check could see them. Here the hole is probed ON THE SOLID, at
# half the thickness of the head, in two directions: between the flats and
# across. A hole that went back to round gives two equal numbers.
_tm_gx = (E.T_HEAD_IN + E.T_HEAD_OUT)/2.0
_pgx = E.xy(E.GX12_S, _tm_gx)
_uxg, _uyg = -E.V[1], E.V[0]
def _void_gx(dz, dl):
    _c = cq.Workplane("XY").box(0.12, 0.12, 0.12).val().translate(
        (_pgx[0] + _uxg*dl, _pgx[1] + _uyg*dl, E.GX12_Z + dz))
    try: return parts["box"].val().intersect(_c).Volume() < 1e-6
    except Exception: return True
def _gap_gx(f):
    _a = 0.0
    while _a < 9.0 and f(_a): _a += 0.02
    _b = 0.0
    while _b > -9.0 and f(_b): _b -= 0.02
    return _a - _b
_h_gx = _gap_gx(lambda t: _void_gx(t, 0.0))     # between the flats
_w_gx_meas = _gap_gx(lambda t: _void_gx(0.0, t))  # where it stays round
# The threshold does not derive from Cl_flats_gx12: zeroing that parameter the
# hole would stay flatted anyway, and a check that took its measuring stick
# from there would not see the return to the round hole, which is the real
# defect.
T("GX12: the hole has the anti-rotation flats", _w_gx_meas - _h_gx >= 0.05,
  "between the flats %.2f, across %.2f: difference %.2f"
  % (_h_gx, _w_gx_meas, _w_gx_meas - _h_gx))
T("GX12: the flats do not pinch the connector",
  _h_gx + 0.1 >= D["W_flats_gx12"],
  "hole %.2f, connector %.2f" % (_h_gx, D["W_flats_gx12"]))

T("the panel goes in without forcing", _play_panel >= 0.30,
  "minimum side play %.3f mm, minimum 0.30" % _play_panel)

# 5) does the magnet really go in?
# The hole in the ring is round in the drawing, but a part fused afterwards can
# plug it again without anybody noticing: it happened to the test feet, where
# the tab went a millimetre into the hole, right at the height of the magnet.
# Here one tries to put the magnet in and looks at whether it touches.
from drawings import hub_radius
def _magnet(cx, cy, cz):
    return (cq.Workplane("XY").workplane(offset=cz).center(cx, cy)
            .circle(D["D_magnet"]/2).extrude(D["Th_magnet"]).val())

_pd = cq.importers.importStep(OUT + "tools/gap_gauges.step").val()
_re = hub_radius()
_touching = []
# The centre of the ring is read from the MAGNET HOLE, looking for its
# cylindrical face in the part. Before, it was derived from the bounding box,
# which needed to know on which side the capacitor cut-out was: since the
# module can be turned round that is no longer information the outline
# contains, and a centre wrong by four millimetres declared a plugged hole
# free. The hole, instead, says where it is on its own. Nor is solids_attrezzi
# imported: that module works at import time and would rewrite the STEPs
# precisely while the audit is reading them.
def _magnet_hole_centre(solid):
    # on the feet the hole is a tenth wider than on the real bracket: the same
    # screw and the same magnet go in and out seven times
    _r_expected = (D["D_hole_magnet_printing"] + D["Cl_test_magnet"])/2
    for _f in solid.Faces():
        _ad = BRepAdaptor_Surface(_f.wrapped)
        if _ad.GetType() != GeomAbs_SurfaceType.GeomAbs_Cylinder:
            continue
        _cyl = _ad.Cylinder()
        if abs(_cyl.Radius() - _r_expected) < 0.02:
            _loc = _cyl.Location()
            return _loc.X(), _loc.Y()
    return None


for _s in _pd.Solids():
    _hole_centre = _magnet_hole_centre(_s)
    if _hole_centre is None:
        _touching.append(("magnet hole not found", 0))
        continue
    _cx, _cy = _hole_centre
    _v = _s.intersect(_magnet(_cx, _cy, 0.0)).Volume()
    if _v > 0.01:
        _touching.append((round(_cy), round(_v, 1)))
T("feet: the magnet goes into the hole", not _touching, str(_touching))

# the cap must have the seat, and as deep as the magnet: that is its whole job,
# and without a seat it is a cylinder good for nothing
_cap = cq.importers.importStep(OUT + "tools/magnet_cap.step").val()
_v = _cap.intersect(_magnet(0.0, 0.0, 0.0)).Volume()
T("cap: the magnet goes into the seat", _v <= 0.01, "%.2f mm3" % _v)
_v = _cap.intersect(_magnet(0.0, 0.0, D["Dp_seat_cap"] + 0.05)).Volume()
T("cap: the seat is not through-going", _v > 10.0, "ceiling of the seat %.1f mm3" % _v)
_v = _cap.intersect(_magnet(0.0, 0.0, D["Dp_seat_cap"] - D["Th_magnet"] - 0.1)).Volume()
T("cap: the wall guides the magnet over the whole seat", _v <= 0.01, "%.2f mm3" % _v)

_st = cq.importers.importStep(OUT + "sensor_bracket.step").val()
_v = _st.intersect(_magnet(0.0, 0.0, D["H_body"])).Volume()
T("bracket: the magnet goes into the ring", _v <= 0.01, "%.2f mm3" % _v)

# --- the motor on the arm ---------------------------------------------------
# These two checks look at the SOLID, and were born from a defect that could
# not be seen from the parameters: the Ø22.2 centring seat was dug on the face
# towards the BODY instead of the one the motor rests on. All the numbers were
# right - diameter, depth, position in plan, and in fact check_dimensions had
# nothing to object - and the part was wrong all the same, because what counts
# is which side it is dug from. The hub of the motor hit the solid plate:
# 682 mm3, measured by putting the real motor into the assembly.
_arm = cq.importers.importStep(OUT + "arm.step").val()

_arm_swept = _swept(_arm)

# --- the bearing seat: compensated, and with the lead-in --------------------
# The bearings had to be forced in. The seat was drawn at a net 13.0, that
# is the diameter of the outer ring taken from the catalogue, and printed it
# measures two tenths less: not a light interference - which is needed, because
# the outer ring must not turn in the plastic - but ten times as much, which on
# a 13 ring jams the balls. A bearing that turns stiffly cancels the reason it
# is there: the arm must stay free to follow the wear of the TPU.
#
# It is measured on the SOLID, looking for where the material starts, and the
# minimum is ABSOLUTE: a tenth and a half. It does not derive from
# Comp_hole_printing, because a check that takes its measuring stick from the
# number it guards would pass again the day the two dimensions get merged into
# one again.
_Pxb, _Pyb = D["R_disc"], D["Off_pivot"]
_z0b = D["Z_bottom_arm"]


_R_PROBE = 0.02


def _r_material(sol, z, a=0.0, step=0.005, cx=None, cy=None):
    """From which radius, around a centre, the material starts at that height.

    The probe is a small ball, so it touches the wall one probe radius BEFORE
    getting there: that radius is added, otherwise the measurement comes back
    systematically narrow by its diameter. The check just written fell for it:
    it read the seat as 13.12 instead of 13.20 and went off through its own
    fault.
    """
    cx = _Pxb if cx is None else cx
    cy = _Pyb if cy is None else cy
    r = 0.0
    while r < 12.0:
        p = cq.Vector(cx + r*math.cos(a), cy + r*math.sin(a), z)
        if sol.intersect(cq.Solid.makeSphere(_R_PROBE, p)).Volume() > 1e-12:
            return r + _R_PROBE
        r += step
    return None


_r_seat = _r_material(_arm, _z0b + D["Th_arm"]/2)
_play_bearing = 2*_r_seat - D["D_seat_bearings"] if _r_seat else -99.0
T("arm: the bearing seat is compensated for printing",
  _play_bearing >= 0.15,
  "seat measured %.2f, bearing %.2f, difference %.2f"
  % (2*(_r_seat or 0), D["D_seat_bearings"], _play_bearing))

# And there is a lead-in on BOTH faces: the bearings go in one per face, with
# the flanges staying outside. Without a lead-in the bearing has to enter flat
# into a seat eight millimetres deep, and part of what feels like a tight seat
# is only the entry.
_no_lead_in = []
for _name, _zf in (("motor face", _z0b + 0.05),
                   ("body face", _z0b + D["Th_arm"] - 0.05)):
    _rb = _r_material(_arm, _zf)
    if _rb is None or _rb - _r_seat < 0.10:
        _no_lead_in.append("%s: mouth %.2f against seat %.2f"
                             % (_name, 2*(_rb or 0), 2*_r_seat))
T("arm: the bearing seat has the lead-in on both faces",
  not _no_lead_in, "; ".join(_no_lead_in))

# The centring hub as the parameters describe it, protruding from the flange
# towards the arm. This is used and not the manufacturer's STEP on purpose: the
# motor file sits on the computer of whoever draws, and a check that depends on
# a downloaded file runs nowhere else. The parameters were checked against the
# real model: square 35.21, holes at ±13, Ø22 hub 2.00 high, Ø5 shaft 20.5
# long.
#
# The hub is built WITH ITS FILLET at the root, and not as a plain cylinder:
# the fillet is the reason the seat has the lead-in, and a hub modelled
# straight would pass even with a straight seat mouth. The check would go
# blind precisely on the thing it must look at. The cone here is bigger than
# the real fillet, which is concave: it errs on the safe side.
_zm = -D["Z_face_motor"]
_motor_hub = (cq.Workplane("XY").workplane(offset=_zm).center(D["Cd_motor"], 0.0)
          .circle(D["D_circle_motor"]/2).extrude(D["H_circle_motor"])
          .union(cq.Workplane(obj=cq.Solid.makeCone(
              D["D_fillet_hub_motor"]/2, D["D_circle_motor"]/2,
              D["H_fillet_hub_motor"],
              cq.Vector(D["Cd_motor"], 0.0, _zm), cq.Vector(0, 0, 1)))).val())
_v = _arm.intersect(_motor_hub).Volume()
T("motor: the centring hub goes into the seat", _v <= 0.01, "%.2f mm3" % _v)

# And on the other side the plate must be SOLID. Without this second check a
# seat dug on both faces would pass, and the first check alone passes even if
# the seat is not there at all and it is the shaft hole that was enlarged.
# THE SEAT IS BLIND AGAIN (for a while it went right through): the plate is
# back to Th_plate_motor = 3.5 and the hub of the motor is 2 tall, and the
# 1.5 mm above the hub are material again. Two things are
# measured: the seat is EMPTY up to H_seat_centring, and ABOVE it there is the
# floor - an annulus between the shaft hole and the seat wall, full.
_seat_column = (cq.Workplane("XY").workplane(offset=-D["Z_face_motor"] - 1.0)
             .center(D["Cd_motor"], 0.0).circle(D["D_seat_centring"]/2 - 0.3)
             .extrude(D["H_seat_centring"] + 1.0 - 0.1).val())
_left = _arm.intersect(_seat_column).Volume()
_floor = (cq.Workplane("XY").workplane(offset=-D["Z_face_motor"] + D["H_seat_centring"] + 0.1)
          .center(D["Cd_motor"], 0.0).circle(D["D_seat_centring"]/2 - 0.3)
          .circle(D["D_clear_shaft"]/2 + 0.3)
          .extrude(D["Th_plate_motor"] - D["H_seat_centring"] - 0.2).val())
_v_fondo = _arm.intersect(_floor).Volume()
T("motor: the centring seat is blind, with the floor above the hub",
  _left <= 1.0 and _v_fondo >= 0.95*_floor.Volume(),
  "in the seat %.1f mm3; solid floor %.0f of %.0f mm3" % (_left, _v_fondo, _floor.Volume()))
_flange_ring = (cq.Workplane("XY").workplane(offset=-D["Z_face_motor"])
           .center(D["Cd_motor"], 0.0)
           .circle(D["Cd_holes_motor"]/2 + D["D_holes_M3_printed"]/2)
           .circle(D["D_seat_centring"]/2)
           .extrude(D["Z_face_motor"]).val())
_full, _expected = _arm.intersect(_flange_ring).Volume(), _flange_ring.Volume()
T("motor: around the seat remains the ring the flange rests on",
  _full >= 0.80*_expected,
  "solid %.0f of %.0f mm3 (%.0f%%)" % (_full, _expected, 100*_full/_expected))

# --- the bearing flange against the collar hub ------------------------------
# The flange on the body side protrudes by Th_flange_bearing from the face of
# the arm hub, and it ended up inside the collar hub: 157 mm3, that is the
# volume of the whole flange. Now the hub has the spot face and the face set
# back.
_col = cq.importers.importStep(OUT + out_subdir("collar") + "collar.step").val()
# _box was further down, in the block of the box-to-collar attachment which
# disappeared with the joint. Many checks still need it, so it is
# loaded here next to the collar: they are the two regions of the same part.
_box = cq.importers.importStep(OUT + out_subdir("box") + "box.step").val()
_ap = math.radians(D["Ang_pivot"])
_px, _py = D["R_pivot"]*math.cos(_ap), D["R_pivot"]*math.sin(_ap)
_spf = D["Th_flange_bearing"]

def _crown(r_int, r_est, z0, z1):
    return (cq.Workplane("XY").workplane(offset=z0).center(_px, _py)
            .circle(r_est).circle(r_int).extrude(z1-z0).val())

# from the TOP FACE OF THE ARM (Z_top_arm), where the upper flange sits: it
# was a literal 0.0, and stayed there when the arm was raised
_zta_c = D["Z_top_arm"]
_flange = _crown(D["D_pivot_arm"]/2, D["D_flange_bearing"]/2, _zta_c, _zta_c + _spf)
_v = _col.intersect(_flange).Volume()
T("bearing flange: goes into the spot face", _v <= 0.01, "%.2f mm3" % _v)

# It is the flange that acts as the shoulder, not the ASA annulus: the arm turns
# on this joint under the preload of the spring, and plastic against plastic
# means friction and dust. Looking only at the interpenetration would not be
# enough: it would pass even with the two faces touching together, which is
# exactly the rejected case. So one checks that below the setback there is
# NOTHING.
_v = _col.intersect(_crown(D["D_pivot_arm"]/2 + 0.2, D["D_hub_pivot"]/2,
                            _zta_c, _zta_c + D["Setback_face_hub"])).Volume()
T("flange: only it rubs, not the ASA face", _v <= 0.01,
  "%.2f mm3 of collar below the setback" % _v)

# ...and that a shoulder really is there: pushed in by a twentieth, the flange
# must find the floor of the spot face. Without this, a through-going spot face
# - or one too deep - would pass the two checks above.
_v = _col.intersect(_flange.moved(cq.Location(cq.Vector(0, 0, 0.05)))).Volume()
T("flange: the floor of the spot face acts as its shoulder", _v > 1.0,
  "%.2f mm3 pushing it in by 0.05" % _v)

# --- the grub screw collar, and the dovetail --------------------------------
# The grub screw used to screw into the ASA. Now it bites into a heat-set
# insert, inside a Ø30 collar that sits below the tread: the height for the
# insert was not there above, because the hub cannot grow upwards - the
# opening of the body ends at 14.3 and the ceiling of the bay at 16.
_clutch_hub = cq.importers.importStep(OUT + "clutch_hub.step").val()
_clutch_tyre = cq.importers.importStep(OUT + "clutch_tyre.step").val()
_XCf = D["Cd_motor"]
_zi = D["Z_insert_grub"]
NT_clutch = int(D["N_teeth_clutch"])


def _solid_at(sol, x, y, z, r=0.06):
    return sol.intersect(cq.Solid.makeSphere(r, cq.Vector(x, y, z))).Volume() > 1e-12


# 1) the collar turns: its radius adds to the centre distance, and it must not
# get into the wheel body. It is measured on the solid, not on the parameter.
_wheel_body = cq.importers.importStep(OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step").val()
_v = _clutch_hub.intersect(_wheel_body).Volume()
T("clutch: the grub screw collar stays out of the body", _v <= 0.01, "%.3f mm3" % _v)
_d_body = _clutch_hub.distance(_wheel_body)
T("clutch: and stays out with a clearance", _d_body >= 0.5, "%.2f mm" % _d_body)

# 2) below the tunnel of the insert the declared wall remains. The solid is
# scanned from below: it is the thinnest wall of the joint.
_z_scan, _below, _edge_z = D["Free_collar_arm"], None, None
while _z_scan < _zi:
    if _solid_at(_clutch_hub, _XCf, D["D_collar_grub"]/2 - 2.0, _z_scan):
        _below = _z_scan if _below is None else _below
        _edge_z = _z_scan
    _z_scan += 0.05
_wall = (_edge_z - D["Free_collar_arm"] + 0.05) if _edge_z else 0.0
# The minimum is ABSOLUTE and does not derive from the parameter: a check that
# takes its measuring stick from the same number it guards moves together with
# the defect and guards nothing. Below eight tenths the insert, melting,
# breaks through.
T("clutch: the wall below the grub screw insert holds",
  _wall >= max(0.8, D["Wall_below_insert_grub"] - 0.1),
  "%.2f mm, declared %.2f, minimum 0.80" % (_wall, D["Wall_below_insert_grub"]))

# 3) around the insert the wall must be solid, as for the other inserts of the
# project: one looks at the sleeve between the diameter at which the insert
# MELTS and a little further out. Less than all round, because below there is
# only the wall measured above: one looks at the half towards the solid of the
# hub.
_y0f = D["D_collar_grub"]/2 - (D["L_insert_M3"] + 0.5)
_sleeve = (cq.Solid.makeCylinder(D["D_out_insert_M3"]/2 + 0.8, D["L_insert_M3"] - 0.4,
                                 cq.Vector(_XCf, _y0f + 0.2, _zi), cq.Vector(0, 1, 0))
           .cut(cq.Solid.makeCylinder(D["D_out_insert_M3"]/2, D["L_insert_M3"],
                                      cq.Vector(_XCf, _y0f, _zi), cq.Vector(0, 1, 0)))
           .cut(cq.Solid.makeBox(40, 40, 40, cq.Vector(_XCf - 20, _y0f - 1, _zi - 40))))
_full_sleeve = _clutch_hub.intersect(_sleeve).Volume()
T("clutch: solid wall around the grub screw insert",
  _full_sleeve >= 0.95*_sleeve.Volume(), "%.0f%%" % (100*_full_sleeve/_sleeve.Volume()))

# 3b) and the insert seat must be there, of its size and at the MOUTH: with a
# grub screw hole all the way along, the wall around would still turn out
# solid and the check above would pass.
_seat_faults = []
for _y, _what in ((D["D_collar_grub"]/2 - 0.3, "at the mouth"),
                  (_y0f + 1.0, "at the bottom")):
    if _solid_at(_clutch_hub, _XCf + D["D_hole_insert_M3"]/2 - 0.25, _y, _zi):
        _seat_faults.append("missing %s" % _what)
if not _solid_at(_clutch_hub, _XCf + D["D_hole_insert_M3"]/2 + 0.35, _y0f + 1.0, _zi):
    _seat_faults.append("too wide")
T("clutch: the insert seat is there, of its size, at the mouth",
  not _seat_faults, "; ".join(_seat_faults))

# 4) the grub screw must reach the flat of the shaft, and pass freely beyond
# the insert: the void on the axis is probed, and the solid just outside.
#
# WHERE it is probed derives from the part and is no longer written by hand.
# Here there were four fixed heights - 4, 6, 8, 10 - good as long as the grub
# screw collar was Ø30: taking it to Ø25 the insert seat came
# down to y 9, and the probe at y 10 found itself INSIDE the seat, where at
# that radius the material is not necessarily there. The check went off on a
# right part. Now the four probes are spread between the shaft hole and the
# bottom of the seat, that is exactly in the stretch of passage the check wants
# to guard, and they follow the collar on their own.
_y_pass0 = D["D_hole_clutch"]/2 + 0.5
_y_pass1 = _y0f - 0.3
_y_probes = [_y_pass0 + (_y_pass1 - _y_pass0)*_k/3 for _k in range(4)]
_blockers = [("%.1f" % _y, ) for _y in _y_probes
             if _solid_at(_clutch_hub, _XCf, _y, _zi)]
_narrow = [("%.1f" % _y, ) for _y in _y_probes
            if not _solid_at(_clutch_hub, _XCf + (D["D_grub"] + D["Cl_clear_grub"])/2 + 0.4, _y, _zi)]

T("clutch: the grub screw passes freely up to the flat",
  not _blockers and not _narrow,
  "obstructed at y %s; too wide at y %s" % (_blockers, _narrow))
_flat = D["Z_flat_shaft"]
T("clutch: and its hole really reaches the flat",
  not _solid_at(_clutch_hub, _XCf, _flat + 0.3, _zi), "at y %.2f there is material" % _flat)

# 4bis) the hole is a D, and the chord is where it should be.
# Before, here there was the opposite of a D: the round PLUS a slot as wide as
# the whole hole, which started from Flat_shaft minus the radius of the DRAWN
# hole - that is three tenths inside the shaft - and no check looked at it. It
# is measured on the solid, and at a height far from the grub screw, because at
# the grub screw height the channel crosses the chord and the solid is not
# necessarily there.
#
# Three different things, and they must be asked separately: that above the
# chord there is MATERIAL (otherwise the slot is back), that below there is
# VOID (otherwise the chord is further in than believed), and that the chord
# leaves its play to the flat of the shaft (otherwise the clutch does not slide
# on).
_z_d = D["Z_top_clutch"] + 6.0
_chord_faults = []
for _x, _where in ((0.0, "in the middle"), (-1.2, "on the left"), (1.2, "on the right")):
    if not _solid_at(_clutch_hub, _XCf + _x, D["Z_flat_hole"] + 0.15, _z_d):
        _chord_faults.append("solid missing above the chord %s" % _where)
    if _solid_at(_clutch_hub, _XCf + _x, D["Z_flat_hole"] - 0.15, _z_d):
        _chord_faults.append("there is material below the chord %s" % _where)
T("clutch: the shaft hole is a D, with the chord in its place",
  not _chord_faults, "; ".join(_chord_faults))
T("clutch: the chord leaves its play to the flat of the shaft",
  D["Z_flat_hole"] - D["Z_flat_shaft"] >= 0.05,
  "chord at %.3f, flat at %.3f" % (D["Z_flat_hole"], D["Z_flat_shaft"]))

# 5) the teeth are DOVETAILS: the tooth of the TPU ring is wider at the bottom
# than at the mouth, and that is what stops it slipping out radially. The
# width of the tooth is measured on the solid of the ring, at two radii: just
# inside the mouth and at the bottom. The tooth measured is the one at 0
# degrees, on the disc side.
def _tooth_width(_r):
    """The width of the ring's tooth at that radius from the clutch axis. It
    is measured along the ARC, not along a straight line: along a straight line
    one ends up in the crown of the ring, which starts just further out, and
    measures that instead of the tooth."""
    _z = D["Z_plane_mid_disc"]

    def _q(_ang):
        _a = math.radians(_ang)
        return (_XCf - _r*math.cos(_a), _r*math.sin(_a))

    # the probe is small: with a six-hundredths ball, flush with the mouth it
    # touched the CROWN of the ring, which starts just further out, and the
    # tooth came out as wide as the whole pitch
    _PROBE = 0.02
    if not _solid_at(_clutch_tyre, _q(0.0)[0], _q(0.0)[1], _z, _PROBE):
        return 0.0
    _lo, _hi = 0.0, 180.0/NT_clutch          # half a pitch between two teeth
    for _ in range(24):
        _m = (_lo + _hi)/2
        if _solid_at(_clutch_tyre, _q(_m)[0], _q(_m)[1], _z, _PROBE):
            _lo = _m
        else:
            _hi = _m
    return 2*_r*math.radians((_lo + _hi)/2)


# The two radii are taken flush with the ends, not two tenths inside: the tooth
# widens continuously, so every millimetre less of setback gives less widening
# to measure, and the comparison must be made with the EXPECTED one at those two
# radii. With a setback of two tenths per side the expected value drops to 0.9
# and the check went off on a sound part.
_IN = 0.1
_w_mouth = _tooth_width(D["D_hub_clutch"]/2 - _IN)
_w_bottom = _tooth_width(D["D_hub_clutch"]/2 - D["Th_teeth_clutch"] + _IN)
_expected = D["Widen_tail_dovetail"]*(D["Th_teeth_clutch"] - 2*_IN)/D["Th_teeth_clutch"]
# Here too the minimum is absolute: with Widen_tail_dovetail at zero the
# expected value became zero and the check passed on a rectangular tooth.
T("clutch: the tooth is a dovetail, not a rectangle",
  _w_bottom - _w_mouth >= max(0.5, 0.8*_expected),
  "mouth %.2f, bottom %.2f: widens by %.2f, expected %.2f, minimum 0.50"
  % (_w_mouth, _w_bottom, _w_bottom - _w_mouth, _expected))

# 6) the grub screw is tightened with the mechanism assembled and the box still
# open: the key comes in from +Y, horizontally. One checks that in front of the
# insert there is void for twenty-five millimetres of key.
_key_path = cq.Solid.makeCylinder(2.5, 25.0, cq.Vector(_XCf, D["D_collar_grub"]/2 + 0.2, _zi),
                                cq.Vector(0, 1, 0))
_obstructions = []
for _name, _sol in (("arm", _arm_swept), ("collar", _col), ("box", _box_solid),
                    ("body", _wheel_body)):
    if _sol.intersect(_key_path).Volume() > 0.01:
        _obstructions.append(_name)
T("clutch: the grub screw key can get there, with the box open", not _obstructions,
  "; ".join(_obstructions))

# --- the clutch window ------------------------------------------------------
# On a test print the clutch passed almost flush. Measured on the part already
# made: 1.50 mm above and 1.53 mm at the side - and no check complained about
# it, because of the window only the parameter chain was checked, and in the
# parameters the window was tied to the clutch by nothing.
#
# The measuring stick here is the SOLID, the threshold is the parameter: this
# way the check verifies that the geometry follows the declared play, and not
# itself.
from OCP.BRepExtrema import BRepExtrema_DistShapeShape as _DSS
_clutch = cq.importers.importStep(OUT + "clutch_assembly.step").val()
_gl = D["Cl_aperture_clutch"]

def _distance(a, b):
    _d = _DSS(a.wrapped, b.wrapped)
    _d.Perform()
    return _d.Value()

# Cylindrical sector, like the one the collar is built with. Copied and not
# imported on purpose: solids_body_collar.py is a script that regenerates the
# parts, importing it here would rebuild them instead of measuring them.
def _sector(a0, a1, r0, r1, z, h, step=1.0):
    _n = max(2, int((a1-a0)/step)+1)
    _A = [a0+(a1-a0)*i/(_n-1) for i in range(_n)]
    _p  = [(r1*math.cos(math.radians(a)), r1*math.sin(math.radians(a))) for a in _A]
    _p += [(r0*math.cos(math.radians(a)), r0*math.sin(math.radians(a))) for a in reversed(_A)]
    return cq.Workplane("XY").workplane(offset=z).polyline(_p).close().extrude(h).val()

_dcf = _distance(_col, _clutch)
T("clutch window: the collar keeps as far from it as the play",
  _dcf >= _gl - 0.05, "%.2f mm, play asked %.2f" % (_dcf, _gl))

# Above and at the side are two different defects and are closed with different
# dimensions - the half-width governs the side, the two z heights govern
# ceiling and floor - so a single measurement would hide one behind the other.
# The side play is isolated by cutting a horizontal slice at the height of the
# tread, where the clutch has its largest diameter: in that slice the distance
# that remains is necessarily horizontal.
_zb = D["Z_plane_mid_disc"]
_slice = cq.Workplane("XY").workplane(offset=_zb-0.05).rect(400, 400).extrude(0.1).val()
_dlat = _distance(_col.intersect(_slice), _clutch.intersect(_slice))
T("clutch window: the side play at the tread",
  _dlat >= _gl - 0.05, "%.2f mm at z %.1f" % (_dlat, _zb))

# And the window must be CLEAR from top to bottom. Between this cut and the one
# of the rib a 0.5 mm shelf remained, as wide as the window and as deep as the
# band, attached only at the two ends: a flake that prints badly in ASA and
# comes off in the hand, and that no distance measurement saw, because it was
# below the clutch and did not touch it. The prism starts from below the flange
# and reaches the ceiling of the window, so if the lower edge goes back up the
# flake reappears in here.
_alr = D["Ang_aperture_clutch"]
_window_ceiling = D["Z_top_clutch"] + D["H_hub_clutch"] + _gl
_prism = _sector(-_alr, _alr, D["D_body"]/2 + 0.15, D["R_out_collar"], -1.0, _window_ceiling + 1.0)
_v = _col.intersect(_prism).Volume()
T("clutch window: clear from top to bottom, no flakes",
  _v <= 0.01, "%.2f mm3 of collar inside the window" % _v)

# --- references of the box, used by the checks below -----------------------
# Here there were also the two checks on the chamfer of the outer edges - that
# the sharp edge was gone and that the chamfer did not eat the wall. The
# chamfer was removed (another edge treatment is to replace it), and they go with
# it: they guarded only it, and keeping them would have meant a check asking a
# part to be the way it no longer is. The third, that the envelope does not
# grow, stays and lives further down: that one says something true anyway.
_Ro = D["R_out_box"]
_ZTb, _ZBb = D["Z_floor_box"], 28.5
import electronics as _E

def _mat_sc(r, ang, z):
    _p = cq.Vector(r*math.cos(math.radians(ang)), r*math.sin(math.radians(ang)), z)
    return _box_solid.intersect(cq.Solid.makeSphere(0.08, _p)).Volume() > 1e-12

_Wb = D["Th_walls_box"]
_Qsp = D["Z_shoulder_box"]

# --- the fillet on the vertical edge ----------------------------------------
# It is the corner the hand meets picking up the instrument from the side: the
# end of the shell on the pivot side, where the flat head meets the back. It is
# probed on the inward diagonal, and both readings are needed - that the sharp
# edge is gone AND that a little further in the material is still there -
# otherwise a huge fillet, eating the wall, would pass the first half.
#
# On the other side, at -30, there is no edge: with the setback of the back
# the outline there turns by 157.6 degrees instead of 90, and a fillet of 4
# would set back by nine hundredths. The check had been seen failing on a
# sound part precisely for this, when it looked for an edge the setback had
# already removed.
#
# The head is not radial: the edge is where the PLANE of the head meets the
# back, and the two faces move away from there one along the head, inwards, and
# the other along the back, towards the board.
_Wb = D["Th_walls_box"]
_rv_s = math.sqrt(_Ro*_Ro - _E.T_HEAD_OUT**2)
_rv_cx, _rv_cy = _E.xy(_rv_s, _E.T_HEAD_OUT)
_rv_ax, _rv_ay = -_E.U[0], -_E.U[1]                      # along the head
_rv_tx, _rv_ty = -_rv_cy/_Ro, _rv_cx/_Ro                 # tangent to the back...
if _rv_tx*_E.V[0] + _rv_ty*_E.V[1] > 0:                  # ...towards decreasing t
    _rv_tx, _rv_ty = -_rv_tx, -_rv_ty
_rv_bx, _rv_by = _rv_ax + _rv_tx, _rv_ay + _rv_ty
_rv_lb = math.hypot(_rv_bx, _rv_by)
_rv_dx, _rv_dy = _rv_bx/_rv_lb, _rv_by/_rv_lb


def _rv_full(_d, _zz=-10.0):
    _p = cq.Vector(_rv_cx + _rv_dx*_d, _rv_cy + _rv_dy*_d, _zz)
    return _box_solid.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() > 1e-9


# The two probes are at FIXED distances, not proportional to the radius: tied
# to the radius, with a fillet of twelve the probe also moved by twelve and
# found material further in. Half a millimetre from the tip there must be
# nothing, at one wall thickness the material must still be there.
T("box: the vertical edge between head and back is filleted",
  not _rv_full(0.5), "still sharp")
T("box: the vertical fillet does not eat the wall",
  _rv_full(_Wb), "wall missing")

# --- the arc around the motor -------------------------------------------------
# The setback that used to end the mechanical lobe was replaced by an arc centred on the motor axis. Its checks - outline, wall, compartment,
# nothing left beyond it, clearance to arm, motor and clutch over the travel -
# live in check_arc_back.py, outside the audit, so that breaking them on
# purpose costs seconds and not a quarter of an hour.

# --- the hollowed shoulder --------------------------------------------------
# Above the shoulder height the bay is closed and only what carries the three
# rear ears remains. The solid is measured in two opposite directions, because
# one half alone would pass on the defect: that beyond the radius of the small
# pillars nothing is left, and that under every ear the pillar really is there -
# an ear hanging from nothing but itself holds until nobody pulls.
def _sector(a0, a1, r0, r1, z, h, step=1.0):
    _n = max(2, int((a1-a0)/step)+1)
    _A = [a0 + (a1-a0)*i/(_n-1) for i in range(_n)]
    _p = [(r1*math.cos(math.radians(a)), r1*math.sin(math.radians(a))) for a in _A]
    _p += [(r0*math.cos(math.radians(a)), r0*math.sin(math.radians(a))) for a in reversed(_A)]
    return (cq.Workplane("XY").workplane(offset=z).polyline(_p).close().extrude(h).val())

# The comparison radius is NOT R_rib_ears: a check that takes its measurement
# from the same parameter it guards moves together with the defect and always
# passes. The right measuring stick is the ear, which reaches r 88: above the
# shoulder nothing must remain beyond ten millimetres past the collar.
_R_max_shoulder = D["R_out_collar"] + 10.0
_beyond_shoulder = _box_solid.intersect(
    _sector(-32, 110, _R_max_shoulder, _Ro+1.0, _Qsp+_Wb+0.5, max(1.0, _ZBb-_Qsp))).Volume()
T("box: above the shoulder nothing superfluous is left",
  _beyond_shoulder <= 1.0,
  "%.1f mm3 beyond r %.1f" % (_beyond_shoulder, _R_max_shoulder))

# The pillar under every rear ear is no longer checked: the ears are gone
# (single part).

# ...and the new ceiling must let through what is in the bay. The clearance is
# measured between the solid of the box and the real contents, not between two
# written heights: it is also the clearance needed to slide the box over the
# already assembled mechanism, which is the way it is assembled.
# The volume searched starts at r 90 and not right against the wall: at 86.5
# the bosses of the collar get in, which reach r 87 and are not contents of the
# bay but the part the box rests on. With those inside, the clearance
# measurement always answered "half a millimetre" whatever the height of the
# ceiling, and the check no longer knew how to fail for the right reason.
_bay_inside = _sector(-28, 61, 90.0, _Ro-_Wb-0.5,
                     _ZTb+_Wb+0.5, (_Qsp-0.5)-(_ZTb+_Wb+0.5))
# The CABLE is excluded, and it is the only exclusion: it necessarily touches
# the ceiling, because it passes through it from its opening. Measuring it
# together with the others, the clearance came out as half a millimetre - the
# clearance of the cable from the edge of its hole, which is not what this
# check wants to know.
_vol_cable = cq.importers.importStep(OUT + out_subdir("sensor_cable") + "sensor_cable.step").val().Volume()
_vol_single_part = cq.importers.importStep(OUT + "box_collar.step").val().Volume()
_highest = -99.0
from parameters import fillet_screw as _fillet_screw
_xa, _ya = _fillet_screw()[0], _fillet_screw()[1]


def _on_fillet_screw(sol):
    c = sol.Center()
    return math.hypot(c.x - _xa, c.y - _ya) <= 1.0
# The COVER of the grip is excluded together with the box, and for the same
# reason: it is not contents of the bay, it is WALL - closed, it remakes the
# back. Its lips, though, sit behind the wall, that is inside the volume this
# check searches, and they rise all the way to the top: left in, it always gave
# "the highest reaches half a millimetre from the ceiling" whatever the height
# of the ceiling, which is the same way of no longer knowing how to fail as the
# collar bosses above.
_vol_cover = (cq.importers.importStep(OUT + "grip_cover.step").val().Volume()
              if os.path.exists(OUT + "grip_cover.step") else -1.0)
for _s in cq.importers.importStep(OUT + out_subdir("full_assembly") + "full_assembly.step").val().Solids():
    if abs(_s.Volume() - _box_solid.Volume()) < 1.0: continue
    # ...and the single part, which in the assembly took the place of the two halves
    if abs(_s.Volume() - _vol_single_part) < 1.0: continue
    if abs(_s.Volume() - _vol_cable) < 1.0: continue
    if abs(_s.Volume() - _vol_cover) < 1.0: continue
    # ...and so are the cover's second screw and its insert:
    # they sit in the collar at the corner with the arc, and they close the
    # box, they are not what stands in it. Told apart by where they are -
    # their centre on the screw's axis from parameters.fillet_screw - since
    # here the solids come without names
    if _on_fillet_screw(_s): continue
    _v = _s.intersect(_bay_inside)
    if _v.Volume() > 1.0: _highest = max(_highest, _v.BoundingBox().zmax)
# The minimum is no longer written here: it is Free_assembly_compartment, the
# same number from which derives how high the pivot support rises. Written in
# two places, the two would have come apart at the first change.
# There used to be an upper bound too, clearance <= 6: the sky was CHOSEN on the
# contents, and the bound kept it from wasting height. Now the roof is
# flush with the top of the collar (Z_shoulder_box is derived from
# it), so the height is no longer the sky's to waste - the guarantee that
# replaces the bound is the one just below: nothing of the part stands above
# the collar.
T("box: between the contents of the bay and the ceiling a hand gets through",
  D["Free_assembly_compartment"] <= _Qsp - _highest,
  "the highest reaches z %.2f, ceiling at %.2f -> clearance %.2f" % (_highest, _Qsp, _Qsp-_highest))

# THE ROOF IS FLUSH WITH THE COLLAR, measured on the two solids: the top of
# the printed part and the top of the collar half. Neither number comes from
# the parameters, so lowering the roof or leaving a bump on it rings here.
# One flat top is the requirement: a 3.5 mm step with three 4 mm pillars on
# it does not print as a face.
_z_part = cq.importers.importStep(OUT + "box_collar.step").val().BoundingBox().zmax
_z_collar = cq.importers.importStep(OUT + out_subdir("collar") + "collar.step").val().BoundingBox().zmax
_box_top = cq.importers.importStep(OUT + out_subdir("box") + "box.step").val().BoundingBox().zmax
T("box: the roof is flush with the collar, and nothing sticks out",
  abs(_z_part - _z_collar) < 0.01 and abs(_box_top - _z_collar) < 0.01,
  "part up to z %.2f, roof of the box at %.2f, collar at %.2f"
  % (_z_part, _box_top, _z_collar))

# The envelope of the box is a constraint of its own, not a consequence of the
# chamfer that was there: R_out_box is the radius beyond which one does not go,
# and anything added out there - a ridge, a boss, a stop - must stay inside.
# The check was born for the chamfer, but it outlives it.
_bbs = _box_solid.BoundingBox()
T("box: nothing goes past R_out_box",
  _bbs.xmax <= D["R_out_box"] + 0.01 and _bbs.ymax <= D["R_out_box"] + 0.01,
  "x up to %.2f, y up to %.2f, R_out_box %.1f" % (_bbs.xmax, _bbs.ymax, D["R_out_box"]))

# --- the gasket presses on material, not on empty space ---------------------
# THE CHECK THAT WAS MISSING, and that should have found the defect by itself.
# The manufacturer already has a small window in the body for reading the
# numbers on the disc, at Ang_window_body (6.5 degrees off the chord, not on
# it as first drawn), 9 wide, from r 66.2 outwards. The
# gasket groove was at 67..70. They are the same place: for those nine
# millimetres the cord pressed on nothing, it pressed on the hole - a light
# leak that was already there and that nobody had seen, because in the model
# the body was drawn SOLID there. A check cannot see what the model does not
# contain, and it is the same family of defect as the electronics bay that
# looked 96% empty because the perfboard was not there.
#
# The cord is searched for on the collar solid, angle by angle, instead of
# being rebuilt from the parameters: this way the check sees the groove WHERE
# IT IS, even where it deviates. OCCT's classifier is used instead of
# intersecting little balls, because here tens of thousands of points are
# needed.
from OCP.BRepClass3d import BRepClass3d_SolidClassifier as _Cl3d
from OCP.gp import gp_Pnt as _Pnt
from OCP.TopAbs import TopAbs_IN as _IN, TopAbs_ON as _ON

def _inside(solid):
    _c = _Cl3d(solid.wrapped)
    def f(x, y, z):
        _c.Perform(_Pnt(x, y, z), 1e-7)
        return _c.State() in (_IN, _ON)
    return f

def _pol_xy(r, ang):
    _a = math.radians(ang)
    return r*math.cos(_a), r*math.sin(_a)

# A stable alias of the factory: further on the name _inside is reused as a
# variable inside a loop, and whoever called it afterwards would find a solid
# instead of the function. It happened, and it cost a build.
_inside_factory = _inside
_in_col = _inside(_col)
_in_body = _inside(cq.importers.importStep(OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step").val())
_pg, _lgc = D["Dp_groove_gasket"], D["L_groove_gasket"]
# The groove is searched for halfway up its REAL walls: from its bottom at
# -Dp_groove_gasket to the face of the flange, which is set back to
# -Cl_groove_collar. It was -_pg/2, that is halfway to z 0, which held only
# while the set-back (0.5) stayed above -0.75: at 0.8 the probe
# fell above the face, the groove "was not found" anywhere, and the gasket
# checks failed on a groove that was there.
_zg = -(D["Dp_groove_gasket"] + D["Cl_groove_collar"])/2
_a0c, _a1c = -D["Ang_collar_opposite"], D["Ang_collar_pivot"]

def _refine(ang, z, ra, rb, wanted):
    for _ in range(8):
        _m = (ra+rb)/2
        if _in_col(*_pol_xy(_m, ang), z) == wanted: rb = _m
        else: ra = _m
    return (ra+rb)/2

def _groove_at(ang, z, step=0.25):
    """Where the groove is at that angle, searched for on the solid: the first
    empty after the first solid, going from the axis outwards. Coarse step and
    then bisection: with a fine step this check alone took the audit from 55
    to 169 seconds."""
    _r, _found_solid = 55.0, False
    while _r < 75.0:
        _p = _in_col(*_pol_xy(_r, ang), z)
        if _p: _found_solid = True
        elif _found_solid: break
        _r += step
    if _r >= 75.0: return None
    _ri = _refine(ang, z, _r-step, _r, False)
    while _r < 75.0 and not _in_col(*_pol_xy(_r, ang), z):
        _r += step
    if _r >= 75.0: return None
    return (_ri, _refine(ang, z, _r-step, _r, True))

_no_rest, _cord = [], []
for _k in range(0, 163, 3):
    _ang = _a0c + _k
    if _ang > _a1c: break
    _c = _groove_at(_ang, _zg)
    if _c is None:
        _no_rest.append("%.0f: groove not found" % _ang)
        continue
    _rm = (_c[0]+_c[1])/2
    _cord.append((_ang, _rm))
    if not _in_body(*_pol_xy(_rm, _ang), 0.3):
        _no_rest.append("%.0f degrees, r %.1f" % (_ang, _rm))
T("gasket: the cord presses on material along its whole length",
  not _no_rest,
  "presses on empty space at " + "; ".join(_no_rest[:6]))

# ...and the bending radius of the deviation. Since the gasket is PRINTED, this
# is no longer the constraint it was: a printed part is born already curved,
# with the deviation inside its own shape, and does not have to bend - it only
# has to fit. The number stays, though, and that is why the check is not
# removed: it says what would be needed the day one went back to a bought
# cord, which instead really has to make the bend. It is measured on the line
# found on the solid, not on the one that was meant to be drawn.
_rmin, _where = 1e9, None
for _i in range(1, len(_cord)-1):
    _p0, _p1, _p2 = [_pol_xy(_cord[_j][1], _cord[_j][0]) for _j in (_i-1, _i, _i+1)]
    _a = math.hypot(_p1[0]-_p0[0], _p1[1]-_p0[1])
    _b = math.hypot(_p2[0]-_p1[0], _p2[1]-_p1[1])
    _cc = math.hypot(_p2[0]-_p0[0], _p2[1]-_p0[1])
    _area = abs((_p1[0]-_p0[0])*(_p2[1]-_p0[1]) - (_p2[0]-_p0[0])*(_p1[1]-_p0[1]))/2
    if _area > 1e-9:
        _R = _a*_b*_cc/(4*_area)
        if _R < _rmin: _rmin, _where = _R, _cord[_i][0]
T("gasket: the deviation could be bent even by a bought cord",
  _rmin >= 3*_lgc, "minimum radius %.1f mm at %.0f degrees, cord Ø%.1f" % (_rmin, _where or 0, _lgc))

# --- the printed gaskets ----------------------------------------------------
# Now the cord is really there and is no longer just its groove, so one can
# look at it instead of at the place where it should be.
# The two names are composed, and that is why the translation of the part
# names did not get here by itself: the string "front_gasket" is not in the
# file whole, a piece of it is. It is the same trap that rename_en.py
# documents for the parameters composed at runtime, and it is searched for the
# same way - a string that starts like a part name and contains a placeholder.
# In English the two words also swapped places.
_gaskets = {n: cq.importers.importStep(OUT + "%s_gasket.step" % n).val()
        for n in ("front", "rear")}
_body_ref = cq.importers.importStep(OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step").val()

# 1) it sits in the groove without being forced in: it must not share a single
#    cubic millimetre with the collar. If it does, either it is wider than the
#    groove or it ended up on the wrong side - it happened: built with the
#    direction reversed, both were born outside the groove and interpenetrated
#    the collar by 620 mm3, that is their whole volume.
_in_groove = {n: _col.intersect(_gaskets[n]).Volume() for n in _gaskets}
T("gaskets: they sit in the groove without forcing",
  all(v <= 1.0 for v in _in_groove.values()),
  "; ".join("%s %.1f mm3" % (n, v) for n, v in _in_groove.items()))

# 2) the lip stands out, and that volume is the squeeze. Two extremes: if it
#    does not stand out it does not touch the body and does not seal; if it
#    stands out too much, once closed it does not fit in the groove and the
#    flange no longer rests.
_stand_out = {n: _gaskets[n].intersect(_body_ref).Volume() for n in _gaskets}
T("gaskets: the lip stands out and presses on the body",
  all(v > 20.0 for v in _stand_out.values()),
  "; ".join("%s %.0f mm3" % (n, v) for n, v in _stand_out.items()))

# 3) ...and squeezed it fits. The volume that stands out must go into the
#    empty space left in the groove. The groove is measured on the solid,
#    angle by angle, not derived from the parameters.
# The key is English like the file, the label was Italian like all the others
# of this module: they are two different things and they ended up being the
# same string. Keeping them together, translating the part name would have
# written "guarnizione front" in the report. (Now that the labels are English
# too the two coincide again, but they stay two fields.)
for _n, _label, _z_mouth, _v in (("front", "front", 0.0, +1),
                              ("rear", "rear", D["H_body"], -1)):
    _bb = _gaskets[_n].BoundingBox()
    _vol_gasket = _gaskets[_n].Volume()
    _arcs = []
    for _k in range(0, 163, 3):
        _ang = _a0c + _k
        if _ang > _a1c: break
        _c = _groove_at(_ang, _zg) if _n == "front" else None
        if _n == "rear":
            _c = (D["R_gasket"]-_lgc/2, D["R_gasket"]+_lgc/2)
        if _c: _arcs.append((_ang, _c))
    _vol_groove = sum((_c[1]**2 - _c[0]**2)/2 * math.radians(3) for _, _c in _arcs) * _pg
    _free = _vol_groove - (_vol_gasket - _stand_out[_n])
    T("%s gasket: squeezed it fits in the groove" % _label,
      _free > _stand_out[_n],
      "%.0f mm3 stand out, %.0f are left free in the groove" % (_stand_out[_n], _free))

# 4) and in the degrees of the small window it must not reach it. The
#    comparison must be made ONLY there: outside that sector the gasket is at
#    its usual radius, which is 69.9 at the outer edge - further out than the
#    window, but eighty degrees away. A check that looked at the maximum
#    radius over the whole arc would sound for a part that has nothing to do
#    with it.
_r_max_window = 0.0
for _v in _gaskets["front"].Vertices():
    _agr = math.degrees(math.atan2(_v.Y, _v.X))
    if abs(_agr - D["Ang_window_numbers"]) <= D["Ang_flat_groove"]:
        _r_max_window = max(_r_max_window, math.hypot(_v.X, _v.Y))
T("front gasket: in the degrees of the window it stays away from it",
  _r_max_window < D["R_in_window_numbers"] - 0.5,
  "reaches r %.2f, the window starts at %.2f" % (_r_max_window, D["R_in_window_numbers"]))

# --- the small window is outside the seal -----------------------------------
# If it fell inside, the light coming in would reach the filter bay. Both
# things are measured on the solid - where the cord ends and where the
# opening starts - and one checks that there is a strip of material between
# them.
_Rfin = D["R_in_window_numbers"]
_worst, _ang_worst = 1e9, None
# round the window where it IS: it was -8..+8 about zero, and with the
# window turned to 6.5 degrees its far edge was left out
for _ang in [D["Ang_window_numbers"] + x*0.5 for x in range(-16, 17)]:
    _c = _groove_at(_ang, _zg)
    if _c is None: continue
    # start a whisker past the edge of the groove: starting EXACTLY on the
    # edge, which is where the bisection left it, the first probe can already
    # fall into empty space and the measure of the strip comes out negative.
    _r = _c[1] + 0.05
    while _r < 75.0 and _in_col(*_pol_xy(_r, _ang), _zg): _r += 0.25
    _r = _refine(_ang, _zg, _r-0.25, _r, False)
    if _r - _c[1] < _worst: _worst, _ang_worst = _r - _c[1], _ang
T("window: a strip of material is left between the cord and the opening", _worst >= 1.0,
  "narrowest strip %.2f mm at %.1f degrees" % (_worst, _ang_worst or 0))

# --- the sensor cable -------------------------------------------------------
# Now the cable is there as a solid, so one can ask it what nobody could until
# now: whether the route really exists. The constraint that rules is not the
# diameter but the BENDING RADIUS - a cable that fits but has to be bent
# tighter than it can bear is a cable that does not fit: it gets stripped, it
# breaks from fatigue, or it pushes back and misaligns what it is attached to.
#
# The radius is measured on the EXPORTED AXIS, not on the points written in
# the generator: it is the same curve along which the tube was swept, so the
# two cannot diverge, but the number comes out of the delivered geometry.
_cable_axis = cq.importers.importStep(OUT + out_subdir("sensor_cable_axis") + "sensor_cable_axis.step").val()
_wire_edge = _cable_axis.Edges()[0]
_cable_pts = [_wire_edge.positionAt(_i/400.0) for _i in range(401)]
_rmin_cable, _where_cable = 1e9, 0.0
for _i in range(1, len(_cable_pts)-1):
    _a3 = (_cable_pts[_i]-_cable_pts[_i-1]).Length
    _b3 = (_cable_pts[_i+1]-_cable_pts[_i]).Length
    _c3 = (_cable_pts[_i+1]-_cable_pts[_i-1]).Length
    _s3 = (_cable_pts[_i]-_cable_pts[_i-1]).cross(_cable_pts[_i+1]-_cable_pts[_i]).Length/2
    if _s3 > 1e-12:
        _R3 = _a3*_b3*_c3/(4*_s3)
        if _R3 < _rmin_cable: _rmin_cable, _where_cable = _R3, _i/400.0
T("sensor cable: it does not bend tighter than its minimum",
  _rmin_cable >= D["R_curvature_min_cable"],
  "minimum radius %.1f mm at %.0f%% of the route, minimum allowed %.1f (to be confirmed)"
  % (_rmin_cable, 100*_where_cable, D["R_curvature_min_cable"]))

# ...and it must go THROUGH THE SLOT, not beside it. The slot is open on the
# inner edge of the roof and runs along the radius: one checks that the axis,
# at mid-thickness of the roof, is inside its lane, and that the whole cable
# does not touch the box. A route that climbs over the roof where there is no
# roof would be a route that does not exist on the assembled machine.
_av_c = math.radians(D["Ang_opening_cable_box"])
_ua_c = (math.cos(_av_c), math.sin(_av_c))
_crossing = [p for p in _cable_pts
          if abs(p.z - (D["Z_shoulder_box"] + D["Th_walls_box"]/2)) < 0.5]
_outside_slot = []
for _p in _crossing:
    _along = _p.x*_ua_c[0] + _p.y*_ua_c[1]
    _lat = abs(-_p.x*_ua_c[1] + _p.y*_ua_c[0])
    if _lat > D["D_opening_cable_box"]/2 - D["D_cable_sensor_measured"]/2 \
            or not (D["R_out_collar"] <= _along <= D["R_opening_cable_box"]):
        _outside_slot.append("r %.1f, sideways %.2f" % (_along, _lat))
T("sensor cable: it crosses the roof inside its slot",
  _crossing and not _outside_slot, "; ".join(_outside_slot) if _crossing else "it does not cross the roof")

# ...and it must not be where the arm turns. The arm is not still: its SWEPT
# envelope is looked at, as is done for the ears of the box.
_cable_solid = cq.importers.importStep(OUT + out_subdir("sensor_cable") + "sensor_cable.step").val()
_v = _cable_solid.intersect(_arm_swept).Volume()
T("sensor cable: it stays out of the arm's travel", _v <= 0.01, "%.2f mm3" % _v)

_v = _cable_solid.intersect(_box_solid).Volume()
T("sensor cable: it does not touch the box, not even in the slot", _v <= 0.01, "%.3f mm3" % _v)

# ...and it must not touch the electronics below it.
_v = sum(_cable_solid.intersect(cq.importers.importStep(OUT + "electronics/%s.step" % _n).val()).Volume()
         for _n in ("perfboard", "pin_sockets", "xiao", "driver", "components", "gx12", "gx12_nut", "led"))
T("sensor cable: it ends above the electronics without touching it", _v <= 0.01, "%.2f mm3" % _v)

# --- the reinforced pivot and its washer ------------------------------------
# The pivot is bored lengthwise and an M3 goes through it, which is the
# reinforcement: the plastic makes the sleeve the bearings turn on, the steel
# makes the structure. Here one checks that the bore is really there, that the
# ASA tube that is left is not a film, that the insert is at the top of the
# hub and not at the root, and that the washer presses where it must.
_ztip = D["Z_bottom_arm"]
# the mouth of the insert, from the model: it was a literal 10.0, and the
# insert moved up with the arm (Z_mouth_insert_pivot)
_ztop = D["Z_mouth_insert_pivot"]

def _full_col(x, y, z, r=0.06):
    return _col.intersect(cq.Solid.makeSphere(r, cq.Vector(x, y, z))).Volume() > 1e-12

def _boundary_col(f, a, b):
    for _ in range(22):
        _m = (a+b)/2
        if f(_m): b = _m
        else: a = _m
    return (a+b)/2

# 1) the bore goes right through: on the axis, from the bottom of the washer
# up to below the seat. The lower half of the bore is in the
# bushing on the washer, not in the collar: both are probed, or the half that
# moved would pass for empty just because it is not there.
_washer_v = cq.importers.importStep(OUT + "pivot_washer.step").val()

def _full_washer(x, y, z, r=0.06):
    return _washer_v.intersect(cq.Solid.makeSphere(r, cq.Vector(x, y, z))).Volume() > 1e-12

_plugged = None
_z = _ztip - D["Th_washer_pivot"] + 0.3
while _z < _ztop - D["Dp_seat_insert_M3_pivot"] - 0.3:
    if _full_col(_px, _py, _z) or _full_washer(_px, _py, _z): _plugged = _z; break
    _z += 0.4
T("reinforced pivot: the screw bore goes right through", _plugged is None,
  "" if _plugged is None else "plugged at z %.2f" % _plugged)

# 2) how much ASA is left around the screw, measured at mid-overhang. The
# number is not derived from the two diameters: it is the solid that has to
# say there is a tube there.
_zmeas = (_ztip + D["Z_top_arm"])/2            # middle of the overhang
# measured on the bushing, which is where the tube is now
_r_bore = _boundary_col(lambda r: _full_washer(_px+r, _py, _zmeas), 0.0, 2.4)
# searched from just past the bore, not from a fixed 2.6: from 2.6 a bushing
# thinned below that radius read as a full one
_r_skin = _boundary_col(lambda r: not _full_washer(_px+r, _py, _zmeas), _r_bore + 0.1, 6.0)
_pivot_wall = _r_skin - _r_bore
T("reinforced pivot: a wall is left around the screw", 0.6 <= _pivot_wall <= 1.5,
  "tube from r %.2f to r %.2f -> %.2f mm of ASA per side"
  % (_r_bore, _r_skin, _pivot_wall))

# 3) the insert seat is at the TOP of the hub and contains it whole. At the
# bottom of the hub, at the root of the pivot, the screw would stop right
# where the moment is greatest: the stretch that breaks would be left
# uncovered.
_r_between = (D["D_clear_screw_pivot"]/2 + D["D_hole_insert_M3"]/2)/2
_p_ins, _p = 20.0, 0.0
while _p < 20.0:
    if _full_col(_px + _r_between, _py, _ztop - _p):
        _p_ins = _boundary_col(lambda q: _full_col(_px+_r_between, _py, _ztop-q), _p-0.25, _p)
        break
    _p += 0.25
T("reinforced pivot: the insert seat is at the top and contains it",
  D["L_insert_M3"] <= _p_ins + 0.06 <= D["L_insert_M3"] + 2.0,
  "seat %.2f deep from the top, insert %.2f long" % (_p_ins + 0.06, D["L_insert_M3"]))

# 4) a catalogue M3 x 20 must reach engagement. Under the head there are the
# washer, the overhang and the hub: if it does not reach, the right screw is
# another one, and it must be said here instead of being found out at
# assembly.
_washer = cq.importers.importStep(OUT + "pivot_washer.step").val()
_z_head = _washer.BoundingBox().zmin
_z_screw_tip = _z_head + 20.0
# The engagement is how much of the THREAD the screw takes, not how far it
# goes: a longer screw does not take more, it comes out of the hub. Hence two
# conditions, and the second is the one a screw that is too long fails.
_engagement = max(0.0, min(_z_screw_tip, _ztop) - (_ztop - _p_ins))
T("reinforced pivot: an M3 x 20 engages the insert without leaving the hub",
  _engagement >= 2.0 and _z_screw_tip <= _ztop + 0.01,
  "engagement %.1f mm of the insert's %.1f, tip at z %.2f (top of the hub %.1f)"
  % (_engagement, D["L_insert_M3"], _z_screw_tip, _ztop))

# 5) the washer presses ONLY on the inner ring. The flanges of the F695ZZ
# belong to the outer ring: anything resting on them locks the bearing.
_bearing_low = _crown(D["D_pivot_arm"]/2, D["D_seat_bearings"]/2,
                      _ztip, _ztip + D["H_bearings"]/2)
_flange_low = _crown(D["D_in_flange_bearing"]/2,
                         D["D_flange_bearing"]/2, _ztip - _spf, _ztip)
_v = _washer.intersect(_flange_low).Volume()
T("pivot washer: it does not touch the flange, which is the outer ring",
  _v <= 0.01, "%.3f mm3" % _v)
_d_washer = _washer.BoundingBox().xlen
T("pivot washer: it sits within the inner ring",
  D["D_pivot_arm"] + 1.0 <= _d_washer <= D["D_ring_in_bearing"],
  "washer %.2f, inner ring %.2f, pivot %.2f"
  % (_d_washer, D["D_ring_in_bearing"], D["D_pivot_arm"]))

# 6) ...and it must really get there: pushed in by a twentieth it must find
# the ring. It is this contact that retains the arm, which today is retained
# by nothing and slides off the pivot. Without this half, a washer too small
# or too far away would pass the check above.
_v = _bearing_low.intersect(_washer.moved(cq.Location(cq.Vector(0, 0, 0.05)))).Volume()
T("pivot washer: the inner ring finds it, and it is what retains the arm",
  _v > 0.3, "%.2f mm3 pushing it in by 0.05" % _v)

# --- the attachment of the box to the collar: IT NO LONGER EXISTS -----------
# Five checks were here: that the insert did not break through the wall, that
# the ears stayed out of the arm's travel and of the bracket, that the screws
# gripped the collar at two different heights to make a couple against the
# moment of the spring, and that ear and boss mated without interpenetrating.
#
# There is no attachment any more: box and collar are the
# same part and that moment is carried by the material. The checks go away
# with what they checked - keeping them with an empty box_attachments() would
# mean five tests that always pass, which is worse than no test.

# --- the flat bottom of the collar ------------------------------------------
# It is NO longer checked that the collar rests on the bed with the flange:
# the collar is not printed by itself, and the flat is the
# electronics hatch on the other side of the part. The question of what is
# born on supports was taken over by src/study_support_orientation.py, which
# asks it on the whole part and in the real orientation.
#
# What remains is the bracket pocket, which has nothing to do with the joint:
# the bracket turns on the magnet to go and reach the screws, so it is tried
# at the two ends of the collar slot and in the middle. The layer no longer
# needs to be pierced to remove the insert bosses: the bosses are gone.
_Fl, _Hc = D["Th_flange_collar"], D["H_body"]
_slab = lambda z0, h: cq.Workplane("XY").workplane(offset=z0).rect(400, 400).extrude(h).val()
_layer = _col.intersect(_slab(_Hc + _Fl, D["H_boss_insert"]))
_hits_fp = []
for _g in (-D["Halfw_slot_collar"], 0.0, D["Halfw_slot_collar"]):
    _v = _st.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _g).intersect(_layer).Volume()
    if _v > 0.01:
        _hits_fp.append("%+.1f degrees: %.2f mm3" % (_g, _v))
T("flat bottom: the bracket sits in its pocket along the whole slot", not _hits_fp,
  "; ".join(_hits_fp))

# --- the electronics in the motor bay ---------------------------------------
# The board sits in the motor bay, on a small panel that closes an opening in
# the bottom: remove three screws and the whole group comes out. These checks
# look that the things that make that sentence true stay true, and measure
# them on the solids.
import electronics as _E
_pan = cq.importers.importStep(OUT + "board_panel.step").val()
_EL = {_n: cq.importers.importStep(OUT + "electronics/%s.step" % _n).val()
       for _n in ("perfboard", "pin_sockets", "xiao", "driver", "components", "gx12", "gx12_nut", "led")}

_v = _pan.intersect(_box).Volume()
T("board panel: it sits in its opening without interpenetrating", _v <= 0.01, "%.3f mm3" % _v)

# 1) The group must COME OUT of the bottom by translation: that is the point
# of the small panel. Not the GX12, that one is screwed to the head. One tries
# to pull it down in several steps: the USB socket and the XIAO board sit in a
# groove of the head, and if it were not open towards the bottom the group
# would get stuck there.
_group = _pan
for _n in ("perfboard", "pin_sockets", "xiao", "driver", "components"):
    _group = _group.fuse(_EL[_n])
_worst = max(_group.moved(cq.Location(cq.Vector(0, 0, -_p))).intersect(_box).Volume()
              for _p in (1, 3, 6, 10, 15, 20, 30, 40))
T("board panel: it comes out of the bottom with the board, without getting stuck",
  _worst <= 0.01, "%.3f mm3 at the worst point" % _worst)

# 2) The electronics touch nothing. Arm, motor and clutch turn: they are looked
# at in five positions of the travel, ends included. The head of the pivot
# screw is not in the model: it is added as an estimate, Ø5.5 x 3 under the
# washer, because it is what gives the lowest spot above the board.
_mot = (cq.importers.importStep(os.path.join(os.path.dirname(os.path.dirname(OUT.rstrip(os.sep))),
                                             "others", "14HS10-0404S.STEP")).val()
        .rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
        .translate(cq.Vector(D["Cd_motor"], 0, -D["Z_face_motor"])))
_moving = {"arm": _arm, "motor": _mot,
           "clutch": cq.importers.importStep(OUT + "clutch_assembly.step").val()}
_fixed = {"collar": _col, "sensor cable": _cable_solid,
          "pivot washer": cq.importers.importStep(OUT + "pivot_washer.step").val(),
          "spring cup": cq.importers.importStep(OUT + "spring_cup.step").val(),
          "pivot screw head (estimate)": cq.Solid.makeCylinder(
              2.75, 3.0, cq.Vector(D["R_disc"], D["Off_pivot"],
                                   D["Z_bottom_arm"] - D["Th_washer_pivot"] - 3.0))}
for _c in __import__("purchased").purchased_parts():
    if _c.get("main") or _c.get("inside_motor"):
        continue
    # A fastener does NOT hit the part it fastens: the screw goes through the
    # holes of the parts it holds together, the insert sits in its seat with
    # the press-in interference, which is intended - Ø3.6 in a 3.25 hole is
    # how one heat-sets it. Without this line, at the first build after putting
    # screws and inserts in the assembly every fastener reported itself.
    # along its own axis: the clutch grub screw and its insert are horizontal,
    # and built along z they ended up somewhere else
    _p0, _p1, _u = __import__("purchased").axis_ends(_c)
    _fixed["%s at %.0f,%.0f" % ((_c["name"],) + tuple(_c["xy"]))] = (
        cq.Solid.makeCylinder(_c["d"]/2, math.dist(_p0, _p1),
                              cq.Vector(*_p0), cq.Vector(*_u)),
        tuple(_c.get("passes_through", ())))
_hits_el, _near = [], []
# THE DISTANCE ONLY WHERE IT CAN BE UNDER THE THRESHOLD. This
# distance() was half the audit - 519 s of 1076, measured - and nearly all of
# it went on pairs centimetres apart: of the 135 pairs, 15 have bounding
# boxes within the threshold, and those take 4.5 s. Boxes farther apart than
# the threshold mean a distance over it, so skipping them changes no answer.
_THRESHOLD_EL = 1.0


def _boxes_near(a, b, m):
    p, q = a.BoundingBox(), b.BoundingBox()
    return not (p.xmax + m < q.xmin or q.xmax + m < p.xmin or p.ymax + m < q.ymin
                or q.ymax + m < p.ymin or p.zmax + m < q.zmin or q.zmax + m < p.zmin)


for _n, _sol in list(_EL.items()) + [("board_panel", _pan)]:
    for _m, _f in _fixed.items():
        _allowed = ()
        if isinstance(_f, tuple):
            _f, _allowed = _f
        if _n in _allowed:
            continue
        if _sol.intersect(_f).Volume() > 0.01:
            _hits_el.append("%s/%s" % (_n, _m))
    for _m, _f in _moving.items():
        for _g in (_TRAVEL_DOWN, _TRAVEL_DOWN/2, 0.0, _TRAVEL_UP/2, _TRAVEL_UP):
            _fr = _f.rotate(_PIVOT_AXIS[0], _PIVOT_AXIS[1], _g)
            if _sol.intersect(_fr).Volume() > 0.01:
                _hits_el.append("%s/%s at %+.2f degrees" % (_n, _m, _g))
            elif _boxes_near(_sol, _fr, _THRESHOLD_EL) and _sol.distance(_fr) < _THRESHOLD_EL:
                _near.append("%s/%s at %+.2f" % (_n, _m, _g))
    if _n not in ("gx12", "gx12_nut") and _sol.intersect(_box).Volume() > 0.01:
        _hits_el.append("%s/box" % _n)
T("electronics: they touch nothing, along the whole travel of the arm", not _hits_el,
  "; ".join(_hits_el))
T("electronics: at least a millimetre is left from what moves", not _near,
  "; ".join(_near))

# The GX12 of the model is a 14.8 cylinder even where it goes through the
# wall, which instead takes its thread: it is looked at outside the thickness
# of the head, inside and outside.
_outside_wall = (cq.Workplane(obj=cq.Solid.makeBox(400, _E.T_HEAD_OUT - _E.T_HEAD_IN + 0.2, 200,
                                                  cq.Vector(-100, _E.T_HEAD_IN - 0.1, -100))
                              .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _E.A_BOARD)).val())
# One solid at a time, and with two orders of the operations: on some
# geometries OCCT returns a null shape instead of a volume. It happened when
# breaking the hole on purpose, and the audit stopped instead of saying what
# was wrong. If neither order succeeds, the check says so and does not pass.
_v, _unmeasured = 0.0, 0
for _gs in _EL["gx12"].Solids() + _EL["gx12_nut"].Solids():
    try:
        _v += _gs.cut(_outside_wall).intersect(_box).Volume()
    except ValueError:
        try:
            _v += _gs.intersect(_box).cut(_outside_wall).Volume()
        except ValueError:
            _unmeasured += 1
T("GX12: nut and body stay outside the wall that carries them",
  _v <= 0.01 and not _unmeasured,
  "%.3f mm3%s" % (_v, ", %d solids not measurable" % _unmeasured if _unmeasured else ""))
# and the hole is really there: along the axis, in the thickness of the head,
# nothing
_gx_p = [cq.Vector(*(_E.xy(_E.GX12_S + _dr, _tt) + (_E.GX12_Z,)))
         for _tt in (_E.T_HEAD_IN + 0.3, _E.T_HEAD_OUT - 0.3)
         for _dr in (-D["D_hole_gx12"]/2 + 0.4, 0.0, D["D_hole_gx12"]/2 - 0.4)]
_plugged = [p for p in _gx_p if _box.intersect(cq.Solid.makeSphere(0.15, p)).Volume() > 1e-9]
T("GX12: the hole goes through the head", not _plugged, "%d solid points" % len(_plugged))

# The LED above the GX12: its hole goes through the head, and inside, the
# collar does not touch the nut. That the LED does not touch the box is
# already said by the general check above, which contains it.
_led_p = [cq.Vector(*(_E.xy(_E.LED_S, _tt) + (_E.LED_Z,)))
          for _tt in (_E.T_HEAD_IN + 0.3, (_E.T_HEAD_IN + _E.T_HEAD_OUT)/2, _E.T_HEAD_OUT - 0.3)]
_plugged = [p for p in _led_p if _box.intersect(cq.Solid.makeSphere(0.15, p)).Volume() > 1e-9]
T("LED: the hole goes through the head", not _plugged, "%d solid points" % len(_plugged))
_d_led = min(_EL["led"].distance(_EL["gx12"]), _EL["led"].distance(_EL["gx12_nut"]))
T("LED: the collar stays as far from the GX12 as the clearance",
  _d_led >= D["Cl_led_gx12"] - 0.1, "%.2f mm" % _d_led)


# 3) The USB socket flush with the outer face. Both are measured on the solid:
# the face of the head by probing the box beside the slot, the mouth of the
# socket from the vertices of the XIAO. If the wall moved, or the socket, the
# number written in the parameters would not notice.
def _full_box(s_, t_, z_):
    return _box.intersect(cq.Solid.makeSphere(
        0.05, cq.Vector(*(_E.xy(s_, t_) + (z_,))))).Volume() > 1e-12


_zu = (_E.Z_USB[0] + _E.Z_USB[1])/2
_up = _E.S_USB + _E.USB_L/2 + D["Cl_usb"] + 3.0          # beside the slot
_a_, _b_ = _E.T_HEAD_IN + 0.5, _E.T_HEAD_OUT + 5.0
for _ in range(24):
    _m_ = (_a_ + _b_)/2
    if _full_box(_up, _m_, _zu): _a_ = _m_
    else: _b_ = _m_
_face = (_a_ + _b_)/2
_mouth = max(_E.st(_v.X, _v.Y)[1] for _v in _EL["xiao"].Vertices()
             if abs(_v.Z - _zu) < 3.0 and abs(_E.st(_v.X, _v.Y)[0] - _E.S_USB) < _E.USB_L/2 + 0.1)
T("USB: the mouth of the socket is flush with the outer face of the head",
  abs(_mouth - _face) <= 0.1, "mouth at t %.2f, face at t %.2f" % (_mouth, _face))
# and round the slot the face is there, because the shell of the right-angle
# plug rests on it: a ring of points is probed 3 mm from the edge of the slot,
# above and beside it (below there is the tab, which is another part)
_missing = [(ds, dz) for ds, dz in ((-1, 0), (1, 0), (0, 1), (-1, 1), (1, 1))
            if not _full_box(_E.S_USB + ds*(_E.USB_L/2 + D["Cl_usb"] + 3.0),
                              _face - 0.3,
                              _zu + dz*(_E.USB_H/2 + D["Cl_usb"] + 3.0))]
T("USB: round the slot the head is solid, for the shell of the plug",
  not _missing, "empty at %s" % _missing)

# 4) Below the socket the slot is closed by the tab of the small panel: no
# open gap in the head, from the bottom to the socket.
_open_at = []
_z_ = D["Z_floor_box"] + 0.3
while _z_ < _E.Z_USB[0] - D["Cl_usb"] - 0.3:
    _p = cq.Vector(*(_E.xy(_E.S_USB, (_E.T_HEAD_IN + _E.T_HEAD_OUT)/2) + (_z_,)))
    _sf = cq.Solid.makeSphere(0.05, _p)
    if _box.intersect(_sf).Volume() < 1e-12 and _pan.intersect(_sf).Volume() < 1e-12:
        _open_at.append("%.1f" % _z_)
    _z_ += 1.0
T("USB: below the socket the slot is closed by the tab", not _open_at,
  "open at z " + ", ".join(_open_at))

# 5) The inserts of the small panel: solid wall around them, in the box and in
# the small columns. The columns on the head side are cut flush with the
# wall, and that is where the wall round the insert is thinnest.
_thin = []
for _s_, _t_ in _E.panel_screws():
    _x, _y = _E.xy(_s_, _t_)
    # above the lead-in, which widens the seat at the mouth on purpose. The
    # height it starts from is that of the STEP, Z_SCREWS: the step is no
    # longer at mid-wall, and this check went looking for the
    # sleeve three millimetres and three lower, where there is no material.
    # It said 0% on a correct part.
    _sleeve = (cq.Workplane("XY").workplane(offset=_E.Z_SCREWS + D["Dp_leadin_insert_M3"] + 0.1)
               .center(_x, _y)
               .circle(D["D_out_insert_M3"]/2 + 1.0).circle(D["D_out_insert_M3"]/2)
               .extrude(D["L_insert_M3"] - D["Dp_leadin_insert_M3"] - 0.2).val())
    _full = _box.intersect(_sleeve).Volume()
    if _full < 0.99*_sleeve.Volume():
        _thin.append("screw %.0f,%.0f: %.0f%%" % (_s_, _t_, 100*_full/_sleeve.Volume()))
# the head column, with the M2.5 insert: it is the only one of the small panel
# that is not on the holes of the board, so it has to be asked separately
_s3c, _t3c = _E.board_head_screw()
_x, _y = _E.xy(_s3c, _t3c)
_sleeve = (cq.Workplane("XY").workplane(offset=_E.Z_BOARD - D["L_insert_M25"] + 0.1)
           .center(_x, _y).circle(D["D_hole_insert_M25"]/2 + 1.0)
           .circle(D["D_hole_insert_M25"]/2 + 0.2).extrude(D["L_insert_M25"] - 0.2).val())
_full = _pan.intersect(_sleeve).Volume()
if _full < 0.99*_sleeve.Volume():
    _thin.append("head column: %.0f%%" % (100*_full/_sleeve.Volume()))
for _s_, _t_ in _E.board_holes():

    _x, _y = _E.xy(_s_, _t_)
    _sleeve = (cq.Workplane("XY").workplane(offset=_E.Z_BOARD - D["L_insert_M2"] + 0.1)
               .center(_x, _y).circle(D["D_hole_insert_M2"]/2 + 1.0)
               .circle(D["D_hole_insert_M2"]/2 + 0.2).extrude(D["L_insert_M2"] - 0.2).val())
    _full = _pan.intersect(_sleeve).Volume()
    if _full < 0.99*_sleeve.Volume():
        _thin.append("column %.0f,%.0f: %.0f%%" % (_s_, _t_, 100*_full/_sleeve.Volume()))
T("board panel: solid wall round the inserts", not _thin, "; ".join(_thin))

# 5b) The inserts of the small panel are set FROM OUTSIDE: from inside they
# cannot be reached, above the bosses the bay is closed. One checks that the
# seat starts at the face of the stop and is empty for the whole length of the
# insert, and that below it, down to the outer face of the bottom, there is
# nothing covering it: the soldering iron must go in straight.
_closed_seats = []
for _s_, _t_ in _E.panel_screws():
    _x, _y = _E.xy(_s_, _t_)
    _rr = D["D_hole_insert_M3"]/2 - 0.3
    # The whole seat is probed, every quarter millimetre: with three probes
    # only, a seat moved further in passed all the same, because the low
    # probes fell into the lead-in and the high one into the stretch of seat
    # that was left open.
    _zz_seat = [D["Z_floor_box"] + 0.2]
    _zz = _E.Z_STOP + 0.2
    while _zz <= _E.Z_STOP + D["L_insert_M3"] - 0.2:
        _zz_seat.append(_zz)
        _zz += 0.25
    for _zz in _zz_seat:
        for _aa in (0, 120, 240):
            _p = cq.Vector(_x + _rr*math.cos(math.radians(_aa)),
                           _y + _rr*math.sin(math.radians(_aa)), _zz)
            if _box.intersect(cq.Solid.makeSphere(0.1, _p)).Volume() > 1e-12:
                _closed_seats.append("%.0f,%.0f at z %.1f" % (_s_, _t_, _zz))
                break
T("board panel: the insert seats can be reached from outside", not _closed_seats,
  "; ".join(_closed_seats))

# 5c) The cable-tie tab, on the inner face of the head: it is there, and its
# slot goes through it. The solid above and below the slot and the empty
# inside it are probed.
def _full_st(s_, t_, z_):
    return _box.intersect(cq.Solid.makeSphere(
        0.1, cq.Vector(*(_E.xy(s_, t_) + (z_,))))).Volume() > 1e-12
_wa = D["W_slot_tie_head"]
_tab_faults = []
if not _full_st(_E.TAB_S, _E.TAB_SLOT_T, _E.TAB_SLOT_Z + _wa/2 + 1.0):
    _tab_faults.append("missing above the slot")
if not _full_st(_E.TAB_S, _E.TAB_SLOT_T, _E.TAB_SLOT_Z - _wa/2 - 1.0):
    _tab_faults.append("missing below the slot")
for _ds in (-D["Th_tab_tie"]/2 + 0.3, 0.0, D["Th_tab_tie"]/2 - 0.3):
    if _full_st(_E.TAB_S + _ds, _E.TAB_SLOT_T, _E.TAB_SLOT_Z):
        _tab_faults.append("slot closed")
        break
T("head: the cable-tie tab is there and its slot goes through", not _tab_faults, "; ".join(_tab_faults))

# 5d) The cut end of the board. It used to be held by two small
# TEETH of the small panel, with a lip over the edge: the lip is born in mid
# air above the gap the board goes into, so it prints on supports, and on
# the printed part one of them broke while the board was slid in - which
# there, precisely because surfaces on supports come out oversize, went in
# with effort. Now there is a SCREW (B05 on the board grid) and two smooth
# GUIDES that square it from the sides.
#
# Three questions, and they differ from the earlier ones because the
# requirement changed: the board is no longer slid in, it is LOWERED from
# above.
_perf = _EL["perfboard"]
_guide_faults = []
_v = _perf.intersect(_pan).Volume()
if _v > 0.01:
    _guide_faults.append("board inside the small panel by %.2f mm3" % _v)
# the head column is there, under the screw hole, and its seat too
_sv3, _tv3 = _E.board_head_screw()
_xv3, _yv3 = _E.xy(_sv3, _tv3)
for _dd in (D["D_boss_cover_sensor"]/2 - 0.5, 0.0):
    _p = cq.Vector(_xv3 + _dd, _yv3, _E.Z_BOARD - 0.3)
    _full = _pan.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() > 1e-12
    if (_dd > 0) != _full:      # solid at the side, empty on the axis (the seat)
        _guide_faults.append("head column: %s at %.1f from the axis"
                    % ("material missing" if _dd > 0 else "the insert seat is not there", _dd))
# the guides stand BESIDE the board and not over it: above the face of the
# board, in line with its edge, there must be nothing
for _side, _s_b in (("inner", _E.S0 + 0.4), ("outer", _E.S1 - 0.4)):
    _tt = _E.T1 - D["L_guides_board"]/2
    _p = cq.Vector(*(_E.xy(_s_b, _tt) + (_E.Z_BOARD_TOP + 0.3,)))
    if _pan.intersect(cq.Solid.makeSphere(0.12, _p)).Volume() > 1e-12:
        _guide_faults.append("%s guide: it still covers the edge, the board cannot be lowered" % _side)
# and the board must be able to go straight down: raised by fifteen
# millimetres and lowered again it meets nothing
_up = _perf.moved(cq.Location(cq.Vector(0, 0, 15.0)))
_v = _up.intersect(_pan).Volume()
if _v > 0.01:
    _guide_faults.append("cannot be lowered from above: %.2f mm3" % _v)
T("board panel: the board is lowered between the guides and screwed at B05",
  not _guide_faults, "; ".join(_guide_faults))

# 5e) The three screws of the small panel are COUNTERSUNK, and a countersink
# wants thickness. How thick the small panel is beside each screw and how deep
# the countersink goes are measured on the solid: if the countersink reached
# the bottom, the head would poke out on the other side and the small panel
# would no longer be clamped.
_sv = []
_p_countersink = ((D["D_head_countersunk_M3"] - D["D_clear_screw_panel"])/2
            / math.tan(math.radians(D["Ang_head_countersunk"]/2)))
for _s, _t in _E.panel_screws():
    _x, _y = _E.xy(_s + 3.0, _t)
    _zz = [_z for _z in [D["Z_floor_box"] + 0.1 + 0.2*_k for _k in range(30)]
           if _pan.intersect(cq.Solid.makeSphere(0.12, cq.Vector(_x, _y, _z))).Volume() > 1e-12]
    _sp = (max(_zz) - min(_zz) + 0.2) if _zz else 0.0
    if _sp < D["Th_panel_screws"] - 0.3:
        _sv.append("screw s%.0f t%.0f: small panel %.2f thick" % (_s, _t, _sp))
    if _sp - _p_countersink < 1.5:
        _sv.append("screw s%.0f t%.0f: %.2f left below the countersink" % (_s, _t, _sp - _p_countersink))
T("board panel: at the screws there is thickness for the countersink",
  not _sv, "; ".join(_sv) + " (countersink %.2f)" % _p_countersink)

# 5f) THE COLUMNS OF THE FRONT EARS: THEY ARE GONE
# They checked that the column really reached the floor instead of stopping
# at the bottom of the bay. Removed together with the ears.

# 5g) THE RIB OF THE SPRING BOSS. Same story: the boss is a cylinder lying in
# the middle of the bay, and its lower half is an overhanging roof. Now under
# it there is a 45 degree wedge that goes down in a rib to the bottom, and
# above it the same rib rises to the roof. It is probed along the spring
# axis, in the vertical plane that contains it: from the bottom to the boss,
# and from the boss to the roof, there must be no holes.
from parameters import spring_axis as _spring_axis, s_spring_axis as _s_spring
_Qx, _Qy, _nxm, _nym, _zmm = _spring_axis()
_s_boss0 = _s_spring(D["R_seat_spring_box"]) - D["Travel_preload"]
_s_boss1 = _s_spring(D["R_out_box"])
_rib_faults = []
for _f in (0.25, 0.5, 0.75):
    _s = _s_boss0 + _f*(_s_boss1 - _s_boss0)
    _x, _y = _Qx + _nxm*_s, _Qy + _nym*_s
    # Above the boss the rib meets the roof - or, near the back, the SLOPING
    # wall of the roof chamfer (Ch_roof_box): there the underside
    # of the roof is not at Z_shoulder_box but on the inner 45 degree face,
    # which starts one wall thickness (times sqrt 2 - 1) lower than the
    # outer one. Probing up to the flat sky, the check walked out of the part
    # and called the rib broken.
    _Wc = D["Th_walls_box"]
    _z_slope = (D["Z_shoulder_box"] + _Wc - D["Ch_roof_box"] + _Wc - _Wc*math.sqrt(2.0)
               + (D["R_out_box"] - _Wc - math.hypot(_x, _y)))
    for _name, _z0, _z1 in (("below", D["Z_floor_box"] + D["Th_walls_box"] + 0.5, _zmm - 8.0),
                            ("above", _zmm + 8.0, min(D["Z_shoulder_box"], _z_slope) - 0.5)):

        for _k in range(0, max(1, int((_z1 - _z0)/2.0)) + 1):
            _z = min(_z1, _z0 + 2.0*_k)
            if _box.intersect(cq.Solid.makeSphere(
                    0.2, cq.Vector(_x, _y, _z))).Volume() < 1e-12:
                _rib_faults.append("%s the boss, at %.0f%% of its length, z %.0f"
                             % (_name, _f*100, _z))
                break
T("box: the rib ties the spring boss to the bottom and to the roof",
  not _rib_faults, "; ".join(_rib_faults))

# 5h) THE REAR EARS: THEY ARE GONE
# Here it was checked that their roof was a truncated cone without points.
# Removed together with the ears: box and collar are a single
# part and there is nothing left to screw.

# 6) The three screws can be reached with the wheel mounted, from below: in
# front of each, forty millimetres of 8 mm cylinder for the screwdriver.
_around = [("box", _box), ("collar", _col), ("arm", _arm_swept),
            ("body", cq.importers.importStep(OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step").val()),
            ("motor", _mot)]
_obstructions = []
for _s_, _t_ in _E.panel_screws():
    _x, _y = _E.xy(_s_, _t_)
    _path_cyl = cq.Solid.makeCylinder(4.0, 40.0, cq.Vector(_x, _y, D["Z_floor_box"] - 40.0 - 0.05))
    for _name, _sol in _around:
        if _sol.intersect(_path_cyl).Volume() > 0.01:
            _obstructions.append("%.0f,%.0f: %s" % (_s_, _t_, _name))
T("board panel: the screws can be reached with the wheel mounted", not _obstructions, "; ".join(_obstructions))

# 7) The bay closed towards the wheel axis. This used to be the
# INNER SKIRT: that it closed the bay, that it rose to half a millimetre under
# the arm, that over its slit nothing of the bay could be seen, and that its
# steps round the pivot left the bearing pack its clearance. The skirt is gone -
# it held the two F695ZZ as in a cup and the arm could not be put in - and the
# wall that replaces it runs from the floor into the collar, so there is no
# slit and nothing under the arm. That the bay is closed is now W1 in
# check_details.py, which costs seconds and can be broken on purpose there.
#
# What stays here is the last of the four, with the new floor instead of the
# skirt: the floor strip under the pivot, and its chamfer, leave the pivot pack
# - bearing flange, printed washer, screw head - its clearance.
_pxp, _pyp = D["R_disc"], D["Off_pivot"]
_zmb = D["Z_bottom_arm"]
_bearing = cq.Solid.makeCylinder(D["D_seat_bearings"]/2, D["H_bearings"],
                              cq.Vector(_pxp, _pyp, _zmb))
_flg = cq.Solid.makeCylinder(D["D_flange_bearing"]/2, D["Th_flange_bearing"],
                             cq.Vector(_pxp, _pyp, _zmb - D["Th_flange_bearing"]))
_tsv = cq.Solid.makeCylinder(
    D["D_head_screw_M3"]/2, D["H_head_screw_M3"],
    cq.Vector(_pxp, _pyp, _zmb - D["Th_washer_pivot"] - D["H_head_screw_M3"]))
_pivot_pack = _bearing.fuse(_flg).fuse(_tsv).fuse(_washer)
# The box is trimmed round the pivot before measuring: the distance between
# two whole solids would cost minutes.
_around_pivot = cq.Solid.makeCylinder(14.0, 24.0, cq.Vector(_pxp, _pyp, -20.0))
_box_near = _box.intersect(_around_pivot)
_v = _box_near.intersect(_pivot_pack).Volume()
T("box: the bottom lets the pivot pack through", _v <= 0.01,
  "%.2f mm3" % _v)
_d_pack = _box_near.distance(_pivot_pack)
T("box: and round the pivot it leaves it its clearance",
  _d_pack >= 0.4, "%.3f mm" % _d_pack)

# 8) The sensor bracket turns along the whole slot of the collar without
# touching collar and box. At 60 degrees the rear ear C stopped it after a
# tenth of a degree; moved to 67, it must let it turn all the way.
_hits_st = []
for _g in (-D["Halfw_slot_collar"], 0.0, D["Halfw_slot_collar"]):
    _sr = _st.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _g)
    for _name, _sol in (("collar", _col), ("box", _box)):
        _v = _sr.intersect(_sol).Volume()
        if _v > 0.01:
            _hits_st.append("%+.1f degrees: %.2f mm3 in the %s" % (_g, _v, _name))
T("sensor bracket: it turns along the whole slot without touching collar and box",
  not _hits_st, "; ".join(_hits_st))

# --- the sensor cover and the cable route -----------------------------------
# The module was uncovered and its cable dangled. Now there is a cover, and it
# has a constraint that comes before all the others: it must rest on the
# BRACKET and never on the board. Anything pressing on the board moves
# H_rest_module, that is it changes the air gap - the hardest-won number of
# the project - and nobody says so: one finds out looking at a wrong angle
# reading six months later. They are two different questions and are measured
# separately, as for the bearing flange: that today they do not touch, and
# that when they do touch, what touches is the bracket.
from drawings import (cover_bosses as _cover_bosses, boss_centre as _boss_centre)


def _rotate_xy(x, y):
    """From the unrotated frame of the bracket to that of the project."""
    _a = math.radians(D["Ang_bracket_sensor"])
    return (x*math.cos(_a) - y*math.sin(_a), x*math.sin(_a) + y*math.cos(_a))


from drawings import (board_outline as _board_outline, bracket_arms as _brs,

                      rotate_points as _rotate, module_angle as _angmod,
                      module_support_pads as _padmod,
                      cover_skirt_radius as _r_skirt,
                      free_pads as _free_pads)
from solids_sensor import (support_outside_hub as _pad_support,
                            Z_FACE_IN as _ZD, Z_FACE_OUT as _ZF,
                            Z_PLATE as _ZP, pol as _polr, on_arm as _ub, Rg as _Rg)
_cover_s = cq.importers.importStep(OUT + "sensor_cover.step").val()
_a0 = D["Ang_bracket_sensor"]
_module_board = (cq.Workplane("XY").workplane(offset=_ZD).polyline(_board_outline(0.0)).close()
            .extrude(D["Th_board_module"]).val()
            .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _a0))
_v = _cover_s.intersect(_st).Volume()
T("sensor cover: it does not interpenetrate the bracket", _v <= 0.01, "%.2f mm3" % _v)
_v = _cover_s.intersect(_module_board).Volume()
T("sensor cover: it does not touch the module board", _v <= 0.01, "%.2f mm3" % _v)
# the real question: pushed down, what does it end up on?
_down = _cover_s.moved(cq.Location(cq.Vector(0, 0, -0.05)))
_vs, _vb = _down.intersect(_st).Volume(), _down.intersect(_module_board).Volume()
T("sensor cover: it rests on the bracket, not on the board",
  _vs > 0.01 and _vb <= 0.01,
  "pushed by 0.05: bracket %.2f mm3, board %.2f mm3" % (_vs, _vb))

# And it must not go into the optical envelope any further than the bracket
# does: the usual rule is "in there only with the small hub", and a cover
# that closed the whole circle would go into it by sixteen millimetres
# instead of seven. The distance is measured EXACTLY, with the distance
# between solids, and not by taking the nearest vertex of the intersection: on
# a curved surface the nearest point is almost never a vertex, and with that
# method an untrimmed skirt - a ring that went into the envelope by sixteen
# millimetres instead of seven - passed the check without anybody noticing.
# Tested by breaking it.
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
# The axis is Off_hole_optical, not a number: it was -48 written by hand, and
# when the optical axis moved to the hole circle of the filter disc
# (45.67) this check would have kept measuring from the old axis.
_axis_line = cq.Edge.makeLine(cq.Vector(-D["Off_hole_optical"], 0, -200),
                              cq.Vector(-D["Off_hole_optical"], 0, 200))
def _from_optical_axis(sol):
    _d = BRepExtrema_DistShapeShape(sol.wrapped, _axis_line.wrapped)
    _d.Perform()
    return _d.Value()
# And the yardstick is not the bracket but the BOARD: the module must be on
# axis with the magnet, so it already goes in further than the small hub, and
# a cover that stopped before it would leave uncovered precisely the edge it
# protects.
_d_st, _d_cover = _from_optical_axis(_st), _from_optical_axis(_cover_s)
_d_board = _from_optical_axis(_module_board)
T("sensor cover: in the optical envelope it goes no further than the board",
  _d_cover >= _d_board - 0.01,
  "board %.2f mm from the axis, cover at %.2f (bracket %.2f)" % (_d_board, _d_cover, _d_st))

# And it must really cover it. The first cover was trimmed to the outline of
# the bracket: at r 16 the bracket is made of the arms only, 8 wide, so of the
# skirt two fragments were left and the module was uncovered on both sides.
# One looks from above: every point of the edge of the board must have the
# cover above it.
_uncovered = []
for _px, _py in _rotate(_board_outline(0.0), D["Ang_bracket_sensor"]):
    _column = (cq.Workplane("XY").workplane(offset=_ZP).center(_px, _py)
                .circle(0.3).extrude(D["Th_cover_sensor"]).val())
    if _cover_s.intersect(_column).Volume() < 0.5*_column.Volume():
        _uncovered.append("%.1f,%.1f" % (_px, _py))
T("sensor cover: it covers the whole edge of the board",
  len(_uncovered) <= 2, "%d points uncovered of %d" % (len(_uncovered), len(_board_outline(0.0))))

# The bosses must be BORN on the arm. At r 40 the arm is at the low height,
# not at the high one past the step: dimensioning them on the wrong face they
# were left hanging in the air three millimetres above the part, and the
# solid did not complain - they were simply two more detached pieces inside
# the same file, which no volume measure tells apart from a whole part.
# Counting the solids tells them apart, and has no thresholds to tune.
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
def _count_solids(sol):
    _e, _n = TopExp_Explorer(sol.wrapped, TopAbs_SOLID), 0
    while _e.More():
        _n += 1
        _e.Next()
    return _n
_n = _count_solids(_st)
T("sensor bracket: it is one single piece, no bosses in the air", _n == 1, "%d solids" % _n)

# Attached is not enough, though: the cover screw pushes down on the boss,
# and on the cable arm the boss bridges over the wire lane, which takes 3.5 of
# the 8 mm of arm away from it. Little more than a third of the base is left
# to bear, and how much must be said: ten square millimetres of ASA hold
# 600 N in compression, while an M2.5 tightened by hand makes 200 at most.
_weak = []
for _phi, _transv in _cover_bosses():
    _x, _y = _rotate_xy(*_boss_centre(_phi, _transv))
    _root = (cq.Workplane("XY").workplane(offset=_ZD - 0.3).center(_x, _y)
               .circle(D["D_boss_cover_sensor"]/2 - 0.2).extrude(0.3).val())
    _area = _st.intersect(_root).Volume()/0.3
    if _area < 10.0:
        _weak.append("%.0f degrees: %.1f mm2" % (_phi, _area))
T("sensor bracket: the bosses rest on the arm", not _weak, "; ".join(_weak))

# The 104 capacitor under the board. It is the tallest component of the
# module and does not fit in the three tenths that the module recess leaves:
# on the test feet one had already run into it, and the board sat on it
# instead of on the pads - that is it measured an air gap that was not the
# right one. On the real bracket the same defect stayed for months without
# anybody seeing it, and it is the final part. Two separate questions: that
# the hole is there and goes through, and that it has not eaten the ring that
# centres the bracket on the magnet.
_rs, _ys = D["R_relief_capacitor"], D["Halfw_relief"]
_capacitor = (cq.Workplane("XY").workplane(offset=_ZD - D["H_capacitor_module"])
         .polyline(_rotate([(_rs, -_ys), (D["L_board_module"]/2, -_ys),
                           (D["L_board_module"]/2, _ys), (_rs, _ys)], _angmod()))
         .close().extrude(D["H_capacitor_module"]).val()
         .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _a0))
_v = _st.intersect(_capacitor).Volume()
T("sensor bracket: the 104 capacitor does not touch the bracket", _v <= 0.01,
  "%.2f mm3 (it stands %.1f below the board)" % (_v, D["H_capacitor_module"]))
# and on the other side it must not hit the face of the body, which the
# bracket rests on: the hole goes through, so the capacitor comes out below it
_clearance = _capacitor.BoundingBox().zmin - D["H_body"]
T("sensor bracket: the capacitor stays clear of the face of the body",
  _clearance >= 0.3, "%.2f mm" % _clearance)

# The centring ring on the magnet must not have been eaten by the relief: the
# magnet reaches 2.30 above the face and it is the ring that centres the
# bracket.
_h_mag = (D["Th_spacer_magnet"] + D["Th_magnet"] + D["Th_glue_stack_magnet"])
_eaten = []
for _r in (D["D_hole_magnet_printing"]/2 + 0.5, _rs - 0.5):
    _x, _y = _polr(_r, _a0 + _angmod())
    _full = (cq.Workplane("XY").workplane(offset=D["H_body"]).center(_x, _y)
              .circle(0.3).extrude(_h_mag).val())
    if _st.intersect(_full).Volume() < 0.95*_full.Volume():
        _eaten.append("r %.1f" % _r)
T("sensor bracket: the relief does not eat into the centring ring", not _eaten,
  "holed at " + "; ".join(_eaten))

# The third rest. The board sat on two pads only, in a row: it could rock
# about that line, and every rocking is air gap changing. On the side of the
# three large unused pads the pad is twice as wide - there is no component
# above it - and this is the check that that width is really on the part.
# And an angular sector is not measured, which on paper covered them and in
# millimetres did not: one probes under the THREE PADS, one by one, where they
# really fall. Stopped at the small hub (7.45) the pad touched none of them,
# because they are at 7.50 and 7.92.
_unsupported = []
for _px, _py in _free_pads():
    _a = math.radians(D["Ang_bracket_sensor"])
    _c, _s = math.cos(_a), math.sin(_a)
    _probe_cyl = (cq.Workplane("XY").workplane(offset=_ZD - 0.6)
            .center(_px*_c - _py*_s, _px*_s + _py*_c)
            .circle(0.8).extrude(0.6).val())
    if _st.intersect(_probe_cyl).Volume() < 0.4*_probe_cyl.Volume():
        _unsupported.append("r %.2f" % math.hypot(_px, _py))
T("sensor bracket: the three free pads have the support under them",
  not _unsupported, "nothing under: " + "; ".join(_unsupported))

# The THIRD rest, on the back of the V. It is not enough that there is
# material: the material was there already, but lowered by the 1.2 mm recess,
# that is the board did not touch it. Here one asks that the solid reaches UP
# TO THE REST PLANE, probing the last three tenths under it: if that sector
# became recess again, the probe would find air and this check would sound.
# The reason the third rest exists lies in the centre lines of the other two,
# 135 and -45 degrees: they are opposite, that is on a single line, and on
# two rests in a row the board rocks. It was seen on the part, not by a check:
# from here on the check sees it too.
from drawings import v_back as _v_back
_ang_back = _v_back() + D["Ang_bracket_sensor"]
_r_back = (D["R_pad_back_v"] + hub_radius())/2
# The probe is small on purpose: where the rotator pinches the pad, the raised
# frame is the 45 hundredths between R_pad_back_v and the small hub wide, and
# a probe bigger than it would fish in the recess beside it and would sound on
# a correct part. Same reason as the margins that live in the part and not in
# the thresholds.
_no_back = []
for _dg in (-D["Ang_pad_back_v"] + 8, 0.0, D["Ang_pad_back_v"] - 8):
    _x, _y = _polr(_r_back, _ang_back + _dg)
    _probe_cyl = (cq.Workplane("XY").workplane(offset=_ZD - 0.3).center(_x, _y)
            .circle(0.15).extrude(0.3).val())
    if _st.intersect(_probe_cyl).Volume() < 0.9*_probe_cyl.Volume():
        _no_back.append("%+.0f degrees" % _dg)
T("sensor bracket: the board has the third rest on the back of the V",
  not _no_back,
  "at r %.2f the solid up to the rest plane is missing at " % _r_back
  + "; ".join(_no_back))

# ...and the support must not come out from under the board on the other
# side. The sector that generates it is 50 degrees wide and reaches r 9, more
# than half the diameter of the board: without the trim on the outline it
# would stick out past the edge, and end up in the air the cover skirt needs.
_sup = _pad_support(D["H_body"], _ZD - D["H_body"])
_outside_board = _sup.cut(cq.Workplane("XY").workplane(offset=D["H_body"] - 1)
                      .polyline(_board_outline(0.0)).close().extrude(20.0)).val().Volume()
T("sensor bracket: the support does not overflow from under the board",
  _outside_board <= 0.01, "%.2f mm3 outside the outline" % _outside_board)

# The rule "inside the rotator envelope only with the small hub" is already
# in check_dimensions, but there it is measured on the 2D PROFILE, and the
# pad support is not in the profile: it is born in 3D, afterwards. Widening
# it to 50 degrees the bracket had come down from 40.55 to 39.58 from the
# optical axis - a millimetre inside the rotator - and no check had noticed.
# This one measures the solid.
_d_hub = D["Off_hole_optical"] - hub_radius()
T("sensor bracket: not even the support goes into the rotator further than the small hub",
  _d_st >= _d_hub - 0.01,
  "bracket %.2f from the axis, small hub alone %.2f" % (_d_st, _d_hub))

# The cable route. The cable arrives sheathed and lies in the saddle, inside
# the pad. A stub of cable LAID ON THE BOTTOM of the saddle is built and two
# different things are asked: that it fits, and that the saddle holds it. The
# second is the only one that says anything about the depth: measuring only
# the first, putting the cable at the height the saddle itself imposes, is a
# check that can never fail - tested, and indeed it did not fail.
_phc = max(_brs()) + _a0
_ux, _uy, _nx, _ny = _ub(_phc)
def _cable_stub(_dl):
    _z = _ZD - D["Dp_channel_cable"] + D["D_cable_sensor"]/2
    _x = D["R_tie_cable"]*_ux + _nx*_dl - _ux*D["L_pad_tie"]/2
    _y = D["R_tie_cable"]*_uy + _ny*_dl - _uy*D["L_pad_tie"]/2
    return cq.Solid.makeCylinder(D["D_cable_sensor"]/2, D["L_pad_tie"],
                                 cq.Vector(_x, _y, _z), cq.Vector(_ux, _uy, 0))
_v = _st.intersect(_cable_stub(0.0)).Volume()
T("sensor bracket: the cable lies in the saddle", _v <= 0.01, "%.2f mm3" % _v)
_pushed = min(_st.intersect(_cable_stub(_d)).Volume() for _d in (-1.0, 1.0))
T("sensor bracket: the saddle holds the cable sideways", _pushed > 0.01,
  "pushed by 1 mm it touches the wall by %.2f mm3" % _pushed)

# The cable tie is the cable clamp, and without it the cable pulls on the pads
# of the module, which are the weak link of the whole chain. Its slots must
# go through - the first ones were rectangles aligned to the world, placed
# 5.25 from the centre line of an arm 8 wide, and did not touch the part.
# It is not enough to look that the tie goes through: a slot placed OUTSIDE
# the part lets it through too, and the check written only that way would
# have passed it - it is exactly the error that was there, two slots 5.25
# from the centre line of an arm 8 wide. So one asks a thing and its reverse:
# inside the slot the empty, just outside the solid the tie pulls on.
_blind_slots = []
for _side in (-1, 1):
    _off = _side*D["Cd_slots_tie"]/2
    def _probe(_d, _r):
        _x = D["R_tie_cable"]*_ux + _nx*(_off + _d)
        _y = D["R_tie_cable"]*_uy + _ny*(_off + _d)
        return (cq.Workplane("XY").workplane(offset=D["H_body"] - 0.5).center(_x, _y)
                .circle(_r).extrude(_ZD - D["H_body"] + 1).val())
    _inside = _probe(0.0, 0.4)
    if _st.intersect(_inside).Volume() > 0.01:
        _blind_slots.append("side %+d: blocked" % _side)
    _outside = _probe(_side*(D["H_slot_tie"]/2 + 0.9), 0.4)
    _expected = _outside.Volume()*(_ZD - D["H_body"])/(_ZD - D["H_body"] + 1)
    if _st.intersect(_outside).Volume() < 0.9*_expected:
        _blind_slots.append("side %+d: no wall outside, the slot is in empty space" % _side)
T("sensor bracket: the cable tie goes through and has something to pull on", not _blind_slots,
  "; ".join(_blind_slots))

# And the four unsheathed wires must be able to get from the tie to the gap
# in the skirt. Two separate questions, and the second is the new one.
#
# 1) the lane is there and is not blocked.
# 2) THE LANE IS OPEN ON TOP along its whole length. Before, the cover boss
#    sat on its axis and bridged it: the wires went through, but to put them
#    in one had to THREAD them from one end, and the sensor cable arrives with
#    the JST connector already crimped, which does not go into a 3.5 x 2
#    tunnel. So the boss moved to the side.
#    The earlier check could not notice: it asked precisely that the lane run
#    UNDER the boss, that is it guarded the defect instead of the
#    requirement.
_r_int = D["R_skirt_cover"] + D["Th_skirt_cover"]/2
_plugged, _covered = [], []
for _r in [_r_int + 1.0 + _k for _k in range(0, int(D["R_tie_cable"] - _r_int - 2))]:
    _x, _y = _polr(_r, _phc)
    _gap = (cq.Workplane("XY").workplane(offset=_ZD - D["H_passage_wires"] + 0.1)
             .center(_x, _y).circle(0.6).extrude(D["H_passage_wires"] - 0.2).val())
    if _st.intersect(_gap).Volume() > 0.01:
        _plugged.append("r %.0f" % _r)
    _above = (cq.Workplane("XY").workplane(offset=_ZD + 0.2).center(_x, _y)
              .circle(0.6).extrude(D["H_boss_cover_sensor"] - 0.4).val())
    if _st.intersect(_above).Volume() > 0.01:
        _covered.append("r %.0f" % _r)
T("sensor bracket: the wires have their lane up to the gap", not _plugged,
  "blocked at " + "; ".join(_plugged))
T("sensor bracket: the wire lane is open on top, no bridge",
  not _covered, "covered at " + "; ".join(_covered))


# --- the pivot hub: how much is born in the air, and who reaches it with the iron
# The flank of the hub was a flat shoulder: 263 mm2 of roof on supports, in an
# orientation in which that face looks at the bed. Now it is a cone, and of
# those 263 there are 39 left.
#
# BUT THE SUPPORT THERE REMAINS, and that is what the earlier check did not
# see: it measured the ANGLE of the flank - an attribute of the shape - instead
# of the property that matters, that is that the hub prints without support.
# The angle was right while the defect was there. In the orientation of the
# collar the hub is a protrusion that points TOWARDS the bed, so its first
# layer is the pad at the top, which floats a millimetre and a half from the
# band: a cone with its tip towards the bed does not stand however steep it
# is, because it is the tip that is the first layer. The section shows it.
#
# THE ROAD DISCARDED, written down so that it is not tried again in six
# months: to make the hub grow from material already printed it has to be
# filleted to the band of the collar, and the fillet has to cover the 10.5 mm
# between the band and the outer edge of the pad. At 45 degrees - the minimum
# that stands - it wants 10.5 mm of drop, but above the top of the hub there
# are SIX: at z 16.00 the box comes in, measured on its solid. It would fit
# only by bringing the mouth of the insert from z 10 to z 5, at the bottom of
# a vertical channel for the tip of the iron, with the screw from M3x20 to
# M3x16. Rejected: the present shape stays and so does the support - an
# 18 mm turret under a Ø9 disc - because 39 mm2 are still seven times less
# than the 263 of the start.
#
# What is guarded is therefore that that area DOES NOT GROW. The limit is
# ABSOLUTE and does not descend from any dimension of the hub: a limit derived
# from the pad would go down together with the defect and would no longer say
# anything.
_pxm = D["R_pivot"]*math.cos(math.radians(D["Ang_pivot"]))
_pym = D["R_pivot"]*math.sin(math.radians(D["Ang_pivot"]))
# The plane of the bed is not written by hand: in the declared orientation -
# rear flange on the bed - the bed IS the highest face of the part, so it is
# taken from the SOLID. Written by hand it would come loose from the collar at
# the first dimension that changes its height, and the check would measure a
# bed that is no longer there.
Z_BED_COLLAR = _col.BoundingBox().zmax


# How far the rest of the previous layer can be for the layer to close by
# itself: it is the span of a short bridge. A millimetre and a half keeps in
# the bottoms of seats and the rings at the bottom of a well - a hole that
# narrows prints - and leaves out what has NOTHING above it, at any distance,
# which is the case of the top of the support.
_GRIP = 1.5


def _born_in_air(solid, inside, z_bed, cx, cy, radius_max, incl_max=45.0):
    """Area of the faces that look at the bed, are flatter than incl_max and
    have no material above them: they are the ones born in the air that want
    support. The SOLID is probed above and below each face, at twenty-five
    points, and the decision is by majority: with a single probe at the
    centroid a ring-shaped face was judged by its hole."""
    tot, det = 0.0, []
    for _f in solid.Faces():
        try:
            _n = _f.normalAt()
        except Exception:
            continue
        if _n.z <= 0.05:                      # looks the other way: it is a floor
            continue
        if 90.0 - math.degrees(math.asin(min(1.0, abs(_n.z)))) > incl_max:
            continue                          # steep enough to stand
        _c = _f.Center()
        if math.hypot(_c.x - cx, _c.y - cy) > radius_max:
            continue
        if _c.z >= z_bed - 0.05:           # rests on the bed: it is not in the air
            continue
        # INSIDE THE ROOF SLAB of the one-piece part: the collar is not
        # printed alone, and a face of collar.step that lies in
        # the slab Z_shoulder_box..+Th_walls_box is buried in the roof, not in
        # the air. It matters because the column of the pivot is a plain
        # cylinder and its Ø21 top sits half way into the slab.
        if D["Z_shoulder_box"] + 0.05 < _c.z < D["Z_shoulder_box"] + D["Th_walls_box"] - 0.05:
            continue
        _n_probes = _up = 0
        _b = _f.BoundingBox()
        for _ux in (0.15, 0.35, 0.5, 0.65, 0.85):
            for _uy in (0.15, 0.35, 0.5, 0.65, 0.85):
                _x = _b.xmin + _ux*(_b.xmax - _b.xmin)
                _y = _b.ymin + _uy*(_b.ymax - _b.ymin)
                if not inside(_x, _y, _c.z - 0.15):
                    continue                  # outside the face
                _n_probes += 1
                # the previous layer is the one TOWARDS THE BED. It rests if
                # there is material there, even just beside it within
                # _GRIP: a hole that narrows, or a face that ends against a
                # wall that goes on, close by themselves on a short bridge and
                # do not want support. Without this, the bottom of every
                # insert seat came out as needing support.
                _rests = inside(_x, _y, _c.z + 0.4)
                if not _rests:
                    for _k in range(8):
                        _aa = 2*math.pi*_k/8
                        if inside(_x + _GRIP*math.cos(_aa),
                                  _y + _GRIP*math.sin(_aa), _c.z + 0.4):
                            _rests = True
                            break
                if not _rests:
                    _up += 1
        if _n_probes and _up*2 >= _n_probes:
            tot += _f.Area()
            det.append("%.1f mm2 at z %.2f" % (_f.Area(), _c.z))
    return tot, det


_air_area, _det_air = _born_in_air(_col, _in_col, Z_BED_COLLAR, _pxm, _pym, 13.0)
# The 39 are the pad at the top; the 7.9 at z 6.5 are the ring at the bottom
# of the insert seat, that is a hole that narrows: that one wants no support,
# it closes by itself on a millimetre and a half of bridge. With the flat
# shoulder of before one goes back above 270.
T("collar: the pivot hub does not grow what is born in the air",
  _air_area <= 55.0, "%.1f mm2 (%s)" % (_air_area, "; ".join(_det_air) or "nothing"))


def _r_hub(z):
    """How far the material of the hub reaches at that height, from its axis."""
    r = 12.0
    while r > 1.0:
        p = cq.Vector(_pxm + r, _pym, z)
        if _col.intersect(cq.Solid.makeSphere(0.05, p)).Volume() > 1e-12:
            return r + 0.05
        r -= 0.02
    return None


# THE COLUMN IS ONE CYLINDER from the arm to the roof (not flared). Measured on the solid at five heights: the radius must be the
# same everywhere, D_hub_pivot / 2. Put the cone back - or any taper - and the
# top readings drop and this sounds.
_zc0 = D["Z_top_arm"] + D["Setback_face_hub"] + 0.6
_zc1 = D["Z_top_support_pivot"] - 0.6
_readings = []
for _k in range(5):
    _zk = _zc0 + (_zc1 - _zc0)*_k/4.0
    _readings.append((_zk, _r_hub(_zk)))
_deviation = max(abs((r or 0.0) - D["D_hub_pivot"]/2) for _, r in _readings)
T("collar: the pivot column is one continuous cylinder up to the roof",
  _deviation <= 0.1,
  "radius read " + ", ".join("%.2f at z %.1f" % ((r or 0.0), z) for z, r in _readings)
  + " (expected %.2f)" % (D["D_hub_pivot"]/2))

# And at the top the wall round the CHANNEL of the soldering iron is left: it
# is the one that guides the tip as it goes down, and it is also all the
# material there is up there. Absolute minimum: a millimetre and a half.
# Before, this check measured the wall round the insert, which now sits ten
# millimetres lower in the middle of the solid: it looked at a spot where
# there is nothing left to guard.
_r_top = _r_hub(D["Z_top_support_pivot"] - 0.15)
_wall = (_r_top - (D["D_tip_iron"] + D["Cl_tip_iron"])/2) if _r_top else -99.0
T("collar: at the top of the support the wall round the channel is left",
  _wall >= 1.5, "wall %.2f mm (top Ø%.2f, channel Ø%.2f)"
  % (_wall, 2*(_r_top or 0), D["D_tip_iron"] + D["Cl_tip_iron"]))

# --- the fillet is really there, and the support is under the roof of the bay
# The fillet is checked ON THE SOLID and at the point that defines it: the
# centre of the fillet arc is at R from the support and at R from the band,
# so at distance R from it the material must be there, and at R plus a hair
# no longer. Removing the fillet the first point falls into empty space and
# the check sounds.
_Rrg = D["R_fillet_support_pivot"]
_Restg = D["R_out_collar"]
_dg = math.hypot(_pxm, _pym)
_ug = (_pxm/_dg, _pym/_dg)
_rmg = D["D_hub_pivot"]/2
_missing = []
for _side in (+1, -1):
    _wg = (-_ug[1]*_side, _ug[0]*_side)
    _ag = ((_Restg + _Rrg)**2 - (_rmg + _Rrg)**2 + _dg*_dg)/(2*_dg)
    _hg = math.sqrt(max(0.0, (_Restg + _Rrg)**2 - _ag*_ag))
    _Cg = (_ag*_ug[0] + _hg*_wg[0], _ag*_ug[1] + _hg*_wg[1])
    # the direction in which the fillet puts material: towards the vertex of
    # the angle, that is on the side opposite the centre of the fillet with
    # respect to the band
    _vx, _vy = _Cg[0]/math.hypot(*_Cg), _Cg[1]/math.hypot(*_Cg)
    # the material of the fillet is OUTSIDE the fillet circle, on the side
    # where the support crosses the band: inside that circle there is empty
    # space, and it is precisely the concavity. So one probes along the
    # direction going from the centre of the fillet to the crossing point,
    # just outside and just inside. The first version of this check probed
    # inside expecting solid, and sounded on the correct part.
    _a2g = (_Restg*_Restg - _rmg*_rmg + _dg*_dg)/(2*_dg)
    _h2g = math.sqrt(max(0.0, _Restg*_Restg - _a2g*_a2g))
    _Xg = (_a2g*_ug[0] + _h2g*_wg[0], _a2g*_ug[1] + _h2g*_wg[1])
    _lx, _ly = _Xg[0] - _Cg[0], _Xg[1] - _Cg[1]
    _ln = math.hypot(_lx, _ly)
    _lx, _ly = _lx/_ln, _ly/_ln
    # half way up the column, where the fillet is fully formed
    _zg = (D["Z_top_arm"] + D["Setback_face_hub"] + D["Z_top_support_pivot"])/2
    _full_outside = _in_col(_Cg[0] + _lx*(_Rrg + 0.3), _Cg[1] + _ly*(_Rrg + 0.3), _zg)
    _empty_inside = _in_col(_Cg[0] + _lx*(_Rrg - 0.3), _Cg[1] + _ly*(_Rrg - 0.3), _zg)
    if not _full_outside:
        _missing.append("side %+d: no material just outside the arc" % _side)
    if _empty_inside:
        _missing.append("side %+d: material inside the arc, the fillet is not hollowed" % _side)
T("collar: the fillet joins the pivot support to the band",
  not _missing, "; ".join(_missing) or
  "R %.1f, tangent by construction on both sides" % _Rrg)

# And the top of the support is under the roof of the bay with its air. It is
# a clearance between TWO PARTS, so both solids are measured: the top of the
# support on the collar, the roof on the box. The declared number is not read
# back from the parameters, which is the way of noticing nothing.
_z_top_real = None
_zz = D["Z_top_support_pivot"] + 2.0
while _zz > D["Z_mouth_insert_pivot"]:
    if _in_col(_pxm, _pym + (D["D_tip_iron"] + D["Cl_tip_iron"])/2 + 0.6, _zz):
        _z_top_real = _zz
        break
    _zz -= 0.05
_in_box = _inside_factory(cq.importers.importStep(OUT + out_subdir("box") + "box.step").val())
_z_sky = None
_zz = D["Z_top_support_pivot"] - 2.0
while _zz < D["Z_top_support_pivot"] + 6.0:
    if _in_box(_pxm, _pym, _zz):
        _z_sky = _zz
        break
    _zz += 0.05
# The support is a FULL COLUMN that runs into the roof: the check that it stayed Free_assembly_compartment under the sky -
# the room to slide the box on, which no longer slides on - became its
# opposite. Now: the column top, measured on the collar, lies INSIDE the roof
# slab, above its underside and below its top - fused, not touching, not
# standing out of it.
_q_under, _q_top = D["Z_shoulder_box"], D["Z_shoulder_box"] + D["Th_walls_box"]
T("collar: the pivot support goes into the roof",
  _z_top_real is not None and _q_under + 0.2 <= _z_top_real <= _q_top - 0.2,
  "top at z %.2f, roof from %.2f to %.2f" % (_z_top_real or -99, _q_under, _q_top))

# And the tip of the soldering iron gets there STRAIGHT. The seat of an insert
# is drawn thinking of the tool that sets it: here the mouth is at the bottom
# of the bay where the arm turns, and the band of the collar passes six
# millimetres from it. The cylinder of the tip is probed from the mouth to
# outside the part.
#
# WATCH THE SEQUENCE: above this mouth the box passes at z 16, so the pivot
# insert must be set ON THE BARE COLLAR. Once the box is mounted it can no
# longer be reached, and it is not the collar that says so - it is another
# part.
# with the clearance: what must pass free is not the bare tip, it is the tip
# plus Cl_tip_iron, or going down it rubs and melts the wall
_rp_iron = (D["D_tip_iron"] + D["Cl_tip_iron"])/2
_obstructed = []
_z = D["Z_mouth_insert_pivot"] + 0.3
while _z <= Z_BED_COLLAR:
    for _k in range(12):
        _a = 2*math.pi*_k/12
        for _rr in (_rp_iron*0.5, _rp_iron - 0.05):
            if _in_col(_pxm + _rr*math.cos(_a), _pym + _rr*math.sin(_a), _z):
                _obstructed.append("z %.1f at r %.1f" % (_z, _rr))
                break
    _z += 0.5
T("collar: the tip of the soldering iron reaches the pivot insert straight",
  not _obstructed, "Ø%.1f obstructed at %s" % (D["D_tip_iron"] + D["Cl_tip_iron"],
                                             "; ".join(_obstructed[:4])))

# --- every printed part comes out in ONE SINGLE PIECE -----------------------
# The collar came out in THREE detached bodies - 45.0 cm3, 7.8 and 0.14 - and
# nobody noticed for days: the volume measures do not change, the
# interferences do not complain, and even the assembly looks right, because
# the detached pieces are exactly where they must be. It showed only opening
# the STEP.
#
# The defect came from the cut that widens the throat: it reached Re+1, that
# is beyond the cylindrical band, and instead of setting a face back it
# severed the flange from the rest all the way round. The labyrinth rib, which
# is born on that face, was left in the air on its own.
#
# Counting the bodies has no thresholds to tune and it is the check that was
# missing. Where the bodies are more than one it is written HOW MANY and why:
# the magnet spacer is printed in four copies on purpose, being a half-gram
# part that gets lost.
_EXPECTED_BODIES = {
    # box_collar in place of collar and box: those are no longer printed
    # parts but the two regions of this one, and they are in out/references/.
    "box_collar": 1, "arm": 1, "clutch_hub": 1, "clutch_tyre": 1,
    "sensor_bracket": 1, "sensor_cover": 1, "board_panel": 1,
    "spring_cup": 1, "pivot_washer": 1,
    "front_gasket": 1, "rear_gasket": 1,
    "magnet_spacer": 4,          # four copies, it is a part that gets lost
}
_broken_parts = []
for _name, _how_many in sorted(_EXPECTED_BODIES.items()):
    _f = OUT + _name + ".step"
    if not os.path.exists(_f):
        _broken_parts.append("%s: the file is missing" % _name)
        continue
    _n_bodies = _count_solids(cq.importers.importStep(_f).val())
    if _n_bodies != _how_many:
        _broken_parts.append("%s: %d bodies instead of %d" % (_name, _n_bodies, _how_many))
T("the parts to print each come out in one single piece", not _broken_parts,
  "; ".join(_broken_parts) or "%d parts checked" % len(_EXPECTED_BODIES))

# --- the co-printed collar: the two materials do not overlap ----------------
# It serves the IDEX, which prints ASA and TPU together. The bodies stay
# separate and named by material - a slicer takes them that way, one body per
# extruder - and above all they do NOT interpenetrate: the gasket fills the
# groove the collar has already dug and stands out by half a millimetre, which
# is the lip to squeeze. Two overlapping materials reach the slicer as a mess,
# and only the print would notice.
_coprinted_f = OUT + "box_collar_coprinted.step"
if not os.path.exists(_coprinted_f):
    T("co-printed part: it is there, with the three bodies", False, "the file is missing")
else:
    _n_cost = _count_solids(cq.importers.importStep(_coprinted_f).val())
    T("co-printed part: it is there, with the three bodies", _n_cost == 3,
      "%d bodies (the part plus the two gaskets)" % _n_cost)
    _in_gasket = []
    for _ng in ("front_gasket", "rear_gasket"):
        _g = cq.importers.importStep(OUT + _ng + ".step").val()
        _in_g = _inside_factory(_g)
        _bg = _g.BoundingBox()
        _seen = _overlapping = 0
        _i = 0
        while _i < 4000 and _seen < 400:
            _i += 1
            _xg = _bg.xmin + (_bg.xmax - _bg.xmin)*((_i*0.6180339887) % 1.0)
            _yg = _bg.ymin + (_bg.ymax - _bg.ymin)*((_i*0.3819660113) % 1.0)
            _zg = _bg.zmin + (_bg.zmax - _bg.zmin)*((_i*0.2360679775) % 1.0)
            if not _in_g(_xg, _yg, _zg):
                continue
            _seen += 1
            if _in_col(_xg, _yg, _zg):
                _overlapping += 1
        if _seen < 20:
            _in_gasket.append("%s: only %d probes inside, blind check" % (_ng, _seen))
        elif _overlapping:
            _in_gasket.append("%s: %d points of %d inside the collar too"
                               % (_ng, _overlapping, _seen))
    T("co-printed collar: ASA and TPU do not overlap", not _in_gasket,
      "; ".join(_in_gasket) or "the two gaskets sit in their grooves")

# --- the throat of the collar does not pinch the body -----------------------
# The throat - the distance between the inner faces of the two flanges - was
# drawn 23.00, that is EXACTLY the height of the wheel body. Zero clearance on
# a printed part, and what is more on a face that is born on supports:
# measured on the printed collar it was 22.8 on average and 22.3 on
# the ridges, so the collar had to be forced on. Now the front face is set
# back and what locates is the rear flange, which is a clean face.
#
# It is measured on the SOLID, scanning along z at a radius where both
# flanges are there and there are neither bosses nor grooves. The minimum is
# ABSOLUTE, three tenths: it does not descend from Cl_groove_collar, or it
# would move together with the defect.
_a_throat = (D["Ang_bracket_sensor"] + D["Ang_pivot"]) / 2      # away from bosses and slots
_r_throat = (D["R_in_flange_collar"] + D["R_out_collar"]) / 2
_xg = _r_throat*math.cos(math.radians(_a_throat))
_yg = _r_throat*math.sin(math.radians(_a_throat))


def _full_col(z):
    return _col.intersect(cq.Solid.makeSphere(0.02, cq.Vector(_xg, _yg, z))).Volume() > 1e-12


_zf, _zr = None, None
_zz = -D["Th_flange_collar"] + 0.1
while _zz < D["H_body"] + D["Th_flange_collar"]:
    if _full_col(_zz):
        if _zz < D["H_body"]/2:
            _zf = _zz                      # the last solid of the front flange
        elif _zr is None:
            _zr = _zz                      # the first solid of the rear one
    _zz += 0.05
_throat = (_zr - _zf) if (_zf is not None and _zr is not None) else -99.0
T("collar: the throat lets the body through instead of pinching it",
  _throat - D["H_body"] >= 0.3,
  "throat %.2f, body %.2f, clearance %.2f" % (_throat, D["H_body"], _throat - D["H_body"]))

# --- every hole that receives a bought part is wider than it ----------------
# This check does not look at a part: it looks at a CLASS OF DEFECTS, and it
# was born from two defects found the same day with the parts in hand. The
# bearing seat was drawn at 13.0, that is the diameter of the outer ring, and
# the clutch shaft hole at 5.0, that is the diameter of the shaft: the design
# dimension and the drawn dimension had become the same number, and printed
# they came out two tenths under. The bearing went in by force, the clutch
# did not go in at all.
#
# The rule: a hole that must RECEIVE a bought part must be drawn wider than
# it, by the design clearance plus the printing compensation. It does not
# apply to the heat-set insert seats, where the rule is reversed - the hole
# must be NARROWER than the insert, which melts into it - and for those the
# check is not there.
#
# The minimum is ABSOLUTE, two and a half tenths, and does not descend from
# Comp_hole_printing: a check that took its yardstick from the number it
# guards would go back to passing the day the two dimensions get confused
# again.
_hh_m = D["Cd_holes_motor"]/2
BOUGHT_HOLES = [
    # HALF WAY UP THE HUB, not at z 3: the clutch starts at Z_top_clutch, which
    # is 6 - below there is nothing left to probe, and the
    # check said "hole not found" of a hole that is there.
    ("clutch: shaft hole", _clutch_hub, (D["Cd_motor"], 0.0),
     D["Z_top_clutch"] + D["H_hub_clutch"]/2, D["D_shaft"], "motor shaft"),
    # And half way up the MOTOR PLATE, not the whole plate: under the motor
    # the plate is stepped, and its former centre line is now air.
    ("arm: passage of a motor screw", _arm,
     (D["Cd_motor"] - _hh_m, -_hh_m),
     -D["Z_face_motor"] + D["Th_plate_motor"]/2, 3.0, "M3 screw"),
    ("collar: passage of the screw inside the pivot", _col,
     (D["R_disc"], D["Off_pivot"]), 5.0, 3.0, "M3 screw"),
]
_tight = []
for _name, _sol, (_cx, _cy), _zm, _dp, _part in BOUGHT_HOLES:
    _rr = _r_material(_sol, _zm, cx=_cx, cy=_cy)
    if _rr is None:
        _tight.append("%s: hole not found" % _name)
        continue
    _clearance = 2*_rr - _dp
    if _clearance < 0.25:
        _tight.append("%s: hole %.2f against %s %.2f, clearance %.2f"
                        % (_name, 2*_rr, _part, _dp, _clearance))
T("every hole that receives a bought part is wider than it",
  not _tight, "; ".join(_tight))


# ---- THE HATCH UNDER THE MOTOR, measured on the STEP files in out/ ----------
# Strategy B: the motor comes up from below through a hatch in the floor,
# after the arm. The condition for it: the motor must still be
# free when the arm moves. The first hatch, cut on the motor at rest, met the
# moving motor for 55 mm3 in its screw ears - the ears rise above the bottom
# of the motor, 1 mm from it, and at the ends of the travel the motor moves
# 1.5..1.8 mm sideways. So: the maker's motor (without its leads, which bend)
# turned about the pivot to both ends and the middle, against the part and the
# cover as exported; the motor coming up from 60 mm below; the cover against
# the part; and the cover's outer face flush with the floor, probed.
import outline_motor as _SMa
_one_piece_h = cq.importers.importStep(OUT + "box_collar.step").val()
_cover_h = cq.importers.importStep(OUT + "hatch_cover.step").val()
_mot_h = _SMa.body()
_Ph = cq.Vector(D["R_disc"], D["Off_pivot"], 0.0)
_touches_h = []
for _g in (CB.limits(D)[0], 0.0, CB.limits(D)[1]):
    _mg = _mot_h.rotate(_Ph, _Ph + cq.Vector(0, 0, 1), _g)
    for _nm, _so in (("one-piece part", _one_piece_h), ("cover", _cover_h)):
        _v = _mg.intersect(_so).Volume()
        if _v > 0.01:
            _touches_h.append("%s at %.2f degrees: %.2f mm3" % (_nm, _g, _v))
T("hatch: the motor moves with the arm without touching part and cover",
  not _touches_h, "; ".join(_touches_h))
_up_h = [dz for dz in range(2, 62, 4)
         if _mot_h.translate(cq.Vector(0, 0, -dz)).intersect(_one_piece_h).Volume() > 0.01]
T("hatch: the motor comes up from 60 mm below to home without touching",
  not _up_h, "touches at %s mm from home" % _up_h)
_v_h = _cover_h.intersect(_one_piece_h).Volume()
T("hatch: the cover does not interpenetrate the part", _v_h < 0.01, "%.2f mm3" % _v_h)
_bh = _cover_h.BoundingBox()
T("hatch: cover flush with the outer face of the floor",
  abs(_bh.zmin - D["Z_floor_box"]) < 0.01, "zmin %.3f against %.3f" % (_bh.zmin, D["Z_floor_box"]))

print("--- OK (%d) ---"%len(ok)); [print("  ",r) for r in ok]
print("--- INCONSISTENCIES (%d) ---"%len(ko)); [print("  !",r) for r in ko]
