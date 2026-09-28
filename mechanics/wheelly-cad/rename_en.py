#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""One-shot: translate the parameter names from Italian to English.

    ./.venv/bin/python rename_en.py            # dry run: says what it would do
    ./.venv/bin/python rename_en.py --apply    # writes the files

Kept in the repository after the migration on purpose. It is the only place
that records WHICH English word was chosen for each Italian one, and the next
person to add a parameter needs that glossary more than they need the diff: a
project that calls the same thing `boss` in one name and `hub` in another is
worse than one in Italian.

The English words are not invented here. Where the project already had an
official English name for a part - `palette.py`, which names every body for
the assembly guide - that name wins, so that a parameter and the part it
belongs to are called the same thing.

WHAT IT CANNOT SEE, and what cost two failed builds: a parameter name that is
not written as one piece. `D["Ang_orecchia_ant_%s" % k]` and
`D["D_testa_%s_%s" % (family, size)]` are names composed at run time, so a
substitution that works on whole names walks straight past them and the build
dies on a KeyError at the first drawing. There were seven of them, in five
files. They have to be hunted separately, and the way to find them is to look
for a string that STARTS like a parameter name and contains a placeholder:

    grep -nE 'PARAM_PREFIX_(%s|format-placeholder)' src/*.py

Two more traps, both hit and both fixed in the glossary below: an English word
with a hyphen (`lead-in`) makes a name that is not a valid identifier, and the
single letters that designate one ear of five (`_A`, `_B`, `_C`) are initials
and not words - lowercased, they stop matching the tuples the code composes
them from.

WHAT THIS DOES NOT DO: it does not translate prose. Comments and descriptions
keep their Italian for now and are translated in a separate pass; what changes
here is every NAME, everywhere it is referenced, including inside the prose, so
that a comment which mentions a parameter still names something that exists.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# --- the prefixes -------------------------------------------------------
# The editor reads the TYPE of a quote from the prefix of its name
# (`ui_quote.TIPO_DAL_NOME`), so this table is not cosmetic: it has to move
# together with that one, or the editor starts offering diameters where a
# thickness was asked for.
PREFIXES = {
    # Weld non ha un corrispondente italiano perche' e' nato in inglese, col
    # pezzo unico: Weld_box_collar e' di quanto la faccia
    # interna del guscio ENTRA nel collare perche' la fusione dia un solido e
    # non un composto di due pezzi. Non e' un gioco - e' il suo contrario -
    # quindi non poteva chiamarsi Cl.
    "Weld": "Weld",    # saldatura  -> weld (compenetrazione voluta)
    # rigidezza di una molla, N/mm: nato con la molla della molletta,
    # misurata in bilancia - una forza per millimetro non e' una
    # forza, e Force_ l'avrebbe fatta leggere come tale
    "Rig": "Rate",     # rigidezza  -> spring rate
    "Sp": "Th",        # spessore   -> thickness
    "D": "D",          # diametro   -> diameter
    "R": "R",          # raggio     -> radius
    "Int": "Cd",       # interasse  -> centre distance
    "Ang": "Ang",      # angolo     -> angle
    "Gioco": "Cl",     # gioco      -> clearance
    "Q": "Z",          # quota      -> z level
    "L": "L",          # lunghezza  -> length
    "W": "W",          # larghezza  -> width
    "H": "H",          # altezza    -> height
    "P": "Dp",         # profondita -> depth
    "Margine": "Marg",
    # the rest of them, in the same spirit: the prefix says what KIND of
    # number it is, so it is translated as a kind and not as a word
    "Agio": "Room",              # agio        -> room to spare
    "Allarga": "Widen",
    "Apertura": "Open",          # apertura di una corsa angolare
    "Aria": "Air",
    "Arretramento": "Setback",
    "Att": "Att",                # attacco: dove una cosa si aggancia
    "Avvicinamento": "Approach",
    "Battuta": "Stop",           # battuta: la spalla contro cui un pezzo va a fine corsa
    "Compensa": "Comp",
    "Coppia": "Trq",             # coppia -> torque
    "Corda": "Chord",
    "Corsa": "Travel",
    "Disco": "Disc",
    "Dist": "Dist",
    "Fascia": "Band",
    "Forza": "Force",
    "Franco": "Free",            # franco: lo spazio che RESTA, non il gioco di un accoppiamento
    "Fresata": "Flat",
    "Lato": "Side",
    "Lembo": "Edge",
    "Lettura": "Read",
    "N": "N",
    "Off": "Off",
    "Parete": "Wall",
    "Passo": "Pitch",
    "Pin": "Pin",
    "Precarico": "Preload",
    "Prof": "Dp",                # come P: profondita'
    "Racc": "Fil",               # raggio di raccordo
    "Rapporto": "Ratio",
    "Rientro": "Setback",
    "S": "S",                    # l'ascissa del riferimento dell'elettronica
    "T": "T",                    # e la sua ordinata
    "Schiacciamento": "Squash",
    "Semiamp": "Halfw",
    "Semiampiezza": "Halfw",
    "Semiarco": "Halfarc",
    "Shore": "Shore",
    "Sm": "Ch",                  # smusso -> chamfer
    "Smusso": "Ch",
    "Spor": "Proj",              # sporgenza -> projection
    "Sporgenza": "Proj",
    "Traferro": "Gap",           # il traferro del sensore
    "Usura": "Wear",
    "Z": "Z",
}

# --- the words ----------------------------------------------------------
# Everything that appears in a name after the prefix. Two rules held
# throughout: the word the guide uses for a part wins over a synonym, and a
# word that means two different things in two places is split rather than
# translated twice (see `testa`).
WORDS = {
    # accesso: lo spazio che l'ATTREZZO vuole per arrivare a una sede, che nel
    # progetto e' una quota come le altre - la punta del saldatore e la testa
    # della vite del perno ne discendono
    "accesso": "access",
    # pavimento: il fondo del vano meccanico, la faccia su cui il pezzo si
    # stampa. E' una quota derivata: il numero -38 scritto a mano si era
    # scollegato dal pezzo
    "pavimento": "floor",
    # parole nate con la frizione rovesciata e il pezzo unico
    "quota_z": "z",            # il suffisso che distingue un franco in altezza
    "profondo": "deep",        # un canale profondo vuole piu' franco di uno corto
    "dado": "nut",
    "girare": "turn",          # la corona in cui un dado si gira per avvitarsi
    "base": "base",
    # the parts, as the assembly guide names them
    "collare": "collar", "braccio": "arm", "scatola": "box",
    "frizione": "clutch", "pannellino": "panel", "staffa": "bracket",
    "bussola": "bushing", "guida": "guide", "coperchio": "cover", "sensore": "sensor", "magnete": "magnet",
    "distanziale": "spacer", "scodellino": "cup", "rondella": "washer",
    "guarnizione": "gasket", "molla": "spring", "motore": "motor",
    "albero": "shaft", "perno": "pivot", "disco": "disc", "corpo": "body",
    "mozzo": "hub", "mozzetto": "hub", "basetta": "board", "modulo": "module",
    "moduli": "modules", "scheda": "board", "driver": "driver", "xiao": "xiao",
    "gx12": "gx12", "led": "led", "usb": "usb", "tpu": "tpu",
    "millefori": "perfboard", "componenti": "components",
    "condensatore": "capacitor", "elettrolitico": "electrolytic",
    "dissipatore": "heatsink", "morsetti": "terminals", "chip": "chip",
    "cuscinetto": "bearing", "cuscinetti": "bearings",
    "cappuccio": "cap", "piedino": "foot", "cavo": "cable",
    # botola: l'apertura nel fondo sotto il motore, da cui il motore entra
    # dal basso (strada B); reoforo: uno dei quattro fili del
    # motore, che nello STEP del costruttore sono sbarre rigide - "lead" e non
    # "cable", che nel progetto e' il cavo del sensore
    "botola": "hatch", "reoforo": "lead",
    # la molla del precarico, misurata: il filo e le spire
    "filo": "wire", "spire": "coils",
    "fili": "wires", "fascetta": "tie", "canalina": "channel",
    "alimentazione": "supply", "alim": "supply", "saldatore": "iron",
    "calibro": "caliper", "prova": "test",
    # fasteners
    "vite": "screw", "viti": "screws", "inserto": "insert",
    "grano": "grub", "filetto": "thread", "svasata": "countersunk",
    # le misure metriche restano MAIUSCOLE: m3 si legge come metri cubi
    "m2": "M2", "m25": "M25", "m3": "M3", "m4": "M4",
    # features
    # filtro, ponte: born in English with the filter disc of
    # reference - the holes the filters screw into and the web of material
    # between two of them
    "filtro": "filter", "ponte": "web",
    "foro": "hole", "fori": "holes", "sede": "seat", "tasche": "pockets",
    "bossa": "boss", "bosso": "boss", "orecchia": "ear", "orecchie": "ears",
    "colonna": "column", "colonnina": "post", "piede": "foot",
    "flangia": "flange", "gonna": "skirt", "dorso": "back",
    "parete": "wall", "pareti": "walls", "muretto": "rib",
    "nervatura": "rib", "costola": "rib", "piastra": "plate",
    "piattello": "washer", "piazzola": "pad", "piazzole": "pads",
    "pad": "pad", "spalla": "shoulder", "spalle": "shoulders",
    "labbro": "lip", "bordo": "rim", "cresta": "crest", "conca": "dish",
    # arco: l'arco centrato sull'albero che chiude il lobo meccanico;
    # tetto: la faccia di sopra della scatola, a filo del collare - non il
    # "cielo" del vano, che e' la stessa lastra vista da dentro
    "arco": "arc", "tetto": "roof",
    "cava": "groove", "gola": "groove", "scanalatura": "slot",
    "asola": "slot", "asole": "slots", "scasso": "notch", "denti": "teeth",
    "invito": "leadin", "smusso": "chamfer", "raccordo": "fillet",
    "racc": "fillet", "cono": "cone", "ogiva": "nose", "anello": "ring",
    "cerchio": "circle", "spina": "spigot", "aletta": "tab",
    "collarino": "collar", "battistrada": "tread", "rondine": "dovetail",
    "labirinto": "labyrinth", "lamatura": "spotface", "fresata": "flat",
    # il plurale ha una parola sua perche' il GX12 ha DUE fresate e la quota
    # che conta e' la distanza fra le due: `W_flats_gx12` non e' la larghezza
    # di una fresata, e chiamarla al singolare la farebbe leggere cosi'
    "fresate": "flats",
    "zigrinata": "knurled", "spigoli": "edges", "bottone": "button",
    "guide": "guides", "detent": "detent", "banda": "band",
    "varco": "opening", "apertura": "opening", "apert": "opening",
    "finestra": "window", "luce": "aperture", "vano": "compartment",
    "sfogo": "relief", "passaggio": "passage", "canale": "channel",
    "sfilo": "pushout", "svaso": "taper", "riduzione": "reduction",
    "allargamento": "widening", "allargato": "widened",
    "ancoraggio": "anchor", "fissaggio": "fixing", "supporto": "support",
    # `ritegno` e non `tenuta`: qui non si tiene fuori niente - e' la parete
    # contro cui l'inserto del precarico va in battuta, quella che gli
    # impedisce di uscire quando la molla tira. `tenuta` e' la guarnizione
    "ritegno": "retain",
    "appoggio": "rest", "tenuta": "seal", "centraggio": "centring",
    "riattacco": "rejoin", "montaggio": "assembly", "stampa": "printing",
    "stampata": "printed", "stampato": "printed", "colla": "glue",
    "pila": "stack", "precarico": "preload", "corsa": "travel",
    # `presa` e' il punto per cui si prende una cosa con le dita, non una presa
    # elettrica ne' una presa d'aria: qui e' il battistrada che sporge dalla
    # scatola. `sbalzo` e' quello della stampa, la falda che resta per aria
    "presa": "grip", "sbalzo": "overhang",
    "ingresso": "entry", "ingombro": "envelope", "numeri": "numbers",
    "asse": "axis", "piano": "plane", "faccia": "face", "fianco": "side",
    "lato": "side", "fondo": "bottom", "piatto": "flat", "cima": "top",
    "punta": "tip", "bocca": "mouth", "coda": "tail", "testa": "head",
    "rientro": "setback", "sopra": "above", "sotto": "below",
    "attorno": "around", "interno": "inner", "interna": "inner",
    "esteso": "extended", "opposto": "opposite", "medio": "mid",
    "radiale": "radial", "rotante": "rotating", "ottico": "optical",
    "diagonali": "diagonal", "netta": "net", "piena": "solid",
    "libera": "free", "libere": "free", "montata": "fitted",
    "misurato": "measured", "nominale": "nominal", "ammessa": "allowed",
    "cavita": "cavity", "curv": "curvature", "inizio": "start",
    "fine": "end", "dev": "dev", "mnm": "mnm",
    # the short ones that are not words
    "est": "out", "int": "in", "ant": "front", "post": "rear",
    "pass": "clear",             # foro passante -> clearance hole
    "stampa": "printing",
    "ugello": "nozzle",          # of the printer: D_nozzle_printing
    "min": "min", "top": "top", "front": "front", "per": "per",
    "su": "on", "sulla": "on", "bra": "arm", "n": "n", "l": "l",
    "v": "v", "w": "w", "ang": "ang",
    # le lettere che designano un'orecchia o una vite sono SIGLE, non
    # parole: restano maiuscole, e il codice le compone a runtime
    # ("Ang_ear_front_%s" % k), quindi devono combaciare con ORECCHIE_ANT
    "a": "A", "b": "B", "c": "C",
}

# --- names that a word-by-word translation gets wrong -------------------
# Rare, and each one is here for a reason written next to it.
SPECIAL = {
    # units and axis letters keep their case: `Force_spring_n` reads as a word,
    # `Force_spring_N` reads as newtons, which is what it is
    "Forza_molla_N": "Force_spring_N",
    "Precarico_N": "Preload_N",
    "Coppia_cresta_detent_mNm": "Trq_detent_crest_mNm",
    "Coppia_tenuta_mNm": "Trq_hold_mNm",
    "N_fori_basetta_L": "N_holes_board_L",
    "N_fori_basetta_W": "N_holes_board_W",
    "Usura_TPU_ammessa": "Wear_TPU_allowed",
    # the centre distance, with no prefix because the project has exactly one:
    # between the wheel axis and the motor axis. Having no prefix is why it
    # slipped through the first run - to_english() left it as it was, and a
    # name left as it was does not look any different from a translated one.
    "Interasse": "Cd_motor",
}


# --- decisions whose parameter no longer exists --------------------------
# Kept, not deleted: the reason a word was chosen outlives the quote that
# needed it, and a glossary that forgets is how the same thing ends up with two
# names. `check_names.py` reads this table too, and complains if one of these
# comes back - a name that returns has to be decided again, not inherited.
RETIRED = {
    # `testa` was the head of a screw in one family of names and the flat end
    # wall of the box in another; word by word both became "head", and the
    # second one read as a screw head that is not there. The three quotes that
    # said `testa_scatola` were absorbed into the electronics reference before
    # the migration ran.
    "Ang_testa_scatola": "Ang_box_end",
    "S_testa_out": "S_box_end_out",
    "T_testa_out": "T_box_end_out",
    # `numeri` here was the printed scale on the wheel, not a quantity. Both
    # quotes gained a second word of their own before the migration
    # (`R_numeri_disco`, `Ang_finestra_numeri`), which says which numbers they
    # are, so the ambiguity this entry existed for is gone.
    "R_numeri": "R_wheel_scale",
    "Ang_numeri": "Ang_wheel_scale",
}



# --- the parts, the files and the bodies --------------------------------
# The second half of the migration, and a different job from the one above:
# here what changes is not a parameter name but the NAME OF A PART - the STEP
# in out/ that is opened to print, and the body in the assembly that the
# guide, the bill of materials and half the checks look up by name.
#
# Where the guide's palette already has an official English name for a part,
# that name wins and is simply written with underscores: the palette is what
# the reader sees, and a part called one thing in the guide and another in
# out/ is worse than one still in Italian.
#
# WHAT THIS CANNOT DO IS A BLIND WORD-FOR-WORD PASS, and that is the whole
# difference from the parameters. `braccio`, `collare`, `scatola`, `albero`
# are ordinary Italian words, and the prose of this project is full of them:
# replacing them everywhere would turn "il braccio spazza" into "il arm
# spazza". So a name made of ONE word is replaced only where it is quoted -
# that is, where it is an identifier and not a word - or followed by `.step`.
# Names made of several words joined by underscores cannot be mistaken for
# prose and are replaced wherever they appear.
PARTS = {
    # i pezzi stampati, coi nomi della tavolozza della guida
    "braccio": "arm",
    "collare": "collar",
    "collare_costampato": "collar_coprinted",
    "scatola": "box",
    "frizione_mozzo_ASA": "clutch_hub",
    "frizione_anello_TPU": "clutch_tyre",
    "frizione_completa": "clutch_assembly",
    "staffa_sensore": "sensor_bracket",
    "coperchio_sensore": "sensor_cover",
    "pannellino": "board_panel",
    "scodellino_molla": "spring_cup",
    "rondella_perno": "pivot_washer",
    "distanziale_magnete": "magnet_spacer",
    "guarnizione_anteriore": "front_gasket",
    "guarnizione_posteriore": "rear_gasket",
    # i riferimenti, che non si stampano
    "corpo_riferimento": "filter_wheel_body",
    "disco_riferimento": "filter_disc",
    "cavo_sensore": "sensor_cable",
    "cavo_sensore_asse": "sensor_cable_axis",
    "assieme_completo": "full_assembly",
    # gli attrezzi di prova
    "cappuccio_magnete": "magnet_cap",
    "piedini_traferro": "gap_gauges",
    # gli ingombri dell'elettronica. Le sigle restano: xiao, driver, gx12,
    # led, c1 e c2 vengono da fuori e non si traducono
    "basetta": "perfboard",
    "zoccoli": "pin_sockets",
    "componenti": "components",
    "morsetti": "terminals",
    "elettronica_basetta": "electronics_perfboard",
    "elettronica_zoccoli": "electronics_pin_sockets",
    "elettronica_componenti": "electronics_components",
    "elettronica_xiao": "electronics_xiao",
    "elettronica_driver": "electronics_driver",
    "elettronica_led": "electronics_led",
    "elettronica_gx12": "electronics_gx12",
    "elettronica_": "electronics_",
    # i comprati, come li nomina purchased.py: qui il nome e' una frase, e
    # diventa un identificatore con lo stesso schema dei parametri,
    # tipo-misura-dove
    "motore NEMA 14": "motor_NEMA14",
    "motore_14HS10-0404S": "motor_14HS10-0404S",
    "mozzo di centraggio": "centring_hub",
    "albero": "shaft",
    "cuscinetto F695ZZ": "bearing_F695ZZ",
    "magnete AS5600": "magnet_AS5600",
    "molla_precarico": "preload_spring",
    "inserto M2 della colonnina": "insert_M2_post",
    "vite M2 della basetta": "screw_M2_board",
    "inserto M2,5 della colonnina di testa": "insert_M25_head_post",
    "vite M2,5 della basetta": "screw_M25_board",
    "inserto M3 del pannellino": "insert_M3_panel",
    "vite M3 del pannellino": "screw_M3_panel",
    "inserto M2,5 del coperchio": "insert_M25_cover",
    "vite M2,5 del coperchio": "screw_M25_cover",
    "vite M3 del perno": "screw_M3_pivot",
    "inserto M3 del perno": "insert_M3_pivot",
    "inserto M3 dell'orecchia": "insert_M3_ear",
    "vite M3 dell'orecchia": "screw_M3_ear",
    "inserto M3 del grano": "insert_M3_grub",
    "inserto M4 del precarico": "insert_M4_preload",
    "grano M4 del precarico": "grub_M4_preload",
    "grano M3 della frizione": "grub_M3_clutch",
    "vite M3 del motore": "screw_M3_motor",
    "vite M3 del collare": "screw_M3_collar",
}


def parts_pairs():
    """(vecchio, nuovo, solo_fra_virgolette).

    Solo fra virgolette quando il nome puo' essere scambiato per prosa: una
    parola sola (`braccio`, `albero`) oppure una frase (`vite M3 del motore`).
    Le forme con gli underscore - `vite_M3_del_motore`, `frizione_mozzo_ASA` -
    in prosa non compaiono mai, e si sostituiscono dovunque.

    Le coppie tornano dalla piu' lunga alla piu' corta: sostituendo `collare`
    prima di `collare_costampato` resterebbe un ibrido che non si nota."""
    out = []
    for old, new in PARTS.items():
        una_parola = ("_" not in old.strip("_")) and (" " not in old)
        out.append((old, new, una_parola or " " in old))
        if " " in old:
            # la forma con cui solids_assembly.py compone il nome del corpo
            sotto = old.replace(" ", "_")
            out.append((sotto, new, False))
            # e la stessa con l'apostrofo PROTETTO DALLA CONTROBARRA. Dentro
            # una stringa fra virgolette doppie, "dell\'orecchia" e'
            # sintassi valida e del tutto equivalente a "dell'orecchia", ma il
            # testo del file non e' lo stesso: cercando l'apostrofo nudo, due
            # fissaggi su ventitre sono rimasti in italiano e la guida si e'
            # fermata su di loro, non qui ma due funzioni piu' in la'.
            if "'" in sotto:
                out.append((sotto.replace("'", "\\'"), new, False))
    return sorted(out, key=lambda t: -len(t[0]))


def rewrite_parts(testo):
    """Il testo con i nomi dei pezzi tradotti, e quante sostituzioni."""
    n = 0
    for old, new, solo_virg in parts_pairs():
        e = re.escape(old)
        if solo_virg:
            for pat, rep in ((r'"%s"' % e, '"%s"' % new),
                             (r"'%s'" % e, "'%s'" % new),
                             (r'%s\.step' % e, '%s.step' % new),
                             (r'%s\.stl' % e, '%s.stl' % new)):
                testo, k = re.subn(pat, rep, testo)
                n += k
        else:
            # Il nome di un corpo dell'assieme porta in coda il suo numero -
            # `vite_M3_del_motore_3` - perche' i corpi uguali devono avere nomi
            # diversi. Quella coda va lasciata passare: col solo (?![\w]) il
            # confine cade sull'underscore del numero e i corpi numerati
            # restavano tutti in italiano, mentre le liste che li nominano
            # venivano tradotte. La guida ci si e' fermata sopra.
            testo, k = re.subn(r"(?<![\w])%s(?=_\d|(?![\w]))" % e, new, testo)
            n += k
    return testo, n



def to_english(name):
    if name in SPECIAL:
        return SPECIAL[name]
    bits = name.split("_")
    head, rest = bits[0], bits[1:]
    if not rest:                       # a name with no prefix: leave it alone
        return name
    if head not in PREFIXES:
        return None
    out = [PREFIXES[head]]
    for w in rest:
        k = w.lower()
        if k not in WORDS:
            return None
        # keep the shape of the original: Th_flange_collar -> Th_flange_collar
        out.append(WORDS[k])
    return "_".join(out)


def build_map(names):
    """{old: new}, plus what could not be translated and what collided."""
    mapping, unknown = {}, []
    for n in sorted(names):
        en = to_english(n)
        if en is None:
            unknown.append(n)
        else:
            mapping[n] = en
    taken = {}
    clashes = []
    for old, new in mapping.items():
        if new in taken:
            clashes.append("%s and %s both become %s" % (taken[new], old, new))
        taken[new] = old
    return mapping, unknown, clashes


# Files whose text mentions parameter names and must follow the rename. The
# documents are included on purpose: a comment or a note that names a parameter
# which no longer exists is worse than one in the wrong language, because it
# cannot be checked by anything.
def files_to_rewrite():
    out = []
    # the whole repository, not just the CAD: the documents at the root cite
    # parameters by name, and a note that names one that no longer exists is
    # worse than one in the wrong language - nothing can check it any more.
    root = os.path.dirname(os.path.dirname(HERE))
    for folder, _sub, names in os.walk(root):
        # out/ is rebuilt, docs/ is generated: rewriting either would be undone
        # by the next build, and would put the translation in the published
        # guide before the build has agreed to it
        if any(x in folder + os.sep for x in (".git", ".venv", os.sep + "out" + os.sep,
                                              os.sep + "docs" + os.sep, "node_modules")):
            continue
        for n in names:
            # NOT ITSELF. This file is a .py inside the tree it rewrites, and the
            # left-hand side of SPECIAL is a column of Italian parameter names:
            # rewritten, `"Interasse": "Cd_motor"` becomes
            # `"Cd_motor": "Cd_motor"` and the glossary forgets the very word it
            # exists to remember. It happened, and the second run then walked
            # past Interasse without a word - the build found it, but only four
            # generators later.
            # NEMMENO check_unchanged.py. La sua docstring spiega il
            # rinominare PER ESEMPIO - "out/scatola.step diventa out/box.step"
            # - e riscritta diventa "box.step diventa box.step", cioe' perde
            # proprio la cosa che spiega. E' la stessa trappola per cui questo
            # file non riscrive se stesso. Il suo codice i nomi nuovi ce li ha
            # gia': confronta i solidi per contenuto, non per nome.
            if n.endswith((".py", ".md")) and n not in (os.path.basename(__file__),
                                                        "check_unchanged.py"):
                out.append(os.path.join(folder, n))
    return sorted(set(out))


def main():
    sys.path.insert(0, os.path.join(HERE, "src"))
    from parameters import D

    mapping, unknown, clashes = build_map(list(D))
    print("parameters: %d | translated: %d | not translated: %d | clashes: %d"
          % (len(D), len(mapping), len(unknown), len(clashes)))
    for u in unknown:
        print("   NOT TRANSLATED  %s" % u)
    for c in clashes:
        print("   CLASH           %s" % c)
    if unknown or clashes:
        print("\nnothing written: fix the glossary first.")
        return 1

    if "--apply" not in sys.argv:
        for old in sorted(mapping)[:8]:
            print("   %-34s -> %s" % (old, mapping[old]))
        print("   ... and %d more. Run with --apply to write." % (len(mapping) - 8))
        return 0

    # longest first: replacing D_perno before D_pivot_arm would eat the
    # first half of the longer name and leave a hybrid nobody notices
    pairs = sorted(mapping.items(), key=lambda kv: -len(kv[0]))
    changed = 0
    for path in files_to_rewrite():
        try:
            s = io.open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        before = s
        for old, new in pairs:
            s = re.sub(r"\b%s\b" % re.escape(old), new, s)
        if s != before:
            io.open(path, "w", encoding="utf-8").write(s)
            changed += 1
    print("rewritten: %d files" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
