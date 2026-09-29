<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Proposing the driver to INDI

What is ready, and what is left, for proposing `indi_wheelly` for inclusion in INDI
itself. Everything below was checked against **indilib/indi master `4661ccd`**.

**The copy in INDI is produced, never edited there**:

```sh
python3 driver/indi-wheelly/upstream/to_indi.py PATH/TO/indi
```

puts the driver's files, the CMake block and the `drivers.xml` entry (with the version
read from this folder's `CMakeLists.txt`) into a checkout of indilib/indi, and
`to_indi.py --docs PATH/TO/drivers-docs` puts the driver's page into a checkout of
[indilib/drivers-docs](https://github.com/indilib/drivers-docs). Run again on the same tree it replaces what it put there, so the same
command serves every later pull request.

## Which repository

INDI's [`CONTRIBUTING.md`](https://github.com/indilib/indi/blob/master/CONTRIBUTING.md)
decides it by dependencies: a driver that builds with only what INDI Core already has
goes in **indilib/indi**, under `drivers/<category>/`; one that needs anything else goes
in indi-3rdparty. This driver needs libindi and nothing else, so it is a Core driver, in
`drivers/filter_wheel/`. The maintainers have the last word, which is why the ROADMAP
says to ask on the [INDI forum](https://indilib.org/forum.html) first.

## What is copied, and where

Into `drivers/filter_wheel/wheelly/` of INDI's tree (the list is `DRIVER_FILES` in
`to_indi.py`):

| file | |
|---|---|
| `wheelly.cpp`, `wheelly.h` | the driver |
| `plot.cpp`, `plot.h` | the magnet sweep plot |
| `wheelly_protocol.h` | the protocol, byte for byte `firmware/wheelly/wheelly_protocol.h` |
| `wheelly_config.h.cmake` | version and device name |

Not copied: this folder's own
`CMakeLists.txt` and `indi_wheelly.xml.cmake` (INDI builds and lists the driver its own
way, below), `driver_bench.py` and `doc/` (they need the simulator in `firmware/`, which
stays here), and `upstream/`.

A subfolder, not files loose in `drivers/filter_wheel/`, because the driver has six
files and one of them has a name (`plot`) too generic for a folder shared by fifteen
drivers. INDI already does it this way for the Shelyak driver in
`drivers/spectrograph/shelyak/`: sources in a subfolder, named from the category's
`CMakeLists.txt`, no `CMakeLists.txt` of their own.

The folder builds on its own: nothing in it includes from outside
(`firmware/test/test_driver_standalone.py` fails if something does, or if the two copies
of the protocol header differ).

## CMake and drivers.xml

- [`CMakeLists-indi.txt`](CMakeLists-indi.txt): the block `to_indi.py` appends to
  `drivers/filter_wheel/CMakeLists.txt`. Modelled on the filter wheels already there
  (`xagyl_wheel`, `rasa_filtercube`: one executable, linked to `indidriver`, installed to
  `bin`) and on Shelyak for the subfolder.
- [`drivers-xml-entry.xml`](drivers-xml-entry.xml): the `<device>` to add in the
  *Filter Wheels* group of INDI's `drivers.xml`, `manufacturer="DIY"` as INDI files
  MyFocuserPro2, ESP32go and the other self-built devices.

**Tried** on a Raspberry Pi (Arch Linux ARM, gcc) against master `4661ccd`: INDI
cloned in `/tmp`, `to_indi.py` run on it, `make indi_wheelly` - which builds
`libindidriver` from the same tree first (82 s with `-j3`). INDI compiles its drivers
with `-Wall -Wextra -Werror` (checked in the target's `flags.make`): the driver built
with **no warning**, linked to the tree's own `libindidriver`, and under `indiserver`,
with `LANG=it_IT.UTF-8`, it connected to the **real wheel**, read firmware, protocol,
filter names, position and sensor, showed no Language switch, and disconnected cleanly.
`to_indi.py` was also run twice on the same tree (the second run leaves it identical)
and on a tree where another driver's block follows ours (ours is replaced, the other
kept). One quirk
of INDI's, not ours: on a glibc as recent as Arch's, INDI's `configure` stops at
"Could NOT find Iconv", because its `-Werror` meets glibc's `_FORTIFY_SOURCE requires
compiling with optimization` warning inside CMake's own test programs. Passing
`-DCMAKE_C_FLAGS=-O2 -DCMAKE_CXX_FLAGS=-O2` gets past it.

## Code style

INDI formats C++ with Artistic Style, and its CI (`.github/workflows/linux-codestyle.yml`,
running `scripts/check-codestyle.sh`) fails a pull request whose changed lines are not
formatted. The options, from INDI's README ("Code Style") and that script:

```sh
astyle --style=allman --align-reference=name --indent-switches --indent-modifiers \
       --indent-classes --pad-oper --indent-col1-comments --lineend=linux \
       --max-code-length=124
```

The driver's sources and both copies of the protocol header are in that style
(astyle 3.6.18, `brew install astyle`), and `firmware/test/test_driver_standalone.py`
fails when a whole file is not: INDI's script only looks at the lines a pull request
changes, so a file can drift here unnoticed. Do not trust INDI's script on the Mac:
its regex `(.*?)` is not accepted by macOS's bash 3.2, and it then passes every file
without looking at it.

## Language

INDI's drivers are English, and INDI's maintainers asked, in the first review, for the
translation layer to go: no keys, no catalogues, no Language switch. The driver was
changed here, not only in the copy: it is English in this repository too, with the texts
written where they are used, so the copy in INDI and the driver here are the same files
and a fix made on INDI's side can be brought back as it is. The guides stay bilingual.
`firmware/test/test_driver_standalone.py` fails if a `tr(` call, a key or a catalogue
comes back.

## Licence

**The driver is LGPL-2.1-or-later**, the same as INDI (it was MIT before, changed
by its only author so the driver can live in INDI's tree). The copy proposed to INDI
and the one in this repository are the same files under the same licence.

- **The exception is `wheelly_protocol.h`, which stays MIT**: it is a byte-for-byte
  copy of the firmware's header, and the firmware stays MIT. MIT code inside an
  LGPL driver is fine - INDI's `COPYRIGHT` already lists files under other
  licences than the LGPL.
- **INDI is LGPL-2.1-or-later.** Its `LICENSE` is the LGPL 2.1, its `COPYRIGHT` gives
  `LGPL-2.1+` as the licence of the tree, and CONTRIBUTING asks for "a license
  header to all source files": every driver file carries its SPDX line; if the
  maintainers want the full LGPL notice instead, it goes on the copy there.
- LGPL still allows commercial use; what it adds is that changes to the driver
  itself must be shared under the same licence.

## Documentation

INDI's maintainers keep driver pages in
[indilib/drivers-docs](https://github.com/indilib/drivers-docs), not in INDI's tree
(CONTRIBUTING still says `doc/` in the driver's folder; the first review asked for
drivers-docs). The page is [`doc/wheelly.md`](doc/wheelly.md) with its metadata
[`doc/wheelly.yaml`](doc/wheelly.yaml) and the 300x300 thumbnail `doc/wheelly.webp`,
in that repository's shape (overview, features, installation, configuration, usage
and tips); `to_indi.py --docs` puts them in `src/content/docs/filter-wheels/generic/
wheelly/`, fills in the version and converts the screenshots to WebP from the panel
guide's renders in `docs/driver/img/`, so they are not kept twice. Manufacturer
*Generic*, as drivers-docs files the other self-built devices. The page is short on
purpose and links the full panel guide.

## Still to do

- Pull requests opened: indilib/indi#2499 (driver) and indilib/drivers-docs#42 (page). Whether Core or 3rd-party is asked in its
  description rather than on the forum first, since CONTRIBUTING's rule is plain.
- After the move, the protocol header in INDI's tree is a third copy the check here
  cannot see: a protocol change means a pull request to INDI too, and INDI's driver
  refuses a firmware with another `PROTOCOL_VERSION`, which is what keeps it safe
  meanwhile.
