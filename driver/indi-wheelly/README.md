<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# indi-wheelly — the INDI driver of the wheel

`indi_wheelly_wheel` is an `INDI::FilterWheel` driver for the Wheelly motorised filter wheel.
It translates the firmware's line protocol into INDI properties, and that is all: **the
decisions are taken in the firmware**. Comparing against the tolerances, retrying and
giving the final verdict happen on the XIAO, so the wheel behaves the same when driven by
hand from a serial monitor, and there are no two copies of the same logic to drift apart.

The protocol and the reasoning behind it are in [`firmware.md`](../../firmware.md),
sections 4 and 5. The protocol itself is one header, `firmware/wheelly/wheelly_protocol.h`,
compiled by both the firmware and this driver. The driver compiles its own copy,
`wheelly_protocol.h` in this folder, byte for byte the same: that way this folder
builds on its own, also inside INDI's source tree where `firmware/` does not exist.
`firmware/test/test_driver_standalone.py` (run by `firmware/test/run_all.sh`) fails
while the two copies differ; the firmware's is the one to edit.

## Building

With cmake:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build
```

It needs `libindi` with its headers: on Arch (and so on AstroArch) they are in the
`libindi` package, on Debian and Ubuntu in `libindi-dev`. `CMakeLists.txt` tries
`pkg-config libindi` first and falls back to `find_package(INDI)`. The device name shown
to clients is a cache variable, `-DWHEELLY_DEVICE_NAME=...` (default `Wheelly`), because
the name is a trademark and whoever forks the project must be able to change it in one
place (`TRADEMARK.md`).

Where cmake is missing, one g++ line does the same. This is what
`doc/refresh_panel.sh` runs on AstroArch: `wheelly_config.h` is made from `wheelly_config.h.cmake` with the
version and device name read from `CMakeLists.txt`, then

```sh
g++ -std=c++17 -O2 -Wall -Wextra -Ibuild -I. $(pkg-config --cflags libindi) \
    wheelly.cpp -o build/indi_wheelly_wheel \
    $(pkg-config --libs libindi) -lindidriver
```

That line produces only the binary: the `indi_wheelly.xml` that KStars needs (see below)
is made by cmake from `indi_wheelly.xml.cmake`, and without cmake it has to be filled in
the same way by hand.

Two things that cost half an hour if you do not know them:

- the linker needs **`-lindidriver`**, which `pkg-config --libs libindi` does not return;
  without it the link fails on missing symbols;
- with libindi 2.x the C entry points (`ISGetProperties` and friends) are **not** written
  by hand: a static `std::unique_ptr` to the device is enough, and the framework provides
  them.

Inside INDI's own source tree the driver builds from INDI's CMake, not this file:
[`upstream/`](upstream/README.md) has the lines to add, the `drivers.xml` entry, the code
style INDI checks, and what is left before proposing the driver to INDI.

## Installing and running under Ekos

`cmake --install build` (with `sudo`) installs two files:

| file | what it is for |
|---|---|
| `/usr/bin/indi_wheelly_wheel` | the driver executable |
| `/usr/share/indi/indi_wheelly.xml` | what makes the wheel appear in KStars, under *Filter Wheels* |

Configure with **`-DCMAKE_INSTALL_PREFIX=/usr`**: the cmake default is `/usr/local`, where
INDI does not look, and the result is a silent duplicate with Ekos still using the old
driver. **Restart KStars** after installing: the Profile Editor reads the XML files only at
start-up. Then choose *Wheelly* as the filter wheel of an Ekos profile, or start it by hand
with `indiserver -v indi_wheelly_wheel`. To uninstall, delete the two files.

The executable used to be called `indi_wheelly`: it follows INDI's convention now,
every filter wheel's executable ending in `_wheel`. Installing over an older version
leaves `/usr/bin/indi_wheelly` behind, unused - delete it. Ekos profiles are not
affected: they choose the driver by its name, *Wheelly*, not by its executable.

## How the wheel is found

The wheel is recognised **by its answer, not by the name of the port**. On macOS a name
like `/dev/cu.usbmodem20114301` encodes the USB socket, not the device, and changes when the
plug moves. So `Handshake()` sends `version` and accepts the port only if the answer says
`name=wheelly` with the protocol version the driver was built for.

- **Port filter.** The driver gives INDI the pattern `303a|espressif|wheelly|usbmodem`
  (Espressif's USB vendor id, the vendor name that `/dev/serial/by-id/` uses on Linux, and
  the macOS port name), so INDI proposes the XIAO's port without the user choosing it.
- **Auto search.** With INDI's standard *Auto Search* on, when the saved port does not
  answer, the other serial ports are tried until a Wheelly answers.
- **Serial number.** Every wheel reports a serial number made by the firmware from the
  chip's MAC address. The driver saves it in the profile's configuration
  (`WHEELLY_FIRMWARE`), and `Connect()` makes two passes: first it accepts **only the
  wheel of this profile**, so with two wheels plugged in each profile finds its own; if that
  wheel is on no port (a replaced board, a wheel left at home) it tries again accepting any
  Wheelly, says so in the log, and adopts the new serial number.
- The **number of slots** comes from the wheel at connection (`slots=` in the `version`
  answer); the driver sizes `FILTER_SLOT`, the names, angles and trims to it.

## Language

The driver speaks English, as every INDI driver: the labels and the log messages are
written in the code where they are used. The guides are bilingual (below); the panel is
not, because INDI takes into its tree only English drivers without translation code, and
one driver, the same file here and there, is simpler to keep right than two. The reasons,
and the bilingual driver it replaced, are in `firmware.md`, section 13.

## The bench test

```sh
python3 driver_bench.py [path/to/indi_wheelly_wheel] [path/to/simulator]
```

It starts the Python simulator (`firmware/simulator/wheelly_sim.py`) on a fake serial port
(a pty), runs the **real compiled driver** under its own `indiserver`, and talks to it with
the same INDI XML that Ekos uses: what the test sees is what Ekos would see. The defaults
are `build/indi_wheelly_wheel` and the simulator; the second argument can instead be the
**firmware compiled for the PC** (`firmware/test/firmware_bench.cpp`), and running the test
against both checks that the two halves of the project agree. It checks, among other
things, which **tab** each property lands in (only visible in the XML: `indi_getprop` does
not show groups), that the driver speaks English even under an Italian `LANG`, that a filter change
succeeds, that an invalid filter name is refused with an explanation, and that a wheel
that never arrives puts `FILTER_SLOT` in `Alert`, which is what stops an Ekos sequence.

It runs even while KStars has a session open: `indiserver` always opens a local socket at a
hard-wired path (`/tmp/indiserver`) that Ekos in *Local* mode already holds, so the test
passes `-u` with a socket of its own, and a free TCP port and pty of its own per run.

To look at it with your own eyes instead:

```sh
../../firmware/simulator/wheelly_sim.py --pty --link /tmp/wheelly &
indiserver -v ./build/indi_wheelly_wheel
```

then connect KStars to `localhost`, port 7624, and set `/tmp/wheelly` as the port (INDI's
port search never lists a pty). The simulator has switches to break things on purpose
(`--slip`, `--sensor-silent`, `--no-magnet`, `--drift`, ...): see `--help`.

## When something goes wrong

- **Calibration and Diagnostics → Hardware check** sends `diag` and writes the answers in
  the log: whether the AS5600 answers on I2C, whether it sees the magnet, with which field
  flags and magnitude, and whether the motor driver answers on its UART, by the name the chip
  itself reports. Ask it first: a loose wire on the motor driver looks like "the motor does
  not turn" and sends you looking in ten wrong places.
- **Options → Debug**, then the **Driver Debug** level: every line exchanged with the XIAO,
  both ways, goes to the log, with nothing to rebuild. A dedicated level added with
  `addDebugLevel("Protocol Verbose", ...)` looks right and does **not** work on libindi 2.2:
  it lands in slot `DBG_EXTRA_2`, but `DEBUG_LEVEL` publishes only five levels and stops at
  `DBG_EXTRA_1`, so the level existed and its switch did not.

## The panel

The full guide to every property, tab by tab, with pictures of the real panel, is in
[`docs/driver/`](../../docs/driver/README.md) (English) and
[`docs/driver/it/`](../../docs/driver/it/README.md) (Italian). It is generated from the panel
the driver really declares: after changing a property, capture it again with
`doc/refresh_panel.sh` (see `doc/README.md`).

## Where it is meant to end up

INDI's `CONTRIBUTING` says that a driver with no external dependencies belongs in the
**main** repository, in `drivers/filter_wheel/`, where integrating it is four lines of
CMake and an entry in `drivers.xml`, not in `indi-3rdparty`. The `CMakeLists.txt` here
builds it on its own, for now. Whether to propose it upstream is still open (`firmware.md`,
section 14).
