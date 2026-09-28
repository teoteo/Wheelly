<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

*[Read in English](../01-the-parameters-page.md)*

# Capitolo 1 — Adattarlo alla tua ruota

*La versione pubblicata di questo capitolo, con le immagini accanto al testo e l'indice sempre in vista, è nella [guida](01-the-parameters-page.html).*

Wheelly non è un oggetto unico: è un insieme di generatori che disegnano i pezzi attorno alla ruota che hai davvero. La pagina di questo capitolo è dove dici loro com&#x27;è fatta quella ruota - il diametro, quanti filtri porta, quale magnete ci hai incollato - e tutto quello che viene dopo, dai pezzi stampati ai disegni, discende da lì.

> **Forse questo capitolo puoi saltarlo.** Se costruisci sulla stessa ruota attorno a cui è stato disegnato questo progetto - una ruota portafiltri manuale da Ø158 mm - e usi lo stesso magnete diametrale da Ø8 × 1 mm, puoi passare direttamente al capitolo successivo: i pezzi pubblicati vanno già bene, e i numeri di questa pagina sono quelli da cui sono stati generati.

## Cosa serve per questo capitolo

| Q.tà | Pezzo | |
|---:|---|---|

**Attrezzi:** un computer con Python 3.12, un browser, un calibro, per l&#x27;unica misura che torna nel modello.

<h3>Passo 1 — Fai girare i generatori</h3><ul><li>I pezzi non sono file STL che esistono e basta: sono <b>generati</b>, e per cambiarne uno fai girare il generatore. Ti servono Python 3.12 e due librerie: CadQuery, che costruisce i solidi, ed ezdxf, che scrive i disegni.</li><li>Dal repository: `cd mechanics/wheelly-cad`, poi `uv venv --python python3.12 .venv` e `VIRTUAL_ENV=.venv uv pip install cadquery ezdxf`. Vanno bene anche il semplice `python -m venv` e `pip install cadquery ezdxf`, solo più lenti.</li><li><b>Attenzione:</b> Usa sempre l&#x27;interprete dentro `.venv`, mai quello di sistema: `./.venv/bin/python`. Il Python di sistema non ha nessuna delle due librerie, e l&#x27;errore che ti dà punta alla cosa sbagliata.</li></ul>

<table><tr>
<td width="55%"><img src="../img/01-02-the-parameters-page.png" alt="Apri la pagina" width="760"></td>
<td valign="top"><h3>Passo 2 — Apri la pagina</h3><ul><li>`./.venv/bin/python ui.py` apre l&#x27;editor su <b>http://127.0.0.1:8760/</b> e lancia il browser. Con `--porta N` lo metti su un&#x27;altra porta, con `--no-apri` il browser non si apre: è quello che vuoi se lavori via SSH.</li><li>La pagina elenca tutti i parametri divisi in sezioni, con il loro significato, dove sono usati e se sono stati <b>misurati su un pezzo vero</b>, dichiarati da un fornitore o assunti. Quest&#x27;ultima colonna vale la pena di leggerla prima di fidarti di un numero: la maggior parte dei difetti trovati in questo progetto veniva da valori assunti che nessuno aveva controllato.</li><li><b>Attenzione:</b> La pagina non rilegge i file da sola. Se cambi un generatore o un parametro su disco devi <b>riavviarla</b>: altrimenti stai guardando i valori letti all&#x27;avvio, e non coincideranno con quello che produce il build.</li><li>Il disegno a destra si aggiorna mentre scrivi, e sotto le <b>catene di quote</b> mostrano cosa ha fatto ogni modifica agli accoppiamenti che contano: l&#x27;imbocco sull&#x27;albero, lo schiacciamento delle guarnizioni, se la vite <b>M2</b> passa ancora. Una modifica che ne rompe uno lì diventa rossa, prima che tu abbia stampato qualsiasi cosa.</li></ul></td>
</tr></table>

<h3>Passo 3 — Cambia quello che ti serve, e solo quello</h3><ul><li>Le modifiche vanno in `src/parameters_local.py`, che <b>sovrascrive</b> `src/parameters.py` e lascia intatta la base. Così la tua ruota e quella di riferimento restano fianco a fianco, e un aggiornamento futuro del progetto non ti porta via i tuoi numeri senza che te ne accorga.</li><li>Per una ruota diversa contano il diametro del disco rotante, il numero di posizioni dei filtri e il magnete, diametro e spessore. Se cambi il magnete, la staffa del sensore si sposta con lui: il traferro è una conseguenza, non un&#x27;impostazione.</li><li>Tutto il resto ha un valore predefinito che funziona. Un parametro che non capisci è un parametro da lasciare stare: ognuno dice quali pezzi dipendono da lui, e certi ne alimentano sei.</li></ul>

<h3>Passo 4 — Lancia il build, e controlla che sia andato a buon fine</h3><ul><li>`./.venv/bin/python build.py` rigenera tutto: solidi, disegni e controlli. Ci mette una ventina di minuti.</li><li>`./.venv/bin/python build.py --solo-dxf` fa solo la geometria 2D, in pochi secondi. Usalo mentre iteri su una quota, e il build completo per confermare che niente si compenetra.</li><li><b>Attenzione:</b> <b>Leggi la fine del build prima di stampare.</b> Il senso sta nei controlli: misurano i solidi prodotti e dicono se due pezzi si compenetrano, se le viti arrivano ancora, se la ruota passa ancora libera dalla scatola. Un build finito in errore lascia su disco i file STEP precedenti, e sembrano identici a quelli buoni.</li><li>I pezzi da stampare escono in `out/`, e lì non esce nient&#x27;altro: `out/tools/` contiene gli attrezzi di prova e `out/drawings/` i disegni. Con una cartella sola, aprendola per mandare in stampa finisci per stampare un attrezzo al posto di un pezzo, e ti costa un&#x27;ora.</li></ul>
