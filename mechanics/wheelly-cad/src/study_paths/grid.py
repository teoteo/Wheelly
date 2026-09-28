# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# Voxel grid of the obstacles (box with the motor already home, inserts,
# gaskets) and point cloud of the arm with its bearings, both by horizontal
# slices rasterised like check_thin. Saved as .npz for the search.
import sys, os, math
import os, tempfile
os.makedirs(os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")), exist_ok=True)
# the project this file sits in, not a fixed path: the same tools run on a branch checked out elsewhere
_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_HERE, "src"))
os.chdir(_HERE)
import numpy as np
import cadquery as cq
from multiprocessing import Pool
from matplotlib.path import Path
from guide import scene, write

V = 0.5
LO = np.array([30.0, -60.0, -45.0]); HI = np.array([150.0, 100.0, 70.0])
N = np.ceil((HI - LO)/V).astype(int)
OBST = ["box_collar", "motor_14HS10-0404S", "front_gasket", "rear_gasket", "insert_M3_pivot_1",
       "insert_M3_panel_1", "insert_M3_panel_2", "insert_M3_panel_3", "insert_M3_cover_1",
       "insert_M4_preload_1",
       "insert_M3_hatch_1", "insert_M3_hatch_2"]
MOB = ["arm", "bearing_F695ZZ_1", "bearing_F695ZZ_2"]
# "molla": the spring and its cup are obstacles too. Strategy C puts them in
# BEFORE the arm (with the arm in there is no room for them), so the arm's
# way in has to miss them. Written to grid_spring.npz.
SPRING = "molla" in sys.argv[1:]
if SPRING:
    OBST = OBST + ["preload_spring", "spring_cup"]
_K = None

def bodies():
    global _K
    if _K is None:
        _K = scene.load(write.ASSEMBLY)
    return _K

def layer(arg):
    names, k, lo, n = arg
    z = lo[2] + (k + 0.5)*V
    xs = lo[0] + (np.arange(n[0]) + 0.5)*V; ys = lo[1] + (np.arange(n[1]) + 0.5)*V
    X, Y = np.meshgrid(xs, ys, indexing="ij"); pts = np.column_stack([X.ravel(), Y.ravel()])
    m = np.zeros(n[0]*n[1], bool)
    K = bodies()
    for name in names:
        s = K[name]; b = s.BoundingBox()
        if z < b.zmin or z > b.zmax:
            continue
        slab = cq.Solid.makeBox(500, 500, 0.02, cq.Vector(-250, -250, z - 0.01))
        try:
            x = s.intersect(slab)
        except Exception:
            continue
        for f in x.Faces():
            if f.normalAt().z < 0.99:
                continue
            def poly(w):
                p = [w.positionAt(t/240.0) for t in range(241)]
                return Path([(q.x, q.y) for q in p])
            d = poly(f.outerWire()).contains_points(pts)
            for w in f.innerWires():
                d &= ~poly(w).contains_points(pts)
            m |= d
    return k, m.reshape(n[0], n[1])

if __name__ == "__main__":
    with Pool(8) as p:
        occ = np.zeros(N, bool)
        for k, m in p.imap_unordered(layer, [(OBST, k, LO, N) for k in range(N[2])]):
            occ[:, :, k] = m
        # the arm: its own bounding box, same voxel size
        K = bodies()
        bb = None
        for n in MOB:
            b = K[n].BoundingBox()
            bb = b if bb is None else bb.add(b)
        alo = np.array([bb.xmin - 1, bb.ymin - 1, bb.zmin - 1]); an = np.ceil((np.array([bb.xmax + 1, bb.ymax + 1, bb.zmax + 1]) - alo)/V).astype(int)
        arm = np.zeros(an, bool)
        for k, m in p.imap_unordered(layer, [(MOB, k, alo, an) for k in range(an[2])]):
            arm[:, :, k] = m
    idx = np.argwhere(arm)
    punti = alo + (idx + 0.5)*V
    np.savez_compressed(os.path.join(os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")), "grid_spring.npz" if SPRING else "grid.npz"),
                        occ=occ, lo=LO, v=V, punti=punti)
    print("obstacle voxels %d of %d, arm points %d" % (occ.sum(), occ.size, len(punti)))
