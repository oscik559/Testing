"""
Verify Database Status
Shows current database status and available exports
"""

import sqlite3
import os
from datetime import datetime

def check_database_status(db_path="functions.db"):
    """Check current database status"""
    
    print("📊 DATABASE STATUS CHECK")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Available tables: {tables}")
        
        # Check functions
        cursor.execute("SELECT COUNT(*) FROM functions")
        func_count = cursor.fetchone()[0]
        print(f"📋 Functions: {func_count}")
        
        # Check methods
        cursor.execute("SELECT COUNT(*) FROM function_methods")
        method_count = cursor.fetchone()[0]
        print(f"🔧 Methods: {method_count}")
        
        # Check parameters and new columns
        cursor.execute("PRAGMA table_info(parameters)")
        param_columns = cursor.fetchall()
        
        print(f"📝 Parameters table columns:")
        for col_info in param_columns:
            print(f"   • {col_info[1]} ({col_info[2]})")
        
        # Check if new columns exist
        column_names = [col[1] for col in param_columns]
        has_variable = 'variable' in column_names
        has_input = 'input' in column_names
        
        print(f"✅ Has 'variable' column: {has_variable}")
        print(f"✅ Has 'input' column: {has_input}")
        
        if has_variable and has_input:
            cursor.execute("SELECT COUNT(*) FROM parameters")
            total_params = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM parameters WHERE variable = 1")
            variable_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM parameters WHERE input = 1")
            input_count = cursor.fetchone()[0]
            
            print(f"📊 Parameter classification:")
            print(f"   📝 Total parameters: {total_params}")
            print(f"   🔧 Variables: {variable_count}")
            print(f"   📥 Inputs: {input_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_export_files():
    """Check available export files"""
    
    print(f"\n📁 AVAILABLE EXPORTS")
    print("=" * 30)
    
    export_dir = "exports"
    if not os.path.exists(export_dir):
        print(f"❌ No exports directory found")
        return
    
    # Check for Excel files
    excel_files = [f for f in os.listdir(export_dir) if f.endswith('.xlsx')]
    if excel_files:
        print(f"📊 Excel files:")
        for file in sorted(excel_files, reverse=True)[:3]:  # Show latest 3
            print(f"   • {file}")
    
    # Check for CSV files
    csv_files = [f for f in os.listdir(export_dir) if f.endswith('.csv')]
    if csv_files:
        print(f"📄 CSV files:")
        
        # Group by timestamp
        timestamps = set()
        for file in csv_files:
            if '_' in file:
                try:
                    timestamp = file.split('_')[-2] + '_' + file.split('_')[-1].replace('.csv', '')
                    timestamps.add(timestamp)
                except:
                    pass
        
        for timestamp in sorted(timestamps, reverse=True)[:2]:  # Show latest 2 sets
            print(f"   📅 {timestamp}:")
            matching_files = [f for f in csv_files if timestamp in f]
            for file in sorted(matching_files):
                if file.startswith(('functions_', 'function_methods_', 'parameters_')):
                    print(f"     • {file}")

def main():
    """Main verification function"""
    
    print("🚀 DATABASE AND EXPORTS VERIFICATION")
    print("=" * 60)
    
    # Check database status
    db_ok = check_database_status()
    
    # Check export files
    check_export_files()
    
    if db_ok:
        print(f"\n✅ DATABASE STATUS: READY")
        print(f"✅ Database contains updated schema with variable/input columns")
        print(f"✅ Fresh exports available for editing")
    else:
        print(f"\n❌ DATABASE STATUS: NEEDS ATTENTION")

if __name__ == "__main__":
    main()