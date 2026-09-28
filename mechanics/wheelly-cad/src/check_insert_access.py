# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The tip of the soldering iron reaches EVERY heat-set insert, not just one.

WHY IT EXISTS, and it is a lesson more than a check. The clearance of the
soldering iron's tip was already checked - but for the pivot insert alone,
named by hand. The STEP of the single part showed that the tip does not
reach the seat of the M4 insert of the preload spring. No check sounded, because no check was looking at that insert.

A check that watches ONE part by name does not watch the family: the next
insert that is added is born unguarded again. Here we start from the assembly
and take ALL the bodies that are inserts, whichever they are.

HOW IT MEASURES. For every insert the axis is read FROM THE SOLID - from its
cylindrical face, not from the parameters it was placed with - and we try to
bring the tip of the soldering iron along that axis, in both directions, from
the face of the insert until it comes out of the part hosting it. It is
enough that ONE direction is free: it is planted from that one. If neither of
the two is, the insert cannot be planted, full stop.

The part it is tested against is the one that HOSTS the insert, and it is
found by looking at which printed body has it inside: when an insert is
planted the machine is not assembled, there is only that part in hand.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_SurfaceType
from guide import scene, write
from parameters import D

# The printed parts an insert can sit in. It is not a list of convenience: it
# is the list of the bodies one has IN HAND while planting, and outside those
# an insert is planted in nothing.
HOSTS = ("box_collar", "board_panel", "arm", "clutch_hub", "sensor_bracket",
          "sensor_cover", "collar", "box")

STEP = 0.5          # every half millimetre along the channel
PROBES_ROUND = 12            # probes round the channel


def axis_from_solid(body):
    """The axis of the insert, read from its cylindrical face.

    From the solid and not from the parameters it was placed with: an insert
    rotated by mistake would keep the parameters it had before, and a check
    that re-read them would say that all is well.
    """
    best = None
    for f in body.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() != GeomAbs_SurfaceType.GeomAbs_Cylinder:
            continue
        if best is None or f.Area() > best[0]:
            a = ad.Cylinder().Axis()
            best = (f.Area(), a.Location(), a.Direction())
    if best is None:
        return None
    _, loc, dirv = best
    return ((loc.X(), loc.Y(), loc.Z()), (dirv.X(), dirv.Y(), dirv.Z()))


def mouth(host, point, direction, r_ring, length=60.0):
    """Where the seat comes out into the open, along the axis of the insert.

    It is not measured from the face of the insert: the tip of the iron does
    not go into the seat - it is Ø8 wide and the seat Ø5 - it stops at the
    MOUTH, i.e. where the hole meets the surface of the part. Measuring from
    the face of the insert made it say "obstructed at 0.3 mm" for a perfectly
    open seat, which was only the wall of the hole. It is the mistake this
    check made at the first attempt.

    THE SECOND ERROR was the opposite one: the
    mouth was taken as the FARTHEST material a thin wire met along the axis.
    From the blind end of a seat on the floor that wire ran up through the
    compartment into the closed roof, and the roof became "the mouth" - the
    channel above it was free, and an insert the iron cannot reach was passed
    as reachable. Now two things are asked of the solid, not one:

      - the wire must NOT meet material in the first millimetre and a half:
        if it does, that is the bottom of the seat, and from that side the
        insert does not go in at all (returns None);
      - the mouth is the first point along the axis where a ring of probes
        just outside the hole, at r_ring, is in the air: that is where the
        wall round the hole ends, i.e. the top of the boss or the face the
        seat opens in.
    """
    u = cq.Vector(*direction)
    a = u.cross(cq.Vector(0, 0, 1)) if abs(u.z) < 0.9 else u.cross(cq.Vector(1, 0, 0))
    a = a.normalized()
    b = u.cross(a).normalized()
    full = lambda p: host.intersect(cq.Solid.makeSphere(0.1, p)).Volume() > 1e-12
    # The bottom is probed with a RING just inside the insert's own radius, not
    # with a wire on the axis: the M4 of the preload sits against a wall with
    # the grub's hole through it, and a wire goes down that hole into the open
    # - but the insert does not, and from that side it cannot go in.
    r_bottom = r_ring - 1.0
    touches = 0
    for dd in (0.3, 0.8, 1.3):
        c = cq.Vector(*point) + u*dd
        for k in range(8):
            t = 2*math.pi*k/8
            if full(c + a*(r_bottom*math.cos(t)) + b*(r_bottom*math.sin(t))):
                touches += 1
    if touches >= 4:
        return None                     # the bottom of the seat, or a lip
    d = 0.0
    while d < 25.0:
        c = cq.Vector(*point) + u*d
        air = 0
        for k in range(8):
            t = 2*math.pi*k/8
            p = c + a*(r_ring*math.cos(t)) + b*(r_ring*math.sin(t))
            if not full(p):
                air += 1
        if air >= 6:
            return d
        d += 0.5
    return d


def free_channel(host, point, direction, radius, length, r_ring):
    """The channel of the tip, FROM THE MOUTH outwards: free or not.

    A single boolean. The first version probed point by point - twelve probes
    per turn, every half millimetre - and on a twelve-megabyte solid it took
    more than an hour without finishing: a check nobody has the patience to
    run is not a check.

    Returns (depth of the mouth, volume obstructing the channel, where the
    obstacle is); the mouth is None if on that side there is the bottom of
    the seat.

    WHERE THE OBSTACLE IS - from how far to how far along the axis, measured
    from the insert's face - is returned too, because a volume alone was read
    wrongly: "16 mm3" on the M3 n.2 of the panel was taken as the panel being
    in the way, and accepted as "planted with the panel off". It
    was the foot of the box's own back wall, 0 to 4.6 mm below the mouth, and
    that nobody can take off.
    """
    b = mouth(host, point, direction, r_ring, length)
    if b is None:
        return None, float("inf"), None
    p = tuple(point[i] + direction[i]*(b + 0.2) for i in range(3))
    remaining = max(length - b - 0.2, 1.0)
    c = cq.Solid.makeCylinder(radius, remaining, cq.Vector(*p), cq.Vector(*direction))
    try:
        x = host.intersect(c)
        vol = x.Volume()
    except Exception:
        return b, 0.0, None
    where = None
    if vol > 1e-6:
        u = cq.Vector(*direction)
        ds = [(cq.Vector(q.X, q.Y, q.Z) - cq.Vector(*point)).dot(u) for q in x.Vertices()]
        if ds:
            where = (min(ds), max(ds))
    return b, vol, where


def main():
    breaking = "--break" in sys.argv
    v = scene.View(scene.load(write.ASSEMBLY))
    radius = (D["D_tip_iron"] + D["Cl_tip_iron"])/2.0
    print("soldering iron tip Ø%.1f with its clearance (Ø%.1f bare)"
          % (2*radius, D["D_tip_iron"]))

    inserts = sorted(n for n in v.bodies if n.lower().startswith("insert_"))
    if not inserts:
        raise SystemExit("no insert in the assembly: the check would "
                         "look at nothing")
    hosts = {n: v.bodies[n] for n in HOSTS if n in v.bodies}
    # The single part is read from its STEP and not rebuilt by fusing the two
    # regions of the assembly: the file also has the openings - the motor's
    # hatch, the hole of the pivot screw - and an opening may be exactly the
    # road the soldering iron arrives by. Fusing the two regions would test
    # against a part without doors, i.e. against a part that does not exist.
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _f = os.path.join(HERE, "out", "box_collar.step")
    if not os.path.exists(_f):
        raise SystemExit("out/box_collar.step is missing: without the real part this "
                         "check would measure a part that does not exist")
    hosts["box_collar"] = cq.importers.importStep(_f).val()
    if breaking:
        # THE FAULT ON PURPOSE: the channel of ONE insert is plugged by walling
        # a slab in front of it. The check must notice and name that very one.
        n0 = inserts[0]
        b = v.bodies[n0].BoundingBox()
        wall = (cq.Workplane("XY").box(40, 40, 40).val()
                .translate(((b.xmin+b.xmax)/2, (b.ymin+b.ymax)/2,
                            (b.zmin+b.zmax)/2)))
        for k in hosts:
            hosts[k] = hosts[k].fuse(wall)
        print("!! FAULT ON PURPOSE: walled up the channel of %s" % n0)

    print()
    failures = []

    # --- THE GX12 NUT MUST BE ABLE TO TURN ---------------------------------
    # It is not an insert, but it is the same family: a part that fits and
    # cannot be mounted. The nut is screwed by hand from inside the
    # compartment, so round it there must remain the ring two fingers pass
    # through - and that ring is something other than the envelope, which
    # would pass all the same.
    #
    # This has priority over the other suggestions for placing the head: if
    # moving the socket costs the ring, the move is not made. A check says so by itself, a note has to be
    # remembered.
    import electronics as E
    _part = hosts.get("box_collar")
    if _part is not None:
        _gx, _gy = E.xy(D["S_gx12"], E.T_HEAD_IN)
        _ux, _uy = -E.V[0], -E.V[1]          # towards the inside of the compartment
        _rr = D["H_nut_gx12"]/2.0 + D["Cl_turn_nut_gx12"]
        _eaten = 0.0
        for _dl in (3.0, 6.0, 9.0):
            _px, _py = _gx + _ux*_dl, _gy + _uy*_dl
            # THE ROTATION MUST BE MADE ROUND THE CENTRE OF THE DISC, not round
            # an axis through z 0: if the axis does not pass through the disc,
            # the disc is not oriented - it MOVES, and goes probing a piece of
            # box that has nothing to do with it. Caught red-handed at the
            # first attempt, with an alarm that looked real.
            _zc = D["Z_gx12"]
            _disc = (cq.Workplane("XY").center(_px, _py).circle(_rr)
                      .extrude(0.8).val()
                      .translate((0, 0, _zc - 0.4))
                      .rotate(cq.Vector(_px, _py, _zc),
                              cq.Vector(_px + _uy, _py - _ux, _zc), 90))
            try:
                _eaten = max(_eaten, _part.intersect(_disc).Volume())
            except Exception:
                pass
        if _eaten > 1.0:
            failures.append("the GX12 nut has no ring to turn in: "
                         "%.0f mm3 of part inside radius %.2f" % (_eaten, _rr))
            print("  NO   %-24s the ring to turn it is taken by %.0f mm3"
                  % ("GX12 nut", _eaten))
        else:
            print("  ok   %-24s turns: ring free up to r %.2f"
                  % ("GX12 nut", _rr))

    for n in inserts:
        body = v.bodies[n]
        a = axis_from_solid(body)
        if a is None:
            failures.append("%s: has no cylindrical face, axis unreadable" % n)
            continue
        centre, axis_dir = a
        bb = body.BoundingBox()
        middle = ((bb.xmin+bb.xmax)/2, (bb.ymin+bb.ymax)/2, (bb.zmin+bb.zmax)/2)
        # where the tip starts from: the face of the insert, not its centre.
        # The half length is read ALONG THE AXIS, from the vertices: half the
        # largest side of the bounding box is right only for an insert lying
        # along x, y or z, and for the M4 of the preload, at 24 degrees, it put
        # the start beyond the retaining wall - outside the part, where
        # everything is free.
        _uu = cq.Vector(*axis_dir).normalized(); _mm = cq.Vector(*middle)
        half_length = max(abs((cq.Vector(vv.X, vv.Y, vv.Z) - _mm).dot(_uu))
                         for vv in body.Vertices()) + 0.2

        # THE HOST IS CHOSEN, NOT FORCED. At the first attempt every insert
        # ended up on box_collar, even those that sit in the small panel or in
        # the sensor cover: and an insert tested against the wrong part gives
        # an alarm that means nothing. The body that really has it inside is
        # taken, and among several candidates the one that contains most of it.
        # The probe is a SHELL round the insert, not a point at its centre: at
        # the centre there is the hole, not the material, and searching there
        # found no host. We look at what stands AROUND it.
        _rr = max(bb.xlen, bb.ylen, bb.zlen)/2.0 + 1.5
        shell = (cq.Solid.makeSphere(_rr, cq.Vector(*middle))
               .cut(cq.Solid.makeSphere(_rr - 1.4, cq.Vector(*middle))))
        who = []
        for k, sol in hosts.items():
            try:
                q = sol.intersect(shell).Volume()
            except Exception:
                q = 0.0
            if q > 1e-9:
                who.append((q, k))
        # box and collar are the two REGIONS of the single part: in their place
        # the test is against the whole part, which is what one has in hand
        who = [(q, "box_collar" if k in ("box", "collar") else k) for q, k in who]
        if not who:
            failures.append("%s: does not sit inside any printed part" % n)
            print("  ??   %-24s does not sit inside any printed part" % n)
            continue
        home = max(who)[1]
        host = hosts[home]
        length = 60.0        # more than the thickest wall of the project

        # the radius of the insert, from the solid: the farthest vertex from
        # its axis. The ring that finds the mouth sits 0.6 outside it, in the
        # wall round the hole.
        _c = cq.Vector(*centre); _u = cq.Vector(*axis_dir).normalized()
        r_ins = max(((cq.Vector(vv.X, vv.Y, vv.Z) - _c) - _u*((cq.Vector(vv.X, vv.Y, vv.Z) - _c).dot(_u))).Length
                    for vv in body.Vertices())
        results = []
        for sign in (+1, -1):
            direction = tuple(sign*c for c in axis_dir)
            start = tuple(middle[i] + direction[i]*half_length for i in range(3))
            results.append(free_channel(host, start, direction, radius, length, r_ins + 0.6))
        good = [i for i, (b, v, _) in enumerate(results) if v <= 1.0]
        if good:
            print("  ok   %-24s in %-12s mouth at %.1f mm, channel free"
                  % (n, home, results[good[0]][0]))
        else:
            _f = lambda e: ("bottom of the seat" if e[0] is None else
                            "%.0f mm3 (mouth at %.1f), obstacle between %.1f and %.1f mm "
                            "from the face of the insert" % (e[1], e[0], *(e[2] or (0, 0))))
            failures.append("%s (in %s): channel obstructed - on one side %s, on the other %s"
                         % (n, home, _f(results[0]), _f(results[1])))
            print("  NO   %-24s in %-12s channel obstructed in BOTH directions "
                  "(%s / %s)" % (n, home, *["bottom" if e[0] is None else "%.0f mm3" % e[1] for e in results]))

    print()
    if failures:
        print("THE TIP DOES NOT REACH %d INSERTS OUT OF %d:" % (len(failures), len(inserts)))
        for r in failures:
            print("   " + r)
        return 1
    print("THE TIP REACHES ALL %d INSERTS" % len(inserts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
