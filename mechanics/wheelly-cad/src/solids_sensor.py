# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The bracket of the AS5600 sensor, in its assembly position.

The outline is the one of drawings.bracket_outline(), the same as the DXF: here
it is given its thickness and put in its place, on the telescope-side face,
rotated by Ang_bracket_sensor. It serves the interference check, which without
a solid could not see the bracket, and to look at it in the assembly.

In height it is stepped. The hub and the inner part of the arms sit on the
face of the body and reach H_rest_module, where the board rests. Beyond
bracket_step_radius() the arms rise by Th_flange_collar, because the paddles
are clamped over the rear flange of the collar by the same M3 that holds the
collar.

Under the board the plane is not solid: see module_notch().
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
import math
import cadquery as cq
from parameters import D
from drawings import (bracket_outline, screw_slot, bracket_arms,
                      bracket_step_radius, hub_radius, board_outline,
                      arm_rect, tie_pad, tie_slots,
                      cable_saddle, wire_passage, capacitor_relief,
                      module_holes, module_support_pads, used_pads_angle,
                      free_pads_angle, rotate_points, cable_arm,
                      cover_skirt_radius, cover_bosses, boss_centre,
                      cable_boss_pad, cable_arm_strips,
                      tie_groove, wire_passage_mouth, mouth_step,
                      hub_radius)
from drawings_assembly import from_bulge

Hc = D["H_body"]
h = D["H_rest_module"]                 # where the board rests
Fl = D["Th_flange_collar"]
Rg = bracket_step_radius()
OVERLAP = 4.0          # how much the upper stretch rests on the lower one: it is the joint
HOLE_CHAMFER = 0.3     # lead-in at the bottom of the magnet hole, against the elephant foot


def prism(points, z, height):
    return cq.Workplane("XY").workplane(offset=z).polyline(points).close().extrude(height)


def annulus(r0, r1, z, height):
    return (cq.Workplane("XY").workplane(offset=z).circle(r1).circle(r0)
            .extrude(height))


def sector(a0, a1, r0, r1, z, height, step=2.0):
    """A piece of circular annulus, from a0 to a1 and from r0 to r1."""
    n = max(2, int((a1 - a0) / step) + 1)
    ang = [a0 + (a1 - a0) * i / (n - 1) for i in range(n)]
    p = lambda r, a: (r*math.cos(math.radians(a)), r*math.sin(math.radians(a)))
    pts = [p(r1, a) for a in ang] + [p(r0, a) for a in reversed(ang)]
    return cq.Workplane("XY").workplane(offset=z).polyline(pts).close().extrude(height)


def module_notch(z_rest, outline=None):
    """The void under the board, to subtract from the part.

    The underside of the module is not smooth: there are SMD resistors and
    capacitors, with their solder joints. Resting the board on a solid plane
    means setting it on those, and the gap dimension no longer holds.
    So the whole plane under the module's envelope is lowered by
    Dp_notch_module, except two pads around the M2 holes, which are the only
    place where a module never carries anything: the screw passes there.

    It takes the height of the resting plane - the one of the pads - because
    the same geometry serves the bracket, which sits at Hc, and the test
    feet, which sit at zero.
    """
    p = D["Dp_notch_module"]
    # normally the notch is cut under the module's envelope; the test feet,
    # which are wider than the hub, pass their own outline and have the whole
    # plane cut except the pads
    if outline is None:
        outline = board_outline(D["Cl_notch_module"])
    void = (cq.Workplane("XY").workplane(offset=z_rest - p)
            .polyline(outline).close().extrude(p + 1))
    # The pads stay up: the void takes them off itself. They do not take the
    # whole width of the ring - further in there are the components - but
    # only the annulus each one declares: around the M2 holes one can start
    # from R_pad_module, on the back of the V not, because there one is in a
    # diagonal quadrant and the components reach further out.
    for mid, ap, r_out, r_in in module_support_pads():
        pad = sector(mid - ap, mid + ap, r_in,
                     r_out + 0.01, z_rest - p - 0.5, p + 2)
        # trimmed to the outline of the board: the pad on the free side comes
        # out of the hub to reach under the three pads, and without this trim
        # it would spill out from under the board instead of stopping at its
        # edge
        pad = pad.intersect(prism(board_outline(0.0),
                                  z_rest - p - 0.5, p + 2))
        void = void.cut(pad)
    return void


def arm_widened_relief(z_base, height):
    """The reinforcement of the cable arm in the stretch that gets holed.

    The capacitor - which is also the point the cable comes out from - is in
    line with the arm, and its relief is 9.2 wide on an arm 8 wide: as it is,
    the hole does not widen the arm, it CUTS it. Tried: the bracket comes out
    as two solids. Here the arm is brought to W_arm_widened_relief in the
    affected stretch only, and after the hole two ribs remain that bridge
    over it.

    Widening on this side costs no envelope: the cable arm points away from
    the optical axis.
    """
    lu = D["R_end_widening_relief"]
    return prism(arm_rect(lu/2, 0.0, lu, D["W_arm_widened_relief"],
                              cable_arm()), z_base, height)


def support_outside_hub(z_base, height):
    """The material under the pads that come out of the hub.

    A pad is only the plane the board rests on: if it falls beyond the edge of
    the hub - which ends at 7.45 - there is nothing under it, and the pad
    stays an intention drawn in the void. Here the material is put in, at full
    height from the face up to the resting plane, and only in the sector that
    is needed.

    It applies to TWO pads out of three: the one of the three free pads and
    the one on the back of the V. The third stops at the hub and already has
    its material. Before, this function knew a single case, written inside
    it: when the pad on the back was added, the pad was there and the
    material under it was not.
    """
    outer = None
    for mid, ap, r_out, r_in in module_support_pads():
        if r_out <= hub_radius() + 0.01:
            continue
        s = support_under_pad(mid, ap, r_out, z_base, height)
        outer = s if outer is None else outer.union(s)
    return outer


def support_under_pad(mid, ap, r_out, z_base, height):
    """The material under one pad that comes out of the hub.

    The case it was born from: the three free pads fall at r 7.50 and 7.92,
    the hub ends at 7.45, and a pad, however wide it is made, still stays
    inside the hub and finds nothing under them. Here the hub is swollen in
    the needed sector only, up to the edge of the board - which also acts as
    the template, so the swelling cannot stick out.

    There is however a second trim, and without it the pad on the back of the
    V could not be made at all: the back faces the OPTICAL AXIS - the V opens
    towards the side free of the rotator, so the rotator is behind - and the
    project's rule is that inside its envelope the bracket may enter ONLY with
    the hub, which reaches 40.55 mm from the axis. The outline of the board on
    its own is not enough to respect it: the board enters it more than the
    hub, down to 39.58, and taking the bracket there too would be a millimetre
    of rotator eaten for a few tenths more of rest. So the support is cut on
    the cylinder of the hub: it stays wide where the rotator is far and thins
    down approaching the axis, by itself.
    """
    s = (sector(mid - ap, mid + ap, hub_radius() - 1.0,
                r_out, z_base, height)
         # it starts from inside the hub, not from zero: so it fuses with the
         # hub instead of resting against it edge-on
         .intersect(prism(board_outline(0.0), z_base, height)))
    # the optical axis, in the NON-rotated frame of the bracket: in assembly
    # position it is at (-Off_hole_optical, 0), so here it is where the inverse
    # rotation takes it. Written by hand it would be yet another dimension
    # disconnected from Ang_bracket_sensor.
    a = math.radians(D["Ang_bracket_sensor"])
    cx, cy = -D["Off_hole_optical"]*math.cos(a), D["Off_hole_optical"]*math.sin(a)
    return s.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
        D["Off_hole_optical"] - hub_radius(), height + 2,
        cq.Vector(cx, cy, z_base - 1))))


def relief_window(z_base, z_rest):
    """The through window that makes room for the 104 capacitor.

    Under the board, beyond R_relief_capacitor and on the side where the cable
    and the pads arrive, there is the 104: it is the tallest component of the
    module and does NOT fit in the three tenths that module_notch() leaves. On
    the test feet the problem had already come up - the board rested on the
    capacitor instead of on the pads, that is it measured a gap that was not
    the one - and there it was solved by cutting the part straight at that
    radius. On the real bracket the same defect was there and nobody had seen
    it: and the bracket is the final part, if the board rests on the
    capacitor the gap is wrong for ever.

    Here the straight cut cannot be made - right outside the hub the arms
    begin - and so a HOLE is made: through from side to side, from the radius
    of the capacitor outwards. Through and not lowered because the height of
    that capacitor is not known: nobody measured it, and a bottom left by eye
    would be the same bet as before.

    Inside R_relief_capacitor nothing is touched: there is the ring that goes
    round the magnet, and it is what centres the bracket. The capacitor is
    further out than the magnet, so the two compete for nothing.
    """
    return extrude_at(capacitor_relief(), z_base - 1, z_rest - z_base + 2)


def magnet_hole(diameter, z_bottom, height):
    """The magnet hole, with the chamfer at the bottom.

    The chamfer is needed: the magnet sits right on the first layer, where the
    elephant foot tightens the hole, and without a lead-in it does not go in
    even if the diameter is right. It also serves as a mouth when the bracket
    is slipped onto the magnet.
    """
    r = diameter/2
    hole = (cq.Workplane("XY").workplane(offset=z_bottom - 1)
            .circle(r).extrude(height + 2))
    chamfer = (cq.Workplane("XY").workplane(offset=z_bottom)
               .circle(r + HOLE_CHAMFER).workplane(offset=HOLE_CHAMFER)
               .circle(r).loft())
    return hole.union(chamfer)


def flat_shape():
    """The bare bracket, NOT yet rotated into its assembly position.

    All the geometry - this, the bosses, the channel, the cover - is drawn
    with the arm at +45 and at -45, that is in the frame bracket_outline()
    lives in, and the rotation by Ang_bracket_sensor is done once only at the
    end. Rotating halfway and then going on working with the angles of before
    is exactly the mistake that had put the bosses five degrees off the arms:
    at r 40 that is three and a half millimetres, and the boss ended up half
    in the void.
    """
    shape = lambda z, height: prism(from_bulge(bracket_outline(), 0.3), z, height)
    # lower stretch: inside the step, on the face of the body
    lower = shape(Hc, h).intersect(
        cq.Workplane("XY").workplane(offset=Hc).circle(Rg).extrude(h))
    # upper stretch: outside, over the flange of the collar; it starts a bit
    # before the step so as to rest on the lower stretch instead of touching
    # it edge-on
    upper = shape(Hc + Fl, h).intersect(
        annulus(Rg - OVERLAP, 200.0, Hc + Fl, h))
    s = lower.union(upper)

    # The added material must be joined BEFORE the holes, not after: the
    # widening of the arm passes over the magnet hole and over both M2 holes
    # - its half width, 7.5, is more than the 5.75 the screws are at - and
    # joined afterwards it plugged them all again. The magnet no longer went
    # into the ring by 25 mm3, and it was a check that said so at once.
    s = s.union(arm_widened_relief(Hc, h))
    s = s.union(support_outside_hub(Hc, h))

    # the holes: ring on the magnet, M2 of the module, M3 slots of the paddles
    s = s.cut(magnet_hole(D["D_hole_magnet_printing"], Hc, h))
    for cx, cy in module_holes():
        s = s.cut(cq.Workplane("XY").workplane(offset=Hc - 1).center(cx, cy)
                  .circle(D["D_holes_M2"]/2).extrude(h + 2))
    for phi in bracket_arms():
        s = s.cut(prism(from_bulge(screw_slot(phi), 0.3), Hc - 1, Fl + h + 2))
    # and the room for the components under the board: it takes in the arms
    # too, which pass under the module down to r 16
    s = s.cut(module_notch(Hc + h))
    s = s.cut(relief_window(Hc, Hc + h))
    return s


def cable_arm_edges(sol, radius):
    """The convex vertical edges of the cable arm's outline: straight,
    vertical, as tall as the plate, from the end of the capacitor window to the
    end of the tie pad. Past the tie pad the arm climbs onto the collar flange
    and carries the M3 slot, whose outline is a polyline of short chords -
    nothing there to round.

    CONVEX IS TESTED ON THE SOLID, and the first test was wrong: a point out
    along the bisector of the two faces is air at a convex corner, but also at
    the corner of a HOLE, where both faces look into the hole - the tie slots
    came out as convex. The test that tells them apart steps out along one
    face's normal and back along the other's: at a convex corner that point is
    outside both faces, at a hole corner it is inside the second one.

    An edge with ANY other vertical edge - convex or not - closer than a
    fillet's width across is left alone: the stretch between them is too
    short to take the fillet, and OCCT refuses the whole set for it. That is
    the 0.5 mm jog where the strip on the tie side starts, W_pad_tie/2 = 8
    against the 7.5 of the widening round the window."""
    phi = math.radians(cable_arm())
    u, n = (math.cos(phi), math.sin(phi)), (-math.sin(phi), math.cos(phi))
    r_min = hub_radius() + 4.0                  # the end of the window
    r_max = D["R_tie_cable"] + D["L_pad_tie"]/2 + 1.0
    found, all_edges = [], []
    for e in sol.Edges():
        p0, p1 = e.startPoint(), e.endPoint()
        if (e.geomType() != "LINE" or abs(p0.x - p1.x) > 1e-6
                or abs(p0.y - p1.y) > 1e-6 or abs(p1.z - p0.z) < 0.9*h):
            continue
        r = p0.x*u[0] + p0.y*u[1]
        t = p0.x*n[0] + p0.y*n[1]
        if not (r_min + 0.25 < r < r_max and abs(t) < 20.0):
            continue
        zm = (p0.z + p1.z)/2
        pm = cq.Vector(p0.x, p0.y, zm)
        all_edges.append((e, cq.Vector(p0.x, p0.y, 0)))
        adjacent = [f for f in sol.Faces()
                    if f.geomType() == "PLANE" and f.distance(cq.Vertex.makeVertex(pm.x, pm.y, zm)) < 1e-6]
        if len(adjacent) != 2:
            continue
        m1, m2 = [f.normalAt(pm) for f in adjacent]
        if sol.isInside(pm + (m1 - m2)*0.3, 1e-6) or sol.isInside(pm + (m2 - m1)*0.3, 1e-6):
            continue                                   # re-entrant, or a hole
        if sol.isInside(pm + (m1 + m2)*0.3, 1e-6):
            continue
        found.append((e, cq.Vector(p0.x, p0.y, 0)))
    kept = [e for e, q in found
            if all((q - q2).Length > 2*radius + 0.2 for e2, q2 in all_edges if e2 is not e)]
    return kept


def bracket():
    """The finished bracket, in its assembly position."""
    s = bosses_and_channel(flat_shape())
    # The convex vertical edges of the cable arm, rounded. The arm is the part of the
    # bracket that sticks out alone and that the hand meets feeding the cable.
    edges = cable_arm_edges(s.val(), D["Fil_edges_arm_cable"])
    if not edges:
        raise SystemExit("bracket: no convex vertical edge found on the cable arm "
                         "- the search has stopped seeing the arm")
    s = cq.Workplane(obj=s.val().fillet(D["Fil_edges_arm_cable"], edges))
    print("bracket: %d vertical edges of the cable arm rounded (r %.1f)"
          % (len(edges), D["Fil_edges_arm_cable"]))
    return s.rotate((0, 0, 0), (0, 0, 1), D["Ang_bracket_sensor"])


def pol(r, degrees):
    a = math.radians(degrees)
    return (r*math.cos(a), r*math.sin(a))


# --- the sensor cover, and the route of the cable --------------------------
# The module was left uncovered: above the board, from z 29.73 up, there was
# nothing - neither bracket, nor collar, nor body. The chip, the pads and the
# solder joints faced the reducer bare-faced.
#
# The constraint that rules the shape is a single one: the cover rests on the
# BRACKET and never on the board. Anything pressing from above moves
# H_rest_module, that is it changes the gap - the most hard-won number of the
# project, and the one you do not see change until you look at a wrong
# measurement. Hence the two bosses on the arms, and the skirt that stays
# hovering three tenths above the face instead of resting on it.
# The arms have TWO face heights, and it is an easy mistake to take one for
# the other: inside the step (r < bracket_step_radius) they are at Hc + h,
# the same plane the board rests on; outside they rise by Th_flange_collar.
# The bosses are at r 40, that is INSIDE: dimensioning them on the high face
# left them hovering in the air three millimetres above the arm, and the
# channel dug into the void. Hence the two distinct names.
Z_FACE_IN = Hc + h                   # 28.13
Z_FACE_OUT = Hc + Fl + h             # 31.13
Z_PLATE = Z_FACE_IN + D["H_boss_cover_sensor"]

def on_arm(phi):
    """The radial unit vector of the arm and the one across it.

    Everything that runs along an arm - saddle, slots, wire passage - must be
    oriented with it, not with the X and Y axes: the first slots were
    rectangles aligned to the world, as wide across the arm as they should
    have been along it."""
    ux, uy = pol(1.0, phi)
    return ux, uy, -uy, ux


def extrude_chamfered(points, z, height):
    """Like extrude_at(), but with the top CHAMFERED at 45 degrees all round.

    It serves the cover, which was rejected as too square. It is not a
    fillet made afterwards on the edges: the outline of the cover is that of
    the module, that is a polyline of some forty segments three millimetres
    long, and a fillet of two on segments that short OCCT carries out
    silently returning an inverted solid - tried, volume -528 cm3.
    Here instead it is extruded twice: at full shape up to the chamfer from
    the top, and then with a draft. On a CONVEX shape - and all the pieces of
    the cover are, the plate, the bands of the tabs and their round ends -
    the draft cannot self-intersect.

    That the pieces can be chamfered one by one and then joined is not a
    shortcut: where two pieces overlap the chamfer of one falls inside the
    solid of the other and the union closes it again, which is exactly what
    is wanted - the chamfer stays only on the outer outline.
    """
    sm = D["Ch_cover_sensor"]
    below = extrude_at(points, z, height - sm)
    return below.union(cq.Workplane("XY").workplane(offset=z + height - sm)
                       .polyline(points).close().extrude(sm, taper=45))


def chamfered_round(x, y, r, z, height):
    """A cylinder with a chamfered top, for the round ends of the tabs."""
    sm = D["Ch_cover_sensor"]
    below = (cq.Workplane("XY").workplane(offset=z).center(x, y)
             .circle(r).extrude(height - sm))
    return below.union(cq.Workplane("XY").workplane(offset=z + height - sm)
                       .center(x, y).circle(r).extrude(sm, taper=45))


def extrude_at(points, z, height):

    """From a flat shape - one of those that live in drawings.py - to the
    solid that comes out extruding it. The shapes of the cable route live
    there because the same ones serve the DXF, the assembly view and the
    checks."""
    return cq.Workplane("XY").workplane(offset=z).polyline(points).close().extrude(height)


def bosses_and_channel(s):
    """What is added to the bracket: the two bosses that carry the cover and,
    on the cable arm, the route of the cable.

    The route is made of three distinct pieces, and they are distinct because
    the cable changes nature along the way. From outside down to r 49 it
    arrives sheathed: it rests in the SADDLE and there the tie locks it onto
    the PAD, and it is that tie that saves the pads of the module. From r 49
    inwards only the four stripped wires go on, which do not pull: for them
    the PASSAGE is enough, two millimetres high.

    THE PASSAGE WAS A TUNNEL, and now it is not any more. The boss was on the
    axis of the arm and bridged it: the wires passed under it, but to put them
    there one had to THREAD them from one end, and the cable must be layable
    even when the JST connector is already crimped - which does
    not go into a 3.5 x 2 tunnel. The boss has been offset by Off_boss_cable
    (see drawings.cover_bosses) and the lane stays open on top for its
    whole length. The arm, 8 wide, does not reach under the offset boss:
    there it widens with cable_boss_pad().
    """

    H = D["H_passage_wires"]
    # The pad under the offset boss, BEFORE the boss: a boss placed where the
    # arm does not reach stays a solid of its own inside the same file, and
    # only by counting the solids does one notice that the part is two parts.
    s = s.union(extrude_at(cable_boss_pad(), Hc, Z_FACE_IN - Hc))
    # the arm widened to the edges of its two pads: see
    # cable_arm_strips() for why
    for _r in cable_arm_strips():
        s = s.union(extrude_at(_r, Hc, Z_FACE_IN - Hc))
    for phi, across in cover_bosses():
        x, y = boss_centre(phi, across)
        s = s.union(cq.Workplane("XY").workplane(offset=Z_FACE_IN).center(x, y)
                    .circle(D["D_boss_cover_sensor"]/2)
                    .extrude(D["H_boss_cover_sensor"]))
        s = s.cut(cq.Workplane("XY").workplane(offset=Z_PLATE + 0.5).center(x, y)
                  .circle(D["D_hole_insert_M25"]/2).extrude(-(D["L_insert_M25"]+0.5)))
    # the pad of the cable clamp, a local widening of the arm
    s = s.union(extrude_at(tie_pad(), Hc, Z_FACE_IN - Hc))
    # The saddle is inside the pad and nowhere else, and its bottom is flat.
    # Two reasons, both measured. The flat bottom because a cylindrical saddle
    # of 6.5 dug 1.2 deep has a mouth 5.04 wide: a 6 cable does not rest in
    # there, it gets stuck. And only in the pad because only there is the arm
    # 16 wide and can afford a 6.5 groove - on the bare arm, 8 wide, 0.75 of
    # wall per side would be left. Outside the pad the cable rests on the arm
    # and that is all: what holds it still is the tie, not the shape.
    s = s.cut(extrude_at(cable_saddle(), Z_FACE_IN - D["Dp_channel_cable"],
                         D["Dp_channel_cable"] + 1))
    # the two slots of the tie, one per side of the cable, that go right
    # through the pad
    for slot in tie_slots():
        s = s.cut(extrude_at(slot, Hc - 1, Z_FACE_IN - Hc + 2))
    # THE RIM BETWEEN SADDLE AND SLOT (check_thin). The slots sit
    # Cd_slots_tie/2 from the centre line to clear the CABLE by 0.75, and the
    # saddle is the cable plus half a millimetre: between the side of the
    # saddle and the inner edge of each slot, as deep as the saddle, a rim of
    # half a millimetre was left - one loose line of the slicer. It holds
    # nothing: the tie comes up the slot and goes straight over the cable. So
    # where that rim is thinner than Th_min_wall_printing it is taken away,
    # as long as the slot and only as deep as the saddle; the slots and the
    # saddle stay where they were chosen.
    _rim = (D["Cd_slots_tie"]/2 - D["H_slot_tie"]/2) - D["D_channel_cable"]/2
    if 0.0 < _rim < D["Th_min_wall_printing"]:
        for side in (-1, 1):
            _t = side*(D["D_channel_cable"]/2 + _rim/2)
            s = s.cut(extrude_at(arm_rect(D["R_tie_cable"], _t, D["W_slot_tie"], _rim + 0.02,
                                              cable_arm()),
                                 Z_FACE_IN - D["Dp_channel_cable"], D["Dp_channel_cable"] + 1))
        print("bracket: %.2f rim between saddle and tie slots taken away" % _rim)
    # ...and the groove underneath that joins them, so the tie passing under
    # the arm does not lift the bracket off the wheel body
    s = s.cut(extrude_at(tie_groove(), Hc - 1, 1 + D["Dp_groove_tie"]))
    # The passage of the wires: a lane dug in the face of the arm, from the
    # tie up to the side of the skirt. The boss bridges over it - it is joined
    # first and the lane stops below the face - and the wires pass under it.
    # Between the top of the lane and the bottom of the insert's seat 2 mm of
    # solid boss remain.
    s = s.cut(extrude_at(wire_passage(), Z_FACE_IN - H, H))
    # The mouth of the passage, rounded where it opens into the capacitor
    # window: the wires come out of the window and turn
    # into the passage right there, and a square corner is an edge to bend
    # them over. A true arc - the square of side Rf in the corner minus the
    # disc of radius Rf tangent to both walls - and only as deep as the
    # passage, because below its floor the material is continuous and there is
    # no corner, only a notch to make.
    #
    # TWICE THE STEP, not the step (the first try showed why): a
    # radius as wide as the step between window and passage makes a quarter
    # circle, tangent to both; twice as wide it no longer fits across, so the
    # arc stays tangent to the wall of the passage and runs out ON THE CORNER
    # of the window, meeting its side wall at about 120 degrees instead of
    # 90. Along the passage it reaches L = sqrt(2 R s - s^2) from the window,
    # which for R = s is s again - the quarter circle of before.
    corners, rf = wire_passage_mouth()
    sg = mouth_step()
    lb = math.sqrt(2*rf*sg - sg*sg)
    phi = math.radians(cable_arm())
    ux, uy = math.cos(phi), math.sin(phi)
    for rc, tc, side in corners:
        square = extrude_at(arm_rect(rc + lb/2 - 0.005, tc + side*sg/2, lb + 0.01, sg),
                            Z_FACE_IN - H, H + 1)
        cr, ct = rc + lb, tc + side*rf
        disc = (cq.Workplane("XY").workplane(offset=Z_FACE_IN - H - 1)
                .center(cr*ux - uy*ct, cr*uy + ux*ct).circle(rf).extrude(H + 3))
        s = s.cut(square.cut(disc))
    return s


def optical_axis_distance(points):
    """How close the given flat shape comes to the optical axis, once put in
    its assembly position. The optical axis is at Off_hole_optical from the
    disc centre, on the side opposite the V."""
    a = math.radians(D["Ang_bracket_sensor"])
    c, s = math.cos(a), math.sin(a)
    return min(math.hypot(x*c - y*s + D["Off_hole_optical"], x*s + y*c)
               for x, y in points)


def cover():
    """The sensor cover: a hat over the BOARD, not over the bracket.

    The first design trimmed it to the outline of the bracket. It looked
    prudent and instead covered nothing: at radius 16 the bracket is made of
    the arms alone, 8 wide, so of the skirt two fragments survived instead of
    a ring and the module stayed uncovered on both sides.
    Now the outline is that of the board, swollen by Cl_cover_module plus the
    thickness of the skirt: the cover follows the part it has to protect.

    Towards the optical axis the constraint remains, but stated the right
    way. It is not "do not go beyond the bracket" - the true constraint is the
    covered part: the BOARD already goes in there further than the hub,
    because it must be on the axis of the magnet, and a cover that stopped
    before it would leave uncovered precisely the edge it protects. So it is
    cut with a cylinder that passes where the board passes: the cover gets
    that far and not a tenth further.

    Two ears reach the bosses on the arms: they are what holds it, and never
    the board.
    """
    sp, sg = D["Th_cover_sensor"], D["Th_skirt_cover"]
    z_skirt = Hc + h + D["Cl_skirt_bracket"]
    inner = board_outline(D["Cl_cover_module"])
    outer = board_outline(D["Cl_cover_module"] + sg)
    # the plate, plus the two ears that go and take the bosses. The end of
    # the ear is a ROUND centred on the boss and not a straight cut: it was
    # one of the sharp edges that made the cover square, and a round end costs
    # nothing because the boss under it is round anyway.
    _r_ear = D["D_boss_cover_sensor"]/2 + 0.5
    c = extrude_chamfered(outer, Z_PLATE, sp)
    for phi, _across in cover_bosses():
        _bx, _by = boss_centre(phi, _across)
        c = c.union(extrude_chamfered(arm_rect(D["R_boss_cover_sensor"]/2, _across,
                                                   D["R_boss_cover_sensor"], 2*_r_ear, phi),
                                      Z_PLATE, sp))
        c = c.union(chamfered_round(_bx, _by, _r_ear, Z_PLATE, sp))
    # the skirt: it goes down around the board and stays hovering three
    # tenths above the face of the bracket, so the cover never rests there
    c = c.union(extrude_at(outer, z_skirt, Z_PLATE - z_skirt)
                .cut(extrude_at(inner, z_skirt - 1, Z_PLATE - z_skirt + 2)))
    # the two screw holes, centred on the bosses: on the cable arm the boss is
    # offset, and a hole left on the axis of the arm would have ended up six
    # millimetres beside its screw
    for phi, _across in cover_bosses():
        x, y = boss_centre(phi, _across)
        c = c.cut(cq.Workplane("XY").workplane(offset=Z_PLATE - 1).center(x, y)
                  .circle(D["D_clear_screw_cover_sensor"]/2).extrude(sp + 2))
    # The cable opening is where the cable really comes out: in line with the
    # arm, over the capacitor hole, which does two jobs - relief for the
    # capacitor and exit for the cable.
    c = c.cut(extrude_at(arm_rect(D["L_board_module"]/2, 0.0,
                                      4*(sg + D["Cl_cover_module"]),
                                      D["W_opening_cable"], cable_arm()),
                         z_skirt, Z_PLATE - z_skirt))
    # and the cut of the optical envelope, at the same distance the board
    # reaches: neither further in than it, nor uselessly further out
    d = optical_axis_distance(board_outline())
    c = c.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
        d, 400.0, cq.Vector(-D["Off_hole_optical"], 0, -200), cq.Vector(0, 0, 1)))
        .rotate((0, 0, 0), (0, 0, 1), -D["Ang_bracket_sensor"]))
    return c.rotate((0, 0, 0), (0, 0, 1), D["Ang_bracket_sensor"])




if __name__ == "__main__":
    st = bracket()
    cq.exporters.export(st, OUT + "sensor_bracket.step")
    cov = cover()
    cq.exporters.export(cov, OUT + "sensor_cover.step")
    print("sensor cover %.1f cm3 (%.0f g ASA), top at z %.2f"
          % (cov.val().Volume()/1000, cov.val().Volume()*1.07e-3,
             Z_PLATE + D["Th_cover_sensor"]))
    print("sensor bracket %.1f cm3 (%.0f g ASA), step at r %.1f, module notch %.1f"
          % (st.val().Volume()/1000, st.val().Volume()*1.07e-3, Rg, D["Dp_notch_module"]))
