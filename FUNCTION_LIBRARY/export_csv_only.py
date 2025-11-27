"""
Force CSV Export of Functions Database
Creates CSV files even when Excel is available
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_to_csv_only(db_path="functions.db", output_dir="exports"):
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
        
        # Export parameters table WITH NEW COLUMNS including function_ref
        print("📝 Exporting parameters table (with function_ref, variable/input columns)...")
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
        
        # Show column info for parameters
        print(f"   📊 Parameters table columns: {list(params_df.columns)}")
        
        # Show parameter type summary
        if 'parameter_type_flag' in params_df.columns:
            variable_count = (params_df['parameter_type_flag'] == 1).sum()
            input_count = (params_df['parameter_type_flag'] == 0).sum()
            print(f"   🔧 Variables (flag=1): {variable_count}")
            print(f"   📥 Inputs (flag=0): {input_count}")
        
        # Create summary CSV
        print("📊 Creating summary file...")
        summary_data = {
            'Metric': [
                'Total Functions',
                'Total Methods', 
                'Total Parameters',
                'Variable Parameters (flag=1)',
                'Input Parameters (flag=0)',
                'Average Methods per Function',
                'Export Date',
                'Database File'
            ],
            'Value': [
                len(functions_df),
                len(methods_df),
                len(params_df),
                variable_count if 'parameter_type_flag' in params_df.columns else 'N/A',
                input_count if 'parameter_type_flag' in params_df.columns else 'N/A',
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
        
        # Show a preview of the parameters with new columns
        print(f"\n📋 PARAMETERS TABLE PREVIEW (with merged column):")
        if not params_df.empty:
            preview_columns = ['parameter_name', 'parameter_value', 'parameter_type_flag', 'method_name']
            available_columns = [col for col in preview_columns if col in params_df.columns]
            if available_columns:
                preview_df = params_df[available_columns].head(10)
                print(preview_df.to_string(index=False))
        
        conn.close()
        return exported_files
        
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        conn.close()
        return None

def main():
    """Main CSV export function"""
    
    print("🚀 CSV EXPORT TOOL (with Variable/Input columns)")
    print("=" * 60)
    
    # Check if database exists
    db_path = "functions.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    # Export to CSV
    csv_files = export_to_csv_only(db_path)
    
    if csv_files:
        print(f"\n🎉 CSV EXPORT COMPLETE!")
        print(f"✅ Database exported with updated schema including variable/input columns")
        print(f"✅ Ready for manual editing in any spreadsheet application")

if __name__ == "__main__":
    main()