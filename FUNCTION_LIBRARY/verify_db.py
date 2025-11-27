import sqlite3

# Connect to the database
conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("Database Verification")
print("=" * 50)

# Check functions table
cursor.execute("SELECT COUNT(*) FROM functions")
func_count = cursor.fetchone()[0]
print(f"Functions count: {func_count}")

cursor.execute("SELECT function_name, category FROM functions LIMIT 10")
functions = cursor.fetchall()
print(f"\nSample Functions:")
for name, category in functions:
    print(f"  - {name} [{category}]")

# Check function_methods table  
cursor.execute("SELECT COUNT(*) FROM function_methods")
method_count = cursor.fetchone()[0]
print(f"\nFunction Methods count: {method_count}")

cursor.execute("""
    SELECT fm.method_name, fm.object_chain, f.function_name 
    FROM function_methods fm 
    JOIN functions f ON fm.function_ref = f.function_id 
    LIMIT 10
""")
methods = cursor.fetchall()
print(f"\nSample Methods:")
for method_name, object_chain, func_name in methods:
    chain = object_chain if object_chain else "standalone"
    print(f"  - {chain}.{method_name} (from {func_name})")

# Check parameters table
cursor.execute("SELECT COUNT(*) FROM parameters")
param_count = cursor.fetchone()[0]
print(f"\nParameters count: {param_count}")

cursor.execute("""
    SELECT p.parameter_name, p.parameter_type, fm.method_name
    FROM parameters p
    JOIN function_methods fm ON p.method_ref = fm.id
    LIMIT 10
""")
params = cursor.fetchall()
print(f"\nSample Parameters:")
for param_name, param_type, method_name in params:
    print(f"  - {param_name} ({param_type}) for {method_name}")

conn.close()
print(f"\n✓ Database contains {func_count} functions, {method_count} methods, and {param_count} parameters")