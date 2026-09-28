# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The clutch: ASA hub and TPU ring, co-printed.

HOW IT GOES ON THE MACHINE: **vertical axis, the face of the collar on the
bed**. The Ø30 collar that carries the grub insert is at the bottom and is the
first layer, 707 mm2 of solid circle. The insert tunnel therefore comes out
horizontal and will come out a little oval: for a seat in which the insert
MELTS that is fine, and it is the opposite for the shaft hole, which is long
and narrow and in this orientation is printed along its own axis.

THE GRUB TAKES IN A HEAT-SET INSERT, not in the ASA: the thread formed in the
plastic strips after a few times and, under constant load, the ASA creeps and
the grip goes away by itself - a grub that lets go makes the clutch slip on
the shaft without saying so.

WHEN IT IS TIGHTENED: with the mechanism fitted and the box still open. The
key goes in horizontally, from the side of the collar, and with the box
closed it would not reach it: that is a check.

THE TEETH BETWEEN THE TWO MATERIALS ARE DOVETAILS, wider at the bottom than at
the mouth: the TPU ring can no longer slip out radially,
and the torque no longer relies only on the adhesion between the two
materials and on the interlocking the slicer makes at layer scale. The
profile lies in the printing plane, so it adds no overhangs.
"""
import math
import cadquery as cq
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
from parameters import D
DT,DC,DS = D["D_clutch"], D["D_hub_clutch"], D["D_shoulders_clutch"]
HM,HS = D["H_hub_clutch"], D["H_shoulder_clutch"]
# BO is the diameter the hole is DRAWN with - shaft plus running clearance
# plus printing compensation - not the shaft's nominal. It was exactly
# D_shaft: printed it came out 4.8 on a 5 shaft, and the clutch would not go
# on. The flat of the hole and the aim of the grub also follow from BO, and
# must follow it.
BO,FL,GR = D["D_hole_clutch"], D["Flat_shaft"], D["D_grub"]
NT,TD,TW = int(D["N_teeth_clutch"]), D["Th_teeth_clutch"], D["L_teeth_clutch"]
z0 = (D["Z_plane_mid_disc"] - D["Z_top_clutch"]) - D["Th_clutch"]/2
z1 = z0 + D["Th_clutch"]
Q0=D["Z_top_clutch"]; XC=D["Cd_motor"]      # position in the assembly frame
# The hub is built in stretches around the band of the tread, and below and
# above that band the two shoulders must remain. Z_top_clutch decides where the
# band falls: taking it out of its range, one of the two stretches goes to
# zero and cadquery stops on an extrusion of zero height - an error that says
# nothing to someone who has only changed a number in the parameter editor. It
# really happened, with Z_top_clutch at 6. Here instead we say what does not
# add up and between which values one can stay.
# WHAT MUST EXIST ARE THE TWO SHOULDERS, not a disc under them. The guard
# demanded a stretch of hub BELOW the low shoulder, and so it forbade by
# construction the question whether that disc is really needed. It is not: what retains the tread are the two Ø46 shoulders,
# above and below. So now we demand that the shoulders fit, and the bottom
# disc is allowed to be zero tall.
_h_base = z0 - HS           # the disc under the low shoulder: may be zero
_below = z0                 # how much there is below the tread: must carry the shoulder
_above = HS                 # above the tread only the shoulder remains
if _below < HS or _above <= 0:
    _pm, _sp = D["Z_plane_mid_disc"], D["Th_clutch"]
    raise SystemExit(
        "Z_top_clutch = %.2f cannot be made.\n"
        "The clutch hub would be left without one of its two shoulders, which\n"
        "are what retains the tread: below the\n"
        "tread there are %+.2f mm left and above %+.2f mm, and more than zero is\n"
        "needed for both.\n"
        "With the other dimensions as they are now the valid range is\n"
        "  %.2f < Z_top_clutch < %.2f\n"
        "To get out of it one can also raise H_hub_clutch (now %.2f) or lower\n"
        "H_shoulder_clutch (now %.2f), which are the other two terms in play."
        % (D["Z_top_clutch"], _below, _above,
           _pm + _sp/2 + HS - HM, _pm - _sp/2 - HS, HM, HS))
def cyl(d,h,z):
    return (cq.Workplane("XY").workplane(offset=Q0+z).center(XC,0).circle(d/2).extrude(h))
# ABOVE THE TOP SHOULDER THERE IS NOTHING ANY MORE. Above it there used to be
# another Ø44 cylinder 2 tall, and then the grub collar. It was removed
# because it did nothing except move
# the grub two millimetres away from the tread and lengthen the part. Now the
# collar rests directly on the shoulder.
#
# THE Ø46 SHOULDER STAYS, and it is not the cylinder that was removed: it
# is a millimetre tall and retains the TPU ring axially. Without it the tread
# has nothing to stop it upwards.
hub = cyl(DS,HS,z0-HS).union(cyl(DC,z1-z0,z0)).union(cyl(DS,HS,z1))
if _h_base > 0.01:
    hub = hub.union(cyl(D["D_base_clutch"], _h_base, 0))
_z_top_hub = z1 + HS          # where the hub ends, in local coordinates

# --- the bottom disc stays OUTSIDE the screw heads ---------------------------
# Before, it passed over them at Ø44 and was dug out with a ring. Now it does
# not pass over them at all:
# D_base_clutch stops where the heads begin. Measured, the two ways gave the
# same numbers - 11.2 g, 1.90 mm of clearance, the same overhangs - but the
# groove left outside it a ring 0.87 mm wide and one tall, attached only at
# the top of the shoulder: a little flash that prints badly and comes off.
#
# THE CLEARANCE IS CHECKED HERE, because it is a fit between two parts that
# nobody else looks at: the clutch turns and the screws stay still, so it is
# not enough that they avoid each other at one point - they must avoid each
# other for the whole turn.
_r_screws = D["Cd_holes_motor"]/2.0 * math.sqrt(2.0)
_r_head = _r_screws - D["D_head_screw_M3"]/2.0
_r_disc = D["D_base_clutch"]/2.0
if _h_base > 0.01 and _r_disc > _r_head:
    raise SystemExit(
        "the bottom disc of the clutch (r %.2f) passes over the heads of the\n"
        "motor screws, which begin at r %.2f. Turning, it runs into them.\n"
        "D_base_clutch follows from Cd_holes_motor and D_head_screw_M3: if one\n"
        "of the two has changed, the disc must follow them."
        % (_r_disc, _r_head))
if _h_base > 0.01:
    print("   the bottom disc stops at r %.2f, the heads begin at %.2f: %.2f of clearance"
          % (_r_disc, _r_head, _r_head - _r_disc))
else:
    print("   no bottom disc: the hub starts with the low shoulder")


# ---------------- the collar that carries the grub insert ----------------
# The grub used to screw into the ASA: the thread formed in the plastic strips,
# and under constant load the ASA creeps, so the grip goes away by itself. Now
# there is an M3 heat-set insert.
#
# The insert is Ø5 x 3 and wants height: above the tread the hub has three
# millimetres of it, and cannot grow upwards - the opening of the body ends at
# 14.3 and the roof of the compartment at 16, which must let the hand through.
# So the hub grows DOWNWARDS, with a Ø30 collar that comes to within a
# clearance of the face of the arm. Thirty because the collar turns: its
# radius adds to the centre distance, and at Ø30 it stays outside the body
# (r 82.5 against 79) and passes beyond the heads of the motor screws, which
# are 15.6 from the shaft.
#
# The insert tunnel is kept LOW: above it the hub carries on solid, below
# Wall_below_insert_grub remains. It is the thinnest wall of the joint, and
# the check measures it on the solid.
# THE COLLAR IS ABOVE THE HUB, no longer below. Trying to plant the insert on
# the printed part showed why: with the
# collar below, the iron tip goes in in a straight line but passes CLOSE to the
# tread - measured, the Ø8.5 tip centred at z 3.62 reaches 7.87 and the TPU
# starts at 7.00. It is not the seat that is tight: it is the tip that is
# taller than the space between the insert and the tread, which is 0.88 mm.
#
# Turning it over, the insert goes to z 16.5 and the tip occupies
# 12.25..20.75: all above the tread. And there is room - measured with
# study_clutch_profile.py: above the tread the free radius is 25 up to z 13
# and 18 from 14 to 21, while the collar is Ø25, that is r 12.5.
#
# And from it follows the real gift: the bottom of the clutch rises from 0.30
# to 5.00, so the motor rises by 4.70 and the floor of the box follows it. Less
# height is a design goal, not a side effect.
# THE COLLAR MUST CONTAIN THE INSERT, as well as let the tip through.
# H_collar_grub follows from the tip, which is the larger constraint; this is
# the other one, and if one day the insert grew or the tip got smaller it
# would overtake it without anyone noticing.
_h_needed = D["D_hole_insert_M3"] + 2*D["Wall_below_insert_grub"]
if D["H_collar_grub"] < _h_needed:
    raise SystemExit(
        "the grub collar is %.2f tall and the insert with its wall wants\n"
        "%.2f: the wall above or below the hole disappears. H_collar_grub follows\n"
        "from the iron tip (%.1f + %.1f), which so far was the larger\n"
        "constraint: now it no longer is."
        % (D["H_collar_grub"], _h_needed, D["D_tip_iron"], D["Cl_tip_iron"]))

_h_coll = D["H_collar_grub"]
hub = hub.union(cyl(D["D_collar_grub"], _h_coll, _z_top_hub))

# --- NO RECESS in the top shoulder -----------------------------------------
# Here a ring was cut out of the face of the top shoulder, from the collar out
# to D_hub_clutch/2 - 1, so that the barrel of the iron planting the grub
# insert could pass: when the insert sat at z 14.32 the iron (Ø8.5 with its
# clearance) came down to 10.07, a millimetre into a shoulder ending at 11.
# What it left was the retaining ring over the tread joined to the rest of the
# hub along ONE EDGE - the recess ended exactly where the ring began - and
# the section shows the risk of it coming off the tread. Avoid it.
#
# It is not needed any more, and that is why it can go without moving
# anything: the collar is now H_collar_grub = D_tip_iron + Cl_tip_iron tall
# and the insert sits half way up it, so the iron comes down exactly to the
# base of the collar, which IS the top of the shoulder. Tangent, not
# overlapping. Should the chain ever change so that it overlaps again, the
# answer is to raise the insert, not to cut the ring loose: stop here.
_z_bottom_tip = D["Z_insert_grub"] - (D["D_tip_iron"] + D["Cl_tip_iron"])/2
if _z_bottom_tip < D["Z_base_collar_grub"] - 1e-6:
    raise SystemExit(
        "the iron tip for the grub goes down to z %.2f, below the top shoulder\n"
        "of the clutch (%.2f): the insert must be raised, not the shoulder dug\n"
        "out - the recess left the ring above the tread attached by one edge."
        % (_z_bottom_tip, D["Z_base_collar_grub"]))

teeth = None
for i in range(NT):
    # The tooth is a DOVETAIL: TW wide at the mouth, on the edge of the hub,
    # and TW + Widen_tail_dovetail at the bottom. That way the TPU ring cannot
    # slip out radially and the torque does not rely only on the adhesion
    # between the two materials. The profile lies in the printing plane, so it
    # adds no overhangs: it prints like the straight teeth of before.
    _w2 = (TW + D["Widen_tail_dovetail"])/2
    _prof = [(DC/2, TW/2), (DC/2, -TW/2), (DC/2-TD, -_w2), (DC/2-TD, _w2)]
    t = (cq.Workplane("XY").workplane(offset=Q0+z0).polyline(_prof).close()
         .extrude(z1-z0).rotate((0,0,0),(0,0,1),360.0/NT*i)
         .translate((XC,0,0)))
    teeth = t if teeth is None else teeth.union(t)
hub = hub.cut(teeth)
_z_hole = Q0 - 1.0                  # below the hub: the shaft goes in from there
# The hole is a D: the round cut by the CHORD, and above the chord material
# remains that mates with the shaft's flat. Before, the cut was made the other
# way round - a rectangle as wide as the whole hole was removed, from the plane
# of the flat upwards - so instead of the D came the round PLUS a slot, and on
# top of that the slot started from Flat_shaft minus the radius of the DRAWN
# hole, that is three tenths inside the shaft. The defect showed looking at
# the cut in the slicer; the fix is the true D, not just a moved slot.
#
# What changes in hand: the torque no longer depends only on the grub's
# friction, because the flat of the hole rests on the shaft's flat. In
# exchange the hole is no longer larger than the shaft on all sides, and
# Flat_shaft is a DECLARED catalogue figure, not measured: if on the real motor
# the flat were less deep than 4.5, the D would be tight. To be measured with
# the caliper.
_hole = (cq.Workplane("XY").workplane(offset=_z_hole).center(XC,0)
         .circle(BO/2).extrude(_z_top_hub + _h_coll + 2))
_chord = (cq.Workplane("XY").workplane(offset=_z_hole)
          .center(XC, D["Z_flat_hole"] + BO/2).rect(2*BO, BO)
          .extrude(_z_top_hub + _h_coll + 2))
hub = hub.cut(_hole.cut(_chord))
# 45 degree lead-in at the mouth of the hole, on the face from which the
# clutch slides onto the shaft - the collar's, towards the arm. The cone
# starts half a millimetre outside the face, in the air: coplanar leaves chips
# on the edge.
_z_mouth = Q0
hub = hub.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_mouth_hole_clutch"]/2 + 0.5, D["D_hole_clutch"]/2,
    D["H_leadin_hole_clutch"] + 0.5,
    cq.Vector(XC, 0, _z_mouth - 0.5), cq.Vector(0, 0, 1))))

# the seat of the insert, the grub's clearance hole and the lead-in. The grub
# goes in from +Y, that is from the side of the collar, and presses on the
# flat.
_r_coll = D["D_collar_grub"]/2
_z_ins = D["Z_insert_grub"]
_y_bottom_seat = _r_coll - (D["L_insert_M3"] + 0.5)
# The channel reaches the outer limit of the BODY THE INSERT SITS IN, which
# is the Ø25 collar and no longer the hub. As long as the
# collar hung below, above the tunnel the hub stuck out up to Ø46 and the tool
# ran into it: the channel therefore had to come out beyond the shoulders, at
# r 24. With the collar turned over, nothing sticks out above the insert any
# more - the collar is the outermost part at that height - and a channel still
# aiming at r 24 would cut air for eleven and a half millimetres. It did: the
# check read a "hole" of 14.16, which was the void around the collar and not a
# seat.
#
# It is also what the printed part asked for - the seat closer to the outer
# edge, so the iron does not sink all the way in: now it
# sinks L_insert_M3 + 0.5, that is 3.5 mm instead of ten.
_y_out = _r_coll + 1.0
hub = hub.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
    D["D_hole_insert_M3"]/2, _y_out - _y_bottom_seat,
    cq.Vector(XC, _y_bottom_seat, _z_ins), cq.Vector(0, 1, 0))))
_y_aim_grub = D["Z_flat_shaft"] - 1.0     # one millimetre inside the flat
hub = hub.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
    (GR + D["Cl_clear_grub"])/2, _y_bottom_seat - _y_aim_grub,
    cq.Vector(XC, _y_aim_grub, _z_ins), cq.Vector(0, 1, 0))))
# The lead-in is no longer needed and is not there: the channel crosses the
# hub from outside, so the insert meets no edge to enter. In its place, a
# chamfer where the channel comes out on the collar, because there a coplanar
# cone would leave chips on the edge.
hub = hub.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_hole_insert_M3"]/2 + D["Dp_leadin_insert_M3"], D["D_hole_insert_M3"]/2,
    D["Dp_leadin_insert_M3"],
    cq.Vector(XC, _r_coll, _z_ins), cq.Vector(0, -1, 0))))
tyre = (cq.Workplane("XY").workplane(offset=Q0+z0).center(XC,0).circle(DT/2).circle(DC/2)
        .extrude(z1-z0)).union(teeth)
outer=[e for e in tyre.edges("%CIRCLE").vals() if abs(e.radius()-DT/2)<0.01]
tyre = tyre.newObject(outer).fillet(D["R_fillet_tread"])
# THE TREAD MUST NOT HAVE MOVED, and it is checked BEFORE writing: its height
# is decided by the wheel's disc, not by the clutch, and it is the only thing
# that turning the hub over must not carry along with it. The check was at the
# end, after the exports - that is, a wrong tread ended up in out/ and stayed
# there, and that folder is opened while work is going on.
# THE BAND THAT TOUCHES THE DISC IS MEASURED, not the envelope of the solid. At
# the first attempt the check looked at the bounding box of tyre, and breaking
# the tread on purpose - moving it by 2 mm - it DID NOT SOUND: in the solid
# there are also the dovetail teeth, which had not moved, and they kept the
# envelope low. A check that measures the envelope of two things watches zero.
_band = (cq.Workplane("XY").circle(DT/2).circle(DT/2 - 0.4)
           .extrude(100).val().translate((XC, 0, -50)))
_tpu = tyre.val().intersect(_band).BoundingBox()
_expected = D["Z_plane_mid_disc"] - D["Th_clutch"]/2
if abs(_tpu.zmin - _expected) > 0.05:
    raise SystemExit("the tread has moved: the band that touches the "
                     "disc is at z %.2f and must be at %.2f, which is the plane "
                     "of the disc. Turning the hub over carried it along."
                     % (_tpu.zmin, _expected))

# DOES THE SHAFT COVER THE GRUB HOLE? It was a derivation - Z_face_motor was
# obtained from here - and it became a check when lowering the
# grub loosened that constraint and it stopped ruling the height of the motor.
# Loosened does not mean gone: if someone raises the grub again, or shortens
# the shaft, the grub ends up pressing on nothing and the clutch slips on the
# shaft without saying so.
_z_tip_shaft = -D["Z_face_motor"] + D["L_shaft"]
_z_top_grub = D["Z_insert_grub"] + D["D_grub"]/2
if _z_tip_shaft < _z_top_grub:
    raise SystemExit(
        "the shaft does not cover the grub hole: it reaches z %.2f and the hole\n"
        "ends at %.2f. The grub would press on nothing for %.2f mm and the\n"
        "clutch would slip on the shaft without saying so.\n"
        "The three dimensions in play: L_shaft %.1f, Z_face_motor %.2f, "
        "Z_insert_grub %.2f."
        % (_z_tip_shaft, _z_top_grub, _z_top_grub - _z_tip_shaft,
           D["L_shaft"], D["Z_face_motor"], D["Z_insert_grub"]))
print("   the shaft reaches z %.2f, the grub hole ends at %.2f: covered by %.2f"
      % (_z_tip_shaft, _z_top_grub, _z_tip_shaft - _z_top_grub))

# ---- THE HOLES FOR THE MOTOR SCREWS (strategy C) ----
# The clutch cannot come in from above: on the shaft it is caged, and it
# touches the roof after 1 mm of the 13 it needs to leave the shaft. So it
# goes in FIRST, from the wheel side, and the motor comes up into it from
# below; the four motor screws then go in from above, THROUGH the clutch -
# head and hex key. One hole over each screw, as wide as the socket head plus
# Cl_hole_screw_clutch per side, through the hub and through the tyre where
# the hole reaches it (the head needs r 21.1 from the shaft, the tyre's
# dovetail starts at r 20.5). The clutch turns: the holes line up with the
# screws only when it is turned to them, and that is how it is assembled.
_hh = D["Cd_holes_motor"]/2
_r_hole = D["D_head_screw_M3"]/2 + D["Cl_hole_screw_clutch"]
_v_tpu0 = tyre.val().Volume()
for _sx in (-1, 1):
    for _sy in (-1, 1):
        _f = cq.Workplane(obj=cq.Solid.makeCylinder(_r_hole, 200.0,
                                                    cq.Vector(XC + _sx*_hh, _sy*_hh, -100.0)))
        hub = hub.cut(_f)
        tyre = tyre.cut(_f)
# measured: a screw head's cylinder, along each screw axis over the whole
# height of the clutch, meets neither hub nor tyre
for _sx in (-1, 1):
    for _sy in (-1, 1):
        _t = cq.Solid.makeCylinder(D["D_head_screw_M3"]/2, 60.0,
                                   cq.Vector(XC + _sx*_hh, _sy*_hh, Q0 - 10.0))
        _v = _t.intersect(hub.val()).Volume() + _t.intersect(tyre.val()).Volume()
        if _v > 0.01:
            raise SystemExit("clutch: the head of a motor screw does not pass through its hole "
                             "(%.2f mm3 at %+.0f, %+.0f)" % (_v, _sx*_hh, _sy*_hh))
print("clutch: 4 holes Ø%.1f for the motor screws; the tread loses %.1f mm3 to them"
      % (2*_r_hole, _v_tpu0 - tyre.val().Volume()))
cq.exporters.export(hub, OUT + "clutch_hub.step")
cq.exporters.export(tyre, OUT + "clutch_tyre.step")
# "mozzo_ASA" and "anello_TPU" are the body names written into the STEP: output
# data, left as they are
cq.Assembly().add(hub,name="mozzo_ASA").add(tyre,name="anello_TPU").save(OUT + "clutch_assembly.step")
_hb = hub.val().BoundingBox()
print("hub %.1f g ASA | ring %.1f g TPU | z %.2f..%.2f, collar Ø%.0f ON TOP, "
      "grub insert at z %.2f"
      % (hub.val().Volume()*1.07e-3, tyre.val().Volume()*1.21e-3,
         _hb.zmin, _hb.zmax, D["D_collar_grub"], D["Z_insert_grub"]))
# THE BOTTOM OF THE CLUTCH IS WHAT DECIDES WHERE THE MOTOR IS: it is stated,
# and stated here, because it is the number from which follows how tall the
# machine is.
print("   the bottom is at z %.2f: the motor rises by %.2f compared with the design "
      "with the collar below" % (_hb.zmin, _hb.zmin - D["Free_collar_arm"]))
