# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The outline of the arm, once only for 2D and for 3D.

The two drawings in plan - the dimensioned one of the arm and the assembly
view - each rebuilt it on its own, and the solid on its own again. As long
as the arm was a wedge the three copies looked alike enough not to bother;
as soon as the plate became straight along the spring's side they started
telling three different parts. Here the outline is computed once and
everybody uses it, and check_audit compares it with the section of the STEP.

The outline is not obtained with a boolean union: these drawings are
generated with --solo-dxf too, without OCCT. A property of the shape is used
instead: take any line perpendicular to the arm's axis, the solid it meets is
a single stretch. It is enough then, for each station along the arm, to know
how far the material reaches on either side - and the outline is the two rows
of extremes, one on the way out and the other on the way back.

The local frame has its origin on the pivot, x along the arm towards the
motor and y outwards, that is towards the spring.
"""
import math


def _motor_square(D, Lb):
    """The corners of the motor plate, in local coordinates.

    The plate is a square aligned with the GLOBAL axes, not with the arm: the
    motor stands straight in the box, not skewed like the arm. In local
    coordinates therefore the square is turned, and its corners are neither
    at the top nor at the bottom of the straight plate - it is exactly from
    this that the extra corners of the outline are born.
    """
    rot = math.degrees(math.atan2(-D["Off_pivot"]/Lb, (D["Cd_motor"]-D["R_disc"])/Lb))
    half_diag = D["Side_motor"]/2*math.sqrt(2)
    return [(Lb + half_diag*math.cos(math.radians(a - rot)),
             half_diag*math.sin(math.radians(a - rot)))
            for a in (45, 135, 225, 315)]


def ogive(x, y0, y1, xb):
    """The flank that goes from y0 to y1 with two tangent arcs, over a run of xb.

    It serves to remove the step between the pivot hub and the flank of the
    plate: the hub is r 10.5, the plate is 17.6 wide, and the two met edge on
    with a step of 7.1 mm. A single fillet would not be enough: the two
    tangents to respect are both HORIZONTAL - the top of the hub and the
    straight flank - and a single arc cannot be tangent to two parallels
    except by making half a turn. An ogive is needed: two arcs of equal
    radius taking over from each other half way.

    The radius comes out of the geometry, it is not chosen: with a = (y1-y0)/2
    of rise and b = xb/2 of run for each arc, R = (a^2 + b^2) / (2a).
    """
    if xb <= 1e-9:
        return y1
    sense = 1.0 if y1 >= y0 else -1.0
    a, b = abs(y1 - y0)/2.0, xb/2.0
    if a < 1e-9:
        return y0
    R = (a*a + b*b)/(2.0*a)
    if x <= b:
        d = R - math.sqrt(max(0.0, R*R - x*x))
    else:
        d = 2.0*a - (R - math.sqrt(max(0.0, R*R - (xb - x)**2)))
    return y0 + sense*d


def _corner_arc(prev, vert, nxt, radius, step=0.25):
    """The corner `vert` replaced by the arc tangent to the two sides.

    Returns the points from the setback on the side of `prev` to the one on
    the side of `nxt`, so it slots into the polygon in place of the vertex. If
    the fillet does not fit on the sides, the corner stays sharp: better to
    say so than to fake it.
    """
    ux, uy = prev[0]-vert[0], prev[1]-vert[1]
    wx, wy = nxt[0]-vert[0], nxt[1]-vert[1]
    lu, lw = math.hypot(ux, uy), math.hypot(wx, wy)
    if lu < 1e-9 or lw < 1e-9 or radius <= 0:
        return [vert]
    ux, uy, wx, wy = ux/lu, uy/lu, wx/lw, wy/lw
    t = math.acos(max(-1.0, min(1.0, ux*wx + uy*wy)))
    if t < 1e-6 or abs(t - math.pi) < 1e-6:
        return [vert]
    d = radius/math.tan(t/2.0)
    if d > lu or d > lw:
        return [vert]
    p1 = (vert[0]+ux*d, vert[1]+uy*d)
    p2 = (vert[0]+wx*d, vert[1]+wy*d)
    bx, by = ux+wx, uy+wy
    lb = math.hypot(bx, by)
    if lb < 1e-9:
        return [vert]
    c = (vert[0]+bx/lb*radius/math.sin(t/2.0), vert[1]+by/lb*radius/math.sin(t/2.0))
    a1 = math.atan2(p1[1]-c[1], p1[0]-c[0])
    da = math.atan2(p2[1]-c[1], p2[0]-c[0]) - a1
    while da > math.pi:  da -= 2*math.pi
    while da < -math.pi: da += 2*math.pi
    n = max(2, int(abs(da)*radius/step) + 1)
    return [(c[0]+radius*math.cos(a1+da*k/n), c[1]+radius*math.sin(a1+da*k/n))
            for k in range(n+1)]


def _polygon_span(corners, x):
    """The stretch of y that the convex polygon occupies on the vertical x."""
    ys = []
    n = len(corners)
    for i in range(n):
        (x0, y0), (x1, y1) = corners[i], corners[(i+1) % n]
        if x0 == x1:
            if abs(x - x0) < 1e-9: ys += [y0, y1]
            continue
        if min(x0, x1) - 1e-9 <= x <= max(x0, x1) + 1e-9:
            ys.append(y0 + (y1-y0)*(x-x0)/(x1-x0))
    return (min(ys), max(ys)) if ys else None


def _simplify(points, tolerance=0.02):
    """Drop the points that are in line with their neighbours: a sampled
    outline is made almost all of straight stretches, and writing them point
    by point bloats the DXF without adding anything."""
    if len(points) < 3:
        return points
    kept = [points[0]]
    for i in range(1, len(points)-1):
        (ax, ay), (bx, by), (cx, cy) = kept[-1], points[i], points[i+1]
        length = math.hypot(cx-ax, cy-ay)
        dev = (abs((cx-ax)*(ay-by) - (ax-bx)*(cy-ay)) / length) if length > 1e-9 else 0.0
        if dev > tolerance:
            kept.append(points[i])
    kept.append(points[-1])
    return kept


def local_outline(D, step=0.25):
    """The outline of the arm in the local frame, anticlockwise."""
    Lb = D["L_arm"]
    h = D["Side_motor"]/2                      # half width of the plate
    sp = Lb - D["L_plate_solid"]              # where the full width starts
    rm = D["D_hub_pivot"]/2
    w = D["L_band_arm"]/2
    corners = _motor_square(D, Lb)
    xb = D["L_nose_arm"]
    # The two corners of the plate that stick out on the mounted part are the
    # ones with negative global y, that is corners[2] and corners[3]: they get
    # knocked handling the arm, and must be filleted. The other two not - one
    # is buried in the body of the arm, the other is already obtuse, because
    # there the flank of the plate arrives askew.
    #
    # The round is done CLOCKWISE (0, 3, 2, 1) for a practical reason: the
    # wedge meets the corners exactly in this order, so its points are a
    # contiguous slice of this list and the arcs need not be turned round.
    _order = [0, 3, 2, 1]
    _groups = []
    for i, k in enumerate(_order):
        prev, vert, nxt = (corners[_order[i-1]], corners[k],
                           corners[_order[(i+1) % 4]])
        _groups.append(_corner_arc(prev, vert, nxt, D["R_edges_plate_motor"])
                       if k in (2, 3) else [vert])
    square = [p for g in _groups for p in g]

    # the starting wedge: from the band on the pivot to the diagonal corners
    # The same points as the polygon in solids_arm.py, in the same order:
    # the corner near the pivot is NOT in it, and putting it in pinched the
    # inner flank by a millimetre compared with the real part. The filleted
    # corners go in with their arc, or the wedge would take them back sharp.
    wedge = [(0.0, w)] + _groups[0] + _groups[1] + _groups[2] + [(0.0, -w)]

    # the centring spigot of the spring sticks out of the flank: in plan it is
    # a small tooth as wide as it is, and it goes in the drawing, because it
    # is on the part.
    rs = D["D_spigot_spring"]/2

    def extremes(x):
        top, bottom = [], []
        if -rm <= x <= rm:
            dy = math.sqrt(max(0.0, rm*rm - x*x)); top.append(dy); bottom.append(-dy)
        if sp - 1e-9 <= x <= Lb + 1e-9:
            # Between the hub and the plate the flank rises with the ogive
            # instead of jumping with a step. It holds only if the full plate
            # reaches the pivot: if L_plate_solid stops it earlier, there is
            # already the wedge and the ogive would have nothing to attach to.
            if sp <= 1e-9 and 0.0 <= x < xb:
                top.append(ogive(x, rm, h, xb))
                bottom.append(ogive(x, -rm, -h, xb))
            else:
                top.append(h); bottom.append(-h)
        if abs(x - D["Att_spring"]) <= rs:
            top.append(h + D["Proj_spigot_spring"])
        for poly in (square, wedge):
            t = _polygon_span(poly, x)
            if t: bottom.append(t[0]); top.append(t[1])
        return (max(top), min(bottom)) if top else None

    xs = [s[0] for s in square]     # the filleted square, not the sharp corners:
                                    # the fillet shortens the tip on the right
    x0, x1 = min(xs + [-rm, sp, 0.0]), max(xs + [Lb])
    n = max(2, int((x1-x0)/step) + 1)
    grid = [x0 + (x1-x0)*i/(n-1) for i in range(n)]
    upper, lower = [], []
    for x in grid:
        e = extremes(x)
        if e is None: continue
        upper.append((x, e[0])); lower.append((x, e[1]))
    return upper + lower[::-1]


def global_outline(D, step=0.25):
    """The same outline, brought to where the part is: origin on the optical axis."""
    Lb = D["L_arm"]
    Px, Py = D["R_disc"], D["Off_pivot"]
    ux, uy = (D["Cd_motor"]-Px)/Lb, (0.0-Py)/Lb
    nx, ny = -uy, ux
    if nx*Px + ny*Py < 0: nx, ny = -nx, -ny
    return [(Px + x*ux + y*nx, Py + x*uy + y*ny) for x, y in local_outline(D, step)]


def clip_inside(points, radius):
    """The outline deprived of what lies under a radius: the inner edge.

    The points that went into the circle are pushed onto the circle: what
    comes out is the fillet arc. The outline must be kept dense UP TO HERE and
    thinned only after: thinning first, of a long stretch the two ends are
    saved, and if both fall outside the circle the chord joining them passes
    through it all the same. Measured against the STEP, the inner flank came
    in by a millimetre and a half that way.
    """
    out = []
    for x, y in points:
        d = math.hypot(x, y)
        out.append((x, y) if d >= radius else (x*radius/d, y*radius/d))
    return out


def outline(D, inner_radius=None, step=0.25):
    """The outline good for drawing: global, clipped and thinned."""
    if inner_radius is None:
        inner_radius = D["R_rim_inner"]
    return _simplify(clip_inside(global_outline(D, step), inner_radius))
