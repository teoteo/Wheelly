# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The GLOBAL bill of materials: BOM.md at the root of the repository, in
English, everything needed to build a Wheelly - the printed parts, what is
bought for the mechanics and what is bought for the electronics.

One global BOM, because otherwise in the assembly guide the electronics
seems to come from nowhere. Nothing here is
written by hand: the printed parts and their masses come from the solids
(bom_mechanics), the bought mechanical parts from the assembly with the same
sentence the guide uses (bom_mechanics.describe), the electronics from
bom_electronics - the one list the guide reads too.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bom_mechanics
import bom_electronics
from guide import palette

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BOM = os.path.join(ROOT, "BOM.md")


def write():
    r = ["<!--",
         "SPDX-FileCopyrightText: 2026 Matteo Beretta",
         "SPDX-License-Identifier: CC-BY-4.0",
         "-->",
         "",
         "# Wheelly - bill of materials",
         "",
         "**Generated** by `mechanics/wheelly-cad/src/bom_global.py` at every build:",
         "do not edit it by hand. Masses come from the solids, quantities from the",
         "assembly, screw lengths from what the model needs under the head, and the",
         "electronics from `src/bom_electronics.py`. The reasons behind the",
         "electronic parts are in [`pcb/BOM.md`](pcb/BOM.md) and",
         "[`hardware.md`](hardware.md); the assembly guide is in",
         "[`docs/assembly/`](docs/assembly/README.md).",
         "",
         "Dimensions marked **M** were measured with a caliper on a real part.",
         "",
         "## 1. Printed parts",
         "",
         "| Qty | Part | Material | Mass | How it prints |",
         "|---:|---|---|---:|---|"]
    tot = {}
    for name, mat, dens, q, _orientation in bom_mechanics.PRINTED:
        m = bom_mechanics.mass(name, dens)
        if m is not None:
            tot[mat] = tot.get(mat, 0.0) + m*q
        r.append("| %d | %s | %s | %s | %s |" % (q, palette.label(name), mat,
                                                 "%.1f g" % (m*q) if m else "**file missing**",
                                                 palette.orientation(name) or ""))
    r += ["", "In all: " + ", ".join("**%.0f g** of %s" % (v, k) for k, v in sorted(tot.items())) + ".",
          "",
          "## 2. Bought: mechanics",
          "",
          "| Qty | Part | What exactly |",
          "|---:|---|---|"]
    rows = bom_mechanics.purchased_rows()
    for name, g in sorted(rows.items()):
        r.append("| %d | %s | %s |" % (g["n"], palette.item_label(name),
                                       bom_mechanics.describe(name, g["entry"], "en")))
    r += ["",
          "## 3. Bought: electronics",
          ""]
    for where, title in (("board", "On the board"), ("off the board", "Off the board"),
                         ("cables", "Cables")):
        r += ["### " + title, "", "| Qty | Ref | Part | What exactly |", "|---:|---|---|---|"]
        for ref, q, part, spec, w, _b in bom_electronics.ITEMS:
            if w == where:
                r.append("| %d | %s | %s | %s |" % (q, ref, part, spec))
        r.append("")
    with open(BOM, "w", encoding="utf-8") as f:
        f.write("\n".join(r))
    print("wrote the global BOM.md: %d printed, %d mechanics entries, %d electronics"
          % (len(bom_mechanics.PRINTED), len(rows), len(bom_electronics.ITEMS)))


if __name__ == "__main__":
    write()
