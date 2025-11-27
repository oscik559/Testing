"""
complimentary_library_schema.py - Database creation script

Contains CREATE TABLE statements and database creation logic
Imports data from the populate script
When executed, creates and populates the database
"""

import sqlite3
import os
from datetime import datetime
from complimentary_library_populate import (
    FUNCTIONS_DATA,
    PARAMETERS_DATA, 
    EXAMPLES_DATA,
    DEPENDENCIES_DATA
)

DATABASE_PATH = 'complimentary_library.db'



def create_database_schema(db_path: str = DATABASE_PATH):
    """Create the database schema with all required tables"""
    
    # Remove existing database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating database schema in: {db_path}")
    
    # Create functions table (master function definitions)
    cursor.execute("""
        CREATE TABLE functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_id TEXT NOT NULL UNIQUE,
            function_name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created table: functions")
    
    # Create function_methods table (individual method calls within functions)
    cursor.execute("""
        CREATE TABLE function_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref_id INTEGER NOT NULL,
            method_name TEXT NOT NULL,
            step_order INTEGER DEFAULT 1,
            description TEXT,
            object_chain TEXT,
            full_call TEXT,
            return_type TEXT,
            object_type TEXT,
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (function_ref_id) REFERENCES functions(id)
        )
    """)
    print("Created table: function_methods")
    
    # Create function_parameters table
    cursor.execute("""
        CREATE TABLE function_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_ref_id INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_type TEXT,
            parameter_value TEXT,
            is_required BOOLEAN DEFAULT TRUE,
            parameter_order INTEGER,
            description TEXT,
            example_values TEXT,
            validation_rules TEXT,
            FOREIGN KEY (method_ref_id) REFERENCES function_methods(id)
        )
    """)
    print("Created table: function_parameters")
    
    # Create function_examples table
    cursor.execute("""
        CREATE TABLE function_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref_id INTEGER NOT NULL,
            example_name TEXT,
            example_code TEXT,
            example_description TEXT,
            input_parameters TEXT,
            expected_output TEXT,
            use_case TEXT,
            FOREIGN KEY (function_ref_id) REFERENCES functions(id)
        )
    """)
    print("Created table: function_examples")
    
    # Create function_dependencies table
    cursor.execute("""
        CREATE TABLE function_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref_id INTEGER NOT NULL,
            depends_on_function_ref_id INTEGER NOT NULL,
            dependency_type TEXT DEFAULT 'requires',
            description TEXT,
            FOREIGN KEY (function_ref_id) REFERENCES functions(id),
            FOREIGN KEY (depends_on_function_ref_id) REFERENCES functions(id)
        )
    """)
    print("Created table: function_dependencies")
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX idx_functions_function_id ON functions(function_id)")
    cursor.execute("CREATE INDEX idx_functions_category ON functions(category)")
    cursor.execute("CREATE INDEX idx_methods_function_ref_id ON function_methods(function_ref_id)")
    cursor.execute("CREATE INDEX idx_methods_object_type ON function_methods(object_type)")
    cursor.execute("CREATE INDEX idx_methods_step_order ON function_methods(step_order)")
    cursor.execute("CREATE INDEX idx_parameters_method_ref_id ON function_parameters(method_ref_id)")
    cursor.execute("CREATE INDEX idx_examples_function_ref_id ON function_examples(function_ref_id)")
    cursor.execute("CREATE INDEX idx_dependencies_function_ref_id ON function_dependencies(function_ref_id)")
    print("Created database indexes")
    
    conn.commit()
    conn.close()
    print("Database schema created successfully")

def populate_database(db_path: str = DATABASE_PATH):
    """Populate the database with data from the populate script"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Populating database with function data...")
    
    # First, create unique functions from the FUNCTIONS_DATA
    unique_functions = {}
    for func_data in FUNCTIONS_DATA:
        function_id = func_data[1]  # function_id
        function_name = func_data[2]  # function_name
        description = func_data[4]  # description
        
        if function_id not in unique_functions:
            unique_functions[function_id] = {
                'function_name': function_name,
                'description': description,
                'category': 'General'
            }
    
    # Insert unique functions
    functions_to_insert = []
    for func_id, func_info in unique_functions.items():
        functions_to_insert.append((
            func_id,
            func_info['function_name'],
            func_info['description'],
            func_info['category']
        ))
    
    cursor.executemany("""
        INSERT INTO functions (function_id, function_name, description, category)
        VALUES (?, ?, ?, ?)
    """, functions_to_insert)
    print(f"Inserted {len(functions_to_insert)} unique functions")
    
    # Create function_id to internal_id mapping
    cursor.execute("SELECT id, function_id FROM functions")
    function_id_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Insert method data with function references
    methods_to_insert = []
    method_id_map = {}  # Map original id to new method id
    
    for func_data in FUNCTIONS_DATA:
        original_id = func_data[0]
        function_id = func_data[1]
        function_ref_id = function_id_map[function_id]
        method_name = func_data[6]
        step_order = func_data[3]  # step_variant becomes step_order
        description = func_data[4]
        object_chain = func_data[5]
        full_call = func_data[7]
        return_type = func_data[8]
        object_type = func_data[9]
        created_timestamp = func_data[10]
        
        methods_to_insert.append((
            function_ref_id, method_name, step_order, description, object_chain,
            full_call, return_type, object_type, created_timestamp
        ))
    
    cursor.executemany("""
        INSERT INTO function_methods 
        (function_ref_id, method_name, step_order, description, object_chain,
         full_call, return_type, object_type, created_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, methods_to_insert)
    print(f"Inserted {len(methods_to_insert)} method records")
    
    # Create mapping from original function IDs to new method IDs
    cursor.execute("SELECT id, function_ref_id, step_order FROM function_methods ORDER BY id")
    method_results = cursor.fetchall()
    
    for i, func_data in enumerate(FUNCTIONS_DATA):
        original_id = func_data[0]
        method_id_map[original_id] = method_results[i][0]
    
    # Insert parameters data with method references
    parameters_to_insert = []
    for param_data in PARAMETERS_DATA:
        original_param_id = param_data[0]
        original_function_id = param_data[1]
        
        if original_function_id in method_id_map:
            method_ref_id = method_id_map[original_function_id]
            parameters_to_insert.append((
                original_param_id,
                method_ref_id,
                param_data[2],  # parameter_name
                param_data[3],  # parameter_type
                param_data[4],  # parameter_value
                param_data[5],  # is_required
                param_data[6],  # parameter_order
                param_data[7],  # description
                param_data[8],  # example_values
                param_data[9]   # validation_rules
            ))
    
    cursor.executemany("""
        INSERT INTO function_parameters
        (id, method_ref_id, parameter_name, parameter_type, parameter_value,
         is_required, parameter_order, description, example_values, validation_rules)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, parameters_to_insert)
    print(f"Inserted {len(parameters_to_insert)} parameter records")
    
    # Insert examples data (if any)
    if EXAMPLES_DATA:
        cursor.executemany("""
            INSERT INTO function_examples
            (id, function_id, example_name, example_code, example_description,
             input_parameters, expected_output, use_case)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, EXAMPLES_DATA)
        print(f"Inserted {len(EXAMPLES_DATA)} example records")
    
    # Insert dependencies data (if any)
    if DEPENDENCIES_DATA:
        cursor.executemany("""
            INSERT INTO function_dependencies
            (id, function_id, depends_on_function_id, dependency_type, description)
            VALUES (?, ?, ?, ?, ?)
        """, DEPENDENCIES_DATA)
        print(f"Inserted {len(DEPENDENCIES_DATA)} dependency records")
    
    conn.commit()
    conn.close()
    print("Database population completed successfully")

def verify_database(db_path: str = DATABASE_PATH):
    """Verify the database was created and populated correctly"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nDatabase verification:")
    print("=" * 50)
    
    # Get actual counts
    cursor.execute("SELECT COUNT(*) FROM functions")
    functions_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_methods")
    methods_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_parameters")
    parameters_count = cursor.fetchone()[0]
    
    # Check table counts
    tables_to_check = [
        ('functions', functions_count, f"~{len(set([f[1] for f in FUNCTIONS_DATA]))}"),
        ('function_methods', methods_count, len(FUNCTIONS_DATA)),
        ('function_parameters', parameters_count, len(PARAMETERS_DATA)),
        ('function_examples', len(EXAMPLES_DATA), len(EXAMPLES_DATA)),
        ('function_dependencies', len(DEPENDENCIES_DATA), len(DEPENDENCIES_DATA))
    ]
    
    for table_name, actual_count, expected_count in tables_to_check:
        status = "✓"
        print(f"{status} {table_name}: {actual_count} records (expected: {expected_count})")
    
    # Show sample data
    print("\nSample function records:")
    cursor.execute("SELECT function_id, function_name, category FROM functions LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row[0]} | {row[1]} | {row[2]}")
    
    print("\nSample method records:")
    cursor.execute("""
        SELECT fm.method_name, fm.object_type, fm.step_order, f.function_id
        FROM function_methods fm 
        JOIN functions f ON fm.function_ref_id = f.id 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]}) | Step: {row[2]} | Function: {row[3]}")
    
    print("\nSample parameter records:")
    cursor.execute("""
        SELECT p.parameter_name, p.parameter_type, p.parameter_value, fm.method_name 
        FROM function_parameters p 
        JOIN function_methods fm ON p.method_ref_id = fm.id 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]}): {row[2]} | Method: {row[3]}")
    
    # Show functions with method counts
    cursor.execute("""
        SELECT f.function_id, f.function_name, f.category, COUNT(fm.id) as method_count
        FROM functions f 
        LEFT JOIN function_methods fm ON f.id = fm.function_ref_id 
        GROUP BY f.id 
        ORDER BY method_count DESC
        LIMIT 10
    """)
    print(f"\nFunctions with most methods:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[2]}): {row[3]} methods")
    
    conn.close()
    print("\nDatabase verification completed")

def rebuild_database(db_path: str = DATABASE_PATH):
    """Complete database rebuild - create schema and populate data"""
    
    print(f"Rebuilding database: {db_path}")
    print("=" * 50)
    
    # Step 1: Create schema
    create_database_schema(db_path)
    
    # Step 2: Populate with data
    populate_database(db_path)
    
    # Step 3: Verify result
    verify_database(db_path)
    
    print(f"\nDatabase rebuild completed: {db_path}")

def get_database_info(db_path: str = DATABASE_PATH):
    """Get comprehensive database information"""
    
    if not os.path.exists(db_path):
        print(f"Database does not exist: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Database Information: {db_path}")
    print("=" * 50)
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {', '.join(tables)}")
    
    # Get table info for each table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        print(f"\nTable: {table} ({count} records)")
        for col in columns:
            pk_info = " (PK)" if col[5] else ""
            null_info = " NOT NULL" if col[3] else ""
            default_info = f" DEFAULT {col[4]}" if col[4] is not None else ""
            print(f"  - {col[1]} {col[2]}{pk_info}{null_info}{default_info}")
    
    conn.close()

if __name__ == "__main__":
    # Default action: rebuild the database
    print("PyCATIA Function Library Database Schema")
    print("=" * 40)
    
    rebuild_database()
    
    print("\nTo use this script:")
    print("  rebuild_database()       - Complete rebuild")
    print("  create_database_schema() - Create schema only") 
    print("  populate_database()      - Populate data only")
    print("  verify_database()        - Verify database")
    print("  get_database_info()      - Show database info")