from pycatia import catia
import win32com.client  # noqa: F401 (import retained for potential COM interop extensions)
import math  # noqa: F401 (reserved for future trigonometric parameterisation)

"""
Flying Wing Parametric Construction Script (CATIA V5 / PyCATIA)
----------------------------------------------------------------
This script builds a simplified flying wing surface model using Generative Shape Design
operations. It mirrors the manual procedure (Flying-Wing-Instructions PDF) and is annotated
step-by-step for clarity, future automation, and potential database-driven replay.

Major Phases:
  0. Environment & Container Setup
  1. Construction Plane Creation
  2. Root Reference Point
  3. Tip Reference Point (spanwise placement)
  4. Root Airfoil Spline (Spline.1)
  5. Tip Airfoil Spline (Spline.2 – reversed order for opposite tangency)
  6. Reference Lines (Line.1 direction + Line.2 angled)
  7. Profile Extrusions (Extrude.1 & Extrude.2) – surface scaffolds
  8. Additional Spanwise Points (Point.3 & Point.4)
  9. Spanwise Splines (Spline.3 & Spline.4)
 10. Guide Curves (Spline.5 & Spline.6)
 11. Local Edge Extrusions (Extrude.3 & Extrude.4) – optional support surfaces
 12. Multi-Section Loft (final wing panel surface)
 13. Completion & Return

Dependencies & Rationale Notes:
  * Tangency control uses add_point_with_constraint_from_curve referencing axis directions.
  * Line.2 provides a controlled sweep / pseudo aerodynamic direction for early extrusions.
  * Additional splines (3..6) supply intermediate span geometry + guide curves for loft fairness.
  * Extrude.3 / Extrude.4 not strictly required for loft here but can act as trimming / support in extensions.

CAUTION: Logic/order must remain intact—only commentary & structural clarity were added.
"""


def create_flying_wing():
    """Construct the flying wing geometry in CATIA.

    Returns:
        part: The CATIA Part object containing the constructed hybrid shapes.
    """
    try:
        # ------------------------------------------------------------------
        # STEP 1: Initialize CATIA and GSD Workbench
        # ------------------------------------------------------------------
        caa = catia()  # Launch / attach to CATIA session
        documents = caa.documents  # Access documents collection
        documents.add("Part")  # Create a new Part document
        document = caa.active_document
        part = document.part
        caa.start_workbench("GenerativeShapeDesignWorkbench")  # Ensure GSD context

        # Hybrid design container (Geometrical Set)
        hybrid_shape_factory = part.hybrid_shape_factory
        shape_factory = part.shape_factory
        hybrid_bodies = part.hybrid_bodies
        geom_set = hybrid_bodies.add()
        geom_set.name = "Geometrical Set.1"

        # ------------------------------------------------------------------
        # REFERENCE SETUP: Planes & Axis Directions
        # ------------------------------------------------------------------
        planes = part.origin_elements
        xy_plane = planes.plane_xy
        yz_plane = planes.plane_yz
        zx_plane = planes.plane_zx

        # Axis directions (explicit—kept for clear constraint references)
        x_axis = hybrid_shape_factory.add_new_direction_by_coord(
            1, 0, 0
        )  # X (span / chord ref)
        y_axis = hybrid_shape_factory.add_new_direction_by_coord(
            0, 1, 0
        )  # Y (vertical or lateral depending on orientation)
        z_axis = hybrid_shape_factory.add_new_direction_by_coord(
            0, 0, 1
        )  # Z (used for tangency control)
        x_axis.name = "X Axis"
        y_axis.name = "Y Axis"
        z_axis.name = "Z Axis"
        geom_set.append_hybrid_shape(x_axis)
        geom_set.append_hybrid_shape(y_axis)
        geom_set.append_hybrid_shape(z_axis)

        part.update()

        # ------------------------------------------------------------------
        # STEP 2: Create Construction Plane
        #    Offset from ZX plane to set aerodynamic reference height / chord plane.
        # ------------------------------------------------------------------
        plane1 = hybrid_shape_factory.add_new_plane_offset(zx_plane, 500.0, False)
        plane1.name = "Plane.1"
        geom_set.append_hybrid_shape(plane1)
        part.update()

        # ------------------------------------------------------------------
        # STEP 3: Create Root Chord Point
        #    chord origin reference on Plane.1
        # ------------------------------------------------------------------
        point1 = hybrid_shape_factory.add_new_point_on_plane(plane1, -250.0, 0.0)
        point1.name = "Point.1"
        geom_set.append_hybrid_shape(point1)
        part.update()

        # ------------------------------------------------------------------
        # STEP 4: Create Tip Chord Point
        #    spanwise offset using YZ direction for planform extent
        # ------------------------------------------------------------------
        yz_direction = hybrid_shape_factory.add_new_direction(yz_plane)
        point2 = hybrid_shape_factory.add_new_point_on_surface_with_reference(
            plane1, point1, yz_direction, 300.0
        )
        point2.name = "Point.2"
        geom_set.append_hybrid_shape(point2)
        part.update()

        # ------------------------------------------------------------------
        # STEP 5: Create Wing Root Spline
        #    defining root profile curve
        # ------------------------------------------------------------------
        # Create references
        ref_point1 = part.create_reference_from_object(point1)
        ref_z_axis = part.create_reference_from_object(z_axis)
        ref_point2 = part.create_reference_from_object(point2)

        spline1 = hybrid_shape_factory.add_new_spline()

        # Set spline properties (equivalent to VBScript SetSplineType and SetClosing)
        spline1.spline_type = 0  # 0 = Standard spline type
        spline1.closing = 0  # 0 = Open spline (not closed)
        spline1.degree = 3  # Cubic spline for smoothness

        spline1.add_point_with_constraint_from_curve(
            ref_point1, ref_z_axis, 0.5, 1, 1
        )  # Tangent at root
        spline1.add_point(point2)  # Simple pass-through at tip reference

        spline1.name = "Spline.1"
        geom_set.append_hybrid_shape(spline1)

        # Set as work object and update (matching VBScript behavior)
        part.in_work_object = spline1
        part.update()

        # ------------------------------------------------------------------
        # STEP 6: Create Wing Tip Spline
        #    reverse ordering to manage tangency influence
        # ------------------------------------------------------------------
        spline2 = hybrid_shape_factory.add_new_spline()
        spline2.add_point(ref_point2)  # Start at tip
        spline2.add_point_with_constraint_from_curve(
            ref_point1, ref_z_axis, 0.3, 0, 1
        )  # Tangent at root with lower tension
        spline2.name = "Spline.2"
        geom_set.append_hybrid_shape(spline2)
        part.update()

        # ------------------------------------------------------------------
        # STEP 7: Create Reference Line
        #    linear reference from point along plane direction
        # ------------------------------------------------------------------
        dir_plane1 = hybrid_shape_factory.add_new_direction(plane1)

        line1 = hybrid_shape_factory.add_new_line_pt_dir(
            point1, dir_plane1, 0.0, 20.0, False
        )
        line1.name = "Line.1"
        geom_set.append_hybrid_shape(line1)

        part.update()

        # ------------------------------------------------------------------
        # STEP 8: Create Angled Line
        #    angled reference line for sweep direction control
        # ------------------------------------------------------------------
        ref_xy_plane = part.create_reference_from_object(xy_plane)
        ref_line1 = part.create_reference_from_object(line1)

        line2 = hybrid_shape_factory.add_new_line_angle(
            ref_line1, ref_xy_plane, point1, False, 0.0, 20.0, -30.0, False
        )
        line2.name = "Line.2"
        geom_set.append_hybrid_shape(line2)

        part.update()

        # ------------------------------------------------------------------
        # STEP 9: Extrude Root Profile
        #    extrude root spline along angled direction
        # ------------------------------------------------------------------
        dir_line2 = hybrid_shape_factory.add_new_direction(line2)

        extrude1 = hybrid_shape_factory.add_new_extrude(spline1, 500.0, 0.0, dir_line2)
        extrude1.name = "Extrude.1"
        geom_set.append_hybrid_shape(extrude1)

        part.update()

        # ------------------------------------------------------------------
        # STEP 10: Extrude Tip Profile
        #    extrude tip spline along angled direction
        # ------------------------------------------------------------------
        dir_line2 = hybrid_shape_factory.add_new_direction(line2)

        extrude2 = hybrid_shape_factory.add_new_extrude(spline2, 500.0, 0.0, dir_line2)
        extrude2.name = "Extrude.2"
        geom_set.append_hybrid_shape(extrude2)

        part.update()

        # ------------------------------------------------------------------
        # STEP 11: Create Additional Points 3
        # ------------------------------------------------------------------
        point3 = hybrid_shape_factory.add_new_point_coord(-300, 0.0, 0.0)
        point3.name = "Point.3"
        geom_set.append_hybrid_shape(point3)

        part.update()

        # ------------------------------------------------------------------
        # STEP 11: Create Additional Points 4
        # ------------------------------------------------------------------
        point4 = hybrid_shape_factory.add_new_point_coord(1000, 0.0, 0.0)
        point4.name = "Point.4"
        geom_set.append_hybrid_shape(point4)

        part.update()

        # ------------------------------------------------------------------
        # STEP 12: Create Spline.3
        # ------------------------------------------------------------------
        ref_point3 = part.create_reference_from_object(point3)
        ref_z_axis = part.create_reference_from_object(z_axis)

        spline3 = hybrid_shape_factory.add_new_spline()
        spline3.add_point_with_constraint_from_curve(ref_point3, ref_z_axis, 0.5, 0, 1)
        spline3.add_point(point4)
        spline3.name = "Spline.3"
        geom_set.append_hybrid_shape(spline3)

        part.update()

        # ------------------------------------------------------------------
        # STEP 12: Create Spline.4
        # ------------------------------------------------------------------
        ref_point3 = part.create_reference_from_object(point3)
        ref_point4 = part.create_reference_from_object(point4)
        ref_z_axis = part.create_reference_from_object(z_axis)

        spline4 = hybrid_shape_factory.add_new_spline()
        spline4.add_point(ref_point4)
        spline4.add_point_with_constraint_from_curve(ref_point3, ref_z_axis, 0.3, 0, 1)
        spline4.name = "Spline.4"
        geom_set.append_hybrid_shape(spline4)

        part.update()

        # ------------------------------------------------------------------
        # Create Guide Splines (Spline.5 ) – for governing loft fairness
        # ------------------------------------------------------------------
        ref_y_axis = part.create_reference_from_object(y_axis)

        spline5 = hybrid_shape_factory.add_new_spline()
        spline5.add_point_with_constraint_from_curve(ref_point3, ref_y_axis, 1, 0, 1)
        spline5.add_point_with_constraint_from_curve(point1, line2, 1, 0, 1)
        spline5.name = "Spline.5"
        geom_set.append_hybrid_shape(spline5)

        part.update()

        # ------------------------------------------------------------------
        # Create Guide Splines ( Spline.6) – for governing loft fairness
        # ------------------------------------------------------------------
        ref_point4 = part.create_reference_from_object(point4)
        ref_point2 = part.create_reference_from_object(point2)
        ref_y_axis = part.create_reference_from_object(y_axis)

        spline6 = hybrid_shape_factory.add_new_spline()
        spline6.add_point_with_constraint_from_curve(ref_point4, ref_y_axis, 1, 1, 1)
        spline6.add_point_with_constraint_from_curve(ref_point2, ref_y_axis, 1, 1, 1)
        spline6.name = "Spline.6"
        geom_set.append_hybrid_shape(spline6)

        part.update()

        # ------------------------------------------------------------------
        # Local Support Extrusions (Extrude.3 ) – auxiliary geometry (optional)
        # ------------------------------------------------------------------
        dir_zx_plane = hybrid_shape_factory.add_new_direction(zx_plane)

        extrude3 = hybrid_shape_factory.add_new_extrude(
            spline4, 30.0, 0.0, dir_zx_plane
        )
        extrude3.name = "Extrude.3"
        geom_set.append_hybrid_shape(extrude3)
        part.update()

        # ------------------------------------------------------------------
        # Local Support Extrusions (Extrude.4) – auxiliary geometry (optional)
        # ------------------------------------------------------------------

        extrude4 = hybrid_shape_factory.add_new_extrude(
            spline3, 30.0, 0.0, dir_zx_plane
        )
        extrude4.name = "Extrude.4"
        geom_set.append_hybrid_shape(extrude4)
        part.update()

        # ------------------------------------------------------------------
        # STEP 13: Create Wing Surface Loft
        #    final multi-section aerodynamic surface
        # ------------------------------------------------------------------
        # Create references for sections and guides
        ref_spline1 = part.create_reference_from_object(spline1)
        ref_spline2 = part.create_reference_from_object(spline2)
        ref_spline3 = part.create_reference_from_object(spline3)
        ref_spline4 = part.create_reference_from_object(spline4)
        ref_spline5 = part.create_reference_from_object(spline5)
        ref_spline6 = part.create_reference_from_object(spline6)

        dir_spline5 = hybrid_shape_factory.add_new_direction(spline5)
        dir_spline6 = hybrid_shape_factory.add_new_direction(spline6)

        # Create references for supports (matching the dialog image)
        ref_extrude1 = part.create_reference_from_geometry(
            extrude1
        )  # Support for Spline.1
        ref_extrude2 = part.create_reference_from_object(
            extrude2
        )  # Support for Spline.2
        ref_extrude3 = part.create_reference_from_object(
            extrude3
        )  # Support for Spline.3
        ref_extrude4 = part.create_reference_from_object(
            extrude4
        )  # Support for Spline.4

        # Create temporary closing point references (required for add_section_to_loft)
        ref_closingpoint1 = part.create_reference_from_object(point1)
        ref_closingpoint2 = part.create_reference_from_object(point2)
        ref_closingpoint3 = part.create_reference_from_object(point3)
        ref_closingpoint4 = part.create_reference_from_object(point4)

        loft_surface1 = hybrid_shape_factory.add_new_loft()

        # Add sections with temporary closing points
        loft_surface1.add_section_to_loft(ref_spline4, 1, ref_closingpoint4)
        loft_surface1.add_section_to_loft(ref_spline2, 1, ref_closingpoint2)

        # ##########
        # loft_surface1.insert_section_to_loft(y
        #     False,  # i_type: position indicator
        #     ref_spline3,  # Spline.3 (first section in dialog)
        #     1,  # orientation
        #     ref_closingpoint3,  # closing point
        #     ref_extrude3,  # Extrude.3 as support
        # )

        # loft_surface1.insert_section_to_loft(
        #     False,  # i_type: position indicator
        #     ref_spline1,  # Spline.1 (second section in dialog)
        #     1,  # orientation
        #     ref_closingpoint1,  # closing point
        #     ref_extrude1,  # Extrude.2 as support
        # )
        # ##############
        # Remove the closing points since we don't want them
        loft_surface1.remove_section_point(ref_spline4)
        loft_surface1.remove_section_point(ref_spline2)

        # Add guides

        loft_surface1.add_guide(ref_spline6)
        loft_surface1.add_guide(ref_spline5)

        # Set loft properties for better surface quality (from VBScript equivalent)
        # loft_surface1.section_coupling = 1
        # loft_surface1.relimitation = 1

        # Set a face to the start and end section from the lofted surface.
        loft_surface1.set_start_face_for_closing(ref_extrude1)
        # loft_surface1.set_end_face_for_closing(ref_extrude3)

        # Set tangent surfaces for start and end sections
        # loft_surface1.set_start_section_tangent(ref_extrude1)  # Tangent to Extrude.1
        # loft_surface1.set_end_section_tangent(ref_extrude3)  # Tangent to Extrude.1

        loft_surface1.name = "Multi Sections Surface.1"
        geom_set.append_hybrid_shape(loft_surface1)

        #################

        part.update()

        # ------------------------------------------------------------------
        # STEP 14: Create Wing Surface Underside Loft
        #    final multi-section aerodynamic surface
        # ------------------------------------------------------------------

        loft_surface2 = hybrid_shape_factory.add_new_loft()

        # Add sections with temporary closing points
        loft_surface2.add_section_to_loft(ref_spline3, 1, ref_closingpoint3)
        loft_surface2.add_section_to_loft(ref_spline1, 1, ref_closingpoint1)

        # Remove the closing points since we don't want them
        loft_surface2.remove_section_point(ref_spline3)
        loft_surface2.remove_section_point(ref_spline1)

        # Add guides
        loft_surface2.add_guide(ref_spline5)
        loft_surface2.add_guide(ref_spline6)

        # Set loft properties for better surface quality (from VBScript equivalent)
        loft_surface2.section_coupling = 1
        loft_surface2.relimitation = 1

        loft_surface2.name = "Multi Sections Surface.2"
        geom_set.append_hybrid_shape(loft_surface2)

        part.update()

        # ------------------------------------------------------------------
        # STEP 15: Create Join Operation
        #    Join the two loft surfaces to create a unified wing surface
        # ------------------------------------------------------------------

        # Create references for the loft surfaces
        ref_loft2 = part.create_reference_from_object(loft_surface2)

        # Create join operation
        join_operation1 = hybrid_shape_factory.add_new_join(ref_extrude1, ref_extrude2)
        join_operation1.name = "Join.1"

        # Set join parameters (matching the dialog settings)
        join_operation1.check_tangency = True
        join_operation1.check_connectivity = True
        join_operation1.check_manifold = True
        join_operation1.simplify_result = False
        join_operation1.ignore_erroneous_elements = False
        join_operation1.merging_distance = 0.001  # 0.001mm as shown in dialog
        join_operation1.heal_merged_cells = False
        join_operation1.angular_threshold = 0.5  # 0.5deg as shown in dialog

        geom_set.append_hybrid_shape(join_operation1)
        part.update()

        # ------------------------------------------------------------------
        # STEP 14: join the two lofts

        # ------------------------------------------------------------------

        # Create references for the loft surfaces
        ref_loft1 = part.create_reference_from_object(loft_surface1)

        # Create join operation
        join_operation2 = hybrid_shape_factory.add_new_join(ref_loft1, ref_loft2)
        join_operation2.name = "Join.2"

        # Set join parameters (matching the dialog settings)
        join_operation2.check_tangency = True
        join_operation2.check_connectivity = True
        join_operation2.check_manifold = True
        join_operation2.simplify_result = False
        join_operation2.ignore_erroneous_elements = False
        join_operation2.merging_distance = 0.001
        join_operation2.heal_merged_cells = False
        join_operation2.angular_threshold = 0.5

        geom_set.append_hybrid_shape(join_operation2)
        part.update()

        # ------------------------------------------------------------------
        # STEP 16: Create Final Join Operation
        #    Join all elements to create a unified wing surface
        # ------------------------------------------------------------------

        # Create references for the join operations
        ref_join1 = part.create_reference_from_object(join_operation1)
        ref_join2 = part.create_reference_from_object(join_operation2)

        # Create final join operation combining both previous joins
        final_join = hybrid_shape_factory.add_new_join(ref_join1, ref_join2)
        final_join.name = "Join.3"

        # Set join parameters (matching the dialog settings)
        final_join.check_tangency = False  # Unchecked in dialog
        final_join.check_connectivity = True
        final_join.check_manifold = True
        final_join.simplify_result = False
        final_join.ignore_erroneous_elements = False
        final_join.merging_distance = 0.001  # 0.001mm as shown in dialog
        final_join.heal_merged_cells = False
        final_join.angular_threshold = 0.5  # 0.5deg as shown in dialog

        geom_set.append_hybrid_shape(final_join)
        part.update()

        # ------------------------------------------------------------------
        # STEP 17: Create Thick Surface Operation
        #    Add thickness to create a solid wing structure
        # ------------------------------------------------------------------
        ref_yz_plane = part.create_reference_from_object(yz_plane)
        ref_final_join = part.create_reference_from_object(final_join)

        # Step 4: Apply thickness operation
        # Parameters: (reference, offset_sense, top_offset, bottom_offset)
        thick_surface1 = shape_factory.add_new_volume_thick_surface(
            ref_final_join, 0, 3.0, 0.0
        )
        thick_surface1.name = "ThickSurface.1"

        part.update()

        # ------------------------------------------------------------------
        # STEP 18: Create Symmetry Operation
        #    Mirror the wing about the ZX plane to create full wingspan
        # ------------------------------------------------------------------
        ref_thick_surface1 = part.create_reference_from_object(thick_surface1)
        ref_zx_plane = part.create_reference_from_object(zx_plane)

        # Create symmetry operation
        symmetry1 = hybrid_shape_factory.add_new_symmetry(
            ref_thick_surface1, ref_zx_plane
        )
        symmetry1.name = "Symmetry.1"
        symmetry1.volume_result = True

        geom_set.append_hybrid_shape(symmetry1)
        part.update()
        # ------------------------------------------------------------------
        # STEP 14: Update Part
        #    Final update to complete the wing design
        # ------------------------------------------------------------------

        return part

    except Exception as e:  # pragma: no cover - CATIA runtime dependent
        import traceback

        print(f"Error in create_flying_wing: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting flying wing creation...")
    wing_part = create_flying_wing()
    if wing_part:
        print("Successfully created flying wing UAV model")
    else:
        print("Failed to create flying wing model")
