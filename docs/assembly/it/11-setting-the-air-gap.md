<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

*[Read in English](../11-setting-the-air-gap.md)*

# Capitolo 11 — Regolare il traferro

*La versione pubblicata di questo capitolo, con le immagini accanto al testo e l'indice sempre in vista, è nella [guida](11-setting-the-air-gap.html).*

Il sensore legge un magnete attraverso un traferro di meno di un millimetro, e quel traferro dipende da una sola quota di un solo pezzo stampato: il piedistallo su cui poggia la staffa. Troppo lontano e il campo è troppo debole per leggerlo bene; troppo vicino e il magnete tocca il chip. In questo capitolo l&#x27;altezza giusta si trova misurando, non calcolando, perché nella pila da cui dipende c&#x27;è anche la colla.

> **Forse questo capitolo puoi saltarlo.** Se costruisci sulla stessa ruota attorno a cui è disegnato questo progetto - una ruota portafiltri manuale da Ø158 mm, con il disco rotante da Ø145 mm - e con lo stesso magnete diametrale da Ø8 × 1 mm, passa direttamente al capitolo successivo: la staffa pubblicata ha già l'altezza a cui è arrivata questa procedura. Torna qui solo se le letture del capitolo 13 vengono scarse.

## Cosa serve per questo capitolo

| Q.tà | Pezzo | |
|---:|---|---|
| 1 | U3 modulo encoder magnetico AS5600 | tondo Ø16,85 spianato a 15, una fila di 8 piazzole; vuole il ponticello VDD5V-VDD3V3, dopo il quale non accetta più i 5 V |

**Attrezzi:** una scheda ESP32 qualsiasi su una breadboard: non deve per forza essere lo XIAO, 2 viti <b>M2 × 4</b>, a testa cilindrica o svasata, un cacciavite a taglio da 2 mm, o quello adatto a quelle teste, un calibro, Chrome o Edge: la pagina di prova usa Web Serial.

<h3>Passo 1 — Perché non si può calcolare</h3><ul><li>Secondo il disegno, distanziale e magnete arrivano 1,8 mm sopra la faccia del mozzo. Incollati su un perno vero <b>misurano 2,3</b>: mezzo millimetro sparisce fra i due giunti e la tolleranza di stampa del distanziale.</li><li>Qui mezzo millimetro non è un dettaglio: senza contarlo la staffa viene bassa proprio di tanto, e il traferro vero era di <b>0,07 mm</b>, con il magnete che sfiorava il chip.</li><li>Quindi l&#x27;altezza si sceglie provando piedini di spessore noto e leggendo cosa dice il sensore. Ci vogliono venti minuti, ed è l&#x27;unico modo di tener conto della colla.</li></ul>

<h3>Passo 2 — Stampa i piedini e il distanziale</h3><ul><li>`out/tools/gap_gauges.step` contiene 7 piedini, alti da 4,6 a 5,8 mm - traferri da 0,67 a 1,87 mm - con l&#x27;altezza incisa sulla linguetta. `out/magnet_spacer.step` è il distanziale su cui poggia il magnete.</li><li><b>Attenzione:</b> Nello slicer <b>non attivare anche la compensazione dei fori</b>: il foro del magnete è già disegnato maggiorato per tenerne conto, e le due correzioni si sommano.</li><li>Dopo la stampa <b>misura il foro del magnete col calibro</b> e dillo al modello: `Comp_hole_printing` è un numero che riguarda la tua stampante, non questo progetto, e da lì in poi vale anche per la staffa vera, che quell&#x27;accoppiamento lo vuole stretto.</li><li>Ti servono anche due viti <b>M2 × 4</b>, a testa cilindrica o svasata: si fanno il filetto da sole nel foro da 1,8 mm. Quelle più lunghe sporgono dall&#x27;altra parte e tengono il piedino sollevato dalla faccia.</li></ul>

<h3>Passo 3 — Cabla la schedina del sensore sul banco</h3><ul><li>Per questo va bene qualunque ESP32: un WROOM-32 su una breadboard è perfetto, non serve lo XIAO. Alimenta il modulo AS5600 a <b>3,3 V</b>, SDA e SCL ai due piedini I²C, e DIR a massa.</li><li><b>Attenzione:</b> Il modulo deve avere il <b>ponticello VDD5V-VDD3V3</b>, e con quel ponticello non sopporta più i 5 V. Prima di dare tensione controlla la continuità fra i piedini 1 e 2 del chip: un ponticello staccato non si fa notare, dimezza in silenzio le letture e sembra in tutto e per tutto un magnete debole.</li><li>Carica `firmware/air_gap_test/air_gap_test.ino`: `cd firmware &amp;&amp; ./flash.sh air_gap_test`.</li></ul>

<h3>Passo 4 — Leggi sulla pagina, non sul monitor seriale</h3><ul><li>`cd firmware &amp;&amp; ./gap_page.sh` serve il banco di prova su <b>http://localhost:8770/</b> e lo apre. Mostra l&#x27;AGC in tempo reale, accende i settori del giro man mano che li copri, e tiene la tabella delle misure con il traferro consigliato già calcolato.</li><li><b>Attenzione:</b> Serve <b>Chrome o Edge</b>: la pagina parla con la scheda via Web Serial, che Safari e Firefox non hanno. E va servita da localhost, non aperta come file.</li><li><b>Attenzione:</b> Prima chiudi ogni altro monitor seriale: quello dell&#x27;IDE, o quello che `flash.sh` lascia aperto. La porta la può tenere un solo programma alla volta.</li></ul>

<table><tr>
<td width="55%"><img src="../img/11-05-setting-the-air-gap.png" alt="Un piedino alla volta, e fai fare al disco un giro intero" width="760"></td>
<td valign="top"><h3>Passo 5 — Un piedino alla volta, e fai fare al disco un giro intero</h3><ul><li>Ruota sul tavolo, lato telescopio in alto. Il piedino sulla faccia con l&#x27;anello attorno al magnete - si centra da solo e resta lì col suo peso - poi la schedina del sensore <b>avvitata sopra</b>.</li><li><b>Attenzione:</b> Avvitata, non solo appoggiata. Una schedina appoggiata si solleva, e allora non è più il piedino a stabilire il traferro. È il primo errore da non fare due volte.</li><li>Per ogni piedino: `r` sulla pagina o sul monitor, <b>un giro intero</b> del disco a mano - prendilo dal bordo zigrinato - poi `s` per il riepilogo. Il giro intero conta perché il magnete non è mai centrato alla perfezione, e un punto solo lo premia o lo penalizza.</li><li>Giudica sulla <b>magnitudine</b>, non sull&#x27;AGC. Con questo magnete a 3,3 V l&#x27;AGC resta a fondo scala a qualunque altezza, quindi non ti dice niente; la magnitudine è il numero che si muove.</li><li><b>Attenzione:</b> Se nemmeno il piedino più basso riesce a far salire le letture, il magnete da <b>Ø8 × 1 mm</b> così com&#x27;è è troppo debole e te ne serve uno più spesso. È una conclusione, non un fallimento.</li></ul></td>
</tr></table>
