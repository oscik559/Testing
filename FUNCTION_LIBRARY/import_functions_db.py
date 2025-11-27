"""
Import Functions Database from Excel/CSV
Imports improved function data from Excel or CSV files back into functions.db
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def import_from_csv(csv_dir="exports", db_path="functions.db"):
    """Import data from CSV files back into database"""
    
    print(f"📥 IMPORTING FUNCTIONS DATABASE FROM CSV")
    print("=" * 60)
    
    # Find the most recent CSV files
    if not os.path.exists(csv_dir):
        print(f"❌ Export directory not found: {csv_dir}")
        return False
    
    # Get list of CSV files
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        return False
    
    # Find the most recent timestamp
    timestamps = []
    for file in csv_files:
        if file.startswith('functions_') and file.endswith('.csv'):
            try:
                # Extract timestamp from filename like "functions_20251009_235438.csv"
                timestamp_part = file.replace('functions_', '').replace('.csv', '')
                if len(timestamp_part) == 15 and '_' in timestamp_part:  # YYYYMMDD_HHMMSS
                    timestamps.append(timestamp_part)
            except:
                continue
    
    if not timestamps:
        print(f"❌ No timestamped CSV files found")
        return False
    
    latest_timestamp = max(timestamps)
    
    # Expected file names
    functions_file = os.path.join(csv_dir, f"functions_{latest_timestamp}.csv")
    methods_file = os.path.join(csv_dir, f"function_methods_{latest_timestamp}.csv")
    params_file = os.path.join(csv_dir, f"parameters_{latest_timestamp}.csv")
    
    # Check if files exist
    missing_files = []
    if not os.path.exists(functions_file):
        missing_files.append(functions_file)
    if not os.path.exists(methods_file):
        missing_files.append(methods_file)
    if not os.path.exists(params_file):
        missing_files.append(params_file)
    
    if missing_files:
        print(f"❌ Missing CSV files:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print(f"📁 Using CSV files with timestamp: {latest_timestamp}")
    
    # Backup existing database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(db_path):
        os.rename(db_path, backup_path)
        print(f"💾 Backed up existing database to: {backup_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Recreate schema
    print("🏗️  Recreating database schema...")
    create_schema(cursor)
    
    try:
        # Import functions
        print("📋 Importing functions...")
        functions_df = pd.read_csv(functions_file)
        
        # Clean and validate functions data
        functions_df = functions_df.dropna(subset=['function_name'])
        
        for _, row in functions_df.iterrows():
            cursor.execute("""
                INSERT INTO functions (function_name, function_description, category, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                row['function_name'],
                row.get('function_description', ''),
                row.get('category', 'Other'),
                row.get('timestamp', datetime.now().isoformat())
            ))
        
        print(f"   ✅ Imported {len(functions_df)} functions")
        
        # Import methods
        print("🔧 Importing methods...")
        methods_df = pd.read_csv(methods_file)
        
        # Clean and validate methods data
        methods_df = methods_df.dropna(subset=['method_name', 'function_name'])
        
        for _, row in methods_df.iterrows():
            # Get function_id from function_name
            cursor.execute("SELECT function_id FROM functions WHERE function_name = ?", 
                          (row['function_name'],))
            result = cursor.fetchone()
            if result:
                function_id = result[0]
                
                cursor.execute("""
                    INSERT INTO function_methods (
                        function_ref, method_name, step_order, object_chain,
                        method_call, method_parameters, object_type, return_type, 
                        method_description, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    function_id,
                    row['method_name'],
                    row.get('step_order', 1),
                    row.get('object_chain', ''),
                    row.get('method_call', ''),
                    row.get('method_parameters', ''),
                    row.get('object_type', ''),
                    row.get('return_type', ''),
                    row.get('method_description', ''),
                    row.get('timestamp', datetime.now().isoformat())
                ))
        
        print(f"   ✅ Imported {len(methods_df)} methods")
        
        # Import parameters
        print("📝 Importing parameters...")
        params_df = pd.read_csv(params_file)
        
        if not params_df.empty:
            # Clean and validate parameters data
            params_df = params_df.dropna(subset=['parameter_name', 'method_name', 'function_name'])
            
            for _, row in params_df.iterrows():
                # Get function_id and method_id from function_name and method_name
                cursor.execute("""
                    SELECT f.function_id, fm.id 
                    FROM function_methods fm
                    JOIN functions f ON fm.function_ref = f.function_id
                    WHERE fm.method_name = ? AND f.function_name = ?
                """, (row['method_name'], row['function_name']))
                
                result = cursor.fetchone()
                if result:
                    function_id, method_id = result
                    
                    # Handle both old (variable/input) and new (parameter_type_flag) column formats
                    if 'parameter_type_flag' in row:
                        # New merged column format
                        cursor.execute("""
                            INSERT INTO parameters (
                                function_ref, method_ref, parameter_name, parameter_type, parameter_value,
                                parameter_position, parameter_description, parameter_type_flag
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            function_id,
                            method_id,
                            row['parameter_name'],
                            row.get('parameter_type', ''),
                            row.get('parameter_value', ''),
                            row.get('parameter_position', 1),
                            row.get('parameter_description', ''),
                            row.get('parameter_type_flag', 1)
                        ))
                    else:
                        # Legacy variable/input columns format
                        parameter_type_flag = 1 if row.get('variable', 0) == 1 else 0
                        cursor.execute("""
                            INSERT INTO parameters (
                                function_ref, method_ref, parameter_name, parameter_type, parameter_value,
                                parameter_position, parameter_description, parameter_type_flag
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            function_id,
                            method_id,
                            row['parameter_name'],
                            row.get('parameter_type', ''),
                            row.get('parameter_value', ''),
                            row.get('parameter_position', 1),
                            row.get('parameter_description', ''),
                            parameter_type_flag
                        ))
            
            print(f"   ✅ Imported {len(params_df)} parameters")
        else:
            print("   ℹ️  No parameters to import")
        
        # Commit changes
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM functions")
        func_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM function_methods")
        method_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM parameters")
        param_count = cursor.fetchone()[0]
        
        print(f"\n✅ Import completed successfully!")
        print(f"📊 Final counts:")
        print(f"   📋 Functions: {func_count}")
        print(f"   🔧 Methods: {method_count}")
        print(f"   📝 Parameters: {param_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        conn.rollback()
        conn.close()
        
        # Restore backup
        if os.path.exists(backup_path):
            os.rename(backup_path, db_path)
            print(f"🔄 Restored database from backup")
        
        return False

def create_schema(cursor):
    """Recreate database schema"""
    
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
    
    # Create parameters table
    cursor.execute("""
        CREATE TABLE parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_ref INTEGER NOT NULL,
            parameter_name TEXT NOT NULL,
            parameter_type TEXT,
            parameter_value TEXT,
            parameter_position INTEGER DEFAULT 1,
            parameter_description TEXT,
            parameter_type_flag INTEGER DEFAULT 1,
            FOREIGN KEY (method_ref) REFERENCES function_methods(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_function_methods_function_ref ON function_methods(function_ref)")
    cursor.execute("CREATE INDEX idx_function_methods_step_order ON function_methods(step_order)")
    cursor.execute("CREATE INDEX idx_parameters_method_ref ON parameters(method_ref)")
    cursor.execute("CREATE INDEX idx_parameters_type_flag ON parameters(parameter_type_flag)")
    cursor.execute("CREATE INDEX idx_functions_category ON functions(category)")

def show_import_instructions():
    """Show instructions for editing CSV files"""
    
    print(f"📝 EDITING INSTRUCTIONS")
    print("=" * 40)
    print(f"")
    print(f"Your database has been exported to CSV files in the 'exports' directory.")
    print(f"You can now edit these files to improve your function library:")
    print(f"")
    print(f"📋 functions_YYYYMMDD_HHMMSS.csv:")
    print(f"   • Edit function names, descriptions, and categories")
    print(f"   • Add new functions by adding rows")
    print(f"   • Delete unwanted functions by removing rows")
    print(f"")
    print(f"🔧 function_methods_YYYYMMDD_HHMMSS.csv:")
    print(f"   • Edit method calls and parameters")
    print(f"   • Modify step order")
    print(f"   • Update object chains and return types")
    print(f"")
    print(f"📝 parameters_YYYYMMDD_HHMMSS.csv:")
    print(f"   • Edit parameter names, types, and values")
    print(f"   • Add parameter descriptions")
    print(f"")
    print(f"⚠️  IMPORTANT:")
    print(f"   • Don't change the 'function_name' column in methods - it's used for linking")
    print(f"   • Don't change the 'method_name' and 'function_name' in parameters")
    print(f"   • Keep the CSV structure intact")
    print(f"")
    print(f"After editing, run this script again to import your changes back to the database.")

def main():
    """Main import function"""
    
    print("🚀 FUNCTION DATABASE IMPORT TOOL")
    print("=" * 60)
    
    # Check if there are CSV files to import
    csv_dir = "exports"
    if not os.path.exists(csv_dir):
        print(f"❌ No exports directory found")
        show_import_instructions()
        return
    
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        show_import_instructions()
        return
    
    print(f"📁 Found CSV files in {csv_dir}:")
    for file in sorted(csv_files):
        print(f"   • {file}")
    
    # Import from most recent CSV files
    success = import_from_csv(csv_dir)
    
    if success:
        print(f"\n🎉 DATABASE IMPORT COMPLETE!")
        print(f"✅ Your improved function library is now ready to use")
    else:
        print(f"\n❌ Import failed. Please check the CSV files and try again.")
        show_import_instructions()

if __name__ == "__main__":
    main()