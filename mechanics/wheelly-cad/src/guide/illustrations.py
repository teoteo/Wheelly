# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Small drawings for the guide, where a render of the assembly cannot say
the thing: the magnetisation of a magnet is not in its shape.

Each drawing is an SVG written by code, with no words in it - N and S are the
same in every language - so one file serves both pages; what it shows is said
in the caption, which goes through the translations. A step asks for one
with "illustrations": {point number: name} in chapters.py.
"""

RED, BLUE = "#d8453c", "#3a6fd8"          # N and S, as on every school magnet
GREEN, WRONG = "#2e9e5b", "#c0392b"


def _cylinder(cx, y, rx, ry, h, diametral):
    """A magnet seen from above at an angle: top face, and the side below it.
    Diametral: the left half N, the right half S, top and side alike.
    Axial: the top face N, the side (and the face under it) S."""
    bottom = y + h
    # the top face split in two by its vertical diameter, and the side in two
    # by the line under it
    left_top = "M%g,%g A%g,%g 0 0 0 %g,%g Z" % (cx, y - ry, rx, ry, cx, y + ry)
    right_top = "M%g,%g A%g,%g 0 0 1 %g,%g Z" % (cx, y - ry, rx, ry, cx, y + ry)
    left_side = ("M%g,%g L%g,%g A%g,%g 0 0 0 %g,%g L%g,%g A%g,%g 0 0 1 %g,%g Z"
               % (cx - rx, y, cx - rx, bottom, rx, ry, cx, bottom + ry, cx, y + ry, rx, ry, cx - rx, y))
    right_side = ("M%g,%g L%g,%g A%g,%g 0 0 1 %g,%g L%g,%g A%g,%g 0 0 0 %g,%g Z"
               % (cx + rx, y, cx + rx, bottom, rx, ry, cx, bottom + ry, cx, y + ry, rx, ry, cx + rx, y))
    edge = "stroke=\"#1b1f23\" stroke-opacity=\".55\" stroke-width=\"1\""
    letter = ("<text x=\"%g\" y=\"%g\" font-family=\"system-ui,sans-serif\" font-size=\"%g\" "
               "font-weight=\"700\" fill=\"#fff\" text-anchor=\"middle\" dominant-baseline=\"central\">%s</text>")
    if diametral:
        r = ["<path d=\"%s\" fill=\"%s\" %s/>" % (left_side, RED, edge),
             "<path d=\"%s\" fill=\"%s\" %s/>" % (right_side, BLUE, edge),
             # the top face a little lighter than the side, so it reads as a face
             "<path d=\"%s\" fill=\"%s\" %s/>" % (left_top, "#ea6a61", edge),
             "<path d=\"%s\" fill=\"%s\" %s/>" % (right_top, "#6190ea", edge),
             letter % (cx - rx * .5, y, 15, "N"), letter % (cx + rx * .5, y, 15, "S")]
    else:
        # split at half the thickness, as the magnet is: the upper half N
        # (top face and the band of side under it), the lower half S. Only
        # the top face N read as a painted face, not as a magnetised half
        middle = y + h / 2.0
        side = ("M%g,%g L%g,%g A%g,%g 0 0 0 %g,%g L%g,%g Z"
                % (cx - rx, y, cx - rx, bottom, rx, ry, cx + rx, bottom, cx + rx, y))
        band_n = ("M%g,%g L%g,%g A%g,%g 0 0 0 %g,%g L%g,%g Z"
                    % (cx - rx, y, cx - rx, middle, rx, ry, cx + rx, middle, cx + rx, y))
        r = ["<path d=\"%s\" fill=\"%s\" %s/>" % (side, BLUE, edge),
             "<path d=\"%s\" fill=\"%s\" %s/>" % (band_n, RED, edge),
             "<ellipse cx=\"%g\" cy=\"%g\" rx=\"%g\" ry=\"%g\" fill=\"#ea6a61\" %s/>"
             % (cx, y, rx, ry, edge),
             letter % (cx, y, 15, "N"), letter % (cx, bottom + ry * .45, 11, "S")]
    return r


def _arrow(x1, y1, x2, y2, colour="currentColor"):
    """The field, from S to N."""
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - 9 * math.cos(a - .45), y2 - 9 * math.sin(a - .45))
    p2 = (x2 - 9 * math.cos(a + .45), y2 - 9 * math.sin(a + .45))
    return ("<line x1=\"%g\" y1=\"%g\" x2=\"%g\" y2=\"%g\" stroke=\"%s\" stroke-width=\"2\"/>"
            "<path d=\"M%g,%g L%g,%g L%g,%g Z\" fill=\"%s\"/>"
            % (x1, y1, x2, y2, colour, x2, y2, p1[0], p1[1], p2[0], p2[1], colour))


def _mark(cx, cy, right):
    """A tick in a green disc, or a cross in a red one."""
    if right:
        stroke = "M%g,%g l5,5 l9,-10" % (cx - 7, cy)
        colour = GREEN
    else:
        stroke = "M%g,%g l12,12 M%g,%g l-12,12" % (cx - 6, cy - 6, cx + 6, cy - 6)
        colour = WRONG
    return ("<circle cx=\"%g\" cy=\"%g\" r=\"13\" fill=\"%s\"/>"
            "<path d=\"%s\" stroke=\"#fff\" stroke-width=\"2.6\" fill=\"none\" "
            "stroke-linecap=\"round\" stroke-linejoin=\"round\"/>" % (cx, cy, colour, stroke))


def magnet():
    """The magnet to buy, on the left, and the one that looks the same and
    must not be bought, on the right: magnetised across the diameter, or
    through the thickness. The AS5600 reads the direction of a field that
    lies in the plane of the magnet and turns with it; the axial one has its
    field along the axis, and turning it changes nothing the chip can see."""
    # thicker than the real Ø8 x 1, so that the halves of the axial one
    # can be seen
    rx, ry, h = 46, 16, 26
    r = ["<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 320 150\" width=\"320\" "
         "height=\"150\" role=\"img\" color=\"#6b7178\">"]
    # left: diametral, the field across the top face
    r += _cylinder(90, 52, rx, ry, h, True)
    r.append(_arrow(118, 28, 62, 28))
    r.append(_mark(90, 126, True))
    # right: axial, the field up through the thickness
    r += _cylinder(230, 52, rx, ry, h, False)
    r.append(_arrow(292, 94, 292, 34))
    r.append(_mark(230, 126, False))
    r.append("</svg>")
    return "\n".join(r)


def motor_wires():
    """The motor's four wires in the J1 plug, with their colours on the
    connector, for chapter 7 step 1. Taken
    from wiring.py - the same list the wiring booklet is drawn from - so the
    order and the colours cannot differ from the board: each phase, its
    colour, and the hole of J1 it lands on, labelled as PRINTED on the
    perfboard (drawing_common.hole_label). No words, only marks that read the
    same in every language: J1, A+ A- B+ B-, the hole labels."""
    import wiring
    from drawing_common import hole_label
    phases = sorted(((to, net) for _frm, to, net, *_w in wiring.WIRES
                     if net.startswith("fase")), key=lambda t: t[0][1])
    if len(phases) != 4:
        raise SystemExit("illustrations: wiring.py has %d motor phases, not 4" % len(phases))
    pitch, x0 = 56, 76
    r = ["<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 320 150\" width=\"320\" "
         "height=\"150\" role=\"img\" font-family=\"system-ui,sans-serif\">"]
    # the plug's housing, seen from the side the wires come out of
    left, right = x0 - 26, x0 + 3*pitch + 26
    r.append("<rect x=\"%d\" y=\"14\" width=\"%d\" height=\"30\" rx=\"4\" fill=\"#f4f1e8\" "
             "stroke=\"#6b7178\" stroke-width=\"1.5\"/>" % (left, right - left))
    r.append("<text x=\"%d\" y=\"34\" font-size=\"13\" font-weight=\"700\" fill=\"#333\" "
             "text-anchor=\"end\">J1</text>" % (left - 8))
    for i, ((col, row), net) in enumerate(phases):
        x = x0 + i*pitch
        colour = wiring.COLOURS[net][0]
        r.append("<rect x=\"%d\" y=\"20\" width=\"18\" height=\"18\" rx=\"2\" fill=\"#d9d4c7\"/>" % (x - 9))
        r.append("<path d=\"M%d,38 C%d,70 %d,70 %d,96\" stroke=\"%s\" stroke-width=\"7\" "
                 "fill=\"none\" stroke-linecap=\"round\"/>" % (x, x, x, x, colour))
        r.append("<text x=\"%d\" y=\"116\" font-size=\"14\" font-weight=\"700\" fill=\"#222\" "
                 "text-anchor=\"middle\">%s</text>" % (x, net[4:].replace("-", "\u2212")))
        r.append("<text x=\"%d\" y=\"136\" font-size=\"12\" fill=\"#6b7178\" "
                 "text-anchor=\"middle\">%s</text>" % (x, hole_label(col, row)))
    # the two pairs, which must stay side by side
    for k, (a, b) in enumerate(((0, 1), (2, 3))):
        xa, xb = x0 + a*pitch, x0 + b*pitch
        r.append("<path d=\"M%d,8 L%d,4 L%d,4 L%d,8\" stroke=\"#6b7178\" fill=\"none\"/>" % (xa, xa, xb, xb))
    r.append("</svg>")
    return "\n".join(r)


DRAWINGS = {"magnet-magnetisation.svg": magnet, "motor-wires.svg": motor_wires}
