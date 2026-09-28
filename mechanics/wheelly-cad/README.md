<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: CERN-OHL-P-2.0 -->

# Wheelly — parametric generator

The mechanical design of the motorised filter wheel, generated entirely from
code. Every drawing, every solid and the parameter table for Fusion 360 come from
a single parameter file, and a suite of checks verifies that they stay
consistent with each other.

**If you only want to print Wheelly, you do not need any of this**: the printable
STEP and STL files are attached to each release. This folder is for whoever wants
to regenerate them — for a different wheel, a different motor, a different
printer.

## Installation

```
pip install cadquery ezdxf
```

CadQuery brings the OCCT kernel with it (the same as FreeCAD's): the install
weighs a few hundred MB and is the only heavy dependency. Python 3.10–3.12.

The system Python may be newer than that: in that case a dedicated environment is
needed, otherwise CadQuery does not install.

```
uv venv --python python3.12 .venv && VIRTUAL_ENV=.venv uv pip install cadquery ezdxf
.venv/bin/python build.py
```

The parameter editor on its own needs only `ezdxf`, which runs on any version.

**The build also needs the makers' models of the bought parts** (motor, XIAO,
driver, GX12 socket): they are not redistributed with the project. Where to download them, and
under which file name, is in [`../others/README.md`](../others/README.md). If one
is missing, the build says which one and stops before generating anything.

## Use

```
.venv/bin/python build.py                # regenerate everything and check   (~20 min)
.venv/bin/python build.py --dxf-only     # the 2D drawings only               (a few seconds)
.venv/bin/python build.py --check-only   # only the checks, on the existing files
```

Always `.venv/bin/python`: the system Python has neither `cadquery` nor `ezdxf`.
The full build takes about twenty minutes, and more than half of it is the
checks, which run in parallel; `--one-by-one` runs them one at a time.

The results go into `out/`: there only the parts to print; the test tools in
`out/tools/`, the DXFs and the CSV in `out/drawings/`, the electronics envelopes
in `out/electronics/`, the reference solids (wheel body, disc, assembly) in
`out/references/`. If a check fails, `build.py` exits with code 2 and prints
which chain does not add up.

In `out/stl/` there are **coarse STLs** of every part, and an `assembly.stl` with
all the parts in place: three tenths of chordal error, small files, to open on the
fly in any viewer. They are not for printing: to print, start from the STEPs.

## Changing the design

The parameters are in `src/parameters.py`, but **that file is not edited**:
changes go into `src/parameters_local.py` (see *Local overrides*, below), by hand
or from the editor. Each row of the base is a tuple:

```python
("D_clutch", "mm", "50 mm", 50.0, "clutch_section; collar_plan"),
#  name       unit  expression value  drawings it appears in
```

The expression is what ends up in the CSV importable into Fusion and may refer to
other parameters (`"R_disc + D_clutch / 2"`); the numeric value is what the
scripts use. **They must be kept aligned**: change one, change the other.
`build.py` does not check it, because it does not evaluate expressions — the
editor does.

Then `.venv/bin/python build.py`, and the checks say at once whether the change
breaks something.

### Local overrides

`src/parameters.py` is the base and is best left alone: what you change goes
into `src/parameters_local.py`, next to it, which acts as an override. It is a
dictionary `name: (expression, value)` holding **only** what differs from the
base, and `parameters.py` loads it by itself, by path, if it is there.

```python
OVERRIDES = {
    "Dp_slot_front": ("8.5 mm", 8.5),
    "Chord_slot":   ("2 * sqrt(...)", 71.3),   # derived: only the value changes
}
```

It also holds derived parameters, with the expression unchanged and the new
value, because `parameters.py` keeps values already computed and cannot redo the
sums by itself — the editor evaluates the expressions. To go back to the base
design, delete the file; to see in two lines what was changed, open it.

The file shipped with the project holds the values of the wheel Wheelly was built
around (a five-position StarDikor for 2-inch filters): **for a different wheel,
this is the file you change.**

## Structure

```
build.py                        single entry point
ui.py                           the parameter editor
src/parameters.py               SOURCE OF TRUTH: every parameter
src/parameters_local.py         overrides of the base, written by the editor
src/drawings.py                 DXF: plans, sections, gasket, sensor bracket + CSV
src/drawings_assembly.py        DXF: the assembly view, in plan and in section
src/drawing_dimensioned.py      dimensioned DXF of the body (native DIMENSION entities)
src/solids_body_collar.py       STEP: reference body, disc, collar
src/solids_wheel.py             STEP: clutch (ASA hub + TPU tyre)
src/solids_arm.py               STEP: motor arm
src/solids_box_collar.py        STEP: box and collar, one part, with the electronics in the motor bay
src/electronics.py              where the electronics sit: board, head, board panel
src/solids_electronics.py       STEP: board panel, and the electronics envelopes in out/electronics
src/solids_sensor.py            STEP: sensor bracket, in its mounting position
src/solids_tools.py             STEP: tools (magnet gluing cap, air-gap test feet)
src/solids_cables.py            STEP: the cables, as solids, with their bend radius
src/stl_preview.py              coarse STLs of every part and of the assembly, in out/stl
src/check_dimensions.py         dimensional chains (axial, radial, torques, box, sensor)
src/check_audit.py              cross audit + interpenetrations, measured on the solids
src/check_*.py                  the other checks (assembly paths, grip, inserts, ...)
src/bom_*.py                    the bills of materials, generated: BOM.md here and ../../BOM.md
src/guide/                      the assembly guide (docs/assembly), generated from the solids
src/ui_*.py, src/ui_static/     the parameter editor (see below)
out/                            results
```

## The two levels of checking

`check_dimensions.py` verifies the **numeric chains**: that the walls add up to
the body's height, that the hub fits inside the opening, that the motor's holes
fall outside the edge of the arm, that the required torque has margin on the
motor's holding torque, that the sensor's air gap is in the allowed window.

`check_audit.py` does something different and stricter: **it reads back the
generated files** and compares them with the parameters, instead of trusting that
they come from the same generator. It checks that the CSV matches the parameters,
that every hole in the DXFs is where it should be, that the STEP envelopes add up,
and that the solids do not interpenetrate in pairs.

The second one found the real errors: the arm inside the collar's flange, and the
clutch modelled in a reference system different from the assembly's.

## Reference system

Common to all files, and worth learning before reading the drawings:

- **origin** on the centre of the disc, its axis of rotation — *not* on the
  optical axis, which is off by `Off_hole_optical` because it is on the circle of
  the filter holes
- **+X** along the line from the disc centre to the clutch axis
- **z = 0** on the camera-side face, **+z** towards the telescope

In the sections: X = radius from the disc centre, Y = axial height.

## Parts to print

**The list of parts, with quantity, material, mass and print orientation, is the
generated bill of materials**: [`BOM.md`](BOM.md) here, and the global one,
[`../../BOM.md`](../../BOM.md). The build writes them from `src/bom_mechanics.py`,
with the mass measured on the solid. A new part is registered in `PRINTED`, in
`src/bom_mechanics.py`, print orientation included.

Only what the list does not say is here: the why of the orientations.

- **box + collar** (`box_collar`): as modelled, the electronics door on the bed.
  **It needs a 200 × 200 bed.**
- **grip and door cover** (`grip_cover`): upside down, top face on the bed. It
  carries the plate that closes the door over the motor, and standing up it would
  be a 45 × 60 overhang. It is held by two knurled-head M3 DIN 912 screws,
  vertical, that come off by hand to clean the filters, each in an insert in the
  collar.
- **cover of the hatch under the motor** (`hatch_cover`): outer face on the bed,
  which is the visible one, flush with the bottom. The motor goes in from below
  after the arm; the cover is held by two countersunk M3 × 8 in inserts set from
  below into the raised floor.
- **clutch**: the hub prints with its axis vertical, collar face on the bed, and
  the TPU 87A–95A tyre is co-printed with the hub, held by dovetail teeth.
- **board panel** (`board_panel`): outer face on the bed, so that the seat,
  standoffs, guides and tab grow upwards.

The collar has a **window for reading the filter number**, repeating the one the
maker already put in the metal body, and it follows that one's angle
(`Ang_window_body`). The gasket groove goes round it without a break: the numbers
are at r 68.5, exactly where the bead used to run.

The box has a **recess in line with the clutch**: there the wall steps in from
r 130 to `R_grip_box` = 120.1, below the radius of the tread, and the tread sticks
out of the opening by `Proj_tread_grip` = 2 mm **measured in the working
position**, with the TPU squashed against the disc. The wheel turns by hand with
the thumb — a little over half a turn per filter — and the plug closes the recess
when it is not needed, because an opening next to the friction pair invites dust
exactly there. The opening is ±10.44 degrees wide because it must let the clutch
pass over **the arm's whole travel**, not where it is drawn: the arm carries it
3.6 mm around. The plug also closes the recess **at the top**, with a flap flush
with the box's ceiling. It comes out by its **fingernail notch**, which crosses its
face and has the flap itself as ceiling. **The recess needs no support**: there is
no ceiling (the recess goes up to the top), the flare below opens at 45 degrees
until it meets the wall again, and the ceiling of the opening is a cone at the
same slope. `check_audit.py` watches it face by face on the solid.

The **gaskets print flat**, and the direction matters: that way the compression
travels **across** the layers instead of trying to split them, which is the right
way for a part that works squashed. The profile is **hollow**: solid, the 50 %
squeeze the groove assumes would need an excessive force on a 95A TPU, paid by
the collar, which is ASA. Hollow, the same seal is had with **25 %** squeeze, and
the inner void also makes room for the material being pushed aside — rubber is
incompressible, and a groove filled 100 % does not close. At rest the groove is
**83 %** full.

**Box and collar are ONE PART**, printed with the electronics door on the bed.
They used to be two parts held by 5 screws and 5 heat-set inserts, and that joint
cost three defects found with the parts in hand: the box would not pass over the
pivot screw while being slid on, an ear of the collar snapped while being fitted,
and the screws were ten chances to get it wrong. Joined, two defects out of three
disappear by construction. It costs 17 mm of bed (from 166 to 184) and 17 % more
support (from 11,361 to 13,336 mm²). **It needs a 200 × 200 bed.**

The two sealing faces face each other, and whichever way it prints one comes out
well and the other is an overhang — **they swap, they do not add up**. The
reasons the choice is not free are these three:

1. One of the two sealing faces necessarily ends up on supports — measured on the
   solid they overhang 100 %, 2,371 mm² the front and 2,662 the rear, because
   below r 79.15 there is no band under them. So one chooses **which** to
   sacrifice, and they are not equivalent: the camera face has **two barriers in
   series**, gasket plus labyrinth rib; the telescope face has **the gasket
   only**. In this orientation the one with a single barrier gets the first
   layer's finish.
2. The Ø3.2 hole of the reinforced pivot is **19 mm long and must print along its
   own axis**: laid down it would come out oval and the M3 would not go in. That
   is why the on-its-side orientation, which would have a third of the overhangs,
   is ruled out.
3. This way the pivot **grows upwards from solid material** instead of being an
   isolated Ø5 pillar.

**The pivot support is 13.7 mm tall and blends into the band with a fillet.** Its
top stops **two millimetres** below the ceiling of the box's mechanics bay, and
those two millimetres are not a tolerance: they are the clearance to slide the box
over the already assembled mechanism, which is how the machine is assembled. It
is the same number the bay's check watches, not a copy of it. The lower part stays
**cylindrical Ø21** — that is where the arm's moment goes into the body — and the
taper starts only where it has to close the difference in radius, at **52
degrees**, two more than the minimum that holds up: the margin is in the part, not
in the check's threshold.

The **fillet** has radius 3 and is tangent by construction, not an OCCT fillet:
OCCT's fillet crashes on this geometry, because the curve where the cone meets the
band is a 33 mm B-spline. The profile is three arcs — support, band and blending
arc — stacked in a loft, so the fillet fades as it rises instead of ending in an
edge facing the bed.

**At the top 44.8 mm² are left to support, on purpose.** In this orientation the
support points at the bed, so its first layer is the top face: a cone with its
tip towards the bed does not hold up however steep. Removing them would mean
bringing the insert's mouth from z 10 to z 5 and the screw from M3 × 20 to
M3 × 16; it was chosen not to pay that. Above the mouth there is the **Ø8 channel
for the soldering iron tip**, which is also why the mouth stays at 10.

**The pivot insert is set with the collar bare.** Above its mouth the box passes
at z 16: once the box is on, the soldering iron cannot reach it any more.

**The co-print is sliced with "Use beam interlocking" on** (PrusaSlicer). Tried:
the gaskets hold well. That option weaves beams between the two volumes, so it
works together with the joint's dovetail teeth instead of replacing them — whoever
prints without it still has the teeth.

**The part also comes out co-printed.** `out/box_collar_coprinted.step` carries the
three bodies — the ASA part and the two TPU gaskets — separate and named by
material, which is how a slicer for an IDEX printer takes them, one body per
extruder. That the two materials do not overlap is checked.

**The collar has a flat bottom.** On that side the three rear bosses stuck out by
2 mm, and only they rested on the bed: 269 mm², with the whole flange hanging
above and to be supported. Now those 2 mm are solid over the whole footprint of
the flange and the part rests on **3,638 mm²**, 76 % of the flange. Two groups of
**pockets** remain, because in that layer sit the paddles of the sensor bracket and
the three rear ears of the box: the bottom of each pocket is the old resting face,
so bracket, box and air gap do not move. The pockets have 0.5 mm of play and centre
nothing (the bosses centre the box, the magnet centres the bracket), and the
bracket's is its outline swept over the ±`Halfw_slot_collar` of the slot, because
the bracket rotates to reach the screws. The pockets' ceilings still need
breakaway supports: before, the whole flange did. Measured on a collar printed in
ASA, the pockets do not narrow towards the ceiling.

The **front ears** go down to the bed as two columns with a Ø16 round foot and a
cone opening very gently to Ø22: the pair that carries the spring's moment rests on
a pillar instead of a bracket. Lightening is left to the slicer, so the mass in
the bill of materials is the fully solid one, not that of the printed part.

**The box prints as modelled**, with the floor of the mechanics bay on the bed.
The alternatives were worse by an order of magnitude: upside down (standing on
the six ears) the first layer is a few hundred mm² and the overhangs much larger;
on its side there is no resting face at all. The overhangs left are mostly the
**ceilings of the two bays**, internal surfaces: nobody sees the support marks
there and they seal nothing — the right place for breakaway supports.

`filter_wheel_body.step` and `filter_disc.step` **are not printed**: they are used
to check the envelopes against the real part.

The STEPs are placed in the assembly's system, so far from the origin: slicers
re-centre them by themselves.

## Licence

CERN-OHL-P-2.0 for the mechanics, as the SPDX header of each file says; the full
picture is in [`../../LICENSING.md`](../../LICENSING.md).

## Parameter format

```python
("D_clutch", "mm", "50 mm", 50.0, "clutch_section; collar_plan", "S",
  "Contact diameter of the clutch wheel. It governs the reduction ratio..."),
```

| field | content |
|---|---|
| name | as it appears in Fusion and in the scripts |
| unit | `mm`, `deg` or `""` for unitless values |
| expression | the one that ends up in the CSV; it may refer to other parameters |
| value | the number the scripts use — **to be kept aligned with the expression** |
| drawings | which files it appears in, to know what breaks when it changes |
| origin | `M` measured on the part · `S` design choice · `D` derived · `R` from a catalogue |
| description | what the dimension refers to, in words |

The **origin** field says how negotiable a dimension is. `S` ones change freely and
the checks will say what suffers. `M` ones change only by measuring the part again.
`D` ones are not touched: change the parameter they derive from. `R` ones come
from the datasheet.

The description also ends up in the Comments field of the CSV, so you read it
inside Fusion in the parameters window.

## The parameter editor

The seven fields drive an editor: name and expression for the input field, origin
to decide whether it is editable, description for the help text, and the list of
drawings to show the right figure next to it.

```
.venv/bin/python ui.py              opens the editor at http://127.0.0.1:8760/
.venv/bin/python ui.py --port N     on another port
.venv/bin/python ui.py --no-open    without opening the browser
```

The editor **does not reload the files by itself**: restart it after changing a
generator or the parameters by hand.

Change an expression and three things happen, in half a second: the parameters
that derive from it are recomputed following the dependency graph, the DXFs are
regenerated, and the dimensional chains are re-run, showing at the top those that
no longer pass and an arrow on those whose margin got worse.

**The expression is the source, the value follows from it.** The editor
interprets Fusion's syntax (`^`, `sqrt`, `atan`, references to other parameters,
`mm` and `deg` units) and derives the number, instead of asking you to keep them
aligned by hand. `D` parameters with a formula are read-only: their value is a
result. Circular dependencies and invalid expressions are refused without
touching the model.

**It writes nothing.** Changes live in memory and regeneration happens in a
temporary folder: `src/parameters.py` is never touched, and neither is
`parameters_local.py`. *Export parameters_local.py* gives the file of overrides to
save, and *Changes* shows its diff against the one already on disk.

The editor starts from **the base plus the overrides already saved**, and the
export puts them all back, not only those of this session: otherwise exporting
again would lose yesterday's work. For the same reason *Reset* goes back to the
saved overrides, not to the bare base — to go back to the base, delete
`parameters_local.py`.

**Generate the STEPs** does the rest, what `build.py` does: the solids, the
dimensional chains and the cross-audit checks, interpenetrations included. It goes
through the OCCT kernel and costs as much as the full build, so it runs in a
thread and the window shows the steps as they go, with the masses and volumes
each module prints.

This too happens in a sandbox. If the parameters are those on disk and every check
passes, the files go **into `out/` by themselves**: they are exactly what
`build.py` would produce. Saving also removes files no generator produces any
more, so `out/` does not accumulate leftovers. When there are parameters not yet
exported, or a check fails, saving stays manual behind *Move the files to out/*,
and the window first says which parameters differ: an `out/` generated from
parameters that are not in the parameter files is exactly the divergence
`check_audit.py` exists to find.

**The selected dimension is traced on the drawing.** The `drawings` field says in
which figure a parameter appears, not where: the place is found by measuring,
looking in the DXF for the geometry worth that number — the same method with
which `check_audit.py` verifies that a hole is where it should be. Editing
`D_holes_M3` lights up the four M3 holes with their diameter dimension, and the
view moves onto them. The colour says where the number comes from, with the same
scale as the marks in the list: orange `S` changes freely, blue `M` is measured
on the part, purple `D` is a result and is not edited, green `R` comes from the
datasheet. The panel zooms with the wheel and pans by dragging; *dimension* brings
the view back to the annotation, *fit* puts the whole drawing back in.

The method has a declared limit: not every dimension is found in a drawing, and
a common value matches many geometries, so only the matches of the most specific
kind are kept, and duplicates in the same place are removed.

```
src/ui_model.py             reading, evaluating expressions, export
src/ui_build.py             sandboxed regeneration (2D and full) and reading the checks
src/ui_dimensions.py        where a dimension is in the drawing, found by measuring
src/ui_render.py            DXF -> SVG, and tracing the selected dimension
src/ui_server.py            local server
src/ui_static/index.html    the page
```

## The assembly view

The other drawings show one part at a time, dimensioned for printing.
`assembly_plan` and `assembly_section` are for the eye: where each thing is
relative to the others. In the editor they are two tabs always present, next to
the detail drawings of the chosen parameter.

The line says what is what. **Solid and bold** the parts that are printed —
collar, arm, clutch, box. **Dashed** the reference ones, not printed: wheel body,
disc, the rotator's envelope around the optical axis. **Transparent tint** the
bought or external items: motor, sensor module, magnet, spring. A legend repeats
the three conventions, and **every item carries its name**, with a leader starting
from a point on the item itself.

The drawing is composed in three layers: first all the tints, then all the lines,
finally the leaders. DXF has no depth, whoever is written last wins: without this
order the motor's fill covered the arm's plate and half the clutch. Where two parts
really occupy the same area the tint is laid once, otherwise the transparencies
add up and the area goes dark. The colour is explicit in the DXF because it is the
only thing that survives conversion to SVG, and for the same reason these two
views render in colour while the others stay monochrome. The leaders are on a
separate layer that `ui_dimensions.py` skips: a leader line as long as it happens
to be would gladly offer itself as a match for any dimension.

## Design notes

### The sensor bracket is on the telescope side

The sensor sits on the **telescope-side face**. The disc's hub is flush there too,
the same (Ø7.95), so magnet, cap and ring do not change: the face does. The
bracket could not go on the camera side, because **there are no screws there to
hold on to**: the four M3 of the back plate are threaded for 6 mm from the
telescope side, and none shows from the camera side.

On the telescope side, however, there is the **rotator**: its envelope around the
optical axis passes practically through the disc centre, and any arm pointing
towards the optical axis ends up inside it. Of the four M3 screws (at −40, 50, 140
and 230 degrees) only **−40 and 50** are on the free side, and they are exactly
the ones the collar is screwed to.

Hence the shape: a **V**, with the hub in the middle and two arms 90 degrees
apart, one per screw. `Ang_bracket_sensor` is derived, `(Ang_screw_A +
Ang_screw_B) / 2`, the bisector: if measuring the real screws shows they are
elsewhere, the bracket follows them by itself. The paddles rest on the **collar's
rear flange** and are clamped with the same M3 that holds the collar, lengthened
to **M3 × 12**: paddle 3.43 + flange 3 make 6.43, leaving 5.57 engaged in the 6 of
thread.

In height the bracket is therefore **stepped**. The hub and the inner part of the
arms sit on the body's face, `H_rest_module` tall; at r 61.5 — a millimetre before
the inner edge of the flange — the arms rise by `Th_flange_collar`. Two supports
rather than a cantilever: by symmetry the chip does not tilt about the bisector,
and the other way the torsion of the arms holds it.

The **slots** are radial, ±2.5 mm, and 4 wide instead of 3.4. Radial because the
angle is taken up by the bracket rotating on the magnet: the screws are on a
square and move together. Wide because with two arms not in line the offset
between the centre of the square of screws and the disc axis can no longer be
taken up by rotating, and it is left to the side play.

`check_dimensions` checks that every paddle falls on a screw, that the bracket
stays inside the collar, that the paddles all sit on the flange's arc and that only
the hub enters the rotator — which it must, by its whole radius, because the
magnet is there.

### How the sensor module rests

The resting plane under the module is **lowered by `Dp_notch_module`** (1.2 mm)
everywhere except **two pads around the M2 holes**: the module touches only
there, where no module carries components because the screw passes. Under the
module, on the same face as the chip, there are capacitors and resistors with
their solder joints: resting on them would mean the air gap is no longer the one
in the drawing. The recess follows the module's real outline — a Ø16.85 round
with two flats at 15, **the two M2 holes on the axis of the flats** — and also
takes in the arms, since the module overhangs the Ø15.3 hub.

The screws **tap themselves into the hub**. The module's holes are Ø2.0, measured,
and the M2 screw passes through; under the hub there is the body's face, so a nut
does not fit. The hole in the hub is **1.8**: the pilot for an M2 screw with a
parallel thread, which has no cutting edges and at 1.7 would split the hub instead
of forming the thread.

The magnet hole is drawn **wider than the design**. By design the ring sits on the
magnet with 0.075 of radial play, which is the centring; but an FDM hole comes out
one or two tenths undersize and the seam leaves a bump in it, so of 0.075 nothing
is left and the magnet does not turn. The model therefore carries
`D_hole_magnet_printing` = design + `Comp_hole_printing`, and the test feet add
`Cl_test_magnet` on top. The compensation is a number of the printer and is
corrected by measuring a printed part. At the bottom of the hole there is a 0.3
lead-in cone: the magnet sits on the first layer, where the elephant foot
tightens, and without the lead-in it does not go in even at the right diameter.
The audit tries to slide the magnet into every test foot and into the bracket,
and says so if it touches.

### Centring the sensor

The AS5600 wants the magnet centred on the chip within 0.25 mm. The bracket's ring
is dimensioned on what it touches — the **magnet**, the only cylindrical thing
standing out of that face — `D_magnet + 2 × Cl_ring_bracket`, with the play held
tight at 0.075: the bracket centres itself as it comes down on the magnet. The
wheel turns rarely and by few degrees, wear of the hole is not a concern.

A **plug gauge cannot be made**: between the magnet (8.0) and the ring's hole
there are 0.275 mm radially, and no printable wall passes there. So the gauge's
job is done by the ring itself, which is better, because the centring is
permanent instead of to be redone at every disassembly.

What remains is the **gluing cap**, `magnet_cap`: the magnet goes in a seat, glue
goes on, the cap is rested on the face and pressed. The magnet lands on the top of
the hub flat, square and flush, and does not slide sideways while the glue sets.
The absolute centring is given by the eye: Ø8 on a Ø7.95 hub leaves 0.025 of rim
each side, and an even rim all round is easy to see. The drawing `magnet_cap.dxf`
carries the procedure next to the part.

### The spring

`R_seat_spring_box` is not a chosen number but `R_rest_spring_arm +
L_spring_fitted` — the axis is almost radial, the approximation is worth two
hundredths — so the seat in the box follows the spring. The arm carries a
**spigot** that enters the spring's inner diameter and keeps it on its axis:
`D_spigot_spring`, on a tab under the arm (`H_tab_spring_arm`).

`check_audit.py` does not take the arm's flank from the parameters: it probes the
solid with a ball along the spring's axis until it leaves the material, and checks
that the gap up to the seat equals `L_spring_fitted`. The flank the spring rests
on is a straight side, perpendicular to its axis.
