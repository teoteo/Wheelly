#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

# All the firmware tests, one after the other. No hardware needed.
#
#     ./run_all.sh
#
# Four benches, from the smallest to the largest:
#
#   0. test_pins.py          the firmware's pins against the real board, i.e.
#                            against the drawing the board is soldered from. It comes
#                            first because it is the only one not meant to find
#                            a logic error: it finds two halves that do not
#                            describe the same hardware, and until they agree
#                            the other tests pass anyway and mean nothing.
#   1. test_protocol.cpp     the naming rule and the constants, on the shared
#                            header that ends up on the microcontroller
#   2. the SIMULATOR         the whole dialogue, faults included, plus the
#                            comparison between the two copies of the naming rule
#   3. the REAL FIRMWARE     the very same tests as step 2, but against the
#                            Wheel and Dialog that end up on the XIAO,
#                            compiled for the PC with fake mechanics underneath
#
# Step 3 matters most: if the firmware and the simulator did not behave the
# same way, one of them would be wrong and nobody would notice until the wheel
# is assembled.
set -e
cd "$(dirname "$0")"

CXX="${CXX:-c++}"
BENCH=/tmp/wheelly_bench

echo "### the firmware's pins against the board"
python3 test_pins.py
echo
echo "### the air-gap test bench texts: en and it, every key"
python3 test_gap_page.py
echo

echo "### the units between wheel.cpp and the XIAO's mechanics"
python3 test_units.py
echo

echo "### the driver folder stands on its own: its copy of the protocol header"
python3 test_driver_standalone.py
echo

./test_protocol.sh

echo
echo "### the Python simulator"
python3 test_simulator.py

echo
echo "### the LED's Morse, unit by unit, on the firmware's code"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o /tmp/wheelly_test_morse \
       test_morse.cpp ../wheelly/wheel.cpp ../wheelly/dialog.cpp
/tmp/wheelly_test_morse

echo
echo "### the LED pulsing during a position change, with fake time"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o /tmp/wheelly_test_pulse \
       test_pulse.cpp ../wheelly/wheel.cpp ../wheelly/dialog.cpp
/tmp/wheelly_test_pulse

echo
echo "### the LED's alarm signals: position, drift, magnet; silent with the LED off"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o /tmp/wheelly_test_alarms \
       test_alarms.cpp ../wheelly/wheel.cpp ../wheelly/dialog.cpp
/tmp/wheelly_test_alarms

echo
echo "### the AS5600 field flags reach status and diag as the chip reports them"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o /tmp/wheelly_test_field \
       test_field.cpp ../wheelly/wheel.cpp ../wheelly/dialog.cpp
/tmp/wheelly_test_field

echo
echo "### the motor driver still holds its setup: each witness of a reset alone"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o /tmp/wheelly_test_driver_check \
       test_driver_check.cpp
/tmp/wheelly_test_driver_check

echo
echo "### the sweep viewer: same-angle samples merged, a minimum window"
node test_sweep_viewer.mjs

echo
echo "### the real firmware, compiled for this computer"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 -o "$BENCH" \
       firmware_bench.cpp ../wheelly/wheel.cpp ../wheelly/dialog.cpp
python3 test_simulator.py "$BENCH"
