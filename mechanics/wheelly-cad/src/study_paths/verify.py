# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
import sys, json, math
import os, tempfile
os.makedirs(os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")), exist_ok=True)
sys.path.insert(0, "src")
import numpy as np, cadquery as cq
from multiprocessing import Pool
from guide import scene, write
D = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
OBST = ["box_collar", "front_gasket", "rear_gasket", "insert_M3_pivot_1", "insert_M3_panel_1",
       "insert_M3_panel_2", "insert_M3_panel_3", "insert_M3_cover_1", "insert_M4_preload_1",
       "insert_M3_hatch_1", "insert_M3_hatch_2"]
MOB = ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2"]
K = None
def move(sol, R, t, c):
    # p' = R (p - c) + c + t, with R taken back to a true rotation (axis + angle)
    from scipy.spatial.transform import Rotation as Rot
    rv = Rot.from_matrix(np.array(R)).as_rotvec()
    a = float(np.linalg.norm(rv))
    s = sol
    if a > 1e-9:
        ax = rv/a
        s = s.rotate(cq.Vector(*c), cq.Vector(*(np.array(c) + ax)), math.degrees(a))
    return s.translate(cq.Vector(*t))
def work(arg):
    global K
    if K is None:
        K = scene.load(write.ASSEMBLY)
    i, R, t, c = arg
    worst, who = 0.0, ""
    for m in MOB:
        s = move(K[m], R, t, c)
        for o in OBST:
            v = s.intersect(K[o]).Volume() - K[m].intersect(K[o]).Volume()
            if v > worst:
                worst, who = v, "%s/%s" % (m, o)
    return i, worst, who
if __name__ == "__main__":
    name = sys.argv[1]
    d = json.load(open(D + name)); c = d["c"]; path = d["cammino"]
    idx = list(range(0, len(path), 5)) + [len(path) - 1]
    with Pool(8) as p:
        res = sorted(p.map(work, [(i, path[i][0], path[i][1], c) for i in idx]))
    worst = max(res, key=lambda r: r[1])
    print("%s: %d poses checked of %d; worst overlap %.2f mm3 at pose %d (%s); poses over 0.5 mm3: %d"
          % (name, len(res), len(path), worst[1], worst[0], worst[2], sum(1 for r in res if r[1] > 0.5)))
