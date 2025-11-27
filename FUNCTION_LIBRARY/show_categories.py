import sqlite3

conn = sqlite3.connect('functions.db')
cursor = conn.cursor()

print("Function Library Categories")
print("=" * 50)

# Get all categories and their functions
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM functions
    GROUP BY category
    ORDER BY category
""")

categories = cursor.fetchall()

for category, count in categories:
    print(f"\n📁 {category} ({count} functions):")
    
    cursor.execute("""
        SELECT function_name, function_description
        FROM functions
        WHERE category = ?
        ORDER BY function_name
    """, (category,))
    
    functions = cursor.fetchall()
    for name, desc in functions:
        # Truncate description for display
        short_desc = desc[:60] + "..." if len(desc) > 60 else desc
        print(f"   • {name}")
        if short_desc:
            print(f"     └─ {short_desc}")

conn.close()