# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The cable route on the sensor bracket.

Four requirements, from a review of the bracket seen from above, each measured
here on the printed solid (sensor_bracket.step), never on the shapes in
drawings.py that built it:

  1. the wire passage one millimetre wider - and still a passage: open on top,
     with its floor and its walls;
  2. the cable arm widened to the edges of its two pads (red lines);
  3. the two walls rounded where the passage opens into the capacitor window
     (green lines) - rounded only as deep as the passage;
  4. a groove UNDER the arm from one tie slot to the other: the arm rests on
     the face of the wheel body, and a tie passing under it would lift the
     bracket by its thickness.

Each probe asks a thing and its opposite - void where the change took
material away, material right next to it - because a probe that only asks for
void also passes when the whole part is missing there.

Runs outside check_audit.py so that it can be broken on purpose in seconds.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D
from drawings import cable_arm, wire_passage_mouth, mouth_step

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
BRACKET = OUT + "sensor_bracket.step"

ok, ko = [], []


def T(name, cond, det=""):
    (ok if cond else ko).append("%-52s %s" % (name, det))


st = cq.importers.importStep(BRACKET).val()
Hc = D["H_body"]
ZF = Hc + D["H_rest_module"]                   # top face of the arm, Z_FACE_IN
H = D["H_passage_wires"]
phi = math.radians(cable_arm() + D["Ang_bracket_sensor"])
ux, uy = math.cos(phi), math.sin(phi)


def full(r, t, z):
    """Material at radial r and across t on the cable arm, at height z."""
    p = cq.Vector(r*ux - uy*t, r*uy + ux*t, z)
    return st.intersect(cq.Solid.makeSphere(0.1, p)).Volume() > 1e-12


def verdict(name, expected):
    """expected: [(description, r, t, z, wants_material)]"""
    wrong = ["%s (r %.1f t %+.1f z %.2f)" % (d, r, t, z)
              for d, r, t, z, v in expected if full(r, t, z) != v]
    T(name, not wrong, "; ".join(wrong[:3]))


# 1) the passage: void inside its width, walls just outside it, floor under it
w = D["W_passage_wires"]/2
verdict("cable route: the wire passage is W_passage_wires wide",
      [("void inside", r, s*(w - 0.25), ZF - 0.5, False) for r in (20.0, 30.0) for s in (-1, 1)]
      + [("wall outside", r, s*(w + 0.35), ZF - 0.5, True) for r in (20.0, 30.0) for s in (-1, 1)]
      + [("floor under", r, 0.0, ZF - H - 0.4, True) for r in (20.0, 30.0)])

# 2) the widened arm, on both sides, every 3 mm along its length. The first
#    version probed only near the two ends, and a stretch taken out of the
#    middle - the fault it was broken with - passed unseen.
b1 = D["Off_boss_cable"] + D["D_boss_cover_sensor"]/2 + 1.0
b0 = -D["W_pad_tie"]/2
r0 = D["R_end_widening_relief"]
_along = lambda a, b: [a + k*3.0 for k in range(int((b - a)/3.0) + 1)]
verdict("cable route: the arm reaches the red lines",
      [("widened, boss side", r, b1 - 0.4, Hc + 1.0, True)
       for r in _along(r0 + 0.5, D["R_boss_cover_sensor"] - 5.0)]
      + [("widened, far side", r, b0 + 0.4, Hc + 1.0, True)
         for r in _along(r0 + 0.5, D["R_tie_cable"] - 5.0)]
      + [("no further", r0 + 5.0, b1 + 0.5, Hc + 1.0, False),
         ("no further", r0 + 5.0, b0 - 0.5, Hc + 1.0, False)])

# 3) the mouth: void in the corner above the passage floor, the arc reaching
#    as far along the wall as a radius of TWICE the step does, and the corner
#    still full below the floor. The second probe is the one that knows the
#    radius: two millimetres short of the tangent point (4.07 from the window)
#    the new arc is still 0.45 off the wall, while the old one, at one step
#    (2.35), had already closed to 0.02 there. One millimetre short would not
#    do: the arc is only 0.11 off the wall by then, and the probe sat on it.
corners, rf = wire_passage_mouth()
sg = mouth_step()
lb = math.sqrt(2*rf*sg - sg*sg)
verdict("cable route: the mouth of the passage is rounded, twice the step",
      [("corner gone", rc + 0.3, tc + s*0.3, ZF - 0.5, False) for rc, tc, s in corners]
      + [("still cut 2 mm short of the tangent", rc + lb - 2.0, tc + s*0.15, ZF - 0.5, False)
         for rc, tc, s in corners]
      + [("wall past the tangent", rc + lb + 0.5, tc + s*0.3, ZF - 0.5, True) for rc, tc, s in corners]
      + [("full below the floor", rc + 0.3, tc + s*0.3, ZF - H - 0.5, True) for rc, tc, s in corners])

# 4) the groove under the pad: void from slot to slot at the underside,
#    material above it, and material outside the slots, where the tie pulls
rt, gd = D["R_tie_cable"], D["Dp_groove_tie"]
outside_slot = D["Cd_slots_tie"]/2 + D["H_slot_tie"]/2 + 0.8
verdict("cable route: a groove under the arm joins the tie slots",
      [("groove", rt, t, Hc + 0.3, False) for t in (-2.0, 0.0, 2.0)]
      + [("roof of the groove", rt, 0.0, Hc + gd + 0.4, True)]
      + [("wall outside the slot", rt, s*outside_slot, Hc + 0.3, True) for s in (-1, 1)])

# 5) no slit where the boss pad meets the tie pad. The strip used to stop
#    on the boss side stopped at the boss, and between the slanted end of the
#    boss pad and the start of the tie pad a wedge 0 to 0.3 mm wide went right
#    through the plate. Probed every tenth of a millimetre across that
#    junction, at the bottom and near the top of the plate.
rt0 = D["R_tie_cable"] - D["L_pad_tie"]/2
verdict("cable route: no slit between the boss pad and the tie pad",
      [("junction", rt0 + 0.1*k, t, z, True)
       # up to r 45.4: the strip ends at r 46 in a corner rounded at 1.5
       # (check 6), whose fillet starts 1.5 before it
       for k in range(-15, 5) for t in (b1 - 3.0, b1 - 1.5, b1 - 0.6)
       for z in (Hc + 0.6, ZF - 0.6)])

# 6) the convex vertical edges of the cable arm are rounded. The corners are
#    worked out from the dimensions that BUILD the arm, not from the edge
#    search in solids_sensor.py that does the rounding: a check that finds
#    its corners with the same search would round nothing and see nothing.
#    At each corner, 0.3 mm in along the diagonal is air if it is rounded and
#    material if it is sharp; a little past R (sqrt 2 - 1) it is material, or
#    the fillet ate the wall.
rf2 = D["Fil_edges_arm_cable"]
r_str0 = D["R_end_widening_relief"] - 1.0          # start of the strips
r_tie1 = D["R_tie_cable"] + D["L_pad_tie"]/2       # end of the tie pad
r_str1 = D["R_tie_cable"] - D["L_pad_tie"]/2 + 1.0 # end of the boss-side strip
w_tie = D["W_pad_tie"]/2
edges = [(r_str0, b1, +1, -1), (r_str1, b1, -1, -1),
           (r_tie1, w_tie, -1, -1), (r_tie1, -w_tie, -1, +1)]
_q = 1/math.sqrt(2)
verdict("cable route: the convex edges of the cable arm are rounded",
      [("corner rounded", r + dr*0.3*_q, t + dt*0.3*_q, Hc + 2.5, False)
       for r, t, dr, dt in edges]
      + [("wall behind the fillet", r + dr*(rf2*(math.sqrt(2) - 1) + 0.4)*_q,
          t + dt*(rf2*(math.sqrt(2) - 1) + 0.4)*_q, Hc + 2.5, True)
         for r, t, dr, dt in edges])

print("--- OK (%d) ---" % len(ok))
[print("  ", r) for r in ok]
print("--- TO FIX (%d) ---" % len(ko))
[print("  !", r) for r in ko]
