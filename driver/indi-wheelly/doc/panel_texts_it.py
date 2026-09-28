# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""The Italian catalogue of the panel guide (panel_texts.py): key -> (fingerprint of
the English it translates, Italian text). Checked by panel_language.problems()."""
CATALOGUE = {
    'CONNECTION/what': ('debd610d',
        "Collega il driver alla ruota e lo scollega. Su Connect il driver apre la porta "
        "seriale, manda 'version' e accetta il dispositivo solo se risponde come una Wheelly "
        "che parla il protocollo 2. Poi legge dalla ruota il numero di posizioni, i nomi dei "
        "filtri, gli angoli di taratura, le tolleranze, la corrente di marcia e quella di "
        "tenuta, il verso di rotazione e il modo del LED, e solo allora mostra le proprietà "
        "Wheelly. Tutte le proprietà proprie di Wheelly esistono solo finché si è collegati."),
    'CONNECTION/elements/CONNECT': ('f2b20459',
        "Apre la porta, riconosce la ruota e ne mostra le proprietà."),
    'CONNECTION/elements/DISCONNECT': ('ad8bd238',
        "Chiude la porta; tutte le proprietà Wheelly spariscono e il file del registro dei "
        "movimenti viene chiuso."),
    'CONNECTION/notes/1': ('5863a3bc',
        "La ruota si riconosce da quello che risponde, non dal nome della porta: il firmware "
        "comunica un numero di serie ricavato dal chip, e il driver lo ricorda nella "
        "configurazione del profilo al primo collegamento (log: «D'ora in poi questo profilo "
        "cerca la ruota col seriale ...»)."),
    'CONNECTION/notes/2': ('c4253745',
        "Con due ruote Wheelly collegate, ogni profilo cerca prima il proprio numero di serie; una "
        "Wheelly diversa viene saltata (log: «Questa è una Wheelly diversa ...»). Se la sua ruota "
        "non è su nessuna porta, il driver si collega alla prima Wheelly che trova, lo dice nel "
        "log, e da lì in poi adotta quel numero di serie."),
    'CONNECTION/notes/3': ('15a8fa5e',
        "La ricerca sulle altre porte la fa l'Auto Search di INDI (DEVICE_AUTO_SEARCH); con Auto "
        "Search spento si prova solo la porta in DEVICE_PORT."),
    'CONNECTION/notes/4': ('9d793d18',
        "Messaggi nel log quando non riesce: «Il dispositivo su questa porta non ha risposto "
        "come una ruota Wheelly. Controlla la porta.» oppure «Questo firmware parla il "
        "protocollo X, il driver parla il Y. Aggiorna uno dei due.» Il protocollo 2 non ha il "
        "ritocco di rotazione: un firmware del protocollo 1 punta all'angolo + il ritocco, "
        "quindi viene rifiutato invece di essere guidato a metà - si ricarica il firmware "
        "della ruota e si installa il driver insieme."),
    'CONNECTION/notes/5': ('e815da94',
        "Se il canale seriale cade mentre si è collegati (errore di lettura o cavo staccato), il "
        "log dice «La ruota non risponde.» e il collegamento va in Alert e si scollega. Un singolo "
        "comando che non riceve risposta entro 3 s viene scritto nel log ma non fa scollegare."),
    'FILTER_SLOT/what': ('e8a7ecfd',
        "La posizione del filtro standard di INDI: la posizione su cui sta la ruota, e il "
        "posto dove chiederne un'altra. Ekos scrive qui quando una sequenza cambia filtro. Il "
        "driver manda 'go <slot>' e la ruota fa il resto da sola: gira nel verso che "
        "WHEELLY_DIRECTION consente (di base la via più corta, oppure un verso solo), tiene "
        "il motore fermo alimentato per 300 ms (WHEELLY_HOLD) mentre il disco si assesta, "
        "legge il magnete, confronta l'errore residuo con le tolleranze e ritenta se serve. "
        "Il driver riferisce soltanto il verdetto."),
    'FILTER_SLOT/elements/FILTER_SLOT_VALUE': ('122f0cef',
        "Numero della posizione, da 1 al numero di posizioni che la ruota dichiara."),
    'FILTER_SLOT/notes/1': ('91e40efb',
        "Intervallo da 1 al numero di posizioni che la ruota dichiara al collegamento (5 su una "
        "ruota di fabbrica, al massimo 12); passo 1."),
    'FILTER_SLOT/notes/2': ('57d53dc2',
        "Busy mentre la ruota si muove. Ok quando è arrivata entro la tolleranza Buona (log: "
        "«Posizione N raggiunta, errore residuo X gradi.»)."),
    'FILTER_SLOT/notes/3': ('cac82331',
        "Arrivata fra la tolleranza Buona e quella d'Allarme: ancora Ok, quindi la sequenza va "
        "avanti, con un avviso nel log («Posizione N raggiunta ma fuori di X gradi, oltre la "
        "tolleranza buona. La ripresa prosegue.»)."),
    'FILTER_SLOT/notes/4': ('231fa621',
        "Ancora oltre la tolleranza d'Allarme dopo tutti i ritentativi: Alert, che fa fermare "
        "subito la sequenza a Ekos (log: «Posizione N NON raggiunta ... La ripresa viene fermata, "
        "così non si scatta a ruota fuori posto.»)."),
    'FILTER_SLOT/notes/5': ('4d0e19fb',
        "Dopo ogni posizione non raggiunta, e dopo il limite di tempo qui sotto, una "
        "seconda riga del log suggerisce la prima cosa da controllare: «Se il motore si "
        "blocca o la frizione slitta, controlla prima di tutto che il fermo della ruota "
        "(lo scatto a molla) sia stato tolto ...» - il motore non riesce a uscire dalle "
        "sue tacche, e la guida di montaggio lo toglie nel capitolo 10, Il corpo della "
        "ruota."),
    'FILTER_SLOT/notes/6': ('c0ae1ada',
        "Limiti di tempo: la ruota ricava da sé il tetto di tempo di un movimento dalla "
        "velocità del motore, dall'accelerazione, dai ritentativi, dal verso di rotazione e "
        "dalla tenuta dopo l'arrivo, e oltre quel tetto smette di ritentare; il driver "
        "dichiara Alert da sé se la ruota non ha finito 3 s dopo quel tetto (log: «La ruota "
        "non ha finito entro N secondi. La ripresa viene fermata.»). Con un firmware che non "
        "dichiara il suo tetto il limite del driver è 28 s."),
    'FILTER_SLOT/notes/7': ('d645b33a',
        "Ekos rinuncia per conto suo a un cambio filtro dopo 30 s: quando il tetto della ruota va"
        " oltre, il log lo dice (vedi WHEELLY_DIRECTION)."),
    'FILTER_SLOT/notes/8': ('107ecde4',
        "Un movimento viene rifiutato subito, con Alert, se il sensore non risponde o non vede il"
        " magnete; il motivo è nel log."),
    'FILTER_SLOT/notes/9': ('9e9e8b56',
        "La posizione è assoluta (encoder magnetico): niente ricerca dello zero. Se la ruota "
        "viene girata a mano o da un altro programma, questo valore la segue all'interrogazione "
        "successiva."),
    'FILTER_SLOT/notes/10': ('2642abf3',
        "Il tempo massimo di Ekos per il cambio filtro conta dalla richiesta; la fine di un "
        "movimento si nota all'interrogazione successiva, quindi un POLLING_PERIOD lungo ritarda "
        "l'Ok."),
    'FILTER_NAME/what': ('6a8262d1',
        "I nomi dei filtri standard di INDI, uno per posizione. I nomi sono conservati nella ruota "
        "stessa: al collegamento il driver li legge dalla ruota, così una ruota spostata su un "
        "altro computer si presenta coi suoi nomi. Quando cambi un nome, il driver lo scrive "
        "nella ruota. Ekos usa questi nomi nella parola chiave FITS FILTER e nei nomi di file e "
        "cartelle, ed è per questo che la regola è severa."),
    'FILTER_NAME/elements/FILTER_SLOT_NAME_1': ('ff087606',
        "Nome della posizione 1."),
    'FILTER_NAME/elements/FILTER_SLOT_NAME_2': ('f1cde93b',
        "Nome della posizione 2."),
    'FILTER_NAME/elements/FILTER_SLOT_NAME_3': ('28c56452',
        "Nome della posizione 3."),
    'FILTER_NAME/elements/FILTER_SLOT_NAME_4': ('d7508a53',
        "Nome della posizione 4."),
    'FILTER_NAME/elements/FILTER_SLOT_NAME_5': ('700ce155',
        "Nome della posizione 5."),
    'FILTER_NAME/notes/1': ('17b6fd55',
        "Ammessi: lettere non accentate, cifre, _ - e . ; da 1 a 32 caratteri; il primo e "
        "l'ultimo devono essere una lettera o una cifra. I nomi di dispositivo di Windows (CON, "
        "PRN, AUX, NUL, COM1-COM9, LPT1-LPT9, anche con un'estensione) vengono rifiutati. Due "
        "posizioni non possono avere lo stesso nome, senza distinguere maiuscole e minuscole."),
    'FILTER_NAME/notes/2': ('7c95acdd',
        "Una posizione senza filtro: lascia vuoto il suo campo. Il driver le dà il nome Empty_ "
        "seguito dal numero della posizione (Empty_5), che è unico e valido, così più posizioni "
        "possono essere vuote insieme; il nome è lo stesso in ogni lingua, perché è conservato "
        "nella ruota e scritto nell'intestazione FITS. Il campo e l'elenco dei filtri di Ekos "
        "mostrano poi quel nome, e il log lo dice."),
    'FILTER_NAME/notes/3': ('cb180e29',
        "Un nome rifiutato non viene corretto di nascosto: la proprietà diventa rossa (Alert), il "
        "campo torna al nome di prima, e il log dice quale posizione, quale nome, cosa non va e, "
        "quando può, un nome che sarebbe accettato, seguiti dai caratteri ammessi. Quella riga è "
        "sempre la più recente del log, quella in cima in KStars; quando è troppo lunga per un "
        "solo messaggio INDI, i caratteri ammessi vanno nella riga subito prima. FILTER_SLOT non "
        "viene toccata, così un errore di battitura non ferma mai una sequenza."),
    'FILTER_NAME/notes/4': ('9af4898c',
        "Il numero dei campi segue il numero di posizioni che la ruota dichiara; la cattura del "
        "pannello mostra i cinque di una ruota di fabbrica."),
    'FILTER_NAME/notes/5': ('f8039908',
        "Nomi di fabbrica: Lum, Red, Green, Blue, Ha (Filter1, Filter2 ... su una ruota con un "
        "numero diverso di posizioni)."),
    'FILTER_NAME/notes/6': ('b6040427',
        "Un nome nuovo resta nella ruota solo fino allo spegnimento, a meno che tu non prema "
        "«Salva nella ruota» (WHEELLY_SAVE)."),
    'FILTER_NAME/notes/7': ('64a82554',
        "I nomi vengono sempre dalla ruota, a ogni collegamento - anche quando la configurazione "
        "INDI del computer ha dei nomi salvati da una sessione precedente: una ruota rinominata "
        "su un altro computer mostra i suoi."),
    'WHEELLY_POSITION/what': ('2245f42b',
        "Dove si trova davvero la ruota, letto dal sensore magnetico, aggiornato a ogni "
        "interrogazione (ogni POLLING_PERIOD, 250 ms di base). Guardalo mentre centri una "
        "posizione, o quando un cambio filtro è finito con un avviso o un fallimento: dice di "
        "quanto la ruota si è fermata fuori posto e quanti ritentativi ci sono voluti."),
    'WHEELLY_POSITION/elements/ANGLE': ('23355654',
        "Angolo del disco letto dal sensore AS5600, in gradi, da 0 a 360."),
    'WHEELLY_POSITION/elements/ERROR': ('b93909d6',
        "Errore residuo in gradi, col segno: angolo misurato meno l'angolo obiettivo (l'angolo "
        "di taratura) dell'ultima posizione chiesta, dalla parte più corta. A riposo continua "
        "ad aggiornarsi, quindi mostra anche una ruota che deriva."),
    'WHEELLY_POSITION/elements/RETRIES': ('6fc5f01a',
        "Ritentativi usati dalla ruota nell'ultimo posizionamento (0 = raggiunta al primo "
        "tentativo)."),
    'WHEELLY_POSITION/notes/1': ('862a6bf7',
        "Sola lettura. Limiti di visualizzazione: angolo 0-360, errore da -180 a +180, "
        "ritentativi 0-99."),
    'WHEELLY_POSITION/notes/2': ('e43e78b5',
        "Il verdetto (arrivata, avviso, fallita) lo dà il firmware, non questa proprietà: vedi "
        "FILTER_SLOT e il log."),
    'WHEELLY_POSITION/notes/3': ('4339938b',
        "Se la ruota si sposta da sola a riposo oltre la tolleranza d'Allarme, il log lo dice una "
        "volta per episodio e consiglia la tenuta a riposo (WHEELLY_HOLD) o, se è già accesa, di "
        "guardare il precarico della molla della frizione."),
    'WHEELLY_SENSOR/what': ('e3d18ff8',
        "Lo stato del sensore magnetico AS5600, aggiornato a ogni interrogazione. È "
        "strumentazione da tenere d'occhio: un filo del sensore che si allenta, o il ponticello "
        "di alimentazione del modulo del sensore che si solleva, si vede qui prima che in un "
        "fotogramma rovinato. La proprietà diventa rossa (Alert) quando il magnete non viene "
        "rilevato."),
    'WHEELLY_SENSOR/elements/AGC': ('a54d078c',
        "Guadagno automatico del sensore, da 0 a 255 come viene mostrato. Col magnete che usa "
        "Wheelly a 3,3 V resta a fondo scala (128) a qualunque traferro, quindi si mostra per la "
        "diagnosi ma non è il criterio."),
    'WHEELLY_SENSOR/elements/MAGNITUDE': ('a5643431',
        "Intensità del campo magnetico vista dal sensore, in conteggi, da 0 a 4095. È questo il "
        "criterio: sotto 350 il magnete è troppo lontano o fuori centro. La sua variazione su un "
        "giro completo misura quanto bene è centrato il magnete (vedi la spazzolata del "
        "magnete)."),
    'WHEELLY_SENSOR/elements/MD': ('4ebf0365',
        "1 = magnete rilevato, 0 = non rilevato (la proprietà allora va in Alert)."),
    'WHEELLY_SENSOR/elements/ML': ('c87aae80',
        "Segnale di campo troppo debole (1 = debole), come lo riporta l'AS5600. Col magnete di "
        "riferimento a 3,3 V di solito vale 1, perché il guadagno del chip resta a fondo scala; è "
        "anche l'aspetto di un ponticello VDD5V-VDD3V3 interrotto sul modulo, quindi va letto "
        "insieme alla magnitude."),
    'WHEELLY_SENSOR/elements/MH': ('02d75c58',
        "Segnale di campo troppo forte (1 = forte), come lo riporta l'AS5600: il magnete è troppo "
        "vicino al chip."),
    'WHEELLY_SENSOR/notes/1': ('65834d39',
        "Sola lettura."),
    'WHEELLY_SENSOR/notes/2': ('36987b7d',
        "Se il sensore non risponde affatto, Guadagno e Magnitude valgono 0 e MD vale 0."),
    'WHEELLY_SENSOR/notes/3': ('e4be8e7f',
        "Quando il magnete sparisce il log mostra un errore: «Il sensore non rileva più il "
        "magnete. È un guaio serio: controlla il cablaggio del sensore prima di continuare a "
        "riprendere.» Una volta per episodio: se il magnete torna e poi si perde di nuovo, lo "
        "ridice."),
    'WHEELLY_SENSOR/notes/4': ('cc609a5a',
        "Per un controllo completo del sensore e del driver del motore usa «Controllo "
        "dell'hardware» (WHEELLY_DIAG)."),
    'WHEELLY_SLOTS/what': ('134a40a4',
        "Quante posizioni per i filtri ha la ruota. Il numero sta nella ruota, e il driver lo "
        "legge a ogni collegamento: impostalo qui una volta, quando la ruota viene costruita. "
        "Cambiarlo fa ripartire la taratura da angoli equidistanti e nomi di filtro generici, e"
        " il pannello si ridisegna subito col nuovo numero di posizioni, nomi e angoli, e i "
        "pulsanti di passo di una posizione lo seguono (360 diviso il numero)."),
    'WHEELLY_SLOTS/elements/COUNT': ('1b31af2f',
        "Il numero di posizioni per i filtri della ruota."),
    'WHEELLY_SLOTS/notes/1': ('e038e661',
        "Dopo averlo cambiato: insegna ogni posizione (i passi, poi Set sulla sua riga degli "
        "angoli), dai i nomi ai filtri, poi premi «Salva nella ruota». Il log lo ricorda."),
    'WHEELLY_SLOTS/notes/2': ('6832b726',
        "Nella memoria permanente della ruota non si scrive niente fino a «Salva nella ruota»: "
        "spegnendo la ruota tornano il numero e la taratura di prima, quindi un clic sbagliato "
        "non costa niente."),
    'WHEELLY_SLOTS/notes/3': ('cf17e406',
        "Rifiutato mentre la ruota si muove; il motivo è nel log."),
    'WHEELLY_ANGLE_1/what': ('947bcb50',
        "Gli angoli di taratura, una riga per posizione, ognuna col suo Set: questa è quella "
        "della posizione 1, e le righe delle altre posizioni funzionano allo stesso modo. Il "
        "numero è l'angolo di taratura, in gradi, a cui quel filtro sta nel cammino della luce "
        "e dove la ruota va per portarcelo, come è conservato nella ruota. La posizione su cui "
        "sta la ruota è segnata con una freccia, «▶ 1». PER TARARE UNA POSIZIONE: sceglila in "
        "FILTER_SLOT; centra il filtro coi passi (WHEELLY_JOG_DOWN e WHEELLY_JOG_UP) - dopo "
        "ogni passo la sua riga mostra l'angolo in cui la ruota si trova adesso, con un "
        "asterisco, «▶ 1 *», che vuol dire non ancora tarato; premi Set su quella riga per "
        "tararla; fai lo stesso per ogni posizione, poi premi «Salva nella ruota»."),
    'WHEELLY_ANGLE_1/elements/ANGLE': ('4b4de6dd',
        "Angolo di taratura della posizione, in gradi (da 0 a 360); dopo un passo, sulla "
        "posizione corrente, l'angolo in cui la ruota si trova adesso."),
    'WHEELLY_ANGLE_1/notes/1': ('15bf06ea',
        "L'asterisco, «▶ 1 *»: la riga mostra dove si trova la ruota dopo i passi, NON quello "
        "che la posizione ha imparato. Set col valore così com'è lo conferma: la posizione "
        "prende quell'angolo e la ruota non si muove, perché è già lì (log: «La posizione 1 "
        "vuol dire d'ora in poi l'angolo in cui la ruota si trova adesso ...»). Se lasci la "
        "posizione senza premere Set - scegliendo un altro filtro, facendo la spazzolata, o "
        "premendo Set su un'altra riga - la riga torna all'angolo di taratura, senza asterisco:"
        " i passi non hanno insegnato niente."),
    'WHEELLY_ANGLE_1/notes/2': ('617da091',
        "Set su una riga con un valore diverso - scritto a mano, su qualunque riga, compresa "
        "quella con l'asterisco: la posizione prende il nuovo angolo e la ruota ci va subito, "
        "come se la posizione fosse stata scelta in FILTER_SLOT, che va in Busy e poi in Ok o "
        "Alert. È così che si centra un filtro coi numeri, e che si corregge la taratura "
        "guardando una stella o un flat. Set su una riga col valore invariato porta soltanto la"
        " ruota a quella posizione."),
    'WHEELLY_ANGLE_1/notes/3': ('29f7528f',
        "Ogni cambiamento è scritto nel log - «Posizione 2: 122.87° → 123.10°.» - e, col "
        "registro dei movimenti acceso, come riga di wheelly_movements.csv con esito angle-"
        "taught (un asterisco confermato) o angle-set (un valore scritto): il nuovo angolo "
        "nella colonna target, il vecchio nella colonna angle, la differenza nella colonna "
        "error. È la storia delle correzioni: un angolo che continua a spostarsi notte dopo "
        "notte vuol dire che qualcosa nella meccanica si muove."),
    'WHEELLY_ANGLE_1/notes/4': ('577960f9',
        "Restano nella ruota solo fino allo spegnimento: premi «Salva nella ruota» per tenerli."
        " Riavviare la ruota senza salvare riporta l'ultima taratura salvata, ed è il modo di "
        "annullare un esperimento."),
    'WHEELLY_ANGLE_1/notes/5': ('d8238b91',
        "Un valore fuori da 0-360 viene rifiutato dalla ruota: la riga va in Alert, resta il "
        "valore vecchio, e il log dice perché. Rifiutato anche mentre la ruota si muove."),
    'WHEELLY_ANGLE_1/notes/6': ('05df11c7',
        "Se la ruota viene girata a mano la sua riga non la segue (segue solo i passi): per "
        "insegnare il punto in cui l'ha lasciata la mano, scrivi nella riga l'angolo mostrato "
        "in WHEELLY_POSITION e premi Set."),
    'WHEELLY_ANGLE_1/notes/7': ('beafa5ca',
        "La freccia resta sulla posizione mentre la ruota viene spostata a passi fuori da lì "
        "per centrarla. INDI non sa colorare un campo, e un'etichetta arriva al client solo "
        "quando la proprietà viene definita, quindi il driver definisce di nuovo le righe - e "
        "con loro le proprietà che le seguono in questa scheda, che altrimenti finirebbero "
        "sopra - solo alla fine di un passo, a un cambio di posizione e a una taratura, mai "
        "mentre la ruota viene soltanto osservata."),
    'WHEELLY_ANGLE_1/notes/8': ('26e96546',
        "Una ruota mai tarata ha le posizioni equidistanti (0, 72, 144, 216 e 288 gradi su una "
        "ruota a cinque posizioni): si può usare, ma non è una taratura."),
    'WHEELLY_ANGLE_1/notes/9': ('a78c201f',
        "Una proprietà per posizione, non un solo WHEELLY_ANGLES con un unico Set per tutti e "
        "un pulsante a parte, «Salva posizione» (WHEELLY_TEACH): il Set sulla riga con "
        "l'asterisco fa quello che farebbe quel pulsante. Una ruota salvata da un firmware "
        "precedente con un «Ritocco di rotazione» per posizione trova i ritocchi sommati ai "
        "suoi angoli, una volta, alla prima accensione col firmware attuale. Questi angoli "
        "sono segnati anche sul grafico della spazzolata del magnete."),
    'WHEELLY_ANGLE_2/what': ('958734a5',
        "L'angolo di taratura della posizione 2, col suo Set: funziona come la riga della "
        "posizione 1 (WHEELLY_ANGLE_1), che spiega come."),
    'WHEELLY_ANGLE_2/elements/ANGLE': ('4b4de6dd',
        "Angolo di taratura della posizione, in gradi (da 0 a 360); dopo un passo, sulla "
        "posizione corrente, l'angolo in cui la ruota si trova adesso."),
    'WHEELLY_ANGLE_3/what': ('2d34e8e8',
        "L'angolo di taratura della posizione 3, col suo Set: funziona come la riga della "
        "posizione 1 (WHEELLY_ANGLE_1), che spiega come."),
    'WHEELLY_ANGLE_3/elements/ANGLE': ('4b4de6dd',
        "Angolo di taratura della posizione, in gradi (da 0 a 360); dopo un passo, sulla "
        "posizione corrente, l'angolo in cui la ruota si trova adesso."),
    'WHEELLY_ANGLE_4/what': ('20db4392',
        "L'angolo di taratura della posizione 4, col suo Set: funziona come la riga della "
        "posizione 1 (WHEELLY_ANGLE_1), che spiega come."),
    'WHEELLY_ANGLE_4/elements/ANGLE': ('4b4de6dd',
        "Angolo di taratura della posizione, in gradi (da 0 a 360); dopo un passo, sulla "
        "posizione corrente, l'angolo in cui la ruota si trova adesso."),
    'WHEELLY_ANGLE_5/what': ('2a56cbb4',
        "L'angolo di taratura della posizione 5, col suo Set: funziona come la riga della "
        "posizione 1 (WHEELLY_ANGLE_1), che spiega come."),
    'WHEELLY_ANGLE_5/elements/ANGLE': ('4b4de6dd',
        "Angolo di taratura della posizione, in gradi (da 0 a 360); dopo un passo, sulla "
        "posizione corrente, l'angolo in cui la ruota si trova adesso."),
    'WHEELLY_JOG_DOWN/what': ('ba0b34af',
        "Sposta la ruota indietro di un passo, verso angoli decrescenti, per centrare il filtro"
        " della posizione corrente; WHEELLY_JOG_UP va dall'altra parte, e il Set sulla riga "
        "della posizione, che segue i passi, tiene il risultato. Il primo pulsante è una "
        "posizione, 360 gradi diviso il numero di posizioni (72 su una ruota a cinque "
        "posizioni), e porta al filtro vicino; gli altri sono 10, 1 e 0,1 gradi. Ogni passo è "
        "un movimento VERSO l'angolo letto adesso meno il passo, fatto dalla ruota ad anello "
        "chiuso - gli stessi tratti di un cambio filtro, col gioco della gomma della frizione "
        "recuperato - e non un conto di passi del motore: la gomma si mangia circa 0,6 gradi "
        "prima che il disco si muova. Ogni pulsante agisce una volta e torna su."),
    'WHEELLY_JOG_DOWN/elements/JOG_M_PITCH': ('05ee182b',
        "Sposta la ruota di una posizione (360 / posizioni) verso angoli decrescenti."),
    'WHEELLY_JOG_DOWN/elements/JOG_M10': ('c9c852ed',
        "Sposta la ruota di 10 gradi verso angoli decrescenti."),
    'WHEELLY_JOG_DOWN/elements/JOG_M1': ('7e83f0c5',
        "Sposta la ruota di 1 grado verso angoli decrescenti."),
    'WHEELLY_JOG_DOWN/elements/JOG_M0_1': ('77d933d5',
        "Sposta la ruota di 0,1 gradi verso angoli decrescenti."),
    'WHEELLY_JOG_DOWN/notes/1': ('c8b3d46e',
        "Busy mentre la ruota si muove, poi Ok, e il log dice dov'è: «La ruota è a A°, a "
        "E° da dove chiedeva il passo.» Alert se non ci è arrivata (log: «La ruota non è "
        "arrivata dove chiedeva il passo ...», seguita dalla riga che suggerisce di "
        "controllare che il fermo della ruota sia stato tolto), o se la ruota ha "
        "rifiutato il passo."),
    'WHEELLY_JOG_DOWN/notes/2': ('bacafba1',
        "Un passo che non ha coperto almeno metà di sé stesso è un fallimento, mai un avviso: "
        "la fascia di allarme di un cambio filtro è più larga dei passi piccoli, quindi "
        "altrimenti un passo di 0,5 gradi che non si è mosso affatto risulterebbe fatto."),
    'WHEELLY_JOG_DOWN/notes/3': ('cd7bc4fe',
        "Un passo non è un cambio filtro: FILTER_SLOT resta com'è, e il passo va sempre nel suo"
        " verso, qualunque cosa dica WHEELLY_DIRECTION - in un verso solo, un passo al "
        "contrario farebbe tutto il giro della ruota. Su una meccanica più dura in un verso che"
        " nell'altro, un passo nel verso duro può bloccarsi."),
    'WHEELLY_JOG_DOWN/notes/4': ('f4753ed2',
        "Il passo di una posizione arriva sul filtro successivo su una ruota con gli angoli "
        "equidistanti; l'etichetta segue il numero di posizioni. Su una ruota a due posizioni "
        "il passo è mezzo giro, e va nel verso che dice il suo pulsante."),
    'WHEELLY_JOG_DOWN/notes/5': ('2b72bb1b',
        "Rifiutato mentre la ruota si muove (log: «Non si può spostare la ruota di un passo "
        "mentre si muove ...»)."),
    'WHEELLY_JOG_DOWN/notes/6': ('1dd7cd7a',
        "Due righe e non una: KStars mostra più di quattro pulsanti esclusivi come un menu a "
        "tendina. Non c'è un passo di 0,05 gradi: è sotto quello che il sensore sa leggere (un"
        " conteggio vale 0,088 gradi), quindi un passo di 0,05 che non si è mosso non si "
        "distinguerebbe da uno che si è mosso."),
    'WHEELLY_JOG_UP/what': ('081acc98',
        "Sposta la ruota avanti di un passo, verso angoli crescenti: lo specchio di "
        "WHEELLY_JOG_DOWN, che spiega come funziona un passo."),
    'WHEELLY_JOG_UP/elements/JOG_P0_1': ('67400812',
        "Sposta la ruota di 0,1 gradi verso angoli crescenti."),
    'WHEELLY_JOG_UP/elements/JOG_P1': ('04aca78e',
        "Sposta la ruota di 1 grado verso angoli crescenti."),
    'WHEELLY_JOG_UP/elements/JOG_P10': ('b9cdd2d9',
        "Sposta la ruota di 10 gradi verso angoli crescenti."),
    'WHEELLY_JOG_UP/elements/JOG_P_PITCH': ('8e6e727c',
        "Sposta la ruota di una posizione (360 / posizioni) verso angoli crescenti."),
    'WHEELLY_JOG_UP/notes/1': ('3cf130c0',
        "Busy mentre la ruota si muove, poi Ok o Alert, come WHEELLY_JOG_DOWN."),
    'WHEELLY_SAVE/what': ('afd616e1',
        "Tutto quello che cambi nel pannello di taratura sta nella memoria di lavoro della "
        "ruota finché non premi «Salva nella ruota»; salvare è un atto voluto, così puoi "
        "sperimentare liberamente. Il pulsante agisce una volta e torna su. Lo stesso pulsante "
        "c'è anche in Options, sotto «Configurazione della ruota» (WHEELLY_CONFIG)."),
    'WHEELLY_SAVE/elements/SAVE': ('8b60ccb5',
        "Scrive nella memoria permanente della ruota tutto quello che contiene: numero di "
        "posizioni, angoli di taratura, nomi dei filtri, tolleranze, corrente di marcia e di "
        "tenuta, tenuta dopo l'arrivo, velocità, accelerazione, verso di rotazione e modo del "
        "LED. Log: «Taratura salvata nella ruota.»"),
    'WHEELLY_SAVE/notes/1': ('ab9eff15',
        "Ok quando la ruota ha salvato, Alert quando non ci è riuscita; il motivo è nel log "
        "(per esempio «La ruota non è riuscita a salvare nella sua memoria.»)."),
    'WHEELLY_SAVE/notes/2': ('0b9b90a5',
        "La posizione di un filtro si insegna col Set sulla sua riga degli angoli "
        "(WHEELLY_ANGLE_1 e le altre), quindi qui non c'è un pulsante «Ritara qui la "
        "posizione», e non ci sono ritocchi da azzerare."),
    'WHEELLY_TOLERANCE/what': ('5043fac3',
        "Quanto preciso deve essere un cambio filtro, e quanto ci prova la ruota. Dopo un "
        "movimento la ruota confronta l'errore residuo con due soglie: entro Buona è un "
        "successo; fra Buona e Allarme è un successo con un avviso nel log, e la ripresa "
        "prosegue; oltre Allarme ritenta, fino a Ritentativi massimi, e poi dichiara il "
        "fallimento, che ferma la sequenza di Ekos."),
    'WHEELLY_TOLERANCE/elements/GOOD': ('fda49b90',
        "Tolleranza Buona, in gradi: entro questa il movimento è un successo pieno. Di "
        "base 0.30."),
    'WHEELLY_TOLERANCE/elements/WARN': ('42bec25f',
        "Tolleranza d'Allarme, in gradi: oltre questa la ruota ritenta, e fallisce dopo "
        "l'ultimo ritentativo. Di base 0.80. È anche la fascia entro cui la ruota si "
        "dichiara su una posizione, e la soglia per segnalare una deriva a riposo."),
    'WHEELLY_TOLERANCE/elements/RETRIES': ('9c203ae8',
        "Numero massimo di ritentativi dopo il primo tentativo. Di base 3."),
    'WHEELLY_TOLERANCE/notes/1': ('c2a86956',
        "Limiti nel pannello: da 0.01 a 45 gradi (passo 0.01) per entrambe le tolleranze, da 0 a "
        "20 ritentativi (passo 1). La ruota pretende anche che Buona non sia più grande di "
        "Allarme; altrimenti rifiuta i tre valori, la proprietà va in Alert e il log spiega."),
    'WHEELLY_TOLERANCE/notes/2': ('24671a87',
        "I ritentativi hanno anche un limite di tempo: la ruota smette di ritentare dopo 25 s "
        "dall'inizio del movimento."),
    'WHEELLY_TOLERANCE/notes/3': ('881f18e5',
        "Restano nella ruota fino allo spegnimento; premi «Salva nella ruota» per tenerle."),
    'WHEELLY_TOLERANCE/notes/4': ('0122b52d',
        "Salvate anche nella configurazione INDI, ma al collegamento i valori mostrati sono "
        "quelli letti dalla ruota; la copia salvata viene mandata alla ruota solo quando si "
        "carica la configurazione (CONFIG_PROCESS, Load)."),
    'WHEELLY_TOLERANCE/notes/5': ('7ec42e1d',
        "Per avere un'idea: un conteggio dell'AS5600 vale 0,088 gradi; la ruota fa la media di 8 "
        "letture per ogni misura. Un grado di disco sposta un filtro di circa 0,9 mm su un "
        "cerchio dei filtri di circa 50 mm di raggio (una stima). I valori di base tengono conto "
        "dell'ultimo mezzo grado, fino a un grado, che assorbe la gomma in TPU della trasmissione; "
        "valori più stretti si possono provare quando il registro dei movimenti mostra gli errori "
        "veri."),
    'WHEELLY_DIAG/what': ('e2cf7b51',
        "Fa alla ruota una domanda sola: sta parlando davvero col suo sensore e col suo driver del "
        "motore? La risposta va nel riquadro del log. È la prima cosa da premere quando la ruota "
        "fa qualcosa di inatteso: un filo allentato sul driver del motore si presenta come «il "
        "motore non gira» e ti manda a cercare nei posti sbagliati."),
    'WHEELLY_DIAG/elements/RUN': ('be55cbb0',
        "Manda il controllo; la risposta compare nel log."),
    'WHEELLY_DIAG/notes/1': ('598a0b50',
        "Righe del log, in ordine: «Chiedo alla ruota se sta parlando davvero col suo sensore e "
        "col suo driver del motore:», poi 'AS5600 at 0x36: responding' con una riga "
        "'STATUS md=... AGC=... MAG=...', oppure 'AS5600 at 0x36: SILENT' con il consiglio di "
        "controllare il cablaggio e il ponticello VDD5V-VDD3V3 sul modulo."),
    'WHEELLY_DIAG/notes/2': ('09a48fb7',
        "Quando la magnitude è sotto 350 una riga in più dice che il magnete è troppo lontano o "
        "fuori centro."),
    'WHEELLY_DIAG/notes/3': ('34c3e8d7',
        "Poi il driver del motore: '<chip> over UART: responding, run X mA, hold Y mA', oppure "
        "'<chip> over UART: SILENT - check VM at the driver, then the 1k on the single wire'. Il "
        "nome del chip (TMC2208 o TMC2209) viene letto dal chip stesso; un chip muto non può "
        "dire quale sia, e quella riga si legge 'TMC2208/2209 over UART: SILENT'."),
    'WHEELLY_DIAG/notes/4': ('ef6df889',
        "Le righe di questo controllo sono testo del firmware e non vengono tradotte."),
    'WHEELLY_DIAG/notes/5': ('83ee3474',
        "Ok quando la ruota ha risposto, Alert quando no."),
    'WHEELLY_DIAG/notes/6': ('29c6e69d',
        "Non muove la ruota."),
    'WHEELLY_SWEEP/what': ('e04ff4ee',
        "La spazzolata del magnete: la ruota fa un giro completo, una posizione alla volta, sempre "
        "nello stesso verso, e il driver registra la magnitude del sensore e l'angolo a ogni "
        "interrogazione. Alla fine disegna un grafico della magnitude in funzione dell'angolo. "
        "Più piccola è la variazione sul giro, meglio è centrato il magnete: usala prima e dopo "
        "aver regolato il traferro del sensore o il magnete."),
    'WHEELLY_SWEEP/elements/RUN': ('972c7503',
        "Avvia la spazzolata. La ruota si muove."),
    'WHEELLY_SWEEP/notes/1': ('619cf443',
        "La ruota si muove davvero: falla a coperchio aperto, mai durante una sequenza (log: "
        "«Faccio un giro completo misurando il magnete a ogni passo ...»). FILTER_SLOT va in "
        "Busy a ogni passo."),
    'WHEELLY_SWEEP/notes/2': ('e7ce32eb',
        "Un salto per posizione (5 su una ruota di fabbrica): la ruota finisce sulla posizione da "
        "cui era partita."),
    'WHEELLY_SWEEP/notes/3': ('855f53bb',
        "Durante la spazzolata il driver interroga ogni 100 ms invece che ogni POLLING_PERIOD, "
        "per avere abbastanza campioni."),
    'WHEELLY_SWEEP/notes/4': ('9d5c28e4',
        "Rifiutata, con Alert, mentre è in corso un cambio filtro o un'altra spazzolata."),
    'WHEELLY_SWEEP/notes/5': ('b477928f',
        "Alla fine: Ok, il grafico viene mandato in «Ultima spazzolata» (WHEELLY_SWEEP_PLOT), una "
        "copia viene scritta nella cartella delle spazzolate, e il log dà il numero di campioni, "
        "il minimo e il massimo della magnitude e l'escursione in conteggi e in percentuale, poi "
        "il percorso del file."),
    'WHEELLY_SWEEP/notes/6': ('9f736311',
        "Se un salto fallisce o va oltre il tempo, o si sono presi meno di 4 campioni, il "
        "grafico non viene fatto e la proprietà va in Alert (log: «La spazzolata si è fermata "
        "prima di finire il giro ...»)."),
    'WHEELLY_SWEEP/notes/7': ('80e36a97',
        "Ogni salto è un movimento normale, quindi viene scritto anche nel registro dei movimenti "
        "quando è acceso."),
    'WHEELLY_SWEEP_PLOT/what': ('4d967992',
        "Il grafico dell'ultima spazzolata, mandato al client come file PNG. Nel pannello una "
        "proprietà di tipo file non mostra immagini: KStars salva il file dove tiene i file "
        "ricevuti, e il driver non sa quale sia quel posto. Per questo il driver scrive anche una "
        "copia sua e ne mostra il percorso in «File su disco» (WHEELLY_FILES)."),
    'WHEELLY_SWEEP_PLOT/elements/PLOT': ('56fabd9c',
        "Il PNG dell'ultima spazzolata: magnitude (conteggi) in funzione dell'angolo (gradi), con "
        "una griglia ogni 45 gradi, gli angoli di taratura delle posizioni segnati, e il numero "
        "di campioni, il minimo, il massimo e l'escursione scritti sopra."),
    'WHEELLY_SWEEP_PLOT/notes/1': ('f4d2e904',
        "Sola lettura. Dichiarato apposta col formato '.wheelly.png': con un semplice '.png' "
        "KStars apre una finestra di visualizzazione che, chiudendola, chiude anche il pannello "
        "INDI; con questa estensione salva soltanto il file. Il nome finisce comunque in .png."),
    'WHEELLY_SWEEP_PLOT/notes/2': ('19682f56',
        "Il client lo riceve solo se accetta file da questa proprietà (in KStars, la casella "
        "accanto alla proprietà, spuntata di base)."),
    'WHEELLY_SWEEP_PLOT/notes/3': ('7b197e47',
        "Il file non è compresso (qualche centinaio di kB)."),
    'WHEELLY_SWEEP_PLOT/notes/4': ('f9cd2d65',
        "I testi dentro il grafico seguono la lingua del driver, in maiuscolo senza accenti."),
    'WHEELLY_SWEEP_DIR/what': ('424ff9f5',
        "La cartella in cui il driver scrive una copia di ogni grafico della spazzolata. Di base "
        "è la cartella Documents nella home del computer su cui gira il driver (su un Raspberry, "
        "quella del Raspberry, non del tuo portatile). Indirizzala altrove, per esempio su un "
        "disco esterno, se tieni lì i tuoi dati."),
    'WHEELLY_SWEEP_DIR/elements/DIR': ('43e3074b',
        "Percorso della cartella. Un '~/' iniziale diventa la cartella home."),
    'WHEELLY_SWEEP_DIR/notes/1': ('a44e8578',
        "Ogni spazzolata ha il suo file, chiamato YYYY-MM-DD_HH-MM-SS_wheelly_sweep.png in ora "
        "locale, così si possono confrontare una spazzolata prima e una dopo una regolazione; "
        "non si sovrascrive niente."),
    'WHEELLY_SWEEP_DIR/notes/2': ('b5bc039a',
        "Quando la cambi il driver crea la cartella (un livello solo) e controlla di poterci "
        "scrivere. Se non può, la proprietà diventa rossa e il log dice «La cartella ... adesso "
        "non si può usare: ... Le spazzolate non verranno salvate finché non si potrà.» Il "
        "valore viene tenuto comunque (un disco può semplicemente non essere ancora montato)."),
    'WHEELLY_SWEEP_DIR/notes/3': ('b348197e',
        "Salvata subito nella configurazione INDI."),
    'WHEELLY_SWEEP_DIR/notes/4': ('588ee90c',
        "Una cartella vuota vuol dire quella di base."),
    'WHEELLY_LOG/what': ('af092375',
        "Accende o spegne il registro dei movimenti: un file CSV con una riga per ogni cambio "
        "filtro finito, da aprire in un foglio di calcolo quando vuoi vedere quanto è precisa la "
        "ruota nell'arco di una notte o di mesi. Spento di base."),
    'WHEELLY_LOG/elements/LOG_ON': ('68ab8590',
        "Scrive il registro dei movimenti (log: «Registro dei movimenti acceso: <percorso>»)."),
    'WHEELLY_LOG/elements/LOG_OFF': ('5f1527ef',
        "Smette di scriverlo (log: «Registro dei movimenti spento.»)."),
    'WHEELLY_LOG/notes/1': ('0dd21c13',
        "Il file è ~/.indi/wheelly_movements.csv sul computer su cui gira il driver, fisso; il "
        "suo percorso è sempre mostrato in «File su disco». Le righe nuove si aggiungono in "
        "fondo; non si cancella niente."),
    'WHEELLY_LOG/notes/2': ('f5ec81ea',
        "Colonne: timestamp (UTC, ISO 8601), slot (la posizione chiesta), target (angolo "
        "obiettivo, gradi), angle, error (gradi), retries, outcome (arrived, warning, failed o "
        "timeout), agc, magnitude."),
    'WHEELLY_LOG/notes/3': ('cc70bb75',
        "La scelta viene salvata nella configurazione INDI e applicata al collegamento "
        "successivo."),
    'WHEELLY_LOG/notes/4': ('c85cc41c',
        "Se il file non si può aprire il log dice perché e l'interruttore torna su Spento."),
    'WHEELLY_FILES/what': ('5fc5c91c',
        "Dove sono i due file che il driver scrive, così i percorsi non si perdono nel log: il "
        "registro dei movimenti e il grafico dell'ultima spazzolata. Entrambi i percorsi sono "
        "sul computer su cui gira il driver."),
    'WHEELLY_FILES/elements/PATH': ('0c3fd3b7',
        "Percorso del CSV del registro dei movimenti. Mostrato anche quando il registro è "
        "spento."),
    'WHEELLY_FILES/elements/SWEEP': ('27b887b1',
        "Percorso dell'ultimo grafico della spazzolata scritto dal driver, oppure «non ancora "
        "scritta»."),
    'WHEELLY_FILES/notes/1': ('65834d39',
        "Sola lettura."),
    'WHEELLY_FILES/notes/2': ('ecf5326c',
        "«Ultima spazzolata» mostra «non ancora scritta» dopo ogni avvio del driver, finché non "
        "si fa una spazzolata; i grafici più vecchi restano nella cartella delle spazzolate."),
    'WHEELLY_FILES/notes/3': ('2434ef8b',
        "Alert quando non è stato possibile scrivere l'ultimo grafico; il motivo è nel log («Non "
        "riesco a scrivere il grafico in ...»)."),
    'DEBUG/what': ('c0f7d789',
        "L'interruttore di debug standard di INDI. Quando è abilitato, INDI aggiunge le "
        "impostazioni del livello di debug e dell'uscita del log; col livello 'Driver Debug' "
        "acceso, il driver Wheelly scrive nel log ogni riga scambiata con la ruota, nei due "
        "sensi ('-> ' mandata, '<- ' ricevuta). È la prima cosa da accendere quando la ruota fa "
        "qualcosa di inatteso, e non serve ricompilare niente."),
    'DEBUG/elements/ENABLE': ('2455df14',
        "Debug acceso: compaiono altre proprietà per i livelli e l'uscita del log."),
    'DEBUG/elements/DISABLE': ('627abf30',
        "Debug spento (di base)."),
    'DEBUG/notes/1': ('ccdd594b',
        "Salvato nella configurazione INDI e ripristinato all'avvio del driver."),
    'DEBUG/notes/2': ('fcfbc80b',
        "Al livello di debug il driver scrive anche «Vado alla posizione N.» all'inizio di ogni "
        "movimento."),
    'DEBUG/notes/3': ('5b74a65b',
        "Finiscono nel log anche le interrogazioni di stato, parecchie al secondo: rispegnilo "
        "quando hai finito."),
    'SIMULATION/what': ('b50a9870',
        "L'interruttore di simulazione standard di INDI. Il driver Wheelly non ha un modo di "
        "simulazione: non guarda questo interruttore, e parla comunque con la porta seriale. "
        "Lascialo disabilitato. Per provare il driver senza una ruota, usa il simulatore del "
        "firmware del progetto (firmware/simulator) su una porta seriale virtuale."),
    'SIMULATION/elements/ENABLE': ('77031523',
        "Non ha effetto sulla ruota; vedi la nota."),
    'SIMULATION/elements/DISABLE': ('cbb3cd50',
        "Di base; lascialo qui."),
    'SIMULATION/notes/1': ('88f728b0',
        "Trappola: con la simulazione accesa, il Disconnect di libindi ritorna senza chiudere la "
        "porta, quindi la porta seriale resta aperta dopo Disconnect."),
    'CONFIG_PROCESS/what': ('ab0ce937',
        "Il file di configurazione standard di INDI di questo dispositivo, tenuto sul computer "
        "su cui gira il driver (~/.indi/, col nome del dispositivo). Attenzione: la taratura "
        "non sta qui: angoli, nomi dei filtri, correnti e modo del LED sono conservati nella "
        "ruota con «Salva nella ruota». La configurazione tiene le impostazioni di questo "
        "computer e di questo profilo."),
    'CONFIG_PROCESS/elements/CONFIG_LOAD': ('75b354e3',
        "Ricarica la configurazione salvata e la applica."),
    'CONFIG_PROCESS/elements/CONFIG_SAVE': ('584174f9',
        "Salva le impostazioni correnti nel file di configurazione."),
    'CONFIG_PROCESS/elements/CONFIG_DEFAULT': ('37447ee8',
        "Carica il file di configurazione di base che INDI tiene accanto alla configurazione."),
    'CONFIG_PROCESS/elements/CONFIG_PURGE': ('2aaf873e',
        "Cancella il file di configurazione."),
    'CONFIG_PROCESS/notes/1': ('010daad3',
        "Cosa aggiunge Wheelly alle voci standard di INDI (collegamento, porta, baud rate, "
        "ricerca automatica, debug, periodo di interrogazione, posizione del filtro, nomi dei "
        "filtri, joystick): i dati del firmware, compreso il numero di serie della ruota di "
        "questo profilo, le tolleranze, la cartella delle spazzolate, l'interruttore del "
        "registro dei movimenti e la lingua."),
    'CONFIG_PROCESS/notes/2': ('591614ee',
        "Load riapplica i valori salvati come se fossero stati scritti a mano: le tolleranze "
        "vengono mandate alla ruota (solo nella memoria di lavoro), e viene chiesta la posizione "
        "del filtro salvata, quindi la ruota può muoversi."),
    'CONFIG_PROCESS/notes/3': ('0ed0f9d1',
        "Purge dimentica anche quale ruota appartiene a questo profilo; il collegamento "
        "successivo adotta la prima Wheelly che trova."),
    'CONFIG_PROCESS/notes/4': ('9fd77e1f',
        "Alcune voci si salvano da sole quando cambiano: la cartella delle spazzolate, "
        "l'interruttore del registro dei movimenti, la lingua, il numero di serie imparato, la "
        "porta."),
    'WHEELLY_CONFIG/what': ('56294122',
        "«Salva nella ruota», anche qui: scrive nella memoria permanente della ruota tutto "
        "quello che la ruota contiene, come fa il pulsante con lo stesso nome nella scheda "
        "Calibration and Diagnostics (WHEELLY_SAVE). Sta subito sotto Configuration perché le "
        "impostazioni di questa scheda che stanno nella ruota - motore, tenuta, verso, LED - si"
        " salvino senza uscirne."),
    'WHEELLY_CONFIG/elements/SAVE': ('716393c2',
        "Scrive nella ruota numero di posizioni, angoli di taratura, nomi dei filtri, "
        "tolleranze, corrente di marcia e di tenuta, tenuta dopo l'arrivo, velocità, "
        "accelerazione, verso di rotazione e modo del LED. Log: «Taratura salvata nella "
        "ruota.»"),
    'WHEELLY_CONFIG/notes/1': ('ea8e99c8',
        "Configuration, sopra, è di INDI e salva le impostazioni di questo computer e di questo"
        " profilo, non quelle della ruota: l'una non sostituisce l'altra. Una riga a sé e non "
        "un quinto pulsante in Configuration: Ekos conta sui suoi quattro, e KStars ne "
        "mostrerebbe cinque come un menu a tendina."),
    'WHEELLY_CONFIG/notes/2': ('c9f90927',
        "C'è sempre, come Configuration; premuto con la ruota scollegata va in Alert e il log "
        "dice «Prima collega la ruota.»"),
    'POLLING_PERIOD/what': ('f5cf3938',
        "Il periodo di interrogazione standard di INDI. Per Wheelly è ogni quanto il driver "
        "chiede alla ruota il suo stato: posizione, errore residuo, letture del sensore, la fine "
        "di un movimento, una ruota girata a mano. Il driver lo imposta a 250 ms."),
    'POLLING_PERIOD/elements/PERIOD_MS': ('7bd6c42c',
        "Tempo fra due richieste di stato, in millisecondi. Di base 250."),
    'POLLING_PERIOD/notes/1': ('eac9a472',
        "Limiti nel pannello: da 10 a 600000 ms."),
    'POLLING_PERIOD/notes/2': ('45b2a254',
        "La fine di un cambio filtro si nota all'interrogazione successiva, e anche il limite di "
        "tempo del driver per un movimento viene controllato a ogni interrogazione: un periodo "
        "lungo fa sembrare più lenti i cambi filtro e ritarda la segnalazione dei fallimenti."),
    'POLLING_PERIOD/notes/3': ('d9c902b7',
        "Durante una spazzolata del magnete il driver interroga comunque ogni 100 ms."),
    'POLLING_PERIOD/notes/4': ('ccdd594b',
        "Salvato nella configurazione INDI e ripristinato all'avvio del driver."),
    'POLLING_PERIOD/notes/5': ('8d59bd5e',
        "Una riga di stato sono circa 2 ms di traffico seriale, quindi il valore di base costa "
        "poco."),
    'USEJOYSTICK/what': ('173f3743',
        "L'interruttore standard di INDI del joystick per le ruote portafiltri. Quando è "
        "abilitato, il driver ascolta un joystick servito dal driver joystick di INDI e ti "
        "permette di cambiare filtro con quello."),
    'USEJOYSTICK/elements/ENABLE': ('340dc99b',
        "Ascolta il joystick; compare una proprietà per associare i comandi."),
    'USEJOYSTICK/elements/DISABLE': ('023b2f19',
        "Ignora il joystick (di base)."),
    'USEJOYSTICK/notes/1': ('3072ec56',
        "Associazione fatta da libindi: la leva 'Change Filter' (di base JOYSTICK_1) spinta tutta "
        "in su va alla posizione precedente, in giù alla successiva, ricominciando dal fondo; il "
        "pulsante 'Reset' (di base BUTTON_1) va alla posizione 1."),
    'USEJOYSTICK/notes/2': ('904bb2c8',
        "Niente di specifico di Wheelly: ogni richiesta diventa un movimento normale con le "
        "stesse tolleranze e gli stessi ritentativi."),
    'USEJOYSTICK/notes/3': ('4c692564',
        "Un movimento chiesto dal joystick compare in «Posizione» come ogni altro: Busy mentre "
        "la ruota gira."),
    'SNOOP_JOYSTICK/what': ('a399c38c',
        "Il nome del dispositivo joystick INDI che questo driver ascolta quando il joystick è "
        "abilitato. Proprietà standard di INDI."),
    'SNOOP_JOYSTICK/elements/SNOOP_JOYSTICK_DEVICE': ('8e436230',
        "Nome del dispositivo del driver joystick. Di base 'Joystick'."),
    'SNOOP_JOYSTICK/notes/1': ('18246573',
        "Cambialo solo se il tuo joystick ha un altro nome in INDI."),
    'WHEELLY_FIRMWARE/what': ('37309a68',
        "Quello che la ruota ha detto di sé quando il driver si è collegato: versione del "
        "firmware, versione del protocollo e numero di serie. Utile quando si segnala un "
        "problema, e per sapere a quale ruota è legato questo profilo."),
    'WHEELLY_FIRMWARE/elements/FW': ('ea7b61d4',
        "Versione del firmware che gira sulla ruota."),
    'WHEELLY_FIRMWARE/elements/PROTO': ('5302549c',
        "Versione del protocollo del firmware. Questo driver accetta solo 1."),
    'WHEELLY_FIRMWARE/elements/SERIAL': ('f4523784',
        "Numero di serie della ruota, ricavato dal firmware dall'indirizzo MAC del chip, quindi "
        "diverso per ogni ruota."),
    'WHEELLY_FIRMWARE/notes/1': ('65834d39',
        "Sola lettura."),
    'WHEELLY_FIRMWARE/notes/2': ('6f8e5b4c',
        "Salvato nella configurazione INDI: il numero di serie salvato è quello che il profilo "
        "cerca al collegamento successivo (vedi CONNECTION)."),
    'WHEELLY_FIRMWARE/notes/3': ('2c097f48',
        "Un firmware con un'altra versione di protocollo viene rifiutato al collegamento, con un "
        "messaggio nel log che dice quale parte aggiornare."),
    'WHEELLY_MOTOR/what': ('f74cf531',
        "Le impostazioni del motore passo-passo mentre gira la ruota. La corrente di marcia è "
        "quella da regolare: alzala finché la trasmissione a frizione smette di slittare, e non "
        "oltre, perché più corrente vuol dire più calore."),
    'WHEELLY_MOTOR/elements/RUN_MA': ('a1d41bb2',
        "Corrente di marcia, in mA (RMS, impostata nel driver del motore TMC). Di base 350."),
    'WHEELLY_MOTOR/elements/SPEED': ('4c68c35b',
        "Velocità massima, in passi interi del motore al secondo. Di base 300."),
    'WHEELLY_MOTOR/elements/ACCEL': ('c148b98d',
        "Accelerazione, in passi interi del motore al secondo quadrato. Di base 1200."),
    'WHEELLY_MOTOR/notes/1': ('42f68c4c',
        "Limiti nel pannello: corrente di marcia da 1 a 800 mA (passo 5), velocità da 1 a 5000 "
        "(passo 10), accelerazione da 1 a 50000 (passo 50)."),
    'WHEELLY_MOTOR/notes/2': ('d66edd4a',
        "Il valore di base di 350 mA è misurato sulla ruota di riferimento, dove la frizione "
        "smette di slittare; il motore è dato per 400 mA per fase. Col fermo ancora al suo "
        "posto la ruota voleva 400 mA per uscire da una tacca; col fermo tolto, come la guida "
        "di montaggio fa sempre, a 350 mA è arrivata a ogni velocità da 100 a 1000 passi/s."),
    'WHEELLY_MOTOR/notes/3': ('0b88c8be',
        "Set manda i tre valori alla ruota insieme; poi i campi mostrano quello che la ruota ha "
        "accettato."),
    'WHEELLY_MOTOR/notes/4': ('c422f6ed',
        "Abbassare la corrente di marcia sotto quella di tenuta abbassa anche la corrente di "
        "tenuta nella ruota."),
    'WHEELLY_MOTOR/notes/5': ('7184481b',
        "Velocità e accelerazione sono in passi interi del motore: 200 passi/s è un giro di "
        "motore al secondo, circa 124 gradi di disco al secondo su Wheelly (la frizione fa girare"
        " il disco 2,9 volte più lento del motore); i 300 passi/s di base sono circa 186 gradi "
        "al secondo."),
    'WHEELLY_MOTOR/notes/6': ('49205a16',
        "Più lento non vuol dire più delicato: questo motore ha poca coppia sotto i 250 "
        "passi/s circa (75 giri al minuto, dove comincia la curva del suo datasheet), e a 50 "
        "passi/s si bloccava vibrando su alcune tacche del fermo della ruota di riferimento "
        "(ora tolto) anche nel verso facile, mentre da 100 fino a 1000 ogni movimento "
        "arrivava. Il valore di base è 300/1200. Dopo un tratto che si blocca comunque, la "
        "ruota fa il successivo al doppio della velocità e dell'accelerazione (al massimo 1000"
        " passi/s) per uscire dalla tacca."),
    'WHEELLY_MOTOR/notes/7': ('45a794df',
        "Il tetto di tempo della ruota su un movimento segue la velocità: se con i nuovi valori "
        "il cambio filtro più lungo possibile andasse oltre i 30 s dopo i quali Ekos rinuncia, il"
        " log avverte («Con queste impostazioni del motore il cambio di filtro più lungo può "
        "durare fino a N s ...»)."),
    'WHEELLY_MOTOR/notes/8': ('da809c5e',
        "Resta nella ruota fino allo spegnimento; premi «Salva nella ruota» per tenerla. Non "
        "viene salvata nella configurazione INDI."),
    'WHEELLY_MOTOR/notes/9': ('a3cc9e8b',
        "Alert se la ruota ha rifiutato il valore; il motivo è nel log."),
    'WHEELLY_HOLD/what': ('b4f52a0e',
        "Se il motore resta alimentato quando la ruota è ferma. Di base è 0: alla fine di "
        "ogni movimento il motore viene rilasciato, senza corrente, senza calore accanto alla "
        "camera e senza il rumore del chopper durante le pose. Il fermo della ruota si toglie "
        "sempre (il motore non riesce a uscire dalle sue tacche), quindi a tenere fermo il "
        "disco a riposo è la frizione che ci preme sopra; se la ruota si sposta comunque da "
        "sola - il log lo dice - imposta una corrente di tenuta ridotta così il disco non può "
        "girare da solo. Il secondo campo è per quanto il motore fermo continua a tenere il "
        "disco, alla corrente di marcia, dopo ogni movimento prima di essere rilasciato - "
        "anche quando la corrente di tenuta a riposo è 0."),
    'WHEELLY_HOLD/elements/HOLD_MA': ('4a980818',
        "Corrente di tenuta a riposo, in mA; 0 = motore rilasciato. Il campo mostra il valore "
        "che ha la ruota, 0 compreso."),
    'WHEELLY_HOLD/elements/SETTLE_MS': ('a533bf3a',
        "Tenuta dopo l'arrivo, in ms: per quanto il motore resta alimentato alla corrente di "
        "marcia dopo che ogni tratto di un movimento si è fermato, prima che la ruota legga "
        "dove sta il disco e - alla fine del movimento - lo rilasci. Di base 300; 0 = legge e "
        "rilascia subito."),
    'WHEELLY_HOLD/notes/1': ('d643a65a',
        "Lo dice anche la luce: verde finché la corrente di tenuta è accesa, grigia quando il "
        "motore è rilasciato (0), sia che il valore sia stato impostato dal pannello sia che "
        "sia stato letto al collegamento."),
    'WHEELLY_HOLD/notes/2': ('1fdebf31',
        "Da dove partire, se la ruota si sposta da sola: 150 mA, il valore che questo progetto"
        " consiglia. Lo dice anche il log, nel messaggio che segnala lo spostamento. Il campo "
        "mostra quello che la ruota tiene, 0 compreso, e non 150 come suggerimento: una ruota "
        "salvata a 0 sembrerebbe tornata a 150."),
    'WHEELLY_HOLD/notes/3': ('badb4bb9',
        "Limiti nel pannello: da 0 a 800 mA, passo 5. La ruota rifiuta una corrente di tenuta "
        "più alta di quella di marcia (il log spiega, la proprietà va in Alert)."),
    'WHEELLY_HOLD/notes/4': ('9ba1e1e5',
        "Impostare un valore sopra 0 scrive un avviso nel log: il motore scalda accanto al "
        "sensore e il driver canta durante le pose."),
    'WHEELLY_HOLD/notes/5': ('127a4740',
        "150 mA e non la corrente di marcia perché la tenuta dura tutta la notte: circa 1,35 W "
        "invece di 7,4 W."),
    'WHEELLY_HOLD/notes/6': ('a1850967',
        "Perché la tenuta dopo l'arrivo: il motore muove il disco per attrito, e un motore "
        "fermo ancora alimentato tiene la gomma, che frena il disco; rilasciato subito, il "
        "disco potrebbe proseguire per inerzia. La ruota legge il verdetto alla fine della "
        "tenuta, così un disco che ha continuato a muoversi viene giudicato dove si è fermato "
        "e corretto come qualunque altro errore. Un disco più pesante o una gomma più morbida "
        "possono volerne di più; 0 legge prima che il disco si sia assestato e costa tratti "
        "in più."),
    'WHEELLY_HOLD/notes/7': ('96dd8a56',
        "Limiti della tenuta dopo l'arrivo: da 0 a 2000 ms, passo 50. Allunga ogni tratto, "
        "quindi il tetto di tempo della ruota su un movimento cresce con lei (il log avvisa se"
        " supera i 30 s di Ekos, vedi WHEELLY_DIRECTION). Viene riletta dalla ruota al "
        "collegamento; un firmware precedente non ce l'ha, tiene i suoi 300 ms fissi, e una "
        "modifica di questo campo va in Alert."),
    'WHEELLY_HOLD/notes/8': ('da809c5e',
        "Resta nella ruota fino allo spegnimento; premi «Salva nella ruota» per tenerla. Non "
        "viene salvata nella configurazione INDI."),
    'WHEELLY_DIRECTION/what': ('fa07a4c3',
        "Da che parte può girare la ruota per raggiungere una posizione. Una meccanica più "
        "dura in un verso che nell'altro - come una ruota con un fermo asimmetrico, un fianco "
        "dolce da una parte e uno ripido dall'altra - può bloccarsi nel verso duro: il motore "
        "ronza e vibra e il disco non si muove. Girare in un verso solo lo evita. "
        "L'interruttore mostra il valore riletto dalla ruota."),
    'WHEELLY_DIRECTION/elements/DIR_SHORTEST': ('dae77216',
        "La via più corta, in un verso o nell'altro. Il valore di fabbrica, perché la guida di"
        " montaggio toglie il fermo della ruota."),
    'WHEELLY_DIRECTION/elements/DIR_UP': ('1ebe88dd',
        "Sempre verso angoli crescenti, come li legge il sensore."),
    'WHEELLY_DIRECTION/elements/DIR_DOWN': ('0d72eb44',
        "Sempre verso angoli decrescenti. Il verso in cui il fermo asimmetrico della ruota di "
        "riferimento lasciava passare - salendo, il motore si bloccava a ogni tacca. Crescenti"
        " e decrescenti restano per una meccanica più dura in un verso."),
    'WHEELLY_DIRECTION/notes/1': ('54fc4d3d',
        "In un verso solo, ogni movimento e ogni ritentativo vanno da quella parte: dopo "
        "un sorpasso la ruota fa tutto il giro invece di tornare indietro nel verso duro. "
        "Perché non sorpassi, ogni tratto si ferma un po' prima della meta e i successivi "
        "si avvicinano a piccoli passi: un movimento richiede qualche tratto, e questi "
        "tratti di avvicinamento non sono ritentativi. Se è arrivata lo giudica sempre "
        "l'angolo letto."),
    'WHEELLY_DIRECTION/notes/2': ('2c35d4c8',
        "In un verso solo un movimento può essere quasi un giro intero, e un ritentativo un altro"
        " giro: il tetto di tempo della ruota su un movimento cresce di conseguenza. Se il cambio"
        " filtro più lungo possibile andasse oltre i 30 s dopo i quali Ekos rinuncia, il log "
        "avverte («Con queste impostazioni del motore il cambio di filtro più lungo può durare "
        "fino a N s ...») - quando si imposta il verso o la velocità del motore, e al "
        "collegamento. Alza la velocità, o scegli la via più corta se la ruota lo permette."),
    'WHEELLY_DIRECTION/notes/3': ('da809c5e',
        "La ruota la tiene finché non viene spenta; premi «Salva nella ruota» per conservarla. "
        "Non è salvata nella configurazione di INDI."),
    'WHEELLY_DIRECTION/notes/4': ('fe9c1bb8',
        "Grigio (Idle) solo con un firmware che non conosce l'impostazione; Alert se la ruota ha "
        "rifiutato il comando."),
    'WHEELLY_LED/what': ('eb8dbfd1',
        "Cosa fa il LED sulla ruota. Il LED sta dentro il cammino della luce, quindi di base "
        "resta spento finché va tutto bene: respira piano mentre la ruota va a un altro filtro, "
        "e lampeggia un segnale suo quando qualcosa non va - la tabella qui sotto dice quale. "
        "L'interruttore mostra il modo riletto dalla ruota."),
    'WHEELLY_LED/elements/LED_ON': ('24085b33',
        "Acceso fisso; i segnali d'allarme si vedono comunque."),
    'WHEELLY_LED/elements/LED_PULSE': ('bc06fee3',
        "Spento a riposo; pulsa piano mentre la ruota va a un'altra posizione. Di base."),
    'WHEELLY_LED/elements/LED_OFF': ('273b530f',
        "Sempre spento - pulsazione e segnali d'allarme compresi - per non avere nessuna luce "
        "vicino all'ottica, o per girare la ruota a mano."),
    'WHEELLY_LED/elements/LED_TEST': ('1a5131dd',
        "Lampeggia WHEELLY in codice Morse una volta (circa 6,7 s), poi torna al modo in uso. "
        "Risponde alla domanda «il LED è vivo?»."),
    'WHEELLY_LED/table/header/1': ('d75022b4',
        "Cosa fa il LED"),
    'WHEELLY_LED/table/header/2': ('57e2a7ce',
        "Cosa vuol dire"),
    'WHEELLY_LED/table/header/3': ('96bdb66b',
        "Fino a quando"),
    'WHEELLY_LED/table/1/1': ('ae1ef014',
        "Spento"),
    'WHEELLY_LED/table/1/2': ('42392d66',
        "Va tutto bene, la ruota è ferma"),
    'WHEELLY_LED/table/1/3': ('3bc15c8a',
        "-"),
    'WHEELLY_LED/table/2/1': ('281cdfb9',
        "Respira piano (1,7 s)"),
    'WHEELLY_LED/table/2/2': ('6f1f8a4c',
        "Va a un'altra posizione (in «Pulsa durante il movimento»)"),
    'WHEELLY_LED/table/2/3': ('9874ff12',
        "Arriva"),
    'WHEELLY_LED/table/3/1': ('5a1dbe78',
        "Lampeggia veloce, 4 al secondo"),
    'WHEELLY_LED/table/3/2': ('e54d84b8',
        "Non ha raggiunto la posizione dopo tutti i ritentativi"),
    'WHEELLY_LED/table/3/3': ('9a7dd21e',
        "Raggiunge una posizione, o viene mandata di nuovo"),
    'WHEELLY_LED/table/4/1': ('fdb31621',
        "Due lampi brevi ogni 2 s"),
    'WHEELLY_LED/table/4/2': ('fb77e2ad',
        "La ruota si è spostata da sola a riposo, oltre la tolleranza"),
    'WHEELLY_LED/table/4/3': ('cf2e20b3',
        "Viene mandata a una posizione"),
    'WHEELLY_LED/table/5/1': ('264d9344',
        "Tre lampi brevi ogni 2 s"),
    'WHEELLY_LED/table/5/2': ('c2bd78ec',
        "Il sensore non vede più il magnete"),
    'WHEELLY_LED/table/5/3': ('8c64a5db',
        "Lo rivede"),
    'WHEELLY_LED/table/6/1': ('b7962dad',
        "Scrive WHEELLY in Morse"),
    'WHEELLY_LED/table/6/2': ('bf88df68',
        "La prova del LED"),
    'WHEELLY_LED/table/6/3': ('96319117',
        "Circa 6,7 s"),
    'WHEELLY_LED/notes/1': ('f282aeb0',
        "Un modo nuovo resta nella ruota solo fino allo spegnimento; il log ti ricorda di "
        "premere «Salva nella ruota» per tenerlo."),
    'WHEELLY_LED/notes/2': ('c96af8a6',
        "Fai la prova a coperchio aperto o di giorno: il LED sta dentro il cammino ottico. Il "
        "log lo dice quando la prova comincia."),
    'WHEELLY_LED/notes/3': ('34ae7115',
        "Durante la prova l'interruttore mostra già di nuovo il modo in uso; il lampeggio va "
        "avanti per i suoi 6,7 s."),
    'WHEELLY_LED/notes/4': ('fe31fae9',
        "I segnali d'allarme della tabella si mostrano uno alla volta, prima il più grave "
        "(magnete, poi posizione non raggiunta, poi deriva), alla luminosità del culmine della "
        "pulsazione. In «Spento» non ce n'è nessuno: è anche il modo per girare la ruota a mano "
        "col motore non alimentato, cosa che altrimenti verrebbe letta come una deriva."),
    'WHEELLY_LED/notes/5': ('187b1296',
        "Alert se la ruota ha rifiutato il comando."),
    'WHEELLY_LANGUAGE/what': ('9e8e002d',
        "La lingua delle etichette del pannello e dei messaggi del driver nel log: inglese o "
        "italiano. «Come il sistema» segue la localizzazione del computer su cui gira il driver "
        "(LC_ALL, LC_MESSAGES o LANG che cominciano con 'it' danno l'italiano; tutto il resto "
        "dà l'inglese)."),
    'WHEELLY_LANGUAGE/elements/AUTO': ('3495f3d0',
        "Segue la localizzazione del sistema del computer del driver (di base)."),
    'WHEELLY_LANGUAGE/elements/EN': ('449abdb4',
        "Inglese."),
    'WHEELLY_LANGUAGE/elements/IT': ('54b579bd',
        "Italiano."),
    'WHEELLY_LANGUAGE/notes/1': ('b348197e',
        "Salvata subito nella configurazione INDI."),
    'WHEELLY_LANGUAGE/notes/2': ('29780b1e',
        "Le etichette si costruiscono una volta sola, all'avvio del driver: la nuova lingua si "
        "vede dopo aver fermato e fatto ripartire INDI in Ekos - scollegarsi e ricollegarsi non "
        "basta. Il log lo dice."),
    'WHEELLY_LANGUAGE/notes/3': ('431aad29',
        "I nomi delle schede e le proprietà standard di INDI restano in inglese; anche le righe "
        "del Controllo dell'hardware sono testo del firmware e restano in inglese."),
    'DRIVER_INFO/what': ('0aeec448',
        "Informazioni standard di INDI sul driver: il nome, il programma che lo esegue, la "
        "versione e il tipo di dispositivo."),
    'DRIVER_INFO/elements/DRIVER_NAME': ('ffabf41c',
        "Nome del driver (Wheelly)."),
    'DRIVER_INFO/elements/DRIVER_EXEC': ('ced59fca',
        "Nome dell'eseguibile (indi_wheelly)."),
    'DRIVER_INFO/elements/DRIVER_VERSION': ('6a7b3b19',
        "Versione del driver."),
    'DRIVER_INFO/elements/DRIVER_INTERFACE': ('6313764d',
        "Codice dell'interfaccia INDI; 16 vuol dire ruota portafiltri."),
    'DRIVER_INFO/notes/1': ('b2c66e5a',
        "Sola lettura. La versione del firmware della ruota è in WHEELLY_FIRMWARE, sotto "
        "Options."),
    'CONNECTION_MODE/what': ('ec08a51d',
        "La scelta standard di INDI del modo di raggiungere il dispositivo. Wheelly offre solo il "
        "collegamento seriale, sul cavo USB dello XIAO ESP32-S3."),
    'CONNECTION_MODE/elements/CONNECTION_SERIAL': ('6e4d42ef',
        "Porta seriale (l'unica scelta)."),
    'DEVICE_PORT/what': ('60f3f0f5',
        "La porta seriale della ruota. Raramente serve scriverla: il driver dà a INDI uno schema "
        "per scegliere la porta di un ESP32-S3 fra quelle trovate, e con Auto Search acceso "
        "prova le altre porte finché una Wheelly risponde. La ruota poi si riconosce dalla "
        "risposta e dal numero di serie, non dal nome della porta, che può cambiare quando "
        "sposti la spina in un'altra presa USB."),
    'DEVICE_PORT/elements/PORT': ('5fddb165',
        "Percorso della porta seriale, per esempio /dev/ttyACM0 su Linux o /dev/cu.usbmodem... "
        "su macOS."),
    'DEVICE_PORT/notes/1': ('34b67d94',
        "Schema dato a INDI: '303a|espressif|wheelly|usbmodem', senza distinguere maiuscole e "
        "minuscole: 303a è l'identificativo USB del produttore Espressif, e su Linux le porte "
        "sotto /dev/serial/by-id/ portano invece il nome del produttore (la ruota è "
        "usb-Espressif_USB_JTAG_serial_debug_unit_<serial>-if00). Secondo libindi si usa solo "
        "quando la porta salvata non esiste più."),
    'DEVICE_PORT/notes/2': ('ff66a979',
        "Verificato sul Raspberry con la ruota vera e nessuna configurazione salvata: il driver "
        "propone da solo la porta della ruota e si collega."),
    'DEVICE_PORT/notes/3': ('7ddb01df',
        "INDI salva la porta nella configurazione quando cambia."),
    'DEVICE_PORT/notes/4': ('7429ec56',
        "Scrivere un percorso che non è fra le porte trovate spegne Auto Search."),
    'SYSTEM_PORTS/what': ('94d068b6',
        "Pulsanti scorciatoia standard di INDI, uno per ogni porta seriale che il sistema trova: "
        "premerne uno copia quella porta in Ports. Compare solo quando il computer ha delle "
        "porte seriali; con la ruota collegata, il suo pulsante porta il nome della porta USB "
        "dello XIAO (Espressif USB JTAG/serial debug unit, seguito dal numero di serie della "
        "scheda)."),
    'SYSTEM_PORTS/variable_elements': ('060611c9',
        "Una porta trovata dal sistema; premila per usarla."),
    'SYSTEM_PORTS/notes/1': ('e39b01d2',
        "L'elenco lo fa libindi all'avvio del driver: una porta collegata dopo compare dopo "
        "'Refresh' (Scan Ports)."),
    'DEVICE_BAUD_RATE/what': ('3160979d',
        "La velocità seriale standard di INDI. Il driver sceglie 115200 di base, che è la "
        "velocità con cui il firmware apre la sua porta seriale. Lasciala lì."),
    'DEVICE_BAUD_RATE/elements/9600': ('85faaecf',
        "9600 baud."),
    'DEVICE_BAUD_RATE/elements/19200': ('049a8c73',
        "19200 baud."),
    'DEVICE_BAUD_RATE/elements/38400': ('21c076fe',
        "38400 baud."),
    'DEVICE_BAUD_RATE/elements/57600': ('76a2a561',
        "57600 baud."),
    'DEVICE_BAUD_RATE/elements/115200': ('8858dc84',
        "115200 baud (di base, la velocità del firmware)."),
    'DEVICE_BAUD_RATE/elements/230400': ('9133e496',
        "230400 baud."),
    'DEVICE_BAUD_RATE/notes/1': ('a78137f7',
        "Non importa quale si sceglie: lo XIAO ESP32-S3 parla sulla sua porta USB nativa, dove "
        "il baud rate non viene usato sul filo (verificato sulla ruota vera: si collega a 9600 "
        "come a 115200)."),
    'DEVICE_AUTO_SEARCH/what': ('9de5df6e',
        "La ricerca automatica standard di INDI: se la ruota non risponde sulla porta in "
        "DEVICE_PORT, prova tutte le altre porte seriali trovate, in ordine casuale, finché una "
        "risponde. Per Wheelly è anche ciò che permette a un profilo di trovare la sua ruota "
        "quando ce ne sono due collegate."),
    'DEVICE_AUTO_SEARCH/elements/INDI_ENABLED': ('d4f2649f',
        "Prova le altre porte quando quella configurata non va (di base)."),
    'DEVICE_AUTO_SEARCH/elements/INDI_DISABLED': ('8360c54e',
        "Prova solo la porta in DEVICE_PORT."),
    'DEVICE_AUTO_SEARCH/notes/1': ('09e382b9',
        "Su Linux, libindi spegne Auto Search da sé dopo aver trovato il dispositivo su un'altra "
        "porta, e salva la porta nuova."),
    'DEVICE_AUTO_SEARCH/notes/2': ('aee04f28',
        "Una Wheelly con un numero di serie diverso non viene accettata al primo giro, quindi "
        "Auto Search passa alla porta successiva."),
    'DEVICE_PORT_SCAN/what': ('594b0198',
        "Il pulsante standard di INDI per cercare di nuovo le porte seriali del sistema, per "
        "esempio dopo aver collegato la ruota. Le porte trovate compaiono come pulsanti fra cui "
        "scegliere."),
    'DEVICE_PORT_SCAN/elements/Scan Ports': ('cb91cc1e',
        "Cerca le porte seriali adesso; il log dice quante ne ha trovate."),
    'tabs/Main Control': ('70507dae',
        "Quello che usi ogni notte: collegarti, scegliere il filtro, dare i nomi ai filtri, e "
        "guardare dove si trova davvero la ruota e come sta il suo sensore magnetico. Le "
        "proprietà Wheelly compaiono qui solo quando la ruota è collegata; il numero di "
        "posizioni e di nomi dei filtri è quello che la ruota dichiara."),
    'tabs/Connection': ('a67bc83e',
        "Le impostazioni standard di INDI per il collegamento seriale. Wheelly si collega sul "
        "cavo USB a 115200 baud e si riconosce da quello che risponde e dal numero di serie, non "
        "dal nome della porta, quindi con Auto Search acceso raramente serve cambiare qualcosa "
        "qui."),
    'tabs/Options': ('9e0b7f02',
        "Le opzioni standard di INDI (debug, simulazione, file di configurazione, periodo di "
        "interrogazione, joystick) e le impostazioni della macchina: informazioni sul firmware,"
        " corrente del motore, velocità e accelerazione, tenuta a riposo, verso di rotazione, "
        "LED e lingua. Motore, tenuta, verso e LED stanno nella ruota e restano dopo lo "
        "spegnimento solo con «Salva nella ruota», subito sotto Configuration o nella scheda "
        "Calibration and Diagnostics."),
    'tabs/Calibration and Diagnostics': ('a7c8215e',
        "Tarare e controllare la ruota, cose da fare a coperchio aperto o durante la messa a "
        "punto, non nel mezzo di una sequenza: gli angoli di taratura, i passi, il pulsante per"
        " salvare, le tolleranze, il controllo dell'hardware, la spazzolata del magnete col suo"
        " grafico, e il registro dei movimenti. Le modifiche alla taratura stanno nella memoria"
        " di lavoro della ruota finché non premi «Salva nella ruota». Le spiegazioni di quello "
        "che è successo vanno nel riquadro del log in fondo, non in campi aggiunti."),
}
