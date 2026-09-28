<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Proposing the driver to INDI

What is ready, and what is left, for proposing `indi_wheelly` for inclusion in INDI
itself. Nothing here has been sent anywhere: no fork, no pull request, no forum post.
Everything below was checked against **indilib/indi master `224173c`**.

## Which repository

INDI's [`CONTRIBUTING.md`](https://github.com/indilib/indi/blob/master/CONTRIBUTING.md)
decides it by dependencies: a driver that builds with only what INDI Core already has
goes in **indilib/indi**, under `drivers/<category>/`; one that needs anything else goes
in indi-3rdparty. This driver needs libindi and nothing else, so it is a Core driver, in
`drivers/filter_wheel/`. The maintainers have the last word, which is why the ROADMAP
says to ask on the [INDI forum](https://indilib.org/forum.html) first.

## What is copied, and where

Into `drivers/filter_wheel/wheelly/` of INDI's tree:

| file | |
|---|---|
| `wheelly.cpp`, `wheelly.h` | the driver |
| `translations.cpp`, `translations.h` | the English texts, by key |
| `plot.cpp`, `plot.h` | the magnet sweep plot |
| `wheelly_protocol.h` | the protocol, byte for byte `firmware/wheelly/wheelly_protocol.h` |
| `wheelly_config.h.cmake` | version, device name, `WHEELLY_ITALIAN` |

Not copied: `translations_it.cpp` (INDI's drivers are English), this folder's own
`CMakeLists.txt` and `indi_wheelly.xml.cmake` (INDI builds and lists the driver its own
way, below), `driver_bench.py` and `doc/` (they need the simulator in `firmware/`, which
stays here), and `upstream/`.

A subfolder, not files loose in `drivers/filter_wheel/`, because the driver has seven
files and two of them have names (`translations`, `plot`) too generic for a folder shared
by fifteen drivers. INDI already does it this way for the Shelyak driver in
`drivers/spectrograph/shelyak/`: sources in a subfolder, named from the category's
`CMakeLists.txt`, no `CMakeLists.txt` of their own.

The folder builds on its own: nothing in it includes from outside
(`firmware/test/test_driver_standalone.py` fails if something does, or if the two copies
of the protocol header differ).

## CMake and drivers.xml

- [`CMakeLists-indi.txt`](CMakeLists-indi.txt): the lines to append to
  `drivers/filter_wheel/CMakeLists.txt`. Modelled on the filter wheels already there
  (`xagyl_wheel`, `rasa_filtercube`: one executable, linked to `indidriver`, installed to
  `bin`) and on Shelyak for the subfolder. It sets `WHEELLY_ITALIAN` OFF.
- [`drivers-xml-entry.xml`](drivers-xml-entry.xml): the `<device>` to add in the
  *Filter Wheels* group of INDI's `drivers.xml`, `manufacturer="DIY"` as INDI files
  MyFocuserPro2, ESP32go and the other self-built devices.

**Tried** on a Raspberry Pi (Arch Linux ARM, gcc): INDI master
cloned in `/tmp`, the seven files and the CMake lines added, `make indi_wheelly` - which
builds `libindidriver` from the same tree first (2 min 12 s with `-j3`). INDI compiles
its drivers with `-Wall -Wextra -Werror`: the driver built with **no warning**, linked to
the tree's own `libindidriver.so.2`, and under `indiserver`, against the simulator, it
connected, showed English labels under `LANG=it_IT.UTF-8` and no Language switch. One quirk
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
(astyle 3.6.18, `brew install astyle`). Run it again on any C++ file of the
driver after editing it.

## Language

INDI's drivers are English. `WHEELLY_ITALIAN` (CMake option, ON in this repository) is
what lets the same folder serve both without a fork: OFF, `translations_it.cpp` is not
compiled, the driver speaks English whatever the system language, and the Language
switch is not defined. Both ways were built and tried; the English-only
binary, started under `LANG=it_IT.UTF-8`, showed English labels and no Language switch.

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

## Still to do before proposing

- **`drivers/filter_wheel/doc/wheelly/index.md`**: CONTRIBUTING requires it (overview,
  features, installation, configuration, usage and tips, screenshots). The material is
  in the panel guide, `docs/driver/`; it has to be written in INDI's shape, in English.
- Ask on the INDI forum whether Core or 3rd-party, then fork and open the pull request.
- After the move, the protocol header in INDI's tree is a third copy the check here
  cannot see: a protocol change means a pull request to INDI too, and INDI's driver
  refuses a firmware with another `PROTOCOL_VERSION`, which is what keeps it safe
  meanwhile.
