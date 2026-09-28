# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Where the parts we do NOT print stand, and how big they are.

Motor, bearings, screws, magnet: their position is written here once, and
both places that show them read it - the STEP of the assembly
(solids_assembly.py) and the assembly views of the editor
(drawings_assembly.py). Two copies drift apart at the first touch-up, and the
second one lies without saying so.

Why a module of its own instead of inside solids_assembly.py: that one
imports CadQuery, and the 2D drawings must be able to run without OCCT -
that is the promise of `build.py --solo-dxf`. In here there is nothing more
than arithmetic.

Each entry is a dictionary:

    name     what it is called in the drawing
    shape    "square" or "round"
    xy       where it stands, in the project's frame (origin = disc centre)
    side/d   the side of the square or the diameter of the round
    z        (from, to) along the axis: z=0 is the camera-side face, +z goes
             in. For screws it is the SHANK: the head is added beyond the end
    start/axis/length  for the fasteners that do NOT lie along z, like the
             clutch grub, which is horizontal: the starting point in three
             coordinates, the unit vector of the axis and the length. Whoever
             reads these entries must not need to know which of the two forms
             was used: they ask axis_ends(), which is the only place that
             knows both
    flange   for the bearings: (diameter, direction) - the direction says
             which way it sticks out, -1 towards the camera and +1 towards
             the body
    head     the screw has its head beyond the end given
    passes_through  the parts this fastener goes through by trade: a screw
             passes inside the holes of the parts it holds together, an
             insert sits in its seat with the intended interference. Whoever
             checks collisions must skip them, or every fastener reports
             itself - and it happened at the first build after adding them
    inside_motor  already part of the maker's model: in the STEP of the
             assembly it is not added, in the drawings it is
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parameters
from parameters import D, spring_axis, s_spring_axis


class _Entries(list):
    """The list of purchased parts, which signs each entry as it receives it.

    It serves whoever draws: the dimension signature (see
    `dimension_signature.py`) attaches to each entity the parameters read to
    build it, but the assembly views ask for the WHOLE list before drawing its
    first part. The reads of sixty-six parameters thus ended up on the first
    entity drawn - the motor also carried the angles of the ears and the
    screws of the collar - and a signature of sixty-six names narrows nothing
    any more: it was the defect called "fixed signature".

    Here the signature is taken entry by entry, at the point where the entry
    is added: the arguments of the `dict` have already been evaluated, so the
    parameters of that part have already been read and no others. Whoever
    draws then signs the entity with `v["_dims"]` instead of with the current
    tracker.

    With the tracker off - outside the drawings - `read_and_reset_tracker`
    returns empty and costs nothing.
    """

    def append(self, v):
        v["_dims"] = parameters.read_and_reset_tracker()
        list.append(self, v)


def pol(r, degrees):
    a = math.radians(degrees)
    return (r * math.cos(a), r * math.sin(a))


def axis_ends(v):
    """The two ends of the part's axis, in three coordinates, and its unit
    vector.

    Almost all fasteners lie along z and are described with xy and z; the
    clutch grub does not, and as long as this module could only describe
    parts along z the grub - which is the only thing holding the clutch on
    the shaft - was neither in the assembly nor in the BOM. Whoever draws or
    measures a fastener asks for the ends here instead of reading v["z"], so
    the new case does not have to be added in five places.
    """
    if "axis" in v:
        p0, a, lu = v["start"], v["axis"], v["length"]
        n = math.sqrt(sum(c*c for c in a)) or 1.0
        u = tuple(c/n for c in a)
        return p0, tuple(p0[i] + u[i]*lu for i in range(3)), u
    x, y = v["xy"]
    z0, z1 = v["z"]
    return (x, y, z0), (x, y, z1), (0.0, 0.0, 1.0)


def along_z(v):
    """Whether the part lies along the z axis, like the vast majority."""
    return abs(axis_ends(v)[2][2]) > 0.999


def purchased_parts():
    zm = -D["Z_face_motor"]                 # face the motor rests on
    Px, Py = D["R_disc"], D["Off_pivot"]      # pivot
    Mx, My = D["Cd_motor"], 0.0               # motor axis
    hh = D["Cd_holes_motor"] / 2
    Hc = D["H_body"]
    entries = _Entries()

    # --- the motor, and what sticks out of it -----------------------------
    entries.append(dict(name="motor_NEMA14", shape="square", xy=(Mx, My),
                        side=D["Side_motor"], z=(zm - D["L_motor"], zm),
                        main=True))
    # The centring boss goes into the arm's seat: it is what centres the
    # motor, not the screws, and it is the piece of geometry that revealed the
    # seat cut on the wrong face.
    entries.append(dict(name="centring_hub", shape="round", xy=(Mx, My),
                        d=D["D_circle_motor"], z=(zm, zm + D["H_circle_motor"]),
                        inside_motor=True))
    # The shaft goes through the arm and into the clutch hub: it is the chain
    # that carries the motion to the disc, and in section it must be visible.
    # `flat` carries the NAME of the dimension, not its value: whoever draws
    # reads it from D at drawing time, and so the entity comes out signed with
    # that dimension. With the value written in, the drawing contained the
    # plane of the flat but did not say where it came from, and the editor
    # went back to guessing.
    #
    # The shaft has the FLAT, and it is on that the grub presses: drawn as a
    # plain round, the plane on which the whole locking rests existed in no
    # drawing, and whoever looked for that dimension in plan ended up on two
    # circles that were worth 2.00 by chance.
    entries.append(dict(name="shaft", shape="round", xy=(Mx, My),
                        d=D["D_shaft"], z=(zm, zm + D["L_shaft"]),
                        flat="Z_flat_shaft", inside_motor=True))

    # --- the two bearings on the pivot ------------------------------------
    # The flanges stay outside the seat, one per face: they are the axial
    # reference, and it is for the body-side flange that the collar hub has
    # the counterbore.
    #
    # FROM THE BOTTOM OF THE ARM, not from the motor face. The two
    # were the same z until the plate got its step: then zm went to -1.5 while
    # the hub of the pivot stayed at Z_bottom_arm, and the bearings were drawn
    # 4.5 mm above their seat, half out of the arm - visibly staggered in the
    # assembly. The seat is cut z0..z0+Th_arm in solids_arm.py, so the
    # bearings take the same z0.
    half = D["H_bearings"] / 2
    _z0a = D["Z_bottom_arm"]
    for dz, direction in ((0.0, -1), (half, +1)):
        entries.append(dict(name="bearing_F695ZZ", shape="round", xy=(Px, Py),
                            d=D["D_seat_bearings"], z=(_z0a + dz, _z0a + dz + half),
                            flange=(D["D_flange_bearing"], direction)))

    # --- THE SMALL STUFF: heat-set inserts and screws ---------------------
    # These go into the assembly too. It is not to look good
    # in the render - it is that what the model does not contain no check can
    # see. Without the screw you cannot see whether the head has room, whether
    # the key reaches it, whether the tip comes out the other side; without
    # the insert you cannot see the wall left round it. In this project a
    # missing screw has already hidden a defect: the pivot's existed only in a
    # comment, and put into the solid it turned out to be twelve millimetres
    # too long.
    #
    # The heads are the ones of the reference build: M2 COUNTERSUNK, M2.5 and M3
    # SOCKET HEAD. It is not an aesthetic detail: the countersunk head
    # disappears into the thickness and wants the conical lead-in, the socket
    # head rests flat and wants room for the key.
    import electronics as _E

    # the two posts of the panel: M2 insert and countersunk screw coming down
    # into it through the board
    for _s, _t in _E.board_holes():
        _x, _y = _E.xy(_s, _t)
        entries.append(dict(name="insert_M2_post", shape="round",
                            xy=(_x, _y), d=D["D_out_insert_M2"],
                            z=(_E.Z_BOARD - D["L_insert_M2"], _E.Z_BOARD),
                            insert=True, passes_through=("board_panel",)))
        entries.append(dict(name="screw_M2_board", shape="round",
                            xy=(_x, _y), d=2.0,
                            z=(_E.Z_BOARD - D["L_insert_M2"],
                               _E.Z_BOARD + D["Th_board"]),
                            head=+1, size="M2", head_type="countersunk",
                            passes_through=("perfboard", "board_panel")))

    # the third screw of the board, at the cut end: M2.5 insert in the panel's
    # post and a socket-head screw coming down into it through hole B05, which
    # is opened on the perfboard. It is M2.5 and not M2 like the other two
    # because that size is at hand with a socket head: above the board the
    # head has eleven millimetres before the underside of the XIAO, so there
    # is no need to countersink it.
    _s3, _t3 = _E.board_head_screw()
    _x3, _y3 = _E.xy(_s3, _t3)
    entries.append(dict(name="insert_M25_head_post", shape="round",
                        xy=(_x3, _y3), d=D["D_out_insert_M25"],
                        z=(_E.Z_BOARD - D["L_insert_M25"], _E.Z_BOARD),
                        insert=True, passes_through=("board_panel",)))
    entries.append(dict(name="screw_M25_board", shape="round",
                        xy=(_x3, _y3), d=2.5,
                        z=(_E.Z_BOARD - D["L_insert_M25"],
                           _E.Z_BOARD + D["Th_board"]),
                        head=+1, size="M2.5", head_type="socket",
                        passes_through=("perfboard", "board_panel")))

    # the three screws of the panel: the M3 insert sits in the boss of the
    # BOX and is planted from the face of the step, so it grows inwards. The
    # step is no longer at half the wall: in the screw zones the panel is
    # Th_panel_screws thick, and the OUTER face of the floor - where the head
    # rests - is that height minus that thickness. So it stays a relation and
    # not a -38 written by hand.
    for _s, _t in _E.panel_screws():
        _x, _y = _E.xy(_s, _t)
        entries.append(dict(name="insert_M3_panel", shape="round",
                            xy=(_x, _y), d=D["D_out_insert_M3"],
                            z=(_E.Z_SCREWS, _E.Z_SCREWS + D["L_insert_M3"]),
                            insert=True, passes_through=("box",)))
        entries.append(dict(name="screw_M3_panel", shape="round",
                            xy=(_x, _y), d=3.0,
                            z=(_E.Z_SCREWS - D["Th_panel_screws"],
                               _E.Z_SCREWS + D["L_insert_M3"]),
                            head=-1, size="M3", head_type="countersunk",
                            passes_through=("board_panel", "box")))

    # the two screws of the cover of the hatch under the motor: the same
    # scheme as the panel - insert planted from below into the raised floor,
    # countersunk screw through the ear of the cover. Where they stand comes
    # from outline_motor.hatch(), which is also what cuts them in the part.
    import outline_motor as _SM
    for _x, _y, _l in _SM.hatch()["screws"]:
        entries.append(dict(name="insert_M3_hatch", shape="round",
                            xy=(_x, _y), d=D["D_out_insert_M3"],
                            z=(_E.Z_SCREWS, _E.Z_SCREWS + D["L_insert_M3"]),
                            insert=True, passes_through=("box",)))
        entries.append(dict(name="screw_M3_hatch", shape="round",
                            xy=(_x, _y), d=3.0,
                            z=(_E.Z_SCREWS - D["Th_panel_screws"],
                               _E.Z_SCREWS + D["L_insert_M3"]),
                            head=-1, size="M3", head_type="countersunk",
                            passes_through=("hatch_cover", "box")))

    # the two screws of the sensor cover: the M2.5 insert sits in the boss of
    # the bracket, the screw comes down from the cover.
    #
    # THE POSITIONS MUST BE ROTATED. Here there was pol(R_boss, ±45), that is
    # the NON-rotated frame of the bracket: the bracket however is mounted
    # turned by Ang_bracket_sensor, and at r 40 five degrees are three and a
    # half millimetres. In the assembly view screws and inserts were not
    # centred on their holes, and it showed on the drawing. It is
    # the same mistake - an angle copied by hand into one place only - that
    # had already put the bosses outside the arms. Now the centres come from
    # drawings.boss_centre(), which is also what cuts them, and the rotation
    # is done here at the end, once: so the offset boss of the cable arm
    # carries it along by itself.
    from drawings import cover_bosses as _bosses, boss_centre as _boss_centre
    _a_st = math.radians(D["Ang_bracket_sensor"])
    _z_plate = (Hc + D["H_rest_module"] + D["H_boss_cover_sensor"])
    for _phi, _transv in _bosses():
        _xl, _yl = _boss_centre(_phi, _transv)
        _x = _xl*math.cos(_a_st) - _yl*math.sin(_a_st)
        _y = _xl*math.sin(_a_st) + _yl*math.cos(_a_st)

        entries.append(dict(name="insert_M25_cover", shape="round",
                            xy=(_x, _y), d=D["D_out_insert_M25"],
                            z=(_z_plate - D["L_insert_M25"], _z_plate),
                            insert=True, passes_through=("sensor_bracket",)))
        entries.append(dict(name="screw_M25_cover", shape="round",
                            xy=(_x, _y), d=2.5,
                            z=(_z_plate - D["L_insert_M25"],
                               _z_plate + D["Th_cover_sensor"]),
                            head=+1, size="M2.5", head_type="socket",
                            passes_through=("sensor_cover", "sensor_bracket")))

    # the two screws of the AS5600 module (from the real assembly): M2
    # COUNTERSUNK, driven with a PH0 through the module's holes
    # into the pilot holes of the bracket hub (D_holes_M2, the screw forms its
    # own thread). They were never in the model - the bracket had the holes,
    # the guide never said how the module was held, and the bill lacked them.
    # Where they stand is the same module_holes() that cuts the holes, turned
    # by the bracket's angle like the cover bosses above. Along z the shank
    # ends on top of the board - the board rests at Hc + H_rest_module and is
    # Th_board_module thick - and goes L_screw_M2 down from there: the length
    # is the parameter the dimension checks already guard (grip in the boss,
    # never out under the hub), not a number written here. The module itself
    # is not modelled: the upper Th_board_module of the shank stands in the air
    # where its board would be.
    from drawings import module_holes as _module_holes
    _z_board_top = Hc + D["H_rest_module"] + D["Th_board_module"]
    for _xl, _yl in _module_holes():
        _x = _xl*math.cos(_a_st) - _yl*math.sin(_a_st)
        _y = _xl*math.sin(_a_st) + _yl*math.cos(_a_st)
        entries.append(dict(name="screw_M2_module", shape="round",
                            xy=(_x, _y), d=2.0,
                            z=(_z_board_top - D["L_screw_M2"], _z_board_top),
                            head=+1, size="M2", head_type="countersunk",
                            passes_through=("sensor_bracket",)))

    # --- the screw that holds the pivot together --------------------------
    # It comes down from the insert at the top of the hub to below the
    # washer, and it is the lowest part of the whole pivot stack: it is its
    # head that says how far down the inner skirt of the box has to cut its
    # step. It was only in a comment, and so the model did not know it
    # existed: the skirt stopped twelve millimetres lower than needed, in the
    # name of a clearance no check could measure.
    # The upper end is the top of the hub, where it bites in the insert; the
    # lower one is the underside of the washer, and beyond it is the head. The
    # first attempt made it reach z 19.6, twelve millimetres beyond the top of
    # the hub, and the check of the clearance under the roof of the bay found
    # it.
    entries.append(dict(name="screw_M3_pivot", shape="round", xy=(Px, Py),
                        # under the washer, which sits under the ARM (Z_bottom_arm),
                        # not under the motor face: from zm the screw came out
                        # 4.5 mm short, an M3 x 15.5 that does not exist
                        # ...and up to its TIP, L_screw_pivot above the head: the
                        # insert's mouth is half a millimetre higher on purpose
                        # (Z_mouth_insert_pivot), and ending the screw there made
                        # the BOM ask for 20.5 under the head, an M3 x 25 - the
                        # M3 x 20 is kept, it is enough
                        d=3.0, z=(D["Z_bottom_arm"] - D["Th_washer_pivot"],
                                  D["Z_bottom_arm"] - D["Th_washer_pivot"] + D["L_screw_pivot"]),
                        head=-1))
    # ...and the insert that screw bites in, at the top of the collar hub.
    # The screw was there and the insert was not: the BOM read "M3 pivot
    # screw" and nobody would have bought the insert it screws into.
    entries.append(dict(name="insert_M3_pivot", shape="round", xy=(Px, Py),
                        d=D["D_out_insert_M3"],
                        z=(D["Z_mouth_insert_pivot"] - D["L_insert_M3"],
                           D["Z_mouth_insert_pivot"]),
                        insert=True, passes_through=("collar",)))

    # --- the insert and the socket head M3 that hold the cover shut --------
    # The insert sits in the collar, next to the straight
    # edge of the door, under the pocket of the tab; the screw goes down
    # through the tab, its knurled socket head on top of it, proud of the
    # roof so it turns by hand (it was countersunk). The numbers come from
    # the same parameters the generator takes them from.
    _xi = D["Edge_opening_motor_box"] - D["D_out_insert_M3"]/2 - D["Wall_insert_cover"]
    _yi = D["Off_insert_cover"]
    _z_roof = D["Z_shoulder_box"] + D["Th_walls_box"]
    _z_pocket = _z_roof - D["Th_tab_cover"] - D["Cl_cover_grip"]
    entries.append(dict(name="insert_M3_cover", shape="round", xy=(_xi, _yi),
                        d=D["D_out_insert_M3"],
                        z=(_z_pocket - D["L_insert_M3"], _z_pocket),
                        insert=True, passes_through=("box_collar",)))
    entries.append(dict(name="screw_M3_cover", shape="round", xy=(_xi, _yi), d=3.0,
                        z=(_z_roof - D["L_screw_cover"], _z_roof),
                        head=+1, size="M3", head_type="socket",
                        passes_through=("grip_cover", "box_collar")))

    # --- the SECOND cover screw, at the corner of collar and arc, -y side ---
    # Vertical like the first, through the round tab of
    # the cover into an insert in the collar; where it is comes from
    # parameters.fillet_screw, which is also what the generator cuts. It was
    # square to the 45 degree chamfer, into a boss behind it, for a few hours.
    from parameters import fillet_screw as _fs
    _xv2, _yv2, _ = _fs()
    entries.append(dict(name="insert_M3_cover", shape="round", xy=(_xv2, _yv2),
                        d=D["D_out_insert_M3"],
                        z=(_z_pocket - D["L_insert_M3"], _z_pocket),
                        insert=True, passes_through=("box_collar",)))
    entries.append(dict(name="screw_M3_cover", shape="round", xy=(_xv2, _yv2), d=3.0,
                        z=(_z_roof - D["L_screw_cover"], _z_roof),
                        head=+1, size="M3", head_type="socket",
                        passes_through=("grip_cover", "box_collar")))

    # --- the ears: THEY ARE GONE ------------------------------------------
    # Here stood five M3 screws and five heat-set inserts, the largest group
    # of fasteners of the machine: they held the box screwed to the collar.
    # Now box and collar are one part and there is nothing left
    # to screw. Ten parts out of the BOM, and ten steps fewer in assembly.

    # --- the grub that locks the clutch on the shaft, and its insert ------
    # They are HORIZONTAL, along +Y, and that is why they were missing: the
    # entries could only describe parts along z. The grub is the only thing
    # holding the clutch on the shaft, so not being able to put it in the
    # assembly meant that no check could see whether it fits, whether the key
    # reaches it and whether the tip really reaches the flat.
    #
    # The insert sits at the bottom of the seat, which starts where the
    # channel narrows to the clearance hole; the grub starts from the plane of
    # the shaft's flat - where its tip presses - and reaches the outer end of
    # the insert, which is how long it must be to take the thread.
    _y_seat = D["D_collar_grub"]/2 - (D["L_insert_M3"] + 0.5)
    entries.append(dict(name="insert_M3_grub", shape="round",
                        d=D["D_out_insert_M3"], xy=(D["Cd_motor"], _y_seat),
                        start=(D["Cd_motor"], _y_seat, D["Z_insert_grub"]),
                        axis=(0.0, 1.0, 0.0), length=D["L_insert_M3"],
                        # passes_through names the BODY of the assembly it goes
                        # through: "clutch_hub", the ASA hub the insert is
                        # planted in. It said "frizione", the part's Italian
                        # name, which matched no body - an entry nobody read,
                        # because check_audit.py compares it only with the
                        # electronics bodies. Named right, it stays true the
                        # day a check compares it with the others.
                        insert=True, passes_through=("clutch_hub",)))
    # The SPRING PRELOAD: an M4 grub pushing on the back of the spring cup,
    # screwed into a heat-set insert planted at the mouth of the boss. They
    # were the only fasteners of the machine the model did not contain: the
    # parameters were there, the seat in the boss too, the checks watched them
    # - but nobody drew them, and so they were missing from the BOM as well.
    # It showed in chapter 0 of the guide, where the screw was not there. It is the fourth time a fastener is missing from
    # the roll call: whoever adds a seat in a solid must add here the part
    # that goes in it.
    #
    # The dimensions are not rewritten: the axis is the one of spring_axis(),
    # the row inside the boss and its length are the same sums as in
    # solids_box.py, and the back of the spring cup is where solids_box.py
    # puts it - S0 plus the thickness of the cup.
    _Qmx, _Qmy, _mnx, _mny, _zmm = spring_axis()
    _S0m = s_spring_axis(D["R_seat_spring_box"])
    _travel, _th_cup = D["Travel_preload"], D["Th_cup_spring"]
    _row = (2*_travel + _th_cup) + D["Dp_seat_insert_M4"] + D["Th_retain_insert_M4"]
    _L_boss = max(s_spring_axis(D["R_out_box"]) - (_S0m - _travel) + 1.0, _row)
    _s_mouth = (_S0m - _travel) + _L_boss         # the face it is screwed in from
    _s_back = _S0m + _th_cup                      # the back of the spring cup
    # The insert no longer starts at the face of the boss: from there inwards
    # there is first the wall that retains it, Th_retain_insert_M4, because it
    # is now planted from INSIDE and works in compression against that wall.
    _s_insert = _s_mouth - D["Th_retain_insert_M4"]
    entries.append(dict(name="insert_M4_preload", shape="round",
                        d=D["D_out_insert_M4"],
                        xy=(_Qmx + _mnx*_s_insert, _Qmy + _mny*_s_insert),
                        start=(_Qmx + _mnx*_s_insert, _Qmy + _mny*_s_insert, _zmm),
                        axis=(-_mnx, -_mny, 0.0), length=D["L_insert_M4"],
                        insert=True, passes_through=("box",)))
    # `span` is (Italian, English) text that ends up in the BOM: the Italian
    # half is the Italian localisation, and stays.
    entries.append(dict(name="grub_M4_preload", shape="round",
                        d=D["D_grub_spring"],
                        xy=(_Qmx + _mnx*_s_back, _Qmy + _mny*_s_back),
                        start=(_Qmx + _mnx*_s_back, _Qmy + _mny*_s_back, _zmm),
                        axis=(_mnx, _mny, 0.0), length=_s_mouth - _s_back,
                        grub=True, size="M4",
                        span=("dal dorso dello scodellino all'imbocco del bosso",
                              "from the back of the spring cup to the mouth of "
                              "the boss"),
                        passes_through=("box", "spring_cup")))
    entries.append(dict(name="grub_M3_clutch", shape="round",
                        d=D["D_grub"], xy=(D["Cd_motor"], D["Z_flat_shaft"]),
                        start=(D["Cd_motor"], D["Z_flat_shaft"], D["Z_insert_grub"]),
                        axis=(0.0, 1.0, 0.0),
                        length=_y_seat + D["L_insert_M3"] - D["Z_flat_shaft"],
                        grub=True, size="M3",
                        span=("dalla fresata dell'albero all'inserto",
                              "from the shaft flat to the insert"),
                        # the hub it is screwed through (same reason as the
                        # insert above), and the shaft whose flat it presses
                        # on - which in the assembly is inside the maker's
                        # motor body, not a body of its own
                        passes_through=("clutch_hub", "shaft")))

    # --- the screws -------------------------------------------------------
    # The motor's go in from the body side into the motor's threaded holes;
    # the collar's take the M3s already in the base plate and also clamp the
    # paddles of the sensor bracket.
    #
    # The head sits ON THE TOP OF THE MOTOR PLATE, zm + Th_plate_motor, and the
    # shank is L_screw_motor long. It was z=(zm - 4, 0): the head
    # at a literal 0, which was the top of the plate when the plate was 8 thick
    # and the motor face at -8. With the plate stepped to 3.5 and raised, the
    # head stayed at 0 and was drawn INSIDE the plate - the screws visibly
    # collided in the assembly. Z_face_motor itself is derived from a head
    # standing on the plate top, so this is the same relation, not a new one.
    _z_head_m = zm + D["Th_plate_motor"]
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        entries.append(dict(name="screw_M3_motor", shape="round",
                            xy=(Mx + sx * hh, My + sy * hh), d=3.0,
                            z=(_z_head_m - D["L_screw_motor"], _z_head_m),
                            head=+1))
    for a in (D["Ang_screw_A"], D["Ang_screw_B"]):
        entries.append(dict(name="screw_M3_collar", shape="round",
                            xy=pol(D["R_screw_anchor"], a), d=3.0,
                            z=(Hc - 6.0, Hc + D["Th_flange_collar"] + 3.43),
                            head=+1))

    # --- the magnet, on the spacer, telescope side --------------------------
    z_mag = Hc + D["Th_spacer_magnet"] + D["Th_glue_stack_magnet"]
    entries.append(dict(name="magnet_AS5600", shape="round", xy=(0.0, 0.0),
                        d=D["D_magnet"], z=(z_mag, z_mag + D["Th_magnet"])))
    return entries
