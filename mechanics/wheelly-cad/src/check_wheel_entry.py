# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Does the Ø158 wheel still go in from the side? The check the single part lacked.

Why it exists. Joining box and collar into one part removes the threading-in
of the box - the defect found with the parts in hand - but the collar was a
HALF ring on purpose: the wheel is not lowered along the axis, it slides in
from the side. Closing the ring, or bringing the low wall towards the centre
as point 3 of the specification says, can plug that passage without it
showing: with the machine assembled the solids do not touch all the same.

What it measures, and on what. It re-reads no parameter: it takes the bodies
from the assembly the build has just produced, DERIVES FROM THE SOLID on which
side the collar is open, and passes the wheel through it. The corridor that
comes out of it - the volume the wheel sweeps going in - is the real
constraint for whoever redesigns: the wall can go wherever it likes as long as
it stays out of there.

Why the direction is derived and not written. Writing it by hand would mean
that, moving the opening of the collar, the test would keep bringing the wheel
in from the old side, and keep saying that all is well.
"""
import math
import os
import sys

# the path is derived from the file and not from the folder it is launched
# from: the build calls the checks from mechanics/wheelly-cad, by hand they
# are launched from the root, and a line written by hand works in only one of
# the two places
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from guide import scene, write

# The test travel is chosen here and does not descend from any dimension of the
# part: 200 mm is more than the diameter of the wheel, so it is enough to bring
# it clear of any obstruction, and no dimension of the box can shorten it. If
# the travel came from a parameter of the part, zeroing that parameter would
# zero the test too - the trap that in this project has already cost five
# checks that checked nothing.
TRAVEL = 200.0
STEPS = 40          # five millimetres per step: the longest step that
                    # still does not jump over an ear (the bosses are 6)
THRESHOLD = 1.0     # mm3: below it there is only the noise of the tessellation

# The bodies that move with the wheel: the magnet and its spacer are already
# glued on the hub of the disc when the wheel goes in (chapter 9 of the
# guide), so they go in with it and must be swept with it.
WHEEL_GROUP = ["filter_wheel_body", "filter_disc",
               "magnet_spacer", "magnet_AS5600_1"]
# What it is tested against. NOT the clutch: the TPU ring sits inside the
# wheel's place on purpose, and the arm is held back while the wheel goes in.
OBSTACLES = ["box_collar"]


def collar_opening(collar, cx, cy, z, radius):
    """On which side the collar is open, read on the solid.

    Probes a ring of probes at the given height and radius and looks for the
    widest empty sector: that is the mouth the wheel goes in by. Returns the
    angle of its bisector and its width, in degrees.
    """
    STEP = 2
    full = []
    for g in range(0, 360, STEP):
        a = math.radians(g)
        probe = (cq.Workplane("XY").box(1.0, 1.0, 1.0).val()
                 .translate((cx + radius*math.cos(a), cy + radius*math.sin(a), z)))
        try:
            full.append(collar.intersect(probe).Volume() > 1e-6)
        except Exception:
            full.append(False)
    n = len(full)
    if all(full):
        raise SystemExit("the collar is full all round at r %.0f: there is no mouth" % radius)
    # the longest run of empties, read in a circle
    start = next(i for i in range(n) if full[i] and not full[(i-1) % n])
    best, current, head = (0, 0), 0, None
    for k in range(n + 1):
        i = (start + k) % n
        if not full[i]:
            if head is None:
                head = i
            current += 1
            if current > best[0]:
                best = (current, head)
        else:
            current, head = 0, None
    count, head = best
    centre = (head + (count - 1) / 2.0) % n
    return centre * STEP, count * STEP


def main():
    v = scene.View(scene.load(write.ASSEMBLY))
    # THE FAULTS ON PURPOSE, which are the way this test proves itself alive.
    # The test has two halves and they must be broken one at a time, or only
    # the one that speaks first is proven:
    #   --break-mouth    closes the collar into a full ring. The reader of the
    #                    mouth must sound, which is what decides on which side
    #                    the wheel goes in;
    #   --break-wall     puts a wall inside the corridor, as point 3 of the
    #                    specification taken too far in would. The sweep must
    #                    sound.
    break_mouth = "--break-mouth" in sys.argv
    break_wall = "--break-wall" in sys.argv
    wheel = v.bodies["filter_wheel_body"]
    bb = wheel.BoundingBox()
    cx, cy = (bb.xmin + bb.xmax) / 2.0, (bb.ymin + bb.ymax) / 2.0
    r_wheel = bb.xlen / 2.0
    print("the wheel, measured on the solid: Ø%.1f, z %.1f .. %.1f, axis at (%.2f, %.2f)"
          % (bb.xlen, bb.zmin, bb.zmax, cx, cy))

    if break_mouth:
        c = v.bodies["box_collar"]
        v.bodies["box_collar"] = c.fuse(
            c.rotate(cq.Vector(cx, cy, -50), cq.Vector(cx, cy, 50), 180.0))
        print("!! FAULT ON PURPOSE: the collar closed into a full ring")

    z_mid = (bb.zmin + bb.zmax) / 2.0
    g_mouth, width = collar_opening(v.bodies["box_collar"], cx, cy,
                                    z_mid, r_wheel + 4.0)
    print("the mouth of the collar, read on the solid at z %.1f: centred at %+.0f degrees, %.0f wide"
          % (z_mid, g_mouth, width))
    a = math.radians(g_mouth)
    # the wheel goes IN towards the centre: it starts outside the mouth and slides in
    ux, uy = -math.cos(a), -math.sin(a)
    print("entry direction: (%+.3f, %+.3f), test travel %.0f mm\n" % (ux, uy, TRAVEL))

    if break_wall:
        # a wall as tall as the wheel, placed halfway along the lane: it is
        # the low wall of point 3 brought up right into the passage
        wall = (cq.Workplane("XY").box(6.0, 60.0, bb.zlen).val()
                .translate((cx - ux * 60.0, cy - uy * 60.0,
                            bb.zmin + bb.zlen / 2.0)))
        v.bodies["box_collar"] = v.bodies["box_collar"].fuse(wall)
        print("!! FAULT ON PURPOSE: a wall in the middle of the lane, 60 mm from home")

    group = [v.bodies[n] for n in WHEEL_GROUP if n in v.bodies]
    missing = [n for n in WHEEL_GROUP if n not in v.bodies]
    if missing:
        raise SystemExit("missing from the assembly: %s" % ", ".join(missing))

    hits = []
    for i in range(STEPS + 1):
        t = TRAVEL * (STEPS - i) / STEPS      # from outside (t = TRAVEL) to home (0)
        d = (ux * -t, uy * -t, 0.0)
        for name in OBSTACLES:
            obs = v.bodies[name]
            vol = 0.0
            for body in group:
                try:
                    vol += obs.intersect(body.translate(d)).Volume()
                except Exception:
                    pass
            if vol > THRESHOLD:
                hits.append((t, name, vol))
                print("  HIT at %6.1f mm from home: %-8s %7.0f mm3" % (t, name, vol))

    print()
    if hits:
        print("THE WHEEL DOES NOT GO IN: %d hits, the largest %.0f mm3"
              % (len(hits), max(u[2] for u in hits)))
        return 1
    print("THE WHEEL GOES IN: no hit in %d steps against %s"
          % (STEPS + 1, " and ".join(OBSTACLES)))

    # --- the corridor: the constraint for whoever redesigns ------------------
    # Saying "it goes in" is not enough. Whoever brings the wall towards the
    # centre needs to know WHERE it cannot go, and the place is the volume the
    # wheel sweeps going in: its final place plus the lane it arrives by.
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    seat = (cq.Workplane("XY").center(cx, cy).circle(r_wheel).extrude(bb.zlen)
            .translate((0, 0, bb.zmin))).val()
    # The lane is built along +X and THEN rotated: building it already moved
    # in the entry direction and rotating it afterwards would apply the
    # direction twice. At the first attempt it was like that, and the number
    # that came out looked good.
    lane = (cq.Workplane("XY").box(TRAVEL, 2 * r_wheel, bb.zlen).val()
            .translate((cx - TRAVEL / 2.0, cy, bb.zmin + bb.zlen / 2.0))
            .rotate(cq.Vector(cx, cy, 0), cq.Vector(cx, cy, 1),
                    math.degrees(math.atan2(uy, ux))))
    tunnel = seat.fuse(lane)
    print("\nthe entry corridor (the wheel's place + lane): %.0f cm3"
          % (tunnel.Volume() / 1000.0))
    for name in OBSTACLES:
        dd = BRepExtrema_DistShapeShape(tunnel.wrapped, v.bodies[name].wrapped)
        dd.Perform()
        print("   %-8s stays %.2f mm away from it" % (name, dd.Value()))
    print("\nWhoever redesigns the single part has this: the wall can go wherever")
    print("it likes as long as it stays out of the corridor. What reads above")
    print("is the margin there is today, and that a wall brought towards the")
    print("centre eats up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
