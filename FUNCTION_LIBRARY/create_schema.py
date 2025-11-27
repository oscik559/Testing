"""
Function Library Database Schema Creator
Creates the complete database structure for the function library
Run this first to create the empty database with proper schema
"""

import sqlite3
import os
from datetime import datetime

def create_function_library_schema(db_path="functions.db"):
    """Create the complete function library database schema"""
    
    print("🏗️  CREATING FUNCTION LIBRARY DATABASE SCHEMA")
    print("=" * 60)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database: {db_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📋 Creating functions table...")
    cursor.execute("""
        CREATE TABLE functions (
            function_id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_name TEXT NOT NULL UNIQUE,
            function_description TEXT,
            category TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("🔧 Creating function_methods table...")
    cursor.execute("""
        CREATE TABLE function_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref INTEGER NOT NULL,
            method_name TEXT NOT NULL,
            step_order INTEGER NOT NULL DEFAULT 1,
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
    
    print("📝 Creating parameters table...")
    cursor.execute("""
        CREATE TABLE parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_ref INTEGER NOT NULL,
            method_ref INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_type TEXT,
            parameter_value TEXT,
            parameter_position INTEGER DEFAULT 1,
            parameter_description TEXT,
            parameter_type_flag INTEGER DEFAULT 1,
            FOREIGN KEY (function_ref) REFERENCES functions(function_id) ON DELETE CASCADE,
            FOREIGN KEY (method_ref) REFERENCES function_methods(id) ON DELETE CASCADE
        )
    """)
    
    print("🔍 Creating performance indexes...")
    
    # Functions indexes
    cursor.execute("CREATE INDEX idx_functions_category ON functions(category)")
    cursor.execute("CREATE INDEX idx_functions_name ON functions(function_name)")
    
    # Function_methods indexes
    cursor.execute("CREATE INDEX idx_function_methods_function_ref ON function_methods(function_ref)")
    cursor.execute("CREATE INDEX idx_function_methods_step_order ON function_methods(step_order)")
    cursor.execute("CREATE INDEX idx_function_methods_name ON function_methods(method_name)")
    
    # Parameters indexes
    cursor.execute("CREATE INDEX idx_parameters_function_ref ON parameters(function_ref)")
    cursor.execute("CREATE INDEX idx_parameters_method_ref ON parameters(method_ref)")
    cursor.execute("CREATE INDEX idx_parameters_type_flag ON parameters(parameter_type_flag)")
    cursor.execute("CREATE INDEX idx_parameters_name ON parameters(parameter_name)")
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Commit changes
    conn.commit()
    
    # Verify schema creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    print(f"\n✅ Schema creation completed!")
    print(f"📊 Created tables: {len(tables)} ({', '.join(tables)})")
    print(f"📊 Created indexes: {len([i for i in indexes if not i.startswith('sqlite_')])}")
    
    # Show schema details
    print(f"\n📋 SCHEMA DETAILS:")
    
    for table in tables:
        if table != 'sqlite_sequence':
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n📊 {table} table:")
            for col_id, col_name, col_type, not_null, default_val, pk in columns:
                constraints = []
                if pk:
                    constraints.append("PRIMARY KEY")
                if not_null:
                    constraints.append("NOT NULL")
                if default_val is not None:
                    constraints.append(f"DEFAULT {default_val}")
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                print(f"   • {col_name} ({col_type}){constraint_str}")
    
    # Show foreign key relationships
    print(f"\n🔗 FOREIGN KEY RELATIONSHIPS:")
    print(f"   • function_methods.function_ref → functions.function_id")
    print(f"   • parameters.function_ref → functions.function_id") 
    print(f"   • parameters.method_ref → function_methods.id")
    
    # Show parameter type flag meaning
    print(f"\n🏷️  PARAMETER TYPE FLAG:")
    print(f"   • parameter_type_flag = 1 → Variable (objects, outputs)")
    print(f"   • parameter_type_flag = 0 → Input (values, literals)")
    
    conn.close()
    
    print(f"\n🎉 DATABASE SCHEMA READY!")
    print(f"📁 Database file: {os.path.abspath(db_path)}")
    print(f"✅ Ready for population with data")
    
    return True

def verify_schema(db_path="functions.db"):
    """Verify the created schema"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Test foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        
        if fk_violations:
            print(f"⚠️  Foreign key violations found: {fk_violations}")
        else:
            print(f"✅ Foreign key constraints verified")
        
        # Test table creation
        cursor.execute("SELECT COUNT(*) FROM functions")
        cursor.execute("SELECT COUNT(*) FROM function_methods") 
        cursor.execute("SELECT COUNT(*) FROM parameters")
        
        print(f"✅ All tables accessible and empty")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        conn.close()
        return False

def main():
    """Main schema creation function"""
    
    print("🚀 FUNCTION LIBRARY SCHEMA CREATOR")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create schema
    success = create_function_library_schema()
    
    if success:
        # Verify schema
        verify_success = verify_schema()
        
        if verify_success:
            print(f"\n🎊 SCHEMA CREATION COMPLETE!")
            print(f"✅ Database schema created successfully")
            print(f"✅ All tables and indexes in place")
            print(f"✅ Foreign key constraints enabled")
            print(f"")
            print(f"📋 NEXT STEP:")
            print(f"   Run: python populate_database.py")
            print(f"   This will populate the database with function data")
        else:
            print(f"\n❌ Schema verification failed")
    else:
        print(f"\n❌ Schema creation failed")

if __name__ == "__main__":
    main()