#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""The guide to the driver's control panel: docs/driver/README.md and
docs/driver/index.html, one section per tab and one entry per property, each
with the portion of the panel it talks about.

Every command and option of the panel, with a picture of
the part of the panel the paragraph explains, and a guide that follows the
driver by itself - a property added or removed must not leave it silently
wrong. So nothing is listed by hand:

  - WHAT is in the panel comes from panel_en.xml, captured from the real
    compiled driver (refresh_panel.sh). The driver is English only, as every
    INDI driver: the Italian page shows the same panel, the same pictures and
    the same labels, and explains them in Italian;
  - the pictures are drawn from the same XML (draw_panel.py);
  - the words are panel_texts.py, one entry per property, in English; the
    other languages are catalogues checked against it (panel_language.py), and
    each language has its page: docs/driver/ in English, docs/driver/it/.

problems() says what does not match, and the build's check_panel_guide.py
fails on it: a property with no text, a text for a property that is gone, an
element described that the property does not have, a property named in
wheelly.cpp that the captured XML does not have (capture again), and a
TODO(check) left in a text.

    python3 panel_guide.py            writes the guide (and redraws the pictures
                                      when doc/.venv and the colour scheme are there)
"""
import html
import importlib
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel_language  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(DRIVER))
OUT_DIR = os.path.join(ROOT, "docs", "driver")
IMG = os.path.join(OUT_DIR, "img")
COLORS = os.path.expanduser("~/Library/Application Support/kstars/themes/BreezeDark.colors")


def read_panel(language):
    """The properties in declaration order: name -> dict, and the tabs in order."""
    text = open(os.path.join(HERE, "panel_%s.xml" % language), encoding="utf-8").read()
    root = ET.fromstring(text)
    prop, order, tabs = {}, [], []
    for e in root:
        m = re.match(r"^def(Number|Text|Switch|Light|BLOB)Vector$", e.tag)
        if not m or e.get("name") in prop:
            continue
        n = e.get("name")
        prop[n] = dict(kind=m.group(1), label=e.get("label") or n, tab=e.get("group"),
                       perm=e.get("perm"), rule=e.get("rule"),
                       elements=[dict(name=c.get("name"), label=c.get("label") or c.get("name"),
                                      min=c.get("min"), max=c.get("max"), step=c.get("step"))
                                 for c in e])
        order.append(n)
        if e.get("group") not in tabs:
            tabs.append(e.get("group"))
    return prop, order, tabs


def texts():
    sys.path.insert(0, HERE)
    import panel_texts
    return importlib.reload(panel_texts)


def names_in_source():
    """The properties wheelly.cpp itself declares: each is filled once as
    X.fill(getDeviceName(), "NAME", ...). The standard ones come from the
    base classes of libindi and are not named there."""
    src = open(os.path.join(DRIVER, "wheelly.cpp"), encoding="utf-8").read()
    return set(re.findall(r'\.fill\(\s*getDeviceName\(\)\s*,\s*"([A-Z0-9_]+)"', src))


def numbered_in_source():
    """The properties wheelly.cpp declares one per slot, named with a printf
    pattern - snprintf(name, ..., "WHEELLY_ANGLE_%d", ...) - as regular
    expressions. The calibration angles are one property per slot: their
    names are not literals, and names_in_source() alone would take them for
    libindi's."""
    src = open(os.path.join(DRIVER, "wheelly.cpp"), encoding="utf-8").read()
    return [re.compile("^" + re.escape(p).replace("%d", r"\d+") + "$")
            for p in re.findall(r'snprintf\([^;]*"(WHEELLY_[A-Z0-9_]*%d)"', src)]


def wheelly_own():
    """Which properties are Wheelly's own: those wheelly.cpp declares. The
    others come from libindi's base classes, and every INDI driver of the kind
    has them; the guide says which is which."""
    # the driver's own names start with WHEELLY_; FILTER_NAME is filled in
    # wheelly.cpp too, but it is INDI's standard property, the one Ekos knows
    # (so it is not marked Wheelly's)
    _p, order, _t = read_panel("en")
    numbered = {n for n in order if any(r.match(n) for r in numbered_in_source())}
    return {n for n in names_in_source() if n.startswith("WHEELLY_")} | numbered


def problems():
    en, order, tabs = read_panel("en")
    T = texts()
    out = []
    for n in order:
        if n not in T.TEXTS:
            out.append("the panel has %s, panel_texts.py has no text for it" % n)
            continue
        if T.TEXTS[n].get("variable_elements"):
            # the elements are what the system finds (SYSTEM_PORTS: one per
            # serial port, named after it): one text for all, none per element
            continue
        el = {e["name"] for e in en[n]["elements"]}
        for x in sorted(set(T.TEXTS[n].get("elements", {})) - el):
            out.append("%s: panel_texts.py describes element %s, which it does not have" % (n, x))
        for x in sorted(el - set(T.TEXTS[n].get("elements", {}))):
            out.append("%s: element %s has no text" % (n, x))
    for n in sorted(set(T.TEXTS) - set(order)):
        out.append("panel_texts.py describes %s, which the panel no longer has" % n)
    for g in tabs:
        if g not in T.TABS:
            out.append("tab %s has no introduction in panel_texts.TABS" % g)
    for r in numbered_in_source():
        if not any(r.match(n) for n in order):
            out.append("wheelly.cpp declares %s but panel_en.xml has none of them: capture "
                       "the panel again (doc/refresh_panel.sh)" % r.pattern)
    for n in sorted(names_in_source() - set(order)):
        out.append("wheelly.cpp declares %s but panel_en.xml does not have it: capture the "
                   "panel again (doc/refresh_panel.sh)" % n)
    for n, t in T.TEXTS.items():
        everything = " ".join([t.get("what", "")] + list(t.get("elements", {}).values())
                         + list(t.get("notes", [])))
        if "TODO" in everything:
            out.append("%s: a TODO is left in its text" % n)
    # every other language follows the English (panel_language)
    for l in panel_language.LANGUAGES[1:]:
        out += panel_language.problems(l)
    # the published sweep viewer is the source's copy (the driver's log links it)
    if not os.path.exists(VIEWER_OUT) or open(VIEWER_OUT, "rb").read() != open(VIEWER, "rb").read():
        out.append("docs/tools/sweep.html is not a copy of doc/sweep_viewer.html: run panel_guide.py")
    # and every picture the pages show is there (both pages show the same)
    missing = [f for f in [picture(n) for n in order]
               + [tab_picture(i, g) for i, g in enumerate(tabs, 1)]
               if not os.path.exists(os.path.join(OUT_DIR, f))]
    if missing:
        out.append("%d pictures missing, the first %s: draw them again (panel_guide.py)"
                   % (len(missing), missing[0]))
    # and none is left over: a property taken out of the driver leaves its
    # drawing behind, and a published folder of pictures nobody shows is litter
    used = {picture(n) for n in order} | {tab_picture(i, g) for i, g in enumerate(tabs, 1)}
    for n, t in T.TEXTS.items():
        if t.get("figure"):
            for l in panel_language.LANGUAGES:
                used.add(figure_picture(n, l))
                if not os.path.exists(os.path.join(OUT_DIR, figure_picture(n, l))):
                    out.append("%s: its figure is missing (%s): run panel_guide.py" % (n, figure_picture(n, l)))
            for f in t["figure"]["sweeps"]:
                if not os.path.exists(os.path.join(HERE, f)):
                    out.append("%s: the figure's sweep %s is missing" % (n, f))
    if os.path.isdir(IMG):
        stale = sorted("img/" + f for f in os.listdir(IMG) if f.endswith(".png") and "img/" + f not in used)
        if stale:
            out.append("%d pictures no page shows, the first %s: delete them" % (len(stale), stale[0]))
    return out


def draw():
    py = os.path.join(HERE, ".venv", "bin", "python")
    if not (os.path.exists(py) and os.path.exists(COLORS)):
        print("  pictures NOT redrawn: doc/.venv (PySide6) or the colour scheme is missing;"
              " the ones in docs/driver/img stay")
        return
    os.makedirs(IMG, exist_ok=True)
    # one set, the panel as the driver draws it, for both pages
    r = subprocess.run([py, os.path.join(HERE, "draw_panel.py"),
                        os.path.join(HERE, "panel_en.xml"), IMG, COLORS],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("draw_panel.py failed:\n" + r.stderr[-800:])


def figure_picture(n, language):
    return "img/%s-%s-figure.png" % (language, n.lower().replace("_", "-"))


# The figures come from the sweep viewer itself, fed with sweeps kept in doc/
# (measured on the reference wheel), in headless Chrome: the picture in the
# guide is what the page draws, and it is drawn again when the page changes.
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def draw_figures():
    import base64
    T = texts()
    if not os.path.exists(CHROME):
        print("  figures NOT redrawn: Google Chrome is missing; the ones in docs/driver/img stay")
        return
    for n, t in T.TEXTS.items():
        if not t.get("figure"):
            continue
        parts = []
        for f in t["figure"]["sweeps"]:
            with open(os.path.join(HERE, f), "rb") as fh:
                parts.append("name=%s&csv=%s" % (os.path.basename(f), base64.b64encode(fh.read()).decode()))
        for language in panel_language.LANGUAGES:
            url = "file://%s#lang=%s&view=figure&%s" % (VIEWER, language, "&".join(parts))
            out = os.path.join(OUT_DIR, figure_picture(n, language))
            r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                "--window-size=920,615", "--screenshot=" + out, url],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(out):
                raise SystemExit("the figure of %s could not be drawn: %s" % (n, r.stderr[-400:]))


def picture(n):
    return "img/en-%s.png" % n.lower().replace("_", "-")


def tab_picture(i, g):
    # named after the tab's position and its name
    return "img/en-%d-%s.png" % (i, re.sub(r"\W+", "-", g).strip("-").lower())


def limits(e, language):
    if e["min"] is None:
        return ""
    # libindi writes the limits with twenty digits (a step of 0.01 arrives as
    # "0.010000000000000000208", the binary double in full): %g gives back
    # the number the driver wrote
    def short(x):
        try:
            return "%g" % float(x)
        except (TypeError, ValueError):
            return x
    return UI[language]["limits"] % (short(e["min"]), short(e["max"]), short(e["step"]))


# the words of the page itself, around the texts of panel_texts
UI = {
    "en": dict(
        title="The Wheelly INDI driver: the control panel",
        page_title="INDI driver - Wheelly",
        h1="The INDI driver: the control panel",
        description="Every command and option of the Wheelly INDI driver's panel, with the "
                    "part of the panel it talks about.",
        lede="Every command and option of the panel, with the part of the panel it "
                  "talks about. In the "
                  "contents, ● marks what is Wheelly's own and ○ what is standard INDI.",
        generated="*Generated* by `driver/indi-wheelly/doc/panel_guide.py` from the panel "
                 "the real driver declares (captured with `doc/refresh_panel.sh`) and from "
                 "`doc/panel_texts.py`: do not edit it by hand. The pictures are drawn from "
                 "the same capture, in the theme KStars has on AstroArch.",
        kinds_md="Each entry is marked 🟦 **Wheelly** when the property is this driver's own, "
                "or ⬜ *standard INDI* when it comes from INDI itself: every INDI driver of "
                "the kind has it, Ekos knows it, and it behaves here as it does everywhere, "
                "bar what the entry says.",
        contents="Contents", skip="Skip to content", driver="INDI driver",
        in_this_tab="In this tab", element="Element",
        per_port="one per port found", read_only="read-only", limits="%s to %s, step %s",
        std="standard INDI",
        filter="Filter the properties", no_match="No property matches."),
    "it": dict(
        title="Il driver INDI di Wheelly: il pannello di controllo",
        page_title="Driver INDI - Wheelly",
        h1="Il driver INDI: il pannello di controllo",
        description="Ogni comando e ogni opzione del pannello del driver INDI di Wheelly, "
                    "con la parte del pannello di cui si parla.",
        lede="Ogni comando e ogni opzione del pannello, con la parte del pannello di "
                  "cui si parla. Le etichette sono in inglese, come sullo schermo. "
                  "Nell'indice ● segna ciò che è proprio di Wheelly e ○ ciò che è INDI standard.",
        generated="*Generato* da `driver/indi-wheelly/doc/panel_guide.py` a partire dal "
                 "pannello che dichiara il driver vero (catturato con "
                 "`doc/refresh_panel.sh`) e dai testi di `doc/panel_texts.py`, tradotti in "
                 "`doc/panel_texts_it.py`: non va modificato a mano. Le immagini sono "
                 "disegnate dalla stessa cattura, col tema che KStars ha su AstroArch. Il "
                 "pannello è in inglese, come quello di ogni driver INDI: le etichette sono "
                 "riportate come appaiono sullo schermo, e il testo le spiega in italiano.",
        kinds_md="Ogni voce è segnata 🟦 **Wheelly** quando la proprietà è di questo driver, "
                "o ⬜ *INDI standard* quando viene da INDI stesso: ce l'ha ogni driver INDI "
                "del genere, Ekos la conosce, e qui si comporta come dappertutto, salvo "
                "quello che dice la voce.",
        contents="Indice", skip="Vai al contenuto", driver="Driver INDI",
        in_this_tab="In questa scheda", element="Elemento",
        per_port="una per porta trovata", read_only="sola lettura",
        limits="da %s a %s, passo %s", std="INDI standard",
        filter="Filtra le proprietà", no_match="Nessuna proprietà corrisponde."),
}


def write(language="en"):
    en, order, tabs = read_panel("en")
    here = en
    TEXTS, TABS = panel_language.translated(language)
    U = UI[language]
    # the Italian pages sit in it/, and reach pictures and style one level up
    up = "" if language == "en" else "../"
    anchor = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    tab_name = lambda g: g
    kind_md = {True: "🟦 **Wheelly**", False: "⬜ *%s*" % U["std"]}
    kind_html = {True: ("wheelly", "Wheelly"), False: ("std", U["std"])}
    md = ["<!--", "SPDX-FileCopyrightText: 2026 Matteo Beretta",
          "SPDX-License-Identifier: CC-BY-4.0", "-->", "",
          "# %s" % U["title"], "", U["generated"], "", U["kinds_md"], ""]
    md += ["## %s" % U["contents"], ""]
    for g in tabs:
        md.append("- [%s](#%s)" % (tab_name(g), anchor(tab_name(g))))
    md.append("")
    body_html = []
    mine = wheelly_own()
    for i, g in enumerate(tabs, 1):
        gq = tab_name(g)
        md += ["## %s" % gq, "",
               TABS.get(g, ""), "", "![%s](%s%s)" % (gq, up, tab_picture(i, g)), "",
               "| %s | |" % U["in_this_tab"], "|---|---|"]
        in_tab = [n for n in order if en[n]["tab"] == g]
        md += ["| [%s](#%s) | %s |" % (here[n]["label"], anchor(here[n]["label"]),
                                       kind_md[n in mine]) for n in in_tab] + [""]
        # the anchors of the tabs are the ENGLISH names in both languages, so
        # that the pill keeps the reader where they were (#hash follows it)
        body_html.append("<h2 id=\"%s\">%s</h2>" % (anchor(g), html.escape(gq)))
        body_html.append("<p>%s</p>" % html.escape(TABS.get(g, "")))
        body_html.append("<img class=\"scheda\" src=\"%s%s\" alt=\"%s\">"
                          % (up, tab_picture(i, g), html.escape(gq)))
        for n in in_tab:
            p, t = here[n], TEXTS.get(n, {})
            ro = " · %s" % U["read_only"] if p["perm"] == "ro" else ""
            md += ["### %s" % p["label"], "",
                   "%s · `%s`%s" % (kind_md[n in mine], n, ro), "",
                   "![%s](%s%s)" % (p["label"], up, picture(n)), "",
                   t.get("what", ""), ""]
            css_class, kind_name = kind_html[n in mine]
            body_html.append("<section class=\"passo voce %s\" id=\"%s\"><h3>%s</h3>"
                              % (css_class, n.lower(), html.escape(p["label"])))
            body_html.append("<p class=\"nome\"><span class=\"badge %s\">%s</span> <code>%s</code>%s</p>"
                              % (css_class, kind_name, n, html.escape(ro)))
            body_html.append("<img src=\"%s%s\" alt=\"%s\">" % (up, picture(n), html.escape(p["label"])))
            body_html.append("<p>%s</p>" % html.escape(t.get("what", "")))
            md += ["| %s | |" % U["element"], "|---|---|"]
            body_html.append("<table><tr><th>%s</th><th></th></tr>" % U["element"])
            if t.get("variable_elements"):
                md.append("| *(%s)* | %s |" % (U["per_port"], t["variable_elements"]))
                body_html.append("<tr><td><em>%s</em></td><td>%s</td></tr>"
                                  % (U["per_port"], html.escape(t["variable_elements"])))
            for e in ([] if t.get("variable_elements") else p["elements"]):
                d = t.get("elements", {}).get(e["name"], "")
                lim = limits(e, language)
                if lim:
                    d = (d + " " if d else "") + "(%s)" % lim
                md.append("| %s | %s |" % (e["label"], d))
                body_html.append("<tr><td>%s</td><td>%s</td></tr>"
                                  % (html.escape(e["label"]), html.escape(d)))
            body_html.append("</table>")
            md.append("")
            # a table of its own, where an entry needs one (the LED's signals)
            if t.get("table"):
                tab = t["table"]
                md += ["| " + " | ".join(tab["header"]) + " |",
                       "|" + "---|" * len(tab["header"])]
                md += ["| " + " | ".join(r) + " |" for r in tab["rows"]] + [""]
                body_html.append("<table><tr>" + "".join("<th>%s</th>" % html.escape(h) for h in tab["header"])
                                  + "</tr>" + "".join("<tr>" + "".join("<td>%s</td>" % html.escape(c) for c in r)
                                                      + "</tr>" for r in tab["rows"]) + "</table>")
            # a figure, where an entry has one: a picture that is not the
            # panel (the sweep viewer's before and after), drawn per language
            if t.get("figure"):
                f = figure_picture(n, language)
                md += ["![%s](%s%s)" % (t["figure"]["caption"], up, f), "",
                       "*%s*" % t["figure"]["caption"], ""]
                body_html.append("<figure><img src=\"%s%s\" alt=\"%s\"><figcaption>%s</figcaption></figure>"
                                  % (up, f, html.escape(t["figure"]["caption"]),
                                     html.escape(t["figure"]["caption"])))
            if t.get("notes"):
                md += ["- " + x for x in t["notes"]] + [""]
                body_html.append("<ul>" + "".join("<li>%s</li>" % html.escape(x) for x in t["notes"]) + "</ul>")
            body_html.append("</section>")
    folder = OUT_DIR if language == "en" else os.path.join(OUT_DIR, language)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    # THE ASSEMBLY GUIDE'S FRAME, with a table of contents like the assembly
    # guide's: its stylesheet, its logo, its pinned index,
    # its language pill and the script that follows the reading - taken from
    # there, not copied, so the two guides look and behave the same and there
    # is one CSS to keep. The tabs are the chapters, the properties their steps.
    sys.path.insert(0, os.path.join(ROOT, "mechanics", "wheelly-cad", "src"))
    from guide import site as site_
    assembly = up + "../assembly/"
    contents = ["<details class=\"indice\" id=\"indice\" open>", "<summary>%s</summary>" % U["contents"],
              site_._logo("marchio", "wheelly-logo-horizontal", 190,
                         inside="<span>%s</span>" % U["driver"],
                         link=assembly + ("index.html" if language == "en" else "it/index.html"),
                         root=assembly),
              # THE FILTER (the field, its style and its
              # script are guide/site.py's, shared with the assembly guide): 34 properties in four tabs are
              # too many to find by eye. It looks in the label and in the INDI
              # name, so "slot" and FILTER_SLOT find the same entry
              site_.filter_field(U["filter"], U["no_match"]),
              "<nav><ol>"]
    for i, g in enumerate(tabs, 1):
        contents.append("<li class=\"cap attuale\" data-cerca=\"%s\"><a href=\"#%s\"><span class=\"num\">%d</span>"
                      "<span>%s</span></a><ol class=\"passi\">"
                      % (html.escape(tab_name(g)), anchor(g), i,
                         html.escape(tab_name(g))))
        for n in order:
            if en[n]["tab"] == g:
                search_text = " ".join([here[n]["label"], n])
                contents.append("<li data-cerca=\"%s\"><a href=\"#%s\"><span class=\"num\">%s</span><span>%s</span></a></li>"
                              % (html.escape(search_text), n.lower(), "●" if n in mine else "○",
                                 html.escape(here[n]["label"])))
        contents.append("</ol></li>")
    contents.append("</ol></nav></details>")
    head = ["<!doctype html>", "<html lang=\"%s\">" % language, "<head>", "<meta charset=\"utf-8\">",
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
             "<title>%s</title>" % html.escape(U["page_title"]),
             "<meta name=\"description\" content=\"%s\">" % html.escape(U["description"]),
             "<link rel=\"canonical\" href=\"%s\">" % site_._twin("index.html", language, language),
             "<link rel=\"alternate\" hreflang=\"en\" href=\"%s\">" % site_._twin("index.html", language, "en"),
             "<link rel=\"alternate\" hreflang=\"it\" href=\"%s\">" % site_._twin("index.html", language, "it"),
             "<link rel=\"alternate\" hreflang=\"x-default\" href=\"%s\">"
             % site_._twin("index.html", language, "en")]
    if language == "en":
        # the same first visit as the assembly guide: an Italian browser is
        # taken to the Italian page, a choice made with the pill is kept
        head.append("<script>%s</script>" % (site_.REDIRECT % site_._twin("index.html", "en", "it")))
    head += ["<link rel=\"icon\" type=\"image/svg+xml\" href=\"%sbrand/wheelly-mark.svg\">" % assembly,
              "<link rel=\"stylesheet\" href=\"%sguide.css\">" % assembly]
    page = ("\n".join(head) + "\n<style>"
              ".badge{display:inline-block;font-size:.78rem;font-weight:600;padding:.08rem .55rem;"
              "border-radius:999px}.badge.wheelly{background:#1f6feb;color:#fff}"
              ".badge.std{background:var(--pillola);color:var(--pillola-testo)}"
              ".voce{margin:2.4rem 0}.voce.wheelly{border-left:4px solid #1f6feb50;padding-left:.9rem}"
              ".it{color:var(--muto);font-weight:normal}"
              "main table{border-collapse:collapse;width:100%;margin:.6rem 0 1rem;font-size:.95rem}"
              "main td,main th{border-bottom:1px solid var(--filo);padding:.35rem .5rem;text-align:left;"
              "vertical-align:top}main img{max-width:100%;border-radius:8px}"
              "main code{background:var(--fondo2);padding:0 .3rem;border-radius:4px}"
              ".indice .passi .num{font-size:.7rem;color:#1f6feb}"
              "</style>\n</head>\n<body>\n"
              + "<a class=\"salta\" href=\"#contenuto\">%s</a>\n" % html.escape(U["skip"])
              + "<div class=\"pagina\">\n" + "\n".join(contents)
              + "\n<main id=\"contenuto\">" + site_._language_switch(language, "index.html")
              + "<h1>%s</h1><p class=\"occhiello\">%s</p>" % (html.escape(U["h1"]), html.escape(U["lede"]))
              + "".join(body_html) + "</main></div>\n<script>%s%s</script>\n</body>\n</html>" % (site_.FOLLOW, site_.FILTER))
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("docs/driver (%s): %d properties in %d tabs" % (language, len(order), len(tabs)))


# The sweep viewer: one self-contained page (sweep_viewer.html, next to this
# file) published at docs/tools/sweep.html, where the driver's log and the
# guide point. Copied, not written by hand in docs/, like everything there.
VIEWER = os.path.join(HERE, "sweep_viewer.html")
VIEWER_OUT = os.path.join(ROOT, "docs", "tools", "sweep.html")


def publish_viewer():
    os.makedirs(os.path.dirname(VIEWER_OUT), exist_ok=True)
    with open(VIEWER, "rb") as src, open(VIEWER_OUT, "wb") as dst:
        dst.write(src.read())


if __name__ == "__main__":
    draw()
    draw_figures()
    for l in panel_language.LANGUAGES:
        write(l)
    publish_viewer()
