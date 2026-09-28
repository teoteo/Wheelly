# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Where the electronics stands, and everything that follows from it.

The electronics sits in the MOTOR BAY, on a 30 x 70 board screwed to a small
panel that closes an opening in the floor. Here there is only the geometry,
written once and read by box, panel, checks and drawings.

THE FRAME. The board is not a sector: it is a rectangle, and a rectangle is
not described well with angles and radii. So it gets a frame of its own:

    s  along the bisector of the board, Ang_board, from the disc centre
    t  across, positive towards increasing angles (towards the head)
    z  the usual one

The board occupies s in [R_in_board, R_in_board + W_board] and
t in [-L_board/2, +L_board/2]. The XIAO sits at the positive t end, with the
USB socket facing the head of the box.

THE HEAD WALL follows from the socket, not the other way round: its outer
face stands FLUSH with the mouth of the USB socket, because the shell of the
right-angle plug must rest on a flat face and the plug must go all the way
in. The wall is therefore a plane t = constant, perpendicular to the board,
and not a radial wall: on a radial wall the socket would arrive askew.

THE STACK IN HEIGHT, from the floor up: panel (flush with the floor), posts,
board, female socket strip, spacer of the male pins, module. The driver has
the heatsink on top as well, and it is the one that sets the height.
"""
import math
from parameters import D

A_BOARD = D["Ang_board"]
U = (math.cos(math.radians(A_BOARD)), math.sin(math.radians(A_BOARD)))   # s
V = (-U[1], U[0])                                                         # t

S0 = D["R_in_board"]
S1 = S0 + D["W_board"]
S_MID = (S0 + S1)/2
T0 = -D["L_board"]/2                  # far end, whole

# ---------------- the perfboard grid ----------------
# Everything on the board sits on its holes, and the grid is centred on the
# WHOLE board. Columns C0..C23 starting from the head, rows R0..R9 starting
# from the BACK side (away from the wheel axis): R0 is the row printed "10" on
# the perfboard, R9 the row printed "01", and printed "01" is on the AXIS side.
#
# WHY THE BACK SIDE. R0 used to be on the axis side and the drawings called it
# "10": the silkscreen of the perfboard of the reference build says the
# opposite - "01" is on the axis side (seen on a photo of the board on its
# panel). A board built by the printed labels was therefore the MIRROR of the
# model across its long axis: every part on the right label,
# every part on the wrong side. It showed at the XIAO, whose rows R2 and R8
# are not centred on the board: its USB socket stood 2.54 mm - one hole -
# towards the axis from the slot of the head and the tongue of the panel
# (measured on the built board: 4.5 mm from the axis-side edge of the board to
# the XIAO; the model said 7.5). The labels, the wiring and the pinouts do not change:
# only the side the rows count from, here, and every s follows from s_row.
#
# The XIAO has its pin rows 15.24 apart, that is six pitches: it sits on rows
# R2 and R8, and its centre falls on row R5, half a pitch off the centre of the
# board - towards the axis. The driver does NOT: its rows are 12.7 apart, five
# pitches, on R2 and R7 (wiring.R_DRIVER).
PITCH = D["Pitch_perfboard"]
N_COL, N_ROW = int(D["N_holes_board_L"]), int(D["N_holes_board_W"])


def t_col(c):
    """The t of column c (fractional too), C0 on the head side."""
    return (N_COL - 1)*PITCH/2 - c*PITCH


def s_row(r):
    """The s of row r (fractional too), R0 on the BACK side: s grows towards
    the back, the rows grow towards the axis."""
    return S_MID - (r - (N_ROW - 1)/2)*PITCH


W_WALL = D["Th_walls_box"]
# The floor comes from Z_floor_box and no longer from the number -38 written
# here: it was repeated in three places - here, the stop and the screws - and
# three copies of a dimension come apart at the first part that moves.
Z_FLOOR_TOP = D["Z_floor_box"] + W_WALL   # inner face of the floor = of the panel


def xy(s, t):
    """From the board's frame to the project's plane."""
    return (U[0]*s + V[0]*t, U[1]*s + V[1]*t)


def st(x, y):
    """From the project's plane to the board's frame."""
    return (x*U[0] + y*U[1], x*V[0] + y*V[1])


# ---------------- the stack ----------------
Z_BOARD = Z_FLOOR_TOP + D["H_post"]                   # underside of the board
Z_BOARD_TOP = Z_BOARD + D["Th_board"]
# The measurement (on the reference build) takes socket strip and spacer together: from the board
# to the underside of the module. The driver has its own, because its pin
# header is not the XIAO's.
Z_MODULE = Z_BOARD_TOP + D["H_below_board_xiao"]
Z_MODULE_DRIVER = Z_BOARD_TOP + D["H_below_board_driver"]
Z_DRIVER_TOP = Z_MODULE_DRIVER + D["Th_board_driver"] + D["H_heatsink_driver"]

# ---------------- the XIAO and its socket ----------------
# From the maker's model (mechanics/others/XIAO-ESP32S3 v2.step): board
# 20.95 x 17.78, 1.25 thick; the USB-C socket is 8.94 wide, 4.20 high starting
# 0.26 above the underside of the board, and sticks out 1.53 beyond the edge.
# In the millimetre of board that goes into the head there are components too:
# they reach 1.98 above the underside of the board, and the groove must let
# them through. Found by the interference test, not by eye.
L_XIAO, W_XIAO, TH_XIAO = D["L_xiao"], 17.78, 1.25
USB_L, USB_PROJ = 8.94, D["Proj_usb_xiao"]
USB_H, USB_Z0 = D["H_usb"], D["Z_usb_on_board"]
H_XIAO_EDGE = 1.98
NP_XIAO = int(D["Pin_xiao_per_side"])

# The XIAO has its pins on columns C0..C6: its edge stands beyond C0 by as much
# as the board reaches past the first pin. The HEAD follows from there: its
# outer face flush with the mouth of the socket. And the board is CUT at
# Cl_head_board from the inner face: whole, with the first column 5.8 mm from
# the edge, the socket would stay inside it.
T_XIAO_EDGE = t_col(0) + (L_XIAO - (NP_XIAO - 1)*PITCH)/2
T_HEAD_OUT = T_XIAO_EDGE + USB_PROJ
T_HEAD_IN = T_HEAD_OUT - W_WALL
T1 = T_HEAD_IN - D["Cl_head_board"]          # CUT end of the board
CUT_MARGIN = T1 - t_col(0)                     # board beyond the first hole
XIAO_OVERHANG = T_XIAO_EDGE - T1
T_XIAO = (T_XIAO_EDGE - L_XIAO, T_XIAO_EDGE)
# The centre of the XIAO follows its rows in wiring.py, not a row written
# here: it was s_row(5) by hand, one more place that would not have moved
# with the module.
import wiring as _W
S_XIAO_C = s_row(sum(_W.R_XIAO)/2)
S_XIAO = (S_XIAO_C - W_XIAO/2, S_XIAO_C + W_XIAO/2)
S_USB = S_XIAO_C
# BELOW the socket the slot of the head - and the panel's tongue that closes
# it - reach one pitch further towards the back than the socket needs. It is
# for the ARM, not for the socket: its declared path in through the
# electronics opening (guide/paths/arm_door.json) was found with the slot one
# hole further back, where the socket sat before the rows were turned,
# and it passes through the bottom of the slot there. With the
# slot moved and nothing else, the arm grazed the head wall by 1.0 mm3 at z
# -30.5 (check_assembly_paths, move 5.3). The tongue fills it once the panel
# is on, so the head stays closed.
EXT_SLOT_BACK = PITCH
Z_USB = (Z_MODULE + USB_Z0, Z_MODULE + USB_Z0 + USB_H)

# ---------------- the driver ----------------
# Pins on columns C8..C15, rows wiring.R_DRIVER (R2 and R7): C7 stays free
# between the two modules. Row R7, on the axis side, is the power row, with
# VM and GND in C15. The centre of the module stands between its two rows,
# not on the XIAO's R5: it used to stand there, and its rows fell
# half a hole off, on R2.5 and R7.5.
L_DRIVER, W_DRIVER = 20.32, 15.24
T_DRIVER_C = t_col(11.5)
S_DRIVER_C = s_row(sum(_W.R_DRIVER)/2)
T_DRIVER = (T_DRIVER_C - L_DRIVER/2, T_DRIVER_C + L_DRIVER/2)
S_DRIVER = (S_DRIVER_C - W_DRIVER/2, S_DRIVER_C + W_DRIVER/2)
T_HEATSINK = (T_DRIVER_C - D["L_heatsink_driver"]/2, T_DRIVER_C + D["L_heatsink_driver"]/2)
S_HEATSINK = (S_DRIVER_C - D["W_heatsink_driver"]/2, S_DRIVER_C + D["W_heatsink_driver"]/2)

# ---------------- the components, in holes ----------------
# One table only, from which come the envelopes in the model and the layout
# drawing (pcb/en_board-layout.svg and it_disposizione-basetta.svg; the drawn
# descriptions are in texts_drawings_*.py). Each entry: reference, what it is,
# shape ("round" or "block"), columns and rows of the centre or of the ends of
# the body, diameter, height above the board, and the holes of the leads. The
# body sizes are catalogue ESTIMATES, except where stated.
#
# THE POSITIONS ARE THE ONES CHECKED on the real board of the reference build,
# after fitting the components: the connectors did not fit where the design
# had put them. They are given on the grid PRINTED on the perfboard, which runs
# from A to X and from 01 to 10; the conversion is direct - the letter is the
# column number (A = C0) and the row is 10 minus the row number (row 10 = R0,
# the one on the BACK side, see the grid above) - and it can be recognised
# from the two modules,
# which sit on printed rows 08 and 02 and on R2 and R8 here.
#
#   C1 sits just beyond the end of the driver on the VM and GND side (C15, R7),
#      on printed S03/S02 (column 18, R7 and R8), minus on row 02: it moves
#      up with the driver's power row, confirmed on the real board.
#      C2 stays on S05/S04, minus on 04. Two rows apart the two drawn bodies
#      (D_electrolytic, catalogue estimate) overlap, but on the real board
#      they fit: the true diameter is to be measured.
#      It cannot sit alongside, on row R8, because there it would pass under
#      the driver's board. Its leads reach the pins with two millimetres.
#      In the checked layout it had been moved three columns further over,
#      on S03/S04, and there the VM-bridge-GND loop went from about 13 to 40
#      mm2: that constraint in pcb/README comes BEFORE the envelope, and
#      so it is back close and C2 moved instead.
#   C2 sits on S04/S05 and not on S06/S07 as would have come naturally: at S06
#      its Ø6.4 body would hit the J3 terminal block, which reaches row 07.
#   The single ground node is the negative terminal of C1.
# The descriptions (second field) are notes for whoever reads this table: the
# drawings take theirs from the translation catalogues, "comp.<reference>".
COMPONENTS = [
    ("C1", "47 µF 63 V, driver VM", "round", (18.0, 7.5), D["D_electrolytic"], D["H_electrolytic"],
     [(18, 7), (18, 8)]),
    ("C2", "47 µF 63 V, 12 V input (optional)", "round", (18.0, 5.5), D["D_electrolytic"], D["H_electrolytic"],
     [(18, 5), (18, 6)]),
    ("J1", "terminal block for phases A and B, four poles", "block", (21.5, 24.5, 2.5, 6.5), None, D["H_terminals"],
     [(23, 3), (23, 4), (23, 5), (23, 6)]),
    ("J3", "12 V terminal block", "block", (18.5, 21.5, -1.0, 3.0), None, D["H_terminals"],
     [(20, 0), (20, 2)]),
    ("J4", "sensor header, 4 poles", "block", (9.5, 13.5, 8.5, 9.5), None, 8.5,
     [(10, 9), (11, 9), (12, 9), (13, 9)]),     # SDA, SCL, VCC, GND
    ("J5", "LED header, 2 poles", "block", (2.5, 4.5, -0.5, 1.5), None, 8.5,
     [(3, 0), (4, 0)]),
    ("R1", "10 kΩ, EN pull-up", "block", (12.0, 15.0, 0.6, 1.4), None, 2.5,
     [(12, 1), (15, 1)]),
    ("R2", "1 kΩ in series, UART", "block", (11.0, 15.0, -0.4, 0.4), None, 2.5,
     [(11, 0), (15, 0)]),
    ("R3", "1 kΩ in series, LED", "block", (6.0, 10.0, -0.4, 0.4), None, 2.5,
     [(6, 0), (10, 0)]),
]


def st_component(entry):
    """(t0, t1, s0, s1) of a component's footprint."""
    ref, what, shape, pos, d, h, pins = entry
    if shape == "round":
        tc, sc = t_col(pos[0]), s_row(pos[1])
        return (tc - d/2, tc + d/2, sc - d/2, sc + d/2)
    c0, c1, r0, r1 = pos
    # Sorted, not taken in order: t falls as the column grows, and s falls as
    # the row grows since the rows count from the back - in
    # order, the envelope came out inside out and the panel failed to build.
    t0, t1 = sorted((t_col(c0), t_col(c1)))
    s0, s1 = sorted((s_row(r0), s_row(r1)))
    return (t0, t1, s0, s1)


C1_ST = (s_row(7.5), t_col(18.0))
C2_ST = (s_row(2.5), t_col(17.0))

# ---------------- the panel ----------------
# The opening in the floor is the board widened by Marg_panel, but towards
# the head it stops at the inner face of the wall: beyond it is the wall.
# Towards the axis the opening stops at the INNER SKIRT of the box, the wall
# that closes the bay under the collar: the inner side of the rectangle is
# tangent to it at t = 0, and elsewhere it stands further off.
R_SKIRT = (D["R_out_collar"] + D["Cl_skirt_collar"],
           D["R_out_collar"] + D["Cl_skirt_collar"] + W_WALL)

# THE INNER WALL UNDER THE WHEEL, which replaces the
# skirt as the side of the box towards the wheel axis. Its outer face stands
# Cl_wall_inner_motor inside the motor, which is what comes nearest to the axis
# below the collar; the inner face is a wall thickness further in. R_SKIRT
# stays: the panel opening and the raised floors of the ears still measure
# from the collar, not from this wall.
R_INNER_WALL = (D["Cd_motor"] - D["Side_motor"]/2 - D["Cl_wall_inner_motor"] - W_WALL,
                D["Cd_motor"] - D["Side_motor"]/2 - D["Cl_wall_inner_motor"])

# ---------------- how high the inner skirt rises ----------------
# The top of the skirt is not a chosen dimension: it is the UNDERSIDE OF THE
# ARM minus the clearance. The arm turns about a vertical axis, so its
# underside stays the same plane at any angle of the travel, and the skirt
# can come within half a millimetre of it without the rotation eating
# anything.
#
# Before, the top stood at -14, written by hand on the head of the pivot
# screw. Measuring the envelope of what really passes over the skirt's band,
# angle by angle, the head of the screw has nothing to do with it: it sits on
# the pivot, at r 91.6, and with its radius of 2.75 it reaches r 88.86, that
# is just OUTSIDE the band 86.3..88.8. What governs is the arm at -8 and,
# round the pivot, the three discs under it. So the skirt rises five and a
# half millimetres, and of the eleven millimetres of window open towards the
# bay only the slit of the clearance remains.
Z_SKIRT_TOP = D["Z_skirt_inner"]           # = Z_bottom_arm - clearance
Z_SKIRT_HIGH = -D["Th_flange_collar"]      # beyond the passage: up to the collar
XY_PIVOT = (D["R_disc"], D["Off_pivot"])


def skirt_pivot_recesses():
    """The steps the skirt cuts into itself round the pivot: (radius, bottom).

    Under the arm, on the pivot, there are three concentric discs that go
    lower than the underside: the flange of the lower bearing, the printed
    washer and the head of the screw that holds the pivot together. Each one
    dictates a cylinder as wide as itself plus the clearance, deep down to
    below its lower face; they are nested one in the other, and the narrowest
    is also the deepest.

    They come from here and not from three numbers because two of those three
    parts are PURCHASED: changing bearing or screw, the steps follow on their
    own. The head of the screw, in particular, is a catalogue dimension still
    to be confirmed.
    """
    z_under = D["Z_bottom_arm"]
    g = D["Cl_skirt_arm"]
    return [(D["D_flange_bearing"]/2 + g,
             z_under - D["Th_flange_bearing"] - g),
            (D["D_washer_pivot"]/2 + g,
             z_under - D["Th_washer_pivot"] - g),
            (D["D_head_screw_M3"]/2 + g,
             z_under - D["Th_washer_pivot"] - D["H_head_screw_M3"] - g)]
OP_S = (max(S0 - D["Marg_panel"], R_SKIRT[1]), S1 + D["Marg_panel"])
OP_T = (T0 - D["Marg_panel"], T_HEAD_IN)
# The stop: over the outer half of the thickness the opening is wider by
# Stop_panel, and the panel has the same step. So it does not go into the
# bay and sits flush with the floor on both sides.
Z_STOP = D["Z_floor_box"] + W_WALL/2
# In the three screw zones the stop is not at half thickness: there the
# panel is Th_panel_screws thick and the box cuts it a step just as high. Two
# reasons, both found on the printed parts: on the 1.25 flap the screws
# bit on nothing, and above all the ceiling of the step stood a millimetre and
# a quarter above the bed, where supports cannot develop. At five
# millimetres the supports have room to grow, and inside the box in that zone
# there is no envelope.
Z_SCREWS = D["Z_floor_box"] + D["Th_panel_screws"]
# At the far end the stop widens to carry the two screws, which bite in
# bosses made in the floor, outside the opening.
T_FAR_SCREWS = OP_T[0] - D["Proj_screws_panel"]/2
# The outer one cannot be too close to the back: the insert's seat is entered
# from outside, and its lead-in must open wholly inside the stop, not under
# the wall. The check that it can be reached from outside found it at
# r 126.5, with half the mouth covered by the back.
_r_max_screw = D["R_out_box"] - W_WALL - D["D_leadin_insert_M3"]/2 - 0.5
S_FAR_SCREWS = (OP_S[0] + D["Setback_screws_panel"],
                min(OP_S[1] - D["Setback_screws_panel"],
                    math.sqrt(_r_max_screw**2 - T_FAR_SCREWS**2)))
# At the head end a single screw, on the inner side, in the corner between the
# head and the skirt: on the outer side the boss would stand over the board.
# The boss goes a millimetre into the head, to weld to it.
def head_panel_screw():
    """The screw at the head end, (s, t).

    It is a function and not a pair of constants, and the reason is not
    style. The tracker that signs the dimensions in the drawings is OFF while
    the modules are imported: a parameter read up here ends up in no
    signature, and the editor - looking for it in the drawing later - goes
    back to guessing it by value. It really happened: `D_boss_panel` on the
    plan assembly view had two matches, NEITHER signed, and the one indicated
    had nothing to do with it. Read in here,
    instead, the read happens while drawing and the signature becomes true.

    It holds for every module constant that describes geometry drawn later:
    if one day another is added, it must be written this way.
    """
    return (OP_S[0] - D["D_boss_panel"]/2,
            OP_T[1] - D["D_boss_panel"]/2 + 1.0)


def panel_screws():
    """The three screws of the panel, (s, t)."""
    return [(S_FAR_SCREWS[0], T_FAR_SCREWS), (S_FAR_SCREWS[1], T_FAR_SCREWS),
            head_panel_screw()]


def panel_ears():
    """The two thick zones of the panel, the ones that carry the screws:
    (s0, s1, t0, t1, inner_side) each, in the board's frame.

    They are the same two outlines the panel fills and the box cuts into
    itself: written once only because if the two drift apart the panel no
    longer goes into its step, and it is a defect that shows only in the hand.

    `inner_side` says which of the four sides borders the body of the panel
    instead of the box: there the panel does not take off the clearance,
    because on that side it must weld to its own body, and the box does not
    widen the raised floor, because over there is the opening and not its
    own material.

    The head ear reaches ONE MILLIMETRE into the opening, and is not tangent
    to it: the body of the panel starts at the edge of the opening plus the
    clearance, so tangent it would stay two tenths apart - two parts in the
    same file instead of one. The far ear does not need it: the stop of the
    panel already sticks out beyond the edge and they overlap.
    """
    bt = D["Stop_panel"]
    rb = D["D_boss_panel"]/2
    s_hs, t_hs = head_panel_screw()
    return [(OP_S[0], OP_S[1] + bt,
             OP_T[0] - D["Proj_screws_panel"], OP_T[0], "t1", 0.0),
            (s_hs - rb, OP_S[0] + 1.0,
             t_hs - rb, OP_T[1] + bt, "s1", 1.0)]






def board_holes():
    """The two fixing holes of the board, at the far end: those of the head
    go away with the cut. (s, t)."""
    ds = D["Cd_holes_board_w"]/2
    t_ = T0 + D["Dist_holes_board_rim"]
    return [(S_MID - ds, t_), (S_MID + ds, t_)]


# The screw at the cut end: where, and why exactly there.
#
# The head end had no screws - the board is cut and the holes of that end
# went away with the cut - and two small teeth of the panel held it, with a
# lip over the edge. On the printed part a tooth broke:
# the lip is born in mid-air over the slot the board goes into, so it prints
# on supports, and it is fragile exactly in the direction it works in.
# Slipping the board in there was hard too, which is the other face of the
# same thing (surfaces on supports come out oversize).
#
# The replacement is a screw: the board is drilled and a post like the other
# two goes under it. The position is NOT chosen by eye - it is the one that
# stands furthest from everything already on the perfboard: the distance of
# every free hole from the wires of wiring.py and from the occupied leads is
# measured, and the maximum is taken among those that stand far enough inside
# the edge to carry a whole boss.
#
#   (C1, R5) - printed B05 on the board's grid - is 4.93 mm from the nearest
#   wire (D0 -> STEP) and 7.62 from the nearest lead, and sits under the
#   XIAO, between its two rows of pins.
#
#   (C0, R5), that is A05, would be even roomier (6.34 mm from the first wire)
#   but it is 1.39 mm from the cut end: the insert's seat would come out of
#   it. We do not go there, and it is the reason the number below is 1 and
#   not 0.
#
# The screw is an M2.5 socket head. Above the board its head
# has H_below_board_xiao - 11 mm - before meeting the underside of the XIAO,
# so it touches nothing: eight and a half millimetres of clearance over a head
# two and a half high.
COL_HEAD_SCREW, ROW_HEAD_SCREW = 1, 5


def board_head_screw():
    """The screw that holds the cut end of the board: (s, t)."""
    return (s_row(ROW_HEAD_SCREW), t_col(COL_HEAD_SCREW))


def board_hole_label(col, row):
    """The label PRINTED on the perfboard: letter = column from A, row = 10
    minus the row here. It is the one read on the part."""
    return "%s%02d" % (chr(ord("A") + int(col)), int(N_ROW - row))


def board_guides():
    """The two guides that square the cut end of the board from the sides:
    (s0, s1, t0, t1) each.

    Guides and no longer teeth: no lip over the edge, so the board is lowered
    from above instead of sliding under, and the panel prints all from the
    solid. Holding it down is the job of the screw above.
    """
    l_, th_ = D["L_guides_board"], D["Th_guides_board"]
    g_ = D["Cl_guides_board"]
    gp_ = D["Cl_panel"]
    # inside the edge of the panel: on the axis side between the board and
    # the edge of the opening there are only two point two millimetres, and a
    # whole guide would spill over, running into the wall of the opening
    return [(max(S0 - g_ - th_, OP_S[0] + gp_), S0 - g_, T1 - l_, T1),
            (S1 + g_, min(S1 + g_ + th_, OP_S[1] - gp_), T1 - l_, T1)]




# ---------------- the GX12 ----------------
# On the same head, above the XIAO. From the model: nut Ø16.7, 2 thick, a body
# that inside the wall reaches 6.5 and pins to 11.1.
GX12_S, GX12_Z = D["S_gx12"], D["Z_gx12"]
# The height of the nut is a dimension, not a number in the code: the
# position of the GX12 follows from it, and a dimension that lives in here
# cannot appear in any expression.
GX12_NUT, GX12_INSIDE = D["H_nut_gx12"], 11.1

# ---------------- the cable-tie tab ----------------
# It sticks out of the inner face of the head, next to the GX12 on the back
# side: that is where the wires of the GX12 and the LED come down. It stands
# half way between the nut of the GX12 and the inner face of the back,
# measured at the tip of the tab.
_t_tip = T_HEAD_IN - D["L_tab_tie"]
_s_back = math.sqrt((D["R_out_box"] - W_WALL)**2 - _t_tip**2)
# ...plus Off_tab_tie towards the back: exactly half way,
# the root of its 45 degree underside took 0.25 mm3 of the XIAO's board where
# it runs into the head. One millimetre towards the back leaves 0.65 of air;
# the other way it got worse (1.2 mm3), and raising the root by 1 mm left 0.014.
TAB_S = (D["S_gx12"] + 16.7/2 + _s_back)/2 + D["Off_tab_tie"]
TAB_Z = (D["Z_gx12"] - D["H_tab_tie"]/2, D["Z_gx12"] + D["H_tab_tie"]/2)
# the slot, half way along the tab
TAB_SLOT_T = T_HEAD_IN - D["L_tab_tie"]/2
TAB_SLOT_Z = D["Z_gx12"]

# ---------------- the LED ----------------
# Above the GX12, on the same head. It goes in from inside and stops on its
# collar: its height follows from the nut of the GX12, which is the widest
# thing near it.
LED_S = GX12_S
LED_Z = GX12_Z + GX12_NUT/2 + D["Cl_led_gx12"] + D["D_collar_led"]/2
LED_COLLAR, LED_LENGTH = 1.0, 5.3        # from the catalogue, 3 mm LED


def head_angle(r, face="in"):
    """At what angle the head (inner or outer face) meets the radius r."""
    T = T_HEAD_IN if face == "in" else T_HEAD_OUT
    return A_BOARD + math.degrees(math.asin(T/r))
