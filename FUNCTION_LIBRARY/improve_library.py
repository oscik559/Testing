"""
Function Generalization and Database Update Script
Creates generic function templates and updates method calls to use parameter placeholders
"""

import sqlite3
import re
from typing import Dict, List, Tuple

def get_pycatia_method_signature(method_name: str, pycatia_db_path: str = "../pycatia_methods.db") -> Dict:
    """Get method signature from pycatia database"""
    try:
        conn = sqlite3.connect(pycatia_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pm.id, pm.method_name, pm.full_method_name, pm.return_annotation
            FROM pycatia_methods pm
            WHERE pm.method_name = ?
            LIMIT 1
        """, (method_name,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
            
        method_id, name, full_name, return_annotation = result
        
        # Get parameters
        cursor.execute("""
            SELECT parameter_position, parameter_name, parameter_annotation,
                   has_default, default_value_repr
            FROM method_parameters
            WHERE method_id = ?
            ORDER BY parameter_position
        """, (method_id,))
        
        parameters = cursor.fetchall()
        
        conn.close()
        
        return {
            'method_name': name,
            'full_method_name': full_name,
            'return_annotation': return_annotation,
            'parameters': parameters
        }
    except Exception as e:
        print(f"Error getting signature for {method_name}: {e}")
        return None

def generalize_method_call(method_call: str, method_name: str, pycatia_db_path: str = "../pycatia_methods.db") -> Tuple[str, List[str]]:
    """Convert specific method call to generic template with parameter names"""
    
    # Get PyCATIA method signature
    signature = get_pycatia_method_signature(method_name, pycatia_db_path)
    
    if not signature or not signature['parameters']:
        # Fallback: just replace with generic parameters
        if '(' in method_call:
            method_part, params_part = method_call.split('(', 1)
            params_part = params_part.rstrip(')')
            
            if params_part.strip():
                param_count = len([p.strip() for p in params_part.split(',') if p.strip()])
                generic_params = ', '.join([f'param{i+1}' for i in range(param_count)])
                param_names = [f'param{i+1}' for i in range(param_count)]
            else:
                generic_params = ''
                param_names = []
            
            return f"{method_part}({generic_params})", param_names
        return method_call, []
    
    # Use actual parameter names from PyCATIA
    param_names = []
    for pos, param_name, param_annotation, has_default, default_value in signature['parameters']:
        param_names.append(param_name)
    
    # Create generic method call
    if '(' in method_call:
        method_part, _ = method_call.split('(', 1)
        generic_params = ', '.join(param_names)
        generic_call = f"{method_part}({generic_params})"
    else:
        generic_call = method_call
    
    return generic_call, param_names

def merge_similar_functions(db_path: str = "functions.db"):
    """Merge similar functions into generic templates"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Define merge groups based on our analysis
    merge_groups = [
        {
            'generic_name': 'Create_Additional_Point',
            'generic_description': 'Create additional spanwise reference points',
            'category': 'Construction_Geometry',
            'original_functions': ['Create_Additional_Point3', 'Create_Additional_Point4']
        },
        {
            'generic_name': 'Create_Additional_Spline',
            'generic_description': 'Create additional spanwise splines for wing structure',
            'category': 'Curve_Creation',
            'original_functions': ['Create_Additional_Spline3', 'Create_Additional_Spline4']
        },
        {
            'generic_name': 'Create_Guide_Spline',
            'generic_description': 'Create guide splines for loft surface control',
            'category': 'Curve_Creation',
            'original_functions': ['Create_Guide_Spline5', 'Create_Guide_Spline6']
        },
        {
            'generic_name': 'Create_Support_Extrude',
            'generic_description': 'Create support extrusions for loft scaffolding',
            'category': 'Surface_Creation',
            'original_functions': ['Create_Extrude3', 'Create_Extrude4']
        },
        {
            'generic_name': 'Join_Surfaces',
            'generic_description': 'Join surfaces with specified parameters',
            'category': 'Surface_Creation',
            'original_functions': ['Join_All_Surfaces', 'Join_Extrude_Surfaces', 'Join_Loft_Surfaces']
        }
    ]
    
    print("Merging similar functions...")
    
    for group in merge_groups:
        print(f"\n📝 Processing group: {group['generic_name']}")
        
        # Get one representative function's methods (use the first one)
        first_func_name = group['original_functions'][0]
        
        cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", (first_func_name,))
        result = cursor.fetchone()
        
        if not result:
            print(f"   ❌ Function {first_func_name} not found")
            continue
            
        template_func_id = result[0]
        
        # Create new generic function
        cursor.execute("""
            INSERT INTO functions (function_name, function_description, category)
            VALUES (?, ?, ?)
        """, (group['generic_name'], group['generic_description'], group['category']))
        
        new_func_id = cursor.lastrowid
        print(f"   ✓ Created generic function: {group['generic_name']} (ID: {new_func_id})")
        
        # Get template methods
        cursor.execute("""
            SELECT method_name, step_order, object_chain, method_call, 
                   method_parameters, object_type, return_type, method_description
            FROM function_methods
            WHERE function_ref = ?
            ORDER BY step_order
        """, (template_func_id,))
        
        template_methods = cursor.fetchall()
        
        # Create generic methods
        for method_data in template_methods:
            method_name, step_order, object_chain, method_call, method_params, object_type, return_type, method_desc = method_data
            
            # Generalize the method call
            generic_call, param_names = generalize_method_call(method_call, method_name)
            
            # Insert generic method
            cursor.execute("""
                INSERT INTO function_methods (
                    function_ref, method_name, step_order, object_chain,
                    method_call, method_parameters, object_type, return_type, method_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_func_id,
                method_name,
                step_order,
                object_chain,
                generic_call,
                str(param_names),  # Store parameter names as list
                object_type,
                return_type,
                method_desc
            ))
            
            print(f"     • Added method: {object_chain}.{method_name}")
            print(f"       Generic call: {generic_call}")
        
        # Delete original functions
        for orig_func_name in group['original_functions']:
            cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", (orig_func_name,))
            result = cursor.fetchone()
            if result:
                orig_func_id = result[0]
                # Delete will cascade to function_methods and parameters due to foreign keys
                cursor.execute("DELETE FROM functions WHERE function_id = ?", (orig_func_id,))
                print(f"   🗑️  Deleted original function: {orig_func_name}")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Function merging completed!")

def update_all_method_calls(db_path: str = "functions.db"):
    """Update all method calls to use generic parameter placeholders"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nUpdating all method calls to generic format...")
    
    # Get all function methods
    cursor.execute("""
        SELECT id, method_name, method_call
        FROM function_methods
        WHERE method_call LIKE '%(%'
    """)
    
    methods = cursor.fetchall()
    
    updated_count = 0
    
    for method_id, method_name, method_call in methods:
        # Skip if already generic
        if 'param1' in method_call or not '(' in method_call:
            continue
            
        generic_call, param_names = generalize_method_call(method_call, method_name)
        
        if generic_call != method_call:
            cursor.execute("""
                UPDATE function_methods 
                SET method_call = ?, method_parameters = ?
                WHERE id = ?
            """, (generic_call, str(param_names), method_id))
            
            updated_count += 1
            
            if updated_count <= 5:  # Show first 5 examples
                print(f"   Updated: {method_call}")
                print(f"        →  {generic_call}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated_count} method calls to generic format")

def main():
    """Main function to improve the library"""
    
    print("Function Library Improvement")
    print("=" * 50)
    
    # Step 1: Export current database
    print("\n1. Exporting current database...")
    from export_database import export_all
    export_all()
    
    # Step 2: Merge similar functions
    print("\n2. Merging similar functions...")
    merge_similar_functions()
    
    # Step 3: Update all method calls to generic format
    print("\n3. Updating method calls to generic format...")
    update_all_method_calls()
    
    # Step 4: Show final statistics
    print("\n4. Final database statistics:")
    conn = sqlite3.connect("functions.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM functions")
    func_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_methods")
    method_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parameters")
    param_count = cursor.fetchone()[0]
    
    print(f"   📊 Functions: {func_count}")
    print(f"   📊 Methods: {method_count}")
    print(f"   📊 Parameters: {param_count}")
    
    conn.close()
    
    print(f"\n🚀 Library improvement completed!")

if __name__ == "__main__":
    main()