# Required imports for CATIA automation and mathematical operations
from pycatia import catia
import math


def step_01_initialize_catia_app():
    """Step 1: Initialize CATIA environment and enter GSD workbench"""
    # PDF Step 1: Initialize CATIA application and create new part document
    caa = catia()
    documents = caa.documents
    documents.add("Part")
    document = caa.active_document
    part = document.part
    caa.start_workbench("GenerativeShapeDesignWorkbench")
    
    return {
        'caa': caa,
        'documents': documents,
        'document': document,
        'part': part
    }


def step_02_setup_hybrid_shape_environment(part):
    """Step 2: Set up hybrid shape design environment"""
    # PDF Step 2: Configure hybrid shape factory and geometrical set
    hybrid_shape_factory = part.hybrid_shape_factory
    shape_factory = part.shape_factory
    hybrid_bodies = part.hybrid_bodies
    geom_set = hybrid_bodies.add()
    geom_set.name = "Geometrical Set.1"
    
    return {
        'hybrid_shape_factory': hybrid_shape_factory,
        'shape_factory': shape_factory,
        'hybrid_bodies': hybrid_bodies,
        'geom_set': geom_set
    }


def step_03_define_reference_planes(part):
    """Step 3: Define reference planes"""
    # PDF Step 3: Access origin coordinate system planes
    planes = part.origin_elements
    xy_plane = planes.plane_xy
    yz_plane = planes.plane_yz
    zx_plane = planes.plane_zx
    
    return {
        'planes': planes,
        'xy_plane': xy_plane,
        'yz_plane': yz_plane,
        'zx_plane': zx_plane
    }


def step_04_define_reference_axes(hybrid_shape_factory, geom_set, part):
    """Step 4: Define reference coordinate axes"""
    # PDF Step 4: Create directional references for construction geometry
    x_axis = hybrid_shape_factory.add_new_direction_by_coord(1, 0, 0)
    y_axis = hybrid_shape_factory.add_new_direction_by_coord(0, 1, 0)
    z_axis = hybrid_shape_factory.add_new_direction_by_coord(0, 0, 1)
    x_axis.name = "X Axis"
    y_axis.name = "Y Axis"
    z_axis.name = "Z Axis"
    geom_set.append_hybrid_shape(x_axis)
    geom_set.append_hybrid_shape(y_axis)
    geom_set.append_hybrid_shape(z_axis)
    
    part.update()
    
    return {
        'x_axis': x_axis,
        'y_axis': y_axis,
        'z_axis': z_axis
    }


def step_05_create_construction_plane(hybrid_shape_factory, zx_plane, geom_set, part):
    """Step 5: Create construction plane for wing geometry"""
    # PDF Step 5: Create a Plane - Create an offset plane from the zx plane
    plane1 = hybrid_shape_factory.add_new_plane_offset(zx_plane, 500.0, False)
    plane1.name = "Plane.1"
    geom_set.append_hybrid_shape(plane1)
    part.update()
    
    return plane1


def step_06_create_root_point(hybrid_shape_factory, plane1, geom_set, part):
    """Step 6: Create root chord reference point"""
    # PDF Step 6: Create a Point - Create a point in the middle of Plane.1
    point1 = hybrid_shape_factory.add_new_point_on_plane(plane1, -250.0, 0.0)
    point1.name = "Point.1"
    geom_set.append_hybrid_shape(point1)
    part.update()
    
    return point1


def step_07_create_tip_point(hybrid_shape_factory, plane1, point1, yz_plane, geom_set, part):
    """Step 7: Create tip chord reference point"""
    # PDF Step 7: Create a Point - Create a point with 300mm YZ offset from Point.1
    yz_direction = hybrid_shape_factory.add_new_direction(yz_plane)
    point2 = hybrid_shape_factory.add_new_point_on_surface_with_reference(
        plane1, point1, yz_direction, 300.0
    )
    point2.name = "Point.2"
    geom_set.append_hybrid_shape(point2)
    part.update()
    
    return point2


def step_08_create_root_spline(hybrid_shape_factory, point1, point2, z_axis, geom_set, part):
    """Step 8: Create wing root airfoil spline"""
    # PDF Step 8: Create a Spline through Point.1 and Point.2 with Z axis tangency
    ref_point1 = part.create_reference_from_object(point1)
    ref_z_axis = part.create_reference_from_object(z_axis)
    
    spline1 = hybrid_shape_factory.add_new_spline()
    spline1.spline_type = 0
    spline1.closing = 0
    spline1.add_point_with_constraint_from_curve(ref_point1, ref_z_axis, 0.5, 1, 1)
    spline1.add_point(point2)
    spline1.name = "Spline.1"
    geom_set.append_hybrid_shape(spline1)
    part.in_work_object = spline1
    part.update()
    
    return spline1


def step_09_create_tip_spline(hybrid_shape_factory, point1, point2, z_axis, geom_set, part):
    """Step 9: Create wing tip airfoil spline"""
    # PDF Step 9: Create Spline number two (reverse direction with 0.3 tension)
    ref_point1 = part.create_reference_from_object(point1)
    ref_point2 = part.create_reference_from_object(point2)
    ref_z_axis = part.create_reference_from_object(z_axis)
    
    spline2 = hybrid_shape_factory.add_new_spline()
    spline2.add_point(ref_point2)
    spline2.add_point_with_constraint_from_curve(ref_point1, ref_z_axis, 0.3, 0, 1)
    spline2.name = "Spline.2"
    geom_set.append_hybrid_shape(spline2)
    part.update()
    
    return spline2


def step_10_create_reference_line(hybrid_shape_factory, point1, plane1, geom_set, part):
    """Step 10: Create reference line for sweep direction"""
    # PDF Step 10: Create a Line - Point-Direction type using Plane.1 as Direction
    dir_plane1 = hybrid_shape_factory.add_new_direction(plane1)
    line1 = hybrid_shape_factory.add_new_line_pt_dir(
        point1, dir_plane1, 0.0, 20.0, False
    )
    line1.name = "Line.1"
    geom_set.append_hybrid_shape(line1)
    part.update()
    
    return line1


def step_11_create_angled_line(hybrid_shape_factory, line1, xy_plane, point1, geom_set, part):
    """Step 11: Create angled line for wing sweep control"""
    # PDF Step 11: Create one more Line - Angle/Normal to curve type
    ref_xy_plane = part.create_reference_from_object(xy_plane)
    ref_line1 = part.create_reference_from_object(line1)
    line2 = hybrid_shape_factory.add_new_line_angle(
        ref_line1, ref_xy_plane, point1, False, 0.0, 20.0, -30.0, False
    )
    line2.name = "Line.2"
    geom_set.append_hybrid_shape(line2)
    part.update()
    
    return line2


def step_12_extrude_root_spline(hybrid_shape_factory, spline1, line2, geom_set, part):
    """Step 12: Extrude root spline to create surface scaffold"""
    # PDF Step 12: Extrude Surface (1/2) - Choose Spline.1 as Profile and Line.2 as Direction
    dir_line2 = hybrid_shape_factory.add_new_direction(line2)
    extrude1 = hybrid_shape_factory.add_new_extrude(spline1, 500.0, 0.0, dir_line2)
    extrude1.name = "Extrude.1"
    geom_set.append_hybrid_shape(extrude1)
    part.update()
    
    return extrude1


def step_13_extrude_tip_spline(hybrid_shape_factory, spline2, line2, geom_set, part):
    """Step 13: Extrude tip spline to create surface scaffold"""
    # PDF Step 13: Extrude Surface (2/2) - Repeat procedure with Spline.2 as Profile
    dir_line2 = hybrid_shape_factory.add_new_direction(line2)
    extrude2 = hybrid_shape_factory.add_new_extrude(spline2, 500.0, 0.0, dir_line2)
    extrude2.name = "Extrude.2"
    geom_set.append_hybrid_shape(extrude2)
    part.update()
    
    return extrude2


def step_14_create_additional_point3(hybrid_shape_factory, geom_set, part):
    """Step 14: Create additional spanwise reference points"""
    # PDF Step 14: Create a Point - Create a new point as following
    point3 = hybrid_shape_factory.add_new_point_coord(-300, 0.0, 0.0)
    point3.name = "Point.3"
    geom_set.append_hybrid_shape(point3)
    part.update()
    
    return point3


def step_15_create_additional_point4(hybrid_shape_factory, geom_set, part):
    """Step 15: Create additional spanwise reference points"""
    # PDF Step 15: Create a Point - Create a new point as following
    point4 = hybrid_shape_factory.add_new_point_coord(1000, 0.0, 0.0)
    point4.name = "Point.4"
    geom_set.append_hybrid_shape(point4)
    part.update()
    
    return point4


def step_16_create_additional_spline3(hybrid_shape_factory, point3, point4, z_axis, geom_set, part):
    """Step 16: Create additional spanwise splines for wing structure"""
    # PDF Step 16: Create another Profile (Two more Splines) - Introduce new profile
    ref_point3 = part.create_reference_from_object(point3)
    ref_z_axis = part.create_reference_from_object(z_axis)
    spline3 = hybrid_shape_factory.add_new_spline()
    spline3.add_point_with_constraint_from_curve(ref_point3, ref_z_axis, 0.5, 0, 1)
    spline3.add_point(point4)
    spline3.name = "Spline.3"
    geom_set.append_hybrid_shape(spline3)
    part.update()
    
    return spline3


def step_17_create_additional_spline4(hybrid_shape_factory, point3, point4, z_axis, geom_set, part):
    """Step 17: Create additional spanwise splines for wing structure"""
    # Create additional spanwise splines for wing structure
    ref_point3 = part.create_reference_from_object(point3)
    ref_point4 = part.create_reference_from_object(point4)
    ref_z_axis = part.create_reference_from_object(z_axis)
    spline4 = hybrid_shape_factory.add_new_spline()
    spline4.add_point(ref_point4)
    spline4.add_point_with_constraint_from_curve(ref_point3, ref_z_axis, 0.3, 0, 1)
    spline4.name = "Spline.4"
    geom_set.append_hybrid_shape(spline4)
    part.update()
    
    return spline4


def step_18_create_guide_spline5(hybrid_shape_factory, point3, point1, y_axis, line2, geom_set, part):
    """Step 18: Create guide splines for loft surface control"""
    # Create a Spline connecting the two profiles with tangent directions
    ref_point3 = part.create_reference_from_object(point3)
    ref_y_axis = part.create_reference_from_object(y_axis)
    spline5 = hybrid_shape_factory.add_new_spline()
    spline5.add_point_with_constraint_from_curve(ref_point3, ref_y_axis, 1, 0, 1)
    spline5.add_point_with_constraint_from_curve(point1, line2, 1, 0, 1)
    spline5.name = "Spline.5"
    geom_set.append_hybrid_shape(spline5)
    part.update()
    
    return spline5


def step_19_create_guide_spline6(hybrid_shape_factory, point4, point2, y_axis, geom_set, part):
    """Step 19: Create guide splines for loft surface control"""
    # Create a Spline connecting the two profiles with tangent directions
    ref_point4 = part.create_reference_from_object(point4)
    ref_point2 = part.create_reference_from_object(point2)
    ref_y_axis = part.create_reference_from_object(y_axis)
    spline6 = hybrid_shape_factory.add_new_spline()
    spline6.add_point_with_constraint_from_curve(ref_point4, ref_y_axis, 1, 1, 1)
    spline6.add_point_with_constraint_from_curve(ref_point2, ref_y_axis, 1, 1, 1)
    spline6.name = "Spline.6"
    geom_set.append_hybrid_shape(spline6)
    part.update()
    
    return spline6


def step_20_create_extrude3(hybrid_shape_factory, spline3, zx_plane, geom_set, part):
    """Step 20: Create support extrusions for loft scaffolding"""
    # Create additional guide splines - Create an Extrude Surface
    dir_zx_plane = hybrid_shape_factory.add_new_direction(zx_plane)
    extrude3 = hybrid_shape_factory.add_new_extrude(
        spline3, -30.0, 0.0, dir_zx_plane
    )
    extrude3.name = "Extrude.3"
    geom_set.append_hybrid_shape(extrude3)
    part.update()
    
    return extrude3


def step_21_create_extrude4(hybrid_shape_factory, spline4, zx_plane, geom_set, part):
    """Step 21: Create support extrusions for loft scaffolding"""
    # Create additional guide splines - Create an Extrude Surface
    dir_zx_plane = hybrid_shape_factory.add_new_direction(zx_plane)
    extrude4 = hybrid_shape_factory.add_new_extrude(
        spline4, -30.0, 0.0, dir_zx_plane
    )
    extrude4.name = "Extrude.4"
    geom_set.append_hybrid_shape(extrude4)
    part.update()
    
    return extrude4


def step_22_create_upper_loft_surface(hybrid_shape_factory, spline2, spline4, spline5, spline6, point2, point4, extrude2, extrude3, geom_set, part):
    """Step 22: Create upper wing loft surface"""
    # PDF Step 22: Create a Multi-section Surface - Choose sections and guides with tangent surfaces
    ref_spline2 = part.create_reference_from_object(spline2)
    ref_spline4 = part.create_reference_from_object(spline4)
    ref_spline5 = part.create_reference_from_object(spline5)
    ref_spline6 = part.create_reference_from_object(spline6)

    ref_extrude2 = part.create_reference_from_object(extrude2)
    ref_extrude3 = part.create_reference_from_object(extrude3)

    ref_closingpoint2 = part.create_reference_from_object(point2)
    ref_closingpoint4 = part.create_reference_from_object(point4)

    loft_surface1 = hybrid_shape_factory.add_new_loft()
    loft_surface1.add_section_to_loft(ref_spline4, 1, ref_closingpoint4)
    loft_surface1.set_start_face_for_closing(ref_extrude3)
    loft_surface1.add_section_to_loft(ref_spline2, 1, ref_closingpoint2)
    loft_surface1.set_end_face_for_closing(ref_extrude2)

    loft_surface1.remove_section_point(ref_spline4)
    loft_surface1.remove_section_point(ref_spline2)

    loft_surface1.add_guide(ref_spline5)
    loft_surface1.add_guide(ref_spline6)

    loft_surface1.name = "Multi-sections Surface.1"
    geom_set.append_hybrid_shape(loft_surface1)
    part.update()
    
    return loft_surface1


def step_23_create_lower_loft_surface(hybrid_shape_factory, spline1, spline3, spline5, spline6, point1, point3, extrude1, extrude4, geom_set, part):
    """Step 23: Create wing surface using multi-section loft"""
    # PDF Step 23: Create a Multi-section Surface - Choose sections and guides with tangent surfaces
    ref_spline1 = part.create_reference_from_object(spline1)
    ref_spline3 = part.create_reference_from_object(spline3)
    ref_spline5 = part.create_reference_from_object(spline5)
    ref_spline6 = part.create_reference_from_object(spline6)

    ref_closingpoint1 = part.create_reference_from_object(point1)
    ref_closingpoint3 = part.create_reference_from_object(point3)

    ref_extrude4 = part.create_reference_from_object(extrude4)
    ref_extrude1 = part.create_reference_from_geometry(extrude1)
    loft_surface2 = hybrid_shape_factory.add_new_loft()
    loft_surface2.add_section_to_loft(ref_spline3, 1, ref_closingpoint3)
    loft_surface2.set_start_face_for_closing(ref_extrude4)
    loft_surface2.add_section_to_loft(ref_spline1, 1, ref_closingpoint1)
    loft_surface2.set_end_face_for_closing(ref_extrude1)

    loft_surface2.remove_section_point(ref_spline3)
    loft_surface2.remove_section_point(ref_spline1)

    loft_surface2.add_guide(ref_spline5)
    loft_surface2.add_guide(ref_spline6)
    loft_surface2.section_coupling = 1
    loft_surface2.relimitation = 1
    loft_surface2.name = "Multi-sections Surface.2"
    geom_set.append_hybrid_shape(loft_surface2)
    part.update()
    
    return loft_surface2


def step_24_join_extrude_surfaces(hybrid_shape_factory, extrude1, extrude2, geom_set, part):
    """Step 24: Join extrusion surfaces"""
    # PDF Step 24: Create a Join - Join Extrude.1 and Extrude.2 surfaces
    ref_extrude1 = part.create_reference_from_object(extrude1)
    ref_extrude2 = part.create_reference_from_object(extrude2)
    join_operation1 = hybrid_shape_factory.add_new_join(ref_extrude1, ref_extrude2)
    join_operation1.name = "Join.1"
    join_operation1.check_tangency = True
    join_operation1.check_connectivity = True
    join_operation1.check_manifold = True
    join_operation1.simplify_result = False
    join_operation1.ignore_erroneous_elements = False
    join_operation1.merging_distance = 0.001
    join_operation1.heal_merged_cells = False
    join_operation1.angular_threshold = 0.5
    geom_set.append_hybrid_shape(join_operation1)
    part.update()
    
    return join_operation1


def step_25_join_loft_surfaces(hybrid_shape_factory, loft_surface1, loft_surface2, geom_set, part):
    """Step 25: Join loft surfaces"""
    # PDF Step 25: Create a Join - Select loft surfaces of the model
    ref_loft1 = part.create_reference_from_object(loft_surface1)
    ref_loft2 = part.create_reference_from_object(loft_surface2)
    join_operation2 = hybrid_shape_factory.add_new_join(ref_loft1, ref_loft2)
    join_operation2.name = "Join.2"
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
    
    return join_operation2


def step_26_join_all_surfaces(hybrid_shape_factory, join_operation1, join_operation2, geom_set, part):
    """Step 26: Join the loft surfaces together"""
    # PDF Step 26: Create final unified wing surface - Unify all wing surfaces
    ref_join1 = part.create_reference_from_object(join_operation1)
    ref_join2 = part.create_reference_from_object(join_operation2)
    final_join = hybrid_shape_factory.add_new_join(ref_join1, ref_join2)
    final_join.name = "Join.3"
    final_join.check_tangency = False
    final_join.check_connectivity = True
    final_join.check_manifold = True
    final_join.simplify_result = False
    final_join.ignore_erroneous_elements = False
    final_join.merging_distance = 0.001
    final_join.heal_merged_cells = False
    final_join.angular_threshold = 0.5
    geom_set.append_hybrid_shape(final_join)
    part.update()
    
    return final_join


def step_27_add_thickness(shape_factory, final_join, part):
    """Step 27: Add thickness to create solid wing structure"""
    # PDF Step 27: Create a ThickSurface - Choose Join.3 and give thickness of 10mm
    ref_final_join = part.create_reference_from_object(final_join)
    thick_surface1 = shape_factory.add_new_volume_thick_surface(
        ref_final_join, 0, 10.0, 0.0
    )
    thick_surface1.name = "ThickSurface.1"
    part.update()
    
    return thick_surface1


def step_28_mirror_wing(hybrid_shape_factory, thick_surface1, zx_plane, geom_set, part):
    """Step 28: Mirror wing to create full wingspan"""
    # PDF Step 28: Create a Symmetry - Choose ThickSurface.1 as Element and zx plane as Reference
    ref_zx_plane = part.create_reference_from_object(zx_plane)
    symmetry1 = hybrid_shape_factory.add_new_symmetry(thick_surface1, ref_zx_plane)
    symmetry1.name = "Symmetry.1"
    symmetry1.volume_result = True
    geom_set.append_hybrid_shape(symmetry1)
    part.in_work_object = symmetry1
    part.update()
    
    return symmetry1


def step_29_control_element_visibility(document, geom_set):
    """Step 29: Control element visibility for cleaner design view"""
    # PDF Step 29: Hide help surfaces and set visibility for geometric elements
    selection = document.selection
    hybrid_shapes = geom_set.hybrid_shapes

    elements_to_hide = [
        "Plane.1",
        "Point.1",
        "Point.2",
        "Point.3",
        "Point.4",
        "Spline.1",
        "Spline.2",
        "Spline.3",
        "Spline.4",
        "Spline.5",
        "Spline.6",
        "Line.1",
        "Line.2",
        "Multi-sections Surface.1",
        "Multi-sections Surface.2",
        "Extrude.4",
        "Extrude.3",
        "Extrude.2",
        "Extrude.1",
        "Join.1",
        "Join.2",
        "Join.3",
    ]

    for element_name in elements_to_hide:
        try:
            hybrid_shape = hybrid_shapes.item(element_name)
            selection.add(hybrid_shape)
            vis_properties = selection.vis_properties
            vis_properties.set_show(1)
            selection.clear()
        except Exception as vis_error:
            print(f"Could not set visibility for {element_name}: {vis_error}")
            selection.clear()


def create_flying_wing():
    """
    Main orchestrator function that calls all individual step functions.
    Create a parametric flying wing UAV model in CATIA using PyCATIA.
    """
    try:
        # Step 1: Initialize CATIA
        catia_objects = step_01_initialize_catia_app()
        part = catia_objects['part']
        document = catia_objects['document']
        
        # Step 2: Setup hybrid environment
        hybrid_objects = step_02_setup_hybrid_shape_environment(part)
        hybrid_shape_factory = hybrid_objects['hybrid_shape_factory']
        shape_factory = hybrid_objects['shape_factory']
        geom_set = hybrid_objects['geom_set']
        
        # Step 3: Define reference planes
        planes_objects = step_03_define_reference_planes(part)
        xy_plane = planes_objects['xy_plane']
        yz_plane = planes_objects['yz_plane']
        zx_plane = planes_objects['zx_plane']
        
        # Step 4: Define reference axes
        axes_objects = step_04_define_reference_axes(hybrid_shape_factory, geom_set, part)
        x_axis = axes_objects['x_axis']
        y_axis = axes_objects['y_axis']
        z_axis = axes_objects['z_axis']
        
        # Step 5: Create construction plane
        plane1 = step_05_create_construction_plane(hybrid_shape_factory, zx_plane, geom_set, part)
        
        # Step 6: Create root point
        point1 = step_06_create_root_point(hybrid_shape_factory, plane1, geom_set, part)
        
        # Step 7: Create tip point
        point2 = step_07_create_tip_point(hybrid_shape_factory, plane1, point1, yz_plane, geom_set, part)
        
        # Step 8: Create root spline
        spline1 = step_08_create_root_spline(hybrid_shape_factory, point1, point2, z_axis, geom_set, part)
        
        # Step 9: Create tip spline
        spline2 = step_09_create_tip_spline(hybrid_shape_factory, point1, point2, z_axis, geom_set, part)
        
        # Step 10: Create reference line
        line1 = step_10_create_reference_line(hybrid_shape_factory, point1, plane1, geom_set, part)
        
        # Step 11: Create angled line
        line2 = step_11_create_angled_line(hybrid_shape_factory, line1, xy_plane, point1, geom_set, part)
        
        # Step 12: Extrude root spline
        extrude1 = step_12_extrude_root_spline(hybrid_shape_factory, spline1, line2, geom_set, part)
        
        # Step 13: Extrude tip spline
        extrude2 = step_13_extrude_tip_spline(hybrid_shape_factory, spline2, line2, geom_set, part)
        
        # Step 14: Create additional point 3
        point3 = step_14_create_additional_point3(hybrid_shape_factory, geom_set, part)
        
        # Step 15: Create additional point 4
        point4 = step_15_create_additional_point4(hybrid_shape_factory, geom_set, part)
        
        # Step 16: Create additional spline 3
        spline3 = step_16_create_additional_spline3(hybrid_shape_factory, point3, point4, z_axis, geom_set, part)
        
        # Step 17: Create additional spline 4
        spline4 = step_17_create_additional_spline4(hybrid_shape_factory, point3, point4, z_axis, geom_set, part)
        
        # Step 18: Create guide spline 5
        spline5 = step_18_create_guide_spline5(hybrid_shape_factory, point3, point1, y_axis, line2, geom_set, part)
        
        # Step 19: Create guide spline 6
        spline6 = step_19_create_guide_spline6(hybrid_shape_factory, point4, point2, y_axis, geom_set, part)
        
        # Step 20: Create extrude 3
        extrude3 = step_20_create_extrude3(hybrid_shape_factory, spline3, zx_plane, geom_set, part)
        
        # Step 21: Create extrude 4
        extrude4 = step_21_create_extrude4(hybrid_shape_factory, spline4, zx_plane, geom_set, part)
        
        # Step 22: Create upper loft surface
        loft_surface1 = step_22_create_upper_loft_surface(hybrid_shape_factory, spline2, spline4, spline5, spline6, point2, point4, extrude2, extrude3, geom_set, part)
        
        # Step 23: Create lower loft surface
        loft_surface2 = step_23_create_lower_loft_surface(hybrid_shape_factory, spline1, spline3, spline5, spline6, point1, point3, extrude1, extrude4, geom_set, part)
        
        # Step 24: Join extrude surfaces
        join_operation1 = step_24_join_extrude_surfaces(hybrid_shape_factory, extrude1, extrude2, geom_set, part)
        
        # Step 25: Join loft surfaces
        join_operation2 = step_25_join_loft_surfaces(hybrid_shape_factory, loft_surface1, loft_surface2, geom_set, part)
        
        # Step 26: Join all surfaces
        final_join = step_26_join_all_surfaces(hybrid_shape_factory, join_operation1, join_operation2, geom_set, part)
        
        # Step 27: Add thickness
        thick_surface1 = step_27_add_thickness(shape_factory, final_join, part)
        
        # Step 28: Mirror wing
        symmetry1 = step_28_mirror_wing(hybrid_shape_factory, thick_surface1, zx_plane, geom_set, part)
        
        # Step 29: Control element visibility
        step_29_control_element_visibility(document, geom_set)
        
        return part

    except Exception as e:
        import traceback
        print(f"Error in create_flying_wing: {e}")
        traceback.print_exc()
        return None


# Main execution block
if __name__ == "__main__":
    print("Starting flying wing creation...")
    wing_part = create_flying_wing()
    if wing_part:
        print("Successfully created flying wing UAV model")
    else:
        print("Failed to create flying wing model")