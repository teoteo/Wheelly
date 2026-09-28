# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The connections of the board, hole by hole.

The wires of the wiring diagram come from here (pcb/en_board-layout.svg and
it_disposizione-basetta.svg, second view). The positions of the components
are in electronics.py; here there are the pinouts of the two modules and the
list of wires, with the star-ground rule: a single node, the negative of C1,
and from there one wire per branch.

THE PINOUTS, seen from the component side with the head (the USB) on the left.

  XIAO. The maker draws it with the USB at the top: on the left, from the USB
  down, D0..D6; on the right 5V, GND, 3V3, D10, D9, D8, D7. Turned with the USB
  on the left, the D0..D6 row ends up AT THE BOTTOM (R8) and the other at the
  top (R2). CHECKED ON THE REAL XIAO, on a photo of the solder side. From
  below, with the USB at the top, D0..D6 is on the
  RIGHT; the view from below is mirrored, so from the component side that row
  is on the LEFT, and that is what the maker says. Turned with the USB on the
  left, it ends up at the bottom: row 08 below is right. The old layout
  (pcb/superato/), which had D0..D6 at the top, was the wrong one.
  The bottom of that view is the WHEEL AXIS side of the box - and the model
  used to have it on the back side: the layout drawing drew s
  growing downwards, a mirror of the view from above, so drawing and board
  agreed while the model was the mirror of both. Found because the XIAO's
  USB socket stood one hole off its slot (electronics.py, the grid).

  TMC2209. StepStick pinout, with pin 1 (EN) and VMOT on the C1 side: control
  row at the top, power row at the bottom (R8), the same orientation as the
  old layout.

  THE TWO MODULES DO NOT HAVE THE SAME WIDTH (it showed on the regenerated
  wiring drawings). The XIAO has its rows 15.24 apart, six
  holes: R2 and R8. The TMC2209 is a StepStick: rows 12.7 apart, FIVE holes -
  measured on the maker's STEP (others/TMC2209.step), pins at y +-6.35. Until
  then both were drawn on R2 and R8, and the driver sat between the holes.
  Written here once, with the pinout; the position of the module, its sockets
  and the drawings follow from it.

  WHICH FIVE ROWS: the driver is aligned with the XIAO ON THE RESISTORS'
  SIDE, not on the side of J4 - control row on R2, the same row as the XIAO's
  top row, power row on R7. Beware the two row names: the printed grid and the
  drawings name the rows 10 - r, so printed row 03 is R7 and printed row 08 is
  R2. Reading "row 03" as R3 once put the driver on R3 and R8, one row towards
  J4. C1 moves up with the power row: on the reference board it is on S03/S02
  (column 18, rows R7 and R8), minus on row 02; C2 stays on S05/S04, minus on
  row 04.
"""

R_XIAO = (2, 8)          # the XIAO's two rows of pins
R_DRIVER = (2, 7)        # the driver's: control, power (printed rows 08 and 03)

XIAO = {  # (column, row): name
    (0, 2): "5V", (1, 2): "GND", (2, 2): "3V3", (3, 2): "D10", (4, 2): "D9", (5, 2): "D8", (6, 2): "D7",
    (0, 8): "D0", (1, 8): "D1", (2, 8): "D2", (3, 8): "D3", (4, 8): "D4", (5, 8): "D5", (6, 8): "D6",
}
TMC = {
    (8, 2): "DIR", (9, 2): "STEP", (10, 2): "SLP", (11, 2): "RST", (12, 2): "UART",
    (13, 2): "MS2", (14, 2): "MS1", (15, 2): "EN",
    (8, 7): "GND", (9, 7): "VDD", (10, 7): "A2", (11, 7): "A1", (12, 7): "B1",
    (13, 7): "B2", (14, 7): "GND", (15, 7): "VM",
}
# the pinouts sit on the rows declared above, and only on those
assert {r for _, r in XIAO} == set(R_XIAO), "XIAO pinout off its rows"
assert {r for _, r in TMC} == set(R_DRIVER), "TMC pinout off its rows"


def pin(pinout, name):
    """Where a pin is, by its name: the drawings ask for "STEP" and not for a
    hole, so that moving a module does not leave them pointing at the old one
    (the wiring drawings kept the driver on row 2 after it moved to row 3, and
    drew its pins as "?")."""
    found = [p for p, n in pinout.items() if n == name]
    if len(found) != 1:
        raise KeyError("pin %r: %d matches" % (name, len(found)))
    return found[0]


OTHERS = {  # the leads of the components, by name
    # The positions are the ones CHECKED on the real board of the reference
    # build (see electronics.COMPONENTS): the connectors did not fit where the
    # design had put them, and almost all of them moved. C1 and the 12 V
    # terminal block are the only ones left where they were - C1 because the
    # constraint of the VM-GND loop comes before the envelope, so it stays
    # close to the driver's pins, and C2 moved instead.
    (18, 7): "C1 +", (18, 8): "C1 −",
    (18, 5): "C2 +", (18, 6): "C2 −",
    (23, 3): "A+", (23, 4): "A−", (23, 5): "B+", (23, 6): "B−",
    (20, 0): "12V +", (20, 2): "12V −",
    (10, 9): "SDA", (11, 9): "SCL", (12, 9): "VCC", (13, 9): "GND",
    (3, 0): "LED +", (4, 0): "LED −",
    (12, 1): "R1", (15, 1): "R1", (11, 0): "R2", (15, 0): "R2",
    (6, 0): "R3", (10, 0): "R3",
}

NODE = (18, 8)   # the negative of C1: the only point where the grounds touch

# (from, to, net[, waypoints]). The nets decide the colour. The waypoints are
# intermediate points, at half a row too, for the wires that would otherwise
# run over a row of pins and look connected to all of them: they serve the
# drawing, and also say where it pays to route them. The three "stella" (star)
# wires all start from the NODE: no other ground connects to another ground,
# except inside its own branch (the logic bus: GND of the XIAO, of the sensor,
# of the LED, MS1, MS2).
#
# The net names ("vm", "stella", "gnd_pot", "segnale", ...) stay as they are:
# they are keys of the translation catalogues ("net.<name>" in
# texts_drawings_*.py), and the drawings look their legend up by them.
WIRES = [
    # power
    ((15, 7), (18, 7), "vm"),          # VM -> C1 +, short lead
    ((14, 7), (18, 8), "gnd_pot"),     # power GND -> C1 -, short lead
    ((18, 7), (20, 0), "vm"),          # C1 + -> 12 V terminal +
    ((18, 5), (20, 0), "vm"),          # C2 + on the + of the terminal
    ((18, 6), (20, 2), "gnd_pot"),     # C2 - on the - of the terminal: it is the 12 V branch
    # the star: three wires from the node
    (NODE, (20, 2), "stella"),         # 12 V return
    (NODE, (8, 7), "stella"),          # logic ground of the driver
    (NODE, (1, 2), "stella"),          # ground of the XIAO
    # motor phases
    ((11, 7), (23, 3), "faseA+"),
    ((10, 7), (23, 4), "faseA-"),
    ((12, 7), (23, 5), "faseB+"),
    ((13, 7), (23, 6), "faseB-"),
    # logic
    ((0, 8), (9, 2), "segnale"),       # D0 -> STEP
    ((1, 8), (8, 2), "segnale"),       # D1 -> DIR
    ((3, 8), (15, 2), "segnale"),      # D3 -> EN, direct
    ((15, 1), (15, 2), "segnale"),     # R1 -> EN, R1 sits over the pin
    ((12, 1), (2, 2), "3v3", [(12, 1.75), (2, 1.75)]),   # R1 -> 3V3
    ((2, 2), (9, 7), "3v3"),           # 3V3 -> VDD of the driver
    ((2, 2), (12, 9), "3v3"),          # 3V3 -> VCC of the sensor
    ((5, 2), (11, 0), "segnale"),      # D8 (TX) -> R2, near end
    ((15, 0), (12, 2), "segnale"),     # R2 -> UART
    ((4, 2), (12, 2), "segnale", [(4, 1.45), (12, 1.45)]),   # D9 (RX) -> UART, direct
    ((4, 8), (10, 9), "i2c"),          # D4 -> SDA
    ((5, 8), (11, 9), "i2c"),          # D5 -> SCL
    ((3, 2), (10, 0), "segnale"),      # D10 -> R3
    ((6, 0), (3, 0), "segnale"),       # R3 -> LED +
    # the logic ground bus, all from the GND of the XIAO
    ((1, 2), (4, 0), "gnd_log"),       # LED -
    ((1, 2), (13, 9), "gnd_log"),      # GND of the sensor
    ((8, 7), (14, 2), "gnd_log"),      # MS1 to the logic ground of the driver
    ((8, 7), (13, 2), "gnd_log"),      # MS2 to the logic ground of the driver
]

# The conductors of the CAT5 that runs from J4 on the board to the AS5600
# module, keyed by the J4 hole they land on. DECLARED, not measured: the
# colours soldered on the sensor module of the reference build. The module end is
# already soldered, so the board end must follow the same colours, or SDA and
# SCL end up swapped.
#
# FOUR WIRES, NOT SIX. On the WROOM bench white-green
# carried DIR (module pad 2) to GND at the far end. DIR only fixes which way the
# angle grows and must not float; it is now tied to GND ON THE MODULE, with a
# jumper from pad 2 to pad 1 - so nothing about DIR travels in the cable any
# more. Using the spare whites as extra grounds paired with SDA and SCL was
# weighed and dropped: on a metre of CAT5 at I2C speed the gain is small, and
# three wires crimped into the one GND contact of J4 is a poor joint. The
# spare conductors are cut back and insulated at the board end.
# Each colour: (name on the drawing, solid colour, stripe or None).
CAT5_SENSOR = {
    (12, 9): [("brown", "#7A4A24", None)],
    (13, 9): [("white-brown", "#FFFFFF", "#7A4A24")],
    (10, 9): [("blue", "#2F5FB0", None)],
    (11, 9): [("green", "#3F8F3A", None)],
}
CAT5_SPARE = ("white-green", "white-blue", "orange", "white-orange")

# (colour, note) per net. The note is for whoever reads this table: the
# drawings write the legend from the catalogues, "net.<name>".
COLOURS = {
    "vm": ("#E0457B", "12 V and VM"),
    "stella": ("#8A4F0E", "star ground: the wires that start from the node"),
    "gnd_pot": ("#3A3A38", "power ground: lead of C1, − of C2"),
    "gnd_log": ("#6E6C66", "logic ground, local bus of its branch"),
    "3v3": ("#E08A1E", "3V3 of the XIAO"),
    "segnale": ("#7B4FB5", "signals"),
    "i2c": ("#3E8C74", "I²C of the sensor"),
    "faseA+": ("#1E1E1C", "phase A+ (black)"),
    "faseA-": ("#5E9022", "phase A− (green)"),
    "faseB+": ("#C0392B", "phase B+ (red)"),
    "faseB-": ("#2F6FC4", "phase B− (blue)"),
}
