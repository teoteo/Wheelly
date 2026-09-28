# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The placement of the components on the board, and its wires, for whoever wires it.

It comes out in pcb/en_board-layout.svg and pcb/it_disposizione-basetta.svg, next to the wiring diagrams.
It is not drawn by hand: it reads electronics.py (where each component sits,
the same source as the envelopes of the mechanical model) and wiring.py (the
pinouts and the wires), so layout, wires and box cannot say different
things.

Two views of the same board, FROM ABOVE, that is from the component side,
with the head (the USB) on the left and the far end (terminals, towards the
motor) on the right; the BOTTOM edge is the one towards the wheel axis,
where the row printed 01 is (R9 in the model: the rows count from the back,
see electronics.py). The title says it too, because a board
held the other way up puts every part on the right label and the wrong side:
  1. the layout, with the pins of each component;
  2. the same with the wires, coloured by net, and the star ground highlighted.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parameters import D
import electronics as E
import wiring as W
from drawing_common import curve, hole_label, hole_label_below, tr, with_language, sections_of, check_language, LANGUAGES
# Two languages, _en and _it. This is a script, not a
# set of functions: run without WHEELLY_LINGUA it runs itself once per
# language and stops.
if "WHEELLY_LINGUA" not in os.environ:
    import subprocess
    for _l in LANGUAGES:
        _r = subprocess.run([sys.executable, os.path.abspath(__file__)],
                            env=dict(os.environ, WHEELLY_LINGUA=_l))
        if _r.returncode:
            sys.exit(_r.returncode)
    sys.exit(0)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "pcb", with_language("disposizione-basetta", "svg"))

K = 9.0                      # pixels per millimetre
X0 = 70.0                    # left edge of the WHOLE board on the sheet
WIDTH = 800
H_BOARD = D["W_board"]*K


def text(x, y, t, cls="ts", anchor="start"):
    return '<text class="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (cls, x, y, anchor, t)


def marker(letter, x, y):
    """A circled letter next to a point: the band below explains it."""
    return ('<circle class="segno" cx="%.1f" cy="%.1f" r="9"/>' % (x, y)
            + text(x, y + 4, letter, "seg", "middle"))


def view(y0, with_wires, from_below=False):
    """A view of the board with its top-left corner at y0.
    Returns (elements, notable points).

    from_below flips the drawing the way the board is flipped to solder it:
    the direction of the columns is mirrored, the rows stay where they are.
    The LETTERS however are not mirrored with it - they stay in order from
    left to right - because the perfboard carries the silkscreen on both faces
    and each one reads that way. It is the reason the same hole has two names.
    """

    # s grows UPWARDS on the sheet. Seen from above with the head on the left,
    # the frame (s, t, z) is right-handed, so s points up and the wheel axis
    # (small s) is at the bottom. Rejected: s growing downwards - the sheet
    # was then the MIRROR of the model, and since the sheet was right about
    # the XIAO's pinout, the model was the one off: a board built from the
    # sheet came out mirrored with respect to the box (electronics.py).
    def px(t, s):
        _t = (D["L_board"]/2 + t) if from_below else (D["L_board"]/2 - t)
        return (X0 + _t*K, y0 + (E.S1 - s)*K)

    def hole_xy(p):
        return px(E.t_col(p[0]), E.s_row(p[1]))

    def rect(t0, t1, s0, s1, cls, rx=2):
        # The ends are sorted: seen from below the x direction reverses, and
        # a rectangle of negative width is drawn by nobody - it would vanish
        # silently, which is the worst way.
        xa, ya = px(t1, s0)
        xb, yb = px(t0, s1)
        x0_, x1_ = min(xa, xb), max(xa, xb)
        y0_, y1_ = min(ya, yb), max(ya, yb)
        return '<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d"/>' % (
            cls, x0_, y0_, x1_ - x0_, y1_ - y0_, rx)

    _vs = -1.0 if from_below else 1.0        # the x direction, for the offsets

    def beside(x, dx, anchor):
        """A label placed beside a point. From below the side reverses:
        leaving it where it was, the names end up over the wrong part - the
        two LED pins, one pitch apart, printed one on top of the other and
        read LEDED."""
        if from_below:
            return x - dx, {"start": "end", "end": "start", "middle": "middle"}[anchor]
        return x + dx, anchor

    el = []
    el.append(rect(E.T1, D["L_board"]/2, E.S0, E.S1, "taglio", 4))
    el.append(rect(E.T0, E.T1, E.S0, E.S1, "perfboard", 4))
    for c in range(E.N_COL):
        for r in range(E.N_ROW):
            x, y = hole_xy((c, r))
            el.append('<circle cx="%.1f" cy="%.1f" r="1.6" fill="#C4C2BA"/>' % (x, y))
    # Iterate over the LETTERS and look for the column under each one, not
    # the other way round: so from left to right A, C, E... always appear in
    # both views, which is how they are silkscreened.
    for _i in range(0, E.N_COL, 2):
        _c = (E.N_COL - 1 - _i) if from_below else _i
        x, _ = hole_xy((_c, 0))
        el.append(text(x, y0 - 26, chr(ord("A") + _i), "tg", "middle"))
    for r in range(E.N_ROW):
        _, y = hole_xy((0, r))
        el.append(text(X0 + D["L_board"]*K + 10, y + 4, "%02d" % (10 - r), "tg"))

    # sockets, module boards, heatsink, connector
    # each module on its own rows (wiring.R_XIAO / R_DRIVER): the driver's
    # are five holes apart, not six like the XIAO's
    for (c0, c1), rows in (((0, E.NP_XIAO - 1), W.R_XIAO), ((8, 15), W.R_DRIVER)):
        for r in rows:
            el.append(rect(E.t_col(c1) - 1.27, E.t_col(c0) + 1.27,
                           E.s_row(r) - 1.27, E.s_row(r) + 1.27, "strip", 2))
    el.append(rect(E.T_XIAO[0], E.T_XIAO[1], E.S_XIAO[0], E.S_XIAO[1], "modulo", 3))
    el.append(rect(E.T_DRIVER[0], E.T_DRIVER[1], E.S_DRIVER[0], E.S_DRIVER[1], "modulo", 3))
    if not with_wires:
        el.append(rect(E.T_HEATSINK[0], E.T_HEATSINK[1], E.S_HEATSINK[0], E.S_HEATSINK[1], "dis", 2))
    xa, ya = px(E.T_HEAD_OUT, E.S_USB - E.USB_L/2)
    xb, yb = px(E.T_XIAO_EDGE, E.S_USB + E.USB_L/2)
    el.append('<rect class="usb" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"/>'
              % (min(xa, xb), min(ya, yb), abs(xb - xa), abs(yb - ya)))
    x, y = px((E.T_XIAO[0] + E.T_XIAO[1])/2, E.S_XIAO_C)
    el.append(text(x, y + 5, "XIAO", "th" if not with_wires else "thf", "middle"))
    x, y = px(E.T_DRIVER_C, E.S_DRIVER_C)
    el.append(text(x, y + 5, "TMC2209", "th" if not with_wires else "thf", "middle"))

    # the components of the table, with the reference inside and the pins marked
    CLS = {"C": "pow", "J": "box", "R": "res"}
    for entry in E.COMPONENTS:
        t0, t1, s0, s1 = E.st_component(entry)
        cls = CLS[entry[0][0]] + (" smorto" if with_wires else "")
        x, y = px((t0 + t1)/2, (s0 + s1)/2)
        if entry[2] == "round":
            el.append('<circle class="%s" cx="%.1f" cy="%.1f" r="%.1f"/>' % (cls, x, y, entry[4]/2*K))
        else:
            el.append(rect(t0, t1, s0, s1, cls, 3))
        if not with_wires:
            el.append(text(x, y + 4, entry[0], "sig", "middle"))
            for p_ in entry[6]:
                xp, yp = hole_xy(p_)
                el.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="#2A2A28"/>' % (xp, yp))

    # fixing
    for s_, t_ in E.board_holes():
        x, y = px(t_, s_)
        el.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#FFFFFF" stroke="#55534E" stroke-width="1.2"/>'
                  % (x, y, 1.0*K))
    # the third fixing, the one the builder opens with the drill: drawn bolder than
    # the other two, because on the board the hole is not there yet
    _sv, _tv = E.board_head_screw()
    x, y = px(_tv, _sv)
    el.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#FFFFFF" stroke="#B03A2E" stroke-width="2.0"/>'
              % (x, y, 1.25*K))
    for s0, s1, t0, t1 in E.board_guides():
        el.append(rect(t0, t1, s0, s1, "dente", 1))

    if with_wires:
        # first the normal wires, then the star ones on top of all
        for star in (False, True):
            for wire in W.WIRES:
                a, b, net = wire[:3]
                if (net == "stella") != star:
                    continue
                wire_points = [hole_xy(a)] + [hole_xy(v) for v in (wire[3] if len(wire) > 3 else [])] + [hole_xy(b)]
                d = curve(wire_points)
                cl = "filo-stella" if star else "filo"
                # first the white halo, then the wire: so a wire passing over
                # another opens a gap in it, and at the crossings you see which
                # is on top. With straight wires a wire could not be told from
                # a line of the drawing.
                el.append('<path class="alone-%s" d="%s"/>' % (cl, d))
                el.append('<path class="%s" d="%s" stroke="%s"/>'
                          % (cl, d, W.COLOURS[net][0]))
        # all the pins, with their name
        names = dict(W.XIAO)
        names.update(W.TMC)
        names.update(W.OTHERS)
        for (c, r), n in names.items():
            x, y = hole_xy((c, r))
            el.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="#2A2A28"/>' % (x, y))
            if (c, r) in W.XIAO or (c, r) in W.TMC or n in ("VCC", "GND", "SDA", "SCL"):
                # The module rows and the sensor header: the names sit above
                # or below the row, on TWO levels alternating column by column.
                # On one level only the long names touch - UART ran into MS2,
                # GND into VM - and two names stuck together read as one.
                el.append(text(x, y + (-6 if r <= 3 else 14), n, "pin", "middle"))
                # J4: the colour of the CAT5 conductor that lands here, as a
                # chip under the name: the colours next to the connector, on
                # the views from above and below. Same data
                # as the connection drawing: wiring.CAT5_SENSOR.
                for _k, (_nm, _solid, _stripe) in enumerate(W.CAT5_SENSOR.get((c, r), [])):
                    _yc = y + (-22 if r <= 3 else 18) + 7*_k
                    el.append('<rect x="%.1f" y="%.1f" width="12" height="5" rx="1" fill="%s" '
                              'stroke="#8A887F" stroke-width="0.6"/>' % (x - 6, _yc, _solid))
                    if _stripe:
                        el.append('<rect x="%.1f" y="%.1f" width="12" height="1.8" fill="%s"/>'
                                  % (x - 6, _yc + 1.6, _stripe))
            elif n.startswith("LED"):
                # The two LED pins are adjacent, one pitch apart: written on
                # the same side they overlap. The plus goes to the left of its
                # hole, the minus to the right of its own.
                if n.endswith("+"):
                    _xe, _an = beside(x, -6, "end")
                else:
                    _xe, _an = beside(x, 6, "start")
                el.append(text(_xe, y + 3, n, "pin", _an))
            else:
                _xe, _an = beside(x, 6, "start")
                el.append(text(_xe, y + 3, n, "pin", _an))

    # the ground node
    xn, yn = hole_xy(W.NODE)
    el.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="#8A4F0E"/>' % (xn, yn, 7 if with_wires else 5))

    x_usb, y_usb = px(E.T_HEAD_OUT, E.S_USB + E.USB_L/2)
    x_tg = px((E.T1 + D["L_board"]/2)/2, E.S0)[0]
    f_s, f_t = E.board_holes()[0]
    x_f, y_f = px(f_t, f_s)
    d_s0, d_s1, d_t0, d_t1 = E.board_guides()[0]
    x_d, y_d = px((d_t0 + d_t1)/2, d_s0)
    v_s, v_t = E.board_head_screw()
    x_v, y_v = px(v_t, v_s)
    points = [
        ("A", (xn + 16*_vs, yn + 14) if not with_wires else (xn - 20*_vs, yn + 18),
         tr("pt.A")),
        ("B", (x_usb - 12*_vs, y_usb + 16),
         tr("pt.B")),
        ("C", (x_tg, y0 + (27.0 if with_wires else 3.0)*K),
         tr("pt.C", mm="%.2f" % E.CUT_MARGIN)),
        ("D", (x_f - 22*_vs, y_f + 4),
         tr("pt.D")),
        ("E", (x_d - 26*_vs, y_d - 6),
         tr("pt.E")),
        ("F", (x_v - 24*_vs, y_v - 12),
         tr("pt.F", hole=E.board_hole_label(E.COL_HEAD_SCREW, E.ROW_HEAD_SCREW))),

    ]
    for letter, (x, y), _ in points:
        el.append(marker(letter, x, y))
    return el, points


def hole_name(p):
    n = W.XIAO.get(p) or W.TMC.get(p) or W.OTHERS.get(p) or ""
    who = "XIAO " if p in W.XIAO else ("driver " if p in W.TMC else "")
    # Two labels: the one read holding the board from the component side and
    # the one read from the copper side, where you solder. They mirror each
    # other and refer to the SAME hole: whoever holds the soldering iron looks
    # at the second, and without it written would have to convert it in their
    # head every time - which is the way to get the column wrong.
    return "%s%s (%s/%s)" % (who, n, hole_label(*p), hole_label_below(p[0], p[1], E.N_COL))


# The heights at which the sections start. The drawing writes them and whoever
# lays out the booklet reads them: they were numbers copied by hand into
# print_diagrams_pdf.py - 900, 1443 - and at the first section added they would
# have cut in the wrong place without anyone noticing.
SECTIONS = {}

# ---------------- view 1: the layout ----------------
y = 90
everything = [text(WIDTH/2, 34, tr("lay.title"), "tt", "middle"),
         text(40, y - 42, tr("lay.s1"), "th")]
el, points = view(y + 40, False)
everything += el
y += 40 + H_BOARD + 50

# legend
leg = [(c, tr("lay.leg." + c)) for c in
       ("perfboard", "strip", "modulo", "dis", "pow", "box", "res", "dente")]

everything.append('<line x1="30" y1="%d" x2="%d" y2="%d" stroke="#B0AEA6"/>' % (y - 14, WIDTH - 30, y - 14))
for i, (cls, t) in enumerate(leg):
    x = 40 + (i % 2)*380
    yy = y + 10 + (i // 2)*22
    everything.append('<rect class="%s" x="%d" y="%d" width="22" height="14" rx="2"/>' % (cls, x, yy - 11))
    everything.append(text(x + 30, yy, t))
y += 10 + 4*22 + 14
everything.append(text(40, y, tr("lay.components"), "th"))
y += 20
for entry in E.COMPONENTS:
    everything.append(text(40, y, entry[0], "th"))
    everything.append(text(80, y, tr("comp." + entry[0])))
    everything.append(text(400, y, tr("lay.pins_in", holes=", ".join(hole_label(*p_) for p_ in entry[6]))))
    y += 17
y += 12
everything.append(text(40, y, tr("lay.points"), "th"))
y += 20
for letter, _, explanation in points:
    everything.append(marker(letter, 49, y - 4))
    everything.append(text(70, y, explanation))
    y += 22

# ---------------- view 2: the wires ----------------
y += 40
everything.append('<line x1="30" y1="%d" x2="%d" y2="%d" stroke="#B0AEA6" stroke-width="1.5"/>' % (y - 30, WIDTH - 30, y - 30))
SECTIONS["vista_fili"] = int(y - 30)
everything.append(text(40, y, tr("lay.s2"), "th"))
el, _ = view(y + 50, True)
everything += el
y += 50 + H_BOARD + 60

everything.append(text(40, y, tr("lay.nets"), "th"))
y += 20
nets = list(W.COLOURS.items())
for i, (net, (col, explanation)) in enumerate(nets):
    x = 40 + (i % 2)*380
    yy = y + (i // 2)*20
    klass = "filo-stella" if net == "stella" else "filo"
    everything.append('<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (klass, x, yy - 4, x + 24, yy - 4, col))
    everything.append(text(x + 32, yy, tr("net." + net)))
y += ((len(nets) + 1)//2)*20
# the chips at J4: what they are, in the legend band and not on the board
_cat5 = [(n, f) for (_c, _r), fl in sorted(W.CAT5_SENSOR.items(), key=lambda kv: -kv[0][0])
         for n, f in [(W.OTHERS[(_c, _r)], fl[0])]]
_x = 40
for _pin, (_nm, _solid, _stripe) in _cat5:
    everything.append('<rect x="%d" y="%d" width="12" height="5" rx="1" fill="%s" stroke="#8A887F" '
                 'stroke-width="0.6"/>' % (_x + 6, y - 7, _solid))
    if _stripe:
        everything.append('<rect x="%d" y="%.1f" width="12" height="1.8" fill="%s"/>' % (_x + 6, y - 5.4, _stripe))
    _x += 24
everything.append(text(_x + 8, y, tr("lay.cat5", list=", ".join("%s %s" % (tr("col." + f[0]), p)
                                                             for p, f in _cat5)), "ts"))
y += 16 + 16

SECTIONS["stella"] = int(y - 26)
everything.append(text(40, y, tr("lay.star"), "th"))
y += 20
for line in [
    tr("lay.star.%d" % k) for k in range(1, 6)
]:
    everything.append(text(40, y, line, "tn"))
    y += 16
y += 12

everything.append(text(40, y, tr("lay.wires"), "th"))
y += 18
everything.append(text(40, y, tr("lay.wires_note"), "tn"))
y += 20
half = (len(W.WIRES) + 1)//2
for i, wire in enumerate(W.WIRES):
    a, b, net = wire[:3]
    x = 40 + (0 if i < half else 380)
    yy = y + (i if i < half else i - half)*16
    klass = "filo-stella" if net == "stella" else "filo"
    everything.append('<line class="%s" x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>'
                 % (klass, x, yy - 4, x + 14, yy - 4, W.COLOURS[net][0]))
    everything.append(text(x + 20, yy, "%s → %s" % (hole_name(a), hole_name(b)), "tn"))
y += half*16 + 20

# ---------------- view 3: the board from below, for whoever solders ----------------
# Soldering you look at the copper, that is the underside,
# and a view taken from above has to be read mirrored just while you hold the
# soldering iron. The LETTERS however stay in order from left to right, because
# the silkscreen is on both faces and each one reads that way: the same hole
# therefore has two names, and the one from below is the second in brackets in
# the list of wires above.
y += 30
SECTIONS["vista_sotto"] = int(y - 30)
everything.append('<line x1="30" y1="%d" x2="%d" y2="%d" stroke="#B0AEA6" stroke-width="1.5"/>' % (y - 20, WIDTH - 30, y - 20))
everything.append(text(40, y, tr("lay.s3"), "th"))
y += 18
everything.append(text(40, y, tr("lay.s3_note"), "tn"))
el, _ = view(y + 46, True, from_below=True)
everything += el
y += 46 + H_BOARD + 46

for line in [
    tr("lay.warn.%d" % k) for k in range(1, 6)
]:
    everything.append(text(40, y, line, "tn"))
    y += 16
HEIGHT = int(y + 20)

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img">'
       % (WIDTH, HEIGHT, WIDTH, HEIGHT),
       '<title>%s</title>' % tr("lay.svg_title"),
       '<desc>%s</desc>' % tr("lay.svg_desc"),
       '''<style>
text{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;fill:#2A2A28}
.tt{font-size:16px;font-weight:600}
.th{font-size:14px;font-weight:600}
.thf{font-size:14px;font-weight:600;fill:#B0AEA6}
.ts{font-size:12px;fill:#55534E}
.tn{font-size:11.5px;fill:#3F3E3A}
.tg{font-size:10px;fill:#8B8880}
.pin{font-size:7.3px;fill:#2A2A28;font-weight:600;letter-spacing:-0.2px;paint-order:stroke;stroke:#FCFBF7;stroke-width:2.2px;stroke-linejoin:round}
.perfboard{fill:#FBFAF7;stroke:#B0AEA6;stroke-width:1.2}
.taglio{fill:none;stroke:#B0AEA6;stroke-width:1;stroke-dasharray:5 4}
.strip{fill:#3A3A38;stroke:none;opacity:0.8}
.modulo{fill:none;stroke:#2F6FC4;stroke-width:1.4;stroke-dasharray:6 3}
.dis{fill:#DDE6F3;stroke:#2F6FC4;stroke-width:0.8;opacity:0.6}
.box{fill:#F6F5F1;stroke:#8B8880;stroke-width:1}
.res{fill:#E4F1EB;stroke:#3E8C74;stroke-width:1}
.pow{fill:#FBF0DA;stroke:#B5751A;stroke-width:1.2}
.smorto{opacity:0.45}
.usb{fill:#C9C7BF;stroke:#55534E;stroke-width:1}
.dente{fill:#D1483C;opacity:0.7}
.filo{stroke-width:2.2;fill:none;opacity:0.9;stroke-linecap:round;stroke-linejoin:round}
.alone-filo{stroke-width:5.2;fill:none;stroke:#FCFBF7;stroke-linecap:round;stroke-linejoin:round}
.alone-filo-stella{stroke-width:7.8;fill:none;stroke:#FCFBF7;stroke-linecap:round;stroke-linejoin:round}
.filo-stella{stroke-width:4.5;fill:none;stroke-linecap:round}
.sig{font-size:11px;font-weight:600;fill:#2A2A28}
.seg{font-size:11px;font-weight:700;fill:#FFFFFF}
.segno{fill:#55534E}
</style>''',
       '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (WIDTH, HEIGHT)]
svg += everything + ['</svg>']
# EVERY CLASS USED MUST HAVE A RULE. The perfboard rectangle had
# class "perfboard" while the style still said ".basetta" - left behind by the
# rename to English - and a shape with no rule is filled BLACK: the board came
# out black in the printed PDF and the black pin labels on it could not be
# read. Nothing complained, because an SVG with a missing rule is valid.
import re as _re
_svg_text = "\n".join(svg)
_rules = set(_re.findall(r"\.([A-Za-z][\w-]*)\s*\{", _svg_text))
_used = set(c for g in _re.findall(r'class="([^"]+)"', _svg_text) for c in g.split())
_without = sorted(_used - _rules)
if _without:
    raise SystemExit("board layout: classes with no style rule, "
                     "they would come out black: %s" % ", ".join(_without))
check_language(_svg_text, "board layout")
open(OUTPUT, "w").write(_svg_text + "\n")

# The heights of the sections next to the drawing: whoever lays out the booklet
# crops by these, instead of carrying around numbers copied by hand that at
# the first touch-up cut in the wrong place.
SECTIONS["fondo"] = HEIGHT
SECTIONS["largo"] = WIDTH
import json as _json
_sec = sections_of(OUTPUT)
open(_sec, "w").write(_json.dumps(SECTIONS, indent=1, sort_keys=True) + "\n")
print("wrote %s (%d x %d)" % (os.path.relpath(OUTPUT, os.path.dirname(os.path.dirname(HERE))), WIDTH, HEIGHT))
