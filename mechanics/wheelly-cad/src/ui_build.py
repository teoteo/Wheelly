# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Regeneration of the drawings and of the checks on modified parameters.

Everything happens in a temporary folder that holds a copy of parameters.py
with the changes inside and a link to the real modules. The project's source
is never written: the preview is a simulation, not a change.
"""
import os, re, shutil, subprocess, sys, tempfile

SRC  = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)

# The 2D modules: fast (no OCCT) and enough for the preview of the drawings.
GENERATORS = ["drawings.py", "drawing_dimensioned.py", "drawings_assembly.py"]
CHECKS  = ["check_dimensions.py"]

# The solids: they go through the OCCT kernel, cost a couple of minutes and
# are needed only when the CAD files and the cross audit are really wanted.
# FROM build.py, not written here: this list was written by hand and had
# drifted - it still named solids_box.py, gone since box and collar became one
# part, and missed the one-piece box, the electronics, the cables and the
# assembly. The generators and the descriptions are build.py's,
# up to the STL previews: the bill and the guide stay out of the editor.
sys.path.insert(0, os.path.dirname(SRC))
import build as _build
_end = [m for m, _d in _build.SOLIDS].index("stl_preview.py") + 1
SOLIDS = [m for m, _d in _build.SOLIDS][:_end]
AUDIT  = "check_audit.py"

DRAWINGS = ["assembly_plan", "assembly_section", "assembly_details",
           "collar_plan", "collar_section", "arm_plan",
           "clutch_section", "flat_gasket", "sensor_bracket",
           "magnet_cap", "body_dimensioned"]

CHECK_LINE = re.compile(r"^(?P<nome>.*?)\s{2,}(?P<valore>-?\d+\.\d+)\s+"
                      r"(?P<verso>>=|<=)\s+(?P<limite>-?\d+\.\d+)\s*(?P<unita>\S*)$")


class Sandbox(object):
    """Throwaway working copy of the project."""

    def __init__(self):
        # THE SANDBOX HAS THE PROJECT'S OWN LAYOUT: wheelly-cad/src and
        # wheelly-cad/out, with others/ beside wheelly-cad as a link to the
        # real one. The modules find the bought parts' STEP files as
        # "../others" from their project folder, and with src/ and out/
        # straight in the temporary folder that pointed nowhere. It broke
        # when purchased.py started asking sagoma_motore where the
        # hatch screws are - which reads the maker's motor: build.py was fine,
        # and the editor could not draw the assembly view.
        self.dir = tempfile.mkdtemp(prefix="wheelly-ui-")
        self.base = os.path.join(self.dir, "wheelly-cad")
        self.src = os.path.join(self.base, "src")
        self.out = os.path.join(self.base, "out")
        os.makedirs(self.src); os.makedirs(self.out)
        os.symlink(os.path.join(os.path.dirname(os.path.dirname(SRC)), "others"),
                   os.path.join(self.dir, "others"))
        self.refresh_modules()

    def refresh_modules(self):
        """Brings the modules into the sandbox as they are now in the project.

        It is redone at every regeneration, not only at start-up: whoever
        works on the generators wants to see the new drawing without
        restarting the server. It holds only for the subprocesses, though -
        ui_render and ui_dimensions run inside this process and stay the ones
        loaded at start-up.

        ALL of src/ is copied, and not a list of modules: a list gets
        forgotten. It has already happened twice - with ui_model.py, which the
        audit imports to re-evaluate the expressions, and with purchased.py,
        which the assembly drawings import to know where the bought
        components are. In both cases the module was missing only in the
        sandbox, so build.py ran perfectly well and the editor said
        "generation failed, drawing not available" - that is, the defect
        showed only where nobody was looking for it. The lists above say what
        is RUN, which is another question.

        The two parameter files stay out, and not by oversight: parameters.py
        is rewritten by _write_parameters() with the changes being tried
        inside, and parameters_local.py would overwrite those changes with the
        saved overrides - the preview would show numbers that are not the
        ones being tried.
        """
        for name in sorted(os.listdir(SRC)):
            if name.endswith(".py") and not name.startswith("parameters"):
                shutil.copy(os.path.join(SRC, name), self.src)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write_parameters(self, source):
        with open(os.path.join(self.src, "parameters.py"), "w", encoding="utf-8") as f:
            f.write(source)

    def _run(self, module):
        # the sandbox builds no solids: the pages' true shape (true_shape.py)
        # is read from the real project's out/, where the last build left them
        # (WHEELLY_OUT_SOLIDI is the variable true_shape.py reads: it stays)
        env = dict(os.environ, WHEELLY_OUT_SOLIDI=os.path.join(os.path.dirname(SRC), "out"))
        return subprocess.run([sys.executable, os.path.join(self.src, module)],
                              capture_output=True, text=True, cwd=self.base, env=env)

    def regenerate(self, source):
        """Rewrites the parameters, redoes the DXF files and reruns the dimension chains.

        The keys of the dictionary it returns are read by the page (JSON):
        they stay Italian."""
        self.refresh_modules()
        self._write_parameters(source)
        for module in GENERATORS:
            r = self._run(module)
            if r.returncode != 0:
                return {"ok": False, "fase": module,
                        "errore": (r.stderr or r.stdout).strip()[-1500:], "controlli": []}
        r = self._run(CHECKS[0])
        if r.returncode != 0:
            return {"ok": False, "fase": CHECKS[0],
                    "errore": (r.stderr or r.stdout).strip()[-1500:], "controlli": []}
        checks = _read_checks(r.stdout)
        return {"ok": True,
                "controlli": checks,
                "falliti": [c for c in checks if not c["passa"]],
                "disegni": [n for n in DRAWINGS
                            if os.path.exists(os.path.join(self.out, "drawings", n + ".dxf"))]}

    def dxf(self, name):
        path = os.path.join(self.out, "drawings", name + ".dxf")
        return path if os.path.exists(path) else None


def _read_checks(output):
    """Turns the list printed by check_dimensions into data.

    The two final lists already report every check with a known outcome:
    those prefixed by '!' are the chains that do not add up.
    """
    checks, inside = [], None
    for line in output.splitlines():
        if line.startswith("--- OK"):
            inside = True; continue
        if line.startswith("--- TO FIX"):
            inside = False; continue
        if inside is None or not line.strip():
            continue
        body = line.strip()
        passes = not body.startswith("!")
        m = CHECK_LINE.match(body.lstrip("! ").rstrip())
        if not m:
            continue
        checks.append({"nome": m.group("nome").strip(),
                       "valore": float(m.group("valore")),
                       "verso": m.group("verso"),
                       "limite": float(m.group("limite")),
                       "unita": m.group("unita") or "mm",
                       "passa": passes and inside,
                       "margine": (float(m.group("valore")) - float(m.group("limite")))
                                  * (1 if m.group("verso") == ">=" else -1)})
    return checks


# --------------------------------------------------------------------------
# Complete regeneration: STEP files and cross audit
# --------------------------------------------------------------------------

# the names of the steps, shown by the page in the log of the regeneration
DESCRIPTIONS = {
    "drawings.py":            "2D drawings and parameters CSV",
    "drawing_dimensioned.py": "dimensioned section of the body",
    "drawings_assembly.py":    "assembly view: plan, section and details",
    "solids_body_collar.py":  "reference body, disc, collar",
    "solids_wheel.py":        "clutch: ASA hub and TPU ring",
    "solids_arm.py":          "motor arm",
    "solids_sensor.py":      "sensor bracket and cover",
    "solids_tools.py":     "assembly tools",
    "stl_preview.py":       "coarse STL files to look at",
    "check_dimensions.py":    "dimension chains",
    "check_audit.py":         "cross audit and interpenetrations",
}
# and build.py's own words for the generators this dict does not name
for _m, _d in _build.SOLIDS:
    DESCRIPTIONS.setdefault(_m, _d)


class CadJob(object):
    """A complete regeneration in progress, with its log.

    It runs in a thread of its own because the solids cost a couple of
    minutes: the page meanwhile stays alive and shows the steps as they
    finish. The state strings ("in corso", "finito", "errore") and the keys
    of snapshot() are read by the page's script: they stay Italian.
    """

    def __init__(self):
        self.state = "in corso"
        self.steps = []
        self.checks = []
        self.audit = []
        self.error = None
        self.files = []
        self.saved = None            # outcome of the save into out/, if it happened
        self.duration = 0.0

    def snapshot(self):
        return {"stato": self.state, "passi": self.steps, "controlli": self.checks,
                "audit": self.audit, "errore": self.error, "file": self.files,
                "salvati": self.saved, "durata": round(self.duration, 1),
                "falliti": [c for c in self.checks + self.audit if not c["passa"]]}


def regenerate_cad(sandbox, source, job):
    """Redoes drawings, solids and checks as build.py does, inside the sandbox."""
    import time
    start = time.time()
    # the makers' models are not shipped: say which, instead of a traceback from
    # the box's generator (why they stop everything: src/vendor_files.py)
    import vendor_files
    gone = vendor_files.missing()
    if gone:
        job.state = "errore"
        job.error = vendor_files.explain(gone)
        job.duration = time.time() - start
        return job
    sandbox.refresh_modules()
    sandbox._write_parameters(source)
    try:
        for module in GENERATORS + SOLIDS:
            t0 = time.time()
            r = sandbox._run(module)
            if r.returncode != 0:
                job.state = "errore"
                job.error = "%s: %s" % (module, (r.stderr or r.stdout).strip()[-1200:])
                return job
            job.steps.append({"nome": DESCRIPTIONS.get(module, module),
                              "secondi": round(time.time() - t0, 1),
                              "righe": [x for x in r.stdout.strip().split("\n") if x]})

        r = sandbox._run(CHECKS[0])
        job.checks = _read_checks(r.stdout)
        job.steps.append({"nome": DESCRIPTIONS[CHECKS[0]], "secondi": 0.0, "righe": []})

        t0 = time.time()
        r = sandbox._run(AUDIT)
        if r.returncode != 0:
            job.state = "errore"
            job.error = "%s: %s" % (AUDIT, (r.stderr or r.stdout).strip()[-1200:])
            return job
        job.audit = _read_audit(r.stdout)
        job.steps.append({"nome": DESCRIPTIONS[AUDIT],
                          "secondi": round(time.time() - t0, 1), "righe": []})

        job.files = sorted(
            os.path.relpath(os.path.join(r, n), sandbox.out)
            for r, _, ns in os.walk(sandbox.out) for n in ns
            if n.rsplit(".", 1)[-1] in ("dxf", "step", "csv"))
        job.state = "finito"
    except Exception as exc:                      # the thread must not die in silence
        job.state = "errore"
        job.error = "%s: %s" % (type(exc).__name__, exc)
    finally:
        job.duration = time.time() - start
    return job


def _read_audit(output):
    """check_audit prints name and detail, without comparable values."""
    checks, inside = [], None
    for line in output.splitlines():
        if line.startswith("--- OK"):
            inside = True; continue
        if line.startswith("--- INCONSISTENCIES"):
            inside = False; continue
        if inside is None or not line.strip():
            continue
        body = line.strip()
        passes = inside and not body.startswith("!")
        body = body.lstrip("! ").rstrip()
        if not body:
            continue
        pieces = body.split("  ")
        checks.append({"nome": pieces[0].strip(),
                       "dettaglio": " ".join(x for x in pieces[1:] if x.strip()).strip(),
                       "passa": passes})
    return checks


EXTENSIONS = ("dxf", "step", "csv")


def publish(sandbox, destination):
    """Brings the files just generated into out/, and removes those that are not.

    A generator renamed or removed leaves behind a file that nobody produces
    any more and that the audit does not look at: it stays there looking like
    a result. out/ must hold the outcome of this generation and nothing else.
    """
    os.makedirs(destination, exist_ok=True)
    brought = []
    for f in sorted(os.listdir(sandbox.out)):
        if f.rsplit(".", 1)[-1] in EXTENSIONS:
            shutil.copy2(os.path.join(sandbox.out, f), os.path.join(destination, f))
            brought.append(f)
    removed = []
    for f in sorted(os.listdir(destination)):
        if f.rsplit(".", 1)[-1] in EXTENSIONS and f not in brought:
            os.remove(os.path.join(destination, f))
            removed.append(f)
    # the preview STL files are in a folder of their own: it is replaced whole,
    # otherwise the earlier ones stay there showing parts that are no longer so
    stl = os.path.join(sandbox.out, "stl")
    if os.path.isdir(stl):
        shutil.rmtree(os.path.join(destination, "stl"), ignore_errors=True)
        shutil.copytree(stl, os.path.join(destination, "stl"))
        brought += ["stl/" + f for f in sorted(os.listdir(stl))]
    return brought, removed
