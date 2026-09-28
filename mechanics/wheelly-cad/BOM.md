<!--
SPDX-FileCopyrightText: 2026 Matteo Beretta
SPDX-License-Identifier: CC-BY-4.0
-->

# Distinta della parte meccanica

**Questo file e' GENERATO** da `src/bom_mechanics.py` a ogni build: non si
modifica a mano, perche' la modifica sparisce al build dopo. Quello che c'e'
scritto discende dal modello - la massa dal solido, la quantita' dal conteggio
dei pezzi nell'assieme, la lunghezza di una vite dal suo gambo.

La distinta di TUTTO, meccanica ed elettronica, in inglese, e' quella
globale: [`../../BOM.md`](../../BOM.md), generata anche lei. Le ragioni
dei componenti elettronici stanno in [`../../pcb/BOM.md`](../../pcb/BOM.md).

## Pezzi da stampare

| pezzo | materiale | q.ta | massa | giacitura |
|---|---|---|---|---|
| box collar | ASA | 1 | 124.9 g | sportello dell'elettronica, o la faccia del GX12, sul piatto: il piatto lo misura bed.py |
| arm | ASA | 1 | 14.5 g | faccia superiore sul piatto: corpo e piastra del motore finiscono tutti e due a Z_top_arm, e la linguetta della molla cresce verso l'alto |
| clutch hub | ASA | 1 | 11.8 g | asse verticale, faccia del collare sul piatto |
| clutch tyre | TPU 87A-95A | 1 | 1.7 g | costampato col mozzo |
| sensor bracket | ASA | 1 | 10.4 g |  |
| sensor cover | ASA | 1 | 3.2 g |  |
| board panel | ASA | 1 | 9.9 g | faccia esterna sul piatto |
| spring cup | ASA | 1 | 0.3 g |  |
| grip cover | ASA | 1 | 11.7 g | capovolto, faccia superiore sul piatto: porta la piastra sopra il motore, e le teste delle viti zigrinate appoggiano sulle linguette; il generatore e check_grip lo stampano così |
| hatch cover | ASA | 1 | 5.2 g | faccia esterna sul piatto: e' quella in vista, a filo del fondo; le orecchie salgono dritte e gli svasi si aprono sul piatto |
| pivot washer | ASA | 1 | 0.2 g |  |
| magnet spacer | ASA | 4 | 0.6 g | quattro copie: e' un pezzo che si perde |
| front gasket | TPU 87A-95A | 1 | 0.7 g | piatta sul letto, labbro in su (costampata col pezzo, se hai il multimateriale) |
| rear gasket | TPU 87A-95A | 1 | 0.7 g | piatta sul letto, labbro in su (costampata col pezzo, se hai il multimateriale) |

In tutto: **193 g** di ASA, **3 g** di TPU 87A-95A.

## Da comprare

| pezzo | q.ta | quota | dove |
|---|---|---|---|
| bearing_F695ZZ | 2 | F695ZZ flangiato, 5 x 13 x 4 | |
| grub_M3_clutch | 1 | M3 x 10, GRANO a brugola senza testa (dalla fresata dell'albero all'inserto ci sono 10.0) | |
| grub_M4_preload | 1 | M4 x 14, GRANO a brugola senza testa (dal dorso dello scodellino all'imbocco del bosso ci sono 12.1) | |
| insert_M25_cover | 2 | inserto a caldo M2,5, Ø4.6 x 4.0 **M** | |
| insert_M25_head_post | 1 | inserto a caldo M2,5, Ø4.6 x 4.0 **M** | |
| insert_M2_post | 2 | inserto a caldo M2, Ø3.6 x 4.0 **M** | |
| insert_M3_cover | 2 | inserto a caldo M3, Ø5.0 x 3.0 **M** | |
| insert_M3_grub | 1 | inserto a caldo M3, Ø5.0 x 3.0 **M** | |
| insert_M3_hatch | 2 | inserto a caldo M3, Ø5.0 x 3.0 **M** | |
| insert_M3_panel | 3 | inserto a caldo M3, Ø5.0 x 3.0 **M** | |
| insert_M3_pivot | 1 | inserto a caldo M3, Ø5.0 x 3.0 **M** | |
| insert_M4_preload | 1 | inserto a caldo M4, Ø6.3 x 8.1 **M** | |
| magnet_AS5600 | 1 | Ø8 x 1, **DIAMETRALMENTE MAGNETIZZATO** | |
| motor_NEMA14 | 1 | NEMA 14 14HS10-0404S | |
| preload_spring | 1 | molla di compressione, filo 0.9, Ø esterno 6.7, libera 13.5, montata 11.1, 5.7 N/mm (quella del prototipo viene da una molletta per i panni) | |
| screw_M25_board | 1 | M2,5 x 6, testa brugola (servono 5.5 sotto testa) | |
| screw_M25_cover | 2 | M2,5 x 8, testa brugola (servono 7.0 sotto testa) | |
| screw_M2_board | 2 | M2 x 6, testa svasata (servono 5.5 sotto testa) | |
| screw_M2_module | 2 | M2 x 4, testa svasata (servono 4.0 sotto testa) | |
| screw_M3_collar | 2 | M3 x 14, testa brugola (servono 12.4 sotto testa) | |
| screw_M3_cover | 2 | M3 x 6, testa brugola (servono 6.0 sotto testa) | |
| screw_M3_hatch | 2 | M3 x 8, testa svasata (servono 8.0 sotto testa) | |
| screw_M3_motor | 4 | M3 x 8, testa brugola (servono 8.0 sotto testa) | |
| screw_M3_panel | 3 | M3 x 8, testa svasata (servono 8.0 sotto testa) | |
| screw_M3_pivot | 1 | M3 x 20, testa brugola (servono 20.0 sotto testa) | |

Le quote marcate **M** sono misurate col calibro su un esemplare vero. Le
lunghezze delle viti sono la prima taglia di catalogo che copre quello che
serve sotto la testa, misurato sul modello.
