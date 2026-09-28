# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

import ezdxf
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out") + os.sep
os.makedirs(OUT, exist_ok=True)
from parameters import D
from dimension_signature import Msp

doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.MM
for n,c in (("PROFILO",7),("DISCO",5),("COSTRUZIONE",8),("QUOTE",1)):
    doc.layers.add(n, color=c)
ds = doc.dimstyles.get("EZDXF")
ds.dxf.dimdsep = ord("."); ds.dxf.dimdec = 2; ds.dxf.dimzin = 8
# The modelspace SIGNS the entities with the dimensions read to build them:
# without that, the editor has to find this drawing again by measuring, and on
# a dimensioned drawing - made of repeated numbers - it errs more than anywhere.
m = Msp(doc.modelspace(), doc)
OV = {"dimtxt":2.2,"dimasz":1.8,"dimexe":1.2,"dimexo":0.8,"dimgap":0.7,"dimdec":2,"dimclrt":1,"dimdsep":46,"dimzin":8}

def fmt(v):
    return ("%.2f" % v).rstrip("0").rstrip(".").replace(".", ",")
def dimV(base_x, y1, y2, x_ref, off=0.0):
    m.add_linear_dim(base=(base_x,(y1+y2)/2), p1=(x_ref,y1), p2=(x_ref,y2),
                     angle=90, dimstyle="EZDXF", override=OV, text=fmt(abs(y2-y1)),
                     dxfattribs={"layer":"QUOTE"}).render()
def dimH(base_y, x1, x2, y_ref):
    m.add_linear_dim(base=((x1+x2)/2, base_y), p1=(x1,y_ref), p2=(x2,y_ref),
                     angle=0, dimstyle="EZDXF", override=OV, text=fmt(abs(x2-x1)),
                     dxfattribs={"layer":"QUOTE"}).render()

Rc=D["D_body"]/2; Rd=D["R_disc"]; Hc=D["H_body"]
a0=D["Th_wall_front"]; a1=a0+D["H_opening"]; Rw=Rc-D["Th_wall_radial"]
pm=D["Z_plane_mid_disc"]; sd=D["Th_disc"]; sc=D["Dp_slot_front"]
X0=60.0; DX=120.0

def disc(dx):
    m.add_lwpolyline([(X0+dx,pm-sd/2),(Rd+dx,pm-sd/2),(Rd+dx,pm+sd/2),(X0+dx,pm+sd/2)],
                     close=True, dxfattribs={"layer":"DISCO"})
    m.add_line((X0+dx,pm),(Rc+dx+6,pm), dxfattribs={"layer":"COSTRUZIONE"})

# --- A: section in the plane of the window ---
m.add_lwpolyline([(X0,0),(Rc-sc,0),(Rc-sc,a0),(X0,a0)], close=True, dxfattribs={"layer":"PROFILO"})
m.add_lwpolyline([(X0,a1),(Rc,a1),(Rc,Hc),(X0,Hc)], close=True, dxfattribs={"layer":"PROFILO"})
m.add_line((Rc,0),(Rc,a0), dxfattribs={"layer":"COSTRUZIONE"})
disc(0)
dimV(52, 0, a0, X0+2); dimV(52, a0, a1, X0+2); dimV(52, a1, Hc, X0+2)
dimV(43, 0, Hc, X0+2)
dimH(-7, Rc-sc, Rc, a0)
dimH(-14, Rd, Rc, pm)
m.add_text("A - sezione nel piano della finestra", height=2.2,
           dxfattribs={"layer":"COSTRUZIONE"}).set_placement((X0, Hc+12))
m.add_text("scanalatura frontale, tutta la corda", height=1.6,
           dxfattribs={"layer":"COSTRUZIONE"}).set_placement((Rc-14, -20))

# --- B: section beside the window ---
m.add_lwpolyline([(X0+DX,0),(Rc+DX,0),(Rc+DX,Hc),(X0+DX,Hc),(X0+DX,a1),(Rw+DX,a1),
                  (Rw+DX,a0),(X0+DX,a0)], close=True, dxfattribs={"layer":"PROFILO"})
disc(DX)
dimH(-7, Rw+DX, Rc+DX, a0+3)
dimV(Rc+DX+10, pm-sd/2, pm+sd/2, Rd+DX)
dimV(Rc+DX+20, a0, pm-sd/2, Rw+DX)
dimV(Rc+DX+30, pm+sd/2, a1, Rw+DX)
dimV(52+DX, 0, pm, X0+DX+2)
m.add_text("B - sezione di fianco alla finestra (parete piena)", height=2.2,
           dxfattribs={"layer":"COSTRUZIONE"}).set_placement((X0+DX, Hc+12))

for dx in (0, DX):
    m.add_line((X0+dx-2,0),(X0+dx-2,Hc), dxfattribs={"layer":"COSTRUZIONE"})
    m.add_text("verso centro disco", height=1.4, rotation=90,
               dxfattribs={"layer":"COSTRUZIONE"}).set_placement((X0+dx-4, 2))
m.add_text("quote in mm - Y = quota assiale, 0 = faccia lato camera, 23 = faccia lato telescopio",
           height=1.8, dxfattribs={"layer":"COSTRUZIONE"}).set_placement((X0, -26))
os.makedirs(OUT + "drawings", exist_ok=True)
doc.saveas(OUT + "drawings/body_dimensioned.dxf")
print("ok")
