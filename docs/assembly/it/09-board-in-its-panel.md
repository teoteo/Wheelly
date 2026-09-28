<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

*[Read in English](../09-board-in-its-panel.md)*

# Capitolo 9 — La basetta nel pannellino

*La versione pubblicata di questo capitolo, con le immagini accanto al testo e l'indice sempre in vista, è nella [guida](09-board-in-its-panel.html).*

L&#x27;elettronica sta su un pezzo di basetta millefori avvitato al pannellino che chiude il lato inferiore della scatola. Basetta e pannellino escono insieme, in un pezzo solo: è così che arrivi a un XIAO o a un driver quando la macchina è già sul telescopio. In questo capitolo la basetta va nel pannellino; cosa va dove sulla basetta non lo ripetiamo qui: il libretto dei collegamenti in `pcb/` è disegnato per chi ha la millefori in mano e il saldatore caldo.

## Cosa serve per questo capitolo

| Q.tà | Pezzo | |
|---:|---|---|
| 1 | basetta millefori | doppia faccia, passo 2,54, tagliata a 70 × 30,3 (24 × 10 fori) |
| 2 | strip femmina, 1 × 7 | piedini tondi passanti da due lati, corpo 3,0 mm - lo zoccolo del XIAO |
| 2 | strip femmina, 1 × 8 | lo zoccolo del driver |
| 1 | C1 condensatore elettrolitico | 47 µF 63 V, Ø6,35 × 13 mm (M) - di riserva sulla VM del driver, obbligatorio, e il suo posto sulla basetta conta |
| 1 | C2 condensatore elettrolitico | 47 µF 63 V - facoltativo, di riserva sull'ingresso a 12 V |
| 1 | R1 resistenza | 10 kΩ ¼ W - pull-up su EN, non in serie |
| 1 | R2 resistenza | 1 kΩ ¼ W - in serie su TX; non metterla se il modulo del driver ne ha già una |
| 1 | R3 resistenza | 1 kΩ ¼ W - in serie al LED |
| 1 | J1 presa JST XH, 4 vie | passo 2,5 - fasi del motore A± B±, un solo connettore; con la sua spina |
| 1 | J3 morsettiera a vite, 2 poli | passo 5,08 - ingresso 12 V |
| 1 | J4 presa JST XH, 4 vie | passo 2,5 - sensore: SDA, SCL, VCC, GND; con la sua spina |
| 1 | J5 presa JST XH, 2 vie | passo 2,5 - LED di stato; con la sua spina |
| 2 | vite M2 · basetta | M2 × 6, testa svasata (servono 5,5 sotto testa) |
| 1 | vite M2,5 · basetta | M2,5 × 6, testa brugola (servono 5,5 sotto testa) |
| 1 | U1 Seeed XIAO ESP32-S3 | USB-C nativo; antenna FPC su U.FL |
| 1 | U2 driver stepstick TMC2208, con il suo dissipatore | modulo a 8+8 pin, Rsense 0,110 Ω (M, marcata R110). Un TMC2208, non un TMC2209: vedi pcb/BOM.md |

**Attrezzi:** saldatore, una punta da Ø2,7 mm, per il foro B05 della basetta millefori, chiave a brugola da 2 mm, per la vite <b>M2,5</b>, un cacciavite PH0 per le viti <b>M2</b> svasate.

<table><tr>
<td width="55%"><img src="../img/09-01-board-in-its-panel.png" alt="Prima costruisci la basetta, sul banco" width="304"></td>
<td valign="top"><h3>Passo 1 — Prima costruisci la basetta, sul banco</h3><ul><li>La basetta è un pezzo di millefori a passo 2,54 mm da 70 × 30,3 mm, 24 × 10 fori, tagliato a misura con due lati spianati.</li><li><b>Attenzione:</b> Un foro va allargato prima di saldare qualunque cosa, finché la basetta è ancora nuda: <b>B05</b> - seconda colonna dal lato della testata, riga 05, fra le due file di piedini dello XIAO - passa dal Ø2 mm della griglia stampata a Ø2,7 mm. È il foro della terza vite, e una <b>M2,5</b> nella griglia così com&#x27;è non passa. Adesso è molto più facile che con i componenti montati.</li><li>Cabla come mostra il libretto in `pcb/`. Salda gli <b>zoccoli</b>, non i moduli: XIAO e driver devono poter uscire di nuovo, e il giorno che uno dei due si guasta non vuoi un saldatore vicino al telescopio.</li><li>Tieni bassi i componenti alti. Fra la basetta e il tetto del vano ci sono 50,5 mm di spazio, e non uno di più.</li><li><b>Attenzione:</b> Finisci tutta la basetta adesso e provala sul banco, alimentata dalla USB, prima di metterla nella macchina. Finché è sul tavolo arrivi dappertutto; dopo, quasi da nessuna parte.</li></ul></td>
</tr></table>

<table><tr>
<td width="55%"><img src="../img/09-02-board-in-its-panel.png" alt="Cala la basetta nel pannellino e avvitala" width="300"></td>
<td valign="top"><h3>Passo 2 — Cala la basetta nel pannellino e avvitala</h3><ul><li>Avvita la basetta <b>prima</b> di montare XIAO e driver: la <b>M2,5 × 6</b> dal lato della testata sta sotto lo XIAO, e con il modulo al suo posto non ci arrivi più.</li><li>La basetta <b>entra dall&#x27;alto</b>, fra le due guide lisce che la mettono in squadra, e si appoggia sulle tre colonnine in cui hai piantato gli inserti al capitolo 2.</li><li>Due viti svasate <b>M2 × 6</b> dal lato largo, nei due fori stampati; una <b>M2,5 × 6</b> dal lato della testata, nel foro che hai allargato a Ø2,7 mm, con la chiave a brugola da 2 mm. Non sono intercambiabili.</li><li><b>Attenzione:</b> Le guide mettono in squadra la basetta, non la tengono giù: non forzarla di lato sotto di loro. Un pannellino precedente aveva un labbro che copriva il bordo della basetta, e si è rotto.</li></ul></td>
</tr></table>

<table><tr>
<td width="55%"><img src="../img/09-03-board-in-its-panel.png" alt="Innesta lo XIAO e il driver" width="300"></td>
<td valign="top"><h3>Passo 3 — Innesta lo XIAO e il driver</h3><ul><li>Lo XIAO ESP32-S3 entra nelle sue due file di zoccoli, con la porta USB verso il lato della testata.</li><li>Il driver TMC2208 entra nel suo zoccolo, in piedi.</li><li><b>Attenzione:</b> Prima di spingerli a fondo, controlla l&#x27;orientamento di tutti e due sul libretto. Un driver montato al contrario è l&#x27;unico errore, qui, che brucia qualcosa.</li></ul></td>
</tr></table>
