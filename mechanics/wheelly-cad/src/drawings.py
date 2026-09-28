# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

# The texts placed in the DXF (add_text), the layer names and the CSV header
# are outputs and stay as they are; only names and comments are English here.

import math, ezdxf, csv
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT + "drawings", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
import parameters as params
from parameters import P, D
from outline_arm import outline as arm_outline
import true_shape

R = math.radians; deg = math.degrees
B90 = math.tan(math.radians(90)/4)

from dimension_signature import Msp as _Msp, APPID as APPID_DIM


def newdoc():
    d = ezdxf.new("R2010", setup=True); d.units = ezdxf.units.MM
    for n,c in (("PROFILO",7),("FORI",1),("COSTRUZIONE",8),("QUOTE",4)):
        d.layers.add(n, color=c)
    return d, _Msp(d.modelspace(), d)

def pol(cx,cy,r,a): return (cx+r*math.cos(R(a)), cy+r*math.sin(R(a)))

def datum_plan(m):
    """origin = optical axis, +X = the line joining the axes. The same on every plan."""
    m.add_line((-8,0),(D["Cd_motor"]+30,0), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_line((0,-8),(0,8), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle((0,0), 2.0, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("CENTRO DISCO (asse di rotazione) - origine comune", height=2.5,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((4,-7))

def datum_section(m):
    """origin = optical axis, X = radius, Y = global axial height."""
    m.add_line((0,-4),(0,D["H_body"]+4), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("CENTRO DISCO", height=1.5,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((1.5,-3))

def line_circle(p0,p1,c,rad):
    """first t in [0,1] on the segment p0->p1 that touches the circle (c,rad)"""
    dx,dy = p1[0]-p0[0], p1[1]-p0[1]
    fx,fy = p0[0]-c[0], p0[1]-c[1]
    a = dx*dx+dy*dy; b = 2*(fx*dx+fy*dy); cc = fx*fx+fy*fy-rad*rad
    disc = b*b-4*a*cc
    if disc < 0: return None
    s = math.sqrt(disc)
    for t in sorted(((-b-s)/(2*a), (-b+s)/(2*a))):
        if -0.02 <= t <= 1.02: return (p0[0]+dx*t, p0[1]+dy*t)
    return None

def arc_points(r, a0, a1, step=1.0):
    """The points of an arc from a0 to a1, both ends included.

    It exists because range() wants integers and only goes forward: with
    Ang_collar_pivot at 110 the third arc of the collar plan came out empty,
    and the outline closed with a straight chord in place of the band between
    90 and 110 degrees.
    """
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [pol(0, 0, r, a0 + (a1 - a0) * i / (n - 1)) for i in range(n)]


def base_screws():
    """The four M3 already threaded in the base of the wheel body.

    They are the same ones the collar takes up with its slots and to which the
    sensor bracket is anchored: the starting angle is Ang_screw_A, one only,
    because the solid used to say -40 and the gasket -30, and the holes did
    not fall in the same places.
    """
    return [(D["R_screw_anchor"], D["Ang_screw_A"] + 90 * k) for k in range(4)]


def bulge(c, p0, p1, ccw):
    a0 = math.atan2(p0[1]-c[1], p0[0]-c[0]); a1 = math.atan2(p1[1]-c[1], p1[0]-c[0])
    d = (a1-a0) % (2*math.pi) if ccw else -((a0-a1) % (2*math.pi))
    return math.tan(d/4)

# ================= 1) CLUTCH SECTION (revolution) =================
def d_profile(cx, cy, radius, chord):
    """The outline of a round cut by a chord, as a polyline with bulge.

    One place only for the milled shaft and for the hole that takes it: they
    are the same shape at two different radii, and both the clutch section and
    the assembly plan draw it. A TRUE arc, not a broken line.
    """
    w = math.sqrt(max(radius*radius - chord*chord, 0.0))     # half chord
    sweep = 2*deg(math.atan2(chord, w)) + 180.0              # the arc goes the long way round
    return [(cx - w, cy + chord, 0, 0, math.tan(R(sweep)/4)),
            (cx + w, cy + chord, 0, 0, 0)]


def clutch_hole_true_shape(m, cx, cy):
    """The shaft hole seen in plan, in true shape, with the shaft inside.

    It is needed because the section cuts the hub ALONG the axis: of a D hole,
    there, only the radius shows, and the flat - which is half of the design,
    because it is what mates with the flat milled on the shaft - does not show
    at all. Worse: the bore of the hole was drawn with the radius of the SHAFT
    instead of that of the hole, so the drawing declared a round Ø5.00 hole
    where the part has a Ø5.30 D hole. Whoever checked it with the calliper
    found two different numbers, neither of them wrong through his own fault.
    It came out comparing a hand drawing of the hole with the part.

    It is drawn with a TRUE ARC - a two-point polyline with bulge - and not
    with a broken line: the same rule as the other curved faces of the project.
    """
    rf = D["D_hole_clutch"]/2
    yc = D["Z_flat_hole"]                       # the chord, from the axis
    m.add_lwpolyline(d_profile(cx, cy, rf, yc),
                     format="xyseb", close=True, dxfattribs={"layer": "FORI"})
    # the shaft inside, as a reference: round and milled, in construction
    # line because it is not the part that gets printed
    ra, ya = D["D_shaft"]/2, D["Z_flat_shaft"]
    m.add_lwpolyline(d_profile(cx, cy, ra, ya),
                     format="xyseb", close=True, dxfattribs={"layer": "COSTRUZIONE"})
    m.add_line((cx - rf - 3, cy), (cx + rf + 3, cy), dxfattribs={"layer": "COSTRUZIONE"})
    m.add_line((cx, cy - rf - 3), (cx, cy + rf + 3), dxfattribs={"layer": "COSTRUZIONE"})
    for text, dy in (
            ("FORO ALBERO, vera forma (il piatto guarda il grano)", rf + 4.2),
            # the two lines sit lower than they would need to: between the
            # figure and them runs the LABEL of the dimension that the editor
            # draws on top, and without this room it covered them
            ("foro Ø%.2f, corda a %.2f dall'asse" % (2*rf, yc), -rf - 7.0),
            ("albero Ø%.2f, fresata a %.2f: resta %.2f di aria sul piatto"
             % (2*ra, ya, yc - ya), -rf - 9.0)):
        m.add_text(text, height=1.0,
                   dxfattribs={"layer": "QUOTE"}).set_placement((cx - rf - 3, cy + dy))


def clutch_section():
    d,m = newdoc()
    # rb is the radius of the HOLE, not of the shaft: they are two different
    # numbers - the hole carries the running clearance and the print
    # compensation - and here it used to say D_shaft/2, that is the drawing
    # said the hole is as big as the shaft.
    rb, rc, rs, rt = D["D_hole_clutch"]/2, D["D_hub_clutch"]/2, D["D_shoulders_clutch"]/2, D["D_clutch"]/2
    z0 = D["Z_top_clutch"]; hs = D["H_shoulder_clutch"]; hm = D["H_hub_clutch"]
    t0 = D["Z_plane_mid_disc"] - D["Th_clutch"]/2
    t1 = t0 + D["Th_clutch"]; f = D["R_fillet_tread"]
    Ia = D["Cd_motor"]
    X = lambda r: Ia - r            # from clutch radius to optical-axis radius
    m.add_lwpolyline([(X(rb),z0),(X(rc),z0),(X(rc),t0-hs),(X(rs),t0-hs),(X(rs),t0),
                      (X(rc),t0),(X(rc),t1),(X(rs),t1),(X(rs),t1+hs),(X(rc),t1+hs),
                      (X(rc),z0+hm),(X(rb),z0+hm)],
                     close=True, dxfattribs={"layer":"PROFILO"})
    m.add_lwpolyline([(X(rc),t0,0,0,0),(X(rt-f),t0,0,0,-B90),(X(rt),t0+f,0,0,0),
                      (X(rt),t1-f,0,0,-B90),(X(rt-f),t1,0,0,0),(X(rc),t1,0,0,0)],
                     format="xyseb", close=True, dxfattribs={"layer":"PROFILO"})
    m.add_line((Ia,z0-4),(Ia,z0+hm+4), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("asse frizione  X=Cd_motor", height=1.2,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Ia+1,z0+hm+5))
    m.add_lwpolyline([(0,D["Z_plane_mid_disc"]-D["Th_disc"]/2),
                      (D["R_disc"],D["Z_plane_mid_disc"]-D["Th_disc"]/2),
                      (D["R_disc"],D["Z_plane_mid_disc"]+D["Th_disc"]/2),
                      (0,D["Z_plane_mid_disc"]+D["Th_disc"]/2)],
                     close=True, dxfattribs={"layer":"COSTRUZIONE"})
    # the true-shape view of the hole, set apart below the section: the
    # section reaches down to z0 - 4 with the axis, so below it there is room
    clutch_hole_true_shape(m, Ia, z0 - 16.0)
    # the true shape: the clutch and the disc cut through the clutch's axis
    true_shape.draw(m, [("clutch_hub.step", ("y", 0.0)), ("clutch_tyre.step", ("y", 0.0)),
                           ("references/filter_disc.step", ("y", 0.0))],
                       (0.0, z0 - 26.0), 1.0, x_min=0.0)
    datum_section(m)
    for y,t in ((D["Z_plane_mid_disc"]-D["Th_disc"]/2,"faccia ant. disco"),
                (D["Z_plane_mid_disc"],"piano medio disco  Z_plane_mid_disc"),
                (D["Z_plane_mid_disc"]+D["Th_disc"]/2,"faccia post. disco")):
        m.add_line((0,y),(Ia+16,y), dxfattribs={"layer":"COSTRUZIONE"})
        m.add_text(t, height=0.9, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Ia+17,y-0.45))
    d.saveas(OUT + "drawings/clutch_section.dxf")

# ================= 2) ARM PLAN =================
def arm_plan():
    d,m = newdoc()
    Lb, Off, Rd, Ia = D["L_arm"], D["Off_pivot"], D["R_disc"], D["Cd_motor"]
    ux,uy = (Ia-Rd)/Lb, -Off/Lb          # local X unit vector, in global
    rot = deg(math.atan2(uy,ux))          # -68 degrees
    M = (Lb,0.0)
    half_h = D["Cd_holes_motor"]/2*math.sqrt(2)
    ang = [45-rot, 135-rot, 225-rot, 315-rot]
    H = [pol(M[0],M[1],half_h,a) for a in ang]
    # local -> global transform (origin on the optical axis)
    Px, Py = Rd, Off
    g = lambda p: (Px + p[0]*ux + p[1]*(-uy), Py + p[0]*uy + p[1]*ux)
    Og = (0.0, 0.0)
    # The outline is no longer rebuilt here: arm_outline gives it, the same
    # one the assembly view uses and that check_audit compares with the STEP.
    # The three copies of before looked alike as long as the arm was a wedge;
    # since the plate went straight along the spring's side they described
    # three different parts.
    m.add_lwpolyline([p+(0,0,0) for p in arm_outline(D)],
                     format="xyseb", close=True, dxfattribs={"layer":"PROFILO"})
    m.add_circle(g((0,0)), D["D_seat_bearings_printed"]/2, dxfattribs={"layer":"FORI"})
    m.add_circle(g((0,0)), D["D_pivot_arm"]/2, dxfattribs={"layer":"FORI"})
    m.add_circle(g(M), D["D_seat_centring"]/2, dxfattribs={"layer":"FORI"})
    m.add_circle(g(M), D["D_clear_shaft"]/2, dxfattribs={"layer":"FORI"})
    for i in range(4): m.add_circle(g(H[i]), D["D_holes_M3_printed"]/2, dxfattribs={"layer":"FORI"})
    # Here there used to be a Ø10 circle at Q, the spring attachment. It
    # looked like a spring seat and as such it ended up in the solid: a
    # cylinder of material centred on Q, where the spring never gets - its end
    # stops seventeen millimetres earlier, on the side of the plate. In its
    # place, the axis of the spring, which is what really passes through Q.
    Qg = g((D["Att_spring"], 0))
    m.add_line(Qg, g((D["Att_spring"], 30)), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("asse molla  Att_spring dal perno", height=2,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement(g((D["Att_spring"]+2, 32)))
    m.add_line(g((0,0)), g(M), dxfattribs={"layer":"COSTRUZIONE"})
    for r in (D["R_rim_inner"], Rd, D["D_body"]/2, D["R_out_collar"]):
        m.add_circle(Og, r, dxfattribs={"layer":"COSTRUZIONE"})
    datum_plan(m)
    # the true shape: the arm cut at its top face and through the spring tab
    # below it, where the two spring spigots are
    true_shape.draw(m, [("arm.step", ("z", 0.0)), ("arm.step", ("z", -10.0))],
                       (-60.0, -95.0))
    d.saveas(OUT + "drawings/arm_plan.dxf")

# ================= 3) COLLAR PLAN (window-side half) =================
def collar_plan():
    d,m = newdoc()
    ri, re = D["D_body"]/2, D["R_out_collar"]
    rs, ap, ao = D["R_out_box"], D["Ang_collar_pivot"], D["Ang_collar_opposite"]
    # The ends of the collar are not necessarily inside +-90: the band must be
    # drawn from where it starts to where it ends, not from -90 to 90.
    a_min, a_max = min(-ao, -90.0), max(ap, 90.0)
    pts = (arc_points(re, a_min, -ao) + arc_points(rs, -ao, ap) + arc_points(re, ap, a_max)
           + arc_points(ri, a_max, a_min))
    m.add_lwpolyline(pts, close=True, dxfattribs={"layer":"PROFILO"})
    datum_plan(m)
    Pp = (D["R_disc"], D["Off_pivot"])
    m.add_circle(Pp, D["D_hub_pivot"]/2, dxfattribs={"layer":"PROFILO"})
    m.add_circle(Pp, D["D_pivot_arm"]/2, dxfattribs={"layer":"FORI"})
    Mm = (D["Cd_motor"],0.0)
    m.add_circle(Mm, D["D_clutch"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle((0,0), D["R_disc"], dxfattribs={"layer":"COSTRUZIONE"})
    sc = D["Dp_slot_front"]; Rb = D["D_body"]/2
    dp = D["D_plane_opening"]; ca = D["Chord_opening"]; cs = D["Chord_slot"]
    m.add_line((dp,-ca/2),(dp,ca/2), dxfattribs={"layer":"COSTRUZIONE"})   # straight cut of the opening
    if abs((Rb-sc) - dp) > 0.05:      # with the slot on the plane of the opening it would be the same line
        m.add_line((Rb-sc,-cs/2),(Rb-sc,cs/2), dxfattribs={"layer":"COSTRUZIONE"})  # bottom of the slot
    rb0 = Rb - sc + 0.5; rb1 = rb0 + D["Th_rib_labyrinth"]
    m.add_lwpolyline([(rb0,-cs/2+1.5),(rb1,-cs/2+1.5),(rb1,cs/2-1.5),(rb0,cs/2-1.5)],
                     close=True, dxfattribs={"layer":"PROFILO"})
    m.add_text("apertura e scanalatura: tagli DRITTI (piani)", height=2.0,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((10, -95))
    # axis of the spring seat: through the attachment on the arm, perpendicular to the arm
    Lb = D["L_arm"]; t = D["Att_spring"]/Lb
    Qg = (Pp[0]+t*(Mm[0]-Pp[0]), Pp[1]+t*(Mm[1]-Pp[1]))
    ux,uy = (Mm[0]-Pp[0])/Lb, (Mm[1]-Pp[1])/Lb
    nx,ny = -uy, ux
    if nx*Qg[0]+ny*Qg[1] < 0: nx,ny = -nx,-ny
    m.add_line(Qg, (Qg[0]+nx*32, Qg[1]+ny*32), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle(Qg, D["D_washer_spring"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    for s in (-1,1):
        m.add_circle(pol(0,0,(ri+re)/2, s*90), D["D_screws_collar"]/2, dxfattribs={"layer":"FORI"})
    m.add_text("perno  R_pivot / Ang_pivot", height=2, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Pp[0]+10,Pp[1]+10))
    m.add_text("sede molla", height=2, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Qg[0]+nx*35,Qg[1]+ny*35))
    # the true shape of the ONE PART box + collar: the white lines above are
    # still the older two-part collar, drawn from its parameters. Cut at
    # the floor (the hatch and the panel opening), in the motor bay, and in
    # the collar band (the ring cut for the motor and the clutch)
    true_shape.draw(m, [("box_collar.step", ("z", -30.5)),
                           ("box_collar.step", ("z", -12.0)),
                           ("box_collar.step", ("z", 10.0))],
                       (10.0, -100.0))
    d.saveas(OUT + "drawings/collar_plan.dxf")

# ================= 4) COLLAR SECTION =================
def collar_section():
    """X = radius from the disc centre, Y = axial height. Collar + reference body."""
    d,m = newdoc()
    Rc=D["D_body"]/2; H=D["H_body"]; Rd=D["R_disc"]
    a0=D["Th_wall_front"]; a1=a0+D["H_opening"]; Rw=Rc-D["Th_wall_radial"]
    sc=D["Dp_slot_front"]; pm=D["Z_plane_mid_disc"]; sd=D["Th_disc"]
    Re=D["R_out_collar"]; Fl=D["Th_flange_collar"]; Rg=D["R_gasket"]
    lg=D["L_groove_gasket"]; pg=D["Dp_groove_gasket"]
    rb0=Rc-sc+0.5; rb1=rb0+D["Th_rib_labyrinth"]; hb=D["H_rib_labyrinth"]
    Ri=D["R_in_flange_collar"]
    # --- reference body, dashed ---
    m.add_lwpolyline([(0,0),(Rc-sc,0),(Rc-sc,a0),(0,a0)], close=True,
                     dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline([(Rw,a0),(Rc,a0),(Rc,a1),(Rw,a1)], close=True,
                     dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline([(0,a1),(Rc,a1),(Rc,H),(0,H)], close=True,
                     dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline([(0,pm-sd/2),(Rd,pm-sd/2),(Rd,pm+sd/2),(0,pm+sd/2)], close=True,
                     dxfattribs={"layer":"COSTRUZIONE"})
    # --- collar ---
    m.add_lwpolyline([(Ri,-Fl),(Re,-Fl),(Re,H+Fl),(Ri,H+Fl),(Ri,H),
                      (Rg-lg/2,H),(Rg-lg/2,H+pg),(Rg+lg/2,H+pg),(Rg+lg/2,H),
                      (Rc,H),(Rc,0),(rb1,0),(rb1,hb),(rb0,hb),(rb0,0),
                      (Rg+lg/2,0),(Rg+lg/2,-pg),(Rg-lg/2,-pg),(Rg-lg/2,0),(Ri,0)],
                     close=True, dxfattribs={"layer":"PROFILO"})
    for y,t in ((0,"faccia lato camera = 0"), (a0,"bordo sup. apertura"),
                (pm,"Z_plane_mid_disc"), (a1,"bordo inf. apertura"),
                (H,"faccia lato telescopio")):
        m.add_line((0,y),(Re+16,y), dxfattribs={"layer":"COSTRUZIONE"})
        m.add_text(t, height=0.9, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Re+17,y-0.45))
    m.add_text("scanalatura frontale (prof. %.1f) e costola di labirinto" % sc, height=1.0,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Rc-30, -Fl-4))
    m.add_text("cava guarnizione r%.0f su entrambe le facce" % Rg, height=1.0,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Rg-14, H+Fl+3))
    datum_section(m)
    # the true shape: the one part cut on the plane through the motor's axis
    true_shape.draw(m, [("box_collar.step", ("y", 0.0)),
                           ("references/filter_wheel_body.step", ("y", 0.0))],
                       (0.0, -Fl - 10.0), 1.0, x_min=0.0)
    d.saveas(OUT + "drawings/collar_section.dxf")

# ================= 6) FUSION PARAMETERS CSV =================
def csv_params():
    with open(OUT + "drawings/filter_wheel_parameters.csv","w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Nome","Unità","Espressione","Valore","Commenti","Preferito"])
        for r in P:
            if len(r)==1: continue
            n,u,e,v,drw,orig,descr = r
            w.writerow([n,u,e,"%.2f"%v,descr,"false"])

def flat_gasket():
    """sealing ring on the flat faces, collar sector."""
    d,m = newdoc()
    rg, lg = D["R_gasket"], D["L_groove_gasket"]
    a = D["Ang_collar_pivot"]; b = D["Ang_collar_opposite"]
    for r in (rg-lg/2, rg+lg/2):
        pts=[pol(0,0,r,x) for x in range(-int(b), int(a)+1)]
        m.add_lwpolyline(pts, dxfattribs={"layer":"PROFILO"})
    for ang in (-b, a):
        m.add_line(pol(0,0,rg-lg/2,ang), pol(0,0,rg+lg/2,ang), dxfattribs={"layer":"PROFILO"})
    # the three reference radii, each with its label at a different angle:
    # all placed in the same direction they overlapped
    for ang,(r,name) in zip((150, 168, 186),
                            ((D["D_body"]/2, "D_body"),
                             (D["R_screw_anchor"], "viti M3"),
                             (D["D_body"]/2-D["Dp_slot_front"], "fondo scanalatura frontale"))):
        m.add_circle((0,0), r, dxfattribs={"layer":"COSTRUZIONE"})
        m.add_line(pol(0,0,r,ang), pol(0,0,r+6,ang), dxfattribs={"layer":"COSTRUZIONE"})
        m.add_text("r%.1f  %s" % (r, name), height=1.8,
                   dxfattribs={"layer":"COSTRUZIONE"}).set_placement(pol(0,0,r+7,ang))
    for rv,av in base_screws():
        m.add_circle(pol(0,0,rv,av), D["D_holes_M3"]/2, dxfattribs={"layer":"FORI"})
    datum_plan(m)
    m.add_text("guarnizione r%.1f, cava %.0f mm - identica sulle due facce" % (rg, lg), height=2.5,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-60,-100))
    d.saveas(OUT + "drawings/flat_gasket.dxf")

# Radial half travel of the M3 slot in the paddles of the bracket. The round
# head of the paddle is concentric with the end of the slot, so the tip sits
# at R_screw_anchor + this + 6.5: with 5 it reached r 88.8, beyond the collar
# (86) and into the electronics bay. 2.5 is enough for a radius taken with the
# calliper.
SLOT_HALF_TRAVEL = 2.5
WB_BRACKET, WP_BRACKET = 4.0, 6.5               # half width of arm and paddle


def _rotate_b(p, angle):
    """Rotate a polyline (x, y, bulge): the rotation does not change the bulges."""
    c, s = math.cos(R(angle)), math.sin(R(angle))
    return [(x*c - y*s, x*s + y*c, b) for x, y, b in p]


def hub_radius():
    """The hub is set by the module, not by the ring: it must hold the two M2
    holes with their edge. Dimensioned on the ring, the holes spilled out of it."""
    return D["Cd_holes_module"]/2 + D["D_holes_M2"]/2 + D["Th_hub_bracket"]


def bracket_arms():
    """The directions of the two arms, from the bisector of the bracket (local +X).

    They go to the two M3 of the base that are on the side free of the
    rotator, Ang_screw_A and Ang_screw_B: the same ones the collar screws onto.
    """
    s = (D["Ang_screw_B"] - D["Ang_screw_A"]) / 2
    return (-s, s)


def cable_arm():
    """The arm along which the sensor cable runs: the one that faces the
    box."""
    return max(bracket_arms())


def arm_rect(rc, across, length, width, phi=None):
    """A rectangle aligned with one arm of the bracket, in the frame of the
    unrotated bracket: centred at radius rc, shifted by 'across' to the side of
    the arm's axis, 'length' long radially and 'width' wide across.

    It lives here and not in the single generators because the same shape
    serves the solid, the DXF, the assembly view and the checks: four places to
    write it by hand are four chances to write it differently. And because a
    rectangle aligned with the world axes, on an arm at 50 degrees, is wide
    where it should be long - a mistake already made, with the cable-tie slots.
    """
    if phi is None:
        phi = cable_arm()
    ux, uy = math.cos(R(phi)), math.sin(R(phi))
    cx, cy = rc*ux - uy*across, rc*uy + ux*across
    return [(cx + ux*a - uy*b, cy + uy*a + ux*b)
            for a, b in ((-length/2, -width/2), (length/2, -width/2),
                         (length/2, width/2), (-length/2, width/2))]


def cover_bosses():
    """The two bosses that hold the sensor cover: (phi, across).

    On the cable arm the boss is NOT on the axis. It used to be, and the lane
    of the four wires passed under it in a tunnel two millimetres high: the
    cable had to be threaded in from one end, and with the JST connector
    already crimped it does not go through. Offset by Off_boss_cable, the lane
    stays open along its whole length and the wires are laid into it from
    above, connector included. Under the offset boss the arm alone does not
    reach: cable_boss_pad() takes care of that.

    The offset goes towards increasing angles, that is to the side OPPOSITE
    the other arm: between the two arms passes the board, and a widening on
    that side would eat the room it needs.
    """
    cable = cable_arm()
    return [(phi, D["Off_boss_cable"] if phi == cable else 0.0)
            for phi in bracket_arms()]


def boss_centre(phi, across):
    """The centre of a boss in the UNROTATED frame of the bracket.

    It lives here, and is not written three times, because the bracket solid,
    the cover solid, the assembly view, the fasteners and the checks all read
    it. The boss set five degrees off the arm - which ended up half in thin
    air - was born precisely from an angle copied by hand in one place only."""
    ux, uy = math.cos(R(phi)), math.sin(R(phi))
    r = D["R_boss_cover_sensor"]
    return (r*ux - uy*across, r*uy + ux*across)


def cable_boss_pad():
    """The widening of the cable arm under the offset boss.

    A boss must GROW from the arm: off its side there is nothing to rest on,
    and a solid resting on thin air is not one part - it is two parts in the
    same file, which no volume measurement tells apart. The pad starts from
    the opposite side of the arm, so it fuses with it, and reaches one
    millimetre beyond the edge of the boss.
    """
    off, db = D["Off_boss_cable"], D["D_boss_cover_sensor"]
    margin = 1.0
    b0, b1 = -WB_BRACKET, off + db/2 + margin
    return arm_rect(D["R_boss_cover_sensor"], (b0 + b1)/2,
                        db + 2*margin, b1 - b0, cable_arm())


def tie_pad():

    """The local widening of the arm under the cable tie.

    The arm is 8 wide and the cable 6: the two slots the tie passes through
    would not fit beside the cable. The pad takes the width to W_pad_tie only
    where it is needed.
    """
    return arm_rect(D["R_tie_cable"], 0.0, D["L_pad_tie"],
                        D["W_pad_tie"])


def tie_slots():
    """The two slots the cable tie passes through, one on each side of the cable."""
    return [arm_rect(D["R_tie_cable"], side*D["Cd_slots_tie"]/2,
                         D["W_slot_tie"], D["H_slot_tie"])
            for side in (-1, 1)]


def tie_groove():
    """The groove on the UNDERSIDE of the pad, from one tie slot to the other.

    The arm rests on the face of the wheel body (measured: z 23.0), so the tie,
    which goes up one slot, over the cable, down the other and back UNDER the
    arm, would otherwise lift the bracket by its own thickness. As long as the slots are along the arm, and as wide across as
    the two slots measured on their outer edges: the tie turns into it
    without a step."""
    return arm_rect(D["R_tie_cable"], 0.0, D["W_slot_tie"],
                        D["Cd_slots_tie"] + D["H_slot_tie"])


def cable_arm_strips():
    """The cable arm widened to the edges of its two pads: two rectangles, because the two pads end at
    different radii.

    On the side of the offset boss the arm now runs as wide as the pad under
    the boss, from the widening round the capacitor window up to the boss; on
    the other side as wide as the tie pad, all the way to it. It is worth it
    because the wire passage grew by a millimetre: on an arm 8 wide the walls
    beside a 4.5 passage would be 1.75 each. And it costs no clearance: the
    cable arm points away from the optical axis (checked in
    check_dimensions.py, which includes these shapes)."""
    r0 = D["R_end_widening_relief"] - 1.0          # overlaps the widening it continues
    b0 = -D["W_pad_tie"]/2
    b1 = D["Off_boss_cable"] + D["D_boss_cover_sensor"]/2 + 1.0   # = cable_boss_pad
    r_boss = D["R_boss_cover_sensor"]
    r_tie = D["R_tie_cable"] - D["L_pad_tie"]/2 + 1.0
    # BOTH strips run on to the tie pad. The one on the boss side used to stop
    # at the boss (r_boss), and between the slanted end of the boss pad and the
    # start of the tie pad a wedge-shaped slit was left, 0 to 0.3 mm wide and
    # three long, right through the plate: a hairline in the render, a notch
    # in the print. Found mapping the arm at 0.1 mm.
    return [arm_rect((r0 + r_tie)/2, (b0 + b1)/2, r_tie - r0, b1 - b0),
            arm_rect((r0 + r_tie)/2, (b0 + WB_BRACKET)/2, r_tie - r0, WB_BRACKET - b0)]


def wire_passage_mouth():
    """The two corners to round where the wire passage opens into the capacitor
    window: [(radial, across, side)] in the frame of the cable arm, plus the
    radius. The window is drawn in the frame of the module and the passage in
    the frame of the arm; the corner is where the two meet only because the
    module is aligned with the arm, so that is demanded, not assumed."""
    if abs(module_angle() - cable_arm()) > 1e-6:
        raise SystemExit("wire_passage_mouth: the module is no longer aligned "
                         "with the cable arm, the mouth of the passage has to be "
                         "worked out again")
    r_end = hub_radius() + 4.0                 # outer edge of capacitor_relief()
    w = D["W_passage_wires"]/2
    return [(r_end, side*w, side) for side in (-1, 1)], D["Fil_mouth_passage_wires"]


def mouth_step():
    """The width of the step between the capacitor window and the wire
    passage, on each side: the room the mouth fillet has across the arm."""
    return D["Halfw_relief"] - D["W_passage_wires"]/2


def cable_saddle():
    """The flat-bottomed seat in which the sheathed cable lies, inside the
    pad."""
    return arm_rect(D["R_tie_cable"], 0.0, D["L_pad_tie"] + 2,
                        D["D_channel_cable"])


def cover_skirt_radius():
    """How far, in radius, the outer face of the cover's skirt reaches.

    The skirt follows the board, not a radius picked at the desk: it is half
    the diameter of the module, plus the air left around it, plus the
    thickness of the skirt."""
    return (D["L_board_module"]/2 + D["Cl_cover_module"]
            + D["Th_skirt_cover"])


def wire_passage():
    """The lane of the four stripped wires, from the cable tie to the gap in
    the cover's skirt. It passes UNDER the boss, which bridges it.

    It starts where the skirt ends: it used to start from r 17, the old
    radius of the skirt when the skirt was a ring at a fixed radius, and with
    the skirt redrawn on the board the lane hung in thin air for five
    millimetres before meeting the gap."""
    r_in = cover_skirt_radius()
    return arm_rect((r_in + D["R_tie_cable"])/2, 0.0,
                        D["R_tie_cable"] - r_in, D["W_passage_wires"])


def capacitor_relief():
    """The window that makes room for the 104 capacitor under the board.

    On the side where the cable and the pads arrive, that is local +X, which
    is the bisector of the V: beyond R_relief_capacitor and inside the half
    width that leaves the two pads standing. Inside that radius nothing is
    touched, because there sits the ring that goes around the magnet.
    """
    rs, ys = D["R_relief_capacitor"], D["Halfw_relief"]
    re_ = hub_radius() + 4.0
    return rotate_points([(rs, -ys), (re_, -ys), (re_, ys), (rs, ys)], module_angle())


def bracket_step_radius():
    """From here outwards the bracket sits higher by Th_flange_collar: the
    paddles rest on the rear flange of the collar, the hub on the face of the
    body. One millimetre before the inner edge of the flange."""
    return D["R_in_flange_collar"] - 1.0


def rotate_points(points, angle):
    c, s = math.cos(R(angle)), math.sin(R(angle))
    return [(x*c - y*s, x*s + y*c) for x, y in points]


def module_angle():
    """How much the module is turned on the bracket.

    Everything that concerns the module - outline, M2 holes, support pads,
    capacitor relief - is drawn in the orientation in which the module was
    MEASURED (holes on the Y axis, capacitor towards +X) and then turned by
    this. One number only, read from one place only: the bracket, the test
    feet, the DXF and the cover can no longer half agree.
    """
    return D["Ang_module_on_bracket"]


def module_holes():
    """The centres of the two M2 holes, already turned."""
    return rotate_points([(0, D["Cd_holes_module"]/2), (0, -D["Cd_holes_module"]/2)],
                       module_angle())


def free_pads_angle():
    """The direction of the three large pads that are not used - PWM, GND, 5V.

    With the module aligned with the arms this falls on the arm OPPOSITE the
    cable one, which is solid material at full height: the board support sits
    on it, can be seen and is not cantilevered. It is the reason the module is
    turned by 45 degrees."""
    return module_angle() - 90.0


def used_pads_angle():
    """The direction of the edge of the six pads that are used - DIR, SCL,
    SDA, PGO, 5V, GND. It is on the other side of the board, necessarily: the
    two edges are opposite. The wires then leave through the capacitor hole,
    which is the exit point of the cable."""
    return module_angle() + 90.0


def v_back():
    """The direction opposite the two arms, in the frame of the bracket.

    It is not 180 written by hand: it is the bisector of the arms plus half a
    turn, and if the arms move the back follows them. It is also the direction
    in which the optical axis lies, because the V opens on the side free of
    the rotator.
    """
    b0, b1 = bracket_arms()
    return (b0 + b1)/2 + 180.0


def module_support_pads():
    """The THREE pads the board rests on: centre line, half width, outer
    radius, inner radius.

    They are not equal, and it is not an oversight. The one on the side of
    the six used pads stays narrow and stops at the hub: under there is all
    sorts, and the less flat surface is left, the less likely it is to meet a
    component.

    The one on the side of the three large unused pads is twice as wide and
    reaches the EDGE of the board. The radius is the part that matters, and
    it is the mistake that had been made: stopped at the hub, the pad does not
    even touch the three pads. They fall at r 7.50 - 7.92, while the hub ends
    at 7.45, and under them there was nothing. So the support leaves the hub
    and the bracket puts material under it, trimmed to the outline of the
    board so it cannot overhang.

    The THIRD is on the back of the V, found looking at the printed part:
    there the resting plane stopped at the hub and under the edge of the
    board there was nothing. It is not an extra: the first two have their
    centre lines at 135 and -45 degrees, that is on ONE STRAIGHT LINE, and on
    two supports in a row the board rocks around that line - the third stops
    it because it is forty-five degrees from it. It starts further out than
    the other two, at R_pad_back_v: here we are in a diagonal quadrant, where
    the SMD components reach 6.4, and not around an M2 hole where the module
    carries nothing.
    """
    r_edge = D["L_board_module"]/2 + 0.6
    return ((used_pads_angle(), D["Ang_pad_module"], hub_radius(),
             D["R_pad_module"]),
            (free_pads_angle(), D["Ang_pad_pads_free"], r_edge,
             D["R_pad_module"]),
            (v_back(), D["Ang_pad_back_v"], r_edge, D["R_pad_back_v"]))


def free_pads():
    """Where the three large unused pads really fall.

    They are in a row on the flat, at a pitch of 2.54. They are used to
    measure that the support really reaches under them, instead of trusting an
    angular sector that on paper seems to cover them and in millimetres does
    not."""
    # -half and not +half: the three pads are on the flat that faces
    # free_pads_angle(), that is module_angle() - 90. Taking the other one,
    # the support was measured on the wrong edge, and the check said OK while
    # looking at the place where the support was not supposed to be.
    half = -D["W_board_module"]/2
    return rotate_points([(k*D["Pitch_pads_module"], half) for k in (-1, 0, 1)],
                       module_angle())


def board_outline(clearance=0.0):
    """The outline of the AS5600 module, in the frame of the bracket.

    It is not a rectangle: it is a round of L_board_module with two flats at
    W_board_module, and the two M2 holes are on the axis of the flats. It used
    to be drawn as a 15 x 16.8 rectangle turned by ninety degrees: the board
    came out long where it is wide, and the recess under it came out the wrong
    shape.

    With clearance > 0 the outline comes out inflated, which is that of the
    recess and - wider still - that of the cover.
    """
    r = D["L_board_module"]/2 + clearance
    half = D["W_board_module"]/2 + clearance
    t = deg(math.asin(min(1.0, half/r)))        # where the flat cuts the round
    pts = []
    # the arcs around 180 and 0 remain, that is where |y| does not exceed the
    # flat; the two straight stretches between one arc and the other are the flats
    for a0, a1 in ((180-t, 180+t), (360-t, 360+t)):
        n = max(2, int((a1-a0)/4))
        pts += [pol(0, 0, r, a0 + (a1-a0)*i/n) for i in range(n+1)]
    return rotate_points(pts, module_angle())


def bracket_outline():
    """Outline of the sensor bracket: (x, y, bulge), origin = disc centre,
    +X on the bisector of the two arms.

    It sits on the telescope-side face. It is a V: the hub in the centre,
    which centres on the magnet, and two arms towards the two M3 of the
    collar, 90 degrees apart. The other two M3 cannot be used: every arm that
    goes towards the optical axis enters the envelope of the rotator, which is
    on this side. Two supports and not a cantilever: by symmetry the chip does
    not tilt around the bisector, and in the other direction the torsion of
    the arms holds it.

    It lives here and not inside sensor_bracket() because the assembly view
    uses it too: the part is drawn once only.

    The outline runs anticlockwise, so the convex bulges are positive: with
    the minus sign the hub goes concave and the paddles swell, and the bracket
    comes out like a butterfly instead of like a key.
    """
    re_ = hub_radius()
    Rv = D["R_screw_anchor"]
    wb, wp = WB_BRACKET, WP_BRACKET
    xr = math.sqrt(max(re_*re_ - wb*wb, 0.0))   # where the arm meets the hub
    a = deg(math.atan2(wb, xr))                 # half width of the arm on the hub
    B = 0.4142                                  # round step arm -> paddle
    Rt = Rv + SLOT_HALF_TRAVEL                  # centre of the round head
    phis = sorted(bracket_arms())
    outer = []
    for i, phi in enumerate(phis):
        # the hub arc that goes from this arm to the next one
        sweep = (phis[(i+1) % len(phis)] - phi - 2*a) % 360
        arm = [(xr, -wb, 0.0), (Rv-7, -wb, B), (Rv-7, -wp, 0.0), (Rt, -wp, 1.0),
               (Rt, wp, 0.0), (Rv-7, wp, B), (Rv-7, wb, 0.0),
               (xr, wb, math.tan(R(sweep)/4))]
        outer += _rotate_b(arm, phi)
    return outer


def screw_slot(phi):
    """The M3 slot of the paddle that lies in the direction phi.

    It is radial and absorbs the uncertainty on the radius of the screw; the
    angle is taken by the bracket turning on the magnet, because the screws
    are on a square and move together. 4 wide and not 3.4: with two arms not
    in line, the offset between the centre of the square of screws and the
    axis of the disc can no longer be recovered by turning, and it falls to
    the side clearance, half a millimetre.
    """
    Rv = D["R_screw_anchor"]
    a, c = 2.0, SLOT_HALF_TRAVEL
    p = [(Rv-c, -a, 0.0), (Rv+c, -a, 1.0), (Rv+c, a, 0.0), (Rv-c, a, 1.0)]
    return _rotate_b(p, phi)


def sensor_bracket():
    """origin = disc centre / pivot axis; +X on the bisector of the arms."""
    d,m = newdoc()
    ri = D["D_hole_magnet_printing"]/2
    hx = D["Cd_holes_module"]/2
    Rv = D["R_screw_anchor"]; wb = WB_BRACKET
    m.add_lwpolyline([(x, y, 0, 0, b) for x, y, b in bracket_outline()],
                     format="xyseb", close=True, dxfattribs={"layer":"PROFILO"})
    m.add_circle((0,0), ri, dxfattribs={"layer":"FORI"})
    for c in module_holes():
        m.add_circle(c, D["D_holes_M2"]/2, dxfattribs={"layer":"FORI"})
    rg = bracket_step_radius()
    for phi in bracket_arms():
        m.add_lwpolyline([(x, y, 0, 0, b) for x, y, b in screw_slot(phi)],
                         format="xyseb", close=True, dxfattribs={"layer":"FORI"})
        m.add_line((0,0), pol(0,0,Rv+10,phi), dxfattribs={"layer":"COSTRUZIONE"})
        # the step: a line across the arm, where the flange begins
        m.add_line(pol(*pol(0,0,rg,phi),wb+1.5,phi-90), pol(*pol(0,0,rg,phi),wb+1.5,phi+90),
                   dxfattribs={"layer":"COSTRUZIONE"})
    # --- the cable's route, on the arm that faces the box -------------------
    # The drawing must show this too, otherwise the bracket on the sheet is no
    # longer the bracket of the solid: the pad widens the arm from 8 to 16, and
    # without it the two cable-tie slots would fall outside the part.
    m.add_lwpolyline(tie_pad(), close=True,
                     dxfattribs={"layer":"PROFILO"})
    for slot in tie_slots():
        m.add_lwpolyline(slot, close=True, dxfattribs={"layer":"FORI"})
    m.add_lwpolyline(cable_saddle(), close=True, dxfattribs={"layer":"COSTRUZIONE"})
    for _r in cable_arm_strips():
        m.add_lwpolyline(_r, close=True, dxfattribs={"layer":"PIENO"})
    m.add_lwpolyline(tie_groove(), close=True, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline(wire_passage(), close=True, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline(capacitor_relief(), close=True, dxfattribs={"layer":"FORI"})
    for phi in bracket_arms():                  # the bosses that hold the cover
        m.add_circle(pol(0, 0, D["R_boss_cover_sensor"], phi),
                     D["D_boss_cover_sensor"]/2, dxfattribs={"layer":"COSTRUZIONE"})
        m.add_circle(pol(0, 0, D["R_boss_cover_sensor"], phi),
                     D["D_hole_insert_M25"]/2, dxfattribs={"layer":"FORI"})
    m.add_line((-14,0),(14,0), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_line((0,-14),(0,14), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle((0,0), D["D_pivot_hub"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle((0,0), D["D_magnet"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_lwpolyline(board_outline(), close=True, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("foro magnete %.2f (progetto %.2f + %.2f di compensazione stampa)"
               % (D["D_hole_magnet_printing"], D["D_in_ring_bracket"], D["Comp_hole_printing"]),
               height=1.2, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-14,-10.6))
    m.add_text("ingombro basetta AS5600", height=1.2,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-14,-12))
    # the recess for the components under the board, and the pads left standing
    m.add_lwpolyline(board_outline(D["Cl_notch_module"]), close=True,
                     dxfattribs={"layer":"COSTRUZIONE"})
    for mid, ap, r_out, r_in in module_support_pads():
        arc_points = lambda r: [pol(0, 0, r, mid - ap + 2*ap*i/12) for i in range(13)]
        m.add_lwpolyline(arc_points(r_in) + arc_points(r_out)[::-1], close=True,
                         dxfattribs={"layer":"COSTRUZIONE"})
    # and the three free pads, which are the reason the support is there: they
    # must show on the drawing, otherwise the support looks gratuitous
    for c in free_pads():
        m.add_circle(c, 0.9, dxfattribs={"layer":"COSTRUZIONE"})
    # the widening of the arm around the capacitor hole: it is material added
    # in 3D, so the outline alone would not say it, and a drawing that does not
    # say it makes one believe the hole cuts the arm in two
    lu = D["R_end_widening_relief"]
    m.add_lwpolyline(arm_rect(lu/2, 0.0, lu, D["W_arm_widened_relief"],
                                  cable_arm()), close=True,
                     dxfattribs={"layer":"PIENO"})
    m.add_text("il braccio si allarga a %.0f dove lo fora lo sfogo del "
               "condensatore, che e' anche l'uscita del cavo"
               % D["W_arm_widened_relief"], height=1.2,
               dxfattribs={"layer":"QUOTE"}).set_placement((-14, -21))
    # the three pads describe themselves: the text is built from the list,
    # otherwise it says what the pads were and not what they are
    _names = ("sei piazzole", "tre libere", "dorso della V")
    _txt = "; ".join("%s r%.1f-%.1f +-%.0f" % (n, r_in, r_out, ap)
                     for n, (mid, ap, r_out, r_in)
                     in zip(_names, module_support_pads()))
    m.add_text("scasso %.1f sotto la basetta, appoggia su tre pad: %s"
               % (D["Dp_notch_module"], _txt), height=1.2,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-14,-13.8))
    m.add_text("CENTRO DISCO = asse perno - faccia lato telescopio", height=1.4,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((4,-16))
    m.add_text("gradino r%.1f: da qui in fuori +%.0f mm, le palette stanno sulla flangia del collare"
               % (rg, D["Th_flange_collar"]), height=1.4,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((4,-19))
    d.saveas(OUT + "drawings/sensor_bracket.dxf")

def magnet_cap():
    """The cap that holds the magnet while the glue sets.

    Plan on the left, section on the right. The magnet goes into the seat from
    the face that rests on the wheel body. The seat is much deeper than the
    stack that goes into it - spacer and magnet - on purpose: inside a tall
    wall the magnet cannot tilt while it goes down, and the cap keeps it flat
    and square until the glue takes.
    """
    d, m = newdoc()
    R = D["D_cap"]/2
    rs = D["D_seat_cap"]/2
    h, ps = D["H_cap"], D["Dp_seat_cap"]
    rf = D["D_pushout_cap"]/2

    # --- plan, seen from the side that rests ------------------------------
    m.add_circle((0,0), R, dxfattribs={"layer":"PROFILO"})
    m.add_circle((0,0), rs, dxfattribs={"layer":"FORI"})
    m.add_circle((0,0), rf, dxfattribs={"layer":"FORI"})
    m.add_circle((0,0), D["D_magnet"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_circle((0,0), D["D_pivot_hub"]/2, dxfattribs={"layer":"COSTRUZIONE"})
    m.add_line((-R-3,0), (R+3,0), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_line((0,-R-3), (0,R+3), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("magnete %.0f e perno %.2f, tratteggiati" % (D["D_magnet"], D["D_pivot_hub"]),
               height=0.9, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-R, -R-3))

    # --- section: y = 0 on the face that rests, y positive into the solid ---
    ox = R + 14                                  # moved to the right of the plan
    def rect(x0, y0, x1, y1, layer="PROFILO"):
        m.add_lwpolyline([(ox+x0,y0),(ox+x1,y0),(ox+x1,y1),(ox+x0,y1)],
                         close=True, dxfattribs={"layer":layer})
    for s in (-1, 1):
        rect(s*rf, 0, s*R, h)                    # the body, holed in the centre
        rect(s*rs, 0, s*rf, ps, "FORI")          # the magnet seat
    m.add_line((ox-R-3,0), (ox+R+3,0), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_line((ox,-3), (ox,h+3), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("appoggia qui, sulla faccia lato TELESCOPIO", height=0.9,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((ox-R, -2))
    m.add_text("sede %.2f x %.1f - dentro ci vanno distanziale %.1f e magnete %.1f"
               % (D["D_seat_cap"], ps, D["Th_spacer_magnet"], D["Th_magnet"]), height=0.9,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((ox-R, h+1.5))

    # --- how to use it -------------------------------------------------------
    instructions = [
        "CAPPUCCIO DI INCOLLAGGIO DEL MAGNETE - come si usa",
        "",
        "0. A RUOTA GIA' RICHIUSA: il magnete e' piu' largo del foro a boccola del",
        "   coperchio e non ci passa piu'. Si incolla per ultimo, sul perno che affiora.",
        "1. Magnete nella sede del cappuccio, con la faccia che andra' incollata in fuori.",
        "   La sede e' %.2f su un magnete %.1f: entra a mano e non balla. La sede e'" % (D["D_seat_cap"], D["D_magnet"]),
        "   profonda %.1f, molto piu' del magnete: dentro una parete alta non si inclina." % D["Dp_seat_cap"],
        "2. Colla sulla faccia esposta del magnete, poca e al centro. Poi il distanziale",
        "   %.1f x %.1f sopra, e altra colla sulla sua faccia esposta: si incolla" % (D["D_spacer_magnet"], D["Th_spacer_magnet"]),
        "   tutta la pila in una volta sola.",
        "3. Appoggiare il cappuccio sulla faccia lato TELESCOPIO, centrato sul perno",
        "   a occhio: il magnete %.1f sul perno %.2f sborda di %.3f per parte, quindi" % (D["D_magnet"], D["D_pivot_hub"], (D["D_magnet"]-D["D_pivot_hub"])/2),
        "   se e' centrato la faccia del perno non si vede da nessuna parte. Appena",
        "   spunta una mezzaluna lucida, e' gia' fuori di piu'. E' questo il controllo.",
        "4. Premere e lasciare tirare. Il cappuccio tiene la pila piana e squadrata.",
        "   Il distanziale la tiene sollevata %.1f dal coperchio: il magnete gira," % D["Th_spacer_magnet"],
        "   il coperchio sta fermo, e senza aria si toccherebbero.",
        "5. Sfilare il cappuccio. Se il magnete resta dentro, spingerlo dal foro da %.0f." % D["D_pushout_cap"],
        "",
        "Poi la staffa: il suo anello (foro %.2f) scende sul magnete con %.3f di gioco" % (D["D_in_ring_bracket"], D["D_in_ring_bracket"]/2 - D["D_magnet"]/2),
        "e si centra da solo. Si stringono le due viti M3 nelle asole e si monta il modulo.",
        "Il perno non lo tocca niente: affiora a filo della faccia e non e' afferrabile.",
    ]
    for i, text_line in enumerate(instructions):
        m.add_text(text_line, height=1.1 if i == 0 else 0.9,
                   dxfattribs={"layer":"COSTRUZIONE"}).set_placement((-R, -R - 8 - i*1.9))
    d.saveas(OUT + "drawings/magnet_cap.dxf")


if __name__ == "__main__":
    clutch_section(); arm_plan(); collar_plan(); collar_section(); sensor_bracket()
    magnet_cap()
    flat_gasket(); csv_params()
    print("gasket perimeter r%.0f: %.1f mm" % (D["R_gasket"], 2*math.pi*D["R_gasket"]*(D["Ang_box_pivot"]+D["Ang_box_opposite"])/360))
