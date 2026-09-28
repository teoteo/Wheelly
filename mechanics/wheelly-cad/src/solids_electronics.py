# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The board panel that carries the perfboard, and the envelopes of the
electronics.

THE BOARD PANEL closes the opening in the bottom of the motor compartment and
carries the perfboard on three posts: with the three screws out, the whole
group comes out of the bottom and can be worked on at the table. It sits flush
with the bottom on both sides, held inwards by the stop and outwards by the
screws.

HOW IT GOES ON THE MACHINE: outer face on the bed. The step of the stop, the
posts, the guides and the tab grow upwards from solid material, so no support
at all is needed. It was true before too except in one spot, and that spot
broke: the two little teeth that held the cut end of the perfboard had a lip
born in mid-air above a slit, and one snapped while the perfboard was slid
in - which in that zone, precisely because it was
printed on supports, went in with difficulty. The lip is gone: in its place a
third screw (B05 on the perfboard's grid) and two smooth guides that square it
from the side.

THE THREE SCREWS bite in zones Th_panel_screws thick and no longer on a flap
of half a wall: there the protruding head has something to rest on, and the
step the box carves for it is high enough for the supports to be born inside
it.


THE TAB closes the slot of the USB socket below the socket: the slot is open
towards the bottom because the socket goes in rising, and without the tab
below it there would remain a slit fifteen millimetres high.

THE ENVELOPES are not printed and live in out/electronics/. XIAO and driver
are the makers' models; the heatsink is measured on the real part, not the model's,
which is 15 high instead of 13.67. Sockets, pin spacers, the components of the
table in electronics.py and the LED are declared ESTIMATES: they serve to see
whether things fit, not to draw them.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out") + os.sep
OUT_EL = os.path.join(OUT, "electronics") + os.sep
PURCHASED = os.path.join(os.path.dirname(HERE), "others") + os.sep
os.makedirs(OUT_EL, exist_ok=True)
import cadquery as cq
from parameters import D
import electronics as E

# THE FLOOR IS NO LONGER -38, and this was the fourth place where that number
# was written by hand: the other three - the box generator and twice the
# dimensions of electronics.py - had been hooked to Z_floor_box, this one had
# stayed behind. So the board panel came out six and
# a half millimetres lower than the floor it has to close, and the checks of
# the countersink measured 2.40 of thickness where there are five.
ZT = D["Z_floor_box"]
W = E.W_WALL
Ro = D["R_out_box"]


def to_project(sol):
    """From the perfboard's frame (x = s, y = t) to the project's."""
    return sol.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), E.A_BOARD)


def block(s0, s1, t0, t1, z0, z1):
    return to_project(cq.Solid.makeBox(s1-s0, t1-t0, z1-z0, cq.Vector(s0, t0, z0)))


def inside_back(clearance, z0, h):
    """The plan of the compartment up to the inner face of the back, minus the
    clearance. In the electronics sector the back is at constant r."""
    return cq.Workplane("XY").workplane(offset=z0).circle(Ro - W - clearance).extrude(h).val()


# ---------------- the board panel ----------------
g = D["Cl_panel"]
bt = D["Stop_panel"]
rb = D["D_boss_panel"]/2
# the inner half, which sits in the opening
pan = block(E.OP_S[0] + g, E.OP_S[1] - g, E.OP_T[0] + g, E.OP_T[1] - g,
            E.Z_STOP, E.Z_FLOOR_TOP)
# the outer half, widened by the stop, with the two ears of the screws
outer = block(E.OP_S[0] + g, E.OP_S[1] + bt - g, E.OP_T[0] - bt + g, E.OP_T[1] + bt - g,
              ZT, E.Z_STOP)
# The two zones of the screws are Th_panel_screws thick instead of half a
# wall: the 1.25 flap the screws bit on was too little, and the step matching
# it in the box was an overhanging roof just above the bed, where supports
# are not born. The shapes are the ones the box carves for itself
# (E.panel_ears()), shrunk by the clearance on the free sides: the one
# towards the body of the board panel is not touched, because there they are
# attached.
for _s0, _s1, _t0, _t1, _side, _ovl in E.panel_ears():

    # the clearance is taken off the FREE sides; not off the one facing the
    # body of the board panel, because there the ear has to fuse to it
    _d = {"s0": +g, "s1": -g, "t0": +g, "t1": -g}
    _d[_side] = 0.0

    outer = outer.fuse(block(_s0 + _d["s0"], _s1 + _d["s1"],
                             _t0 + _d["t0"], _t1 + _d["t1"], ZT, E.Z_SCREWS))

pan = pan.fuse(outer).intersect(inside_back(g, ZT - 1, 10.0))
# the tab, in the slot of the socket
gu = D["Cl_usb"]
# The tab starts where the inner half of the board panel ends, not a
# millimetre earlier: with the end of the perfboard half a millimetre from the
# head, a millimetre ran into it - found by the check of the little teeth,
# 7.5 mm3.
pan = pan.fuse(block(E.S_USB - E.USB_L/2 - gu + g, E.S_USB + E.USB_L/2 + gu - g + E.EXT_SLOT_BACK,
                     E.OP_T[1] - g, E.T_HEAD_OUT,
                     ZT, E.Z_USB[0] - gu))
# (one pitch wider towards the back: it closes the bottom of the slot the arm
# goes in through - electronics.EXT_SLOT_BACK)
# The posts of the perfboard, with the M2.5 insert. The two on the head side
# would stick out beyond its inner face: the perfboard hole is 2 mm from the
# end, the post has a radius of 3.5, and between perfboard and head there is
# a millimetre. They are cut flush, with the clearance: around the insert
# wall remains.
# The cut is made on the posts ALONE: made on the whole board panel it took
# away the tab too, which lies just beyond that plane - the check of the slot
# found it, not the eye.
_beyond_head = to_project(cq.Solid.makeBox(200.0, 50.0, 40.0,
                                           cq.Vector(0.0, E.T_HEAD_IN - g, E.Z_FLOOR_TOP - 0.05)))
for s_, t_ in E.board_holes():
    x, y = E.xy(s_, t_)
    post_ = cq.Solid.makeCylinder(D["D_post"]/2, E.Z_BOARD - E.Z_FLOOR_TOP + 0.01,
                                  cq.Vector(x, y, E.Z_FLOOR_TOP - 0.01)).cut(_beyond_head)
    pan = pan.fuse(post_)
    pan = pan.cut(cq.Solid.makeCylinder(D["D_hole_insert_M2"]/2, D["L_insert_M2"] + 0.5,
                                        cq.Vector(x, y, E.Z_BOARD - D["L_insert_M2"])))
# THE THIRD POST, at the cut end. Before, there was nothing there and the
# perfboard was held by two little teeth of the board panel, with a lip over
# the edge: the lip is born in mid-air above the slit, so it is printed on
# supports, and on the printed part one of them broke. Now the end
# is held by an M2.5 socket screw, in hole B05 of the grid printed on the
# perfboard (see electronics.board_head_screw): it is the free hole farthest
# from wires and pins among those far enough inside the edge to carry a whole
# boss. An M2.5 insert and not M2 because that size is at hand with a socket
# head, and above the perfboard its head has eleven millimetres before the
# XIAO.
_sv, _tv = E.board_head_screw()
_xv, _yv = E.xy(_sv, _tv)
pan = pan.fuse(cq.Solid.makeCylinder(
    D["D_boss_cover_sensor"]/2, E.Z_BOARD - E.Z_FLOOR_TOP + 0.01,
    cq.Vector(_xv, _yv, E.Z_FLOOR_TOP - 0.01)).cut(_beyond_head))
pan = pan.cut(cq.Solid.makeCylinder(D["D_hole_insert_M25"]/2, D["L_insert_M25"] + 0.5,
                                    cq.Vector(_xv, _yv, E.Z_BOARD - D["L_insert_M25"])))
# THE TWO GUIDES of the cut end: two ribs beside the long edges of the
# perfboard, with no lip on top. They do not hold it down - the screw above
# sees to that - they just square it, and they stick out H_guides_board above
# the face to act as a lead-in when it is lowered in. Without a lip there is
# no undercut: they grow from the solid of the board panel and print without
# supports, which is the defect this whole change was born from.
for s0_, s1_, t0_, t1_ in E.board_guides():
    # cut on the back like the rest of the board panel: the outer one reaches
    # it within a tenth, and without the cut it would overhang the part by
    # that tenth
    pan = pan.fuse(block(s0_, s1_, t0_, t1_, E.Z_FLOOR_TOP - 0.01,
                         E.Z_BOARD_TOP + D["H_guides_board"])
                   .intersect(inside_back(g, E.Z_FLOOR_TOP - 1.0, 20.0)))

# The screws, COUNTERSUNK head, and now it can be done. With the stop at half a wall the board panel was 1.25 thick there
# and the countersink did not fit - that is why the screws had a protruding
# head - but in the screw zones it is now Th_panel_screws thick. The
# countersink is a cone at Ang_head_countersunk closing on the clearance hole,
# so its depth DERIVES from the two dimensions instead of being chosen: 3.7 mm
# of material remain below. The cone is born three tenths outside the face,
# like all the other lead-ins of the project: born coplanar it leaves chips on
# the edge.
_rp = D["D_clear_screw_panel"]/2
_p_taper = (D["D_head_countersunk_M3"]/2 - _rp)/math.tan(math.radians(D["Ang_head_countersunk"]/2))
for s_, t_ in E.panel_screws():
    x, y = E.xy(s_, t_)
    pan = pan.cut(cq.Solid.makeCylinder(_rp, 20.0, cq.Vector(x, y, ZT - 5.0)))
    pan = pan.cut(cq.Solid.makeCone(D["D_head_countersunk_M3"]/2 + 0.3, _rp,
                                    _p_taper + 0.3, cq.Vector(x, y, ZT - 0.3),
                                    cq.Vector(0, 0, 1)))
print("board panel: M3 countersink %.2f mm deep in %.1f of thickness"
      % (_p_taper, D["Th_panel_screws"]))

pan = cq.Workplane(obj=pan.clean())
cq.exporters.export(pan, OUT + "board_panel.step")

# ---------------- the envelopes ----------------
envelopes = {}
envelopes["perfboard"] = block(E.S0, E.S1, E.T0, E.T1, E.Z_BOARD, E.Z_BOARD_TOP)   # cut at T1


def strip(s_centre, t0, t1, z_top):
    """A rectangular socket with the pin spacer on top, up to the underside of
    the module: its height is measured on the reference build."""
    return block(s_centre - 1.27, s_centre + 1.27, t0, t1, E.Z_BOARD_TOP, z_top)


# each module on ITS OWN rows: the XIAO's are six holes apart, the driver's
# five (wiring.R_XIAO, R_DRIVER - both used to be written here as R2 and R8)
import wiring as _W
_z = None
for rows, (c0_, c1_), z_top in ((_W.R_XIAO, (0, int(D["Pin_xiao_per_side"]) - 1), E.Z_MODULE),
                                (_W.R_DRIVER, (8, 15), E.Z_MODULE_DRIVER)):
    for r_ in rows:
        z_ = block(E.s_row(r_) - 1.27, E.s_row(r_) + 1.27,
                   E.t_col(c1_) - 1.27, E.t_col(c0_) + 1.27, E.Z_BOARD_TOP, z_top)
        _z = z_ if _z is None else _z.fuse(z_)
envelopes["pin_sockets"] = _z

# the maker's XIAO: in its file the length is X with the socket towards +X,
# the thickness Y with the components towards +Y, the width Z
xi = cq.importers.importStep(PURCHASED + "XIAO-ESP32S3 v2.step").val()
xi = xi.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90)       # Y -> Z, Z -> -Y
xi = xi.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90)       # X -> Y (= t)
bb = xi.BoundingBox()
xi = xi.translate(cq.Vector(E.S_XIAO_C - (bb.xmin + bb.xmax)/2,
                            E.T_XIAO_EDGE - 12.28,
                            E.Z_MODULE - (-0.25)))
# THE MODULE IS FILED DOWN AT THE SIDES OF THE SOCKET, and the model says so.
# The maker draws it whole: as it is it would enter the head by 0.97 mm - as
# much as the socket sticks out beyond the edge, minus the thickness of the
# wall - and to let it through the box had a groove as wide as the module,
# which left two recesses at the sides of the board panel's tower. They are
# filled: the module of the reference build is filed down in that zone on
# purpose and no longer enters the wall. Here what the file takes off is taken
# off, except the socket, which does pass through its slot: so
# the envelope in the model is the REAL part, and the interpenetration with
# the head stays a defect instead of becoming an exception to remember by
# heart.
_filed = cq.Solid.makeBox(200.0, 50.0, 60.0, cq.Vector(0.0, E.T_HEAD_IN, -60.0))
_filed = _filed.cut(cq.Solid.makeBox(E.USB_L + 2*gu, 50.0, 60.0,
                                     cq.Vector(E.S_USB - E.USB_L/2 - gu,
                                               E.T_HEAD_IN, -60.0)))
_v_filed = xi.intersect(_filed).Volume()
xi = xi.cut(_filed)
envelopes["xiao"] = to_project(xi)

# the driver: board and pins from the model, the heatsink from the measurement
dr = cq.importers.importStep(PURCHASED + "TMC2209.step")
parts = [v for v in dr.solids().vals()
         if not (v.BoundingBox().xlen > 14 and v.BoundingBox().zmin > 1.5)]   # away with the model's heatsink
drv = parts[0]
for v in parts[1:]:
    drv = drv.fuse(v)
drv = drv.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90)   # X (pin row) -> t
drv = drv.translate(cq.Vector(E.S_DRIVER_C, E.T_DRIVER_C, E.Z_MODULE_DRIVER))
# ARE ITS PINS ON THE HOLES? Measured on the maker's model once placed: every
# pin - the thin solids reaching lowest - must stand on the centre of a hole
# of the board, within a tenth. The driver sat half a hole off for weeks,
# drawn on the XIAO's rows; nothing checked it.
_pins = [v for v in dr.solids().vals()
         if v.BoundingBox().zmin < min(w.BoundingBox().zmin for w in dr.solids().vals()) + 0.5
         and v.BoundingBox().xlen < 1.5 and v.BoundingBox().ylen < 1.5]
_off = []
for _p in _pins:
    _c = _p.Center()
    # the same rotation and move as the module: X -> t, then to its place
    _q = cq.Vector(-_c.y, _c.x, 0).add(cq.Vector(E.S_DRIVER_C, E.T_DRIVER_C, 0))
    _r = min(range(E.N_ROW), key=lambda r: abs(E.s_row(r) - _q.x))
    _k = min(range(E.N_COL), key=lambda k: abs(E.t_col(k) - _q.y))
    if abs(E.s_row(_r) - _q.x) > 0.1 or abs(E.t_col(_k) - _q.y) > 0.1:
        _off.append("pin at s %.2f t %.2f" % (_q.x, _q.y))
if len(_pins) != 16 or _off:
    raise SystemExit("driver: %d pins found, off the holes: %s" % (len(_pins), "; ".join(_off) or "none"))
print("driver: 16 pins, all on holes (rows %s)" % (sorted(set(
    min(range(E.N_ROW), key=lambda r: abs(E.s_row(r) - (E.S_DRIVER_C - p_.Center().y))) for p_ in _pins)),))
envelopes["driver"] = to_project(drv).fuse(
    block(E.S_HEATSINK[0], E.S_HEATSINK[1], E.T_HEATSINK[0], E.T_HEATSINK[1],
          E.Z_MODULE_DRIVER + D["Th_board_driver"], E.Z_DRIVER_TOP))

# the components of the table, one per entry, all in a single file
_comp = None
for entry in E.COMPONENTS:
    t0_, t1_, s0_, s1_ = E.st_component(entry)
    if entry[2] == "round":
        x, y = E.xy((s0_ + s1_)/2, (t0_ + t1_)/2)
        c_ = cq.Solid.makeCylinder(entry[4]/2, entry[5], cq.Vector(x, y, E.Z_BOARD_TOP))
    else:
        c_ = block(s0_, s1_, t0_, t1_, E.Z_BOARD_TOP, E.Z_BOARD_TOP + entry[5])
    _comp = c_ if _comp is None else _comp.fuse(c_)
envelopes["components"] = _comp
# the LED: collar resting on the inner face of the head, body in the hole
_t0 = E.T_HEAD_IN - E.LED_COLLAR
_led = cq.Solid.makeCylinder(D["D_collar_led"]/2, E.LED_COLLAR,
                             cq.Vector(E.LED_S, _t0, E.LED_Z), cq.Vector(0, 1, 0))
_led = _led.fuse(cq.Solid.makeCylinder(D["D_led"]/2, E.LED_LENGTH,
                                       cq.Vector(E.LED_S, _t0, E.LED_Z), cq.Vector(0, 1, 0)))
envelopes["led"] = to_project(_led)
# the GX12: axis along Y, inner face of the panel at y -3, the body comes out towards +Y
# (a plain file name: the makers' models are downloaded by
# the builder, mechanics/others/README.md, so the name must be one they can type)
gx = cq.importers.importStep(PURCHASED + "GX12-2P.step").val()
gx = gx.translate(cq.Vector(E.GX12_S, E.T_HEAD_IN + 3.0, E.GX12_Z))
# THE NUT IS A BODY OF ITS OWN. The maker's STEP has five solids:
# the nut, Ø16.8 and 2 thick against the inner face of the head, then the
# body, the back and two pins, all narrower than the hole. Kept as one
# body, the connector could get into its hole from neither side - and it
# goes in FROM OUTSIDE, with the nut run on from inside. The nut
# is told apart by what it is, the widest solid, not by its index.
_gx_parts = sorted(gx.Solids(), key=lambda s: -s.BoundingBox().xlen)
_nut, _body = _gx_parts[0], _gx_parts[1:]
envelopes["gx12"] = to_project(cq.Compound.makeCompound(_body))
envelopes["gx12_nut"] = to_project(_nut)

for name, sol in envelopes.items():
    cq.exporters.export(cq.Workplane(obj=sol), OUT_EL + name + ".step")

print("board panel %.1f cm3 (%.0f g ASA) | envelopes: %s"
      % (pan.val().Volume()/1000, pan.val().Volume()*1.07e-3, ", ".join(envelopes)))
print("XIAO: %.1f mm3 filed off at the sides of the socket, that is %.2f mm of module "
      "that would otherwise enter the head" % (_v_filed, E.T_XIAO_EDGE - E.T_HEAD_IN))

print("driver stack from the board panel: %.2f mm (top at z %.2f) | USB socket z %.2f..%.2f | the XIAO overhangs the perfboard by %.2f"
      % (E.Z_DRIVER_TOP - E.Z_FLOOR_TOP, E.Z_DRIVER_TOP, E.Z_USB[0], E.Z_USB[1], E.XIAO_OVERHANG))
print("perfboard cut %.2f mm from the head: beyond the first hole %.2f remain, %.1f long"
      % (D["Cl_head_board"], E.CUT_MARGIN, E.T1 - E.T0))
