import sqlite3

def examine_database():
    conn = sqlite3.connect('C:/Users/oscik35/Desktop/PROJECTS/TEST/complimentary_table_approach/complimentary_library.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [table[0] for table in tables])
    
    # Get schema for each table
    for table in tables:
        table_name = table[0]
        print(f"\n--- Table: {table_name} ---")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} {col[2]} (PK: {col[5]}, NotNull: {col[3]}, Default: {col[4]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")
        
        # Show first few rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        print("Sample data (first 3 rows):")
        for row in rows:
            print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    examine_database()