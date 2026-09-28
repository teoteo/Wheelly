# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# The assembled group (arm+bearings+motor [+clutch]) out of the part, with the
# stepped-in wall of the recess above the tread slot removed: r 117..121, +-(Halfw_grip + 1) deg about the motor axis,
# z from 10.5 up. Exit = every point above the roof or outside r 131.
import sys, heapq, itertools, json
import os, tempfile
os.makedirs(os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")), exist_ok=True)
import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation as Rot
D = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
g = np.load(D + "grid.npz"); occ, lo, v, arm = g["occ"], g["lo"], float(g["v"]), g["punti"]
mot = np.load(D + "grid_motor.npz")["occ"]; clu = np.load(D + "grid_clutch.npz")["occ"]
N = np.array(occ.shape)
xs = lo[0] + (np.arange(N[0]) + 0.5)*v; ys = lo[1] + (np.arange(N[1]) + 0.5)*v; zs = lo[2] + (np.arange(N[2]) + 0.5)*v
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
with_clutch = "frizione" in sys.argv
cut = "taglio" in sys.argv
obst = occ & ~mot & ~clu
if cut:
    R_ = np.hypot(X, Y); A_ = np.degrees(np.arctan2(Y, X))
    obst &= ~((R_ > 117.0) & (R_ < 121.0) & (np.abs(A_) < 12.63) & (Z > 10.5))
occ_e = ndimage.binary_erosion(obst)
def cloud(m):
    return lo + (np.argwhere(m) + 0.5)*v
P = np.vstack([arm, cloud(mot)] + ([cloud(clu)] if with_clutch else []))
k = np.round((P - P.min(0))/v).astype(int); P = P[(k % 2 == 0).all(1)]
c = P.mean(0)
def hits(R, t, grid=occ_e):
    q = (P - c) @ R.T + c + t
    i = np.floor((q - lo)/v).astype(int); ok = (i >= 0).all(1) & (i < N).all(1)
    return int(grid[i[ok, 0], i[ok, 1], i[ok, 2]].sum()), q
def inside(q):
    return int(((q[:, 2] < 28.8) & (np.hypot(q[:, 0], q[:, 1]) < 131.0)).sum())
R0, t0 = np.eye(3), np.zeros(3)
print("group points %d, at home: collisions eroded %d, full %d" % (len(P), hits(R0, t0)[0], hits(R0, t0, obst)[0]))
cnt = itertools.count()
MOVES = [("t", a, s) for a in range(3) for s in (-1.0, 1.0)] + [("r", a, s) for a in range(3) for s in (-3.0, 3.0)]
def key(R, t):
    return tuple(np.round(t).astype(int)) + tuple(np.round(np.degrees(Rot.from_matrix(R).as_rotvec())/3.0).astype(int))
open_ = [(inside(hits(R0, t0)[1]), next(cnt), R0, t0)]
seen = {key(R0, t0): None}; pose = {key(R0, t0): (R0, t0)}
found, it = None, 0
while open_ and it < 150000:
    f, _, R, t = heapq.heappop(open_); it += 1; kk = key(R, t)
    for kind, a, s in MOVES:
        if kind == "t":
            t2 = t.copy(); t2[a] += s; R2 = R
        else:
            ax = np.zeros(3); ax[a] = 1.0
            R2 = Rot.from_rotvec(np.radians(s)*ax).as_matrix() @ R; t2 = t
        k2 = key(R2, t2)
        if k2 in seen: continue
        n, q = hits(R2, t2); seen[k2] = kk
        if n > 0: continue
        pose[k2] = (R2, t2); d = inside(q)
        if d == 0: found = k2; break
        heapq.heappush(open_, (d, next(cnt), R2, t2))
    if found: break
tag = ("frizione_" if with_clutch else "") + ("taglio" if cut else "com_e")
print("%s: %s after %d expansions" % (tag, "FOUND" if found else "not found", it))
if found:
    path = []; kk = found
    while kk is not None:
        R, t = pose[kk]; path.append((R.tolist(), t.tolist())); kk = seen[kk]
    path.reverse()
    json.dump({"c": c.tolist(), "cammino": path, "gruppo": "frizione" if with_clutch else "braccio+motore"}, open(D + "path_group_%s.json" % tag, "w"))
    print("path of %d poses" % len(path))
