#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Proof that a rename did not move the geometry by one micron.

    ./.venv/bin/python src/check_unchanged.py --save   # before the change
    ./.venv/bin/python build.py                        # do the change, rebuild
    ./.venv/bin/python src/check_unchanged.py          # after: must report nothing

This exists for the translation of the project into English, where 378
parameter names and the names of the files in `out/` all change at once. A
rename that is correct changes every name and no number; a rename that is
wrong - one substitution landing inside a longer name, one override in
`parameters_local.py` left behind - changes a number too, and nothing else in
the build would say so. The dimension chains still pass, because they are
computed from the same parameters that moved.

**Nothing here is compared by file name**, and that is the whole point: the
translation is what renames `out/scatola.step` to `out/box.step` in the first
place, so a comparison by name would report sixteen files missing and sixteen
new ones, and prove nothing. (Those two names are written here in full on
purpose, and this paragraph is the one place in the project where the old one
survives: the rename pass walks over every file including this one, and a
docstring that explained the rename by example would have ended up saying that
box.step is called box.step.) What is compared is the CONTENT, as a multiset: the same fifteen
solids must still exist with the same volume and the same bounding box, and the
same drawings with the same geometry, whatever they are called now.

Signatures are rounded, and the rounding is chosen so that it cannot hide a
real change: a solid is compared to 1e-6 mm3 of volume and 1e-9 mm of extent,
which is far below anything a design change can produce and far above the noise
of OCCT rebuilding the same shape twice.

The drawing signature deliberately IGNORES the XDATA. That is where the quote
signature lives - the parameter names attached to each entity - and those names
are expected to change: it is the geometry that must not.
"""
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))

OUT = os.path.join(HERE, "out") + os.sep
REFERENCE = os.path.join(HERE, "out", "unchanged.json")

# The heavy one: 59 MB and about a minute to read. It carries no geometry of
# its own - every body in it is one of the parts compared below, already in its
# assembly position - so it is skipped unless asked for.
ASSEMBLY = "references/full_assembly.step"


def _solid_signature(path):
    """Volume and bounding box of every solid in one STEP file."""
    import cadquery as cq
    shape = cq.importers.importStep(path).val()
    out = []
    for s in shape.Solids():
        b = s.BoundingBox()
        out.append((round(s.Volume(), 6),
                    round(b.xmin, 9), round(b.xmax, 9),
                    round(b.ymin, 9), round(b.ymax, 9),
                    round(b.zmin, 9), round(b.zmax, 9)))
    # sorted: a file holding four identical spacers must not depend on the
    # order OCCT happens to hand them back
    return sorted(out)


def _drawing_signature(path):
    """A digest of every entity in one DXF, geometry only.

    Coordinates are rounded to a nanometre before hashing: two builds of the
    same shape can differ in the last bit of a float, and a digest that reacts
    to the last bit would cry wolf on an unchanged file.
    """
    import ezdxf
    doc = ezdxf.readfile(path)
    rows = []
    for e in doc.modelspace():
        kind = e.dxftype()
        nums = []
        if kind == "LINE":
            nums = list(e.dxf.start) + list(e.dxf.end)
        elif kind == "CIRCLE":
            nums = list(e.dxf.center) + [e.dxf.radius]
        elif kind == "ARC":
            nums = list(e.dxf.center) + [e.dxf.radius,
                                         e.dxf.start_angle, e.dxf.end_angle]
        elif kind == "LWPOLYLINE":
            for p in e.get_points("xyb"):
                nums.extend(p)
        elif kind == "TEXT":
            nums = list(e.dxf.insert) + [e.dxf.height]
        elif kind == "HATCH":
            for p in e.paths:
                for v in getattr(p, "vertices", []):
                    nums.extend(v[:2])
        rows.append("%s|%s|%s" % (kind, e.dxf.layer,
                                  ",".join("%.9f" % float(n) for n in nums)))
    rows.sort()
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def _parameter_values():
    """The parameter values, WITHOUT their names.

    The names are exactly what the translation changes, so comparing them would
    fail by design. What must not change is the set of numbers the model is
    built from - and its size, because a botched substitution that merges two
    names into one would silently drop a parameter.
    """
    import csv
    path = OUT + "drawings/filter_wheel_parameters.csv"
    if not os.path.exists(path):
        # the file is renamed by the translation too
        cands = glob.glob(OUT + "drawings/*.csv")
        if not cands:
            return None
        path = cands[0]
    with open(path, encoding="utf-8") as f:
        vals = [round(float(r["Valore"] if "Valore" in r else r["Value"]), 9)
                for r in csv.DictReader(f)]
    return sorted(vals)


def snapshot(with_assembly=False):
    steps, drawings = {}, {}
    for path in sorted(glob.glob(OUT + "**/*.step", recursive=True)):
        rel = os.path.relpath(path, OUT)
        if rel.replace(os.sep, "/") == ASSEMBLY and not with_assembly:
            continue
        steps[rel] = _solid_signature(path)
    for path in sorted(glob.glob(OUT + "**/*.dxf", recursive=True)):
        drawings[os.path.relpath(path, OUT)] = _drawing_signature(path)
    return {"steps": steps, "drawings": drawings,
            "parameters": _parameter_values()}


def _multiset(d):
    """{name: signature} -> {signature: how many}, i.e. names thrown away."""
    out = {}
    for sig in d.values():
        key = json.dumps(sig, sort_keys=True)
        out[key] = out.get(key, 0) + 1
    return out


def compare(before, after):
    """What moved. Empty list means the rename was pure."""
    problems = []
    for kind in ("steps", "drawings"):
        a, b = _multiset(before[kind]), _multiset(after[kind])
        gone = sorted(set(a) - set(b))
        new = sorted(set(b) - set(a))
        for key in gone:
            problems.append("%s: one that was there is no longer, or has "
                            "changed: %s" % (kind, key[:160]))
        for key in new:
            problems.append("%s: one that was not there has appeared, or has "
                            "changed: %s" % (kind, key[:160]))
        for key in set(a) & set(b):
            if a[key] != b[key]:
                problems.append("%s: %d of them before, %d now: %s"
                                % (kind, a[key], b[key], key[:120]))
        if len(before[kind]) != len(after[kind]):
            problems.append("%s: %d files before, %d now"
                            % (kind, len(before[kind]), len(after[kind])))

    pa, pb = before.get("parameters"), after.get("parameters")
    if pa is None or pb is None:
        problems.append("parameters: no CSV to compare")
    elif len(pa) != len(pb):
        problems.append("parameters: %d values before, %d now" % (len(pa), len(pb)))
    else:
        moved = [(x, y) for x, y in zip(pa, pb) if abs(x - y) > 1e-9]
        if moved:
            problems.append("parameters: %d values moved, the first is %s -> %s"
                            % (len(moved), moved[0][0], moved[0][1]))
    return problems


def main():
    with_assembly = "--assieme" in sys.argv or "--assembly" in sys.argv
    if "--save" in sys.argv or "--salva" in sys.argv:
        snap = snapshot(with_assembly)
        with open(REFERENCE, "w", encoding="utf-8") as f:
            json.dump(snap, f)
        print("reference saved: %d solid files, %d drawings, %d parameters"
              % (len(snap["steps"]), len(snap["drawings"]),
                 len(snap["parameters"] or [])))
        return 0

    if not os.path.exists(REFERENCE):
        print("!  no reference to compare against. Run --save first, on the "
              "build BEFORE the change.")
        return 1
    with open(REFERENCE, encoding="utf-8") as f:
        before = json.load(f)
    problems = compare(before, snapshot(with_assembly))
    if problems:
        for p in problems:
            print("!  %s" % p)
        print("\n%d differences: the geometry MOVED." % len(problems))
        return 1
    print("--- OK ---")
    print("   nothing moved: %d solid files, %d drawings, %d parameter values"
          % (len(before["steps"]), len(before["drawings"]),
             len(before["parameters"] or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
