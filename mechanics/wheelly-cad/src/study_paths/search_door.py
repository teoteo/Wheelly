# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# Best-first search of the arm's way OUT through the ELECTRONICS OPENING, with
# the pivot washer and screw already on it, as on the real assembly. Reads
# grid_door.npz (grid_door.py).
#
# The start is not the arm at home: at home the screw is in the pivot insert.
# The first leg is straight down the pivot axis by DROP mm - the screw comes
# out of the insert along its own bore, the bushing off the pivot's spot face
# - and it is written in front of the found path by export_door.py. In the
# hand the screw is simply held back in the bushing; drawn protruding along
# its axis it sweeps only its own bore, so the leg is the same move.
#
# The way out through the hatch under the motor is CLOSED here (everything
# under the top of the floor with y < 28): the question is the door.
#
#   python search_door.py [largo] [fitto] [media] [drop=<mm>] [espansioni=N]
#
#   largo   obstacles dilated by a voxel: half a millimetre of air by
#           construction (the default is the exact grid)
import heapq
import itertools
import json
import os
import sys
import tempfile

import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from parameters import D as _D, spring_axis as _axis

DIR = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
g = np.load(DIR + "grid_door.npz")
occ, lo, v, points = g["occ"], g["lo"], float(g["v"]), g["punti"]
N = np.array(occ.shape)
args = sys.argv[1:]
WIDE = "largo" in args
_i = np.indices(occ.shape)
_y = lo[1] + (_i[1] + 0.5)*v
_z = lo[2] + (_i[2] + 0.5)*v
occ = occ | ((_y < 28.0) & (_z < -28.9))            # the hatch is not the way
del _i, _y, _z
occ_s = ndimage.binary_dilation(occ) if WIDE else occ
# the spring and its cup, back by Travel_preload (the preload grub is not in)
_, _, nx, ny, _ = _axis()
sh = (int(round(nx*_D["Travel_preload"]/v)), int(round(ny*_D["Travel_preload"]/v)))
SPRING = np.roll(np.roll(g["spring"], sh[0], axis=0), sh[1], axis=1)
# 9 mm: the screw is out of the insert and the bushing off the spot face;
# at 10 the arm meets the bosses of the panel inserts under it
DROP = float(([a[5:] for a in args if a.startswith("drop=")] or ["9"])[0])
LIMIT = int(([a[11:] for a in args if a.startswith("espansioni=")] or ["300000"])[0])
Z_FLOOR = -31.5

# every other point, ~1 mm apart, unless "fitto": the full cloud made one
# expansion cost half a second
_k = np.round((points - points.min(0))/v).astype(int)
P = points if "fitto" in args else points[(_k % 2 == 0).all(1)]
c = points.mean(0)


def hits(R, t, grid=occ_s):
    q = (P - c) @ R.T + c + t
    i = np.floor((q - lo)/v).astype(int)
    ok = (i >= 0).all(1) & (i < N).all(1)
    return int(grid[i[ok, 0], i[ok, 1], i[ok, 2]].sum()), q


R0 = np.eye(3)
for d in range(0, int(DROP) + 1):
    t = np.array([0, 0, -float(d)])
    print("drop %2d mm: obstacle %d, spring %d" % (d, hits(R0, t)[0], hits(R0, t, SPRING)[0]))
t0 = np.array([0, 0, -DROP])
n0 = hits(R0, t0)[0]
M0 = hits(R0, t0, SPRING)[0]
print("start (dropped %.0f mm): obstacle %d, spring %d (never more than that)" % (DROP, n0, M0))


# "media": the heuristic is the MEAN height of the cloud above the exit, not
# the highest point: with the highest point the search sat at the floor and
# never tried to put the pivot end through first
MEAN = "media" in args


def h(q):
    if MEAN:
        above = np.maximum(q[:, 2] - (Z_FLOOR - 1.0), 0.0)
        return float(above.mean()) if above.max() > 0 else 0.0
    return q[:, 2].max() - (Z_FLOOR - 1.0)


def key(R, t):
    return tuple(np.round(t).astype(int)) + tuple(
        np.round(np.degrees(Rot.from_matrix(R).as_rotvec())/3.0).astype(int))


MOVES = [("t", a, s) for a in range(3) for s in (-1.0, 1.0)] + \
        [("r", a, s) for a in range(3) for s in (-3.0, 3.0)]
cnt = itertools.count()
q0 = hits(R0, t0)[1]
open_ = [(h(q0), next(cnt), R0, t0)]
seen = {key(R0, t0): None}
pose = {key(R0, t0): (R0, t0)}
found, it = None, 0
best = (1e9, None)
while open_ and it < LIMIT:
    f, _, R, t = heapq.heappop(open_)
    it += 1
    if it % 5000 == 0:
        print("  %d expansions, best height left %.1f mm" % (it, best[0]), flush=True)
    kk = key(R, t)
    for kind, a, s in MOVES:
        if kind == "t":
            t2 = t.copy(); t2[a] += s; R2 = R
        else:
            ax = np.zeros(3); ax[a] = 1.0
            R2 = Rot.from_rotvec(np.radians(s)*ax).as_matrix() @ R; t2 = t
        k2 = key(R2, t2)
        if k2 in seen:
            continue
        n, q = hits(R2, t2)
        seen[k2] = kk
        if n > n0:
            continue
        if hits(R2, t2, SPRING)[0] > M0:
            continue
        pose[k2] = (R2, t2)
        hh = h(q)
        if hh < best[0]:
            best = (hh, k2)
        if hh <= 0:
            found = k2
            break
        heapq.heappush(open_, (hh, next(cnt), R2, t2))
    if found:
        break
print("door: %s after %d expansions; best height left %.1f mm at %s"
      % ("FOUND" if found else "not found", it, best[0], best[1]))
end = found or best[1]
path, kk = [], end
while kk is not None:
    R, t = pose[kk]
    path.append((R.tolist(), t.tolist()))
    kk = seen[kk]
path.reverse()
name = "path_door%s%s%s.json" % ("_largo" if WIDE else "", "_media" if MEAN else "",
                                 "" if found else "_partial")
json.dump({"c": c.tolist(), "drop": DROP, "cammino": path}, open(DIR + name, "w"))
print("path of %d poses saved to %s" % (len(path), name))
