# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
# From a path found by search_door.py to the path the assembly guide declares
# (src/guide/paths/arm_door.json): the straight drop along the pivot axis in
# front, 1 mm a pose, then the search's poses as rotation vectors in degrees
# about the group's centre plus translations, absolute from home - the format
# check_assembly_paths reads.
#
#   python export_door.py path_door_largo.json arm_door.json [every]
import json
import os
import sys
import tempfile

import numpy as np
from scipy.spatial.transform import Rotation as Rot

D = os.environ.get("WHEELLY_PERCORSI", os.path.join(tempfile.gettempdir(), "wheelly_paths")) + os.sep
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(D + sys.argv[1]))
c = np.array(d["c"])
every = int(sys.argv[3]) if len(sys.argv) > 3 else 1
head = [[0.0, 0.0, 0.0, 0.0, 0.0, -float(k)] for k in range(1, int(d["drop"]) + 1)]
poses = []
for k, (R, t) in enumerate(d["cammino"]):
    if k == 0 or (k % every and k != len(d["cammino"]) - 1):
        continue                      # the first is the end of the drop
    rv = Rot.from_matrix(np.array(R)).as_rotvec(degrees=True)
    poses.append([round(float(x), 4) for x in list(rv) + list(t)])
json.dump({"c": [round(float(x), 4) for x in c], "origine": sys.argv[1],
           "pose": head + poses},
          open(os.path.join(HERE, "guide", "paths", sys.argv[2]), "w"), indent=0)
print("%d poses written to guide/paths/%s" % (len(head) + len(poses), sys.argv[2]))
