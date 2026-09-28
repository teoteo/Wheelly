<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# Contributing

Questions, bug reports and patches are welcome through the repository's
**Issues** and pull requests. There is no mailing list and no private contact
address.

## Licensing of contributions

By contributing you agree that your contribution is released under the licence
that already applies to the files you touch — see [`LICENSING.md`](LICENSING.md).
The rule is that the licence follows the directory: MIT for `firmware/` and
`driver/`, CERN-OHL-P-2.0 for `mechanics/`, CC-BY-4.0 for documentation.

There is no contributor licence agreement to sign. The permissive licences make
one unnecessary: everyone, the author included, has the same rights over the
result.

If you add files, run `tools/spdx_headers.py` so they carry the right header.

## Before opening a pull request

The project has a working method that is easy to miss and annoying to correct
afterwards. Each rule below exists because breaking it has already cost a
defect.

**How to build and test**

- **the CAD verifies itself.** `mechanics/wheelly-cad/build.py` regenerates the
  solids and runs the dimensional audit (about twenty minutes). It must be green,
  and it must be run with the project's `.venv/bin/python`. Check that the build
  succeeded *before* measuring anything: after a failed build you read old STEP
  files and get false measurements that look true;
- **the firmware has its own bench**: `firmware/test/run_all.sh`, no hardware
  needed. Compile for the ESP32 too, not only on the host: a defect has already
  gone through the host tests and shown only on the real compiler;
- **the driver has its bench**: `driver/indi-wheelly/driver_bench.py`, under a
  real `indiserver`, against the firmware simulator;
- **the parameter editor** (`ui.py`) does not reload files by itself: restart it
  after changing a generator or the parameters.

**How things are verified**

- **measure the solid, do not re-read the parameter** that the check is supposed
  to watch. A check that derives its measurement from the parameter it guards
  guards nothing;
- **new checks must be proven able to fail.** Break the thing the check watches
  and confirm it complains. A check that cannot fail is worse than no check;
- **tell measured from declared.** Dimensions taken with a calliper are marked as
  such (`M`); those assumed from a catalogue or written by hand are where most of
  the defects so far came from;
- **what the model does not contain, no check can see.** Bought parts drawn
  fuller than the real thing have already hidden defects: before saying "it
  fits", check that the part that has to fit is in the model;
- **no hand-written numbers where a relation is needed.** Dimensions that follow
  from others are derived: slots, openings and cable passages written by hand
  drifted away from the part they had to follow;
- **defects that show at the second use escape the tests**: a test builds
  everything from scratch and uses it once, a person connects, disconnects and
  connects again.

**Design rules**

- **a new part must be registered** or it does not show: the assembly and STL
  lists (`stl_preview.py`), its colour in `solids_assembly.py`, its checks in
  `check_audit.py`, and its row in `PRINTED` in `src/bom_mechanics.py`, print
  orientation included;
- **the print orientation is part of the design**, decided while drawing and
  written with the part. A long narrow hole prints along its own axis;
- **exposed sharp edges are chamfered or filleted**;
- **soluble supports only if there is no alternative**: first look for a shape
  that prints with breakaway supports;
- **every part is checked in the assembly and disassembly sequence too**, not
  only assembled: a part that fits but cannot be fitted is useless;
- **the output folder stays split**: `out/` only the parts to print,
  `out/tools/` the test tools, `out/drawings/`, `out/electronics/`,
  `out/references/` the rest. Printing a tool for a part costs an hour;
- **what depends on one wheel's mechanics is an option with a default**, not a
  constant: Wheelly is meant for wheels other than the prototype's.

**Say why in the commit message**, not only what, and put the why in the comment
next to the dimension too. Most of the comments in this project exist to stop
someone re-trying a road that was already found closed.

## Language

The project is written in English: code, comments, parameter names, file names,
documents. User-facing strings go through translation keys, with an English and
an Italian catalogue; the guides are bilingual, with English as the source and
the Italian in a separate catalogue that records the fingerprint of the English
it translates — change an English text and the build fails until the translation
is redone (`python3 -m guide.language it` from `mechanics/wheelly-cad/src`,
`python3 panel_language.py it` from `driver/indi-wheelly/doc`). Names that come
from outside (`F695ZZ`, `AS5600`, `TMC2209`, `GX12`) are never translated.
