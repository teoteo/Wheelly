#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Capture the INDI panel the driver really declares, in English and Italian,
# and bring it back into the repository as doc/panel_en.xml and panel_it.xml -
# the source of the panel guide (docs/driver/).
#
# WHY ON ASTROARCH: the driver builds only there (libindi's headers are not on
# the Mac). Nothing is installed and nothing outside /tmp is touched: the
# driver and the simulator are copied into /tmp/wheelly-panel, built there,
# run under an indiserver of their own (driver_bench.py's bench) and left.
#
#     doc/refresh_panel.sh [user@host]
#
# Run it again whenever a property of the driver changes: the build's check
# (check_panel_guide.py) says so when wheelly.cpp names a property the
# captured XML does not have.
#
# RUN IT WITH A WHEEL (or any serial device) PLUGGED INTO ASTROARCH: libindi
# defines SYSTEM_PORTS only when it finds a port, and the bench's fake port
# is a pty it does not list. Captured with no port present, SYSTEM_PORTS
# vanishes and the build fails on the guide's text for it; such a capture
# needs the previous SYSTEM_PORTS spliced back.
set -e
HOST="${1:-astronaut@astroarch.local}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
REMOTE=/tmp/wheelly-panel

ssh "$HOST" "rm -rf $REMOTE && mkdir -p $REMOTE/driver $REMOTE/firmware"
rsync -a --exclude build --exclude doc/.venv "$ROOT/driver/indi-wheelly" "$HOST:$REMOTE/driver/"
rsync -a --exclude .pio --exclude __pycache__ "$ROOT/firmware/simulator" "$ROOT/firmware/wheelly" \
      "$HOST:$REMOTE/firmware/"
# AstroArch has g++ and libindi but no cmake: the driver is built with one g++
# line, and wheelly_config.h is made from wheelly_config.h.cmake with the values CMakeLists.txt
# sets - read from it, not written again here - so nothing has to be installed.
MAJOR=$(sed -n 's/^set(WHEELLY_VERSION_MAJOR \([0-9]*\)).*/\1/p' "$HERE/../CMakeLists.txt")
MINOR=$(sed -n 's/^set(WHEELLY_VERSION_MINOR \([0-9]*\)).*/\1/p' "$HERE/../CMakeLists.txt")
NAME=$(sed -n 's/^set(WHEELLY_DEVICE_NAME "\([^"]*\)".*/\1/p' "$HERE/../CMakeLists.txt")
ssh "$HOST" "cd $REMOTE/driver/indi-wheelly && mkdir -p build \
  && sed -e 's/@WHEELLY_VERSION_MAJOR@/$MAJOR/' -e 's/@WHEELLY_VERSION_MINOR@/$MINOR/' \
         -e 's/@WHEELLY_DEVICE_NAME@/$NAME/' \
         -e 's/^#cmakedefine01 WHEELLY_ITALIAN$/#define WHEELLY_ITALIAN 1/' \
         wheelly_config.h.cmake > build/wheelly_config.h \
  && g++ -std=c++17 -O2 -Wall -Wextra -Ibuild -I. \$(pkg-config --cflags libindi) \
         wheelly.cpp translations.cpp translations_it.cpp plot.cpp -o build/indi_wheelly \
         \$(pkg-config --libs libindi) -lindidriver \
  && python3 doc/capture_panel.py $REMOTE/out"
scp -q "$HOST:$REMOTE/out/panel_en.xml" "$HOST:$REMOTE/out/panel_it.xml" "$HERE/"
echo "panel captured into $HERE/panel_en.xml and panel_it.xml"
