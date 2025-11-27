"""
Advanced Function Library Consolidation
Further merges similar functions into even more generic templates
"""

import sqlite3
from typing import Dict, List, Tuple

def analyze_remaining_duplicates(db_path: str = "functions.db"):
    """Analyze remaining functions for further consolidation opportunities"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 ANALYZING REMAINING FUNCTIONS FOR CONSOLIDATION")
    print("=" * 60)
    
    # Get all functions
    cursor.execute("""
        SELECT function_id, function_name, function_description, category
        FROM functions
        ORDER BY category, function_name
    """)
    
    functions = cursor.fetchall()
    
    # Group similar functions
    consolidation_groups = [
        {
            'generic_name': 'Extrude_Spline',
            'generic_description': 'Extrude spline to create surface scaffold',
            'category': 'Surface_Creation',
            'pattern_functions': ['Extrude_Root_Spline', 'Extrude_Tip_Spline']
        },
        {
            'generic_name': 'Create_Spline',
            'generic_description': 'Create splines for wing structure',
            'category': 'Curve_Creation',
            'pattern_functions': ['Create_Root_Spline', 'Create_Tip_Spline', 'Create_Additional_Spline', 'Create_Guide_Spline']
        },
        {
            'generic_name': 'Create_Point',
            'generic_description': 'Create reference points for wing geometry',
            'category': 'Construction_Geometry', 
            'pattern_functions': ['Create_Root_Point', 'Create_Tip_Point', 'Create_Additional_Point']
        }
    ]
    
    # Show current functions by category
    by_category = {}
    for func_id, name, desc, category in functions:
        if category not in by_category:
            by_category[category] = []
        by_category[category].append({'id': func_id, 'name': name, 'desc': desc})
    
    for category, funcs in by_category.items():
        print(f"\n📁 {category} ({len(funcs)} functions):")
        for func in funcs:
            print(f"  {func['id']:2d}. {func['name']}")
    
    print(f"\n🎯 PROPOSED CONSOLIDATIONS:")
    
    for group in consolidation_groups:
        print(f"\n📋 {group['generic_name']} ({group['category']}):")
        print(f"   📝 {group['generic_description']}")
        
        existing_functions = []
        for func_id, name, desc, category in functions:
            if name in group['pattern_functions']:
                existing_functions.append({'id': func_id, 'name': name, 'desc': desc})
        
        if existing_functions:
            print(f"   🔗 Will merge {len(existing_functions)} functions:")
            for func in existing_functions:
                print(f"      • {func['name']} (ID: {func['id']})")
        else:
            print(f"   ⚠️  No matching functions found")
    
    conn.close()
    return consolidation_groups

def get_method_signature_for_comparison(func_id: int, conn) -> str:
    """Get a signature for comparing function methods"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT method_name, object_chain
        FROM function_methods
        WHERE function_ref = ?
        ORDER BY step_order
    """, (func_id,))
    
    methods = cursor.fetchall()
    signature = "|".join([f"{obj}.{method}" for method, obj in methods])
    return signature

def consolidate_advanced_functions(db_path: str = "functions.db"):
    """Perform advanced consolidation of similar functions"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔄 PERFORMING ADVANCED FUNCTION CONSOLIDATION")
    print("=" * 60)
    
    # More comprehensive consolidation groups
    consolidation_groups = [
        {
            'generic_name': 'Extrude_Spline',
            'generic_description': 'Extrude spline to create surface scaffold',
            'category': 'Surface_Creation',
            'target_functions': ['Extrude_Root_Spline', 'Extrude_Tip_Spline']
        },
        {
            'generic_name': 'Create_Spline',
            'generic_description': 'Create splines for wing structure',
            'category': 'Curve_Creation',
            'target_functions': ['Create_Root_Spline', 'Create_Tip_Spline', 'Create_Additional_Spline', 'Create_Guide_Spline']
        },
        {
            'generic_name': 'Create_Point', 
            'generic_description': 'Create reference points for wing geometry',
            'category': 'Construction_Geometry',
            'target_functions': ['Create_Root_Point', 'Create_Tip_Point', 'Create_Additional_Point']
        }
    ]
    
    functions_processed = 0
    
    for group in consolidation_groups:
        print(f"\n📝 Processing: {group['generic_name']}")
        
        # Find existing functions to merge
        target_func_ids = []
        template_func_id = None
        
        for func_name in group['target_functions']:
            cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", (func_name,))
            result = cursor.fetchone()
            if result:
                func_id = result[0]
                target_func_ids.append(func_id)
                if template_func_id is None:  # Use first found as template
                    template_func_id = func_id
                    print(f"   📋 Using {func_name} as template (ID: {func_id})")
                else:
                    print(f"   🔗 Will merge {func_name} (ID: {func_id})")
        
        if len(target_func_ids) <= 1:
            print(f"   ⚠️  Only {len(target_func_ids)} function(s) found, skipping merge")
            continue
        
        # Create new generic function
        cursor.execute("""
            INSERT INTO functions (function_name, function_description, category)
            VALUES (?, ?, ?)
        """, (group['generic_name'], group['generic_description'], group['category']))
        
        new_func_id = cursor.lastrowid
        print(f"   ✅ Created generic function: {group['generic_name']} (ID: {new_func_id})")
        
        # Copy methods from template function with generic calls
        cursor.execute("""
            SELECT method_name, step_order, object_chain, method_call,
                   method_parameters, object_type, return_type, method_description
            FROM function_methods
            WHERE function_ref = ?
            ORDER BY step_order
        """, (template_func_id,))
        
        template_methods = cursor.fetchall()
        
        for method_data in template_methods:
            method_name, step_order, object_chain, method_call, method_params, object_type, return_type, method_desc = method_data
            
            # Make method call more generic
            generic_call = generalize_method_call_advanced(method_call, method_name)
            
            cursor.execute("""
                INSERT INTO function_methods (
                    function_ref, method_name, step_order, object_chain,
                    method_call, method_parameters, object_type, return_type, method_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_func_id, method_name, step_order, object_chain,
                generic_call, method_params, object_type, return_type, method_desc
            ))
        
        print(f"   📋 Copied {len(template_methods)} methods")
        
        # Delete old functions (cascade will handle methods and parameters)
        for func_id in target_func_ids:
            cursor.execute("DELETE FROM functions WHERE function_id = ?", (func_id,))
            functions_processed += 1
        
        print(f"   🗑️  Removed {len(target_func_ids)} original functions")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Advanced consolidation completed!")
    print(f"   📊 Functions processed: {functions_processed}")
    
    return functions_processed

def generalize_method_call_advanced(method_call: str, method_name: str) -> str:
    """Make method calls even more generic"""
    
    # Remove specific naming patterns
    generic_call = method_call
    
    # Replace specific spline/point names with generic ones
    generic_call = generic_call.replace('spline1', 'spline')
    generic_call = generic_call.replace('spline2', 'spline') 
    generic_call = generic_call.replace('spline3', 'spline')
    generic_call = generic_call.replace('spline4', 'spline')
    generic_call = generic_call.replace('spline5', 'spline')
    generic_call = generic_call.replace('spline6', 'spline')
    
    generic_call = generic_call.replace('point1', 'point')
    generic_call = generic_call.replace('point2', 'point')
    generic_call = generic_call.replace('point3', 'point')
    generic_call = generic_call.replace('point4', 'point')
    
    generic_call = generic_call.replace('extrude1', 'extrude')
    generic_call = generic_call.replace('extrude2', 'extrude')
    generic_call = generic_call.replace('extrude3', 'extrude')
    generic_call = generic_call.replace('extrude4', 'extrude')
    
    # Replace specific names in assignments
    generic_call = generic_call.replace("'Spline.1'", "'Spline.N'")
    generic_call = generic_call.replace("'Spline.2'", "'Spline.N'")
    generic_call = generic_call.replace("'Spline.3'", "'Spline.N'")
    generic_call = generic_call.replace("'Spline.4'", "'Spline.N'")
    generic_call = generic_call.replace("'Spline.5'", "'Spline.N'")
    generic_call = generic_call.replace("'Spline.6'", "'Spline.N'")
    
    generic_call = generic_call.replace("'Point.1'", "'Point.N'")
    generic_call = generic_call.replace("'Point.2'", "'Point.N'")
    generic_call = generic_call.replace("'Point.3'", "'Point.N'")
    generic_call = generic_call.replace("'Point.4'", "'Point.N'")
    
    generic_call = generic_call.replace("'Extrude.1'", "'Extrude.N'")
    generic_call = generic_call.replace("'Extrude.2'", "'Extrude.N'")
    generic_call = generic_call.replace("'Extrude.3'", "'Extrude.N'")
    generic_call = generic_call.replace("'Extrude.4'", "'Extrude.N'")
    
    return generic_call

def show_final_library_state():
    """Show the final optimized library state"""
    
    conn = sqlite3.connect("functions.db")
    cursor = conn.cursor()
    
    print(f"\n📊 FINAL OPTIMIZED LIBRARY STATE")
    print("=" * 60)
    
    # Get final statistics
    cursor.execute("SELECT COUNT(*) FROM functions")
    func_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_methods")
    method_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parameters")
    param_count = cursor.fetchone()[0]
    
    print(f"📈 Final Statistics:")
    print(f"   Functions: {func_count}")
    print(f"   Methods: {method_count}")
    print(f"   Parameters: {param_count}")
    
    # Show functions by category
    cursor.execute("""
        SELECT category, COUNT(*) as count, GROUP_CONCAT(function_name, ', ') as names
        FROM functions
        GROUP BY category
        ORDER BY count DESC
    """)
    
    categories = cursor.fetchall()
    
    print(f"\n📁 Functions by Category:")
    for category, count, names in categories:
        print(f"   {category}: {count} functions")
        name_list = names.split(', ')
        for name in name_list:
            print(f"     • {name}")
    
    conn.close()

def main():
    """Main consolidation function"""
    
    print("🚀 ADVANCED FUNCTION LIBRARY CONSOLIDATION")
    print("=" * 60)
    
    # Step 1: Analyze current state
    print("1️⃣ Analyzing current functions...")
    consolidation_groups = analyze_remaining_duplicates()
    
    # Step 2: Perform advanced consolidation
    print("\n2️⃣ Performing consolidation...")
    processed = consolidate_advanced_functions()
    
    # Step 3: Show final state
    print("\n3️⃣ Final library state...")
    show_final_library_state()
    
    print(f"\n🎉 ADVANCED CONSOLIDATION COMPLETE!")
    print(f"✅ Further optimized the function library")
    print(f"✅ Merged similar spline, point, and extrude functions")
    print(f"✅ Created more generic and reusable templates")

if __name__ == "__main__":
    main()