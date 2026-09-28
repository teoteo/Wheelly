# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Reference body and disc, collar, pivot washer.

HOW THE COLLAR GOES INTO THE PRINTER: **telescope side down**, that is the rear
flange on the bed, with normal breakaway supports. The three reasons, because
none of the three can be guessed by looking at the part:

1. One of the two sealing faces necessarily ends up on the supports, and it is
   not a question of how much: measured on the solid they overhang ONE HUNDRED
   per cent - front 2,371 mm2, rear 2,662 - because below r 79.15 there is no
   band under them. So one chooses WHICH one to sacrifice, and the two are not
   equivalent: on the camera face there are two barriers in series, the
   gasket at r 67…70 plus the labyrinth rib at r 71…73 that goes into the
   slot of the body; on the telescope face there is the gasket alone.
   So the one with a single barrier faces up and comes out with the finish of
   the first layer, and the one that has the reserve goes on the supports.
2. The Ø3.2 hole of the reinforced pivot is 19 mm long and MUST be printed
   along its own axis. Sideways it would come out oval and sagging and the M3
   would not go in - and that is why the lying orientation, which would have a
   third of the overhangs (3,218 mm2 against 8,460), is excluded.
3. This way up the pivot grows upwards from solid material instead of being an
   isolated Ø5 little pillar in the middle of the bed. The rest on the bed is
   given by the flat bottom, further down: 3,638 mm2.

Left in the drawer, not done: shortening the flange inwards
(R_in_flange_collar 62.5 -> 65, 19% less face to support) and a chamfer cut
on the outer edge of the undercut (20% less). They are in the working notes.

THE NUMBERS WINDOW, and the defect it brought out. The metal body has its own
little window for reading the numbers of the disc, and the collar covered it.
Making it again here it turned out that **that window and the groove of the
gasket are the same place**: the bead, for those nine millimetres, was not
pressing on material but on the hole. It is not a defect we introduced: it was
already there, and it was invisible because in the model the body was drawn
SOLID there. Now the window of the body is modelled, the groove deviates
locally to go around it while staying continuous, and there is the check that
measures whether the bead presses on material along its whole length.
"""
import math, cadquery as cq
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT + "references", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
from parameters import D, out_subdir
import arm_travel as CB
# z = axial height, 0 = camera-side face, +z towards the telescope
Rc=D["D_body"]/2; Rd=D["R_disc"]; Hc=D["H_body"]
Tha=D["Th_wall_front"]; Thp=D["Th_wall_rear"]; Thr=D["Th_wall_radial"]
ap0=Tha; ap1=ap0+D["H_opening"]
ahalf=math.degrees(math.asin(D["Chord_opening"]/D["D_body"]))


def _pxy(r, a):
    return (r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))


def _arc(wp, r, a0, a1):
    """Runs along the arc of radius r from a0 to a1 with TRUE ARCS, broken into
    spans of no more than ninety degrees because beyond half a turn an arc
    through three points is no longer determined."""
    n = max(1, int(math.ceil(abs(a1 - a0)/90.0)))
    for i in range(n):
        b0 = a0 + (a1 - a0)*i/n
        b1 = a0 + (a1 - a0)*(i + 1)/n
        wp = wp.threePointArc(_pxy(r, (b0 + b1)/2), _pxy(r, b1))
    return wp


def sector(a0,a1,r0,r1,z,h,step=1.0):
    """Sector between two radii, with the curved faces made of ARCS and not of
    polylines. With a step of one degree at r 86 the polyline was off by three
    thousandths - nothing - but it left dozens of flat faces instead of one
    single cylindrical face: it shows on the part, and a fillet on such a face
    is not generated, because instead of the intersection curve it finds the
    edges between one facet and the next. Where the radius is not constant -
    r0 or r1 a function of the angle - the arc does not exist and it stays a
    polyline."""
    if callable(r0) or callable(r1):
        m=max(2,int(abs(a1-a0)/step)+1)
        A=[a0+(a1-a0)*i/(m-1) for i in range(m)]
        f1 = r1 if callable(r1) else (lambda a: r1)
        f0 = r0 if callable(r0) else (lambda a: r0)
        pts=[_pxy(f1(a), a) for a in A] + [_pxy(f0(a), a) for a in reversed(A)]
        return cq.Workplane("XY").workplane(offset=z).polyline(pts).close().extrude(h)
    wp = cq.Workplane("XY").workplane(offset=z).moveTo(*_pxy(r1, a0))
    wp = _arc(wp, r1, a0, a1)
    if abs(r0) < 1e-9:
        wp = wp.lineTo(0.0, 0.0)
    else:
        wp = wp.lineTo(*_pxy(r0, a1))
        wp = _arc(wp, r0, a1, a0)
    return wp.close().extrude(h)

def cyl(d,h,z,dint=0):
    w=cq.Workplane("XY").workplane(offset=z).circle(d/2)
    if dint: w=w.circle(dint/2)
    return w.extrude(h)

# ---------------- REFERENCE BODY ----------------
body = cyl(2*Rc, Tha, 0).union(cyl(2*Rc, Thp, ap1))
def plane(dist, z, h, width=90.0):
    return (cq.Workplane("XY").workplane(offset=z).center((dist+Rc+10)/2, 0)
            .rect(Rc+10-dist, width).extrude(h))
body = body.union(cyl(2*Rc, D["H_opening"], ap0, dint=2*(Rc-Thr))
                    .cut(plane(D["D_plane_opening"], ap0, D["H_opening"])))
# slot on the camera face: the whole chord, Dp_slot_front deep
body = body.cut(plane(Rc-D["Dp_slot_front"], -1, Tha+1))

# ---------------- the numbers window, IN THE BODY ----------------
# This was already there on the real part and not in the model, and the
# difference is not academic: as long as the body here was drawn solid, the
# gasket of the collar appeared to press on a solid face exactly where instead
# it presses on the hole. A check cannot see what the model does not contain,
# and it is the same kind of defect as the electronics compartment that looked
# 96% empty because the perfboard was not there.
#
# The dimensions are measured with the caliper on the reference wheel, not
# taken from a catalogue: 9 wide, from r 66.2 outwards up to the chord. Beyond the chord
# the flat is already milled away by the slot, so the window is the stretch
# that joins that milling to the radius of the numbers. Its ANGLE is not the
# chord's: drawn at 0, centred on the chord, it was wrong - on the reference
# wheel the number shows 6.5 degrees off, with the metal window centred on
# it. Ang_window_body is estimated from a photo, still to be measured.
body = body.cut(cq.Workplane("XY").workplane(offset=-1)
                  .center((D["R_in_window_numbers"] + Rc)/2, 0)
                  .rect(Rc - D["R_in_window_numbers"], D["L_window_numbers"])
                  .extrude(Tha+2)
                  .rotate((0, 0, 0), (0, 0, 1), D["Ang_window_body"]))
# central hole and optical hole
body = body.cut(cyl(8.0, Hc+2, -1))
OFX = -D["Off_hole_optical"]      # optical hole opposite the window
body = body.cut(cq.Workplane("XY").workplane(offset=-1).center(OFX,0)
                  .circle(27.5).extrude(Hc+2))
# 4 M3 screws in the back plate
Rv=D["R_screw_anchor"]
for k in range(4):
    a=math.radians(D["Ang_screw_A"]+90*k)
    body = body.cut(cq.Workplane("XY").workplane(offset=Hc-6)
                      .center(Rv*math.cos(a), Rv*math.sin(a)).circle(1.5).extrude(7))
cq.exporters.export(body, OUT + out_subdir("filter_wheel_body") + "filter_wheel_body.step")

# ---------------- DISC ----------------
disc = cyl(2*Rd, D["Th_disc"], D["Z_plane_mid_disc"]-D["Th_disc"]/2)
disc = disc.union(cyl(D["D_pivot_hub"], D["Z_plane_mid_disc"]-D["Th_disc"]/2, 0))
# the pivot comes out flush on the telescope side too: that is where the magnet is
_zt = D["Z_plane_mid_disc"]+D["Th_disc"]/2
disc = disc.union(cyl(D["D_pivot_hub"], Hc-_zt, _zt))
# The filter holes: M48 x 0.75 threads, drawn at the thread's minor diameter
# (D_hole_filter), on the circle of the optical axis. They were a radius of
# 25.5 and a count of 5 written here by hand: Ø51 at 48 mm cut 1 mm into the
# rim, while the real disc has closed holes with ~3 mm of rim (estimated from
# a photo of the reference wheel). The first hole is at 180 degrees, on the optical axis
# (-Off_hole_optical, 0). check_filter_disc.py measures rim and web on this solid.
_nf = int(round(D["N_holes_filter"]))
_zd = D["Z_plane_mid_disc"] - D["Th_disc"]/2
for k in range(_nf):
    a=math.radians(180+360.0/_nf*k)
    disc = disc.cut(cq.Workplane("XY").workplane(offset=_zd - 1)
                      .center(D["Off_hole_optical"]*math.cos(a), D["Off_hole_optical"]*math.sin(a))
                      .circle(D["D_hole_filter"]/2).extrude(D["Th_disc"] + 2))
cq.exporters.export(disc, OUT + out_subdir("filter_disc") + "filter_disc.step")

# ---------------- COLLAR ----------------
a0=-D["Ang_collar_opposite"]; a1=D["Ang_collar_pivot"]
Re=D["R_out_collar"]; Rg=D["R_gasket"]; Fl=D["Th_flange_collar"]
_Rband = Rc + 0.15               # inner radius of the band: the radial clearance
                                 # on the body. It is in a variable because the
                                 # cut of the groove must STOP here, and the two
                                 # numbers must stay tied.
col = sector(a0,a1,_Rband,Re,0,Hc)                                  # cylindrical band
Rif=D["R_in_flange_collar"]
lg=D["L_groove_gasket"]; pg=D["Dp_groove_gasket"]

# ---------------- the groove that goes around the window ----------------
# The maker printed the numbers 1..5 on the face of the disc, towards the
# camera, at r 68.5, and in the metal body there is already its own window to
# read them. The collar covered it. Making it again here has a problem that
# does not show until it is measured: **68.5 is exactly in the middle of the
# groove of the gasket**, which without deviations is at 67..70. The digit is
# under the bead, not beside it.
#
# Outwards is not possible: between the outer edge of the groove and the
# labyrinth rib there is one millimetre, beyond r 73 the flange in that sector
# is already cut away by the aperture of the clutch, and above all on the BODY
# the camera-side flat is milled away for x > 70.5 - measured: between the
# groove and the void five tenths of face are left to press on. That is the
# reason why the gasket is already at 68.5 and no further out.
#
# So the groove deviates INWARDS, and the window looks out from the outer side
# of the seal.
#
# The deviation does NOT depend on how the opening is closed, and it is not up
# for discussion: the bead must press on material regardless. It was needed
# even before anyone talked about windows - the defect it brought to light was
# already there, with the opening of the body and the straight groove.
#
# The bead is NEVER interrupted: it moves and comes back with a raised cosine
# blend, which has no edges. And the flange follows it, extending towards the
# axis as much as needed to always leave it Edge_in_groove of lip behind, and
# Edge_out_groove in front - the one that separates the bead from the hole.
# At the peak the flange reaches r 59.7, two point eight further in than a
# plain ring. An earlier figure, 61.2, was wrong because it left out the
# outer lip, and without it the groove opened sideways into the window.
_A_win = D["Ang_window_numbers"]
_dev = Rg - (D["R_in_window_numbers"] - D["Edge_out_groove"] - lg/2)
_ap, _ad = D["Ang_flat_groove"], D["Ang_dev_groove"]

def r_groove(a):
    """Radius of the axis of the groove at that angle."""
    t = abs(a - _A_win)
    if t >= _ad: return Rg
    if t <= _ap:  return Rg - _dev
    x = (t - _ap)/(_ad - _ap)
    return Rg - _dev*0.5*(1.0 + math.cos(math.pi*x))

def r_in_flange(a):
    """Inner edge of the front flange: it follows the groove where it deviates."""
    return min(Rif, r_groove(a) - lg/2 - D["Edge_in_groove"])

def band(f_in, f_out, z, h, pitch=0.5):
    """Like sector(), but the two radii can change angle by angle.

    The OUTER edge is sampled with the same step as sector(), one degree, and
    not with the fine one: making it denser, the polygon gets closer to the
    true circle and the collar grows by a few hundredths: enough for the ears
    of the box, which rest against it at r 86, to come out interpenetrating.
    They were 0.36 mm3, which are not a design error but a discretisation one,
    and the way not to have them is that the two parts see the SAME polygon.
    """
    n_e = max(2, int((a1-a0)/1.0)+1)
    A_e = [a0 + (a1-a0)*i/(n_e-1) for i in range(n_e)]
    n_i = max(2, int((a1-a0)/pitch)+1)
    A_i = [a0 + (a1-a0)*i/(n_i-1) for i in range(n_i)]
    p  = [(f_out(a)*math.cos(math.radians(a)), f_out(a)*math.sin(math.radians(a))) for a in A_e]
    p += [(f_in(a)*math.cos(math.radians(a)), f_in(a)*math.sin(math.radians(a)))
          for a in reversed(A_i)]
    return cq.Workplane("XY").workplane(offset=z).polyline(p).close().extrude(h)

col = col.union(band(r_in_flange, lambda a: Re, -Fl, Fl))   # front flange
# The inner face of the front flange is SET BACK by Cl_groove_collar and no
# longer touches the wheel body. The groove was 23.00, that is exactly the
# height of the body, and that face is born on the supports: measured on the
# printed part the groove was 22.8 on average and 22.3 on the ridges, so the
# collar gripped the body instead of sliding onto it.
#
# It moves nothing else, and that is the reason why it is done this way instead
# of widening the groove by moving the flange: the bottom of the gasket groove
# stays at its height, so the gasket keeps reaching z +0.5 and being squeezed
# by the same five tenths against the face of the body. The labyrinth rib too,
# which grows from z 0 towards the body, and the bosses on the outer face stay
# where they are.
#
# In position the collar is put by the REAR flange, pulled by the two screws in
# the back plate: that is a clean face, born above the flat bottom, and the
# supports do not see it.
# The cut STOPS at the inner radius of the band. Going as far as Re+1, as it
# did, it did not set back a face: it CUT THE COLLAR IN TWO all the way round,
# because the cylindrical band starts at z 0 and the flange ended at -0.5. The
# part came out in three detached bodies - 45.0 cm3, 7.8 and 0.14 - and no
# volume measure noticed: it showed only opening the STEP, as a gap between
# the top plane and the wall that should not be there. Now a check looks at it,
# and not only here: every part that is printed must be one single part.
col = col.cut(band(r_in_flange, lambda a: _Rband, -D["Cl_groove_collar"],
                    D["Cl_groove_collar"]))
col = col.union(sector(a0,a1,Rif,Re,Hc,Fl))                    # rear flange

# ---------------- the flat bottom ----------------
# The collar is printed telescope side down, and on that side the three rear
# bosses stand out by H_boss_insert from the flange: on the bed ONLY THEY
# rested, 269 mm2 in three islands, with the whole flange hanging two
# millimetres above. The flat bottom fills those two millimetres over the whole
# footprint of the flange, so the part is born resting on 3,638 mm2.
#
# Filling everything is not possible, and it is not a hypothesis: measured on
# the assembly, in that layer there are already the paddles of the sensor
# bracket (733 mm3) and the three rear ears of the box (226 mm3), which sit on
# the face of the flange at z 26. The bottom leaves each its pocket, and the
# floor of the pocket stays the resting face of before: bracket and box do not
# move by a tenth, and the air gap does not change.
#
# The pockets locate nothing, and have clearance on purpose (Cl_pockets_bottom):
# the box is put in position by the bosses, the bracket by the magnet. The
# pocket of the bracket is its outline SWEPT over the whole slot of the
# collar, because the bracket turns on the magnet to go and catch the screws
# where they really are.
#
# It is joined here, together with the flange, and not at the end: so the
# slots, the aperture of the optical envelope and the holes of the inserts,
# which come later, go through it by themselves. Joined at the end, it would
# have plugged the holes of the inserts again.
_Hfp, _gtf = D["H_boss_insert"], D["Cl_pockets_bottom"]
col = col.union(sector(a0,a1,Rif,Re,Hc+Fl,_Hfp))

def ear_pocket(ang):
    """The place of the rear ear in the flat bottom: its outline
    (solids_box.orecchia) widened by the clearance, SWEPT along the direction
    in which the box goes in.

    The sweep is not a luxury. The pocket opened RADIALLY, but the ear does not
    arrive radially: the whole box goes in along Ang_entry_box, and the two
    ears at the ends - at -24 and at +67 degrees - are at forty-five degrees
    from that direction. Going in, they rubbed against the side of the pocket:
    21 mm3 measured per ear, a little tooth of flat bottom two millimetres high
    that stopped them. They were found assembling the printed parts, before
    any check saw them.

    It is swept in steps instead of with a single outline because the pocket
    is a sector of a ring, which is not convex: the box of the steps covers it
    all without having to build the envelope by hand. The step is fine
    compared with the width of the pocket (fourteen millimetres), so on the
    straight sides it leaves nothing and on the arcs it leaves fractions of a
    hundredth.
    """
    _Sao = D["Halfw_ear_box"] + math.degrees(_gtf/D["R_in_ear"])
    _base = sector(ang-_Sao, ang+_Sao, D["R_in_ear"]-_gtf, Re+1, Hc+Fl, _Hfp+1)
    _ai = math.radians(D["Ang_entry_box"])
    _ux, _uy = math.cos(_ai), math.sin(_ai)
    _lu = D["Travel_entry_box"]
    _n = int(math.ceil(_lu / 1.5))
    _t = _base
    for _i in range(1, _n + 1):
        _d = _lu * _i / _n
        _t = _t.union(_base.translate((_ux*_d, _uy*_d, 0)))
    return _t

def bracket_pocket():
    """The place of the sensor bracket in the flat bottom: its outline,
    widened by the clearance and swept over the whole rotation that the slots
    of the collar allow it, one degree at a time. Between one step and the
    next the envelope loses at most r*(1-cos 0.5 degrees), three thousandths
    at r 86: nothing, against half a millimetre of clearance."""
    from drawings import bracket_outline
    from drawings_assembly import from_bulge
    _f = cq.Wire.makePolygon([cq.Vector(x, y, Hc+Fl) for x, y in
                              from_bulge(bracket_outline(), 0.3)], close=True)
    _f = _f.offset2D(_gtf)[0]
    _base = cq.Workplane("XY").add(cq.Solid.extrudeLinear(
        cq.Face.makeFromWires(_f), cq.Vector(0, 0, _Hfp+1)))
    _n = int(math.ceil(2*_Sac))
    t = None
    for i in range(_n+1):
        _g = D["Ang_bracket_sensor"] - _Sac + 2*_Sac*i/_n
        _r = _base.rotate((0, 0, 0), (0, 0, 1), _g)
        t = _r if t is None else t.union(_r)
    return t

_Sac = D["Halfw_slot_collar"]
# THE POCKETS OF THE EARS ARE GONE. They received the bosses of the box when
# the box was a part of its own slid on top; now box and collar
# are printed together (see solids_box_collar.py) and there is nothing left to
# slide on nor to put in position. Removed also because a pocket that receives
# nothing is an invitation to break: an ear of a printed collar snapped while
# being slid in.
_bracket_pk = bracket_pocket()
col = col.cut(_bracket_pk)
# THE SKIN THE POCKET LEAVES AT THE OUTER FACE (check_thin). The
# paddles of the bracket reach almost to the rim of the collar, and their
# swept pocket stops a few tenths short of Re: between pocket and outside a
# skin 0.2-0.4 mm thick and two millimetres tall was left, the top layers of
# the part (it prints roof up), along six degrees at each paddle. It holds
# nothing - the bracket is located by the magnet - and printed it is one
# loose line. So wherever the pocket comes within Th_min_wall_printing of the
# outer face, the band between it and the outside goes, with radial ends: at
# the ends the skin is that thick. The angles are MEASURED on the pocket
# solid, not written: the pocket follows the bracket and its sweep.
_tm = D["Th_min_wall_printing"]
_near = _bracket_pk.intersect(sector(a0, a1, Re - _tm, Re + 1, Hc + Fl - 1, _Hfp + 3))
for _so in _near.val().Solids():
    _angs = []
    for _e in _so.Edges():
        for _k in range(21):
            _p = _e.positionAt(_k/20.0)
            _angs.append(math.degrees(math.atan2(_p.y, _p.x)))
    col = col.cut(sector(min(_angs), max(_angs), Re - _tm, Re + 1, Hc + Fl - 0.01, _Hfp + 1))
    print("bracket pocket: skin under %.1f mm at the rim taken away, %.1f..%.1f degrees"
          % (_tm, min(_angs), max(_angs)))
# gasket grooves on the two contact faces: the front one deviates, the rear
# one does not - the numbers are on the camera face and on the other side
# there is nothing to read, so it makes no sense to weaken that seal too.
col = col.cut(band(lambda a: r_groove(a)-lg/2, lambda a: r_groove(a)+lg/2, -pg, pg))
col = col.cut(sector(a0,a1,Rg-lg/2,Rg+lg/2,Hc,pg))

# ---------------- the numbers window ----------------
# IT STAYS OPEN, AND IT IS A CHOICE, not an oversight. In six months a through
# hole towards the optical train will look like a slip, so it is written here
# why it is not.
#
# First: the light path existed before us. The bought body already has its
# window, open, and it is modelled above: plugging it on our side would close
# nothing, it would only close our half of a passage that stays open on the
# other. Second, and more interesting: a window blind to light is blind to the
# DIGIT as well. To read a number light is needed above it, so a labyrinth
# that does not let the light through does not let the image through either -
# it is the paradox that had that road discarded too, not only the transparent
# insert.
#
# Discarded therefore: transparent insert, co-printed or glued, and labyrinth.
# The opening is the maker's, made again the same.
#
# Rectangle with filleted corners, from the radii of the window of the body,
# and chamfered on both faces. The face towards the camera is the one it is
# looked at from, and a sharp edge there casts a shadow on the digit; the one
# towards the body is a sealing face, and a sharp edge on a sealing face is a
# blade.
#
# Printing the collar telescope side down this flange faces UP, so the window
# is a through hole in a horizontal plane: it has no roof and asks for no
# support. The upper chamfer prints by itself, the lower one is at 45 degrees.
_Rwi, _Rwo = D["R_in_window_numbers"], D["R_out_window_numbers"]
_Lw, _chw, _rcw = D["L_window_numbers"], D["Ch_window_numbers"], D["Fil_window_numbers"]
_cxw = (_Rwi + _Rwo)/2

def _window_pts(widen):
    w, l = (_Rwo-_Rwi)/2 + widen, _Lw/2 + widen
    rc = min(_rcw + widen, w-0.05, l-0.05)
    pts = []
    for (sx, sy), a_in in (((1,1),0), ((-1,1),90), ((-1,-1),180), ((1,-1),270)):
        cx0, cy0 = sx*(w-rc), sy*(l-rc)
        for k in range(9):
            ang = math.radians(a_in + 90.0*k/8)
            pts.append((_cxw + cx0 + rc*math.cos(ang), cy0 + rc*math.sin(ang)))
    return pts

def _window_prism(widen, z, h):
    return (cq.Workplane("XY").workplane(offset=z)
            .polyline(_window_pts(widen)).close().extrude(h))

def _taper(a_low, z_low, a_high, z_high):
    return (cq.Workplane("XY").workplane(offset=z_low)
            .polyline(_window_pts(a_low)).close()
            .workplane(offset=z_high-z_low)
            .polyline(_window_pts(a_high)).close().loft(ruled=True))

_win = _window_prism(0.0, -Fl-1.0, Fl+2.0)
# The chamfer is INSIDE the thickness of the flange, not below it: from z -2.2
# to z -3 it widens. Put below the face, as it once was, the cone is in
# the air and cuts nothing - measured, the mouth stayed at exactly 66.21.
_win = _win.union(_taper(0.0, -Fl+_chw, _chw, -Fl))        # camera-side chamfer
# On the SEALING face the chamfer does not go, and it is not an oversight:
# widening the mouth right at z 0 would eat the lip that separates the bead
# from the opening. Measured with the chamfer: the lip went down from 1.50 to
# 0.70. There the edge stays sharp, and it is harmless - it is a flat face
# pressed against the body, not an edge someone touches.
# The chamfer must NOT go beyond the outer edge of the window: out there, at
# r 71, the labyrinth rib starts, and a chamfer that bites into it takes away
# exactly the reserve barrier that this face has more than the other.
# Measured before adding this cut: the rib was eaten by three tenths and the
# lip at 70..71 disappeared completely.
_win = _win.intersect(cq.Workplane("XY").workplane(offset=-Fl-2.0)
                      .center(_Rwo/2 - 10.0, 0).rect(_Rwo + 20.0, 3*_Lw)
                      .extrude(Fl+4.0))
# Turned to Ang_window_numbers, which the groove's deviation above already
# followed while the window itself stayed drawn at zero: the angle was one
# number read in one place out of two (it showed when it stopped being 0).
col = col.cut(_win.rotate((0, 0, 0), (0, 0, 1), _A_win))
# aperture for the friction wheel
#
# The two z dimensions are NO LONGER written in here. They were -1.5 below and
# +3 above, chosen by hand and unrelated to the half width, which was in turn a
# 15 degrees chosen by hand: three independent numbers that gave 1.5 mm of
# clearance without anyone having decided it, and that on a test print showed
# up almost flush. Now window and clutch have one single link,
# Cl_aperture_clutch, and the window moves along with the clutch if the clutch
# changes.
#
# The lower edge goes down for a second reason too, which shows only on the
# solid: between this cut and the one of the rib below a SHELF of 0.5 mm was
# left (z 3.0..3.5), as wide as the window and as deep as the band, attached
# only at its two ends. A flake like that in ASA prints badly and comes off in
# the hand. With the lower edge at Q_top - clearance the two cuts overlap and
# the flake is gone.
al=D["Ang_aperture_clutch"]; gl=D["Cl_aperture_clutch"]
col = col.cut(sector(-al,al,Rc-2,Re+2,D["Z_top_clutch"]-gl,D["H_hub_clutch"]+2*gl))
# ...and above the hub passes the GRUB COLLAR, which is on top and no longer
# below. It is much narrower than the tread - Ø25 against
# Ø50 - so it takes away less than a third of the material that raising the
# window over its whole width would take away. Right there the band carries
# the upper flange, and it does not pay to thin it more than needed.
_ag = D["Ang_aperture_grub"]
_z_top_clutch = D["Z_base_collar_grub"] + D["H_collar_grub"]
col = col.cut(sector(-_ag, _ag, Rc-2, Re+2,
                   D["Z_top_clutch"] + D["H_hub_clutch"] - gl,
                   (_z_top_clutch + gl) - (D["Z_top_clutch"] + D["H_hub_clutch"] - gl)))
# M3 slots in the rear flange: they go through the flat bottom too
_Sac = D["Halfw_slot_collar"]
for av in (D["Ang_screw_A"], D["Ang_screw_B"]):
    col = col.cut(sector(av-_Sac,av+_Sac,D["R_screw_anchor"]-1.7,D["R_screw_anchor"]+1.7,
                       Hc-1,Fl+_Hfp+2))
# labyrinth rib that goes into the front slot
sc=D["Dp_slot_front"]; sl=D["Th_rib_labyrinth"]
cs=D["Chord_slot"]
# The rib is born from the inner face of the flange, which the groove SETS
# BACK: if it keeps starting from zero it floats in front of it, and it is the
# third of the three detached bodies. So it starts from the true face and is
# lengthened by as much, so its tip - the one that goes into the slot of the
# body - stays where it was.
_zcl = -D["Cl_groove_collar"]
col = col.union(cq.Workplane("XY").workplane(offset=_zcl).center(Rc-sc+0.5+sl/2, 0)
                .rect(sl, cs-3).extrude(D["H_rib_labyrinth"] - _zcl))
col = col.cut(sector(-al,al,Rc-6,Re+2,-1,D["H_rib_labyrinth"]+1))
# THE TWO TIPS OF WHAT IS LEFT OF THE RIB across the window (check_thin).
# The cut above keeps the rib only inside r Rc-6, so across the
# window the rib is a lens between its straight inner face (x = Rc-sc+0.5) and
# that circle, and the lens ends in two knife tips, 0 to 0.8 mm wide over
# three millimetres each side, standing 3.5 mm tall: a single line of the
# slicer, or nothing. They go, whole, from where the lens is
# Th_min_wall_printing wide out to the edge of the window, with radial ends -
# so at the end the lens is exactly that wide. The labyrinth loses 3 mm of rib
# each side, where it was a hair anyway. Only the rib is cut (intersected with
# its own block), nothing else of the collar.
_x_rib = Rc - sc + 0.5                                     # inner face of the rib
_x_k = _x_rib + D["Th_min_wall_printing"]
if (Rc - 6)**2 > _x_k**2:
    _a_k = math.degrees(math.atan2(math.sqrt((Rc - 6)**2 - _x_k**2), _x_k))
    _rib = (cq.Workplane("XY").workplane(offset=_zcl - 0.5).center(Rc-sc+0.5+sl/2, 0)
                .rect(sl + 0.02, cs - 3 + 0.02).extrude(D["H_rib_labyrinth"] - _zcl + 1.0))
    for _s in (-1, 1):
        _a0, _a1 = sorted((_s*_a_k, _s*al))
        col = col.cut(_rib.intersect(sector(_a0, _a1, Rc - 12, Re + 2,
                                              _zcl - 1, D["H_rib_labyrinth"] - _zcl + 2)))
    print("labyrinth rib: tips under %.1f mm taken away from %.1f to %.1f degrees"
          % (D["Th_min_wall_printing"], _a_k, al))
# pivot hub + pin
Rp=D["R_pivot"]; ap=math.radians(D["Ang_pivot"])
px,py=Rp*math.cos(ap), Rp*math.sin(ap)
# The hub stands BACK by Setback_face_hub from the face of the hub of the arm,
# and has a spot face for the flange of the bearing. The two things together
# decide who rubs against whom: the arm turns on this joint under the preload
# of the spring, and ASA against ASA would mean friction and dust exactly where
# it has to move freely. Setting the face back, what is left rubbing is only
# the smooth steel of the flange, which is also what H_bearings says: the
# flanges are the axial reference.
#
# Without the spot face the body-side flange ended up INSIDE this hub: 157 mm3
# of interpenetration, that is the volume of the whole flange, found when
# assembling.
_setb, _spf = D["Setback_face_hub"], D["Th_flange_bearing"]
# Everything round the pivot starts from the TOP FACE OF THE ARM, not from z 0:
# the arm now stands at Z_top_arm. The setback, the spot face,
# the top of the pin and the foot of the support were all counted from a
# literal 0, and would have stayed two millimetres below the arm.
_zta = D["Z_top_arm"]
# THE SUPPORT OF THE PIVOT: it rises up to the roof of the compartment and
# blends into the band.
#
# Before it was 9.8 mm tall and joined the band edge-on, with too little
# surface in contact with the collar. TWENTY tall was tried and does not fit: at z 16 the roof
# of the mechanical compartment closes (Z_shoulder_box), and that roof had
# already been LOWERED by ten millimetres on purpose to lighten the box, so
# raising it would undo a choice already made. 15.3 fit, 56% more than before.
#
# THE SHAPE: ONE CYLINDER, Ø D_hub_pivot, from the arm up into the roof - not
# flared, a continuous cylinder. It used to be
# a cylinder up to Z_start_cone_support and a cone narrowing to Ø11.5 at the
# top: the cone was there so as not to leave a flat Ø21 shoulder facing the
# bed. Since the column goes into the roof slab (Z_top_support_pivot is half
# way through it) there is no shoulder any more - the top of the cylinder is
# inside the roof - and the cone was only material taken away from the part
# that carries the moment of the arm. Four parameters went with it
# (D_top_support_pivot, Z_start_cone_support, Ang_min_side_support,
# Marg_ang_side_support); check_audit now measures that the radius does not
# change with height.
#
# THE GROOVE towards the band is what the sketch asks for. It is not a
# fillet: OCCT's fillet on this geometry CRASHES the process - signal
# 139, tried with radii from 3 to 0.6 - because the curve where the cone meets
# the band is a BSPLINE 33 mm long. It is built instead geometrically, and it
# is tangent BY CONSTRUCTION: the profile is three arcs - the one of the
# support, the one of the band and the blending arc of radius R tangent to
# both - and the centre of the blend is the point at R+r from the support and
# R+Rf from the axis of the wheel. The sections are stacked in a loft, so the
# groove FADES going up along the cone instead of ending with an edge: a sharp
# edge would face the bed, and would be another piece of roof to support.
_qc = D["Z_top_support_pivot"]
_Rm = D["D_hub_pivot"]/2
_Rout = D["R_out_collar"]
_Rr = D["R_fillet_support_pivot"]
_qbo = D["Z_mouth_insert_pivot"]

_sup = (cq.Workplane("XY").workplane(offset=_zta + _setb).center(px, py)
        .circle(_Rm).extrude(_qc - (_zta + _setb)))


def _r_support(z):
    """Radius of the support at height z: the same at all heights."""
    return _Rm


def _groove_profile(rm, side):
    """The three arcs of the groove between the support (radius rm around the
    pivot) and the outer face of the band. Returns None where the support no
    longer touches the band: there the groove does not exist and the loft
    stops."""
    d = math.hypot(px, py)
    u = (px/d, py/d); w = (-u[1]*side, u[0]*side)
    _a = ((_Rout + _Rr)**2 - (rm + _Rr)**2 + d*d)/(2*d)
    _hq = (_Rout + _Rr)**2 - _a*_a
    _a2 = (_Rout*_Rout - rm*rm + d*d)/(2*d)
    _h2q = _Rout*_Rout - _a2*_a2
    if _hq <= 0 or _h2q <= 0:
        return None
    _h, _h2 = math.sqrt(_hq), math.sqrt(_h2q)
    C = (_a*u[0] + _h*w[0], _a*u[1] + _h*w[1])
    X = (_a2*u[0] + _h2*w[0], _a2*u[1] + _h2*w[1])
    Tm = (px + (C[0]-px)*rm/(rm+_Rr), py + (C[1]-py)*rm/(rm+_Rr))
    Tf = (C[0]*_Rout/(_Rout+_Rr), C[1]*_Rout/(_Rout+_Rr))

    def _mid(c, r, p, q):
        v = []
        for t in (p, q):
            dx, dy = t[0]-c[0], t[1]-c[1]
            n = math.hypot(dx, dy)
            v.append((dx/n, dy/n))
        mx, my = v[0][0]+v[1][0], v[0][1]+v[1][1]
        n = math.hypot(mx, my)
        if n < 1e-9:
            return None
        return (c[0] + r*mx/n, c[1] + r*my/n)
    Mm, Mf, Mr = _mid((px, py), rm, Tm, X), _mid((0, 0), _Rout, X, Tf), _mid(C, _Rr, Tf, Tm)
    if None in (Mm, Mf, Mr):
        return None
    return Tm, Mm, X, Mf, Tf, Mr


# The heights of the loft stop where the support goes into the band by less
# than half a millimetre: below that threshold the two circles are almost
# tangent, the profile thins down until it degenerates and the loft has nothing
# left to stack. The threshold is on the SOLID - the true penetration - not on
# a dimension written by hand, so it follows the cone if the cone changes.
_z_groove = []
_z = _zta + _setb
while _z <= _qc:
    if _r_support(_z) >= (Rp - _Rout) + 0.5:
        _z_groove.append(_z)
    _z += 0.5
# the section does not change with height any more: bottom and top suffice
_groove_levels = [_z_groove[0], _z_groove[-1]]
_groove_levels = sorted(set(round(_q, 3) for _q in _groove_levels if _q <= _z_groove[-1]))
for _side in (+1, -1):
    _wp = cq.Workplane("XY")
    _prev, _n = 0.0, 0
    for _z in _groove_levels:
        _p = _groove_profile(_r_support(_z), _side)
        if _p is None:
            continue
        Tm, Mm, X, Mf, Tf, Mr = _p
        _wp = (_wp.workplane(offset=_z - _prev)
               .moveTo(*Tm).threePointArc(Mm, X).threePointArc(Mf, Tf)
               .threePointArc(Mr, Tm).close())
        _prev, _n = _z, _n + 1
    if _n < 2:
        raise SystemExit("the groove of the pivot support: not enough sections")
    _sup = _sup.union(_wp.loft(ruled=True))
col = col.union(_sup)
# Setback and spot face are dug over the WHOLE collar and not only on the hub,
# because on this side the cylindrical band passes underneath too: digging
# only the hub, the flange kept hitting against it by 12.4 mm3, and the face
# of the hub of the arm would have rubbed on it all the same.
# Both cuts start from exactly z=0: a tenth lower and they would eat the front
# flange, which ends right there.
col = col.cut(cq.Workplane("XY").workplane(offset=_zta - 0.01).center(px,py)
              .circle(D["D_hub_pivot"]/2).extrude(_setb + 0.01))
col = col.cut(cq.Workplane("XY").workplane(offset=_zta - 0.01).center(px,py)
              .circle(D["D_spotface_hub"]/2).extrude(_spf + 0.01))
# THE PIN IS NO LONGER PART OF THE COLLAR: the washer is joined to the part
# inside the bearings. Before, a Ø5 pin stood out
# of the spot face down to Z_bottom_arm, and the arm had to be slid onto it -
# in the one-piece part, inside a closed compartment. Now the pin is a BUSHING
# printed on the washer: the arm with its bearings is held under the hub, and
# the bushing goes up through the bearings from below, with the screw inside.
# The collar keeps the spot face, whose floor is where the bushing stops, and
# the bore for the screw. See the washer at the end of this file.
_z_tip = D["Z_bottom_arm"]

# ---------------- the reinforced pivot ----------------
# The pivot was a Ø5 ASA cantilever overhanging for nine millimetres, with the
# layer lines crossed right at the root - that is, the point that breaks, made
# in the worst direction. Now it is bored lengthwise and an M3 screw goes
# through it, like a rebar in concrete: the plastic stops being the structure
# and becomes the sleeve the bearings turn on.
#
# What it is worth, in stiffness: ASA is around 2 GPa, steel around 200. The
# solid ASA pivot gives E*I of about 61,000 N mm2; bored at 3.2 the tube that
# is left gives 51,000; the core of an M3 gives 383,000. Together they are
# 434,000, that is seven times the one before, and nine tenths of that number
# are steel.
#
# The insert is at the TOP of the hub, not at the root of the pivot. At the
# root the screw would stop exactly where the moment is maximum and would leave
# that stretch uncovered; from the top instead the screw goes through the whole
# root and the whole overhang, which is what is needed. It wants a long screw:
# from the bottom of the washer to the top of the hub there are about twenty
# millimetres, so a catalogue M3 x 20.
#
# ATTENTION, and it holds for everything that follows: the tightened screw puts
# the pivot in compression, where FDM is strong - but ASA under constant load
# CREEPS, and within months the preload goes away by itself. So the design must
# not depend on it: the steel is the reinforcement, and it must work with the
# screw loose too. The tightening only serves to hold the stack together, not
# to stiffen.
_z_top = D["Z_mouth_insert_pivot"]                  # top face of the hub
col = col.cut(cq.Workplane("XY").workplane(offset=_z_tip-1).center(px,py)
              .circle(D["D_clear_screw_pivot"]/2)
              .extrude(_z_top - D["Dp_seat_insert_M3_pivot"] - (_z_tip-1)))
col = col.cut(cq.Workplane("XY")
              .workplane(offset=_z_top - D["Dp_seat_insert_M3_pivot"]).center(px,py)
              .circle(D["D_hole_insert_M3"]/2).extrude(D["Dp_seat_insert_M3_pivot"]))
# The lead-in starts half a millimetre above the face, in the air: a cone
# coplanar with the face leaves splinters on the edge.
col = col.cut(cq.Workplane(obj=cq.Solid.makeCone(
    D["D_leadin_insert_M3"]/2 + 0.5, D["D_hole_insert_M3"]/2,
    D["Dp_leadin_insert_M3"] + 0.5,
    cq.Vector(px, py, _z_top + 0.5), cq.Vector(0, 0, -1))))
# THE CHANNEL OF THE SOLDERING IRON. The support now rises above the mouth of
# the insert, so above it the road is needed for the tip that plants it: the
# seat of a heat-set insert is designed thinking of the TOOL, not only of the
# insert. The channel is straight and vertical - the tip comes down along the
# axis of the pivot, which is also the axis of the insert - and reaches out of
# the part.
#
# It is also the reason why the mouth stays at height 10 instead of rising to
# the top of the support: so the screw of the reinforced pivot stays a
# catalogue M3 x 20. Bringing the mouth to the top would have needed 26 under
# the head, a length that does not exist, and the screw would have ended up
# against the roof of the compartment.
# The channel is wider than the tip by Cl_tip_iron: the tip is red hot, and a
# wall that touches it while it comes down melts where it should not.
col = col.cut(cq.Workplane("XY").workplane(offset=_z_top).center(px, py)
              .circle(D["D_channel_iron_deep"]/2)
              .extrude(_qc + 1.0 - _z_top))
# The recess the arm passes through. Its three dimensions were written by hand
# - sector(-22, 54, Rc-0.5, ...) - and did not follow from the travel of the
# arm: angularly they were generous, but the inner radius stopped at 78.5
# while the arm, turning towards the disc to follow the wear of the TPU, dives
# down to 77.88. The arm touched the flange at -1.5 degrees, that is before
# having finished its useful travel, and no check noticed: the audit checked
# the other things AGAINST the sweep, never the sweep against this.
# Now the recess is the envelope of what the arm really sweeps.
_pa0, _pa1, _pri = CB.passage(D)
col = col.cut(sector(_pa0, _pa1, _pri, Re+1, -Fl-1, Fl+1))   # recess for the arm passage
# ...and ABOVE the arm the clearance is needed, which was not here. The recess
# above stops at z 0 because it is Fl+1 tall starting from -Fl-1: but z 0 is
# exactly the height of the top face of the arm, so the two faces stayed
# coplanar and the arm rubbed on the collar - 159 mm2, found moving the
# screwed part by hand, not by the audit, which measured the interpenetration, and
# between two faces that touch the interpenetration is zero.
#
# The setback starts at r = D_body/2: further in the collar rests on the face
# of the wheel body, and it is its resting plane, while further out it is a
# shelf that stands above the arm and nothing more. The measured contact was
# between r 80 and 86, that is all beyond that radius.
# Up to the top face of the arm plus the air, since the arm is raised to
# Z_top_arm: from z 0 to there the collar band is hollowed where
# the arm passes, between D_body/2 and the outside.
col = col.cut(sector(_pa0, _pa1, max(_pri, D["D_body"]/2), Re+1,
                   0.0, D["Z_top_arm"] + D["Free_above_arm"]))

col = col.cut(cq.Workplane("XY").workplane(offset=-Fl-2)          # rotator/reducer envelope
              .center(-D["Off_hole_optical"],0)
              .circle(D["R_envelope_optical"]).extrude(Hc+2*Fl+4))
# ---------------- fixing of the box: IT NO LONGER EXISTS ----------------
# Here were the six bosses with their M3 heat-set inserts, three per flange,
# which the box was screwed onto with its ears. They were there to carry the
# 22.3 N of the spring and the moment of 680 N mm that followed from it, and
# they were at two different heights on purpose to make a couple.
#
# They carry nothing any more: box and collar are the same
# part, and that moment is carried by the material. With them 5 M3 screws and
# 5 heat-set inserts leave the BOM - ten pieces of hardware and ten chances to
# get the assembly wrong.
#
# The two screw_M3_collar do NOT go: those did not hold the box, they go into
# the M3 holes already in the back plate of the wheel and also clamp the
# paddles of the sensor bracket. They are the only thing that holds the machine
# on the wheel.

# ---------------- the gaskets, printed in TPU ----------------
# They are TWO different parts, not one printed twice: only the front one has
# the deviation around the window. And they are ARCS, not rings, because the
# collar is an arc of 162 degrees.
#
# On the two ends: they are not a weak point for light, and it is worth saying
# because it would seem so. Beyond the end of the arc there is not the dark on
# the other side of the seal: there is no collar at all. The light gets in
# there because the cover is missing, not because the bead ends - the seal is
# needed where the collar is. What the ends must do is not slip out, and that
# is why the retaining buttons are there too.
#
# THE PROFILE IS HOLLOW, and the reason is the closing force. A solid bead of
# 3 in the 1.5 groove would be squeezed by 50%: on TPU 95A it wants an
# outrageous force, which the collar pays - and it is ASA - and which goes onto
# the screws and onto a long cantilevered flange. Hollow, the same seal is
# obtained with 25% squeeze and a fraction of the force. And the void is needed
# for another thing too: rubber is incompressible, so what is squeezed has to
# go somewhere, and a groove filled 100% does not close. With this profile the
# groove stays 82% full at rest.
#
# It is printed FLAT on the bed: so the compression travels ACROSS the layers
# and does not separate them, which is the good direction for a part that
# works squeezed. The roof of the cavity is two slopes at 45 degrees and not
# flat, so it does not want support: the bridge that is left is half a
# millimetre wide.
_Lgk, _Hgk = D["L_gasket"], D["H_gasket"]
_Lcav, _Hcav = D["L_cavity_gasket"], D["H_cavity_gasket"]
_Llab, _Hlab = D["L_lip_gasket"], D["H_lip_gasket"]
_z_cav = pg - _Hcav - 0.3          # the roof of the cavity stays 0.3 below the lip


def _w_out(h):
    """Half width of the profile at that height from the bottom of the groove."""
    if h < pg: return _Lgk/2
    if h < _Hgk - 0.2: return _Llab/2
    return max(0.05, _Llab/2 - (h - (_Hgk - 0.2)))       # top rounded at 45


def _w_cav(h):
    """Half width of the inner cavity: zero where there is none."""
    if h < 0.4 or h >= _z_cav + _Hcav: return 0.0
    if h < _z_cav + _Hcav - _Lcav/2 + 0.3: return _Lcav/2
    return max(0.0, _Lcav/2 - (h - (_z_cav + _Hcav - _Lcav/2 + 0.3)))


def gasket(f_radius, z_bottom, direction, step_z=0.1):
    """The gasket, built in slices of height.

    Each slice is a band of variable radius, the same shape the groove is dug
    with: so the gasket follows the deviation by construction, instead of
    having to bend. That is why the minimum bending radius is no longer the
    constraint - see the comment of the groove.
    """
    body = None
    h = 0.0
    while h < _Hgk - 1e-9:
        hm = h + step_z/2
        we, wc = _w_out(hm), _w_cav(hm)
        z0 = z_bottom + direction*h if direction > 0 else z_bottom - (h + step_z)
        slice_ = band(lambda a, w=we: f_radius(a) - w,
                      lambda a, w=we: f_radius(a) + w, z0, step_z)
        if wc > 0:
            slice_ = slice_.cut(band(lambda a, w=wc: f_radius(a) - w,
                                    lambda a, w=wc: f_radius(a) + w, z0-0.01, step_z+0.02))
        body = slice_ if body is None else body.union(slice_)
        h += step_z
    return body


# The front one follows the deviation, the rear one does not: they are two
# different parts and not the same one printed twice.
# The direction: in front the groove has its bottom at -pg and its mouth at
# z 0, so the gasket grows towards +z; at the rear the bottom is at Hc+pg and
# the mouth at Hc, so it grows towards -z. Swapped, the two parts were born
# outside the groove and interpenetrated the collar by 620 mm3 - that is their
# whole volume.
gk_front = gasket(r_groove, -pg, +1)
gk_rear = gasket(lambda a: Rg, Hc + pg, -1)

# THE COLLAR ENDS ON THE PLANE OF THE HEAD. The outer face of the box head - the flat face that carries the
# USB and the GX12 - is a plane, and the collar ran on past it by a wedge of
# about five degrees, 72 to 78 at its outer radius. Cut there, the head face is
# ONE flat face from the box floor across the collar, a candidate face to put
# on the print bed. The gaskets run to the end of the collar
# in its grooves, so they are cut on the same plane, or they would stand out
# of it. Only the positive-s side is cut: the collar never reaches the far side
# of the plane, and a half space that went round would take the whole ring.
import electronics as _E
def _beyond_head():
    return cq.Workplane(obj=cq.Solid.makeBox(300.0, 200.0, 200.0,
                                             cq.Vector(0.0, _E.T_HEAD_OUT, -100.0))
                        .rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), _E.A_BOARD))
_gk_section = gk_front.val().Volume() / (math.radians(a1-a0) * Rg)   # before the cut
gk_front = gk_front.cut(_beyond_head())
gk_rear = gk_rear.cut(_beyond_head())
cq.exporters.export(gk_front, OUT + "front_gasket.step")
cq.exporters.export(gk_rear, OUT + "rear_gasket.step")

print("gasket: profile %.2f x %.2f, section %.2f mm2 of %.2f of groove = %.0f%% full"
      % (_Lgk, _Hgk, _gk_section, lg*pg, 100*_gk_section/(lg*pg)))
print("   squeeze when closed %.1f%% (lip %.1f of height %.1f), TPU %.0f shore A"
      % (100*_Hlab/_Hgk, _Hlab, _Hgk, D["Shore_gasket"]))

# THE COLLAR IS NO LONGER A PRINTED PART. It goes in out/references/ because
# whoever opens out/ to send to print must not find it there: it is half of
# the one-piece part, and printing it alone would mean throwing away an hour.
# The one that joins it and puts the gaskets in is solids_box_collar.py, which
# runs afterwards.
from parameters import out_subdir
col = col.cut(_beyond_head())                  # on the plane of the head: see above
cq.exporters.export(col, OUT + out_subdir("collar") + "collar.step")

# --- the CO-PRINTED part is no longer made here -----------------------------
# The gaskets are still printed together with the ASA they rest on, but that
# ASA is now the whole one-piece part and not the collar alone: the file for
# the IDEX is written by solids_box_collar.py, which is the only one holding
# the whole part.

# ---------------- pivot washer ----------------
# It is not bought, it is printed to size, and the size is not a whim: a
# hardware-store M3 washer is 7 outside but above all it is thin, and here the
# outer diameter is constrained by something that does not exist on normal
# washers. The flanges of the F695ZZ stand out one millimetre from the faces of
# the hub of the arm and are part of the OUTER RING: anything resting on them
# locks the bearing. So the washer must press ONLY on the inner ring, and pass
# inside the hole of the flange without brushing it.
#
# And it does a third job that cannot be guessed by looking at it: IT RETAINS
# THE ARM AXIALLY. Today the arm is retained by nothing - upwards it is stopped
# by the spot face of the hub, downwards nothing - and it slides off the pivot.
# Tightening the washer against the inner rings, the stack stays on the pivot
# and the arm with it.
#
# On creep, again: the washer must not get squashed. Under the head of an M3
# tightened by hand there are hundreds of newtons on a few square millimetres,
# that is tens of MPa, close to the yield of ASA. Here the screw does not bottom
# out on the plastic: the face of the pivot and that of the inner ring are
# coplanar, so the stack closes on the STEEL of the rings, which does not
# yield, and the washer is clamped between two hard faces instead of being the
# only thing that opposes the pull.
#
# AND IT CARRIES THE BUSHING: the Ø5 sleeve the bearings turn
# on, which used to be the pin of the collar. Printed with the washer it prints
# standing on the washer's face, so the long Ø3.4 hole comes out along its own
# axis, and the sleeve is loaded across its layers only by the bearings, which
# is compression and not the bending at the root the pin used to take.
#
# ITS LENGTH IS CRITICAL and it is not written by hand: from the top of the
# washer (Z_bottom_arm) to the floor of the spot face in the collar
# (Z_top_arm + Th_flange_bearing), i.e. L_bushing_pivot = H_bearings +
# Th_flange_bearing. Tightening the screw closes the stack on the BUSHING,
# against the collar, and not on the bearings: that is what the shoulder of
# the pin did before, and the job moves with the bushing. Shorter, and the
# screw would squeeze the inner rings against the collar; longer, and the
# washer would stand off the inner ring and the arm would have play.
_z_washer = D["Z_bottom_arm"] - D["Th_washer_pivot"]
_z_bushing = D["Z_top_arm"] + D["Th_flange_bearing"]
if abs(D["Z_bottom_arm"] + D["L_bushing_pivot"] - _z_bushing) > 1e-6:
    raise SystemExit("the pivot bushing is %.2f long and from the washer to the floor "
                     "of the spot face there are %.2f: the stack would close on the "
                     "bearings or would leave play"
                     % (D["L_bushing_pivot"], _z_bushing - D["Z_bottom_arm"]))
_washer = (cq.Workplane("XY").workplane(offset=_z_washer)
         .center(px, py).circle(D["D_washer_pivot"]/2)
         .extrude(D["Th_washer_pivot"])
         .union(cq.Workplane("XY").workplane(offset=D["Z_bottom_arm"] - 0.01)
                .center(px, py).circle(D["D_pivot_arm"]/2)
                .extrude(_z_bushing - D["Z_bottom_arm"] + 0.01)))
# a lead-in at the top of the bushing, 45 degrees: it is the end that has to
# find the bore of two bearings held by hand
_ci = D["Ch_bushing_pivot"]
_washer = _washer.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
    D["D_pivot_arm"], _ci + 1.0, cq.Vector(px, py, _z_bushing - _ci)).cut(
    cq.Solid.makeCone(D["D_pivot_arm"]/2, D["D_pivot_arm"]/2 - _ci - 1.0, _ci + 1.0,
                      cq.Vector(px, py, _z_bushing - _ci)))))
_washer = _washer.cut(cq.Workplane("XY").workplane(offset=_z_washer - 1)
                  .center(px, py).circle(D["D_hole_washer_pivot"]/2)
                  .extrude(_z_bushing - _z_washer + 2))
cq.exporters.export(_washer, OUT + "pivot_washer.step")

_l_screw = (_z_top - (D["Z_bottom_arm"] - D["Th_washer_pivot"]))
print("body %.0f cm3 | disc %.0f cm3 | collar %.1f cm3 (%.0f g ASA)"
      % (body.val().Volume()/1000, disc.val().Volume()/1000,
         col.val().Volume()/1000, col.val().Volume()*1.07e-3))
print("reinforced pivot: through hole %.1f, M3 insert at the top of the hub;"
      " %.1f mm needed under the head -> M3 x 20 screw" % (D["D_clear_screw_pivot"], _l_screw))
print("pivot washer with the bushing: %.1f x %.1f, bushing Ø%.1f x %.1f, hole %.1f (%.2f cm3)"
      % (D["D_washer_pivot"], D["Th_washer_pivot"], D["D_pivot_arm"], D["L_bushing_pivot"],
         D["D_hole_washer_pivot"], _washer.val().Volume()/1000))
