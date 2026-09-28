# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The site of the guide: static HTML, to be served with GitHub Pages from `docs/`.

Why a site and not only the Markdown in the repository: the guide is read
**while assembling**, with dirty hands and the part in hand, and in that
condition two things are needed that the Markdown rendered by GitHub does not
give. The first is the **fixed contents**: always knowing where one is and
jumping to the right step without searching. The second is a **calm layout**:
a big picture, a few lines beside it, and nothing else around.

The reference form is RatRig's Dozuki guides, but their look is not copied:
here the parts have colours of their own and are the most colourful thing on
the page, so everything else stays on greys and a single accent.

All static, with no scaffolding: no Jekyll (there is `.nojekyll`), no site
generators, no library. One page per chapter, one style sheet, twenty lines
of JavaScript to make the contents follow the step being looked at - and if
the JavaScript does not start, the page works all the same.
"""
import html
import os
import re

from . import chapters, interface, language as languages

# The style sheet. It is written to docs/assembly/guide.css as it is: its
# comments are part of the output, so they stay as they were written.
STYLE = """/* SPDX-FileCopyrightText: 2026 Matteo Beretta
   SPDX-License-Identifier: CC-BY-4.0
   Generato da src/guide/site.py: non si modifica a mano. */

/* I colori sono quelli del marchio: Ink #16191D, Amber #EFA00B, Paper #F7F6F3.
   L'ambra pero' NON si usa per il testo: su fondo chiaro fa 2,1:1 di contrasto
   e non si legge. Vale la regola della guida del brand - "the eye, accents
   only" - quindi ambra sui segni piccoli (i punti elenco, la barra del passo
   che si sta leggendo) e una sua versione scura dove serve leggere parole. */
:root {
  --fondo: #f7f6f3; --fondo2: #efece5; --carta: #ffffff;
  --testo: #16191d; --muto: #6a6f76; --filo: #e2ded5;
  --accento: #efa00b; --accento-testo: #8a5a06;
  --attenzione: #8a5a06; --attenzione-fondo: #fbf2e2;
  /* the language pill: its own tokens, because --carta is the white behind
     the pictures and stays white in the dark theme too - the active button
     on it would be light text on white. The idle text is darker than --muto:
     on the pill's ground --muto makes 4.3:1, under the 4.5 small text wants */
  --pillola: #efece5; --pillola-attiva: #ffffff; --pillola-testo: #50555c;
  --indice: 286px;
  --titoli: "Fredoka", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #14171a; --fondo2: #1a1e22; --carta: #f7f6f3;
    --testo: #e9ebed; --muto: #98a1aa; --filo: #272c31;
    --accento: #efa00b; --accento-testo: #efa00b;
    --attenzione: #efa00b; --attenzione-fondo: #241d12;
    --pillola: #1f2428; --pillola-attiva: #343a40; --pillola-testo: #aab2ba;
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 1.5rem; }
body {
  margin: 0; background: var(--fondo); color: var(--testo);
  font: 17px/1.62 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accento-testo); }
/* Fredoka e' il carattere del marchio, e sta sui titoli: nel corpo del testo
   resta il carattere di sistema, che a misure piccole e con le mani sporche si
   legge meglio. Se il carattere non arriva - officina senza rete - la pagina
   ricade sulla pila di sistema e non cambia nient'altro. */
h1, h2, h3 { font-family: var(--titoli); line-height: 1.2; letter-spacing: -0.01em; }

.salta { position: absolute; left: -999px; }
.salta:focus { left: 1rem; top: 1rem; background: var(--fondo); padding: .5rem 1rem; }

.pagina { display: flex; align-items: flex-start; }

/* ---------------------------------------------------------- l'indice fisso */
.indice {
  width: var(--indice); flex: 0 0 var(--indice);
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  border-right: 1px solid var(--filo); background: var(--fondo2);
  padding: 1.6rem 1.1rem 3rem;
}
.indice summary { display: none; }
/* Lo spazio attorno al logo e' il diametro dell'occhio, come chiede la guida
   del marchio; a 190 px di larghezza sono circa 16 px. La misura minima del
   lockup orizzontale e' 120 px e qui ne abbiamo 190. */
.marchio { display: block; text-decoration: none; color: inherit; margin: .2rem .4rem 1.6rem; }
/* <picture> e' un elemento inline che avvolge l'immagine: senza questa riga il
   sottotitolo gli si affianca invece di stargli sotto. */
.marchio picture, .insegna picture { display: block; }
.marchio img { display: block; width: 190px; max-width: 100%; height: auto; }
.marchio span { display: block; margin-top: .55rem; font-size: .78rem; color: var(--muto);
                letter-spacing: .09em; text-transform: uppercase; }
.indice ol { list-style: none; margin: 0; padding: 0; }
/* `.indice nav a` e non `.indice a`: il logo e' anche lui un link dentro
   all'indice, e con la regola larga diventava una riga di sommario - flex, e
   quindi stretto a 129 px invece dei 190 dichiarati, col sottotitolo di fianco
   invece che sotto. Misurato nel browser, non dedotto. */
.indice nav a { display: flex; gap: .6rem; text-decoration: none; color: var(--testo);
                padding: .34rem .5rem; border-radius: 7px; font-size: .93rem; }
.indice nav a:hover { background: rgba(127, 140, 155, .14); }
.indice .num { color: var(--muto); font-variant-numeric: tabular-nums; min-width: 1.1rem; }
.indice .manca > a { color: var(--muto); cursor: default; }
.indice .manca > a:hover { background: none; }
.indice .attuale > a { font-weight: 640; }
.indice .passi { margin: .15rem 0 .8rem 1.75rem; border-left: 1px solid var(--filo); }
.indice .passi a { font-size: .875rem; color: var(--muto); padding: .22rem .55rem; border-radius: 0 7px 7px 0; }
.indice .passi a.qui { color: var(--testo); background: rgba(127, 140, 155, .16);
                       box-shadow: inset 2px 0 0 var(--accento); }
/* THE FILTER at the top of the contents, the same in both
   guides. The steps of the chapters not being read are in the page but folded
   away (.altrove), and open only while filtering: so a word found in chapter
   11 shows the step it is in, and the link goes straight there. */
/* a drawing inside a point of a step (the magnet's magnetisation): white
   ground in both themes, as the renders have */
.punti figure.illustrazione { margin: .7rem 0 .2rem; }
.punti figure.illustrazione img { display: block; width: 320px; max-width: 100%; height: auto;
                                  background: #fff; border-radius: 8px; padding: .3rem; }
.punti figure.illustrazione figcaption { font-size: .85rem; color: var(--muto); margin-top: .4rem; }
.filtro { margin: 0 0 1rem; }
.filtro input { width: 100%; box-sizing: border-box; font: inherit; font-size: .9rem;
                padding: .45rem .7rem; border-radius: 8px; border: 1px solid var(--filo);
                background: var(--carta); color: var(--testo); }
.filtro input:focus { outline: 2px solid var(--accento); outline-offset: 1px; }
.filtro-vuoto { font-size: .875rem; color: var(--muto); margin: 0 .5rem 1rem; }
.indice .passi.altrove { display: none; }
.indice.filtrando .passi.altrove { display: block; }

/* --------------------------------------------------------------- il testo */
main { flex: 1 1 auto; min-width: 0; max-width: 1060px; margin: 0 auto;
       padding: 3.2rem 3.4rem 5rem; }
.briciole { margin: 0 0 .5rem; color: var(--muto); font-size: .82rem;
            letter-spacing: .09em; text-transform: uppercase; }
.insegna { display: block; width: 260px; max-width: 70%; height: auto; margin: 0 0 1.6rem; }
h1 { margin: 0 0 1rem; font-size: 2.3rem; }
.occhiello { font-size: 1.12rem; color: var(--muto); margin: 0 0 2.6rem; max-width: 62ch; }

.serve { border: 1px solid var(--filo); border-radius: 12px; padding: 1.4rem 1.6rem;
         margin-bottom: 3.2rem; background: var(--fondo2); }
.serve h2 { margin: 0 0 1.1rem; font-size: .84rem; letter-spacing: .1em;
            text-transform: uppercase; color: var(--muto); }
.due { display: grid; grid-template-columns: 1.35fr 1fr; gap: 1.6rem; }
.due h3 { margin: 0 0 .5rem; font-size: .95rem; }
.due ul { list-style: none; margin: 0; padding: 0; }
.due li { padding: .3rem 0; border-top: 1px solid var(--filo); font-size: .95rem; }
.due li:first-of-type { border-top: 0; }
.serve li.sezione { font-weight: 600; margin-top: 1rem; list-style: none; }
.serve li.sezione:first-child { margin-top: 0; }
.q { display: inline-block; min-width: 2.1rem; color: var(--muto);
     font-variant-numeric: tabular-nums; }
.due em { display: block; margin-left: 2.1rem; color: var(--muto);
          font-style: normal; font-size: .86rem; }
.attrezzi li::before { content: "·"; color: var(--accento-testo); margin-right: .5rem; font-weight: 700; }

.passo { padding-top: 2.2rem; border-top: 1px solid var(--filo); margin-bottom: 3rem; }
.passo h2 { display: flex; gap: .85rem; align-items: baseline; margin: 0 0 1.4rem; font-size: 1.42rem; }
.passo .numero { color: var(--accento-testo); font-size: .95rem; font-weight: 700;
                 letter-spacing: .08em; text-transform: uppercase; white-space: nowrap;
                 padding-top: .25rem; }
.corpo { display: grid; grid-template-columns: minmax(0, 1.32fr) minmax(0, 1fr);
         gap: 2.2rem; align-items: start; }
/* Un passo senza immagine prende tutta la colonna invece di lasciare a destra
   un riquadro vuoto, che si legge come un'immagine che non ha caricato. */
.corpo.solo-testo { grid-template-columns: minmax(0, 1fr); }
/* Il riquadro "questo capitolo forse non ti serve", in testa alla pagina. Sta
   PRIMA di "What you need" apposta: chi puo' saltare il capitolo non deve
   prima leggersi l'elenco di quello che gli servirebbe.

   Si chiama salta-capitolo e NON salta, che era il nome ovvio: `.salta` e'
   gia' il link di salto dell'accessibilita', quello in cima al body che sta
   fuori schermo finche' non prende il fuoco. Chiamandolo cosi' il riquadro
   nuovo lo rendeva visibile, e gli finiva addosso all'indice. */
.salta-capitolo { background: var(--attenzione-fondo);
         border: 1px solid var(--accento);
         border-radius: 12px; padding: 1rem 1.2rem; margin: 0 0 1.8rem;
         display: flex; gap: .9rem; align-items: flex-start; }
/* La freccia si scrive COL CARATTERE e non con l'escape CSS: questo foglio
   di stile vive dentro una stringa Python, e un escape che comincia con la
   barra rovescia lo mangia Python come OTTALE prima che il CSS lo veda -
   diventa un carattere di controllo e lascia le cifre restanti come testo.
   Nel riquadro si leggeva un carattere illeggibile seguito da B7. */
.salta-capitolo::before { content: "↷"; color: var(--attenzione);
                 font-size: 1.5rem; line-height: 1; flex: none; }
.salta-capitolo p { margin: 0; }
.salta-capitolo strong { color: var(--attenzione); }
figure { margin: 0; }
figure a { display: block; background: var(--carta); border: 1px solid var(--filo);
           border-radius: 12px; padding: .9rem; }
/* L'immagine non riempie per forza la colonna: un esploso verticale alto
   quanto lo schermo caccia fuori dal campo il testo che lo spiega, ed e'
   proprio il testo che dice cosa si sta guardando. */
figure img { display: block; margin: 0 auto; width: auto; height: auto;
             max-width: 100%; max-height: 470px; }
figcaption { margin-top: .5rem; font-size: .8rem; color: var(--muto); }
.punti { list-style: none; margin: 0; padding: 0; }
.punti li { position: relative; padding: 0 0 .85rem 1.25rem; }
.punti li::before { content: ""; position: absolute; left: 0; top: .62em;
                    width: 6px; height: 6px; border-radius: 2px; background: var(--accento); }
.punti .attenzione { background: var(--attenzione-fondo); border-radius: 8px;
                     padding: .6rem .8rem .6rem 1.9rem; margin-bottom: .85rem; }
.punti .attenzione::before { content: "!"; background: none; color: var(--attenzione);
                             font-weight: 800; width: auto; height: auto;
                             left: .8rem; top: .62rem; }

.avanti { display: flex; justify-content: space-between; gap: 1rem;
          border-top: 1px solid var(--filo); padding-top: 1.6rem; }
.avanti a { text-decoration: none; font-weight: 600; }
.avanti span { display: block; font-size: .78rem; color: var(--muto);
               font-weight: 400; letter-spacing: .08em; text-transform: uppercase; }

/* ------------------------------------------------ the language switch
   Modelled on trendupgraphic.com (tug.css, .lang-switch): a pill with two
   real links, EN and IT, each to THE SAME PAGE in the other language. Real
   links and not a button that swaps texts: each language is a page of its
   own, that a search engine can index and a reader can bookmark. 2.75rem =
   44 px targets, the size a finger needs - and the guide is read with dirty
   hands, next to the bench. */
.testata { display: flex; justify-content: flex-end; margin: -1.6rem 0 1.2rem; }
.lang-switch { display: inline-flex; align-items: center; gap: 4px; padding: 4px;
               border-radius: 999px; background: var(--pillola);
               border: 1px solid var(--filo); }
.lang-btn { display: inline-flex; align-items: center; justify-content: center;
            min-width: 2.75rem; min-height: 2.75rem; padding: 0 .75rem;
            border-radius: 999px; color: var(--pillola-testo); font-size: .9rem;
            font-weight: 600; text-decoration: none;
            transition: background-color 180ms ease, color 180ms ease; }
.lang-btn:hover { color: var(--testo); }
.lang-btn.is-active { background: var(--pillola-attiva); color: var(--testo); }
.lang-btn:focus-visible { outline: 2px solid var(--accento); outline-offset: 2px; }

/* The fade between the two languages (Chrome, Edge, Safari; elsewhere an
   ordinary page change), as on trendupgraphic.com. The two pages have the
   same layout, so only the words seem to change. */
@view-transition { navigation: auto; }
@media (prefers-reduced-motion: reduce) {
  @view-transition { navigation: none; }
  html { scroll-behavior: auto; }
  .lang-btn { transition: none; }
}

/* ------------------------------------------------------------- l'ingresso */
.capitoli { list-style: none; margin: 0; padding: 0; }
.capitoli li { border-top: 1px solid var(--filo); }
.capitoli a, .capitoli .vuoto { display: flex; gap: 1.1rem; align-items: baseline;
                                padding: .95rem .3rem; text-decoration: none; color: var(--testo); }
.capitoli .vuoto { color: var(--muto); }
.capitoli .num { color: var(--muto); font-variant-numeric: tabular-nums; min-width: 1.6rem; }
.capitoli b { font-weight: 600; }
.capitoli em { font-style: normal; color: var(--muto); font-size: .9rem; }
.capitoli .vuoto b { color: var(--muto); font-weight: 500; }
.nota { color: var(--muto); font-size: .92rem; border-top: 1px solid var(--filo);
        margin-top: 3rem; padding-top: 1.2rem; max-width: 62ch; }
.sostegno { margin-top: 2.4rem; padding: 1.3rem 1.6rem; border-radius: 12px;
            background: var(--fondo2); border: 1px solid var(--filo); max-width: 62ch; }
.sostegno h2 { margin: 0 0 .6rem; font-size: 1.05rem; }
.sostegno p { margin: 0 0 .6rem; font-size: .95rem; }
.sostegno .minuto { margin: 0; font-size: .86rem; color: var(--muto); }
/* The sponsor button: amber ground, ink text - 9.6:1, the brand's accent used
   as a surface and not as text, which the brand guide allows ("the eye"). */
.sponsor { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem .9rem;
           margin: .9rem 0 1rem; }
.sponsor-btn { display: inline-flex; align-items: center; gap: .45rem;
               padding: .6rem 1.15rem; border-radius: 999px; background: #efa00b;
               color: #16191d; font-family: var(--titoli); font-weight: 600;
               font-size: 1.02rem; text-decoration: none;
               box-shadow: 0 1px 0 rgba(0,0,0,.12); }
.sponsor-btn:hover { background: #f6b53a; }
.sponsor-btn:focus-visible { outline: 2px solid var(--testo); outline-offset: 2px; }
.sponsor-dove { color: var(--muto); font-size: .88rem; }

/* The landing page, docs/index.html: no side contents, the three guides. */
.casa { max-width: 980px; margin: 0 auto; padding: 1.2rem 16px 3rem; }
.guide { list-style: none; padding: 0; margin: 1.8rem 0 0; display: grid; gap: 1rem;
         grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.guide li { background: var(--fondo2); border: 1px solid var(--filo); border-radius: 12px;
            padding: 1.1rem 1.3rem 1.2rem; display: flex; flex-direction: column; }
.guide h2 { font-family: var(--titoli); font-size: 1.2rem; margin: 0 0 .5rem; }
.guide h2 a { color: var(--testo); text-decoration: none; }
.guide h2 a:hover { color: var(--accento-testo); }
.guide p { margin: 0 0 .9rem; font-size: .95rem; flex: 1; }
.guide .apri { display: block; font-weight: 600; margin-top: .25rem; }

@media (max-width: 1040px) {
  .pagina { display: block; }
  .indice { position: static; width: auto; height: auto; padding: 1rem 1.2rem;
            border-right: 0; border-bottom: 1px solid var(--filo); }
  .indice summary { display: block; cursor: pointer; font-weight: 600; padding: .3rem 0; }
  .indice[open] summary { margin-bottom: .6rem; }
  .marchio { margin: .2rem .2rem 1rem; }
  main { padding: 2rem 1.2rem 4rem; }
  .testata { margin: -.8rem 0 1rem; }
  h1 { font-size: 1.85rem; }
  /* minmax(0, 1fr) e non 1fr, per cautela: `1fr` vale `minmax(auto, 1fr)` e
     il minimo automatico di un'immagine con un tetto d'altezza si calcola sul
     rapporto d'aspetto, non sulla larghezza disponibile. Sul telefono non e'
     stato visto succedere - la pagina a 500 px sta dentro - ma il caso e'
     quello in cui succederebbe. */
  .corpo, .due { grid-template-columns: minmax(0, 1fr); gap: 1.2rem; }
  figure a { padding: .6rem; }
}
"""

# Twenty lines, and the page works even if they do not start: the contents
# stay a list of links, only without the mark of how far one has got.
FOLLOW = """
(function () {
  var indice = document.getElementById('indice');
  if (indice && window.innerWidth <= 1040) { indice.open = false; }
  var voci = {}, passi = [].slice.call(document.querySelectorAll('.passo'));
  passi.forEach(function (p) {
    var a = document.querySelector('.passi a[href="#' + p.id + '"]');
    if (a) { voci[p.id] = a; }
  });
  if (!passi.length || !('IntersectionObserver' in window)) { return; }
  var visti = {};
  var occhio = new IntersectionObserver(function (righe) {
    righe.forEach(function (r) { visti[r.target.id] = r.isIntersecting; });
    var scelto = passi.filter(function (p) { return visti[p.id]; })[0];
    passi.forEach(function (p) {
      if (voci[p.id]) { voci[p.id].classList.toggle('qui', scelto === p); }
    });
  }, { rootMargin: '-10% 0px -70% 0px' });
  passi.forEach(function (p) { occhio.observe(p); });
})();
"""


# The filter of the contents, shared by the two guides. It looks in what each
# entry carries in data-cerca - titles, and for the assembly guide the words
# of the steps; for the driver guide the labels in both languages and the INDI
# name. Accents, case and underscores do not count ("proprieta" finds
# "proprietà", filter_slot finds FILTER_SLOT). A chapter whose own words match
# shows all its steps; otherwise only the steps that match, and a chapter with
# none disappears. Escape empties the field.
FILTER = """
(function () {
  var campo = document.getElementById('filtro');
  if (!campo) { return; }
  var indice = document.getElementById('indice');
  var vuoto = document.querySelector('.filtro-vuoto');
  var capi = [].slice.call(document.querySelectorAll('.indice nav > ol > li'));
  function piano(t) {
    return (t || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
                    .toLowerCase().replace(/_/g, ' ');
  }
  function filtra() {
    var q = piano(campo.value).trim(), trovate = 0;
    indice.classList.toggle('filtrando', q !== '');
    capi.forEach(function (c) {
      var tutto = q === '' || piano(c.dataset.cerca).indexOf(q) >= 0, qui = 0;
      [].slice.call(c.querySelectorAll('.passi > li')).forEach(function (v) {
        var si = tutto || piano(v.dataset.cerca).indexOf(q) >= 0;
        v.hidden = !si;
        if (si) { qui++; }
      });
      c.hidden = !(tutto || qui > 0);
      if (!c.hidden) { trovate++; }
    });
    vuoto.hidden = trovate > 0;
  }
  campo.addEventListener('input', filtra);
  campo.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { campo.value = ''; filtra(); }
  });
})();
"""


def filter_field(placeholder, nothing):
    """The field and the "nothing found" line, for the top of the contents."""
    return ("<div class=\"filtro\"><input type=\"search\" id=\"filtro\" placeholder=\"%s\" "
            "aria-label=\"%s\" autocomplete=\"off\" spellcheck=\"false\"></div>"
            "<p class=\"filtro-vuoto\" hidden>%s</p>" % (_e(placeholder), _e(placeholder), _e(nothing)))


def _search_text(step):
    """The words of a step, for the filter: its title and its points, without
    the marks of emphasis."""
    points = [x[0] if isinstance(x, (tuple, list)) else x for x in step.get("points", [])]
    t = " ".join([step["title"]] + points).replace("**", "")
    return " ".join(t.lstrip("!").split())


# THE LANGUAGE A VISITOR GETS, as tug.js does it on trendupgraphic.com: the
# English page is the default; a visitor who comes to it from OUTSIDE the
# site with an Italian browser is sent to the Italian page. No cookie and no
# storage: the choice is remembered by the referrer alone - who clicks "EN" on
# an Italian page arrives from this same site, and stays in English.
# ?lang=it forces Italian (a link that must open in Italian).
#
# One difference from tug.js, and why: this guide is also opened FROM DISK
# (see the root index.html). A file:// page gets no
# referrer, so every link followed inside the English guide would look like an
# arrival from outside, and an Italian browser would be thrown back to Italian
# at each click - after the reader had chosen English. On file:// there is no
# "outside", so only ?lang=it redirects there.
#
# In <head> and not at the end, so the redirect happens before anything is
# painted. %s is where the Italian twin of this page is.
REDIRECT = """
(function () {
  var params = new URLSearchParams(window.location.search);
  var scelta = params.get('lang');
  var daQui = false;
  try {
    daQui = document.referrer !== '' &&
            new URL(document.referrer).origin === window.location.origin;
  } catch (e) { daQui = false; }
  var lingue = navigator.languages && navigator.languages.length ?
               navigator.languages[0] : (navigator.language || '');
  var italiano = lingue.toLowerCase().indexOf('it') === 0;
  var suDisco = window.location.protocol === 'file:';
  if (scelta === 'it' || (scelta === null && !daQui && !suDisco && italiano)) {
    window.location.replace('%s' + window.location.hash);
  }
})();
"""

# Where the guide is published, for canonical and hreflang. Empty: the links
# are relative, which the HTML standard allows and search engines resolve;
# with an address here they become absolute, as on trendupgraphic.com.
ADDRESS = ""


# The brand files the site carries with it. They are in brand/ at the root of
# the repository, which GitHub Pages does NOT publish - Pages serves only
# docs/ - so the generator puts a copy of them next to the pages. The source
# stays one: whoever changes the logo changes brand/ and that is all.
BRAND = ("wheelly-logo-horizontal.svg", "wheelly-logo-horizontal-reversed.svg",
         "wheelly-mark.svg", "wheelly-mark-reversed.svg")

# The owner's GitHub user name, for the sponsor button. If it stays empty the
# invitation is there all the same but without a link: better a sentence with
# no link than a link that leads to a page that does not exist.
# It is also in .github/FUNDING.yml, which switches on the "Sponsor" button at
# the top of the repository page: the two must be kept in agreement.
GITHUB_HANDLE = "teoteo"


def _e(t):
    return html.escape(t, quote=True)


def _logo(css_class, name, width, inside="", link=None, root=""):
    """The logo, in the right version for the viewer's theme.

    Two files and not one coloured with CSS: the brand mark is a two-colour
    drawing and on a dark ground inverting it is not enough, it takes the
    reversed version that the brand package provides on purpose. `<picture>`
    chooses by itself and without JavaScript; whoever does not support it sees
    the light version, which is the main one.
    """
    img = ("<picture>"
           "<source media=\"(prefers-color-scheme: dark)\" srcset=\"%sbrand/%s-reversed.svg\">"
           "<img src=\"%sbrand/%s.svg\" width=\"%d\" alt=\"Wheelly\">"
           "</picture>" % (root, name, root, name, width))
    if link:
        return "<a class=\"%s\" href=\"%s\">%s%s</a>" % (css_class, link, img, inside)
    return "<div class=\"%s\">%s%s</div>" % (css_class, img, inside)


def _root(lang):
    """From a page to the shared files: pictures, style and brand are one copy,
    in the English folder, and the Italian pages reach them one level up."""
    return "" if lang == "en" else "../"


def _twin(page, lang, towards):
    """The link from a page in `language` to the same page in `towards`."""
    if lang == towards:
        return page
    return ("%s/%s" % (towards, page)) if lang == "en" else ("../" + page)


def _head(title, description, lang, page):
    """The <head>, and the top of the body.

    lang, canonical and the alternates as trendupgraphic.com has them: each
    page names itself as canonical, both languages as alternates, and English
    as x-default - the one to show a reader whose language is neither."""
    def absolute(towards):
        rel = page if towards == "en" else "it/" + page
        return (ADDRESS.rstrip("/") + "/" + rel) if ADDRESS else _twin(page, lang, towards)
    r = ["<!doctype html>", "<html lang=\"%s\">" % lang, "<head>",
         "<meta charset=\"utf-8\">",
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
         "<title>%s</title>" % _e(title),
         "<meta name=\"description\" content=\"%s\">" % _e(description),
         "<link rel=\"canonical\" href=\"%s\">" % absolute(lang),
         "<link rel=\"alternate\" hreflang=\"en\" href=\"%s\">" % absolute("en"),
         "<link rel=\"alternate\" hreflang=\"it\" href=\"%s\">" % absolute("it"),
         "<link rel=\"alternate\" hreflang=\"x-default\" href=\"%s\">" % absolute("en")]
    if lang == "en":
        r.append("<script>%s</script>" % (REDIRECT % _twin(page, "en", "it")))
    r += ["<link rel=\"icon\" type=\"image/svg+xml\" href=\"%sbrand/wheelly-mark.svg\">"
          % _root(lang),
          "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">",
          "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>",
          "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?"
          "family=Fredoka:wght@500;600&display=swap\">",
          "<link rel=\"stylesheet\" href=\"%sguide.css\">" % _root(lang),
          "</head>", "<body>",
          "<a class=\"salta\" href=\"#contenuto\">%s</a>"
          % _e(interface.t("skip_to_steps", lang)),
          "<div class=\"pagina\">", ""]
    return "\n".join(r)


def _language_switch(lang, page):
    """The EN / IT pill, at the top of the text column: in the side contents
    it would vanish on a phone, where the contents fold shut."""
    r = ["<div class=\"testata\"><nav class=\"lang-switch\" aria-label=\"%s\">"
         % _e(interface.t("language", lang))]
    for towards, code, name in (("en", "EN", "English"), ("it", "IT", "Italiano")):
        active = towards == lang
        r.append("<a class=\"lang-btn%s\"%s href=\"%s\" hreflang=\"%s\" lang=\"%s\" "
                 "aria-label=\"%s\">%s</a>"
                 % (" is-active" if active else "",
                    " aria-current=\"page\"" if active else "",
                    _twin(page, lang, towards), towards, towards, name, code))
    r.append("</nav></div>")
    return "".join(r)


def _side_contents(written, lang, current=None):
    """The contents: all the chapters, always; those not written yet show that
    they are missing instead of disappearing, or the reader does not know how
    much road is left. The chapter being looked at has its steps open."""
    r = ["<details class=\"indice\" id=\"indice\" open>",
         "<summary>%s</summary>" % _e(interface.t("contents", lang)),
         _logo("marchio", "wheelly-logo-horizontal", 190,
               inside="<span>%s</span>" % _e(interface.t("assembly_guide", lang)),
               link="index.html", root=_root(lang)),
         filter_field(interface.t("filter", lang), interface.t("filter_empty", lang)),
         "<nav><ol>"]
    for num, title, note in languages.plan(lang):
        cap = written.get(num)
        if cap is None:
            r.append("<li class=\"manca\" data-cerca=\"%s\"><a><span class=\"num\">%d</span>"
                     "<span>%s</span></a></li>" % (_e(title), num, _e(title)))
            continue
        here = (current is not None and current["num"] == num)
        r.append("<li class=\"cap%s\" data-cerca=\"%s\"><a href=\"%s\"><span class=\"num\">%d</span>"
                 "<span>%s</span></a>" % (" attuale" if here else "",
                                          _e(" ".join([title, _unmarked(note or "")])),
                                          _page_of(cap), num, _e(title)))
        # the steps of every chapter, not only of this one: the others folded
        # away (.altrove), for the filter to open
        r.append("<ol class=\"passi%s\">" % ("" if here else " altrove"))
        for step in cap["steps"]:
            r.append("<li data-cerca=\"%s\"><a href=\"%s#step-%d\"><span class=\"num\">%d</span>"
                     "<span>%s</span></a></li>"
                     % (_e(_search_text(step)), "" if here else _page_of(cap),
                        step["n"], step["n"], _e(step["title"])))
        r.append("</ol>")
        r.append("</li>")
    r.append("</ol></nav></details>")
    return "\n".join(r)


def _page_of(cap):
    return "%02d-%s.html" % (cap["num"], cap["id"])


def _chapter(cap, written, before, after):
    lang = cap.get("language", "en")
    T = lambda k: interface.t(k, lang)
    page = _page_of(cap)
    r = [_head(T("chapter_title") % cap["title"], _unmarked(cap["intro"])[:150],
               lang, page),
         _side_contents(written, lang, cap),
         "<main id=\"contenuto\">",
         _language_switch(lang, page),
         "<p class=\"briciole\">%s</p>" % (T("chapter_n") % cap["num"]),
         "<h1>%s</h1>" % _e(cap["title"]),
         # through _bold: with _e() alone the chapter 13 intro would show its
         # **isolates one thing** with the asterisks
         "<p class=\"occhiello\">%s</p>" % _bold(cap["intro"])]
    if cap.get("skip"):
        r.append("<div class=\"salta-capitolo\"><p>%s</p></div>" % _bold(_e(cap["skip"])))
    r += ["<section class=\"serve\"><h2>%s</h2><div class=\"due\">" % T("what_you_need"),
          "<div><h3>%s</h3><ul>" % T("parts")]
    for n, label, note in cap["bom"]:
        if n is None:                       # a section of the list
            r.append("<li class=\"sezione\">%s</li>" % _e(label))
            continue
        r.append("<li><span class=\"q\">%d×</span>%s%s</li>"
                 % (n, _e(label),
                    ("<em>%s</em>" % _e(_unmarked(note))) if note else ""))
    r.append("</ul></div><div><h3>%s</h3><ul class=\"attrezzi\">" % T("tools"))
    for a in cap["tools"]:
        r.append("<li>%s</li>" % _bold(a))
    r.append("</ul></div></div></section>")

    for step in cap["steps"]:
        r.append("<section class=\"passo\" id=\"step-%d\">" % step["n"])
        r.append("<h2><span class=\"numero\">%s</span> <span>%s</span></h2>"
                 % (T("step_n") % step["n"], _e(step["title"])))
        # A step without a picture takes the whole column: there is nothing to
        # show, and an empty box next to the text reads as a picture that did
        # not load.
        r.append("<div class=\"corpo%s\">" % ("" if step["png"] else " solo-testo"))
        if step["png"]:
            # the picture opens at full size: it is the "zoom" that is really
            # needed when trying to understand which way round a part goes
            r.append("<figure><a href=\"%simg/%s\"><img src=\"%simg/%s\" alt=\"%s\" "
                     "width=\"%d\" height=\"%d\" loading=\"lazy\"></a></figure>"
                     % (_root(lang), step["png"], _root(lang), step["png"],
                        _e(step["title"]),
                        step["img_w"], step["img_h"]))
        r.append("<ul class=\"punti\">")
        for k, (text, careful) in enumerate(step["points"], 1):
            r.append("<li%s>%s%s</li>" % (" class=\"attenzione\"" if careful else "",
                                          _bold(text),
                                          illustration(step, k, _root(lang) + "img/", lang)))
        r.append("</ul></div></section>")

    if before or after:
        r.append("<nav class=\"avanti\">")
        r.append(_shortcut(before, T("previous")) if before else "<span></span>")
        r.append(_shortcut(after, T("next")) if after else "<span></span>")
        r.append("</nav>")
    r.append("</main></div>\n<script>%s%s</script>\n</body>\n</html>" % (FOLLOW, FILTER))
    return "\n".join(r)


def _shortcut(cap, towards):
    """The link to the chapter before or after; `towards` is its label,
    Previous or Next."""
    return ("<a href=\"%s\"><span>%s</span>%d. %s</a>"
            % (_page_of(cap), towards, cap["num"], _e(cap["title"])))


def _unmarked(t):
    return t.replace("**", "")


# WHAT IDENTIFIES A PART, in bold wherever the text names it: M3 and
# Ø5,0 × 3,0 mm, and in general every measure or mark that identifies a
# part. Whoever assembles has a handful of screws and
# inserts that look alike, and reads the step looking for which one to take.
# A rule here and not ** in every text: it holds in both languages and for
# the texts still to be written.
#   - screw and insert sizes: M2, M2.5 / M2,5, M3, M4, with their length
#     (M3 × 20);
#   - a pair of measures that is a part: Ø5,0 × 3,0 mm (an insert), Ø8 × 1
#     (the magnet) - a single Ø is a hole or a bit, not a part;
#   - catalogue codes of bought parts.
_IDENTIFIES = re.compile(
    r"(?<![\w.,])M[2-4](?:[.,]5)?(?: ?× ?\d+(?:[.,]\d+)?)?(?![\w])"
    r"|Ø\d+(?:[.,]\d+)? ?× ?\d+(?:[.,]\d+)?(?: mm)?"
    r"|\bF695ZZ\b|\bGX12\b|\bJST XH\b|\bDIN 912\b")


def _highlight(t):
    """Bold on what identifies a part, outside `code` (a command is not a
    part name)."""
    pieces = t.split("`")
    for i in range(0, len(pieces), 2):
        pieces[i] = _IDENTIFIES.sub(lambda m: "<b>%s</b>" % m.group(0), pieces[i])
    return "`".join(pieces)


def _bold(t):
    """The little Markdown the step texts really use: **bold**; and outside
    the bold, in bold also what identifies a part."""
    out, pieces = [], _e(t).split("**")
    for i, p in enumerate(pieces):
        out.append(_highlight(p) if i % 2 == 0 else "<b>%s</b>" % p)
    return "".join(out)


def _support(lang):
    """The invitation to support the project.

    It sits at the bottom of the index and not on top of the steps: whoever is
    assembling has busy hands and that is not the moment to ask them
    something. The text also says what does NOT change by paying, because an
    invitation that does not say so makes one think there is a better version
    somewhere."""
    T = lambda k: interface.t(k, lang)
    # The button is the loudest thing in the box: a link
    # inside a sentence reads as a footnote. Without a handle there is no
    # page to send anyone to, and the box says so with words only.
    if GITHUB_HANDLE:
        button = ("<p class=\"sponsor\"><a class=\"sponsor-btn\" "
                  "href=\"https://github.com/sponsors/%s\">"
                  "<span aria-hidden=\"true\">\u2665</span> %s</a>"
                  "<span class=\"sponsor-dove\">%s</span></p>"
                  % (GITHUB_HANDLE, _e(T("sponsor")), _e(T("sponsor_where"))))
    else:
        button = ""
    return ("<section class=\"sostegno\">"
            "<h2>%s</h2>" % _e(T("support")) +
            "<p>%s</p>" % _e(T("support_text")) +
            button +
            "<p class=\"minuto\">%s</p>" % _e(T("support_small")) +
            "</section>")


def _index_page(written, lang):
    T = lambda k: interface.t(k, lang)
    r = [_head(T("index_title"), T("index_description"), lang, "index.html"),
         _side_contents(written, lang),
         "<main id=\"contenuto\">",
         _language_switch(lang, "index.html"),
         _logo("insegna", "wheelly-logo-horizontal", 260, root=_root(lang)),
         "<h1>%s</h1>" % _e(T("assembly_guide")),
         "<p class=\"occhiello\">%s</p>" % _e(T("index_lede")),
         "<ul class=\"capitoli\">"]
    for num, title, note in languages.plan(lang):
        cap = written.get(num)
        if cap is None:
            r.append("<li><span class=\"vuoto\"><span class=\"num\">%d</span>"
                     "<span><b>%s</b> <em>— %s</em></span></span></li>"
                     % (num, _e(title), _e(T("not_written_yet"))))
        else:
            r.append("<li><a href=\"%s\"><span class=\"num\">%d</span>"
                     "<span><b>%s</b>%s</span></a></li>"
                     % (_page_of(cap), num, _e(title),
                        (" <em>— %s</em>" % _e(note)) if note else ""))
    r.append("</ul>")
    # the note carries its own <b>: it is markup from the catalogue, not text
    r.append("<p class=\"nota\">%s</p>" % T("index_note"))
    r.append(_support(lang))
    r.append("</main></div>\n<script>%s%s</script>\n</body>\n</html>" % (FOLLOW, FILTER))
    return "\n".join(r)


def illustration(step, k, img, lang, md=False):
    """The drawing a step asks for after its point k, with its caption - or
    nothing. The file is one for both languages (it has no words); the
    caption and the alternative text are translated."""
    name = step.get("illustrations", {}).get(k)
    if not name:
        return ""
    from . import illustrations
    if name not in illustrations.DRAWINGS:
        raise SystemExit("guide: a step asks for the drawing %s, which illustrations.py "
                         "does not make" % name)
    stem = name.rsplit(".", 1)[0]
    alt = _e(interface.t("alt_" + stem, lang))
    caption = _e(interface.t("caption_" + stem, lang))
    if md:      # GitHub: no classes, a plain image and a line under it
        return '<br><img src="%s%s" alt="%s" width="320"><br><sub>%s</sub>' % (img, name, alt, caption)
    return ("<figure class=\"illustrazione\"><img src=\"%s%s\" alt=\"%s\" width=\"320\" "
            "height=\"150\"><figcaption>%s</figcaption></figure>" % (img, name, alt, caption))


def _write_illustrations(destination):
    """Writes the drawings into img/, where the renders are: from code, at
    every run, so a drawing changed in illustrations.py cannot be left old."""
    from . import illustrations
    os.makedirs(os.path.join(destination, "img"), exist_ok=True)
    for name, draw in illustrations.DRAWINGS.items():
        with open(os.path.join(destination, "img", name), "w", encoding="utf-8") as f:
            f.write(draw())


def _copy_brand(destination):
    """Copies into docs/ the brand files the pages use."""
    import shutil
    root = os.path.dirname(os.path.dirname(destination))
    src_dir = os.path.join(root, "brand", "svg")
    a = os.path.join(destination, "brand")
    os.makedirs(a, exist_ok=True)
    for f in BRAND:
        source = os.path.join(src_dir, f)
        if not os.path.exists(source):
            raise SystemExit("brand file missing: %s" % source)
        shutil.copyfile(source, os.path.join(a, f))


def write_pages(prepared, destination, lang="en"):
    """The pages of one language. English in `destination`, the others in a
    folder of their own; the style, the brand and the pictures are shared and
    written once, with the English."""
    folder = destination if lang == "en" else os.path.join(destination, lang)
    os.makedirs(folder, exist_ok=True)
    written = {c["num"]: c for c in prepared}
    ordered = sorted(prepared, key=lambda c: c["num"])
    for i, cap in enumerate(ordered):
        before = ordered[i-1] if i else None
        after = ordered[i+1] if i + 1 < len(ordered) else None
        with open(os.path.join(folder, _page_of(cap)), "w", encoding="utf-8") as f:
            f.write(_chapter(cap, written, before, after))
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(_index_page(written, lang))
    print("site (%s): %d chapters + index in %s" % (lang, len(ordered), folder))
    if lang != "en":
        return
    with open(os.path.join(destination, "guide.css"), "w", encoding="utf-8") as f:
        f.write(STYLE)
    _copy_brand(destination)
    _write_illustrations(destination)
    # GitHub Pages, without Jekyll: the pages are already HTML and Jekyll must
    # not lay hands on them. The file goes at the root of what is published.
    root = os.path.dirname(destination)
    open(os.path.join(root, ".nojekyll"), "w").close()
    write_home(root)


# The board guide's files: made by the wiring generator into pcb/, which GitHub
# Pages does not publish (it serves only docs/). Copied, like the brand: the
# source stays one. Per language: (PDF, SVG).
BOARD_FILES = {"en": ("en_wheelly-wiring-diagrams.pdf", "en_board-layout.svg"),
               "it": ("it_wheelly-schemi-montaggio.pdf", "it_disposizione-basetta.svg")}


def write_home(root):
    """The first page of the published site, docs/index.html and its Italian
    twin docs/it/index.html: the three guides side by side, and the support
    box.

    It gives room to all three guides (rejected: a redirect into the
    assembly guide, which hid the other two). The language script stays:
    an Italian reader arriving from outside lands on the Italian page, as
    before. The style is the assembly guide's, one file for the whole site."""
    import shutil
    repo = os.path.dirname(root)
    board = os.path.join(root, "pcb")
    os.makedirs(board, exist_ok=True)
    for pair in BOARD_FILES.values():
        for f in pair:
            source = os.path.join(repo, "pcb", f)
            if not os.path.exists(source):
                raise SystemExit("board guide file missing: %s" % source)
            shutil.copyfile(source, os.path.join(board, f))
    for lang in interface.LANGUAGES:
        T = lambda k: interface.t(k, lang)
        up = "" if lang == "en" else "../"
        folder = root if lang == "en" else os.path.join(root, lang)
        os.makedirs(folder, exist_ok=True)
        sub = "" if lang == "en" else "it/"
        pdf, svg = BOARD_FILES[lang]
        r = ["<!doctype html>", "<html lang=\"%s\">" % lang, "<head>",
             "<meta charset=\"utf-8\">",
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
             "<title>%s</title>" % _e(T("home_title")),
             "<meta name=\"description\" content=\"%s\">" % _e(T("home_description")),
             "<link rel=\"canonical\" href=\"index.html\">",
             "<link rel=\"alternate\" hreflang=\"en\" href=\"%sindex.html\">" % up,
             "<link rel=\"alternate\" hreflang=\"it\" href=\"%s\">"
             % ("it/index.html" if lang == "en" else "index.html"),
             "<link rel=\"alternate\" hreflang=\"x-default\" href=\"%sindex.html\">" % up]
        if lang == "en":
            r.append("<script>%s</script>" % (REDIRECT % "it/index.html"))
        r += ["<link rel=\"icon\" type=\"image/svg+xml\" href=\"%sassembly/brand/wheelly-mark.svg\">" % up,
              "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">",
              "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>",
              "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?"
              "family=Fredoka:wght@500;600&display=swap\">",
              "<link rel=\"stylesheet\" href=\"%sassembly/guide.css\">" % up,
              "</head>", "<body>", "<div class=\"casa\">", "<main id=\"contenuto\">",
              _language_switch(lang, "index.html"),
              _logo("insegna", "wheelly-logo-horizontal", 260, root=up + "assembly/"),
              "<p class=\"occhiello\">%s</p>" % _e(T("home_lede")),
              "<ul class=\"guide\">"]
        cards = (("home_assembly", "%sassembly/%sindex.html" % (up, sub), None),
                 ("home_board", "%spcb/%s" % (up, pdf),
                  [("home_board_pdf", "%spcb/%s" % (up, pdf)),
                   ("home_board_svg", "%spcb/%s" % (up, svg))]),
                 ("home_driver", "%sdriver/%sindex.html" % (up, sub), None))
        for key, href, extra in cards:
            links = extra or [("home_open", href)]
            r.append("<li><h2><a href=\"%s\">%s</a></h2><p>%s</p><div>%s</div></li>"
                     % (href, _e(T(key)), _e(T(key + "_text")),
                        "".join("<a class=\"apri\" href=\"%s\">%s &rarr;</a>"
                                % (h, _e(T(k))) for k, h in links)))
        r += ["</ul>", _support(lang), "</main></div>", "</body>", "</html>", ""]
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
            f.write("\n".join(r))
    print("site: landing page with the three guides in %s" % root)
