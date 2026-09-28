<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CERN-OHL-P-2.0 -->

# Assembly path search - diagnostic tools

Not checks and not in the build: tools used to find whether and how the arm
(and the motor, the clutch) can get into the one-piece box. Run from
`mechanics/wheelly-cad` with the venv python; they write to
`$TMPDIR/wheelly_paths/`, or `$WHEELLY_PERCORSI` when set (so that a branch checked out elsewhere keeps its own grids).

1. `grid.py` - voxel grid (0.5 mm) of the obstacles (box, motor at home,
   inserts, gaskets) and point cloud of the arm with its bearings, by
   horizontal slices (4 min). `grid_motor.py`, `grid_clutch.py` -
   the same for the motor and the clutch alone, to subtract or add them.
2. `search.py sopra|sotto [senza_motore]` - best-first search from the known
   last stretch (arm tilted 8 deg on the edge of the motor face) out through
   the top or the bottom. Obstacles eroded by one voxel (0.5 mm tolerance),
   moves of 1 mm and 3 deg (also about the shaft hole).
3. `search_group.py [taglio] [frizione]` - the same for the whole group
   arm+motor(+clutch), optionally with the stepped-in recess wall removed.
4. `verify.py <path_*.json>` - checks a found path with exact booleans
   every fifth pose.

What they found: motor first, the arm cannot get in; arm
alone, it can (paths through top and bottom, rubbing a few tenths when checked
exactly); the group arm+motor cannot, even with the recess wall removed - the
lock is the pivot column and the collar over the arm's pivot half. Hence a
hatch under the motor, the motor coming up from below after the arm.

## Through the electronics opening, screw already on

On the printed parts the arm goes in **through the electronics opening** in the
floor, with the pivot washer and screw already fitted - not through the hatch
under the motor; this is the route the guide uses. Two more tools for that route:

5. `grid_door.py` - the grid of what is in the box at that point of the guide
   (box, inserts, gaskets, GX12 with its nut, LED; no motor, no panel), the
   spring and its cup apart, and the cloud of arm + bearings + washer + screw
   (4 min).
6. `search_door.py largo media fitto` - from home dropped 9 mm along the pivot
   axis (the screw out of its insert), best-first out below the floor with the
   hatch closed; half a millimetre of air (`largo`), the mean height as
   heuristic (`media`), every point (`fitto`: with every other point the path
   rubbed 2.4 mm3 when checked exactly). `export_door.py` writes it to
   `src/guide/paths/arm_door.json`, which chapter 5 declares.

