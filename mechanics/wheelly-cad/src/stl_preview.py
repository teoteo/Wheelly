# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Coarse STLs, to look at the parts without opening a CAD.

They are not for printing: the tessellation is loose (three tenths of chord
deviation) and the files stay small, to open on the fly with the Mac's
Preview or any viewer. To print, start from the STEPs.

One per part, and an assembly.stl with all the parts in place: the STEPs are
already in assembly coordinates, so putting them together is enough.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
STL = OUT + "stl" + os.sep
os.makedirs(STL, exist_ok=True)
import cadquery as cq
from parameters import out_subdir

TOLERANCE, ANGLE = 0.3, 0.5          # mm of chord deviation, radians

ASSEMBLY = ("filter_wheel_body", "filter_disc", "collar", "arm",
           "clutch_hub", "clutch_tyre", "box",
           "sensor_bracket", "sensor_cover",
           "board_panel", "spring_cup", "pivot_washer", "grip_cover", "hatch_cover",
           "front_gasket", "rear_gasket", "sensor_cable")
TOOLS = ("magnet_cap", "gap_gauges")   # they live in out/tools/
# The part that is actually printed: the assembly holds its two REGIONS
# (collar and box, which stay separate bodies because that is how the
# geometry is written), but on the bed it goes whole. Without this line there
# would be no preview of the part that is printed.
OTHERS = ("magnet_spacer", "box_collar")          # real parts, outside the assembly
# the envelopes of the electronics: they are not printed, they live in
# out/electronics/, and they go in the assembly because they are what the
# compartment must allow for
ELECTRONICS = ("perfboard", "pin_sockets", "xiao", "driver", "components", "gx12", "gx12_nut", "led")


def _step(name):
    """Where the STEP of this part lives. The subfolder is decided by one
    function only, in parameters.py: here there was a second copy of the same
    rule, and two copies drift apart at the first part that moves."""
    return OUT + out_subdir(name) + name + ".step"

for f in os.listdir(STL):              # no leftovers of parts that no longer exist
    if f.endswith(".stl"):
        os.remove(STL + f)

solids = []
for name in ASSEMBLY + TOOLS + OTHERS + ELECTRONICS:
    shape = cq.importers.importStep(_step(name)).val()
    prefix = "electronics_" if name in ELECTRONICS else ""
    cq.exporters.export(shape, STL + prefix + name + ".stl",
                        tolerance=TOLERANCE, angularTolerance=ANGLE)
    if name in ASSEMBLY or name in ELECTRONICS:
        solids.append(shape)
cq.exporters.export(cq.Compound.makeCompound(solids), STL + "assembly.stl",
                    tolerance=TOLERANCE, angularTolerance=ANGLE)

kb = sum(os.path.getsize(STL + f) for f in os.listdir(STL)) / 1024
print("%d STL in out/stl, %.0f kB in all" % (len(os.listdir(STL)), kb))
