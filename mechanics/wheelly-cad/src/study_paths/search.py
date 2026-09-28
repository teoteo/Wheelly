# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# Best-first search of a way OUT for the arm (with its bearings), from the
# known last stretch (tilted 8 deg pivot-end-down on the edge of the motor
# face) to fully above the roof (out through the motor cap) or fully below the
# floor (out through the electronics door, panel not mounted yet).
# Obstacles eroded by one voxel (0.5 mm of tolerance); the path is re-checked
# exactly afterwards.
# The command-line keywords (sopra|sotto, largo, fitto, molla, molla_cede,
# senza_motore, solo_botola, perno=, espansioni=) stay in Italian: they name
# the path files already produced, and the declared paths record them in
# their "origine".
import sys, heapq, math, json
import os, tempfile
os.makedirs(os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")), exist_ok=True)
import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation as Rot
D = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
g = np.load(D + ("grid_spring.npz" if "molla" in sys.argv[2:] else "grid.npz"))
occ, lo, v, points = g["occ"], g["lo"], float(g["v"]), g["punti"]
if "senza_motore" in sys.argv[2:]:
    occ = occ & ~np.load(D + "grid_motor.npz")["occ"]
# "solo_botola": the way out through the electronics door is closed, so the
# search has to find the hatch under the motor. The first dense path went out
# through the door and grazed the corner of the panel opening (22 mm3), and
# widening the panel opening would mean reprinting the panel, while the
# hatch cover was still to be printed. Everything below the top
# of the floor with y > 25 becomes obstacle; the hatch spans y -21..21.
if "solo_botola" in sys.argv[2:]:
    _i = np.indices(occ.shape)
    _y = lo[1] + (_i[1] + 0.5)*v; _z = lo[2] + (_i[2] + 0.5)*v
    occ = occ | ((_y > 25.0) & (_z < -28.9))
    del _i, _y, _z
# THE CLEARANCE MODE. The first searches ran on obstacles ERODED by a voxel,
# i.e. they accepted half a millimetre of overlap, and the paths they found
# rubbed 51..98 mm3 when checked exactly. "largo" as last argument runs on
# obstacles DILATED by a voxel instead: a path found that way has half a
# millimetre of air by construction.
WIDE = "largo" in sys.argv[2:]
occ_e = ndimage.binary_dilation(occ) if WIDE else ndimage.binary_erosion(occ)
N = np.array(occ.shape)
# "molla_cede": the spring and its cup are there (strategy C puts them in
# before the arm) but they YIELD a little: the cup sits at the back of its
# travel (Travel_preload - the preload grub is not in yet) and the spring
# compresses where the arm pushes it home. So they are kept apart from the
# dilated obstacles: not dilated, moved back along the spring axis, and the
# arm may never touch them MORE than it does where the search starts - it can
# push them as it comes home, it cannot go through them on the way.
SPRING_YIELDS = "molla_cede" in sys.argv[2:]
if SPRING_YIELDS:
    _base = np.load(D + "grid.npz")["occ"]
    _spring = np.load(D + "grid_spring.npz")["occ"] & ~_base
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from parameters import D as _Dm, spring_axis as _am
    _, _, _nx, _ny, _ = _am()
    _sh = (int(round(_nx*_Dm["Travel_preload"]/v)), int(round(_ny*_Dm["Travel_preload"]/v)))
    SPRING = np.roll(np.roll(_spring, _sh[0], axis=0), _sh[1], axis=1)
    print("spring and cup: %d voxels, moved back %s voxels" % (SPRING.sum(), _sh))
# every other point: ~1 mm spacing for the search
k = np.round((points - points.min(0))/v).astype(int)
# "fitto": every point, 0.5 mm apart. Every other point let thin parts of the
# arm slip between two samples: the "largo" paths still rubbed 2..7 mm3 when
# checked exactly
P = points if "fitto" in sys.argv[2:] else points[(k % 2 == 0).all(1)]
c = P.mean(0)
EXIT = sys.argv[1] if len(sys.argv) > 1 else "sopra"
Z_ROOF, Z_FLOOR = 28.5, -31.5

def hits(R, t, grid=occ_e, pts=P):
    q = (pts - c) @ R.T + c + t
    i = np.floor((q - lo)/v).astype(int)
    ok = (i >= 0).all(1) & (i < N).all(1)
    return int(grid[i[ok, 0], i[ok, 1], i[ok, 2]].sum()), q

# start: hinged 8 deg about the motor face edge (y 17.6, z -6), axis x
A0 = np.array([0.0, 17.6, -6.0])
R0 = Rot.from_rotvec(np.radians(-8.0)*np.array([1.0, 0, 0])).as_matrix()
t0 = R0 @ (c - A0) + A0 - c
for ang in (0, 2, 4, 6, 8):
    Ra = Rot.from_rotvec(np.radians(-ang)*np.array([1.0, 0, 0])).as_matrix()
    ta = Ra @ (c - A0) + A0 - c
    print("hinge %d deg: collisions eroded %d, full grid %d" % (ang, hits(Ra, ta)[0], hits(Ra, ta, occ)[0]))

print("sanity: arm moved 25 mm down collides %d, 25 mm up %d" % (hits(np.eye(3), np.array([0, 0, -25.0]))[0], hits(np.eye(3), np.array([0, 0, 25.0]))[0]))
import itertools
_cont = itertools.count()

def h(q):
    return (Z_ROOF + 1.0 - q[:, 2].min()) if EXIT == "sopra" else (q[:, 2].max() - (Z_FLOOR - 1.0))

MOVES = ([("t", a, s) for a in range(3) for s in (-1.0, 1.0)] + [("r", a, s) for a in range(3) for s in (-3.0, 3.0)]
         + [("f", a, s) for a in range(3) for s in (-3.0, 3.0)])
# the centre of the arm's hole over the motor shaft, at mid plate: rotations
# about it keep the hole on the shaft
HOLE = np.array([97.5, 0.0, -2.0])
def key(R, t):
    return tuple(np.round(t).astype(int)) + tuple(np.round(np.degrees(Rot.from_matrix(R).as_rotvec())/3.0).astype(int))

# "perno=<deg>": start from home turned about the pivot axis by that many
# degrees (negative: towards the disc, away from the spring). With the spring
# already in its seat (strategy C) the arm cannot come home by the hinge on
# the motor face: it has to swing home about the pivot, pressing the spring,
# as it would in the hand.
_pp = [a for a in sys.argv[2:] if a.startswith("perno=")]
if _pp:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from parameters import D as _Dp
    _P = np.array([_Dp["R_disc"], _Dp["Off_pivot"], 0.0])
    R0 = Rot.from_rotvec(np.radians(float(_pp[0][6:]))*np.array([0, 0, 1.0])).as_matrix()
    t0 = R0 @ (c - _P) + _P - c
    print("start turned %s deg about the pivot: collisions %d (dilated grid)" % (_pp[0][6:], hits(R0, t0)[0]))
n0, q0 = hits(R0, t0)
M0 = hits(R0, t0, SPRING)[0] if SPRING_YIELDS else 0
if SPRING_YIELDS:
    print("at the start the arm touches the spring for %d voxels: never more than that" % M0)
open_ = [(h(q0), next(_cont), R0, t0, None)]
seen = {key(R0, t0): None}
parent = {}
it = 0
found = None
# "espansioni=N": how far the search may go before giving up (default 250000)
_lim = [int(a[11:]) for a in sys.argv[2:] if a.startswith("espansioni=")]
while open_ and it < (_lim[0] if _lim else 250000):
    f, _, R, t, _ = heapq.heappop(open_); it += 1
    kk = key(R, t)
    for kind, a, s in MOVES:
        if kind == "t":
            t2 = t.copy(); t2[a] += s; R2 = R
        else:
            ax = np.zeros(3); ax[a] = 1.0
            Rm = Rot.from_rotvec(np.radians(s)*ax).as_matrix()
            R2 = Rm @ R
            if kind == "r":
                t2 = t                   # rotate about the current centroid c + t
            else:
                # about the current place of the hole: p' = Rm (p - F) + F, F the hole now
                F = R @ (HOLE - c) + c + t
                t2 = Rm @ (c + t - F) + F - c
        k2 = key(R2, t2)
        if k2 in seen:
            continue
        n, q = hits(R2, t2)
        seen[k2] = kk
        if n > 0:
            continue
        if SPRING_YIELDS and hits(R2, t2, SPRING)[0] > M0:
            continue
        parent[k2] = (R2, t2)
        hh = h(q)
        if hh <= 0:
            found = k2; break
        heapq.heappush(open_, (hh, next(_cont), R2, t2, None))
    if found: break
print("exit %s: %s after %d expansions" % (EXIT, "FOUND" if found else "not found", it))
if found:
    # walk back to the start
    path = []
    kk = found
    while kk is not None:
        if kk in parent:
            R, t = parent[kk]; path.append((R.tolist(), t.tolist()))
        kk = seen[kk]
    path.append((R0.tolist(), t0.tolist()))
    path.reverse()
    json.dump({"c": c.tolist(), "cammino": path}, open(D + "path_%s%s.json" % (EXIT, "".join("_" + a for a in sys.argv[2:] if not a.startswith("espansioni="))), "w"))
    print("path of %d poses saved" % len(path))
