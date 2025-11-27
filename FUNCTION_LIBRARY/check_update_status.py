import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("🔍 CHECKING DATABASE UPDATE STATUS")
print("=" * 50)

# Check for generic functions
generic_functions = [
    'Create_Additional_Point',
    'Create_Additional_Spline', 
    'Create_Guide_Spline',
    'Create_Support_Extrude',
    'Join_Surfaces'
]

print("🎯 Looking for generic functions:")
for func_name in generic_functions:
    cursor.execute("SELECT function_id, function_description FROM functions WHERE function_name = ?", (func_name,))
    result = cursor.fetchone()
    if result:
        print(f"✅ {func_name} - FOUND (ID: {result[0]})")
        print(f"   📝 {result[1]}")
    else:
        print(f"❌ {func_name} - NOT FOUND")

# Check for old duplicate functions that should be removed
old_functions = [
    'Create_Additional_Point3',
    'Create_Additional_Point4',
    'Create_Extrude3', 
    'Create_Extrude4'
]

print(f"\n🗑️  Checking if old functions were removed:")
for func_name in old_functions:
    cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", (func_name,))
    result = cursor.fetchone()
    if result:
        print(f"❌ {func_name} - STILL EXISTS (should be removed)")
    else:
        print(f"✅ {func_name} - REMOVED")

# Check method calls format
print(f"\n🔧 Checking method call format:")
cursor.execute("""
    SELECT method_name, method_call, method_parameters
    FROM function_methods 
    WHERE function_ref = (SELECT function_id FROM functions WHERE function_name = 'Create_Additional_Point')
    ORDER BY step_order
    LIMIT 3
""")

methods = cursor.fetchall()
if methods:
    print("Sample methods from Create_Additional_Point:")
    for method_name, method_call, method_params in methods:
        print(f"  • {method_name}")
        print(f"    Call: {method_call}")
        print(f"    Params: {method_params}")
else:
    print("❌ No methods found for Create_Additional_Point")

# Overall stats
print(f"\n📊 Database Statistics:")
cursor.execute("SELECT COUNT(*) FROM functions")
func_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM function_methods")  
method_count = cursor.fetchone()[0]

print(f"Functions: {func_count}")
print(f"Methods: {method_count}")

conn.close()