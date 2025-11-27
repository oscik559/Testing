"""
Function Library Database Schema
Creates a database to store CATIA automation functions, their methods, and parameters.
"""

import sqlite3
import os
from datetime import datetime

def create_functions_database():
    """Create the functions.db database with required tables"""
    
    # Database file path
    db_path = os.path.join("FUNCTION_LIBRARY", "functions.db")
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create functions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS functions (
            function_id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_name TEXT NOT NULL UNIQUE,
            function_description TEXT,
            category TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create function_methods table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS function_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref INTEGER NOT NULL,
            method_name TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            object_chain TEXT,
            method_call TEXT,
            method_parameters TEXT,
            object_type TEXT,
            return_type TEXT,
            method_description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (function_ref) REFERENCES functions(function_id) ON DELETE CASCADE
        )
    """)
    
    # Create parameters table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_ref INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_type TEXT,
            parameter_value TEXT,
            parameter_position INTEGER,
            parameter_description TEXT,
            FOREIGN KEY (method_ref) REFERENCES function_methods(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_function_methods_function_ref ON function_methods(function_ref)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_function_methods_step_order ON function_methods(step_order)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameters_method_ref ON parameters(method_ref)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameters_position ON parameters(parameter_position)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_functions_category ON functions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_functions_name ON functions(function_name)")
    
    # Commit changes
    conn.commit()
    print(f"Database created successfully at: {db_path}")
    
    # Display table structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {[table[0] for table in tables]}")
    
    # Show table schemas
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\nTable '{table_name}' structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})" + (" PRIMARY KEY" if col[5] else "") + (" NOT NULL" if col[3] else ""))
    
    conn.close()
    return db_path

def verify_database():
    """Verify the database was created correctly"""
    db_path = os.path.join("FUNCTION_LIBRARY", "functions.db")
    
    if not os.path.exists(db_path):
        print("Database file does not exist!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = ['functions', 'function_methods', 'parameters']
    
    for table in expected_tables:
        if table in tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing")
            return False
    
    # Check foreign key constraints
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    if not fk_violations:
        print("✓ Foreign key constraints are valid")
    else:
        print(f"✗ Foreign key violations: {fk_violations}")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("Creating Function Library Database Schema...")
    print("=" * 50)
    
    # Create FUNCTION_LIBRARY directory if it doesn't exist
    if not os.path.exists("FUNCTION_LIBRARY"):
        os.makedirs("FUNCTION_LIBRARY")
        print("Created FUNCTION_LIBRARY directory")
    
    # Create the database
    db_path = create_functions_database()
    
    print("\n" + "=" * 50)
    print("Verifying Database...")
    
    # Verify the database
    if verify_database():
        print("\n✓ Database schema created successfully!")
        print(f"Database location: {os.path.abspath(db_path)}")
    else:
        print("\n✗ Database verification failed!")