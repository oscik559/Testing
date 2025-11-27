import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

# Test several functions to ensure method extraction is working correctly
test_functions = [
    'Initialize_CATIA_app',
    'Define_Reference_Axes', 
    'Create_Root_Spline',
    'Create_Upper_Loft_Surface'
]

for func_name in test_functions:
    print(f"\n{'='*60}")
    print(f"Methods for '{func_name}' function:")
    print('='*60)
    
    # Get the function ID
    cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", (func_name,))
    result = cursor.fetchone()
    
    if result:
        function_id = result[0]
        
        # Get methods for this function  
        cursor.execute("""
            SELECT step_order, method_name, object_chain, method_call
            FROM function_methods
            WHERE function_ref = ?
            ORDER BY step_order
        """, (function_id,))
        
        methods = cursor.fetchall()
        
        if methods:
            for step, method_name, object_chain, method_call in methods:
                print(f"{step:2d}. {object_chain}.{method_name}")
                # Truncate long method calls for readability
                call_display = method_call[:80] + "..." if len(method_call) > 80 else method_call
                print(f"    {call_display}")
        else:
            print("No methods found")
    else:
        print(f"Function '{func_name}' not found")

# Summary statistics
print(f"\n{'='*60}")
print("SUMMARY STATISTICS")
print('='*60)

cursor.execute("SELECT COUNT(*) FROM functions")
func_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM function_methods")
method_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM parameters")
param_count = cursor.fetchone()[0]

print(f"Total Functions: {func_count}")
print(f"Total Methods: {method_count}")
print(f"Total Parameters: {param_count}")
print(f"Average Methods per Function: {method_count/func_count:.1f}")

conn.close()