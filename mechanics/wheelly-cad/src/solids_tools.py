# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Accessory parts of the sensor, plus a test tool.

The magnet CAP and the gap test FEET are tools: they are printed, used to
assemble and to measure, and stay in the drawer. They go in out/tools/ so as
not to be mistaken for the parts to print for real.

The magnet SPACER is not: it is a real part, solids_assembly imports it and
it decides the gap, so it stays in out/ with the others. It was in here only
because it is born from the same drawing.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT + "tools", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
import cadquery as cq
from parameters import D

# ---------------- the magnet gluing cap ----------------
# z 0 is the face that rests on the wheel body; the solid is above it. The
# seat is Dp_seat_cap deep, much more than the magnet: inside a tall wall the
# magnet cannot tilt. The cap is set on the face, the magnet is pushed to the
# bottom through the push-out hole, and it settles on the head of the pivot
# flat and flush.
# The seat is cut with a NEGATIVE distance: on a bottom face the normal of the
# workplane points outwards, and a positive cutBlind would cut air. That is
# how it was for a while: the cap came out as a solid cylinder with only the
# push-out hole, without any check saying so.
cap = (cq.Workplane("XY").circle(D["D_cap"]/2).extrude(D["H_cap"])
       .faces("<Z").workplane().circle(D["D_seat_cap"]/2).cutBlind(-D["Dp_seat_cap"])
       .faces(">Z").workplane().circle(D["D_pushout_cap"]/2).cutThruAll())
cap = cap.edges(">Z").chamfer(0.4)

cq.exporters.export(cap, OUT + "tools/magnet_cap.step")
print("magnet cap: outside %.0f x %.0f, seat %.2f x %.1f, push-out hole %.0f"
      % (D["D_cap"], D["H_cap"], D["D_seat_cap"],
         D["Dp_seat_cap"], D["D_pushout_cap"]))

# ---------------- the magnet spacer ----------------
# It goes between the head of the pivot and the magnet and keeps the magnet
# lifted off the cover of the wheel, which stands still while the magnet
# turns. It is smaller than the pivot on purpose: so it does not touch the
# cover even when fitted off-centre, and it takes nothing away from the
# centring, which is still done by looking at the rim of pivot around the
# magnet.
# Four are printed: it is a half-gram part that gets lost, and the
# pivot-spacer-magnet stack is glued once only.
_spacer = cq.Workplane("XY").circle(D["D_spacer_magnet"]/2).extrude(D["Th_spacer_magnet"])
spacers = [_spacer.translate((i*12.0, 0, 0)) for i in range(4)]
cq.exporters.export(cq.Compound.makeCompound([d.val() for d in spacers]),
                    OUT + "magnet_spacer.step")
print("magnet spacer: %.1f x %.1f, four pieces"
      % (D["D_spacer_magnet"], D["Th_spacer_magnet"]))

# ---------------- the gap test feet ----------------
# The gap is not chosen on paper: the AGC of the AS5600 is measured and the
# one that brings it to half scale is kept. These are the hub of the bracket
# alone - same ring on the magnet, same M2 holes - at different heights: they
# are set on the face, the board is screwed on top and the value is read.
#
# The height is the one the board rests at, that is H_rest_module: the gap
# is H - Th_spacer_magnet - Th_magnet - H_body_chip (the chip under the
# board). The spacer is there so the magnet does not rest on the cover of the
# wheel, and it raises the whole series by as much.
# They are multiples of 0.2 on purpose, which is the layer height: so the
# dimension that is read is the one that comes out of the printer.
from drawings import (hub_radius, module_holes, module_angle,
                      capacitor_relief as relief_shape, rotate_points)
from solids_sensor import module_notch, magnet_hole   # the same as the real bracket's

# from the parameters, not written here: the guide and the test bench page
# quote the same feet, and a list in three places drifts (it did: the guide
# still said 3.6..4.2, from before the spacer and the glue)
HEIGHTS = tuple(round(D["H_min_foot_test"] + i*D["Pitch_foot_test"], 2) for i in range(int(D["N_foot_test"])))
TH_TAB = 1.6                    # the tab with the height written on it
r_hub = hub_radius()

def foot(h):
    # First all the solid - ring and tab - and then the voids. The other way
    # round, as it was written before, the tab was joined after the hole and
    # plugged it again: it went a millimetre into the magnet hole, for the
    # first 1.6 mm of height, that is exactly where the magnet must sit.
    # And the magnet did not go in.
    R = D["R_out_foot"]
    p = cq.Workplane("XY").circle(R).extrude(h)
    # the tab to take it in hand: it stops 2.4 mm inside the edge of the
    # ring, so it grips but stays away from the hole
    # it turns together with the module: the tab is always on the side
    # opposite the capacitor relief, otherwise one takes it in hand right there
    x0, x1 = -(R + 12.0), -(R - 2.4)
    tab = [((x0 + x1)/2 + dx, dy) for dx, dy in
            ((-(x1-x0)/2, -4.0), ((x1-x0)/2, -4.0), ((x1-x0)/2, 4.0), (-(x1-x0)/2, 4.0))]
    p = p.union(cq.Workplane("XY").polyline(rotate_points(tab, module_angle()))
                .close().extrude(TH_TAB))
    # magnet hole, screw holes
    p = p.cut(magnet_hole(D["D_hole_magnet_printing"] + D["Cl_test_magnet"], 0.0, h))
    for cx, cy in module_holes():
        p = p.cut(cq.Workplane("XY").workplane(offset=-1).center(cx, cy)
                  .circle((D["D_holes_M2"] + D["Cl_holes_M2_foot"])/2).extrude(h+2))
    # the board rests on the two pads, not on the plane: under it there are
    # its SMD components. Identical to the real bracket, otherwise the test
    # measures a rest the finished part does not have.
    # on the foot the plane is lowered everywhere except the pads, not only
    # under the board: outside the module it touches nothing and so it makes
    # no ridges
    round_ = [((R+1)*math.cos(math.radians(a)), (R+1)*math.sin(math.radians(a)))
             for a in range(0, 360, 5)]
    p = p.cut(module_notch(h, round_))
    # relief for the 104 capacitor, on the side opposite the tab: beyond
    # R_relief_capacitor it is cut straight, and the band left in front of the
    # cut goes down to H_bottom_relief. The module notch alone is not enough:
    # the 104 is taller than the three tenths that it leaves, and the board
    # rested on it instead of on the pads.
    rs, ys = D["R_relief_capacitor"], D["Halfw_relief"]
    cut = [(rs, -2*R), (rs + 2*R, -2*R), (rs + 2*R, 2*R), (rs, 2*R)]
    p = p.cut(cq.Workplane("XY").workplane(offset=-1)
              .polyline(rotate_points(cut, module_angle())).close().extrude(h + 2))
    band = [(0, -ys), (rs, -ys), (rs, ys), (0, ys)]
    p = p.cut(cq.Workplane("XY").workplane(offset=D["H_bottom_relief"])
              .polyline(rotate_points(band, module_angle())).close().extrude(h + 1))
    # text and tab turn together: it is composed in the measuring direction
    # and everything is turned as a block, otherwise the text ends up off the
    # tab
    text = (cq.Workplane("XY").workplane(offset=TH_TAB)
               .center(-R - 4.0, 0).text("%.1f" % h, 4.0, -0.4)
               .rotate((0, 0, 0), (0, 0, 1), module_angle()))
    return p.cut(text)

FEET_PITCH = 24.0


def feet_centres():
    """Where the centre of the ring of each foot falls, in a row on the bed.

    It serves the checks: before, they derived the centre from the bounding
    box, taking for granted that the capacitor cut was on +X. Since the module
    can be turned that inference is false, and a check that gets the centre
    wrong by four millimetres declares a plugged hole free."""
    return [(0.0, i*FEET_PITCH) for i in range(len(HEIGHTS))]


# The part is turned back by -Ang_module_on_bracket before putting it in the
# row. The inner geometry does not change - between relief, tab, pads and M2
# holes the relations stay those of the real bracket, and that is the only
# thing that counts on a loose tool - but the tab goes back to pointing at
# -X. Turned together with the module, it stuck out at -45 and the four feet
# interlaced in the row: the first reached y 9.9 and the second began at 5.6.
feet = [foot(h).rotate((0, 0, 0), (0, 0, 1), -module_angle())
        .translate((0, i*FEET_PITCH, 0)) for i, h in enumerate(HEIGHTS)]
cq.exporters.export(cq.Compound.makeCompound([p.val() for p in feet]),
                    OUT + "tools/gap_gauges.step")
print("gap gauges: %s (gap %s)"
      % (", ".join("%.1f" % h for h in HEIGHTS),
         ", ".join("%.2f" % (h - D["Th_spacer_magnet"] - D["Th_magnet"]
                             - D["Th_glue_stack_magnet"] - D["H_body_chip"])
                   for h in HEIGHTS)))

# ---------------- the grip test slice ------------------------------------
# A piece of the one-piece box, cut out of the real out/box_collar.step, with
# everything the grip cover mates with: the recess with its two end walls and
# the groove of the +y tongue, the two pads with the pockets of the tabs, the
# opening over the motor and the edge of the collar with the pocket of the
# screw. An hour of printing instead of the whole part, to try the cover in
# the hand - how it goes in, whether it stays put, whether the tabs hold -
# before committing the 120 g of the real one.
#
# Two regions joined: the sector round the recess, from the bottom of the pads
# up, and the slab of the roof over the whole door, down to z 20. They meet
# through the back and the roof, so it comes out as one piece.
#
# IT PRINTS ROOF DOWN, on the top face: the roof is flush with the collar, so
# that is one plane over the whole slice. Upside down the pads' 45 degree
# undersides face the nozzle, the splay stays at 45 degrees, and the floors of
# the pockets become 3 mm bridges. It is NOT the orientation of the real part,
# which prints on its floor: the fit it tests is the one of the shapes, the
# surface of the grooves will differ a little.
import math as _m
_part = cq.importers.importStep(OUT + "box_collar.step").val()
_a0f, _a1f = _m.radians(-16.0), _m.radians(17.0)
_pts_f = [(0.0, 0.0)] + [(140.0*_m.cos(_a0f + (_a1f - _a0f)*i/20), 140.0*_m.sin(_a0f + (_a1f - _a0f)*i/20))
                         for i in range(21)]
_sector_f = (cq.Workplane("XY").workplane(offset=-18.0).polyline(_pts_f).close()
              .extrude(18.0 + 30.0)
              .cut(cq.Workplane("XY").workplane(offset=-19.0).circle(105.0).extrude(50.0)))
_slab_f = cq.Workplane("XY").box(68.0, 64.0, 9.0).translate((98.0, 0.0, 24.5))
_slice = _sector_f.union(_slab_f).val().intersect(_part)
_solids_f = sorted(_slice.Solids(), key=lambda s: -s.Volume())
if len(_solids_f) != 1:
    print("test slice: %d bodies, the largest is kept (%.2f cm3); the others: %s"
          % (len(_solids_f), _solids_f[0].Volume()/1000,
             ", ".join("%.3f cm3" % (s.Volume()/1000) for s in _solids_f[1:])))
_slice = _solids_f[0]
if not _slice.isValid():
    raise SystemExit("grip test slice: invalid solid")
cq.exporters.export(cq.Workplane(obj=_slice), OUT + "tools/grip_test_slice.step")
_bf = _slice.BoundingBox()
print("grip test slice: %.1f cm3 -> %.0f g in ASA, %.0f x %.0f x %.0f, prints with the roof on the bed"
      % (_slice.Volume()/1000, _slice.Volume()*1.07e-3, _bf.xlen, _bf.ylen, _bf.zlen))
