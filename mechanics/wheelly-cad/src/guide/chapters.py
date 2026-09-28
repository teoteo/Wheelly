# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The chapters of the assembly guide: what is mounted, in what order, and how
it is framed.

Here there is ONLY the sequence - the knowledge that is not in the model: which
part first and which after, from which side it goes in, which tool it needs.
Everything else - the measures, the quantities, the short names of the screws -
is not written here: it is asked of the model when the guide is generated. A
number copied by hand into a step comes loose from the part at the first
touch-up, and nobody notices until somebody assembles the machine with the
guide in hand.

The texts are in English: the guide is the part of the project that gets
published.

Every step is a dictionary:

    title    the bold line of the step
    points   the bulleted lines, in English. They may contain {placeholders}
             filled with measures taken from the model (see measures() in
             write.py)
    mounts   the assembly bodies that ARRIVE in this step: the chapter's bill
             of materials comes from here, and from nowhere else
    context  the bodies already mounted that are seen around, see-through
    view     how it is framed: direction, which bodies are exploded and by
             how much, where the section plane goes, the arrows
"""

# The example chapter: the clutch on the motor shaft. It was the first written
# because it is the most instructive of the three kinds of picture needed - a
# single part, an exploded view and a section - and because it holds the only
# fit of the machine that cannot be seen from outside: the flat of the D of
# the hole against the milled flat of the shaft.

CHAPTER_INSERTS = {
    "num": 2,
    "id": "heat-set-inserts",
    "title": "Heat-set inserts",
    "intro": ("Before anything is assembled, the printed parts get their brass "
              "inserts. Doing them all in one sitting is not just convenience: "
              "some of them can only be reached while the part is bare, and the "
              "pivot insert is the clearest case - once the arm hangs on that "
              "pivot, no soldering iron will ever reach it again. The clutch's "
              "insert goes in here too, last."),
    # every insert is here, the clutch's too: on the real parts they all go
    # in at one sitting, with the iron already hot
    "steps": [
        {
            "title": "The collar: the pivot insert, first of all",
            "points": [
                "Put the collar in front of you with the telescope side up - the "
                "side the pivot boss is on.",
                "Melt the {inserto_M3} mm M3 insert into the end of the pivot, "
                "flush with the face around it.",
                "!Do this one before the others and before anything else is "
                "assembled. The arm hangs on this pivot and the screw that holds "
                "it comes from the far side: once the collar is on the wheel "
                "there is no way back to this hole.",
                "Keep the iron straight along the pivot. The hole is on the axis "
                "of a Ø{d_perno:.0f} mm post, and an insert that goes in crooked "
                "takes the screw crooked with it.",
            ],
            "mounts": ["box_collar", "insert_M3_pivot_1"],
            "context": [],
            "view": {"direction": (0.45, 0.55, 0.85), "zoom": 0.09,
                      "frame": ["insert_M3_pivot_1"],
                      "explode": {"insert_M3_pivot_1": (0, 0, 16)},
                      "arrows": [("insert_M3_pivot_1", (0, 0, -9))]},
        },
        {
            "title": "The box: three inserts for the panel screws",
            "points": [
                "The box takes three M3 inserts, all on the outside face around "
                "the panel opening.",
                "Same {inserto_M3} mm inserts again.",
                "The panel screws are countersunk and pull the panel flat against "
                "this face, so what matters here is that the inserts end up flush "
                "and not proud.",
            ],
            # the part is already on the bench from the pivot insert: box and
            # collar are one piece, so it is context here
            "mounts": ["insert_M3_panel_1",
                      "insert_M3_panel_2", "insert_M3_panel_3"],
            "context": ["box_collar"],
            "view": {"direction": (0.30, 0.35, -1.0), "up": (0, 0, 1), "zoom": 0.80,
                      "frame": ["box_collar"],
                      "explode": {"insert_M3_panel_1": (0, 0, -18),
                                 "insert_M3_panel_2": (0, 0, -18),
                                 "insert_M3_panel_3": (0, 0, -18)},
                      "arrows": [("insert_M3_panel_1", (0, 0, 11)),
                                 ("insert_M3_panel_2", (0, 0, 11)),
                                 ("insert_M3_panel_3", (0, 0, 11))]},
        },
        {
            "title": "The box: two inserts for the motor hatch",
            "points": [
                "Two more {inserto_M3} mm M3 inserts, on the outside face of "
                "the floor, in the two pockets beside the square hatch under "
                "the motor.",
                "They go in from below, like the panel ones, and end flush with "
                "the ceiling of their pocket: the hatch cover's two ears sit in "
                "those pockets and its countersunk screws pull them flat.",
            ],
            "mounts": ["insert_M3_hatch_1", "insert_M3_hatch_2"],
            "context": ["box_collar"],
            "view": {"direction": (0.30, -0.35, -1.0), "up": (0, 0, 1), "zoom": 0.30,
                      "frame": ["insert_M3_hatch_1", "insert_M3_hatch_2"],
                      "explode": {"insert_M3_hatch_1": (0, 0, -18),
                                 "insert_M3_hatch_2": (0, 0, -18)},
                      "arrows": [("insert_M3_hatch_1", (0, 0, 11)),
                                 ("insert_M3_hatch_2", (0, 0, 11))]},
        },
        {
            "title": "The collar: the insert for the cover screw",
            "points": [
                "One more {inserto_M3} mm M3 insert, into the small round pocket "
                "in the top of the collar, beside the big opening over the motor.",
                "It goes in from above, straight down, flush with the floor of "
                "the pocket. The cover's tab sits in that pocket and its screw "
                "comes down into this insert.",
            ],
            "mounts": ["insert_M3_cover_1"],
            "context": ["box_collar"],
            "view": {"direction": (0.45, 0.55, 0.85), "zoom": 0.12,
                      "frame": ["insert_M3_cover_1"],
                      "explode": {"insert_M3_cover_1": (0, 0, 16)},
                      "arrows": [("insert_M3_cover_1", (0, 0, -9))]},
        },
        {
            "title": "The collar: the insert for the second cover screw",
            "points": [
                "A second {inserto_M3} mm M3 insert for the cover, in the other "
                "small round pocket in the top of the collar: the one at the "
                "corner where the collar meets the curved wall round the motor, "
                "on the side away from the electronics.",
                "Straight down like the first, flush with the floor of the pocket.",
            ],
            "mounts": ["insert_M3_cover_2"],
            "context": ["box_collar"],
            "view": {"direction": (0.20, -0.75, 0.62), "zoom": 0.14,
                      "frame": ["insert_M3_cover_2"],
                      "explode": {"insert_M3_cover_2": (0, 0, 16)},
                      "arrows": [("insert_M3_cover_2", (0, 0, -9))]},
        },
        {
            # the nail: on the reference build an 8 mm insert tip did not
            # reach, and a nail heated with the iron did the job
            "title": "The box: the M4 insert for the preload screw",
            "points": [
                "One more goes into the box, and it is the odd one: an M4 insert, "
                "{inserto_M4} mm, into the outer wall behind the spring seat.",
                "It goes in **horizontally, from inside the box**, along the axis "
                "of the spring: the iron comes across the compartment from the "
                "wheel side, through the small round hole in the inner wall, "
                "and pushes the insert out towards the outer wall. Keep the iron "
                "level. (If your insert tip is too short to reach - on the "
                "reference build the 8 mm one was - use a nail instead, heated "
                "with the iron: that is how this insert went in.)",
                "!This is the insert the preload grub screw lives in, and the spring "
                "pushes on it with {forza_N} N for the life of the machine. It is "
                "worth the extra minute of getting it square.",
            ],
            "mounts": ["insert_M4_preload_1"],
            # the box SOLID and not see-through: what must read here is the
            # wall the insert goes into, and a see-through wall is not a wall
            "context": ["box_collar"],
            # the BOX is framed, not the insert. Tight on the insert only the
            # boss could be seen - it stands 4.7 mm proud of the side - and it
            # looked like a ring floating on its own, with the side curving
            # away almost edge-on. Whoever assembles must see which wall it is
            # on, not what the mouth looks like
            # cut level with the insert's axis and seen from above: the insert
            # now comes from the compartment, and from outside the wall hid it
            "view": {"direction": (0.15, -0.10, 1.0), "up": (0, 1, 0), "zoom": 0.60,
                      "frame": ["box_collar"],
                      "cut": ["box_collar"],
                      "plane": ((124.4, 48.9, -8.0), (0, 0, -1)),
                      # FROM INSIDE, along the spring axis (0.913, 0.408 points
                      # out of the box, read from the solid): the guide had it
                      # coming from outside, and check_assembly_paths found it
                      # going through the wall, 28 mm3 at 4 mm.
                      # The generator always said inside: the iron reaches it
                      # through the hole in the inner wall
                      "explode": {"insert_M4_preload_1": (-31.96, -14.28, 0)},
                      "arrows": [("insert_M4_preload_1", (17, 8, 0))]},
        },
        {
            "title": "The panel: three small inserts for the board",
            "points": [
                "The board panel takes three inserts on its inside face, on top of "
                "the posts the board will sit on.",
                "Two are M2, {inserto_M2} mm, and the one at the head end is M2.5, "
                "{inserto_M25} mm. They are not interchangeable - fit the M2.5 tip "
                "for that one.",
                "!These are small. Let the iron do the work and stop as soon as "
                "the brass is level with the post: a post pushed too far melts "
                "short, and the board then sits on the panel instead of on the "
                "posts.",
            ],
            "mounts": ["board_panel", "insert_M2_post_1",
                      "insert_M2_post_2",
                      "insert_M25_head_post_1"],
            "context": [],
            "view": {"direction": (0.35, 0.45, 1.0), "zoom": 0.80,
                      "frame": ["board_panel"],
                      "explode": {"insert_M2_post_1": (0, 0, 14),
                                 "insert_M2_post_2": (0, 0, 14),
                                 "insert_M25_head_post_1": (0, 0, 14)},
                      "arrows": [("insert_M2_post_1", (0, 0, -9)),
                                 ("insert_M2_post_2", (0, 0, -9)),
                                 ("insert_M25_head_post_1", (0, 0, -9))]},
        },
        {
            "title": "The sensor bracket: two inserts for its cover",
            "points": [
                "Last, the sensor bracket: two M2.5 inserts, {inserto_M25} mm, one "
                "at each end of the cover seat.",
                "The cover screws down onto these two and holds the sensor board "
                "against the bracket, so keep them square.",
            ],
            "mounts": ["sensor_bracket", "insert_M25_cover_1",
                      "insert_M25_cover_2"],
            "context": [],
            "view": {"direction": (0.40, 0.35, 0.85), "zoom": 0.80,
                      "frame": ["sensor_bracket"],
                      "explode": {"insert_M25_cover_1": (0, 0, 13),
                                 "insert_M25_cover_2": (0, 0, 13)},
                      "arrows": [("insert_M25_cover_1", (0, 0, -8)),
                                 ("insert_M25_cover_2", (0, 0, -8))]},
        },
        {
            # ALL the inserts go in this chapter, the clutch's too: on the real
            # parts it is done in the same sitting as the others, with the
            # iron already hot (as the first step of the clutch chapter it
            # meant heating the iron a second time)
            "title": "The clutch: the M3 insert for its grub screw",
            "points": [
                "Take the printed clutch - off the machine, in your hand - and find "
                "the channel in the side of the hub. It runs from the outside "
                "straight to the shaft bore.",
                "Push the {inserto} insert into the channel with the M3 tip, "
                "brass first.",
                "Keep the iron in line with the channel. The channel is open all the "
                "way to the outside for that reason: the shoulders of the tyre reach "
                "Ø{d_spalle:.0f} mm, and an iron coming in at an angle lands on them "
                "instead of on the insert.",
                "!The insert stops by itself where the channel narrows into the "
                "clearance hole for the grub screw. Do not push it past that: "
                "there is no way to get it back out.",
            ],
            "mounts": ["clutch_hub", "clutch_tyre", "insert_M3_grub_1"],
            "context": [],
            "view": {"direction": (0.40, 1.0, 0.30), "zoom": 0.95,
                      "explode": {"insert_M3_grub_1": (0, 26, 0)},
                      "arrows": [("insert_M3_grub_1", (0, -14, 0))]},
        },
    ],
    "tools": [
        "soldering iron with heat-set tips for M2, M2.5, M3 and M4 inserts",
        "a square block to press against, or a steady hand",
    ],
}

CHAPTER_ARM = {
    "num": 4,
    "id": "arm-bearings-and-pivot",
    "title": "Arm, bearings and pivot",
    "intro": ("The arm is what carries the motor and lets it swing against the "
              "spring, so the whole clutch force passes through this joint. It "
              "turns on two bearings pressed into the arm and riding on the "
              "pivot you put the insert in, back in chapter {cap_heat_set_inserts}. Nothing here is "
              "tight: the joint has to turn with no effort at all."),
    "steps": [
        {
            "title": "Press the two bearings into the arm",
            "points": [
                "The seat in the arm goes right through, {sp_braccio} mm deep, "
                "which is exactly two {cusc} mm F695ZZ bearings stacked.",
                "Put them in **flange outwards**: one from each face, so the two "
                "flanges end up on the outside and the plain faces meet in the "
                "middle.",
                "The seat is drawn Ø{sede_cusc} mm so that it prints Ø13. Press "
                "by hand, or between two flat jaws - never hammer on the inner "
                "ring.",
                "!Press on the outer ring only. A bearing tapped in through its "
                "inner ring feels fine and runs rough forever after.",
            ],
            "mounts": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2"],
            "context": [],
            "view": {"direction": (0.80, -0.55, 0.26), "zoom": 0.80,
                      "frame": ["bearing_F695ZZ_1", "bearing_F695ZZ_2"],
                      "explode": {"bearing_F695ZZ_1": (0, 0, -16),
                                 "bearing_F695ZZ_2": (0, 0, 16)},
                      "arrows": [("bearing_F695ZZ_1", (0, 0, 9)),
                                 ("bearing_F695ZZ_2", (0, 0, -9))]},
        },
        {
            # the washer and the screw go on the arm BEFORE it goes into the
            # box: the arm goes in as one piece with them, through the
            # electronics opening. Rejected: fitting them last, from the
            # camera side with the arm already on its pivot - on the real
            # assembly that is the harder way.
            "title": "Washer and screw on the arm, on the bench",
            "points": [
                "The printed washer carries the pin: a Ø{d_perno:.0f} mm bushing "
                "{perno_lungo:.0f} mm long. Push it through both bearings from "
                "the face with the four motor holes - the camera side - until "
                "the washer sits on the inner ring of the near bearing.",
                "Put the {vite_perno} screw through the washer and the bushing. "
                "Hold it back with a finger, so that its tip does not stand out "
                "of the bushing: it is driven home once the arm is on the pivot.",
            ],
            "mounts": ["pivot_washer", "screw_M3_pivot_1"],
            "context": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2"],
            "view": {"direction": (0.50, -0.55, -0.70), "up": (0, 0, 1), "zoom": 0.22,
                      "frame": ["pivot_washer"],
                      "explode": {"pivot_washer": (0, 0, -13),
                                 "screw_M3_pivot_1": (0, 0, -24)},
                      "arrows": [("screw_M3_pivot_1", (0, 0, 13))]},
        },
        {
            # found on the real assembly: the arm goes in
            # through the ELECTRONICS OPENING in the floor - the one the board
            # panel closes in chapter 12 - with the washer and the screw
            # already on it, not through the hatch under the motor. The path
            # is declared (guide/paths/arm_door.json, found by
            # src/study_paths/grid_door.py and search_door.py) and
            # check_assembly_paths follows it with the whole group: arm,
            # bearings, washer and screw. It starts with a drop along the
            # pivot axis: the screw leaves the insert along its own bore,
            # which in the hand is the screw held back in the bushing.
            "title": "The arm in through the electronics opening",
            "points": [
                "Turn the part upside down, camera side up. The arm goes in from "
                "below, through the large opening in the floor that the board "
                "panel will close - the electronics opening - with its washer "
                "and screw on, keeping the screw held back.",
                "It goes in **pivot end first**, then the motor end follows "
                "towards the hatch as the arm comes level: the picture shows "
                "where it comes from.",
                # found on the real assembly: the spring
                # does not go home by itself as the arm swings in: it is
                # compressed by hand and put in the arm's seat
                "With the help of a screwdriver, compress the preload spring and "
                "slip it into the arm's seat.",
                "Bring the bushing under the round spot face at the end of the "
                "pivot. The arm only goes one way round: the flat face with the "
                "four motor holes looks towards the camera side.",
            ],
            "mounts": [],
            "context": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2",
                         "pivot_washer", "screw_M3_pivot_1", "box_collar"],
            "path": {"arm": "arm_door.json"},
            # the spring and its cup are already in (chapter 4): the arm
            # meets them, and the cup can go back its preload travel
            "yields": ["preload_spring", "spring_cup"],
            "view": {"direction": (0.92, -0.38, -0.30), "up": (0, 0, 1), "zoom": 0.62,
                      "frame": ["arm"],
                      # drawn below the electronics opening, where the
                      # declared path leaves the box (towards +y, down)
                      "explode": {"arm": (-14, 28, -34),
                                 "bearing_F695ZZ_1": (-14, 28, -34),
                                 "bearing_F695ZZ_2": (-14, 28, -34),
                                 "pivot_washer": (-14, 28, -34),
                                 "screw_M3_pivot_1": (-14, 28, -34)},
                      # anchored out of the arm, towards the camera: born at
                      # the arm's centre the arrow was inside it and did not
                      # show
                      "arrows": [("arm", (6, -12, 14), (40, -16, -26))]},
        },
        {
            "title": "Drive the screw into the pivot",
            "points": [
                "Drive the {vite_perno} screw through the bushing into the insert "
                "at the far end of the pivot, from the camera side.",
                "The bushing is exactly as long as the bearings plus one flange: "
                "the screw pulls it against the collar, not the bearings, so the "
                "arm still turns with the screw tight.",
                "Tighten until the washer is held, no more. Then check: the arm "
                "must swing with a fingertip and have no shake at all.",
                "Above the arm there are {franco_braccio} mm of clearance to the "
                "collar, and that gap is what keeps the arm from rubbing as it "
                "swings. If the arm binds anywhere in its travel, the screw is "
                "too tight or the washer is missing.",
            ],
            "mounts": [],
            "context": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2",
                         "pivot_washer", "screw_M3_pivot_1", "box_collar"],
            "view": {"direction": (0.50, -0.55, -0.70), "up": (0, 0, 1), "zoom": 0.22,
                      "frame": ["pivot_washer"],
                      "explode": {"screw_M3_pivot_1": (0, 0, -9)},
                      "arrows": [("screw_M3_pivot_1", (0, 0, 6))]},
        },
    ],
    "tools": [
        "2.5 mm hex key",
        "a flat, clean surface to press the bearings against",
        # to compress the spring, found necessary on the real assembly
        "a screwdriver, to compress the preload spring",
    ],
}

CHAPTER_MOTOR = {
    "num": 5,
    "id": "motor-on-the-arm",
    "title": "The motor on the arm",
    "intro": ("The motor hangs under the arm with its shaft pointing up through "
              "it. Four screws hold it, and they go in from the top face of the "
              "arm - which is the reason the motor goes on now, with the arm "
              "already on its pivot but nothing else in the way yet."),
    "steps": [
        {
            "title": "Bring the motor up through the hatch, into the clutch",
            "points": [
                # the motor is wired BEFORE it goes in: once it hangs under the arm its
                # leads are inside the box, out of reach
                "Wire it first, on the bench: its four leads go into the J1 "
                "plug, a 4-way JST XH, with the pairs side by side - "
                "**black+green** and **red+blue**, the pairs chapter "
                "{cap_first_checks} checks. Leave them long enough to reach the "
                "board.",
                "Bend the four leads down along the body of the motor first: "
                "they pass the hatch beside it, and they are wires.",
                "Turn the shaft so that its milled flat lines up with the flat in "
                "the clutch's bore, which you can see from above.",
                "From below, through the hatch, push the motor up: the shaft goes "
                "through the arm and into the clutch, and the motor's front face "
                "comes flat against the arm.",
                "Turn it so the leads come out towards the electronics bay and the "
                "four holes in the motor face line up with the arm's.",
                # on the first power-up of the assembled reference wheel
                # every move ran away from its target: DIR was the wrong way
                # for this wire order, and the firmware now inverts it
                "!Keep the order in the drawing - black A+, green A-, red B+, "
                "blue B-. The firmware inverts the motor's DIR signal for exactly "
                "this order: with a phase the other way round every move runs "
                "away from its target, and the fix is then in the firmware "
                "(`mechanics_esp32.cpp`), not in the wiring you have already "
                "crimped.",
            ],
            # the wires on the connector, drawn from wiring.py: the colours
            # are what the builder has to match, so they get a diagram
            "illustrations": {1: "motor-wires.svg"},
            "mounts": ["motor_14HS10-0404S"],
            "context": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2",
                         "box_collar", "clutch_hub", "clutch_tyre",
                         "insert_M3_grub_1"],
            # the maker's STEP draws the leads as rigid bars; they bend
            "bent_leads": ["motor_14HS10-0404S"],
            "view": {"direction": (0.75, -0.45, -0.40), "up": (0, 0, 1), "zoom": 0.85,
                      "frame": ["motor_14HS10-0404S"],
                      "explode": {"motor_14HS10-0404S": (0, 0, -40)},
                      "arrows": [("motor_14HS10-0404S", (0, 0, 22))]},
        },
        {
            "title": "Lock it with the grub screw",
            "points": [
                "Push the clutch down onto the shaft as far as it goes. Turn the "
                "shaft by hand until the grub screw hole faces the middle of the "
                "collar: the key comes in from there, through the gap in the ring.",
                "Drive the {grano} grub screw into the insert with a "
                "{chiave} mm hex key, until it sits on the flat of the shaft.",
                "The section shows what you cannot see from outside: the flat of the "
                "bore is already resting on the flat of the shaft, so the grub screw "
                "only has to hold the clutch down - the torque goes through the flats, "
                "not through friction.",
                "!Tighten firmly but without leaning on it: on its thin side the "
                "insert is held by {parete} mm of ASA.",
                "Check by hand that the clutch cannot be turned on the shaft and "
                "cannot be pulled off.",
            ],
            "mounts": ["grub_M3_clutch_1"],
            "context": ["clutch_hub", "clutch_tyre",
                         "insert_M3_grub_1", "motor_14HS10-0404S", "box_collar"],
            "view": {"direction": (0.0, 0.0, 1.0), "up": (0, 1, 0), "zoom": 0.92,
                      # the clutch is framed, not the motor: the motor is there
                      # because the section must show the shaft, but it is the
                      # outline of the clutch that must fill the picture
                      "frame": ["clutch_hub"],
                      "cut": ["clutch_hub", "clutch_tyre",
                                 "motor_14HS10-0404S"],
                      "plane": "grub",
                      # turned the way it is held: grub towards the middle of
                      # the collar, where the key comes from; the grub drawn
                      # out along that way, with the arrow
                      "turn": "grub_to_centre",
                      "explode": {"grub_M3_clutch_1": (-14, 0, 0)},
                      "arrows": [("grub_M3_clutch_1", (9, 0, 0))]},
        },
        {
            "title": "Four screws, from the top, through the clutch",
            "points": [
                "Turn the clutch until its four holes stand over the four holes in "
                "the arm. Through the opening over the motor, drop each "
                "{vite_motore} screw through its hole in the clutch and drive it "
                "into the motor's own threads with a {chiave_motore} mm hex key, "
                "through the same hole.",
                "Cross them like a wheel - one, then the one opposite - and pull "
                "them down evenly. The motor face has to end up flat on the arm, "
                "because everything the clutch does depends on the shaft being "
                "square to it.",
                "!Do not force them. These thread into the motor's own holes and "
                "there is nothing to gain past snug.",
            ],
            "mounts": ["screw_M3_motor_1", "screw_M3_motor_2",
                      "screw_M3_motor_3", "screw_M3_motor_4"],
            "context": ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2",
                         "motor_14HS10-0404S", "clutch_hub", "clutch_tyre",
                         "insert_M3_grub_1", "grub_M3_clutch_1", "box_collar"],
            "view": {"direction": (0.55, -0.40, 0.95), "zoom": 0.80,
                      "frame": ["screw_M3_motor_1", "screw_M3_motor_2",
                                   "screw_M3_motor_3", "screw_M3_motor_4"],
                      "explode": {"screw_M3_motor_1": (0, 0, 20),
                                 "screw_M3_motor_2": (0, 0, 20),
                                 "screw_M3_motor_3": (0, 0, 20),
                                 "screw_M3_motor_4": (0, 0, 20)},
                      "arrows": [("screw_M3_motor_1", (0, 0, -12)),
                                 ("screw_M3_motor_4", (0, 0, -12))]},
        },
        {
            # PROVISIONAL PLACE: with strategy B the motor comes
            # up through this hatch after the arm is in the box, and the whole
            # guide is to be reordered on that sequence (an open point). Until
            # then the step sits here, right after the motor is on.
            "title": "Close the hatch under the motor",
            "points": [
                "The square hatch in the floor under the motor is how the motor "
                "comes in. Once it is on the arm, close it.",
                "The cover goes in from below, flat face out: its rim sits on "
                "the step round the hatch and it ends up flush with the floor.",
                "Fix it with two {vite_botola} countersunk screws through its "
                "ears, into the inserts beside the hatch - a PH0 screwdriver.",
            ],
            "mounts": ["hatch_cover", "screw_M3_hatch_1", "screw_M3_hatch_2"],
            "context": ["box_collar", "motor_14HS10-0404S"],
            "view": {"direction": (0.30, -0.35, -1.0), "up": (0, 0, 1), "zoom": 0.30,
                      "frame": ["hatch_cover"],
                      "explode": {"hatch_cover": (0, 0, -20),
                                 "screw_M3_hatch_1": (0, 0, -34),
                                 "screw_M3_hatch_2": (0, 0, -34)},
                      "arrows": [("hatch_cover", (0, 0, 12)),
                                 ("screw_M3_hatch_1", (0, 0, 10))]},
        },
    ],
    # the grub's key belongs here, where step 2 drives the grub, not in
    # chapter 6, which drives nothing
    "tools": ["{chiave} mm hex key, for the clutch grub screw",
                 "{chiave_motore} mm hex key, for the motor screws",
                 # the hatch screws are countersunk: PH0, not a 2 mm hex key
                 "a PH0 screwdriver, for the countersunk hatch screws"],
}

CHAPTER_ZERO = {
    "num": 0,
    "id": "parts-tools-and-printing",
    "title": "Parts, tools and printing",
    "intro": ("Before the first insert goes in, here is the whole machine, "
              "everything it is made of and everything you need to have on the "
              "bench. The colours you see here are the colours every part keeps "
              "for the rest of the guide: if you can tell the arm from the "
              "collar in this picture, you can tell them apart fifteen steps "
              "later, half hidden behind the box."),
    # this chapter's bill of materials is the GENERAL one, not the one of its
    # steps: it is the chapter that says what to buy and what to print, and it
    # mounts nothing. So it stays out of the count of the bodies.
    "full_bom": True,
    "steps": [
        {
            "title": "What you are building",
            "points": [
                "A manual filter wheel, motorised: the printed parts clamp "
                "around the wheel you already own, and they come off again "
                "without cutting anything. It was designed around a "
                "five-position StarDikor for 2-inch filters - that is the "
                "wheel in every picture - and a different wheel is a handful of "
                "parameters, not a redesign.",
                "The stepper hangs under an arm that swings on a pivot, and a "
                "spring pushes the arm so that the clutch presses on the rim of "
                "the filter disc. Everything else - the sensor, the board, the "
                "box - hangs off those few parts.",
                "**The wheel body itself goes on last**, and the reason is "
                "measured: above the clutch there is no room to start it onto "
                "the shaft once the wheel is in place.",
            ],
            "mounts": [],
            "context": ["box_collar", "arm", "clutch_hub",
                         "clutch_tyre", "sensor_bracket",
                         "sensor_cover", "board_panel", "spring_cup",
                         "pivot_washer", "front_gasket",
                         "rear_gasket", "motor_14HS10-0404S",
                         "preload_spring", "sensor_cable"],
            # box, wheel and disc see-through: in solid colours the box hides
            # the whole mechanism, and it is the mechanism this step has to
            # show
            "backdrop": ["box_collar", "filter_wheel_body", "filter_disc"],
            "view": {"direction": (0.75, -0.62, 0.45), "zoom": 0.95},
        },
        {
            "title": "The parts you print",
            "points": [
                "{n_stampati} printed parts: ASA for what stays, TPU for the tyre and "
                "the gaskets - any grade from 87A to 95A: the machine has been "
                "tried on 87A only, and up to 95A it is calculated, not tried. Masses and print orientations are in "
                "the list above - the orientation is part of the design, not a "
                "choice left to the slicer.",
                "Print in PETG first if you are prototyping: it is easier, and "
                "the tolerances in this project were measured on ASA, so a PETG "
                "part may fit slightly differently.",
                "The parts are shown here where they end up, not laid out on a "
                "plate, and the box is drawn see-through so that what it "
                "covers can be seen. Look at the colours: they do not change "
                "from here on.",
            ],
            "mounts": [],
            # from the bill of printed parts, like the bought ones: a list
            # written here by hand had lost the grip cover, the hatch cover
            # and the magnet spacer
            "context": "PRINTED",
            "backdrop": ["box_collar"],
            "view": {"direction": (0.70, -0.55, 0.55), "zoom": 0.95},
        },
        {
            # "mechanical": with the electronics in the list above, a title
            # saying just "what you buy" promised all of it while the picture
            # shows the mechanics only
            "title": "And the mechanical parts you buy",
            "points": [
                "The motor, two bearings, the magnet, the spring, and the "
                "screws and inserts - shown here on their own, without the "
                "printed parts around them, so you can see how few there are "
                "and where each one lives.",
                "Steel is the screws and the bearings, brass is the heat-set "
                "inserts: two colours, because in a picture of a machine they "
                "would otherwise be the same grey smudge.",
                "The electronics are bought too, and are in the list above, "
                "under their own heading: they have no picture here because "
                "they are wired on the bench before they meet the machine, in "
                "chapter {cap_board_in_its_panel}.",
                "!Check the magnet before you buy it: it must be "
                "**diametrically magnetised**. One magnetised through its "
                "thickness looks identical, is easy to buy by mistake, and "
                "gives the sensor nothing to read.",
            ],
            # the magnetisation is not in the magnet's shape, so no render can
            # show it: a drawing, in the warning it belongs to
            "illustrations": {4: "magnet-magnetisation.svg"},
            "mounts": [],
            "context": "PURCHASED",
            "view": {"direction": (0.70, -0.55, 0.55), "zoom": 0.95},
        },
    ],
    # EVERY tool of the guide, gathered here from the chapters (the drill
    # bit for the perfboard, the PH0 screwdriver, the spanner and the
    # computer once went missing from this list). A tool added to a chapter
    # goes here too.
    "tools": [
        # any TPU from 87A to 95A: tried on 87A,
        # calculated up to 95A - see TPU_GAMMA in bom_mechanics.py
        "a 3D printer, and the filament: ASA and TPU, any grade from 87A to "
        "95A (tried on 87A, calculated up to 95A)",
        "soldering iron with heat-set tips for M2, M2.5, M3 and M4 inserts, "
        "and a fine tip for wiring the board",
        "a Ø{foro_basetta_M25} mm drill bit, for one hole of the perfboard",
        "hex keys: 1.5, 2, 2.5 mm",
        "a PH0 screwdriver and a 2 mm flat screwdriver",
        "a 14 mm spanner, for the nut of the GX12 connector",
        "a caliper, to check what came off the plate",
        "a 2.5 mm cable tie, for the sensor cable",
        "a drop of glue for the magnet: cyanoacrylate or epoxy",
        "a computer with Python 3.12 and Chrome or Edge, and a USB-C cable",
        "any ESP32 board on a breadboard, to set the air gap",
        "the 12 V supply and its GX12 lead, for the first checks",
        # at the end so the Italian keys by position do not shift; from chapters 2, 5 and 11
        "a square block to press the inserts against",
        "a flat, clean surface to press the bearings against",
        "2 × M2 × 4 screws, cylinder or countersunk head, for the air gap feet",
        # from chapter 10: the detent comes off
        "a screwdriver to fit the screws of the wheel's detent",
    ],
}

CHAPTER_GASKETS = {
    "num": 3,
    "id": "collar-and-gaskets",
    "title": "The collar and its gaskets",
    "intro": ("Two TPU gaskets keep dust out of the wheel where the collar meets "
              "it. They are arcs, not rings - the collar is an arc of "
              "{arco_collare}° and so are they - and they are held in their "
              "grooves by small buttons that click into sockets. This is bench "
              "work: the collar does not go near the wheel until chapter "
              "{cap_the_wheel_body}."),
    # the arc is derived ({arco_collare}): a hand-written 162° went stale
    # when Ang_collar_pivot changed; and the wheel body's chapter is named
    # by reference, since it is no longer the last one
    "steps": [
        {
            "title": "The gasket on the camera side",
            "points": [
                "Start at one end and press the gasket into the groove, working "
                "along it. The buttons underneath click into their sockets as "
                "you go: that is what holds it while you handle the collar.",
                "The lip faces out of the groove. The groove is "
                "{cava_larga} mm wide and {cava_fonda} mm deep, the gasket is "
                "{guarn_larga} mm wide, so it goes in without stretching - if "
                "you are stretching it, it is the wrong way round.",
                "When it is home, {labbro} mm of lip stand proud of the face. "
                "That half millimetre is the squash: it is what seals when the "
                "wheel body is finally pushed on.",
                "The gaskets are TPU; their squash is calculated for "
                "{shore}A, and a softer one seals with less force. If you printed them separately "
                "they came off the plate flat, lip up; if you have a "
                "multi-material printer you can print them straight onto the "
                "collar instead, and then there is nothing to fit here.",
            ],
            "mounts": ["front_gasket"],
            # The gasket is TPU and its buttons click into their sockets: the
            # interference on the way in is how it goes on, not a collision.
            # check_assembly_paths reports it as a note, with its volume.
            "snap_in": ["front_gasket"],
            "context": ["box_collar"],
            "backdrop": [],
            # three-quarter view, not along z: looking along the axis of the
            # explosion the gasket seems to sit BESIDE the collar instead of
            # lifted off its face, and the arrow shrinks to a dot
            "view": {"direction": (0.62, 0.50, -0.62), "up": (0, 0, 1), "zoom": 0.90,
                      "frame": ["box_collar"],
                      "explode": {"front_gasket": (0, 0, -20)},
                      "arrows": [("front_gasket", (0, 0, 13))]},
        },
        {
            "title": "And the one on the telescope side",
            "points": [
                "Turn the collar over and do the same in the groove on the "
                "other face.",
                "!Take more care over this one. On the camera side there are "
                "two barriers in series - this gasket and a labyrinth rib "
                "behind it - while on the telescope side the gasket is the only "
                "thing between the dust and your filters.",
                "Run a finger along both when you have finished: the lip should "
                "stand the same all the way round, with no section sitting "
                "proud where a button did not click home.",
            ],
            "mounts": ["rear_gasket"],
            "snap_in": ["rear_gasket"],   # TPU buttons, as above
            "context": ["box_collar", "front_gasket"],
            "view": {"direction": (0.62, 0.50, 0.62), "up": (0, 0, 1), "zoom": 0.90,
                      "frame": ["box_collar"],
                      "explode": {"rear_gasket": (0, 0, 20)},
                      "arrows": [("rear_gasket", (0, 0, -13))]},
        },
    ],
    "tools": ["your hands - nothing else"],
}

# ==========================================================================
# Chapter 1: the parameters page
# ==========================================================================
# It mounts nothing and has no pictures: it is the only chapter done in front
# of a screen. It comes BEFORE everything else because what it decides comes
# out of the printer, and afterwards it cannot be changed any more.
CHAPTER_PARAMETERS = {
    "num": 1,
    "id": "the-parameters-page",
    "title": "Making it fit your wheel",
    "intro": ("Wheelly is not a single object: it is a set of generators that "
              "draw the parts around the wheel you actually own. The page in "
              "this chapter is where you tell them what that wheel is - its "
              "diameter, how many filters it holds, which magnet you glued on - "
              "and everything downstream, from the printed parts to the "
              "drawings, follows from it."),
    # The box: whoever has the reference wheel has nothing to do here.
    "skip": ("If you are building on the same wheel this project was drawn "
              "around - a {ruota_rif} mm manual filter wheel - and you are using "
              "the same {magnete_rif} mm diametral magnet, **you can skip "
              "straight to the next chapter**: the parts as published already "
              "fit, and the numbers on this page are the ones they were "
              "generated from."),
    "steps": [
        {
            "title": "Get the generators running",
            "points": [
                "The parts are not STL files that happen to exist: they are "
                "**generated**, and to change one you run the generator. You need "
                "Python 3.12 and two libraries - CadQuery, which builds the "
                "solids, and ezdxf, which writes the drawings.",
                "From the repository: `cd mechanics/wheelly-cad`, then "
                "`uv venv --python python3.12 .venv` and "
                "`VIRTUAL_ENV=.venv uv pip install cadquery ezdxf`. Plain "
                "`python -m venv` and `pip install cadquery ezdxf` work as well, "
                "just slower.",
                "!Always call the interpreter inside `.venv`, never the system "
                "one: `./.venv/bin/python`. The system Python has neither "
                "library, and the error it gives you points at the wrong thing.",
            ],
            "mounts": [],
        },
        {
            "title": "Open the page",
            "points": [
                "`./.venv/bin/python ui.py` opens the editor on "
                "**http://127.0.0.1:8760/** and brings up a browser. "
                "`--porta N` puts it somewhere else, `--no-apri` leaves the "
                "browser alone - which is what you want over SSH.",
                "The page lists every parameter in sections, with what it means, "
                "where it is used, and whether it was **measured on a real part**, "
                "declared by a supplier, or assumed. That last column is worth "
                "reading before you trust a number: most of the defects this "
                "project has found came from assumed values nobody checked.",
                "!The page does not reload the files by itself. Change a "
                "generator or a parameter on disk and you must **restart it** - "
                "otherwise you are looking at the values it read when it started, "
                "and they will disagree with what the build produces.",
                "The drawing on the right redraws as you type, and under it the "
                "**dimensional chains** show what each change did to the fits "
                "that matter - shaft engagement, gasket squeeze, whether the M2 "
                "screw still passes. A change that breaks one turns red there, "
                "before you have printed anything.",
            ],
            "mounts": [],
            "screenshot": "parameters-editor.png",
        },
        {
            "title": "Change what you need, and only that",
            "points": [
                "Edits go into `src/parameters_local.py`, which **overrides** "
                "`src/parameters.py` and leaves the base untouched. That way your "
                "wheel and the reference wheel stay side by side, and a future "
                "update of the project does not silently take your numbers away.",
                "The ones that matter for a different wheel are the rotating "
                "disc diameter, the number of filter positions, and the magnet - "
                "diameter and thickness. Change the magnet and the sensor bracket "
                "moves with it: the air gap is a consequence, not a setting.",
                "Everything else has a default that works. A parameter you do not "
                "understand is a parameter you should leave alone - each one says "
                "which parts depend on it, and some feed six.",
            ],
            "mounts": [],
        },
        {
            "title": "Build, and check it built",
            "points": [
                "`./.venv/bin/python build.py` regenerates everything: solids, "
                "drawings and the checks. It takes about twenty minutes.",
                "`./.venv/bin/python build.py --solo-dxf` does the 2D geometry "
                "only, in seconds. Use it while you iterate on a dimension, and "
                "the full build to confirm nothing now collides.",
                "!**Read the end of the build before you print.** The checks are "
                "the point: they measure the solids that came out and say whether "
                "parts intersect, whether screws still reach, whether the wheel "
                "still clears the box. A build that ended in an error leaves the "
                "previous STEP files on disk, and they look exactly like good ones.",
                "The parts to print come out in `out/`, and nothing else does: "
                "`out/tools/` holds the test jigs and `out/drawings/` the "
                "drawings. Opening one folder to send a job is how a jig gets "
                "printed instead of a part, and that costs an hour.",
            ],
            "mounts": [],
        },
    ],
    "tools": [
        "a computer with Python 3.12",
        "a web browser",
        "a caliper, for the one measurement that goes back into the model",
    ],
}

CHAPTERS = [CHAPTER_ZERO, CHAPTER_PARAMETERS, CHAPTER_INSERTS, CHAPTER_GASKETS, CHAPTER_ARM, CHAPTER_MOTOR, {
    "num": 6,
    "id": "clutch-on-the-motor-shaft",
    "title": "The clutch on the motor shaft",
    "intro": ("The clutch is what pushes the filter disc: a printed ASA hub with a "
              "co-printed TPU tyre around it. It grips the motor shaft on the milled "
              "flat, through a grub screw that lives in a heat-set insert. It goes on "
              "now and not earlier, because it is Ø50 and the hole it would have to "
              "pass in the arm is Ø7: the motor has to be on the arm first. And it "
              "has to go on before the wheel body does - with the wheel in place "
              "there is no room above the shaft to start the clutch onto it."),
    "steps": [
        {
            # STRATEGY C: on the shaft the clutch is caged
            # - it touches the roof after 1 mm of the 13 it needs to leave the
            # shaft - so it goes in BEFORE the motor, from the middle of the
            # collar, before the wheel. The ring of the collar is cut over the
            # angles of this very move (solids_box_collar.py). The path, from
            # home outwards: 65 mm towards the wheel axis, then straight up
            # out of the collar.
            "title": "Slide the clutch in from the middle of the collar",
            "points": [
                "The wheel is not in yet, so the middle of the collar is empty. "
                "Lower the clutch into it from the telescope side, flat, tyre "
                "down, hub collar up.",
                "Slide it outwards, level, through the gap in the collar ring, "
                "until it sits over the arm where the motor shaft will come up.",
                "Turn it so its **four holes** stand over the four holes in the "
                "arm: the motor screws go through them, later, from above.",
                "It just rests on the arm for now. The motor comes up into it next.",
            ],
            "mounts": [],
            "context": ["clutch_hub", "clutch_tyre", "insert_M3_grub_1",
                         "arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2",
                         "box_collar", "pivot_washer", "screw_M3_pivot_1"],
            "path": {"clutch_hub": {"pose": [[0, 0, 0, -65, 0, 0],
                                                 [0, 0, 0, -65, 0, 70]]}},
            "view": {"direction": (0.35, -0.60, 0.72), "zoom": 0.55,
                      "frame": ["clutch_hub", "box_collar"],
                      "explode": {"clutch_hub": (-45, 0, 0),
                                 "clutch_tyre": (-45, 0, 0),
                                 "insert_M3_grub_1": (-45, 0, 0)},
                      "arrows": [("clutch_hub", (25, 0, 0))]},
        },
    ],
    # The tools are given by name and size: whoever assembles must be able
    # to put them on the table before starting. No hex key here: the grub
    # screw is driven in chapter 7, and the 1.5 mm key goes with it. No
    # soldering iron either: the clutch's insert goes in chapter 2 with the
    # others
    "tools": ["your hands - nothing else"],
}]


# ==========================================================================
# Chapter 6: the board in its panel
# ==========================================================================
# The panel is the lid of the compartment under the box, and the board lives
# on it: it is assembled on its own, on the table, and this chapter comes
# before the box on purpose - when the box is in hand, the panel will already
# be ready to screw on. What the chapter does NOT tell is the wiring: that is
# in the board's booklet, in pcb/, which is made for whoever has the perfboard
# in hand and the soldering iron on.
CHAPTER_BOARD = {
    "num": 7,
    "id": "board-in-its-panel",
    "title": "The board in its panel",
    "intro": ("The electronics live on a piece of perfboard screwed to the panel "
              "that closes the underside of the box. Board and panel come out "
              "together, as one piece, which is how you get at a XIAO or a driver "
              "once the machine is on a telescope. This chapter puts the board in "
              "the panel; what goes where on the board is not repeated here - the "
              "wiring booklet in `pcb/` is drawn for someone with the perfboard in "
              "hand and the iron hot."),
    "steps": [
        {
            "title": "Build the board first, on the bench",
            "points": [
                "The board is a {perfboard} mm piece of 2.54 mm perfboard, "
                "{fori_basetta} holes, cut to shape with two flats.",
                "!One hole has to be drilled before anything is soldered, while "
                "the board is still bare: **B05** - second column from the head "
                "end, row 05, between the two rows of XIAO pins - goes from the "
                "Ø{fori_stampati_basetta} mm of the printed grid to "
                "Ø{foro_basetta_M25} mm. That is the hole the third screw uses, "
                "and an M2.5 will not pass the grid as it comes. It is far easier "
                "now than with the components on.",
                "Wire it as the booklet in `pcb/` shows. Solder **sockets**, not the "
                "modules: the XIAO and the driver have to come out again, and the "
                "day one of them fails you do not want a soldering iron anywhere "
                "near the telescope.",
                "Keep the tall parts short. There is {sopra_basetta:.1f} mm of head "
                "room between the board and the roof of the compartment, and that is "
                "all there is.",
                "!Do the whole board now and test it on the bench, powered over USB, "
                "before it ever goes into the machine. Everything is reachable while "
                "it is lying on the table and almost nothing is, later.",
            ],
            "mounts": ["electronics_perfboard", "electronics_pin_sockets",
                      "electronics_components"],
            "context": [],
            "view": {"direction": (0.40, -0.55, 0.90), "zoom": 0.85,
                      "frame": ["electronics_perfboard"]},
        },
        {
            "title": "Drop the board into the panel and screw it down",
            # BEFORE the XIAO goes in: the M2.5 at the
            # head end sits under the XIAO, and with the module in its sockets
            # the screwdriver cannot reach it
            "points": [
                "Screw the board down **before** the XIAO and the driver go in: "
                "the {vite_basetta_M25} at the head end is under the XIAO, and "
                "with the module in place it cannot be reached.",
                "The board **drops in from above**, between the two smooth guides "
                "that square it up, and lands on the three posts you put the inserts "
                "in back in chapter {cap_heat_set_inserts}.",
                "Two {vite_basetta_M2} countersunk screws at the wide end, through "
                "the two printed holes; one {vite_basetta_M25} at the head end, "
                "through the hole you opened to Ø{foro_basetta_M25} mm - a "
                "{chiave_M25} mm hex key for that one. They are not "
                "interchangeable.",
                "!The guides square the board, they do not hold it down: do not "
                "force the board sideways under them. An earlier panel had a lip "
                "that covered the edge of the board, and it broke.",
            ],
            "mounts": ["screw_M2_board_1", "screw_M2_board_2",
                      "screw_M25_board_1"],
            "context": ["board_panel", "electronics_perfboard", "electronics_pin_sockets",
                         "electronics_components"],
            "view": {"direction": (0.35, -0.55, 0.85), "zoom": 0.85,
                      "frame": ["board_panel"],
                      "explode": {"electronics_perfboard": (0, 0, 20),
                                 "electronics_pin_sockets": (0, 0, 20),
                                 "electronics_components": (0, 0, 20),
                                 "screw_M2_board_1": (0, 0, 34),
                                 "screw_M2_board_2": (0, 0, 34),
                                 "screw_M25_board_1": (0, 0, 34)},
                      "arrows": [("electronics_perfboard", (0, 0, -14), (-18, 16, 0)),
                                 ("screw_M2_board_1", (0, 0, -10)),
                                 ("screw_M2_board_2", (0, 0, -10)),
                                 ("screw_M25_board_1", (0, 0, -10))]},
        },
        {
            "title": "Plug in the XIAO and the driver",
            "points": [
                "The XIAO ESP32-S3 goes into its two rows of sockets, USB port "
                "towards the head of the board.",
                "The TMC2208 driver goes into its own socket, standing up.",
                "!Check the orientation of both against the booklet before you push "
                "them home. A driver in backwards is the one mistake here that "
                "destroys something.",
            ],
            "mounts": ["electronics_xiao", "electronics_driver"],
            "context": ["board_panel", "electronics_perfboard",
                         "electronics_pin_sockets", "electronics_components",
                         "screw_M2_board_1", "screw_M2_board_2",
                         "screw_M25_board_1"],
            "view": {"direction": (0.50, -0.60, 0.80), "zoom": 0.85,
                      "frame": ["electronics_perfboard"],
                      "explode": {"electronics_xiao": (0, 0, 26),
                                 "electronics_driver": (0, 0, 26)},
                      "arrows": [("electronics_xiao", (0, 0, -16)),
                                 ("electronics_driver", (0, 0, -16))]},
        },
    ],
    "tools": [
        "soldering iron",
        "a Ø{foro_basetta_M25} mm drill bit, for hole B05 of the perfboard",
        # the M2 screws are countersunk, driven with the PH0: no step here
        # uses a 1.5 mm key
        "{chiave_M25} mm hex key, for the M2.5 screw",
        "a PH0 screwdriver for the countersunk M2 screws",
    ],
}


# ==========================================================================
# Chapter 7: the box, with the spring inside
# ==========================================================================
# The spring is NOT a chapter of its own: its two supports are the bottom of
# its seat in the box and the flank of the arm plate, so until the box is there
# the spring has nothing to push on. And the box is not lowered from above: its
# ears grip the collar's from both faces - two below, three above - so the
# only way left is to go in sideways, towards the wheel axis. Measured on the
# assembly: the pads sit at r 81, that is just outside the rim of the wheel.
CHAPTER_BOX = {
    "num": 8,
    "id": "the-box-and-its-spring",
    "title": "The box, and the spring inside it",
    "intro": ("The box closes over the whole mechanism and carries two things of "
              "its own: the connector in its head, and the preload spring that "
              "pushes the arm - and with it the clutch - against the filter disc. "
              "The spring is not a chapter of its own because it has nothing to "
              "push against until the box is there: one end sits in a seat in the "
              "box, the other on the flank of the arm plate."),
    "steps": [
        {
            # FROM OUTSIDE. The connector's axis, read
            # from the solid, points out of the head along (-0.755, 0.656).
            # Until the nut was a body of its own the connector could get into
            # its hole from neither side: the maker's STEP carries the nut,
            # Ø16.8, fused with the body.
            "title": "The GX12 connector, from outside the head",
            "points": [
                # the connector and the LED are wired BEFORE they go in: once
                # in the head, their
                # pins face a wall a few millimetres away and the iron cannot
                # get at them
                "Wire them first, on the bench: two wires on the GX12's pins, "
                "for the 12 V terminal on the board (J3), and two on the LED's "
                "legs, for its 2-way JST XH plug (J5). Make them long enough to "
                "reach the board: the board is on the panel, and the panel comes "
                "off downwards. Once they are in the head, there is no room for "
                "the iron.",
                "The head of the box is the flat wall at the far end. The GX12 "
                "connector goes into its Ø{gx12_foro} mm hole **from the outside**, "
                "pins first, until its body sits against the outer face.",
                "Hold it there: the nut goes on from inside in the next step.",
            ],
            "mounts": ["electronics_gx12"],
            # what it goes into, for check_assembly_paths: not drawn, so not
            # in the context - the picture is about the part, not the box
            "target": ["box_collar"],
            "context": [],
            "backdrop": ["box_collar"],
            "view": {"direction": (-0.66, 0.60, 0.40), "zoom": 0.30,
                      "frame": ["electronics_gx12"],
                      "explode": {"electronics_gx12": (-22.6, 19.7, 0)},
                      "arrows": [("electronics_gx12", (10.6, -9.2, 0))]},
        },
        {
            # the nut and the LED come from inside: 16 mm along the axis -
            # past the connector's tail, 11 mm inside the wall - and down out
            # of the electronics door, which is still open
            "title": "Its nut and the status LED, from inside",
            "points": [
                "Reach in through the electronics opening in the floor. Run the "
                "nut onto the connector from inside and tighten it against the "
                "inner face of the head.",
                "The status LED sits just above the connector: push it into its "
                "hole from inside until its collar stops on the wall.",
                "Leave both sets of wires long enough inside to reach the board: "
                "the board is on the panel, and the panel comes off downwards, "
                "so those wires have to follow it.",
            ],
            "mounts": ["electronics_gx12_nut", "electronics_led"],
            # the box SOLID and cut, not see-through: through it the spring's
            # seat showed behind the nut, and read as the spring going in
            "context": ["electronics_gx12", "box_collar"],
            "path": {"electronics_gx12_nut": {"pose": [[0, 0, 0, 12.08, -10.50, 0],
                                                           [0, 0, 0, 12.08, -10.50, -60]]}},
            "view": {"direction": (0.66, 0.75, 0.25), "zoom": 0.30,
                      "frame": ["electronics_gx12", "electronics_gx12_nut",
                                   "electronics_led"],
                      # cut through the connector's axis: these come from inside
                      "cut": ["box_collar"],
                      "plane": ((40.5, 98.6, 3.4), (-0.656, -0.755, 0)),
                      "explode": {"electronics_gx12_nut": (12.1, -10.5, 0),
                                 "electronics_led": (12.1, -10.5, 0)},
                      "arrows": [("electronics_gx12_nut", (-7, 6, 0)),
                                 ("electronics_led", (-7, 6, 0))]},
        },
        {
            "title": "The spring and its cup, into their seat in the box",
            "points": [
                "Find the boss inside the box, on the outer wall, in line with the "
                "arm. The spring goes into it **from the inside**, pushed outwards "
                "until it bottoms. (The prototype's spring came from a clothes "
                "peg: {molla_filo} mm wire, Ø{molla_esterno} mm outside - any "
                "spring with those measures and about {molla_k} N/mm will do.)",
                "The cup goes on the outer end of the spring, dished side towards "
                "the spring: it is what the preload screw will push on.",
                "The box is upside down and the hatch under the motor is still "
                "open: that is the way in. Bring spring and cup up through the "
                "hatch, across towards the seat, and push them into it along its "
                "axis.",
                "The spring is {molla_libera} mm free and will end up "
                "{molla_montata} mm long with the machine together. Do not try to "
                "set anything now - that is what the grub screw is for, once the "
                "arm is in (chapter {cap_setting_the_preload}).",
            ],
            "mounts": ["preload_spring", "spring_cup"],
            "target": ["box_collar"],   # their seat, for check_assembly_paths
            "path": {"preload_spring": {"pose": [[0, 0, 0, -7.30, -3.26, 0],
                                                     [0, 0, 0, -7.30, -33.26, 0],
                                                     [0, 0, 0, -7.30, -33.26, -60]]}},
            "context": [],
            "backdrop": ["box_collar"],
            "view": {"direction": (-0.30, -0.85, 0.45), "zoom": 0.22,
                      "frame": ["preload_spring", "spring_cup"],
                      "explode": {"preload_spring": (-22, -10, 0),
                                 "spring_cup": (-22, -10, 0)},
                      # the way in, from home outwards: 8 mm back along the
                      # axis, 30 mm across towards the hatch, 60 mm down out of
                      # it. Straight back along the axis it meets the inner
                      # wall; straight down after backing out, the floor
                      # (measured on the solids)
                      "arrows": [("preload_spring", (14, 6, 0))]},
        },
        # No step slides the box sideways onto collar ears: with the
        # one-piece box+collar there is nothing to slide.
        {
            "title": "Set the preload with the grub screw",
            "points": [
                "The {grano_precarico} grub screw goes into the M4 insert in the "
                "outer wall of the box, behind the spring, and presses on the back "
                "of the cup. A {chiave_precarico} mm hex key.",
                # Two forces, not to be swapped, and the "mm more" is the
                # compression - not Travel_preload, which is the +/- adjustment
                # range of the cup. The spring gives
                # Force_spring_N at L_spring_fitted; the clutch gets Preload_N,
                # that force through the arm's lever about the pivot.
                "Run it in until you feel the spring start to load, then give it "
                "{compressione_molla} mm more: the spring goes from {molla_libera} "
                "to {molla_montata} mm and pushes with about {forza_N} N. Through "
                "the arm's lever that is roughly {precarico_N} N of the clutch on "
                "the disc, once the wheel is in. The cup has {corsa_precarico} mm "
                "of travel either way from there, to add or take off preload.",
                "Check the arm: it must still swing freely and come back by itself. "
                "If it sticks, the trouble is in the pivot, not here - go back to "
                "chapter {cap_arm_bearings_and_pivot}.",
                "!You will set this again for real in the last chapter, with the "
                "wheel in and the motor turning. What you want now is a spring that "
                "is loaded, not a spring that is crushed.",
            ],
            "mounts": ["grub_M4_preload_1"],
            "context": ["spring_cup", "preload_spring"],
            "backdrop": ["box_collar"],
            "view": {"direction": (0.85, 0.35, 0.40), "zoom": 0.22,
                      "frame": ["grub_M4_preload_1", "spring_cup"],
                      "explode": {"grub_M4_preload_1": (24, 11, 0)},
                      "arrows": [("grub_M4_preload_1", (-15, -7, 0))]},
        },
    ],
    # only the preload key: the one-piece box has no ear screws, and the
    # GX12 nut is tightened in chapter 4 with its step
    "tools": [
        "{chiave_precarico} mm hex key for the preload grub screw",
    ],
}


# ==========================================================================
# Chapter 8: the wheel body
# ==========================================================================
# The wheel goes in SIDEWAYS, not along its axis: the collar is a half ring
# open on the side away from the box, and the wheel slides into it between the
# two gaskets. Measured on the assembly: in the wheel's place - the cylinder
# r 79 between z 0 and 23 - and along all of its travel there is nothing, no
# box, no bracket, no cable; the only thing inside it is the TPU ring of the
# clutch, 256 mm3, and that is exactly why the arm has to be held back. It is
# also why the sensor comes AFTER: its magnet, glued on the hub of the disc,
# rises to z 25.3, while the bracket's pad starts at z 23 - the magnet would
# pass through the bracket.
CHAPTER_WHEEL = {
    "num": 9,
    "id": "the-wheel-body",
    "title": "The wheel body",
    "intro": ("Now the machine goes onto the wheel it was built around: a "
              "Ø{d_ruota} mm manual filter wheel. The collar is a half ring, open "
              "on the side away from the box, so the wheel does not drop in along "
              "its axis - it slides in sideways, between the two gaskets, until "
              "its centre is on the collar's centre. The magnet goes on the disc "
              "before that, because afterwards there is no way to reach it."),
    "steps": [
        {
            "title": "The detent off, the magnet on the hub of the filter disc",
            "points": [
                "With the wheel still in your hands, turn its disc through a full "
                "revolution: the knurled rim sticks {sporgenza_bordo} mm out of the "
                "window in the side of the body, and that is what your thumb is "
                "for. Feel it drop into each detent - the spring click stop that "
                "holds a manual wheel on each filter - and listen for anything that "
                "catches.",
                # the detent ALWAYS comes off: on the reference wheel the motor
                # stalled against the steep flank of the asymmetric notches and
                # needed its full 400 mA over the easy one. The firmware and the
                # driver have no "has a detent" option (rejected: a friction
                # drive cannot be relied on to climb a detent), and their log
                # sends the reader back here when a move stalls or slips.
                "Now take the detent off: unscrew it from the wheel body and put "
                "it away somewhere safe, with its spring and any small parts - you "
                "need it to use the wheel by hand again. Then screw the detent's "
                "screws back into their holes in the body, so they do not get lost.",
                "!The detent must come off, always. The motor turns the disc by "
                "friction, through the clutch, and it cannot climb out of the "
                "notches: it stalls against them, humming, and the wheel never "
                "reaches its filter. If a move ever stalls or slips later, the "
                "driver's log sends you back to this step.",
                "Turn the disc once more: it must now go round smoothly, with no "
                "clicks.",
                # the grip in the back of the box gives the thumb back: this is
                # the last time by the rim, not the last time by hand
                "!This is the last time you turn it by the rim: the clutch takes "
                "that same window, and the box closes it. Once the machine is on, "
                "the disc still turns by hand through the grip in the back of the "
                "box, rolling the tyre of the clutch with a thumb - see chapter "
                "{cap_first_checks}.",
                "Now find the centre of the filter disc on the telescope side. The "
                "{distanziale} mm printed spacer goes there first, centred on the "
                "axis - print four, it is a part that gets lost.",
                "The {magnete_mis} mm magnet goes on the spacer, with about "
                "{colla} mm of glue. Centre it: what the sensor reads is the "
                "direction of the field, and a magnet off centre reads as an error "
                "that changes with the angle.",
                "!The magnet must be magnetised **across its diameter**, not "
                "through its thickness. An axially magnetised magnet looks "
                "identical, is easy to buy by mistake, and gives no useful reading "
                "at all - and you will not find out until everything is together.",
                "Stacked up, the face of the magnet ends {magnete_sopra:.1f} mm "
                "above the face of the disc. Nothing here is adjustable, so take "
                "the time to get it flat.",
            ],
            "mounts": ["magnet_spacer", "magnet_AS5600_1"],
            "target": ["filter_disc"],  # the hub they go on, for check_assembly_paths
            "context": [],
            "backdrop": ["filter_disc", "filter_wheel_body"],
            "view": {"direction": (0.45, -0.55, 0.85), "zoom": 0.10,
                      "frame": ["magnet_spacer", "magnet_AS5600_1"],
                      "explode": {"magnet_spacer": (0, 0, 18),
                                 "magnet_AS5600_1": (0, 0, 30)},
                      "arrows": [("magnet_spacer", (0, 0, -11)),
                                 ("magnet_AS5600_1", (0, 0, -11))]},
        },
        {
            "title": "Slide the wheel into the collar",
            "points": [
                "Hold the arm back against the spring - the clutch has to be out of "
                "the way, because where the wheel is going the tyre is already.",
                "Bring the wheel in **sideways**, from the open side of the collar, "
                "with the magnet facing the telescope side. The two gasket lips will "
                "spread as the rim passes them.",
                "Push until the wheel is home against the collar flange and the "
                "magnet is on the axis. Then let the arm go: the clutch closes on "
                "the rim of the filter disc by itself.",
                "Check by eye, all the way round, that the wheel is home against "
                "the collar flange and that the magnet sits on the axis. This is "
                "what you have instead of turning it: the window the rim came "
                "through is now full of clutch.",
            ],
            "mounts": [],
            "context": ["filter_wheel_body", "filter_disc",
                         "magnet_spacer", "magnet_AS5600_1", "box_collar",
                         "clutch_hub", "clutch_tyre"],
            "backdrop": ["box_collar", "arm", "motor_14HS10-0404S"],
            "view": {"direction": (0.10, -0.40, 1.0), "up": (0, 1, 0), "zoom": 0.95,
                      "frame": ["filter_wheel_body", "box_collar"],
                      "explode": {"filter_wheel_body": (-105, 0, 0),
                                 "filter_disc": (-105, 0, 0),
                                 "magnet_spacer": (-105, 0, 0),
                                 "magnet_AS5600_1": (-105, 0, 0)},
                      "arrows": [("filter_wheel_body", (48, 0, 0), (0, 0, 45))]},
        },
    ],
    "tools": [
        "cyanoacrylate or epoxy for the magnet",
        "a screwdriver to fit the screws of the wheel's detent",
    ],
}


# ==========================================================================
# Chapter 9: the sensor, and closing up
# ==========================================================================
# The sensor goes last because its pad comes flush with the face of the wheel
# and the magnet stands up above it: with the bracket already screwed on, the
# wheel would no longer go in. And the panel is closed at the very end because
# the sensor cable has to be plugged into the board, and the board sits right
# on the panel.
CHAPTER_SENSOR = {
    "num": 11,
    "id": "sensor-and-closing-up",
    "title": "The sensor, and closing up",
    "intro": ("The sensor arch goes on last. Its pad reaches over the centre of "
              "the wheel, a hair above the face of the filter disc, with the "
              "magnet looking up at it through a hole; that is why it could not go "
              "on before the wheel. Once its cable is plugged into the board, the "
              "panel goes up under the box and the machine is closed."),
    "steps": [
        {
            "title": "The bracket, over the wheel and onto the collar",
            "points": [
                "Before it goes on, thread a 2.5 mm cable tie through the pad on "
                "the arm that faces the box: down one of the two slots, along "
                "the groove underneath, up the other one. Leave it open. Once "
                "the bracket sits on the wheel there is no way under the arm - "
                "the groove is what lets the tie pass there without lifting "
                "the bracket off the wheel.",
                "Lower the bracket so that its pad comes down over the magnet and "
                "its two feet land on the collar flange.",
                # the collar has no ears nor inserts (purchased.py): these
                # screws clamp the feet and the
                # collar flange under them into the wheel's own M3 holes
                "{vite_collare} screws, one through each foot and the collar "
                "flange under it, into the threaded M3 holes already in the "
                "rear plate of the wheel body, on the telescope side.",
                "!Do not force it down. The pad rides just above the face of the "
                "disc: if it touches, something underneath is not home - most "
                "likely the wheel is not all the way into the collar.",
            ],
            "mounts": ["screw_M3_collar_1", "screw_M3_collar_2"],
            "context": ["sensor_bracket", "box_collar", "magnet_AS5600_1",
                         "magnet_spacer"],
            "backdrop": ["filter_wheel_body", "filter_disc"],
            "view": {"direction": (0.40, -0.50, 0.80), "zoom": 0.80,
                      "frame": ["sensor_bracket"],
                      "explode": {"sensor_bracket": (0, 0, 30),
                                 "screw_M3_collar_1": (0, 0, 52),
                                 "screw_M3_collar_2": (0, 0, 52)},
                      "arrows": [("sensor_bracket", (0, 0, -18)),
                                 ("screw_M3_collar_1", (0, 0, -12)),
                                 ("screw_M3_collar_2", (0, 0, -12))]},
        },
        {
            # how the module is held: two M2 countersunk screws into the
            # pilot holes of the bracket, before the cable and the cover. A
            # step of its own: with the cover in the same picture the screws,
            # under it, do not show at all (the guide's own check says so)
            "title": "The AS5600 module, on its two screws",
            "points": [
                "The AS5600 module drops into the seat in the top of the bracket, "
                "chip side down, over the hole that looks at the magnet. It leaves "
                "about {traferro} mm of air between the chip and the magnet.",
                "Fix it with two {vite_modulo} countersunk screws, through its "
                "two holes into the pilot holes of the bracket, with a PH0 "
                "screwdriver. They form their own thread in the plastic: "
                "tighten them snug, no more.",
            ],
            "mounts": ["screw_M2_module_1", "screw_M2_module_2"],
            "context": ["sensor_bracket"],
            # the module itself is not in the model: the screws stand where
            # its board would be, above the pilot holes
            "view": {"direction": (0.45, -0.40, 0.75), "zoom": 0.12,
                      "frame": ["screw_M2_module_1", "screw_M2_module_2"],
                      "explode": {"screw_M2_module_1": (0, 0, 10),
                                 "screw_M2_module_2": (0, 0, 10)},
                      "arrows": [("screw_M2_module_1", (0, 0, -6)),
                                 ("screw_M2_module_2", (0, 0, -6))]},
        },
        {
            "title": "The cable, then the cover over the module",
            "points": [
                "Plug the cable onto the module before the cover goes on: with the "
                "cover down, the connector is no longer reachable.",
                "The cover goes on over it and takes two {vite_coperchio} screws "
                "into the M2.5 inserts you put in the bracket in chapter {cap_heat_set_inserts}. It "
                "rests on the bracket, never on the module: the module is held by "
                "its own two screws.",
                # the cover does not hold the module against its seat: the
                # two M2 screws do
            ],
            "mounts": ["sensor_cover", "screw_M25_cover_1",
                      "screw_M25_cover_2"],
            "context": ["sensor_bracket", "screw_M2_module_1", "screw_M2_module_2"],
            "view": {"direction": (0.45, -0.40, 0.75), "zoom": 0.45,
                      "frame": ["sensor_cover", "sensor_bracket"],
                      "explode": {"sensor_cover": (0, 0, 22),
                                 "screw_M25_cover_1": (0, 0, 36),
                                 "screw_M25_cover_2": (0, 0, 36)},
                      "arrows": [("sensor_cover", (0, 0, -13)),
                                 ("screw_M25_cover_1", (0, 0, -10)),
                                 ("screw_M25_cover_2", (0, 0, -10))]},
        },
        {
            "title": "Route the sensor cable down into the box",
            "points": [
                "The {sensor_cable} mm cable leaves the cover along the open "
                "channel in the arm of the bracket - it lies in from above, it does "
                "not thread through anything - and drops into the box through the "
                "opening in its wall.",
                "Keep it easy: nowhere should it bend tighter than about "
                "{raggio_cavo} mm radius.",
                "Close the cable tie you threaded under the arm over the cable, "
                "on the flat seat between the two slots, and cut the tail. It "
                "is what keeps a pull on the cable away from the solder pads of "
                "the sensor board - the weakest joint of the whole chain.",
                "!Leave enough slack inside the box for the panel to hang down on "
                "its cable when you open it again. A cable cut to exactly the right "
                "length is a cable you tear out the second time you go in.",
            ],
            "mounts": ["sensor_cable"],
            "context": ["sensor_bracket", "sensor_cover", "box_collar"],
            "backdrop": ["box_collar", "filter_wheel_body"],
            "view": {"direction": (0.45, -0.45, 0.85), "zoom": 0.55,
                      "frame": ["sensor_cable"]},
        },
        {
            "title": "Plug everything in and close the panel",
            "points": [
                "Three cables meet at the board: the motor, the sensor, and the "
                "connector and LED in the head of the box. Plug them all in with the "
                "panel still hanging free, where you can see what you are doing.",
                "Offer the panel up into its step in the underside of the box and "
                "push it flat. It sits in a rebate, so it will only go one way.",
                "Three {vite_pannellino} countersunk screws into the inserts around "
                "the opening. Start all three, then pull them down together.",
                "!Take the panel off and put it back once, now, before the machine "
                "goes anywhere. What goes wrong with a lid is never the first time "
                "it is closed - it is the second time it is opened.",
            ],
            "mounts": ["screw_M3_panel_1", "screw_M3_panel_2",
                      "screw_M3_panel_3"],
            "target": ["box_collar"],   # the panel closes the box: for check_assembly_paths
            "context": ["board_panel", "electronics_perfboard", "electronics_pin_sockets",
                         "electronics_components", "electronics_xiao",
                         "electronics_driver"],
            "backdrop": ["box_collar"],
            "view": {"direction": (0.40, -0.50, -0.90), "up": (0, 1, 0), "zoom": 0.80,
                      "frame": ["board_panel"],
                      "explode": {"board_panel": (0, 0, -34),
                                 "electronics_perfboard": (0, 0, -34),
                                 "electronics_pin_sockets": (0, 0, -34),
                                 "electronics_components": (0, 0, -34),
                                 "electronics_xiao": (0, 0, -34),
                                 "electronics_driver": (0, 0, -34),
                                 "screw_M3_panel_1": (0, 0, -52),
                                 "screw_M3_panel_2": (0, 0, -52),
                                 "screw_M3_panel_3": (0, 0, -52)},
                      "arrows": [("board_panel", (0, 0, 20), (-46, -31, 0)),
                                 ("screw_M3_panel_1", (0, 0, 12)),
                                 ("screw_M3_panel_2", (0, 0, 12)),
                                 ("screw_M3_panel_3", (0, 0, 12))]},
        },
    ],
    # the AS5600 module and its capacitor on the module's pads: no body in
    # the assembly, so by reference. In chapter 11 too, which can be skipped
    "electronics": ["U3", "C3"],
    "tools": [
        "2.5 mm hex key",
        "{chiave_M25} mm hex key for the cover screws",
        # the module's screws too
        "a PH0 screwdriver for the countersunk module and panel screws",
        "one 2.5 mm cable tie",
    ],
}


# ==========================================================================
# Chapter 10: the first checks
# ==========================================================================
# It mounts nothing, and that is why the sequence check lets it show the whole
# machine: the exemption is not asked for with a flag in the data, it is earned
# by mounting nothing.
CHAPTER_CHECKS = {
    "num": 12,
    "id": "first-checks",
    "title": "First checks",
    "intro": ("Everything below is done on the bench, with the machine on the "
              "table and nothing screwed to a telescope. The order matters, and "
              "not only because each check assumes the one before it passed: "
              "each one **isolates one thing**. When something is wrong, you "
              "want to be looking at one possible cause and not three - three is "
              "how an evening goes, and this project has spent one that way."),
    "steps": [
        {
            "title": "Before any power, by eye and by the preload screw",
            "points": [
                # not "the disc can no longer be turned by hand": step 5 and
                # the last step turn it by hand, through the clutch, in the grip
                "!The disc no longer turns by its own rim: the clutch now fills "
                "the window its knurled rim used to stick out of. It turns "
                # a glove, not to leave grease on the friction surface
                "through the clutch - a thumb on the tyre (better with a glove, "
                "so as not to leave grease on it), in the recess at the "
                "back of the box that the last step closes - and step 3 uses "
                "that. This first step needs no turning at all.",
                "Look down the gap between the collar and the wheel, all the way "
                "round: the wheel must be home against the flange everywhere, with "
                "an even gap.",
                # the pad is the bracket's, not the cover's
                "Look at the sensor bracket from the side. There must be daylight "
                "between its pad, under the cover, and the face of the disc.",
                "The one moving thing you can still reach is the preload. Back the "
                "{grano_precarico} grub screw right out until the spring goes "
                "slack, then take it back in to where it was, feeling the point "
                "where the spring starts to load. It must move smoothly the whole "
                "way - if it grinds or steps, the arm is binding on its pivot, and "
                "that is worth opening the box for now rather than on a mount in "
                "the dark.",
            ],
            "mounts": [],
            "context": ["filter_wheel_body", "filter_disc", "box_collar",
                         "sensor_bracket", "sensor_cover",
                         "front_gasket", "rear_gasket"],
            "view": {"direction": (0.55, -0.75, 0.55), "zoom": 0.95,
                      "frame": ["box_collar", "filter_wheel_body"]},
        },
        # WHEN THE 12 V GO ON AND OFF, said at each step: a chapter that uses
        # them from its second step and only in its fifth says "USB first,
        # with nothing else connected" leaves the reader guessing.
        {
            "title": "The two supplies: when the 12 V go on, and when they come off",
            "points": [
                "The machine has two supplies, and they do different things. The "
                "**USB** from the computer runs the board: firmware, sensor, "
                "status LED. The **12 V**, through the GX12 at the head of the "
                "box, run only the motor driver and the motor. Everything the "
                "board has to say, it says on USB alone.",
                "**On** only to turn the motor: from step 4 to step 7 here, and "
                "on the telescope. The USB goes in first and the 12 V after, "
                "as the wiring booklet does; the other order does not harm the "
                "driver, but this way the board is already up and watching when "
                "the motor side wakes.",
                "!**Off** - pull the GX12 lead - before you plug or unplug "
                "anything inside the box, the motor above all: a stepper pulled "
                "off a live driver kills it on the spot. Off before the panel "
                "comes out, and off when you have finished: 12 V first, then the "
                "USB.",
                "Turning the disc by hand does not need them off: at rest the "
                "motor is released, and a thumb on the clutch turns it. Turn "
                "slowly. If you turned a holding current on (Options), take the "
                "12 V off first, or you are fighting the motor; and set the LED "
                "to Off if you do not want its alarm flashes - to the firmware, a "
                "disc moved by hand is a drift.",
            ],
            "mounts": [],
        },
        {
            "title": "USB only: the board comes up, and reads the angle",
            "points": [
                "Plug in the USB only - the port comes out at the head of the "
                "box - and leave the 12 V off. Check that the status LED comes "
                "up.",
                "Turn the disc slowly with a thumb on the clutch tyre, in the "
                "grip at the back of the box, and watch the angle the sensor "
                "reports. It must change smoothly and come back to the same value "
                "at the same filter, to within a fraction of a degree.",
                "!If the reading jumps or sticks, stop: it is almost always the "
                "magnet - not centred, or magnetised through its thickness instead "
                "of across its diameter.",
            ],
            "mounts": [],
            "context": ["box_collar", "board_panel", "electronics_perfboard",
                         "electronics_xiao", "electronics_driver",
                         "electronics_gx12", "electronics_gx12_nut", "electronics_led"],
            "backdrop": ["box_collar", "filter_wheel_body"],
            "view": {"direction": (0.50, 0.75, -0.55), "up": (0, 0, 1), "zoom": 0.45,
                      "frame": ["electronics_gx12", "electronics_led"]},
        },
        {
            "title": "Now the 12 V: the driver chip, before anything turns",
            "points": [
                "Plug in the 12 V. Then `cd firmware && ./flash.sh driver_test` "
                "asks the board what it "
                "can see, which is faster than a multimeter and wrong less often.",
                "It answers two questions. First, **does the single-wire UART "
                "echo?** Four bytes go out and must come straight back, because "
                "TX and RX are joined through the 1 kΩ resistor - and that is "
                "true whether or not the driver chip is alive. No echo means the "
                "fault is in the wire or that resistor, and the driver is not "
                "even a suspect yet.",
                "Second, **who answers, and at which address**. It prints the "
                "silicon version: `0x20` is a TMC2208, `0x21` a TMC2209. The "
                "firmware accepts both.",
                "!From here on the 12 V must be on: without them the chip is "
                "simply off and says nothing, and that silence is not a finding.",
                "!Never unplug the motor with the 12 V in - it kills the driver "
                "instantly. The motor goes in before the power, not after.",
            ],
            "mounts": [],
        },
        {
            "title": "Does the motor turn, and are the phases paired right?",
            "points": [
                "`./flash.sh motor_test` runs one full turn one way and one "
                "back, reading the driver's status half way through each.",
                "**Watch the shaft.** This step exists for a fault no register "
                "can see: the four driver outputs are two **pairs**, A with A and "
                "B with B, and if the four-way connector breaks a pair the motor "
                "buzzes, warms up and stays put. As far as the driver is "
                "concerned two coils are connected, so it reports nothing wrong.",
                "The right pairs on this motor are **black+green** and "
                "**red+blue**.",
                "Two opposite turns and the power side is good.",
            ],
            "mounts": [],
        },
        {
            "title": "How much current your clutch wants",
            "points": [
                "`./flash.sh torque_test` climbs in steps - 150, 200, 250, 300, "
                "350 mA - and holds the motor turning for eight seconds at each, "
                "so you can **resist the clutch with your hand** and feel where "
                "it stops slipping.",
                "You are at the wheel and not at the screen, so the motor tells "
                "you which step it is on: before each one it makes that many "
                "short **nudges**, countable by ear or with a hand on the disc.",
                "The reference build settled at **350 mA**, and that is the "
                "firmware default. Yours may want less.",
                "!It stops below the motor's 400 mA rating on purpose. If the "
                "clutch still slips at the top step, the answer is not the last "
                "fifty milliampere: it is the **spring preload**, because that is "
                "what sets the slipping threshold, not the motor.",
                "!At 350 mA the motor burns about 7 W while it moves. That is "
                "nothing for the two seconds of a filter change, because the "
                "holding current is zero and the motor is released at rest - but "
                "it would be a different matter with holding turned on.",
            ],
            "mounts": [],
        },
        {
            "title": "Under power, one position at a time",
            "points": [
                "With the 12 V still on, ask for the next filter position. The "
                "disc should turn, slow down, and settle on its position.",
                # the shortest way is the factory direction, and the detent is
                # always removed (chapter 10): a stall
                # means a detent left in place, or a clutch slipping
                "Go round all the positions twice. The wheel takes the shortest way "
                "round (the panel's Direction of travel) and creeps into each "
                "position in a few short legs. A move that runs away from its target "
                "instead means J1's phase order does not match the firmware (chapter "
                "{cap_motor_into_the_clutch}); a position that is not reached means "
                "the motor stalled or the clutch is slipping - check first that the "
                "wheel's detent is really off (chapter {cap_the_wheel_body}).",
                "It is the first time the wheel finds its positions by itself, so "
                "watch and listen for the whole first revolution.",
                "If it slips, bring the preload grub screw in by a quarter turn at a "
                "time - no more - and try again.",
                "!Only when all of this passes should the machine go on a telescope. "
                "It is much easier to take the panel off on a table than at the back "
                "of a mount in the dark.",
                "Done: the 12 V off first, then the USB.",
            ],
            "mounts": [],
            "context": ["filter_wheel_body", "filter_disc", "box_collar",
                         "sensor_bracket", "sensor_cover",
                         "sensor_cable", "electronics_gx12", "electronics_gx12_nut", "electronics_led"],
            "view": {"direction": (0.60, -0.55, 0.60), "zoom": 0.95,
                      "frame": ["filter_wheel_body", "box_collar"]},
        },
        {
            "title": "Turn it by hand, then close the grip",
            "points": [
                "Find the recess in the back of the box, in line with the clutch. "
                "The black tyre of the clutch stands {sporgenza_presa} mm out of it: "
                "roll it with a thumb and the disc turns. A little over half a turn "
                "of the thumb moves one filter along.",
                "Use it now to check by hand what you have just watched under power, "
                "and use it later whenever the filters or the optical train need "
                "cleaning with the train off.",
                "The cover goes in **from above**. The two thick tabs under its "
                "foot drop into their pockets at the bottom of the recess, the "
                "tongue at the spring end runs down the groove in the end wall, "
                "the flat top drops into the opening over the motor and the "
                "two small round tabs into the pockets in the collar. It all "
                "comes flush with the top of the box.",
                "Fix it with two {vite_presa} socket head screws with a "
                # through the small round tabs over the collar, not the thick
                # ones under the foot the paragraph above names first
                "**knurled** head, one through each small round tab, into the "
                "inserts in the "
                "collar. Their heads stand on the tabs, above the top of the box, "
                "so they turn by hand. The cover also wraps the top of the curved "
                "wall, and the two screws are what make sure it stays closed.",
                "To take it off, undo both screws with your fingers - no key "
                "needed - then hook a fingernail in the "
                "notch across its face - "
                "the one in line with the clutch - and pull straight up: the "
                "flat top of the notch is the face to pull on.",
                "!Leave the cover on whenever you are not turning the wheel by hand. "
                "The opening looks onto the friction surface, and dust that settles "
                "there is dust between the clutch and the disc.",
            ],
            "mounts": ["grip_cover", "screw_M3_cover_1", "screw_M3_cover_2"],
            "context": ["box_collar", "clutch_hub", "clutch_tyre"],
            # from high up: the cover also has a flat top over the motor and a
            # screw in the collar, and from the side of the recess neither can
            # be seen
            "view": {"direction": (0.60, -0.25, 0.75), "zoom": 0.30,
                      "frame": ["grip_cover", "screw_M3_cover_1"],
                      "explode": {"grip_cover": (0, 0, 26),
                                 "screw_M3_cover_1": (0, 0, 40),
                                 "screw_M3_cover_2": (0, 0, 40)},
                      "arrows": [("grip_cover", (0, 0, -16)),
                                 ("screw_M3_cover_1", (0, 0, -10)),
                                 ("screw_M3_cover_2", (0, 0, -10))]},
        },
    ],
    "tools": [
        "a USB-C cable",
        "the 12 V supply and its GX12 lead",
        "{chiave_precarico} mm hex key, in case the preload needs a touch",
        # the cover screws are knurled and go in by hand; the key only if a
        # finger is not enough
        "{chiave_motore} mm hex key, only if the knurled cover screws are too "
        "tight for your fingers",
    ],
}


# The plan of the chapters, in assembly order. It is here and not in a separate
# document because the guide's index is generated from here: a list written by
# hand comes loose at the first chapter added, and the reader does not notice.
# Written = the chapter exists in CHAPTERS; the others are still to be written.
# The order is not a preference: it is the one the geometry leaves open.
# Above the clutch the wheel body starts at z 14.30, one millimetre and three
# tenths above its top, so with the wheel mounted the clutch no longer slides
# onto the shaft and the arm+motor group does not have the 8 mm of travel it
# needs to climb onto the pivot. Two consequences follow that decide the order:
# the wheel goes in **last**, and the clutch goes on the shaft **after** the
# motor is on the arm - its 50 mm diameter does not pass through the arm's
# 7 mm hole. Confirmed on the real parts.
# ==========================================================================
# Chapter 10: the air gap
# ==========================================================================
# It sits BETWEEN the magnet and the bracket, and the place is not chosen for
# convenience: the magnet must already be glued because it is what is
# measured, and the bracket must not be there yet because the height found
# here is its own.
CHAPTER_AIR_GAP = {
    "num": 10,
    "id": "setting-the-air-gap",
    "title": "Setting the air gap",
    "intro": ("The sensor reads a magnet through a gap of less than a "
              "millimetre, and that gap is set by one dimension of one printed "
              "part - the pad the bracket stands on. Too far and the field is "
              "too weak to resolve; too close and the magnet touches the chip. "
              "This chapter finds the right height by measuring, not by "
              "calculating, because the stack it depends on includes the glue."),
    "skip": ("If you are building on the same wheel this project was drawn "
              "around - a {ruota_rif} mm manual filter wheel, {disco_rif} mm "
              "across the rotating disc - with the same {magnete_rif} mm "
              "diametral magnet, **skip straight to the next chapter**: the "
              "bracket as published already carries the height this procedure "
              "arrived at. Come back here only if the readings in "
              "chapter {cap_first_checks} come out poor."),
    "steps": [
        {
            "title": "Why this cannot be calculated",
            "points": [
                "The design stack says the spacer and magnet sit 1.8 mm above the "
                "hub face. Glued on a real pivot it **measures 2.3** - half a "
                "millimetre disappears into the two joints and the print "
                "tolerance of the spacer.",
                "Half a millimetre is not a detail here: without counting it the "
                "bracket comes out that much too low, and the real gap was "
                "**0.07 mm** - the magnet grazing the chip.",
                "So the height is chosen by trying feet of known thickness and "
                "reading what the sensor says. It takes twenty minutes and it is "
                "the only way to include the glue.",
            ],
            "mounts": [],
        },
        {
            "title": "Print the feet and the spacer",
            "points": [
                "`out/tools/gap_gauges.step` holds {piedini_n} feet, "
                "{piedini_da} to {piedini_a} mm tall - gaps from {traferro_da} to "
                "{traferro_a} mm - with the height engraved on the "
                "tab. `out/magnet_spacer.step` is the spacer the magnet sits on.",
                "!In the slicer, **do not also turn on hole compensation**: the "
                "magnet hole is already drawn oversize for it, and the two "
                "corrections add up.",
                "After printing, **measure the magnet hole with a caliper** and "
                "tell the model: `Comp_hole_printing` is a number about your "
                "printer, not about this project, and from then on it applies to "
                "the real bracket too - which wants that fit tight.",
                "You also need two **M2 × 4** screws, cylinder or countersunk "
                "head: they cut their own thread in the 1.8 mm hole. Longer ones "
                "poke through and hold the foot off the face.",
            ],
            "mounts": [],
        },
        {
            "title": "Wire the sensor board on the bench",
            "points": [
                "Any ESP32 will do for this - a WROOM-32 on a breadboard is fine, "
                "it does not have to be the XIAO. Power the AS5600 module at "
                "**3.3 V**, SDA and SCL to the two I²C pins, and DIR to ground.",
                "!The module must carry its **VDD5V-VDD3V3 jumper**, and after "
                "that jumper it no longer tolerates 5 V. Check continuity between "
                "pins 1 and 2 of the chip before you power anything: a lifted "
                "jumper does not go silent, it quietly halves the readings and "
                "looks exactly like a weak magnet.",
                "Load `firmware/air_gap_test/air_gap_test.ino`: "
                "`cd firmware && ./flash.sh air_gap_test`.",
            ],
            "mounts": [],
        },
        {
            "title": "Read it on the page, not on the serial monitor",
            "points": [
                "`cd firmware && ./gap_page.sh` serves the test bench on "
                "**http://localhost:8770/** and opens it. It shows AGC live, "
                "lights up the sectors of the turn as you cover them, and keeps "
                "the table of measurements with the suggested gap already worked "
                "out.",
                "!It needs **Chrome or Edge**: the page talks to the board over "
                "Web Serial, which Safari and Firefox do not have. And it must be "
                "served over localhost, not opened as a file.",
                "!Close any other serial monitor first - the IDE's, or the one "
                "`flash.sh` leaves open. One program at a time can hold the port.",
            ],
            "mounts": [],
        },
        {
            "title": "One foot at a time, and turn the disc a full turn",
            "points": [
                "Wheel on the table, telescope side up. Foot on the face with its "
                "ring around the magnet - it centres itself and stays there under "
                "its own weight - then the sensor board **screwed down on top**.",
                "!Screwed, not just resting. A board that only sits there lifts, "
                "and then the foot is not what sets the gap any more. It is the "
                "first mistake to not make twice.",
                "For each foot: `r` on the page or the monitor, **one whole turn** "
                "of the disc by hand - take it by the knurled rim - then `s` for "
                "the summary. A full turn matters because the magnet is never "
                "perfectly centred, and a single spot flatters or punishes it.",
                "Judge on **magnitude**, not on AGC. With this magnet at 3.3 V the "
                "AGC sits at full scale whatever the height, so it tells you "
                "nothing; magnitude is the number that moves.",
                "!If even the lowest foot cannot bring the readings up, the "
                "{magnete_rif} mm magnet is too weak as it stands and you want a "
                "thicker one. That is a conclusion, not a failure.",
            ],
            "mounts": [],
            # the test page three quarters of the way round a turn, simulated
            # (firmware/gap_page/index.html?demo=0.75): 27 of 36 sectors lit
            "screenshot": "rotation-test.png",
        },
    ],
    # the module is wired on the bench here; it has no body in the assembly,
    # so it enters the list by its reference
    "electronics": ["U3"],
    "tools": [
        "any ESP32 board on a breadboard - it does not have to be the XIAO",
        "2 × M2 × 4 screws, cylinder or countersunk head",
        "a 2 mm flat screwdriver, or the driver for those heads",
        "a caliper",
        "Chrome or Edge: the test page uses Web Serial",
    ],
}

CHAPTERS += [CHAPTER_BOARD, CHAPTER_BOX, CHAPTER_WHEEL, CHAPTER_AIR_GAP,
             CHAPTER_SENSOR, CHAPTER_CHECKS]

# ==========================================================================
# STRATEGY C: the order the one-piece box allows
# ==========================================================================
# The box and the collar are one part, and it is there from the first
# insert: nothing is lowered over the mechanism any more, everything goes
# INTO it. check_assembly_paths decided the order:
#  - the spring and its cup go in BEFORE the arm: they sit between the arm
#    plate and their seat, and with the arm in they went through it (357 mm3);
#    the connector goes with them, it only needs the box;
#  - the arm goes in from below along a declared path, through the
#    electronics opening with washer and screw already on (found on the real
#    assembly; rejected: through the hatch, with the screw fitted last);
#  - the clutch goes in BEFORE the motor, from the middle of the collar: on
#    the shaft it is caged under the roof;
#  - the motor comes up through the hatch into the clutch; its screws go in
#    from above through the holes in the clutch;
#  - the preload is set once the arm is there to push against.
CHAPTER_SPRING = {
    "num": 4,
    "id": "spring-and-connector",
    "title": "The spring and the connector, before the arm",
    "intro": ("Two things go into the box before the arm does. The preload spring "
              "and its cup sit between their seat in the box and the flank of the "
              "arm plate: once the arm is in, there is no room left to put them "
              "there. And the GX12 connector and the status LED go into the head "
              "of the box now, while nothing is in the way of the nut."),
    # chosen by WHAT THEY MOUNT, not by position: with [:2] the spring step
    # slid into the preload chapter - after the arm, the very order strategy
    # C must avoid - as soon as the connector step was split in two, and
    # chapter 4 showed the nut and no spring
    "steps": [p for p in CHAPTER_BOX["steps"]
              if set(p["mounts"]) & {"electronics_gx12", "electronics_gx12_nut",
                                    "electronics_led", "preload_spring", "spring_cup"}],
    # never empty (the page would say "Tools: .") - the nut of the GX12 is
    # tightened in step 2
    "tools": ["a 14 mm spanner, for the nut of the GX12 connector",
              # they are wired before they go in
              "a soldering iron, to wire the connector and the LED first"],
}
CHAPTER_BOX["steps"] = [p for p in CHAPTER_BOX["steps"]
                             if p not in CHAPTER_SPRING["steps"]]
# and the order must say so: the spring before the arm, or check_assembly_paths
# sees the arm go through it
assert any("preload_spring" in p["mounts"] for p in CHAPTER_SPRING["steps"]), \
    "the spring step is not in the chapter before the arm"
CHAPTER_BOX["id"] = "setting-the-preload"
CHAPTER_BOX["title"] = "Setting the preload"
CHAPTER_BOX["intro"] = ("The spring has been in its seat since before the arm went "
                             "in. Now that the arm and the motor are there for it to push "
                             "against, the grub screw behind the seat sets how hard the "
                             "clutch is pressed on the filter disc.")
_CLUTCH = [c for c in CHAPTERS if c["id"] == "clutch-on-the-motor-shaft"][0]
_CLUTCH["id"] = "clutch-before-the-motor"
_CLUTCH["title"] = "The clutch, before the motor"
_CLUTCH["intro"] = ("The clutch is what pushes the filter disc: a printed ASA hub with a "
                      "co-printed TPU tyre around it, gripping the motor shaft on its milled "
                      "flat through a grub screw. It goes in now, before the motor: once "
                      "it is on the shaft it cannot be lifted off - the roof of the box "
                      "is a millimetre above it - so it is put in place first, from the "
                      "middle of the collar, and the motor comes up into it. Its insert "
                      "is already in, from chapter {cap_heat_set_inserts}.")
# the last sentence: the clutch arrives here with its insert, planted in
# chapter 2 with all the others
CHAPTER_MOTOR["id"] = "motor-into-the-clutch"
CHAPTER_MOTOR["title"] = "The motor, up into the clutch"
CHAPTER_MOTOR["intro"] = ("The motor comes in last of the mechanism, from below through "
                            "the hatch in the floor, and its shaft finds the clutch that "
                            "is already waiting over the arm. Then the clutch is locked on "
                            "the shaft, the four motor screws go in from above through the "
                            "holes in the clutch, and the hatch is closed.")
for _c, _n in ((CHAPTER_ZERO, 0), (CHAPTER_PARAMETERS, 1), (CHAPTER_INSERTS, 2),
               (CHAPTER_GASKETS, 3), (CHAPTER_SPRING, 4), (CHAPTER_ARM, 5),
               (_CLUTCH, 6), (CHAPTER_MOTOR, 7), (CHAPTER_BOX, 8),
               (CHAPTER_BOARD, 9), (CHAPTER_WHEEL, 10), (CHAPTER_AIR_GAP, 11),
               (CHAPTER_SENSOR, 12), (CHAPTER_CHECKS, 13)):
    _c["num"] = _n
CHAPTERS.append(CHAPTER_SPRING)
CHAPTERS.sort(key=lambda c: c["num"])

PLAN = [
    (0,  "Parts, tools and printing", "the general bill of materials, what to print and how"),
    (1,  "Making it fit your wheel", "the parameters page: skip it if your wheel is the reference one"),
    (2,  "Heat-set inserts", "all the inserts, in the order that keeps the iron reachable"),
    (3,  "The collar and its gaskets", ""),
    (4,  "The spring and the connector, before the arm", "with the arm in there is no room for them"),
    # through the electronics opening, screw already on - not through the
    # hatch
    (5,  "Arm, bearings and pivot", "in from below through the electronics opening, screw already on"),
    (6,  "The clutch, before the motor", "on the shaft it is caged under the roof"),
    (7,  "The motor, up into the clutch", "through the hatch; its screws go through the clutch"),
    (8,  "Setting the preload", "once the arm is there to push against"),
    (9,  "The board in its panel", "the board drops in between the two guides"),
    # The wheel goes in SIDEWAYS - the collar is a half ring - and comes BEFORE
    # the sensor (measured on the assembly: with the bracket already screwed
    # on, the magnet glued on the hub of the disc does not get past).
    (10, "The wheel body", "it slides in sideways, and the magnet goes on first"),
    (11, "Setting the air gap", "measured and not calculated: the glue is in the stack"),
    (12, "The sensor, and closing up", "the bracket reaches over the wheel, so it goes on last"),
    (13, "First checks", "before you put it on a telescope"),
]
