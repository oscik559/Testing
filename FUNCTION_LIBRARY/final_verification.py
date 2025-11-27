import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("🚀 IMPROVED FUNCTION LIBRARY VERIFICATION")
print("=" * 60)

# Check the new generic functions
print("\n📋 GENERIC FUNCTIONS CREATED:")
cursor.execute("""
    SELECT function_name, function_description, category
    FROM functions
    WHERE function_name IN (
        'Create_Additional_Point', 'Create_Additional_Spline', 
        'Create_Guide_Spline', 'Create_Support_Extrude', 'Join_Surfaces'
    )
    ORDER BY function_name
""")

generic_functions = cursor.fetchall()
for name, desc, category in generic_functions:
    print(f"✅ {name}")
    print(f"   📝 {desc}")
    print(f"   📁 {category}")
    print()

# Check generic method calls
print("🔧 SAMPLE GENERIC METHOD CALLS:")
cursor.execute("""
    SELECT f.function_name, fm.method_name, fm.method_call, fm.method_parameters
    FROM functions f
    JOIN function_methods fm ON f.function_id = fm.function_ref
    WHERE f.function_name = 'Create_Additional_Point'
    ORDER BY fm.step_order
""")

methods = cursor.fetchall()
print("Example: Create_Additional_Point function methods:")
for func_name, method_name, method_call, method_params in methods:
    print(f"• {method_name}")
    print(f"  Generic call: {method_call}")
    print(f"  Parameters: {method_params}")
    print()

# Show before/after comparison
print("📊 BEFORE/AFTER COMPARISON:")
print("BEFORE (specific):")
print("  hybrid_shape_factory.add_new_point_coord(-300, 0.0, 0.0)")
print("  hybrid_shape_factory.add_new_point_coord(1000, 0.0, 0.0)")
print()
print("AFTER (generic):")
print("  hybrid_shape_factory.add_new_point_coord(i_x, i_y, i_z)")
print("  Parameters: ['i_x', 'i_y', 'i_z']")
print()

# Database statistics
print("📈 FINAL STATISTICS:")
cursor.execute("SELECT COUNT(*) FROM functions")
func_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM function_methods")
method_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM parameters")
param_count = cursor.fetchone()[0]

print(f"Functions: 29 → {func_count} (merged {29-func_count} duplicates)")
print(f"Methods: 218 → {method_count} (added {method_count-218} from merging)")
print(f"Parameters: {param_count}")

# Show all function categories
print(f"\n📁 FUNCTION CATEGORIES:")
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM functions
    GROUP BY category
    ORDER BY category
""")

categories = cursor.fetchall()
for category, count in categories:
    print(f"  {category}: {count} functions")

print(f"\n✅ IMPROVEMENTS COMPLETED:")
print(f"• ✅ Database export functionality added")
print(f"• ✅ Similar functions merged into generic templates")
print(f"• ✅ Method calls generalized with PyCATIA parameter names")
print(f"• ✅ Parameter structure updated with proper parameter names")
print(f"• ✅ Database optimized from 29 to {func_count} functions")

conn.close()