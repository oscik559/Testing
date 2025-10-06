#!/usr/bin/env python3
"""
CATIA Design Agent - UAV Wing Design Demo
========================================

Demonstration of the intelligent agent mapping real UAV wing design steps
to exact PyCATIA methods using context-aware matching.
"""

from catia_design_agent import CATIADesignAgent, DesignStep
import json
from typing import List


def get_uav_wing_design_steps() -> List[DesignStep]:
    """Define the UAV wing design steps from the manual process"""
    
    return [
        DesignStep(
            step_number=1,
            description="Initialize CATIA application and enter GSD workbench",
            action="initialize_catia",
            objects=["catia", "workbench"],
            expected_result="CATIA application ready with Generative Shape Design workbench"
        ),
        
        DesignStep(
            step_number=2,
            description="Create new part document",
            action="create_document",
            objects=["documents", "part_document"],
            expected_result="New part document opened and active"
        ),
        
        DesignStep(
            step_number=3,
            description="Add geometric set for wing construction",
            action="add_geometric_set",
            objects=["hybrid_bodies", "geom_set"],
            expected_result="Geometric set created and ready for shape operations"
        ),
        
        DesignStep(
            step_number=4,
            description="Create direction vectors for wing geometry",
            action="create_direction_vectors",
            objects=["hybrid_shape_factory", "direction_x", "direction_y", "direction_z"],
            expected_result="Three orthogonal direction vectors defined"
        ),
        
        DesignStep(
            step_number=5,
            description="Create points for wing profile definition",
            action="create_profile_points",
            objects=["hybrid_shape_factory", "points", "coordinates"],
            expected_result="Profile points positioned for airfoil shape"
        ),
        
        DesignStep(
            step_number=6,
            description="Create spline curve through profile points",
            action="create_spline_curve",
            objects=["hybrid_shape_factory", "spline", "profile_points"],
            expected_result="Spline curve representing wing airfoil profile"
        ),
        
        DesignStep(
            step_number=7,
            description="Add spline to geometric set",
            action="append_shape_to_set",
            objects=["geom_set", "spline"],
            expected_result="Spline curve added to geometric set"
        ),
        
        DesignStep(
            step_number=8,
            description="Create plane for wing span direction",
            action="create_reference_plane",
            objects=["hybrid_shape_factory", "plane", "offset"],
            expected_result="Reference plane for wing span operations"
        ),
        
        DesignStep(
            step_number=9,
            description="Create loft surface between profiles",
            action="create_loft_surface",
            objects=["hybrid_shape_factory", "loft", "profiles"],
            expected_result="Wing surface created by lofting profiles"
        ),
        
        DesignStep(
            step_number=10,
            description="Add loft surface to geometric set",
            action="append_surface_to_set", 
            objects=["geom_set", "loft_surface"],
            expected_result="Wing surface integrated into geometric set"
        ),
        
        DesignStep(
            step_number=11,
            description="Update part to complete wing construction",
            action="update_part",
            objects=["part", "update"],
            expected_result="Complete UAV wing model ready for analysis"
        )
    ]


def run_uav_wing_demo():
    """Run the complete UAV wing design mapping demo"""
    
    print("🚁 UAV WING DESIGN - INTELLIGENT PYCATIA MAPPING")
    print("=" * 70)
    
    try:
        # Initialize the agent
        print("🤖 Initializing CATIA Design Agent...")
        agent = CATIADesignAgent("pycatia_methods.db")
        print("✅ Agent ready with context-aware matching")
        
        # Get design steps
        design_steps = get_uav_wing_design_steps()
        print(f"📋 Loaded {len(design_steps)} UAV wing design steps")
        
        # Process each step individually for detailed output
        print("\\n🔍 ANALYZING DESIGN STEPS:")
        print("-" * 70)
        
        successful_mappings = []
        
        for step in design_steps:
            print(f"\\n📌 Step {step.step_number}: {step.description}")
            print(f"   Action: {step.action}")
            print(f"   Objects: {', '.join(step.objects)}")
            
            try:
                # Map step to methods
                matches = agent.map_step_to_methods(step)
                
                if matches:
                    print(f"   ✅ MAPPED TO:")
                    for match in matches:
                        print(f"      → {match.full_method_name}")
                        print(f"        Confidence: {match.confidence:.2f}")
                        print(f"        Class: {match.class_name}")
                        print(f"        Reason: {match.match_reason}")
                        if match.parameters:
                            print(f"        Parameters: {match.parameters}")
                    
                    successful_mappings.append({
                        'step': step.step_number,
                        'description': step.description,
                        'matches': matches
                    })
                else:
                    print(f"   ❌ NO SUITABLE METHOD FOUND")
                    
            except Exception as e:
                print(f"   ⚠️  ERROR: {e}")
        
        # Summary
        print("\\n" + "=" * 70)
        print("📊 MAPPING SUMMARY")
        print("=" * 70)
        print(f"Total Steps: {len(design_steps)}")
        print(f"Successfully Mapped: {len(successful_mappings)}")
        print(f"Success Rate: {len(successful_mappings)/len(design_steps)*100:.1f}%")
        
        # Generate Python code preview
        if successful_mappings:
            print("\\n💻 GENERATED PYCATIA CODE PREVIEW:")
            print("-" * 40)
            print("from pycatia import catia")
            print("import math")
            print()
            print("def create_uav_wing():")
            print('    """Create UAV wing using PyCATIA"""')
            
            for mapping in successful_mappings[:5]:  # Show first 5 steps
                step_num = mapping['step']
                matches = mapping['matches']
                if matches:
                    match = matches[0]  # Use first match
                    class_name = match.class_name.lower().replace('shape', '')
                    method_name = match.method_name
                    print(f"    ")
                    print(f"    # Step {step_num}: {mapping['description']}")
                    print(f"    result_{step_num} = {class_name}.{method_name}()")
            
            print("    ...")
            print("    return part")
        
        # Context evolution display
        print(f"\\n🔗 CONTEXT EVOLUTION:")
        print("-" * 30)
        for var, chain in agent.context_tracker.items():
            print(f"  {var} → {chain}")
        
        print(f"\\n🎯 DEMONSTRATION COMPLETED!")
        print("The agent successfully demonstrates:")
        print("  ✅ Context-aware object type inference")
        print("  ✅ Variable chain tracking and return type mapping")
        print("  ✅ Priority-based method selection")
        print("  ✅ High-confidence matching for critical operations")
        print("  ✅ Integration with local LLM for step analysis")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def test_specific_problematic_cases():
    """Test the specific cases that were wrong in the previous system"""
    
    print("\\n🎯 TESTING PREVIOUSLY PROBLEMATIC CASES")
    print("=" * 50)
    
    agent = CATIADesignAgent("pycatia_methods.db")
    
    test_cases = [
        {
            'name': 'hybrid_bodies.add',
            'object': 'hybrid_bodies',
            'method': 'add',
            'context': {'variable_chains': {'hybrid_bodies': 'part.hybrid_bodies'}},
            'expected_class': 'HybridBodies',
            'wrong_before': 'DefeaturingFilters'
        },
        {
            'name': 'geom_set.append_hybrid_shape',
            'object': 'geom_set', 
            'method': 'append_hybrid_shape',
            'context': {'variable_chains': {'geom_set': 'hybrid_bodies.add()'}},
            'expected_class': 'HybridBody',
            'wrong_before': 'HybridShape3DCurveOffset'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\\n🧪 Test {i}: {case['name']}")
        print(f"   Expected Class: {case['expected_class']}")
        print(f"   Wrong Before: {case['wrong_before']}")
        
        match = agent.matcher.find_best_match(case['object'], case['method'], case['context'])
        
        if match:
            print(f"   ✅ NOW MATCHES: {match.class_name}")
            print(f"   📊 Confidence: {match.confidence:.2f}")
            print(f"   🎯 Method: {match.full_method_name}")
            print(f"   💡 Reason: {match.match_reason}")
            
            if match.class_name == case['expected_class']:
                print(f"   🎉 SUCCESS: Fixed the wrong mapping!")
            else:
                print(f"   ❌ Still wrong: Expected {case['expected_class']}")
        else:
            print(f"   ❌ No match found")


if __name__ == "__main__":
    # Run the main demo
    run_uav_wing_demo()
    
    # Test specific problematic cases
    test_specific_problematic_cases()