# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

"""The firmware pin table must be the board that was actually soldered.

    python3 test_pins.py [wiring.py] [mechanics_esp32.h]

This bench exists because of a defect that is easy to take for a wiring fault.
`diag` reported `TMC2209 over UART:
SILENT`, and EN measured 0 V - driver enabled - while the firmware believes it
leaves EN high at rest. Two symptoms, one cause: the firmware pin table was a
*proposal* written first, the wiring drawing was laid out later and
verified on the real board, and nobody ever put the two side by side. Six
signals out of eight disagreed. The firmware was talking to the driver on D6/D7
while the single wire is on D8/D9, and it was driving the LED on D3 - which is
where EN actually is, which is why EN sat low.

No measurement finds that kind of defect: both halves are self-consistent, both
compile, and the board is right. Only comparing the two tables finds it, so that
is what this bench does - from the drawing the board is soldered from,
mechanics/wheelly-cad/src/wiring.py (cablaggio.py before the move to English), which is also what draws
pcb/en_board-layout.svg and it_disposizione-basetta.svg, and never from a second hand-written copy.

It follows the connections the way the wires do:

  * wires join holes; everything reachable through wires alone is one net;
  * a resistor is NOT a short. R1 would otherwise merge EN with 3V3 and collapse
    the whole logic rail into a single net. A resistor is crossed only on
    purpose, once, and only for the pins the drawing says sit behind one: R2 on
    the UART's TX side, R3 on the LED.

The GPIO numbers behind the D labels are a fact about the XIAO ESP32-S3, not
about this board, so nothing in the repository can derive them. They are held
here a second time, from Seeed's pinout, and compared against the copy in the
firmware: the same trick as the two copies of the naming rule, and for the same
reason - a table that exists once is a table nobody checks.
"""

import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# The drawing's module was cablaggio.py until the project moved to English
#: the English name wins, the old one is still accepted so that a
# checkout from either side of the rename can be compared.
_SRC = os.path.join(ROOT, "mechanics", "wheelly-cad", "src")
WIRING = next((os.path.join(_SRC, n) for n in ("wiring.py", "cablaggio.py")
               if os.path.exists(os.path.join(_SRC, n))),
              os.path.join(_SRC, "wiring.py"))
HEADER = os.path.join(HERE, "..", "wheelly", "mechanics_esp32.h")

# The XIAO ESP32-S3 pinout, from Seeed's own diagram. A second copy on purpose:
# the first one is the `xiao` enum in mechanics_esp32.h, and the two are
# compared below.
GPIO_OF = {
    "D0": 1, "D1": 2, "D2": 3, "D3": 4, "D4": 5, "D5": 6,
    "D6": 43, "D7": 44, "D8": 7, "D9": 8, "D10": 9,
}

# What each firmware pin has to reach on the board. The hole is named the way
# the pinouts in wiring.py name it; the module says which pinout holds it.
EXPECTED = [
    ("sda",     "OTHERS", "SDA"),
    ("scl",     "OTHERS", "SCL"),
    ("step",    "TMC",   "STEP"),
    ("dir",     "TMC",   "DIR"),
    ("en",      "TMC",   "EN"),
    ("uart_rx", "TMC",   "UART"),   # arrives straight
    ("uart_tx", "TMC",   "UART"),   # arrives through R2: the single wire
    ("led",     "OTHERS", "LED +"),
]

# The two pins that share one hole - the single-wire UART - are told apart by
# the resistor: TX goes through R2, RX comes straight. Datasheet page 20, and
# pcb/README.md, the paragraph on R2 sitting on the TX side only.
THROUGH_A_RESISTOR = {"uart_tx": True, "uart_rx": False, "led": True}


class Broken(Exception):
    pass


def load_wiring(path):
    spec = importlib.util.spec_from_file_location("wiring", path)
    if spec is None or spec.loader is None:
        raise Broken("%s is not a Python module this bench can read" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def holes_named(pinout, name):
    return [hole for hole, label in pinout.items() if label == name]


def nets_of_wires(wires):
    """Connected components over wires alone: hole -> the set it belongs to."""
    neighbours = {}
    for wire in wires:
        a, b = wire[0], wire[1]
        neighbours.setdefault(a, set()).add(b)
        neighbours.setdefault(b, set()).add(a)

    nets = {}
    for start in neighbours:
        if start in nets:
            continue
        seen, todo = set(), [start]
        while todo:
            hole = todo.pop()
            if hole in seen:
                continue
            seen.add(hole)
            todo.extend(neighbours.get(hole, ()))
        for hole in seen:
            nets[hole] = seen
    return nets


def resistors(others):
    """The two holes of each resistor, by name: R1, R2, R3."""
    found = {}
    for hole, name in others.items():
        if re.fullmatch(r"R\d+", name):
            found.setdefault(name, []).append(hole)
    for name, holes in found.items():
        if len(holes) != 2:
            raise Broken("%s has %d legs on the drawing, not two" % (name, len(holes)))
    return found


def xiao_pins_in(net, xiao):
    return sorted({xiao[hole] for hole in net if hole in xiao})


def pin_reaching(wiring, nets, hole_name, module, across_a_resistor):
    """Which XIAO pin reaches that hole - optionally across one resistor."""
    pinout = getattr(wiring, module)
    holes = holes_named(pinout, hole_name)
    if len(holes) != 1:
        raise Broken("hole \"%s\" appears %d times in %s" % (hole_name, len(holes), module))
    net = nets.get(holes[0])
    if net is None:
        raise Broken("hole \"%s\" has no wire on it" % hole_name)

    if not across_a_resistor:
        pins = xiao_pins_in(net, wiring.XIAO)
        if len(pins) != 1:
            raise Broken("\"%s\" touches %d XIAO pins: %s"
                         % (hole_name, len(pins), pins or "none"))
        return pins[0]

    # One resistor, on purpose: find the one with a leg in this net, step to its
    # far leg, and look for the XIAO pin over there.
    found = []
    for name, legs in resistors(wiring.OTHERS).items():
        near = [leg for leg in legs if leg in net]
        if not near:
            continue
        far = legs[0] if legs[1] in near else legs[1]
        for pin in xiao_pins_in(nets.get(far, {far}), wiring.XIAO):
            found.append((name, pin))
    if len(found) != 1:
        raise Broken("from \"%s\" across one resistor you reach %d pins: %s"
                     % (hole_name, len(found), found or "none"))
    return found[0][1]


def read_header(path):
    """The `xiao` enum and the Pins defaults, read as text.

    The header sits behind #ifdef ARDUINO, so it cannot be compiled here: it is
    parsed. A pin written as a bare GPIO number instead of a xiao::Dn label is
    rejected rather than ignored, because a bare number is the shape the defect
    had - nobody can compare 43 with a drawing that says D6.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()

    enum_body = re.search(r"namespace\s+xiao\s*\{(.*?)\}\s*//\s*namespace\s+xiao",
                          text, re.S)
    if enum_body is None:
        raise Broken("the header has no `xiao` namespace with the pinout in it")
    gpio = {name: int(value)
            for name, value in re.findall(r"\b(D\d+)\s*=\s*(\d+)", enum_body.group(1))}

    struct_body = re.search(r"struct\s+Pins\s*\{(.*?)\};", text, re.S)
    if struct_body is None:
        raise Broken("the header has no `Pins` struct")
    pins = {}
    for line in struct_body.group(1).splitlines():
        line = line.split("//")[0]
        field = re.search(r"\b(\w+)\s*=\s*([^;]+);", line)
        if field is None:
            continue
        name, value = field.group(1), field.group(2).strip()
        label = re.fullmatch(r"xiao::(D\d+)", value)
        if label is None:
            raise Broken("Pins::%s is \"%s\": pins are written with the name "
                         "printed on the XIAO (xiao::Dn), not with a GPIO number"
                         % (name, value))
        pins[name] = label.group(1)
    return gpio, pins


def run(wiring_path, header_path):
    wiring = load_wiring(wiring_path)
    nets = nets_of_wires(wiring.WIRES)
    header_gpio, pins = read_header(header_path)

    faults = []

    # 1. the two copies of the XIAO pinout
    for name, number in sorted(GPIO_OF.items()):
        if name not in header_gpio:
            faults.append("the header does not say which GPIO %s is" % name)
        elif header_gpio[name] != number:
            faults.append("%s: the header says GPIO %d, Seeed's pinout says %d"
                          % (name, header_gpio[name], number))

    # 2. the firmware drives exactly the signals the drawing wires
    wanted = {name for name, _, _ in EXPECTED}
    if set(pins) != wanted:
        faults.append("Pins has the fields %s, the drawing describes %s"
                      % (sorted(pins), sorted(wanted)))

    # 3. the pin table against the board
    for name, module, hole in EXPECTED:
        if name not in pins:
            continue
        try:
            expected = pin_reaching(wiring, nets, hole, module,
                                    THROUGH_A_RESISTOR.get(name, False))
        except Broken as e:
            faults.append("%s: %s" % (name, e))
            continue
        if pins[name] != expected:
            faults.append("%s: the firmware uses %s, the board carries it to %s (%s)"
                          % (name, pins[name], expected, hole))

    if faults:
        print("### the firmware pin table and the board DO NOT agree")
        for fault in faults:
            print("  ! " + fault)
        print("\nThe board is soldered: the one that is wrong is the firmware.")
        print("The drawing: %s" % os.path.relpath(wiring_path, ROOT))
        return 1

    print("the firmware pin table agrees with the board: %d signals" % len(EXPECTED))
    return 0


if __name__ == "__main__":
    wiring_file = sys.argv[1] if len(sys.argv) > 1 else WIRING
    header_file = sys.argv[2] if len(sys.argv) > 2 else HEADER
    try:
        sys.exit(run(wiring_file, header_file))
    except Broken as fault:
        # A shape this bench cannot read at all is a failure like any other, not
        # a stack trace: it still means firmware and board are not comparable.
        print("### the firmware pin table and the board cannot be compared")
        print("  ! %s" % fault)
        sys.exit(1)
