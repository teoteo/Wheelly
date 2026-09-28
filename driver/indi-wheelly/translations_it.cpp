// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: LGPL-2.1-or-later

// Wheelly - the Italian texts for the user, by key.
//
// A file of its own because INDI's drivers are English, and a copy
// of this folder inside INDI's tree builds without it (CMake option
// WHEELLY_ITALIAN, OFF there, ON in the Wheelly repository). The keys are
// those of the English catalogue in translations.cpp, where the comments on
// what each text is for also live; firmware/test/test_driver_standalone.py
// fails if a key is here and not there, or there and not here.
//
// Italian written with the real accented letters (perché, è), never the
// apostrophe in their place.

#include "translations.h"

namespace wheelly
{

const CatalogueEntry ITALIAN_CATALOGUE[] =
{
    {"prop.slot",               "Posizione"},
    {"prop.names",              "Nomi dei filtri"},
    {"prop.position",           "Dov'è la ruota"},
    {"prop.position.angle",     "Angolo"},
    {"prop.position.err",       "Errore residuo"},
    {"prop.position.retries",   "Ritentativi"},
    {"prop.sensor",             "Sensore magnetico"},
    {"prop.sensor.agc",         "Guadagno"},
    {"prop.sensor.mag",         "Magnitude"},
    {"prop.sensor.md",          "Magnete rilevato"},
    {"prop.sensor.ml",          "Campo troppo debole"},
    {"prop.sensor.mh",          "Campo troppo forte"},
    {"prop.angle.value",        "Angolo di taratura (°)"},
    {"prop.angles.here",        "▶ %1$s"},
    {"prop.angles.unsaved",     "▶ %1$s *"},
    {"prop.actions",            "Azioni di taratura"},
    {"prop.slots",              "Numero di posizioni"},
    {"prop.slots.count",        "Posizioni"},
    {"prop.actions.save",       "Salva nella ruota"},
    {"prop.wheelconfig",        "Configurazione della ruota"},
    {"num.decimal",             ","},
    {"prop.jog.down",           "Passo indietro"},
    {"prop.jog.up",             "Passo avanti"},
    {"prop.jog.mpitch",         "-%1$s°"},
    {"prop.jog.m10",            "-10°"},
    {"prop.jog.m1",             "-1°"},
    {"prop.jog.m01",            "-0,1°"},
    {"prop.jog.p01",            "+0,1°"},
    {"prop.jog.p1",             "+1°"},
    {"prop.jog.p10",            "+10°"},
    {"prop.jog.ppitch",         "+%1$s°"},
    {"prop.tolerance",          "Tolleranze"},
    {"prop.tolerance.good",     "Buona (gradi)"},
    {"prop.tolerance.warn",     "Allarme (gradi)"},
    {"prop.tolerance.retries",  "Ritentativi massimi"},
    {"prop.motor",              "Motore"},
    {"prop.motor.ma",           "Corrente di marcia (mA)"},
    {"prop.motor.speed",        "Velocità"},
    {"prop.motor.accel",        "Accelerazione"},
    {"prop.hold",               "Tenuta a riposo"},
    {"prop.hold.ma",            "Corrente (mA, 0 = rilasciata)"},
    {"prop.hold.settle",        "Tenuta dopo l'arrivo (ms)"},
    {"prop.direction",          "Verso di rotazione"},
    {"prop.direction.shortest", "La via più corta"},
    {"prop.direction.up",       "Solo angoli crescenti"},
    {"prop.direction.down",     "Solo angoli decrescenti"},
    {"prop.led",                "LED"},
    {"prop.led.on",             "Acceso fisso"},
    {"prop.led.pulse",          "Pulsa durante il movimento"},
    {"prop.led.off",            "Spento"},
    {"prop.led.test",           "Prova (lampeggia WHEELLY)"},
    {"prop.diag",               "Controllo dell'hardware"},
    {"prop.diag.run",           "Interroga la ruota"},
    {"prop.sweep",              "Spazzolata del magnete"},
    {"prop.sweep.run",          "Fai un giro completo"},
    {"prop.sweep.image",        "Ultima spazzolata"},
    {"prop.sweep.plot",         "Grafico"},
    {"prop.log",                "Registro dei movimenti"},
    {"prop.log.on",             "Acceso"},
    {"prop.log.off",            "Spento"},
    {"prop.files",              "File su disco"},
    {"prop.files.log",          "Registro dei movimenti"},
    {"prop.files.sweep",        "Ultima spazzolata"},
    {"prop.files.none",         "non ancora scritta"},
    {"prop.sweepdir",           "Cartella delle spazzolate"},
    {"prop.sweepdir.path",      "Cartella"},
    {"prop.firmware",           "Firmware"},
    {"prop.firmware.version",   "Versione"},
    {"prop.firmware.proto",     "Protocollo"},
    {"prop.firmware.serial",    "Numero di serie"},
    {"prop.language",           "Lingua"},
    {"prop.language.auto",      "Come il sistema"},
    {"prop.language.en",        "Inglese"},
    {"prop.language.it",        "Italiano"},
    {
        "msg.connected",
        "Collegato a Wheelly, firmware %1$s, protocollo %2$s."
    },
    {
        "msg.wrong.device",
        "Il dispositivo su questa porta non ha risposto come una ruota Wheelly. "
        "Controlla la porta."
    },
    {
        "msg.serial.other",
        "Questa è una Wheelly diversa (seriale %1$s) da quella di questo profilo "
        "(%2$s): cerco la tua sulle altre porte."
    },
    {
        "msg.serial.notfound",
        "La ruota di questo profilo (seriale %1$s) non è su nessuna porta. Mi "
        "collego alla Wheelly che c'è."
    },
    {
        "msg.serial.learned",
        "D'ora in poi questo profilo cerca la ruota col seriale %1$s."
    },
    {
        "msg.drift.suggest",
        "La ruota si è spostata di %1$s gradi da sola mentre era ferma, oltre la "
        "tolleranza d'allarme, e a riposo il motore è rilasciato, quindi niente la "
        "tiene: accendi la tenuta a riposo - %2$s mA è il valore che questo "
        "progetto consiglia."
    },
    {
        "msg.drift.holding",
        "La ruota si è spostata di %1$s gradi da sola mentre era ferma, oltre la "
        "tolleranza d'allarme, e la tenuta a riposo è già accesa a %2$s mA. "
        "Alzarla può aiutare, ma guarda anche la meccanica: una frizione che molla "
        "da ferma è una faccenda di precarico della molla."
    },
    {
        "msg.wrong.protocol",
        "Questo firmware parla il protocollo %1$s, il driver parla il %2$s. "
        "Aggiorna uno dei due."
    },
    {
        "msg.slots.unsupported",
        "La ruota dichiara %1$s posizioni, e questo driver ne gestisce "
        "da %2$s a %3$s."
    },
    {
        "msg.no.answer",
        "La ruota non risponde."
    },
    {
        "msg.moving",
        "Vado alla posizione %1$s."
    },
    {
        "msg.arrived",
        "Posizione %1$s raggiunta, errore residuo %2$s gradi."
    },
    {
        "msg.warning",
        "Posizione %1$s raggiunta ma fuori di %2$s gradi, oltre la tolleranza "
        "buona. La ripresa prosegue."
    },
    {
        "msg.failed",
        "Posizione %1$s NON raggiunta: fuori di %2$s gradi dopo %3$s ritentativi. "
        "La ripresa viene fermata, così non si scatta a ruota fuori posto."
    },
    {
        "msg.timeout",
        "La ruota non ha finito entro %1$s secondi. La ripresa viene fermata."
    },
    {
        "msg.link.lost",
        "Il collegamento USB con la ruota si è interrotto (%1$s). Il driver resta "
        "collegato e si ricollega da solo appena la ruota torna; fino ad allora i "
        "comandi non le arrivano."
    },
    {
        "msg.link.hangup",
        "la porta è stata chiusa"
    },
    {
        "msg.link.back",
        "La ruota è tornata su %1$s: ricollegata."
    },
    {
        "msg.link.down",
        "In questo momento la ruota non è raggiungibile: aspetto che torni il "
        "collegamento USB."
    },
    {
        "msg.driver.power",
        "Il driver del motore ha ricevuto i 12 V dopo l'avvio della ruota, ed è "
        "stato configurato adesso."
    },
    {
        "msg.driver.reset",
        "Il driver del motore aveva perso le impostazioni - i 12 V sono mancati e "
        "tornati - ed è stato configurato di nuovo prima di muovere."
    },
    {
        "msg.magnet.lost",
        "Il sensore non rileva più il magnete. È un guaio serio: controlla il "
        "cablaggio del sensore prima di continuare a riprendere."
    },
    {
        "msg.hold.on",
        "La tenuta è accesa: il motore resta alimentato a riposo. Scalda accanto "
        "al sensore e il driver canta durante la posa. Lasciala spenta, a meno "
        "che la ruota non si sposti da sola a riposo."
    },
    {
        "msg.hint.detent",
        "Se il motore si blocca o la frizione slitta, controlla prima di tutto che "
        "il fermo della ruota (lo scatto a molla) sia stato tolto: il motore non "
        "riesce a uscire dalle sue tacche. Guida di montaggio, capitolo 10, Il corpo "
        "della ruota."
    },
    {
        "msg.diag",
        "Chiedo alla ruota se sta parlando davvero col suo sensore e col suo "
        "driver del motore:"
    },
    {
        "msg.slots.changed",
        "La ruota ora ha %1$s posizioni. La taratura riparte da angoli equidistanti "
        "e nomi generici: insegna ogni posizione (i passi, poi Set sulla sua riga) "
        "e dai i nomi ai filtri, poi premi 'Salva nella ruota'. Fino ad allora non viene "
        "scritto niente: spegnendo la ruota torna la configurazione di prima."
    },
    {
        "msg.slots.refused",
        "La ruota ha rifiutato il nuovo numero di posizioni: %1$s"
    },
    {
        "msg.saved",
        "Taratura salvata nella ruota."
    },
    {
        "msg.notconnected",
        "Prima collega la ruota."
    },
    {
        "msg.angle.changed",
        "Posizione %1$s: %2$s° → %3$s°."
    },
    {
        "msg.angle.volatile",
        "I nuovi angoli stanno nella memoria di lavoro della ruota: premi «Salva "
        "nella ruota» per tenerli anche dopo lo spegnimento."
    },
    {
        "msg.angle.refused",
        "Posizione %1$s: l'angolo non è stato cambiato. %2$s"
    },
    {
        "msg.angle.notnow",
        "Non si possono cambiare gli angoli mentre la ruota si muove: aspetta che "
        "si fermi."
    },
    {
        "msg.taught",
        "La posizione %1$s vuol dire d'ora in poi l'angolo in cui la ruota si "
        "trova adesso. Premi 'Salva nella ruota' per tenerla anche dopo lo "
        "spegnimento."
    },
    {
        "msg.jog.done",
        "La ruota è a %1$s°, a %2$s° da dove chiedeva il passo."
    },
    {
        "msg.jog.failed",
        "La ruota non è arrivata dove chiedeva il passo: è a %1$s°, a %2$s° di "
        "distanza. Riprova, oppure girala a mano e scrivi nella sua riga l'angolo "
        "che raggiunge."
    },
    {
        "msg.jog.notnow",
        "Non si può spostare la ruota di un passo mentre si muove: aspetta che si "
        "fermi."
    },
    {
        "msg.led.pulse",
        "Il LED resta spento, e respira piano mentre la ruota va a un altro "
        "filtro. Premi «Salva nella ruota» per tenere la scelta anche dopo lo spegnimento."
    },
    {
        "msg.led.mode",
        "Modo del LED cambiato. Premi «Salva nella ruota» per tenere la scelta anche dopo lo "
        "spegnimento."
    },
    {
        "msg.direction.set",
        "Verso di rotazione cambiato. Premi «Salva nella ruota» per tenere la scelta anche dopo lo "
        "spegnimento."
    },
    {
        "msg.ceiling.ekos",
        "Con queste impostazioni del motore il cambio di filtro più lungo può durare fino a "
        "%1$s s, più dei %2$s s dopo i quali Ekos rinuncia. Alza la velocità del motore, "
        "accorcia la tenuta dopo l'arrivo, o scegli la via più corta se la tua ruota lo "
        "permette."
    },
    {
        "msg.led.test",
        "Il LED sta lampeggiando WHEELLY in Morse per %1$s secondi. "
        "Fallo a coperchio aperto o di giorno: sta dentro il cono ottico."
    },
    {
        "msg.sweep.start",
        "Faccio un giro completo misurando il magnete a ogni passo. La ruota si "
        "muove: fallo a coperchio aperto, non durante una sequenza."
    },
    {
        "msg.sweep.done",
        "Spazzolata finita: %1$s campioni, magnitude da %2$s a %3$s, escursione "
        "%4$s conteggi (%5$s%%). Più è piccola, meglio il magnete è centrato."
    },
    {
        "msg.sweep.file",
        "Il grafico è qui: %1$s"
    },
    {
        "msg.sweepdir.bad",
        "La cartella %1$s adesso non si può usare: %2$s. Le spazzolate non "
        "verranno salvate finché non si potrà."
    },
    {
        "msg.sweep.nofile",
        "Non riesco a scrivere il grafico in %1$s: %2$s"
    },
    {
        "msg.sweep.notnow",
        "Non si può fare la spazzolata mentre la ruota si muove: aspetta che si "
        "fermi."
    },
    {
        "msg.sweep.failed",
        "La spazzolata si è fermata prima di finire il giro: il grafico direbbe "
        "una cosa falsa sul magnete, quindi non l'ho fatto."
    },
    {
        "msg.log.on",
        "Registro dei movimenti acceso: %1$s"
    },
    {
        "msg.log.off",
        "Registro dei movimenti spento."
    },
    {
        "msg.log.failed",
        "Non riesco a scrivere il file di registro %1$s: %2$s"
    },
    {
        "msg.language.later",
        "La lingua cambia quando il driver riparte: i pannelli si costruiscono una "
        "volta sola, all'avvio. In Ekos ferma INDI e fallo ripartire."
    },
    {"graf.titolo",             "SPAZZOLATA DEL MAGNETE"},
    {"graf.asse.x",             "ANGOLO (GRADI)"},
    {"graf.asse.y",             "MAGNITUDE"},
    {"graf.campioni",           "CAMPIONI"},
    {"graf.escursione",         "ESCURSIONE"},
    {"graf.min",                "MIN"},
    {"graf.max",                "MAX"},
    {
        "err.1",
        "La ruota non ha capito il comando."
    },
    {
        "err.2",
        "Argomenti sbagliati per il comando."
    },
    {
        "err.3",
        "Valore fuori intervallo: atteso %1$s, ricevuto %2$s."
    },
    {
        "err.4",
        "Il sensore di posizione non risponde. Controlla il cablaggio, e "
        "il ponticello VDD5V-VDD3V3 sul modulo."
    },
    {
        "err.5",
        "Il sensore funziona ma non vede il magnete."
    },
    {
        "err.6",
        "Il driver del motore non risponde: l'alimentazione a 12 V è collegata? "
        "Senza, la ruota non si muove."
    },
    {
        "err.7",
        "Non si può adesso: la ruota sta lavorando."
    },
    {
        "err.8",
        "La ruota non è riuscita a salvare nella sua memoria."
    },
    {
        "err.9",
        "Nome di filtro non valido (%1$s)."
    },
    {
        "err.unknown",
        "La ruota ha segnalato l'errore %1$s."
    },
    {
        "nome.empty",
        "il nome è vuoto"
    },
    {
        "nome.too-long",
        "troppo lungo: al massimo 32 caratteri"
    },
    {
        "nome.bad-edge",
        "deve cominciare e finire con una lettera o una cifra"
    },
    {
        "nome.bad-char",
        "c'è dentro un carattere che non si può usare"
    },
    {
        "nome.bad-char.space",
        "c'è uno spazio"
    },
    {
        "nome.bad-char.accent",
        "c'è una lettera accentata o non inglese"
    },
    {
        "nome.bad-char.invisible",
        "c'è dentro un carattere invisibile"
    },
    {
        "nome.bad-char.quale",
        "\"%1$s\" non si può usare"
    },
    {
        "nome.reserved",
        "è un nome di dispositivo riservato su Windows, e il "
        "nome del filtro viene usato anche come cartella"
    },
    {
        "nome.duplicate",
        "un'altra posizione ha già questo nome, senza "
        "distinguere maiuscole e minuscole"
    },
    {
        "nome.rifiutato",
        "Nome del filtro rifiutato: %1$s"
    },
    {
        "nome.rifiutato.slot",
        "Posizione %1$s: \"%2$s\" rifiutato - %3$s."
    },
    {
        "nome.rifiutato.slot.prova",
        "Posizione %1$s: \"%2$s\" rifiutato - %3$s. Un nome che qui sarebbe "
        "accettato: \"%4$s\"."
    },
    {
        "nome.vuoto.dato",
        "Posizione %1$s lasciata vuota, quindi senza filtro: ora si chiama \"%2$s\"."
    },
    {
        "nome.ammessi",
        "Ammessi: lettere non accentate, cifre, _ - e . ; da 1 a 32 caratteri; il "
        "primo e l'ultimo devono essere una lettera o una cifra."
    },
};

const size_t ITALIAN_CATALOGUE_SIZE = sizeof ITALIAN_CATALOGUE / sizeof ITALIAN_CATALOGUE[0];

}  // namespace wheelly
