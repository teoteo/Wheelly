# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

import math
from parameters import D
ok=[]; ko=[]
import texts_editor as TE
def chk(key, value, limit, sense, unit="mm"):
    """key: a key of the editor catalogues, "chk.<key>" - the names are
    shown in the parameters editor, so they come in the language of the page
    (WHEELLY_LINGUA, English by default). A key with fields is (key, {..})."""
    fields = {}
    if isinstance(key, tuple):
        key, fields = key
    name = TE.tr("chk." + key, **fields)
    good = value >= limit if sense == ">=" else value <= limit
    (ok if good else ko).append("%-46s %8.2f %s %.2f %s" % (name, value, sense, limit, unit))

Rc = D["D_body"]/2; Rd = D["R_disc"]; Ia = D["Cd_motor"]
ap0 = D["Th_wall_front"]; ap1 = ap0 + D["H_opening"]
pm  = D["Z_plane_mid_disc"]; sd = D["Th_disc"]
t0 = pm - D["Th_clutch"]/2; t1 = pm + D["Th_clutch"]/2
# z1 is the top of the HUB, not of the clutch: above the hub sits the grub
# collar, which is at r 12.5 from the shaft, that is OUTSIDE the wheel body, and
# so it does not have to fit inside its opening. Mixing the two up measured the
# collar against a constraint that has nothing to do with it.
z0 = D["Z_top_clutch"]; z1 = z0 + D["H_hub_clutch"]
Rw = Rc - D["Th_wall_radial"]          # inner wall
half = D["Side_motor"]/2

print("=== AXIAL CHAINS ===")
chk("wall_sum",
    abs(ap0 + D["H_opening"] + D["Th_wall_rear"] - D["H_body"]), 0.01, "<=")
chk("disc_in_opening_top", (pm-sd/2) - ap0, 0.5, ">=")
chk("disc_in_opening_bottom", ap1 - (pm+sd/2), 0.5, ">=")
chk("tread_in_knurled_band", (D["Band_knurled_net"]-D["Th_clutch"])/2, 0.2, ">=")
chk("hub_in_opening_top", z0 - ap0, 0.5, ">=")
chk("hub_in_opening_bottom", ap1 - z1, 0.5, ">=")
# The grip on the shaft does not end with the hub: above it is the grub collar,
# and the shaft runs through it - that is exactly where the grub clamps it.
# Measuring it up to z1 made it five millimetres when it is eleven and a half,
# and would have had a part shortened that is in fact fine.
_z_top_clutch = D["Z_base_collar_grub"] + D["H_collar_grub"]
chk("shaft_grip_in_hub",
    min(-D["Z_face_motor"] + D["L_shaft"], _z_top_clutch) - z0, 7.5, ">=")

print("\n=== RADIAL CHAINS ===")
chk("centre_distance", abs(Ia - Rd - D["D_clutch"]/2), 0.01, "<=")
chk("clutch_hub_vs_inner_wall", (Ia - D["D_hub_clutch"]/2) - Rw, 0.3, ">=")
chk("clutch_shoulders_vs_disc_rim", (Ia - D["D_shoulders_clutch"]/2) - Rd, 1.0, ">=")
# The two shoulders of the clutch hub are what is left below and above the
# tread band, and Z_top_clutch decides where that band falls. Outside its range
# one of the two stretches goes to zero: the solid no longer builds and
# cadquery stops on an extrusion of zero height, without saying why. Here the
# problem shows before generating, that is when the number is changed.
_zt0 = (pm - D["Z_top_clutch"]) - D["Th_clutch"]/2     # base of the band in the hub
_zt1 = _zt0 + D["Th_clutch"]
# The two shoulders must BE THERE; below the lower shoulder there must be
# nothing else. The limit was 0.2 and demanded a stretch of hub below the
# shoulder: it was removed because it retained nothing, and
# the hub now starts exactly with the shoulder. Zero is the right value, not a
# concession.
chk("shoulder_below_tread", _zt0 - D["H_shoulder_clutch"], 0.0, ">=")
chk("shoulder_above_tread",
    D["H_hub_clutch"] - _zt1 - D["H_shoulder_clutch"], 0.0, ">=")
chk("grub_collar_outside_body", (Ia - D["D_collar_grub"]/2) - Rc, 3.0, ">=")
# And clear of the MOTOR SCREW HEADS, which is the constraint that was missing.
# The collar turns with the hub a few millimetres from the motor face: the four
# holes are on a square at Cd_holes_motor, so the screws are at
# Cd_holes_motor/sqrt(2) from the shaft axis, and their heads start at that
# radius minus their own. As long as the collar stays inside that circle it
# passes; if it touches it, one finds out while screwing the motor on. At Ø30
# the clearance was six tenths and no check said so - it showed on the
# printed part, and the collar went down to Ø25.
_r_motor_heads = D["Cd_holes_motor"]/math.sqrt(2) - D["D_head_screw_M3"]/2
chk("grub_collar_under_screw_heads",
    _r_motor_heads - D["D_collar_grub"]/2, 1.5, ">=")

# The height of the grub follows from the collar that holds it, and the collar
# starts above the upper shoulder: the old sum started from Free_collar_arm,
# that is the clearance between the collar and the arm, which made sense as
# long as the collar HUNG below the hub. With the collar turned over, that
# clearance has nothing to do with it any more - and the check went off by ten
# millimetres seventy on a correct part.
chk("grub_insert_height",
    abs(D["Z_base_collar_grub"] + D["H_collar_grub"]/2 - D["Z_insert_grub"]),
    0.01, "<=")
chk("motor_inner_corner_outside_body", (Ia - half) - Rc, 0.5, ">=")
chk("motor_holes_vs_arm_rim", math.hypot(Ia-D["Cd_holes_motor"]/2, D["Cd_holes_motor"]/2) - D["R_rim_inner"], 3.0, ">=")
chk("motor_outer_corner_vs_box_wall", D["R_out_box"] - (Ia + half), 4.0, ">=")
chk("clutch_rim_vs_box_wall", D["R_out_box"] - (Ia + D["D_clutch"]/2), 3.0, ">=")
# The board sits in the motor bay: its farthest outer corner must stay inside
# the inner face of the back wall. These were two numbers written by hand,
# 106 + 15 and 35, from when the board sat in the electronics bay.
import electronics as _E
chk("board_inside_box_wall",
    D["R_out_box"] - D["Th_walls_box"] - math.hypot(_E.S1, _E.T1), 1.0, ">=")
chk("half_chord_vs_clutch_radius", D["Chord_opening"]/2 - D["D_clutch"]/2, 5.0, ">=")
chk("disc_rim_proud_of_flat", D["Proj_rim"], 0.5, ">=")
chk("clutch_clear_of_flat", Rd - D["D_plane_opening"], 0.5, ">=")
# The half-width of the window follows from the clearance: here we check that
# the number in the table is still the one the formula gives. The worst edge
# is on the outer surface of the band, because going outwards the flank of the
# cut gets closer to the clutch axis.
Rec = D["R_out_collar"]
_cos = (Rec**2 + Ia**2 - (D["D_clutch"]/2 + D["Cl_aperture_clutch"])**2)/(2*Rec*Ia)
chk("window_half_width",
    abs(math.degrees(math.acos(_cos)) - D["Ang_aperture_clutch"]), 0.01, "<=", "deg")

print("\n=== PIVOT AND ARM ===")
Rp = math.hypot(Rd, D["Off_pivot"])
chk("r_pivot_consistent", abs(Rp - D["R_pivot"]), 0.05, "<=")
Lb = math.hypot(Ia-Rd, D["Off_pivot"])
chk("l_arm_consistent", abs(Lb - D["L_arm"]), 0.05, "<=")
P=(Rd,D["Off_pivot"]); M=(Ia,0.0); dx,dy=M[0]-P[0],M[1]-P[1]
t=-(P[0]*dx+P[1]*dy)/(dx*dx+dy*dy); t=max(0,min(1,t))
chk("arm_axis_min_radius",
    math.hypot(P[0]+t*dx, P[1]+t*dy) - D["R_rim_inner"], 5.0, ">=")
chk("pivot_hub_vs_body", (Rp - D["D_hub_pivot"]/2) - Rc, 2.0, ">=")

print("\n=== TORQUES AND FORCES ===")
Ft = D["Trq_detent_crest_mNm"]*1.3/Rd
# THE GROUND FOR THE FORCE IS NOW A MEASUREMENT. The preload used
# to be derived here from the detent's crest torque - friction 0.6, safety
# factor 2.5, for a 95A tyre - and it asked for 22.3 N of spring. Measured on
# the reference wheel, 6.9 N on the arm (700 g, tyre in TPU 87A) drive the
# disc, and two kit springs giving 12..15 N were chosen. The check is now the margin of the
# design force over what was measured; the old estimate is printed alongside.
N  = Ft/0.6*2.5
print("   (the old estimate from the crest torque asked for a preload of %.1f N)" % N)
chk("spring_force_margin_on_measured", D["Force_spring_N"]/D["Force_spring_min_N"], 1.7, ">=", "x")  # 1.7: all of the kit springs' 12..15 N passes (12/6.9 = 1.74)
Cm = Ft*D["D_clutch"]/2
chk("motor_torque_margin", 140.0/Cm, 2.0, ">=", "x")
Mm = D["Preload_N"]*D["Off_pivot"]
chk("spring_force_consistent", abs(Mm/D["Att_spring"] - D["Force_spring_N"]), 1.5, "<=", "N")

print("\n=== BOX ===")
import math as _m
_mx = max(Ia + D["D_clutch"]/2, _m.hypot(Ia+half, half), D["R_seat_spring_box"])
chk("box_wall_past_moving_parts", D["R_out_box"] - _mx, 3.0, ">=")
chk("collar_reaches_box_end", D["Ang_collar_pivot"] - D["Ang_box_pivot"], 0.0, ">=", "deg")
# The two angles that follow from the head: the table holds the number, here
# we look that it is still the formula's.
# The board is cut on the head side: past the first hole at least half a pitch
# must be left, or the cut runs through the pads of column C0.
chk("board_cut_past_column_c0", _E.CUT_MARGIN, D["Pitch_perfboard"]/2, ">=")
chk("box_end_consistent",
    abs(_E.head_angle(D["R_out_collar"], "out") - D["Ang_box_pivot"]), 0.01, "<=", "deg")
chk("front_ear_b_consistent",
    abs((_E.head_angle(D["R_out_collar"], "in") + _E.head_angle(D["R_out_collar"], "out"))/2
        - D["Ang_ear_front_B"]), 0.01, "<=", "deg")

print("\n=== EXTENDED COLLAR ===")
# The angle to check is the one the collar really reaches in the solid, that
# is Ang_collar_pivot. Ang_collar_extended says 130 but no generator uses it:
# checking it meant measuring a part that does not exist.
_Rif=D["R_in_flange_collar"]
_a=math.radians(D["Ang_collar_pivot"])
chk("collar_flange_vs_rotator",
    math.hypot(_Rif*math.cos(_a)+D["Off_hole_optical"], _Rif*math.sin(_a)) - D["R_envelope_optical"], 1.0, ">=")
chk("collar_covers_box",
    D["Ang_collar_pivot"] - D["Ang_box_pivot"], 0.0, ">=", "deg")

print("\n=== SEAL ON THE CAMERA FACE ===")
# The gasket presses on a ring of face that must be solid. Past the bottom of
# the front slot the face is no longer there: the slot goes right through the
# front plate. These three numbers were written by hand (3, 72, 76.3) and
# stood still while the parameters moved.
_Rg=D["R_gasket"]; _lg=D["L_groove_gasket"]; _bottom=Rc-D["Dp_slot_front"]
chk("gasket_below_groove_bottom", _bottom - (_Rg+_lg/2), 0.5, ">=")
chk("gasket_inside_m3_screws", D["R_screw_anchor"] - (_Rg+_lg/2), 1.5, ">=")
chk("gasket_outside_inner_flange", (_Rg-_lg/2) - _Rif, 0.5, ">=")
# The labyrinth rib rises from the same face as the groove: if the two overlap
# in radius the collar profile crosses itself.
_rb0=Rc-D["Dp_slot_front"]+0.5
chk("labyrinth_rib_outside_groove", _rb0 - (_Rg+_lg/2), 0.5, ">=")

print("\n=== SPRING AND BEARINGS ===")
chk("spring_fitted_shorter", D["L_spring_free"] - D["L_spring_fitted"], 1.0, ">=")
chk("compression_within_45",
    100*(D["L_spring_free"]-D["L_spring_fitted"])/D["L_spring_free"], 45.0, "<=", "%")
chk("bearing_seat_through", abs(D["H_bearings"] - D["Th_arm"]), 0.01, "<=")

print("\n=== SENSOR ===")
# The ring surrounds the magnet, not the pivot: the pivot comes up flush and
# nothing touches it. On the magnet the clearance is kept tight, but not zero.
chk("bracket_ring_clearance_magnet", (D["D_in_ring_bracket"]-D["D_magnet"])/2, 0.05, ">=")
chk("bracket_ring_clear_of_pivot", (D["D_in_ring_bracket"]-D["D_pivot_hub"])/2, 0.05, ">=")
# the web is measured on the hole as printed, not the design one, and on the
# test foot, whose hole is wider still
chk("web_ring_to_m2_holes",
    D["Cd_holes_module"]/2 - D["D_holes_M2"]/2
    - (D["D_hole_magnet_printing"] + D["Cl_test_magnet"])/2, 0.4, ">=")
# and the wide hole must not eat the centring: what the magnet can rattle in
# the ring is offset between chip and magnet, and the AS5600 allows 0.25 in
# all
chk("foot_centres_module",
    (D["D_hole_magnet_printing"] + D["Cl_test_magnet"] - D["D_magnet"])/2, 0.25, "<=")
chk("magnet_clearance_printed_hole",
    (D["D_hole_magnet_printing"] - D["D_magnet"])/2, 0.25, "<=")
chk("air_gap_within_3", D["H_rest_module"]-D["H_body_chip"]-D["Th_magnet"], 3.0, "<=")
chk("air_gap_over_05", D["H_rest_module"]-D["H_body_chip"]-D["Th_magnet"], 0.5, ">=")
# --- the bracket against the rest ----------------------------------------
# The bracket has no solid, so the interference check does not see it: here
# the true outline is measured, the one from bracket_outline().
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from drawings import (bracket_outline, bracket_arms, hub_radius,
                      bracket_step_radius, tie_pad,
                      cable_arm_strips)
from drawings_assembly import from_bulge, rotate, densify
# densified: the straight sides of the arms have only their two ends, and the
# point that goes deepest into the rotator lies mid-side, not on a vertex.
# The cable arm widened to its pads goes in too, for the same
# reason. The tie pad goes into the outline together with the profile: it is a
# local widening of the arm, and a check that did not see it would measure a
# bracket narrower than the one that gets printed.
_st = densify(rotate(from_bulge(bracket_outline()), D["Ang_bracket_sensor"]), 0.3) \
      + densify(rotate(tie_pad(), D["Ang_bracket_sensor"]), 0.3) \
      + [p for _r in cable_arm_strips()
         for p in densify(rotate(_r, D["Ang_bracket_sensor"]), 0.3)]
_rmax = max(math.hypot(x, y) for x, y in _st)
chk("bracket_inside_collar_rim", D["R_out_collar"] - _rmax, 0.5, ">=")
# Each arm falls on one of the four M3 of the bottom plate, which sit at
# Ang_screw_A + 90 k on the telescope-side face, the same as the bracket's.
_screws = [(D["Ang_screw_A"] + 90*k) % 360 for k in range(4)]
def _offset(a):
    a %= 360
    return min(min(abs(a-v), 360-abs(a-v)) for v in _screws)
for _i, _phi in enumerate(bracket_arms(), 1):
    chk(("paddle_on_bottom_screw", {"n": _i}),
        _offset(D["Ang_bracket_sensor"] + _phi), 0.5, "<=", "deg")
# The rotator is on this side and its circle reaches the disc centre (it
# passed exactly through it while the axis was at 48; at Off_hole_optical
# 45.67 it goes 2.3 mm past it):
# the boss necessarily goes into it, by its whole radius, because the magnet
# is there. The arms do not: no point of the bracket may go deeper into it
# than the boss.
_Oo = (-D["Off_hole_optical"], 0.0)
def _inside(p):
    return D["R_envelope_optical"] - math.hypot(p[0] - _Oo[0], p[1] - _Oo[1])
_boss_depth = D["R_envelope_optical"] - (D["Off_hole_optical"] - hub_radius())
chk("bracket_in_rotator_only_boss", _boss_depth - max(_inside(p) for p in _st), -0.05, ">=")
# Past the step the paddles rest on the rear flange of the collar: they must
# all fit on it, in angle and in radius.
_Rg = bracket_step_radius()
_high = [p for p in _st if math.hypot(*p) >= _Rg]
_ang = [math.degrees(math.atan2(p[1], p[0])) for p in _high]
chk("paddles_inside_collar_arc",
    min(min(a + D["Ang_collar_opposite"], D["Ang_collar_pivot"] - a) for a in _ang), 1.0, ">=", "deg")
# and under the board the bracket must stay low, or the module does not sit on it
chk("bracket_step_outside_board",
    _Rg - (D["L_board_module"]/2 + D["Cl_notch_module"]), 2.0, ">=")

# --- the seat of the board -------------------------------------------------
# Under the module are its SMD components: the board rests only on the two
# pads round the M2 holes, and the rest of the surface sits lower.
chk("board_pad_past_components",
    D["R_pad_module"] - D["R_components_module"], 0.5, ">=")
chk("material_m2_hole_to_pad_edge",
    hub_radius() - (D["Cd_holes_module"]/2 + D["D_holes_M2"]/2), 0.5, ">=")
chk("material_beside_m2_hole",
    D["Cd_holes_module"]/2*math.sin(math.radians(D["Ang_pad_module"])) - D["D_holes_M2"]/2,
    0.8, ">=")
chk("pad_reaches_past_screw", hub_radius() - D["R_pad_module"], 1.5, ">=")
chk("recess_floor_material",
    D["H_rest_module"] - D["Dp_notch_module"], 1.5, ">=")
chk("recess_taller_than_components", D["Dp_notch_module"] - 0.93, 0.2, ">=")
# The M2 screw goes through the board and threads into the boss: there is no
# room for a nut below, so the hole in the boss must be narrower than the
# screw, but not so much as to split the material.
chk("m2_screw_through_board", D["D_holes_board"] - 2.0, 0.0, ">=")
chk("leadin_narrower_than_m2", 2.0 - D["D_holes_M2"], 0.15, ">=")
chk("leadin_not_too_narrow", 2.0 - D["D_holes_M2"], 0.5, "<=")
# The screw goes in from above, through the board and into the boss: below it
# is the face of the body, and if it pokes out it holds the part lifted. The
# lowest test foot is 3.2, shorter than the real boss.
chk("m2_not_below_boss",
    D["H_rest_module"] + D["Th_board_module"] - D["L_screw_M2"], 0.3, ">=")
chk("m2_not_below_lowest_foot",
    3.2 + D["Th_board_module"] - D["L_screw_M2"], 0.3, ">=")
chk("m2_grip_in_boss", D["L_screw_M2"] - D["Th_board_module"], 2.0, ">=")

print("\n--- OK (%d) ---" % len(ok)); [print("  ", r) for r in ok]
print("\n--- TO FIX (%d) ---" % len(ko)); [print("  !", r) for r in ko]
