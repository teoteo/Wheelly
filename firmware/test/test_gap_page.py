# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT
"""The texts of the air-gap test bench (firmware/gap_page/index.html).

The page speaks English (default) and Italian (?lang=it) from two JSON
catalogues inside the page itself. A key missing from a catalogue shows on
the page as [key], but only in the language and the state it is opened in:
here everything is checked at once, without a browser.

  1. the two catalogues have the same keys;
  2. every key used - data-t, data-th, t("...") - exists in the catalogues;
  3. every catalogue key is used: an orphan key is a text someone translates
     for nothing, or a t() that has changed name.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "gap_page", "index.html")


def main(path=PAGE):
    s = open(path, encoding="utf-8").read()
    m = re.search(r'<script id="texts" type="application/json">(.*?)</script>', s, re.S)
    if not m:
        print("MISSING the text catalogue in the page"); return 1
    cat = json.loads(m.group(1))
    en, it = set(cat["en"]), set(cat["it"])
    rest = s[:m.start()] + s[m.end():]
    used = set(re.findall(r'data-th?="([a-z_A-Z0-9]+)"', rest))
    used |= set(re.findall(r'\bt\("([a-z_A-Z0-9]+)"', rest))
    # keys chosen at runtime inside t(): t(cond ? "a" : "b")
    for a, b in re.findall(r'\bt\([^"\n]*?\?\s*"([a-z_]+)"\s*:\s*"([a-z_]+)"\)', rest):
        used |= {a, b}
    errors = []
    if en != it:
        errors.append("catalogues differ: only en %s, only it %s"
                      % (sorted(en - it), sorted(it - en)))
    if used - en:
        errors.append("keys used and not in the catalogue: %s" % sorted(used - en))
    if en - used:
        errors.append("keys in the catalogue and never used: %s" % sorted(en - used))
    errors += consistency_with_project(s)
    for e in errors:
        print("ERROR:", e)
    if not errors:
        print("page texts: %d keys, en and it equal, all used" % len(en))
    return 1 if errors else 0


PARAMETERS = os.path.join(HERE, "..", "..", "mechanics", "wheelly-cad", "src", "parameters.py")


def value(name, text):
    """The value of a parameter, read from parameters.py without importing it:
    the test bench runs on the system python, which has no cadquery."""
    m = re.search(r'\(\s*"%s"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*([-0-9.]+)' % name, text)
    return float(m.group(1)) if m else None


def consistency_with_project(s, path=PARAMETERS):
    """The numbers the page repeats by hand must be the project's.
    They once were not: the page offered the 3.6 to 4.2 feet from
    before the spacer and the glue, and with the right chain gave negative
    air gaps; and it suggested writing Traferro_nominale, a name the project
    no longer had."""
    par = open(path, encoding="utf-8").read()
    err = []
    for constant, name in (("TH_SPACER", "Th_spacer_magnet"), ("TH_MAGNET", "Th_magnet"),
                           ("TH_GLUE", "Th_glue_stack_magnet"), ("CHIP_BODY", "H_body_chip")):
        m = re.search(r"\b%s = ([-0-9.]+)" % constant, s)
        v = value(name, par)
        if not m or v is None or abs(float(m.group(1)) - v) > 1e-6:
            err.append("%s of the page (%s) differs from %s (%s)"
                       % (constant, m.group(1) if m else "?", name, v))
    h0, n, pitch = (value(k, par) for k in ("H_min_foot_test", "N_foot_test", "Pitch_foot_test"))
    expected = ["%.1f" % (h0 + i*pitch) for i in range(int(n))] if None not in (h0, n, pitch) else []
    offered = re.findall(r"<option(?: selected)?>([0-9.]+)</option>", s)
    if offered != expected:
        err.append("feet of the page %s, of the project %s" % (offered, expected))
    for name in set(re.findall(r"<code>([A-Z][A-Za-z_]+) = \{g\}</code>", s)):
        if value(name, par) is None:
            err.append("the page suggests %s, which is not in parameters.py" % name)
    return err


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
