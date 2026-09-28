# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0
import os


"""Single source of truth for the DXF, the STEP and the Fusion parameter CSV."""
import math

# (name, unit, expression, value, drawings label, origin, description)
# The drawings label and the description are English; their Italian is kept in
# texts_parameters_it.py, keyed by name, and shown by the editor when
# WHEELLY_LINGUA=it. A new row is written in English only. The drawings label
# is also matched by ui_render.drawings_of: keep the drawing file names in it
# (collar_plan, clutch_section, ...) and the part word at its head.
P = [
 ("--- FILTER WHEEL BODY (reference, not printed) ---",),
 ("D_body", "mm", "158 mm", 158.0, "filter_wheel_body; collar_plan", "M",
    "Outer diameter of the filter wheel body. It is the radial reference of the whole design: the collar rests on it and every radius is measured from the centre of this cylinder."),
 ("H_body", "mm", "23 mm", 23.0, "filter_wheel_body; collar_section", "M",
    "Total height of the body with the wheel closed, from the camera-side face to the telescope-side face. It sets the zero and the full scale of all axial dimensions."),
 ("Th_wall_front", "mm", "4.3 mm", 4.3, "filter_wheel_body; collar_section", "M",
    "Thickness of the front plate, camera side. The front flange of the collar rests on top of it; below it begins the air above the disc."),
 ("Th_wall_radial", "mm", "5.86 mm", 5.86, "filter_wheel_body - measured at the opening rim", "M",
    "Thickness of the side wall measured on the cut edge of the opening. Different from the front one, so it has its own parameter."),
 ("H_opening", "mm", "10 mm", 10.0, "filter_wheel_body; clutch_section", "M",
    "Net height of the side opening, derived from two depth readings taken from the face. It is the space the clutch hub has to pass through."),
 ("Th_wall_rear", "mm", "H_body - Th_wall_front - H_opening", 8.7, "filter_wheel_body; collar_section", "D",
    "Thickness of the rear plate on the telescope side, by difference. It hosts the four M3 holes threaded to 6 mm into which the collar is screwed, and with it the sensor bracket."),
 ("Read_caliper_opening", "mm", "149.5 mm", 149.50, "MEASURED - jaw on the flat, the opposite one on the cylinder", "M",
    "Caliper reading across the body: one jaw on the flat of the opening, the other on the opposite cylinder. It is the primary measurement from which the cutting plane, the chord and the projection of the rim are derived."),
 ("D_plane_opening", "mm", "Read_caliper_opening - D_body / 2", 70.50, "filter_wheel_body - plane of the straight cut", "D",
    "Distance from the axis of the plane on which the opening was milled. The opening is a straight cut, not a curved sector."),
 ("Chord_opening", "mm", "2 * sqrt((D_body / 2) ^ 2 - D_plane_opening ^ 2)", 71.30, "filter_wheel_body", "D",
    "Length of the opening measured in a straight line between its two ends. It must stay wider than the diameter of the clutch, with margin."),
 ("Proj_rim", "mm", "R_disc - D_plane_opening", 2.00, "documentation - the knurled rim projects from the flat", "D",
    "How far the knurled rim of the disc projects beyond the plane of the cut. Positive means the clutch never touches the milled flat."),
 ("Chord_slot", "mm", "2 * sqrt((D_body / 2) ^ 2 - (D_body / 2 - Dp_slot_front) ^ 2)", 43.13, "filter_wheel_body", "D",
    "Length of the front slot, shorter than the opening because its plane is less deep."),
 ("Dp_slot_front", "mm", "3 mm", 3.0, "filter_wheel_body - slot in the camera face, along the whole chord", "M",
    "Radial depth of the slot cut into the camera-side face, which runs along the whole chord. It is a light path into the interior and has to be closed."),
 ("Th_rib_labyrinth", "mm", "2 mm", 2.0, "collar - rib that enters the slot", "S",
    "Thickness of the collar rib that enters the front slot. Half a millimetre of clearance per side."),
 ("H_rib_labyrinth", "mm", "3 mm", 3.0, "collar", "S",
    "How far the rib sinks into the slot. The deeper it is, the longer the path light would have to take to get in."),
 ("Disc_rotating", "mm", "145 mm", 145.0, "filter_wheel_body; arm_plan", "M",
    "Diameter of the disc that carries the filters. The clutch touches it on the knurled rim."),
 ("Th_disc", "mm", "4 mm", 4.0, "filter_wheel_body; clutch_section", "M",
    "Thickness of the disc at the rim, chamfers included."),
 ("Band_knurled_net", "mm", "3.6 mm", 3.6, "clutch_section", "M",
    "Width of the knurling alone, less the 0.2 mm chamfers on each side. It is the surface usable for contact and it limits the width of the tread."),
 ("Z_plane_mid_disc", "mm", "Th_wall_front + Air_above_disc + Th_disc / 2", 8.5, "ALL - axial datum", "D",
    "Height of the mid-plane of the disc from the camera-side face. It is the axial datum of the design: the tread is centred on it."),
 ("Air_above_disc", "mm", "2.2 mm", 2.2, "filter_wheel_body", "M",
    "Free space between the inner face of the front plate and the front face of the disc."),
 ("R_disc", "mm", "Disc_rotating / 2", 72.5, "arm_plan; collar_plan", "D",
    "Radius of the disc. The clutch contact happens exactly here."),

 ("N_holes_filter", "", "5", 5.0, "reference - filter disc; COUNTED", "M",
    "Number of filter holes in the disc, equally spaced. Five on the reference wheel, the StarDikor: it sets the angle between two holes (360 / 5 = 72 degrees) and, with the web between two holes, the radius of the hole circle."),
 ("D_thread_filter", "mm", "48 mm", 48.0, "reference - filter disc; M48x0.75 thread", "R",
    "Nominal diameter of the thread the filters screw into: M48 x 0.75, the standard thread of 2-inch filters. A standard figure, not a caliper reading. The hole is NOT drawn at this diameter: see D_hole_filter."),
 ("Pitch_thread_filter", "mm", "0.75 mm", 0.75, "reference - filter disc; M48x0.75 thread", "R",
    "Pitch of the filter thread, M48 x 0.75 (standard, ISO fine pitch)."),
 ("D_hole_filter", "mm", "D_thread_filter - 1.08253 * Pitch_thread_filter", 47.1881, "reference - filter disc; ESTIMATED from the thread", "D",
    "Diameter of the filter holes in the disc as the model draws them: the MINOR diameter of the internal thread, D1 = D - 1.08253 P (ISO 68-1 / ISO 965 basic profile, 5/8 of H twice, H = 0.866 P), 47.19 mm for M48 x 0.75. The thread crests are what material there is: the web between two holes and the rim outside them are measured from here. A hand-written radius of 25.5 (a 51 mm hole) at 48 mm from the centre would cut 1 mm into the rim of a 145 mm disc; the real disc has closed holes (from a photo of the reference disc: about 47 mm, about 3.2 mm of rim)."),
 ("W_web_filter", "mm", "6.5 mm", 6.5, "reference - filter disc; ESTIMATED by hand, to be measured", "S",
    "Material between two adjacent filter holes, at its narrowest. ESTIMATED BY HAND on the reference wheel, NOT with the caliper - measuring it means dismounting the wheel: to be measured with the caliper when the wheel is dismounted. Together with D_hole_filter and N_holes_filter it gives the radius of the hole circle, that is the optical axis: an error of 0.3 mm here moves the axis by 0.26 mm."),
 ("Off_hole_optical", "mm", "(W_web_filter + D_hole_filter) / (2 * sin(180 deg / N_holes_filter))", 45.6714, "reference - optical hole off-centre relative to the disc centre; ESTIMATED", "D",
    "How far the optical axis is off-centre relative to the centre of the disc: the radius of the circle of the filter holes, because a filter in position IS on the optical axis, so the two cannot be two numbers. Two adjacent holes are 2 R sin(36 deg) apart, centre to centre, and that is one hole plus one web: R = (web + D1) / (2 sin(180 / n)), 45.67 mm. It agrees with a photo of the dismounted reference disc (about 45.8, scale taken on the 145 mm diameter) and leaves 3.24 mm of rim, the photo says about 3.2. A hand-written 48 mm, classed as MEASURED with no record of what was measured, was rejected: with 51 mm holes it cut the rim, and 48 is also the thread size of the filters and the value of R_envelope_optical, which is probably where it came from. It is an ESTIMATE until the web is measured with the caliper. Everything placed on the optical axis follows it: the optical hole of the body, the rotator envelope and the cuts it makes in the collar and in the sensor bracket and cover. The electronics window is on the opposite side."),

 ("--- KINEMATICS ---",),
 ("D_clutch", "mm", "50 mm", 50.0, "clutch_section; collar_plan", "S",
    "Contact diameter of the clutch wheel. It governs the reduction ratio and, through the centre distance, the position of the motor relative to the body."),
 ("Cd_motor", "mm", "R_disc + D_clutch / 2", 97.5, "arm_plan; collar_plan", "D",
    "Distance between the disc centre and the clutch axis. With the current diameter the motor stays entirely outside the body."),
 ("Off_pivot", "mm", "56 mm", 56.0, "arm_plan; collar_plan", "S",
    "Distance of the pivot from the contact point, measured on the perpendicular to the line joining the axes. The kinematic constraint is the line, not the distance: any value is fine as long as the pivot hub stays outside the body."),
 ("L_arm", "mm", "sqrt((D_clutch / 2) ^ 2 + Off_pivot ^ 2)", 61.33, "arm_plan", "D",
    "Distance between the pivot axis and the motor axis."),
 ("R_pivot", "mm", "sqrt(R_disc ^ 2 + Off_pivot ^ 2)", 91.61, "collar_plan", "D",
    "Radius at which the pivot lies, from the centre of the disc."),
 ("Ang_pivot", "deg", "atan(Off_pivot / R_disc)", 37.68, "collar_plan", "D",
    "Angle of the pivot relative to the line joining the axes."),
 ("Ratio_reduction", "", "Disc_rotating / D_clutch", 2.90, "documentation", "D",
    "Clutch turns per disc turn."),

 ("--- CLUTCH ---",),
 ("Th_clutch", "mm", "3 mm", 3.0, "clutch_section - tread width", "S",
    "Width of the TPU tread. Narrower than the knurled band, so it all stays engaged even with a few tenths of misalignment."),
 ("D_hub_clutch", "mm", "44 mm", 44.0, "clutch_section", "S",
    "Diameter of the ASA core on which the TPU ring is printed."),
 ("D_shoulders_clutch", "mm", "46 mm", 46.0, "clutch_section", "S",
    "Diameter of the two shoulders that stop the tread from walking axially."),
 ("H_hub_clutch", "mm", "Z_base_collar_grub - Z_top_clutch", 5.0, "clutch", "D",
    "How tall the clutch HUB is, that is the part around the tread: the lower shoulder, the tread band, the upper shoulder. It does not include the grub collar, which sits above it and is another thing. It was 8 and it was a choice, from when the hub was a single cylinder from which the band was cut out; since the hub has started at the lower shoulder and ended at the upper shoulder, its height is no longer free - it is what the three bands add up to. It stayed 8 while the hub had become 5, and the checks of the axial chains were measuring three millimetres that were not there."),
 ("Z_top_clutch", "mm", "Z_plane_mid_disc - Th_clutch / 2 - H_shoulder_clutch", 6.0, "clutch_section - height of the hub top", "S",
    "Height of the top of the hub. Together with the height, it positions the clutch inside the opening."),
 ("H_shoulder_clutch", "mm", "1 mm", 1.0, "clutch_section", "S",
    "Height of each retaining shoulder."),
 ("R_fillet_tread", "mm", "0.3 mm", 0.3, "clutch_section", "S",
    "Fillet on the two shoulders of the tread. It removes the edge load without reducing the useful cylindrical zone."),
 ("N_teeth_clutch", "", "8", 8.0, "clutch STEP - circular pattern", "S",
    "Radial teeth on the hub that transmit the torque to the TPU. They work together with the slicer's beam interlocking, at different scales."),
 ("Th_teeth_clutch", "mm", "1 mm", 1.0, "clutch STEP", "S",
    "Radial depth of the teeth, that is how far the dovetail goes into the hub."),
 ("L_teeth_clutch", "mm", "2.5 mm", 2.5, "clutch STEP", "S",
    "Width of the tooth at the MOUTH, on the edge of the hub. Towards the bottom it widens: that is the dovetail."),
 ("Widen_tail_dovetail", "mm", "1.5 mm", 1.5, "clutch - teeth", "S",
    "How much wider the tooth is at the bottom than at the mouth. It is what makes the joint a dovetail: the TPU ring can no longer slip out radially, and the torque no longer relies only on the adhesion between the two materials. It prints without overhangs because the profile lies in the print plane and is extruded along the axis. TESTED BY HAND: pulling the TPU ring on a co-printed clutch, IT DOES NOT COME OFF. It is the verification no check could make - the bond between two materials is not in the solid - and it is the reason the teeth exist: so that the torque does not depend on the adhesion between ASA and TPU. MIND WHAT IT ACTUALLY TESTED: the test part was sliced with PrusaSlicer's 'Use beam interlocking' enabled, so the test says that TEETH PLUS INTERLOCKING together hold, and does not separate the two contributions. Anyone printing without that option does not have this test, and anyone wanting to remove the teeth trusting the slicer does not have it at all."),
 ("D_collar_grub", "mm", "30 mm", 30.0, "clutch - insert collar", "S",
    "Diameter of the collar that, below the tread, carries the heat-set insert of the grub. Thirty and no more: the collar turns with the hub, so its radius has to be added to the centre distance - at Ø30 it reaches r 82.5 from the centre of the disc, that is it stays outside the wheel body (79) and passes beyond the heads of the motor screws, which are 15.6 from the shaft."),
 ("H_collar_grub", "mm", "D_tip_iron + Cl_tip_iron", 8.5, "clutch - insert collar", "D",
    "How long the collar that carries the grub insert is. It follows from the LARGER of two constraints, and they are two different things asking for the same dimension.\n\nThe first is what the collar has to CONTAIN: the insert hole plus a wall above and one below, 6.65. The second is what it has to let THROUGH, and it is worth more: the soldering iron goes in horizontally, on the axis of the insert, and with the hole centred on the height of the collar the tip reaches half its diameter below that axis. If the collar is shorter than the tip, the tip ends up below the base of the collar and hits the ring that retains the tread, which is right there below and cannot be removed. Eight and a half, that is the tip with its clearance: the expression carries THIS constraint, which is the one that wins, and that the other is satisfied is stated by a check in solids_wheel.py. A single relation and a check can be read; a max() of two relations cannot - and the parameter editor does not even evaluate it.\n\nIt was Z_top_clutch - Free_collar_arm, the length the collar had when it HUNG below the hub: a dimension that, with the collar on top, no longer had anything to do with it."),
 ("Free_collar_arm", "mm", "0.3 mm", 0.3, "clutch - insert collar", "S",
    "How far the collar stays above the face of the arm. The collar comes down this far because the insert needs the height: above the tread there are only three millimetres, and the opening of the body and the roof of the compartment do not let the hub grow upwards."),
 ("Free_above_arm", "mm", "0.3 mm", 0.3, "collar - arm passage notch", "S",
    "How far the underside of the collar is set back ABOVE the arm, in the sector where the arm passes. It is not Free_collar_arm, which is another pair of faces - that of the grub collar on the clutch. It was needed and it was not there: the passage notch hollowed the collar from below and stopped exactly at z 0, which is the height of the top face of the arm (-Z_face_motor + Th_arm). The two faces stayed COPLANAR, that is the arm rubbed on the collar over 159 mm2 - and no check noticed, because two faces that touch have ZERO interpenetration and the audit measured exactly that: contact shows only by moving the arm with the part screwed on. Three tenths and not the two of the hub setback: at the pivot the two faces are concentric and turn one on the other, here instead the arm SWEEPS under them, and the ledge of the collar beyond r 79 is cantilevered. The setback starts at r = D_body/2 and no further in: up to there the collar rests on the face of the wheel body, and setting it back would mean lifting it off its seating plane."),
 ("Wall_below_insert_grub", "mm", "1 mm", 1.0, "clutch - insert collar", "S",

    "ASA wall below the insert tunnel. It is the thinnest in the joint: above the tunnel the hub continues solid for three millimetres, at the sides there is plenty of material, below this is what remains. More than a millimetre does not fit without raising the hub."),
 ("Z_base_collar_grub", "mm", "Z_plane_mid_disc + Th_clutch / 2 + H_shoulder_clutch", 11.0, "clutch - insert collar", "D",
    "Where the collar that carries the grub insert starts: right above the shoulder that retains the tread. It follows from the PLANE OF THE DISC and not from the height of the hub, because it is the disc that decides where the tread is, and everything else goes around it. Another cylinder between the shoulder and the collar, Ø44 and 2 tall, was removed: it did nothing except move the grub away from the tread and make the part longer."),
 ("Z_insert_grub", "mm", "Z_base_collar_grub + H_collar_grub / 2", 15.25, "clutch - insert collar", "D",
    "Height of the axis of the grub and of its insert, from the camera-side face of the body. It follows from the clearance to the arm, from the wall below and from the diameter of the insert hole: it is not chosen."),
 ("Cl_clear_grub", "mm", "0.4 mm", 0.4, "clutch - grub clearance hole", "S",
    "How much wider than the grub the hole beyond the insert is: the grub passes through it freely and only bites in the insert."),

 ("--- MOTOR 14HS10-0404S ---",),
 ("Side_motor", "mm", "35.2 mm", 35.2, "arm_plan", "R",
    "Side of the NEMA14 flange."),
 ("L_motor", "mm", "26 mm", 26.0, "pianta_scatola", "R",
    "Length of the motor body. It projects on the camera side, where there is room."),
 ("Cd_holes_motor", "mm", "26 mm", 26.0, "arm_plan", "R",
    "Centre distance of the four M3 fixing holes, in a square."),
 ("D_circle_motor", "mm", "22 mm", 22.0, "arm_plan", "R",
    "Diameter of the centring circle on the flange. It is this that centres the motor on the arm, not the screws."),
 ("H_circle_motor", "mm", "2 mm", 2.0, "arm_plan", "R",
    "Projection of the centring circle from the plane of the holes."),
 ("Cl_clutch_shaft", "mm", "0.15 mm", 0.15, "clutch - shaft hole", "S",
    "Sliding clearance between the hole in the clutch hub and the motor shaft. It was missing altogether: the hole was exactly D_shaft, that is the nominal of the shaft, and that hub has to SLIDE ON by hand and then be locked by the grub, not be forced onto ground steel. The eccentricity the clearance allows is at most half of it, 0.075, and against the travel of the arm - where one degree is worth a millimetre of TPU squash - it does not show. Hole compensation applies to the clutch as to any other printed hole."),
 ("D_hole_clutch", "mm", "D_shaft + Cl_clutch_shaft + Comp_hole_printing", 5.35, "clutch - drawn hole", "D",
    "The diameter with which the shaft hole is DRAWN: the nominal of the shaft, plus the sliding clearance, plus the print compensation. They were three dimensions that had become a single one, and the result was a hole that measured 4.8 as printed on a shaft of 5: the clutch would not go on."),
 ("D_mouth_hole_clutch", "mm", "D_hole_clutch + 0.6 mm", 5.95, "clutch - hole lead-in", "D",
    "Diameter of the lead-in at the mouth of the shaft hole, on the face from which the clutch slides on. It guides the hub as it goes down onto the shaft, and it is the practice the design uses on every hole."),
 ("H_leadin_hole_clutch", "mm", "(D_mouth_hole_clutch - D_hole_clutch) / 2", 0.3, "clutch", "D",
    "Depth of the lead-in: half the difference of the diameters, that is forty-five degrees."),
 ("D_shaft", "mm", "5 mm", 5.0, "clutch_section; arm_plan", "R",
    "Diameter of the motor shaft."),
 ("L_shaft", "mm", "20.5 mm", 20.5, "documentation - from the seating plane", "R",
    "Usable length of the shaft from the seating plane. It determines how much grip remains in the clutch hub."),
 ("Z_flat_shaft", "mm", "Flat_shaft - D_shaft / 2", 2.0, "clutch - plane of the flat", "D",
    "How far the plane of the flat is from the AXIS of the shaft. It is the design dimension of the flat, and until now it did not exist: in the solid it said 'Flat_shaft - radius of the DRAWN hole', which is something else - it mixes the flat of the shaft with the clearance and with the print compensation of the hole, and the plane of the hole ended up at 1.85 instead of 2.15, that is three tenths inside the shaft. It is the same confusion between design dimension and drawing dimension already found four times in this design; it showed in the slicer's section, not in any check."),
 ("Z_flat_hole", "mm", "Z_flat_shaft + (Cl_clutch_shaft + Comp_hole_printing) / 2", 2.175, "clutch - chord of the hole", "D",
    "Where the chord that cuts the shaft hole is drawn. It is the plane of the flat plus the same radial offset the round hole has - half the sliding clearance plus half the print compensation - so the plane of the hole is to the flat of the shaft as the wall of the hole is to its diameter. The chord follows from here: whoever changes the clearance or the compensation finds it moved by itself."),
 ("Flat_shaft", "mm", "4.5 mm", 4.5, "clutch - D-shaped hole on the shaft", "M",
    "Dimension on the flat of the motor shaft: the grub rests on it instead of on a round surface, and since the clutch hole has been a D the plane of the hole rests on it too. CONFIRMED on the motor of the reference build. Before, it was a CATALOGUE figure and not measured, and it was the only dimension on which it depended whether the clutch slides on: with the D-shaped hole the chord is 0.15 above the plane of the flat, so a flat shallower than 4.5 would have been tight."),
 ("D_grub", "mm", "3 mm", 3.0, "clutch - locking grub", "S",
    "Grub that locks the clutch on the shaft, pressing on the flat. It screws into a HEAT-SET INSERT, not into the ASA: the thread formed in the plastic strips and, under load, gives way over time, and a grub that loses its grip lets the clutch slip on the shaft without telling."),

 ("--- ARM ---",),
 ("Th_arm", "mm", "8 mm", 8.0, "arm_plan", "S",
    "Thickness of the arm. It has to house the two bearings in the pivot hub and stay entirely above the camera-side face so as not to meet the collar."),
 ("Cl_tip_iron_deep", "mm", "1.5 mm", 1.5, "pivot column - soldering iron channel", "S",
    "The clearance around the soldering iron tip when the channel is DEEP, in place of Cl_tip_iron which is half a millimetre. It serves the channel that goes down from the floor to the seat of the pivot insert: forty millimetres of channel with half a millimetre of clearance mean that the tip, going down, rubs on the wall for the whole travel and melts it. A short channel you enter and leave at once; a deep one you travel along."),
 ("D_channel_iron_deep", "mm", "D_tip_iron + Cl_tip_iron_deep", 9.5, "pivot column - soldering iron channel", "D",
    "The diameter of the deep soldering iron channel: Ø9.5 against the Ø8.5 of the short one. The channel stays open on the floor once assembly is finished, and a snap-fit plug closes it."),
 ("Z_top_arm", "mm", "2 mm", 2.0, "arm_plan - top face", "S",
    "Height of the top face of the arm: how far it stands above the camera-side face of the wheel body (z 0). Two, not zero: at zero the head of the pivot screw, under the washer, sat 1 mm inside the estimated envelope of the components on the board, and two millimetres up leave it 1 mm clear. Only the BODY of the arm rises: the plate the motor bolts to stays where the clutch chain puts it (Z_face_motor), so a step appears between the two on the edge of the motor square. The collar is hollowed where the raised arm passes."),
 ("Z_axis_spring", "mm", "-Th_flange_collar - (D_tip_iron + Cl_tip_iron)/2 - Free_iron_flange", -8.0, "axis of the preload spring", "D",
    "Height of the axis of the preload spring, and with it of the M4 insert, the grub, the cup and the boss. It is not chosen: the M4 insert is planted from inside, along its own axis, and the channel of the iron - D_tip_iron plus Cl_tip_iron - has to pass UNDER the front flange of the collar, which ends at -Th_flange_collar. Measured on the solid: at -4 the channel met 239 mm3 of flange 40 to 60 mm from the insert, at -7 still 7, at -8 nothing. It used to be the mid-plane of the arm; now the arm carries a tab below it for the spring to rest on."),
 ("Free_iron_flange", "mm", "0.75 mm", 0.75, "axis of the preload spring", "S",
    "Air between the channel of the soldering iron that plants the M4 preload insert and the underside of the collar's front flange. Three quarters of a millimetre: enough not to scorch the flange with a hot tip held by hand, and it puts the axis at a round -8."),
 ("L_screw_pivot", "mm", "20 mm", 20.0, "screw of the built-up pivot", "R",
    "Length under the head of the M3 screw that runs up through the pivot into its insert. Twenty, a catalogue length that is easy to find - chosen when the column of the pivot went up to the roof, instead of a 36 mm screw reaching an insert flush with it. The insert stays inside the column at Z_mouth_insert_pivot, which follows this length."),
 ("H_tab_spring_arm", "mm", "D_spring_out / 2 + 1 mm", 4.35, "arm - spring rest tab", "D",
    "How far below the spring axis the tab under the arm reaches, for the end of the spring to rest on. The spring works below the arm (Z_axis_spring against Z_bottom_arm), so the flank it used to rest on is not there any more: the tab puts it back, half the outer diameter of the spring plus a millimetre, so the whole end coil rests on a face."),
 ("L_chamfer_tab_spring_arm", "mm", "Z_bottom_arm - Z_axis_spring + H_tab_spring_arm", 6.35, "arm - chamfer of the spring tab", "D",
    "Legs of the 45 degree gusset that joins the spring tab to the underside of the arm, on the side away from the spring: it reinforces the tab without thickening it. As tall as the tab hangs below the arm, so the wedge runs from the tip of the tab to the underside of the arm: the tab is a cantilever pushed outwards by the spring, and the face away from the spring is the one in tension at the root."),
 ("Th_tab_spring_arm", "mm", "Dp_spigot_spring + 1.5 mm", 5.5, "arm - spring rest tab", "D",
    "Thickness of the tab under the arm, along the spring axis, from the face the spring rests on into the arm: the depth the spring spigot is buried in, plus a millimetre and a half of wall behind it."),
 ("Z_bottom_arm", "mm", "Z_top_arm - Th_arm", -6.0, "arm_plan - bottom face", "D",
    "The arm is raised, so its top face is at Z_top_arm and not at z 0. The BOTTOM face of the arm, the one towards the telescope: it is where the tip of the pivot emerges, where the bearing seat begins, where the washer rests and how far down the box skirt has to stay wide. It once coincided with -Z_face_motor: the arm was a plate of a single thickness and the motor was screwed to its bottom, so a single number served two things. Flipping the clutch, the motor went up and the plate became stepped, and the two things separated: seventeen places in the design read -Z_face_motor meaning THIS. Keeping them as one number made the audit look for the bearing seat at a height where the arm no longer is."),
 ("D_base_clutch", "mm", "2 * (Cd_holes_motor / 2 * sqrt(2) - D_head_screw_M3 / 2 - Cl_head_screw_clutch)", 29.67, "clutch - disc below the shoulder", "D",
    "The diameter of the clutch disc BELOW the tread shoulder. It was equal to D_hub_clutch, 44, and did not exist as a dimension of its own. Reduced to about 30 to stay clear of the screws, and written as a RELATION instead of by hand: the disc stops where the heads of the motor screws begin, that is at their diagonal minus half a head minus the clearance. It comes to 29.66, and if one day the motor changes centre distance or the screws change head, the disc follows them by itself.\n\nWhy shrink it instead of hollowing into it, which was the first route: measured, the two are equivalent in everything - same mass 11.2 g, same clearance 1.90 mm, same overhangs. But the groove leaves outside itself a ring 0.87 mm wide and one high, attached only at the top of the shoulder: a little fin that prints badly and breaks off. The step does not."),
 ("Cl_head_screw_clutch", "mm", "0.8 mm", 0.8, "clutch - disc below the shoulder", "S",
    "The RADIAL clearance between the bottom disc of the clutch and the heads of the motor screws. Not to be confused with Cl_head_clutch_z, which is the one in height: for a moment they were the same dimension through an oversight, and a diameter found itself inside a vertical clearance."),
 ("Cl_head_clutch_z", "mm", "1 mm", 1.0, "clutch - clearance above the screw heads", "S",
    "The clearance IN HEIGHT between the head of a motor screw and the bottom of the clutch. It is what decides how far the motor can rise, that is how low the machine can be: the motor rises until the heads touch the clutch. One millimetre and no less, because the clutch turns and the head is a bought part whose real height varies by a few tenths from one batch to another."),
 ("Cl_hole_screw_clutch", "mm", "0.3 mm", 0.3, "clutch - holes over the motor screws", "S",
    "Air per side between the socket head of a motor screw and its hole through the clutch (strategy C: the clutch goes in before the motor, and the four motor screws go in from above through it). It is a passage, not a fit: the head and the hex key go down through it once, with the clutch turned to line the holes up. Kept small because the hole already reaches into the dovetail of the TPU tyre."),
 ("Cl_head_screw_clutch", "mm", "0.8 mm", 0.8, "clutch - head notch", "S",
    "How much the notch in the bottom of the clutch stays wider than the head of the motor screw, per side. It is not a fit: the clutch TURNS and the heads stay still, so what passes over the notch changes at every turn and the clearance only serves not to graze them. Eight tenths take into account the fact that the real position of the screws depends on how the motor centred itself in its seat."),
 ("Th_plate_motor", "mm", "3.5 mm", 3.5, "arm_plan - motor plate", "S",
    "The thickness of the arm plate under the motor. It is NOT Z_face_motor, and the difference is the point: Z_face_motor says how far the motor face is below the reference plane, this says how much material there is. As long as the plate was equally thick everywhere the two coincided; since it grows upwards they separate. Upwards is possible because at the motor there is no collar - it is at r 86 and the motor at 97.5 - and above the plate there is only the clutch."),
 ("Th_min_plate_motor", "mm", "2.5 mm", 2.5, "arm_plan - motor plate", "S",
    "The minimum thickness the arm plate can have under the motor. It is compared with Th_plate_motor, which is the material actually there, and not with Z_face_motor, which only says where the face is. It is not a dimension that draws anything: it is a THRESHOLD, and it is here because Z_face_motor is no longer a choice and nobody would notice that the plate had become thinner. Every millimetre the motor rises - and that is a goal, because the lower machine is better - is a millimetre the plate loses. Two and a half is how much remains with the flipped clutch, that is the case is at the limit by construction: moving the grub higher the plate disappears, and the generator stops instead of producing an arm that gives way in the hand."),
 ("Z_face_motor", "mm", "Th_plate_motor + H_head_screw_M3 + Cl_head_clutch_z - Z_top_clutch", 1.5, "arm_plan - above the top face of the body", "D",
    "How far the seating face of the motor is above the camera-side face. It has followed three different things, and the three tell the reasoning. It was a CHOICE, 8 mm. Then, with the clutch flipped, it became the shaft's grip on the grub: the motor rose as much as needed for the shaft to reach the grub. Then the Ø44 cylinder above the shoulder was removed, the grub went down and that constraint loosened: the motor could have gone DOWN, that is the machine would have become taller again, and so it switched to following from the plate.\n\nNow it follows from the HEADS OF THE MOTOR SCREWS, and this is the true constraint: the plate grows above the z 0 plane, the heads rise with it, and above the heads is the bottom of the clutch. The motor rises until the heads touch the clutch. The loop is closed: the lower the machine the better, and the limit is there.\n\nMillimetres are gained in three ways, all three visible in the expression: a thinner plate (but it has a minimum), lower-head screws, or raising Z_top_clutch, that is starting the clutch hub higher - which is what removing the bottom disc did."),
 ("D_hub_pivot", "mm", "21 mm", 21.0, "arm_plan; collar_plan", "S",
    "Diameter of the hub around the pivot, on the arm and on the collar. It has to contain the bearing seat and their flanges, and stay outside the surface of the wheel body."),
 ("R_fillet_support_pivot", "mm", "3 mm", 3.0, "collar - groove between the pivot support and the band", "S",
    "Radius of the groove that blends the pivot support into the band of the collar. The support attached at a sharp edge had little surface in contact with the body, and it is also the point where the moment of the arm is discharged. Three millimetres is as much as the groove can widen while staying inside the collar sector and outside the arm passage; any larger and it would be cut by the notch, which is worse than not having it, because it would leave an edge halfway."),
 ("Z_mouth_insert_pivot", "mm", "Z_bottom_arm - Th_washer_pivot + L_screw_pivot + 0.5 mm", 12.0, "collar - mouth of the pivot insert seat", "D",
    "DERIVED: from the underside of the pivot washer, a screw of L_screw_pivot, plus the half millimetre of insert left above its tip - the same relation that made it 10 with the arm at -8. Raising the arm raises the mouth by as much, so the screw stays an M3 x 20, the easy one to buy. Height of the MOUTH of the seat of the M3 insert of the built-up pivot. It is no longer the top face of the support, which now rises up to Z_top_support_pivot: above this mouth there is the channel down which the soldering iron tip comes. Keeping it fixed at 10 is what leaves the screw a catalogue M3 x 20, whereas bringing it to the top of the support would have needed 26 mm under the head, that is a length that does not exist and that would stick out against the roof of the compartment. It is also the upper end of the screw: from under its head to the top of the hub there are 20.5 mm, that is a catalogue M3 x 20. It was written by hand in solids_body_collar as _z_cima = 10.0, and the screw - which was not in the model - could not follow from it."),
 ("Free_assembly_compartment", "mm", "2 mm", 2.0, "box - roof of the compartment; collar - top of the pivot support", "S",
    "How much has to be free between the contents of the mechanical compartment and the roof that closes it. It is not a tolerance: it is the clearance to SLIDE the box over the mechanism already assembled, which is how the machine is assembled, and the check that watches it was already there - but the number was written by hand inside it. Now the same parameter also decides how high the pivot support can rise, which is the tallest object in the compartment: raising it to half a millimetre from the roof, as had been done, the assembly check sounded at once."),
 ("Marg_top_support", "mm", "0.1 mm", 0.1, "collar - top of the pivot support", "S",
    "How much lower the top of the support stays than the minimum the assembly clearance imposes. One tenth, and it is in the PART: building the top exactly at the limit, the clearance comes out at a round 2.00 and the compartment check - which compares two measurements taken on the solids - reads it back a hair below and sounds on a correct part. Widening the check's threshold instead would have covered the truly insufficient clearances too. Same reason as Marg_ang_side_support."),
 ("Z_top_support_pivot", "mm", "Z_shoulder_box + Th_walls_box / 2", 26.75, "collar - top of the pivot support", "D",
    "The support is a FULL COLUMN that runs into the roof: its top is half a wall inside the roof slab, so column and roof fuse into one. Above the insert only the channel of the iron goes down, from the hole in the roof. REJECTED earlier, when the support stopped short of the roof: a free-standing support 20 mm tall (from 9.8, for more surface in contact with the body) did not fit - at 16 it closed the compartment, whose roof had been LOWERED by ten millimetres on purpose to lighten the box. That stand-alone version reached 13.7, its top two millimetres below the roof, the clearance to slide the box over the mechanism already assembled."),
 ("--- BUILT-UP PIVOT AND WASHER ---",),
 ("D_access_iron_pivot", "mm", "D_channel_iron_deep", 9.5, "box+collar - access to the pivot seat", "D",
    "The hole in the roof of the mechanical compartment, on the pivot axis. It is NOT access for the pivot SCREW, as it was first described, on the belief that the screw entered from the telescope side - the head of that screw is at the BOTTOM, under the washer, and the screw goes up into the insert at the top of the hub. It is not the screw that passes through the roof: it is the TIP OF THE SOLDERING IRON that plants the insert, and for that the right diameter is that of the deep channel, not that of the head of an M3.\n\nBefore the merge the insert was planted with the collar bare, from above, and the channel ended in air; now there is the roof above, and the channel has to cross it."),
 ("D_access_driver_pivot", "mm", "D_head_screw_M3 + 2.5 mm", 8.0, "box+collar - access to the pivot screw", "D",
    "The hole in the FLOOR, on the pivot axis, through which the screwdriver reaches the head of the pivot screw. The screw is driven from below - its head is under the washer, some twenty millimetres from the floor - and with the box closed that is the only way. It follows from the screw head and not from the screwdriver, because it is the head that has to pass while the screw is lowered into position.\n\nThe hole stays open once assembly is finished and a snap-fit plug closes it: it is a hole in the resting plane, that is the face through which dust gets in."),
 ("D_clear_screw_pivot", "mm", "D_holes_M3 + Comp_hole_printing", 3.4, "collar - hole for the screw inside the pivot", "D",
    "Hole that runs lengthwise through pivot and hub. It is a wide PASSAGE, not a fitted hole: on the 5 pivot it leaves 0.8 mm of wall per side, that is two perimeters, and a screw forced in there would split it instead of reinforcing it. The screw must not touch the plastic at its side: it works in tension between the insert at the top and the washer at the bottom."),
 ("Dp_seat_insert_M3_pivot", "mm", "L_insert_M3 + 0.5 mm", 3.5, "collar - seat of the insert at the top of the hub", "D",
    "Depth of the insert seat, at the top of the hub. Half a millimetre more than the insert, for the same reason as the M4 seat of the grub: flush, the insert would push the molten plastic to the bottom instead of letting it flow back."),
 ("D_leadin_insert_M3", "mm", "D_hole_insert_M3 + 0.6 mm", 5.25, "collar - lead-in of the seat", "D",
    "Diameter of the flared mouth above the seat of the M3 insert."),
 ("Dp_leadin_insert_M3", "mm", "0.8 mm", 0.8, "collar - lead-in of the seat", "S",
    "Depth of the conical chamfer at the mouth of the M3 insert seat."),
 ("D_washer_pivot", "mm", "D_ring_in_bearing - 0.4 mm", 6.6, "pivot_washer", "D",
    "Outer diameter of the printed washer. It sits under the inner ring of the bearing and must press ONLY on that: four tenths less than the ring keep it away from the shield, and it still stays much narrower than the hole of the flange, which belongs to the outer ring."),
 ("D_hole_washer_pivot", "mm", "D_holes_M3_printed", 3.4, "pivot_washer", "D",
    "Hole of the washer: clearance for the shank of the screw, and it is the same drawn M3 clearance hole as all the others. It was D_clear_screw_pivot + 0.2: since the passage inside the pivot carries the print compensation, that +0.2 would have counted it twice. It was found by the expression check."),
 ("L_bushing_pivot", "mm", "H_bearings + Th_flange_bearing", 9.0, "pivot_washer - bushing inside the bearings", "D",
    "Length of the Ø5 bushing printed on the pivot washer, the sleeve the two F695ZZ turn on: washer and bearing sleeve are one part (it used to be the pin of the collar). From the top of the washer to the floor of the spot face in the collar: the screw closes the stack on the bushing and not on the bearings, so this length is what keeps the inner rings from being squeezed. The generator stops if it does not match the gap it has to fill."),
 ("Ch_bushing_pivot", "mm", "0.4 mm", 0.4, "pivot_washer - lead-in of the bushing", "S",
    "Lead-in at the top of the bushing, 45 degrees: the end that has to find the bore of two bearings held in the other hand."),
 ("Th_washer_pivot", "mm", "2.5 mm", 2.5, "pivot_washer", "S",
    "Thickness of the washer. Two and a half make it printable and put the screw head at a height such that a catalogue M3 x 20 engages the insert without breaking through the hub."),
 ("D_head_screw_M25", "mm", "4.5 mm", 4.5, "bought - heads of the M2.5 screws", "R",
    "Diameter of the head of the M2.5 screws, SOCKET HEAD in the reference build: standard dimension of the DIN 912 cylindrical head, from the catalogue and not from the caliper. They are the two screws that hold the sensor cover."),
 ("H_head_screw_M25", "mm", "2.5 mm", 2.5, "bought - heads of the M2.5 screws", "R",
    "Height of the socket head of the M2.5 screws, DIN 912. It is used to see whether room for the key remains above the head, which is the defect that an unmodelled screw does not reveal."),
 ("D_head_screw_M2", "mm", "3.8 mm", 3.8, "bought - heads of the M2 screws", "R",
    "Diameter of the head of the M2 screws, COUNTERSUNK in the reference build: standard dimension of the DIN 7991 conical head, from the catalogue. The countersunk head is not a cosmetic detail - it disappears into the thickness instead of resting flat, so it wants the conical lead-in in the part and changes the geometry around the hole."),
 ("H_head_screw_M2", "mm", "1.2 mm", 1.2, "bought - heads of the M2 screws", "R",
    "Height of the M2 countersunk head, that is the depth of the cone. It is also how far the lead-in must go down into the part for the screw to end flush."),
 ("D_head_countersunk_M2", "mm", "3.8 mm", 3.8, "bought - countersunk heads", "R",
    "Diameter of the M2 conical head, DIN 7991. It is the same number as D_head_screw_M2 because the M2 screws of the reference build are countersunk: it is here all the same, spelled out, because the head type and the size must be able to change one without the other."),
 ("H_head_countersunk_M2", "mm", "1.2 mm", 1.2, "bought - countersunk heads", "R",
    "Depth of the cone of the M2 countersunk head, DIN 7991."),
 ("D_head_countersunk_M25", "mm", "4.7 mm", 4.7, "bought - countersunk heads", "R",
    "Diameter of the M2.5 conical head, DIN 7991."),
 ("H_head_countersunk_M25", "mm", "1.5 mm", 1.5, "bought - countersunk heads", "R",
    "Depth of the cone of the M2.5 countersunk head, DIN 7991."),
 ("D_head_countersunk_M3", "mm", "6 mm", 6.0, "bought - countersunk heads; panel", "R",
    "Diameter of the M3 conical head, DIN 7991. It is NOT D_head_screw_M3: that one is the socket cap head, 5.5, and is still needed for the pivot screw, from which the step of the inner skirt derives. They are two different screws and must remain two different dimensions, otherwise changing the head of the panel screws would move the skirt."),
 ("H_head_countersunk_M3", "mm", "1.65 mm", 1.65, "bought - countersunk heads; panel", "R",
    "Depth of the cone of the M3 countersunk head, DIN 7991. With it the countersink in the panel is (D_head_countersunk_M3 - D_clear_screw_panel) / 2 deep on a 90-degree cone, that is 1.3 mm: in the screw area the panel is 5 thick, so 3.7 mm of material remain below the countersink."),
 ("D_clear_screw_panel", "mm", "3.4 mm", 3.4, "board_panel", "S",
    "Clearance hole of the M3 in the panel. It was 3.4 hand-written inside the generator, as radius 1.7: here it becomes a dimension, because the depth of the countersink derives from it."),
 ("Ang_head_countersunk", "deg", "90 deg", 90.0, "bought - countersunk heads", "R",

    "Included angle of the cone of the countersunk heads, ninety degrees as the metric standard requires. It is the figure that makes the difference between a lead-in that receives the head and one that leaves it protruding."),
 ("D_head_screw_M3", "mm", "5.5 mm", 5.5, "bought - heads of the M3 screws", "R",
    "Diameter of the head of the design's M3 screws. The SOCKET head is the one used in the reference build, so the diameter is the standard one of the DIN 912 cylindrical head: from the catalogue and not from the caliper, and that is the reason for class R. A slotted or cross head would be wider, about 6 mm, and from here derives the step that the inner skirt carves around the pivot. It was hand-written as 2.75 radius inside solids_assieme, and for the pivot screw it was not there at all: the skirt stopped twelve millimetres lower for the sake of an envelope the model did not contain, and what the model does not contain no check can see."),
 ("H_head_screw_M3", "mm", "3 mm", 3.0, "bought - heads of the M3 screws", "R",
    "Height of the head of the M3 screws, from the catalogue for DIN 912. On the pivot screw, under the washer, it brings the lowest point of the stack to -13.5: it is the number that was written in the comment of Z_skirt_inner."),
 ("L_screw_motor", "mm", "8 mm", 8.0, "bought - motor screws", "R",
    "Length under the head of the four M3 socket screws that hold the motor to the arm plate: an M3 x 8, a catalogue length that is easy to find. The head stands on the top of the plate (Z_face_motor is derived from exactly that), so the shank crosses Th_plate_motor and goes L_screw_motor - Th_plate_motor = 4.5 mm into the motor. Drawing the screw from a literal z 0 - the top of the plate only while the plate was 8 thick - put the head inside the plate once the step appeared: hence the derivation."),
 ("L_band_arm", "mm", "18 mm", 18.0, "arm_plan", "S",
    "Width of the arm band between the pivot hub and the motor plate. It does not follow the hub: taking it to 21, the outer edge would hit the boss of the spring seat in the box."),
 ("L_plate_solid", "mm", "L_arm", 61.33, "arm_plan", "S",
    "How far the plate stays as wide as the motor, measured from the centre of the motor towards the pivot. Below it there is in any case the cut of R_rim_inner, which makes the inner side by itself: what this parameter governs is the outer side. Brought to Side_motor / 2, the wide part is only the square of the motor and the arm goes back to being the wedge it was before. The wedge had two defects. The spring rested on it on a ramp inclined 15 degrees to its own axis, so it pressed edge-on, with a good six newtons of the 22.3 pushing it to slide along the side: only the spigot held it. And stopping the wide part halfway does not solve it, because the step between the ramp and the straight side is a re-entrant corner right where the spring pushes. Keeping it for the whole length, the side is a single straight line, perpendicular to the spring axis, without steps, and the arm gains a gram and a half of section where the moment is greatest."),
 ("Squash_clutch", "mm", "0.4 mm", 0.4, "arm travel - working point", "S",
    "How much the TPU ring must be squashed against the disc for the clutch to drive. It is the working point, and until now it did not exist: Cd_motor equals R_disc + D_clutch / 2 to the thousandth, that is at rest the ring is exactly TANGENT to the disc and does not push. Where the arm would really stop was decided by the spring against the rubber, and it was not written anywhere. Four tenths are 20% of the two millimetres of rubber: enough to have grip, little enough not to cook the ring. Whoever fits a harder TPU should lower it."),
 ("Wear_TPU_allowed", "mm", "1 mm", 1.0, "arm travel - how much wear to follow", "S",
    "How much rubber the mechanism must be able to wear away while still pushing as on the first day. The spring takes care of it by itself, provided the arm is FREE to rotate: one millimetre is half the radial thickness of the ring. It is not a number of convenience: it is what says how much space is needed between the arm and the collar, and until now that space was a leftover, not a choice. One degree is worth about one millimetre, so every tenth asked for here is a tenth of a degree to free up."),
 ("Marg_travel_arm", "mm", "0.4 mm", 0.4, "arm travel - eccentricity and tolerances", "S",
    "How much to add to the travel for the things that cannot be controlled: the eccentricity of the bought disc, which makes the arm oscillate at every turn, and the printing tolerance of the parts that decide the centre distance. Without it, the travel would suffice on paper and not on the bench."),
 ("Approach_travel_arm", "mm", "Squash_clutch + Wear_TPU_allowed + Marg_travel_arm", 1.8, "arm travel", "D",
    "How far the clutch must be able to go into the disc, adding up working point, wear to follow and margin. It is the figure from which the negative end of the travel derives, and therefore how wide the passage of the arm in the collar must be."),
 ("Open_travel_arm", "mm", "1.5 mm", 1.5, "arm travel - end stop on the spring side", "S",
    "How far the clutch can come away from the disc before an end stop halts it. There is no need to go further, and this was verified on the assembly instead of assumed: the box is not lowered along the axis - lifting it by half a millimetre it interpenetrates the collar by 199 mm3 - but slid in by running its six ears astride the two flanges of the collar, and that movement never touches the arm; the arm in turn is fitted afterwards, lowering it onto the pivot from below, and it slides off freely for twenty millimetres with box and collar already in place. At no moment of the assembly does it need to be opened more than this. The limit is needed though, because on that side the arm is free until the clutch hits the box, at +5.29 degrees measured, and nothing stops it."),
 ("Cl_passage_arm", "mm", "1 mm", 1.0, "collar - arm passage recess", "S",
    "How much wider the collar recess is around what the arm sweeps, over its whole travel. The recess is there to let the arm through, but its dimensions were hand-written and did not derive from the travel: that is why at -1.5 degrees the arm touched the flange."),
 ("D_spring_out", "mm", "6.7 mm", 6.7, "spring - outer diameter; MEASURED", "M",
    "Outer diameter of the preload spring, MEASURED with the caliper on the spring of the reference build: 0.9 wire, 6.7 outside, 13.5 free - taken from a clothes peg. REJECTED: an 8.9 x 19.8 spring of unrecorded origin, and two 0.7 x 7 x 20 springs stacked one above the other, which took the spring tab 3 mm lower and left the arm no clean way in. The number was already in the design, but it lived only inside the description of D_spigot_spring: not being a dimension, nothing could depend on it. It is needed here because it decides WHERE the spring touches the side of the arm, and therefore how far the side must stay straight: the footprint goes from Att_spring - 4.45 to Att_spring + 4.45, that is from 23.15 to 32.05."),
 ("Marg_nose_spring", "mm", "1 mm", 1.0, "arm_plan - how far the nose stays from the spring", "S",
    "How far BEFORE the start of the spring footprint the nose of the side closes. It is not generic caution: the nose is curved, and a spring resting astride the tangency point would go back to pressing edge-on, which is exactly the defect for which L_plate_solid was brought to full length. One millimetre keeps the tangency outside the footprint even if R_rest_spring_arm shifts by a few tenths."),
 ("L_nose_arm", "mm", "Att_spring - D_spring_out / 2 - Marg_nose_spring", 23.25, "arm_plan; arm", "D",
    "Length of the nose that blends the pivot hub into the side of the plate, measured from the pivot along the arm. Before, there was a SHARP STEP of 7.1 mm there: the hub is r 10.5 and the plate is 17.6 wide, and the two met at an edge. On the outer side the whole step was visible; on the inner one the cut of R_rim_inner left its tip, and it is the tip that could be seen sticking out at the top left in the plan view. Now the two blend with two tangent arcs - horizontal tangent to the hub, tangent to the straight side - and the side reaches the plate without edges. The length is dictated by the spring, not by looks: the nose must close before the spring starts resting on it, otherwise the spring goes back to pressing on a curved surface."),
 ("R_edges_plate_motor", "mm", "2.5 mm", 2.5, "arm_plan; arm", "S",
    "Radius of the two outer corners of the motor plate, the ones that on the fitted part stick outward and get knocked when handling it. Two and a half is a choice of shape, not an imposed maximum: the real limit is much further. The M3 holes of the motor seem to be the constraint but they are not - the point of a hole closest to the corner tip is 4.91 mm away, and the fillet recedes along the diagonal only by R*(sqrt(2)-1), so it would start eating into the hole just beyond R 11.8, where it would be a different shape anyway and not a fillet. The number was verified by deliberately breaking the part: at R 6 the check on the holes was rightly silent, and that is how it was seen that the limit written here before, 3.47, was wrong - it was a coordinate of the hole, not a distance."),
 ("D_seat_bearings_printed", "mm", "D_seat_bearings + Comp_hole_printing", 13.2, "arm_plan - drawn seat", "D",
    "The diameter with which the bearing seat is DRAWN. The design one remains D_seat_bearings: this is it plus the print compensation, as has always been done with the magnet hole. The two dimensions had become the same number, and the printed seat measured two tenths less than the bearing: not a light interference fit - which is what is needed, because the outer ring must not turn in the plastic - but ten times that. On a 13 ring that is enough to jam the balls - the bearings had to be forced in - and a bearing that turns stiffly cancels the reason it is there: the arm must stay free to follow the wear of the TPU. CONFIRMED BY HAND on an arm printed in ASA: the bearings slide in JUST RIGHT and the arm rotates well without play - it stays where you leave it, does not wobble and does not slide. It is the proof that the compensation had to be added: before, the two dimensions had become the same number and the printed seat came out two tenths tight. As for the collar groove, it remains a FIT test by hand and not a caliper reading, so the parameter does not change class; but now it is known that it works, and whoever touches it should redo the test."),
 ("D_mouth_seat_bearings", "mm", "D_seat_bearings_printed + 0.6 mm", 13.8, "arm_plan - lead-in of the seat", "D",
    "Diameter of the lead-in at the mouth of the bearing seat, on BOTH faces of the arm: the bearings go in one per face, with the flanges staying outside. Without a lead-in the bearing must enter flat into a seat eight millimetres deep, and what feels like a tight seat is partly just the entry."),
 ("H_leadin_seat_bearings", "mm", "(D_mouth_seat_bearings - D_seat_bearings_printed) / 2", 0.3, "arm_plan", "D",
    "Depth of the lead-in, equal to half the difference of the diameters: forty-five degrees, the practice the design uses on all holes."),
 ("D_seat_bearings", "mm", "13 mm", 13.0, "arm_plan - 2 x F695ZZ", "R",
    "Seat for two stacked flanged F695ZZ bearings, outer diameter 13. They are the ones used in the reference build. The 608ZZ was rejected: with its outer diameter of 22 the hub would go to 30 and end up inside the wheel body."),
 ("D_pivot_arm", "mm", "5 mm", 5.0, "collar_plan; arm_plan", "R",
    "Diameter of the pivot that comes out of the collar: it is the bore of the F695ZZ. The two bearings slide on here, with the flanges facing outward. CONFIRMED BY HAND on a collar printed in ASA: the bearing FITS PERFECTLY on the pivot. It is the first time that fit has been tested on the real part, and it indirectly confirms the machine compensation in a case that had never been verified: the pivot is a SHAFT, not a hole, so the compensation eats into it instead of enlarging it."),
 ("H_bearings", "mm", "8 mm", 8.0, "arm_plan", "R",
    "Overall height of the two bearings, 4 mm each. The flanges stay outside the seat, on the two faces of the hub, and give the axial reference: the bearings space themselves."),
 ("D_in_flange_bearing", "mm", "10.5 mm", 10.5, "bearing F695ZZ - measured with the caliper", "M",
    "Inner diameter of the flange, that is the bore of the OUTER ring. It is the passage the washer must go through to reach and touch the inner ring: below this diameter it passes, above it presses on the outer ring and the bearing locks. The 10.5 was born as a cautious estimate and was confirmed with the caliper on the bearings of the reference build."),
 ("D_ring_in_bearing", "mm", "7 mm", 7.0, "bearing F695ZZ - measured with the caliper", "M",
    "Outer diameter of the INNER ring, the one that turns together with the pivot. It is the largest diameter on which a washer can press without touching the shield. Born as a cautious estimate, confirmed with the caliper: 7.0. The bore, 5.0, also confirms the pivot."),
 ("D_flange_bearing", "mm", "15 mm", 15.0, "collar - spot face of the hub", "M",
    "Diameter of the flange of the F695ZZ, measured with the caliper. It was a standard taken on trust, now it is a measured figure: and it is what says how wide the spot face in the collar hub must be."),
 ("Th_flange_bearing", "mm", "1 mm", 1.0, "collar - spot face of the hub", "M",
    "Thickness of the flange, measured with the caliper. It sets how deep the spot face must be: the flange must rest ON it, not be squashed into it. The body-side flange sticks out by that much from the face of the arm hub, and without the spot face it ended up inside the collar hub - 157 mm3 of interpenetration, which is the volume of the whole flange."),
 ("D_spotface_hub", "mm", "D_flange_bearing + 0.4 mm", 15.4, "collar", "D",
    "Diameter of the spot face on the pivot hub of the collar: two tenths per side around the flange, as everywhere in the design."),
 ("Setback_face_hub", "mm", "0.2 mm", 0.2, "collar", "S",
    "How far the face of the collar hub is set back from the face of the arm hub, so as NOT to touch it. The arm really rotates on that joint, under the preload of the spring, and ASA against ASA means friction and dust exactly where it must move freely. Set back by two tenths, only the smooth steel of the flange is left rubbing - which is what H_bearings says: the flanges are the axial reference, not the printed faces."),
 ("D_seat_centring", "mm", "D_circle_motor + 0.2 mm", 22.2, "arm_plan", "D",
    "Seat in the arm for the circle of the motor, with two tenths of clearance."),
 ("H_seat_centring", "mm", "H_circle_motor + 0.2 mm", 2.2, "arm_plan", "D",
    "Depth of the centring seat."),
 ("Th_min_floor_seat_centring", "mm", "1 mm", 1.0, "arm_plan - floor of the centring seat", "S",
    "Thinnest floor the centring seat may leave above the hub of the motor before it has to go through the plate instead. With the plate at 3.5 and the hub 2 tall the floor is 1.3. Under a millimetre it is a membrane that the four motor screws would crack when tightened - with a floor of 0.4 the seat has to go through the plate."),
 ("D_fillet_hub_motor", "mm", "23 mm", 23.0, "arm_plan", "M",
    "Diameter reached by the FILLET at the root of the motor's centring hub. Measured on the manufacturer's model, and the measurement contradicts the drawing that would come to mind: the hub is not a clean 22 cylinder. In the first half millimetre from the flange it widens up to 23, then stays cylindrical at 22 for one millimetre - which is the whole band that actually centres - and ends with a lead-in chamfer at 21. Without this number the seat at 22.2 hits the fillet and the motor sits two tenths raised, on the fillet instead of on the flange: 1.7 mm3 of interpenetration measured."),
 ("H_fillet_hub_motor", "mm", "0.5 mm", 0.5, "arm_plan", "M",
    "How tall that fillet is, again measured on the manufacturer's model. From here down starts the 22 cylindrical band that does the centring, and it is one millimetre tall: it is the reason why the lead-in cannot be as deep as one likes, otherwise the seat stops engaging it."),
 ("D_mouth_seat_centring", "mm", "D_fillet_hub_motor + 0.4 mm", 23.4, "arm_plan", "D",
    "Diameter of the lead-in at the mouth of the centring seat. It clears the fillet, leaving it the same two tenths per side that the seat leaves the hub."),
 ("H_leadin_seat_centring", "mm", "(D_mouth_seat_centring - D_seat_centring) / 2", 0.6, "arm_plan", "D",
    "Depth of the lead-in, equal to half the difference of the diameters: that is forty-five degrees, which is the practice the design already uses on all holes. Besides clearing the fillet, it guides the hub while the motor goes down into its seat."),
 ("D_clear_shaft", "mm", "7 mm", 7.0, "arm_plan", "S",
    "Hole in the arm for the shaft to pass through."),
 ("D_holes_M3_printed", "mm", "D_holes_M3 + Comp_hole_printing", 3.4, "arm_plan - drawn hole", "D",
    "The diameter with which the CLEARANCE holes of the M3 screws are drawn. The design one remains D_holes_M3: this is it plus the print compensation. Without it, the printed hole measured 3.0 and the screw rubbed inside it - and on the four motor screws that is not a nuisance but a defect, because the motor must be centred by its Ø22 hub and not by the screws."),
 ("D_holes_M3",            "mm", "3.2 mm",    3.2,  "arm_plan", "S",
  "Through holes for the motor screws."),
 ("Cl_rim_inner", "mm", "1 mm", 1.0, "arm_plan", "S",
    "Minimum distance between arm and body surface."),
 ("R_rim_inner", "mm", "D_body / 2 + Cl_rim_inner", 80.0, "arm_plan", "D",
    "Radius on which the inner edge of the arm is cut."),
 ("Att_spring", "mm", "L_arm * 0.45", 27.60, "arm_plan; collar_plan", "D",
    "Distance of the spring attachment from the pivot. Together with the pivot offset it determines how much force the spring needs to obtain the desired preload."),
 ("D_washer_spring", "mm", "10 mm", 10.0, "assembly_plan - envelope with which the spring is drawn", "S",
    "Diameter with which the spring is DRAWN in the assembly views. It is not a part: there are no spring washers, the spring rests on one side on the side of the arm plate and on the other at the bottom of the box seat. The name has already misled once - the construction circle that marked the spring attachment was taken for a real washer and became a cylinder of material in the solid, in a place the spring does not reach."),

 ("--- COLLAR ---",),
 ("Ang_collar_pivot",    "deg","110 deg",  110.0, "collar; flat_gasket", "S",
  "Angular extent of the collar on the pivot side. The 110 degrees of the base served to support the ELECTRONICS COMPARTMENT, which reached 108: that compartment no longer exists since the electronics moved into the motor compartment, and the dimension was left orphaned of its reason. What the collar must still reach on this side is the last thing it carries: front ear B at 71 degrees and the end of the box at 71.9, plus the material around the boss of its insert. Whoever changes it should look at those two angles, not at this number."),
 ("Ang_collar_opposite",  "deg","52 deg",   52.0,  "collar; flat_gasket", "S",
  "Angular extent of the collar on the side opposite the pivot."),
 ("Cl_groove_collar", "mm", "0.5 mm", 0.5, "collar - inner face of the front flange", "S",
    "How far the inner face of the FRONT flange is set back from the wheel body, so as not to touch it. The collar groove was drawn at 23.00, that is EXACTLY the height of the body: zero play on a printed part, the same defect as the clutch hole that was the exact diameter of the shaft. On a printed collar the groove measures 22.8 on average and 22.3 on the support crests - that face is born on the supports and has excess material hanging into the groove - so the collar gripped the body with two tenths of interference, seven on the crests, and that is why it strained to snap on. Half a millimetre covers the average with margin; the crests, which are support leftovers, are removed with a scrape. The collar is located by the REAR flange, which is a clean face: it is born above the flat bottom and the supports never see it. The squash of the gasket does not change, because the bottom of its groove stays where it was. CONFIRMED BY HAND: a collar reprinted in ASA slides onto the wheel body with the RIGHT RESISTANCE. Before this half millimetre the collar was tight, because the groove was 23.00 - exactly the height of the body - and that face is born on the supports. The confirmation is worth what it is: a fit test by hand, not a caliper reading, so the parameter stays CHOSEN and does not become measured; but now it is known that it works, and whoever changed it would have to redo the test."),
 ("Th_collar", "mm", "7 mm", 7.0, "collar_plan; collar_section", "S",
    "Radial thickness of the cylindrical band of the collar."),
 ("R_out_collar", "mm", "D_body / 2 + Th_collar", 86.0, "collar_plan", "D",
    "Outer radius of the collar."),
 ("L_groove_gasket", "mm", "3 mm", 3.0, "collar_section; sviluppo_guarnizione", "S",
    "Width of the groove that houses the foam gasket."),
 ("Dp_groove_gasket", "mm", "1.5 mm", 1.5, "collar_section", "S",
    "Depth of the groove. The 3 mm gasket compresses into it."),
 ("Halfarc_seal", "mm", "62 mm", 62.0, "sviluppo_guarnizione; pianta_scatola", "S",
    "Half-span of the sealing perimeter, a legacy of the first radial architecture. Today the seal is flat."),
 ("D_screws_collar", "mm", "4 mm", 4.0, "collar_plan", "S",
    "Collar screws, no longer used since it screws onto the existing M3 screws."),

 ("R_gasket", "mm", "72 mm", 72.0, "flat_gasket; collar", "S",
    "Radius of the centre line of the flat gasket, identical on the two faces. It lies inside the M3 screws and below the bottom of the slot: the face it presses on must be solid, and beyond the bottom of the slot it no longer is."),
 ("--- THE SENSOR CABLE AND ITS OPENING ---",),
 ("D_cable_sensor_measured", "mm", "5.6 mm", 5.6, "CAT5 cable - MEASURED with the caliper", "M",
    "Outer diameter of the CAT5 of the reference build. Before, the design had 6, which was a cautious estimate taken from the catalogue range 5÷6: the channel on the bracket is sized on that and is left as it is, because a cable squashes but does not get thinner and the extra half millimetre does no harm. This number instead is needed where the clearance really matters, that is in the opening and in the bend radius."),
 ("R_curvature_min_cable", "mm", "4 * D_cable_sensor_measured", 22.4, "cable - TO BE CONFIRMED on the datasheet", "D",
    "Minimum bend radius of the cable. Four times the outer diameter is the rule commonly given for installed 4-pair UTP, but it is a CATEGORY rule and not the datasheet of the cable in use: here it counts as a declared constraint still to be confirmed, not as a certainty. The number is not academic - a 90-degree bend with this radius takes up 22.4 mm in each of the two directions, and inside the box there is little room."),
 ("Ang_opening_cable_box", "deg", "Ang_bracket_sensor + (Ang_screw_B - Ang_screw_A) / 2", 50.0, "BOX - cable slot in the roof", "D",
    "Where the cable crosses the roof of the compartment: in line with the arm of the bracket that carries the cable clamp, so the cable goes down in a single plane and does not also bend sideways. Bending sideways while going down, at 48 degrees, the minimum radius stayed two tenths below its limit. The free corridor goes from the pillar of ear B (up to 26) to that of ear C (from 61)."),
 ("R_opening_cable_box", "mm", "107 mm", 107.0, "BOX - cable slot in the roof", "S",
    "The bottom of the cable slot: the centre of its rounded end. The slot is OPEN on the inner edge of the roof, at r 86, so that the cable enters it sideways with the connector already wired, instead of having to be threaded through a hole. It is long because the cable cannot go down vertically: passing over the paddle of the bracket it needs 22 mm of radius, and it crosses the roof obliquely at r 107 (solids_cables.py): the bottom of the slot is there."),
 ("Room_opening_cable", "mm", "2.4 mm", 2.4, "BOX - cable passage in the roof", "S",
    "How much wider the opening is than the cable. It is not the clearance of a fit: the cable CROSSES the opening at a slant, it does not sit still inside it. The roof is 2.5 thick and the cable cuts through it at an angle, so in the direction of travel it sees an opening shorter than it is wide: two millimetres and four tenths of room let a cable inclined up to 45 degrees through without it touching the edge."),
 ("D_opening_cable_box", "mm", "D_cable_sensor_measured + Room_opening_cable", 8.0, "BOX", "D",
    "Width of the cable slot: the cable diameter plus the room, and NO print compensation. Before, it had it, and it was a wrong link: the compensation serves to make a FIT come out right, and here there is no fit - there is a Ø5.6 cable passing through a slot with 2.4 mm of room, that is 43% of its diameter, where one or two tenths change nothing. That useless link did damage: raising the compensation to 0.25 to correct the shaft hole, the slot went to 8.25 and a boolean silently EMPTIED half the box - only the fillet check noticed, because it no longer found the edge between head and back."),
 ("Ch_opening_cable", "mm", "1 mm", 1.0, "BOX - edges of the opening", "S",
    "Chamfer of the opening, on both faces. It is not cosmetic: a cable resting on a sharp edge of printed ASA wears there and gets stripped after months, not on assembly day. On both sides because the cable touches above going in and below coming out, depending on how it has settled."),

 ("D_cable_motor", "mm", "5 mm", 5.0, "motor cable - MEASURED", "M",
    "Diameter of the bundle of the four motor wires. Measured, they are around 4.5; here there is 5 because they get a sleeve, and the sleeve is what then passes through the holes."),
 ("D_cable_supply", "mm", "5.8 mm", 5.8, "supply cable - MEASURED", "M",
    "Diameter of the 12 V cable, from the GX12 to the driver."),
 ("R_curvature_min_cable_supply", "mm", "4 * D_cable_supply", 23.2, "12V cable - TO BE CONFIRMED", "D",
    "Minimum radius of the supply cable, with the same criterion and the same caveat as the CAT5: four times the diameter is a category rule, not the datasheet of this cable."),

 ("--- GASKETS PRINTED IN TPU ---",),
 ("Shore_gasket", "", "95", 95.0, "gaskets - TPU of the reference build", "S",
    "Hardness of the TPU the gaskets are printed with, in Shore A. Ninety-five is the TPU of the reference build and it is also the easiest to print: below 85 the filament struggles to pass through a Bowden (indirect-drive) extruder. It is a default, not a constant: whoever has a softer TPU gets the same seal with less force and can raise the squash, whoever has a harder one must lower it. The number is here so that whoever changes it knows they must redo the closing-force calculations, not for show."),
 ("L_gasket", "mm", "L_groove_gasket - 0.2 mm", 2.8, "gaskets", "D",
    "Width of the gasket. Two tenths less than the groove: it slips in by hand without forcing and without rattling. It is not made to the exact size because printed TPU comes out a few hundredths oversize, and a gasket that has to be forced in twists in the groove instead of lying flat in it."),
 ("H_gasket", "mm", "2 mm", 2.0, "gaskets", "S",
    "Total height of the gasket at rest. The groove is 1.5 deep, so it protrudes by half a millimetre: it is that half millimetre that gets squashed on closing, that is 25% of the height. On a hollow profile 25% is sealing compression; on a solid bead it would be 50%, which on TPU 95A would require a disproportionate force - paid for by the collar, which is ASA, and discharged onto the screws and onto a long cantilevered flange."),
 ("L_cavity_gasket", "mm", "1.4 mm", 1.4, "gaskets - hollow profile", "S",
    "Width of the inner cavity. It is what makes the gasket compliant: without it, it would be solid rubber. It also serves to make room for the material that is displaced - a groove filled to 100% does not close, because rubber is incompressible and has to go somewhere."),
 ("H_cavity_gasket", "mm", "0.8 mm", 0.8, "gaskets - hollow profile", "S",
    "Height of the inner cavity. Its roof is a 45-degree double pitch, not flat, so it prints without support: the flat stretch left as a bridge is half a millimetre wide."),
 ("H_lip_gasket", "mm", "0.5 mm", 0.5, "gaskets - sealing lip", "D",
    "How much the lip protrudes from the groove. It is the part that gets squashed, and it equals H_gasket minus the depth of the groove."),
 ("L_lip_gasket", "mm", "1.2 mm", 1.2, "gaskets - sealing lip", "S",
    "Width of the lip. Narrow on purpose: for the same force, less contact area means more pressure, and pressure is what seals. As wide as the gasket, it would take four times the force for the same seal."),
 ("D_button_gasket", "mm", "1.2 mm", 1.2, "gaskets - retention", "S",
    "Diameter of the buttons that hold the gasket in the groove. It is not glue: the gasket is a consumable part and must stay removable, so you just pull it off."),
 ("Dp_button_gasket", "mm", "0.8 mm", 0.8, "gaskets - retention", "S",
    "How far the button goes into the bottom of the groove. Below it 0.7 mm of flange remain, which is enough: the button carries no load, it only holds the gasket during assembly."),

 ("--- THE WINDOW ONTO THE DISC NUMBERS ---",),
 ("R_numbers_disc", "mm", "68.5 mm", 68.5, "disc - MEASURED with the caliper", "M",
    "Radius at which the manufacturer printed the numbers 1..5 on the flat face of the disc, on the CAMERA side, one next to each filter hole. It is the number from which everything else derives, and it falls exactly in the middle of the gasket groove, which without deviations would be at 67..70."),
 ("Ang_window_body", "deg", "6.5 deg", 6.5, "filter_wheel_body - reading window; ESTIMATED from a photo", "S",
    "Angle of the reading window the manufacturer made in the METAL body, from the centre of the chord (the rim slot, 0 degrees), positive towards the electronics panel. ESTIMATED from a photo of the reference wheel, to be measured with the caliper. At 0, centred on the chord, the collar's window with it, the number showed 6.5 degrees beside the collar's window on the motorised wheel, while the metal window is centred on the number: the rim slot is centred on the chord, the window is not."),
 ("Ang_window_numbers", "deg", "Ang_window_body", 6.5, "collar - reading window", "D",
    "Angle at which the number is read through the collar: the collar's window stands over the METAL body's window, so it is that angle and not a number of its own. The clutch stays at zero, on the chord: it is the rim slot that sits there, not the window."),
 ("R_in_window_numbers", "mm", "66.2 mm", 66.2, "collar - window; MEASURED on the body", "M",
    "Inner radius of the window, copied from the one the manufacturer already made in the metal body."),
 ("R_out_window_numbers", "mm", "D_body / 2 - Dp_slot_front", 70.5, "collar - window", "D",
    "Outer radius of the window: the chord on which the body's window ends. Beyond that point the body's plate is milled away, so looking further out would show no more disc."),
 ("L_window_numbers", "mm", "9 mm", 9.0, "collar - window; MEASURED on the body", "M",
    "Width of the window. Nine millimetres frame ONE digit only, and that is the point: the digits are 72 degrees apart, that is 86 mm of arc at r 68.5, so there is margin to spare and it pays to stay narrow. A wide window that showed two would no longer tell which position is on axis."),
 ("Ang_flat_groove", "deg", "6 deg", 6.0, "collar - groove deviation", "S",
    "Half-width of the stretch in which the groove is already fully displaced, before it starts to come back. It must cover the window with margin: half a window is 4.5 mm, which at r 65 makes 3.97 degrees."),
 ("Ang_dev_groove", "deg", "20 deg", 20.0, "collar - groove deviation", "S",
    "Total half-width of the deviation. Between Ang_flat_groove and this value the groove returns to its usual radius with a raised-cosine transition, which has no corners: it is the length of this stretch that decides the bending radius the cord has to make."),
 ("Edge_out_groove", "mm", "1.5 mm", 1.5, "collar - edge between groove and window", "S",
    "How much edge of flange remains BETWEEN the deviated groove and the rim of the window. Without it, the groove would open sideways into the opening: the compressed cord would have nothing holding it on that side and would come out of the hole, besides being visible. One and a half millimetres on a three-millimetre cord is the minimum that holds. Without this edge r 61.2 would seem enough for the flange: with it the flange has to reach 59.7."),
 ("Edge_in_groove", "mm", "2 mm", 2.0, "collar - edge of flange inside the groove", "S",
    "How much edge of flange remains INSIDE the groove, towards the axis. It is what holds the cord: if it is thin, the compressed cord pushes it out and the seal is gone. Where the groove is deviated the flange extends accordingly, up to r 61.2 at the peak."),
 ("Ch_window_numbers", "mm", "0.8 mm", 0.8, "collar - rim of the window", "S",
    "Chamfer on the rim of the window, on both faces. The one towards the chamber is the face you look from, and a sharp edge there casts a shadow on the digit; the one towards the body is a sealing face, and a sharp edge on a sealing face is a blade."),
 ("Fil_window_numbers", "mm", "1.5 mm", 1.5, "collar - corners of the window", "S",
    "Fillet at the corners of the window. A rectangular opening with sharp corners is also the point from which a flange cracks, besides being ugly to look at."),

 ("R_in_flange_collar", "mm", "R_gasket - 6 mm", 66.0, "collar; collar_section; assembly_section", "D",
    "Inner radius of the two flanges of the collar. It follows the gasket, keeping three millimetres inside the rim of the groove: that is the edge of flange that closes the groove on the axis side. It was written as 66 by hand in three different files, and when the gasket moved it was left behind."),
 ("--- SENSOR COVER AND CABLE ROUTE ---",),
 ("D_cable_sensor", "mm", "6 mm", 6.0, "sensor_bracket; sensor_cover", "R",
    "Diameter of the sensor cable: it is a length of whole CAT5, sheath included. It is sized on 6 and not on 5 because a cable squashes but does not get thinner, and the channel has to take it even where the sheath bends."),
 ("D_channel_cable", "mm", "D_cable_sensor + 0.5 mm", 6.5, "sensor_bracket", "D",
    "Width of the saddle in which the still-sheathed cable lies, with half a millimetre of play. A flat-bottomed saddle and not a round channel: a cylindrical groove of 6.5 cut 1.2 deep has a mouth 5.04 wide, and a 6 cable does not lie in there, it gets jammed."),
 ("Dp_channel_cable", "mm", "1.2 mm", 1.2, "sensor_bracket", "S",
    "Depth of the saddle. It is enough to keep the cable from slipping sideways while the cable tie is tightened, and no more is needed: what holds it still is the cable tie, not the shape. The saddle exists only inside the pad, where the arm is 16 wide and it leaves 4.75 of wall per side; on the bare arm, 8 wide, a 6.5 groove would leave 0.75."),
 ("R_tie_cable", "mm", "49 mm", 49.0, "sensor_bracket", "S",
    "Radius at which the cable tie clamps the cable onto the bracket. It is the cable strain relief, and it is not an accessory: the pads of the module are the weak link of the whole chain, and a cable pulling on a solder joint tears it off sooner or later. Only the four stripped wires enter the cover, and they do not pull."),
 ("W_pad_tie", "mm", "16 mm", 16.0, "sensor_bracket", "S",
    "Width of the strain-relief pad, across the arm. It is needed because the cable tie has to pass on either side of the cable: on the bare arm, 8 wide, the two slots would be where the cable already runs. Sixteen leave 2.75 of wall outside each slot."),
 ("L_pad_tie", "mm", "8 mm", 8.0, "sensor_bracket", "S",
    "Length of the strain-relief pad, along the arm."),
 ("Cd_slots_tie", "mm", "9 mm", 9.0, "sensor_bracket", "S",
    "Centre distance of the two slots of the cable tie. Nine mm put each slot 4.5 from the centre line: three quarters of a millimetre beyond the side of the cable, which is enough for the cable tie to close without having to pinch the sheath."),
 ("W_slot_tie", "mm", "3.5 mm", 3.5, "sensor_bracket", "S",
    "Length of the two slots for the cable tie, along the arm. Good for a 2.5 cable tie."),
 ("H_slot_tie", "mm", "1.5 mm", 1.5, "sensor_bracket", "S",
    "Width of the slots of the cable tie, across the arm."),
 ("W_passage_wires", "mm", "3.5 mm", 3.5, "sensor_bracket", "S",
    "Width of the passage for the four stripped wires, which goes through the boss of the cover instead of going round it: at r 40 the boss is 7 wide on an arm 8 wide, and there would be no lane left beside it. The wires pass inside the pedestal, not next to it."),
 ("H_passage_wires", "mm", "2 mm", 2.0, "sensor_bracket", "S",
    "Height of the wire passage. Three and a half by two makes 7 mm2 against the 3.1 taken up by four insulated AWG24 wires: they pass without being squashed, and it is a span the print bridges without supports."),
 ("Dp_groove_tie", "mm", "H_slot_tie", 1.5, "sensor_bracket - groove for the cable tie underneath", "D",
    "Depth of the groove on the UNDERSIDE of the cable arm, from one tie slot to the other. Under the arm there is the face of the wheel body - measured, the arm rests on it at z 23.0 - so a cable tie closing round the arm would lift the bracket by its own thickness. The groove is as deep as the slots are wide, because the slot width IS the allowance for the thickness of the tie."),
 ("Fil_mouth_passage_wires", "mm", "2 * (Halfw_relief - W_passage_wires / 2)", 5.70, "sensor_bracket - mouth of the wire passage", "D",
    "Fillet on the two walls where the wire passage opens into the capacitor window, which is also where the wires come out. It is not chosen: it is TWICE the width of the step between the window and the passage, because one step proved too tight. At one step the curve was a quarter circle tangent to both walls; at two it no longer fits across, so it stays tangent to the wall of the passage and runs out on the corner of the window, at about 120 degrees to its side wall. Only as deep as the passage: below its floor there is no corner to round."),
 ("Fil_edges_arm_cable", "mm", "1.5 mm", 1.5, "sensor_bracket - vertical edges of the cable arm", "S",
    "Fillet on the convex vertical edges of the cable arm of the sensor bracket, a part that gets handled. One and a half millimetres because the shortest straight stretches of that outline - the steps between the pads - are three to four long: a fillet takes its radius off both ends of each, and at two the shortest would be gone."),
 ("R_boss_cover_sensor", "mm", "40 mm", 40.0, "sensor_bracket; sensor_cover", "S",
    "Radius at which the two bosses carrying the sensor cover sit, one per arm. On the arms and not around the module: the cover must rest on the BRACKET and never on the board, because anything pressing from above shifts H_rest_module and changes the air gap, which is the hardest-won number in the design."),
 ("D_boss_cover_sensor", "mm", "D_hole_insert_M25 + 2*Wall_around_insert", 7.75, "sensor_bracket", "D",
    "Diameter of the bosses. Around the melted-in M2.5 insert 1.75 mm of wall remains. It now DERIVES from the insert hole instead of being a 7 written by hand: with the real insert it comes out at 7.75. Staying at 7, around the new hole 1.38 mm of wall would have remained, below the one and a half that in this design is the minimum around a heat-set insert."),
 ("Off_boss_cable", "mm", "(W_passage_wires + D_boss_cover_sensor) / 2 + 0.5 mm", 6.125, "sensor_bracket; sensor_cover", "D",
    "How far the cover boss is offset from the axis of the arm, on the cable arm only. Before, it was on axis and the wire lane passed UNDER it, in a tunnel two millimetres high: the cable had to be threaded through, and with the JST connector already crimped it no longer fits. Offset by this amount the boss leaves the lane open along its whole length and the wires are laid into it from above. The dimension derives from the two widths it has to separate - half the lane plus half the boss - plus half a millimetre of clearance, so that if the lane or the insert is widened the boss moves by itself. The arm, which on its own does not reach that far, widens there with a pad.",),
 ("Ch_cover_sensor", "mm", "2 mm", 2.0, "sensor_cover", "S",
    "45-degree chamfer along the whole outline of the top of the sensor cover. The cover was a box shape with two square-cut tabs: sharp edges on the top and at the ends of the tabs, in a part that is in view inside the wheel and gets picked up in the dark: rejected. Two millimetres on a three-millimetre plate is plenty: a third of the thickness stays at full outline and the top is set back two millimetres all round. It is a CHAMFER and not a fillet for a construction reason, not one of taste: the outline of the cover is that of the module, that is a polyline of some forty segments, and an OCCT fillet on segments three millimetres long comes out silently with negative volume - tried. The chamfer is obtained instead by extruding the same outline with a draft, which on the convex outlines of the cover cannot fail.",),

 ("H_boss_cover_sensor", "mm", "6 mm", 6.0, "sensor_bracket; sensor_cover", "S",

    "Height of the bosses, measured from the INNER face of the arms: at r 40 they are inside the step, so they start from H_body + H_rest_module, the same plane the board rests on, and not from the upper face that the arms have only beyond raggio_gradino_staffa. Dimensioning them from the upper face left them hanging in mid-air. Six millimetres put the underside of the cover 4.4 above the board - the four stripped wires and their solder joints pass there - and leave 2 mm of solid boss between the bottom of the M2.5 insert seat and the wire passage, which runs underneath."),
 ("Th_cover_sensor", "mm", "3 mm", 3.0, "sensor_cover", "S",
    "Thickness of the sensor cover."),
 ("D_clear_screw_cover_sensor", "mm", "2.9 mm", 2.9, "sensor_cover", "S",
    "Clearance hole for the two M2.5 screws holding the cover. Clearance and not threaded: the thread is in the insert inside the bracket boss, and the cover must be able to slide up and down on the screw without pushing sideways on the bosses."),
 ("W_opening_cable", "mm", "6 mm", 6.0, "sensor_cover", "S",
    "Width of the opening in the skirt of the cover through which the four stripped wires enter. Wider than the lane that brings them there because the wires fan out to the six pads, which are all along the edge of the board."),
 ("Cl_cover_module", "mm", "1 mm", 1.0, "sensor_cover", "S",
    "Clearance between the edge of the board and the inner face of the cover skirt. The cover is shaped on the BOARD and not on the bracket: cut out on the bracket, the skirt survived only where the arms pass - two fragments instead of a ring - and the module was left uncovered."),
 ("R_skirt_cover", "mm", "16 mm", 16.0, "sensor_cover", "S",
    "No longer used: the skirt follows the outline of the board, not a radius. It stays so as not to break the references."),
 ("Th_skirt_cover", "mm", "2 mm", 2.0, "sensor_cover", "S",
    "Thickness of the skirt."),
 ("Cl_skirt_bracket", "mm", "0.3 mm", 0.3, "sensor_cover", "S",
    "How far the skirt stays suspended above the face of the bracket. Three tenths: they keep out dust and guarantee that the cover does not rest there instead of on the bosses."),
 ("--- ELECTRONICS IN THE MOTOR COMPARTMENT ---",),
 ("L_board", "mm", "70 mm", 70.0, "electronics; panel", "S",
    "Length of the perfboard, across the bisector. It is the common 30 x 70, whole: it fits in the motor compartment if the compartment reaches about 70 degrees, and the compartment was widened for this. A 30 x 50 would fit even in the previous compartment. CONFIRMED INDIRECTLY: the cut board of the reference build measures 65.66, and the model - which already has the cut - leaves 65.59. Seven hundredths, that is the same thing. This remains the WHOLE board: the cut is separate."),
 ("W_board", "mm", "30.3 mm", 30.3, "electronics; panel", "M",
    "Width of the board, along the bisector. MEASURED with the caliper on the board of the reference build: 30.3 and not a round 30."),
 ("Th_board", "mm", "1.5 mm", 1.5, "electronics", "M",
    "Thickness of the perfboard, the standard one. MEASURED: 1.5 and not the catalogue 1.6. One tenth, but it is one of the bricks of the stack that carries the driver, and the stack had already been got wrong by four millimetres by trusting two estimates."),
 ("Ang_board", "deg", "49 deg", 49.0, "electronics; box - head; panel", "S",
    "Bisector of the board. Chosen on the map of free heights in the compartment: centred here, the 30 x 70 has at least 15 mm above it everywhere and 25 over a continuous stretch of 50, towards the head. The arm, the motor and the clutch were accounted for over their whole travel."),
 ("R_in_board", "mm", "91 mm", 91.0, "electronics; panel", "S",
    "Distance of the inner edge of the board from the centre of the disc, along the bisector. Further in, the board passes under the arm pivot where the space drops to 22; further out, the outer corners reach the back."),
 ("N_holes_board_L", "", "24", 24.0, "electronics - perfboard grid; MEASURED", "M",
    "Holes of the board along its length: the 30 x 70 of the reference build is a 10 x 24."),
 ("N_holes_board_W", "", "10", 10.0, "electronics - perfboard grid; MEASURED", "M",
    "Holes of the board along its width."),
 ("Pitch_perfboard", "mm", "2.54 mm", 2.54, "electronics - grid", "R",
    "The pitch of the perfboard. The grid is centred on the whole board: the first column is 5.8 mm from the short edge."),
 ("L_xiao", "mm", "20.95 mm", 20.95, "electronics - from the XIAO model", "R",
    "Length of the XIAO board, from the manufacturer's model."),
 ("Pin_xiao_per_side", "", "7", 7.0, "electronics - XIAO", "R",
    "XIAO pins per side, at 2.54 pitch, centred on the board (estimate from the manufacturer's drawing)."),
 ("Proj_usb_xiao", "mm", "1.53 mm", 1.53, "electronics - from the XIAO model", "R",
    "How far the USB-C socket projects beyond the edge of the XIAO board, from the manufacturer's model."),
 ("D_holes_fixing_board", "mm", "2 mm", 2.0, "panel - post screws", "M",
    "Diameter of the fixing holes of the board, MEASURED: two millimetres. It did not exist as a parameter and it needed to be known, because it decides the screw: an M2.5 does NOT pass through a 2 hole, and the posts had been designed with M2.5 inserts. Either the screw goes down to M2 - which just passes through a 2 hole, as already happens for the sensor module - or the holes are enlarged with a drill."),
 ("Ang_entry_box", "gradi", "(Ang_ear_front_A + Ang_ear_front_B) / 2", 21.05, "box - entry slots of the pockets", "D",
    "Direction along which the box slides onto the collar, that is the direction in which the slots that receive the ear bosses open. It is the bisector of the two front ears, which are the furthest apart: this way the slot faces outwards for all five, even for those at the ends, which are fifty degrees from this direction. It is not an aesthetic preference: it is the only direction in which the box can go in, because the front bosses face down and the rear ones up, and along the axis the two families block each other."),
 ("Travel_entry_box", "mm", "24 mm", 24.0, "box - entry slots of the pockets", "S",
    "How long the entry slot is, from the centre of the pocket outwards. MEASURED on the model before choosing it: pulling the box along Ang_entry_box, the interpenetration with the collar disappears at 20 mm of travel (at 15, 35 mm3 remained, all on the front ears). Twenty-four is those twenty plus four of margin. Shorter and the boss stays snagged; much longer and it eats into the compartment wall for no purpose."),
 ("D_hole_board_M25", "mm", "2.7 mm", 2.7, "panel - third board screw, hole to be opened on the perfboard", "R",
    "Diameter to which hole B05 of the perfboard is drilled out, for the third M2.5 screw that holds the cut end of the board. The printed holes of the board are 2 (see D_holes_fixing_board) and an M2.5 does NOT pass through them: either the screw went down to M2, or that hole is enlarged. Enlarging it was chosen, because that screw alone holds the end where the little tooth that broke used to be. It is the drill BIT used for the reference build, not a calculated dimension - the standard clearance hole for an M2.5 would be 2.9 - and that is why it is class R. The number is also in pcb/README.md, written by hand: if it changes, change it there."),
 ("Cd_holes_board_w", "mm", "26 mm", 26.0, "panel - posts", "M",
    "Centre distance of the two fixing holes of the board, across. ESTIMATE for a common 30 x 70 with the holes 2 mm from the edges: to be measured. Only the two at the far end are used: those at the head end go away with the cut. MEASURED with the caliper: a round 26, that is the estimate was right. Note that it does NOT derive from the width: with W 30.3 and the holes 2 from the edges it would come out at 26.3, so the holes are not 2 from all edges and deriving it would have been wrong by three tenths."),
 ("Dist_holes_board_rim", "mm", "2 mm", 2.0, "panel - posts", "M",
    "Distance of the fixing holes from the short edge away from the head. ESTIMATE, like the previous one. CONFIRMED with the caliper: the two millimetres of the estimate were right."),
 ("L_guides_board", "mm", "10 mm", 10.0, "panel - guides", "S",
    "Length of the two guides of the panel along the board, at the head end. Before, they were two little TEETH with a lip covering the edge of the board: that lip started in mid-air above a gap and was printed on supports, and one broke off while the board was slid in, which went in with difficulty in that area (REJECTED). Now the head end is held by a screw (see Q_vite_testa_basetta in electronics.py), the guides only square the board sideways, and the board is lowered from above instead of sliding: no lip, no undercut, no supports."),
 ("Cl_guides_board", "mm", "0.3 mm", 0.3, "panel - guides", "S",
    "Clearance between the long edge of the board and the guide beside it. Three tenths per side: the board is lowered between the two without forcing and stays square. The guides grow from the solid of the panel, so this is a vertical face against a vertical face, not a fit on supports."),
 ("Th_guides_board", "mm", "2 mm", 2.0, "panel - guides", "S",

    "Thickness of the guides, outside the edge of the board."),
 ("H_guides_board", "mm", "1.5 mm", 1.5, "panel - guides", "S",
    "How far the guides project above the upper face of the board. It serves as a lead-in: the board is lowered between the two guides and finds its own way in. It is not a lip and covers nothing - above the board the guides do not project inwards - so it prints entirely from the solid."),
 ("R_column_ear", "mm", "11 mm", 11.0, "box - front ears", "S",
    "Radius of the round, centred on the screw, that softens the outline of the two front ears and makes them the column that goes down to the floor. The ear was a sharp-edged annular sector hanging in mid-air under the collar flange: on one side two acute corners in a part that gets picked up by hand, on the other an overhanging ceiling twenty-seven millimetres above the bed. By joining them with a round around their own screw the outline becomes soft, and the same outline extruded down to the floor acts as a column: the couple between the front ears and the rear ones - which is what carries the moment of the spring - no longer bears on a bracket but on a pillar. The outline follows a hand-drawn sketch (mechanics/others/Colonna.dxf, view from below), remade parametrically instead of copied point by point, so it follows R_screws_box if the screw moves. Eleven millimetres is the size that traces the sketch - it reaches r 92.5 against the 93 of its spline - and leaves 8.25 mm of material around the clearance hole."),
 ("D_foot_column_ear", "mm", "16 mm", 16.0, "box - front ears", "S",
    "Diameter of the foot with which the column of the front ear touches the floor. At the first attempt the column came down flush with the bottom of the compartment and stopped there: but the bottom of the compartment exists only from r 86.2 outwards, so over most of its footprint the column touched nothing and its underside was an overhanging ceiling two and a half millimetres above the bed. Now it goes down to the outer face of the bottom and rests on it with a round foot. Sixteen: around the screw channel 4.5 mm of wall remains, and on the bed it is a first-layer island wide enough not to come loose."),
 ("R_fillet_column_ear", "mm", "3 mm", 3.0, "box - front ears", "S",
    "Radius of the fillet between the column of the front ear and the wall it leans on. Without it, the column meets the wall at a sharp edge: it is the point through which all the load the spring puts on the ear passes, and it is also a groove in which the print lays down two perimeters that touch without bonding. Three millimetres is what the thinnest wall of the joint can afford: any larger and the fillet would eat into the screw channel, which passes 3.5 from the axis."),
 ("H_taper_column_ear", "mm", "30 mm", 30.0, "box - front ears", "S",

    "Height of the cone that brings the foot of the front-ear column to full diameter. The first attempt made it 3.84 mm high - the minimum height that keeps the flank at the design's printable angle, like the pivot support on the collar - and the result was a stubby foot with a small collar under a straight shaft. Thirty is the WHOLE height of the column: this way the shaft is gone and the column is a single truncated cone that widens very gently, from Ø16 at the ground to Ø22 under the ear. The flank comes out at 84 degrees from horizontal, that is nearly vertical, so printability is not even worth discussing. The value is truncated to the available height: asking for more, the cone would eat the ear plate, which instead must stay Th_ear_box thick over its whole footprint."),
 ("D_channel_screw_ear", "mm", "7 mm", 7.0, "box - front ears", "S",

    "Diameter of the channel running through the column of the front ear, from the foot up to under the ear. It is not the screw hole: it is the passage through which the screw and the hex key arrive from below. The head of the M3 is Ø5.5 and must be able to go down the channel as far as the shoulder, where the hole narrows to D_clear_screw_ear; seven leave three quarters of a millimetre per side to the head and room for a ball-end key. Without the channel the column plugged the screw and the ear could no longer be tightened - a defect no check had caught."),
 ("D_clear_screw_ear", "mm", "3.4 mm", 3.4, "box - ears", "S",
    "Clearance hole for the M3 in the ear. It was 3.4 written by hand inside the generator, as radius 1.7: here it becomes a dimension because from it derives the shoulder on which the screw head rests at the bottom of the column channel."),
 ("Th_rib_boss_spring", "mm", "4 mm", 4.0, "box", "S",


    "Thickness of the vertical rib carrying the spring boss. The boss is a cylinder lying on its side inside the compartment: its lower half is an overhanging ceiling, and in the print orientation of the box - bottom on the bed - it needs supports. The rib lies in the vertical plane of the spring axis, joins the cylinder to the bottom with two 45-degree faces and continues up to the ceiling of the compartment: besides removing the supports it ties the boss to the vault, which is the point the spring pushes on permanently with 22.3 N. Four millimetres is a rib that prints solid with two and a half perimeters and does not plug the compartment: below and above the boss the space is there and nothing goes in it."),
 ("Th_panel_screws", "mm", "5 mm", 5.0, "panel; box", "S",

    "Thickness of the panel at the three screws, and therefore also height of the step the box cuts around it. Elsewhere the panel has its seating rebate at half thickness, that is 1.25 mm: there the screws gripped on a thin edge, and above all the step of the box remained an overhanging ceiling a millimetre and a quarter above the bed, where supports have no room to build up. Bringing the screw area to five millimetres the edge becomes a real piece of panel and the step of the box rises enough to be supported. Inside the box, in that area, there is nothing in the way."),
 ("H_post", "mm", "5 mm", 5.0, "panel - posts", "S",
    "Height of the posts that hold the board raised off the panel: underneath must pass the trimmed leads and the solder joints of a point-to-point wired perfboard. Every millimetre here adds to the height of the driver, which is the tallest part. Five and not three: a wired board takes four or five millimetres of air underneath, and with three the bent leads did not fit. The five are taken, that is the larger of the two, because the constraint it adds to - the height of the driver in the compartment - still has margin; if the compartment check complained, go down to four."),
 ("D_post", "mm", "D_hole_insert_M2 + 2*Wall_around_insert", 6.75, "panel - posts", "D",
    "Diameter of the posts. Around the M2.5 insert 1.75 mm of wall remains. It now DERIVES from the insert instead of being a 7 written by hand: with the M2 it comes out at 6.35, and if the measured insert turned out different the post follows it by itself."),
 ("D_out_insert_M25", "mm", "4.6 mm", 4.6, "sensor bracket - cover bosses", "M",
    "Outer diameter of the M2.5 heat-set insert of the reference build, MEASURED: 4.6. The catalogue derived a 3.4 hole from it, which is the right hole for a 3.75 insert: in that hole this insert does NOT GO IN, or it splits the boss. It is the third time the catalogue has been wrong here, always on the small side."),
 ("D_hole_insert_M25", "mm", "D_out_insert_M25 - 0.35 mm", 4.25, "panel - posts", "D",
    "Hole for the M2.5 heat-set insert, as the maker says. TO BE CONFIRMED with the inserts in use, and with the holes of the board, which on 30 x 70 boards are often 2. It now DERIVES from the measured insert instead of being the catalogue number: 4.25 and not 3.4. Because of it the boss also had to grow, since with the previous wall it would have been left at 1.38 mm around the hole."),
 ("L_insert_M25", "mm", "4 mm", 4.0, "panel - posts", "S",
    "Length of the M2.5 insert. Longer than the post: the rest goes down into the panel. CHOSEN between the two lengths of the reference build, 4 and 5.7: the 4 is taken. The cover boss is 6 high: with the 5.7 insert three tenths of bottom would remain, and that bottom is needed for the tip of the screw and to keep the insert from punching through while it is set. With 4, 2 remain, and the engagement is still one and a half diameters."),
 ("H_below_board_xiao", "mm", "11 mm", 11.0, "electronics - MEASURED", "M",
    "Air between the upper face of the board and the UNDERSIDE of the XIAO board, plugged in: rectangular socket plus pin spacer in a single number. Before, they were two numbers, one estimated, and together they were off by four millimetres: taller sockets are needed, because the pins do not go into the round ones."),
 ("H_below_board_driver", "mm", "11 mm", 11.0, "electronics - MEASURED", "M",
    "The same for the driver, measured: it is the driver, with the heatsink, that sets the height of all the electronics."),
 ("Z_usb_on_board", "mm", "0.26 mm", 0.26, "electronics - from the XIAO model", "R",
    "How far above the underside of the board the USB socket starts. It comes from the manufacturer's model, confirmed on the real board."),
 ("Z_usb_top_on_board", "mm", "4.5 mm", 4.5, "electronics - MEASURED", "M",
    "From the UNDERSIDE of the XIAO board to the TOP of the USB socket. It is the measurement from which the slot in the head derives. It agrees with the manufacturer's model: 4.5 minus the 0.26 at which the socket starts makes 4.24, that is the 4.2 the model declares. Two earlier readings - 12 from the board to the underside of the socket and 3.2 of height - do not agree with this one and were discarded."),
 ("H_usb", "mm", "Z_usb_top_on_board - Z_usb_on_board", 4.24, "electronics", "D",
    "Height of the USB-C socket, by difference between the two dimensions on the board. The slot in the head is this high plus the clearance, with the top part ROUNDED like the socket: the radius is half the height."),
 ("Th_board_driver", "mm", "1.6 mm", 1.6, "electronics - from the TMC2209 model", "R",
    "Thickness of the driver board."),
 ("H_heatsink_driver", "mm", "13.67 mm", 13.67, "electronics - MEASURED", "M",
    "Height of the driver heatsink, adhesive included. It is what governs the height of all the electronics: from the panel, with the rest of the stack, it makes 26.9."),
 ("L_heatsink_driver", "mm", "15 mm", 15.0, "electronics - MEASURED", "M",
    "Footprint of the heatsink, along the pin rows."),
 ("W_heatsink_driver", "mm", "14.5 mm", 14.5, "electronics - MEASURED", "M",
    "Footprint of the heatsink, across."),
 ("D_electrolytic", "mm", "6.35 mm", 6.35, "electronics - C1 and C2, 47 uF 63 V; MEASURED", "M",
    "Diameter of the two electrolytics, C1 and C2, measured with the caliper: 6.35 (6.4 in an earlier reading, pcb/BOM.md). The catalogue says 6.3. On the reference board C1 (S03/S02) and C2 (S05/S04) stand two rows apart, 5.08 mm, less than one diameter: the two bodies cannot both stand upright there, and the drawing shows them overlapping by 1.3 mm. They fit on the real board, so they lean apart on their leads."),
 ("H_electrolytic", "mm", "13 mm", 13.0, "electronics - C1 and C2 standing upright; MEASURED", "M",
    "Height of the electrolytics mounted upright, leads included, measured. C1 stays upright because of the constraint of the VM-GND loop (pcb/README.md); the driver is taller anyway."),
 ("D_led", "mm", "3 mm", 3.0, "box - head, LED; electronics", "M",
    "Diameter of the status LED, D1 in the BOM: red, 3 mm. It sits on the head, above the power socket, and in service it is off: next to a telescope a lit red light is a defect."),
 ("D_collar_led", "mm", "3.8 mm", 3.8, "electronics - LED", "R",
    "The collar at the base of the 3 mm LED, from the catalogue: it is what rests inside the head and what decides how far the LED must stay from the GX12 nut."),
 ("D_hole_led", "mm", "D_led + Comp_hole_printing", 3.2, "box - head, LED", "D",
    "Hole for the LED in the head: the LED goes in from the inside and stops on its collar."),
 ("W_flats_gx12", "mm", "11.75 mm", 11.75, "BOX - GX12 hole", "M",
    "Distance between the two anti-rotation flats of the GX12, MEASURED with the caliper. It is not a D: the threaded barrel has one flat PER SIDE, 180 degrees apart. As long as the hole was a plain round, the connector turned when the ring nut was screwed on, and no check could see it - in the model the GX12 is simplified to a cylinder, so those two flats do not exist."),
 ("Cl_flats_gx12", "mm", "0.1 mm", 0.1, "BOX - GX12 hole", "S",
    "Total clearance between the flats of the connector and those of the hole. It is tight on purpose: it is a fit of SHAPE, which must prevent a rotation, not a sliding fit. The engagement that remains is little more than seven hundredths per side, and that is enough, because what stops the connector is a shoulder and not friction."),
 ("Cl_led_gx12", "mm", "1 mm", 1.0, "box - head, LED", "S",
    "Air between the LED collar and the GX12 nut, inside the head. The position of the LED derives from this."),
 ("Cl_modules", "mm", "2 mm", 2.0, "electronics", "S",
    "Air between the XIAO and the driver, along the board."),
 ("H_terminals", "mm", "10 mm", 10.0, "electronics - ESTIMATE", "S",
    "Height of the 5.08-pitch terminal blocks: catalogue estimate, to be measured on the ones at home."),
 ("D_out_insert_M2", "mm", "3.6 mm", 3.6, "panel - posts", "M",
    "Outside diameter of the M2 heat-set insert in the posts. It was a catalogue figure, and in this project the catalogue has already been wrong twice - it gave the M3s as 4.6 and they are 5.0, the M4s as 5.6 and they are 6.3. The posts went from M2.5 to M2 because the holes in the board were measured at Ø2 and an M2.5 does not go through; an M2 does, just, as already happens on the sensor module. MEASURED: 3.6, and the catalogue said 3.2. Third time out of three that the catalogue is wrong in this project - M3 4.6 against 5.0, M4 5.6 against 6.3 - and every time on the small side, that is, in the direction that splits the boss instead of leaving the insert loose."),
 ("D_hole_insert_M2", "mm", "D_out_insert_M2 - 0.35 mm", 3.25, "panel - posts", "D",
    "Hole the M2 insert melts into. Thirty-five hundredths narrower than the insert, the same rule as for the M3s and the M4s: as it melts in it must bite, not slide."),
 ("L_insert_M2", "mm", "4 mm", 4.0, "panel - posts", "S",
    "Length of the M2 insert. TO BE MEASURED like the diameter. If it came out longer than the post, the rest goes down into the panel, which is solid there. CHOSEN from the three lengths of the reference build - 2.5, 3 and 4: the longest is taken. Four millimetres on an M2 are TWO DIAMETERS of engagement, whereas the 3 mm of the M3 inserts are a scant diameter, the practical minimum. It all fits inside the post, which is 5 high, and below the insert a millimetre of bottom still remains. The other two lengths offer nothing in return: here there is no height constraint to save on, because the insert sits inside solid material."),
 ("Wall_around_insert", "mm", "1.75 mm", 1.75, "panel - posts", "S",
    "Wall left around a heat-set insert, in any boss or post. It was the number implicit in D_post, which was 7 written by hand with the wall written only in the comment: changing the insert from M2.5 to M2, that comment would have started to lie."),
 ("Cl_head_board", "mm", "0.5 mm", 0.5, "box - head; electronics - cutting the board", "S",
    "Air between the CUT end of the board and the inner face of the head wall. The head is decided by the XIAO, which must have its socket flush with the outer face and its pins on the grid; the board is cut at this distance from the head. It cannot grow much: beyond the first hole at least 1.27 mm of board must remain, and with 0.5 there remain 1.39."),
 ("Marg_panel", "mm", "3 mm", 3.0, "panel; box - opening in the bottom", "S",
    "How much larger the opening in the bottom is than the board: it is the air for sliding it in and out together with the panel, with the leads sticking out."),
 ("Cl_panel", "mm", "0.2 mm", 0.2, "board_panel", "S",
    "Air between the panel and its opening, all round. It is applied to the PANEL, which is made smaller by this much per side: it is not to be touched any more, so that a panel already printed stays good; more air is added on the other side (see Cl_panel_box)."),
 ("Cl_panel_box", "mm", "0.2 mm", 0.2, "BOX - panel opening", "S",
    "EXTRA air cut into the box's opening, per side, on top of what has already been taken off the panel. It is needed because two tenths per side are right on paper and nil in the hand: measured on the solids, the side play in the plate is 0.199 - exactly the nominal - and the panel still slides in only with effort. On a part eighty-five millimetres long that tenth and a half is eaten by shrinkage, and the panel does not even have to locate anything: what holds it in position are the three screws in their inserts, not the fit. It is kept separate from Cl_panel, and not added to it, because the air is added ONLY on the box side: the panel already printed stays good."),
 ("Stop_panel", "mm", "1.5 mm", 1.5, "panel; box", "S",
    "Width of the step that keeps the panel flush: over the outer half of the thickness, the opening and the panel are wider by this much."),
 ("Proj_screws_panel", "mm", "10 mm", 10.0, "panel; box", "S",
    "How far the panel widens beyond the opening, at the end away from the head, to carry the two screws at that end."),
 ("Setback_screws_panel", "mm", "5 mm", 5.0, "board_panel", "S",
    "Distance of the two screws at the far end from the edges of the opening."),
 ("D_boss_panel", "mm", "9 mm", 9.0, "box - bosses of the panel screws", "S",
    "Diameter of the bosses that carry the M3 inserts of the panel. Around the melted-in insert 2 mm remain."),
 ("Z_skirt_inner", "mm", "Z_bottom_arm - Cl_skirt_arm", -6.5, "box - inner skirt", "D",
    "How high the skirt that closes the compartment towards the axis rises, under the arm. It is no longer chosen: it is the UNDERSIDE OF THE ARM less the clearance. Before, it was -14, written by hand on the head of the pivot screw, which comes down to -13.5: but the screw is on the pivot, at r 91.6, and its head reaches r 88.9, that is, just OUTSIDE the band of the skirt - it was not the one in charge, and for it the steps around the pivot are enough. The one in charge is the arm, and the skirt rises five and a half millimetres more than before. Beyond the arm's passage, instead, it rises up to the collar."),
 ("Cl_skirt_arm", "mm", "0.5 mm", 0.5, "box - inner skirt", "S",
    "Air between the top of the inner skirt and the underside of the arm, and around the discs that the pivot carries under the arm. The rotation of the arm does not use it up: the arm turns about a vertical axis, so its underside stays the same plane at any angle of the travel. What uses it up are the print tolerances and the axial play of the bearing stack, and it is also the gap left open towards the compartment: half a millimetre, against the eleven of before."),
 ("Th_tab_tie", "mm", "3 mm", 3.0, "box - cable-tie tab", "S",
    "Thickness of the tab that projects from the inner face of the head, next to the GX12, for tying the wires with a nylon cable tie."),
 ("Off_tab_tie", "mm", "1 mm", 1.0, "box - cable-tie tab", "S",
    "How far the cable-tie tab stands from the middle between the GX12 nut and the back, towards the back. In the middle, the root of its 45 degree underside took 0.25 mm3 of the XIAO's board; at +1 there are 0.65 mm of air, at -1 it touched more (1.2 mm3)."),
 ("L_tab_tie", "mm", "9 mm", 9.0, "box - cable-tie tab", "S",
    "How far the tab projects from the head inwards. Its lower edge is at 45 degrees: the box is printed on its bottom, and a tab with a horizontal edge would want support."),
 ("H_tab_tie", "mm", "12 mm", 12.0, "box - cable-tie tab", "S",
    "Height of the tab at its free edge, centred on the level of the GX12, from which the wires to be tied come down."),
 ("W_slot_tie_head", "mm", "3 mm", 3.0, "box - cable-tie tab", "S",
    "Cable-tie slot in the tab, in height: for common 2.5 mm cable ties. To be confirmed with the ones in use."),
 ("H_slot_tie_head", "mm", "1.6 mm", 1.6, "box - cable-tie tab", "S",
    "Cable-tie slot in the tab, in length along the tab: a 2.5 cable tie is about one thick."),
 ("Weld_box_collar", "mm", "0.5 mm", 0.5, "box - inner face of the shell", "S",
    "How far the inner face of the shell goes INTO the collar. It is not a clearance, it is the opposite: box and collar are a single part, and two solids that touch without interpenetrating fuse into a COMPOUND of two parts instead of into one solid - a sliver that comes off in the bag, or worse a part that the slicer prints in two. Half a millimetre of interpenetration makes the fusion unambiguous and has no effect whatsoever on the finished shape, because that face inside the part no longer exists. It has taken the place of Cl_box_collar, which was 0.2 and was the clearance with which the box SLID onto the collar: nothing slides on any more."),
 ("Cl_box_collar", "mm", "0.2 mm", 0.2, "box - inner face of the shell", "S",
    "Air between the inner face of the shell and the outer face of the collar. The box slides onto the collar by running the ears astride the flanges, and it is the bosses that put it in position: the two cylindrical surfaces must not touch. Without clearance they fell on the same cylinder, and since the two parts are described with polygons of different pitch - half a degree the box, one degree the collar - the finer one stuck out: the audit found a hundredth of a cubic millimetre of interpenetration spread over the whole development."),
 ("Cl_skirt_collar", "mm", "0.3 mm", 0.3, "box - inner skirt", "S",
    "Air between the inner skirt and the outer face of the collar. Without it, the two faces fall on the same cylinder: the two parts are described with polygons of different pitch, half a degree the box and one degree the collar, so the finer one sticks out and the audit finds an interpenetration of a hundredth - the same discretisation defect already seen on the ears. It is also the clearance needed to slide the box onto the collar."),
 ("Cl_wall_inner_motor", "mm", "3 mm", 3.0, "box - inner wall under the wheel", "S",
    "Air between the motor and the inner wall that closes the box towards the wheel axis, under the wheel. The wall used to be the inner skirt at r 86, which rose under the arm to half a millimetre from it and carved steps round the pivot: the two bearings sat in it as in a cup, and the arm could not be put in by any path tried. Moved in, the wall is no longer under the arm at all. Its outer face is derived, not written: the motor is the body that comes nearest to the wheel axis below the collar (its square face, Cd_motor - Side_motor/2 = 79.9), and the face stands this much inside it. Three gives r 74.5 for the inner face. Below the collar only: above z 0 the same ring is the body of the wheel."),
 ("L_chamfer_below_flange", "mm", "7 mm", 7.0, "single part - under the collar flange, towards the wheel axis", "S",
    "The 45 degree chamfer in the inside corner between the underside of the collar flange (z -Th_flange_collar) and the outer face of the inner wall under the wheel, running on round the corner along the arc round the motor on the -y side and under the collar-arc fillet: seven millimetres. The part prints on its floor, so under the flange that corner was a flat ceiling over air; the chamfer is material in the corner, a 45 degree face instead of a bridge. The reading window of the filter numbers and the channel of the iron for the M4 insert cross it, and it is cut away round them: the window opens downwards at 45 degrees (a trapezoid), the channel runs on along its own axis."),
 ("L_chamfer_wall_inner_floor", "mm", "10 mm", 10.0, "box - inner wall under the wheel", "S",
    "The 45 degree chamfer in the inside corner between the inner wall under the wheel and the floor. The part prints on its floor, so the chamfer is a fillet of material in the corner, not an overhang. It stops where the motor drops in: there it is cut by the motor's silhouette plus Cl_entry_motor, because the motor comes down to z -27.5 at r 80.7 and a 10 mm chamfer would be in its way."),
 ("Cl_usb", "mm", "0.4 mm", 0.4, "box - USB slot", "S",
    "Air around the USB socket in the slot in the head. The slot is open towards the bottom: the socket goes in rising, together with the panel."),
 ("S_gx12", "mm", "101 mm", 101.0, "box - head, GX12", "S",
    "Where the GX12 sits on the head, along the bisector."),
 ("H_nut_gx12", "mm", "16.7 mm", 16.7, "box - head, GX12", "M",
    "Height of the GX12 nut, that is, of the body that projects inside the box. It was the number 16.7 written inside electronics.py next to GX12_DENTRO: a dimension of a bought part that sat in the code instead of among the dimensions, and so could not appear in any expression."),
 ("Cl_turn_nut_gx12", "mm", "5 mm", 5.0, "box - head, GX12", "S",
    "The free ring that must remain around the GX12 nut so that it can be TURNED to screw it on. It is not an envelope: the nut would fit even without it, and that is exactly why it needs a dimension of its own - a check on the envelope would pass and the part would be unusable all the same. Five millimetres is enough for two fingers on a knurl; a C-spanner would want less, but assembly is done by hand.\n\nThis ring has PRIORITY over the other placements on the head: if moving the socket or the LED costs this ring, the move is not made. That is why it became a check and not a note."),
 ("Cl_cable_driver", "mm", "2 mm", 2.0, "sensor cable", "S",
    "How far above the tallest thing on the board, which is the driver's heatsink, the sheath of the sensor cable stops. Below the sheath the four stripped wires come down, which do not pull and move aside by themselves: it is they that reach the connector, not the sheath. Two millimetres so that the sheath does not rest on the heatsink, which gets hot."),
 ("Cl_gx12_usb", "mm", "2 mm", 2.0, "box - head, GX12", "S",
    "How far the GX12 nut must stay from the XIAO's USB socket. Two millimetres: the shell of the right-angle USB plug has to pass there, and so does the hand that plugs it in in the dark."),
 ("Z_gx12", "mm", "Z_floor_box + Th_walls_box + H_post + Th_board + H_below_board_xiao + Z_usb_top_on_board + Cl_gx12_usb + H_nut_gx12 / 2", 3.35, "box - head, GX12", "D",
    "Level of the GX12 on the head: above the XIAO, with the nut kept Cl_gx12_usb from its socket, and below the ceiling of the compartment.\n\nIT WAS THE NUMBER -1 WRITTEN BY HAND, and its description already said in words what it had to derive from - above the XIAO, two millimetres from the socket - without deriving from it. When the floor of the box rose by six and a half millimetres, and the electronics stack with it, the GX12 stayed where it was, and its nut went INTO the XIAO's USB socket by 2.35 mm - seen on the part, not by a check.\n\nThe LED derives from this level, so it rises with it."),
 ("D_hole_gx12", "mm", "12.2 mm", 12.2, "box - head, GX12", "R",
    "Hole for the GX12: M12 thread plus two tenths. The body in the model is simplified to a 14.8 cylinder: the hole dimension is from the catalogue, to be confirmed on the connector."),
 ("--- BOX-TO-COLLAR MOUNTING ---",),
 ("R_screws_box", "mm", "81.5 mm", 81.5, "collar; box", "S",
    "Radius of the six screws that hold the box to the collar. Chosen because there the insert has wall all around it: 2.2 mm remain to the outer edge of the flange, and inwards the flange continues to 62.5. Further out the wall gets thinner; further in the insert would end up where the wheel body is above."),
 ("D_out_insert_M3", "mm", "5 mm", 5.0, "collar; box - M3 heat-set insert; MEASURED with the caliper", "M",
    "Outside diameter of the M3 heat-set insert of the reference build, measured with the caliper on a sample. Previously it said here that the insert is 4.6 outside and goes into a 4 hole: it was an assumption, and wrong by four tenths. It is the same mistake already made with the M4, where the catalogue says 5.6 and the real one is 6.3. Anyone with different inserts changes this number and L_insert_M3, and hole, lead-in, seat and boss follow it."),
 ("L_insert_M3", "mm", "3 mm", 3.0, "collar; box - M3 heat-set insert; MEASURED with the caliper", "M",
    "Length of the insert, measured. It is none of the lengths in the catalogue assortment (4.0 / 4.8 / 5.7): it is a different type, and that is why the measurement counts for more than the photo. WARNING: 3 mm of engagement on an M3 is A SCANT DIAMETER, that is, the practical minimum. It holds, but where the joint carries load - the six screws that hold the box under the 22.3 N of the spring - there is no margin to spend. If more engagement were needed, the assortment has M3s of 4.0 and 4.8 with the same outside diameter."),
 ("D_tip_iron", "mm", "8 mm", 8.0, "collar - access to the insert seats", "M",
    "Diameter of the tip of the soldering iron used to set the heat-set inserts. CONFIRMED on the iron in use: eight. It serves to check that the tip reaches the mouth of every seat STRAIGHT: a seat that can only be reached at a slant sets the insert crooked, and a crooked insert carries the screw crooked."),
 ("Cl_tip_iron", "mm", "0.5 mm", 0.5, "collar - soldering-iron channel", "S",
    "How much wider than the tip the soldering-iron channel must be. It is not an assembly clearance: the tip is RED-HOT, and plastic that touches it on the way down melts where it should not. Half a millimetre in all, that is, a quarter per side, is enough for the tip not to rub the wall of the channel. From this derive the width of the channel in the collar and the diameter of the top of its support, which must go on leaving wall around it."),
 ("D_hole_insert_M3", "mm", "D_out_insert_M3 - 0.35 mm", 4.65, "collar; box - insert seat", "D",
    "Hole the insert melts into. Deliberately three and a half tenths narrower than the insert: as it melts in it must bite, not slide. It is the same rule used for the M4. Before, it was 4.0, consistent with a 4.6 insert which, however, is not the one fitted: with 4.0 a 5 insert would not have gone in, or would have split the boss."),
 ("D_boss_insert", "mm", "D_hole_insert_M3 + 7 mm", 11.65, "collar; box", "D",
    "Diameter of the boss that carries the insert, on the outer face of the flange. It gives the wall around the melted-in insert, and also acts as a spigot: it goes into the pocket of the ear and puts the box in position even before it is screwed down."),
 ("H_boss_insert", "mm", "2 mm", 2.0, "collar; box", "S",
    "Height of the boss. Two millimetres are enough to keep the insert out of the band and to centre the box."),
 ("Th_ear_box", "mm", "5 mm", 5.0, "box", "S",
    "Thickness of the box's ear: it must contain the pocket for the boss, 2 deep, and leave 3 of bottom around the screw."),
 ("R_in_ear", "mm", "76 mm", 76.0, "box", "S",
    "How far the ear goes in under the collar flange. At 76 the screw has 5.5 mm of ear on one side and 4.5 on the other."),
 ("Ang_ear_front_A", "deg", "-29 deg", -29.0, "box; collar - front ear", "S",
    "The FRONT ears sit where the box actually has material at that level, and not where it would be convenient: at z -8..-3 the box exists only on the two heads of the compartment, the rib at -30..-28 and the head wall beyond the board. In the rest of the mechanical compartment there is nothing to screw into, because that compartment is open towards the collar. This is the head rib on the side opposite the pivot; it also lies outside the travel of the arm, which occupies -13.4..+44.7 below z 0.5. Those two angles are no longer written by hand: they come from corsa_braccio.passaggio(), so they follow the real travel. The number from before, -16..+44, was the result of the old sweep invented by hand and did not correspond to anything measured - the conclusion, however, does not change, because -29 lies outside both intervals."),
 ("Ang_ear_front_B", "deg", "Ang_board + (atan(((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao - Th_walls_box) / sqrt(R_out_collar ^ 2 - ((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao - Th_walls_box) ^ 2)) + atan(((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao) / sqrt(R_out_collar ^ 2 - ((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao) ^ 2))) / 2", 71.10, "box; collar - front ear", "D",
    "The second front ear sits on the HEAD WALL, where the box has material at that level: at half the thickness of the head, at the radius at which the box comes up to the collar. It used to sit on the partition wall between the two compartments, which disappeared along with the electronics compartment. The third front ear, which sat on the electronics compartment, is gone: beyond the head there is no box to hold down, and between the two heads the compartment is open towards the collar."),
 ("Ang_ear_rear_A", "deg", "-24 deg", -24.0, "box; collar - rear ear", "S",
    "The three REAR ears rest on the ceiling of the compartment, which covers the whole sector up to the head at the right level. They must stay outside the two zones of the sensor bracket, -46..-34 and +44..+56 with the bracket at rest - and each of those zones widens by Halfw_slot_collar, because the bracket rotates on its slot."),
 ("Ang_ear_rear_B", "deg", "20 deg", 20.0, "box; collar - rear ear", "S",
    "This one falls under the spring, which pushes at 21 degrees: it is the screw that takes the full pull."),
 ("Ang_ear_rear_C", "deg", "67 deg", 67.0, "box; collar - rear ear", "S",
    "The last one before the head. It was at 60, and there the sensor bracket, rotating on its slot to go and pick up the screws, touched this ear after a tenth of a degree: the bracket at rest fitted, the one being adjusted did not. At 67 it stays outside the whole slot, with its boss."),
 ("Ang_screw_A", "deg", "-40 deg", -40.0, "collar - M3 slot, side opposite the pivot", "S",
    "Angle of the first M3 anchor screw relative to the centre of the window. Absorbed by a slot, because the real position is not known precisely."),
 ("Ang_screw_B", "deg", "50 deg", 50.0, "collar - M3 slot, pivot side", "S",
    "Angle of the second screw. The two must add up to 90 degrees."),
 ("Th_flange_collar", "mm", "3 mm", 3.0, "collar", "S",
    "Thickness of the two flanges that fold over onto the faces of the body."),
 ("Cl_rib_head_body", "mm", "1 mm", 1.0, "box - web between head, skirt and wheel", "S",
    "Gap between the web at the head and the cylinder of the wheel body. The web is a wall that stiffens the corner between the head and the skirt."),
 ("L_rib_head_skirt", "mm", "17 mm", 17.0, "box - web between head, skirt and wheel", "S",
    "How far along the skirt, from the head plane, the web runs before its straight edge goes back to the wheel. Seventeen, from the sketch of the web: it ends 17 mm from the head, where the skirt is at r 86."),
 ("Halfw_slot_collar", "deg", "5 deg", 5.0, "collar - M3 slots; sensor_bracket - pockets in the bottom", "S",
    "Half width of the two M3 slots in the rear flange. It absorbs the real position of the rear plate screws, which is not known precisely. It also decides how far the sensor bracket can rotate, since it follows the screws by rotating about the magnet: that is why the pocket the flat bottom leaves for it is as wide as its outline swept over this whole angle."),
 ("Halfw_ear_box", "deg", "5 deg", 5.0, "box - ears; collar - pockets in the bottom", "S",
    "Half width of the box's ears. It was a 5 written by hand in the box, and the flat bottom of the collar must leave the rear ears a pocket that follows them."),
 ("Cl_pockets_bottom", "mm", "0.5 mm", 0.5, "collar - flat bottom", "S",
    "Clearance all around the pockets that the flat bottom of the collar leaves for the rear ears and for the paddles of the bracket. The pockets must NOT locate anything: the box is located by the bosses, the bracket by the magnet. A close-fitting pocket would be a second reference in conflict with the first."),
 ("Cl_aperture_clutch", "mm", "3 mm", 3.0, "collar - clutch window", "S",
    "How much empty space must remain between the clutch wheel and the edge of the collar window, all round. Before, it did not exist: the window was three numbers unconnected to one another - a half width of 15 degrees chosen by hand and two offsets written in the code - which by chance left 1.5 mm. On a test print the clutch passed almost flush, and that is too little for a printed part with a wheel turning in it: closing that millimetre and a half takes no more than the print tolerance of the collar, the TPU ring deforming under the 22.3 N, and the eccentricity of the disc that makes the arm swing. Both the half width of the window and its two z levels derive from this, so if this number changes the window follows the clutch on its own. It costs stray light, but less than it seems: vertically the window is already covered by the body, which above z 14.3 is solid and below z 3 is already open for the cut of the rib, so the only real price is the angular widening, a millimetre and a half per side."),
 ("Ang_aperture_clutch", "deg",
    "acos((R_out_collar ^ 2 + Cd_motor ^ 2 - (D_clutch / 2 + Cl_aperture_clutch) ^ 2) / (2 * R_out_collar * Cd_motor))",
    16.026116, "collar - clutch wheel passage", "D",
    "Half width of the opening in the collar for the passage of the clutch wheel. It is no longer chosen by hand: it derives from the clearance. The point where the window really pinches is the edge between the side of the cut and the OUTER surface of the band, at R_out_collar: going outwards the side comes closer to the clutch axis, so the largest radius is the worst. The cosine rule on the triangle disc axis - clutch axis - edge gives the angle that puts that edge at D_clutch/2 + clearance from the clutch axis."),
 ("Ang_aperture_grub", "deg", "acos((R_out_collar ^ 2 + Cd_motor ^ 2 - (D_collar_grub / 2 + Cl_aperture_clutch) ^ 2) / (2 * R_out_collar * Cd_motor))", 6.51, "collar - recess for the grub-screw collar", "D",
    "Half width of the recess in the collar for the GRUB-SCREW COLLAR of the clutch, which is a different thing from the tread window and sits higher up. When the clutch was turned over, the grub-screw collar went above the hub, and growing up to z 19.50 it came out of the window, which ends at 14 - its inner edge touches the collar band at r 85 out of 86, for 34 mm3.\n\nA recess of its own is made instead of raising the window because the window is as wide as the TREAD, and raising it by five and a half millimetres over that whole width would eat the band exactly where it carries the upper flange. The grub-screw collar is less than half the tread, and its recess takes away less than a third of the material.\n\nSame cosine rule as the window, with the radius of the grub-screw collar in place of that of the tread."),

 # ---- BOX: the grip for turning the wheel by hand ----------------------
 # Once the machine is assembled the knurled rim of the wheel ends up under the
 # box and the disc can no longer be turned with the fingers. The grip gives
 # that gesture back: the wall steps in until it passes BELOW the radius of the
 # clutch tread, and the tread stands out of the opening like the wheel of a
 # mouse. The ratio is comfortable on its own - a 50 mm clutch on a 145 mm disc
 # - so a little over half a turn of a thumb moves one filter along.
 ("Proj_tread_grip", "mm", "2 mm", 2.0, "BOX - grip for turning by hand", "S",
    "How far the clutch tread stands out of the recessed wall. Everything else about the grip descends from this, and it is the only figure chosen by hand: larger gives the thumb more to hold, but the wall steps in by as much and the recess deepens. Two millimetres is what the knurled rim of the manual wheel stood out by - that is, the grip this machine had before it was motorised."),
 ("R_grip_box", "mm", "Cd_motor + D_clutch / 2 - Squash_clutch - Proj_tread_grip", 120.10, "BOX - grip for turning by hand", "D",
    "Radius of the OUTER face of the wall inside the recess, from the wheel axis. Not a chosen number: it is the radius of the tread less how much of it is to show, so if the clutch ever changes diameter the recess follows on its own. The ordinary wall stands at R_out_box = 130, so here it steps in by nine and nine tenths. Squash_clutch is in there because the tread that the thumb finds is not the one on the drawing: in service the arm holds the clutch against the disc and the rubber is squashed by that much, so the tread sits four tenths further in. Left out, the grip measured two millimetres on the solid and gave one point six in the hand. As the TPU wears the arm follows it inwards and the tread shows less: a millimetre still, with the whole of Wear_TPU_allowed gone."),
 ("Cl_grip_clutch", "mm", "0.5 mm", 0.5, "BOX - grip for turning by hand", "S",
    "Air between the turning clutch and the edge of the opening, all round. Less generous than the 3 mm of the clutch window in the collar, and for a reason: there the window has to let the clutch through while it is being ASSEMBLED, here the clutch is already in place and the only movement left is rotation about a fixed axis. What remains is the half millimetre that print tolerance and the squash of the TPU under 22.3 N need."),
 ("Room_travel_grip", "mm", "1 mm", 1.0, "BOX - grip for turning by hand", "S",
    "Road left to the arm PAST its end stop before the clutch would touch the edge of the opening. On the spring side the arm has no end stop of its own yet, and what stops it is the clutch meeting the box; check_audit asks for half a degree of travel beyond the nominal limit, which on the 61.33 mm of lever between pivot and clutch axis is 0.54 mm. A millimetre covers that with something to spare."),
 ("Halfw_grip_slot", "deg",
    "acos(((R_grip_box - Th_walls_box) ^ 2 + Cd_motor ^ 2 - (D_clutch / 2 + Open_travel_arm + Room_travel_grip + Cl_grip_clutch) ^ 2) / (2 * (R_grip_box - Th_walls_box) * Cd_motor))",
    10.44, "BOX - grip for turning by hand", "D",
    "Half width of the opening the tread stands out of. Same cosine rule as Ang_aperture_clutch, but the critical radius is the other way round: in the collar the band sits INSIDE the clutch and pinches at the largest radius, here the wall sits OUTSIDE it and the corner that comes nearest the clutch axis is the one on the INNER face, at R_grip_box - Th_walls_box. Taking the outer radius instead would make the opening two degrees narrower, and the wall would touch the clutch just inside its edge. And what the opening has to clear is not the clutch where it is drawn but the whole of what it SWEEPS: the arm carries it Open_travel_arm further out, which on the drawing is a millimetre and a half and is where the arm is held while the wheel goes in. Derived from the clutch standing still, the opening came out at 8.1 degrees and the audit caught it - the clutch touched the box at exactly the end of the travel, with no road left."),
 ("Marg_grip_box", "mm", "2.5 mm", 2.5, "BOX - grip for turning by hand", "S",
    "The band of wall left around the opening inside the recess: at the sides, where it becomes an angle, and below, where it stays millimetres. It is there so that the opening does not break out onto the edge of the recess, which is where the stepped-in wall joins the ordinary one."),
 ("Halfw_grip_box", "deg", "Halfw_grip_slot + atan(Marg_grip_box / R_grip_box)", 11.63, "BOX - grip for turning by hand", "D",
    "Half width of the recess, that is, of the stretch where the wall stands stepped in. It is the opening plus the margin, turned into an angle at the radius of the recess: one margin, declared in millimetres, serving both at the side and below. THE VALUE IS DECLARED TO TWO DECIMALS, and so is the one it builds on, because the editor's model rounds every value it computes to two (ui_model) and this is the one derived quantity in the project that stands on ANOTHER derived quantity: the rounding of the first compounds into the second, and at 11.6374 against the model's 11.63 it ran past the five thousandths the guardian of the derived values allows. Breaking the chain by writing the cosine rule out again here would fix the arithmetic and put the same quote in two places, which is the older and worse defect. Seven thousandths of a degree is fifteen microns of recess."),
 ("Z_grip_box", "mm", "Z_top_clutch - Cl_grip_clutch - Marg_grip_box", 3.0, "BOX - grip for turning by hand", "D",
    "The level at which the recess begins, that is, the lowest point where the wall is already fully stepped in. Below it the wall splays back out at 45 degrees until it meets its ordinary position: that splay is what keeps the stepped-in wall from beginning in mid air, which when printed would mean supports inside the box."),
 ("Ang_overhang_printing", "deg", "45 deg", 45.0, "printing - steepest unsupported overhang", "S",
    "The steepest overhang the printer manages without supports, measured from the vertical. Forty-five degrees is what the whole part is tuned to. It lives among the parameters rather than in the code because the two surfaces that descend from it - the splay under the recess and the roof of the opening - have to move TOGETHER if the part is ever printed to another profile."),
 ("Th_cover_grip", "mm", "Th_walls_box", 2.5, "BOX - cover of the grip", "D",
    "Thickness of the cover that closes the recess. It is the thickness of the wall it stands in for: closed, the cover remakes the profile of the back, and from outside the box is the one it was before."),
 ("Th_tab_cover_grip", "mm", "3 mm", 3.0, "grip cover - tabs at the foot", "S",
    "Radial thickness of the two tabs under the foot of the cover, which drop into pockets in the box: thick, because of how it prints. The cover prints upside down: a tab is the last thing printed, with its layers across its length, and a thin one breaks between layers."),
 ("W_tab_cover_grip", "mm", "10 mm", 10.0, "grip cover - tabs at the foot", "S",
    "Width of each tab along the back."),
 ("L_tab_cover_grip", "mm", "5 mm", 5.0, "grip cover - tabs at the foot", "S",
    "How far each tab goes down into its pocket, below the foot of the cover."),
 ("Ang_tab_cover_grip", "deg", "8 deg", 8.0, "grip cover - tabs at the foot", "S",
    "Where the +y tab stands, from the axis of the clutch. The -y one is not a parameter: it goes as far towards -y as the back is still the circle about the wheel, which the generator measures - past that the back is the arc about the motor and there is no material under the foot of the cover for a pocket."),
 ("Wall_pad_cover_grip", "mm", "2 mm", 2.0, "grip cover - tabs at the foot", "S",
    "Material round each pocket, in the pad that the box grows under the foot of the cover."),
 ("Dp_groove_cover_grip", "mm", "2 mm", 2.0, "grip cover - tongue at +y", "S",
    "How deep the tongue at the +y end of the cover goes into the groove of the end wall; the end wall is made thicker by as much."),
 ("W_groove_cover_grip", "mm", "2.6 mm", 2.6, "grip cover - tongue at +y", "S",
    "Width of the groove in the +y end wall: the tongue is this minus a clearance each side, 2 mm, centred between the stepped-in wall and the back."),
 ("Cl_cover_grip", "mm", "0.3 mm", 0.3, "BOX - cover of the grip", "S",
    "Clearance all round the cover. The cover is a part that goes on and comes off many times in the life of the machine - every time the filters are cleaned - so it wants the clearance of a sliding fit and not that of a snap: a cover that has to be forced in the first time is, by the tenth, either worn or stuck."),

 ("Cl_entry_motor", "mm", "1 mm", 1.0, "single part - door over the motor", "S",
    "Air round the silhouette of the motor where it drops in from above: the motor goes in first, straight down from the top, then the arm, then the screws. The door in the roof let the motor down to z 24.5 only: below it the collar ring, r 79.5..86.5 from z 14, stood across its path over 6 mm. The cut is the motor's own silhouette - read from the maker's STEP, sections every millimetre, without the leads, which the STEP draws as rigid bars and which bend - grown by this much, from the bottom of the motor up through the roof: it takes only what the motor's way down needs. Shifting the motor out while it drops, then sliding it in, was measured and rejected: it saves collar only by notching the outer arc wall, the face seen from outside."),
 ("D_lead_motor", "mm", "0.91 mm", 0.91, "single part - hatch under the motor", "R",
    "Thickness of one motor lead where it leaves the body, READ FROM THE MAKER'S STEP (14HS10-0404S.STEP: four bars 0.91 mm square, starting at the body face on the +y side). A catalogue figure, not a caliper one: the real leads are round and insulated, and have not been measured. It is here because the leads bend down along the body when the motor comes up through the hatch, and the hatch must leave them room all round - the whole hatch is widened a little rather than cutting a slot for the wires, which looks bad."),
 ("Cl_hatch_motor", "mm", "Cl_entry_motor + D_lead_motor", 1.91, "single part - hatch under the motor", "D",
    "Air round the motor's silhouette in the hatch under the motor, all round and not only on the side of the leads (no slot). The hatch is also cut on the ENVELOPE of the motor over the whole travel of the arm (sagoma_motore.inviluppo_corsa), because the motor moves 1.5..1.8 mm sideways at the ends of the travel and the screw ears outside the hatch rise above its bottom."),
 ("Cl_entry_clutch", "mm", "1 mm", 1.0, "single part - ring cut for the clutch's way in", "S",
    "Air per side round the clutch where it slides in radially from the middle of the collar, through the cut in the collar ring (strategy C): the clutch goes in before the wheel and before the motor, because on the shaft it is caged under the roof. Like Cl_entry_motor, a passage made once."),
 ("R_fillet_collar_arc", "mm", "17 mm", 17.0, "single part - fillet between collar and motor arc, -y side", "S",
    "Radius of the concave fillet that joins the collar's outer face to the arc wall round the motor, on the -y side. There the ring cut for the clutch's way in (strategy C) had left the collar ring open to the outside; the fillet closes it from outside. It was 10, from a sketch; it is 17 since the cover's second screw moved into it. The pocket of that screw's tab reaches past the collar's outer face (r 82 + 4.8 against 86), and the fillet is the only wall it has there: at 10 that wall was 0.25 mm, at 16 1.5, at 17 about 1.7 - the generator measures it on the solid and stops under 2 * Th_min_wall_printing."),
 ("Edge_opening_motor_box", "mm", "75.5 mm", 75.5, "single part - door over the motor", "S",
    "The straight edge of the door over the motor, on the collar side. It was PORTA_X[0] written in solids_box_collar.py; since the cover screws into an insert placed from this edge the assembly needs it too, and a number in two files drifts."),
 ("Th_tab_cover", "mm", "2 mm", 2.0, "cover - tab on the collar", "S",
    "Thickness of the tabs by which the cover goes over the collar, and depth of their pockets in the collar (plus Cl_cover_grip). The screws are socket head and sit on top of the tab, their knurled heads proud of the roof so they turn by hand; two millimetres of tab under the head leave three under the pocket for the insert, which is what the collar has there: 5 mm from z 23 to the roof. (It was sized for the cone of a countersunk M3 before.)"),
 ("R_tab_cover", "mm", "4.5 mm", 4.5, "cover - tab on the collar", "S",
    "Radius of the round end of the tab about the insert: the countersunk head is Ø6, so a millimetre and a half of tab all round it."),
 ("Off_insert_cover", "mm", "16 mm", 16.0, "cover - insert in the collar", "S",
    "Where along the straight edge of the door the insert of the cover goes. NOT on the axis of the clutch: there the collar between its gasket groove (r 70) and the door (x 75.5) is 5.5 mm wide, and a Ø5 insert would keep a quarter of a millimetre a side. At 16 the strip is 7.5 wide; the generator measures the wall on the solid and stops under 0.6."),
 ("Wall_insert_cover", "mm", "1 mm", 1.0, "cover - insert in the collar", "S",
    "Material left between the insert of the cover and the edge of the door: it fixes the x of the insert from the door, instead of a number written by hand."),
 ("L_screw_cover", "mm", "6 mm", 6.0, "bought parts - cover screw", "R",
    "Length under the head of the two M3 that hold the grip cover. They are SOCKET HEAD, DIN 912, with a knurled head, not countersunk: the cover comes off to clean the filters and the screws must undo by hand (knurled DIN 912 M3 are easy to find, 5 to 20 mm). DIN 912 measures under the head: tab 2 + clearance 0.3 + insert 3, and the 0.7 left over goes into the hole below the insert; an M3 x 6 is a common length."),
 ("L_min_support_printing", "mm", "1 mm", 1.0, "printing - steepest unsupported overhang", "S",
    "The side of the smallest square a support could stand on. Used by the check that hunts for overhangs: a downward-facing face smaller than this squared is not reported, because no support can be placed on it and none could be broken off it afterwards - the slicer bridges it in a layer. It is a real limit of the process and not a threshold tuned until the check passed: when the grip was drawn, the two faces it lets through are the four hundredths of a square millimetre left by truncating the cone of each detent, and everything else in that corner of the part came out at zero."),
 ("D_nozzle_printing", "mm", "0.4 mm", 0.4, "printing - nozzle", "S",
    "Diameter of the printer nozzle, 0.4 on the reference printer. It is here for one reason: the thinnest wall worth printing, Th_min_wall_printing, descends from it, and check_thin.py and the generators that trim slivers read that one."),
 ("Th_min_wall_printing", "mm", "2 * D_nozzle_printing", 0.8, "printing - thinnest wall", "D",
    "The thinnest wall worth printing: two lines of the nozzle. Thinner than this, the slicer prints one line that stands alone, or drops the wall altogether. check_thin.py reports every place of a printed part narrower than this in a layer; where a generator leaves a sliver where two cuts nearly meet, it trims it back to this, or takes it away whole."),

 ("H_notch_cover_grip", "mm", "3 mm", 3.0, "BOX - cover of the grip", "S",
    "Height of the nail notch, the groove across the outer face of the cover that gives a fingernail something to pull up on. Its ROOF is the underside of the top web, so the nail bears on the web itself and not on a ledge invented for the purpose - three millimetres is what a fingernail needs under it, and nothing below the notch has to be thinned to make room."),
 ("Dp_notch_cover_grip", "mm", "1.2 mm", 1.2, "BOX - cover of the grip", "S",
    "How deep the nail notch cuts into the cover, out of the Th_cover_grip it has. What is left behind it is more than a millimetre, which is plenty for a part that carries nothing. Deeper would grip better and would start to matter to a cover that is already thin."),
 ("L_notch_cover_grip", "mm", "16 mm", 16.0, "BOX - cover of the grip", "S",
    "Width of the nail notch along the back. A finger is wider than this, so the figure is about finding it in the dark rather than about the grip: it is centred on the clutch axis, which is the same place the opening is, so the notch also says where the grip is without looking."),

 ("Ang_axis_spring", "deg", "20.5 deg", 20.50, "spring axis, perpendicular to the arm", "D",
    "Inclination of the spring axis. It is perpendicular to the arm, so the force turns entirely into moment about the pivot."),
 ("R_rest_spring_arm", "mm", "106.8 mm", 106.80, "arm - side of the plate; assembly_plan", "M",
    "Radius at which the spring rests on the arm: it is the outer side of the plate, measured on the STEP along the spring axis. It was 96.22, which was the bottom of the centring dimple, buried ten millimetres inside the solid: the spring would never have reached it. Then 106.2, the side of the wedge; now 106.8, because with L_plate_solid the full width reaches beyond the spring attachment and the side there is the straight side of the plate, no longer the ramp. It is re-measured every time the shape of the arm is touched, and the seat in the box follows it on its own."),
 ("R_seat_spring_box", "mm", "R_rest_spring_arm + L_spring_fitted", 117.93, "BOX - fixed end of the spring; assembly_plan", "D",
    "Radius of the fixed end against which the spring is compressed. It is not a choice: it is where it has to be for the fitted spring to be as long as it should. The spring axis is almost radial, so the sum of the radii equals the distance along the axis to within two hundredths."),
 ("L_spring_free",       "mm", "13.5 mm",   13.50, "arm; box - MEASURED", "M",
  "Free length of the preload spring, MEASURED: the spring from a clothes peg, 0.9 x 6.7."),
 ("D_wire_spring", "mm", "0.9 mm", 0.9, "spring - wire; MEASURED", "M",
    "Wire of the preload spring, MEASURED with the caliper."),
 ("D_spring_in", "mm", "4.6 mm", 4.6, "spring - inside diameter; MEASURED", "M",
    "Inside diameter of the preload spring, MEASURED: 4.6, a doubtful reading because the caliper jaws hardly go in - from the wire and the outside it would be 6.7 - 2 x 0.9 = 4.9. The spigot is sized on the measured 4.6, the worse of the two, so it goes in either way."),
 ("N_coils_spring", "", "6", 6.0, "spring - total coils; COUNTED", "M",
    "Total coils of the preload spring, COUNTED, six (seven had been assumed). It gives the solid length (coils x wire), and from it the stiffness out of the scale test."),
 ("Force_solid_spring_N", "", "46.1", 46.1, "spring - force near solid; MEASURED", "M",
    "The force of the preload spring pressed almost solid on a kitchen scale: 4.7 kg, MEASURED."),
 ("Rate_spring", "N/mm", "Force_solid_spring_N / (L_spring_free - N_coils_spring * D_wire_spring)", 5.69, "spring - stiffness", "D",
    "Stiffness of the preload spring from the scale test: the force near solid over the travel to solid (solid length = coils x wire, with the coils assumed). The spring formula gave 5.9..7.4 N/mm for 4..6 active coils (stainless): with six coils counted, four active, the scale says 5.7 - close."),
 ("L_spring_fitted", "mm", "L_spring_free - Force_spring_N / Rate_spring", 11.13, "length at Force_spring_N", "D",
    "Length at which the spring develops the design force: from the free length and the stiffness measured on the scale. The seat in the box follows it (R_seat_spring_box). Stiff as it is, the preload grub is sensitive but not too much: one turn of an M4 (0.7 mm) is Rate_spring x 0.7, about 4 N, so it is set by quarter turns."),
 ("D_spigot_spring", "mm", "D_spring_in - 0.4 mm", 4.2, "arm - spring centring spigot", "D",
    "Diameter of the spigot that goes into the inside of the spring and keeps it on axis: two tenths of play per side on the measured inside diameter, which is the worse of the two readings, so the spring slides on without forcing and its end does not escape."),
 ("Proj_spigot_spring", "mm", "4 mm", 4.0, "arm - spring centring spigot", "S",
    "How far the spigot sticks out from the side of the arm into the spring. A good third of the fitted spring is enough to guide it, and it stays clear of the bottom of the pocket in the box, which engages another seven from the other side."),
 ("Dp_spigot_spring", "mm", "4 mm", 4.0, "arm - spring centring spigot", "S",
    "How far the spigot continues INSIDE the solid of the plate. On the finished part it cannot be seen, and that is exactly the point: without it, the cylinder started out resting on the side with only its base face - a butt joint, which is where the part breaks off. It also serves as a margin: R_rest_spring_arm is a rounded dimension, and if it falls a few tenths outside the real side the spigot really does start out detached."),
 ("R_fillet_edges_box", "mm", "4 mm", 4.0, "BOX - fillets on the vertical edges", "S",
    "Radius of the fillets on the VERTICAL edges of the outline in plan, that is the corners the hand meets when picking up the instrument from the side. They must not be confused with the horizontal chamfer that used to be on the edges of the back: that was removed because it was the wrong thing, not the wrong amount - from the side you do not touch the edge of the back, you touch the corner of the outline. Four millimetres can be felt with a finger and cost little: at the corner the fillet cuts in radially by 0.29 times its own radius, that is 1.2 mm of the 2.5 of the back wall, and behind it there is the head wall anyway, 9.25 mm thick on the electronics lobe and 17.25 on the mechanical one. Above 5 mm, on the other hand, the fillet would start to break through the back."),
 ("R_arc_back_box", "mm", "R_out_box - Cd_motor", 32.5, "BOX - the arc around the motor", "D",
    "Radius of the arc that closes the mechanical lobe of the box, centred on the MOTOR AXIS. It replaces the old setback, a curve centred on nothing in particular that came back to the back at -8 degrees. It is not chosen: it is the radius that makes the arc TANGENT to the back on the line from the wheel centre through the shaft, so the outline has no kink there. Beyond the shaft the box then only wraps what it holds. Measured on the real assembly with the arm swung over its whole travel (src/study_motor_arc.py): arm, motor and clutch reach 23.9 mm from the shaft, the inner face of the arc sits at 30.0 - 6.1 mm of air."),
 ("Ch_roof_box", "mm", "10 mm", 10.0, "BOX - chamfer along the top outer edge", "S",
    "Chamfer, at 45 degrees, along the whole edge where the outer wall of the box meets its roof: the back, the arc round the motor and the head. It became possible when the roof rose 3.5 mm to be flush with the collar, and it is a sloping WALL of Th_walls_box, not a cut: the void is chamfered by the same amount one wall thickness in. It saves material, looks better, and it is the face a hand meets reaching over the box; facing up at 45 degrees it prints without supports."),
 ("Z_top_collar", "mm", "H_body + Th_flange_collar + H_boss_insert", 28.0, "collar - top face of the rear flange", "D",
    "Height of the top of the collar: the body, the rear flange and the flat bottom under the insert bosses. It is the highest face of the one-piece box+collar, and the roof of the box is flush with it (Z_shoulder_box)."),
 ("Z_shoulder_box", "mm", "Z_top_collar - Th_walls_box", 25.5, "BOX - height at which the mechanical compartment closes", "D",
    "Where the mechanical compartment closes. It is DERIVED: the roof of the box, one wall thickness above this, is flush with the top of the collar. REJECTED: 22, the clutch hub plus three millimetres, which left a 3.5 mm step between roof and collar with the three pillars of the old rear ears sticking out of it - one flat top prints, a step does not, and it costs no height because the collar is already that tall. The 3.5 mm gained inside is what the 10 x 10 chamfer along the outer top edge eats into."),
 ("D_seat_spring_box", "mm", "9.6 mm", 9.6, "BOX - pocket that guides spring and cup", "S",
    "Diameter of the pocket in the box. It guides the spring, which is 8.9 outside, and the cup slides inside it."),
 ("Th_cup_spring", "mm", "3.5 mm", 3.5, "spring_cup", "S",
    "Thickness of the disc of the cup, from the face the spring rests on to the dish the grub screw pushes into. Three and a half millimetres of ASA under 22.3 N are not in question: the thickness is dictated by printing, not by the load."),
 ("Cl_cup", "mm", "0.4 mm", 0.4, "spring_cup in its seat", "S",
    "Clearance on the diameter between cup and pocket. It must slide without jamming but without rattling, otherwise it tilts crosswise and takes the spring with it."),
 ("D_cup_spring", "mm", "D_seat_spring_box - Cl_cup", 9.2, "spring_cup", "D",
    "Outside diameter of the cup, derived by difference from the pocket."),
 ("Travel_preload", "mm", "2 mm", 2.0, "BOX - grub screw travel", "S",
    "How far the cup can go forward and back from its nominal position. The pocket is just long enough for the travel on one side, the cup, and the travel on the other: that way the preload can be both increased and decreased, instead of only being slackened."),
 ("D_dish_grub", "mm", "D_grub_spring - 0.8 mm", 3.2, "spring_cup - dish for the grub screw tip", "D",
    "Diameter of the dish on the back of the cup. Narrower than the grub screw, so the tip centres itself in it and cannot wander over the back."),
 ("D_out_insert_M4", "mm", "6.3 mm", 6.3, "BOX - heat-set insert for the grub screw; MEASURED with the caliper", "M",
    "Outside diameter of the M4 heat-set insert of the reference build, measured with the caliper on a sample and not taken from a catalogue. Beware: it is bigger than the most common M4, which is around 5.6. Anyone with different inserts changes this number and L_insert_M4, and the seat, lead-in and boss length follow."),
 ("L_insert_M4", "mm", "8.1 mm", 8.1, "BOX - heat-set insert for the grub screw; MEASURED with the caliper", "M",
    "Length of the M4 insert of the reference build, measured. It is what decides how long the boss must be: the seat cannot break through into the cup pocket, because there the insert would no longer find plastic around it. A SECOND TYPE exists, 6 x 6 M4 inserts, two millimetres shorter and a touch narrower (hole 5.65 instead of 5.95, hence more wall). HERE THE 8.1 ONES ARE KEPT, and the reason must be remembered: this grub screw sets the SPRING PRELOAD, pushes on the back of the cup under 22.3 N and is adjusted repeatedly, so thread engagement is worth more than the two millimetres of boss saved - and in this design a short engagement has already been noted as the defect not to repeat, on the 3 mm M3s. The 6 x 6 ones remain fine for a fixing that carries no load."),
 ("D_hole_insert_M4", "mm", "D_out_insert_M4 - 0.35 mm", 5.95, "BOX - insert seat", "D",
    "Hole of the seat. It is deliberately NARROWER than the insert: as it melts in, the insert must bite into the plastic and grip it, not slide into it. Three and a half tenths of interference is the rule for a 6.3 outside diameter; on a smaller insert it scales by itself, because it is a difference and not a fixed number."),
 ("Dp_seat_insert_M4", "mm", "L_insert_M4 + 0.5 mm", 8.6, "BOX - insert seat", "D",
    "Depth of the seat: deliberately a touch MORE than the insert. If it were exact or short, the insert would stay proud of the face or push the molten plastic to the bottom instead of letting it flow back, and would end up crooked."),
 ("D_leadin_insert_M4", "mm", "D_out_insert_M4 + 0.6 mm", 6.9, "BOX - seat lead-in", "D",
    "Diameter of the countersunk mouth. Wider than the insert, so the insert sits straight on it on the soldering iron tip before it starts to go down, and the displaced plastic has somewhere to go instead of bulging the face."),
 ("Dp_leadin_insert_M4", "mm", "0.8 mm", 0.8, "BOX - seat lead-in", "S",
    "Depth of the conical chamfer at the mouth of the seat."),
 ("Th_retain_insert_M4", "mm", "1.5 mm", 1.5, "BOX - wall that retains the preload insert", "S",
    "How much ASA remains OUTSIDE the preload insert, between its outer face and the outer face of the boss. It is the wall that retains it, pierced only by the passage for the grub screw: the spring pushes the cup, the cup the grub screw and the grub screw the insert OUTWARDS, and against this wall the insert works in compression instead of in pull-out. Before, the insert was driven in from outside and those 22.3 N pulled, for the whole life of the machine, in the direction the brass had gone in. One and a half millimetres is plenty for the load - on the ring between Ø4.1 and Ø6.3 it is less than two MPa - and is chosen for printing, not for strength."),
 ("D_grub_spring", "mm", "4 mm", 4.00, "BOX - preload adjustment grub screw", "S",
    "Preload adjustment grub screw, from outside the box. Unscrewing it unloads the clutch for storage."),

 ("--- BOX ---",),
 ("R_out_box", "mm", "130 mm", 130.0, "pianta_scatola", "S",
    "Radius of the outer wall of the box. It must lie beyond the outer edge of the clutch, which reaches Cd_motor + D_clutch/2."),
 ("Free_motor_floor", "mm", "1.5 mm", 1.5, "pianta_scatola - bottom of the mechanical compartment", "S",
    "How far the bottom of the motor sits above the inner face of the floor. It is needed so that the motor does not rest on the bottom - it must hang from the arm, which is what holds it at height - and so that air can pass: it gets warm. One and a half millimetres is what there was when the floor was hand-written at -38, and it was kept the same so as not to change two things at once."),
 ("Z_floor_box", "mm", "-(Z_face_motor + L_motor + Free_motor_floor + Th_walls_box)", -31.5, "pianta_scatola - bottom of the mechanical compartment", "D",
    "The OUTER face of the floor, that is the plane the part is printed on. It was the number -38 written by hand in three different places - the box generator and twice in the electronics one - and it derived from nothing: the day the motor moved, none of the three would have followed it. Now it derives from what really decides the floor: the bottom of the motor, which in turn derives from the face the motor is screwed to. That is why flipping the clutch lowers the machine - the motor goes up, and the floor follows it."),
 ("Th_walls_box", "mm", "2.5 mm", 2.5, "pianta_scatola", "S",
    "Wall thickness. Below 2.5 mm black ASA lets red and near-infrared light through."),
 ("Ang_box_pivot", "deg", "Ang_board + atan(((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao) / sqrt(R_out_collar ^ 2 - ((N_holes_board_L - 1) * Pitch_perfboard / 2 + (L_xiao - (Pin_xiao_per_side - 1) * Pitch_perfboard) / 2 + Proj_usb_xiao) ^ 2))", 71.99, "pianta_scatola", "D",
  "How far the box reaches on the pivot side: it is the outer face of the head, at the radius where the box meets the collar. The head is a plane, not a radius, so the further out, the less far it reaches. The collar must reach at least this far."),
 ("Ang_box_opposite", "deg", "30 deg", 30.0, "pianta_scatola", "S",
  "Angular extent of the box on the opposite side, on the mechanical compartment only."),
 ("L_thread_grub", "mm", "10 mm", 10.0, "pianta_scatola - light labyrinth", "S",
    "Length of the thread of the adjustment grub screw. Light cannot follow the helix, so the thread itself acts as a labyrinth."),

 ("Ang_collar_extended",   "deg","130 deg", 130.00, "collar", "S",
  "How far the collar extends beyond the mechanical compartment to support the electronics one, which would otherwise be left overhanging. Limited by the envelope of the rotator, not by the structure."),
 ("R_envelope_optical",    "mm", "48 mm",    48.00, "collar", "M",
  "Radius to keep clear around the optical axis. It is a MEASUREMENT taken on the telescope, not a choice: the 48 mm are real. What is no longer known is WHAT was measured - the rotator body or the light cone - and they are two different things: the rotator body is a solid obstacle on one side only, the light cone is a volume not to be intruded on from any side. Until it is re-measured, the 48 count as a constraint ON BOTH SIDES: it is the prudent assumption, and it is the one the checks apply. The collar flanges are cut by this cylinder (beyond 130 degrees they would end up inside it), the sensor bracket enters it only with its hub and its cover does not go beyond the bracket. What to go and re-measure, and what would change if the 48 were the rotator, is in ROADMAP.md."),

 ("--- AS5600 SENSOR ---",),
 ("D_pivot_hub", "mm", "7.95 mm", 7.95, "sensor_bracket; dima_magnete", "M",
    "Diameter of the disc pivot, which comes out flush with both faces. The sensor is on the telescope side: there the magnet is glued on top of it and the bracket is centred on it."),
 ("Cl_ring_bracket", "mm", "0.075 mm", 0.075, "sensor_bracket", "S",
    "Radial clearance of the bracket ring on the magnet. It is the first term of the sensor centring budget, so it is kept tight: it turns rarely and by a few degrees, wear is not an issue."),
 ("D_in_ring_bracket", "mm", "D_magnet + 2 * Cl_ring_bracket", 8.15, "sensor_bracket", "D",
    "Inside diameter of the bracket centring ring. It is dimensioned on the MAGNET, not on the pivot: the pivot comes out flush with the face and the ring cannot touch it, while the magnet protrudes by one millimetre and is the only cylindrical thing there is to grip. Before, it was dimensioned on the pivot, 8.55, and left three tenths of play on a centring that allows two and a half in total."),
 ("Comp_hole_printing", "mm", "0.2 mm", 0.2, "sensor_bracket; gap_gauges", "M",
    "How much a hole comes out UNDERSIZE from printing, and hence how much wider it must be drawn. MEASURED on an ASA clutch: hole drawn 5.40, read with the caliper 5.20. Before, it was declared - same value, but assumed - and from it derive the shaft hole, the bearing seat, the M3 clearance holes, the magnet hole and the cap seat: five dimensions that stood on a number never verified. The confirmation is twofold, because the measurement was followed by the working test: the clutch printed with these dimensions slides onto the shaft without forcing and without rattling. It is a number of the MACHINE AND THE MATERIAL, not of the design: whoever prints in another material redoes it, and the way to redo it is this - subtract the measured from the drawn, do not infer it from a symptom."),
 ("R_out_foot", "mm", "10 mm", 10.0, "gap_gauges", "S",
    "Outside radius of the test feet. The bracket hub is at 7.45 because there it is stopped by the web around the M2 holes, but the foot does not have to centre anything nor stay inside an envelope: with the ring emptied by the magnet hole, pierced by the screws and hollowed out under the board, at 7.45 you get a part that breaks in your hand. At 10 the annulus stays almost six millimetres wide."),
 ("R_relief_capacitor", "mm", "6.2 mm", 6.2, "gap_gauges - measured on the printed part", "M",
    "Radius at which the foot is cut straight, on the side opposite the tab. Under the board there is the 104 capacitor, which is the tallest component on the module and does not fit in the three tenths the recess leaves: the foot hit it and the board rested on it instead of on the pads, that is it measured an air gap that was not the right one. Beyond this radius the material serves no purpose - on that side the foot neither centres nor holds anything - and removing it also lets the connector through."),
 ("Halfw_relief", "mm", "4.6 mm", 4.6, "gap_gauges", "S",
    "Half-width of the lowered band in front of the cut, measured from the axis of the M2 holes. Kept within 4.6 because the two rest pads start at 60 degrees, that is at 5 in ordinate: the band goes as far as it can without eating into the plane that holds the board."),
 ("H_bottom_relief", "mm", "0.4 mm", 0.4, "gap_gauges", "S",
    "How much of the lowered band is left standing: two 0.2 layers. It is not zero because the part must stay in one piece - the ring around the magnet hole is the only thing that holds the two pads together - and it is not more because the capacitor passes over it."),
 ("Cl_holes_M2_foot", "mm", "0.1 mm", 0.1, "gap_gauges", "S",
    "How much wider the M2 holes of the test feet are than those of the real bracket. On the bracket the hole is 1.8 and the screw forms its own thread: it is tightened only once and must hold. On the feet the same screw goes in and out seven times, once per height, and at 1.8 every turn re-cuts the thread in a hole already threaded: the material crumbles and the foot splits. One tenth more is enough for the screw to pick up the thread it already found."),
 ("Cl_test_magnet", "mm", "0.1 mm", 0.1, "gap_gauges", "S",
    "How much larger the hole of the test feet is than that of the real bracket. The foot must turn freely on the magnet even if the print compensation is not spot on: a foot that jams costs a print, and in the air gap test one tenth more of centring does not change the AGC reading. More than one tenth, however, is not possible: at 0.2 the possible off-centre reaches 0.275 and exceeds the 0.25 that the AS5600 allows, and the check says so. If the hole comes out tight from printing it is not widened here, Comp_hole_printing is corrected, which is the printer's number and holds for the real bracket too."),
 ("D_hole_magnet_printing", "mm", "D_in_ring_bracket + Comp_hole_printing", 8.35, "sensor_bracket; gap_gauges", "D",
    "The diameter with which the magnet hole is drawn and printed. The design one remains D_in_ring_bracket: this is it plus the print compensation."),
 ("D_magnet", "mm", "8 mm", 8.0, "sensor_bracket - diametral, self-centres on the pivot", "S",
    "Diameter of the diametrally magnetised magnet. Chosen equal to the pivot so it centres itself when placed flush."),
 ("Th_magnet", "mm", "1 mm", 1.0, "sensor_bracket", "S",
    "Thickness of the magnet. It enters the chain that sets the rest height of the board."),
 ("Th_spacer_magnet", "mm", "0.8 mm", 0.8, "magnet_spacer; sensor_bracket; gap_gauges", "S",
    "Thickness of the spacer between the pivot head and the magnet. The pivot comes out flush with the face and the magnet is wider than it: without a spacer the magnet rests on the wheel cover, which is stationary while the magnet turns. The friction itself is negligible - half a gram on a 0.025 ring - but the bead of glue that squeezes out from the edge catches there, and if the disc comes up against its axial stop it is the glue joint that acts as the thrust bearing. On the spacer the magnet stays raised and no longer touches anything. Every tenth here is a tenth less of air gap for the same rest height."),
 ("D_spacer_magnet", "mm", "7.6 mm", 7.6, "magnet_spacer", "S",
    "Diameter of the spacer. Deliberately smaller than the pivot (7.95): that way it cannot touch the cover even if it is glued off-centre, and the centring is still done by the magnet on the pivot and by eye on the aluminium edge. It must be plastic, not metal: it sits inside the magnet's field."),
 ("Ang_module_on_bracket", "deg", "45 deg", 45.0, "sensor_bracket; gap_gauges; sensor_cover", "S",
    "How much the AS5600 module is rotated on the bracket, relative to the orientation in which it was measured (M2 holes on the Y axis, capacitor towards +X). At 45 degrees the module is ALIGNED WITH THE ARMS, and that is what puts everything right. The capacitor - which is also the point where the cable comes out - goes in line with the cable arm: there the arm widens and is pierced, and that hole does two jobs, relief for the capacitor and exit for the cable. The THREE large pads that are not used (PWM, GND, 5V) then fall on the OTHER arm, which is solid material at full height: their support sits on it and is visible, instead of being a bulge on the hub. The first attempt was 135 degrees, for fear that the relief - 9.2 wide on an arm 8 wide - would cut the arm in two: and it really does, but the answer is to widen the arm there, not to move the module elsewhere. At 135 the support ended up overhanging the hub, on the optical axis side, and could not be widened there."),
 ("W_arm_widened_relief", "mm", "15 mm", 15.0, "sensor_bracket", "S",
    "Width to which the cable arm is brought over the stretch where it is pierced for the capacitor. The arm is 8 wide and the hole 9.2: cut like that the arm breaks in two, and indeed when tried the bracket came out in two pieces. At 15 there remain 2.9 of material per side, that is two ribs that bridge the hole. It is material on the side opposite the optical axis, so widening there costs nothing in envelope."),
 ("R_end_widening_relief", "mm", "13 mm", 13.0, "sensor_bracket", "S",
    "How far the widening of the arm extends. It must go past the hole, which ends at r 11.4, otherwise the two ribs rejoin inside the hole instead of outside it."),
 ("Cd_holes_module", "mm", "11.5 mm", 11.5, "sensor_bracket", "M",
    "Centre distance of the two fixing holes of the AS5600 module."),
 ("L_board_module", "mm", "16.85 mm", 16.85, "sensor_bracket", "M",
    "Diameter of the board, which is not rectangular: it is a round with two flats. Measured on the real module."),
 ("W_board_module", "mm", "15 mm", 15.0, "sensor_bracket", "M",
    "Distance between the two flats of the board. The two M2 holes lie on the axis of the flats, not on that of the full diameter."),
 ("D_holes_board", "mm", "2 mm", 2.0, "sensor_bracket - measured on the module", "M",
    "Diameter of the holes in the module board. Measured: the M2 screw is a close fit, so the module does not rattle on the screw. The play that remains in the sensor centring comes from here, no longer from a wide clearance hole."),
 ("D_holes_M2",            "mm", "1.8 mm",    1.8,  "sensor_bracket", "S",
  "Pilot hole for the M2 screws in the hub: the screw forms its own thread. It was 2.2, that is a clearance hole, but under the hub there is the face of the body and there is no room for any nut: the screw turned freely in it and held nothing. 1.8 and not 1.7 because the screws in use have a parallel machine thread, not self-tapping: they have no cutting edges and at 1.7 they would split the hub instead of forming the thread. In printing the hole comes out a scant tenth smaller anyway."),
 ("H_min_foot_test", "mm", "4.8 mm", 4.8, "tools - air gap test feet", "S",
    "Height of the lowest air-gap test foot. The feet were 3.6 to 4.2 before the magnet went on its spacer and the glue was measured (Th_spacer_magnet, Th_glue_stack_magnet): with those the old feet gave gaps from -0.33 to 0.27, and the test bench page showed negative gaps. From 4.8 the gaps start at 0.87, around Gap_nominal."),
 ("N_foot_test", "", "4", 4, "tools - air gap test feet", "S",
    "How many test feet are printed, H_min_foot_test upwards by Pitch_foot_test."),
 ("Pitch_foot_test", "mm", "0.2 mm", 0.2, "tools - air gap test feet", "S",
    "Step between one test foot and the next: the layer height, so the height engraved on the tab is the one that comes out of the printer."),
 ("Gap_nominal", "mm", "0.8 mm", 0.8, "sensor_bracket - adjust with AGC, min allowed 0.5", "S",
    "Air between the top face of the magnet and the chip body. Starting value: it is adjusted by printing feet of different heights and choosing the one with AGC near mid-scale."),
 ("Th_board_module", "mm", "1.6 mm", 1.6, "sensor_bracket - measured on the module", "M",
    "Thickness of the module board, measured with the caliper: 1.6, which is also the standard. It enters only the screw length: the screw goes through the board and what remains goes into the hub, and with 4 mm that leaves 2.4 of engagement."),
 ("L_screw_M2", "mm", "4 mm", 4.0, "sensor_bracket - module screw", "S",
    "Length of the two screws that hold the module. It is not free: under the hub there is the face of the body, so the screw must not poke through. With a 1.6 board and a 3.43 hub an M2x6 would come out underneath, and on the lowest test foot it would lift the part off the face."),
 ("H_body_chip", "mm", "1.63 mm", 1.63, "sensor_bracket - measured on the module", "M",
    "How far the chip body protrudes below the board. Measured: 1.63, not 1.75 as the SOIC-8 datasheet maximum said. It is the third link of the chain that sets the module's rest height, and it shifts the plane by a tenth."),
 ("Th_glue_stack_magnet", "mm", "0.5 mm", 0.5, "measured on the real assembly", "M",
    "How much taller the glued stack comes out than the sum of its parts. Spacer and magnet make 1.8 by design, but measured on the real assembly they protrude 2.3 above the face: half a millimetre goes into the two glue joints and the print tolerance of the spacer. Without this term the bracket comes out half a millimetre too low and the air gap narrows by as much - with the 4.0 foot the real air gap was 0.07, that is the magnet was grazing the chip."),
 ("H_rest_module", "mm", "Th_spacer_magnet + Th_magnet + Th_glue_stack_magnet + Gap_nominal + H_body_chip", 5.13, "sensor_bracket", "D",
    "Height at which the sensor board rests, from the telescope-side face. Since the magnet sits on a spacer, the chain starts from there: everything under the magnet also raises the rest, otherwise the air gap narrows by as much."),
 ("Th_hub_bracket", "mm", "0.8 mm", 0.8, "sensor_bracket", "S",
    "Material left between the module's M2 holes and the edge of the bracket hub. It dictates the hub diameter: before, it was dimensioned on the ring and the M2 holes overhung it by half a millimetre."),

 ("Dp_notch_module", "mm", "1.2 mm", 1.2, "sensor_bracket; gap_gauges", "S",
    "How far the plane under the sensor board is lowered, all around the two pads of the M2 screws. The underside of the module is not smooth: there are SMD resistors and capacitors with their solder joints, and before, the plane was solid, so the board rested on them instead of on the pads. The tallest component measures 0.93, so 1.2 leaves just under three tenths."),
 ("R_components_module", "mm", "4.6 mm", 4.6, "sensor_bracket - measured on the photo of the module", "M",
    "How far the SMD components under the board extend, within the sector of the M2 holes. The four components lie in the diagonal quadrants and go out to r 6.4, but towards the holes the corner of R2 and that of C1 stop at 4.6: this is the number that dictates where the pad can start."),
 ("R_pad_module", "mm", "R_components_module + 0.6 mm", 5.2, "sensor_bracket; gap_gauges", "D",
    "Radius at which the board rest pad starts. It is half a millimetre beyond the components: further in, the board would rest on R2 and C1; further out, too little material would remain around the screw."),
 ("H_capacitor_module", "mm", "4.2 mm", 4.2, "sensor_bracket; gap_gauges - MEASURED", "M",
    "How far the 104 capacitor protrudes below the board. Four point two: the rest plane is 5.13 above the face of the bracket, so under the capacitor 0.93 mm would remain - and the module recess, which removes 1.2, falls three millimetres short. Hence the through hole: the capacitor goes into it and protrudes from the lower face, still staying 0.93 from the body face the bracket rests on."),
 ("Pitch_pads_module", "mm", "2.54 mm", 2.54, "sensor_bracket", "M",
    "Pitch of the module pads, the usual tenth of an inch. It is needed to know WHERE the three free pads fall: in a row on the flat at this pitch, that is at r 7.50 the middle one and 7.92 the two on either side. These numbers lie outside the hub, which ends at 7.45, and that is why their support must come out of the hub instead of stopping at it."),
 ("Ang_pad_pads_free", "deg", "25 deg", 25.0, "sensor_bracket; gap_gauges", "S",
    "Half-width of the support on the side of the three unused pads. The three pads lie within +-18.7 degrees of the centreline, so 25 covers them with six degrees of margin per side. It cannot be wider, and it is a limit that cannot be seen from the drawing: the support comes out of the hub to get under the pads, and the more it is widened the more it protrudes towards the optical axis, which lies right on that side. At 25 degrees the point closest to the axis stays at 40.65, that is outside the 40.55 the hub reaches; at 27 it would already be 40.39 and the bracket would enter the rotator more than the hub, which is the rule not to be touched. Tried: at 50 degrees it drops to 39.58."),
 ("Ang_pad_module", "deg", "30 deg", 30.0, "sensor_bracket; gap_gauges", "S",
    "Half-width of the raised pad around each M2 hole: it is what remains of the rest plane. Narrow on purpose, because the less plane is left the less likely it is to meet a component; there must however remain material around the hole for the screw."),
 ("R_components_diagonal_module", "mm", "6.4 mm", 6.4, "sensor_bracket - measured on the photo of the module", "M",
    "How far the SMD components under the board extend in the DIAGONAL QUADRANTS, that is between one M2 hole and the other. It is the same number that was written only in the prose of R_components_module - 'the four components lie in the diagonal quadrants and go out to r 6.4' - and there nobody could use it: the third rest falls precisely in a diagonal quadrant, and without this dimension its starting radius would have been a hand-written number."),
 ("R_pad_back_v", "mm", "R_components_diagonal_module + 0.6 mm", 7.0, "sensor_bracket; gap_gauges", "D",
    "Radius at which the third rest starts, the one on the back of the V. It is not R_pad_module: that one applies around the M2 holes, where the module carries nothing, while here we are in a diagonal quadrant and the components reach 6.4. Half a millimetre beyond them, by the same rule that already dictates R_pad_module."),
 ("Ang_pad_back_v", "deg", "35 deg", 35.0, "sensor_bracket; gap_gauges", "S",
    "Half-width of the third rest, centred on the back of the V. It is needed because the two earlier pads lie on a single LINE - their centrelines are at 135 and at -45 degrees, that is opposite - and on two rests in a row the board can still rock about that line: widening the pad on the free side, which is what had been done, does not remove the rocking because it stays on the same line. Thirty-five degrees put the third rest at 45 degrees from the line, on the edge that was left unsupported, and the pad still stays within the outline of the board - so it does not get any closer to the optical axis than the board itself already is, which is the yardstick the design also applies to the cover."),
 ("Cl_notch_module", "mm", "0.5 mm", 0.5, "sensor_bracket; gap_gauges", "S",
    "How far the recess under the board extends beyond the outline of the module. The board never rests on the edge of the recess, not even when fitted crooked."),
 ("Ang_bracket_sensor", "deg", "(Ang_screw_A + Ang_screw_B) / 2", 5.0, "sensor_bracket; assembly_plan", "D",
    "Bisector of the sensor bracket, which is a V with one arm for each of the two M3s of the collar. The bracket is on the telescope-side face, where the rotator is: its circumference reaches the disc centre (R_envelope_optical is larger than Off_hole_optical), so any arm heading towards the optical axis enters it, and the only screws on the free side are Ang_screw_A and Ang_screw_B. Derived from them: if the real screws are elsewhere, the bracket follows them."),
 ("R_screw_anchor", "mm", "76.3 mm", 76.3, "sensor_bracket - collar M3s, from M3x12", "M",
    "Radius of the four existing M3 screws on the rear plate, telescope side. The sensor bracket uses the two of the collar, Ang_screw_A and Ang_screw_B: its paddles are clamped on top of the rear flange with the same screw, lengthened: paddle 3.43 + flange 3 make 6.43, and an M3x12 leaves 5.57 engaged of the 6 of thread."),

 ("--- THE MAGNET GLUING CAP ---",),
 ("Cl_cap", "mm", "0.05 mm", 0.05, "magnet_cap", "S",
    "Radial clearance of the magnet seat in the cap: it must slide in by hand and not rattle."),
 ("D_seat_cap", "mm", "D_magnet + 2 * Cl_cap + Comp_hole_printing", 8.30, "magnet_cap", "D",
    "Diameter of the seat the magnet sits in while the glue sets. It carries the same print compensation as the ring hole, for the same reason: without it, the seat comes out undersize and the magnet does not go in. The design clearance remains 0.05 per side, which is what is needed for the seat to hold it square."),
 ("D_cap", "mm", "16 mm", 16.0, "magnet_cap", "S",
    "Outside diameter of the cap. It rests on the telescope-side face around the magnet, so it must be wide enough to sit flat and narrow enough to go into the collar ring."),
 ("Dp_seat_cap", "mm", "4 mm", 4.0, "magnet_cap", "S",
    "Depth of the seat, that is the height of the wall surrounding the magnet. It used to be as deep as the magnet is thick, 1 mm, and in there the magnet was guided by nothing: the slightest thing was enough to set it down crooked. With 4 mm of wall it cannot tilt while going down, and it is eased to the bottom by pushing it through the push-out hole."),
 ("H_cap", "mm", "Dp_seat_cap + 2 mm", 6.0, "magnet_cap", "D",
    "Total height of the cap: the seat plus two millimetres of top, which is what is needed for the push-out hole to have a wall around it and for the part to be picked up with two fingers."),
 ("D_pushout_cap", "mm", "3 mm", 3.0, "magnet_cap", "S",
    "Through hole in the centre of the cap, to push the magnet out if it stays glued inside the seat."),


 ("--- CHECKS (no units, documentation) ---",),
 ("Trq_detent_crest_mNm", "", "142", 142.0, "measured - easy direction", "M",
    "Peak torque to get over the detent crest in the easy direction, measured on the reference wheel before its detent was removed. The detent is always removed now (the motor cannot climb out of its notches, assembly guide chapter 10); the number stays as a conservative load for the motor torque check."),
 ("Trq_hold_mNm", "", "285", 285.0, "measured - hard direction", "M",
    "Torque the detent opposed in the hard direction, measured on the reference wheel before its detent was removed. It no longer holds anything: the detent is always removed now (the motor cannot climb out of its notches), and whether the disc stays still with the motor off is watched by the firmware's drift alarm."),
 ("Force_spring_min_N", "", "6.9", 6.9, "design - MEASURED", "M",
    "The push on the arm, in the direction of the spring, that was enough to drive the filter disc: MEASURED on the reference wheel, 700 g on a kitchen scale, with the tyre in TPU 87A. It replaces, as the ground for the design force, the old estimate from the detent's crest torque (friction 0.6, safety factor 2.5), which was written for a 95A tyre and asked for 22.3 N."),
 ("Force_spring_N", "", "13.5", 13.5, "design", "S",
    "Force of the preload spring at its fitted length: 12-15 N, about twice Force_spring_min_N, the push the hand test found enough with the 87A tyre. The fitted length follows from it and from the stiffness measured on the scale; to be checked on the scale with the spring fitted."),
 ("Preload_N", "", "Force_spring_N * Att_spring / Off_pivot", 6.65, "design", "D",
    "Force with which the clutch presses on the disc: the spring's force through the lever arms of the arm about the pivot. It used to go the other way round - derived from the detent's crest torque, and the spring force from it - which is rejected now that the detent is removed."),
]

# --------------------------------------------------------------------------
# Local overrides
# --------------------------------------------------------------------------
# This file is the base and is not touched by hand: what is changed from the
# editor ends up in parameters_local.py, next to it, which acts as an
# override. So the change reads in two lines instead of in a diff of the
# whole file, it is removed by deleting a file, and the base stays comparable
# with anybody else's.
#
# The file is loaded by path, not by import: parameters.py is imported by
# modules that run with different sys.paths, and must not depend on how
# whoever uses it was started.
#
# The dictionary was called SCOSTAMENTI before the sources moved to English:
# a parameters_local.py written with that name is still read.
def _overrides():
    import importlib.util, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parameters_local.py")
    if not os.path.exists(path):
        return {}
    spec = importlib.util.spec_from_file_location("parameters_local", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "OVERRIDES", getattr(module, "SCOSTAMENTI", {}))


OVERRIDES = _overrides()
if OVERRIDES:
    P = [r if len(r) == 1 or r[0] not in OVERRIDES
         else (r[0], r[1], OVERRIDES[r[0]][0], float(OVERRIDES[r[0]][1])) + tuple(r[4:])
         for r in P]

class _Dimensions(dict):
    """The dictionary of the parameters, which can tell which dimensions it
    was asked for.

    It serves the editor, and it serves for a precise defect: the parameter
    page found the dimension in the drawing BY LOOKING FOR A GEOMETRY WORTH
    THAT NUMBER, and 219 parameters out of 336 share their value with
    another. Choosing the first match and taking it as good means pointing at
    the wrong place without saying so: selecting Cd_holes_board_w, which is
    26, the editor showed the holes of the MOTOR, which are 26 too. It is
    serious because that editor is used with the calipers in hand.

    The tracker solves it at the root: while drawing, it records which
    parameters were read, and whoever writes the entity in the DXF attaches
    their names to it. So the drawing CARRIES WITH IT which dimension it was
    born from, and there is no more guessing. It costs an `if` at every
    parameter read, and it stays off for anybody who is not drawing.
    """
    _tracker = None

    def __getitem__(self, key):
        if _Dimensions._tracker is not None:
            _Dimensions._tracker.add(key)
        return dict.__getitem__(self, key)


def tracker_on():
    """Starts recording which parameters are read."""
    _Dimensions._tracker = set()


def tracker_is_on():
    return _Dimensions._tracker is not None


def read_and_reset_tracker():
    """The parameters read since the last call, and starts again from zero."""
    if _Dimensions._tracker is None:
        return set()
    read = set(_Dimensions._tracker)
    _Dimensions._tracker.clear()
    return read


def tracker_off():
    _Dimensions._tracker = None


D = _Dimensions((r[0], r[3]) for r in P if len(r) > 1)

# The ears of the box: two in front, three behind. They are here, and not in
# every file, because they were three per row written by hand in four
# different places, and removing one somebody would have been forgotten.
EARS_FRONT = ("A", "B")
EARS_REAR = ("A", "B", "C")


def collar_arc_fillet():
    """The concave fillet between the collar's outer face and the arc round the
    motor, -y side: (cx, cy, t1, t2) - the centre of the
    fillet circle, R_fillet_collar_arc, and its tangency on the collar (t1) and
    on the arc (t2). Written once: the generator builds it, check_arc_back
    knows it is there on purpose."""
    import math as _m
    MX, RA = D["Cd_motor"], D["R_arc_back_box"]
    Rf, R1 = D["R_fillet_collar_arc"], D["R_out_collar"]
    a, b = R1 + Rf, RA + Rf
    cx = (a*a - b*b + MX*MX)/(2*MX)
    cy = -_m.sqrt(max(a*a - cx*cx, 0.0))
    return cx, cy, (cx*R1/a, cy*R1/a), (MX + (cx - MX)*RA/b, cy*RA/b)


def chamfer_band():
    """Where the chamfer band on the -y side runs, as angles about the motor
    axis (a0, a1): from the fillet's tangency on the arc round the motor to the
    arc at the grip's edge. The band goes from the box to the cover. Running
    it right up to the collar was rejected: with the fillet raised to the roof
    for the second screw, the band stood between them as a horn, joined to
    the wall only at its foot. The box now keeps its
    chamfer up to the tangency, the raised fillet fills in to it, and the two
    45 degree faces meet there as one."""
    import math as _m
    MX, RA = D["Cd_motor"], D["R_arc_back_box"]
    _cx, _cy, _t1, t2 = collar_arc_fillet()
    a0 = _m.atan2(t2[1], t2[0] - MX)
    th = _m.radians(-D["Halfw_grip_box"])
    sg = MX*_m.cos(th) + _m.sqrt((MX*_m.cos(th))**2 - MX*MX + RA*RA)
    a1 = _m.atan2(sg*_m.sin(th), sg*_m.cos(th) - MX)
    return a0, a1


def fillet_screw():
    """The second screw of the grip cover:
    vertical, at the corner where the collar meets the arc round the motor,
    through a round tab of the cover into an insert in the collar, the fillet
    outside it raised to the roof. (x, y, a_cut): the insert's axis, and the
    wheel angle where the collar ring is cut for the clutch's way in.

    The ring cut is the clutch's radial sweep, |y| < D_clutch/2 +
    Cl_entry_clutch, crossing the ring's inner bound r0 = D_body/2 - 0.5: the
    generator takes it from the clutch's STEP and checks it agrees with this.
    The insert sits Wall_insert_cover from that cut and from r0, so its wall is
    derived and not chosen; the generator measures it on the solid all the
    same. It replaced a screw square to the 45 degree chamfer, into a boss
    hanging inside the arc (REJECTED: that boss and the tab of chamfer next
    to it were clumsy, and the tilted countersink was the one overhang the cover
    had to be forgiven)."""
    import math as _m
    r0 = D["D_body"]/2 - 0.5
    a_cut = -_m.asin((D["D_clutch"]/2 + D["Cl_entry_clutch"])/r0)
    ri = D["D_out_insert_M3"]/2 + D["Wall_insert_cover"]
    rc = r0 + ri
    ac = a_cut - _m.asin(ri/rc)
    return rc*_m.cos(ac), rc*_m.sin(ac), a_cut


def spring_axis():
    """The axis of the preload spring: (Qx, Qy, nx, ny, zm).

    The point Q is where the spring bears on the arm, (nx, ny) the direction
    it pushes in, zm the height of its axis - the mid-plane of the arm's
    plate, not a chosen number. It is here and not inside solids_box.py
    because the check that watches the rib of the boss reads it too: a second
    copy of these four lines would be a copy that drifts, and a check that
    measures in the wrong place watches nothing.
    """
    Lb = D["L_arm"]
    ux, uy = (D["Cd_motor"] - D["R_disc"])/Lb, -D["Off_pivot"]/Lb
    nx, ny = -uy, ux
    # THE MID-PLANE OF THE PLATE COMES FROM THE BOTTOM OF THE ARM, not from
    # the motor face. The two dimensions were the same thing as long as the
    # motor screwed onto the bottom of the plate; once the plate became
    # stepped they came apart, and this line - which the docstring
    # above describes correctly in words - started giving z 2.50 instead of
    # -4.00. Six and a half millimetres: the spring seat in the box ended up
    # above the arm's pad instead of in front of it, and five preload checks
    # started probing thin air.
    return (D["R_disc"] + ux*D["Att_spring"], D["Off_pivot"] + uy*D["Att_spring"],
            nx, ny, D["Z_axis_spring"])


def s_spring_axis(radius):
    """At what distance from Q, along the spring axis, a given radius from the
    disc centre is met."""
    Qx, Qy, nx, ny, _ = spring_axis()
    lo, hi = 0.0, 100.0
    for _ in range(60):
        mid = (lo + hi)/2
        if math.hypot(Qx + nx*mid, Qy + ny*mid) < radius:
            lo = mid
        else:
            hi = mid
    return (lo + hi)/2


def box_ears():

    """(angle, rear) of each ear: rear means on the telescope-side face."""
    return ([(D["Ang_ear_front_%s" % k], False) for k in EARS_FRONT] +
            [(D["Ang_ear_rear_%s" % k], True) for k in EARS_REAR])


# --- where a file goes inside out/ ------------------------------------------
# out/ holds ONLY the parts to print for the final assembly: whoever opens
# the folder to send something to print must not be able to mistake a
# reference for a part, because printing one for the other costs an hour.
# Everything else goes in a subfolder that says what it is - tools, drawings,
# stl, electronics, and now references: the models that serve for reasoning
# but are not printed (the body of the purchased wheel, the disc, the route of
# the cable) plus the assembly, which is not a part. It
# is the same rule as the other subfolders carried all the way.
REFERENCES = ("filter_wheel_body", "filter_disc", "sensor_cable",
              "sensor_cable_axis", "full_assembly",
              # The collar shell is NO LONGER a printed part: it is
              # one half of the single part box_collar, and
              # whoever opens out/ to send something to print must not find
              # it among the parts. Box and collar are no longer two PARTS:
              # they are the two regions of the single part box_collar, and
              # they still serve as bodies of the assembly and as the source
              # of the fusion. They do not go in out/: whoever opens that
              # folder to print must not be able to get it wrong and send one
              # of them to the machine on its own.
              "collar", "box")
TOOLS_OUT = ("magnet_cap", "gap_gauges")
ELECTRONICS_OUT = ("perfboard", "pin_sockets", "xiao", "driver", "components", "gx12", "gx12_nut", "led")


def out_subdir(name):
    """The subfolder of out/ this part goes in, with the trailing slash.

    One place only: the same answer must be given by whoever writes the
    file, whoever reads it back to measure it and whoever makes its preview,
    and three copies drift apart at the first part that changes place."""
    if name in REFERENCES:
        return "references" + os.sep
    if name in TOOLS_OUT:
        return "tools" + os.sep
    if name in ELECTRONICS_OUT:
        return "electronics" + os.sep
    return ""
