# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# Voxel grid for the arm's way in THROUGH THE ELECTRONICS OPENING, as it
# went on the real parts: the arm goes
# in with its bearings, the pivot washer and the pivot screw ALREADY FITTED,
# so the moving cloud is arm + bearings + washer + screw. The obstacles are
# what is in the box at that point of the guide (chapters 2-4): the box, its
# inserts, the gaskets, the GX12 connector with its nut, the LED. No motor
# (it comes up later, chapter 7), no panel (the opening is open), no hatch
# cover. The spring and its cup are rasterised APART ("spring"), because
# they yield: search_door.py moves them back by Travel_preload.
#
#   python src/study_paths/grid_door.py      (about 4 minutes, 8 processes)
#
# Written to grid_door.npz in the same folder as the other grids.
import os
import sys
import tempfile

import numpy as np
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grid                      # its layer() rasteriser and its box LO..HI

OBST = ["box_collar", "front_gasket", "rear_gasket", "insert_M3_pivot_1",
        "insert_M3_panel_1", "insert_M3_panel_2", "insert_M3_panel_3",
        "insert_M3_cover_1", "insert_M3_cover_2", "insert_M4_preload_1",
        "insert_M3_hatch_1", "insert_M3_hatch_2",
        "electronics_gx12", "electronics_gx12_nut", "electronics_led"]
SPRING = ["preload_spring", "spring_cup"]
MOB = ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2", "pivot_washer", "screw_M3_pivot_1"]

if __name__ == "__main__":
    LO, N, V = grid.LO, grid.N, grid.V
    with Pool(8) as p:
        occ = np.zeros(N, bool)
        for k, m in p.imap_unordered(grid.layer, [(OBST, k, LO, N) for k in range(N[2])]):
            occ[:, :, k] = m
        spring = np.zeros(N, bool)
        for k, m in p.imap_unordered(grid.layer, [(SPRING, k, LO, N) for k in range(N[2])]):
            spring[:, :, k] = m
        K = grid.bodies()
        bb = None
        for n in MOB:
            b = K[n].BoundingBox()
            bb = b if bb is None else bb.add(b)
        alo = np.array([bb.xmin - 1, bb.ymin - 1, bb.zmin - 1])
        an = np.ceil((np.array([bb.xmax + 1, bb.ymax + 1, bb.zmax + 1]) - alo)/V).astype(int)
        cloud = np.zeros(an, bool)
        for k, m in p.imap_unordered(grid.layer, [(MOB, k, alo, an) for k in range(an[2])]):
            cloud[:, :, k] = m
    points = alo + (np.argwhere(cloud) + 0.5)*V
    out = os.path.join(os.environ.get("WHEELLY_PERCORSI",
                                      os.path.join(tempfile.gettempdir(), "wheelly_paths")),
                       "grid_door.npz")
    np.savez_compressed(out, occ=occ, spring=spring, lo=LO, v=V, punti=points)
    print("obstacle voxels %d, spring voxels %d, group points %d -> %s"
          % (occ.sum(), spring.sum(), len(points), out))
