<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Roadmap and known issues

Where Wheelly stands, what is known not to be right yet, and which numbers in the
design are still estimates. Updated at each release.

## Status — 0.1

One prototype is built and in use, on a five-position StarDikor wheel for 2-inch
filters, driven from Ekos through the INDI driver:

- moves between filters at every speed tried from 100 to 1000 full steps/s, with
  an error under 0.15° on four slots out of five;
- the motor-to-disc ratio measured on the wheel (≈ 2.94 ± 0.03) agrees with the
  one the CAD declares (2.9) within 2 %, and the firmware learns it in use;
- with the wheel's own detent removed and no holding current, the disc holds its
  position at rest.

## Known issues

- **One slot of the prototype lands ~1° off** at almost every speed, the others
  within 0.15°. Not understood yet (a hard spot on the disc? the field?).
- **Sensor magnitude after reassembly** is lower than on the test bench (370–600
  against 750–900): the sensor bracket's height after remounting has to be
  checked. The wheel works, but with less margin above the "magnet too weak"
  threshold (~350).
- **Language switch in the INDI panel** takes effect only after INDI is stopped
  and started again.
- **One driver message is longer than INDI's 255 characters** (the one after a
  change of the number of slots) and gets cut.
- **The magnet sweep** should be redone with the current firmware on the real
  wheel.

## Numbers that are estimates, not measurements

The parameters say for each dimension whether it is measured (`M`), chosen (`S`),
derived (`D`) or from a catalogue (`R`). These ones matter and are not measured
yet:

- **The filter disc of the reference wheel**: M48 × 0.75 holes, the web between
  two holes ~6.5 mm (estimated by hand), from which the radius of the filter
  circle — and so the optical axis — is derived (45.67 mm). To be measured with a
  calliper: the web, the hole, the rim, and the Ø of the body's optical hole.
- **The angle of the number window in the metal body** (`Ang_window_body`,
  ~6.5°, estimated from a photo). The collar's window follows it.
- **The height of the JST XH connectors** with the cable plugged in, and the
  distance of the perfboard's first column from its edge.

## Planned

- **The INDI driver distributed with INDI itself.** It depends on nothing but
  libindi, and INDI's contribution rules put such drivers in the main
  repository ([indilib/indi](https://github.com/indilib/indi)); vendor-SDK
  drivers go to [indi-3rdparty](https://github.com/indilib/indi-3rdparty). The
  maintainers decide which, asked first on the INDI forum. Once it is merged,
  it ships with `libindi` (already installed on AstroArch, StellarMate and the
  Ubuntu PPA) and installing the driver means nothing at all instead of
  building it from source. Until then,
  [`driver/indi-wheelly/README.md`](driver/indi-wheelly/README.md) is the way.

## Ideas, not promised

- The speed test (`firmware/speed_test.py`) as a button in the driver's
  calibration tab.
- An **ASCOM / Alpaca** driver, if there is demand: the serial protocol is
  already free of INDI's vocabulary ([`firmware.md`](firmware.md)).
