# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""What you buy for the electronics, as data: ONE list, read by the assembly
guide (chapter 0 and the chapter that fits the board) and by the global bill
of materials, BOM.md at the root of the repository.

Without it, in the assembly guide the electronics seemed to come from
nowhere. Rejected: a list of the guide's own, written by hand in
guide/write.py - it lumped the components into one row ("C1, C2, R1..R3, J1,
J3, J4, J5", quantity 1) and called the driver a TMC2209, while it is a
TMC2208 (pcb/BOM.md, identified reading the chip). The values and quantities
lived only in the hand-written tables of pcb/BOM.md.

Each item says which body of the assembly stands for it, if one does (the
electronics in the model are ESTIMATED envelopes, electronics_*). The check
in guide/write.bom_gaps, which runs in every build, wants every
body of the assembly covered and every body named here to exist. pcb/BOM.md
keeps the REASONS behind each choice; its references (U1, C1, ...) must be
these, bar the ones in NOT_BOUGHT_HERE, and the same check compares them, so
the two lists cannot drift apart.

Where a value was measured on a real part it says so ("M"), as the project
asks: the numbers taken from a catalogue are where most defects came from.
"""

# (ref, qty, part, spec, where, body)
#   ref   - the reference on the wiring diagrams and in pcb/BOM.md ("" if none)
#   where - "board", "off the board", "cables"
#   body  - the body of the assembly that stands for it, or None
ITEMS = [
    ("U1", 1, "Seeed XIAO ESP32-S3", "native USB-C; FPC antenna on U.FL",
     "board", "electronics_xiao"),
    ("U2", 1, "TMC2208 stepstick driver, with its heatsink",
     "8+8 pin module, Rsense 0.110 Ω (M, marked R110). A TMC2208, not a TMC2209: "
     "see pcb/BOM.md", "board", "electronics_driver"),
    ("C1", 1, "electrolytic capacitor", "47 µF 63 V, Ø6.35 × 13 mm (M) - bulk at the "
     "driver's VM, required, and its place on the board matters", "board",
     "electronics_components"),
    ("C2", 1, "electrolytic capacitor", "47 µF 63 V - optional, bulk at the 12 V input",
     "board", "electronics_components"),
    ("R1", 1, "resistor", "10 kΩ ¼ W - pull-up on EN, not in series", "board",
     "electronics_components"),
    ("R2", 1, "resistor", "1 kΩ ¼ W - in series on TX; leave it out if the driver "
     "module already has one", "board", "electronics_components"),
    ("R3", 1, "resistor", "1 kΩ ¼ W - in series with the LED", "board",
     "electronics_components"),
    # J1, J4, J5: JST XH, 2.5 mm pitch - latched connectors with a housing,
    # as on the reference board (pcb/BOM.md), not 2.54 pin headers; 2.5 on
    # the 2.54 perfboard is 0.12 mm off over four ways, which the holes take.
    ("J1", 1, "JST XH socket, 4 ways", "pitch 2.5 - motor phases A± B±, one connector; with its plug",
     "board", "electronics_components"),
    ("J3", 1, "screw terminal block, 2 ways", "pitch 5.08 - 12 V in", "board",
     "electronics_components"),
    ("J4", 1, "JST XH socket, 4 ways", "pitch 2.5 - sensor: SDA, SCL, VCC, GND; with its plug", "board",
     "electronics_components"),
    ("J5", 1, "JST XH socket, 2 ways", "pitch 2.5 - status LED; with its plug", "board",
     "electronics_components"),
    ("", 2, "female pin strip, 1 × 7", "round pins through both sides, body 3.0 mm - "
     "the XIAO's socket", "board", "electronics_pin_sockets"),
    ("", 2, "female pin strip, 1 × 8", "the driver's socket", "board",
     "electronics_pin_sockets"),
    ("", 1, "perfboard", "double-sided, pitch 2.54, cut to 70 × 30.3 (24 × 10 holes)",
     "board", "electronics_perfboard"),
    ("U3", 1, "AS5600 magnetic encoder module", "round Ø16.85 flattened to 15, a row of "
     "8 pads; needs the VDD5V-VDD3V3 bridge, after which it no longer takes 5 V",
     "off the board", None),
    ("C3", 1, "ceramic capacitor", "100 nF (104), 16 V or more - on the module's pads, "
     "not on the board", "off the board", None),
    ("D1", 1, "red LED, 3 mm", "outside the board; if it comes pre-wired for 12 V, take "
     "its resistor off", "off the board", "electronics_led"),
    ("", 1, "GX12 connector, 2 pins", "panel socket with its nut, and the matching plug "
     "for the 12 V lead", "off the board", "electronics_gx12 electronics_gx12_nut"),
    ("", 1, "CAT5 cable", "solid, Ø5.6 - sensor to board", "cables", "sensor_cable"),
    ("", 1, "USB cable, USB-A to USB-C", "90 degree side elbow at both ends: it goes on "
     "and off at every session", "cables", None),
    ("", 2, "clip-on ferrites", "on the motor lead and the USB cable, two or three turns "
     "through each", "cables", None),
]


# references of pcb/BOM.md that are not in the list above, and why
NOT_BOUGHT_HERE = {
    "M1": "the motor is bought with the mechanics: it is a body of the assembly",
    "D2": "not fitted: only for the buck converter variant",
}


def bodies():
    """Every assembly body the list stands for, and the items behind each."""
    out = {}
    for it in ITEMS:
        for b in (it[5] or "").split():
            out.setdefault(b, []).append(it)
    return out


# THE SAME LIST IN ITALIAN, for the Italian assembly guide. English above stays the source and is not touched; each row
# here is keyed by the item's reference - or by its English part name when it
# has none - and carries the fingerprint of the English part and spec it was
# translated from. When the English changes, the fingerprint no longer
# matches and the guide's build fails (problems_it()), instead of the Italian
# page going on saying the old value. Same scheme as guide/language.py.
#   key: (fingerprint, part, spec)
ITEMS_IT = {
    "U1": ("bfe20ee8", "Seeed XIAO ESP32-S3", "USB-C nativo; antenna FPC su U.FL"),
    "U2": ("e9920d05", "driver stepstick TMC2208, con il suo dissipatore",
           "modulo a 8+8 pin, Rsense 0,110 Ω (M, marcata R110). Un TMC2208, non un "
           "TMC2209: vedi pcb/BOM.md"),
    "C1": ("6048e75b", "condensatore elettrolitico",
           "47 µF 63 V, Ø6,35 × 13 mm (M) - di riserva sulla VM del driver, "
           "obbligatorio, e il suo posto sulla basetta conta"),
    "C2": ("92cdc50e", "condensatore elettrolitico",
           "47 µF 63 V - facoltativo, di riserva sull'ingresso a 12 V"),
    "R1": ("372b58a4", "resistenza", "10 kΩ ¼ W - pull-up su EN, non in serie"),
    "R2": ("56984d3e", "resistenza",
           "1 kΩ ¼ W - in serie su TX; non metterla se il modulo del driver ne "
           "ha già una"),
    "R3": ("48bc890d", "resistenza", "1 kΩ ¼ W - in serie al LED"),
    "J1": ("944abaad", "presa JST XH, 4 vie",
           "passo 2,5 - fasi del motore A± B±, un solo connettore; con la sua spina"),
    "J3": ("d33f215b", "morsettiera a vite, 2 poli", "passo 5,08 - ingresso 12 V"),
    "J4": ("a93cf06c", "presa JST XH, 4 vie",
           "passo 2,5 - sensore: SDA, SCL, VCC, GND; con la sua spina"),
    "J5": ("6a31be0d", "presa JST XH, 2 vie",
           "passo 2,5 - LED di stato; con la sua spina"),
    "female pin strip, 1 × 7": ("7a2b9f58", "strip femmina, 1 × 7",
           "piedini tondi passanti da due lati, corpo 3,0 mm - lo zoccolo del XIAO"),
    "female pin strip, 1 × 8": ("20b933b0", "strip femmina, 1 × 8",
           "lo zoccolo del driver"),
    "perfboard": ("343127d2", "basetta millefori",
           "doppia faccia, passo 2,54, tagliata a 70 × 30,3 (24 × 10 fori)"),
    "U3": ("a27b7fd3", "modulo encoder magnetico AS5600",
           "tondo Ø16,85 spianato a 15, una fila di 8 piazzole; vuole il ponticello "
           "VDD5V-VDD3V3, dopo il quale non accetta più i 5 V"),
    "C3": ("2dd7b287", "condensatore ceramico",
           "100 nF (104), 16 V o più - sulle piazzole del modulo, non sulla basetta"),
    "D1": ("21a88fb3", "LED rosso, 3 mm",
           "fuori dalla basetta; se arriva già cablato per i 12 V, togligli la "
           "resistenza"),
    "GX12 connector, 2 pins": ("9c6b9cfc", "connettore GX12, 2 poli",
           "presa da pannello con il suo dado, e la spina corrispondente per il "
           "cavo dei 12 V"),
    "CAT5 cable": ("e76187c3", "cavo CAT5", "rigido, Ø5,6 - dal sensore alla basetta"),
    "USB cable, USB-A to USB-C": ("78cef1e7", "cavo USB, da USB-A a USB-C",
           "gomito laterale a 90 gradi su tutti e due i capi: si attacca e si "
           "stacca a ogni sessione"),
    "clip-on ferrites": ("4297c1c8", "ferriti a clip",
           "sul cavo del motore e sul cavo USB, due o tre giri dentro ciascuna"),
}


def _key(it):
    return it[0] or it[2]


def _fingerprint(it):
    import hashlib
    return hashlib.sha1(("%s\n%s" % (it[2], it[3])).encode("utf-8")).hexdigest()[:8]


def problems_it():
    """Items with no Italian, Italian gone stale, Italian for nothing."""
    out, keys = [], set()
    for it in ITEMS:
        k = _key(it)
        keys.add(k)
        if k not in ITEMS_IT:
            out.append("bom_electronics: %s has no Italian (ITEMS_IT), fingerprint %s"
                       % (k, _fingerprint(it)))
        elif ITEMS_IT[k][0] != _fingerprint(it):
            out.append("bom_electronics: the Italian of %s is out of date - the English "
                       "has changed since (new fingerprint %s)" % (k, _fingerprint(it)))
    for k in sorted(set(ITEMS_IT) - keys):
        out.append("bom_electronics: %s is translated but no longer in ITEMS" % k)
    return out


def rows(body=None, lang="en"):
    """(qty, label, note) rows, as the guide's lists want them: all items, or
    only the ones a given body stands for; in English or in Italian."""
    sel = ITEMS if body is None else bodies().get(body, [])
    out = []
    for it in sel:
        ref, q, part, spec = it[0], it[1], it[2], it[3]
        if lang == "it":
            _h, part, spec = ITEMS_IT[_key(it)]
        out.append((q, ("%s %s" % (ref, part)) if ref else part, spec))
    return out


def refs():
    return {it[0] for it in ITEMS if it[0]}
