# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""The fixed words of the assembly guide - headings, buttons, the index page,
the support box, the Markdown table headers - in every language, by key.

The chapter texts are not here: they are in chapters.py (English, the source)
and in the chapters_<lang>.py catalogues (guide/it/ for Italian), with their fingerprints (language.py).
These are the words AROUND them, the ones site.py and write.py used to write
inline in English. They sit in one catalogue, English and Italian side by side
under the same key, for the reason the project asks every user-facing string
to go through a key: a string written inline in a page generator is a string
nobody remembers to translate, and the Italian page comes out with "Step 3"
and "Next" in the middle of Italian prose.

Both languages side by side, and not a fingerprint as in language.py, because
here the two texts are on the same line: whoever changes the English sees the
Italian next to it. problems() still checks that neither is missing and that
both take the same %-fields, since a missing %d is an exception at the first
page and an extra one a page that says "%d".

Numbers go into the Italian with the decimal comma (number()); inside code
spans they stay as they are, see write._format.
"""
import re

TEXTS = {
    # ------------------------------------------------------------- the pages
    "skip_to_steps": {"en": "Skip to the steps",
                       "it": "Salta ai passi"},
    "contents": {"en": "Contents",
               "it": "Indice"},
    "alt_magnet-magnetisation": {
        "en": "Two identical-looking disc magnets: on the left N and S side by side across the "
              "diameter, marked right; on the right N on the top face and S underneath, marked wrong.",
        "it": "Due magneti a disco identici all'aspetto: a sinistra N e S affiancati lungo il "
              "diametro, segnato giusto; a destra N sulla faccia superiore e S sotto, segnato sbagliato."},
    "caption_magnet-magnetisation": {
        "en": "Left, the one to buy: N and S side by side, the field across the diameter. "
              "Right, the one that looks the same and does not work: N on top, S underneath.",
        "it": "A sinistra quello da comprare: N e S affiancati, il campo lungo il diametro. "
              "A destra quello che sembra uguale e non funziona: N sopra, S sotto."},
    "alt_motor-wires": {
        "en": "The J1 plug with the motor's four wires in order: black A+, green A-, red B+, "
              "blue B-, each with the perfboard hole it lands on, X07 to X04.",
        "it": "La spina J1 con i quattro fili del motore in ordine: nero A+, verde A-, rosso B+, "
              "blu B-, ciascuno col foro della millefori in cui arriva, da X07 a X04."},
    "caption_motor-wires": {
        "en": "The motor's wires in J1, in the order they sit on the board. Black and green are "
              "phase A, red and blue phase B: each pair side by side, never split.",
        "it": "I fili del motore in J1, nell'ordine in cui stanno sulla basetta. Nero e verde "
              "sono la fase A, rosso e blu la fase B: ogni coppia affiancata, mai divisa."},
    "filter": {"en": "Filter chapters and steps",
               "it": "Filtra capitoli e passi"},
    "filter_empty": {"en": "Nothing matches.",
                     "it": "Nessun risultato."},
    "assembly_guide": {"en": "Assembly guide",
                        "it": "Guida di montaggio"},
    "chapter_title": {"en": "%s — Wheelly assembly guide",
                        "it": "%s — guida di montaggio di Wheelly"},
    "chapter_n": {"en": "Chapter %d",
                   "it": "Capitolo %d"},
    "what_you_need": {"en": "What you need",
                   "it": "Cosa serve"},
    "parts": {"en": "Parts",
              "it": "Pezzi"},
    "tools": {"en": "Tools",
                 "it": "Attrezzi"},
    "step_n": {"en": "Step %d",
                "it": "Passo %d"},
    "previous": {"en": "Previous",
                   "it": "Precedente"},
    "next": {"en": "Next",
                   "it": "Successivo"},
    "careful": {"en": "Careful:",
                   "it": "Attenzione:"},
    # the aria-label of the language pill (as on trendupgraphic.com)
    "language": {"en": "Language",
               "it": "Lingua"},

    # --------------------------------------------------------- the index page
    "index_title": {"en": "Wheelly — assembly guide",
                        "it": "Wheelly — guida di montaggio"},
    "index_description": {
        "en": "Build a motorised filter wheel: step by step, with pictures "
              "rendered from the CAD model.",
        "it": "Costruisci una ruota portafiltri motorizzata: passo per passo, "
              "con immagini generate dal modello CAD."},
    "index_lede": {
        "en": "A motorised filter wheel, made out of a manual one. Work through "
              "the chapters in order: each one starts with the parts and the "
              "tools it needs.",
        "it": "Una ruota portafiltri motorizzata, ricavata da una manuale. Segui "
              "i capitoli in ordine: ognuno comincia con i pezzi e gli attrezzi "
              "che gli servono."},
    "not_written_yet": {"en": "not written yet",
                           "it": "non ancora scritto"},
    "index_note": {
        "en": "Every picture in this guide is rendered from the CAD model of the "
              "machine, so it cannot show a part different from the one you "
              "printed. <b>Each part keeps the same colour from the first step "
              "to the last.</b>",
        "it": "Ogni immagine di questa guida è generata dal modello CAD della "
              "macchina, quindi non può mostrare un pezzo diverso da quello che "
              "hai stampato. <b>Ogni pezzo tiene lo stesso colore dal primo "
              "passo all'ultimo.</b>"},
    "support": {"en": "Support the project",
                 "it": "Sostieni il progetto"},
    # The sponsor link is a BUTTON, not words inside a sentence: the most
    # evident thing in the support box. A link buried
    # in the middle of a paragraph reads as a footnote and nobody clicks it.
    "sponsor": {"en": "Sponsor the repository",
                    "it": "Sponsorizza il repository"},
    "sponsor_where": {"en": "on GitHub Sponsors, monthly or once",
                      "it": "su GitHub Sponsors, ogni mese o una volta sola"},
    "support_text": {
        "en": "Wheelly is free, and it stays free. If this guide saved you an "
              "evening, sponsoring it pays for Claude tokens, for filament, and "
              "for the parts that get printed three times before they fit.",
        "it": "Wheelly è libero, e resta libero. Se questa guida ti ha fatto "
              "risparmiare una serata, sponsorizzarlo paga i token di Claude, il "
              "filamento e i pezzi che si stampano tre volte prima che entrino."},

    # ----------------------------------------------- the landing page, docs/
    # The first page of the published site, rather than a redirect straight
    # into the assembly guide (rejected: the other two guides - the driver's
    # panel and the board - could then only be found by knowing their
    # address).
    "home_title": {"en": "Wheelly — the guides",
                   "it": "Wheelly — le guide"},
    "home_description": {
        "en": "A motorised filter wheel made out of a manual one: how to build "
              "it, how to wire its board, how to drive it from Ekos.",
        "it": "Una ruota portafiltri motorizzata, ricavata da una manuale: come "
              "si costruisce, come si cabla la sua scheda, come si pilota da Ekos."},
    "home_lede": {
        "en": "A motorised filter wheel, made out of a manual one. Three guides "
              "take you from the printer to the first filter change in Ekos.",
        "it": "Una ruota portafiltri motorizzata, ricavata da una manuale. Tre "
              "guide ti portano dalla stampante al primo cambio di filtro in Ekos."},
    "home_assembly": {"en": "Hardware assembly guide",
                      "it": "Guida al montaggio della meccanica"},
    "home_assembly_text": {
        "en": "Printing, heat-set inserts, clutch, motor, sensor: chapter by "
              "chapter, with pictures rendered from the CAD model.",
        "it": "Stampa, inserti a caldo, frizione, motore, sensore: capitolo per "
              "capitolo, con le immagini ricavate dal modello CAD."},
    "home_board": {"en": "Board assembly guide",
                   "it": "Guida al montaggio della scheda"},
    "home_board_text": {
        "en": "The perfboard hole by hole, as you hold it: where every part sits "
              "and every wire runs, printed at 1:1.",
        "it": "La millefori foro per foro, come la tieni in mano: dove sta ogni "
              "componente e dove passa ogni filo, stampabile in scala 1:1."},
    "home_board_pdf": {"en": "Wiring diagrams (PDF)",
                       "it": "Schemi di montaggio (PDF)"},
    "home_board_svg": {"en": "Board layout (SVG)",
                       "it": "Disposizione della basetta (SVG)"},
    "home_driver": {"en": "INDI driver guide",
                    "it": "Guida al driver INDI"},
    "home_driver_text": {
        "en": "Every command and option of the control panel in Ekos, with the "
              "part of the panel it talks about: calibration, tolerances, motor.",
        "it": "Ogni comando e ogni opzione del pannello di controllo in Ekos, con "
              "la parte del pannello di cui parla: taratura, tolleranze, motore."},
    "home_open": {"en": "Open the guide",
                  "it": "Apri la guida"},
    "support_small": {
        "en": "Nothing is held back for sponsors: no paid version, no private "
              "repository, no chapter behind a paywall.",
        "it": "Per chi sponsorizza non c'è niente di riservato: nessuna versione "
              "a pagamento, nessun repository privato, nessun capitolo dietro "
              "un abbonamento."},

    # ------------------------------------------------------- the parts lists
    "sec_printed": {"en": "Printed parts",
                     "it": "Pezzi stampati"},
    "sec_mechanics": {"en": "Mechanics to buy",
                      "it": "Meccanica da comprare"},
    "sec_electronics": {"en": "Electronics to buy",
                        "it": "Elettronica da comprare"},
    "printed": {"en": "printed, %s",
                 "it": "stampato, %s"},

    # ------------------------------------------------ the Markdown for GitHub
    "md_chapter": {"en": "Chapter %d — %s",
                    "it": "Capitolo %d — %s"},
    "md_published": {
        "en": "The published version of this chapter, with pictures side by "
              "side and a pinned table of contents, is in [the guide](%s).",
        "it": "La versione pubblicata di questo capitolo, con le immagini "
              "accanto al testo e l'indice sempre in vista, è nella "
              "[guida](%s)."},
    "md_skip": {"en": "Maybe skip this one.",
                 "it": "Forse questo capitolo puoi saltarlo."},
    "md_what_you_need": {"en": "What this chapter needs",
                      "it": "Cosa serve per questo capitolo"},
    "md_qty": {"en": "Qty",
               "it": "Q.tà"},
    "md_part": {"en": "Part",
                 "it": "Pezzo"},
    "md_tools": {"en": "Tools:",
                    "it": "Attrezzi:"},
    "md_step": {"en": "Step %d — %s",
                 "it": "Passo %d — %s"},
    # the line at the top of every Markdown file that leads to the other
    # language: it names the OTHER language, in that language
    "md_other_language": {"en": "Leggi in italiano",
                        "it": "Read in English"},
    "md_index_intro": {
        "en": "A motorised filter wheel, built from a manual one. Work through "
              "the chapters in order: each one lists the parts and the tools it "
              "needs before its first step.",
        "it": "Una ruota portafiltri motorizzata, ricavata da una manuale. Segui "
              "i capitoli in ordine: ognuno elenca i pezzi e gli attrezzi che "
              "gli servono prima del primo passo."},
    "md_site": {
        "en": "**The published guide is the site** — open `index.html` here, or "
              "the GitHub Pages address of this repository. The Markdown files "
              "below are the same chapters, kept so they can be read and diffed "
              "inside GitHub.",
        "it": "**La guida pubblicata è il sito**: apri `index.html` qui, oppure "
              "l'indirizzo GitHub Pages di questo repository. I file Markdown "
              "qui sotto sono gli stessi capitoli, tenuti perché si possano "
              "leggere e confrontare dentro GitHub."},
    "md_pictures": {
        "en": "Every picture in this guide is rendered from the CAD model itself, "
              "so it cannot show a machine different from the one you printed. "
              "**Each part keeps the same colour from the first step to the "
              "last.**",
        "it": "Ogni immagine di questa guida è generata dal modello CAD stesso, "
              "quindi non può mostrare una macchina diversa da quella che hai "
              "stampato. **Ogni pezzo tiene lo stesso colore dal primo passo "
              "all'ultimo.**"},
    "md_chapter_column": {"en": "Chapter",
                            "it": "Capitolo"},
    "md_as_page": {"en": "as a page",
                       "it": "come pagina"},
}

LANGUAGES = ("en", "it")          # the first is the default

# the %-fields a text takes: %s, %d, %.1f ... ("%%" is not one)
FIELDS = re.compile(r"%(?!%)[-+ #0]*\d*(?:\.\d+)?[sdfr]")


def t(key, language="en"):
    """The text of a key in a language. A missing one stops the guide: a page
    must not come out with a hole where a heading was."""
    try:
        return TEXTS[key][language]
    except KeyError:
        raise SystemExit("guide: the fixed text %r has no %s" % (key, language))


def number(text, language):
    """The decimal separator of the language, in a text made of numbers:
    "Ø5.0 × 3.0" stays so in English and becomes "Ø5,0 × 3,0" in Italian.
    Only a point BETWEEN two digits changes, so "U.FL" and a full stop do not."""
    if language == "it":
        return re.sub(r"(?<=\d)\.(?=\d)", ",", text)
    return text


def problems():
    """Every key in every language, not empty, with the same %-fields."""
    out = []
    for key, texts in sorted(TEXTS.items()):
        for l in LANGUAGES:
            if not (texts.get(l) or "").strip():
                out.append("fixed text %r has no %s" % (key, l))
        if all(texts.get(l) for l in LANGUAGES):
            fields = {l: sorted(FIELDS.findall(texts[l])) for l in LANGUAGES}
            if fields["en"] != fields["it"]:
                out.append("fixed text %r: the %%-fields differ, en %s it %s"
                           % (key, fields["en"], fields["it"]))
        for l in set(texts) - set(LANGUAGES):
            out.append("fixed text %r has a language the guide does not know: %s"
                       % (key, l))
    return out


def english_left():
    """The English fixed texts that must NOT appear in an Italian page: the
    ones that differ from their Italian, cut at the first %-field or tag (the
    fixed part is what would show). Derived from the catalogue, not listed by
    hand, so a key added tomorrow is watched tomorrow."""
    out = set()
    for key, texts in TEXTS.items():
        if key == "md_other_language":        # it IS English on purpose
            continue
        en = texts["en"]
        if en == texts.get("it"):
            continue
        piece = re.split(r"%|<|\*\*|\[|`", en)[0].strip(" —:")
        if len(piece) >= 4:
            out.add(piece)
    return sorted(out)
