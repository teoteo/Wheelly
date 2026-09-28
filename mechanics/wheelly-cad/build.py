#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""
Wheelly - parametric generator
==============================

Regenerates the whole project (DXF + STEP + parameters CSV, the complete
assembly as separate bodies, plus coarse STL files to look at in out/stl) and
checks its consistency.

    python3 build.py              generates everything and checks
    python3 build.py --dxf-only   generates only the 2D drawings (fast, no OCCT)
    python3 build.py --check-only runs only the checks on the files already there
    python3 build.py --one-by-one the checks one at a time instead of together

The Italian flags of before (--solo-dxf, --verifica, --in-fila) still work.

Single source of truth: src/parameters.py
All the results end up in out/
"""
import os, sys, subprocess, time

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")
OUT  = os.path.join(ROOT, "out")

DRAWINGS = [("drawings.py",            "2D drawings + parameters CSV"),
            ("drawing_dimensioned.py", "dimensioned section of the body"),
            ("drawings_assembly.py",   "assembly view: plan and section"),
            # the layout on the board ends up in pcb/, beside the diagrams:
            # the build generates it because it reads the same dimensions as
            # the box
            ("drawing_board_layout.py", "layout on the board (pcb/)"),
            # the wiring diagrams too: they were two SVG files written by hand
            # and at the first move of the layout they became false
            ("drawing_wiring.py",      "wiring diagrams (pcb/schemi/)"),
            # and the paginated booklet, which comes from the two above: every
            # time the diagrams are regenerated an updated PDF comes out in
            # pcb/, so what gets printed cannot fall behind the model. It
            # wants Inkscape and PIL: if they are missing it says
            # so and carries on, because the booklet is an extra and not a
            # part - but it says so, it does not vanish in silence.
            ("print_diagrams_pdf.py",  "booklet to print (pcb/)", ["--dal-build"])]
SOLIDS  = [("solids_body_collar.py",  "reference body, disc, collar"),
           ("solids_wheel.py",        "clutch: ASA hub + TPU ring"),
           ("solids_arm.py",          "motor arm"),
           ("solids_box_collar.py",   "the one piece: box + collar"),
           ("solids_electronics.py",  "the panel and the electronics envelopes"),
           ("solids_sensor.py",       "sensor bracket"),
           ("solids_tools.py",        "assembly tools"),
           ("solids_cables.py",       "the cables, as solids"),
           # The assembly goes AFTER all the others: it reads them back from
           # disk and puts them together. It is here and not apart because it
           # is the only place where the fit errors show, and an assembly that
           # is not regenerated grows old in silence.
           ("solids_assembly.py",     "complete assembly, as separate bodies"),
           ("stl_preview.py",         "coarse STL files to look at"),
           # The bill goes AFTER the assembly: it counts the parts from there
           # and weighs the solids just regenerated. Generated and not written
           # by hand, because a copied-out bill comes loose at the first part
           # that changes.
           ("bom_mechanics.py",       "the bill of the mechanics"),
           # the GLOBAL bill of materials at the root, in English: printed,
           # mechanics and electronics in one place
           ("bom_global.py",          "the global bill of materials (BOM.md)"),
           # The assembly guide: its pictures are renders of the assembly just
           # regenerated, so it sits at the end like the bill. On an old
           # assembly a guide would come out showing yesterday's machine, and
           # the pictures would look right all the same.
           ("assembly_guide.py",      "the assembly guide (docs/assembly/)"),
           # and the guide to the INDI panel, from the panel the real driver
           # declares (driver/indi-wheelly/doc): pictures and words
           ("../../../driver/indi-wheelly/doc/panel_guide.py", "the INDI panel guide (docs/driver/)")]
CHECK   = [# First because it costs a tenth of a second and reads no solid: it
           # watches the NAMES of the parameters, which no other check looks
           # at. check_unchanged.py ignores the names by trade, and the
           # geometry comes out identical whether a dimension is called
           # Th_box or Sp_scatola.
           ("check_names.py",         "the parameter names are in the glossary"),
           ("check_dimensions.py",    "dimension chains"),
           # This one too costs a second and reads two STEP files: it stays
           # outside the audit on purpose, so breaking it to test it costs a
           # second and not twelve minutes.
           ("check_grip.py",          "the grip to turn by hand, and the plug"),
           # This one too stays outside the audit, and for the same reason: it
           # costs a minute and not twelve, so breaking it on purpose to test
           # it can really be done. It is the first of the family that was
           # missing - the assembly PATHS, not the envelopes of the assembled
           # machine.
           ("check_wheel_entry.py",   "the wheel still goes in from the side"),
           # The arc round the motor: outside the audit for the
           # same reason, so it can be broken on purpose in seconds.
           ("check_arc_back.py",      "the arc round the motor"),
           # the head face as a print bed: seconds, same reason
           ("check_head_face.py",     "the head face is one plane"),
           # the reference filter disc: closed holes, the web observed on the
           # real disc, on the body's optical hole. Seconds, same reason
           ("check_filter_disc.py",   "the filter disc: closed holes on the optical axis"),
           # The cable route on the sensor bracket: outside the
           # audit so it can be broken on purpose in seconds.
           ("check_cable_route.py",   "the cable route on the sensor bracket"),
           # eleven details of a review of the parts, on the solids: two of
           # them (bearings, motor screws) had passed a full build unseen.
           # Seconds, outside the audit, so each can be broken on purpose.
           ("check_details.py",       "the details of the parts review"),
           # the INDI panel guide covers every property of the driver
           ("check_panel_guide.py",   "the INDI panel guide follows the driver"),
           ("check_audit.py",         "cross audit files/parameters + interpenetrations"),
           # The editor runs in a sandbox all of its own, and there a new
           # module that does not end up inside it breaks the preview only:
           # build.py, which works on the real files, would never notice.
           ("check_editor.py",        "the editor regenerates its drawings"),
           # The assembly paths: every move the assembly guide
           # declares must get home without going through anything - the
           # family of the box that went through the pivot screw in its last
           # 8 mm, which no check of the assembled machine can see. It was
           # LAST on purpose while the checks ran one after the other and the
           # first failure stopped the build; since they run together (see
           # check_all() below) every check runs to the end whatever the
           # others do. About twelve minutes.
           # in four processes side by side, each making every fourth sweep
           # (--part): alone it was the longest check, ten minutes
           ("check_assembly_paths.py", "assembly moves, part 1 of 4", ["--part", "0/4"]),
           ("check_assembly_paths.py", "assembly moves, part 2 of 4", ["--part", "1/4"]),
           ("check_assembly_paths.py", "assembly moves, part 3 of 4", ["--part", "2/4"]),
           ("check_assembly_paths.py", "assembly moves, part 4 of 4", ["--part", "3/4"])]


# The "!" lines of the checks that already ran. They used to be printed only
# at the very end, after the last check - and since check_assembly_paths
# (last on purpose) started failing, the build stopped before the summary,
# every time: an audit incongruence stayed unseen for a day behind "only the
# assembly paths fail". Now an error prints them first.
KO_SO_FAR = []


def run(module, description, args=()):
    t = time.time()
    print("  %-34s %s" % (description, "..."), end="", flush=True)
    r = subprocess.run([sys.executable, os.path.join(SRC, module)] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(" ERROR")
        print(r.stdout); print(r.stderr, file=sys.stderr)
        if KO_SO_FAR:
            print("\nINCONSISTENCIES ALREADY FOUND by the checks that passed before this one:")
            for line in KO_SO_FAR:
                print("   ", line)
        sys.exit(1)
    KO_SO_FAR.extend(x.strip() for x in r.stdout.split("\n") if x.strip().startswith("!"))
    print("\r  %-34s %5.1fs" % (description, time.time() - t))
    return r.stdout


def check_all():
    """The checks, ALL AT ONCE. They only read out/ - the editor's
    works in a sandbox of its own - and none needs another's result, so run
    one after the other they kept one core of ten busy and the build took the
    sum of them, some 33 minutes, the audit (17) and the assembly paths (12)
    more than half of it. Together it takes as long as the longest. Each still
    runs in its own process; the report comes in the order of CHECK, not in
    the order they finish, so two builds read the same. With --one-by-one they
    run one at a time, as before - for when the Mac is needed for something
    else, or to read one check's output without the others' in between."""
    if "--one-by-one" in sys.argv:
        outcome = ""
        for entry in CHECK:
            outcome += run(entry[0], entry[1], entry[2] if len(entry) > 2 else ())
        return outcome
    from concurrent.futures import ThreadPoolExecutor

    def launch(entry):
        t = time.time()
        r = subprocess.run([sys.executable, os.path.join(SRC, entry[0])]
                           + list(entry[2] if len(entry) > 2 else ()),
                           capture_output=True, text=True)
        return entry, r, time.time() - t

    t0 = time.time()
    print("  %d checks together..." % len(CHECK), flush=True)
    with ThreadPoolExecutor(max_workers=min(len(CHECK), os.cpu_count() or 4)) as ex:
        results = list(ex.map(launch, CHECK))
    outcome, errors = "", []
    for entry, r, dt in results:
        d = entry[1]
        print("  %-34s %5.1fs%s" % (d, dt, "  ERROR" if r.returncode != 0 else ""))
        if r.returncode != 0:
            errors.append((d, r))
        else:
            outcome += r.stdout
    print("  (%.1fs in all)" % (time.time() - t0))
    if errors:
        # a check that stops with an error has no "!" lines to give: print its
        # output, and the incongruences the others found, which are no less
        # true for it
        for d, r in errors:
            print("\nERROR in %s:" % d)
            print(r.stdout); print(r.stderr, file=sys.stderr)
        ko = [x.strip() for x in outcome.split("\n") if x.strip().startswith("!")]
        if ko:
            print("\nINCONSISTENCIES FOUND by the other checks:")
            for line in ko:
                print("   ", line)
        sys.exit(1)
    return outcome


# The flags are English; the older Italian ones stay as
# aliases, because the READMEs, the working notes and the published assembly
# guide (the page on the parameters) quote them, and a command that worked
# yesterday must not stop working because the source changed language.
FLAG_ALIASES = {"--solo-dxf": "--dxf-only", "--verifica": "--check-only",
                "--in-fila": "--one-by-one"}


def main():
    sys.argv[1:] = [FLAG_ALIASES.get(a, a) for a in sys.argv[1:]]
    dxf_only = "--dxf-only" in sys.argv
    check_only = "--check-only" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    # The makers' models are not shipped (src/vendor_files.py says why): say
    # which one is missing BEFORE twenty minutes of build, not as a traceback
    # from a generator halfway through. --dxf-only too: the assembly drawing
    # takes the hatch under the motor from the motor's model.
    sys.path.insert(0, SRC)
    import vendor_files
    gone = vendor_files.missing()
    if gone:
        print(vendor_files.explain(gone))
        sys.exit(3)

    if not check_only:
        print("\nDRAWINGS")
        for entry in DRAWINGS:
            m, d = entry[0], entry[1]
            o = run(m, d, entry[2] if len(entry) > 2 else ())
            for line in (o or "").strip().split("\n"):
                if line.startswith("  WARNING") or line.endswith(".pdf"):
                    print("      " + line.strip())
        if not dxf_only:
            print("\nSOLIDS")
            for m, d in SOLIDS:
                o = run(m, d).strip()
                if o:
                    for line in o.split("\n"):
                        print("      " + line)

    if dxf_only:
        print("\nSkipping the 3D checks (--dxf-only).\n")
        return

    print("\nCHECKS")
    outcome = check_all()

    ko = [r for r in outcome.split("\n") if r.strip().startswith("!")]
    print()
    if ko:
        print("INCONSISTENCIES FOUND:")
        for r in ko:
            print("   ", r.strip())
        sys.exit(2)
    print("All checks passed.")
    n = len([f for f in os.listdir(OUT) if f.split(".")[-1] in ("dxf", "step", "csv")])
    print("%d files in %s\n" % (n, OUT))


if __name__ == "__main__":
    main()
