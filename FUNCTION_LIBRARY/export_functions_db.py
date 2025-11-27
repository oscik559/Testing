"""
Export Functions Database to Excel/CSV
Exports all tables from functions.db to Excel worksheets or CSV files
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_to_excel(db_path="functions.db", output_dir="exports"):
    """Export database tables to Excel file with multiple worksheets"""
    
    # Create exports directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = os.path.join(output_dir, f"functions_db_export_{timestamp}.xlsx")
    
    print(f"📊 EXPORTING FUNCTIONS DATABASE TO EXCEL")
    print("=" * 60)
    
    try:
        # Create Excel writer object
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            
            # Export functions table
            print("📋 Exporting functions table...")
            functions_df = pd.read_sql_query("SELECT * FROM functions ORDER BY function_id", conn)
            functions_df.to_excel(writer, sheet_name='Functions', index=False)
            print(f"   ✅ {len(functions_df)} functions exported")
            
            # Export function_methods table
            print("🔧 Exporting function_methods table...")
            methods_df = pd.read_sql_query("""
                SELECT fm.*, f.function_name 
                FROM function_methods fm
                JOIN functions f ON fm.function_ref = f.function_id
                ORDER BY fm.function_ref, fm.step_order
            """, conn)
            methods_df.to_excel(writer, sheet_name='Function_Methods', index=False)
            print(f"   ✅ {len(methods_df)} methods exported")
            
            # Export parameters table
            print("📝 Exporting parameters table...")
            params_df = pd.read_sql_query("""
                SELECT p.*, fm.method_name, f.function_name
                FROM parameters p
                JOIN function_methods fm ON p.method_ref = fm.id
                JOIN functions f ON p.function_ref = f.function_id
                ORDER BY p.function_ref, fm.step_order, p.parameter_position
            """, conn)
            params_df.to_excel(writer, sheet_name='Parameters', index=False)
            print(f"   ✅ {len(params_df)} parameters exported")
            
            # Create summary sheet
            print("📊 Creating summary sheet...")
            summary_data = {
                'Metric': [
                    'Total Functions',
                    'Total Methods', 
                    'Total Parameters',
                    'Functions by Category',
                    'Average Methods per Function',
                    'Export Date',
                    'Database File'
                ],
                'Value': [
                    len(functions_df),
                    len(methods_df),
                    len(params_df),
                    f"See Functions sheet",
                    f"{len(methods_df)/len(functions_df):.1f}" if len(functions_df) > 0 else "0",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    db_path
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Functions by category
            category_summary = functions_df.groupby('category').size().reset_index(name='count')
            category_summary.to_excel(writer, sheet_name='Categories', index=False)
            print(f"   ✅ Summary sheets created")
        
        print(f"\n✅ Excel export completed successfully!")
        print(f"📁 File saved: {excel_filename}")
        
    except ImportError:
        print("⚠️  openpyxl not available, falling back to CSV export...")
        export_to_csv(db_path, output_dir)
    except Exception as e:
        print(f"❌ Excel export failed: {e}")
        print("⚠️  Falling back to CSV export...")
        export_to_csv(db_path, output_dir)
    
    conn.close()
    return excel_filename

def export_to_csv(db_path="functions.db", output_dir="exports"):
    """Export database tables to separate CSV files"""
    
    # Create exports directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"📊 EXPORTING FUNCTIONS DATABASE TO CSV")
    print("=" * 60)
    
    exported_files = []
    
    try:
        # Export functions table
        print("📋 Exporting functions table...")
        functions_df = pd.read_sql_query("SELECT * FROM functions ORDER BY function_id", conn)
        functions_file = os.path.join(output_dir, f"functions_{timestamp}.csv")
        functions_df.to_csv(functions_file, index=False)
        exported_files.append(functions_file)
        print(f"   ✅ {len(functions_df)} functions exported to {functions_file}")
        
        # Export function_methods table
        print("🔧 Exporting function_methods table...")
        methods_df = pd.read_sql_query("""
            SELECT fm.*, f.function_name 
            FROM function_methods fm
            JOIN functions f ON fm.function_ref = f.function_id
            ORDER BY fm.function_ref, fm.step_order
        """, conn)
        methods_file = os.path.join(output_dir, f"function_methods_{timestamp}.csv")
        methods_df.to_csv(methods_file, index=False)
        exported_files.append(methods_file)
        print(f"   ✅ {len(methods_df)} methods exported to {methods_file}")
        
        # Export parameters table
        print("📝 Exporting parameters table...")
        params_df = pd.read_sql_query("""
            SELECT p.*, fm.method_name, f.function_name
            FROM parameters p
            JOIN function_methods fm ON p.method_ref = fm.id
            JOIN functions f ON p.function_ref = f.function_id
            ORDER BY p.function_ref, fm.step_order, p.parameter_position
        """, conn)
        params_file = os.path.join(output_dir, f"parameters_{timestamp}.csv")
        params_df.to_csv(params_file, index=False)
        exported_files.append(params_file)
        print(f"   ✅ {len(params_df)} parameters exported to {params_file}")
        
        # Create summary CSV
        print("📊 Creating summary file...")
        summary_data = {
            'Metric': [
                'Total Functions',
                'Total Methods', 
                'Total Parameters',
                'Average Methods per Function',
                'Export Date',
                'Database File'
            ],
            'Value': [
                len(functions_df),
                len(methods_df),
                len(params_df),
                f"{len(methods_df)/len(functions_df):.1f}" if len(functions_df) > 0 else "0",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                db_path
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(output_dir, f"summary_{timestamp}.csv")
        summary_df.to_csv(summary_file, index=False)
        exported_files.append(summary_file)
        
        # Functions by category
        category_summary = functions_df.groupby('category').size().reset_index(name='count')
        category_file = os.path.join(output_dir, f"categories_{timestamp}.csv")
        category_summary.to_csv(category_file, index=False)
        exported_files.append(category_file)
        
        print(f"\n✅ CSV export completed successfully!")
        print(f"📁 Files saved in: {output_dir}")
        for file in exported_files:
            print(f"   • {os.path.basename(file)}")
        
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        return None
    
    conn.close()
    return exported_files

def show_database_overview(db_path="functions.db"):
    """Show overview of current database contents"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📊 DATABASE OVERVIEW")
    print("=" * 40)
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM functions")
    func_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_methods")
    method_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parameters")
    param_count = cursor.fetchone()[0]
    
    print(f"📋 Total Functions: {func_count}")
    print(f"🔧 Total Methods: {method_count}")
    print(f"📝 Total Parameters: {param_count}")
    
    # Functions by category
    print(f"\n📁 Functions by Category:")
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM functions 
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    for category, count in cursor.fetchall():
        print(f"   {category}: {count}")
    
    # Sample function names
    print(f"\n📋 Sample Functions:")
    cursor.execute("SELECT function_name FROM functions ORDER BY function_id LIMIT 10")
    for (name,) in cursor.fetchall():
        print(f"   • {name}")
    
    if func_count > 10:
        print(f"   ... and {func_count - 10} more")
    
    conn.close()

def main():
    """Main export function"""
    
    print("🚀 FUNCTION DATABASE EXPORT TOOL")
    print("=" * 60)
    
    # Check if database exists
    db_path = "functions.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   Run functions_schema.py and functions_populate.py first")
        return
    
    # Show current database overview
    show_database_overview(db_path)
    
    print(f"\n🔄 Starting export process...")
    
    # Try Excel export first, fallback to CSV
    try:
        excel_file = export_to_excel(db_path)
        if excel_file and os.path.exists(excel_file):
            print(f"\n🎉 EXPORT COMPLETE!")
            print(f"📁 Excel file: {excel_file}")
            print(f"📝 You can now edit the functions in Excel and re-import them")
    except Exception as e:
        print(f"⚠️  Excel export failed: {e}")
        print("🔄 Trying CSV export...")
        csv_files = export_to_csv(db_path)
        if csv_files:
            print(f"\n🎉 CSV EXPORT COMPLETE!")
            print(f"📁 Files exported to exports/ directory")

if __name__ == "__main__":
    main()