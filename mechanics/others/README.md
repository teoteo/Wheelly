<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# The makers' models of the bought parts

The CAD build places the real motor and the real electronics in the model, from
the makers' own 3D files. **They are not shipped with Wheelly**: they belong to
their makers, and none of them comes with a licence that allows redistributing
it. Download them yourself and save them **in this folder, under exactly the
names below** — the build opens them by name.

**Printing Wheelly does not need them**: the printable STEP and STL files are
attached to each release. They are needed only to regenerate the CAD
(`mechanics/wheelly-cad/build.py`), and without them nothing is generated, not
even the printed parts or the 2D drawings: the box takes the hatch and the arc
under the motor from the motor's model. `python3 mechanics/wheelly-cad/src/vendor_files.py` lists what
is there and what is missing, and the build says the same before starting.

| Save as | Part | Where to get it | Used for |
|---|---|---|---|
| `14HS10-0404S.STEP` | StepperOnline 14HS10-0404S, NEMA14 motor | the download area of the [product page](https://www.omc-stepperonline.com/nema-14-bipolar-1-8deg-14ncm-20oz-in-0-4a-12v-35x35x26mm-4-wires-14hs10-0404s) on omc-stepperonline.com | the box (hatch and arc under the motor), the 2D assembly view, the assembly, the interpenetration checks |
| `XIAO-ESP32S3 v2.step` | Seeed Studio XIAO ESP32S3 | Seeed Studio's downloads for the board, e.g. on the [Wio-SX1262 with XIAO ESP32S3](https://www.seeedstudio.com/Wio-SX1262-with-XIAO-ESP32S3-p-5982.html) page | the electronics envelopes, the USB slot in the box head |
| `TMC2209.step` | stepstick driver module (the prototype uses a TMC2208 in the same format) | [GrabCAD: TMC2209 stepper driver](https://grabcad.com/library/tmc2209-stepper-driver-1) (free account) | the electronics envelopes, the driver's pin rows |
| `GX12-2P.step` | GX12 2-pin aviation socket | [GrabCAD: GX12 2–7 pin circular aviation socket](https://grabcad.com/library/gx12-2-3-4-5-6-7pins-circular-aviation-socket-1/files), the 2-pin one | the electronics envelopes in the box head |

Why none of them is here: the motor and the XIAO come from the makers' download
areas, under their terms of use; the GrabCAD models carry their uploaders' terms,
which do not allow redistribution. None is under an open licence that would let
this project republish it.

The dimensions the design depends on are **not** taken blindly from these files:
where it matters they were checked with a calliper on the real parts, and the
parameters say so (origin `M`). A different model of the same part should give
the same result; if a check fails after you swap a file, compare the model with
your part before changing the design.
