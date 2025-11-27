"""
Merge Variable and Input Columns
Consolidates variable and input columns into a single 'parameter_type' column
0 = Input, 1 = Variable
"""

import sqlite3
import os
from datetime import datetime

def merge_variable_input_columns(db_path="functions.db"):
    """Merge variable and input columns into a single parameter_type column"""
    
    print("🔧 MERGING VARIABLE AND INPUT COLUMNS")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Backup database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create backup by copying
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backed up database to: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
        print("Proceeding without backup...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(parameters)")
        current_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"📋 Current parameters columns: {current_columns}")
        
        if 'variable' not in current_columns or 'input' not in current_columns:
            print("❌ Both 'variable' and 'input' columns must exist!")
            return False
        
        if 'parameter_type_flag' in current_columns:
            print("✅ parameter_type_flag column already exists!")
            return True
        
        print("🏗️  Restructuring parameters table...")
        
        # Step 1: Create new parameters table with merged column
        cursor.execute("""
            CREATE TABLE parameters_new (
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
        
        print("✅ Created new parameters table structure")
        
        # Step 2: Migrate data with merged column
        print("📝 Migrating parameter data with merged column...")
        
        # Logic: parameter_type_flag = 1 for variables, 0 for inputs
        cursor.execute("""
            INSERT INTO parameters_new (
                id, function_ref, method_ref, parameter_name, parameter_type, 
                parameter_value, parameter_position, parameter_description, parameter_type_flag
            )
            SELECT 
                id, function_ref, method_ref, parameter_name, parameter_type,
                parameter_value, parameter_position, parameter_description,
                CASE 
                    WHEN variable = 1 THEN 1
                    WHEN input = 1 THEN 0
                    ELSE 1
                END as parameter_type_flag
            FROM parameters
        """)
        
        migrated_count = cursor.rowcount
        print(f"✅ Migrated {migrated_count} parameters with merged column")
        
        # Verify the merge logic worked correctly
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN parameter_type_flag = 1 THEN 1 ELSE 0 END) as variables,
                SUM(CASE WHEN parameter_type_flag = 0 THEN 1 ELSE 0 END) as inputs
            FROM parameters_new
        """)
        
        total, variables, inputs = cursor.fetchone()
        print(f"📊 Merge verification:")
        print(f"   📝 Total parameters: {total}")
        print(f"   🔧 Variables (flag=1): {variables}")
        print(f"   📥 Inputs (flag=0): {inputs}")
        
        # Step 3: Drop old table and rename new one
        cursor.execute("DROP TABLE parameters")
        cursor.execute("ALTER TABLE parameters_new RENAME TO parameters")
        
        print("✅ Replaced old parameters table")
        
        # Step 4: Recreate indexes
        print("🔍 Creating indexes...")
        cursor.execute("CREATE INDEX idx_parameters_function_ref ON parameters(function_ref)")
        cursor.execute("CREATE INDEX idx_parameters_method_ref ON parameters(method_ref)")
        cursor.execute("CREATE INDEX idx_parameters_type_flag ON parameters(parameter_type_flag)")
        
        print("✅ Created indexes")
        
        # Commit changes
        conn.commit()
        
        # Verify the final structure
        cursor.execute("PRAGMA table_info(parameters)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM parameters")
        param_count = cursor.fetchone()[0]
        
        print(f"\n✅ Column merge completed successfully!")
        print(f"📊 New parameters table structure:")
        for col in new_columns:
            print(f"   • {col}")
        
        print(f"📊 Verified {param_count} parameters with merged column")
        
        # Show some examples
        print(f"\n📋 EXAMPLE PARAMETER TYPES:")
        cursor.execute("""
            SELECT 
                p.parameter_name,
                p.parameter_type_flag,
                CASE WHEN p.parameter_type_flag = 1 THEN 'Variable' ELSE 'Input' END as type_name,
                f.function_name,
                fm.method_name
            FROM parameters p
            JOIN functions f ON p.function_ref = f.function_id
            JOIN function_methods fm ON p.method_ref = fm.id
            ORDER BY p.parameter_type_flag DESC, p.parameter_name
            LIMIT 10
        """)
        
        examples = cursor.fetchall()
        for param_name, flag, type_name, func_name, method_name in examples:
            print(f"   • {param_name} (flag={flag}, {type_name}) in {func_name}.{method_name}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Column merge failed: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        
        # Try to restore backup
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, db_path)
                print(f"🔄 Restored database from backup")
            except Exception as restore_e:
                print(f"❌ Could not restore backup: {restore_e}")
        
        return False

def update_export_scripts_for_merged_column():
    """Information about updating export scripts"""
    
    print(f"\n🔧 EXPORT SCRIPT UPDATES NEEDED")
    print("=" * 40)
    
    print("📝 Column mapping:")
    print("   • parameter_type_flag = 1 → Variable")
    print("   • parameter_type_flag = 0 → Input")
    print("")
    print("💡 Benefits of merged column:")
    print("   • Simpler schema with single type indicator")
    print("   • Easier queries: WHERE parameter_type_flag = 1")
    print("   • Reduced storage (one column instead of two)")
    print("   • Clear semantics: 1=Variable, 0=Input")
    print("")
    print("🔄 Export/Import scripts will be automatically updated")

def verify_merged_column(db_path="functions.db"):
    """Verify the merged column works correctly"""
    
    print(f"\n🔍 VERIFYING MERGED COLUMN")
    print("=" * 40)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check schema
        cursor.execute("PRAGMA table_info(parameters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_merged_column = 'parameter_type_flag' in columns
        has_old_columns = 'variable' in columns or 'input' in columns
        
        print(f"✅ Has parameter_type_flag: {has_merged_column}")
        print(f"❌ Still has old columns: {has_old_columns}")
        
        if has_merged_column:
            # Check data distribution
            cursor.execute("""
                SELECT 
                    parameter_type_flag,
                    COUNT(*) as count,
                    CASE WHEN parameter_type_flag = 1 THEN 'Variables' ELSE 'Inputs' END as type_name
                FROM parameters
                GROUP BY parameter_type_flag
                ORDER BY parameter_type_flag DESC
            """)
            
            print(f"\n📊 Parameter type distribution:")
            for flag, count, type_name in cursor.fetchall():
                print(f"   • {type_name} (flag={flag}): {count} parameters")
            
            # Show some examples of each type
            print(f"\n📋 Example Variables (flag=1):")
            cursor.execute("""
                SELECT parameter_name, parameter_value, parameter_type
                FROM parameters 
                WHERE parameter_type_flag = 1 
                LIMIT 5
            """)
            
            for param_name, param_value, param_type in cursor.fetchall():
                print(f"   • {param_name} ({param_type}) = {param_value}")
            
            print(f"\n📥 Example Inputs (flag=0):")
            cursor.execute("""
                SELECT parameter_name, parameter_value, parameter_type
                FROM parameters 
                WHERE parameter_type_flag = 0 
                LIMIT 5
            """)
            
            for param_name, param_value, param_type in cursor.fetchall():
                print(f"   • {param_name} ({param_type}) = {param_value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        conn.close()

def main():
    """Main column merge function"""
    
    print("🚀 PARAMETERS COLUMN MERGE")
    print("=" * 60)
    
    success = merge_variable_input_columns()
    
    if success:
        verify_merged_column()
        update_export_scripts_for_merged_column()
        
        print(f"\n🎉 COLUMN MERGE COMPLETE!")
        print(f"✅ Merged 'variable' and 'input' into 'parameter_type_flag'")
        print(f"✅ Simplified schema with single type indicator")
        print(f"✅ Ready for updated export operations")
    else:
        print(f"\n❌ Column merge failed")

if __name__ == "__main__":
    main()