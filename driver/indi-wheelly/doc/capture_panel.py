#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Capture the panel the driver really declares, as INDI XML.

WHY FROM THE DRIVER AND NOT FROM THE SOURCE. The panel guide has to follow
the driver by itself when a command is added or removed.
Reading wheelly.cpp would describe what the code seems to declare; running
the compiled driver under indiserver, connected to the simulator, gives what
Ekos actually receives - properties defined only once connected included,
with their groups, labels, permissions and rules, in declaration order.

It uses the same bench as driver_bench.py (simulator on a fake serial port,
indiserver with a home of its own, so the real configuration is not touched).

    python3 capture_panel.py OUT_DIR [path/to/indi_wheelly_wheel] [path/to/simulator]

Writes OUT_DIR/panel_en.xml: every def*Vector the
driver sends, in order, then the set*Vector that follow the connection (the
values the panel shows once connected).
"""
import os
import sys
import time

out_dir = sys.argv[1]
# driver_bench reads the driver and simulator paths from its own argv
sys.argv = [sys.argv[0]] + sys.argv[2:]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import driver_bench as P                                    # noqa: E402


# The serial ports INDI lists (SYSTEM_PORTS) are those of the machine the
# capture runs on, and on Linux a USB device's name carries its serial number -
# an ESP32-S3 its MAC address (/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_
# debug_unit_E0:72:...). The capture is published with the guide, so any
# MAC-shaped or long hex serial in a by-id name is replaced with a placeholder
# (an unfiltered capture puts the device's MAC address in the repository).
# The guide draws the list, not the numbers.
def anonymise(raw):
    import re
    raw = re.sub(rb"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", b"00:00:00:00:00:00", raw)
    return re.sub(rb"(serial_debug_unit_|usb-[A-Za-z0-9_]+_)([0-9A-Fa-f]{12,})",
                  lambda m: m.group(1) + b"0" * len(m.group(2)), raw)


class Recorder(P.Client):
    """The test client, keeping the raw stream as well."""

    def __init__(self, port):
        self.raw = bytearray()
        super().__init__(port)

    def pump(self, seconds=0.5):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            try:
                data = self.s.recv(65536)
            except P.socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            self.raw += data
            self.parser.feed(data)
            for _, element in self.parser.read_events():
                self._collect(element)


def capture(xml_file):
    bench = P.Bench()
    c = Recorder(P.INDI_PORT)
    try:
        result = bench.connect(c)
        if result != "Ok":
            raise SystemExit("the driver did not connect to the simulator (%s)" % result)
        # The bench connects with Auto Search off, so that a failed connection
        # never tries a real wheel's port (driver_bench.Client.set_switch);
        # connected, it is put back as INDI makes it, or the guide would draw
        # it off
        c.set_switch("DEVICE_AUTO_SEARCH", "INDI_ENABLED", ["INDI_DISABLED"])
        c.pump(3.0)
    finally:
        c.close()
        bench.close()
    with open(xml_file, "wb") as f:
        f.write(b"<indi>\n" + anonymise(bytes(c.raw)) + b"\n</indi>\n")
    return len(c.props)


if __name__ == "__main__":
    os.makedirs(out_dir, exist_ok=True)
    n = capture(os.path.join(out_dir, "panel_en.xml"))
    print("%d properties" % n)
