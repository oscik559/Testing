import sqlite3
import os

def examine_database(db_path, db_name):
    """Examine database structure and sample data"""
    if not os.path.exists(db_path):
        print(f"❌ {db_name} not found")
        return
    
    print(f"\n🔍 Examining {db_name}")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(tables)} tables:")
        
        for table in tables:
            print(f"\n📋 Table: {table}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"  Columns ({len(columns)}):")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
            
            # Show sample data for tables with signature-like columns
            signature_cols = []
            for col in columns:
                col_name = col[1].lower()
                if any(keyword in col_name for keyword in ['signature', 'full_name', 'method_name', 'matched']):
                    signature_cols.append(col[1])
            
            if signature_cols and count > 0:
                print(f"  Sample signature data:")
                for sig_col in signature_cols[:2]:  # Show first 2 signature columns
                    cursor.execute(f"SELECT DISTINCT {sig_col} FROM {table} WHERE {sig_col} IS NOT NULL LIMIT 5")
                    samples = cursor.fetchall()
                    if samples:
                        print(f"    {sig_col}:")
                        for sample in samples:
                            if sample[0]:
                                print(f"      - {sample[0]}")
    
    except Exception as e:
        print(f"❌ Error examining {db_name}: {e}")
    
    finally:
        conn.close()

def compare_methods():
    """Compare methods between test and main databases"""
    print(f"\n🔍 Comparing required vs available methods")
    print("=" * 50)
    
    # Get required methods from test database
    if not os.path.exists('test_pycatia_methods.db'):
        print("❌ test_pycatia_methods.db not found")
        return
    
    test_conn = sqlite3.connect('test_pycatia_methods.db')
    test_cursor = test_conn.cursor()
    
    try:
        # Find the correct table and column
        test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in test_cursor.fetchall()]
        
        required_methods = set()
        
        for table in tables:
            # Get columns for this table
            test_cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in test_cursor.fetchall()]
            
            # Look for signature columns
            signature_cols = []
            for col in columns:
                col_lower = col.lower()
                if 'matched' in col_lower and 'signature' in col_lower:
                    signature_cols.append(col)
            
            if signature_cols:
                print(f"📋 Found signature column in {table}: {signature_cols}")
                
                for sig_col in signature_cols:
                    test_cursor.execute(f"""
                        SELECT DISTINCT {sig_col} 
                        FROM {table} 
                        WHERE {sig_col} IS NOT NULL 
                        AND {sig_col} != ''
                    """)
                    
                    for row in test_cursor.fetchall():
                        if row[0]:
                            required_methods.add(row[0])
        
        print(f"✅ Found {len(required_methods)} required methods")
        
        if required_methods:
            print("\n📋 Sample required methods:")
            for i, method in enumerate(sorted(required_methods)[:10]):
                print(f"  {i+1}. {method}")
            if len(required_methods) > 10:
                print(f"  ... and {len(required_methods) - 10} more")
        
        # Now check main database
        if os.path.exists('pycatia_methods.db'):
            main_conn = sqlite3.connect('pycatia_methods.db')
            main_cursor = main_conn.cursor()
            
            try:
                # Get tables from main database
                main_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                main_tables = [row[0] for row in main_cursor.fetchall()]
                
                print(f"\n📊 Main database has {len(main_tables)} tables")
                
                # Check if we can find these methods in main database
                found_methods = set()
                
                for table in main_tables:
                    # Get columns
                    main_cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in main_cursor.fetchall()]
                    
                    # Look for signature columns
                    signature_cols = []
                    for col in columns:
                        col_lower = col.lower()
                        if any(keyword in col_lower for keyword in ['signature', 'full_name', 'method_name', 'name']):
                            signature_cols.append(col)
                    
                    if signature_cols:
                        print(f"  📋 {table} has signature columns: {signature_cols}")
                        
                        # Sample some data to understand the format
                        for sig_col in signature_cols[:1]:  # Check first signature column
                            main_cursor.execute(f"SELECT DISTINCT {sig_col} FROM {table} WHERE {sig_col} IS NOT NULL LIMIT 5")
                            samples = main_cursor.fetchall()
                            if samples:
                                print(f"    Sample {sig_col} values:")
                                for sample in samples:
                                    if sample[0]:
                                        print(f"      - {sample[0]}")
                                        # Check if any required methods match
                                        for req_method in list(required_methods)[:5]:
                                            if req_method in sample[0] or sample[0] in req_method:
                                                found_methods.add(req_method)
                                                print(f"        ✅ MATCH: {req_method}")
                
                print(f"\n📊 Match Analysis:")
                print(f"  Required methods: {len(required_methods)}")
                print(f"  Found matches: {len(found_methods)}")
                if required_methods:
                    print(f"  Match rate: {len(found_methods)/len(required_methods)*100:.1f}%")
                
            finally:
                main_conn.close()
    
    except Exception as e:
        print(f"❌ Error comparing methods: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        test_conn.close()

if __name__ == "__main__":
    # Examine both databases
    examine_database('test_pycatia_methods.db', 'Test Database')
    examine_database('pycatia_methods.db', 'Main PyCATIA Database')
    examine_database('filtered_pycatia_methods.db', 'Filtered Database')
    
    # Compare methods
    compare_methods()