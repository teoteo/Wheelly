# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Every move of the assembly guide can be made: the part gets home without
going through anything on its way.

WHY IT EXISTS. The build checks the machine ASSEMBLED, and a part that fits
there can still be impossible to fit. Once the box, slid onto the
collar, went through the head of the pivot screw during the last 8 mm of its
travel (47 mm3 at 4 mm from home) and not at all once seated - so no check
saw it, and it was found with the printed parts in hand. check_wheel_entry
covers one path, the wheel's; this one covers the FAMILY: every move the
guide declares.

WHERE THE MOVES COME FROM. From the assembly guide (guide/chapters.py), which
already says, step by step, what moves and which way: the exploded offset of
a view ("explode") is the direction the part comes in from. Writing the moves a
second time here would give two lists that drift apart; reading the guide
means that a part added to the guide is checked from its first step, and that
an arrow drawn the wrong way in the guide is a failure, not a picture.

HOW A MOVE IS MADE.
  - the MOVING GROUP: the bodies exploded by the same vector in one step,
    plus everything already joined to them - the arm comes with its bearings
    even where the picture forgets them;
  - the OBSTACLES: the still bodies of the step's scene ("context", the
    other bodies mounted in the step, and "target"
    when the target is not drawn), each
    with everything already joined to it. The guide draws a few bodies around
    the move to explain it; the gasket that is not drawn is still there;
  - the PATH: straight along the vector, from home outwards, 1 mm at a time,
    until the group's bounding box is clear of the obstacles' - NOT for the
    length of the arrow, which is chosen for the picture;
  - what is a collision: volume shared with an obstacle, at some point of the
    path, above THRESHOLD - not counting the material the two already share AT
    HOME. That material is by design and guarded by the audit: an insert in
    its seat (the press interference is how it is planted), a screw in its
    insert. Only that material is taken out of the obstacle, not the whole
    obstacle: the first version skipped every pair that overlapped at home,
    and so for an insert the WHOLE box vanished - a plate planted across its
    path on purpose went unseen. A body sliding home through its
    own seat only ever meets material it also meets at home;
  - an insert is drawn as a SOLID cylinder, and a screw running into it
    would cut brass all the way in: for a screw or grub against an insert,
    the screw's own cylinder, prolonged along its axis, is taken out of the
    insert - that is the threaded bore it runs in. Only for that pair: a
    screw against anything else is a screw against a wall;
  - a part the step declares "snap_in" - an elastic part that clicks in,
    like the TPU gaskets - is reported as a NOTE with its volume, not as a
    failure. It is declared per step and not granted to every TPU part: a
    tyre going through a wall is still a collision;
  - a step may declare "bent_leads": the motor it moves has its leads bent
    out of the way. The maker's STEP draws the four leads as rigid bars 17.6
    mm long, and coming up through the hatch under the motor (strategy B)
    they met the edge of the floor for 37 mm3 - wires, which
    bend. In that step the motor is the body without its leads
    (outline_motor.body), which is also what the hatch was cut round.
    Declared per step, like snap_in: elsewhere a lead is still checked;
  - a step may declare a "path" for a body: a path that is not a straight
    line - poses from home outwards, each a rotation (a rotation vector in
    degrees, about a centre) plus a translation, absolute from home. The
    arm cannot get into the one-piece box along a straight line (it goes in
    tilted and turning, found by src/study_paths), and a check
    that only knows straight lines would either fail it for ever or have it
    left out. Between two poses the body moves in samples no longer than
    STEP and no wider than STEP_ANG; a broken straight line is the same
    thing without rotations. The poses can sit in the step itself or in a
    JSON file in guide/paths/ named by the step;
  - a step may declare that the preload spring and its cup "yields"
    while something else moves: in strategy C they go in before
    the arm, and the arm comes home pressing on them, as it does in the hand.
    In that step the cup sits at the back of its travel (Travel_preload along
    the spring axis: the preload grub is not in yet), and a contact with them
    up to YIELD_MAX is a note - the spring compresses that much - while more
    is a failure: pushing home is allowed, going through them is not;
  - within a step, the moves go in order of the length of their offset, the
    shortest first: in an exploded view the part nearest home goes on first
    (the washer before the screw that goes through it).

After the move the two groups are one, and the next move sees them together.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from guide import chapters, scene, write
from check_insert_access import axis_from_solid

STEP_ANG = 1.0     # degrees between two samples of a path with rotations:
                    # at 60 mm from the centre of rotation, one degree is 1 mm
STEP = 1.0         # mm along the path. The collision that started this was
                    # 8 mm long; the thinnest wall is 2.5, the thinnest moving
                    # part 1: at 1 mm a crossing always leaves a sample inside
YIELD_MAX = 5.0      # mm3 a yielding spring may take from a moving part: the
                    # arm hinging home on the edge of the motor face pushes
                    # the spring's end by 3.3 mm3 with the cup at the back of
                    # its travel (measured) - a few tenths of the
                    # spring's compression
THRESHOLD = 0.5        # mm3: below it only the noise of faces that slide in contact
TRAVEL_MAX = 400.0   # more than the whole machine: a path this long that is
                    # still not clear never leaves


def initial_groups():
    """Union-find over body names: which bodies are joined already."""
    parent = {}

    def root(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def join(a, b):
        parent[root(a)] = root(b)

    def group(n):
        r = root(n)
        return {m for m in list(parent) if root(m) == r}

    return root, join, group


def box_of(s, d=(0.0, 0.0, 0.0)):
    """The bounding box as (lo, hi) tuples, moved by d."""
    b = s.BoundingBox()
    return ((b.xmin + d[0], b.ymin + d[1], b.zmin + d[2]),
            (b.xmax + d[0], b.ymax + d[1], b.zmax + d[2]))


def bbox_of_all(solids):
    lo, hi = None, None
    for s in solids:
        a, b = box_of(s)
        lo = a if lo is None else tuple(map(min, lo, a))
        hi = b if hi is None else tuple(map(max, hi, b))
    return lo, hi


def move_box(r, d):
    return (tuple(r[0][i] + d[i] for i in range(3)), tuple(r[1][i] + d[i] for i in range(3)))


def apart(a, b, margin=0.5):
    return any(a[1][i] + margin < b[0][i] or b[1][i] + margin < a[0][i]
               for i in range(3))


def shared(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return 0.0


def sweep(bodies, moving, obstacles, u):
    """Slide the moving bodies along u from home until clear. Returns the list
    of (moving, obstacle, worst volume, at mm), and the length travelled."""
    # every pair is looked at; what a pair shares at home is cut away below
    pairs = [(m, o) for m in moving for o in obstacles]
    bb_obs = bbox_of_all([bodies[o] for o in obstacles])
    bb_mov = bbox_of_all([bodies[m] for m in moving])
    # how far until the group is clear of every obstacle
    travel, t = None, 0.0
    while t <= TRAVEL_MAX:
        if apart(move_box(bb_mov, tuple(c*t for c in u)), bb_obs):
            travel = t
            break
        t += STEP
    if travel is None:
        travel = TRAVEL_MAX
    # Each obstacle is cut down ONCE to the region the moving body sweeps: the
    # samples then intersect a small piece instead of the whole box, which is
    # what makes a thousand samples cost minutes and not hours.
    local = {}
    for m, o in pairs:
        bm = bodies[m].BoundingBox()
        p0 = cq.Vector(bm.xmin, bm.ymin, bm.zmin)
        p1 = cq.Vector(bm.xmax, bm.ymax, bm.zmax)
        d = cq.Vector(*u).multiply(travel)
        lo = cq.Vector(min(p0.x, p0.x + d.x), min(p0.y, p0.y + d.y), min(p0.z, p0.z + d.z))
        hi = cq.Vector(max(p1.x, p1.x + d.x), max(p1.y, p1.y + d.y), max(p1.z, p1.z + d.z))
        zone = cq.Solid.makeBox(hi.x - lo.x + 1, hi.y - lo.y + 1, hi.z - lo.z + 1,
                                lo - cq.Vector(0.5, 0.5, 0.5))
        loc = bodies[o].intersect(zone)
        if loc.Volume() <= 1e-9:
            continue
        if m.startswith(("screw_", "grub_")) and o.startswith("insert_"):
            axis = axis_from_solid(bodies[m])
            if axis is not None:
                c0, a = axis
                r = max(((cq.Vector(v.X, v.Y, v.Z) - cq.Vector(*c0))
                         - cq.Vector(*a) * (cq.Vector(v.X, v.Y, v.Z) - cq.Vector(*c0)).dot(cq.Vector(*a))).Length
                        for v in bodies[m].Vertices())
                bore = cq.Solid.makeCylinder(r + 0.05, 400.0,
                                             cq.Vector(*c0) - cq.Vector(*a) * 200.0, cq.Vector(*a))
                try:
                    loc = loc.cut(bore)
                except Exception:
                    pass
        # the material the pair shares at home is by design: out of the
        # obstacle, and only that
        if shared(bodies[m], loc) > THRESHOLD:
            try:
                loc = loc.cut(bodies[m])
            except Exception:
                pass
        if loc.Volume() > 1e-9:
            local[(m, o)] = loc
    hits = {}
    n = int(travel / STEP) + 1
    for (m, o), loc in local.items():
        bl = box_of(loc)
        bm = box_of(bodies[m])
        for k in range(1, n + 1):
            t = k * STEP
            if apart(move_box(bm, tuple(c*t for c in u)), bl, 0.0):
                continue
            s = bodies[m].translate(cq.Vector(*u).multiply(t))
            v = shared(s, loc)
            if v > THRESHOLD and v > hits.get((m, o), (0, 0))[0]:
                hits[(m, o)] = (v, t)
    return [(m, o, v, t) for (m, o), (v, t) in sorted(hits.items())], travel


def poses_of(path):
    """The poses of a declared path: (centre, [(rotvec_deg, t), ...]) from home."""
    if isinstance(path, str):
        import json
        path = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "guide", "paths", path)))
    c = tuple(path.get("c", (0.0, 0.0, 0.0)))
    poses = [(tuple(p[:3]), tuple(p[3:6])) for p in path["pose"]]
    if poses[0] != ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)):
        poses = [((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))] + poses
    return c, poses


def samples(c, poses):
    """The samples along the poses, interpolated: rotation by slerp, translation
    straight, never more than STEP or STEP_ANG apart."""
    import math
    from scipy.spatial.transform import Rotation as Rot, Slerp
    out = []
    for (r0, t0), (r1, t1) in zip(poses, poses[1:]):
        R0 = Rot.from_rotvec([math.radians(x) for x in r0])
        R1 = Rot.from_rotvec([math.radians(x) for x in r1])
        dang = math.degrees((R0.inv() * R1).magnitude())
        dt = math.dist(t0, t1)
        # a point far from the centre moves more than the centre: the arm is
        # ~60 mm long, so the rotation is also counted as that much travel
        n = max(1, int(math.ceil(max(dt/STEP, dang/STEP_ANG))))
        sl = Slerp([0.0, 1.0], Rot.concatenate([R0, R1]))
        for k in range(1, n + 1):
            f = k/n
            out.append((sl([f])[0].as_rotvec(degrees=True),
                          tuple(a + (b - a)*f for a, b in zip(t0, t1))))
    return out


def move(s, c, rv, t):
    """p' = R (p - c) + c + t, R the rotation vector rv (degrees)."""
    import math
    a = math.sqrt(sum(x*x for x in rv))
    if a > 1e-9:
        s = s.rotate(cq.Vector(*c), cq.Vector(*(c[i] + rv[i]/a for i in range(3))), a)
    return s.translate(cq.Vector(*t))


def moved_box(bx, c, rv, t):
    """The bounding box of a body moved by (rv, t), from its box at home: the
    box itself, eight corners, moved by the same move() and boxed again. It
    is as large as the moved body's own box or larger, never smaller, so a
    pair it finds apart is apart (computing the true box of the
    moved body at every sample, and the obstacle's again each time, was half
    of this check - 42482 calls at 5 ms)."""
    (x0, y0, z0), (x1, y1, z1) = bx
    box_solid = cq.Solid.makeBox(max(x1 - x0, 1e-3), max(y1 - y0, 1e-3), max(z1 - z0, 1e-3),
                               cq.Vector(x0, y0, z0))
    return box_of(move(box_solid, c, rv, t))


def sweep_path(bodies, moving, obstacles, c, poses):
    """Like sweep, along declared poses instead of a straight line."""
    points = samples(c, poses)
    # the region the group sweeps: the obstacles are cut down to it once
    lo, hi = None, None
    for rv, t in points[::max(1, len(points)//40)] + [points[-1]]:
        for m in moving:
            b = move(bodies[m], c, rv, t).BoundingBox()
            lo = (b.xmin, b.ymin, b.zmin) if lo is None else tuple(map(min, lo, (b.xmin, b.ymin, b.zmin)))
            hi = (b.xmax, b.ymax, b.zmax) if hi is None else tuple(map(max, hi, (b.xmax, b.ymax, b.zmax)))
    zone = cq.Solid.makeBox(hi[0] - lo[0] + 10, hi[1] - lo[1] + 10, hi[2] - lo[2] + 10,
                            cq.Vector(lo[0] - 5, lo[1] - 5, lo[2] - 5))
    local = {}
    for m in moving:
        for o in obstacles:
            loc = bodies[o].intersect(zone)
            if loc.Volume() <= 1e-9:
                continue
            if shared(bodies[m], loc) > THRESHOLD:
                try:
                    loc = loc.cut(bodies[m])
                except Exception:
                    pass
            if loc.Volume() > 1e-9:
                local[(m, o)] = loc
    hits = {}
    bx_loc = {k: box_of(loc) for k, loc in local.items()}
    bx_mov = {m: box_of(bodies[m]) for m in moving}
    for k, (rv, t) in enumerate(points):
        bx_moved = {}
        for (m, o), loc in local.items():
            if m not in bx_moved:
                bx_moved[m] = moved_box(bx_mov[m], c, rv, t)
            if apart(bx_moved[m], bx_loc[(m, o)], 0.0):
                continue
            s = move(bodies[m], c, rv, t)
            v = shared(s, loc)
            if v > THRESHOLD and v > hits.get((m, o), (0, 0))[0]:
                hits[(m, o)] = (v, k)
    return [(m, o, v, k) for (m, o), (v, k) in sorted(hits.items())], len(points)


def moves(bodies):
    """The moves of the guide, in assembly order, with the scene of each."""
    out = []
    for cap in sorted(chapters.CHAPTERS, key=lambda c: c["num"]):
        # chapter 0 shows the finished machine: no moves. Told by "no mounts
        # AND no declared path": the clutch chapter mounts
        # nothing (its insert went to chapter 2 with the clutch), and "no
        # mounts" alone skipped its declared path, unchecked
        if not any(p.get("mounts") or p.get("path") for p in cap["steps"]):
            continue
        for i, p in enumerate(cap["steps"], 1):
            v = p.get("view") or {}
            context = p.get("context", [])
            if isinstance(context, str):
                context = []
            scene_ = (list(p.get("mounts", [])) + list(context)
                      + list(p.get("target", [])))
            offsets = v.get("explode", {})
            by_vector = {}
            for name, d in offsets.items():
                by_vector.setdefault(tuple(float(x) for x in d), []).append(name)
            out.append(dict(cap=cap["num"], n=i, title=p.get("title", ""),
                              mounts=list(p.get("mounts", [])), scene_bodies=scene_,
                              vectors=by_vector,
                              snap_in=set(p.get("snap_in", [])),
                              bent_leads=set(p.get("bent_leads", [])),
                              path=p.get("path", {}),
                              yields=set(p.get("yields", [])),
                              turned=write.rotations(v)))
    return out


def this_part():
    """--part i/n: this process makes only every n-th sweep, starting from the
    i-th. The moves are not independent - the groups of bodies
    grow as the guide mounts them - but the bookkeeping is cheap and every
    process replays all of it; what costs is the sweeps, and a sweep's result
    changes no group, so each can be made by whichever process. build.py runs
    the parts side by side: one process took ten minutes, the longest check."""
    if "--part" not in sys.argv:
        return 0, 1
    i, n = sys.argv[sys.argv.index("--part") + 1].split("/")
    return int(i), int(n)


def main():
    breaking = "--break" in sys.argv
    part, n_parts = this_part()
    k_sweep = 0
    bodies = scene.load(write.ASSEMBLY)
    root, join, group = initial_groups()
    for n in bodies:
        root(n)

    if breaking:
        # THE FAULT ON PURPOSE: a plate across the path of the M3 insert of the
        # cover, 6 mm above its seat and NOT touching anything at home. The
        # check must find it and name that move.
        b = bodies["insert_M3_cover_1"].BoundingBox()
        bodies["box_collar"] = bodies["box_collar"].fuse(
            cq.Solid.makeBox(12, 12, 1.0, cq.Vector((b.xmin + b.xmax)/2 - 6,
                                                   (b.ymin + b.ymax)/2 - 6, b.zmax + 6)))
        print("!! FAULT ON PURPOSE: a plate 6 mm above insert_M3_cover_1")

    if "--break-path" in sys.argv:
        # THE FAULT ON PURPOSE FOR A DECLARED PATH: the plate
        # above only tests the straight moves. A 3 mm cube where the arm is
        # half way along its declared path in - arm_door.json, through the
        # electronics opening - fused
        # into the box, NOT touching the arm at home. It tests the samples
        # along a path and the boxes that decide which of them are looked at.
        c_b, poses_b = poses_of("arm_door.json")
        points_b = samples(c_b, poses_b)
        rv_b, t_b = points_b[len(points_b)//2]
        centre = move(bodies["arm"], c_b, rv_b, t_b).Center()
        cube = cq.Solid.makeBox(3, 3, 3, centre - cq.Vector(1.5, 1.5, 1.5))
        if shared(cube, bodies["arm"]) > 0:
            raise SystemExit("fault on the path: the cube touches the arm at home, move it")
        bodies["box_collar"] = bodies["box_collar"].fuse(cube)
        print("!! FAULT ON PURPOSE: a 3 mm cube on the arm's path at (%.1f, %.1f, %.1f)"
              % (centre.x, centre.y, centre.z))

    problems, notes = [], []
    for mv in moves(bodies):
        unknown = [n for n in mv["scene_bodies"] + [x for l in mv["vectors"].values() for x in l]
                  if n not in bodies]
        if unknown and part == 0:
            problems.append("%d.%d: bodies not in the assembly: %s"
                            % (mv["cap"], mv["n"], ", ".join(sorted(set(unknown)))))
            continue
        all_moving = {x for l in mv["vectors"].values() for x in l}
        for u, listed in sorted(mv["vectors"].items(),
                                  key=lambda kv: sum(c*c for c in kv[0])):
            length = sum(c*c for c in u) ** 0.5
            if length == 0:
                continue
            u1 = tuple(c/length for c in u)
            moving = set()
            for n in listed:
                moving |= group(n)
            forgotten = sorted(moving - set(listed))
            still = [n for n in mv["scene_bodies"] if n not in all_moving and n not in moving]
            obstacles = set()
            for n in still:
                obstacles |= group(n)
            obstacles -= moving
            tag = "%d.%d %s" % (mv["cap"], mv["n"], "+".join(listed))
            if not obstacles:
                # nothing to move against: either a sub-assembly started on
                # the bench, or a target the guide does not name
                if part == 0:
                    notes.append("%s: moves against nothing (bench, or 'target' missing)" % tag)
                continue
            k_sweep += 1
            if (k_sweep - 1) % n_parts != part:
                # another process makes this sweep; the groups join all the same
                for n in list(moving) + list(obstacles):
                    join(n, next(iter(obstacles)))
                continue
            bodies_mv = bodies
            if mv["turned"]:
                # the bodies the picture turns (the clutch on the shaft, grub
                # towards the key): the move is made with them turned
                bodies_mv = dict(bodies_mv)
                for n, (c0, ax, g) in mv["turned"].items():
                    bodies_mv[n] = bodies[n].rotate(cq.Vector(*c0), cq.Vector(*c0) + cq.Vector(*ax), g)
            if mv["bent_leads"] & moving:
                import outline_motor
                bodies_mv = dict(bodies)
                for n in mv["bent_leads"] & moving:
                    bodies_mv[n] = outline_motor.body()
                notes.append("%s: %s with its leads bent (declared bent_leads)"
                            % (tag, ", ".join(sorted(mv["bent_leads"] & moving))))
            if mv["yields"]:
                from parameters import D as _D, spring_axis as _am
                _, _, _nx, _ny, _ = _am()
                _ind = cq.Vector(_nx, _ny, 0).multiply(_D["Travel_preload"])
                bodies_mv = dict(bodies_mv)
                for n in mv["yields"]:
                    bodies_mv[n] = bodies[n].translate(_ind)
            with_path = [n for n in listed if n in mv["path"]]
            if with_path:
                c_p, poses_p = poses_of(mv["path"][with_path[0]])
                hits, n_samples = sweep_path(bodies_mv, sorted(moving), sorted(obstacles), c_p, poses_p)
                hits = [(m, o, v, k) for m, o, v, k in hits]
                travel = float(n_samples)
                tag += " (declared path, %d poses, %d samples)" % (len(poses_p), n_samples)
            else:
                hits, travel = sweep(bodies_mv, sorted(moving), sorted(obstacles), u1)
            if forgotten:
                notes.append("%s: moves with %s, not exploded in the picture"
                            % (tag, ", ".join(forgotten)))
            yielded = [x for x in hits if x[1] in mv["yields"] and x[2] <= YIELD_MAX]
            hits = [x for x in hits if not (x[1] in mv["yields"] and x[2] <= YIELD_MAX)]
            for m, o, vol, t in yielded:
                notes.append("%s: %s pushes %s home - %.1f mm3, within YIELD_MAX (declared yields)"
                            % (tag, m, o, vol))
            snaps = [x for x in hits if x[0] in mv["snap_in"]]
            hits = [x for x in hits if x[0] not in mv["snap_in"]]
            for m, o, vol, t in snaps:
                notes.append("%s: %s clicks into %s - %.0f mm3 of snap at %.0f mm (declared snap_in)"
                            % (tag, m, o, vol, t))
            if hits:
                for m, o, vol, t in hits:
                    problems.append("%s: %s goes through %s - %.1f mm3 at %.0f mm from home"
                                    % (tag, m, o, vol, t))
                print("  NO   %-60s path %.0f mm" % (tag[:60], travel))
            else:
                print("  ok   %-60s path %.0f mm, against %d bodies"
                      % (tag[:60], travel, len(obstacles)))
            # joined from now on
            for n in list(moving) + list(obstacles):
                join(n, next(iter(obstacles)))
        # the bodies mounted in the step without a vector join the scene too
        still_mounted = [n for n in mv["mounts"] if n not in all_moving]
        base = [n for n in mv["scene_bodies"] if n not in all_moving]
        for n in still_mounted:
            for b in base:
                if b != n:
                    join(n, b)
                    break

    print()
    for r in notes:
        print("  note: " + r)
    if problems:
        print("\n%d MOVES DO NOT GO THROUGH%s:" % (len(problems), "" if n_parts == 1
                                                 else " (part %d of %d)" % (part + 1, n_parts)))
        for r in problems:
            print("   " + r)
        return 1
    print("\nEVERY MOVE OF THE GUIDE GETS HOME WITHOUT GOING THROUGH ANYTHING%s"
          % ("" if n_parts == 1 else " (part %d of %d: %d sweeps)" % (part + 1, n_parts,
                                                                       len(range(part, k_sweep, n_parts)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
