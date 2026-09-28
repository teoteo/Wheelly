# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The whole assembly, in a single STEP with SEPARATE BODIES.

Why it is needed: the parts are generated one by one, each in its own file,
and as long as they are looked at one by one the mating errors do not show.
This file puts them all together in the same reference frame - origin at the
centre of the disc, z=0 on the camera-side face - and adds what we do not
print ourselves: the motor, the bearings, the screws, the spring, the magnet.
So the assembly opens in any CAD and the interpenetrations show.

The parts stay DISTINCT SOLIDS with a name each, not one fused block: it is
the only way to be able to hide, measure and move them one by one.

    python3 src/solids_assembly.py        ->  out/full_assembly.step

What is added here is modelled as an ENVELOPE SHAPE, not as the real part: a
screw is a cylinder with its head, a bearing is two rings. It serves to see
where things end up and whether they fit, not to draw the thread.
The only exception is the motor, which is the maker's STEP.
"""
import math, os, sys
import os
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parameters import D, out_subdir
from purchased import purchased_parts, axis_ends, along_z

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out") + os.sep
os.makedirs(OUT + "references", exist_ok=True)
# The motor is read from the project's purchased parts, not from Downloads:
# there it only existed on one machine.
MOTOR_STEP = os.path.join(os.path.dirname(HERE), "others", "14HS10-0404S.STEP")

Rd, Ia, off = D["R_disc"], D["Cd_motor"], D["Off_pivot"]
Px, Py = Rd, off                      # pivot
Mx, My = Ia, 0.0                      # motor axis
Hc = D["H_body"]
zm = -D["Z_face_motor"]            # motor seating face, z = -2.5


def part(part_name):
    return cq.importers.importStep(OUT + out_subdir(part_name) + part_name + ".step")


def envelope(v):
    """The envelope shape of a purchased part, from its entry in purchased.py.

    An envelope and not the real part: a screw is a cylinder with its head, a
    bearing two rings. It serves to see where things end up and whether they
    fit, not to draw the thread.
    """
    p0, p1, u = axis_ends(v)
    x, y = p0[0], p0[1]
    z0, z1 = p0[2], p1[2]
    length = math.dist(p0, p1)
    if v["shape"] == "square":
        s_ = (cq.Workplane("XY").workplane(offset=z0).center(x, y)
              .rect(v["side"], v["side"]).extrude(z1-z0))
    else:
        # along its own axis, which for nearly all is z but for the clutch
        # grub and its insert is horizontal
        s_ = cq.Workplane(obj=cq.Solid.makeCylinder(
            v["d"]/2, length, cq.Vector(*p0), cq.Vector(*u)))
    if "flange" in v:
        df, sense = v["flange"]
        th = D["Th_flange_bearing"]
        zf = z0 - th if sense < 0 else z1
        # The flange is a RING, not a solid disc: it is part of the outer ring
        # and its hole is the passage through which the inner ring is reached.
        # Modelled solid down to the pivot it said that nothing passes in
        # there, and instead the washer passes - which must press precisely on
        # the inner ring, without touching the outer one.
        s_ = s_.union(cq.Workplane("XY").workplane(offset=zf).center(x, y)
                      .circle(df/2).circle(D["D_in_flange_bearing"]/2)
                      .extrude(th))
        s_ = s_.cut(cq.Workplane("XY").workplane(offset=z0-th-1).center(x, y)
                    .circle(D["D_pivot_arm"]/2).extrude(z1-z0+2*th+2))
    if v.get("insert"):
        # A heat-set insert is a TUBE, drilled: solid, it read as a brass peg, and in the steps
        # before its screw a render could not show where the screw goes. The
        # bore is the nominal diameter of the thread, from the name - M2, M25
        # (M2.5), M3, M4 - so the screw that goes in fills it exactly and
        # the two do not overlap; the thread itself is not drawn.
        import re as _re
        _m = _re.search(r"_M(\d)(\d?)_", v["name"] + "_")
        if not _m:
            raise SystemExit("solids_assembly: the insert %s does not say its thread "
                             "(insert_M<n>_...)" % v["name"])
        _bore = float(_m.group(1)) + (float(_m.group(2)) / 10.0 if _m.group(2) else 0.0)
        if _bore >= v["d"]:
            raise SystemExit("solids_assembly: the insert %s is Ø%.2f outside and M%g "
                             "inside" % (v["name"], v["d"], _bore))
        s_ = s_.cut(cq.Workplane(obj=cq.Solid.makeCylinder(
            _bore/2, length, cq.Vector(*p0), cq.Vector(*u))))
    if v.get("head"):
        # The head lies beyond the given end: above z1 if the sense is +1,
        # below z0 if it is -1, as for the pivot screw, which is tightened
        # from below. The diameter and the height are catalogue values and
        # live in the parameters: written here by hand - 2.75 and 3.0 - nobody
        # saw them, and the head of the pivot screw, which is the lowest part
        # of the stack, was not in the model at all.
        # The size and the head type come from the entry: the M2 screws of the
        # reference build are COUNTERSUNK, the M2.5 and the M3 socket head. An
        # entry that does not declare them is one of the M3 screws of before,
        # and the default respects them.
        _size = v.get("size", "M3")
        _type = v.get("head_type", "socket")
        # Two tables and not one: the socket cylinder head and the countersunk
        # cone head of the same size do NOT have the same head. On the M3 they
        # are 5.5 x 3 against 6.0 x 1.65, and as long as there was only one
        # the countersunk screws of the board panel would have carried around
        # the socket head - which on top of that is the dimension the step of
        # the inner skirt around the pivot derives from.
        _tag = {"M2": "M2", "M2.5": "M25", "M3": "M3"}[_size]
        _family = "countersunk" if _type == "countersunk" else "screw"
        rt, ht = D["D_head_%s_%s" % (_family, _tag)]/2, D["H_head_%s_%s" % (_family, _tag)]

        sense = 1 if v["head"] > 0 else -1
        zt = z1 if sense > 0 else z0 - ht
        if not along_z(v):
            # a head off the z axis does not exist yet: the only horizontal
            # fastener is the grub, which has no head. Better to stop here
            # than to draw it in the wrong place.
            # Now there is one: the second screw of the grip
            # cover, square to the 45 degree chamfer. Its head goes along its
            # own axis, beyond the end the entry names, as the z case does.
            uu = cq.Vector(*u)*sense
            base = cq.Vector(*(p1 if sense > 0 else p0))
            if _type == "countersunk":
                s_ = s_.union(cq.Workplane(obj=cq.Solid.makeCone(v["d"]/2, rt, ht, base, uu)))
            else:
                s_ = s_.union(cq.Workplane(obj=cq.Solid.makeCylinder(rt, ht, base, uu)))
            return s_
        if _type == "countersunk":
            # A cone, not a cylinder: the countersunk head sinks into the part
            # instead of resting on it, and drawing it cylindrical would say
            # that room is needed where none is - and would keep quiet about
            # the conical lead-in the part must have.
            _r_low, _r_high = (v["d"]/2, rt) if sense > 0 else (rt, v["d"]/2)
            s_ = s_.union(cq.Workplane(obj=cq.Solid.makeCone(
                _r_low, _r_high, ht, cq.Vector(x, y, zt), cq.Vector(0, 0, 1))))
        else:
            s_ = s_.union(cq.Workplane("XY").workplane(offset=zt).center(x, y)
                          .circle(rt).extrude(ht))
    return s_


def spring():
    """The preload spring, on the axis perpendicular to the arm. The ends are
    not chosen: they are the two radii it rests at, on the side of the arm's
    plate and on the fixed bottom of the box."""
    ux, uy = (Mx-Px)/D["L_arm"], (My-Py)/D["L_arm"]
    nx, ny = -uy, ux
    if nx*Px + ny*Py < 0:
        nx, ny = -nx, -ny
    Qx, Qy = Px + ux*D["Att_spring"], Py + uy*D["Att_spring"]

    def s_at_radius(r):
        lo, hi = 0.0, 200.0
        for _ in range(80):
            mid = (lo+hi)/2
            if math.hypot(Qx+nx*mid, Qy+ny*mid) < r: lo = mid
            else: hi = mid
        return (lo+hi)/2

    s1 = s_at_radius(D["R_rest_spring_arm"])
    s2 = s_at_radius(D["R_seat_spring_box"])
    length = s2 - s1
    zc = D["Z_axis_spring"]      # no longer the mid-plane of the arm
    # from the parameters, not written here: the 7.9 / 1.0 / 6 turns that
    # stood here were the first spring's, written by hand
    d_mean, d_wire = D["D_spring_out"] - D["D_wire_spring"], D["D_wire_spring"]
    coils = int(D["N_coils_spring"]) - 1
    helix = cq.Wire.makeHelix(pitch=length/coils, height=length, radius=d_mean/2)
    section = (cq.Workplane("XZ").center(d_mean/2, 0).circle(d_wire/2))
    m = cq.Workplane(obj=cq.Solid.sweep(section.val(), [], helix, isFrenet=True)) \
        if False else cq.Workplane("XY").add(helix).wires().toPending()
    # explicit sweep: more predictable than the fluent chain
    profile = cq.Workplane("XZ").center(d_mean/2, 0).circle(d_wire/2).val()
    solid = cq.Solid.sweep(profile, [], helix, True)
    m = cq.Workplane(obj=solid)
    # the helix is born along +z at the origin: bring it onto the spring axis
    m = m.rotate((0, 0, 0), (0, 1, 0), 90)          # axis now along +x
    ang = math.degrees(math.atan2(ny, nx))
    m = m.rotate((0, 0, 0), (0, 0, 1), ang)
    m = m.translate((Qx + nx*s1, Qy + ny*s1, zc))
    return m, length


# --------------------------------------------------------------- the assembly
asm = cq.Assembly(name="wheelly")

# 1) what already exists, already in its place
for part_name, colour in (("filter_wheel_body", (0.72, 0.70, 0.78, 0.35)),
                     ("filter_disc", (0.23, 0.66, 0.56, 0.60)),
                     ("arm",           (0.82, 0.25, 0.48, 1.00)),
                     ("clutch_hub", (0.88, 0.54, 0.06, 1.00)),
                     ("clutch_tyre", (0.25, 0.25, 0.28, 1.00)),
                     # THE SINGLE PART, not its two halves. There used to be
                     # "collar" and "box" from out/references/ here: the
                     # assembly showed two bodies, and
                     # without the door and the pivot holes, which are cut AFTER
                     # the union (9.3 cm3 the halves do not have).
                     ("box_collar",    (0.78, 0.76, 0.82, 0.45)),
                     ("sensor_bracket",    (0.55, 0.70, 0.85, 1.00)),
                     ("sensor_cover", (0.40, 0.58, 0.76, 0.55)),
                     ("board_panel",        (0.78, 0.76, 0.82, 1.00)),
                     ("spring_cup",  (0.90, 0.60, 0.20, 1.00)),
                     # the cap of the grip: green, to tell it apart from the
                     # box it snaps into, which is the grey of the part
                     ("grip_cover",        (0.45, 0.72, 0.45, 1.00)),
                     # the cover of the hatch under the motor: violet, so that
                     # from below it does not read as part of the floor
                     ("hatch_cover",       (0.66, 0.52, 0.80, 1.00)),
                     ("pivot_washer",    (0.95, 0.75, 0.15, 1.00)),
                     ("front_gasket",  (0.20, 0.55, 0.35, 1.00)),
                     ("rear_gasket", (0.20, 0.55, 0.35, 1.00)),
                     ("sensor_cable",      (0.15, 0.15, 0.18, 1.00))):
    asm.add(part(part_name), name=part_name, color=cq.Color(*colour))

# 2) what comes out of the printer in its printing position and has to be put
# back in place. The magnet cap does NOT go in here: it is a tool, it holds
# the magnet square while the glue sets and then slides off. Put in the
# assembly it interpenetrated the ring of the sensor bracket by half a cubic
# centimetre, which is exactly the place the two contend for - and which
# neither of them really occupies at the same moment. The same holds for the
# gap gauges, which are a test jig.
#
# the spacer is exported in two copies side by side for printing: only one
# is taken, the one centred on the origin
spacer = [s for s in part("magnet_spacer").solids().vals()
          if abs(s.Center().x) < 5][0]
asm.add(cq.Workplane(obj=spacer).translate((0, 0, Hc)),
        name="magnet_spacer", color=cq.Color(0.85, 0.85, 0.88, 1.0))

# 3) the electronics, as ENVELOPES: XIAO and driver are the makers' models,
#    the rest are declared estimates (solids_electronics.py)
for part_name, colour in (("perfboard",  (0.20, 0.55, 0.30, 1.00)),
                     ("pin_sockets",  (0.10, 0.10, 0.10, 1.00)),
                     ("xiao",     (0.25, 0.30, 0.70, 1.00)),
                     ("driver",   (0.75, 0.15, 0.15, 1.00)),
                     ("components", (0.15, 0.25, 0.60, 1.00)),
                     ("led",      (0.85, 0.10, 0.10, 1.00)),
                     ("gx12",     (0.70, 0.70, 0.72, 1.00)),
                     ("gx12_nut", (0.55, 0.55, 0.58, 1.00))):
    asm.add(cq.importers.importStep(OUT + "electronics" + os.sep + part_name + ".step"),
            name="electronics_" + part_name, color=cq.Color(*colour))

# 4) the maker's motor. In its file the flange is at z=0 with the shaft
#    towards -z: half a turn about X brings it onto the seating face.
if os.path.exists(MOTOR_STEP):
    motor = (cq.importers.importStep(MOTOR_STEP)
             .rotate((0, 0, 0), (1, 0, 0), 180).translate((Mx, My, zm)))
    asm.add(motor, name="motor_14HS10-0404S", color=cq.Color(0.18, 0.44, 0.82, 1.0))
else:
    print("WARNING: %s is missing, the assembly comes out without the motor" % MOTOR_STEP)

# 5) all the rest of the purchased parts - bearings, screws, magnet - from the
#    entries of purchased.py, which is the same list the assembly views take
#    where to draw them from. Not the motor: that is the maker's file, and
#    hub and shaft are already included in there.
_count = {}
for _v in purchased_parts():
    if _v.get("main") or _v.get("inside_motor"):
        continue
    # the names in the assembly must be unique: the bearings are two and the
    # screws six, so they get numbered
    _n = _v["name"].replace(" ", "_")
    _count[_n] = _count.get(_n, 0) + 1
    # the heat-set inserts are brass and the screws steel: two colours, or
    # else in the render they are the same grey blot and one can no longer see
    # which part sits inside which
    _col = (0.72, 0.53, 0.20, 1.0) if _v.get("insert") else (0.55, 0.55, 0.58, 1.0)
    asm.add(envelope(_v), name="%s_%d" % (_n, _count[_n]), color=cq.Color(*_col))

# 8) the preload spring
m, length = spring()
asm.add(m, name="preload_spring", color=cq.Color(0.70, 0.70, 0.30, 1.0))

asm.save(OUT + out_subdir("full_assembly") + "full_assembly.step")
print("written out/full_assembly.step")
print("spring fitted: %.2f mm (parameter L_spring_fitted %.2f)" % (length, D["L_spring_fitted"]))
print("bodies: %d" % len(asm.children))
for c in asm.children:
    b = c.obj.val().BoundingBox() if hasattr(c.obj, "val") else c.obj.BoundingBox()
    print("   %-26s X %8.2f..%8.2f  Y %8.2f..%8.2f  Z %8.2f..%8.2f"
          % (c.name, b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax))
