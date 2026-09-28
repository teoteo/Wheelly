<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# Licensing

Wheelly is released under permissive licences. Anyone may use, modify and
redistribute it, for any purpose including commercial, provided the copyright
notice is kept. Full texts are in [`LICENSES/`](LICENSES/).

| Part of the project | Licence | Why |
|---|---|---|
| `firmware/` — software | **MIT** | short, permissive, universally understood |
| `driver/` — the INDI driver | **LGPL-2.1-or-later** | the licence of INDI itself, so the driver can be carried in INDI's tree unchanged. Still allows commercial use; changes to the driver itself are shared. `wheelly_protocol.h` in it stays **MIT**: a copy of the firmware's header |
| `mechanics/` — CAD and hardware design | **CERN-OHL-P-2.0** | MIT is a *software* licence; hardware needs terms that speak of designs and manufacturing. `-P` is the permissive variant |
| documentation in the repository root | **CC-BY-4.0** | attribution only |

Every file carries an `SPDX-License-Identifier` header, so the licence travels
with the file even when it is moved or copied. The rule is simple: **the licence
follows the directory**. `tools/spdx_headers.py` applies it and is idempotent —
run it after adding files.

## Dependencies: one obligation survives

Two LGPL-2.1 libraries are used. The LGPL does **not** impose its licence on code
that merely links against it; what it requires is **relinkability**, so that
whoever receives a binary can replace the library with a modified version.

| Dependency | Licence | Enters through |
|---|---|---|
| [libindi](https://github.com/indilib/indi) | LGPL-2.1-or-later | `driver/` derives from `INDI::FilterWheel` and links `-lindidriver` |
| [arduino-esp32](https://github.com/espressif/arduino-esp32) | LGPL-2.1 | `firmware/`, through `Preferences.h` and `Wire.h` |

Dynamic linking, or shipping the object files needed to relink, satisfies this.
Worth knowing before shipping a closed binary, not after.

The other firmware libraries are permissive: TMC2209 (BSD-3-Clause), AS5600
(MIT), FastAccelStepper (MIT).

## Trademark: the name and the logo are not open

A permissive licence covers the *work*, not the *name*, and none of the three
licences above grants any right in a mark — MIT, CC-BY-4.0 and CERN-OHL-P-2.0
all leave trademarks out on purpose. So the design can stay open while the name
stays reserved: the two are independent, and this is the usual arrangement for
open hardware.

What that means in practice is written in [`TRADEMARK.md`](TRADEMARK.md), in
plain terms: what anyone may do without asking, what needs permission, and how
to rename the device in one command if you fork it.

Two consequences inside this repository:

| | |
|---|---|
| `brand/` | the **one exception** to "the licence follows the directory". Logo files are `LicenseRef-Wheelly-Brand`, all rights reserved, and `tools/spdx_headers.py` knows it |
| `driver/indi-wheelly` | the name reaches the user in **one place**, the CMake variable `WHEELLY_DEVICE_NAME`. A fork renames with `-DWHEELLY_DEVICE_NAME=...` and the mark is gone from the device name, the INDI driver list and the manufacturer field |

Nothing is registered. A search of TMview — the database EUIPO and the Italian
UIBM both feed — found **no "Wheelly" mark in class 9**, the class this
instrument and its software belong to, either as an EU mark or an Italian one.
The name is live in class 30 (confectionery, an unrelated field) and an old
registration in classes 10 and 12 has expired.

## Sponsorship

Money and licence are independent: a permissive licence does not stop anyone
from supporting the project, and support does not buy anything the licence does
not already give. Wheelly asks through **GitHub Sponsors**, on the repository
itself — the invitation is in [`README.md`](README.md) and at the foot of the
assembly guide.

Nothing is held back for sponsors: there is no paid version, no private
repository and no part of the documentation behind a paywall. What sponsorship
buys is time, filament and the parts that get printed three times before they
fit.

## Not legal advice

This is the standard arrangement for a project that mixes software and hardware.
The one point that would deserve a lawyer, should commercialisation become
concrete, is the relationship with libindi: subclassing a class from an LGPL
library sits closer to the line than plain linking does.
