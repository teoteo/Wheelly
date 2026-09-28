# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# From a path found by search.py to a path the assembly guide can declare
# (src/guide/paths/*.json): the poses as rotation vectors in degrees about
# the arm's centre, plus translations, absolute from home. The search starts
# from the arm tilted 8 deg on the edge of the motor face; the tilt is put
# back in front as poses from home, so the declared path starts at home.
#
#   python export.py path_*.json arm.json [every]
# (arm.json - the way in through the hatch - is retired: the arm goes in
# through the electronics opening, see export_door.py)
#
# "every": keep one pose in so many (default 1). check_assembly_paths
# interpolates between declared poses, so thinning is only safe if the check
# still passes.
# The JSON keys ("cammino", "origine", "pose") stay in Italian: they are
# the format of the path files already written and of guide/paths/*.json,
# which check_assembly_paths reads.
import json, os, sys, tempfile
import numpy as np
from scipy.spatial.transform import Rotation as Rot
D = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(D + sys.argv[1]))
c = np.array(d["c"])
every = int(sys.argv[3]) if len(sys.argv) > 3 else 1
poses = []
for k, (R, t) in enumerate(d["cammino"]):
    if k % every and k != len(d["cammino"]) - 1:
        continue
    rv = Rot.from_matrix(np.array(R)).as_rotvec(degrees=True)
    poses.append([round(float(x), 4) for x in list(rv) + list(t)])
# the hinge from home to the search's first pose: the same rotation about the
# edge of the motor face, in 1 deg steps, written about the centre c
A0 = np.array([0.0, 17.6, -6.0])
head = []
for a in range(1, 8):
    Ra = Rot.from_rotvec(np.radians(-a)*np.array([1.0, 0, 0]))
    ta = Ra.as_matrix() @ (c - A0) + A0 - c
    head.append([round(float(x), 4) for x in list(Ra.as_rotvec(degrees=True)) + list(ta)])
json.dump({"c": [round(float(x), 4) for x in c], "origine": sys.argv[1],
           "pose": head + poses}, open(os.path.join(HERE, "guide", "paths", sys.argv[2]), "w"), indent=0)
print("%d poses written to guide/paths/%s" % (len(head) + len(poses), sys.argv[2]))
