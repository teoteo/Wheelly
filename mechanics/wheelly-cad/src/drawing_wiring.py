# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The wiring diagrams, generated instead of drawn by hand.

They come out in pcb/schemi/: one for the XIAO with the driver, one for the
XIAO with the sensor and the LED. They used to be two SVG files written by
hand, and they carried the hole coordinates: at the first move of the layout
they became false, and it was recorded as a defect. Generated from
wiring.py - the same table the layout and the envelopes come from - they can
no longer drift apart, and they get for free the grid printed on the board
and the smooth wires.

There is no data in here: the pinouts, the nets, the colours and the holes
live in wiring.py. The only thing that lives here is the ORDER of the rows,
which is presentation: which connection is read first.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wiring as W
from drawing_common import curve, hole_label, tr, with_language, check_language, LANGUAGES

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(os.path.dirname(os.path.dirname(HERE)), "pcb", "schemi")

WIDTH, MARG = 760, 40
X_LEFT, W_BOX = 60.0, 200.0        # left box
X_RIGHT = 500.0                      # right box
STEP = 46.0                       # between one row and the next

# Each row: (hole on the left, hole on the right, reference of the resistor in
# between or None, note). The pin name, the net and the colour come from wiring.
def diagrams():
    """The three drawings, with their texts in the language being drawn."""
    return [
    dict(file="collegamenti-xiao-tmc2209",
         title=tr("sch.tmc.title"), desc=tr("sch.tmc.desc"),
         left="XIAO ESP32-S3", right="TMC2209",
         rows=[
             ((2, 2), W.pin(W.TMC, "VDD"), None, tr("sch.tmc.r1")),
             ((0, 8), W.pin(W.TMC, "STEP"), None, tr("sch.tmc.r2")),
             ((1, 8), W.pin(W.TMC, "DIR"), None, tr("sch.tmc.r3")),
             ((3, 8), W.pin(W.TMC, "EN"), None, tr("sch.tmc.r4")),
             ((2, 2), W.pin(W.TMC, "EN"), "R1", tr("sch.tmc.r5")),
             ((5, 2), W.pin(W.TMC, "UART"), "R2", tr("sch.tmc.r6")),
             ((4, 2), W.pin(W.TMC, "UART"), None, tr("sch.tmc.r7")),
         ],
         note=[tr("sch.tmc.n%d" % k) for k in range(1, 5)]),
    dict(file="collegamenti-xiao-as5600-led",
         title=tr("sch.as.title"), desc=tr("sch.as.desc"),
         left="XIAO ESP32-S3", right=tr("sch.as.right"),
         cat5=True,
         rows=[
             ((2, 2), (12, 9), None, tr("sch.as.r1")),
             ((1, 2), (13, 9), None, tr("sch.as.r2")),
             ((4, 8), (10, 9), None, tr("sch.as.r3")),
             ((5, 8), (11, 9), None, tr("sch.as.r4")),
             ((3, 2), (3, 0), "R3", tr("sch.as.r5")),
             ((1, 2), (4, 0), None, tr("sch.as.r6")),
         ],
         note=[tr("sch.as.n%d" % k) for k in range(1, 6)]
              + [tr("sch.as.n6", free=", ".join(tr("col." + c) for c in W.CAT5_SPARE))]),
    dict(file="collegamenti-potenza-motore",
         title=tr("sch.pow.title"), desc=tr("sch.pow.desc"),
         left=tr("sch.pow.left"), right=tr("sch.pow.right"),
         rows=[
             ((11, 7), (23, 3), None, tr("sch.pow.r1")),
             ((10, 7), (23, 4), None, tr("sch.pow.r2")),
             ((12, 7), (23, 5), None, tr("sch.pow.r3")),
             ((13, 7), (23, 6), None, tr("sch.pow.r4")),
             ((15, 7), (18, 7), None, tr("sch.pow.r5")),
             ((18, 7), (20, 0), None, tr("sch.pow.r6")),
             ((18, 5), (20, 0), None, tr("sch.pow.r7")),
             ((14, 7), (18, 8), None, tr("sch.pow.r8")),
             ((18, 8), (20, 2), None, tr("sch.pow.r9")),
             ((18, 8), (8, 7), None, tr("sch.pow.r10")),
             ((18, 8), (1, 2), None, tr("sch.pow.r11")),
         ],
         note=[tr("sch.pow.n%d" % k) for k in range(1, 9)]),
    ]

STYLE = """
text{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;fill:#2A2A28}
.th{font-size:14px;font-weight:600}
.ts{font-size:11.5px;fill:#55534E}
.tn{font-size:10px;fill:#7A786F}
.box{fill:#F6F5F1;stroke:#B0AEA6;stroke-width:1}
.res{fill:#E4F1EB;stroke:#3E8C74;stroke-width:1}
.filo{stroke-width:2.2;fill:none;stroke-linecap:round}
.alone{stroke-width:5.4;fill:none;stroke:#FFFFFF;stroke-linecap:round}
"""


def name(p):
    # a hole with no pin is a wire drawn to the wrong place: it used to come
    # out as "?" in the drawing, and the driver's control row once sat that
    # way after it moved. Now it stops the drawing.
    n = W.XIAO.get(p) or W.TMC.get(p) or W.OTHERS.get(p)
    if n is None:
        raise SystemExit("schemi: a wire ends at %s, where no pin is" % (p,))
    return n


def net_of(a, b):
    """The net of the wire between two holes, taken from wiring: not rewritten here.

    It is looked up in both directions, and if the connection goes through a
    resistor the two stretches are two separate wires: finding one is enough,
    the net is the same.
    """
    for wire in W.WIRES:
        if (wire[0], wire[1]) in ((a, b), (b, a)):
            return wire[2]
    for wire in W.WIRES:
        if a in wire[:2] or b in wire[:2]:
            return wire[2]
    return "segnale"


def draw(sc):
    n = len(sc["rows"])
    height = int(2*MARG + 60 + n*STEP + 20*len(sc.get("note", [])))
    el = ['<rect width="%d" height="%d" fill="#FFFFFF"/>' % (WIDTH, height)]
    y_box0, h_box = MARG + 34, n*STEP + 16
    for x, heading in ((X_LEFT, sc["left"]), (X_RIGHT, sc["right"])):
        el.append('<rect class="box" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="8"/>'
                  % (x, y_box0, W_BOX, h_box))
        el.append('<text class="th" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                  % (x + W_BOX/2, y_box0 - 12, heading))
    for i, (a, b, resistor, remark) in enumerate(sc["rows"]):
        y = y_box0 + 26 + i*STEP
        xa, xb = X_LEFT + W_BOX, X_RIGHT
        col = W.COLOURS[net_of(a, b)][0]
        if resistor:
            xm = (xa + xb)/2
            d1 = curve([(xa, y), (xm - 22, y)], 0.10)
            d2 = curve([(xm + 22, y), (xb, y)], -0.10)
            for d in (d1, d2):
                el.append('<path class="alone" d="%s"/>' % d)
                el.append('<path class="filo" d="%s" stroke="%s"/>' % (d, col))
            el.append('<rect class="res" x="%.1f" y="%.1f" width="44" height="20" rx="5"/>'
                      % (xm - 22, y - 10))
            el.append('<text class="ts" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                      % (xm, y + 4, resistor))
        else:
            d = curve([(xa, y), (xb, y)], 0.055)
            el.append('<path class="alone" d="%s"/>' % d)
            el.append('<path class="filo" d="%s" stroke="%s"/>' % (d, col))
        el.append('<text class="ts" x="%.1f" y="%.1f" text-anchor="end">%s · %s</text>'
                  % (xa - 10, y + 4, name(a), hole_label(*a)))
        el.append('<text class="ts" x="%.1f" y="%.1f">%s · %s</text>'
                  % (xb + 10, y + 4, name(b), hole_label(*b)))
        # the conductor of the sensor CAT5 that lands on this hole: a chip
        # with the colour (white with a stripe for the white-X ones) at the
        # right edge of the box, and its name under them
        _wires = W.CAT5_SENSOR.get(b, []) if sc.get("cat5") else []
        for k, (_nm, _solid, _stripe) in enumerate(_wires):
            _xc = X_RIGHT + W_BOX - 34 - (len(_wires) - 1 - k)*30   # same order as the text
            el.append('<rect x="%.1f" y="%.1f" width="24" height="10" rx="2" fill="%s" '
                      'stroke="#8A887F" stroke-width="0.8"/>' % (_xc, y - 5, _solid))
            if _stripe:
                el.append('<rect x="%.1f" y="%.1f" width="24" height="3.4" fill="%s"/>'
                          % (_xc, y - 1.7, _stripe))
        if _wires:
            # inside the box, under the chips: appended to the note in the
            # middle it ran over both boxes on the GND row (seen rendered)
            el.append('<text class="tn" x="%.1f" y="%.1f" text-anchor="end">%s</text>'
                      % (X_RIGHT + W_BOX - 10, y + 18,
                         tr("sch.cable", names=" + ".join(tr("col." + f[0]) for f in _wires))))
        el.append('<text class="tn" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                  % ((xa + xb)/2, y + (26 if resistor else 20), remark))
    # The notes sit OUTSIDE the drawing, in a reserved band: it is the rule of
    # the project, and here it matters also because the first one says NOT to
    # do something.
    y_notes = y_box0 + h_box + 34
    for line in sc.get("note", []):
        el.append('<text class="tn" x="%.1f" y="%.1f">%s</text>' % (X_LEFT, y_notes, line))
        y_notes += 18
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d" role="img">\n<title>%s</title><desc>%s</desc>\n'
           '<style>%s</style>\n%s\n</svg>\n'
           % (WIDTH, height, WIDTH, height, sc["title"], sc["desc"], STYLE, "\n".join(el)))
    p = os.path.join(FOLDER, with_language(sc["file"], "svg"))
    check_language(svg, sc["file"])
    open(p, "w", encoding="utf-8").write(svg)
    return p, WIDTH, height


for _l in LANGUAGES:
    os.environ["WHEELLY_LINGUA"] = _l
    for _sc in diagrams():
        _p, _w, _h = draw(_sc)
        print("wrote %s (%d x %d)" % (os.path.relpath(_p, os.path.dirname(os.path.dirname(HERE))), _w, _h))
