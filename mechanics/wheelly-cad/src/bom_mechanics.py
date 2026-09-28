# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The bill of materials of the mechanics, GENERATED from the model.

The electronics one (pcb/BOM.md) is written by hand, and that is fine: it
describes components the model does not contain. This one is not. Here every
row descends from something that already exists - the mass from the solid, the
quantity from counting the parts in the assembly, the length of a screw from
its shank - and a list copied by hand comes loose at the first part that
changes, without saying so.

Screw lengths are not chosen: what is needed under the head is measured, and
rounded up to the first catalogue length. So the list says what to buy instead
of describing what is there.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cadquery as cq
from parameters import D
from purchased import purchased_parts, axis_ends

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out") + os.sep
BOM = os.path.join(HERE, "BOM.md")

# densities: ASA is about 1.07, TPU 95A about 1.21
# ONE TPU for every soft part, any grade in this range: tried only on 87A -
# the tyre, and the 700 g that drove the disc - and worked out on paper up
# to 95A, the hardness the gaskets' squash is calculated for (Shore_gasket).
# Rejected: 87A for the tyre and 95A for the gaskets, two reels for 3 g of
# TPU.
TPU_GAMMA = "TPU 87A-95A"

PRINTED = [
    # ONE SINGLE PART: box and collar as two parts screwed together with 5
    # screws and 5 inserts were rejected - that joint cost three defects
    # found with the parts in hand. The bed size needed is not written here:
    # bed.py measures it on the STEP, for the two orientations (GIACITURE,
    # palette).
    ("box_collar", "ASA", 1.07, 1,
     "sportello dell'elettronica, o la faccia del GX12, sul piatto: il piatto lo misura bed.py"),
    ("arm", "ASA", 1.07, 1, "faccia superiore sul piatto: corpo e piastra del motore finiscono tutti e due a Z_top_arm, e la linguetta della molla cresce verso l'alto"),
    ("clutch_hub", "ASA", 1.07, 1, "asse verticale, faccia del collare sul piatto"),
    # 87A on the reference build: the common grade, and with it 700 g on
    # the arm were enough to drive the disc, measured with a kitchen
    # scale. Any grade in TPU_GAMMA will do. The density is the 95A's,
    # not measured
    ("clutch_tyre", TPU_GAMMA, 1.21, 1, "costampato col mozzo"),
    ("sensor_bracket", "ASA", 1.07, 1, ""),
    ("sensor_cover", "ASA", 1.07, 1, ""),
    ("board_panel", "ASA", 1.07, 1, "faccia esterna sul piatto"),
    ("spring_cup", "ASA", 1.07, 1, ""),
    ("grip_cover", "ASA", 1.07, 1, "capovolto, faccia superiore sul piatto: porta la piastra sopra il motore, e le teste delle viti zigrinate appoggiano sulle linguette; il generatore e check_grip lo stampano così"),
    ("hatch_cover", "ASA", 1.07, 1, "faccia esterna sul piatto: e' quella in vista, a filo del fondo; le orecchie salgono dritte e gli svasi si aprono sul piatto"),
    ("pivot_washer", "ASA", 1.07, 1, ""),
    ("magnet_spacer", "ASA", 1.07, 4, "quattro copie: e' un pezzo che si perde"),
    # They are printed separately and pushed into their groove; whoever has a
    # multi-material printer finds them already in place in
    # box_collar_coprinted.step. The normal route is the one that does not
    # need an IDEX.
    ("front_gasket", TPU_GAMMA, 1.21, 1,
     "piatta sul letto, labbro in su (costampata col pezzo, se hai il multimateriale)"),
    ("rear_gasket", TPU_GAMMA, 1.21, 1,
     "piatta sul letto, labbro in su (costampata col pezzo, se hai il multimateriale)"),
]

# The lengths that exist on the market. A screw is bought this long, not as
# long as the drawing would like.
STOCK_LENGTHS = (4, 5, 6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40)


def stock_length(mm):
    for t in STOCK_LENGTHS:
        if t >= mm - 0.05:
            return t
    return None


def mass(name, density):
    f = OUT + name + ".step"
    if not os.path.exists(f):
        return None
    return cq.importers.importStep(f).val().Volume()/1000.0 * density


def purchased_rows():
    """Groups the entries by name, counting how many there are and what
    dimensions they have.

    The SPRING too, which is not an entry of purchased.py - solids_assembly
    draws it with its helix - and for that reason once went missing from the
    list and from the guide's first list. The guide's check now demands that
    every body of the assembly be in a bill of materials."""
    groups = {"preload_spring": {"n": 1, "entry": {"name": "preload_spring"}}}
    for v in purchased_parts():
        if v.get("inside_motor"):
            continue
        g = groups.setdefault(v["name"], {"n": 0, "entry": v})
        g["n"] += 1
    return groups


# The sentences of the list, in Italian and in English. They live in a keyed
# catalogue and not inline in the code because the same row serves two
# different readers: the project's list, which is in Italian, and the
# assembly guide, which is published and so is in English. The NUMBERS are the
# same - they come from the model - and only the language around them changes.
PHRASES = {
    "insert": {"it": "inserto a caldo %s, Ø%.1f x %.1f **M**",
                "en": "%s heat-set insert, Ø%.1f × %.1f mm **M**"},
    # The stretch the length measures is said by the ENTRY, not by this
    # sentence: there are two grubs and they measure two different things -
    # the clutch one from the flat of the shaft, the preload one from the back
    # of the spring cup - and the sentence written for the first told of a flat
    # the second does not even have.
    "grub":   {"it": "%s x %s, GRANO a brugola senza testa (%s ci sono %.1f)",
                "en": "%s × %s headless hex GRUB SCREW (%.1f mm %s)"},
    "unknown_span": {"it": "in tutto", "en": "long overall"},
    "screw":    {"it": "%s x %s, testa %s (servono %.1f sotto testa)",
                "en": "%s × %s, %s head (%.1f mm needed under the head)"},
    "head_socket": {"it": "brugola", "en": "hex socket"},
    "head_countersunk": {"it": "svasata", "en": "countersunk"},
    "bearing": {"it": "F695ZZ flangiato, 5 x 13 x 4",
                   "en": "F695ZZ flanged, 5 × 13 × 4"},
    "magnet": {"it": "Ø%.0f x %.0f, **DIAMETRALMENTE MAGNETIZZATO**",
                "en": "Ø%.0f × %.0f, **DIAMETRICALLY MAGNETISED**"},
    # where the prototype's came from, in brackets: it helps whoever rebuilds
    # it; the measures are what decide, not the source
    "spring":   {"it": "molla di compressione, filo %.1f, Ø esterno %.1f, libera %.1f, montata %.1f, %.1f N/mm (quella del prototipo viene da una molletta per i panni)",
                "en": "compression spring, wire %.1f, Ø%.1f outside, %.1f mm free, %.1f mm fitted, %.1f N/mm (the prototype's came from a clothes peg)"},
    "motor":  {"it": "NEMA 14 14HS10-0404S", "en": "NEMA 14 14HS10-0404S"},
}


def describe(name, v, language="it"):
    """How this bought part is described in a bill of materials: the size,
    the catalogue length, the warning if it has one.

    It lives in a function of its own, and not inside the loop that writes the
    table, because the assembly guide needs the SAME sentence in the chapter's
    list, only in English: two descriptions of the same part, written in two
    places, drift apart at the first touch-up and whoever assembles ends up
    with two different screws under the same name.
    """
    def f(key):
        return PHRASES[key][language]

    def size_in_language(m):
        """The size as it is written in the language: M2,5 in Italian, M2.5 in
        English. The decimal comma in the middle of English text reads as a
        list - "M2, 5 insert" - and it really happened in the first version
        of the guide."""
        return m.replace(",", ".") if language == "en" else m.replace(".", ",")

    # WHAT A PART IS, from its name - the ENGLISH name. The tests below looked
    # for Italian words ("M2 ", "M2,5", "cuscinetto", "magnete", "molla",
    # "motore") and after the rename to English none of them matched: the M2
    # and M2.5 inserts were described as M3, and the bearings, the magnet and
    # the motor had no description at all - the magnet losing its capital
    # DIAMETRICALLY MAGNETISED. Found while chasing the spring missing from
    # the guide's first list.
    import re as _re
    _m = _re.search(r"_M(\d+)(?:_|$)", name)
    if v.get("insert"):
        size = {"2": "M2", "25": "M2,5", "3": "M3", "4": "M4"}[_m.group(1) if _m else "3"]
        q = {"M2": ("D_out_insert_M2", "L_insert_M2"),
             "M2,5": ("D_out_insert_M25", "L_insert_M25"),
             "M3": ("D_out_insert_M3", "L_insert_M3"),
             "M4": ("D_out_insert_M4", "L_insert_M4")}[size]
        return f("insert") % (size_in_language(size), D[q[0]], D[q[1]])
    if v.get("grub"):
        # The grub has no head, so there is no "under the head": what is
        # needed is its whole length, from the tip pressing on the flat of the
        # shaft to the outer end of the insert. Measured on the model like all
        # the others, not written here.
        p0, p1, _u = axis_ends(v)
        length = math.dist(p0, p1)
        t = stock_length(length)
        span = v.get("span") or (f("unknown_span"), f("unknown_span"))
        span = span[0] if language == "it" else span[1]
        if language == "it":
            return f("grub") % (size_in_language(v.get("size", "M3")),
                                 ("%d" % t) if t else "?", span, length)
        return f("grub") % (size_in_language(v.get("size", "M3")),
                             ("%d" % t) if t else "?", length, span)
    if v.get("head"):
        p0, p1, _u = axis_ends(v)
        under_head = math.dist(p0, p1)
        t = stock_length(under_head)
        return f("screw") % (size_in_language(v.get("size", "M3")),
                            ("%d" % t) if t else "?",
                            f("head_" + v.get("head_type", "socket")), under_head)
    if "bearing" in name:
        return f("bearing")
    if "magnet" in name:
        # CAPITALS and bold: it is the feature that makes the
        # difference between a magnet that works and one that does not work at
        # all. A magnet magnetised along its AXIS, identical to look at and
        # easy to buy by mistake, gives no useful reading in front of the
        # AS5600 - and you do not find out until it is mounted inside.
        return f("magnet") % (D["D_magnet"], D["Th_magnet"])
    if "spring" in name:
        return f("spring") % (D["D_wire_spring"], D["D_spring_out"], D["L_spring_free"],
                             D["L_spring_fitted"], D["Rate_spring"])
    if "motor" in name:
        return f("motor")
    return ""


def write():
    r = []
    r.append("<!--")
    r.append("SPDX-FileCopyrightText: 2026 Matteo Beretta")
    r.append("SPDX-License-Identifier: CC-BY-4.0")
    r.append("-->")
    r.append("")
    r.append("# Distinta della parte meccanica")
    r.append("")
    r.append("**Questo file e' GENERATO** da `src/bom_mechanics.py` a ogni build: non si")
    r.append("modifica a mano, perche' la modifica sparisce al build dopo. Quello che c'e'")
    r.append("scritto discende dal modello - la massa dal solido, la quantita' dal conteggio")
    r.append("dei pezzi nell'assieme, la lunghezza di una vite dal suo gambo.")
    r.append("")
    r.append("La distinta di TUTTO, meccanica ed elettronica, in inglese, e' quella")
    r.append("globale: [`../../BOM.md`](../../BOM.md), generata anche lei. Le ragioni")
    r.append("dei componenti elettronici stanno in [`../../pcb/BOM.md`](../../pcb/BOM.md).")
    r.append("")
    r.append("## Pezzi da stampare")
    r.append("")
    r.append("| pezzo | materiale | q.ta | massa | giacitura |")
    r.append("|---|---|---|---|---|")
    tot = {}
    for name, mat, dens, q, orientation in PRINTED:
        m = mass(name, dens)
        if m is None:
            r.append("| %s | %s | %d | **manca il file** | %s |" % (name, mat, q, orientation))
            continue
        tot[mat] = tot.get(mat, 0.0) + m*q
        r.append("| %s | %s | %d | %.1f g | %s |" % (name.replace("_", " "), mat, q, m*q, orientation))
    r.append("")
    r.append("In tutto: " + ", ".join("**%.0f g** di %s" % (v, k) for k, v in sorted(tot.items())) + ".")
    r.append("")
    r.append("## Da comprare")
    r.append("")
    r.append("| pezzo | q.ta | quota | dove |")
    r.append("|---|---|---|---|")
    for name, g in sorted(purchased_rows().items()):
        v, n = g["entry"], g["n"]
        r.append("| %s | %d | %s | |" % (name, n, describe(name, v)))
    r.append("")
    r.append("Le quote marcate **M** sono misurate col calibro su un esemplare vero. Le")
    r.append("lunghezze delle viti sono la prima taglia di catalogo che copre quello che")
    r.append("serve sotto la testa, misurato sul modello.")
    r.append("")
    with open(BOM, "w", encoding="utf-8") as f:
        f.write("\n".join(r))
    print("wrote BOM.md: %d parts to print, %d entries to buy"
          % (len(PRINTED), len(purchased_rows())))


if __name__ == "__main__":
    write()
