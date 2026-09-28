<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

*[Read in English](../07-motor-into-the-clutch.md)*

# Capitolo 7 — Il motore, su dentro la frizione

*La versione pubblicata di questo capitolo, con le immagini accanto al testo e l'indice sempre in vista, è nella [guida](07-motor-into-the-clutch.html).*

Il motore è l&#x27;ultimo pezzo del meccanismo: entra dal basso, dalla botola nel fondo, e il suo albero trova la frizione che lo aspetta già sopra il braccio. Poi si blocca la frizione sull&#x27;albero, si mettono le quattro viti del motore dall&#x27;alto attraverso i fori della frizione e si chiude la botola.

## Cosa serve per questo capitolo

| Q.tà | Pezzo | |
|---:|---|---|
| 1 | motore passo-passo | NEMA 14 14HS10-0404S |
| 1 | grano M3 · frizione | M3 × 10, GRANO a brugola senza testa (dalla fresata dell'albero all'inserto ci sono 10,0) |
| 4 | vite M3 · motore | M3 × 8, testa brugola (servono 8,0 sotto testa) |
| 1 | coperchio della botola del motore | stampato, ASA |
| 2 | vite M3 · coperchio della botola | M3 × 8, testa svasata (servono 8,0 sotto testa) |

**Attrezzi:** chiave a brugola da 1,5 mm, per il grano della frizione, chiave a brugola da 2,5 mm, per le viti del motore, un cacciavite PH0, per le viti svasate della botola.

<table><tr>
<td width="55%"><img src="../img/07-01-motor-into-the-clutch.png" alt="Porta su il motore dalla botola, dentro la frizione" width="520"></td>
<td valign="top"><h3>Passo 1 — Porta su il motore dalla botola, dentro la frizione</h3><ul><li>Cablalo prima, sul banco: i suoi quattro fili vanno nella spina di J1, una <b>JST XH</b> a 4 vie, con le coppie una accanto all&#x27;altra - <b>nero+verde</b> e <b>rosso+blu</b>, le coppie che controlla il capitolo 13. Lasciali abbastanza lunghi da arrivare alla scheda.<br><img src="../img/motor-wires.svg" alt="La spina J1 con i quattro fili del motore in ordine: nero A+, verde A-, rosso B+, blu B-, ciascuno col foro della millefori in cui arriva, da X07 a X04." width="320"><br><sub>I fili del motore in J1, nell&#x27;ordine in cui stanno sulla basetta. Nero e verde sono la fase A, rosso e blu la fase B: ogni coppia affiancata, mai divisa.</sub></li><li>Prima piega i quattro fili in giù lungo il corpo del motore: passano dalla botola accanto a lui, e sono fili.</li><li>Gira l&#x27;albero finché la spianatura non è allineata con quella nel foro della frizione, che vedi dall&#x27;alto.</li><li>Da sotto, attraverso la botola, spingi su il motore: l&#x27;albero passa nel braccio ed entra nella frizione, e la faccia anteriore del motore va ad appoggiare in piano sul braccio.</li><li>Giralo in modo che i fili escano verso il vano dell&#x27;elettronica e i quattro fori sulla faccia del motore siano allineati con quelli del braccio.</li><li><b>Attenzione:</b> Tieni l&#x27;ordine del disegno - nero A+, verde A-, rosso B+, blu B-. Il firmware inverte il segnale DIR del motore proprio per quest&#x27;ordine: con una fase girata ogni movimento scappa via dalla meta, e allora la correzione va nel firmware (`mechanics_esp32.cpp`), non nei fili che hai già crimpato.</li></ul></td>
</tr></table>

<table><tr>
<td width="55%"><img src="../img/07-02-motor-into-the-clutch.png" alt="Bloccalo col grano" width="520"></td>
<td valign="top"><h3>Passo 2 — Bloccalo col grano</h3><ul><li>Spingi la frizione giù sull&#x27;albero fino in fondo. Gira l&#x27;albero a mano finché il foro del grano non guarda il centro del collare: la chiave entra da lì, attraverso il varco nell&#x27;anello.</li><li>Avvita il grano <b>M3 × 10</b> nell&#x27;inserto con una chiave a brugola da 1,5 mm, finché non appoggia sulla spianatura dell&#x27;albero.</li><li>La sezione mostra quello che da fuori non vedi: la spianatura del foro appoggia già sulla spianatura dell&#x27;albero, quindi il grano deve solo tenere giù la frizione. La coppia passa dalle spianature, non dall&#x27;attrito.</li><li><b>Attenzione:</b> Stringi deciso ma senza caricarci sopra: dal lato sottile l&#x27;inserto è tenuto da 1,0 mm di ASA.</li><li>Controlla a mano che la frizione non giri sull&#x27;albero e non si sfili.</li></ul></td>
</tr></table>

<table><tr>
<td width="55%"><img src="../img/07-03-motor-into-the-clutch.png" alt="Quattro viti, dall'alto, attraverso la frizione" width="520"></td>
<td valign="top"><h3>Passo 3 — Quattro viti, dall'alto, attraverso la frizione</h3><ul><li>Gira la frizione finché i suoi quattro fori non stanno sopra i quattro fori del braccio. Dall&#x27;apertura sopra il motore, fai cadere ogni vite <b>M3 × 8</b> nel suo foro della frizione e avvitala nei filetti del motore con una chiave a brugola da 2,5 mm, passando dallo stesso foro.</li><li>Stringile in croce, come le ruote dell&#x27;auto: una, poi quella opposta, e tirale giù in modo uniforme. La faccia del motore deve finire in piano sul braccio, perché tutto il lavoro della frizione dipende dall&#x27;albero perpendicolare al braccio.</li><li><b>Attenzione:</b> Non forzarle. Si avvitano nei fori filettati del motore stesso, e oltre il semplice accostamento non si guadagna niente.</li></ul></td>
</tr></table>

<table><tr>
<td width="55%"><img src="../img/07-04-motor-into-the-clutch.png" alt="Chiudi la botola sotto il motore" width="367"></td>
<td valign="top"><h3>Passo 4 — Chiudi la botola sotto il motore</h3><ul><li>La botola quadrata nel fondo sotto il motore è da dove entra il motore. Una volta che il motore è sul braccio, chiudila.</li><li>Il coperchio entra dal basso, faccia piana verso l&#x27;esterno: il bordo appoggia sul gradino attorno alla botola e finisce a filo del fondo.</li><li>Fissalo con due viti svasate <b>M3 × 8</b> passate nelle sue orecchie, negli inserti accanto alla botola - con un cacciavite PH0.</li></ul></td>
</tr></table>
