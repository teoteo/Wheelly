#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

# Compile and upload a sketch to the ESP32, then open the serial monitor.
#
#     ./flash.sh                         wheelly, port found automatically
#     ./flash.sh wheelly                 the same, spelled out
#     ./flash.sh air_gap_test            the air-gap test, on the WROOM-32
#     ./flash.sh air_gap_test /dev/cu.usbserial-0001    port given by hand
#     ./flash.sh -m                      monitor only, no upload
#     ./flash.sh -c                      compile only, no board needed
#
# Two machines, two arduino-cli, and the script finds its own.
#
# On the Mac it uses the one INSIDE the Arduino IDE: nothing else to install,
# and the ESP32 core is the same one the IDE sees - if there were two, a defect
# could show up in the IDE and not here, or the other way round.
#
# On the Raspberry it uses the system arduino-cli, installed with
# esp32 core 3.3.11, i.e. THE SAME VERSION AS THE MAC. It was put there because
# otherwise testing the motor meant taking the board off the wheel and carrying
# it to the Mac for every upload.
set -e
cd "$(dirname "$0")"

CLI_IDE="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
if [ -x "$CLI_IDE" ]; then
    CLI="$CLI_IDE"
    # The IDE's configuration: that is where the esp32 core URL and the
    # libraries folder the IDE uses are set.
    CFG_ARG="--config-file $HOME/.arduinoIDE/arduino-cli.yaml"
elif command -v arduino-cli > /dev/null 2>&1; then
    CLI="$(command -v arduino-cli)"
    CFG_ARG=""        # the system one already has its own configuration
else
    echo "arduino-cli not found: neither the Arduino IDE in /Applications nor one in the PATH."
    exit 1
fi
BAUD=115200

# The board depends on the sketch: the real firmware runs on the XIAO ESP32-S3,
# the air-gap test on the WROOM-32 on the bench. The wrong board gives no clear
# error - the upload succeeds and then nothing starts - so the script chooses
# instead of leaving it to whoever remembers.
board_for() {
    case "$1" in
        air_gap_test) echo "esp32:esp32:esp32" ;;
        *)            echo "esp32:esp32:XIAO_ESP32S3" ;;
    esac
}

monitor_only=no
compile_only=no
if [ "$1" = "-m" ]; then monitor_only=yes; shift; fi
if [ "$1" = "-c" ]; then compile_only=yes; shift; fi
SKETCH="${1:-wheelly}"
FQBN=$(board_for "$SKETCH")
PORT="$2"

echo "sketch: $SKETCH   board: $FQBN"

if [ "$compile_only" = "yes" ]; then
    exec "$CLI" $CFG_ARG compile --fqbn "$FQBN" --warnings all "$SKETCH"
fi

if [ -z "$PORT" ]; then
    # USB-serial ports are named after the chip on the board - CP2102, CH340,
    # or native USB - and after the system: /dev/cu.* on macOS, /dev/ttyACM*
    # on Linux for the ESP32-S3's native USB and /dev/ttyUSB* for converters.
    PORT=$(ls /dev/cu.usbserial-* /dev/cu.wchusbserial* /dev/cu.SLAB_USBtoUART* \
              /dev/cu.usbmodem* /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | head -1)
fi
[ -n "$PORT" ] || { echo "No port found: plug in the ESP32 (and see 'ls /dev/cu.*')."; exit 1; }
echo "port: $PORT"

if [ "$monitor_only" = "no" ]; then
    "$CLI" $CFG_ARG compile --fqbn "$FQBN" "$SKETCH"
    # If the upload does not start, hold BOOT until it says "Connecting...",
    # then release it.
    "$CLI" $CFG_ARG upload --fqbn "$FQBN" -p "$PORT" "$SKETCH"
fi

echo "monitor at $BAUD - ctrl-C to quit"
exec "$CLI" $CFG_ARG monitor -p "$PORT" -c baudrate=$BAUD
