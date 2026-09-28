# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Italian texts of the parameters: the "drawings" label and the description
of each row of parameters.py, which holds them in English.

Keyed by parameter name ("name#2" for the second row carrying the same name).
A parameter missing here shows its English text: new parameters are written
in English only, and get an Italian entry if and when someone translates it.
Read by texts_editor.parameter_text; orphan keys are caught by
check_editor.py."""

TEXTS = {
    "D_body": {
        "description": "Diametro esterno del corpo della ruota portafiltri. È il riferimento radiale di tutto il progetto: il collare ci si appoggia e ogni raggio si misura dal centro di questo cilindro.",
    },
    "H_body": {
        "description": "Altezza totale del corpo a ruota chiusa, dalla faccia lato camera a quella lato telescopio. Fissa lo zero e il fondo scala di tutte le quote assiali.",
    },
    "Th_wall_front": {
        "description": "Spessore del piatto frontale, lato camera. Sopra di esso appoggia la flangia anteriore del collare; sotto comincia l'aria sopra il disco.",
    },
    "Th_wall_radial": {
        "group": "filter_wheel_body - misurata al bordo apertura",
        "description": "Spessore della parete laterale misurato sul bordo tagliato dell'apertura. Diverso da quello frontale, quindi ha un parametro suo.",
    },
    "H_opening": {
        "description": "Altezza netta dell'apertura laterale, ricavata da due letture in profondità dalla faccia. È lo spazio in cui deve passare il mozzo della frizione.",
    },
    "Th_wall_rear": {
        "description": "Spessore del fondello lato telescopio, per differenza. Ospita i quattro fori M3 filettati a 6 mm su cui si avvita il collare, e con lui la staffa del sensore.",
    },
    "Read_caliper_opening": {
        "group": "MISURATA - becco sul piatto, opposto sul cilindro",
        "description": "Lettura del calibro attraverso il corpo: un becco sul piatto dell'apertura, l'altro sul cilindro opposto. È la misura primaria da cui discendono piano di taglio, corda e sporgenza del bordo.",
    },
    "D_plane_opening": {
        "group": "filter_wheel_body - piano del taglio dritto",
        "description": "Distanza dall'asse del piano su cui è stata fresata l'apertura. L'apertura è un taglio dritto, non un settore curvo.",
    },
    "Chord_opening": {
        "description": "Lunghezza dell'apertura misurata in linea retta fra le due estremità. Deve restare più larga del diametro della frizione con margine.",
    },
    "Proj_rim": {
        "group": "documentazione - il bordo zigrinato sporge dal piatto",
        "description": "Di quanto il bordo zigrinato del disco sporge oltre il piano del taglio. Positivo significa che la frizione non tocca mai il piatto fresato.",
    },
    "Chord_slot": {
        "description": "Lunghezza della scanalatura frontale, più corta dell'apertura perché il suo piano è meno profondo.",
    },
    "Dp_slot_front": {
        "group": "filter_wheel_body - scanalatura sulla faccia camera, tutta la corda",
        "description": "Profondità radiale della scanalatura ricavata nella faccia lato camera, che corre per tutta la corda. È un percorso di luce verso l'interno e va chiusa.",
    },
    "Th_rib_labyrinth": {
        "group": "collare - costola che entra nella scanalatura",
        "description": "Spessore della costola del collare che entra nella scanalatura frontale. Mezzo millimetro di gioco per lato.",
    },
    "H_rib_labyrinth": {
        "description": "Quanto la costola affonda nella scanalatura. Più è profonda, più lungo è il percorso che la luce dovrebbe fare per entrare.",
    },
    "Disc_rotating": {
        "description": "Diametro del disco che porta i filtri. La frizione lo tocca sul bordo zigrinato.",
    },
    "Th_disc": {
        "description": "Spessore del disco al bordo, smussi compresi.",
    },
    "Band_knurled_net": {
        "description": "Larghezza della sola zigrinatura, tolti gli smussi di 0,2 mm per lato. È la superficie utile al contatto e limita la larghezza del battistrada.",
    },
    "Z_plane_mid_disc": {
        "group": "TUTTI - datum assiale",
        "description": "Quota del piano medio del disco dalla faccia lato camera. È il datum assiale del progetto: il battistrada ci si centra sopra.",
    },
    "Air_above_disc": {
        "description": "Spazio libero fra la faccia interna del piatto frontale e la faccia anteriore del disco.",
    },
    "R_disc": {
        "description": "Raggio del disco. Il contatto della frizione avviene esattamente qui.",
    },
    "N_holes_filter": {
        "group": "riferimento - disco portafiltri; CONTATI",
        "description": "Numero dei fori portafiltri del disco, equidistanti. Cinque sulla ruota di riferimento, la StarDikor: fissa l'angolo fra due fori (360 / 5 = 72 gradi) e, col ponte fra due fori, il raggio della circonferenza dei fori.",
    },
    "D_thread_filter": {
        "group": "riferimento - disco portafiltri; filetto M48x0,75",
        "description": "Diametro nominale del filetto in cui si avvitano i filtri: M48 x 0,75, il filetto normale dei filtri da 2 pollici. Quota di norma, non di calibro. Il foro NON si disegna a questo diametro: vedi D_hole_filter.",
    },
    "Pitch_thread_filter": {
        "group": "riferimento - disco portafiltri; filetto M48x0,75",
        "description": "Passo del filetto dei filtri, M48 x 0,75 (normale, passo fine ISO).",
    },
    "D_hole_filter": {
        "group": "riferimento - disco portafiltri; STIMATO dal filetto",
        "description": "Diametro dei fori portafiltri come li disegna il modello: il diametro di NOCCIOLO della madrevite, D1 = D - 1,08253 P (profilo base ISO 68-1 / ISO 965), 47,19 mm per M48 x 0,75. Il materiale che c'è sono le creste del filetto: da qui si misurano il ponte fra due fori e la corona verso il bordo. Un raggio di 25,5 scritto a mano (foro Ø51), a 48 mm dal centro, taglierebbe di 1 mm il bordo di un disco Ø145; il disco vero ha i fori chiusi (da una foto del disco di riferimento: circa 47 mm, circa 3,2 mm di corona).",
    },
    "W_web_filter": {
        "group": "riferimento - disco portafiltri; STIMATO a mano, da misurare",
        "description": "Materiale fra due fori portafiltri vicini, nel punto più stretto. STIMATO A MANO sulla ruota di riferimento, NON col calibro: misurarlo vuol dire smontare la ruota. Da misurare col calibro quando la ruota sarà smontata. Con D_hole_filter e N_holes_filter dà il raggio della circonferenza dei fori, cioè l'asse ottico: 0,3 mm di errore qui spostano l'asse di 0,26 mm.",
    },
    "Off_hole_optical": {
        "group": "riferimento - foro ottico decentrato rispetto al centro disco; STIMATO",
        "description": "Di quanto l'asse ottico è decentrato rispetto al centro del disco: il raggio della circonferenza dei fori portafiltri, perché un filtro in posizione STA sull'asse ottico, e quindi non possono essere due numeri. Due fori vicini distano 2 R sin(36°) da centro a centro, cioè un foro più un ponte: R = (ponte + D1) / (2 sin(180 / n)), 45,67 mm. Torna con una foto del disco di riferimento smontato (circa 45,8, scala sul Ø145) e lascia 3,24 mm di corona, la foto dice circa 3,2. Scartato un 48 mm scritto a mano e classificato MISURATO senza traccia di cosa fosse stato misurato: coi fori Ø51 tagliava il bordo, e 48 è anche la misura del filetto dei filtri e il valore di R_envelope_optical, da cui probabilmente veniva. È una STIMA finché il ponte non si misura col calibro. Tutto quello che sta sull'asse ottico la segue: il foro ottico del corpo, l'ingombro del rotatore e i tagli che fa nel collare, nella staffa e nel coperchio del sensore. La finestra dell'elettronica sta dal lato opposto.",
    },
    "D_clutch": {
        "description": "Diametro di contatto della ruota di frizione. Governa il rapporto di riduzione e, tramite l'interasse, la posizione del motore rispetto al corpo.",
    },
    "Cd_motor": {
        "description": "Distanza fra centro disco e asse della frizione. Con il diametro attuale il motore resta interamente fuori dal corpo.",
    },
    "Off_pivot": {
        "description": "Distanza del perno dal punto di contatto, misurata sulla perpendicolare alla congiungente degli assi. Il vincolo cinematico è la retta, non la distanza: qualsiasi valore va bene purché il mozzo del perno resti fuori dal corpo.",
    },
    "L_arm": {
        "description": "Distanza fra asse perno e asse motore.",
    },
    "R_pivot": {
        "description": "Raggio a cui cade il perno, dal centro del disco.",
    },
    "Ang_pivot": {
        "description": "Angolo del perno rispetto alla congiungente degli assi.",
    },
    "Ratio_reduction": {
        "group": "documentazione",
        "description": "Giri di frizione per giro di disco.",
    },
    "Th_clutch": {
        "group": "clutch_section - larghezza battistrada",
        "description": "Larghezza del battistrada in TPU. Più stretto della fascia zigrinata, così resta tutto in presa anche con qualche decimo di disallineamento.",
    },
    "D_hub_clutch": {
        "description": "Diametro del nucleo in ASA su cui è stampato l'anello TPU.",
    },
    "D_shoulders_clutch": {
        "description": "Diametro delle due spalle che impediscono al battistrada di camminare assialmente.",
    },
    "H_hub_clutch": {
        "group": "frizione",
        "description": "Quanto è alto il MOZZO della frizione, cioè la parte che sta attorno al battistrada: la spalla bassa, la fascia del battistrada, la spalla alta. Non comprende il collare del grano, che ci sta sopra ed è un'altra cosa. Era 8 ed era una scelta, di quando il mozzo era un cilindro unico da cui la fascia veniva ritagliata; da quando il mozzo comincia alla spalla bassa e finisce alla spalla alta, la sua altezza non è più libera - è quello che le tre fasce sommano. Restava 8 mentre il mozzo era diventato 5, e i controlli delle catene assiali misuravano tre millimetri che non c'erano.",
    },
    "Z_top_clutch": {
        "group": "clutch_section - quota sommita mozzo",
        "description": "Quota della sommità del mozzo. Insieme all'altezza posiziona la frizione dentro l'apertura.",
    },
    "H_shoulder_clutch": {
        "description": "Altezza di ciascuna spalla di ritegno.",
    },
    "R_fillet_tread": {
        "description": "Raccordo sulle due spalle del battistrada. Toglie il carico di spigolo senza ridurre la zona cilindrica utile.",
    },
    "N_teeth_clutch": {
        "group": "frizione STEP - pattern circolare",
        "description": "Denti radiali sul mozzo che trasmettono la coppia al TPU. Lavorano insieme al beam interlocking dello slicer, a scale diverse.",
    },
    "Th_teeth_clutch": {
        "group": "frizione STEP",
        "description": "Profondità radiale dei denti, cioè quanto la coda di rondine entra nel mozzo.",
    },
    "L_teeth_clutch": {
        "group": "frizione STEP",
        "description": "Larghezza del dente alla BOCCA, sul bordo del mozzo. Verso il fondo si allarga: è la coda di rondine.",
    },
    "Widen_tail_dovetail": {
        "group": "frizione - denti",
        "description": "Di quanto il dente è più largo in fondo che alla bocca. È quello che rende l'incastro una coda di rondine: l'anello di TPU non può più sfilarsi in senso radiale, e la coppia non conta più solo sull'adesione fra i due materiali. Si stampa senza sbalzi perché il profilo sta nel piano di stampa ed è estruso lungo l'asse. PROVATO IN MANO: tirando l'anello di TPU su una frizione costampata, NON SI STACCA. È la verifica che nessun controllo poteva fare - la tenuta fra due materiali non sta nel solido - ed è la ragione per cui i denti esistono: che la coppia non dipenda dall'adesione fra ASA e TPU. ATTENZIONE A COSA HA PROVATO DAVVERO: il pezzo di prova è stato affettato con 'Use beam interlocking' di PrusaSlicer attivo, quindi la prova dice che DENTI PIÙ INTERLOCKING insieme tengono, e non separa i due contributi. Chi stampasse senza quell'opzione non ha questa prova, e chi volesse togliere i denti fidandosi dello slicer non la ha affatto.",
    },
    "D_collar_grub": {
        "group": "frizione - collare dell'inserto",
        "description": "Diametro del collare che, sotto il battistrada, porta l'inserto a caldo del grano. Trenta e non più: il collare gira col mozzo, quindi il suo raggio va sommato all'interasse - a Ø30 arriva a r 82,5 dal centro del disco, cioè resta fuori dal corpo ruota (79) e passa oltre le teste delle viti del motore, che stanno a 15,6 dall'albero.",
    },
    "H_collar_grub": {
        "group": "frizione - collare dell'inserto",
        "description": "Quanto è lungo il collare che porta l'inserto del grano. Discende dal PIÙ GRANDE fra due vincoli, e sono due cose diverse che chiedono la stessa quota.\n\nIl primo è quello che il collare deve CONTENERE: il foro dell'inserto più una parete sopra e una sotto, 6,65. Il secondo è quello che deve lasciar PASSARE, e vale di più: il saldatore entra orizzontale in asse con l'inserto, e col foro centrato sull'altezza del collare la punta scende di mezzo suo diametro sotto quell'asse. Se il collare è più corto della punta, la punta finisce sotto la base del collare e va a sbattere contro l'anello che trattiene il battistrada, che sta lì sotto e non si può togliere. Otto e mezzo, cioè la punta col suo franco: l'espressione porta QUESTO vincolo, che è quello che vince, e che l'altro sia soddisfatto lo dice un controllo in solids_wheel.py. Una sola relazione e un controllo si leggono; un max() di due relazioni no - e l'editor dei parametri nemmeno lo valuta.\n\nEra Z_top_clutch - Free_collar_arm, la lunghezza che il collare aveva quando PENDEVA sotto il mozzo: una quota che col collare di sopra non c'entrava più niente.",
    },
    "Free_collar_arm": {
        "group": "frizione - collare dell'inserto",
        "description": "Quanto il collare resta sopra la faccia del braccio. Il collare scende fin qui perché l'altezza serve all'inserto: sopra il battistrada ce ne sono solo tre millimetri, e l'apertura del corpo e il cielo del vano non lasciano crescere il mozzo verso l'alto.",
    },
    "Free_above_arm": {
        "group": "collare - scasso di passaggio del braccio",
        "description": "Di quanto la faccia di sotto del collare si ritira SOPRA il braccio, nel settore in cui il braccio passa. Non è Free_collar_arm, che è un'altra coppia di facce - quella del collare del grano sulla frizione. Serviva e non c'era: lo scasso di passaggio scavava il collare da sotto e si fermava esattamente a z 0, che è la quota della faccia di sopra del braccio (-Z_face_motor + Th_arm). Le due facce restavano COMPLANARI, cioè il braccio strisciava sul collare per 159 mm2 - e nessun controllo se ne accorgeva, perché due facce che si toccano hanno compenetrazione ZERO e l'audit misurava proprio quella: il contatto si vede solo muovendo il braccio col pezzo avvitato. Tre decimi e non i due dell'arretramento del mozzo: al perno le due facce sono concentriche e girano una sull'altra, qui invece il braccio le SPAZZA sotto, e la mensola del collare oltre r 79 è a sbalzo. Il ritiro comincia a r = D_body/2 e non più in dentro: fino a lì il collare si appoggia alla faccia del corpo ruota, e ritirarlo vorrebbe dire scollarlo dal suo piano di appoggio.",
    },
    "Wall_below_insert_grub": {
        "group": "frizione - collare dell'inserto",
        "description": "Parete di ASA sotto il tunnel dell'inserto. È la più sottile del giunto: sopra il tunnel il mozzo continua pieno per tre millimetri, di lato il materiale abbonda, sotto resta questo. Più di un millimetro non ci sta senza alzare il mozzo.",
    },
    "Z_base_collar_grub": {
        "group": "frizione - collare dell'inserto",
        "description": "Dove comincia il collare che porta l'inserto del grano: subito sopra la spalla che trattiene il battistrada. Discende dal PIANO DEL DISCO e non dall'altezza del mozzo, perché è il disco a decidere dove sta il battistrada e tutto il resto gli va attorno. Un altro cilindro fra la spalla e il collare, Ø44 alto 2, è stato tolto: non faceva niente se non allontanare il grano dal battistrada e allungare il pezzo.",
    },
    "Z_insert_grub": {
        "group": "frizione - collare dell'inserto",
        "description": "Quota dell'asse del grano e del suo inserto, dalla faccia lato camera del corpo. Discende dal franco col braccio, dalla parete sotto e dal diametro del foro dell'inserto: non è scelta.",
    },
    "Cl_clear_grub": {
        "group": "frizione - foro di passaggio del grano",
        "description": "Quanto il foro oltre l'inserto è più largo del grano: il grano ci passa libero e prende solo nell'inserto.",
    },
    "Side_motor": {
        "description": "Lato della flangia del NEMA14.",
    },
    "L_motor": {
        "description": "Lunghezza del corpo motore. Sporge dal lato camera, dove c'è spazio.",
    },
    "Cd_holes_motor": {
        "description": "Interasse dei quattro fori M3 di fissaggio, in quadrato.",
    },
    "D_circle_motor": {
        "description": "Diametro del cerchio di centraggio sulla flangia. È lui a centrare il motore sul braccio, non le viti.",
    },
    "H_circle_motor": {
        "description": "Sporgenza del cerchio di centraggio dal piano dei fori.",
    },
    "Cl_clutch_shaft": {
        "group": "frizione - foro dell'albero",
        "description": "Gioco di scorrimento fra il foro del mozzo della frizione e l'albero del motore. Mancava del tutto: il foro era D_shaft esatto, cioè il nominale dell'albero, e quel mozzo deve INFILARSI a mano e poi essere bloccato dal grano, non montato a forza su acciaio rettificato. L'eccentricità che il gioco permette è al più la sua metà, 0,075, e contro la corsa del braccio - dove un grado vale un millimetro di schiacciamento del TPU - non si vede. La compensazione dei fori vale per la frizione come per ogni altro foro stampato.",
    },
    "D_hole_clutch": {
        "group": "frizione - foro disegnato",
        "description": "Il diametro con cui il foro dell'albero viene DISEGNATO: il nominale dell'albero, più il gioco di scorrimento, più la compensazione di stampa. Erano tre quote diventate una sola, e il risultato era un foro che stampato misurava 4,8 su un albero da 5: la frizione non ci entrava.",
    },
    "D_mouth_hole_clutch": {
        "group": "frizione - invito del foro",
        "description": "Diametro dell'invito in bocca al foro dell'albero, sulla faccia da cui la frizione si infila. Guida il mozzo mentre scende sull'albero, ed è la pratica che il progetto usa su ogni foro.",
    },
    "H_leadin_hole_clutch": {
        "group": "frizione",
        "description": "Profondità dell'invito: metà della differenza dei diametri, cioè quarantacinque gradi.",
    },
    "D_shaft": {
        "description": "Diametro dell'albero motore.",
    },
    "L_shaft": {
        "group": "documentazione - dal piano di appoggio",
        "description": "Lunghezza utile dell'albero dal piano di appoggio. Determina quanta presa resta nel mozzo della frizione.",
    },
    "Z_flat_shaft": {
        "group": "frizione - piano della fresata",
        "description": "Quanto il piano della fresata dista dall'ASSE dell'albero. È la quota di progetto della fresata, e finora non esisteva: nel solido c'era scritto 'Flat_shaft - raggio del foro DISEGNATO', che è un'altra cosa - mescola la fresata dell'albero col gioco e con la compensazione di stampa del foro, e il piano del foro finiva a 1,85 invece che a 2,15, cioè tre decimi dentro l'albero. È la stessa confusione fra quota di progetto e quota di disegno già trovata quattro volte in questo progetto; si è vista nella sezione dello slicer, non in un controllo.",
    },
    "Z_flat_hole": {
        "group": "frizione - corda del foro",
        "description": "Dove si disegna la corda che taglia il foro dell'albero. È il piano della fresata più lo stesso scostamento radiale che ha il foro tondo - metà del gioco di scorrimento più metà della compensazione di stampa - perciò il piano del foro sta alla fresata dell'albero come la parete del foro sta al suo diametro. Da qui discende la corda: chi cambia il gioco o la compensazione se la ritrova spostata da sola.",
    },
    "Flat_shaft": {
        "group": "frizione - foro a D sull'albero",
        "description": "Quota sulla fresata piana dell'albero del motore: il grano ci appoggia sopra invece che su un tondo, e da quando il foro della frizione è una D ci appoggia anche il piano del foro. CONFERMATA sul motore della costruzione di riferimento. Prima era un dato di CATALOGO e non misurato, ed era l'unica quota da cui dipendeva se la frizione si infila: con il foro a D la corda sta 0,15 sopra il piano della fresata, quindi una fresata meno profonda di 4,5 avrebbe stretto.",
    },
    "D_grub": {
        "group": "frizione - grano di bloccaggio",
        "description": "Grano che blocca la frizione sull'albero, premendo sulla fresata. Si avvita in un INSERTO A CALDO, non nell'ASA: il filetto formato nella plastica si spana e, sotto carico, cede col tempo, e un grano che perde la presa fa slittare la frizione sull'albero senza dirlo.",
    },
    "Th_arm": {
        "description": "Spessore del braccio. Deve ospitare i due cuscinetti nel mozzo del perno e restare tutto sopra la faccia lato camera per non incontrare il collare.",
    },
    "Cl_tip_iron_deep": {
        "group": "colonna del perno - canale del saldatore",
        "description": "Il franco attorno alla punta del saldatore quando il canale è PROFONDO, al posto di Cl_tip_iron che vale mezzo millimetro. Serve al canale che scende dal pavimento alla sede dell'inserto del perno: quaranta millimetri di canale con mezzo millimetro di franco vogliono dire che la punta, scendendo, struscia sulla parete per tutta la corsa e la fonde. Un canale corto lo si imbocca e si esce subito; uno profondo lo si percorre.",
    },
    "D_channel_iron_deep": {
        "group": "colonna del perno - canale del saldatore",
        "description": "Il diametro del canale profondo del saldatore: Ø9,5 contro gli Ø8,5 di quello corto. Il canale resta aperto sul pavimento a montaggio finito, e lo chiude un tappino a incastro.",
    },
    "Z_top_arm": {
        "group": "arm_plan - faccia superiore",
    },
    "Z_axis_spring": {
        "group": "asse della molla di precarico",
    },
    "Free_iron_flange": {
        "group": "asse della molla di precarico",
    },
    "L_screw_pivot": {
        "group": "vite del perno armato",
    },
    "H_tab_spring_arm": {
        "group": "braccio - linguetta di appoggio della molla",
    },
    "L_chamfer_tab_spring_arm": {
        "group": "braccio - smusso della linguetta della molla",
    },
    "Th_tab_spring_arm": {
        "group": "braccio - linguetta di appoggio della molla",
    },
    "Z_bottom_arm": {
        "group": "arm_plan - faccia inferiore",
        "description": "Il braccio è rialzato, quindi la sua faccia superiore sta a Z_top_arm e non a z 0. La faccia INFERIORE del braccio, quella verso il telescopio: è dove affiora la punta del perno, dove comincia la sede dei cuscinetti, dove appoggia la rondella e fin dove la gonna della scatola deve stare larga. Un tempo coincideva con -Z_face_motor: il braccio era una piastra di spessore unico e il motore si avvitava sul suo fondo, quindi un numero solo serviva per due cose. Rovesciando la frizione il motore è salito e la piastra si è scalinata, e le due cose si sono separate: diciassette punti del progetto leggevano -Z_face_motor intendendo QUESTA. Tenerle in un numero solo faceva cercare all'audit la sede dei cuscinetti a una quota dove il braccio non c'è più.",
    },
    "D_base_clutch": {
        "group": "frizione - disco sotto la spalla",
        "description": "Il diametro del disco della frizione SOTTO la spalla del battistrada. Era uguale a D_hub_clutch, 44, e non esisteva come quota a sé. Ridotto a circa 30 per restare fuori dalle viti, e scritto come RELAZIONE invece che a mano: il disco si ferma dove cominciano le teste delle viti del motore, cioè alla loro diagonale meno mezza testa meno il franco. Vengono 29,66, e se un giorno il motore cambia interasse o le viti cambiano testa il disco le segue da solo.\n\nPerché restringerlo invece di scavarci dentro, che era la prima strada: misurate, le due si equivalgono in tutto - stessa massa 11,2 g, stesso franco 1,90 mm, stessi sbalzi. Ma la cava lascia fuori di sé un anello di 0,87 mm alto uno, attaccato solo in cima alla spalla: una bavetta che si stampa male e si stacca. Lo scalino no.",
    },
    "Cl_head_screw_clutch": {
        "group": "frizione - disco sotto la spalla",
        "description": "Il franco RADIALE fra il disco di fondo della frizione e le teste delle viti del motore. Da non confondere con Cl_head_clutch_z, che è quello in altezza: per un momento sono stati la stessa quota per una svista, e un diametro si è trovato dentro un franco verticale.",
    },
    "Cl_head_clutch_z": {
        "group": "frizione - franco sopra le teste delle viti",
        "description": "Il franco IN ALTEZZA fra la testa di una vite del motore e il fondo della frizione. È quello che decide quanto il motore può salire, cioè quanto la macchina può essere bassa: il motore sale finché le teste non toccano la frizione. Un millimetro e non meno, perché la frizione gira e la testa è un pezzo comprato la cui altezza vera varia di qualche decimo fra un lotto e l'altro.",
    },
    "Cl_head_screw_clutch#2": {
        "group": "frizione - scasso delle teste",
        "description": "Quanto lo scasso nel fondo della frizione sta largo oltre la testa della vite del motore, per parte. Non è un accoppiamento: la frizione GIRA e le teste stanno ferme, quindi quello che passa sotto lo scasso cambia a ogni giro e il franco serve solo a non sfiorarle. Otto decimi tengono conto del fatto che la posizione vera delle viti dipende da come il motore si è centrato nella sua sede.",
    },
    "Th_plate_motor": {
        "group": "arm_plan - piastra del motore",
        "description": "Lo spessore della piastra del braccio sotto il motore. NON è Z_face_motor, e la differenza è il punto: Z_face_motor dice quanto la faccia del motore sta sotto il piano di riferimento, questo dice quanto materiale c'è. Finché la piastra era spessa uguale dappertutto le due coincidevano; da quando cresce in su si separano. In su si può perché al motore il collare non c'è - sta a r 86 e il motore a 97,5 - e sopra la piastra c'è solo la frizione.",
    },
    "Th_min_plate_motor": {
        "group": "arm_plan - piastra del motore",
        "description": "Lo spessore minimo che la piastra del braccio può avere sotto il motore. Si confronta con Th_plate_motor, che è il materiale che c'è davvero, e non con Z_face_motor, che dice soltanto dove sta la faccia. Non è una quota che disegna qualcosa: è una SOGLIA, e sta qui perché Z_face_motor non è più una scelta e nessuno si accorgerebbe che la piastra si è assottigliata. Ogni millimetro che il motore sale - ed è un obiettivo, perché la macchina più bassa è meglio - è un millimetro che la piastra perde. Due e mezzo sono quanto restano con la frizione rovesciata, cioè il caso è al limite per costruzione: portando il grano più in alto la piastra sparisce, e il generatore si ferma invece di produrre un braccio che cede in mano.",
    },
    "Z_face_motor": {
        "group": "arm_plan - sopra la faccia sup. corpo",
        "description": "Quanto la faccia di appoggio del motore sta sopra la faccia lato camera. Ha seguito tre cose diverse, e le tre raccontano il ragionamento. Era una SCELTA, 8 mm. Poi, rovesciata la frizione, è diventata la presa dell'albero sul grano: il motore saliva quanto bastava perché l'albero arrivasse al grano. Poi è stato tolto il cilindro Ø44 sopra la spalla, il grano è sceso e quel vincolo si è allentato: il motore avrebbe potuto SCENDERE, cioè la macchina sarebbe tornata più alta, e allora è passata a discendere dalla piastra.\n\nAdesso discende dalle TESTE DELLE VITI DEL MOTORE, e questo è il vincolo vero: la piastra cresce sopra il piano z 0, le teste salgono con lei, e sopra le teste c'è il fondo della frizione. Il motore sale finché le teste non toccano la frizione. Il giro è chiuso: più la macchina è bassa meglio è, e il limite è lì.\n\nSi guadagnano millimetri in tre modi, tutti e tre visibili nell'espressione: piastra più sottile (ma ha un minimo), viti a testa più bassa, oppure alzare Z_top_clutch, cioè cominciare il mozzo della frizione più in alto - che è l'effetto di aver tolto il disco di fondo.",
    },
    "D_hub_pivot": {
        "description": "Diametro del mozzo attorno al perno, sul braccio e sul collare. Deve contenere la sede dei cuscinetti e le loro flange, e restare fuori dalla superficie del corpo ruota.",
    },
    "R_fillet_support_pivot": {
        "group": "collare - gola fra il supporto del perno e la fascia",
        "description": "Raggio della gola che raccorda il supporto del perno alla fascia del collare. Il supporto attaccato di spigolo aveva poca superficie a contatto col corpo, ed è anche il punto dove il momento del braccio si scarica. Tre millimetri sono quanto la gola può allargarsi restando dentro il settore del collare e fuori dal passaggio del braccio; più grande e la si ritroverebbe tagliata dallo scasso, che è peggio di non averla, perché lascerebbe uno spigolo a metà.",
    },
    "Z_mouth_insert_pivot": {
        "group": "collare - bocca della sede dell'inserto del perno",
        "description": "DERIVATA: dalla faccia di sotto della rondella del perno, una vite di L_screw_pivot, più il mezzo millimetro di inserto che resta sopra la sua punta - la stessa relazione che la faceva 10 col braccio a -8. Alzando il braccio la bocca sale altrettanto, quindi la vite resta una M3 x 20, quella facile da comprare. Quota della BOCCA della sede dell'inserto M3 del perno armato. Non è più la faccia superiore del supporto, che adesso sale fino a Z_top_support_pivot: sopra questa bocca c'è il canale da cui scende la punta del saldatore. Tenerla ferma a 10 è quello che lascia la vite una M3 x 20 di catalogo, mentre portarla in cima al supporto avrebbe voluto 26 mm sotto testa, cioè una lunghezza che non esiste e che sporgerebbe contro il cielo del vano. È anche il capo alto della vite: da sotto la sua testa alla cima del mozzo ci sono 20,5 mm, cioè una M3 x 20 da catalogo. Era scritta a mano in solids_body_collar come _z_cima = 10.0, e la vite - che non era nel modello - non poteva discenderne.",
    },
    "Free_assembly_compartment": {
        "group": "scatola - cielo del vano; collare - cima del supporto del perno",
        "description": "Quanto dev'essere libero fra il contenuto del vano meccanico e il cielo che lo chiude. Non è una tolleranza: è il franco per INFILARE la scatola sopra il meccanismo già montato, che è il modo in cui la macchina si monta, e il controllo che lo sorveglia c'era già - ma il numero stava scritto a mano dentro di lui. Adesso lo stesso parametro decide anche fin dove può salire il supporto del perno, che nel vano è l'oggetto più alto: alzandolo a mezzo millimetro dal cielo, come era stato fatto, il controllo del montaggio ha suonato subito.",
    },
    "Marg_top_support": {
        "group": "collare - cima del supporto del perno",
        "description": "Di quanto la cima del supporto sta più bassa del minimo che il franco di montaggio impone. Un decimo, e sta nel PEZZO: costruendo la cima esattamente al limite, il franco esce 2,00 tondi e il controllo del vano - che confronta due misure prese sui solidi - lo rilegge un'inezia sotto e suona su un pezzo giusto. Allargare invece la soglia del controllo avrebbe coperto anche i franchi davvero insufficienti. Stessa ragione di Marg_ang_side_support.",
    },
    "Z_top_support_pivot": {
        "group": "collare - cima del supporto del perno",
        "description": "Il supporto è una COLONNA PIENA che entra nel cielo: la sua cima sta mezza parete dentro la soletta del cielo, così colonna e cielo si fondono in un pezzo solo. Sopra l'inserto scende soltanto il canale del saldatore, dal foro nel cielo. SCARTATO prima, quando il supporto si fermava sotto il cielo: un supporto isolato alto 20 mm (da 9,8, per avere più superficie a contatto col corpo) non ci stava - a 16 chiudeva il vano, il cui cielo era stato ABBASSATO di dieci millimetri apposta per alleggerire la scatola. Quella versione arrivava a 13,7, con la cima due millimetri sotto il cielo, il franco per infilare la scatola sopra il meccanismo già montato.",
    },
    "D_access_iron_pivot": {
        "group": "scatola+collare - accesso alla sede del perno",
        "description": "Il foro nel cielo del vano meccanico, in asse col perno. NON è l'accesso alla VITE del perno, come era stato descritto all'inizio pensando che la vite entrasse dal lato telescopio - la testa di quella vite sta in BASSO, sotto la rondella, e la vite sale nell'inserto in cima al mozzo. Dal cielo non passa la vite: passa la PUNTA DEL SALDATORE che pianta l'inserto, e per quella il diametro giusto è quello del canale profondo, non quello della testa di una M3.\n\nPrima dell'unione l'inserto si piantava a collare nudo, dall'alto, e il canale finiva in aria; adesso sopra c'è il cielo, e il canale deve attraversarlo.",
    },
    "D_access_driver_pivot": {
        "group": "scatola+collare - accesso alla vite del perno",
        "description": "Il foro nel PAVIMENTO, in asse col perno, da cui il cacciavite raggiunge la testa della vite del perno. La vite si avvita da sotto - la sua testa sta sotto la rondella, a una ventina di millimetri dal pavimento - e con la scatola chiusa quella è l'unica strada. Discende dalla testa della vite e non dal cacciavite, perché è la testa a dover passare mentre si cala la vite in posizione.\n\nIl foro resta aperto a montaggio finito e lo chiude un tappino a incastro: è un foro sul piano di appoggio, cioè la faccia da cui entra la polvere.",
    },
    "D_clear_screw_pivot": {
        "group": "collare - foro per la vite dentro il perno",
        "description": "Foro che attraversa perno e mozzo per il lungo. È un PASSAGGIO largo, non un foro giusto: sul perno da 5 lascia 0,8 mm di parete per lato, cioè due perimetri, e una vite forzata lì dentro lo spaccherebbe invece di rinforzarlo. La vite non deve toccare la plastica di fianco: lavora tirata fra l'inserto in cima e la rondella in fondo.",
    },
    "Dp_seat_insert_M3_pivot": {
        "group": "collare - sede dell'inserto in cima al mozzo",
        "description": "Profondità della sede dell'inserto, in cima al mozzo. Mezzo millimetro più dell'inserto, per la stessa ragione della sede M4 del grano: a filo, l'inserto spingerebbe in fondo la plastica fusa invece di lasciarla rifluire.",
    },
    "D_leadin_insert_M3": {
        "group": "collare - invito della sede",
        "description": "Diametro della bocca svasata sopra la sede dell'inserto M3.",
    },
    "Dp_leadin_insert_M3": {
        "group": "collare - invito della sede",
        "description": "Profondità dello smusso conico in bocca alla sede dell'inserto M3.",
    },
    "D_washer_pivot": {
        "description": "Diametro esterno della rondella stampata. Sta sotto l'anello interno del cuscinetto e deve premere SOLO su quello: quattro decimi meno dell'anello la tengono lontana dallo schermo, e resta comunque molto più stretta del foro della flangia, che è dell'anello esterno.",
    },
    "D_hole_washer_pivot": {
        "description": "Foro della rondella: passaggio per il gambo della vite, ed è lo stesso foro di passaggio M3 disegnato di tutti gli altri. Era D_clear_screw_pivot + 0,2: da quando il passaggio dentro il perno porta la compensazione di stampa, quel +0,2 l'avrebbe contata due volte. L'ha trovato il controllo delle espressioni.",
    },
    "L_bushing_pivot": {
        "group": "pivot_washer - bussola dentro i cuscinetti",
    },
    "Ch_bushing_pivot": {
        "group": "pivot_washer - invito della bussola",
    },
    "Th_washer_pivot": {
        "description": "Spessore della rondella. Due e mezzo la rendono stampabile e mettono la testa della vite a quota tale che una M3 x 20 da catalogo arrivi in presa nell'inserto senza sfondare il mozzo.",
    },
    "D_head_screw_M25": {
        "group": "comprati - teste delle viti M2,5",
        "description": "Diametro della testa delle M2,5, a BRUGOLA nella costruzione di riferimento: quota di norma della DIN 912 cilindrica, di catalogo e non di calibro. Sono le due viti che tengono il coperchio del sensore.",
    },
    "H_head_screw_M25": {
        "group": "comprati - teste delle viti M2,5",
        "description": "Altezza della testa a brugola delle M2,5, DIN 912. Serve a vedere se sopra la testa resta il posto per la chiave, che è il difetto che una vite non modellata non fa vedere.",
    },
    "D_head_screw_M2": {
        "group": "comprati - teste delle viti M2",
        "description": "Diametro della testa delle M2, SVASATE nella costruzione di riferimento: quota di norma della DIN 7991 a testa conica, di catalogo. La svasata non è un dettaglio estetico - sparisce nello spessore invece di appoggiare in piano, quindi vuole l'invito conico nel pezzo e cambia la geometria attorno al foro.",
    },
    "H_head_screw_M2": {
        "group": "comprati - teste delle viti M2",
        "description": "Altezza della testa svasata M2, cioè la profondità del cono. È anche quanto l'invito deve scendere nel pezzo perché la vite finisca a filo.",
    },
    "D_head_countersunk_M2": {
        "group": "comprati - teste svasate",
        "description": "Diametro della testa conica M2, DIN 7991. È lo stesso numero di D_head_screw_M2 perché le M2 della costruzione di riferimento sono svasate: sta qui lo stesso, in chiaro, perché il tipo di testa e la misura devono poter cambiare uno senza l'altro.",
    },
    "H_head_countersunk_M2": {
        "group": "comprati - teste svasate",
        "description": "Profondità del cono della testa svasata M2, DIN 7991.",
    },
    "D_head_countersunk_M25": {
        "group": "comprati - teste svasate",
        "description": "Diametro della testa conica M2,5, DIN 7991.",
    },
    "H_head_countersunk_M25": {
        "group": "comprati - teste svasate",
        "description": "Profondità del cono della testa svasata M2,5, DIN 7991.",
    },
    "D_head_countersunk_M3": {
        "group": "comprati - teste svasate; pannellino",
        "description": "Diametro della testa conica M3, DIN 7991. NON è D_head_screw_M3: quello è la cilindrica a brugola, 5,5, e serve ancora alla vite del perno, da cui discende il gradino della gonna interna. Sono due viti diverse e devono restare due quote diverse, se no cambiando testa alle viti del pannellino si sposta la gonna.",
    },
    "H_head_countersunk_M3": {
        "group": "comprati - teste svasate; pannellino",
        "description": "Profondità del cono della testa svasata M3, DIN 7991. Con lei lo svaso nel pannellino è profondo (D_head_countersunk_M3 - D_clear_screw_panel) / 2 su un cono a 90 gradi, cioè 1,3 mm: nella zona delle viti il pannellino è spesso 5, quindi sotto lo svaso restano 3,7 mm di materiale.",
    },
    "D_clear_screw_panel": {
        "description": "Foro di passaggio della M3 nel pannellino. Era 3,4 scritto a mano dentro il generatore, come raggio 1,7: qui diventa una quota, perché da lei discende la profondità dello svaso.",
    },
    "Ang_head_countersunk": {
        "group": "comprati - teste svasate",
        "description": "Angolo compreso del cono delle teste svasate, novanta gradi come vuole la norma metrica. È il dato che fa la differenza fra un invito che accoglie la testa e uno che la lascia sporgere.",
    },
    "D_head_screw_M3": {
        "group": "comprati - teste delle viti M3",
        "description": "Diametro della testa delle viti M3 del progetto. La testa a BRUGOLA è quella della costruzione di riferimento, quindi il diametro è quello di norma della DIN 912 cilindrica: di catalogo e non di calibro, ed è il motivo della classe R. Una testa a taglio o a croce sarebbe più larga, 6 mm circa, e da qui discende il gradino che la gonna interna si scava attorno al perno. Era scritto a mano come 2,75 di raggio dentro solids_assieme, e per la vite del perno non c'era affatto: la gonna si fermava dodici millimetri più in basso in nome di un ingombro che il modello non conteneva, e quello che il modello non contiene nessun controllo lo vede.",
    },
    "H_head_screw_M3": {
        "group": "comprati - teste delle viti M3",
        "description": "Altezza della testa delle viti M3, di catalogo per la DIN 912. Sulla vite del perno, sotto la rondella, porta il punto più basso del pacco a -13,5: è il numero che stava scritto nel commento di Z_skirt_inner.",
    },
    "L_screw_motor": {
        "group": "comprati - viti del motore",
    },
    "L_band_arm": {
        "description": "Larghezza della banda del braccio fra il mozzo del perno e la piastra del motore. Non segue il mozzo: portandola a 21 il bordo esterno andrebbe a sbattere contro il bosso della sede molla nella scatola.",
    },
    "L_plate_solid": {
        "description": "Fin dove la piastra resta larga quanto il motore, misurata dal centro del motore verso il perno. Sotto c'è comunque il taglio di R_rim_inner, che il fianco interno lo fa lui: quello che questo parametro governa è il fianco esterno. Portata a Side_motor / 2 la parte larga è il solo quadrato del motore e il braccio torna il cuneo di prima. Il cuneo aveva due difetti. La molla ci appoggiava su una rampa inclinata di 15 gradi rispetto al proprio asse, quindi premeva di spigolo, con sei newton buoni dei 22,3 che la spingevano a scivolare lungo il fianco: a trattenerla c'era solo la spina. E fermare la parte larga a metà strada non risolve, perché lo scalino fra la rampa e il fianco dritto è uno spigolo rientrante proprio dove la molla spinge. Tenendola per tutta la lunghezza il fianco è una retta sola, perpendicolare all'asse della molla, senza scalini, e il braccio guadagna un grammo e mezzo di sezione dove il momento è più grande.",
    },
    "Squash_clutch": {
        "group": "corsa del braccio - punto di lavoro",
        "description": "Di quanto l'anello di TPU va schiacciato contro il disco perché la frizione trascini. È il punto di lavoro, e finora non esisteva: Cd_motor vale R_disc + D_clutch / 2 al millesimo, cioè a riposo l'anello è esattamente TANGENTE al disco e non spinge. Dove il braccio si fermasse davvero lo decideva la molla contro la gomma, e non era scritto da nessuna parte. Quattro decimi sono il 20% dei due millimetri di gomma: abbastanza da avere presa, poco abbastanza da non cuocere l'anello. Chi monta un TPU più duro lo abbassi.",
    },
    "Wear_TPU_allowed": {
        "group": "corsa del braccio - quanto consumo seguire",
        "description": "Quanta gomma il meccanismo deve poter consumare continuando a spingere come il primo giorno. La molla ci pensa da sola, purché il braccio sia LIBERO di ruotare: un millimetro è metà dello spessore radiale dell'anello. Non è un numero di comodo: è lui a dire quanto spazio serve fra il braccio e il collare, e finora quello spazio era un avanzo, non una scelta. A grado vale circa un millimetro, quindi ogni decimo qui chiesto è un decimo di grado da liberare.",
    },
    "Marg_travel_arm": {
        "group": "corsa del braccio - eccentricità e tolleranze",
        "description": "Quanto aggiungere alla corsa per le cose che non si controllano: l'eccentricità del disco comprato, che fa oscillare il braccio a ogni giro, e la tolleranza di stampa dei pezzi che decidono l'interasse. Senza, la corsa basterebbe sulla carta e non sul banco.",
    },
    "Approach_travel_arm": {
        "group": "corsa del braccio",
        "description": "Di quanto la frizione deve poter entrare nel disco, sommando punto di lavoro, usura da seguire e margine. È il dato da cui discende l'estremo negativo della corsa, e quindi quanto largo dev'essere il passaggio del braccio nel collare.",
    },
    "Open_travel_arm": {
        "group": "corsa del braccio - fine corsa dal lato molla",
        "description": "Di quanto la frizione può staccarsi dal disco prima che un fine corsa la fermi. Oltre non serve andare, e questo è stato verificato sul montaggio invece che supposto: la scatola non si cala in asse - sollevandola di mezzo millimetro compenetra il collare per 199 mm3 - ma si infila facendo scorrere le sue sei orecchie a cavallo delle due flange del collare, e quel movimento non tocca mai il braccio; il braccio a sua volta si monta dopo, calandolo sul perno dal basso, e sfila libero per venti millimetri con scatola e collare già a posto. In nessun momento del montaggio serve aprirlo più di così. Il limite però ci vuole, perché da quella parte il braccio è libero finché la frizione non sbatte nella scatola, a +5,29 gradi misurati, e non lo ferma nessuno.",
    },
    "Cl_passage_arm": {
        "group": "collare - scasso di passaggio del braccio",
        "description": "Quanto lo scasso del collare sta largo attorno a quello che il braccio spazza, in tutta la sua corsa. Lo scasso c'è per far passare il braccio, ma le sue quote erano scritte a mano e non discendevano dalla corsa: per questo a -1,5 gradi il braccio toccava la flangia.",
    },
    "D_spring_out": {
        "group": "molla - diametro esterno",
        "description": "Diametro esterno della molla di precarico. Il numero c'era già nel progetto, ma viveva solo dentro la descrizione di D_spigot_spring: non essendo una quota, niente poteva dipenderne. Serve qui perché decide DOVE la molla tocca il fianco del braccio, e quindi fin dove il fianco deve restare dritto: l'impronta va da Att_spring - 4,45 a Att_spring + 4,45, cioè da 23,15 a 32,05.",
    },
    "Marg_nose_spring": {
        "group": "arm_plan - quanto l'ogiva sta lontana dalla molla",
        "description": "Di quanto l'ogiva del fianco si chiude PRIMA che cominci l'impronta della molla. Non è prudenza generica: l'ogiva è curva, e una molla che appoggiasse a cavallo del punto di tangenza tornerebbe a premere di spigolo, che è esattamente il difetto per cui L_plate_solid è stata portata a tutta lunghezza. Un millimetro tiene la tangenza fuori dall'impronta anche se R_rest_spring_arm si sposta di qualche decimo.",
    },
    "L_nose_arm": {
        "group": "arm_plan; braccio",
        "description": "Lunghezza dell'ogiva che raccorda il mozzo del perno al fianco della piastra, misurata dal perno lungo il braccio. Prima lì c'era uno SCALINO NETTO di 7,1 mm: il mozzo è r 10,5 e la piastra è larga 17,6, e i due si incontravano di spigolo. Sul fianco esterno lo scalino si vedeva tutto; su quello interno il taglio di R_rim_inner ne lasciava la punta, ed è la punta che si vedeva sporgere in alto a sinistra nella pianta. Adesso i due si raccordano con due archi tangenti - tangente orizzontale al mozzo, tangente al fianco dritto - e il fianco arriva alla piastra senza spigoli. La lunghezza la detta la molla, non l'estetica: l'ogiva deve chiudersi prima che la molla cominci ad appoggiare, se no la molla torna a premere su una superficie curva.",
    },
    "R_edges_plate_motor": {
        "group": "arm_plan; braccio",
        "description": "Raggio dei due spigoli esterni della piastra del motore, quelli che sul pezzo montato restano in fuori e si urtano maneggiandolo. Due e mezzo è una scelta di forma, non un massimo imposto: il limite vero sta molto più in là. I fori M3 del motore sembrano il vincolo ma non lo sono - il punto di un foro più vicino alla punta dello spigolo dista 4,91 mm, e il raccordo arretra sulla diagonale solo di R*(radice(2)-1), quindi comincerebbe a mangiare il foro appena oltre R 11,8, dove sarebbe comunque una forma diversa e non un raccordo. Il numero è stato verificato guastando apposta il pezzo: a R 6 il controllo sui fori taceva a ragione, ed è così che si è visto che il limite scritto qui prima, 3,47, era sbagliato - era una coordinata del foro, non una distanza.",
    },
    "D_seat_bearings_printed": {
        "group": "arm_plan - sede disegnata",
        "description": "Il diametro con cui la sede dei cuscinetti viene DISEGNATA. Quello di progetto resta D_seat_bearings: questo è lui più la compensazione di stampa, come si fa da sempre col foro del magnete. Le due quote erano diventate lo stesso numero, e la sede stampata misurava due decimi in meno del cuscinetto: non un accoppiamento forzato leggero - che è quello che ci vuole, perché l'anello esterno non deve girare nella plastica - ma dieci volte tanto. Su un anello da 13 bastano per impuntare le sfere, e un cuscinetto che gira duro annulla la ragione per cui c'è: il braccio deve restare libero di seguire il consumo del TPU - i cuscinetti andavano fatti entrare a forza. CONFERMATO IN MANO su un braccio stampato in ASA: i cuscinetti si infilano GIUSTI e il braccio ruota bene senza gioco - sta dove lo lasci, non balla e non scorre. È la prova che la compensazione andava messa: prima le due quote erano diventate lo stesso numero e la sede stampata usciva due decimi stretta. Come per la gola del collare, resta una prova di ACCOPPIAMENTO in mano e non una lettura di calibro, quindi il parametro non cambia classe; ma adesso si sa che funziona, e chi lo tocca rifaccia la prova.",
    },
    "D_mouth_seat_bearings": {
        "group": "arm_plan - invito della sede",
        "description": "Diametro dell'invito alla bocca della sede dei cuscinetti, su TUTTE E DUE le facce del braccio: i cuscinetti entrano uno per faccia, con le flange che restano fuori. Senza invito il cuscinetto deve imboccare di piatto una sede profonda otto millimetri, e quello che si sente come sede stretta è in parte solo imbocco.",
    },
    "H_leadin_seat_bearings": {
        "description": "Profondità dell'invito, uguale alla metà della differenza dei diametri: quarantacinque gradi, la pratica che il progetto usa su tutti i fori.",
    },
    "D_seat_bearings": {
        "description": "Sede per due cuscinetti F695ZZ flangiati impilati, diametro esterno 13. Sono quelli della costruzione di riferimento. Scartato il 608ZZ: con l'esterno da 22 il mozzo andrebbe a 30 e finirebbe dentro il corpo ruota.",
    },
    "D_pivot_arm": {
        "description": "Diametro del perno che esce dal collare: è il foro dei F695ZZ. I due cuscinetti si infilano qui, con le flange verso l'esterno. CONFERMATO IN MANO su un collare stampato in ASA: il cuscinetto CALZA ALLA PERFEZIONE sul perno. È la prima volta che quell'accoppiamento viene provato sul pezzo vero, e conferma di riflesso la compensazione della macchina in un caso che non era mai stato verificato: il perno è un ALBERO, non un foro, quindi la compensazione lo mangia invece di allargarlo.",
    },
    "H_bearings": {
        "description": "Altezza complessiva dei due cuscinetti, 4 mm l'uno. Le flange restano fuori dalla sede, sulle due facce del mozzo, e danno il riferimento assiale: i cuscinetti si distanziano da soli.",
    },
    "D_in_flange_bearing": {
        "group": "cuscinetto F695ZZ - misurato col calibro",
        "description": "Diametro interno della flangia, cioè il foro dell'anello ESTERNO. È il passaggio che la rondella deve attraversare per arrivare a toccare l'anello interno: sotto questo diametro si passa, sopra si va a premere sull'anello esterno e il cuscinetto si blocca. Il 10,5 era nato come stima prudenziale ed è stato confermato col calibro sui cuscinetti della costruzione di riferimento.",
    },
    "D_ring_in_bearing": {
        "group": "cuscinetto F695ZZ - misurato col calibro",
        "description": "Diametro esterno dell'anello INTERNO, quello che gira insieme al perno. È il più grande diametro su cui una rondella può premere senza toccare lo schermo. Nato come stima prudenziale, confermato col calibro: 7,0. Il foro, 5,0, conferma anche il perno.",
    },
    "D_flange_bearing": {
        "group": "collare - lamatura del mozzo",
        "description": "Diametro della flangia dei F695ZZ, misurato col calibro. Era uno standard dato per buono, adesso è un dato: ed è lui a dire quanto larga va la lamatura nel mozzo del collare.",
    },
    "Th_flange_bearing": {
        "group": "collare - lamatura del mozzo",
        "description": "Spessore della flangia, misurato col calibro. Fissa quanto profonda va la lamatura: la flangia deve appoggiarci SOPRA, non esserci schiacciata dentro. La flangia lato corpo sporge di tanto dalla faccia del mozzo del braccio, e senza lamatura finiva dentro il mozzo del collare - 157 mm3 di compenetrazione, che è il volume della flangia intera.",
    },
    "D_spotface_hub": {
        "description": "Diametro della lamatura sul mozzo del perno del collare: due decimi per parte attorno alla flangia, come ovunque nel progetto.",
    },
    "Setback_face_hub": {
        "description": "Di quanto la faccia del mozzo del collare sta indietro rispetto alla faccia del mozzo del braccio, per NON toccarla. Il braccio ruota davvero su quel giunto, sotto il precarico della molla, e ASA contro ASA vuol dire attrito e polvere proprio dove deve muoversi libero. Arretrata di due decimi, a strisciare resta solo l'acciaio liscio della flangia - che è poi quello che dice H_bearings: sono le flange il riferimento assiale, non le facce stampate.",
    },
    "D_seat_centring": {
        "description": "Sede nel braccio per il cerchio del motore, con due decimi di gioco.",
    },
    "H_seat_centring": {
        "description": "Profondità della sede di centraggio.",
    },
    "Th_min_floor_seat_centring": {
        "group": "arm_plan - fondo della sede di centraggio",
    },
    "D_fillet_hub_motor": {
        "description": "Diametro a cui arriva il RACCORDO alla radice del mozzo di centraggio del motore. Misurato sul modello del costruttore, e la misura smentisce il disegno che verrebbe in mente: il mozzo non è un cilindro netto da 22. Nel primo mezzo millimetro dalla flangia si allarga fino a 23, poi resta cilindrico a 22 per un millimetro - che è tutta la fascia che centra davvero - e finisce con uno smusso d'invito a 21. Senza questo numero la sede a 22,2 va a sbattere contro il raccordo e il motore appoggia due decimi sollevato, su di esso invece che sulla flangia: misurati 1,7 mm3 di compenetrazione.",
    },
    "H_fillet_hub_motor": {
        "description": "Quanto è alto quel raccordo, sempre misurato sul modello del costruttore. Da qui in giù comincia la fascia cilindrica da 22 che fa il centraggio, ed è alta un millimetro: è il motivo per cui l'invito non può essere profondo quanto si vuole, se no la sede smette di impegnarla.",
    },
    "D_mouth_seat_centring": {
        "description": "Diametro dell'invito alla bocca della sede di centraggio. Libera il raccordo lasciandogli gli stessi due decimi per parte che la sede lascia al mozzo.",
    },
    "H_leadin_seat_centring": {
        "description": "Profondità dell'invito, uguale alla metà della differenza dei diametri: cioè quarantacinque gradi, che è la pratica che il progetto usa già su tutti i fori. Oltre a liberare il raccordo, guida il mozzo mentre il motore scende in sede.",
    },
    "D_clear_shaft": {
        "description": "Foro nel braccio per il passaggio dell'albero.",
    },
    "D_holes_M3_printed": {
        "group": "arm_plan - foro disegnato",
        "description": "Il diametro con cui i fori di PASSAGGIO delle viti M3 vengono disegnati. Quello di progetto resta D_holes_M3: questo è lui più la compensazione di stampa. Senza, il foro stampato misurava 3,0 e la vite ci strisciava dentro - e sulle quattro viti del motore non è un fastidio ma un difetto, perché il motore lo deve centrare il suo mozzo Ø22 e non le viti.",
    },
    "D_holes_M3": {
        "description": "Fori passanti per le viti del motore.",
    },
    "Cl_rim_inner": {
        "description": "Distanza minima fra braccio e superficie del corpo.",
    },
    "R_rim_inner": {
        "description": "Raggio su cui è tagliato il bordo interno del braccio.",
    },
    "Att_spring": {
        "description": "Distanza dell'attacco molla dal perno. Insieme all'offset del perno determina quanta forza serve alla molla per ottenere il precarico voluto.",
    },
    "D_washer_spring": {
        "group": "assembly_plan - ingombro con cui si disegna la molla",
        "description": "Diametro con cui la molla viene DISEGNATA nelle viste d'insieme. Non è un pezzo: di piattelli non ce ne sono, la molla appoggia da una parte sul fianco della piastra del braccio e dall'altra in fondo alla sede della scatola. Il nome ha già ingannato una volta - il cerchio di costruzione che marcava l'attacco della molla è stato preso per un piattello vero ed è diventato un cilindro di materiale nel solido, in un punto dove la molla non arriva.",
    },
    "Ang_collar_pivot": {
        "group": "collare; flat_gasket",
        "description": "Estensione angolare del collare dal lato del perno. I 110 gradi della base servivano a sostenere il VANO ELETTRONICO, che arrivava a 108: quel vano non esiste più da quando l'elettronica è entrata nel vano motore, e la quota è rimasta orfana della propria ragione. Quello che il collare deve ancora raggiungere da questa parte è l'ultima cosa che porta: l'orecchia anteriore B a 71 gradi e la testa della scatola a 71,9, più il materiale attorno alla bossa del suo inserto. Chi la cambia guardi quei due angoli, non questo numero.",
    },
    "Ang_collar_opposite": {
        "group": "collare; flat_gasket",
        "description": "Estensione angolare del collare dal lato opposto al perno.",
    },
    "Cl_groove_collar": {
        "group": "collare - faccia interna della flangia anteriore",
        "description": "Di quanto la faccia interna della flangia ANTERIORE si arretra dal corpo ruota, per non toccarlo. La gola del collare era disegnata 23,00, cioè ESATTAMENTE l'altezza del corpo: zero gioco su un pezzo stampato, lo stesso difetto del foro della frizione che era il diametro esatto dell'albero. Su un collare stampato la gola misura 22,8 in media e 22,3 sulle creste dei supporti - quella faccia nasce sui supporti e ha materiale in eccesso che pende dentro la gola - quindi il collare stringeva il corpo con due decimi di interferenza, sette sulle creste, ed è per questo che sforzava a incastrarsi. Mezzo millimetro copre la media con margine; le creste, che sono avanzi di supporto, si tolgono con una raschiata. In posizione il collare lo mette la flangia POSTERIORE, che è una faccia pulita: nasce sopra il fondo piatto e i supporti non la vedono mai. Lo schiacciamento della guarnizione non cambia, perché il fondo della sua cava resta dov'era. CONFERMATO IN MANO: un collare ristampato in ASA si infila sul corpo della ruota con la GIUSTA RESISTENZA. Prima di questo mezzo millimetro il collare stringeva, perché la gola era 23,00 - esattamente l'altezza del corpo - e quella faccia nasce sui supporti. La conferma vale per quello che è: una prova di accoppiamento in mano, non una lettura di calibro, quindi il parametro resta SCELTO e non diventa misurato; ma adesso si sa che funziona, e chi lo cambiasse dovrebbe rifare la prova.",
    },
    "Th_collar": {
        "description": "Spessore radiale della fascia cilindrica del collare.",
    },
    "R_out_collar": {
        "description": "Raggio esterno del collare.",
    },
    "L_groove_gasket": {
        "description": "Larghezza della cava che alloggia la guarnizione in espanso.",
    },
    "Dp_groove_gasket": {
        "description": "Profondità della cava. La guarnizione da 3 mm ci si comprime dentro.",
    },
    "Halfarc_seal": {
        "description": "Semiampiezza del perimetro di tenuta, retaggio della prima architettura radiale. Oggi la tenuta è piana.",
    },
    "D_screws_collar": {
        "description": "Viti del collare, non più usate da quando si avvita alle M3 esistenti.",
    },
    "R_gasket": {
        "group": "flat_gasket; collare",
        "description": "Raggio della linea mediana della guarnizione piana, identico sulle due facce. Sta dentro le viti M3 e sotto il fondo della scanalatura: la faccia su cui preme deve essere piena, e oltre il fondo della scanalatura non lo è più.",
    },
    "D_cable_sensor_measured": {
        "group": "cavo CAT5 - MISURATO col calibro",
        "description": "Diametro esterno del CAT5 della costruzione di riferimento. Prima nel progetto c'era 6, che era una stima prudenziale presa dall'intervallo 5÷6 di catalogo: la canalina sulla staffa è dimensionata su quella e si lascia com'è, perché un cavo si schiaccia ma non si assottiglia e il mezzo millimetro in più non dà fastidio. Questo numero invece serve dove il gioco conta davvero, cioè nel varco e nel raggio di curvatura.",
    },
    "R_curvature_min_cable": {
        "group": "cavo - DA CONFERMARE sul datasheet",
        "description": "Raggio minimo di curvatura del cavo. Quattro volte il diametro esterno è la regola che si dà comunemente per l'UTP a 4 coppie posato, ma è una regola di CATEGORIA e non la scheda tecnica del cavo usato: qui vale come vincolo dichiarato e da confermare, non come certezza. Il numero non è accademico - una curva a 90 gradi con questo raggio occupa 22,4 mm in ognuna delle due direzioni, e dentro la scatola ce n'è poco.",
    },
    "Ang_opening_cable_box": {
        "group": "SCATOLA - asola del cavo nel cielo",
        "description": "Dove il cavo attraversa il cielo del vano: in linea col braccio della staffa che porta il fermacavo, così il cavo scende in un piano solo e non piega anche di lato. Piegando di lato mentre scendeva, a 48 gradi, il raggio minimo restava due decimi sotto il suo limite. Il corridoio libero va dal pilastrino dell'orecchia B (fino a 26) a quello dell'orecchia C (da 61).",
    },
    "R_opening_cable_box": {
        "group": "SCATOLA - asola del cavo nel cielo",
        "description": "Il fondo dell'asola del cavo: il centro del suo tondo. L'asola è APERTA sul bordo interno del cielo, a r 86, perché il cavo ci entri di lato col connettore già cablato, invece di doverlo infilare in un foro. È lunga perché il cavo non può scendere in verticale: passando sopra la paletta della staffa gli servono 22 mm di raggio, e attraversa il cielo in obliquo a r 107 (solids_cables.py): il fondo dell'asola sta lì.",
    },
    "Room_opening_cable": {
        "group": "SCATOLA - passaggio del cavo nel cielo",
        "description": "Quanto il varco è più largo del cavo. Non è il gioco di un accoppiamento: il cavo il varco lo ATTRAVERSA di sbieco, non ci sta dentro fermo. Il cielo è spesso 2,5 e il cavo lo taglia inclinato, quindi in direzione di marcia vede un'apertura più corta di quanto sia larga: due millimetri e quattro di agio lasciano passare un cavo inclinato fino a 45 gradi senza che tocchi il bordo.",
    },
    "D_opening_cable_box": {
        "group": "SCATOLA",
        "description": "Larghezza dell'asola del cavo: il diametro del cavo più l'agio, e NIENTE compensazione di stampa. Prima ce l'aveva, ed era un aggancio sbagliato: la compensazione serve a far uscire giusto un ACCOPPIAMENTO, e qui non c'è nessun accoppiamento - c'è un cavo Ø5,6 che passa in un'asola con 2,4 mm di agio, cioè il 43% del suo diametro, dove uno o due decimi non cambiano niente. Quell'aggancio inutile ha fatto danno: alzando la compensazione a 0,25 per correggere il foro dell'albero, l'asola passava a 8,25 e una booleana SVUOTAVA mezza scatola in silenzio - se ne è accorto solo il controllo del raccordo, che non trovava più lo spigolo fra testa e dorso.",
    },
    "Ch_opening_cable": {
        "group": "SCATOLA - bordi del varco",
        "description": "Svasatura del varco, su tutte e due le facce. Non è estetica: un cavo che appoggia su uno spigolo vivo di ASA stampato si consuma lì e si spela dopo mesi, non il giorno del montaggio. Da tutte e due le parti perché il cavo tocca sopra entrando e sotto uscendo, a seconda di come si è sistemato.",
    },
    "D_cable_motor": {
        "group": "cavo del motore - MISURATO",
        "description": "Diametro del fascio dei quattro fili del motore. Misurati stanno sui 4,5; qui ce n'è 5 perché ci va una guaina, e la guaina è quello che poi passa nei fori.",
    },
    "D_cable_supply": {
        "group": "cavo di alimentazione - MISURATO",
        "description": "Diametro del cavo dei 12 V, dal GX12 al driver.",
    },
    "R_curvature_min_cable_supply": {
        "group": "cavo 12V - DA CONFERMARE",
        "description": "Raggio minimo del cavo di alimentazione, con lo stesso criterio e lo stesso caveat del CAT5: quattro volte il diametro è una regola di categoria, non la scheda di questo cavo.",
    },
    "Shore_gasket": {
        "group": "guarnizioni - TPU della costruzione di riferimento",
        "description": "Durezza del TPU con cui si stampano le guarnizioni, in Shore A. Novantacinque è il TPU della costruzione di riferimento ed è anche il più facile da stampare: sotto gli 85 il filamento fa fatica a passare in un estrusore a presa indiretta. È un default, non una costante: chi ha un TPU più morbido ottiene la stessa tenuta con meno forza e può alzare lo schiacciamento, chi ne ha uno più duro deve abbassarlo. Il numero è qui perché chi lo cambia sappia che deve rifare i conti della forza di chiusura, non per bellezza.",
    },
    "L_gasket": {
        "group": "guarnizioni",
        "description": "Larghezza della guarnizione. Due decimi meno della cava: ci si infila a mano senza forzare e senza ballare. Non si fa a misura esatta perché il TPU stampato esce di qualche centesimo abbondante e una guarnizione che va montata a forza si torce nella cava invece di stendercisi.",
    },
    "H_gasket": {
        "group": "guarnizioni",
        "description": "Altezza totale della guarnizione a riposo. La cava è profonda 1,5, quindi sporge di mezzo millimetro: è quel mezzo millimetro che si schiaccia quando si chiude, cioè il 25% dell'altezza. Su un profilo cavo il 25% è compressione da tenuta; su un cordone pieno sarebbe il 50%, che su TPU 95A vorrebbe una forza spropositata - pagata dal collare, che è ASA, e scaricata sulle viti e su una flangia lunga a sbalzo.",
    },
    "L_cavity_gasket": {
        "group": "guarnizioni - profilo cavo",
        "description": "Larghezza della cavità interna. È lei a rendere la guarnizione cedevole: senza, sarebbe gomma piena. Serve anche a fare posto al materiale che si sposta - una cava riempita al 100% non si chiude, perché la gomma è incomprimibile e deve andare da qualche parte.",
    },
    "H_cavity_gasket": {
        "group": "guarnizioni - profilo cavo",
        "description": "Altezza della cavità interna. Il suo cielo è a due spioventi a 45 gradi, non piatto, così si stampa senza supporto: il tratto piano che resta da ponte è largo mezzo millimetro.",
    },
    "H_lip_gasket": {
        "group": "guarnizioni - labbro di tenuta",
        "description": "Quanto il labbro sporge dalla cava. È la parte che si schiaccia, e coincide con H_gasket meno la profondità della cava.",
    },
    "L_lip_gasket": {
        "group": "guarnizioni - labbro di tenuta",
        "description": "Larghezza del labbro. Stretto apposta: a parità di forza, meno area di contatto vuol dire più pressione, e la pressione è quello che sigilla. Largo quanto la guarnizione servirebbe il quadruplo della forza per la stessa tenuta.",
    },
    "D_button_gasket": {
        "group": "guarnizioni - ritegno",
        "description": "Diametro dei bottoni che tengono la guarnizione nella cava. Non è colla: la guarnizione è un pezzo di consumo e deve restare smontabile, quindi si tira via e basta.",
    },
    "Dp_button_gasket": {
        "group": "guarnizioni - ritegno",
        "description": "Quanto il bottone entra nel fondo della cava. Sotto restano 0,7 mm di flangia, che bastano: il bottone non porta carico, tiene solo la guarnizione mentre si monta.",
    },
    "R_numbers_disc": {
        "group": "disco - MISURATO col calibro",
        "description": "Raggio a cui il costruttore ha stampato i numeri 1..5 sulla faccia piatta del disco, dal lato CAMERA, uno accanto a ciascun foro filtro. È il numero da cui discende tutto il resto, e cade esattamente in mezzo alla cava della guarnizione, che senza deviazioni starebbe a 67..70.",
    },
    "Ang_window_body": {
        "group": "corpo della ruota - finestrella di lettura; STIMATA da una foto",
        "description": "Angolo della finestrella che il costruttore ha fatto nel corpo METALLICO, dal centro della corda (lo scasso del bordo, 0 gradi), positivo verso il pannellino dell'elettronica. STIMATO da una foto della ruota di riferimento, da misurare col calibro. A 0, centrata sulla corda insieme alla finestrella del collare, sulla ruota mossa dal motore il numero compariva 6,5 gradi accanto alla finestrella del collare, mentre la finestrella metallica è centrata sul numero: sulla corda è centrato lo scasso del bordo, non la finestrella.",
    },
    "Ang_window_numbers": {
        "group": "collare - finestrella di lettura",
        "description": "Angolo a cui si legge il numero attraverso il collare: la finestrella del collare sta sopra quella del corpo METALLICO, quindi è quell'angolo e non un numero suo. La frizione resta a zero, sulla corda: lì sta lo scasso del bordo, non la finestrella.",
    },
    "R_in_window_numbers": {
        "group": "collare - finestrella; MISURATA sul corpo",
        "description": "Raggio interno della finestrella, copiato da quella che il costruttore ha già fatto nel corpo metallico.",
    },
    "R_out_window_numbers": {
        "group": "collare - finestrella",
        "description": "Raggio esterno della finestrella: la corda su cui finisce quella del corpo. Oltre di lì il piatto del corpo è fresato via, quindi guardare più in fuori non mostrerebbe altro disco.",
    },
    "L_window_numbers": {
        "group": "collare - finestrella; MISURATA sul corpo",
        "description": "Larghezza della finestrella. Nove millimetri inquadrano UNA cifra sola, ed è il punto: le cifre stanno a 72 gradi l'una dall'altra, cioè 86 mm di arco a r 68,5, quindi di margine ce n'è da vendere e conviene stare stretti. Una finestra larga che ne mostrasse due non direbbe più quale posizione è in asse.",
    },
    "Ang_flat_groove": {
        "group": "collare - deviazione della cava",
        "description": "Semiampiezza del tratto in cui la cava sta già tutta spostata, prima di cominciare a tornare indietro. Deve coprire la finestrella con margine: mezza finestrella sono 4,5 mm, che a r 65 fanno 3,97 gradi.",
    },
    "Ang_dev_groove": {
        "group": "collare - deviazione della cava",
        "description": "Semiampiezza totale della deviazione. Fra Ang_flat_groove e questo valore la cava torna al raggio di sempre con un raccordo a coseno rialzato, che non ha spigoli: è la lunghezza di questo tratto a decidere il raggio di curvatura che il cordone deve fare.",
    },
    "Edge_out_groove": {
        "group": "collare - lembo fra cava e finestrella",
        "description": "Quanto lembo di flangia resta FRA la cava deviata e il bordo della finestrella. Senza, la cava si aprirebbe di fianco nell'apertura: il cordone premuto non avrebbe niente che lo trattiene da quella parte e verrebbe fuori dal buco, oltre a vedersi. Un millimetro e mezzo su un cordone da tre è il minimo che regge. Senza questo lembo r 61,2 sembrerebbe bastare alla flangia: con lui la flangia deve arrivare a 59,7.",
    },
    "Edge_in_groove": {
        "group": "collare - lembo di flangia dentro la cava",
        "description": "Quanto lembo di flangia resta DENTRO la cava, verso l'asse. È lui che tiene il cordone: se è sottile, il cordone premuto lo spinge fuori e la tenuta se ne va. Dove la cava è deviata la flangia si allunga di conseguenza, fino a r 61,2 al culmine.",
    },
    "Ch_window_numbers": {
        "group": "collare - bordo della finestrella",
        "description": "Smusso sul bordo della finestrella, su tutte e due le facce. Quella verso la camera è la faccia da cui si guarda, e uno spigolo vivo lì fa ombra sulla cifra; quella verso il corpo è faccia di tenuta, e uno spigolo vivo su una faccia di tenuta è un tagliente.",
    },
    "Fil_window_numbers": {
        "group": "collare - angoli della finestrella",
        "description": "Raccordo agli angoli della finestrella. Un'apertura rettangolare con gli spigoli vivi è anche il punto da cui una flangia si crepa, oltre che brutta da vedere.",
    },
    "R_in_flange_collar": {
        "group": "collare; collar_section; assembly_section",
        "description": "Raggio interno delle due flange del collare. Segue la guarnizione, tenendosi tre millimetri dentro il bordo della cava: è il lembo di flangia che chiude la cava dalla parte dell'asse. Era scritto 66 a mano in tre file diversi, e spostando la guarnizione restava indietro.",
    },
    "D_cable_sensor": {
        "description": "Diametro del cavo del sensore: è uno spezzone di CAT5 intero, guaina compresa. Si dimensiona su 6 e non su 5 perché un cavo si schiaccia ma non si assottiglia, e la canalina deve accoglierlo anche dove la guaina fa la piega.",
    },
    "D_channel_cable": {
        "description": "Larghezza della sella in cui si posa il cavo ancora inguainato, con mezzo millimetro di gioco. Sella a fondo piatto e non canale tondo: una gola cilindrica da 6,5 scavata di 1,2 ha la bocca larga 5,04, e un cavo da 6 lì dentro non ci si posa, ci si incastra.",
    },
    "Dp_channel_cable": {
        "description": "Profondità della sella. Basta perché il cavo non scappi di lato mentre si stringe la fascetta, e non serve di più: a tenerlo fermo è la fascetta, non la forma. La sella esiste solo dentro la piazzola, dove il braccio è largo 16 e le restano 4,75 di parete per lato; sul braccio nudo, largo 8, una gola da 6,5 ne lascerebbe 0,75.",
    },
    "R_tie_cable": {
        "description": "Raggio a cui la fascetta stringe il cavo sulla staffa. È il fermacavo, e non è un accessorio: le piazzole del modulo sono l'anello debole di tutta la catena, e un cavo che tira su una saldatura la stacca prima o poi. Dentro il coperchio entrano solo i quattro fili sguainati, che non tirano.",
    },
    "W_pad_tie": {
        "description": "Larghezza della piazzola del fermacavo, di traverso al braccio. Serve perché la fascetta deve passare da una parte e dall'altra del cavo: sul braccio nudo, largo 8, le due asole starebbero dove il cavo è già passato. Sedici lasciano 2,75 di parete fuori da ogni asola.",
    },
    "L_pad_tie": {
        "description": "Lunghezza della piazzola del fermacavo, lungo il braccio.",
    },
    "Cd_slots_tie": {
        "description": "Interasse delle due asole della fascetta. Nove mm mettono ogni asola a 4,5 dalla mezzeria: tre quarti di millimetro oltre il fianco del cavo, che è quanto basta perché la fascetta si chiuda senza dover pizzicare la guaina.",
    },
    "W_slot_tie": {
        "description": "Lunghezza delle due asole per la fascetta, lungo il braccio. Buona per una fascetta da 2,5.",
    },
    "H_slot_tie": {
        "description": "Larghezza delle asole della fascetta, di traverso al braccio.",
    },
    "W_passage_wires": {
        "description": "Larghezza del passaggio dei quattro fili sguainati, che attraversa la bossa del coperchio invece di girarle attorno: a r 40 la bossa è larga 7 su un braccio largo 8, e di fianco non resterebbe corsia. I fili passano dentro il piedistallo, non accanto.",
    },
    "H_passage_wires": {
        "description": "Altezza del passaggio dei fili. Tre e mezzo per due fanno 7 mm2 contro i 3,1 occupati da quattro fili AWG24 isolati: ci passano senza schiacciarsi, ed è una luce che la stampa fa a ponte senza sostegni.",
    },
    "R_boss_cover_sensor": {
        "description": "Raggio a cui stanno le due bosse che reggono il coperchio del sensore, una per braccio. Sui bracci e non attorno al modulo: il coperchio deve appoggiare sulla STAFFA e mai sulla basetta, perché qualunque cosa prema dall'alto sposta H_rest_module e cambia il traferro, che è il numero più faticato del progetto.",
    },
    "D_boss_cover_sensor": {
        "description": "Diametro delle bosse. Attorno all'inserto M2,5 fuso restano 1,75 mm di parete. Adesso DISCENDE dal foro dell'inserto invece di essere un 7 scritto a mano: con l'inserto vero viene 7,75. Restando a 7, attorno al foro nuovo sarebbero rimasti 1,38 mm di parete, sotto l'uno e mezzo che in questo progetto è il minimo attorno a un inserto fuso.",
    },
    "Off_boss_cable": {
        "description": "Di quanto la bossa del coperchio si scosta dall'asse del braccio, sul solo braccio del cavo. Prima stava in asse e la corsia dei fili le passava SOTTO, in un tunnel alto due millimetri: il cavo bisognava infilarcelo, e con il connettore JST già crimpato non ci passa più. Scostata di qui la bossa lascia la corsia scoperta per tutta la sua lunghezza e i fili ci si posano dentro dall'alto. La quota discende dalle due larghezze che deve separare - mezza corsia più mezza bossa - più mezzo millimetro di franco, così che allargando la corsia o l'inserto la bossa si sposti da sola. Il braccio, che da solo non ci arriva, si allarga lì sotto con una piazzola.",
    },
    "Ch_cover_sensor": {
        "description": "Smusso a 45 gradi lungo tutto il contorno del cielo del coperchio del sensore. Il coperchio era un parallelepipedo con due alette a capo tagliato: spigoli vivi sul cielo e ai capi delle alette, in un pezzo che sta a vista dentro la ruota e che si prende in mano al buio: scartato. Due millimetri su una piastra spessa tre sono abbondanti: un terzo di spessore resta a piena sagoma e il cielo rientra di due millimetri tutt'attorno. È uno SMUSSO e non un raccordo per una ragione di costruzione, non di gusto: il contorno del coperchio è quello del modulo, cioè una spezzata di una quarantina di segmenti, e un raccordo OCCT su segmenti lunghi tre millimetri esce in silenzio con volume negativo - provato. Lo smusso si ottiene invece estrudendo la stessa sagoma in sformo, che sulle sagome convesse del coperchio non può fallire.",
    },
    "H_boss_cover_sensor": {
        "description": "Altezza delle bosse, misurata dalla faccia INTERNA dei bracci: a r 40 sono dentro il gradino, quindi partono da H_body + H_rest_module, lo stesso piano su cui si posa la basetta, e non dalla faccia alta che i bracci hanno solo oltre raggio_gradino_staffa. Quotarle sulla faccia alta le lasciava sospese in aria. Sei millimetri mettono la faccia inferiore del coperchio a 4,4 sopra la basetta - ci passano i quattro fili sguainati e le loro saldature - e lasciano 2 mm di bossa piena fra il fondo della sede dell'inserto M2,5 e il passaggio dei fili, che corre sotto.",
    },
    "Th_cover_sensor": {
        "description": "Spessore del coperchio del sensore.",
    },
    "D_clear_screw_cover_sensor": {
        "description": "Foro di passaggio delle due M2,5 che tengono il coperchio. Di passaggio e non filettato: il filetto sta nell'inserto dentro la bossa della staffa, e il coperchio deve poter salire e scendere sulla vite senza far forza di lato sulle bosse.",
    },
    "W_opening_cable": {
        "description": "Larghezza del varco nella gonna del coperchio da cui entrano i quattro fili sguainati. Più largo della corsia che li porta fin lì perché i fili si aprono a ventaglio sulle sei piazzole, che stanno su tutto il bordo della basetta.",
    },
    "Cl_cover_module": {
        "description": "Aria fra il bordo della basetta e la faccia interna della gonna del coperchio. Il coperchio si sagoma sulla BASETTA e non sulla staffa: ritagliato sulla staffa, la gonna sopravviveva solo dove passano i bracci - due frammenti invece di un anello - e il modulo restava scoperto.",
    },
    "R_skirt_cover": {
        "description": "Non più usato: la gonna segue il contorno della basetta, non un raggio. Resta per non rompere i riferimenti.",
    },
    "Th_skirt_cover": {
        "description": "Spessore della gonna.",
    },
    "Cl_skirt_bracket": {
        "description": "Quanto la gonna resta sospesa sopra la faccia della staffa. Tre decimi: chiudono alla polvere e garantiscono che il coperchio non si appoggi lì invece che sulle bosse.",
    },
    "L_board": {
        "group": "elettronica; pannellino",
        "description": "Lunghezza della basetta millefori, di traverso alla bisettrice. È la 30 x 70 comune, intera: nel vano motore ci sta se il vano arriva a circa 70 gradi, e il vano è stato allargato per questo. Una 30 x 50 ci starebbe anche nel vano di prima. CONFERMATA INDIRETTAMENTE: la basetta tagliata della costruzione di riferimento misura 65,66, e il modello - che il taglio ce l'ha già - ne lascia 65,59. Sette centesimi, cioè la stessa cosa. Questa resta la basetta INTERA: il taglio è a parte.",
    },
    "W_board": {
        "group": "elettronica; pannellino",
        "description": "Larghezza della basetta, lungo la bisettrice. MISURATO col calibro sulla basetta della costruzione di riferimento: 30,3 e non 30 tondi.",
    },
    "Th_board": {
        "group": "elettronica",
        "description": "Spessore della basetta millefori, lo standard. MISURATO: 1,5 e non l'1,6 di catalogo. Un decimo, ma è uno dei mattoni della pila che porta il driver, e la pila era già stata sbagliata di quattro millimetri fidandosi di due stime.",
    },
    "Ang_board": {
        "group": "elettronica; scatola - testa; pannellino",
        "description": "Bisettrice della basetta. Scelta sulla mappa delle altezze libere del vano: centrata qui, la 30 x 70 ha almeno 15 mm sopra di sé dappertutto e 25 su un tratto continuo di 50, verso la testa. Il braccio, il motore e la frizione sono stati contati in tutta la corsa.",
    },
    "R_in_board": {
        "group": "elettronica; pannellino",
        "description": "Distanza dal centro del disco del bordo interno della basetta, lungo la bisettrice. Più in dentro la basetta passa sotto il perno del braccio dove lo spazio scende a 22; più in fuori gli spigoli esterni arrivano al dorso.",
    },
    "N_holes_board_L": {
        "group": "elettronica - griglia della millefori; MISURATO",
        "description": "Fori della basetta lungo la sua lunghezza: la 30 x 70 della costruzione di riferimento è una 10 x 24.",
    },
    "N_holes_board_W": {
        "group": "elettronica - griglia della millefori; MISURATO",
        "description": "Fori della basetta lungo la sua larghezza.",
    },
    "Pitch_perfboard": {
        "group": "elettronica - griglia",
        "description": "Il passo della millefori. La griglia è centrata sulla basetta intera: la prima colonna sta a 5,8 mm dal bordo corto.",
    },
    "L_xiao": {
        "group": "elettronica - dal modello dello XIAO",
        "description": "Lunghezza della scheda dello XIAO, dal modello del costruttore.",
    },
    "Pin_xiao_per_side": {
        "group": "elettronica - XIAO",
        "description": "Pin dello XIAO per lato, a passo 2,54, centrati sulla scheda (stima dal disegno del costruttore).",
    },
    "Proj_usb_xiao": {
        "group": "elettronica - dal modello dello XIAO",
        "description": "Di quanto la presa USB-C sporge oltre il bordo della scheda dello XIAO, dal modello del costruttore.",
    },
    "D_holes_fixing_board": {
        "group": "pannellino - viti delle colonnine",
        "description": "Diametro dei fori di fissaggio della basetta, MISURATO: due millimetri. Non c'era come parametro e andava saputo, perché decide la vite: in un foro da 2 una M2,5 NON passa, e le colonnine erano state disegnate con gli inserti M2,5. O la vite scende a M2 - che in un foro da 2 passa di misura, come già succede per il modulo del sensore - o i fori si allargano col trapano.",
    },
    "Ang_entry_box": {
        "group": "scatola - scanalature d'ingresso delle tasche",
        "description": "Direzione lungo cui la scatola si infila sul collare, cioè il verso in cui si aprono le scanalature che ricevono le bosse delle orecchie. È la bisettrice delle due orecchie anteriori, che sono le più distanti fra loro: così la scanalatura guarda in fuori per tutte e cinque, anche per quelle ai capi, che stanno a cinquanta gradi da questa direzione. Non è una preferenza estetica: è l'unica direzione in cui la scatola può entrare, perché le bosse davanti guardano in giù e quelle dietro in su, e lungo l'asse le due famiglie si impediscono a vicenda.",
    },
    "Travel_entry_box": {
        "group": "scatola - scanalature d'ingresso delle tasche",
        "description": "Quanto è lunga la scanalatura d'ingresso, dal centro della tasca in fuori. MISURATA sul modello prima di sceglierla: tirando la scatola lungo Ang_entry_box, la compenetrazione con il collare sparisce a 20 mm di corsa (a 15 ne restavano 35 mm3, tutti sulle orecchie anteriori). Ventiquattro sono quei venti più quattro di margine. Più corta e la bossa resta impigliata; molto più lunga si mangia la parete del vano senza servire a niente.",
    },
    "D_hole_board_M25": {
        "group": "pannellino - terza vite della basetta, foro da aprire sulla millefori",
        "description": "Diametro a cui si apre col trapano il foro B05 della millefori, per la terza vite M2,5 che tiene il capo tagliato della basetta. I fori stampati della basetta sono da 2 (vedi D_holes_fixing_board) e una M2,5 NON ci passa: o la vite scendeva a M2, o quel foro si allarga. Si è scelto di allargarlo, perché quella vite tiene da sola il capo dove prima c'era il dentino che si è rotto. È la PUNTA usata per la costruzione di riferimento, non una quota di calcolo - il foro passante di norma per una M2,5 sarebbe 2,9 - ed è per quello di classe R. Il numero sta anche in pcb/README.md, scritto a mano: se cambia, cambiarlo lì.",
    },
    "Cd_holes_board_w": {
        "group": "pannellino - colonnine",
        "description": "Interasse dei due fori di fissaggio della basetta, di traverso. STIMA per una 30 x 70 comune con i fori a 2 mm dai bordi: da misurare. Si usano solo i due del capo lontano: quelli del capo della testa se ne vanno col taglio. MISURATO col calibro: 26 tondi, cioè la stima era giusta. Si noti che NON discende dalla larghezza: con W 30,3 e i fori a 2 dai bordi verrebbe 26,3, quindi i fori non stanno a 2 da tutti i bordi e derivarlo sarebbe stato sbagliato di tre decimi.",
    },
    "Dist_holes_board_rim": {
        "group": "pannellino - colonnine",
        "description": "Distanza dei fori di fissaggio dal bordo corto lontano dalla testa. STIMA, come il precedente. CONFERMATO col calibro: i due millimetri della stima erano giusti.",
    },
    "L_guides_board": {
        "group": "pannellino - guide",
        "description": "Lunghezza delle due guide del pannellino lungo la basetta, al capo della testa. Prima erano due DENTINI con un labbro che copriva il bordo della basetta: quel labbro nasceva per aria sopra una fessura e si stampava sui supporti, e uno si è rotto mentre si infilava la basetta, che in quella zona entrava a fatica (SCARTATI). Adesso il capo della testa lo tiene una vite (vedi Q_vite_testa_basetta in electronics.py), le guide restano solo a squadrare la basetta di lato, e la basetta si cala dall'alto invece di scorrere: niente labbro, niente sottosquadra, niente supporti.",
    },
    "Cl_guides_board": {
        "group": "pannellino - guide",
        "description": "Aria fra il bordo lungo della basetta e la guida che le sta di fianco. Tre decimi per lato: la basetta si cala fra le due senza forzare e resta squadrata. Le guide crescono dal pieno del pannellino, quindi questa è una faccia verticale contro una faccia verticale, non un accoppiamento sui supporti.",
    },
    "Th_guides_board": {
        "group": "pannellino - guide",
        "description": "Spessore delle guide, fuori dal bordo della basetta.",
    },
    "H_guides_board": {
        "group": "pannellino - guide",
        "description": "Quanto le guide sporgono sopra la faccia superiore della basetta. Serve a imboccare: si cala la basetta fra le due guide e ci si trova dentro da sola. Non è un labbro e non copre niente - sopra la basetta le guide non sporgono in dentro - quindi si stampa tutta dal pieno.",
    },
    "R_column_ear": {
        "group": "scatola - orecchie anteriori",
        "description": "Raggio del tondo, centrato sulla vite, che addolcisce la sagoma delle due orecchie anteriori e ne fa la colonna che scende al pavimento. L'orecchia era un settore di corona a spigoli vivi appeso a mezz'aria sotto la flangia del collare: da una parte due angoli acuti in un pezzo che si prende in mano, dall'altra un cielo a sbalzo ventisette millimetri sopra il piatto. Unendole un tondo attorno alla propria vite la sagoma diventa morbida, e la stessa sagoma estrusa fino al pavimento fa da colonna: la coppia fra le orecchie anteriori e quelle posteriori - che è ciò che regge il momento della molla - non scarica più su una mensola ma su un pilastro. La sagoma segue uno schizzo a mano (mechanics/others/Colonna.dxf, vista da sotto), rifatto parametrico invece che ricopiato punto per punto, così segue R_screws_box se la vite si sposta. Undici millimetri sono la misura che ricalca lo schizzo - arriva a r 92,5 contro i 93 della sua spline - e lasciano 8,25 mm di materiale attorno al foro di passaggio.",
    },
    "D_foot_column_ear": {
        "group": "scatola - orecchie anteriori",
        "description": "Diametro del piede con cui la colonna dell'orecchia anteriore tocca il pavimento. La colonna al primo tentativo scendeva a filo del fondo del vano e lì si fermava: ma il fondo del vano esiste solo da r 86,2 in fuori, quindi per la maggior parte della sua pianta la colonna non toccava niente e la sua faccia di sotto era un cielo a sbalzo due millimetri e mezzo sopra il piatto. Adesso scende fino alla faccia esterna del fondo e ci appoggia con un piede tondo. Sedici: attorno al canale della vite restano 4,5 mm di parete, e sul piatto è un'isola di primo strato larga abbastanza da non staccarsi.",
    },
    "R_fillet_column_ear": {
        "group": "scatola - orecchie anteriori",
        "description": "Raggio del raccordo fra la colonna dell'orecchia anteriore e la parete su cui si appoggia. Senza, la colonna incontra la parete di spigolo vivo: è il punto in cui passa tutto il carico che la molla scarica sull'orecchia, ed è anche una gola in cui la stampa deposita due perimetri che si toccano senza legarsi. Tre millimetri sono quanto la parete più sottile del giunto può permettersi: più grande, il raccordo andrebbe a mangiare il canale della vite, che passa a 3,5 dall'asse.",
    },
    "H_taper_column_ear": {
        "group": "scatola - orecchie anteriori",
        "description": "Altezza del cono che porta il piede della colonna dell'orecchia anteriore al diametro pieno. Il primo tiro lo faceva alto 3,84 mm - la quota minima che tiene il fianco all'angolo stampabile del progetto, come il supporto del perno sul collare - e il risultato era un piede tozzo con un collarino sotto un fusto dritto. Trenta è TUTTA l'altezza della colonna: così il fusto non c'è più e la colonna è un unico tronco di cono che si apre pianissimo, da Ø16 a terra a Ø22 sotto l'orecchia. Il fianco viene a 84 gradi sull'orizzontale, cioè quasi verticale, quindi di stampabilità non c'è nemmeno da discutere. Il valore si tronca all'altezza disponibile: chiedendone di più il cono mangerebbe la piastra dell'orecchia, che invece deve restare spessa Th_ear_box per tutta la sua pianta.",
    },
    "D_channel_screw_ear": {
        "group": "scatola - orecchie anteriori",
        "description": "Diametro del canale che attraversa la colonna dell'orecchia anteriore, dal piede fino a sotto l'orecchia. Non è il foro della vite: è il passaggio con cui la vite e la chiave a brugola arrivano da sotto. La testa della M3 è Ø5,5 e deve poter scendere lungo il canale fino alla spalla, dove il foro si stringe a D_clear_screw_ear; sette lasciano tre quarti di millimetro per lato alla testa e il posto per una chiave a sfera. Senza il canale la colonna tappava la vite e l'orecchia non si poteva più stringere - un difetto che nessun controllo aveva visto.",
    },
    "D_clear_screw_ear": {
        "group": "scatola - orecchie",
        "description": "Foro di passaggio della M3 nell'orecchia. Era 3,4 scritto a mano dentro il generatore, come raggio 1,7: qui diventa una quota perché da lei discende la spalla su cui la testa della vite appoggia in fondo al canale della colonna.",
    },
    "Th_rib_boss_spring": {
        "description": "Spessore della nervatura verticale che porta il bosso della molla. Il bosso è un cilindro coricato dentro il vano: la sua metà di sotto è un cielo a sbalzo, e nella giacitura della scatola - fondo sul piatto - vuole i supporti. La nervatura sta nel piano verticale dell'asse della molla, raccorda il cilindro al fondo con due facce a 45 gradi e prosegue in su fino al cielo del vano: oltre a togliere i supporti lega il bosso alla volta, che è il punto su cui la molla spinge in permanenza con 22,3 N. Quattro millimetri sono una costola che si stampa piena con due perimetri e mezzo e non fa da tappo al vano: sotto e sopra il bosso lo spazio c'è e non ci va niente.",
    },
    "Th_panel_screws": {
        "group": "pannellino; scatola",
        "description": "Spessore del pannellino in corrispondenza delle tre viti, e perciò anche altezza del gradino che la scatola gli scava attorno. Altrove il pannellino ha la battuta a mezzo spessore, cioè 1,25 mm: lì le viti prendevano su un lembo sottile, e soprattutto il gradino della scatola restava un cielo a sbalzo un millimetro e un quarto sopra il piatto, dove i supporti non hanno il posto per svilupparsi. Portando la zona delle viti a cinque millimetri il lembo diventa un pezzo di pannello vero e il gradino della scatola si alza abbastanza da poter essere sostenuto. Dentro la scatola, in quella zona, di ingombro non ce n'è.",
    },
    "H_post": {
        "group": "pannellino - colonnine",
        "description": "Altezza delle colonnine che tengono la basetta sollevata dal pannellino: sotto ci devono passare i reofori tagliati e le saldature di una millefori cablata punto-punto. Ogni millimetro qui si somma all'altezza del driver, che è il pezzo più alto. Cinque e non tre: una basetta cablata vuole sotto quattro o cinque millimetri d'aria, e con tre i reofori piegati non ci passavano. Si prendono i cinque, cioè il più largo dei due, perché il vincolo a cui si somma - l'altezza del driver nel vano - ha ancora margine; se il controllo del vano protestasse, si scende a quattro.",
    },
    "D_post": {
        "group": "pannellino - colonnine",
        "description": "Diametro delle colonnine. Attorno all'inserto M2,5 restano 1,75 mm di parete. Adesso DISCENDE dall'inserto invece di essere un 7 scritto a mano: con l'M2 viene 6,35, e se l'inserto misurato risultasse diverso la colonnina lo segue da sola.",
    },
    "D_out_insert_M25": {
        "group": "staffa sensore - bosse del coperchio",
        "description": "Diametro esterno dell'inserto a caldo M2,5 della costruzione di riferimento, MISURATO: 4,6. Il catalogo ne faceva discendere un foro da 3,4, che è il foro giusto per un inserto da 3,75: in quel foro questo inserto NON ENTRA, o spacca la bossa. È la terza volta che il catalogo sbaglia qui, sempre per difetto.",
    },
    "D_hole_insert_M25": {
        "group": "pannellino - colonnine",
        "description": "Foro per l'inserto a caldo M2,5, come dice chi lo fa. DA CONFERMARE con gli inserti usati, e con i fori della basetta, che sulle 30 x 70 sono spesso da 2. Adesso DISCENDE dall'inserto misurato invece di essere il numero di catalogo: 4,25 e non 3,4. Da lui è dovuta crescere anche la bossa, che con la parete di prima sarebbe rimasta a 1,38 mm attorno al foro.",
    },
    "L_insert_M25": {
        "group": "pannellino - colonnine",
        "description": "Lunghezza dell'inserto M2,5. Più lungo della colonnina: il resto scende nel pannellino. SCELTA fra le due lunghezze della costruzione di riferimento, 4 e 5,7: si prendono i 4. La bossa del coperchio è alta 6: con l'inserto da 5,7 resterebbero tre decimi di fondo, e quel fondo serve alla punta della vite e a non far sfondare l'inserto mentre si pianta. Con 4 ne restano 2, e la presa è comunque un diametro e mezzo.",
    },
    "H_below_board_xiao": {
        "group": "elettronica - MISURATO",
        "description": "Aria fra la faccia di sopra della basetta e la faccia di SOTTO della scheda dello XIAO, innestato: zoccolo rettangolare più distanziale dei pin in un numero solo. Prima erano due numeri, uno stimato, e insieme sbagliavano di quattro millimetri: ci vogliono zoccoli più alti, perché nei tondi i pin non entrano.",
    },
    "H_below_board_driver": {
        "group": "elettronica - MISURATO",
        "description": "Lo stesso per il driver, misurato: è lui, col dissipatore, a dare l'altezza di tutta l'elettronica.",
    },
    "Z_usb_on_board": {
        "group": "elettronica - dal modello dello XIAO",
        "description": "Di quanto la presa USB comincia sopra la faccia di sotto della scheda. Viene dal modello del costruttore, confermato sulla scheda vera.",
    },
    "Z_usb_top_on_board": {
        "group": "elettronica - MISURATO",
        "description": "Dalla faccia di SOTTO della scheda dello XIAO alla CIMA della presa USB. È la misura da cui discende l'asola nella testa. Torna col modello del costruttore: 4,5 meno lo 0,26 da cui la presa comincia fa 4,24, cioè i 4,2 che il modello dichiara. Due letture precedenti - 12 dalla basetta al sotto della presa e 3,2 di altezza - non tornano con questa e sono state scartate.",
    },
    "H_usb": {
        "group": "elettronica",
        "description": "Altezza della presa USB-C, per differenza fra le due quote sulla scheda. L'asola nella testa è alta questo più il gioco, con la parte alta STONDATA come la presa: il raggio è mezza altezza.",
    },
    "Th_board_driver": {
        "group": "elettronica - dal modello del TMC2209",
        "description": "Spessore della scheda del driver.",
    },
    "H_heatsink_driver": {
        "group": "elettronica - MISURATO",
        "description": "Altezza del dissipatore del driver, adesivo compreso. È lui a comandare l'altezza di tutta l'elettronica: dal pannellino, col resto della pila, fa 26,9.",
    },
    "L_heatsink_driver": {
        "group": "elettronica - MISURATO",
        "description": "Pianta del dissipatore, lungo le file di pin.",
    },
    "W_heatsink_driver": {
        "group": "elettronica - MISURATO",
        "description": "Pianta del dissipatore, di traverso.",
    },
    "D_electrolytic": {
        "group": "elettronica - C1 e C2, 47 uF 63 V; MISURATO",
        "description": "Diametro dei due elettrolitici, C1 e C2, misurato (pcb/BOM.md). Il catalogo dice 6,3.",
    },
    "H_electrolytic": {
        "group": "elettronica - C1 e C2 in piedi; MISURATO",
        "description": "Altezza degli elettrolitici montati in piedi, reofori compresi, misurata. C1 resta in piedi per il vincolo dell'anello VM-GND (pcb/README.md); il driver è comunque più alto.",
    },
    "D_led": {
        "group": "scatola - testa, LED; elettronica",
        "description": "Diametro del LED di stato, D1 in distinta: rosso da 3 mm. Sta sulla testa, sopra la presa di alimentazione, e in esercizio è spento: accanto a un telescopio una luce rossa accesa è un difetto.",
    },
    "D_collar_led": {
        "group": "elettronica - LED",
        "description": "Il collarino alla base del LED da 3 mm, di catalogo: è lui che appoggia dentro la testa e che decide quanto il LED deve stare lontano dal dado del GX12.",
    },
    "D_hole_led": {
        "group": "scatola - testa, LED",
        "description": "Foro del LED nella testa: il LED ci entra da dentro e si ferma col collarino.",
    },
    "W_flats_gx12": {
        "group": "SCATOLA - foro del GX12",
        "description": "Distanza fra le due fresate di antirotazione del GX12, MISURATA col calibro. Non è una D: il barilotto filettato ha una fresata PER LATO, a 180 gradi una dall'altra. Finché il foro è stato un tondo liscio il connettore girava avvitando la ghiera, e nessun controllo poteva vederlo - nel modello il GX12 è semplificato a un cilindro, quindi quelle due fresate non esistono.",
    },
    "Cl_flats_gx12": {
        "group": "SCATOLA - foro del GX12",
        "description": "Gioco totale fra le fresate del connettore e quelle del foro. Sta stretto apposta: è un accoppiamento di FORMA, che deve impedire una rotazione, non un accoppiamento scorrevole. L'ingaggio che ne resta è poco più di sette centesimi per lato, e basta, perché a fermare il connettore è uno spallamento e non l'attrito.",
    },
    "Cl_led_gx12": {
        "group": "scatola - testa, LED",
        "description": "Aria fra il collarino del LED e il dado del GX12, dentro la testa. Da qui discende la quota del LED.",
    },
    "Cl_modules": {
        "group": "elettronica",
        "description": "Aria fra lo XIAO e il driver, lungo la basetta.",
    },
    "H_terminals": {
        "group": "elettronica - STIMA",
        "description": "Altezza delle morsettiere a passo 5,08: stima di catalogo, da misurare su quelle usate.",
    },
    "D_out_insert_M2": {
        "group": "pannellino - colonnine",
        "description": "Diametro esterno dell'inserto a caldo M2 delle colonnine. Era di catalogo, e in questo progetto il catalogo ha già sbagliato due volte - gli M3 li dava 4,6 e sono 5,0, gli M4 5,6 e sono 6,3. Le colonnine sono passate da M2,5 a M2 perché i fori della basetta sono stati misurati Ø2 e una M2,5 non ci passa; una M2 sì, di misura, come già succede sul modulo del sensore. MISURATO: 3,6, e il catalogo diceva 3,2. Terza volta su tre che il catalogo sbaglia in questo progetto - M3 4,6 contro 5,0, M4 5,6 contro 6,3 - e ogni volta per difetto, cioè nel verso che spacca la bossa invece di lasciare l'inserto lasco.",
    },
    "D_hole_insert_M2": {
        "group": "pannellino - colonnine",
        "description": "Foro in cui fonde l'inserto M2. Più stretto dell'inserto di trentacinque centesimi, la stessa regola degli M3 e degli M4: fondendo deve piantarsi, non scivolare.",
    },
    "L_insert_M2": {
        "group": "pannellino - colonnine",
        "description": "Lunghezza dell'inserto M2. DA MISURARE come il diametro. Se venisse più lungo della colonnina il resto scende nel pannellino, che lì è pieno. SCELTA fra le tre lunghezze della costruzione di riferimento - 2,5, 3 e 4: si prende la più lunga. Quattro millimetri su una M2 sono DUE DIAMETRI di presa, mentre i 3 mm degli inserti M3 sono un diametro scarso, il minimo pratico. Ci sta tutto dentro la colonnina, che è alta 5, e sotto l'inserto resta comunque un millimetro di fondo. Le altre due lunghezze non offrono niente in cambio: qui non c'è un vincolo di altezza da risparmiare, perché l'inserto sta dentro un pieno.",
    },
    "Wall_around_insert": {
        "group": "pannellino - colonnine",
        "description": "Parete che resta attorno a un inserto a caldo, in qualunque bossa o colonnina. Era il numero implicito dentro D_post, che valeva 7 scritti a mano con la parete scritta solo nel commento: cambiando l'inserto da M2,5 a M2 quel commento avrebbe cominciato a mentire.",
    },
    "Cl_head_board": {
        "group": "scatola - testa; elettronica - taglio della basetta",
        "description": "Aria fra il capo TAGLIATO della basetta e la faccia interna della parete di testa. La testa la decide lo XIAO, che deve avere la presa a filo della faccia esterna e i pin sulla griglia; la basetta si taglia a questa distanza dalla testa. Non può crescere molto: oltre il primo foro devono restare almeno 1,27 mm di basetta, e con 0,5 ne restano 1,39.",
    },
    "Marg_panel": {
        "group": "pannellino; scatola - apertura nel fondo",
        "description": "Di quanto l'apertura nel fondo è più grande della basetta: è l'aria per infilarla e sfilarla insieme al pannellino, con i reofori che sporgono.",
    },
    "Cl_panel": {
        "description": "Aria fra il pannellino e la sua apertura, tutto attorno. Si applica al PANNELLINO, che viene rimpicciolito di tanto per parte: non si tocca più, perché un pannellino già stampato resti buono; altra aria si aggiunge dall'altra parte (vedi Cl_panel_box).",
    },
    "Cl_panel_box": {
        "group": "SCATOLA - apertura del pannellino",
        "description": "Aria IN PIÙ scavata nell'apertura della scatola, per parte, oltre a quella già tolta al pannellino. Serve perché due decimi per parte sono giusti sulla carta e nulli in mano: misurato sui solidi, il gioco laterale nella piastra è 0,199 - esattamente il nominale - e il pannellino si infila comunque a fatica. Su un pezzo lungo ottantacinque millimetri quel decimo e mezzo se lo mangia il ritiro, e il pannellino non deve nemmeno centrare niente: a tenerlo in posizione sono le tre viti nei loro inserti, non l'accoppiamento. Sta separato da Cl_panel, e non sommato a lui, perché l'aria si aggiunge SOLO dalla parte della scatola: il pannellino già stampato resta buono.",
    },
    "Stop_panel": {
        "group": "pannellino; scatola",
        "description": "Larghezza del gradino che tiene il pannellino a filo: sulla metà esterna dello spessore l'apertura e il pannellino sono più larghi di questo.",
    },
    "Proj_screws_panel": {
        "group": "pannellino; scatola",
        "description": "Di quanto il pannellino si allarga oltre l'apertura, al capo lontano dalla testa, per portare le due viti di quel capo.",
    },
    "Setback_screws_panel": {
        "description": "Distanza delle due viti del capo lontano dai bordi dell'apertura.",
    },
    "D_boss_panel": {
        "group": "scatola - bosse delle viti del pannellino",
        "description": "Diametro delle bosse che portano gli inserti M3 del pannellino. Attorno all'inserto fuso restano 2 mm.",
    },
    "Z_skirt_inner": {
        "group": "scatola - gonna interna",
        "description": "Fin dove sale la gonna che chiude il vano verso l'asse, sotto il braccio. Non si sceglie più: è il SOTTOPANCIA DEL BRACCIO meno il gioco. Prima era -14, scritto a mano sulla testa della vite del perno, che scende a -13,5: ma la vite sta sul perno, a r 91,6, e la sua testa arriva a r 88,9, cioè appena FUORI dalla fascia della gonna - non era lei a comandare, e per lei bastano i gradini attorno al perno. A comandare è il braccio, e la gonna sale cinque millimetri e mezzo più di prima. Oltre il passaggio del braccio sale invece fino al collare.",
    },
    "Cl_skirt_arm": {
        "group": "scatola - gonna interna",
        "description": "Aria fra la cima della gonna interna e il sottopancia del braccio, e attorno ai dischi che il perno porta sotto il braccio. La rotazione del braccio non la consuma: il braccio gira attorno a un asse verticale, quindi il suo sottopancia resta lo stesso piano a qualunque angolo della corsa. La consumano le tolleranze di stampa e il gioco assiale del pacco di cuscinetti, ed è anche la fessura che resta aperta verso il vano: mezzo millimetro, contro gli undici di prima.",
    },
    "Th_tab_tie": {
        "group": "scatola - aletta della fascetta",
        "description": "Spessore dell'aletta che sporge dalla faccia interna della testa, accanto al GX12, per legare i fili con una fascetta di nylon.",
    },
    "Off_tab_tie": {
        "group": "scatola - aletta della fascetta",
    },
    "L_tab_tie": {
        "group": "scatola - aletta della fascetta",
        "description": "Di quanto l'aletta sporge dalla testa verso l'interno. Il suo bordo inferiore è a 45 gradi: la scatola si stampa sul fondo, e un'aletta con il bordo orizzontale vorrebbe il supporto.",
    },
    "H_tab_tie": {
        "group": "scatola - aletta della fascetta",
        "description": "Altezza dell'aletta sul suo bordo libero, centrata sulla quota del GX12, da cui scendono i fili da legare.",
    },
    "W_slot_tie_head": {
        "group": "scatola - aletta della fascetta",
        "description": "Asola della fascetta nell'aletta, in altezza: per le fascette comuni da 2,5 mm. Da confermare con quelle usate.",
    },
    "H_slot_tie_head": {
        "group": "scatola - aletta della fascetta",
        "description": "Asola della fascetta nell'aletta, in lunghezza lungo l'aletta: una fascetta da 2,5 è spessa circa uno.",
    },
    "Weld_box_collar": {
        "group": "scatola - faccia interna del guscio",
        "description": "Di quanto la faccia interna del guscio entra DENTRO il collare. Non è un gioco, è il contrario: scatola e collare sono un pezzo solo, e due solidi che si sfiorano senza compenetrarsi si fondono in un COMPOSTO di due pezzi invece che in un solido - una scaglia che si stacca nel sacchetto, o peggio un pezzo che lo slicer stampa in due. Mezzo millimetro di compenetrazione rende la fusione non ambigua e non ha nessun effetto sulla forma finita, perché quella faccia dentro il pezzo non esiste più. Ha preso il posto di Cl_box_collar, che valeva 0,2 ed era il gioco con cui la scatola si INFILAVA sul collare: non si infila più niente.",
    },
    "Cl_box_collar": {
        "group": "scatola - faccia interna del guscio",
        "description": "Aria fra la faccia interna del guscio e quella esterna del collare. La scatola si infila sul collare facendo scorrere le orecchie a cavallo delle flange, e in posizione la mettono le bosse: le due superfici cilindriche non devono toccarsi. Senza gioco cadevano sullo stesso cilindro, e siccome i due pezzi sono descritti con poligoni di passo diverso - mezzo grado la scatola, un grado il collare - il più fitto sporgeva: l'audit trovava un centesimo di millimetro cubo di compenetrazione sparso su tutto lo sviluppo.",
    },
    "Cl_skirt_collar": {
        "group": "scatola - gonna interna",
        "description": "Aria fra la gonna interna e la faccia esterna del collare. Senza, le due facce cadono sullo stesso cilindro: i due pezzi sono descritti con poligoni di passo diverso, mezzo grado la scatola e un grado il collare, quindi il più fitto sporge e l'audit trova una compenetrazione di un centesimo - lo stesso difetto di discretizzazione già visto sulle orecchie. È anche il gioco che serve per infilare la scatola sul collare.",
    },
    "Cl_usb": {
        "group": "scatola - asola USB",
        "description": "Aria attorno alla presa USB nell'asola della testa. L'asola è aperta verso il fondo: la presa ci entra salendo, insieme al pannellino.",
    },
    "S_gx12": {
        "group": "scatola - testa, GX12",
        "description": "Dove sta il GX12 sulla testa, lungo la bisettrice.",
    },
    "H_nut_gx12": {
        "group": "scatola - testa, GX12",
        "description": "Altezza del dado del GX12, cioè del corpo che sporge dentro la scatola. Era il numero 16,7 scritto dentro electronics.py accanto a GX12_DENTRO: una quota di un pezzo comprato che stava nel codice invece che fra le quote, e quindi non poteva comparire in nessuna espressione.",
    },
    "Cl_turn_nut_gx12": {
        "group": "scatola - testa, GX12",
        "description": "La corona libera che deve restare attorno al dado del GX12 perché lo si possa GIRARE per avvitarlo. Non è un ingombro: il dado ci starebbe anche senza, ed è proprio per questo che serve una quota a sé - un controllo sull'ingombro passerebbe e il pezzo sarebbe inservibile lo stesso. Cinque millimetri sono quanto basta a due dita su una zigrinatura; una chiave a settore ne vorrebbe meno, ma a montaggio si lavora a mano.\n\nQuesta corona ha la PRIORITÀ sugli altri posizionamenti della testa: se spostare la presa o il LED costa questa corona, lo spostamento non si fa. Per questo è diventata un controllo e non una nota.",
    },
    "Cl_cable_driver": {
        "group": "cavo del sensore",
        "description": "Quanto la guaina del cavo del sensore si ferma sopra la cosa più alta della basetta, che è il dissipatore del driver. Sotto la guaina scendono i quattro fili sguainati, che non tirano e si scostano da soli: sono loro ad arrivare al connettore, non la guaina. Due millimetri perché la guaina non appoggi sul dissipatore, che scalda.",
    },
    "Cl_gx12_usb": {
        "group": "scatola - testa, GX12",
        "description": "Quanto il dado del GX12 deve restare lontano dalla presa USB dello XIAO. Due millimetri: ci deve passare il guscio della spina USB a gomito, e la mano che la infila al buio.",
    },
    "Z_gx12": {
        "group": "scatola - testa, GX12",
        "description": "Quota del GX12 sulla testa: sopra lo XIAO, col dado che resta a Cl_gx12_usb dalla sua presa, e sotto il cielo del vano.\n\nERA IL NUMERO -1 SCRITTO A MANO, e la sua descrizione diceva già a parole da cosa doveva discendere - sopra lo XIAO, a due millimetri dalla presa - senza discenderne. Quando il pavimento della scatola è salito di sei millimetri e mezzo, e la pila dell'elettronica con lui, il GX12 è rimasto dov'era, e il suo dado è entrato DENTRO la presa USB dello XIAO per 2,35 mm - visto sul pezzo, non da un controllo.\n\nIl LED discende da questa quota, quindi sale con lei.",
    },
    "D_hole_gx12": {
        "group": "scatola - testa, GX12",
        "description": "Foro del GX12: filetto M12 più due decimi. Il corpo nel modello è semplificato a un cilindro da 14,8: la quota del foro è di catalogo, da confermare sul connettore.",
    },
    "R_screws_box": {
        "group": "collare; scatola",
        "description": "Raggio delle sei viti che tengono la scatola al collare. Scelto perché lì l'inserto ha parete tutto attorno: restano 2,2 mm fino al bordo esterno della flangia, e verso l'interno la flangia continua fino a 62,5. Più in fuori la parete si assottiglia; più in dentro l'inserto finirebbe dove sopra c'è il corpo ruota.",
    },
    "D_out_insert_M3": {
        "group": "collare; scatola - inserto a caldo M3; MISURATO col calibro",
        "description": "Diametro esterno dell'inserto a caldo M3 della costruzione di riferimento, misurato col calibro su un esemplare. Prima qui c'era scritto che l'inserto è 4,6 di fuori e va in un foro da 4: era un'assunzione, e sbagliata di quattro decimi. È lo stesso errore già fatto con l'M4, dove il catalogo dice 5,6 e quello vero è 6,3. Chi ha inserti diversi cambia questo numero e L_insert_M3, e foro, invito, sede e bossa lo seguono.",
    },
    "L_insert_M3": {
        "group": "collare; scatola - inserto a caldo M3; MISURATO col calibro",
        "description": "Lunghezza dell'inserto, misurata. Non è nessuna delle lunghezze dell'assortimento di catalogo (4,0 / 4,8 / 5,7): è un tipo diverso, ed è il motivo per cui la misura vale più della foto. ATTENZIONE: 3 mm di presa su un M3 sono UN DIAMETRO SCARSO, cioè il minimo pratico. Regge, ma dove il giunto porta carico - le sei viti che tengono la scatola sotto i 22,3 N della molla - non c'è margine da spendere. Se servisse più presa, nell'assortimento ci sono M3 da 4,0 e 4,8 con lo stesso diametro esterno.",
    },
    "D_tip_iron": {
        "group": "collare - accesso alle sedi degli inserti",
        "description": "Diametro della punta del saldatore con cui si piantano gli inserti a caldo. CONFERMATO sul saldatore usato: otto. Serve a sorvegliare che alla bocca di ogni sede la punta arrivi DRITTA: una sede raggiungibile solo di sbieco pianta l'inserto storto, e un inserto storto porta la vite storta.",
    },
    "Cl_tip_iron": {
        "group": "collare - canale del saldatore",
        "description": "Quanto il canale del saldatore dev'essere più largo della punta. Non è un gioco di montaggio: la punta è ROVENTE, e una plastica che la tocca mentre scende fonde dove non deve. Mezzo millimetro in tutto, cioè un quarto per lato, è quanto basta perché la punta non struschi la parete del canale. Da qui discendono la larghezza del canale nel collare e il diametro della cima del suo supporto, che deve continuare a lasciare parete attorno.",
    },
    "D_hole_insert_M3": {
        "group": "collare; scatola - sede dell'inserto",
        "description": "Foro in cui l'inserto fonde. Più stretto dell'inserto di tre decimi e mezzo apposta: fondendo deve piantarsi, non scivolare. È la stessa regola usata per l'M4. Prima era 4,0, coerente con un inserto da 4,6 che però non è quello montato: con 4,0 un inserto da 5 non si sarebbe piantato, o avrebbe spaccato la bossa.",
    },
    "D_boss_insert": {
        "group": "collare; scatola",
        "description": "Diametro della bossa che porta l'inserto, sulla faccia esterna della flangia. Dà la parete attorno all'inserto fuso, e fa anche da spina: entra nella tasca dell'orecchia e mette la scatola in posizione prima ancora di avvitarla.",
    },
    "H_boss_insert": {
        "group": "collare; scatola",
        "description": "Altezza della bossa. Due millimetri bastano a tenere l'inserto fuori dalla fascia e a centrare la scatola.",
    },
    "Th_ear_box": {
        "description": "Spessore dell'orecchia della scatola: deve contenere la tasca della bossa, profonda 2, e restarne 3 di fondo attorno alla vite.",
    },
    "R_in_ear": {
        "description": "Fin dove l'orecchia entra sotto la flangia del collare. A 76 la vite ha 5,5 mm di orecchia da una parte e 4,5 dall'altra.",
    },
    "Ang_ear_front_A": {
        "group": "scatola; collare - orecchia anteriore",
        "description": "Le orecchie ANTERIORI stanno dove la scatola ha davvero materiale a quella quota, e non dove farebbe comodo: a z -8..-3 la scatola esiste solo sulle due teste del vano, la costa a -30..-28 e la parete di testa oltre la basetta. Nel resto del vano meccanico non c'è niente da avvitare, perché quel vano verso il collare è aperto. Questa è la costa di testa dal lato opposto al perno; sta anche fuori dalla corsa del braccio, che occupa -13,4..+44,7 sotto z 0,5. Quei due angoli non sono più scritti a mano: li dà corsa_braccio.passaggio(), quindi seguono la corsa vera. Il numero di prima, -16..+44, era il risultato della vecchia spazzata inventata a mano e non corrispondeva a niente di misurato - la conclusione però non cambia, perché -29 sta fuori da tutti e due gli intervalli.",
    },
    "Ang_ear_front_B": {
        "group": "scatola; collare - orecchia anteriore",
        "description": "La seconda orecchia anteriore sta sulla PARETE DI TESTA, dove la scatola ha materiale a quella quota: a metà dello spessore della testa, al raggio a cui la scatola si accosta al collare. Stava sulla parete di divisione fra i due vani, che col vano elettronico è sparita. La terza orecchia anteriore, che stava sul vano elettronico, non c'è più: oltre la testa non c'è scatola da tenere giù, e fra le due teste il vano è aperto verso il collare.",
    },
    "Ang_ear_rear_A": {
        "group": "scatola; collare - orecchia posteriore",
        "description": "Le tre orecchie POSTERIORI si appoggiano sul cielo del vano, che copre tutto il settore fino alla testa alla quota giusta. Devono stare fuori dalle due zone della staffa del sensore, -46..-34 e +44..+56 a staffa ferma - e ciascuna di quelle zone si allarga di Halfw_slot_collar, perché la staffa ruota sulla sua asola.",
    },
    "Ang_ear_rear_B": {
        "group": "scatola; collare - orecchia posteriore",
        "description": "Questa cade sotto la molla, che spinge a 21 gradi: è la vite che prende in pieno il tiro.",
    },
    "Ang_ear_rear_C": {
        "group": "scatola; collare - orecchia posteriore",
        "description": "L'ultima prima della testa. Stava a 60, e lì la staffa del sensore, ruotando sulla sua asola per andare a prendere le viti, toccava questa orecchia dopo un decimo di grado: la staffa ferma ci stava, quella che si registra no. A 67 resta fuori da tutta l'asola, con la sua bossa.",
    },
    "Ang_screw_A": {
        "group": "collare - asola M3, lato opposto al perno",
        "description": "Angolo della prima vite M3 di ancoraggio rispetto al centro finestra. Assorbito da un'asola, perché la posizione reale non è nota con precisione.",
    },
    "Ang_screw_B": {
        "group": "collare - asola M3, lato perno",
        "description": "Angolo della seconda vite. La somma delle due deve fare 90 gradi.",
    },
    "Th_flange_collar": {
        "description": "Spessore delle due flange che risvoltano sulle facce del corpo.",
    },
    "Cl_rib_head_body": {
        "group": "scatola - anima fra testa, gonna e ruota",
    },
    "L_rib_head_skirt": {
        "group": "scatola - anima fra testa, gonna e ruota",
    },
    "Halfw_slot_collar": {
        "group": "collare - asole M3; sensor_bracket - tasche del fondo",
        "description": "Semiampiezza delle due asole M3 nella flangia posteriore. Assorbe la posizione vera delle viti del fondello, che non è nota con precisione. Decide anche quanto può ruotare la staffa del sensore, che segue le viti ruotando sul magnete: per questo la tasca che il fondo piatto le lascia è larga quanto la sua sagoma spazzata su tutto questo angolo.",
    },
    "Halfw_ear_box": {
        "group": "scatola - orecchie; collare - tasche del fondo",
        "description": "Semiampiezza delle orecchie della scatola. Era un 5 scritto a mano nella scatola, e il fondo piatto del collare deve lasciare alle orecchie posteriori una tasca che le segua.",
    },
    "Cl_pockets_bottom": {
        "group": "collare - fondo piatto",
        "description": "Gioco tutto attorno alle tasche che il fondo piatto del collare lascia alle orecchie posteriori e alle palette della staffa. Le tasche NON devono centrare niente: la scatola la centrano le bosse, la staffa il magnete. Una tasca aderente sarebbe un secondo riferimento in conflitto con il primo.",
    },
    "Cl_aperture_clutch": {
        "group": "collare - finestra della frizione",
        "description": "Quanto vuoto deve restare fra la ruota di frizione e il bordo della finestra del collare, tutto attorno. Prima non esisteva: la finestra era tre numeri scollegati fra loro - una semiampiezza di 15 gradi scelta a mano e due scostamenti scritti nel codice - che per caso lasciavano 1,5 mm. Su una stampa di prova la frizione passava quasi a filo, ed è poco per un pezzo stampato con una ruota che gira: a chiudere quel millimetro e mezzo bastano la tolleranza di stampa del collare, l'anello di TPU che si deforma sotto i 22,3 N, e l'eccentricità del disco che fa oscillare il braccio. Da qui discendono sia la semiampiezza della finestra sia le sue due quote in z, quindi cambiando questo numero la finestra segue la frizione da sola. Costa luce parassita, ma meno di quanto sembri: in verticale la finestra è già coperta dal corpo, che oltre z 14,3 è pieno e sotto z 3 è già aperto per il taglio della costola, quindi l'unico prezzo vero è l'allargamento angolare, un millimetro e mezzo per parte.",
    },
    "Ang_aperture_clutch": {
        "group": "collare - passaggio ruota di frizione",
        "description": "Semiampiezza dell'apertura nel collare per il passaggio della ruota di frizione. Non si sceglie più a mano: discende dal gioco. Il punto in cui la finestra stringe davvero è lo spigolo fra il fianco del taglio e la superficie ESTERNA della fascia, a R_out_collar: andando verso l'esterno il fianco si avvicina all'asse della frizione, quindi il raggio più grande è il peggiore. Il teorema del coseno sul triangolo asse disco - asse frizione - spigolo dà l'angolo che mette quello spigolo a D_clutch/2 + gioco dall'asse della frizione.",
    },
    "Ang_aperture_grub": {
        "group": "collare - scasso del collare del grano",
        "description": "Semiampiezza dello scasso nel collare per il COLLARE DEL GRANO della frizione, che è una cosa diversa dalla finestra del battistrada e sta più in alto. Girando la frizione il collare del grano è andato sopra il mozzo, e crescendo fino a z 19,50 è uscito dalla finestra, che finisce a 14 - il suo bordo interno tocca la fascia del collare a r 85 su 86, per 34 mm3.\n\nSi fa uno scasso a sé invece di alzare la finestra perché la finestra è larga quanto il BATTISTRADA e alzarla di cinque millimetri e mezzo su tutta quella larghezza mangerebbe la fascia proprio dove porta la flangia superiore. Il collare del grano è meno della metà del battistrada, e il suo scasso si porta via meno di un terzo del materiale.\n\nStesso teorema del coseno della finestra, con il raggio del collare del grano al posto di quello del battistrada.",
    },
    "Th_tab_cover_grip": {
        "group": "tappo della presa - linguette al piede",
    },
    "W_tab_cover_grip": {
        "group": "tappo della presa - linguette al piede",
    },
    "L_tab_cover_grip": {
        "group": "tappo della presa - linguette al piede",
    },
    "Ang_tab_cover_grip": {
        "group": "tappo della presa - linguette al piede",
    },
    "Wall_pad_cover_grip": {
        "group": "tappo della presa - linguette al piede",
    },
    "Dp_groove_cover_grip": {
        "group": "tappo della presa - linguetta a +y",
    },
    "W_groove_cover_grip": {
        "group": "tappo della presa - linguetta a +y",
    },
    "Edge_opening_motor_box": {
        "group": "pezzo unico - sportello sopra il motore",
    },
    "Th_tab_cover": {
        "group": "coperchio - linguetta sul collare",
    },
    "R_tab_cover": {
        "group": "coperchio - linguetta sul collare",
    },
    "Off_insert_cover": {
        "group": "coperchio - inserto nel collare",
    },
    "Wall_insert_cover": {
        "group": "coperchio - inserto nel collare",
    },
    "L_screw_cover": {
        "group": "comprati - vite del coperchio",
    },
    "Ang_axis_spring": {
        "group": "asse della molla, perpendicolare al braccio",
        "description": "Inclinazione dell'asse della molla. È perpendicolare al braccio, quindi la forza si traduce tutta in momento sul perno.",
    },
    "R_rest_spring_arm": {
        "group": "braccio - fianco della piastra; assembly_plan",
        "description": "Raggio a cui la molla appoggia sul braccio: è il fianco esterno della piastra, misurato sullo STEP lungo l'asse della molla. Valeva 96,22, che era il fondo della fossetta di centraggio, sepolto dieci millimetri dentro il pieno: la molla non ci sarebbe mai arrivata. Poi 106,2, il fianco del cuneo; adesso 106,8, perché con L_plate_solid la larghezza piena arriva oltre l'attacco della molla e il fianco lì è il fianco dritto della piastra, non più la rampa. Si rimisura ogni volta che si tocca la forma del braccio, e la sede nella scatola gli va dietro da sola.",
    },
    "R_seat_spring_box": {
        "group": "SCATOLA - fondo fisso della molla; assembly_plan",
        "description": "Raggio del fondo fisso contro cui la molla si comprime. Non è una scelta: è dove deve stare perché la molla montata sia lunga quanto deve. L'asse della molla è quasi radiale, quindi la somma dei raggi vale la distanza lungo l'asse a meno di due centesimi.",
    },
    "L_spring_free": {
        "group": "braccio; scatola",
        "description": "Lunghezza libera della molla scelta.",
    },
    "L_spring_fitted": {
        "group": "lunghezza a 22,3 N - da verificare in bilancia",
        "description": "Lunghezza a cui la molla sviluppa la forza voluta. Da verificare in bilancia, perché la rigidezza dichiarata dal venditore non c'è.",
    },
    "D_spigot_spring": {
        "group": "braccio - spina di centraggio della molla",
        "description": "Diametro della spina che entra nel diametro interno della molla e la tiene in asse. La molla è 8,9 di esterno e 6,9 di interno: un quarto di millimetro di gioco per lato la fa infilare senza forzare e non le lascia scappare il capo.",
    },
    "Proj_spigot_spring": {
        "group": "braccio - spina di centraggio della molla",
        "description": "Quanto la spina sporge dal fianco del braccio dentro la molla. Un terzo abbondante della molla montata basta a guidarla, e resta lontana dal fondo della tasca della scatola, che ne impegna altri sette dall'altra parte.",
    },
    "Dp_spigot_spring": {
        "group": "braccio - spina di centraggio della molla",
        "description": "Quanto la spina prosegue DENTRO il pieno della piastra. Sul pezzo finito non si vede, ed è proprio quello il punto: senza, il cilindro nasceva appoggiato al fianco con la sola faccia di base - una giunzione di testa, che è il posto da cui il pezzo si stacca. Serve anche da margine: R_rest_spring_arm è una misura arrotondata, e se cade qualche decimo fuori dal fianco vero la spina nasce staccata per davvero.",
    },
    "R_fillet_edges_box": {
        "group": "SCATOLA - raccordi sugli spigoli verticali",
        "description": "Raggio dei raccordi sugli spigoli VERTICALI della sagoma in pianta, cioè gli angoli che la mano incontra prendendo lo strumento di lato. Non vanno confusi con lo smusso orizzontale che c'era prima sui bordi del dorso: quello è stato tolto perché era la cosa sbagliata, non la quantità sbagliata - di lato non si tocca il bordo del dorso, si tocca lo spigolo del contorno. Quattro millimetri si sentono col dito e costano poco: al vertice il raccordo affonda in raggio di 0,29 volte il proprio raggio, cioè 1,2 mm sui 2,5 di parete del dorso, e dietro c'è comunque la parete di testa, spessa 9,25 mm sul lobo elettronica e 17,25 su quello meccanica. Sopra i 5 mm invece il raccordo comincerebbe a sfondare il dorso.",
    },
    "Z_shoulder_box": {
        "group": "SCATOLA - quota a cui si chiude il vano meccanico",
    },
    "D_seat_spring_box": {
        "group": "SCATOLA - tasca che guida molla e scodellino",
        "description": "Diametro della tasca nella scatola. Guida la molla, che è 8,9 di esterno, e dentro ci scorre lo scodellino.",
    },
    "Th_cup_spring": {
        "description": "Spessore del disco dello scodellino, dalla faccia su cui appoggia la molla alla conca in cui spinge il grano. Tre millimetri e mezzo di ASA sotto 22,3 N non sono in discussione: lo spessore lo detta la stampa, non il carico.",
    },
    "Cl_cup": {
        "group": "spring_cup nella sede",
        "description": "Gioco sul diametro fra scodellino e tasca. Deve scorrere senza incepparsi ma senza ballare, se no si mette di traverso e la molla con lui.",
    },
    "D_cup_spring": {
        "description": "Diametro esterno dello scodellino, per differenza dalla tasca.",
    },
    "Travel_preload": {
        "group": "SCATOLA - corsa del grano",
        "description": "Di quanto lo scodellino può andare avanti e indietro rispetto alla posizione nominale. La tasca è lunga quanto basta per la corsa da una parte, lo scodellino, e la corsa dall'altra: così il precarico si può sia aumentare sia diminuire, invece di poterlo solo mollare.",
    },
    "D_dish_grub": {
        "group": "spring_cup - conca per la punta del grano",
        "description": "Diametro della conca sul dorso dello scodellino. Più stretta del grano, così la punta ci si centra da sola e non può camminare sul dorso.",
    },
    "D_out_insert_M4": {
        "group": "SCATOLA - inserto a caldo del grano; MISURATO col calibro",
        "description": "Diametro esterno dell'inserto a caldo M4 della costruzione di riferimento, misurato col calibro su un esemplare e non preso da catalogo. Attenzione: è più grosso dell'M4 più diffuso, che sta sul 5,6. Chi ha inserti diversi cambia questo numero e L_insert_M4, e sede, invito e lunghezza del bosso lo seguono.",
    },
    "L_insert_M4": {
        "group": "SCATOLA - inserto a caldo del grano; MISURATO col calibro",
        "description": "Lunghezza dell'inserto M4 della costruzione di riferimento, misurata. È lei a decidere quanto il bosso deve essere lungo: la sede non può sbucare nella tasca dello scodellino, perché lì l'inserto non troverebbe più plastica attorno. Esiste un SECONDO TIPO, inserti M4 da 6 x 6, più corti di due millimetri e un filo più stretti (foro 5,65 invece di 5,95, quindi più parete). QUI SI TENGONO GLI 8,1, e il perché va ricordato: questo grano regola il PRECARICO DELLA MOLLA, spinge sul dorso dello scodellino sotto 22,3 N e si manovra ripetutamente, quindi vale più la presa del filetto che i due millimetri di bosso risparmiati - e in questo progetto una presa corta è già stata annotata come il difetto da non ripetere, sugli M3 da 3 mm. I 6 x 6 restano buoni per un fissaggio che non porta carico.",
    },
    "D_hole_insert_M4": {
        "group": "SCATOLA - sede dell'inserto",
        "description": "Foro della sede. È apposta più STRETTO dell'inserto: fondendo, l'inserto deve piantarsi nella plastica e farci presa, non scivolarci dentro. Tre decimi e mezzo di interferenza sono la regola per un esterno da 6,3; su un inserto più piccolo si scala da sola, perché è una differenza e non un numero fisso.",
    },
    "Dp_seat_insert_M4": {
        "group": "SCATOLA - sede dell'inserto",
        "description": "Profondità della sede: apposta un filo PIÙ dell'inserto. Se fosse esatta o corta, l'inserto resterebbe fuori a filo o spingerebbe in fondo la plastica fusa invece di lasciarla rifluire, e resterebbe storto.",
    },
    "D_leadin_insert_M4": {
        "group": "SCATOLA - invito della sede",
        "description": "Diametro della bocca svasata. Più larga dell'inserto, così l'inserto ci si appoggia dritto sulla punta del saldatore prima di cominciare a scendere, e la plastica spostata ha dove andare invece di gonfiare la faccia.",
    },
    "Dp_leadin_insert_M4": {
        "group": "SCATOLA - invito della sede",
        "description": "Profondità dello smusso conico in bocca alla sede.",
    },
    "Th_retain_insert_M4": {
        "group": "SCATOLA - parete che trattiene l'inserto del precarico",
        "description": "Quanto ASA resta FUORI dall'inserto del precarico, fra la sua faccia esterna e la faccia esterna del bosso. È la parete che lo trattiene, forata solo del passaggio del grano: la molla spinge lo scodellino, lo scodellino il grano e il grano l'inserto VERSO L'ESTERNO, e contro questa parete l'inserto lavora in compressione invece che a strappo. Prima l'inserto si piantava da fuori e quei 22,3 N tiravano per tutta la vita della macchina nella direzione in cui l'ottone si era infilato. Un millimetro e mezzo è abbondante per il carico - sull'anello fra Ø4,1 e Ø6,3 fa meno di due MPa - ed è scelto per la stampa, non per la resistenza.",
    },
    "D_grub_spring": {
        "group": "SCATOLA - grano di regolazione precarico",
        "description": "Grano di regolazione del precarico, dall'esterno della scatola. Svitandolo si scarica la frizione per il rimessaggio.",
    },
    "R_out_box": {
        "description": "Raggio della parete esterna della scatola. Deve stare oltre il bordo esterno della frizione, che arriva a Cd_motor + D_clutch/2.",
    },
    "Free_motor_floor": {
        "group": "pianta_scatola - fondo del vano meccanico",
        "description": "Quanto il fondo del motore sta sopra la faccia interna del pavimento. Serve perché il motore non appoggi sul fondo - deve stare appeso al braccio, che è quello che lo tiene in quota - e perché ci passi l'aria: scalda. Un millimetro e mezzo è quanto c'era quando il pavimento era scritto a mano a -38, ed è stato tenuto uguale per non cambiare due cose insieme.",
    },
    "Z_floor_box": {
        "group": "pianta_scatola - fondo del vano meccanico",
        "description": "La faccia ESTERNA del pavimento, cioè il piano su cui il pezzo si stampa. Era il numero -38 scritto a mano in tre posti diversi - il generatore della scatola e due volte quello dell'elettronica - e non discendeva da niente: il giorno in cui il motore si è mosso, nessuno dei tre l'avrebbe seguito. Adesso discende da chi il pavimento lo decide davvero: il fondo del motore, che a sua volta discende dalla faccia su cui il motore si avvita. È la ragione per cui rovesciare la frizione abbassa la macchina - il motore sale, e il pavimento gli va dietro.",
    },
    "Th_walls_box": {
        "description": "Spessore delle pareti. Sotto i 2,5 mm l'ASA nero lascia passare luce rossa e vicino infrarosso.",
    },
    "Ang_box_pivot": {
        "description": "Fin dove arriva la scatola dal lato del perno: è la faccia esterna della testa, al raggio a cui la scatola si accosta al collare. La testa è un piano, non un raggio, quindi più in fuori arriva meno lontano. Il collare deve arrivare almeno fin qui.",
    },
    "Ang_box_opposite": {
        "description": "Estensione angolare della scatola dal lato opposto, sul solo vano meccanico.",
    },
    "L_thread_grub": {
        "group": "pianta_scatola - labirinto luce",
        "description": "Lunghezza del filetto del grano di regolazione. La luce non può seguire l'elica, quindi il filetto stesso fa da labirinto.",
    },
    "Ang_collar_extended": {
        "description": "Fin dove il collare si estende oltre il vano meccanico per sostenere quello elettronico, che altrimenti resterebbe a sbalzo. Limitato dall'ingombro del rotatore, non dalla struttura.",
    },
    "R_envelope_optical": {
        "description": "Raggio da tenere libero attorno all'asse ottico. È una MISURA presa sul telescopio, non una scelta: i 48 mm sono veri. Quello che non si sa più è COSA fu misurato - se il corpo del rotatore o il cono di luce - e sono due cose diverse: il corpo del rotatore è un ostacolo solido da una parte sola, il cono di luce è un volume da non invadere da nessuna. Finché non si rimisura, i 48 valgono come vincolo DA TUTTE E DUE LE PARTI: è l'ipotesi prudente, ed è quella che i controlli applicano. Le flange del collare vengono tagliate da questo cilindro (oltre 130 gradi ci finirebbero dentro), la staffa del sensore ci entra solo col mozzetto e il suo coperchio non va oltre la staffa. Cosa andare a rimisurare, e cosa cambierebbe se i 48 fossero il rotatore, sta in ROADMAP.md.",
    },
    "D_pivot_hub": {
        "description": "Diametro del perno del disco, che affiora a filo di tutte e due le facce. Il sensore sta dal lato telescopio: lì ci si incolla sopra il magnete e ci si centra la staffa.",
    },
    "Cl_ring_bracket": {
        "description": "Gioco radiale dell'anello della staffa sul magnete. È il primo termine del bilancio di centraggio del sensore, quindi si tiene stretto: gira di rado e per pochi gradi, l'usura non è un problema.",
    },
    "D_in_ring_bracket": {
        "description": "Diametro interno dell'anello di centraggio della staffa. Si quota sul MAGNETE, non sul perno: il perno affiora a filo della faccia e l'anello non lo può toccare, mentre il magnete sporge di un millimetro ed è l'unica cosa cilindrica che ci sia da afferrare. Prima era quotato sul perno, 8,55, e lasciava tre decimi di gioco su un centraggio che ne ammette due e mezzo in tutto.",
    },
    "Comp_hole_printing": {
        "description": "Quanto un foro esce SOTTO MISURA dalla stampa, e quindi di quanto va disegnato più largo. MISURATO su una frizione in ASA: foro disegnato 5,40, letto col calibro 5,20. Prima era dichiarato - stesso valore, ma assunto - e da lui discendono il foro dell'albero, la sede dei cuscinetti, i fori di passaggio M3, il foro del magnete e la sede del cappuccio: cinque quote che stavano in piedi su un numero mai verificato. La conferma è doppia, perché alla misura è seguita la prova in funzione: la frizione stampata con queste quote si infila sull'albero senza sforzare e senza ballare. È un numero della MACCHINA E DEL MATERIALE, non del progetto: chi stampa in altro materiale lo rifà, e il modo di rifarlo è questo - si sottrae il misurato dal disegnato, non si deduce da un sintomo.",
    },
    "R_out_foot": {
        "description": "Raggio esterno dei piedini di prova. Il mozzetto della staffa sta a 7,45 perché lì lo ferma il setto attorno ai fori M2, ma il piedino non deve centrare niente né stare dentro un ingombro: con l'anello svuotato dal foro del magnete, forato dalle viti e scavato sotto la basetta, a 7,45 viene un pezzo che si rompe in mano. A 10 la corona resta larga quasi sei millimetri.",
    },
    "R_relief_capacitor": {
        "group": "gap_gauges - misurato sul pezzo stampato",
        "description": "Raggio a cui il piedino viene tagliato dritto, dal lato opposto alla linguetta. Lì sotto la basetta c'è il condensatore da 104, che è il componente più alto del modulo e non sta nei tre decimi che lo scasso lascia: il piedino ci sbatteva contro e la basetta si posava su lui invece che sui pad, cioè misurava un traferro che non era quello. Oltre questo raggio il materiale non serve a niente - da quella parte il piedino non centra e non tiene niente - e toglierlo fa anche passare il connettore.",
    },
    "Halfw_relief": {
        "description": "Metà larghezza della fascia ribassata davanti al taglio, misurata dall'asse dei fori M2. Tenuta dentro i 4,6 perché i due pad d'appoggio cominciano a 60 gradi, cioè a 5 di ordinata: la fascia arriva fin dove può senza mangiarsi il piano che regge la basetta.",
    },
    "H_bottom_relief": {
        "description": "Quanto resta in piedi della fascia ribassata: due strati da 0,2. Non è zero perché il pezzo deve restare intero - l'anello attorno al foro del magnete è l'unica cosa che tiene insieme i due pad - e non è di più perché sopra ci passa il condensatore.",
    },
    "Cl_holes_M2_foot": {
        "description": "Quanto i fori M2 dei piedini di prova sono più larghi di quelli della staffa vera. Sulla staffa il foro è 1,8 e la vite ci si forma il filetto: si stringe una volta sola e deve tenere. Sui piedini la stessa vite entra ed esce sette volte, una per altezza, e a 1,8 ogni giro rifà il filetto in un foro già fatto: il materiale si sbriciola e il piedino si apre. Un decimo in più basta perché la vite riprenda il filetto che ha già trovato.",
    },
    "Cl_test_magnet": {
        "description": "Quanto i piedini di prova hanno il foro più largo della staffa vera. Il piedino deve girare libero sul magnete anche se la compensazione di stampa non è azzeccata: un piedino che si pianta costa una stampa, e nella prova del traferro un decimo di centraggio in più non cambia la lettura dell'AGC. Più di un decimo però non si può: a 0,2 lo scentramento possibile arriva a 0,275 e supera i 0,25 che l'AS5600 ammette, e il controllo lo dice. Se il foro esce stretto dalla stampa non si allarga qui, si corregge Comp_hole_printing, che è il numero della stampante e vale anche per la staffa vera.",
    },
    "D_hole_magnet_printing": {
        "description": "Il diametro con cui il foro del magnete viene disegnato e stampato. Quello di progetto resta D_in_ring_bracket: questo è lui più la compensazione di stampa.",
    },
    "D_magnet": {
        "group": "sensor_bracket - diametrale, si autocentra sul perno",
        "description": "Diametro del magnete diametrale. Scelto pari al perno così si centra da solo appoggiandolo a filo.",
    },
    "Th_magnet": {
        "description": "Spessore del magnete. Entra nella catena che fissa l'altezza di appoggio della basetta.",
    },
    "Th_spacer_magnet": {
        "description": "Spessore del distanziale fra testa del perno e magnete. Il perno affiora a filo della faccia e il magnete è più largo di lui: senza distanziale il magnete appoggia sul coperchio della ruota, che è fermo mentre lui gira. L'attrito in sé è trascurabile - mezzo grammo su un anello di 0,025 - ma il cordoncino di colla che sborda dal bordo si impunta lì, e se il disco va in battuta assiale è il giunto di colla a fare da reggispinta. Sotto il distanziale il magnete resta sollevato e non tocca più niente. Ogni decimo qui è un decimo in meno di traferro a parità di appoggio.",
    },
    "D_spacer_magnet": {
        "description": "Diametro del distanziale. Volutamente più piccolo del perno (7,95): così non può toccare il coperchio nemmeno se lo si incolla scentrato, e il centraggio continuano a farlo il magnete sul perno e l'occhio sul filo d'alluminio. Va di plastica, non di metallo: sta dentro il campo del magnete.",
    },
    "Ang_module_on_bracket": {
        "description": "Di quanto il modulo AS5600 è girato sulla staffa, rispetto al verso in cui è stato misurato (fori M2 sull'asse Y, condensatore verso +X). A 45 gradi il modulo è ALLINEATO AI BRACCI, ed è quello che mette a posto tutto. Il condensatore - che è anche il punto da cui esce il cavo - va in linea col braccio del cavo: lì il braccio si allarga e si fora, e quel foro fa due mestieri, sfogo al condensatore e uscita al cavo. Le TRE piazzole grandi che non si usano (PWM, GND, 5V) cadono allora sull'ALTRO braccio, che è materiale pieno a tutta altezza: il loro supporto ci sta sopra e si vede, invece di essere un gonfiore sul mozzetto. Il primo tentativo era 135 gradi, per paura che lo sfogo - largo 9,2 su un braccio largo 8 - tagliasse il braccio in due: e lo taglia davvero, ma la risposta è allargare il braccio lì, non spostare il modulo altrove. A 135 il supporto finiva a sbalzo sul mozzetto, dalla parte dell'asse ottico, e non ci si poteva allargare.",
    },
    "W_arm_widened_relief": {
        "description": "Larghezza a cui si porta il braccio del cavo nel tratto dove lo si fora per il condensatore. Il braccio è largo 8 e il foro 9,2: tagliato così il braccio si spezza in due, e infatti provandolo la staffa esce in due pezzi. A 15 restano 2,9 di materiale per parte, cioè due costole che scavalcano il foro. È materiale che sta dalla parte opposta all'asse ottico, quindi allargare lì non costa niente di ingombro.",
    },
    "R_end_widening_relief": {
        "description": "Fin dove arriva l'allargamento del braccio. Deve superare il foro, che finisce a r 11,4, se no le due costole si riuniscono dentro il foro invece che fuori.",
    },
    "Cd_holes_module": {
        "description": "Interasse dei due fori di fissaggio del modulo AS5600.",
    },
    "L_board_module": {
        "description": "Diametro della basetta, che non è rettangolare: è un tondo con due spianature. Misurato sul modulo vero.",
    },
    "W_board_module": {
        "description": "Distanza fra le due spianature della basetta. I due fori M2 stanno sull'asse delle spianature, non su quello del diametro pieno.",
    },
    "D_holes_board": {
        "group": "sensor_bracket - misurato sul modulo",
        "description": "Diametro dei fori nella basetta del modulo. Misurato: la vite M2 ci passa di misura, quindi il modulo non balla sulla vite. Il gioco che resta nel centraggio del sensore viene da qui, non più da un foro di passaggio largo.",
    },
    "D_holes_M2": {
        "description": "Foro d'invito per le viti M2 nel mozzetto: la vite ci si fa il filetto da sola. Era 2,2, cioè un foro di passaggio, ma sotto il mozzetto c'è la faccia del corpo e non c'è posto per nessun dado: la vite ci girava dentro libera e non teneva niente. 1,8 e non 1,7 perché le viti in uso sono a filetto cilindrico, non autofilettanti: non hanno taglienti e a 1,7 spaccherebbero il mozzetto invece di formare il filetto. In stampa il foro esce comunque un decimo scarso.",
    },
    "H_min_foot_test": {
        "group": "attrezzi - piedini di prova del traferro",
    },
    "N_foot_test": {
        "group": "attrezzi - piedini di prova del traferro",
    },
    "Pitch_foot_test": {
        "group": "attrezzi - piedini di prova del traferro",
    },
    "Gap_nominal": {
        "group": "sensor_bracket - regolare con AGC, min ammesso 0,5",
        "description": "Aria fra faccia superiore del magnete e corpo del chip. Valore di partenza: si regola stampando piedini di altezza diversa e scegliendo quello con AGC vicino a metà scala.",
    },
    "Th_board_module": {
        "group": "sensor_bracket - misurato sul modulo",
        "description": "Spessore della basetta del modulo, misurato col calibro: 1,6, che è anche lo standard. Entra solo nella lunghezza della vite: la vite attraversa la basetta e quel che resta va nel mozzetto, e con 4 mm ne restano 2,4 di presa.",
    },
    "L_screw_M2": {
        "group": "sensor_bracket - vite del modulo",
        "description": "Lunghezza delle due viti che tengono il modulo. Non è libera: sotto il mozzetto c'è la faccia del corpo, quindi la vite non deve sbucare. Con basetta 1,6 e mozzetto 3,43 una M2x6 uscirebbe di sotto, e sul piedino di prova più basso solleverebbe il pezzo dalla faccia.",
    },
    "H_body_chip": {
        "group": "sensor_bracket - misurato sul modulo",
        "description": "Quanto il corpo del chip sporge sotto la basetta. Misurato: 1,63, non 1,75 come diceva il massimo da datasheet del SOIC-8. È il terzo anello della catena che fissa l'appoggio del modulo, e sposta il piano di un decimo.",
    },
    "Th_glue_stack_magnet": {
        "group": "misurato sul montaggio vero",
        "description": "Quanto la pila incollata viene più alta della somma dei pezzi. Distanziale e magnete fanno 1,8 di progetto, ma misurati sul montaggio vero sporgono 2,3 sopra la faccia: mezzo millimetro se ne va nei due giunti di colla e nella tolleranza di stampa del distanziale. Senza questo termine la staffa esce mezzo millimetro troppo bassa e il traferro si stringe di altrettanto - col piedino da 4,0 il traferro reale era 0,07, cioè il magnete sfiorava il chip.",
    },
    "H_rest_module": {
        "description": "Quota a cui appoggia la basetta del sensore, dalla faccia lato telescopio. Da quando il magnete sta su un distanziale, la catena parte da lì: tutto quello che sta sotto il magnete alza anche l'appoggio, se no il traferro si stringe di altrettanto.",
    },
    "Th_hub_bracket": {
        "description": "Materiale che resta fra i fori M2 del modulo e il bordo del mozzetto della staffa. Detta il diametro del mozzetto: prima era quotato sull'anello e i fori M2 gli sbordavano fuori di mezzo millimetro.",
    },
    "Dp_notch_module": {
        "description": "Di quanto si abbassa il piano sotto la basetta del sensore, tutt'attorno ai due pad delle viti M2. Il lato inferiore del modulo non è liscio: ci sono resistenze e condensatori SMD con le loro saldature, e prima il piano era pieno, quindi la basetta ci si appoggiava sopra invece che sui pad. Il componente più alto misura 0,93, quindi 1,2 lascia poco meno di tre decimi.",
    },
    "R_components_module": {
        "group": "sensor_bracket - misurato sulla foto del modulo",
        "description": "Fin dove arrivano i componenti SMD sotto la basetta, dentro il settore dei fori M2. I quattro componenti stanno nei quadranti diagonali e vanno fino a r 6,4, ma verso i fori l'angolo di R2 e quello di C1 si fermano a 4,6: è questo il numero che detta da dove può cominciare il pad.",
    },
    "R_pad_module": {
        "description": "Raggio a cui comincia il pad d'appoggio della basetta. Sta mezzo millimetro oltre i componenti: più dentro la basetta si poserebbe su R2 e C1, più fuori resterebbe troppo poco materiale attorno alla vite.",
    },
    "H_capacitor_module": {
        "group": "sensor_bracket; gap_gauges - MISURATO",
        "description": "Quanto il condensatore da 104 sporge sotto la basetta. Quattro e due: il piano d'appoggio sta a 5,13 sopra la faccia della staffa, quindi sotto il condensatore resterebbero 0,93 mm - e lo scasso del modulo, che ne toglie 1,2, non basta di tre millimetri. Da qui il buco passante: il condensatore ci infila dentro e sporge dalla faccia inferiore, restando comunque a 0,93 dalla faccia del corpo su cui la staffa appoggia.",
    },
    "Pitch_pads_module": {
        "description": "Passo delle piazzole del modulo, il decimo di pollice di sempre. Serve a sapere DOVE cadono le tre piazzole libere: in fila sulla spianatura a questo passo, cioè a r 7,50 quella di mezzo e 7,92 le due di fianco. Sono numeri che stanno fuori dal mozzetto, che finisce a 7,45, ed è il motivo per cui il loro supporto deve uscire dal mozzetto invece di fermarcisi.",
    },
    "Ang_pad_pads_free": {
        "description": "Semiampiezza del supporto dal lato delle tre piazzole che non si usano. Le tre piazzole stanno entro +-18,7 gradi dalla mezzeria, quindi 25 le copre con sei gradi di margine per parte. Più largo non si può, ed è un limite che non si vede dal disegno: il supporto esce dal mozzetto per arrivare sotto le piazzole, e più lo si allarga più si sporge verso l'asse ottico, che sta proprio da quella parte. A 25 gradi il punto più vicino all'asse resta a 40,65, cioè fuori dai 40,55 a cui arriva il mozzetto; a 27 sarebbe già 40,39 e la staffa entrerebbe nel rotatore più del mozzetto, che è la regola che non si tocca. Provato: a 50 gradi si scende a 39,58.",
    },
    "Ang_pad_module": {
        "description": "Semiampiezza del pad rialzato attorno a ciascun foro M2: è quel che resta del piano d'appoggio. Stretto apposta, perché meno piano si lascia e meno probabile è incontrarci un componente; deve però restare materiale attorno al foro per la vite.",
    },
    "R_components_diagonal_module": {
        "group": "sensor_bracket - misurato sulla foto del modulo",
        "description": "Fin dove arrivano i componenti SMD sotto la basetta nei QUADRANTI DIAGONALI, cioè fra un foro M2 e l'altro. È lo stesso numero che stava scritto solo nella prosa di R_components_module - 'i quattro componenti stanno nei quadranti diagonali e vanno fino a r 6,4' - e lì non lo poteva usare nessuno: il terzo appoggio cade proprio in un quadrante diagonale, e senza questa quota il suo raggio di partenza sarebbe stato un numero scritto a mano.",
    },
    "R_pad_back_v": {
        "description": "Raggio a cui comincia il terzo appoggio, quello sul dorso della V. Non è R_pad_module: quello vale attorno ai fori M2, dove il modulo non porta niente, mentre qui si è in un quadrante diagonale e i componenti arrivano a 6,4. Mezzo millimetro oltre di loro, con la stessa regola che già detta R_pad_module.",
    },
    "Ang_pad_back_v": {
        "description": "Semiampiezza del terzo appoggio, centrato sul dorso della V. Serve perché i due pad di prima stanno su una sola RETTA - le loro mezzerie sono a 135 e a -45 gradi, cioè opposte - e su due appoggi in fila la basetta può ancora dondolare attorno a quella retta: allargare il pad del lato libero, che è quello che era stato fatto, non toglie il dondolio perché resta sulla stessa retta. Trentacinque gradi mettono il terzo appoggio a 45 gradi dalla retta, sul bordo che restava scoperto, e il pad resta comunque dentro il contorno della basetta - quindi non si avvicina all'asse ottico più di quanto ci sia già la basetta stessa, che è il metro che il progetto applica anche al coperchio.",
    },
    "Cl_notch_module": {
        "description": "Di quanto lo scasso sotto la basetta sborda oltre il contorno del modulo. La basetta non si posa mai sul bordo dello scasso, nemmeno montata storta.",
    },
    "Ang_bracket_sensor": {
        "description": "Bisettrice della staffa del sensore, che è una V con un braccio per ciascuna delle due M3 del collare. La staffa sta sulla faccia lato telescopio, dove c'è il rotatore: la sua circonferenza arriva al centro disco (R_envelope_optical è più grande di Off_hole_optical), quindi ogni braccio che va verso l'asse ottico ci entra, e le sole viti dalla parte libera sono Ang_screw_A e Ang_screw_B. Derivata da loro: se le viti vere stanno altrove, la staffa le segue.",
    },
    "R_screw_anchor": {
        "group": "sensor_bracket - M3 del collare, da M3x12",
        "description": "Raggio delle quattro viti M3 esistenti sul fondello, lato telescopio. La staffa del sensore usa le due del collare, Ang_screw_A e Ang_screw_B: le sue palette si stringono sopra la flangia posteriore con la stessa vite, allungata: paletta 3,43 + flangia 3 fanno 6,43, e una M3x12 ne lascia 5,57 in presa sui 6 del filetto.",
    },
    "Cl_cap": {
        "description": "Gioco radiale della sede del magnete nel cappuccio: si deve infilare a mano e non ballare.",
    },
    "D_seat_cap": {
        "description": "Diametro della sede in cui sta il magnete mentre la colla prende. Porta la stessa compensazione di stampa del foro dell'anello, per lo stesso motivo: senza, la sede esce sotto misura e il magnete non ci entra. Il gioco di progetto resta 0,05 per parte, che è quel che serve perché la sede lo tenga squadrato.",
    },
    "D_cap": {
        "description": "Diametro esterno del cappuccio. Appoggia sulla faccia lato telescopio attorno al magnete, quindi deve essere largo abbastanza da stare piano e stretto da entrare nell'anello del collare.",
    },
    "Dp_seat_cap": {
        "description": "Profondità della sede, cioè l'altezza della parete che circonda il magnete. Era profonda quanto il magnete è spesso, 1 mm, e lì dentro il magnete non era guidato da niente: bastava un niente per posarlo storto. Con 4 mm di parete non si può inclinare mentre scende, e si accompagna in fondo spingendolo dal foro di sfilo.",
    },
    "H_cap": {
        "description": "Altezza totale del cappuccio: la sede più due millimetri di cielo, che è quanto serve perché il foro di sfilo abbia una parete attorno e il pezzo si prenda con due dita.",
    },
    "D_pushout_cap": {
        "description": "Foro passante al centro del cappuccio, per spingere fuori il magnete se resta incollato dentro la sede.",
    },
    "Trq_detent_crest_mNm": {
        "group": "misurata - verso facile",
        "description": "Coppia di picco per superare la cresta del fermo nel verso facile, misurata sulla ruota di riferimento prima di togliere il fermo. Il fermo ora si toglie sempre (il motore non riesce a uscire dalle sue tacche, guida di montaggio capitolo 10); il numero resta come carico prudente per il controllo della coppia del motore.",
    },
    "Trq_hold_mNm": {
        "group": "misurata - verso duro",
        "description": "Coppia che il fermo opponeva nel verso duro, misurata sulla ruota di riferimento prima di toglierlo. Non tiene più niente: il fermo ora si toglie sempre (il motore non riesce a uscire dalle sue tacche), e se il disco resta fermo a motore spento lo sorveglia l'allarme di deriva del firmware.",
    },
    "Preload_N": {
        "group": "progetto",
        "description": "Forza con cui la frizione preme sul disco: la forza della molla attraverso i bracci di leva del braccio attorno al perno. Un tempo andava al contrario, ricavata dalla coppia di cresta del fermo: scartato, ora che il fermo si toglie.",
    },
    "Force_spring_N": {
        "group": "progetto",
        "description": "Forza della molla di precarico alla lunghezza di montaggio: 12-15 N, circa il doppio di Force_spring_min_N, la spinta che col battistrada 87A è bastata nella prova a mano. La lunghezza di montaggio discende da lei e dalla rigidezza misurata in bilancia; da verificare in bilancia a molla montata.",
    },
    "Force_spring_min_N": {
        "group": "progetto",
        "description": "La spinta sul braccio, nel verso della molla, che è bastata a trascinare il disco: MISURATA sulla ruota di riferimento, 700 g sulla bilancia da cucina, col battistrada in TPU 87A. Sostituisce la vecchia stima dalla coppia di cresta del fermo (attrito 0,6, fattore 2,5), scritta per un battistrada 95A.",
    },
}
