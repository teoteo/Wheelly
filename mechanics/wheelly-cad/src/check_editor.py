# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Can the editor regenerate the drawings?

It exists because of a real defect, found in use and not by the tests: the
editor works in a SANDBOX - a temporary folder into which it copies the
modules and runs them - and a new module that did not end up in it made the
preview alone fail. build.py, which runs on the real files, did not notice:
it said "all checks passed" while the editor said "generation failed, drawing
not available".

It happened twice, with two different modules. Now the sandbox copies the
whole of src/, but the question no other check answers remains: does what the
editor shows really get generated? This one asks it, and it costs a couple of
seconds because it uses only the 2D generators.
"""
import os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)

import ui_build
import ui_model

OUT = os.path.join(os.path.dirname(SRC), "out") + os.sep

# Beyond this number of names a signature no longer narrows anything down: the
# project has fewer than four hundred parameters, and the editor uses the
# signature to CHOOSE between geometries that have the same value. The defect
# this check watches for - the "fixed signature" - put SIXTY-SIX of them on a
# single polyline, because the assembly views ask for the list of purchased
# parts all at once and the readings of all of them ended up on the first one
# drawn. The limit is generous on purpose: it is there to see whether the
# mechanism has broken again, not to chase the last decimal.
MAX_SIGNATURE = 20

# The assembly views are the drawings the editor falls back on when a
# dimension has no detail drawing, i.e. the case where it was most often wrong.
ASSEMBLY_VIEWS = ("assembly_plan.dxf", "assembly_section.dxf", "assembly_details.dxf")


def narrow_signatures():
    """No entity of the assembly views carries a catch-all signature.

    It is measured on the PRODUCED DRAWING, not on the code that signs: it is
    the only reading that also sees signatures that widen by a new road.
    """
    import ezdxf
    faults = []
    for name in ASSEMBLY_VIEWS:
        path = OUT + "drawings/" + name
        if not os.path.exists(path):
            faults.append((name, "missing", 0))
            continue
        widest, signed = 0, 0
        for e in ezdxf.readfile(path).modelspace():
            try:
                dims = [v for c, v in e.get_xdata("WHEELLY") if c == 1000]
            except Exception:
                continue
            signed += 1
            widest = max(widest, len(dims))
        if widest > MAX_SIGNATURE:
            faults.append((name, "signature of %d dimensions" % widest, signed))
        elif not signed:
            faults.append((name, "no signed entity", 0))
    return faults


def main():
    # The Italian of the parameter descriptions sits in its own catalogue,
    # keyed by name: a rename in parameters.py orphans the key, and the editor
    # quietly falls back to English. Nothing else would notice.
    import texts_editor
    orphans = texts_editor.check_parameters(
        p.texts_key for p in ui_model.Model().parameters)
    if orphans:
        print("!  texts_parameters_it: keys without a parameter   %s" % ", ".join(orphans))
        return 1

    result = ui_build.Sandbox().regenerate(
        ui_model.updated_source(ui_model.Model()))

    if not result["ok"]:
        print("!  the editor does not regenerate   fails at %s" % result.get("fase"))
        print("   " + (result.get("errore") or "").strip().splitlines()[-1])
        return 1

    # Not blowing up is not enough: it must have produced ALL the drawings the
    # editor expects to show. A generator that writes half of the files
    # without complaining would leave the editor with empty frames.
    missing = [n for n in ui_build.DRAWINGS if n not in result["disegni"]]
    if missing:
        print("!  the editor does not regenerate everything   missing: %s" % ", ".join(missing))
        return 1

    faults = narrow_signatures()
    if faults:
        for name, why, _ in faults:
            print("!  signature too wide            %s: %s" % (name, why))
        return 1

    print("--- OK ---")
    print("   the editor regenerates its drawings                  %d of %d"
          % (len(result["disegni"]), len(ui_build.DRAWINGS)))
    print("   the assembly views' signatures narrow down           max %d dimensions"
          % MAX_SIGNATURE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
