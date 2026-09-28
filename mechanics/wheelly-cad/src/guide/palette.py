# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The colour of every part, and its name in English. One place only.

**A part keeps the same colour from the first step to the last**, and keeps it
outside the guide too - in the frames that will serve to present the project.
It is a rule with a precise reason: the colour is the only
thing that ties a part seen in chapter 3 to the same part seen again in
chapter 9, from another side, half covered and with no label. If it changes,
whoever assembles no longer recognises it.

That is why the colours are NOT chosen step by step: they are asked for here
by the name of the body in the assembly. A step may decide to show a part
see-through - the context around what is being assembled - but the TINT stays
its own: the opacity changes, not the colour.

The reader's name sits here next to the colour for the same reason: a body
name of the model, even an English one, is not a reader's word, and the
correspondence between the two worlds must be in one place only, or the same
part ends up called two ways in two chapters.
"""

# name of the body in the assembly -> (colour, English name)
# The printed parts have distinct, saturated tints; the bought ones sit on
# "hardware shop" tints - steel, brass - so what comes out of the printer can
# be told at a glance from what is bought.
PARTS = {
    "filter_wheel_body":      ((0.74, 0.74, 0.78), "filter wheel body"),
    "filter_disc":      ((0.24, 0.62, 0.55), "filter disc"),
    "arm":                ((0.82, 0.25, 0.48), "arm"),
    "clutch_hub":     ((0.91, 0.56, 0.08), "clutch hub"),
    "clutch_tyre":    ((0.24, 0.24, 0.28), "clutch tyre"),
    "box_collar":         ((0.60, 0.65, 0.72), "box and collar"),
    "sensor_bracket":         ((0.33, 0.70, 0.45), "sensor bracket"),
    "sensor_cover":      ((0.58, 0.80, 0.62), "sensor cover"),
    "board_panel":             ((0.55, 0.45, 0.72), "board panel"),
    "spring_cup":       ((0.95, 0.72, 0.26), "spring cup"),
    "grip_cover":             ((0.45, 0.72, 0.45), "grip cover"),
    "hatch_cover":            ((0.66, 0.52, 0.80), "motor hatch cover"),
    "pivot_washer":         ((0.98, 0.84, 0.35), "pivot washer"),
    "front_gasket":  ((0.16, 0.48, 0.32), "front gasket"),
    "rear_gasket": ((0.16, 0.48, 0.32), "rear gasket"),
    "magnet_spacer":    ((0.86, 0.86, 0.90), "magnet spacer"),
    "sensor_cable":           ((0.14, 0.14, 0.17), "sensor cable"),
    "preload_spring":        ((0.62, 0.66, 0.30), "preload spring"),
    "magnet_AS5600":         ((0.78, 0.14, 0.14), "magnet"),
    "motor_14HS10-0404S":    ((0.30, 0.34, 0.40), "stepper motor"),
    "bearing_F695ZZ":      ((0.60, 0.63, 0.66), "F695ZZ bearing"),
    "electronics_perfboard":    ((0.18, 0.50, 0.28), "perfboard"),
    "electronics_pin_sockets":    ((0.10, 0.10, 0.10), "pin sockets"),
    "electronics_xiao":       ((0.24, 0.30, 0.70), "XIAO ESP32-S3"),
    "electronics_driver":     ((0.72, 0.16, 0.16), "TMC2208 driver"),
    "electronics_components": ((0.16, 0.24, 0.58), "discrete components"),
    "electronics_led":        ((0.86, 0.12, 0.12), "status LED"),
    "electronics_gx12":       ((0.68, 0.70, 0.72), "GX12 connector"),
    "electronics_gx12_nut":   ((0.52, 0.53, 0.56), "GX12 nut"),
}

# the families of fasteners: steel the screws, brass the inserts. A fastener
# does not need a tint of its own - there are twenty-five of them - but it
# needs all the screws to look alike and none of them to look like an insert.
#
# The prefixes are the names of the bodies. When the bodies were renamed the
# prefixes matched nothing, and every screw and insert came out in the
# neutral grey of an unknown part - the inserts no longer brass in any
# picture, and no check noticed. problems() now fails when an item of ITEMS
# falls into no family.
FAMILIES = (("screw_",  (0.56, 0.58, 0.62), "screw"),
            ("grub_",   (0.40, 0.42, 0.46), "grub screw"),
            ("insert_", (0.76, 0.56, 0.20), "heat-set insert"))

# The fasteners, as the guide calls them. The family is enough to colour them
# - the screws all steel, the inserts all brass - but not to name them: in a
# chapter that sets eleven inserts, "heat-set insert" eleven times does not
# tell whoever assembles which one goes where. The key is the name of the
# item in purchased.py, which is the only place where those parts really
# exist.
ITEMS = {
    "insert_M3_pivot":                  "M3 insert · pivot",
    "insert_M3_ear":              "M3 insert · collar ear",
    "insert_M3_panel":             "M3 insert · panel screw",
    "insert_M3_grub":                  "M3 insert · clutch grub screw",
    "insert_M2_post":            "M2 insert · board post",
    "insert_M25_head_post": "M2.5 insert · board post, head end",
    "insert_M25_cover":            "M2.5 insert · sensor cover",
    "screw_M3_pivot":                     "M3 screw · pivot",
    "screw_M3_ear":                 "M3 screw · collar ear",
    "screw_M3_panel":                "M3 screw · panel",
    "screw_M3_collar":                   "M3 screw · collar clamp",
    "screw_M3_motor":                    "M3 screw · motor",
    "screw_M2_board":                 "M2 screw · board",
    "screw_M25_board":               "M2.5 screw · board",
    "screw_M25_cover":               "M2.5 screw · sensor cover",
    # the module's two screws
    "screw_M2_module":                "M2 screw · AS5600 module",
    "grub_M3_clutch":               "M3 grub screw · clutch",
    "bearing_F695ZZ":                     "F695ZZ bearing",
    "magnet_AS5600":                        "magnet",
    "motor_NEMA14":                        "stepper motor",
    "preload_spring":                        "preload spring",
    "insert_M3_cover":                       "M3 insert · grip cover",
    "insert_M3_hatch":                       "M3 insert · hatch cover",
    "insert_M4_preload":                     "M4 insert · preload screw",
    "screw_M3_cover":                        "M3 screw · grip cover, knurled head",
    "screw_M3_hatch":                        "M3 screw · hatch cover",
    "grub_M4_preload":                       "M4 grub screw · preload",
}

# The print orientations, in English. In Italian they are in bom_mechanics.py,
# which is the project's bill of materials; here they are translated because
# the guide is published, and the orientation a part is printed in is a
# design datum like a dimension - not a choice of whoever prints.
ORIENTATIONS = {
    # two ways to lay it, and the bed each needs, MEASURED on the STEP by
    # bed.py (rejected: a hand-written "wants a 200 x 200 bed", which did not
    # offer the face of the GX12 nor follow the part)
    "box_collar": "the electronics door on the plate: a {piatto_sportello} × "
                  "{piatto_sportello} mm bed, the part turned {giro_sportello}° on it, "
                  "{alto_sportello} mm tall; or the face of the GX12 connector on the "
                  "plate: {piatto_testa} × {piatto_testa} mm, turned {giro_testa}°, "
                  "{alto_testa} mm tall",
    "clutch_hub": "axis vertical, collar face on the plate",
    "clutch_tyre": "co-printed with the hub",
    "board_panel": "outer face on the plate",
    "grip_cover": "upside down, top face on the plate",
    "hatch_cover": "outer face on the plate - the face in sight, flush with the floor",
    "arm": "top face on the plate - body and motor plate end on the same plane",
    "magnet_spacer": "four of them - it is a part that gets lost",
    "front_gasket": "flat on the bed, lip up (co-print it with the "
                             "collar if you have a multi-material printer)",
    "rear_gasket": "flat on the bed, lip up (co-print it with the "
                              "collar if you have a multi-material printer)",
    # The four below are derived from their shape and what each one must get
    # right:
    # - the bracket's pad sets the air gap, and the module's seat is measured
    #   from it: both are then heights along Z, the printer's best axis, and
    #   the magnet's ring is a vertical hole;
    # - the sensor cover's outer face is the one in sight and flat, the
    #   pockets that press the module open upwards, no supports;
    # - the spring cup's flat back is where the grub screw pushes: on the
    #   plate it is the flattest face there is, and the dish opens upwards;
    # - the pivot washer is a flanged sleeve: flange down, sleeve up along its
    #   own axis, as a long narrow hole wants (CONTRIBUTING.md).
    "sensor_bracket": "the flat underside, with the pad, on the plate",
    "sensor_cover": "outer face on the plate",
    "spring_cup": "flat back on the plate, dish up",
    "pivot_washer": "flange on the plate, sleeve up",
}

UNKNOWN = (0.80, 0.80, 0.84)

# ----------------------------------------------------------------- in Italian
# The guide comes out in Italian too, and a part has to
# be called the same in the chapter text and in its list: these are the words
# the Italian chapters in guide/it/ already use - "collare", "botola",
# "battistrada", "pannellino", "scodellino". Kept here, next to the English,
# and not in the chapter catalogues, for the reason the English is here: one
# place per name. problems() fails the build on a part with no Italian name.
NAMES_IT = {
    "filter_wheel_body": "corpo della ruota",
    "filter_disc": "disco dei filtri",
    "arm": "braccio",
    "clutch_hub": "mozzo della frizione",
    "clutch_tyre": "battistrada della frizione",
    "box_collar": "scatola e collare",
    "sensor_bracket": "staffa del sensore",
    "sensor_cover": "coperchio del sensore",
    "board_panel": "pannellino della basetta",
    "spring_cup": "scodellino della molla",
    "grip_cover": "coperchio della presa",
    "hatch_cover": "coperchio della botola del motore",
    "pivot_washer": "rondella del perno",
    "front_gasket": "guarnizione anteriore",
    "rear_gasket": "guarnizione posteriore",
    "magnet_spacer": "distanziale del magnete",
    "sensor_cable": "cavo del sensore",
    "preload_spring": "molla di precarico",
    "magnet_AS5600": "magnete",
    "motor_14HS10-0404S": "motore passo-passo",
    "bearing_F695ZZ": "cuscinetto F695ZZ",
    "electronics_perfboard": "basetta millefori",
    "electronics_pin_sockets": "zoccoli a strip",
    "electronics_xiao": "XIAO ESP32-S3",
    "electronics_driver": "driver TMC2208",
    "electronics_components": "componenti discreti",
    "electronics_led": "LED di stato",
    "electronics_gx12": "connettore GX12",
    "electronics_gx12_nut": "dado del GX12",
}

FAMILIES_IT = {"screw_": "vite", "grub_": "grano", "insert_": "inserto a caldo"}

ITEMS_IT = {
    "insert_M3_pivot": "inserto M3 · perno",
    "insert_M3_ear": "inserto M3 · orecchia del collare",
    "insert_M3_panel": "inserto M3 · vite del pannellino",
    "insert_M3_grub": "inserto M3 · grano della frizione",
    "insert_M2_post": "inserto M2 · colonnina della basetta",
    "insert_M25_head_post": "inserto M2,5 · colonnina della basetta, lato testata",
    "insert_M25_cover": "inserto M2,5 · coperchio del sensore",
    "screw_M3_pivot": "vite M3 · perno",
    "screw_M3_ear": "vite M3 · orecchia del collare",
    "screw_M3_panel": "vite M3 · pannellino",
    "screw_M3_collar": "vite M3 · serraggio del collare",
    "screw_M3_motor": "vite M3 · motore",
    "screw_M2_board": "vite M2 · basetta",
    "screw_M25_board": "vite M2,5 · basetta",
    "screw_M25_cover": "vite M2,5 · coperchio del sensore",
    "screw_M2_module": "vite M2 · modulo AS5600",
    "grub_M3_clutch": "grano M3 · frizione",
    "bearing_F695ZZ": "cuscinetto F695ZZ",
    "magnet_AS5600": "magnete",
    "motor_NEMA14": "motore passo-passo",
    "preload_spring": "molla di precarico",
    "insert_M3_cover": "inserto M3 · coperchio della presa",
    "insert_M3_hatch": "inserto M3 · coperchio della botola",
    "insert_M4_preload": "inserto M4 · vite di precarico",
    "screw_M3_cover": "vite M3 · coperchio della presa, testa zigrinata",
    "screw_M3_hatch": "vite M3 · coperchio della botola",
    "grub_M4_preload": "grano M4 · precarico",
}

# The Italian of ORIENTATIONS above, not the Italian of bom_mechanics.PRINTED:
# those are the project's own notes on the model and talk to whoever keeps
# it; these talk to whoever prints.
ORIENTATIONS_IT = {
    "box_collar": "lo sportello dell'elettronica sul piatto: un piatto da "
                  "{piatto_sportello} × {piatto_sportello} mm, col pezzo girato di "
                  "{giro_sportello}°, alto {alto_sportello} mm; oppure la faccia del "
                  "connettore GX12 sul piatto: {piatto_testa} × {piatto_testa} mm, girato "
                  "di {giro_testa}°, alto {alto_testa} mm",
    "clutch_hub": "asse verticale, faccia del collarino sul piatto",
    "clutch_tyre": "co-stampato con il mozzo",
    "board_panel": "faccia esterna sul piatto",
    "grip_cover": "capovolto, faccia superiore sul piatto",
    "hatch_cover": "faccia esterna sul piatto: è quella in vista, a filo del fondo",
    "arm": "faccia superiore sul piatto: corpo e piastra del motore finiscono sullo stesso piano",
    "magnet_spacer": "quattro copie: è un pezzo che si perde",
    "front_gasket": "piatta sul letto, labbro in su (co-stampala con il collare "
                    "se hai una stampante multimateriale)",
    "rear_gasket": "piatta sul letto, labbro in su (co-stampala con il collare "
                   "se hai una stampante multimateriale)",
    "sensor_bracket": "la faccia piana di sotto, con il pattino, sul piatto",
    "sensor_cover": "faccia esterna sul piatto",
    "spring_cup": "dorso piatto sul piatto, scodella in su",
    "pivot_washer": "flangia sul piatto, manicotto in su",
}


def problems():
    """A part, a list item or a print orientation with no Italian: the
    Italian page would show the English one in the middle of Italian text."""
    out = []
    for name in sorted(set(PARTS) - set(NAMES_IT)):
        out.append("palette: the part %s has no Italian name (NAMES_IT)" % name)
    for name in sorted(set(ITEMS) - set(ITEMS_IT)):
        out.append("palette: the item %s has no Italian name (ITEMS_IT)" % name)
    for name in sorted(set(ORIENTATIONS) - set(ORIENTATIONS_IT)):
        out.append("palette: %s has no Italian print orientation" % name)
    # every fastener of the guide gets its family's colour: steel, or brass
    # (motor_NEMA14 is the motor's item in the list, not a body: the body is
    # motor_14HS10-0404S, which has its colour in PARTS)
    for name in sorted(set(ITEMS) - {"motor_NEMA14"}):
        if colour(name) == UNKNOWN:
            out.append("palette: %s falls into no family of FAMILIES and would be drawn "
                       "in the grey of an unknown part" % name)
    for prefix, _c, _e in FAMILIES:
        if prefix not in FAMILIES_IT:
            out.append("palette: the family %s has no Italian name" % prefix)
    for name in sorted((set(NAMES_IT) - set(PARTS)) | (set(ITEMS_IT) - set(ITEMS))
                       | (set(ORIENTATIONS_IT) - set(ORIENTATIONS))):
        out.append("palette: %s has an Italian name but no English one" % name)
    return out


def orientation(name, language="en"):
    text = (ORIENTATIONS_IT if language == "it" else ORIENTATIONS).get(name, "")
    if "{" in text:
        # the bed a part needs is measured on its STEP, not written here
        import bed
        text = text.format(**bed.measures())
    return text


def item_label(name, language="en"):
    """What a bill-of-materials item is called, in the language."""
    items = ITEMS_IT if language == "it" else ITEMS
    if name in items:
        return items[name]
    return name


def _entry(name, language="en"):
    """This body's entry. The bodies the assembly numbers - bearing_1,
    screw_M3_motor_3 - fall back on the entry without the number: two
    identical bearings must have the same colour, or they look like two
    different parts."""
    for key in (name, name.rsplit("_", 1)[0]):
        if key in PARTS:
            colour_, en = PARTS[key]
            return (colour_, NAMES_IT[key] if language == "it" else en)
    for prefix, colour_, label_ in FAMILIES:
        if name.startswith(prefix):
            return (colour_, FAMILIES_IT[prefix] if language == "it" else label_)
    return (UNKNOWN, name.replace("_", " "))


def colour(name):
    return _entry(name)[0]


def label(name, language="en"):
    """What this part is called in the guide, in the language of the page."""
    return _entry(name, language)[1]
