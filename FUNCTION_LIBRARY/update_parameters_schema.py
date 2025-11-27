"""
Update Parameters Table Schema
Adds 'variable' and 'input' boolean columns to the parameters table
"""

import sqlite3
import os
from datetime import datetime

def update_parameters_schema(db_path="functions.db"):
    """Add variable and input columns to parameters table"""
    
    print("🔧 UPDATING PARAMETERS TABLE SCHEMA")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Backup database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.rename(db_path, backup_path)
    print(f"💾 Backed up database to: {backup_path}")
    
    # Connect to backup to read data
    backup_conn = sqlite3.connect(backup_path)
    backup_cursor = backup_conn.cursor()
    
    # Connect to new database
    new_conn = sqlite3.connect(db_path)
    new_cursor = new_conn.cursor()
    
    try:
        print("🏗️  Creating updated database schema...")
        
        # Recreate all tables with updated parameters table
        create_updated_schema(new_cursor)
        
        # Copy functions table
        print("📋 Copying functions...")
        backup_cursor.execute("SELECT * FROM functions")
        functions_data = backup_cursor.fetchall()
        
        for row in functions_data:
            new_cursor.execute("""
                INSERT INTO functions (function_id, function_name, function_description, category, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, row)
        
        print(f"   ✅ Copied {len(functions_data)} functions")
        
        # Copy function_methods table
        print("🔧 Copying methods...")
        backup_cursor.execute("SELECT * FROM function_methods")
        methods_data = backup_cursor.fetchall()
        
        for row in methods_data:
            new_cursor.execute("""
                INSERT INTO function_methods (
                    id, function_ref, method_name, step_order, object_chain,
                    method_call, method_parameters, object_type, return_type, 
                    method_description, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        
        print(f"   ✅ Copied {len(methods_data)} methods")
        
        # Copy parameters table with new columns (default values)
        print("📝 Copying parameters with new columns...")
        backup_cursor.execute("SELECT * FROM parameters")
        params_data = backup_cursor.fetchall()
        
        for row in params_data:
            # Analyze parameter to determine if it's variable or input
            param_name = row[2] if len(row) > 2 else ""
            param_value = row[4] if len(row) > 4 else ""
            
            # Simple heuristic to classify parameters
            is_variable = classify_as_variable(param_name, param_value)
            is_input = not is_variable  # If not variable, then it's input
            
            new_cursor.execute("""
                INSERT INTO parameters (
                    id, method_ref, parameter_name, parameter_type, parameter_value,
                    parameter_position, parameter_description, variable, input
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row[0],  # id
                row[1],  # method_ref
                row[2],  # parameter_name
                row[3] if len(row) > 3 else "",  # parameter_type
                row[4] if len(row) > 4 else "",  # parameter_value
                row[5] if len(row) > 5 else 1,   # parameter_position
                row[6] if len(row) > 6 else "",  # parameter_description
                1 if is_variable else 0,         # variable
                1 if is_input else 0             # input
            ))
        
        print(f"   ✅ Copied {len(params_data)} parameters with variable/input classification")
        
        # Commit changes
        new_conn.commit()
        
        # Verify update
        new_cursor.execute("SELECT COUNT(*) FROM parameters WHERE variable = 1")
        variable_count = new_cursor.fetchone()[0]
        
        new_cursor.execute("SELECT COUNT(*) FROM parameters WHERE input = 1")
        input_count = new_cursor.fetchone()[0]
        
        print(f"\n✅ Schema update completed successfully!")
        print(f"📊 Parameter classification:")
        print(f"   🔧 Variables: {variable_count}")
        print(f"   📥 Inputs: {input_count}")
        print(f"   📝 Total: {len(params_data)}")
        
        backup_conn.close()
        new_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
        new_conn.rollback()
        new_conn.close()
        backup_conn.close()
        
        # Restore backup
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rename(backup_path, db_path)
        print(f"🔄 Restored database from backup")
        
        return False

def classify_as_variable(param_name, param_value):
    """Classify parameter as variable or input based on name and value patterns"""
    
    param_name = param_name.lower() if param_name else ""
    param_value = str(param_value).lower() if param_value else ""
    
    # Common variable indicators
    variable_indicators = [
        'point', 'spline', 'line', 'surface', 'extrude', 'loft',
        'plane', 'direction', 'reference', 'hybrid_shape',
        'body', 'part', 'document', 'application'
    ]
    
    # Common input indicators  
    input_indicators = [
        'name', 'value', 'length', 'angle', 'offset', 'distance',
        'coordinate', 'radius', 'thickness', 'count', 'index'
    ]
    
    # Check if parameter name suggests it's a variable
    for indicator in variable_indicators:
        if indicator in param_name:
            return True
    
    # Check if parameter name suggests it's an input
    for indicator in input_indicators:
        if indicator in param_name:
            return False
    
    # Check parameter value patterns
    if param_value:
        # String literals in quotes are often inputs
        if param_value.startswith("'") and param_value.endswith("'"):
            return False
        # Numeric values are often inputs
        if param_value.replace('.', '').replace('-', '').isdigit():
            return False
    
    # Default to variable if uncertain
    return True

def create_updated_schema(cursor):
    """Create database schema with updated parameters table"""
    
    # Create functions table
    cursor.execute("""
        CREATE TABLE functions (
            function_id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_name TEXT NOT NULL UNIQUE,
            function_description TEXT,
            category TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create function_methods table
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
    
    # Create parameters table with new columns
    cursor.execute("""
        CREATE TABLE parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_ref INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_type TEXT,
            parameter_value TEXT,
            parameter_position INTEGER DEFAULT 1,
            parameter_description TEXT,
            variable INTEGER DEFAULT 0,
            input INTEGER DEFAULT 0,
            FOREIGN KEY (method_ref) REFERENCES function_methods(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_function_methods_function_ref ON function_methods(function_ref)")
    cursor.execute("CREATE INDEX idx_function_methods_step_order ON function_methods(step_order)")
    cursor.execute("CREATE INDEX idx_parameters_method_ref ON parameters(method_ref)")
    cursor.execute("CREATE INDEX idx_parameters_variable ON parameters(variable)")
    cursor.execute("CREATE INDEX idx_parameters_input ON parameters(input)")
    cursor.execute("CREATE INDEX idx_functions_category ON functions(category)")

def show_parameter_classification_examples(db_path="functions.db"):
    """Show examples of parameter classification"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n📋 PARAMETER CLASSIFICATION EXAMPLES")
    print("=" * 50)
    
    # Show variable examples
    print("🔧 VARIABLES (variable=1, input=0):")
    cursor.execute("""
        SELECT p.parameter_name, p.parameter_value, fm.method_name, f.function_name
        FROM parameters p
        JOIN function_methods fm ON p.method_ref = fm.id
        JOIN functions f ON fm.function_ref = f.function_id
        WHERE p.variable = 1
        LIMIT 10
    """)
    
    for param_name, param_value, method_name, func_name in cursor.fetchall():
        print(f"   • {param_name} = {param_value} (in {method_name})")
    
    # Show input examples
    print(f"\n📥 INPUTS (variable=0, input=1):")
    cursor.execute("""
        SELECT p.parameter_name, p.parameter_value, fm.method_name, f.function_name
        FROM parameters p
        JOIN function_methods fm ON p.method_ref = fm.id
        JOIN functions f ON fm.function_ref = f.function_id
        WHERE p.input = 1
        LIMIT 10
    """)
    
    for param_name, param_value, method_name, func_name in cursor.fetchall():
        print(f"   • {param_name} = {param_value} (in {method_name})")
    
    conn.close()

def main():
    """Main schema update function"""
    
    print("🚀 PARAMETERS TABLE SCHEMA UPDATE")
    print("=" * 60)
    
    success = update_parameters_schema()
    
    if success:
        show_parameter_classification_examples()
        print(f"\n🎉 SCHEMA UPDATE COMPLETE!")
        print(f"✅ Added 'variable' and 'input' columns to parameters table")
        print(f"✅ Automatically classified existing parameters")
        print(f"✅ Ready to export updated database to Excel/CSV")
    else:
        print(f"\n❌ Schema update failed")

if __name__ == "__main__":
    main()