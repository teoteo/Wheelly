# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Assembly view: all the parts in the same drawing, in plan and in section.

The other drawings show one part at a time, dimensioned for printing it. These
two are for the eye: where each thing sits relative to the others, and what it
is called.

Three ways of drawing a line. Printed parts get a full, heavy line; the
reference ones - body and disc, which are not printed - a dashed line; bought
or external items (motor, sensor board, magnet, spring) a transparent veil.
Every item carries its name, with a callout.

The order of writing matters: DXF has no depth, whoever is written last wins.
So the drawing is composed in three strata - veils, strokes, callouts - and
written in one go at the end, so that the fill of an accessory never covers
the outline of a part.

The colour is explicit because it is the only thing that survives the
conversion to SVG: the DXF layers do not make it there.
"""
import contextlib
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT + "drawings", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
import ezdxf
from ezdxf.enums import TextEntityAlignment
from parameters import D
from outline_arm import outline as arm_outline
from purchased import purchased_parts, axis_ends, along_z
import parameters as params
from dimension_signature import MspFixedSignature
import electronics as E
from drawings import (bracket_outline, screw_slot, bracket_arms,
                      tie_pad, tie_slots, module_holes,
                      cable_arm_strips,
                      d_profile)

R = math.radians
PRINTED      = (0, 0, 0)          # printed parts
REFERENCE    = (105, 105, 105)    # body and disc: not printed
ACCESSORY    = (125, 125, 125)    # motor, board, magnet, spring
CONSTRUCTION = (170, 170, 170)
CALLOUT      = (95, 95, 95)       # the callout lines and the names

# The veils are black and almost fully transparent: they stay readable both on
# the light background and in the dark theme, where the page inverts the whole
# drawing.
VEIL_PART      = 0.06          # opacity of the fill of the printed parts
VEIL_ACCESSORY = 0.13          # accessories are denser: they show underneath

# The standard pitch of the dash pattern is half a millimetre: on a drawing
# 270 mm wide it looks like a continuous line. And the line weight separates
# the parts that get printed from the rest better than colour alone does.
DASH_SCALE   = 6.0
WEIGHT_FULL  = 35        # hundredths of a mm
WEIGHT_LIGHT = 15
WEIGHT_THIN  = 9         # internal features, callouts

LAYERS = (("PROFILO", 7), ("RIFERIMENTO", 8), ("ACCESSORI", 8),
          ("RIEMPIMENTO", 8), ("COSTRUZIONE", 8), ("ETICHETTE", 8))


def _attr(colour, dashed=False, layer="PROFILO", weight=None, scale=None):
    attr = {"layer": layer, "true_color": ezdxf.rgb2int(colour),
            "lineweight": weight if weight is not None else
                          (WEIGHT_FULL if colour == PRINTED else WEIGHT_LIGHT)}
    if dashed:
        attr["linetype"] = "DASHED"
        attr["ltscale"] = DASH_SCALE if scale is None else scale
    return attr


class Scene:
    """The drawing accumulated in strata, written in one go at the end.

    Every method sets aside a function that knows how to draw itself; `emit`
    runs them in the right order: first what is behind, then what is in
    front.
    """
    VEILS, STROKES, CALLOUTS = 0, 1, 2

    def __init__(self, text_height):
        self.strata = ([], [], [])
        self.h = text_height
        self._stack = []
        # without switching the tracker on nothing is recorded, and the
        # signature comes out empty without anyone noticing: it happened at
        # the first attempt
        params.tracker_on()

    def _add(self, stratum, f):
        """Sets aside the closure that draws, WITH THE SIGNATURE of the dimensions.

        Here the signature must be captured now and not when drawing: the
        scene accumulates and writes everything at the end, when the
        parameters were read long before. Without this capture the assembly
        views were the only unsigned drawings, and they are exactly the ones
        the dimensions with no detail drawing fall back on - that is, the case
        in which the editor went wrong the most.
        """
        dims = (self._stack[-1] if self._stack
                else params.read_and_reset_tracker())
        self.strata[stratum].append([dims, f])

    # --- what is behind -----------------------------------------------------
    def veil(self, points, opacity=VEIL_PART):
        """The transparent fill that gives a part its body."""
        def f(m):
            h = m.add_hatch(dxfattribs={"layer": "RIEMPIMENTO",
                                        "true_color": ezdxf.rgb2int((0, 0, 0))})
            h.paths.add_polyline_path([(p[0], p[1]) for p in points], is_closed=True)
            h.transparency = 1.0 - opacity
        self._add(self.VEILS, f)

    # --- the strokes --------------------------------------------------------
    def contour(self, points, colour, closed=True, dashed=False,
                layer="PROFILO", weight=None):
        self._add(self.STROKES, lambda m: m.add_lwpolyline(
            points, close=closed, dxfattribs=_attr(colour, dashed, layer, weight)))

    def circle(self, centre, radius, colour, dashed=False,
               layer="PROFILO", weight=None):
        self._add(self.STROKES, lambda m: m.add_circle(
            centre, radius, dxfattribs=_attr(colour, dashed, layer, weight)))

    def line(self, p0, p1, colour, dashed=False, layer="COSTRUZIONE",
             weight=None, scale=None):
        self._add(self.STROKES, lambda m: m.add_line(
            p0, p1, dxfattribs=_attr(colour, dashed, layer, weight, scale)))

    # --- the parts, as they read --------------------------------------------
    # These methods call others: without the latch below, the first child call
    # would take the whole signature and the second - usually the OUTLINE,
    # that is exactly the geometry the editor looks for - would be left
    # without one. The signature is captured once on entry and holds for the
    # whole group.
    def _group(self, dims=None):
        """Opens a group. With `dims` the caller decides the signature.

        Groups NEST - `signed_with` wraps calls that are in turn composite -
        and in that case the outermost rules: it is the one that knows which
        part the drawing belongs to, while the inner one only knows it is
        drawing an outline.
        """
        if self._stack:
            self._stack.append(self._stack[-1])
            return
        self._stack.append(set(dims) if dims is not None
                           else params.read_and_reset_tracker())

    def _end_group(self):
        group = self._stack.pop()
        if self._stack:
            return
        # The dimensions read INSIDE the group belong to the group. Without
        # this line they went into no signature - the capture is on entry -
        # and on top of that they stayed in the tracker, where the first
        # entity drawn afterwards picked them up. The group's entities hold a
        # reference to this same set, so updating it here updates them all.
        group |= params.read_and_reset_tracker()

    @contextlib.contextmanager
    def signed_with(self, dims):
        """Signs everything drawn in here with dimensions decided outside.

        It serves whoever draws from a list built beforehand: the purchased
        parts are asked for all together, and without this the first entity
        took the parameters of all of them (the «fixed signature», sixty-six
        names on a single polyline).
        """
        self._group(dims)
        try:
            yield
        finally:
            self._end_group()

    def part(self, points, veiled=True):
        """Printed part: heavy outline and, where it helps, a veil of body."""
        self._group()
        try:
            if veiled:
                self.veil(points, VEIL_PART)
            self.contour(points, PRINTED)

        finally:
            self._end_group()

    def round_part(self, centre, radius):
        """Like `part`, but the outline stays a true circle.

        The veil wants a polyline - a fill cannot follow a circle - while
        whoever looks for dimensions in the drawing wants a CIRCLE: that is
        where a diameter is found. So two entities, not one.
        """
        self._group()
        try:
            self.veil(circle_points(centre[0], centre[1], radius, 96), VEIL_PART)
            self.circle(centre, radius, PRINTED)

        finally:
            self._end_group()

    def reference(self, points, closed=True):
        """Body, disc: they are there but are not printed."""
        self._group()
        try:
            self.contour(points, REFERENCE, closed=closed, dashed=True,
                         layer="RIFERIMENTO")

        finally:
            self._end_group()

    def accessory(self, points):
        """Bought or external item: denser veil and grey outline."""
        self._group()
        try:
            self.veil(points, VEIL_ACCESSORY)
            self.contour(points, ACCESSORY, layer="ACCESSORI")

        # --- the names ----------------------------------------------------------
        finally:
            self._end_group()

    def callout(self, text, anchor, tip, tail=None):
        """The item's name, with the line that points at it.

        `anchor` sits on the item, `tip` where the line stops; the text
        continues horizontally on the side the callout heads to.
        """
        self._group()
        try:
            tail = self.h * 1.2 if tail is None else tail
            direction = 1.0 if tip[0] >= anchor[0] else -1.0
            end = (tip[0] + direction * tail, tip[1])
            alignment = (TextEntityAlignment.MIDDLE_LEFT if direction > 0
                         else TextEntityAlignment.MIDDLE_RIGHT)

            def f(m):
                attr = _attr(CALLOUT, layer="ETICHETTE", weight=WEIGHT_THIN)
                m.add_lwpolyline([anchor, tip, end], dxfattribs=attr)
                m.add_circle(anchor, self.h * 0.2, dxfattribs=attr)
                m.add_text(text, height=self.h, dxfattribs=attr).set_placement(
                    (end[0] + direction * self.h * 0.35, end[1]), align=alignment)
            self._add(self.CALLOUTS, f)

        finally:
            self._end_group()

    def legend(self, x, y, entries):
        """The line conventions, in a free corner of the sheet."""
        self._group()
        try:
            step = self.h * 1.9
            sample = self.h * 3.0
            for i, (kind, text) in enumerate(entries):
                yy = y - i * step
                if kind == "bought":
                    self.veil([(x, yy - self.h * 0.45), (x + sample, yy - self.h * 0.45),
                               (x + sample, yy + self.h * 0.45), (x, yy + self.h * 0.45)],
                              VEIL_ACCESSORY)
                    self.contour([(x, yy - self.h * 0.45), (x + sample, yy - self.h * 0.45),
                                  (x + sample, yy + self.h * 0.45), (x, yy + self.h * 0.45)],
                                 ACCESSORY, layer="ETICHETTE")
                else:
                    colour = PRINTED if kind == "printed" else REFERENCE
                    # the sample is short: with the drawing's pitch it would look continuous
                    self.line((x, yy), (x + sample, yy), colour,
                              dashed=(kind == "reference"), layer="ETICHETTE",
                              weight=WEIGHT_FULL if kind == "printed" else WEIGHT_LIGHT,
                              scale=sample / 6.0)
                self._add(self.CALLOUTS, (lambda t, xx, yy: lambda m: m.add_text(
                    t, height=self.h,
                    dxfattribs=_attr(CALLOUT, layer="ETICHETTE", weight=WEIGHT_THIN)
                    ).set_placement((xx, yy), align=TextEntityAlignment.MIDDLE_LEFT)
                    )(text, x + sample + self.h * 0.8, yy))

        finally:
            self._end_group()

    def emit(self, m):
        """Writes everything, giving each group the signature captured at the
        moment it was set aside."""
        mf = MspFixedSignature(m, m.doc)
        for stratum in self.strata:
            for dims, f in stratum:
                mf.dims = dims
                f(mf)


def new_drawing(text_height):
    d = ezdxf.new("R2010", setup=True)
    d.units = ezdxf.units.MM
    for n, c in LAYERS:
        d.layers.add(n, color=c)
    return d, Scene(text_height)


# ==========================================================================
# Service geometry
# ==========================================================================

def pol(r, a, cx=0.0, cy=0.0):
    return (cx + r * math.cos(R(a)), cy + r * math.sin(R(a)))


def rectangle(cx, cy, wid, hgt, rot=0.0):
    p = [(-wid / 2, -hgt / 2), (wid / 2, -hgt / 2),
         (wid / 2, hgt / 2), (-wid / 2, hgt / 2)]
    c, s = math.cos(R(rot)), math.sin(R(rot))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in p]


def circle_points(cx, cy, r, n=48):
    return [pol(r, 360.0 * i / n, cx, cy) for i in range(n)]


def sector(r0, r1, a0, a1, step=1.0):
    # the ends may arrive swapped (the collar goes from 110 to 90): the number
    # of points is counted on the sweep, not on the signed difference,
    # otherwise the arc shrinks to two points and becomes a straight chord.
    n = max(2, int(abs(a1 - a0) / step) + 1)
    ang = [a0 + (a1 - a0) * i / (n - 1) for i in range(n)]
    return ([pol(r1, a) for a in ang] + [pol(r0, a) for a in reversed(ang)])


def from_bulge(points, step=0.5):
    """Expands a polyline (x, y, bulge) in DXF format into a plain polyline.

    The bracket profile is written once only, in drawings.py, with the arcs
    in the DXF way. Here points are needed: for the veil, which cannot follow
    an arc, and because the outline has to be rotated.
    """
    out_pts = []
    for i in range(len(points)):
        x0, y0, b = points[i]
        x1, y1 = points[(i + 1) % len(points)][:2]
        if abs(b) < 1e-9:
            out_pts.append((x0, y0))
            continue
        # centre of the arc: half chord, moved along the perpendicular
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = (x1 - x0) / 2, (y1 - y0) / 2
        k = (1 - b * b) / (2 * b)
        cx, cy = mx - k * dy, my + k * dx
        r = math.hypot(x0 - cx, y0 - cy)
        a0 = math.atan2(y0 - cy, x0 - cx)
        sweep = 4 * math.atan(b)
        n = max(2, int(abs(sweep) * r / step))
        out_pts += [(cx + r * math.cos(a0 + sweep * j / n),
                     cy + r * math.sin(a0 + sweep * j / n)) for j in range(n)]
    return out_pts


def rotate(points, degrees, cx=0.0, cy=0.0):
    c, s = math.cos(R(degrees)), math.sin(R(degrees))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def exits_circle(p0, p1, centre, radius):
    """The point where the segment leaves the circle: p0 inside, p1 outside."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    fx, fy = p0[0] - centre[0], p0[1] - centre[1]
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius
    disc = b * b - 4 * a * c
    if disc <= 0 or a == 0:
        return p0
    tt = (-b + math.sqrt(disc)) / (2 * a)
    return (p0[0] + tt * dx, p0[1] + tt * dy)


def densify(points, step=0.6):
    """The same polyline, with the long sides broken into short spans."""
    dense = []
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % len(points)]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        dense += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    return dense


def clip_inside(points, radius, step=0.6):
    """The outline stripped of what lies below a radius: the inner edge.

    A true boolean cut is not needed - there is no OCCT here, these drawings
    are generated with --solo-dxf too. The outline is densified and the points
    that went inside are pushed onto the circle: what comes out is the
    blending arc.
    """
    out_pts = []
    for x, y in densify(points, step):
        d = math.hypot(x, y)
        out_pts.append((x, y) if d >= radius else (x * radius / d, y * radius / d))
    return out_pts


# ==========================================================================
# PLAN - view from the camera side
# ==========================================================================


def purchased_in_plan(s):
    """The purchased parts, taken from purchased.py: the same positions the
    assembly STEP takes them from. Nothing is redrawn by hand here - a second
    copy drifts at the first touch-up and lies without saying so - and
    whatever is added new shows up in both places together."""
    for v in purchased_parts():
        # Every part carries the signature of ITS dimensions, taken in
        # `purchased.py` at the point where the entry is born. The list is
        # asked for all at once before drawing any of them, so without this
        # the readings of all forty-four parts ended up on the first one
        # drawn: sixty-six names on a single polyline, a signature that no
        # longer narrows anything down. The check is in `check_editor.py`.
        with s.signed_with(v["_dims"]):
            x, y = v["xy"]
            if not along_z(v):
                # in plan a horizontal fastener is not a circle but its
                # flank: the clutch grub is seen for how long it is
                p0, p1, u = axis_ends(v)
                nx, ny = -u[1], u[0]
                r = v["d"]/2
                s.accessory([(p0[0] + nx*r, p0[1] + ny*r), (p1[0] + nx*r, p1[1] + ny*r),
                             (p1[0] - nx*r, p1[1] - ny*r), (p0[0] - nx*r, p0[1] - ny*r)])
            elif v["shape"] == "square":
                s.accessory(rectangle(x, y, v["side"], v["side"]))
            elif v.get("flat"):
                # the shaft is not round: it has the flat, and that is the face
                # the grub presses on. Drawing it smooth means that dimension is
                # in no drawing, and whoever looks for it lands on a number that
                # is equal by chance - it happened, with Z_flat_shaft.
                s.contour(d_profile(x, y, v["d"]/2, D[v["flat"]]), ACCESSORY,
                          layer="ACCESSORI", weight=WEIGHT_THIN)
                # shaft, hub, bearing flanges and screw shanks: they are
                # features inside other parts, not bodies of their own. Thin
                # line and no veil, otherwise everything underneath goes black.
                radius = (v["flange"][0] if v.get("flange") else v["d"]) / 2
                s.circle((x, y), radius, ACCESSORY, layer="ACCESSORI",
                         weight=WEIGHT_THIN)
            else:
                s.accessory(circle_points(x, y, v["d"] / 2))


def purchased_in_section(s, rect):
    """As above, but on the section plane: only what really crosses it is
    drawn. Bearings and screws are off the plane, and in the drawing the
    callouts say so."""
    for v in purchased_parts():
        # Every part carries the signature of ITS dimensions, taken in
        # `purchased.py` at the point where the entry is born. The list is
        # asked for all at once before drawing any of them, so without this
        # the readings of all forty-four parts ended up on the first one
        # drawn: sixty-six names on a single polyline, a signature that no
        # longer narrows anything down. The check is in `check_editor.py`.
        with s.signed_with(v["_dims"]):
            x, y = v["xy"]
            if not along_z(v):
                # The grub and its insert lie along Y, that is perpendicular to
                # the section plane: what shows of them is their circular
                # section, at the height of the axis and at the radius they
                # pass at. They are drawn only if the plane really cuts them.
                p0, p1, _u = axis_ends(v)
                if (p0[1] - 0.0)*(p1[1] - 0.0) > 0 and min(abs(p0[1]), abs(p1[1])) > 0.5:
                    continue
                _r = math.hypot(p0[0], 0.0)
                s.accessory(rect(_r - v["d"]/2, p0[2] - v["d"]/2,
                                 _r + v["d"]/2, p0[2] + v["d"]/2))
                continue
            if abs(y) > 0.5:
                continue
            z0, z1 = v["z"]
            r = math.hypot(x, y)
            half = (v["side"] if v["shape"] == "square" else v["d"]) / 2
            if v.get("inside_motor"):
                s.contour(rect(r - half, z0, r + half, z1), ACCESSORY,
                          layer="ACCESSORI", weight=WEIGHT_THIN)
            else:
                s.accessory(rect(r - half, z0, r + half, z1))


# The callouts of the three views go through the editor catalogues
# (texts_editor): the plan is what the parameters editor shows first, and its
# screenshot is in the English assembly guide. The section and the details
# too: the editor shows them, and they must not be the last Italian in it. A name that appears in more than one view
# (wheel body, collar, clutch, arm, motor, legend) uses the plan's key, so the
# same part is called the same way everywhere.
import texts_editor as TE


def plan():
    d, s = new_drawing(4.0)
    Rc = D["D_body"] / 2
    Rd = D["R_disc"]
    Ia = D["Cd_motor"]
    Re = D["R_out_collar"]
    Ro = D["R_out_box"]
    dp = D["D_plane_opening"]
    ca = D["Chord_opening"]

    # --- wheel body: circle with the straight cut of the opening ------------
    a = math.degrees(math.acos(min(1.0, dp / Rc)))
    s.reference([pol(Rc, x) for x in range(int(a), int(360 - a) + 1)] +
                [(dp, ca / 2), (dp, -ca / 2)])
    s.circle((0, 0), Rd, REFERENCE, dashed=True, layer="RIFERIMENTO")

    # --- optical hole: where the camera looks -------------------------------
    s.circle((-D["Off_hole_optical"], 0), D["R_envelope_optical"],
             CONSTRUCTION, dashed=True, layer="COSTRUZIONE")

    # --- collar -------------------------------------------------------------
    ap, ao = D["Ang_collar_pivot"], D["Ang_collar_opposite"]
    s.part(sector(Rc, Re, -90, -ao))
    s.part(sector(Rc, Re, ap, 90))
    # The central sector is drawn out to ITS own radius. Before, it reached
    # the box's, which covered the same area up to 108 degrees; with the box
    # ending at 75, that trick drew a box that is not there.
    s.part(sector(Rc, Re, -ao, ap))

    # --- box: a single compartment, from the rib at -30 to the flat head ----
    # The head is not radial: it is a plane perpendicular to the board, so the
    # outline closes with a segment and not with a radius.
    a_out, a_in = E.head_angle(Ro, "out"), E.head_angle(Re, "out")
    n = int(a_out + 30.0) + 1
    out_pts = [pol(Ro, -30.0 + (a_out + 30.0)*k/n) for k in range(n + 1)]
    n = int(a_in + 30.0) + 1
    in_pts = [pol(Re, -30.0 + (a_in + 30.0)*k/n) for k in range(n + 1)]
    s.part(out_pts + list(reversed(in_pts)))

    # --- the electronics in the motor compartment: ESTIMATED envelopes ------
    # The small panel is printed; board, XIAO, driver and GX12 are bought, and
    # for XIAO and driver the footprint of the makers' models is drawn.
    def st_poly(s0, s1, t0, t1):
        return [E.xy(s0, t0), E.xy(s1, t0), E.xy(s1, t1), E.xy(s0, t1)]
    s.part(st_poly(E.OP_S[0], E.OP_S[1], E.OP_T[0], E.OP_T[1]), veiled=False)
    s.accessory(st_poly(E.S0, E.S1, E.T0, E.T1))
    s.accessory(st_poly(E.S_XIAO[0], E.S_XIAO[1], E.T_XIAO[0], E.T_XIAO[1]))
    s.accessory(st_poly(E.S_HEATSINK[0], E.S_HEATSINK[1], E.T_HEATSINK[0], E.T_HEATSINK[1]))
    for _v in E.COMPONENTS:
        _t0, _t1, _s0, _s1 = E.st_component(_v)
        s.accessory(st_poly(_s0, _s1, _t0, _t1))
    s.accessory(st_poly(E.GX12_S - E.GX12_NUT/2, E.GX12_S + E.GX12_NUT/2,
                        E.T_HEAD_IN - E.GX12_INSIDE + 3.0, E.T_HEAD_OUT + 6.6))

    # --- the arm's axes -----------------------------------------------------
    Pp = (Rd, D["Off_pivot"])                  # pivot
    Mm = (Ia, 0.0)                             # motor and clutch axis
    Lb = D["L_arm"]
    ux, uy = (Mm[0] - Pp[0]) / Lb, (Mm[1] - Pp[1]) / Lb
    nx, ny = -uy, ux
    if nx * Pp[0] + ny * Pp[1] < 0:
        nx, ny = -nx, -ny                      # outwards, as in the STEP
    w = D["D_hub_pivot"] / 2
    half_side = D["Side_motor"] / 2

    # --- clutch: it lies under the arm, drawn first -------------------------
    s.round_part(Mm, D["D_clutch"] / 2)
    s.circle(Mm, D["D_hub_clutch"] / 2, PRINTED)
    # the shaft hole, which is a D: in plan it shows in true shape, and it is
    # the only place in the assembly where the flat of the hole and that of
    # the shaft are seen one inside the other
    s.contour(d_profile(Mm[0], Mm[1], D["D_hole_clutch"] / 2,
                          D["Z_flat_hole"]), PRINTED, weight=WEIGHT_THIN)

    # --- accessories: motor, board, magnet ----------------------------------
    # The motor plate is not rotated like the arm: the motor and its four
    # holes are aligned with the axes, as in the STEP.
    purchased_in_plan(s)
    s.accessory(rectangle(0, 0, D["L_board_module"], D["W_board_module"]))

    # --- spring: from the seat on the arm to the bottom in the box ----------
    # The axis is perpendicular to the arm; the abscissa s runs from there.
    Q = (Pp[0] + ux * D["Att_spring"], Pp[1] + uy * D["Att_spring"])
    def along(sx):
        return (Q[0] + nx * sx, Q[1] + ny * sx)
    def at_radius(radius):
        lo, hi = 0.0, 100.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if math.hypot(*along(mid)) < radius:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    s0 = at_radius(D["R_rest_spring_arm"])     # flank of the plate
    spring(s, along(s0), (nx, ny), D["L_spring_fitted"], D["D_washer_spring"])
    # The spring cup, where the spring stops. It is not the mouth of the seat:
    # it is a part, and it sits between the spring and the grub so that the
    # grub does not push on its last coil.
    s_sc = at_radius(D["R_seat_spring_box"])
    def _across(sx, t):
        p = along(sx)
        return (p[0] - ny * t, p[1] + nx * t)
    r_sc, sp_sc = D["D_cup_spring"] / 2, D["Th_cup_spring"]
    r_co = D["D_spigot_spring"] / 2
    s.part([_across(s_sc, r_sc), _across(s_sc + sp_sc, r_sc),
            _across(s_sc + sp_sc, -r_sc), _across(s_sc, -r_sc)])
    s.part([_across(s_sc - D["Proj_spigot_spring"], r_co), _across(s_sc, r_co),
            _across(s_sc, -r_co), _across(s_sc - D["Proj_spigot_spring"], -r_co)])
    # the label goes outside, to the right: next to the part it ended up over
    # the drawing
    s.callout(TE.tr("plan.spring_cup"), _across(s_sc + sp_sc / 2, 0), (150, 42))

    # --- arm: the true outline, the STEP's one ------------------------------
    # It is not rebuilt here: arm_outline gives it, the same one that draws
    # the dimensioned plan and that check_audit compares with the section of
    # the STEP. There used to be a third copy of the outline here, and as soon
    # as the arm stopped being a wedge it started drawing a part that does not
    # exist.
    s.part(arm_outline(D))
    s.circle(Pp, D["D_seat_bearings"] / 2, PRINTED, weight=WEIGHT_THIN)
    s.circle(Pp, D["D_pivot_arm"] / 2, PRINTED, weight=WEIGHT_THIN)
    s.circle(Mm, D["D_seat_centring"] / 2, PRINTED, weight=WEIGHT_THIN)
    s.circle(Mm, D["D_clear_shaft"] / 2, PRINTED, weight=WEIGHT_THIN)
    hh = D["Cd_holes_motor"] / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.circle((Mm[0] + sx * hh, Mm[1] + sy * hh), D["D_holes_M3"] / 2,
                     PRINTED, weight=WEIGHT_THIN)

    # --- sensor bracket -----------------------------------------------------
    # It sits at the back, on the telescope-side face: it centres with its
    # ring on the magnet and goes with its two arms to the two M3s of the
    # collar, the only ones on the side free from the rotator.
    asf = D["Ang_bracket_sensor"]
    Rv = D["R_screw_anchor"]
    s.part(rotate(from_bulge(bracket_outline()), asf))
    s.circle((0, 0), D["D_in_ring_bracket"] / 2, PRINTED, weight=WEIGHT_THIN)
    # the M2 holes are no longer on the Y axis: they follow
    # Ang_module_on_bracket, and here they are read from module_holes() instead
    # of rewriting their angles
    for _fm in rotate(module_holes(), asf):
        s.circle(_fm, D["D_holes_M2"] / 2, PRINTED, weight=WEIGHT_THIN)
    for phi in bracket_arms():                  # one M3 slot per paddle
        s.contour(rotate(from_bulge(screw_slot(phi)), asf), PRINTED, weight=WEIGHT_THIN)
    # The cable-clamp pad is part of the outline: without it, the bracket
    # drawn here is no longer the solid's one, and the cable-tie slots would
    # look as if they hung outside the arm.
    s.contour(rotate(tie_pad(), asf), PRINTED)
    # and so does the cable arm widened to its two pads
    for _r in cable_arm_strips():
        s.contour(rotate(_r, asf), PRINTED)
    for _slot in tie_slots():
        s.contour(rotate(_slot, asf), PRINTED, weight=WEIGHT_THIN)
    for phi in bracket_arms():                  # the bosses that hold the cover
        s.circle(pol(D["R_boss_cover_sensor"], asf + phi),
                 D["D_boss_cover_sensor"]/2, PRINTED, weight=WEIGHT_THIN)

    # --- axes ---------------------------------------------------------------
    s.line((-Rc - 6, 0), (Ro + 6, 0), CONSTRUCTION)
    s.line((0, -Rc - 6), (0, Rc + 6), CONSTRUCTION)

    # --- the names ----------------------------------------------------------
    s.callout(TE.tr("plan.wheel_body"), pol(Rc, 152), (-108, 54))
    s.callout(TE.tr("plan.filter_disc"), pol(Rd, 172), (-104, 22))
    s.callout(TE.tr("plan.optical"), pol(D["R_envelope_optical"], 205, -D["Off_hole_optical"], 0),
              (-104, -34))
    s.callout(TE.tr("plan.magnet"), pol(D["D_magnet"] / 2, 250), (-46, -50))
    s.callout(TE.tr("plan.sensor_board"), (D["L_board_module"] / 2, -D["W_board_module"] / 2),
              (-40, -68))
    b1 = asf + min(bracket_arms())
    s.callout(TE.tr("plan.bracket"), pol(D["R_screw_anchor"] - 30, b1),
              (40, -104))
    s.callout(TE.tr("plan.collar_screws"), pol(D["R_screw_anchor"], b1), (104, -84))
    s.callout(TE.tr("plan.collar"), pol((Rc + Re) / 2, 100), (-46, 106))
    s.callout(TE.tr("plan.head"), pol((Re + Ro) / 2 + 8, E.head_angle((Re + Ro) / 2 + 8, "out")), (-40, 150))
    s.callout(TE.tr("plan.board"), E.xy(E.S0 + 4, E.T0 + 6), (-60, 128))
    s.callout(TE.tr("plan.xiao"), E.xy(E.S_XIAO_C, (E.T_XIAO[0] + E.T_XIAO[1]) / 2), (-10, 170))
    s.callout(TE.tr("plan.driver"), E.xy(E.S_DRIVER_C, (E.T_HEATSINK[0] + E.T_HEATSINK[1]) / 2), (60, 160))
    # Below, not beside: here it ended up on the sensor bracket's name, and
    # the two texts overlapped letter on letter.
    s.callout(TE.tr("plan.mech"), pol((Re + Ro) / 2, -18), (108, -116))
    s.callout(TE.tr("plan.clutch"), pol(D["D_clutch"] / 2, -66, Mm[0], Mm[1]), (128, -70))
    s.callout(TE.tr("plan.motor"), (Mm[0] + half_side, Mm[1] - half_side), (146, -36))
    s.callout(TE.tr("plan.arm"), (Pp[0] + ux * 34 - nx * 6, Pp[1] + uy * 34 - ny * 6),
              (150, 100))
    s.callout(TE.tr("plan.spring"), along(s0 + D["L_spring_fitted"] / 2), (140, 62))
    s.callout(TE.tr("plan.pivot"), Pp, (150, 120))

    s.legend(-146, -78,
             [("printed", TE.tr("plan.leg_print")),
              ("reference", TE.tr("plan.leg_ref")),
              ("bought", TE.tr("plan.leg_bought"))])

    m = d.modelspace()
    s.emit(m)
    d.saveas(OUT + "drawings/assembly_plan.dxf")
    return d


def spring(s, base, direction, length, diameter, coils=5):
    """The spring symbol: two end plates and a zigzag between them.

    A grey rectangle is not recognisable; this is.
    """
    nx, ny = direction
    tx, ty = -ny, nx                                   # across the axis
    r = diameter / 2
    def p(sx, t):
        return (base[0] + nx * sx + tx * t, base[1] + ny * sx + ty * t)
    for sx in (0.0, length):
        s.contour([p(sx, -r), p(sx, r)], ACCESSORY, closed=False, layer="ACCESSORI")
    n = coils * 2
    step = length / n
    zig = [p(0.0, 0.0)]
    for i in range(n):
        zig.append(p(step * (i + 0.5), r * 0.8 * (1 if i % 2 == 0 else -1)))
    zig.append(p(length, 0.0))
    s.contour(zig, ACCESSORY, closed=False, layer="ACCESSORI")


# ==========================================================================
# SECTION - plane through the clutch axis
# ==========================================================================
#
# X = radius from the disc centre, Y = axial height, as in the other sections:
# y = 0 on the camera-side face, +y towards the telescope. Pivot and spring do
# not lie on this plane: they appear at their axial height, dashed, to say how
# high they reach.

def section():
    d, s = new_drawing(2.6)
    Rc = D["D_body"] / 2
    Rd = D["R_disc"]
    Ia = D["Cd_motor"]
    Re = D["R_out_collar"]
    Ro = D["R_out_box"]
    H = D["H_body"]
    a0 = D["Th_wall_front"]
    a1 = a0 + D["H_opening"]
    Rw = Rc - D["Th_wall_radial"]
    sc = D["Dp_slot_front"]
    pm = D["Z_plane_mid_disc"]
    sd = D["Th_disc"]
    Fl = D["Th_flange_collar"]
    qf = D["Z_face_motor"]

    def rect(x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    # --- wheel body, not printed --------------------------------------------
    s.reference(rect(0, 0, Rc - sc, a0))
    s.reference(rect(Rw, a0, Rc, a1))
    s.reference(rect(0, a1, Rc, H))
    s.reference(rect(0, pm - sd / 2, Rd, pm + sd / 2))

    # --- accessories: they lie under the parts ------------------------------
    purchased_in_section(s, rect)
    hm = D["H_rest_module"]
    s.accessory(rect(0, H + hm, D["L_board_module"] / 2, H + hm + 1.6))

    # --- sensor bracket -----------------------------------------------------
    # It sits on the telescope-side face. The arms go towards the collar
    # screws, off this plane; here only the ring that centres on the magnet
    # shows. It holds the board at the rest height, and the magnet passes
    # through its hole.
    ra_int = D["D_in_ring_bracket"] / 2
    s.part(rect(ra_int, H, ra_int + 2.0, H + hm))

    # --- collar -------------------------------------------------------------
    Rif = D["R_in_flange_collar"]
    s.part(rect(Rif, -Fl, Re, 0))
    s.part(rect(Rc, 0, Re, H))
    s.part(rect(Rif, H, Re, H + Fl))

    # --- sealing: the two grooves and the labyrinth rib ---------------------
    # They are the reason the collar is made this way, and they were missing:
    # the groove must sit below the bottom of the slot, where the body face is
    # still solid, and the rib must enter the slot without resting on the
    # mouth of the groove.
    Rg = D["R_gasket"]
    lg, pg = D["L_groove_gasket"], D["Dp_groove_gasket"]
    for z, direction in ((0.0, -1.0), (H, 1.0)):
        s.contour(rect(Rg - lg / 2, z, Rg + lg / 2, z + direction * pg),
                  CONSTRUCTION, layer="COSTRUZIONE", weight=WEIGHT_THIN)
    rb0 = Rc - sc + 0.5
    s.part(rect(rb0, 0, rb0 + D["Th_rib_labyrinth"], D["H_rib_labyrinth"]))

    # --- clutch, straddling the mid plane of the disc -----------------------
    sf = D["Th_clutch"]
    z0 = D["Z_top_clutch"]
    s.part(rect(Ia - D["D_clutch"] / 2, pm - sf / 2, Ia + D["D_clutch"] / 2, pm + sf / 2))
    s.part(rect(Ia - D["D_hub_clutch"] / 2, z0,
                Ia + D["D_hub_clutch"] / 2, z0 + D["H_hub_clutch"]), veiled=False)

    # --- box: the two compartments ------------------------------------------
    s.part(rect(Re, D["Z_floor_box"], Ro, 28.5))   # the floor is no longer -38
    s.part(rect(Re, -22.0, Ro, 2.0), veiled=False)   # the compartment is inside the shell

    # --- arm: from the motor face up to height zero -------------------------
    s.part(rect(D["R_pivot"] - D["D_hub_pivot"] / 2, -qf, Ia + D["Side_motor"] / 2, 0))
    # the pivot is not on this plane: only its height
    s.contour(rect(D["R_pivot"] - D["D_hub_pivot"] / 2, -qf,
                   D["R_pivot"] + D["D_hub_pivot"] / 2, H),
              CONSTRUCTION, dashed=True, layer="COSTRUZIONE")

    # --- spring: it is not on this plane either -----------------------------
    # The axis is almost radial and sits at height -6: it is brought here, at
    # its height and at the radii that belong to it, to say where it passes.
    qm = -6.0
    ra, rb = D["R_rest_spring_arm"], D["R_rest_spring_arm"] + D["L_spring_fitted"]
    spring(s, (ra, qm), (1.0, 0.0), rb - ra, D["D_washer_spring"])
    s.contour(rect(D["R_seat_spring_box"], qm - 7.5, Ro, qm + 7.5),
              CONSTRUCTION, dashed=True, layer="COSTRUZIONE")

    # --- reference heights on the axis --------------------------------------
    for y, text in ((0, TE.tr("sec.face_camera")), (pm, TE.tr("sec.mid_plane_disc")),
                    (H, TE.tr("sec.face_telescope"))):
        s.line((0, y), (Ro + 4, y), CONSTRUCTION)
        s._add(Scene.CALLOUTS, (lambda t, yy: lambda m: m.add_text(
            t, height=2.0, dxfattribs=_attr(CONSTRUCTION, layer="ETICHETTE",
                                            weight=WEIGHT_THIN)
            ).set_placement((Ro + 5, yy), align=TextEntityAlignment.MIDDLE_LEFT))(text, y))
    s.line((0, -46), (0, H + hm + 8), CONSTRUCTION)

    # --- the names ----------------------------------------------------------
    s.callout(TE.tr("plan.wheel_body"), (Rc - 14, a1 + 4), (30, 34))
    s.callout(TE.tr("sec.filter_disc"), (Rd - 24, pm), (16, 22))
    s.callout(TE.tr("sec.magnet_board"), (D["L_board_module"] / 2, H + hm + 0.8),
              (-50, 44))
    s.callout(TE.tr("sec.bracket_ring"),
              (ra_int + 1.0, H + hm / 2), (-50, 36))
    s.callout(TE.tr("plan.collar"), (Re - 4, H / 2), (58, 44))
    s.callout(TE.tr("sec.gasket_groove", r="%.1f" % Rg), (Rg, -pg / 2), (-64, -32))
    s.callout(TE.tr("sec.labyrinth_rib"),
              (rb0 + 1, D["H_rib_labyrinth"] / 2), (-64, -40))
    s.callout(TE.tr("plan.clutch"), (Ia, pm + sf / 2), (94, 30))
    s.callout(TE.tr("plan.arm"), (Ia - 24, -qf / 2), (Ro + 20, -10))
    s.callout(TE.tr("plan.motor"), (Ia, -qf - D["L_motor"] / 2), (Ro + 20, -18))
    s.callout(TE.tr("sec.spring_off_plane"), (ra + D["L_spring_fitted"] / 2, qm), (120, -44))
    s.callout(TE.tr("sec.pivot_off_plane"), (D["R_pivot"], H - 3), (128, 40))
    s.callout(TE.tr("sec.box"), (Ro - 6, -30.0), (140, -30))

    s.legend(2, -50,
             [("printed", TE.tr("plan.leg_print")),
              ("reference", TE.tr("plan.leg_ref")),
              ("bought", TE.tr("plan.leg_bought"))])

    m = d.modelspace()
    s.emit(m)
    # the true shape of the parts on this plane (y = 0, through the motor's
    # axis), from the last build: the section above is drawn from the
    # parameters and had fallen behind the one-part box, the hatch, the
    # clutch's holes and the two springs
    import true_shape
    true_shape.draw(m, [(n, ("y", 0.0)) for n in
                           ("box_collar.step", "arm.step", "clutch_hub.step",
                            "clutch_tyre.step", "hatch_cover.step", "grip_cover.step",
                            "references/filter_wheel_body.step",
                            "references/filter_disc.step")],
                       (2.0, -74.0), 2.6, x_min=0.0)   # below the legend, not over it
    d.saveas(OUT + "drawings/assembly_section.dxf")
    return d


# ==========================================================================
# Details to scale: the two joints the assembly views do not show
# ==========================================================================

def details():
    """The motor's seat on the arm and the pivot joint, at 4:1 scale.

    They are the two places where the design went wrong and was corrected -
    the centring seat cut into the wrong face, the bearing flange with no
    room to sit in - and in the assembly views they cannot be seen: in plan
    they are under other parts, and in section the pivot is even off the
    plane. A detail to scale serves to see whether what was corrected is
    really right, and not to make the same mistake again in six months.

    Dimensions are not written here: the names are, and the numbers live in
    the parameters. A drawing that repeats the numbers is a third place to
    keep up to date.
    """
    d, s = new_drawing(3.2)
    K = 4.0                                   # scale 4:1

    def poly(points, ox=0.0, oz=0.0):
        return [((ox + a) * K, (oz + b) * K) for a, b in points]

    def rect(x0, z0, x1, z1, ox=0.0, oz=0.0):
        return poly([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], ox, oz)

    def pt(x, z, ox=0.0, oz=0.0):
        return ((ox + x) * K, (oz + z) * K)

    def title(x, z, text):
        s._add(s.CALLOUTS, (lambda t, p: lambda m: m.add_text(
            t, height=s.h * 1.5,
            dxfattribs=_attr(PRINTED, layer="ETICHETTE", weight=WEIGHT_THIN)
            ).set_placement(p, align=TextEntityAlignment.MIDDLE_LEFT))(text, (x, z)))

    # ---------------------------------------------------------------- A
    # The motor's seat. The arm is cut on the motor axis: the seat shows with
    # its lead-in, the motor hub that enters it, and the flange resting on the
    # face.
    qf = D["Z_face_motor"]
    sp = D["Th_arm"]
    rs = D["D_seat_centring"] / 2
    rb = D["D_mouth_seat_centring"] / 2
    hi = D["H_leadin_seat_centring"]
    hs = D["H_seat_centring"]
    ra = D["D_clear_shaft"] / 2
    rm = D["Side_motor"] / 2
    rc = D["D_circle_motor"] / 2
    rr = D["D_fillet_hub_motor"] / 2
    hc = D["H_circle_motor"]
    hr = D["H_fillet_hub_motor"]

    # the arm, one half at a time: outside, motor face, lead-in, seat, bottom
    # of the seat, shaft hole
    for direction in (-1, 1):
        s.part(poly([(direction * ra, 0), (direction * rm, 0), (direction * rm, -qf),
                     (direction * rb, -qf), (direction * rs, -qf + hi),
                     (direction * rs, -qf + hs), (direction * ra, -qf + hs)]))
    # the motor: flange, hub with its fillet, shaft
    s.accessory(rect(-rm, -qf, rm, -qf - 6.0))
    for direction in (-1, 1):
        s.contour(poly([(direction * rr, -qf), (direction * rc, -qf + hr),
                        (direction * rc, -qf + hc), (direction * ra * 0.7, -qf + hc),
                        (direction * ra * 0.7, -qf)]), ACCESSORY,
                  layer="ACCESSORI", weight=WEIGHT_THIN)
    s.contour(rect(-D["D_shaft"] / 2, -qf, D["D_shaft"] / 2, -qf + sp + 3),
              ACCESSORY, layer="ACCESSORI", weight=WEIGHT_THIN)

    # The callouts of A all sit to the LEFT and at the top, those of B all to
    # the right: pointed towards each other they piled up in the middle of the
    # sheet, and it was seen only by opening the drawing.
    title(-rm * K, (-qf - 11.0) * K, TE.tr("det.title_a"))
    s.callout(TE.tr("det.shaft"), pt(0, -qf + sp + 2.0), pt(-rm - 3, -qf + sp + 4.0))
    s.callout(TE.tr("det.centring_seat"), pt(-rs, -qf + hs - 0.5),
              pt(-rm - 3, -qf + sp - 0.5))
    s.callout(TE.tr("det.leadin_45"),
              pt(-rs - 0.3, -qf + hi / 2), pt(-rm - 3, -qf - 2.0))
    s.callout(TE.tr("det.motor_hub"),
              pt(rr - 0.2, -qf + 0.2), pt(rm + 3, -qf - 2.0))
    s.callout(TE.tr("det.motor_flange_rests"),
              pt(rm - 2, -qf), pt(rm + 3, -qf - 5.0))

    # ---------------------------------------------------------------- B
    # The pivot joint, moved to the right. Here one sees why the collar hub
    # has the spotface and the set-back face.
    OX = rm + 46.0
    rmz = D["D_hub_pivot"] / 2
    rse = D["D_seat_bearings"] / 2
    rfl = D["D_flange_bearing"] / 2
    rla = D["D_spotface_hub"] / 2
    rpe = D["D_pivot_arm"] / 2
    spf = D["Th_flange_bearing"]
    arr = D["Setback_face_hub"]
    hcu = D["H_bearings"] / 2

    for direction in (-1, 1):
        # the arm hub, with the through seat of the bearings
        s.part(rect(direction * rse, -qf, direction * rmz, -qf + sp, OX))
        # the two bearings, each with its flange on the outer side
        s.accessory(rect(direction * rpe, -qf, direction * rse, -qf + hcu, OX))
        s.accessory(rect(direction * rpe, -qf + hcu, direction * rse, -qf + 2 * hcu, OX))
        s.accessory(rect(direction * rpe, -qf - spf, direction * rfl, -qf, OX))
        s.accessory(rect(direction * rpe, 0, direction * rfl, spf, OX))
        # the collar: set-back face, and the spotface that makes room for the flange
        s.part(poly([(direction * rpe, spf), (direction * rla, spf), (direction * rla, arr),
                     (direction * rmz, arr), (direction * rmz, 4.0), (direction * rpe, 4.0)], OX))
    # the pivot, which goes through everything
    s.accessory(rect(-rpe, -qf - spf - 1.0, rpe, spf, OX))

    title((OX - rmz) * K, (-qf - 11.0) * K, TE.tr("det.title_b"))
    s.callout(TE.tr("det.spotface"),
              pt(rla - 0.4, spf / 2, OX), pt(OX + rmz + 3, spf + 3.0))
    s.callout(TE.tr("det.setback_face"),
              pt(rla + 0.6, arr / 2, OX), pt(OX + rmz + 3, -qf + sp + 1.5))
    s.callout(TE.tr("det.flange_only_rubs"),
              pt(rfl - 0.4, spf / 2, OX), pt(OX + rmz + 3, -qf + sp - 2.0))
    s.callout(TE.tr("det.two_bearings"),
              pt(rse - 0.4, -qf + hcu, OX), pt(OX + rmz + 3, -qf - 2.0))
    s.callout(TE.tr("det.collar_pivot"), pt(rpe - 0.2, -qf - spf - 0.5, OX),
              pt(OX + rmz + 3, -qf - 5.0))

    s.legend(-rm * K, (-qf - 16.0) * K,
             [("printed", TE.tr("plan.leg_print")),
              ("bought", TE.tr("plan.leg_bought"))])

    m = d.modelspace()
    s.emit(m)
    d.saveas(OUT + "drawings/assembly_details.dxf")
    return d


if __name__ == "__main__":
    plan()
    section()
    details()
    print("assembly view: plan, section and details")
