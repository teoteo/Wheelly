# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Writes the chapters of the assembly guide and generates their pictures.

The text of the steps is in `chapters.py`; the numbers inside the text are NOT
there: they are measured here on the model just built and slotted into the
placeholders. It is the same rule as the drawings - measure on the solid, do
not re-read the parameter - applied to prose: a guide that says "8.3 mm"
because someone wrote it by hand goes on saying it even when the part has
changed.
"""
import copy
import math
import os
import re
import shutil
import string
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, "src"))

import bom_mechanics
import bom_electronics
from purchased import axis_ends, purchased_parts
from parameters import D

from . import chapters, checks, interface, language as languages, scene, site, palette

ASSEMBLY = os.path.join(HERE, "out", "references", "full_assembly.step")
# The guide lives in the repository and not in out/: it is material to publish
# on GitHub, not a build product to look at and throw away.
DESTINATION = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "assembly")


def _purchased_entry(body):
    """The entry of purchased.py that corresponds to this body of the assembly.

    The assembly numbers identical bodies - screw_M3_motor_3 - because the
    names must be unique; here one goes back to the name of the entry."""
    # the motor in the assembly carries the maker's code, in the bill its
    # catalogue name: it is the only body that is not found by resemblance
    #
    # The `.replace("_", " ")` that was here went away with the translation:
    # the entries of purchased.py used to be called "screw_M3_motor", in words,
    # and now they are called `screw_M3_motor`, that is already like the body
    # minus the number. Left in, it looked for "screw M3 motor" and found
    # nothing any more - and the guide stopped on a None, not here but three
    # functions further on.
    name = ("motor_NEMA14" if body.startswith("motor_1")
            else body.rsplit("_", 1)[0])
    for v in purchased_parts():
        if v["name"] == name:
            return name, v
    return None, None


def _word(n):
    """Small numbers, in letters: "three inserts" reads better than "3"."""
    return ("no", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten")[n] if n <= 10 else str(n)


# The hex key of each size. It is a catalogue datum - ISO 4762 for socket-head
# screws, ISO 4026 for grub screws - and not a dimension of the model: it sits
# here once instead of being repeated in the steps, because whoever assembles
# must be able to put it on the table before starting, and a wrong key ruins
# the hexagon.
HEX_KEYS = {"M2": "1.5", "M2.5": "2", "M3": "2.5", "M4": "3"}


def _short_name(body, size=None):
    """The short name of a fastener - M3 x 8 - as the bill writes it.

    The length is NOT written here: it is the shank measured between the ends
    of the entry and rounded to the catalogue size by the same function that
    generates BOM.md. So the screw the step names and the screw the bill makes
    one buy are the same one, six months from now too.
    """
    _name, v = _purchased_entry(body)
    p0, p1, _u = axis_ends(v)
    sz = (size or v.get("size") or "M3").replace(",", ".")
    return "%s × %d" % (sz, bom_mechanics.stock_length(math.dist(p0, p1)))


# What is bought is NOT listed by hand. It is the assembly minus the printed
# parts, minus the things that are there but are not ordered: the starting
# manual wheel with its disc, the ESTIMATED envelopes of the electronics, the
# sensor cable. Rejected: a list written by hand in the step "And what you
# buy" - SIX items went missing from it (the preload grub and insert, the two
# screws and the two inserts of the board) even after the gap had been pointed
# out. A list copied by hand that has to mirror another one comes unstuck, and
# no amount of care holds it.
NOT_BOUGHT = {"filter_disc", "filter_wheel_body", "sensor_cable"}


def purchased_bodies(view):
    import bom_mechanics
    printed = {n for n, *_ in bom_mechanics.PRINTED}
    return sorted(c for c in view.bodies
                  if c not in printed
                  and c not in NOT_BOUGHT
                  and not c.startswith("electronics_"))


def measures(view):
    """The dimensions the steps quote, measured on the model.

    Each one is taken from the solid or from the parameter that governs it,
    never written here.
    """
    import cadquery as cq
    clutch = view.bodies["clutch_hub"].BoundingBox()
    # the pivot and its engagement in the arm's hub, measured on the solids:
    # how long the pivot is and for how many millimetres the arm sits on it
    # decide the assembly manoeuvre, and are not written in any parameter
    px, py = D["R_disc"], D["Off_pivot"]
    column = (cq.Workplane("XY").center(px, py)
              .circle(D["D_pivot_arm"]/2 + 0.5).extrude(80)
              .translate((0, 0, -40)).val())
    # the pin is the bushing on the washer, not the collar
    pivot = view.bodies["pivot_washer"].intersect(
        column.intersect(cq.Solid.makeBox(40, 40, 60, cq.Vector(px - 20, py - 20,
                                                               D["Z_bottom_arm"])))).BoundingBox()
    hub = view.bodies["arm"].intersect(
        cq.Workplane("XY").center(px, py).circle(12.0).extrude(80)
        .translate((0, 0, -40)).val()).BoundingBox()
    mot = view.bodies["motor_14HS10-0404S"].BoundingBox()
    _n, grub = _purchased_entry("grub_M3_clutch_1")
    # No placeholders for collar ears: box and collar are one piece and
    # there is nothing left to screw together.

    # The keys are the {placeholders} of the texts in chapters.py and in the
    # catalogues, which the fingerprints of the translations cover: they stay
    # as they were written.
    return {
        "inserto": "Ø%.1f × %.1f mm M3" % (D["D_out_insert_M3"], D["L_insert_M3"]),
        "inserto_M2": "Ø%.1f × %.1f" % (D["D_out_insert_M2"], D["L_insert_M2"]),
        "inserto_M25": "Ø%.1f × %.1f" % (D["D_out_insert_M25"], D["L_insert_M25"]),
        "inserto_M3": "Ø%.1f × %.1f" % (D["D_out_insert_M3"], D["L_insert_M3"]),
        "vite_coperchio": "M3 × %.0f" % D["L_screw_cover"],
        # The REFERENCE wheel and magnet, that is the ones the project was
        # built on. They serve the boxes «you may not need this chapter»:
        # whoever has the same wheel and the same magnet can skip them, and
        # must be able to recognise it from a number that comes from the model
        # and not from a sentence copied by hand.
        # The OUTER diameter of the wheel, not that of the rotating disc:
        # whoever has a wheel in hand recognises it by the rim, and nobody
        # measures the inner disc. The first time round here it was 2 * R_disc,
        # that is 145, and the box told a reader with the right wheel that it
        # was not theirs.
        "ruota_rif": "Ø%.0f" % D["D_body"],
        "disco_rif": "Ø%.0f" % (2 * D["R_disc"]),
        "magnete_rif": "Ø%.0f × %.0f" % (D["D_magnet"], D["Th_magnet"]),
        "d_spalle": D["D_shoulders_clutch"],
        "d_foro": "%.2f" % D["D_hole_clutch"],
        "d_albero": D["D_shaft"],
        "d_perno": D["D_pivot_arm"],
        "gioco": "%.2f" % D["Cl_clutch_shaft"],
        # where the clutch rests on the shaft: how far above the motor face it
        # sits, measured between the two solids and not deduced from the
        # parameters
        "sopra_flangia": clutch.zmin - (-D["Z_face_motor"]),
        # and how much the shaft is short of the ceiling of the hub: it is the
        # check whoever assembles can do by eye, looking into the hole
        "sotto_cielo": clutch.zmax - mot.zmax,
        # the grub's short name - M3 x 10 - from the clutch grub's own entry,
        # through the function that writes the BOM. Rejected:
        # taglia(L_thread_grub), the grub of the box's light labyrinth - it gave
        # 10 by coincidence, and would have drifted at the first change to
        # either of the two.
        "grano": _short_name("grub_M3_clutch_1", grub.get("size", "M3")),
        "chiave": "%.1f" % (D["D_grub"] / 2.0),
        "parete": "%.1f" % D["Wall_below_insert_grub"],
        "perno_lungo": pivot.zmax - pivot.zmin,
        "perno_impegno": min(pivot.zmax, hub.zmax) - max(pivot.zmin, hub.zmin),
        "sede_cusc": "%.1f" % D["D_seat_bearings_printed"],
        "cusc": "%d × %d × %d" % (D["D_shaft"], D["D_seat_bearings"], D["H_bearings"]/2),
        "sp_braccio": "%.0f" % D["Th_arm"],
        "franco_braccio": "%.1f" % D["Free_above_arm"],
        # the pivot screw as the BOM buys it, from its own entry. A
        # hand-written taglia(20.5) made chapter 5 say M3 x 25 while the model
        # and the reference build have the M3 x 20
        "vite_perno": _short_name("screw_M3_pivot_1"),
        "cava_larga": "%.1f" % D["L_groove_gasket"],
        "cava_fonda": "%.1f" % D["Dp_groove_gasket"],
        "guarn_larga": "%.1f" % D["L_gasket"],
        "labbro": "%.1f" % D["H_lip_gasket"],
        "shore": "%.0f" % D["Shore_gasket"],
        "d_pass": D["D_clear_shaft"],
        # the motor's cable is the only thing that sticks out of the square of
        # the body: measured on the maker's STEP, not read from a data sheet
        "lato_motore": mot.xlen,
        "sporge_cavo": mot.ylen - mot.xlen,
        # the motor screws from their entry (L_screw_motor): a hand-written
        # taglia(12.0) made chapter 7 ask for M3 x 12 while the BOM bought
        # M3 x 8. The key from the catalogue table, not a literal
        "vite_motore": _short_name("screw_M3_motor_1"),
        "chiave_motore": HEX_KEYS["M3"],

        # --- chapter 6: the board in its panel ------------------------------
        "perfboard": "%.0f × %.1f" % (D["L_board"], D["W_board"]),
        "fori_basetta": "%d × %d" % (D["N_holes_board_L"], D["N_holes_board_W"]),
        "vite_basetta_M2": _short_name("screw_M2_board_1"),
        "vite_basetta_M25": _short_name("screw_M25_board_1"),
        # the perfboard hole to open with the drill: the printed holes are 2
        # and the M2.5 does not go through. The bit is the one used on the
        # reference build, not the standard clearance, which would be 2.9
        "foro_basetta_M25": "%.1f" % D["D_hole_board_M25"],
        "fori_stampati_basetta": "%.0f" % D["D_holes_fixing_board"],
        "chiave_M25": HEX_KEYS["M2.5"],
        # the free height above the board: between its component face and the
        # ceiling of the bay. It is the dimension that says how tall a
        # capacitor can be, and it is measured between two solids
        "sopra_basetta": (view.bodies["box_collar"].BoundingBox().zmax
                          - view.bodies["electronics_perfboard"].BoundingBox().zmax),

        # --- chapter 7: the box and the spring ------------------------------
        "grano_precarico": _short_name("grub_M4_preload_1", "M4"),
        "inserto_M4": "Ø%.1f × %.1f" % (D["D_out_insert_M4"], D["L_insert_M4"]),
        # the key of the preload grub: half its diameter, as for all
        # socket-set grub screws
        "chiave_precarico": "%.1f" % (D["D_grub_spring"] / 2.0),
        "molla_libera": "%.1f" % D["L_spring_free"],
        "molla_filo": "%.1f" % D["D_wire_spring"],
        "molla_esterno": "%.1f" % D["D_spring_out"],
        "molla_k": "%.1f" % D["Rate_spring"],
        "n_stampati": len(bom_mechanics.PRINTED),
        # the collar's arc, from its two extents either side of the box axis
        # (the pivot side is overridden in parameters_locali): a hand-written
        # 162° in chapter 3 went stale when the collar changed from 110°
        "arco_collare": "%.0f" % (D["Ang_collar_pivot"] + D["Ang_collar_opposite"]),
        "molla_montata": "%.1f" % D["L_spring_fitted"],
        # how far the grub squashes the spring from where it starts to load:
        # free minus fitted length. Not Travel_preload, which is the cup's
        # +/- adjustment range
        "compressione_molla": "%.1f" % (D["L_spring_free"] - D["L_spring_fitted"]),
        "corsa_precarico": "%.1f" % D["Travel_preload"],
        "precarico_N": "%.0f" % D["Preload_N"],
        "forza_N": "%.1f" % D["Force_spring_N"],
        "gx12_foro": "%.1f" % D["D_hole_gx12"],
        # the grip for turning by hand: how far the tread sticks out
        "sporgenza_presa": "%.1f" % D["Proj_tread_grip"],

        # --- chapter 8: the wheel -------------------------------------------
        "distanziale": "Ø%.1f × %.1f" % (D["D_spacer_magnet"],
                                         D["Th_spacer_magnet"]),
        "magnete_mis": "Ø%.0f × %.0f" % (D["D_magnet"], D["Th_magnet"]),
        "colla": "%.1f" % D["Th_glue_stack_magnet"],
        # how far the magnet rises above the face of the disc: measured between
        # the two solids, because it is the sum of spacer, glue and magnet and
        # none of the three alone says where the face the sensor looks at stops
        "magnete_sopra": (view.bodies["magnet_AS5600_1"].BoundingBox().zmax
                          - view.bodies["filter_disc"].BoundingBox().zmax),
        "d_ruota": "%.0f" % view.bodies["filter_wheel_body"].BoundingBox().xlen,
        # how far the knurled rim of the disc sticks out of the plane of the
        # opening: it is the grip with which the manual wheel is turned with the
        # thumb, and it is the same window the clutch takes
        "sporgenza_bordo": "%.0f" % D["Proj_rim"],

        # --- chapter 9: the sensor and the closing --------------------------
        "vite_collare": _short_name("screw_M3_collar_1"),
        "vite_coperchio": _short_name("screw_M25_cover_1"),
        # the AS5600 module's own screws, as on the real assembly: M2
        # countersunk into the bracket's pilot holes
        "vite_modulo": _short_name("screw_M2_module_1"),
        "vite_pannellino": _short_name("screw_M3_panel_1"),
        # the grip cover's own screws. Its step used {vite_coperchio}, which is
        # the M2.5 of the sensor cover: the guide asked for the wrong screw
        "vite_presa": _short_name("screw_M3_cover_1"),
        "vite_botola": _short_name("screw_M3_hatch_1"),
        # The air gap is DECLARED, not measured, and here it says why: the
        # AS5600 module is not in the model - there is the magnet, there is the
        # bracket with its hole, but the board that carries the chip is not.
        # What the model does not contain, no measure can see.
        "traferro": "%.1f" % D["Gap_nominal"],
        # the test feet, from the same parameters solids_attrezzi builds them
        # from: gap = foot - spacer - magnet - glue - chip
        "piedini_n": int(D["N_foot_test"]),
        "piedini_da": "%.1f" % D["H_min_foot_test"],
        "piedini_a": "%.1f" % (D["H_min_foot_test"] + (D["N_foot_test"] - 1)*D["Pitch_foot_test"]),
        "traferro_da": "%.2f" % (D["H_min_foot_test"] - D["Th_spacer_magnet"] - D["Th_magnet"]
                                 - D["Th_glue_stack_magnet"] - D["H_body_chip"]),
        "traferro_a": "%.2f" % (D["H_min_foot_test"] + (D["N_foot_test"] - 1)*D["Pitch_foot_test"]
                                - D["Th_spacer_magnet"] - D["Th_magnet"]
                                - D["Th_glue_stack_magnet"] - D["H_body_chip"]),
        # the cable's own diameter, measured: D_cable_sensor is the 6.0 the
        # channel is sized for, not the cable's
        "sensor_cable": "Ø%.1f" % D["D_cable_sensor_measured"],
        "raggio_cavo": "%.0f" % D["R_curvature_min_cable"],
    }


class _Comma(string.Formatter):
    """Fills the placeholders as str.format does, then gives each filled-in
    number the decimal comma. Only the FIELD is touched, never the text around
    it: the translator's own "M2.5" or "U.FL" stay as written."""
    def format_field(self, value, spec):
        return interface.number(super().format_field(value, spec), "it")


def _fill(text, m, lang="en"):
    """A text with its {placeholders} filled from the model's measures.

    In Italian the numbers take the decimal comma - Italian prose writes
    "5,0 mm" - EXCEPT inside `code`: a file name, a parameter or a command is
    copied by the reader as it is, and there a comma would be a different
    thing. So the text is cut at the backticks and only the prose pieces get
    the comma."""
    if lang != "it":
        return text.format(**m)
    pieces = text.split("`")
    return "`".join(p.format(**m) if i % 2 else _Comma().format(p, **m)
                    for i, p in enumerate(pieces))


def _size_note(name, v, lang):
    """bom_mechanics.describe in the language of the page. Its Italian is the
    project's own list and writes "Ø5.0 x 3.0"; in the Italian guide the same
    numbers read "Ø5,0 × 3,0", like the rest of the Italian prose."""
    q = bom_mechanics.describe(name, v, lang)
    if lang == "it":
        q = re.sub(r"(?<=\d) x (?=\d)", " × ", interface.number(q, "it"))
    return q


def rotations(v):
    """The bodies a view turns, {name: (centre, axis, degrees)}. Read by the
    pictures and by check_assembly_paths, which must move the same turned
    bodies the picture shows.

    "grub_to_centre": the clutch turned on the shaft so that its grub screw
    faces the middle of the collar, where the hex key comes in from (as
    modelled, the grub points at a wall). The angle is not
    written: it is the one between the grub's axis and the direction from the
    shaft to the wheel axis."""
    turn = {}
    if v.get("turn") == "grub_to_centre":
        import math
        from purchased import axis_ends
        _n, grub = _purchased_entry("grub_M3_clutch_1")
        p0, p1, _u = axis_ends(grub)
        cx, cy = D["Cd_motor"], 0.0
        a_grub = math.atan2(((p0[1] + p1[1])/2) - cy, ((p0[0] + p1[0])/2) - cx)
        a_centre = math.atan2(0.0 - cy, 0.0 - cx)
        degrees = math.degrees(a_centre - a_grub)
        for body in ("clutch_hub", "clutch_tyre", "insert_M3_grub_1", "grub_M3_clutch_1"):
            turn[body] = ((cx, cy, 0.0), (0.0, 0.0, 1.0), degrees)
    return turn


def _bom(mounted_bodies, quantities, lang="en", references=()):
    """The chapter's bill: only the parts that arrive in its steps.

    It is grouped by ENTRY of the bill, not by body: in the assembly the five
    inserts of the ears are five numbered bodies, but whoever buys and whoever
    assembles sees only one, times five.
    """
    printed = {n: (mat, orient) for n, mat, _d, _q, orient in bom_mechanics.PRINTED}
    electronics = bom_electronics.bodies()
    rows, seen = [], {}
    for body in mounted_bodies:
        n = quantities[body]
        if body in electronics:
            # an electronics body is an estimated envelope standing for one or
            # more items: the list shows the ITEMS, with their values - not
            # "1 discrete components" for eight parts
            for q, label, note in bom_electronics.rows(body, lang):
                if label not in seen:
                    seen[label] = len(rows)
                    rows.append([q, label, note])
            continue
        if body in printed:
            group = body
            label = palette.label(body, lang)
            note = interface.t("printed", lang) % printed[body][0]
        else:
            name, v = _purchased_entry(body)
            # the spring is not an entry of purchased.py (solids_assieme draws
            # it), so the chapter's row had no note while the first list gave
            # its measures: take the same group the first list and BOM.md read
            if v is None and body in bom_mechanics.purchased_rows():
                name, v = body, bom_mechanics.purchased_rows()[body]["entry"]
            if v is None:
                group, label, note = body, palette.label(body, lang), ""
            else:
                group = name
                label = palette.item_label(name, lang)
                note = _size_note(name, v, lang)
        if group in seen:
            rows[seen[group]][0] += n
            continue
        seen[group] = len(rows)
        rows.append([n, label, note])
    # ELECTRONICS WITH NO BODY IN THE ASSEMBLY: the AS5600 module U3 and its
    # capacitor C3 are not modelled, so no step can "mount" them and no
    # chapter would list them, though chapters 11 and 12 wire
    # and mount the sensor. A chapter names them by reference ("electronics")
    # and the rows come from bom_electronics, the same source as the bodies'.
    every = bom_electronics.rows(lang=lang)
    for ref in references:
        found = [r for it, r in zip(bom_electronics.ITEMS, every) if it[0] == ref]
        if not found:
            raise SystemExit("guide: unknown electronics reference %r" % ref)
        for q, label, note in found:
            if label not in seen:
                seen[label] = len(rows)
                rows.append([q, label, note])
    return [tuple(r) for r in rows]


def _picture(view, step, mounted_before, folder, file_name, m):
    """The render of a step.

    Into the scene goes **only what the step names**: the parts that arrive
    now, those the step keeps around itself (`context`) and those that serve
    only to find one's bearings (`backdrop`, transparent). All the rest of the
    machine stays out even if it was already mounted in the chapters before:
    the first time round the scene contained everything mounted, and in the
    step that drives the panel inserts the panel was behind the collar and the
    box - the picture showed two parts that had nothing to do with it. The
    framing check noticed, counting the pixels.
    """
    v = step["view"]
    explode = v.get("explode", {})
    cut = set(v.get("cut", []))
    turn = rotations(v)
    pieces = []
    for body in (list(step["mounts"]) + list(step.get("context", []))
                 + list(step.get("backdrop", []))):
        pieces.append({"name": body,
                       "colour": palette.colour(body),
                       # the colour is always its own: what changes between a
                       # part that arrives now and one that is there to show
                       # where one is is only the opacity, or whoever assembles
                       # no longer recognises the parts from one chapter to the
                       # next
                       "opacity": 0.30 if body in step.get("backdrop", []) else 1.0,
                       "offset": explode.get(body),
                       "turn": turn.get(body),
                       "cut": body in cut})
    plane = None
    if v.get("plane") == "grub":
        # the section plane goes through the axis of the grub: it is not a
        # chosen dimension, it is where the part the section must show is
        _n, grub = _purchased_entry("grub_M3_clutch_1")
        from purchased import axis_ends
        plane = (axis_ends(grub)[0], (0, 0, -1))
    elif isinstance(v.get("plane"), (tuple, list)):
        # a plane given as (point, normal): for the parts that go in from
        # INSIDE the box (strategy C), which no camera outside can see
        plane = (tuple(v["plane"][0]), tuple(v["plane"][1]))
    # The arrow starts from the exploded part and points to its place: tail
    # just outside the part, tip towards the seat. The vector is the movement
    # the part has to make, not just any direction.
    # The arrow is born at the centre of the part, and for a big part this
    # means BEING BORN INSIDE: the box and the wheel body swallowed it whole,
    # and the direction of assembly - the only thing an exploded view does not
    # say by itself - could not be seen. The third element, if there is one,
    # moves the anchor out of the part: above the box, beside the board.
    arrows = []
    for body, vector, *rest in v.get("arrows", []):
        b = view.bodies[body].BoundingBox()
        if body in turn:
            (rx, ry, _rz), _axis, _g = turn[body]
            import math as _m
            _c, _s = _m.cos(_m.radians(_g)), _m.sin(_m.radians(_g))
            _x, _y = b.center.x - rx, b.center.y - ry
            b = type("B", (), {})()
            b.center = type("C", (), {"x": rx + _x*_c - _y*_s, "y": ry + _x*_s + _y*_c,
                                      "z": view.bodies[body].BoundingBox().center.z})()
        s = explode.get(body, (0, 0, 0))
        outward = rest[0] if rest else (0, 0, 0)
        c = (b.center.x + s[0] + outward[0], b.center.y + s[1] + outward[1],
             b.center.z + s[2] + outward[2])
        tail = tuple(c[i] + vector[i]*0.35 for i in range(3))
        tip = tuple(c[i] + vector[i]*1.30 for i in range(3))
        arrows.append((tip, tuple(tip[i] - tail[i] for i in range(3))))
    common = dict(direction=v.get("direction", (1.0, -1.0, 0.6)),
                  up=v.get("up", (0, 0, 1)), zoom=v.get("zoom", 1.0),
                  plane=plane, arrows=arrows, frame=v.get("frame"))
    png = view.render(pieces, os.path.join(folder, file_name), **common)
    # right after, the same scene in flat shades: it is the check that the part
    # the step talks about really shows. It is done here and not apart because
    # only here is one sure it is the same scene.
    return png, view.render(pieces, None, count=True, **common)


def _tool_marks(tools, cap):
    """Every screw a chapter mounts has its tool in the chapter's list:
    countersunk heads take the PH0, socket heads the hex key of their size.
    The head comes from the screw's item in purchased.py, the key from
    HEX_KEYS: a hand-written list once closed the countersunk hatch screws
    with a 2 mm hex key."""
    text = " ".join(tools)
    for step in cap["steps"]:
        for body in step.get("mounts", []):
            # grub screws have their own key (half their diameter), said
            # where they are driven
            if not body.startswith("screw_"):
                continue
            _n, v = _purchased_entry(body)
            if v is None:
                raise SystemExit("guide: chapter %d mounts %s, which purchased.py does not "
                                 "have" % (cap["num"], body))
            # a screw that does not say its head is socket-head, as in
            # solids_assieme.sagoma()
            if v.get("head_type", "socket") == "countersunk":
                if "PH0" not in text:
                    raise SystemExit("guide: chapter %d mounts the countersunk %s but lists no "
                                     "PH0 screwdriver" % (cap["num"], body))
            else:
                hex_key = "%s mm hex key" % HEX_KEYS[v.get("size", "M3")]
                if hex_key not in text and ("hex keys:" not in text):
                    raise SystemExit("guide: chapter %d mounts the socket-head %s but lists no "
                                     "%s" % (cap["num"], body, hex_key))
    return tools


def _tools(cap):
    """A chapter always says what it needs: with none written, its page
    reads "Tools: .". A chapter done by hand says so, as
    the collar's does ("your hands - nothing else")."""
    if not cap["tools"]:
        raise SystemExit("guide: chapter %d (%s) lists no tools" % (cap["num"], cap["id"]))
    return cap["tools"]


def _prepare(view, m, cap, destination):
    """The chapter ready to lay out: texts already filled with the numbers,
    pictures already made, bill already counted.

    It sits in the middle on purpose. Below it there are two layouts - the
    site and the Markdown of the repository - and if each redid the counts on
    its own the two versions of the same chapter would start to diverge
    without anyone noticing: they are both generated, so nobody ever compares
    them.
    """
    quantities, order = {}, []
    for step in cap["steps"]:
        for body in step["mounts"]:
            if body not in quantities:
                quantities[body] = 0
                order.append(body)
            quantities[body] += 1

    steps, mounted = [], []
    for i, step in enumerate(cap["steps"], 1):
        # A STEP MAY HAVE NO PICTURE. Not every step mounts something:
        # installing a program, running a bench, reading a number on a web
        # page have no render that tells them, and putting the whole machine
        # beside them would be a picture that says nothing - worse, it would
        # make one believe the step is about that part. A step without a
        # `view` comes out full width, text only.
        # The step that shows the bought parts does not list them: it asks for
        # the list.
        if step.get("context") == "PURCHASED":
            step = dict(step, context=purchased_bodies(view))
        if step.get("context") == "PRINTED":
            step = dict(step, context=[n for n, *_ in bom_mechanics.PRINTED
                                       if n in view.bodies])

        # A SCREENSHOT IS NOT A RENDER. Some steps can be explained only with a
        # figure the model cannot draw: the parameter editor, the air gap page
        # with the numbers on it. That figure is a SOURCE of the project, it
        # sits in src/guide/screenshots/ and is copied with the same name a
        # render would have had - so the end-of-run cleanup recognises it as
        # its own and does not delete it.
        if "screenshot" in step:
            png_name = "%02d-%02d-%s.png" % (cap["num"], i, cap["id"])
            source = os.path.join(os.path.dirname(__file__), "screenshots",
                                  step["screenshot"])
            if not os.path.exists(source):
                raise SystemExit("screenshot missing: %s" % source)
            shutil.copyfile(source, os.path.join(destination, "img", png_name))
            from PIL import Image
            with Image.open(os.path.join(destination, "img", png_name)) as im:
                img_w, img_h = im.size
            shot_points = []
            for text in step["points"]:
                careful = text.startswith("!")
                shot_points.append((text.lstrip("!").strip().format(**m), careful))
            steps.append({"n": i, "title": step["title"], "png": png_name,
                          "mounts": [], "cited": [], "counts": {},
                          "img_w": img_w, "img_h": img_h,
                          "shown_w": int(min(760, img_w)),
                          "points": shot_points})
            continue

        if "view" not in step:
            text_points = []
            for text in step["points"]:
                careful = text.startswith("!")
                text_points.append((text.lstrip("!").strip().format(**m), careful))
            steps.append({"n": i, "title": step["title"], "png": None,
                          "mounts": [], "cited": [], "counts": {},
                          "img_w": 0, "img_h": 0, "shown_w": 0,
                          "points": text_points})
            continue

        png_name = "%02d-%02d-%s.png" % (cap["num"], i, cap["id"])
        png, counts = _picture(view, step, mounted,
                               os.path.join(destination, "img"), png_name, m)
        # The width of the picture in the page is worked out from its shape,
        # and not left to the browser: a vertical exploded view made to fill
        # the column becomes two screens tall, and the text of the step ends
        # up next to empty space.
        from PIL import Image
        with Image.open(png) as im:
            img_w, img_h = im.size
        mounted = mounted + [c for c in step["mounts"] if c not in mounted]
        points = []
        for text in step["points"]:
            # a point that starts with ! is a warning: it looks different,
            # because in the middle of four identical lines a warning is not
            # read
            careful = text.startswith("!")
            points.append((text.lstrip("!").strip().format(**m), careful))
        # the bodies the step brings in without mounting them: context, parts
        # moved, cut, framed, pointed at by an arrow. The sequence check wants
        # them already mounted in an earlier step.
        v = step["view"]
        cited = (list(step.get("context", [])) + list(step.get("backdrop", []))
                 + list(v.get("explode", {}).keys())
                 + list(v.get("cut", [])) + list(v.get("frame") or [])
                 + [f[0] for f in v.get("arrows", [])])
        steps.append({"n": i, "title": step["title"], "png": png_name,
                      "mounts": list(step["mounts"]), "cited": cited,
                      "counts": counts,
                      "img_w": img_w, "img_h": img_h,
                      "shown_w": int(min(520, max(300, 420.0 * img_w / img_h))),
                      "points": points})

    # the drawings a step asks for, by point (guide/illustrations.py): the
    # steps line up one to one with the chapter's
    for p_out, p_cap in zip(steps, cap["steps"]):
        p_out["illustrations"] = dict(p_cap.get("illustrations", {}))

    bom = (_full_bom() if cap.get("full_bom")
           else _bom(order, quantities, references=cap.get("electronics", ())))
    return {"num": cap["num"], "id": cap["id"], "title": cap["title"],
            "language": "en", "_order": order, "_quantities": quantities,
            # the introduction goes through the placeholders too, and it too
            # ends up under the check: the Ø of the wheel had stayed in braces
            # there and was published like that, because the filling reached
            # only the points of the step
            "intro": cap["intro"].format(**m),
            # The box "you may not need this chapter". It goes through the
            # placeholders like everything else: it contains the Ø of the
            # reference wheel and the magnet, which are measures of the model
            # and not numbers to copy.
            "skip": cap.get("skip", "").format(**m),
            # the tools go through the placeholders too: the size of a key
            # written by hand in the list of tools comes unstuck from the screw
            # it has to turn, and it is the list whoever assembles reads first
            "tools": _tool_marks([a.format(**m) for a in _tools(cap)], cap),
            "bom": bom, "steps": steps}


def _translate(prep, cap, m, lang):
    """The prepared chapter in another language: the same pictures, the same
    counts, the texts from the language's catalogue (guide/language.py) filled
    with the same measures, and the parts list asked again in that language.

    Built FROM the English one and not by preparing the chapter again: the
    pictures are rendered once, and the two pages cannot end up showing two
    different counts of the same screw."""
    if lang == "en":
        return prep
    t = languages.translated(cap, lang)
    out = copy.deepcopy(prep)
    out["language"] = lang
    out["title"] = t["title"]
    out["intro"] = _fill(t["intro"], m, lang)
    out["skip"] = _fill(t.get("skip", ""), m, lang)
    out["tools"] = [_fill(a, m, lang) for a in t["tools"]]
    # the steps line up one to one: _prepare makes one per step of the chapter
    for p_out, p_t in zip(out["steps"], t["steps"]):
        p_out["title"] = p_t["title"]
        p_out["points"] = [(_fill(x.lstrip("!").strip(), m, lang), x.startswith("!"))
                           for x in p_t["points"]]
    out["bom"] = (_full_bom(lang) if cap.get("full_bom")
                  else _bom(prep["_order"], prep["_quantities"], lang,
                            cap.get("electronics", ())))
    return out


# THE ELECTRONICS AND THE CABLE in the first list: they are in the assembly
# as envelopes, and without this they would be missing from the list of what
# to get - the electronics has its own bill in pcb/BOM.md, written by hand, and
# the first list now points there for each of them. The AS5600 module is not
# in the model at all (see the air gap chapter): it is listed here by hand,
# and said to be.


def _full_bom(lang="en"):
    """Everything needed to build the machine, from the project's bill: the
    printed parts with their print orientation, and the bought ones with the
    sentence that already describes each. Nothing is rewritten - it is the
    same function that generates BOM.md, called in English."""
    # in three sections, each opened by a row with no quantity: printed,
    # mechanics, electronics - one list of 45 rows does not say which are to
    # print and which to buy
    T = interface.t
    rows = [(None, T("sec_printed", lang), "")]
    for name, mat, dens, q, _orient in bom_mechanics.PRINTED:
        m = bom_mechanics.mass(name, dens)
        note = T("printed", lang) % mat
        if m:
            note += interface.number(", %.1f g" % (m * q), lang)
        g = palette.orientation(name, lang)
        rows.append((q, palette.label(name, lang), note + ((" — " + g) if g else "")))
    rows.append((None, T("sec_mechanics", lang), ""))
    for name, entry_group in sorted(bom_mechanics.purchased_rows().items()):
        rows.append((entry_group["n"], palette.item_label(name, lang),
                     _size_note(name, entry_group["entry"], lang)))
    # the electronics, item by item, from the one list the global BOM reads too
    rows.append((None, T("sec_electronics", lang), ""))
    rows += bom_electronics.rows(lang=lang)
    return rows


# bodies of the assembly that are not bought and not printed, and why
OUT_OF_BOM = {"filter_disc": "your own filter wheel",
              "filter_wheel_body": "your own filter wheel"}


def bom_gaps(bodies):
    """What the first list does not cover: every body of the assembly must be
    a printed part, a bought row, an electronics row, or out of the list for
    a written reason. The spring once went missing and nothing said so,
    because the list was the sum of two sources and a body that belonged to
    neither simply was not there. Also: no row may keep an
    internal name as its label."""
    printed = {n for n, *_ in bom_mechanics.PRINTED}
    purchased_parts = set(bom_mechanics.purchased_rows())
    electronics = set(bom_electronics.bodies())
    missing = []
    # the electronics list may only name bodies that exist
    for b in sorted(electronics - set(bodies)):
        missing.append("the electronics bill names a body that does not exist: %s" % b)
    # and its references are those of pcb/BOM.md, where the reasons are
    import re as _re
    _pcb = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))), "pcb", "BOM.md")
    # only the tables whose first column is "Ref.": the inserts table has M3
    # and M4 in its first column too, and they are threads, not references
    # (it was "Rif." before pcb/BOM.md was translated: the translation
    # emptied the set, and this check is what said so)
    pcb_refs, in_refs = set(), False
    for line in open(_pcb, encoding="utf-8"):
        if not line.startswith("|"):
            in_refs = False
            continue
        if line.replace(" ", "").startswith("|Ref.|"):
            in_refs = True
            continue
        m_ref = _re.match(r"^\|\s*([A-Z]\d+)\s*\|", line)
        if in_refs and m_ref:
            pcb_refs.add(m_ref.group(1))
    for r in sorted(pcb_refs - bom_electronics.refs() - set(bom_electronics.NOT_BOUGHT_HERE)):
        missing.append("pcb/BOM.md has %s, the electronics bill does not" % r)
    for r in sorted(bom_electronics.refs() - pcb_refs):
        missing.append("the electronics bill has %s, pcb/BOM.md does not" % r)
    for c in sorted(bodies):
        entry, _v = _purchased_entry(c) if c not in printed else (None, None)
        if not (c in printed or c in purchased_parts or entry in purchased_parts
                or c in electronics or c in OUT_OF_BOM):
            missing.append("the first list is missing %s" % c)
    for l in interface.LANGUAGES:
        for q, label, _note in _full_bom(l):
            if q is not None and "_" in label:
                missing.append("in the first list (%s) an entry is still called %s"
                               % (l, label))
    return missing


def missing_translations():
    """Every word the Italian pages need, before a single picture is drawn:
    the fixed texts, the chapters and their plan, the part names and print
    orientations, the electronics list. A hole found after ten minutes of
    rendering is ten minutes lost; found here it costs a second."""
    return (interface.problems() + languages.problems("it") + palette.problems()
            + bom_electronics.problems_it())


def generate(destination=DESTINATION):
    missing = missing_translations()
    if missing:
        for x in missing:
            print("   FAULT: %s" % x)
        raise SystemExit("the guide is not all translated: %d problems" % len(missing))
    view = scene.View(scene.load(ASSEMBLY))
    m = measures(view)
    # THE CROSS-REFERENCES BETWEEN CHAPTERS go through the same placeholders as
    # the measures, and are not written by hand. «in chapter 5» written in the
    # prose survives until someone inserts a chapter before the fifth: the day
    # that happens, five sentences send the reader to the wrong place and no
    # check notices, because a number inside a sentence is prose. One writes
    # {cap_heat_set_inserts} and the guide puts the number in.
    m.update({"cap_" + c["id"].replace("-", "_"): c["num"]
              for c in chapters.CHAPTERS})
    os.makedirs(os.path.join(destination, "img"), exist_ok=True)
    # the names are checked before drawing: a wrong name would stop the
    # render at the first step that names it, and the others would stay hidden
    wrong = checks.names(chapters.CHAPTERS, set(view.bodies))
    if wrong:
        for x in wrong:
            print("   FAULT: %s" % x)
        raise SystemExit("the guide names bodies that do not exist: %d" % len(wrong))

    prepared = [_prepare(view, m, cap, destination) for cap in chapters.CHAPTERS]
    # the same chapters in Italian: same pictures, texts
    # from the catalogues. English stays the default and lives where it was.
    italian = [_translate(p, cap, m, "it") for p, cap in zip(prepared, chapters.CHAPTERS)]

    problems, notes = checks.all_checks(prepared, set(view.bodies))
    problems += ["(it) " + x for x in checks.placeholders(italian)]
    problems += bom_gaps(set(view.bodies))
    for n in notes:
        print("   note: %s" % n)
    if problems:
        for x in problems:
            print("   FAULT: %s" % x)
        raise SystemExit("the guide is not consistent: %d problems" % len(problems))

    for lang, chapters_l in (("en", prepared), ("it", italian)):
        folder = _folder(destination, lang)
        os.makedirs(folder, exist_ok=True)
        for cap in chapters_l:
            _markdown(cap, folder, lang)
        site.write_pages(chapters_l, destination, lang)
        _index(folder, lang)
    _sweep(destination, prepared)
    # the two languages, checked on the files just written: what the reader
    # gets is the pages, and only the pages can say they are right
    problems = checks.bilingual(destination)
    if problems:
        for x in problems:
            print("   FAULT: %s" % x)
        raise SystemExit("the two languages of the guide do not match: %d problems" % len(problems))
    for cap in prepared:
        print("chapter %d, %d steps" % (cap["num"], len(cap["steps"])))


def _folder(destination, lang):
    """English in docs/assembly/, every other language in a folder of its own
    with the same file names - as trendupgraphic.com does with / and /it/."""
    return destination if lang == "en" else os.path.join(destination, lang)


def _sweep(destination, prepared):
    """Away with the files of earlier runs that no longer belong.

    It is needed because the file names carry the chapter number, and the
    numbers change: when the clutch moved from 3 to 5, a chapter and three
    pictures of an order that no longer exists stayed in the folder. In the
    published folder there must be nothing the generator has not just written,
    or sooner or later someone follows an old page."""
    good = {"README.md", "guide.css", "index.html"}
    good |= {os.path.join("brand", f) for f in site.BRAND}
    for cap in prepared:
        good.add("%02d-%s.md" % (cap["num"], cap["id"]))
        good.add("%02d-%s.html" % (cap["num"], cap["id"]))
        for step in cap["steps"]:
            if step["png"]:
                good.add(os.path.join("img", step["png"]))
    # the pages of the other languages have the same names, in their folder;
    # the pictures and the style they share stay one copy, in the English one
    for l in interface.LANGUAGES[1:]:
        good |= {os.path.join(l, f) for f in list(good)
                 if f.endswith((".md", ".html"))}
    removed = 0
    for folder, _sub, files in os.walk(destination):
        for f in files:
            rel = os.path.relpath(os.path.join(folder, f), destination)
            if rel in good or not rel.endswith((".md", ".html", ".png", ".css")):
                continue
            os.remove(os.path.join(destination, rel))
            removed += 1
    if removed:
        print("   removed %d files of an earlier run" % removed)


def _other_language_md(name, lang):
    """The link, at the top of a Markdown file, to the same file in the other
    language (English <-> Italian)."""
    other = "it/" + name if lang == "en" else "../" + name
    return "*[%s](%s)*" % (interface.t("md_other_language", lang), other)


def _markdown(cap, folder, lang="en"):
    """The Markdown version of the chapter: it is read inside GitHub, in diffs
    and in pull requests. The site is what is published; this serves whoever
    looks at the repository, and to see in one diff line what changed in a
    step when the model moves."""
    T = lambda k: interface.t(k, lang)
    img = "img/" if lang == "en" else "../img/"
    name = "%02d-%s.md" % (cap["num"], cap["id"])
    r = ["<!--", "SPDX-FileCopyrightText: 2026 Matteo Beretta",
         "SPDX-License-Identifier: CC-BY-4.0", "-->", "",
         _other_language_md(name, lang), "",
         "# " + T("md_chapter") % (cap["num"], cap["title"]), "",
         "*" + T("md_published") % ("%02d-%s.html" % (cap["num"], cap["id"])) + "*", "",
         site._bold(cap["intro"]), ""]
    if cap.get("skip"):
        r += ["> **%s** " % T("md_skip") + site._unmarked(cap["skip"]), ""]
    r += ["## " + T("md_what_you_need"), "",
          "| %s | %s | |" % (T("md_qty"), T("md_part")), "|---:|---|---|"]
    for n, label, note in cap["bom"]:
        if n is None:                       # a section of the list
            r.append("| | **%s** | |" % label)
            continue
        r.append("| %d | %s | %s |" % (n, label, note))
    r += ["", "**%s** " % T("md_tools") + ", ".join(site._bold(a) for a in cap["tools"])
          + ".", ""]
    for step in cap["steps"]:
        # the bold is converted here too, with the same function as the site:
        # inside an HTML block GitHub no longer looks at the Markdown, and the
        # two asterisks stayed printed on the page
        points = "".join("<li>%s%s%s</li>" % (("<b>%s</b> " % T("careful")) if att else "",
                                              site._bold(t),
                                              site.illustration(step, k, img, lang, md=True))
                         for k, (t, att) in enumerate(step["points"], 1))
        title = T("md_step") % (step["n"], step["title"])
        if step["png"]:
            r += ['<table><tr>',
                  '<td width="55%%"><img src="%s%s" alt="%s" width="%d"></td>'
                  % (img, step["png"], step["title"], step["shown_w"]),
                  '<td valign="top"><h3>%s</h3><ul>%s</ul></td>' % (title, points),
                  '</tr></table>', '']
        else:
            r += ['<h3>%s</h3><ul>%s</ul>' % (title, points), '']
    with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
        f.write("\n".join(r))


def _index(folder, lang="en"):
    """The index of the guide, generated from the plan of the chapters: those
    that exist are links, those that are missing show that they are missing."""
    T = lambda k: interface.t(k, lang)
    written = {c["num"]: c["id"] for c in chapters.CHAPTERS}
    r = ["<!--", "SPDX-FileCopyrightText: 2026 Matteo Beretta",
         "SPDX-License-Identifier: CC-BY-4.0", "-->", "",
         _other_language_md("README.md", lang), "",
         "# " + T("index_title"), "",
         T("md_index_intro"), "",
         T("md_site"), "",
         T("md_pictures"), "",
         "| | %s | |" % T("md_chapter_column"), "|---:|---|---|"]
    for num, title, note in languages.plan(lang):
        if num in written:
            r.append("| %d | [%s](%02d-%s.md) | [%s](%02d-%s.html)%s |"
                     % (num, title, num, written[num], T("md_as_page"),
                        num, written[num], (" · " + note) if note else ""))
        else:
            r.append("| %d | %s | *%s* |" % (num, title, T("not_written_yet")))
    r.append("")
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(r))
