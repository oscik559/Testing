import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("Methods for 'Extrude_Root_Spline' function:")
print("=" * 50)

# Get the function ID first
cursor.execute("SELECT function_id FROM functions WHERE function_name = 'Extrude_Root_Spline'")
result = cursor.fetchone()

if result:
    function_id = result[0]
    
    # Get all methods for this function
    cursor.execute("""
        SELECT step_order, method_name, object_chain, method_call
        FROM function_methods 
        WHERE function_ref = ?
        ORDER BY step_order
    """, (function_id,))
    
    methods = cursor.fetchall()
    
    if methods:
        for step, method_name, object_chain, method_call in methods:
            print(f"Step {step}: {method_name}")
            print(f"  Object chain: {object_chain}")
            print(f"  Method call: {method_call}")
            print()
    else:
        print("No methods found for this function")
else:
    print("Function 'Extrude_Root_Spline' not found in database")

print("\n" + "=" * 50)
print("Expected methods should include:")
print("- add_new_direction")
print("- add_new_extrude") 
print("- name (property assignment)")
print("- append_hybrid_shape")
print("- update")

conn.close()