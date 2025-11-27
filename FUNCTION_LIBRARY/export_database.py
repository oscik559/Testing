"""
Database Export Utility
Export function library database to CSV and Excel formats
"""

import sqlite3
import csv
import os
from datetime import datetime

# Optional imports for Excel functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("pandas not available - Excel export will be skipped")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("openpyxl not available - Excel export will be limited")

def export_to_csv(db_path: str = "functions.db", output_dir: str = "exports"):
    """Export all tables to CSV files"""
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    exported_files = []
    
    for table_name in tables:
        # Get all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Write to CSV
        csv_filename = os.path.join(output_dir, f"{table_name}_{timestamp}.csv")
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Header
            writer.writerows(data)    # Data
        
        exported_files.append(csv_filename)
        print(f"✓ Exported {table_name}: {len(data)} rows to {csv_filename}")
    
    conn.close()
    return exported_files

def export_to_excel(db_path: str = "functions.db", output_dir: str = "exports"):
    """Export all tables to a single Excel file with multiple sheets"""
    
    if not PANDAS_AVAILABLE:
        print("❌ pandas not available - skipping Excel export")
        return None
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = os.path.join(output_dir, f"function_library_{timestamp}.xlsx")
    
    conn = sqlite3.connect(db_path)
    
    # Get all table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    try:
        with pd.ExcelWriter(excel_filename, engine='openpyxl' if OPENPYXL_AVAILABLE else 'xlsxwriter') as writer:
            total_rows = 0
            
            for table_name in tables:
                # Read table into DataFrame
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                
                # Write to Excel sheet
                df.to_excel(writer, sheet_name=table_name, index=False)
                total_rows += len(df)
                print(f"✓ Added sheet '{table_name}': {len(df)} rows")
            
            # Create summary sheet
            summary_data = []
            for table_name in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                summary_data.append({'Table': table_name, 'Row_Count': count})
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        conn.close()
        print(f"✓ Exported all tables to {excel_filename} ({total_rows} total rows)")
        return excel_filename
    
    except Exception as e:
        conn.close()
        print(f"❌ Excel export failed: {e}")
        return None

def export_function_templates(db_path: str = "functions.db", output_dir: str = "exports"):
    """Export function templates for code generation"""
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    template_filename = os.path.join(output_dir, f"function_templates_{timestamp}.csv")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get detailed function information
    cursor.execute("""
        SELECT 
            f.function_name,
            f.function_description,
            f.category,
            COUNT(fm.id) as method_count,
            GROUP_CONCAT(fm.method_name || '(' || fm.object_chain || ')') as methods_summary
        FROM functions f
        LEFT JOIN function_methods fm ON f.function_id = fm.function_ref
        GROUP BY f.function_id
        ORDER BY f.category, f.function_name
    """)
    
    data = cursor.fetchall()
    headers = ['Function_Name', 'Description', 'Category', 'Method_Count', 'Methods_Summary']
    
    with open(template_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(data)
    
    conn.close()
    print(f"✓ Exported function templates to {template_filename}")
    return template_filename

def export_all(db_path: str = "functions.db"):
    """Export database in all formats"""
    
    print("Function Library Database Export")
    print("=" * 50)
    
    try:
        # CSV Export
        print("\n1. Exporting to CSV...")
        csv_files = export_to_csv(db_path)
        
        # Excel Export
        print("\n2. Exporting to Excel...")
        excel_file = export_to_excel(db_path)
        
        # Template Export
        print("\n3. Exporting function templates...")
        template_file = export_function_templates(db_path)
        
        print(f"\n✅ Export completed successfully!")
        print(f"📁 All files saved in 'exports' directory")
        print(f"📊 CSV files: {len(csv_files)}")
        print(f"📋 Excel file: {os.path.basename(excel_file)}")
        print(f"📄 Template file: {os.path.basename(template_file)}")
        
        return {
            'csv_files': csv_files,
            'excel_file': excel_file,
            'template_file': template_file
        }
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None

if __name__ == "__main__":
    # Run export
    result = export_all()
    
    if result:
        print(f"\n🚀 Export Summary:")
        print(f"   - CSV files: {len(result['csv_files'])}")
        print(f"   - Excel file: 1")
        print(f"   - Template file: 1")