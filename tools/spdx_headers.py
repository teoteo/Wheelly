#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CC-BY-4.0
"""Mette l'intestazione SPDX su ogni file sorgente, una volta sola.

The licence follows the folder: firmware/ MIT, driver/ LGPL-2.1-or-later
(except the protocol header, a copy of the firmware's, MIT), mechanics/
CERN-OHL-P-2.0, brand/ its own, the root CC-BY-4.0. Il titolare del copyright e'
un segnaposto volutamente vistoso: va sostituito prima di pubblicare.
"""
import pathlib
import sys

TITOLARE = "2026 Matteo Beretta"

AREE = [
    ("firmware/", "MIT"),
    # The protocol header in the driver is a byte-for-byte copy of the
    # firmware's (checked by firmware/test/test_driver_standalone.py), so it
    # keeps the firmware's licence. It must come BEFORE the driver/ rule.
    ("driver/indi-wheelly/wheelly_protocol.h", "MIT"),
    # LGPL like INDI itself, so the driver can go into INDI's tree unchanged
    # (it was MIT before).
    ("driver/", "LGPL-2.1-or-later"),
    ("mechanics/", "CERN-OHL-P-2.0"),
    # L'eccezione: il marchio non e' aperto. Senza questa riga i file del logo
    # prenderebbero la licenza della radice - CC-BY - e chiunque potrebbe usarli
    # per qualunque cosa, che e' esattamente il contrario di quello che serve.
    # Il nome, che e' cosa diversa dal copyright sui file, sta in TRADEMARK.md.
    ("brand/", "LicenseRef-Wheelly-Brand"),
]
RADICE = "CC-BY-4.0"

# come si commenta, per estensione
DIESIS = {".py", ".sh", ".txt", ".cmake"}
SLASH = {".cpp", ".h", ".ino", ".c", ".hpp"}
HTML = {".md"}


def licenza_di(rel: str) -> str:
    for prefisso, lic in AREE:
        if rel.startswith(prefisso):
            return lic
    return RADICE


def righe(lic: str, stile: str):
    a = f"SPDX-FileCopyrightText: {TITOLARE}"
    b = f"SPDX-License-Identifier: {lic}"
    if stile == "html":
        return [f"<!-- {a} -->", f"<!-- {b} -->", ""]
    pre = "# " if stile == "diesis" else "// "
    return [pre + a, pre + b, ""]


def stile_di(suf: str):
    if suf in HTML:
        return "html"
    if suf in SLASH:
        return "slash"
    if suf in DIESIS:
        return "diesis"
    return None


def inserisci(p: pathlib.Path, lic: str) -> str:
    testo = p.read_text(encoding="utf-8")
    if "SPDX-License-Identifier" in testo:
        return "gia' presente"
    stile = stile_di(p.suffix) or ("diesis" if p.name == "CMakeLists.txt" else None)
    if stile is None:
        return "estensione non gestita"

    linee = testo.split("\n")
    # lo shebang deve restare la prima riga, e la riga di coding entro le prime due
    i = 0
    if linee and linee[0].startswith("#!"):
        i = 1
    if stile == "diesis" and len(linee) > i and "coding" in linee[i] and linee[i].lstrip().startswith("#"):
        i += 1

    nuove = linee[:i] + righe(lic, stile) + linee[i:]
    p.write_text("\n".join(nuove), encoding="utf-8")
    return "aggiunto " + lic


def main():
    radice = pathlib.Path(".").resolve()
    esiti = {}
    for p in sorted(radice.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(radice))
        if rel.startswith((".git/", ".claude/", "LICENSES/")) or rel == "tools/spdx_headers.py":
            continue
        if p.suffix not in (DIESIS | SLASH | HTML) and p.name != "CMakeLists.txt":
            continue
        if p.suffix == ".txt" and p.name != "CMakeLists.txt":
            continue  # i .txt sono dati, non sorgenti
        esito = inserisci(p, licenza_di(rel))
        esiti.setdefault(esito, []).append(rel)

    for esito, files in sorted(esiti.items()):
        print(f"\n{esito}: {len(files)}")
        for f in files[:100]:
            print("   ", f)


if __name__ == "__main__":
    sys.exit(main())
