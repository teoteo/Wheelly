# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Conversion of the generated DXF files to SVG, with the selected dimension drawn on top."""
import math, os, re
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration, ColorPolicy

import ui_dimensions

# The DXF files are monochrome technical drawings. We render them in black on
# a transparent background: the page puts the background, and in the dark
# theme inverting is enough.
_CONFIG = Configuration(color_policy=ColorPolicy.CUSTOM,
                        custom_fg_color="#000000",
                        background_policy=BackgroundPolicy.OFF)

# The assembly views tell the parts apart by colour - solid, reference,
# accessory with the pale fill - so they must be rendered as they are, not
# squashed into monochrome.
_CONFIG_COLOUR = Configuration(color_policy=ColorPolicy.COLOR,
                               background_policy=BackgroundPolicy.OFF)

COLOUR_DRAWINGS = ("assembly_plan", "assembly_section", "assembly_details")


def _config(dxf_path):
    name = os.path.splitext(os.path.basename(dxf_path))[0]
    return _CONFIG_COLOUR if name in COLOUR_DRAWINGS else _CONFIG

MARGIN = 2.0            # mm around the content, as in the page
# The colour of the dimension says where the number comes from, with the same
# scale as the marks in the list: orange changes freely, blue is measured on
# the part and changes only by measuring again, violet is a result, green a
# catalogue figure. Hues chosen to hold on a light background as well as on a
# dark one.
COLOURS = {"S": "#d2601a", "M": "#1f7a8c", "D": "#7a6ea8", "R": "#5f7a3f"}
UNKNOWN_COLOUR = "#8a8178"


def _sizes(diagonal):
    """The dimension's line work, in proportion to the size of the drawing.

    Fixed sizes in millimetres do not hold: the arm plan is 213 x 172, the
    clutch section 110 x 10. A 3.4 mm label on the first is discreet, on the
    second it covers the part.
    """
    text = min(max(diagonal * 0.022, 1.2), 5.0)
    return {"text": text,
            "tick": text * 0.5,
            "offset": text * 0.9,
            "highlight": min(max(diagonal * 0.0035, 0.12), 0.8),
            "dim": min(max(diagonal * 0.0018, 0.06), 0.4)}


def _render(dxf_path):
    """SVG of the drawing, plus the transform from DXF coordinates to SVG ones."""
    doc = ezdxf.readfile(dxf_path)
    backend = svg.SVGBackend()
    Frontend(RenderContext(doc), backend, config=_config(dxf_path)).draw_layout(
        doc.modelspace(), finalize=True)
    bbox = backend.player().bbox()
    page = layout.Page(0, 0, layout.Units.mm, layout.Margins.all(MARGIN))
    text = backend.get_string(page)

    view_box = re.search(r'viewBox="([^"]*)"', text)
    if not view_box or not bbox.has_data:
        return text, None
    width = float(view_box.group(1).split()[2])
    dx = bbox.extmax.x - bbox.extmin.x
    dy = bbox.extmax.y - bbox.extmin.y
    if dx <= 0:
        return text, None
    scale = width / (dx + 2 * MARGIN)
    x0, ymax = bbox.extmin.x, bbox.extmax.y

    def point(x, y):
        return ((x - x0 + MARGIN) * scale, (ymax - y + MARGIN) * scale)

    return text, (point, scale, _sizes(math.hypot(dx, dy)), bbox)


def to_svg(dxf_path, dim=None):
    """The drawing; if `dim` is given, with that dimension traced on top.

    `dim` is a dictionary {nome, valore, unita} (name, value, unit): the
    drawing is searched for the geometries worth that number and they are
    annotated.
    """
    text, transform = _render(dxf_path)
    if dim is None or transform is None:
        return text
    found = ui_dimensions.matches(dim["valore"],
                                  ui_dimensions.features(dxf_path),
                                  name=dim.get("nome"))
    if not found:
        return text
    # how many of these really are the parameter, and not an equal number by
    # chance: it is the difference between pointing at a spot and guessing it
    _signed = ui_dimensions.signed(found, dim.get("nome"))
    if not _signed and len(found) > ui_dimensions.TOO_MANY:
        # too many to mean anything: nothing is drawn and the page is left to
        # say so. The group is there all the same, empty, because that is
        # where the page reads the number. (The class and the data-*
        # attributes are read by the page's script: they stay.)
        return text.replace("</svg>", '<g class="quota" data-riscontri="%d" '
                            'data-firmati="0" data-troppi="1" data-tipo="%s"></g>'
                            % (len(found), found[0][0]) + "</svg>")
    fragment = _annotate(found[:ui_dimensions.MAX_SHOWN], dim, *transform,
                         total=len(found), signed=_signed)
    return text.replace("</svg>", fragment + "</svg>")


# --------------------------------------------------------------------------
# The dimension's line work
# --------------------------------------------------------------------------

def _annotate(found, dim, point, scale, m, bbox, total=0, signed=0):
    """The SVG group with highlighting and dimension lines.

    The "quota" class is for the style sheet: in the dark theme the page
    inverts the whole drawing, and a second invert on this group gives it its
    colour back.
    """
    mm = lambda v: v * scale                       # from millimetres to SVG units
    TICK, OFFSET, TEXT = m["tick"], m["offset"], m["text"]
    WIDTH_HIGHLIGHT, WIDTH_DIM = m["highlight"], m["dim"]
    COLOUR = COLOURS.get(dim.get("origine"), UNKNOWN_COLOUR)
    parts = []
    extremes = []            # to tell the page where to frame
    # When the matches are more than one and NONE carries the parameter's
    # signature, the editor does not know which is its own: they are places
    # worth the same number. Before, only one was labelled - the first that
    # came - and whoever looked read that one as the answer. Now all of them
    # are labelled, numbered, so the uncertainty shows instead of being
    # hidden.
    # Not verified: NO match carries the parameter's signature, so what is
    # about to be highlighted is only worth the same number. Before, the
    # condition also asked for total > 1, and so the worst case stayed silent:
    # a single match, unsigned, was drawn and labelled like all the others:
    # whoever looked read "it is this one" and went to measure it with the
    # calipers. It happened on D_boss_panel, which in assembly_plan was
    # signed nowhere. Doubtful shows: dashed instead of a
    # solid line, and a question mark in front of the name.
    doubtful = signed == 0

    def mark(px, py):
        extremes.append((px, py))
        return px, py

    def line(p0, p1, wide, dashed=""):
        a, b = mark(*point(*p0)), mark(*point(*p1))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="%s" stroke-width="%.1f" stroke-linecap="round"%s/>'
                     % (a[0], a[1], b[0], b[1], COLOUR, mm(wide),
                        ' stroke-dasharray="%.1f %.1f"' % (mm(1.2), mm(1.2))
                        if dashed else ""))

    def circle(cx, cy, r):
        c = point(cx, cy)
        mark(c[0] - mm(r), c[1] - mm(r)); mark(c[0] + mm(r), c[1] + mm(r))
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" '
                     'stroke="%s" stroke-width="%.1f"%s/>'
                     % (c[0], c[1], mm(r), COLOUR, mm(WIDTH_HIGHLIGHT),
                        ' stroke-dasharray="%.1f %.1f"' % (mm(1.6), mm(1.2))
                        if doubtful else ""))

    def ticks(p0, p1):
        """Two oblique strokes at the ends, as on a dimensioned drawing."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        ox, oy = (ux + uy) * TICK / 2, (uy - ux) * TICK / 2
        for p in (p0, p1):
            line((p[0] - ox, p[1] - oy), (p[0] + ox, p[1] + oy), WIDTH_DIM)

    def dim_line(p0, p1):
        line(p0, p1, WIDTH_DIM)
        ticks(p0, p1)

    def label(x, y, text):
        wide_mm = TEXT * 0.56 * len(text) + TEXT * 0.7
        tall_mm = TEXT * 1.65
        x = min(max(x, bbox.extmin.x + wide_mm / 2), bbox.extmax.x - wide_mm / 2)
        y = min(max(y, bbox.extmin.y + tall_mm / 2), bbox.extmax.y - tall_mm / 2)
        px, py = point(x, y)
        wide, tall = mm(wide_mm), mm(tall_mm)
        mark(px - wide / 2, py - tall / 2); mark(px + wide / 2, py + tall / 2)
        parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" '
                     'fill="%s"/>' % (px - wide / 2, py - tall / 2, wide, tall,
                                      mm(TEXT * 0.25), COLOUR))
        parts.append('<text x="%.1f" y="%.1f" fill="#ffffff" font-size="%.1f" '
                     'font-family="ui-monospace, SFMono-Regular, Menlo, monospace" '
                     'text-anchor="middle" dominant-baseline="central">%s</text>'
                     % (px, py, mm(TEXT), text))

    def outward(x, y):
        """Moves the label away from the origin, where there is less drawing."""
        d = math.hypot(x, y) or 1.0
        return x + x / d * OFFSET * 1.6, y + y / d * OFFSET * 1.6

    def _text(index):
        # the question mark says, on the drawing, what the line below the
        # page says in words: this is a place worth that number, not
        # necessarily the place of that parameter
        return (("? " if doubtful else "") + _caption(dim)
                + ("  %d di %d" % (index + 1, total) if doubtful and total > 1 else ""))

    for index, (kind, item) in enumerate(found):
        first = index == 0 or doubtful
        if kind in ("diametro", "raggio"):
            cx, cy, r = item[0], item[1], item[2]
            circle(cx, cy, r)
            if kind == "diametro":
                dim_line((cx - r, cy), (cx + r, cy))
            else:
                dim_line((cx, cy), (cx + r, cy))
            if first:
                label(*outward(cx, cy + r + OFFSET), text=_text(index))

        elif kind == "interasse":
            a, b = item
            circle(a[0], a[1], a[2]); circle(b[0], b[1], b[2])
            dim_line((a[0], a[1]), (b[0], b[1]))
            if first:
                label((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + OFFSET, _text(index))

        elif kind == "lunghezza":
            x1, y1, x2, y2 = item
            line((x1, y1), (x2, y2), WIDTH_HIGHLIGHT, dashed=doubtful)
            nx, ny = _normal(x1, y1, x2, y2)
            q0 = (x1 + nx * OFFSET, y1 + ny * OFFSET)
            q1 = (x2 + nx * OFFSET, y2 + ny * OFFSET)
            line((x1, y1), q0, WIDTH_DIM, dashed=True)
            line((x2, y2), q1, WIDTH_DIM, dashed=True)
            dim_line(q0, q1)
            if first:
                label((q0[0] + q1[0]) / 2 + nx * OFFSET,
                      (q0[1] + q1[1]) / 2 + ny * OFFSET, _text(index))

        elif kind == "spessore":
            # Only the stretch where the two lines FACE EACH OTHER is
            # highlighted. One of the two may be the centre line, as long as
            # the whole drawing: underlining it all to say where a two
            # millimetre dimension is, is like pointing at the street instead
            # of the house, and the automatic framing ended up showing the
            # whole sheet.
            a, b = _facing(*item)
            line((a[0], a[1]), (a[2], a[3]), WIDTH_HIGHLIGHT, dashed=doubtful)
            line((b[0], b[1]), (b[2], b[3]), WIDTH_HIGHLIGHT, dashed=doubtful)
            mx, my = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
            nx, ny = _normal(a[0], a[1], a[2], a[3])
            d = ((b[0] - a[0]) * (a[3] - a[1]) - (b[1] - a[1]) * (a[2] - a[0]))
            sense = 1.0 if d < 0 else -1.0
            dim_line((mx, my), (mx + nx * dim["valore"] * sense,
                                my + ny * dim["valore"] * sense))
            if first:
                label(mx + nx * (dim["valore"] * sense + OFFSET * sense),
                      my + ny * (dim["valore"] * sense + OFFSET * sense),
                      _text(index))

        else:                                       # distance, abscissa, ordinate
            cx, cy, r = item[0], item[1], item[2]
            circle(cx, cy, r)
            from_ = (0.0, 0.0) if kind == "distanza" else (
                     (0.0, cy) if kind == "ascissa" else (cx, 0.0))
            dim_line(from_, (cx, cy))
            if first:
                label((from_[0] + cx) / 2, (from_[1] + cy) / 2 + OFFSET, _text(index))

    if not extremes:
        return '<g class="quota">%s</g>' % "".join(parts)
    xs = [q[0] for q in extremes]; ys = [q[1] for q in extremes]
    return ('<g class="quota" data-riquadro="%.1f %.1f %.1f %.1f" '
            'data-riscontri="%d" data-firmati="%d" data-tipo="%s">%s</g>'
            % (min(xs), min(ys), max(max(xs) - min(xs), 1.0),
               max(max(ys) - min(ys), 1.0), total, signed, found[0][0],
               "".join(parts)))


def _facing(a, b):
    """The two stretches where the parallel segments really face each other.

    Each is cut on the projection of the other; if they face each other for a
    negligible stretch they are left whole, because a fragment of a tenth
    would not show.
    """
    def trim(s_, t_):
        dx, dy = s_[2] - s_[0], s_[3] - s_[1]
        ls = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ls, dy / ls
        p = sorted(((t_[0] - s_[0]) * ux + (t_[1] - s_[1]) * uy,
                    (t_[2] - s_[0]) * ux + (t_[3] - s_[1]) * uy))
        t0 = min(max(p[0], 0.0), ls)
        t1 = min(max(p[1], 0.0), ls)
        if t1 - t0 < 0.2:
            return s_
        return (s_[0] + ux * t0, s_[1] + uy * t0,
                s_[0] + ux * t1, s_[1] + uy * t1) + tuple(s_[4:])

    return trim(a, b), trim(b, a)


def _normal(x1, y1, x2, y2):
    """Unit vector perpendicular to the segment, pointing away from the origin."""
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if nx * mx + ny * my < 0:
        nx, ny = -nx, -ny
    return nx, ny


def _caption(dim):
    """Only the number: the parameter's name is already in the row being edited."""
    unit = {"mm": " mm", "deg": "°"}.get(dim["unita"], "")
    return "%.2f%s" % (dim["valore"], unit)


# --------------------------------------------------------------------------
# Which drawing a parameter is illustrated by
# --------------------------------------------------------------------------
#
# The "drawings" field of parameters.py is prose, not a closed list: next to
# "arm_plan" there are entries like "clutch STEP" or "documentation". Here we
# translate it into the DXF files that really exist, in order of specificity.

ALIAS = [
    ("collar_plan",      "collar_plan"),
    ("collar_section",     "collar_section"),
    ("arm_plan",      "arm_plan"),
    ("clutch_section",    "clutch_section"),
    ("flat_gasket",   "flat_gasket"),
    ("sviluppo_guarnizione", "flat_gasket"),
    ("sensor_bracket",      "sensor_bracket"),
    ("magnet_cap",   "magnet_cap"),
    ("dima_magnete",        "magnet_cap"),
    ("filter_wheel_body",   "body_dimensioned"),
    ("body_dimensioned",       "body_dimensioned"),
    # the prose around the file names is English (not "frizione"); the
    # Italian of the label lives in texts_parameters_it.py and
    # is only shown, never matched here
    ("clutch",              "clutch_section"),
    ("arm",             "arm_plan"),
    ("collar",             "collar_plan"),
]

ALL = ["body_dimensioned", "collar_plan", "collar_section", "arm_plan",
       "clutch_section", "flat_gasket", "sensor_bracket",
       "magnet_cap"]

# The two assembly views belong to no part: they hold for all the parameters,
# and stay always available next to the detail drawing.
ASSEMBLY = ["assembly_plan", "assembly_section"]


def drawings_of(drawings_field):
    """The DXF files the parameter appears in, from the prose field of parameters.py."""
    text = drawings_field.lower()
    # "ALL - axial datum" (was "TUTTI"): only as the head of an entry, since
    # "all" as a bare substring is inside "wall", "small", "install"
    if any(re.match(r"all\b", entry.strip()) for entry in text.split(";")):
        return list(ALL)
    found = []
    for entry in text.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        # The part the entry is about comes first ("collar - arm passage
        # notch" belongs to the collar), and only then the rest of it. Before
        # the English, "collare - ... del braccio" never met the "arm" alias,
        # so the order did not matter; now it would send that row to the arm.
        head = entry.split(" - ")[0]
        for where in (head, entry):
            new = next((drawing for alias_key, drawing in ALIAS
                        if alias_key in where and drawing not in found), None)
            if new:
                found.append(new)
                break
    return found
