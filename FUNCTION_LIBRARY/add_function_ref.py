"""
Update Parameters Table Schema - Add function_ref Column
Adds function_ref column to parameters table for direct function reference
"""

import sqlite3
import os
from datetime import datetime

def update_parameters_with_function_ref(db_path="functions.db"):
    """Add function_ref column to parameters table"""
    
    print("🔧 UPDATING PARAMETERS TABLE - ADDING function_ref")
    print("=" * 60)
    
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
        
        if 'function_ref' in current_columns:
            print("✅ function_ref column already exists!")
            return True
        
        print("🏗️  Restructuring parameters table...")
        
        # Step 1: Create new parameters table with function_ref
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
                variable INTEGER DEFAULT 0,
                input INTEGER DEFAULT 0,
                FOREIGN KEY (function_ref) REFERENCES functions(function_id) ON DELETE CASCADE,
                FOREIGN KEY (method_ref) REFERENCES function_methods(id) ON DELETE CASCADE
            )
        """)
        
        print("✅ Created new parameters table structure")
        
        # Step 2: Migrate data with function_ref populated
        print("📝 Migrating parameter data with function references...")
        
        cursor.execute("""
            INSERT INTO parameters_new (
                id, function_ref, method_ref, parameter_name, parameter_type, 
                parameter_value, parameter_position, parameter_description, variable, input
            )
            SELECT 
                p.id,
                fm.function_ref as function_ref,
                p.method_ref,
                p.parameter_name,
                p.parameter_type,
                p.parameter_value,
                p.parameter_position,
                p.parameter_description,
                p.variable,
                p.input
            FROM parameters p
            JOIN function_methods fm ON p.method_ref = fm.id
        """)
        
        migrated_count = cursor.rowcount
        print(f"✅ Migrated {migrated_count} parameters with function references")
        
        # Step 3: Drop old table and rename new one
        cursor.execute("DROP TABLE parameters")
        cursor.execute("ALTER TABLE parameters_new RENAME TO parameters")
        
        print("✅ Replaced old parameters table")
        
        # Step 4: Recreate indexes
        print("🔍 Creating indexes...")
        cursor.execute("CREATE INDEX idx_parameters_function_ref ON parameters(function_ref)")
        cursor.execute("CREATE INDEX idx_parameters_method_ref ON parameters(method_ref)")
        cursor.execute("CREATE INDEX idx_parameters_variable ON parameters(variable)")
        cursor.execute("CREATE INDEX idx_parameters_input ON parameters(input)")
        
        print("✅ Created indexes")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute("PRAGMA table_info(parameters)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM parameters")
        param_count = cursor.fetchone()[0]
        
        print(f"\n✅ Schema update completed successfully!")
        print(f"📊 New parameters table structure:")
        for col in new_columns:
            print(f"   • {col}")
        
        print(f"📊 Verified {param_count} parameters with dual references")
        
        # Show some examples
        print(f"\n📋 EXAMPLE PARAMETER REFERENCES:")
        cursor.execute("""
            SELECT 
                p.parameter_name,
                f.function_name,
                fm.method_name,
                p.variable,
                p.input
            FROM parameters p
            JOIN functions f ON p.function_ref = f.function_id
            JOIN function_methods fm ON p.method_ref = fm.id
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        for param_name, func_name, method_name, variable, input_flag in examples:
            var_type = "Variable" if variable else "Input" if input_flag else "Unknown"
            print(f"   • {param_name} ({var_type}) in {func_name}.{method_name}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
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

def verify_dual_references(db_path="functions.db"):
    """Verify that parameters now have both function_ref and method_ref"""
    
    print(f"\n🔍 VERIFYING DUAL REFERENCES")
    print("=" * 40)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check schema
        cursor.execute("PRAGMA table_info(parameters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_function_ref = 'function_ref' in columns
        has_method_ref = 'method_ref' in columns
        
        print(f"✅ Has function_ref: {has_function_ref}")
        print(f"✅ Has method_ref: {has_method_ref}")
        
        if has_function_ref and has_method_ref:
            # Check data integrity
            cursor.execute("""
                SELECT COUNT(*) FROM parameters p
                JOIN functions f ON p.function_ref = f.function_id
                JOIN function_methods fm ON p.method_ref = fm.id
                WHERE fm.function_ref = p.function_ref
            """)
            
            consistent_refs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM parameters")
            total_params = cursor.fetchone()[0]
            
            print(f"📊 Total parameters: {total_params}")
            print(f"📊 Consistent references: {consistent_refs}")
            
            if consistent_refs == total_params:
                print("✅ All parameter references are consistent!")
            else:
                print(f"⚠️  {total_params - consistent_refs} parameters have inconsistent references")
            
            # Show reference statistics
            cursor.execute("""
                SELECT 
                    f.function_name,
                    COUNT(p.id) as param_count
                FROM functions f
                LEFT JOIN parameters p ON f.function_id = p.function_ref
                GROUP BY f.function_id, f.function_name
                ORDER BY param_count DESC
                LIMIT 10
            """)
            
            print(f"\n📊 PARAMETERS BY FUNCTION:")
            for func_name, param_count in cursor.fetchall():
                print(f"   • {func_name}: {param_count} parameters")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        conn.close()

def update_import_export_scripts():
    """Update the import/export scripts to handle function_ref"""
    
    print(f"\n🔧 UPDATING IMPORT/EXPORT SCRIPTS")
    print("=" * 40)
    
    print("ℹ️  You'll need to update:")
    print("   • export_functions_db.py - include function_ref in parameters export")
    print("   • import_functions_db.py - handle function_ref during import")
    print("   • Any other scripts that work with parameters table")
    
    print("\n💡 Benefits of dual references:")
    print("   • Direct queries: SELECT * FROM parameters WHERE function_ref = ?")
    print("   • Better joins: JOIN parameters ON function_id = function_ref")
    print("   • Data integrity: Both function and method references enforced")
    print("   • Performance: Index on function_ref for faster function-level queries")

def main():
    """Main schema update function"""
    
    print("🚀 PARAMETERS TABLE DUAL REFERENCE UPDATE")
    print("=" * 60)
    
    success = update_parameters_with_function_ref()
    
    if success:
        verify_dual_references()
        update_import_export_scripts()
        
        print(f"\n🎉 DUAL REFERENCE UPDATE COMPLETE!")
        print(f"✅ Parameters table now has both function_ref and method_ref")
        print(f"✅ Improved data integrity and query performance")
        print(f"✅ Ready for updated export/import operations")
    else:
        print(f"\n❌ Dual reference update failed")

if __name__ == "__main__":
    main()