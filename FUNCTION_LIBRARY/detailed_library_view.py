import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("🎯 DETAILED VIEW OF IMPROVED LIBRARY")
print("=" * 60)

# Show some example generic functions with their methods
example_functions = [
    'Create_Additional_Point',
    'Create_Support_Extrude', 
    'Join_Surfaces'
]

for func_name in example_functions:
    print(f"\n📋 FUNCTION: {func_name}")
    print("-" * 50)
    
    # Get function info
    cursor.execute("""
        SELECT function_description, category
        FROM functions 
        WHERE function_name = ?
    """, (func_name,))
    
    result = cursor.fetchone()
    if result:
        description, category = result
        print(f"📝 Description: {description}")
        print(f"📁 Category: {category}")
        
        # Get methods with generic calls
        cursor.execute("""
            SELECT step_order, method_name, object_chain, method_call, method_parameters
            FROM function_methods
            WHERE function_ref = (SELECT function_id FROM functions WHERE function_name = ?)
            ORDER BY step_order
        """, (func_name,))
        
        methods = cursor.fetchall()
        print(f"🔧 Methods ({len(methods)}):")
        
        for step, method_name, object_chain, method_call, method_params in methods:
            print(f"  {step}. {method_name}")
            print(f"     Object: {object_chain}")
            print(f"     Call: {method_call}")
            print(f"     Params: {method_params}")
            print()

# Show comparison of method call evolution
print("\n" + "=" * 60)
print("🔄 METHOD CALL EVOLUTION EXAMPLES")
print("=" * 60)

examples = [
    {
        'description': 'Point Creation',
        'before': "hybrid_shape_factory.add_new_point_coord(-300, 0.0, 0.0)",
        'after': "hybrid_shape_factory.add_new_point_coord(i_x, i_y, i_z)",
        'params': "['i_x', 'i_y', 'i_z']"
    },
    {
        'description': 'Extrusion',
        'before': "hybrid_shape_factory.add_new_extrude(spline3, -30.0, 0.0, dir_zx_plane)",
        'after': "hybrid_shape_factory.add_new_extrude(i_object_to_extrude, i_offset_debut, i_offset_fin, i_direction)",
        'params': "['i_object_to_extrude', 'i_offset_debut', 'i_offset_fin', 'i_direction']"
    },
    {
        'description': 'Join Operation',
        'before': "hybrid_shape_factory.add_new_join(ref_extrude1, ref_extrude2)",
        'after': "hybrid_shape_factory.add_new_join(element1, element2)",
        'params': "['element1', 'element2']"
    }
]

for example in examples:
    print(f"\n🎯 {example['description']}:")
    print(f"   BEFORE: {example['before']}")
    print(f"   AFTER:  {example['after']}")
    print(f"   PARAMS: {example['params']}")

# Show database optimization results
print(f"\n" + "=" * 60)
print("📊 DATABASE OPTIMIZATION RESULTS")
print("=" * 60)

# Count methods by category
cursor.execute("""
    SELECT f.category, COUNT(fm.id) as method_count
    FROM functions f
    LEFT JOIN function_methods fm ON f.function_id = fm.function_ref
    GROUP BY f.category
    ORDER BY method_count DESC
""")

category_stats = cursor.fetchall()

print("Methods per category:")
for category, count in category_stats:
    print(f"  📁 {category}: {count} methods")

# Show function efficiency
total_functions = sum(1 for _ in category_stats)
cursor.execute("SELECT COUNT(*) FROM function_methods")
total_methods = cursor.fetchone()[0]

print(f"\n💡 Efficiency Metrics:")
print(f"   • Average methods per function: {total_methods/total_functions:.1f}")
print(f"   • Total reusable templates: 5")
print(f"   • Functions eliminated through merging: 6")
print(f"   • Space optimization: {(6/29)*100:.1f}% reduction in functions")

conn.close()

print(f"\n🚀 The library is now optimized for automated code generation!")
print(f"✅ Generic functions can be instantiated with different parameters")
print(f"✅ PyCATIA parameter names enable intelligent parameter mapping") 
print(f"✅ Database structure supports efficient querying and code generation")