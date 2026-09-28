#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Genera la guida di montaggio in docs/assembly/.

    ./.venv/bin/python src/assembly_guide.py

Va DOPO l'assieme, perche' e' da li' che prende le immagini: lanciato su un
assieme vecchio produce una guida che mostra la macchina di ieri, e non se ne
accorge nessuno - le immagini sembrano giuste comunque.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guide import write

if __name__ == "__main__":
    write.generate()
