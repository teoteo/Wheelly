# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The booklet to print: layout and diagrams on five A4 pages.

It serves whoever has the soldering iron in hand, so it is not a design
drawing but a layout of pages: five pages, the board layout first and the
diagrams after it. The drawings are not redrawn - the same SVGs that come out
of the build are taken, cropped by section - so the booklet cannot tell a
different story from the model.

How: each page is built as a real A4 SVG, in millimetres, holding the scaled
drawings and their title; Inkscape renders it at 300 dpi and the pages are
joined into a PDF. Inkscape is needed because the environment has no PDF
library, and it is also the way to keep the texts vector almost to the end.
If it is missing, the program says so instead of producing a mute PDF.

The file comes out in ~/Documents with date and time in its name, and the
folder is a parameter: nothing is ever overwritten.
"""
import datetime
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(os.path.dirname(os.path.dirname(HERE)), "pcb")
OUTPUT_FOLDER = os.path.expanduser("~/Documents")
INKSCAPE = "/Applications/Inkscape.app/Contents/MacOS/inkscape"

A4_W, A4_H = 210.0, 297.0
MARGIN, DPI = 13.0, 300

# every drawing and the booklet come in two languages, _en and _it: the
# language being printed is WHEELLY_LINGUA
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawing_common import tr, with_language, sections_of, LANGUAGES


def layout():
    return os.path.join(PCB, with_language("disposizione-basetta", "svg"))


def sch(name):
    return os.path.join(SCH, with_language(name, "svg"))


SCH = os.path.join(PCB, "schemi")

# Each page: title, and the blocks to stack. Each block is an SVG with the
# window to crop from it (x, y, width, height) in its own units.
#
# The windows are NOT written by hand: the heights at which the sections start
# are published by drawing_board_layout.py in a file next to the drawing.
# Written here - they were 900 and 1443 - adding a section to the drawing was
# enough for the booklet to cut in the wrong place, and nobody would have
# noticed until looking at the printed PDF.
import json


def sections():
    p = sections_of(layout())
    if not os.path.exists(p):
        raise SystemExit("%s is missing: regenerate the board drawing first" % p)
    return json.load(open(p, encoding="utf-8"))


def pages():
    z = sections()
    width = z["largo"]
    return [
        (tr("pdf.p1"),
         [(layout(), (0, 40, width, z["vista_fili"] - 40))]),
        # The view from below sits next to the one from above, on the same
        # page, because soldering you go from one to the
        # other, and turning the page to compare them is the moment you get
        # the hole wrong.
        (tr("pdf.p2"),
         [(layout(), (0, z["vista_fili"], width, z["stella"] - z["vista_fili"])),
          (layout(), (0, z["vista_sotto"], width, z["fondo"] - z["vista_sotto"]))]),
        (tr("pdf.p3"),
         [(layout(), (0, z["stella"], width, z["vista_sotto"] - z["stella"]))]),
        (tr("pdf.p4"),
         [(sch("collegamenti-xiao-tmc2209"), None),
          (sch("collegamenti-xiao-as5600-led"), None)]),
        (tr("pdf.p5"),
         [(sch("collegamenti-potenza-motore"), None)]),
    ]


def read_svg(path):
    """Content and size of an SVG: the shell is removed, the drawing remains."""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    vb = re.search(r'viewBox="([-0-9.]+) ([-0-9.]+) ([0-9.]+) ([0-9.]+)"', s)
    x0, y0, w, h = (float(v) for v in vb.groups())
    body = s[s.index(">", s.index("<svg")) + 1:s.rindex("</svg>")]
    return body, (x0, y0, w, h)


def page(page_title, blocks, n, tot, date_str):
    width = A4_W - 2*MARGIN
    pieces, total_height = [], 0.0
    for path, window in blocks:
        body, vb = read_svg(path)
        x0, y0, w, h = window if window else vb
        k = width / w
        pieces.append((body, x0, y0, k, h*k))
        total_height += h*k
    available = A4_H - MARGIN - 30.0
    gap = 4.0
    total_height += gap*(len(pieces) - 1)
    if total_height > available:                 # if it does not fit, everything shrinks
        r = available/total_height
        pieces = [(c, x, y, k*r, a*r) for c, x, y, k, a in pieces]
    el = ['<rect width="%.1f" height="%.1f" fill="#FFFFFF"/>' % (A4_W, A4_H),
          '<text x="%.1f" y="%.1f" style="font-size:5.2px;font-weight:600;'
          'font-family:Helvetica,Arial,sans-serif;fill:#2A2A28">%s</text>'
          % (MARGIN, MARGIN + 4, page_title),
          '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#B0AEA6" '
          'stroke-width="0.3"/>' % (MARGIN, MARGIN + 7, A4_W - MARGIN, MARGIN + 7)]
    # Each block must be CLIPPED to its window, not just translated: without
    # the clip the whole drawing stays visible and the first page carries
    # along the start of the second, which ends up over the footer.
    y = MARGIN + 13.0
    for i, (body, x0, y0, k, height) in enumerate(pieces):
        el.append('<clipPath id="ritaglio%d"><rect x="%.3f" y="%.3f" width="%.3f" '
                  'height="%.3f"/></clipPath>' % (i, MARGIN, y, width, height))
        el.append('<g clip-path="url(#ritaglio%d)">'
                  '<g transform="translate(%.3f,%.3f) scale(%.5f) translate(%.2f,%.2f)">%s</g></g>'
                  % (i, MARGIN, y, k, -x0, -y0, body))
        y += height + gap
    el.append('<text x="%.1f" y="%.1f" style="font-size:3px;font-family:Helvetica,'
              'Arial,sans-serif;fill:#7A786F">%s</text>'
              % (MARGIN, A4_H - 6, tr("pdf.footer", date=date_str, n=n, tot=tot)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%.0fmm" height="%.0fmm" viewBox="0 0 %.0f %.0f">%s</svg>'
            % (A4_W, A4_H, A4_W, A4_H, "\n".join(el)))


def main():
    # --dal-build: the build calls it at every regeneration of the diagrams.
    # There a missing Inkscape must not bring down the whole build - the
    # booklet is an extra, not a part - but it must SAY so, or it vanishes
    # silently.
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    optional = "--dal-build" in sys.argv
    folder = args[0] if args else OUTPUT_FOLDER
    if not os.path.exists(INKSCAPE):
        warning = "Inkscape is needed to render the pages: not found at " + INKSCAPE
        if optional:
            print("  WARNING: " + warning + " - the booklet does not come out")
            return
        raise SystemExit(warning)
    try:
        from PIL import Image
    except ImportError:
        if optional:
            print("  WARNING: PIL is missing, the booklet does not come out")
            return
        raise
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.datetime.now()
    tmp = os.path.join("/tmp", "wheelly_pagine_%s" % stamp.strftime("%H%M%S"))
    os.makedirs(tmp, exist_ok=True)
    for language_ in LANGUAGES:
        os.environ["WHEELLY_LINGUA"] = language_
        images = []
        PAGES = pages()
        for i, (page_title, blocks) in enumerate(PAGES, 1):
            p_svg = os.path.join(tmp, "p%s%d.svg" % (language_, i))
            p_png = os.path.join(tmp, "p%s%d.png" % (language_, i))
            open(p_svg, "w", encoding="utf-8").write(
                page(page_title, blocks, i, len(PAGES), stamp.strftime("%d/%m/%Y")))
            r = subprocess.run([INKSCAPE, p_svg, "--export-type=png",
                                "--export-filename=" + p_png, "--export-dpi=%d" % DPI],
                               capture_output=True, text=True)
            if not os.path.exists(p_png):
                raise SystemExit("Inkscape did not render page %d: %s" % (i, r.stderr[-400:]))
            images.append(Image.open(p_png).convert("RGB"))
            print("  page %d: %s" % (i, page_title))
        # The dated copy in ~/Documents only when run by hand. Written from
        # the build it piled up - one pair per build, 58 files within days -
        # while the booklet needed is the one in pcb/, always the latest.
        # Whoever wants a dated copy runs this script by hand.
        if not optional:
            output = os.path.join(folder, "%s_%s.pdf" % (with_language("wheelly-schemi-montaggio", "pdf", language_)[:-4], stamp.strftime("%Y%m%d-%H%M%S")))
            images[0].save(output, save_all=True, append_images=images[1:],
                             resolution=DPI, title=tr("pdf.title"))
            print(output)
        # And a copy next to the diagrams, with a FIXED name: there the booklet
        # must always be the latest, and with a name that changes every time the
        # folder would fill with copies without git knowing which to version.
        # git keeps the history; the one with date and time stays in
        # ~/Documents.
        fixed = os.path.join(PCB, with_language("wheelly-schemi-montaggio", "pdf"))
        images[0].save(fixed, save_all=True, append_images=images[1:],
                         resolution=DPI, title=tr("pdf.title"))
        print(fixed)
    # The pages are intermediate files: left behind, they piled up in /tmp,
    # one folder per build (over a thousand of them).
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
