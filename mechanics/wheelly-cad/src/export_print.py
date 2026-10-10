# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The printed parts as they go on the bed, for whoever downloads the STLs.

The STEPs in out/ are in the assembly frame: a part floats at the height it
has on the machine, and the clutch hub has its collar on top, upside down
for printing. Whoever opens them in a slicer has to rebuild fourteen
orientations from the text. Here each part is turned so that its bed face
(BED_FACE in bom_mechanics.py) lies on z = 0, centred on the origin and
turned on the bed to the smallest square it fits (as bed.py does for the
box).

NOT PART OF build.py, on purpose: it runs only when the files are wanted
(a release, a model page), and reads the STEPs the last build left in out/.
Run the build first if the model has changed.

    ./.venv/bin/python src/export_print.py [--out DIR]

DIR defaults to ~/Documents/wheelly/print; each run writes a new folder
named with date and time inside it and never overwrites.

What comes out:
  <part>_<material>_x<qty>.stl   each part alone, on its bed face
  coprint/<part>__<body>.stl      the bodies of a two-material print, in
                                   register: load them together in the
                                   slicer as parts of one object
  README.txt                       what each file is and how it lies

THE CHECK, measured on the turned solid and not on the table: the flat faces
at z = 0 must add up to the whole of the face that was chosen, and nothing
may go below the bed. A normal that points at no flat face, or a turn that
puts the part on the wrong side, stops the export.
"""
import argparse
import datetime
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
import bom_mechanics as B

OUT = B.OUT
# Fine enough to print from: 0.01 mm of chord leaves a Ø5 bearing seat
# round to well under a layer's width. The preview STLs in out/stl use 0.3,
# which is right for looking at and wrong for printing.
TOLERANCE, ANGLE = 0.01, 0.1
FLAT = 1e-3          # mm: how close to z = 0 a face must be to count as on the bed


def load(name):
    return cq.importers.importStep(OUT + name + ".step").val()


def bed_face(solid, wanted):
    """The outermost flat face whose outward normal is closest to `wanted`,
    with the total area lying in that plane."""
    w = cq.Vector(*wanted).normalized()
    best = None
    for f in solid.Faces():
        if f.geomType() != "PLANE":
            continue
        n = f.normalAt()
        if n.dot(w) < 0.99:
            continue
        d = f.Center().dot(n)
        if best is None or d > best[1] + FLAT:
            best = (n, d, f.Area())
        elif abs(d - best[1]) <= FLAT:
            best = (best[0], best[1], best[2] + f.Area())
    return best


def turn_to_bed(shape, n):
    """Rotate so that the outward normal n points down (-z)."""
    down = cq.Vector(0, 0, -1)
    axis = n.cross(down)
    c = max(-1.0, min(1.0, n.dot(down)))
    if axis.Length < 1e-9:
        if c > 0:
            return shape
        return shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
    return shape.rotate(cq.Vector(0, 0, 0), axis.normalized(), math.degrees(math.acos(c)))


def smallest_square_turn(shape):
    """Turn about z, in whole degrees, that fits the footprint in the
    smallest square."""
    pts = [(v.x, v.y) for v in shape.tessellate(0.1)[0]]
    best = None
    for deg in range(90):
        a = math.radians(deg)
        u = [math.cos(a)*x + math.sin(a)*y for x, y in pts]
        v = [-math.sin(a)*x + math.cos(a)*y for x, y in pts]
        side = max(max(u) - min(u), max(v) - min(v))
        if best is None or side < best[0] - 1e-6:
            best = (side, deg)
    return best


def place(name, frame_of=None):
    """The part turned onto its bed face, or onto the bed face of
    `frame_of` (for a co-print). Returns (the transform as a function, the
    area expected on the bed)."""
    ref = load(frame_of or name)
    face = bed_face(ref, B.BED_FACE[frame_of or name])
    if face is None:
        raise SystemExit("%s: BED_FACE %s points at no flat face of the part"
                         % (frame_of or name, B.BED_FACE[frame_of or name]))
    n, _d, area = face
    turned = turn_to_bed(ref, n)
    side, deg = smallest_square_turn(turned)
    turned = turned.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -deg)
    bb = turned.BoundingBox()
    shift = cq.Vector(-(bb.xmin + bb.xmax)/2, -(bb.ymin + bb.ymax)/2, -bb.zmin)

    def move(s):
        s = turn_to_bed(s, n).rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -deg)
        return s.translate(shift)
    return move, area, side, deg


def on_bed_area(s):
    a = 0.0
    for f in s.Faces():
        if f.geomType() == "PLANE" and abs(f.normalAt().z + 1) < 1e-6 \
                and abs(f.Center().z) < FLAT:
            a += f.Area()
    return a


def extent(s):
    """The true extent from the vertices of a fine tessellation: OCC's
    bounding box is padded by a millimetre or two, and the README gives the
    size to fit a bed."""
    pts = s.tessellate(0.05)[0]
    lo = [min(getattr(p, a) for p in pts) for a in "xyz"]
    hi = [max(getattr(p, a) for p in pts) for a in "xyz"]
    return lo, [h - l for h, l in zip(hi, lo)]


def check(name, s, expected):
    bb = s.BoundingBox()
    if bb.zmin < -FLAT:
        raise SystemExit("%s goes %.3f mm below the bed" % (name, -bb.zmin))
    got = on_bed_area(s)
    if abs(got - expected) > max(0.5, 0.005*expected):
        raise SystemExit("%s: %.1f mm2 on the bed, the chosen face is %.1f mm2 -"
                         " the part is not lying on it" % (name, got, expected))
    return got, bb


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.expanduser("~/Documents/wheelly/print"))
    args = ap.parse_args()

    names = [p[0] for p in B.PRINTED]
    if set(names) != set(B.BED_FACE):
        raise SystemExit("PRINTED and BED_FACE do not name the same parts:\n"
                         "  without a bed face: %s\n  bed face of no part: %s"
                         % (sorted(set(names) - set(B.BED_FACE)),
                            sorted(set(B.BED_FACE) - set(names))))
    for f in [OUT + n + ".step" for n in names]:
        if not os.path.exists(f):
            raise SystemExit("missing %s: run the build first" % f)

    dest = os.path.join(args.out, datetime.datetime.now().strftime("%Y-%m-%d_%H%M"))
    os.makedirs(os.path.join(dest, "coprint"), exist_ok=False)
    rows = []
    for name, mat, _dens, q, _orientation in B.PRINTED:
        move, area, side, deg = place(name)
        s = move(load(name))
        got, _bb = check(name, s, area)
        _lo, size = extent(s)
        # the turn found must be the turn applied: the square is measured
        # again on the part as it will be written
        if max(size[0], size[1]) > side + 0.2:
            raise SystemExit("%s: turned to fit a %.1f square, it takes %.1f x %.1f"
                             % (name, side, size[0], size[1]))
        matname = "TPU" if "TPU" in mat else mat
        fn = "%s_%s_x%d.stl" % (name, matname, q)
        cq.exporters.export(s, os.path.join(dest, fn),
                            tolerance=TOLERANCE, angularTolerance=ANGLE)
        rows.append("%-34s %-12s x%d  %5.1f x %5.1f x %5.1f mm tall, %5.0f mm2 on the bed"
                    % (fn, mat, q, size[0], size[1], size[2], got))
        print("  " + rows[-1][:110])

    co = []
    for base, bodies in B.COPRINTED.items():
        move, area, _side, _deg = place(base)
        sb = move(load(base))
        check(base, sb, area)
        cq.exporters.export(sb, os.path.join(dest, "coprint", "%s__%s_ASA.stl" % (base, base)),
                            tolerance=TOLERANCE, angularTolerance=ANGLE)
        for b in bodies:
            st = move(load(b))
            if st.BoundingBox().zmin < -FLAT:
                raise SystemExit("co-print %s: %s goes below the bed" % (base, b))
            clash = sb.intersect(st).Volume()
            if clash > 1e-3:
                raise SystemExit("co-print %s: %s overlaps it by %.3f mm3" % (base, b, clash))
            cq.exporters.export(st, os.path.join(dest, "coprint", "%s__%s_TPU.stl" % (base, b)),
                                tolerance=TOLERANCE, angularTolerance=ANGLE)
        co.append("%s + %s" % (base, ", ".join(bodies)))
        print("  co-print " + co[-1])

    with open(os.path.join(dest, "README.txt"), "w") as f:
        f.write("Wheelly - printed parts, each on its bed face, centred, turned to the\n"
                "smallest square. Generated by src/export_print.py from the STEPs of\n"
                "the last build.\n\n")
        f.write("\n".join(rows) + "\n\n")
        f.write("coprint/: the bodies of each two-material print in register. Load the\n"
                "files of one group together and let the slicer treat them as parts of\n"
                "one object; assign ASA and TPU.\n  " + "\n  ".join(co) + "\n")
    print("written to " + dest)


if __name__ == "__main__":
    main()
