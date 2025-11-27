import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("Function Analysis - Looking for Similar Functions")
print("=" * 60)

# Get functions with similar patterns
cursor.execute("""
    SELECT function_id, function_name, function_description, category
    FROM functions
    ORDER BY category, function_name
""")

functions = cursor.fetchall()

# Group by category and look for patterns
categories = {}
for func_id, name, desc, category in functions:
    if category not in categories:
        categories[category] = []
    categories[category].append({
        'id': func_id,
        'name': name,
        'description': desc
    })

# Look for similar functions within each category
similar_groups = []

for category, funcs in categories.items():
    print(f"\n📁 {category} ({len(funcs)} functions):")
    
    # Look for naming patterns
    patterns = {}
    for func in funcs:
        # Extract base name (remove numbers, common suffixes)
        base_name = func['name']
        
        # Common patterns to check
        if 'Create_Additional_Point' in base_name:
            key = 'Create_Additional_Point'
        elif 'Create_Additional_Spline' in base_name:
            key = 'Create_Additional_Spline'
        elif 'Create_Extrude' in base_name and base_name[-1].isdigit():
            key = 'Create_Extrude'
        elif 'Create_Guide_Spline' in base_name:
            key = 'Create_Guide_Spline'
        elif 'Join_' in base_name:
            key = 'Join_Operations'
        else:
            key = base_name
        
        if key not in patterns:
            patterns[key] = []
        patterns[key].append(func)
    
    # Show grouped functions
    for pattern, group_funcs in patterns.items():
        if len(group_funcs) > 1:
            print(f"  🔗 {pattern} group ({len(group_funcs)} functions):")
            for func in group_funcs:
                print(f"     • {func['name']}")
            similar_groups.append((pattern, group_funcs))
        else:
            print(f"  • {group_funcs[0]['name']}")

# Show detailed method comparison for similar groups
print(f"\n📊 Found {len(similar_groups)} groups of similar functions")

for pattern, group_funcs in similar_groups:
    print(f"\n🔍 Analyzing '{pattern}' group:")
    
    for func in group_funcs:
        print(f"\n   Function: {func['name']}")
        
        # Get methods for this function
        cursor.execute("""
            SELECT step_order, method_name, object_chain, method_call
            FROM function_methods
            WHERE function_ref = ?
            ORDER BY step_order
        """, (func['id'],))
        
        methods = cursor.fetchall()
        for step, method_name, object_chain, method_call in methods:
            # Truncate long method calls
            call_display = method_call[:60] + "..." if len(method_call) > 60 else method_call
            print(f"     {step}. {object_chain}.{method_name}")
            print(f"        {call_display}")

conn.close()