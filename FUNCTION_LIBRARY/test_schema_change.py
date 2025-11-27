import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("Checking the new function_methods table structure:")
print("=" * 60)

# Get table schema
cursor.execute("PRAGMA table_info(function_methods)")
columns = cursor.fetchall()

print("Column order in function_methods table:")
for i, (cid, name, data_type, notnull, default, pk) in enumerate(columns, 1):
    print(f"{i:2d}. {name} ({data_type})")

print(f"\n✓ method_description is now column #{[col[1] for col in columns].index('method_description') + 1}")
print(f"✓ return_type is now column #{[col[1] for col in columns].index('return_type') + 1}")

# Test a sample query
print(f"\nSample data from function_methods:")
cursor.execute("""
    SELECT method_name, object_chain, return_type, method_description 
    FROM function_methods 
    LIMIT 3
""")

for method_name, object_chain, return_type, method_desc in cursor.fetchall():
    print(f"- {object_chain}.{method_name}")
    print(f"  Return type: {return_type}")
    print(f"  Description: {method_desc[:50]}..." if method_desc and len(method_desc) > 50 else f"  Description: {method_desc}")
    print()

conn.close()