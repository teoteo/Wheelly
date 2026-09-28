# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The renders of the assembly guide, taken from the assembly the build makes.

Where the pictures come from, and why from there: `out/references/
full_assembly.step` is an assembly of SEPARATE BODIES, each with its name and
already in its assembled position - 64 bodies, printed parts, the maker's
motor, screws and inserts one by one. So the guide redraws nothing and cannot
tell of a machine different from the modelled one: it chooses which bodies to
show, colours them and frames them.

The render is off-screen VTK: parallel projection (it is a technical drawing,
not a photograph), edges marked in black so the shape reads in black and white
too, and the possibility of CUTTING the parts with a plane to show a fit that
cannot be seen from outside. The cut is `vtkClipClosedSurface` and not a plain
clipping plane: that one leaves the part hollow, and an empty shell in section
reads the wrong way round.
"""
import math
import os

import cadquery as cq
import vtk
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

# how fine the tessellation is: three hundredths of sag. It is not the
# tolerance of the preview STLs (three tenths): there the files must stay
# small, here the round things must be round even when enlarged.
SAG, ANGLE = 0.03, 0.2


def load(path):
    """The bodies of the assembly, by name. Reading it costs ten seconds or
    so: it is done once and kept, because the steps of the guide are dozens
    and they all look at the same assembly."""
    doc = TDocStd_Document(TCollection_ExtendedString("wheelly"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(True)
    reader.ReadFile(path)
    reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)

    bodies = {}
    for i in range(1, roots.Length() + 1):
        children = TDF_LabelSequence()
        tool.GetComponents_s(roots.Value(i), children)
        for j in range(1, children.Length() + 1):
            lab = children.Value(j)
            n = TDataStd_Name()
            if not lab.FindAttribute(TDataStd_Name.GetID_s(), n):
                continue
            bodies[n.Get().ToExtString()] = cq.Shape(tool.GetShape_s(lab))
    if not bodies:
        raise SystemExit("assembly with no named bodies: %s" % path)
    return bodies


def _mesh(shape):
    """From OCCT solid to VTK surface."""
    points, triangles = shape.tessellate(SAG, ANGLE)
    p = vtk.vtkPoints()
    p.SetNumberOfPoints(len(points))
    for i, v in enumerate(points):
        p.SetPoint(i, v.x, v.y, v.z)
    cells = vtk.vtkCellArray()
    for t in triangles:
        cells.InsertNextCell(3, t)
    pd = vtk.vtkPolyData()
    pd.SetPoints(p)
    pd.SetPolys(cells)
    # VTK computes the normals: OCCT's tessellation does not carry them, and
    # without normals the part comes out faceted even where it is round
    nrm = vtk.vtkPolyDataNormals()
    nrm.SetInputData(pd)
    nrm.SetFeatureAngle(40)
    nrm.SplittingOn()
    nrm.ConsistencyOn()
    nrm.Update()
    return nrm.GetOutput()


def _cut(pd, plane, colour):
    """The part cut by a plane, with the cut face CLOSED and DARKER than the
    surface.

    The cut face is coloured on its own because if it has the same tint as
    the part the section does not read as a section: it reads as a part made
    that way. Darker, and not hatched, because hatching in a colour render
    becomes noise - and the part's colour stays its own, as in the whole
    guide.
    """
    p = vtk.vtkPlane()
    p.SetOrigin(*plane[0])
    p.SetNormal(*plane[1])
    planes = vtk.vtkPlaneCollection()
    planes.AddItem(p)
    c = vtk.vtkClipClosedSurface()
    c.SetInputData(pd)
    c.SetClippingPlanes(planes)
    c.GenerateFacesOn()
    c.SetScalarModeToColors()
    c.SetBaseColor(*colour)
    c.SetClipColor(*[max(0.0, x*0.60) for x in colour])
    c.Update()
    return c.GetOutput()


class View(object):
    """A framing: which bodies, in what colour, cut from where, and from which
    side one looks."""

    def __init__(self, bodies):
        self.bodies = bodies
        self._meshes = {}

    def mesh(self, name):
        if name not in self._meshes:
            if name not in self.bodies:
                raise SystemExit("the assembly has no body '%s'" % name)
            self._meshes[name] = _mesh(self.bodies[name])
        return self._meshes[name]

    def render(self, pieces, png_file, direction=(1.0, -1.0, 0.6), up=(0, 0, 1),
               plane=None, frame=None, zoom=1.0, width=1400, height=1050,
               background=(1.0, 1.0, 1.0), arrows=(), count=False):
        """pieces: list of dictionaries
             name     the body in the assembly
             colour   (r, g, b)
             opacity  1 solid, less than 1 see-through (the context)
             offset   (dx, dy, dz) for the exploded views
             turn     (centre, axis, degrees): the body turned about an axis
                      before anything else - before the cut, before the
                      offset. A part that turns in the hand (the clutch on
                      the shaft) is shown the way it is held for the step
             cut      True if this body is to be sectioned by the plane
           frame: the only names to centre on; if missing, all of them.

           count=True changes the function's trade: instead of drawing the
           guide's picture, it redraws the SAME scene - same camera, same
           cut, same arrows covering - giving each body a flat shade all its
           own, and returns how many pixels of each stay visible. It serves
           the check that the part the step talks about really is in the
           frame: that the PNG exists proves nothing, a part out of frame or
           hidden behind another gives a file identical to a good one.
        """
        # the shades of the count: distinct greys, one per body. The
        # background is white (255) and the arrows black (0), so they do not
        # get mixed up.
        shades = {}
        if count:
            for i, p in enumerate(pieces):
                shades[p["name"]] = (i + 1) * 3
            if (len(pieces) + 1) * 3 > 250:
                raise SystemExit("too many bodies in one step to count them in flat shades")
        ren = vtk.vtkRenderer()
        ren.SetBackground(1.0, 1.0, 1.0) if count else ren.SetBackground(*background)
        ren.SetUseDepthPeeling(not count)  # real transparency, not by chance
        ren.SetMaximumNumberOfPeels(8)
        rw = vtk.vtkRenderWindow()
        rw.SetOffScreenRendering(1)
        # no antialiasing when counting: the edge pixels would be in-between
        # shades, and an in-between shade belongs to nobody
        rw.SetMultiSamples(0 if count else 8)
        rw.AddRenderer(ren)
        rw.SetSize(width, height)

        bounds = vtk.vtkBoundingBox()
        for p in pieces:
            pd = self.mesh(p["name"])
            if p.get("turn"):
                (cx, cy, cz), (ax, ay, az), degrees = p["turn"]
                tr = vtk.vtkTransform()
                tr.PostMultiply()
                tr.Translate(-cx, -cy, -cz)
                tr.RotateWXYZ(degrees, ax, ay, az)
                tr.Translate(cx, cy, cz)
                tf = vtk.vtkTransformPolyDataFilter()
                tf.SetTransform(tr)
                tf.SetInputData(pd)
                tf.Update()
                pd = tf.GetOutput()
            is_cut = bool(p.get("cut") and plane)
            if is_cut:
                pd = _cut(pd, plane, p.get("colour", (0.80, 0.80, 0.84)))
            actor = vtk.vtkActor()
            m = vtk.vtkPolyDataMapper()
            m.SetInputData(pd)
            # the cut part carries its colours with it (surface and cut
            # face), the others take them from the actor's property
            m.SetScalarVisibility(is_cut and not count)
            actor.SetMapper(m)
            sp = p.get("offset")
            if sp:
                actor.SetPosition(*sp)
            pr = actor.GetProperty()
            if count:
                v = shades[p["name"]] / 255.0
                pr.SetColor(v, v, v)
                pr.SetOpacity(1.0)            # the context really covers too
                pr.SetLighting(False)
            else:
                pr.SetColor(*p.get("colour", (0.80, 0.80, 0.84)))
                pr.SetOpacity(p.get("opacity", 1.0))
                pr.SetAmbient(0.22)
                pr.SetDiffuse(0.78)
                pr.SetSpecular(0.25)
                pr.SetSpecularPower(28)
            ren.AddActor(actor)

            # the edges: the shape must read printed in black and white too,
            # and a render that is only shaded becomes a blot at that point
            if not count and p.get("opacity", 1.0) > 0.85 and p.get("edges", True):
                edges = vtk.vtkFeatureEdges()
                edges.SetInputData(pd)
                edges.BoundaryEdgesOn()
                edges.FeatureEdgesOn()
                edges.SetFeatureAngle(35)
                edges.NonManifoldEdgesOff()
                edges.ManifoldEdgesOff()
                # ColoringOn is VTK's default and tints the edges by TYPE -
                # the boundaries in red - which here means red lines scattered
                # over the part with no meaning at all for whoever assembles
                edges.ColoringOff()
                ml = vtk.vtkPolyDataMapper()
                ml.SetInputConnection(edges.GetOutputPort())
                ml.SetResolveCoincidentTopologyToPolygonOffset()
                al = vtk.vtkActor()
                al.SetMapper(ml)
                if sp:
                    al.SetPosition(*sp)
                al.GetProperty().SetColor(0.12, 0.12, 0.14)
                al.GetProperty().SetLineWidth(1.4)
                al.GetProperty().SetLighting(False)
                ren.AddActor(al)

            if frame is None or p["name"] in frame:
                b = [0.0]*6
                actor.GetBounds(b)
                bounds.AddBounds(b)

        # The assembly arrows: (point of arrival, vector it arrives along).
        # They are not decoration - they say which way the part goes in, the
        # only thing an exploded view does NOT say by itself: the detached
        # part can be looked at and its place understood, but not from which
        # side it gets there.
        for tip, vector in arrows:
            lu = math.sqrt(sum(x*x for x in vector)) or 1.0
            f = vtk.vtkArrowSource()
            f.SetTipResolution(24)
            f.SetShaftResolution(24)
            f.SetShaftRadius(0.028)
            f.SetTipRadius(0.085)
            f.SetTipLength(0.22)
            # the arrow is born along x from 0 to 1: bring it onto the vector
            t = vtk.vtkTransform()
            t.Translate(tip[0] - vector[0], tip[1] - vector[1], tip[2] - vector[2])
            axis = [vector[i]/lu for i in range(3)]
            # VTK's arrow points along +x: turn it about x ^ axis
            cross = (0.0, -axis[2], axis[1])
            ang = math.degrees(math.acos(max(-1.0, min(1.0, axis[0]))))
            if any(abs(c) > 1e-9 for c in cross):
                t.RotateWXYZ(ang, *cross)
            elif axis[0] < 0:
                t.RotateWXYZ(180, 0, 1, 0)
            t.Scale(lu, lu, lu)
            tp = vtk.vtkTransformPolyDataFilter()
            tp.SetTransform(t)
            tp.SetInputConnection(f.GetOutputPort())
            m = vtk.vtkPolyDataMapper()
            m.SetInputConnection(tp.GetOutputPort())
            a = vtk.vtkActor()
            a.SetMapper(m)
            a.GetProperty().SetColor(0.10, 0.10, 0.12)
            a.GetProperty().SetLighting(False)
            ren.AddActor(a)

        cam = ren.GetActiveCamera()
        cam.ParallelProjectionOn()            # technical drawing, not photograph
        cam.SetViewUp(*up)
        c = [0.0, 0.0, 0.0]
        bounds.GetCenter(c)
        b = [0.0]*6
        bounds.GetBounds(b)
        radius = max(1.0, 0.5 * bounds.GetDiagonalLength())
        n = math.sqrt(sum(x*x for x in direction)) or 1.0
        eye = [c[i] + direction[i]/n * radius * 6 for i in range(3)]
        cam.SetFocalPoint(*c)
        cam.SetPosition(*eye)
        # The framing is computed on the PROJECTED OUTLINE, not on the sphere
        # that contains the part: VTK's ResetCamera uses the sphere, and a flat
        # wide part - almost all of them here - ends up in the middle of a
        # white field as large as its diameter.
        forward = [(c[i] - eye[i]) for i in range(3)]
        na = math.sqrt(sum(x*x for x in forward)) or 1.0
        forward = [x/na for x in forward]
        right = [forward[1]*up[2] - forward[2]*up[1],
                 forward[2]*up[0] - forward[0]*up[2],
                 forward[0]*up[1] - forward[1]*up[0]]
        nd = math.sqrt(sum(x*x for x in right)) or 1.0
        right = [x/nd for x in right]
        high = [right[1]*forward[2] - right[2]*forward[1],
               right[2]*forward[0] - right[0]*forward[2],
               right[0]*forward[1] - right[1]*forward[0]]
        mx = my = 0.0
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    v = [b[ix] - c[0], b[2+iy] - c[1], b[4+iz] - c[2]]
                    mx = max(mx, abs(sum(v[k]*right[k] for k in range(3))))
                    my = max(my, abs(sum(v[k]*high[k] for k in range(3))))
        aspect = float(width) / float(height)
        half = max(my, mx/aspect) * 1.06 / max(zoom, 0.01)   # 6% of air around
        cam.SetParallelScale(half)
        cam.SetClippingRange(radius*6 - radius*3, radius*6 + radius*3)

        lights = vtk.vtkLightKit()
        lights.SetKeyLightIntensity(1.05)
        lights.AddLightsToRenderer(ren)

        rw.Render()
        if count:
            return _count_shades(rw, shades)
        f = vtk.vtkWindowToImageFilter()
        f.SetInput(rw)
        f.SetScale(2)                          # twice the size, then shrunk
        f.Update()
        w = vtk.vtkPNGWriter()
        os.makedirs(os.path.dirname(png_file), exist_ok=True)
        w.SetFileName(png_file)
        w.SetInputConnection(f.GetOutputPort())
        w.Write()
        _trim(png_file, background)
        return png_file


def _count_shades(rw, shades):
    """How many pixels each body keeps in the flat-shaded scene."""
    import numpy as np
    from vtkmodules.util import numpy_support
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(rw)
    f.Update()
    im = f.GetOutput()
    wide, high, _ = im.GetDimensions()
    a = numpy_support.vtk_to_numpy(im.GetPointData().GetScalars())
    a = a.reshape(high * wide, -1)[:, :3]
    # a pixel belongs to a body only if it is exactly its shade on all three
    # channels: the smudges between two bodies count for nobody
    greys = a[(a[:, 0] == a[:, 1]) & (a[:, 1] == a[:, 2])][:, 0]
    how_many = np.bincount(greys, minlength=256)
    return {name: int(how_many[v]) for name, v in shades.items()}


def _trim(png_file, background, margin=0.03, final_width=1200):
    """Takes off the white around and shrinks.

    It is needed because the parts of this machine are almost all wide, low
    discs: framed in a 4:3 picture they leave two empty bands above and below
    as big as the part, and in the page - where the picture takes half a
    column - those bands eat half the space.
    """
    from PIL import Image
    im = Image.open(png_file).convert("RGB")
    ground = tuple(int(round(c*255)) for c in background)
    diff = Image.new("RGB", im.size, ground)
    from PIL import ImageChops
    box = ImageChops.difference(im, diff).convert("L").point(lambda v: 255 if v > 8 else 0).getbbox()
    if box:
        m = int(margin * max(box[2]-box[0], box[3]-box[1]))
        box = (max(0, box[0]-m), max(0, box[1]-m),
               min(im.size[0], box[2]+m), min(im.size[1], box[3]+m))
        im = im.crop(box)
    if im.size[0] > final_width:
        alt = int(round(im.size[1] * final_width / float(im.size[0])))
        im = im.resize((final_width, alt), Image.LANCZOS)
    im.save(png_file)
