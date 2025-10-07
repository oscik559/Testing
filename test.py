import sqlite3
import os

def create_filtered_pycatia_db():
    """
    Create a filtered version of pycatia_methods.db containing only methods
    referenced in the matched_full_signature column of test_pycatia_methods.db
    """
    
    # Database paths
    main_db = "pycatia_methods.db"
    test_db = "test_pycatia_methods.db" 
    filtered_db = "filtered_pycatia_methods.db"
    
    # Check if source databases exist
    if not os.path.exists(main_db):
        print(f"❌ Error: {main_db} not found")
        return
    
    if not os.path.exists(test_db):
        print(f"❌ Error: {test_db} not found")
        return
    
    # Remove existing filtered database
    if os.path.exists(filtered_db):
        os.remove(filtered_db)
        print(f"🗑️ Removed existing {filtered_db}")
    
    print("🔍 Creating filtered PyCATIA methods database...")
    
    # Connect to databases
    main_conn = sqlite3.connect(main_db)
    test_conn = sqlite3.connect(test_db)
    filtered_conn = sqlite3.connect(filtered_db)
    
    try:
        # Step 1: Get all matched method signatures from test database
        print("📋 Reading required methods from test database...")
        test_cursor = test_conn.cursor()
        test_cursor.execute("""
            SELECT DISTINCT matched_full_signature 
            FROM final_steps_methods 
            WHERE matched_full_signature IS NOT NULL 
            AND matched_full_signature != ''
        """)
        
        required_methods = set()
        for row in test_cursor.fetchall():
            signature = row[0]
            if signature:
                required_methods.add(signature)
        
        print(f"✅ Found {len(required_methods)} unique required methods")
        
        # Step 2: Get schema from main database and recreate in filtered database
        print("🏗️ Copying database schema...")
        main_cursor = main_conn.cursor()
        
        # Get all table creation statements
        main_cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        filtered_cursor = filtered_conn.cursor()
        for row in main_cursor.fetchall():
            if row[0]:  # Skip None values
                filtered_cursor.execute(row[0])
        
        # Get all index creation statements
        main_cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        
        for row in main_cursor.fetchall():
            if row[0]:  # Skip None values
                try:
                    filtered_cursor.execute(row[0])
                except sqlite3.Error:
                    pass  # Skip if index already exists
        
        filtered_conn.commit()
        print("✅ Schema copied successfully")
        
        # Step 3: Get all table names and order them properly
        main_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        all_tables = [row[0] for row in main_cursor.fetchall()]
        
        # Process tables in proper order: main tables first, then related tables
        table_order = ["pycatia_methods", "method_parameters", "method_purposes"]
        table_names = []
        
        # Add ordered tables first
        for table in table_order:
            if table in all_tables:
                table_names.append(table)
        
        # Add any remaining tables
        for table in all_tables:
            if table not in table_names:
                table_names.append(table)
        
        print(f"📊 Found {len(table_names)} tables to process: {table_names}")
        
        # Step 4: Copy filtered data for each table
        total_copied = 0
        
        for table_name in table_names:
            print(f"🔄 Processing table: {table_name}")
            
            # Get column names for this table
            main_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in main_cursor.fetchall()]
            column_list = ", ".join(columns)
            
            # Handle different tables with specific filtering logic
            if table_name == "pycatia_methods":
                # This is the main methods table - filter by full_method_name
                print(f"  🎯 Filtering methods table by full_method_name")
                
                # Create WHERE clause for exact matches
                if required_methods:
                    where_conditions = []
                    params = []
                    
                    for method in required_methods:
                        where_conditions.append("full_method_name = ?")
                        params.append(method)
                    
                    where_clause = " OR ".join(where_conditions)
                    query = f"SELECT {column_list} FROM {table_name} WHERE {where_clause}"
                    
                    main_cursor.execute(query, params)
                    rows = main_cursor.fetchall()
                    
                    if rows:
                        placeholders = ", ".join(["?" for _ in columns])
                        filtered_cursor.executemany(
                            f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                            rows
                        )
                        total_copied += len(rows)
                        print(f"  ✅ Copied {len(rows)} rows")
                    else:
                        print(f"  ⚠️ No matching methods found")
                else:
                    print(f"  ⚠️ No required methods to filter by")
                    
            elif table_name == "method_parameters":
                # Filter parameters table by method_id from filtered methods
                print(f"  🔗 Filtering parameters by method_id relationships")
                
                # First check if pycatia_methods table has been populated in filtered database
                try:
                    filtered_cursor.execute("SELECT id FROM pycatia_methods")
                    method_ids = [row[0] for row in filtered_cursor.fetchall()]
                except sqlite3.OperationalError:
                    # pycatia_methods table hasn't been processed yet, skip for now
                    method_ids = []
                
                if method_ids:
                    where_conditions = []
                    params = []
                    
                    for method_id in method_ids:
                        where_conditions.append("method_id = ?")
                        params.append(method_id)
                    
                    where_clause = " OR ".join(where_conditions)
                    query = f"SELECT {column_list} FROM {table_name} WHERE {where_clause}"
                    
                    main_cursor.execute(query, params)
                    rows = main_cursor.fetchall()
                    
                    if rows:
                        placeholders = ", ".join(["?" for _ in columns])
                        filtered_cursor.executemany(
                            f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                            rows
                        )
                        total_copied += len(rows)
                        print(f"  ✅ Copied {len(rows)} rows")
                    else:
                        print(f"  ⚠️ No matching parameters found")
                else:
                    print(f"  ⚠️ No method IDs to filter parameters by")
                    
            elif table_name == "method_purposes":
                # Filter purposes table by method_id from filtered methods
                print(f"  🔗 Filtering purposes by method_id relationships")
                
                # First check if pycatia_methods table has been populated in filtered database
                try:
                    filtered_cursor.execute("SELECT id FROM pycatia_methods")
                    method_ids = [row[0] for row in filtered_cursor.fetchall()]
                except sqlite3.OperationalError:
                    # pycatia_methods table hasn't been processed yet, skip for now
                    method_ids = []
                
                if method_ids:
                    where_conditions = []
                    params = []
                    
                    for method_id in method_ids:
                        where_conditions.append("method_id = ?")
                        params.append(method_id)
                    
                    where_clause = " OR ".join(where_conditions)
                    query = f"SELECT {column_list} FROM {table_name} WHERE {where_clause}"
                    
                    main_cursor.execute(query, params)
                    rows = main_cursor.fetchall()
                    
                    if rows:
                        placeholders = ", ".join(["?" for _ in columns])
                        filtered_cursor.executemany(
                            f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                            rows
                        )
                        total_copied += len(rows)
                        print(f"  ✅ Copied {len(rows)} rows")
                    else:
                        print(f"  ⚠️ No matching purposes found")
                else:
                    print(f"  ⚠️ No method IDs to filter purposes by")
                    
            else:
                # For other tables (like sqlite_sequence), copy everything
                print(f"  📋 Copying entire table (utility table)")
                main_cursor.execute(f"SELECT {column_list} FROM {table_name}")
                rows = main_cursor.fetchall()
                
                if rows:
                    placeholders = ", ".join(["?" for _ in columns])
                    filtered_cursor.executemany(
                        f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
                        rows
                    )
                    total_copied += len(rows)
                    print(f"  ✅ Copied {len(rows)} rows")
        
        filtered_conn.commit()
        
        # Step 5: Verification
        print("\n📊 Verification Summary:")
        print(f"✅ Total rows copied: {total_copied}")
        
        # Show table counts in filtered database
        for table_name in table_names:
            filtered_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = filtered_cursor.fetchone()[0]
            print(f"  📋 {table_name}: {count} rows")
        
        print(f"\n🎯 Filtered database created: {filtered_db}")
        print(f"📏 Original methods required: {len(required_methods)}")
        print("✅ Database filtering complete!")
        
        # Optional: Show sample of what was included
        print("\n📋 Sample of included methods:")
        for i, method in enumerate(sorted(required_methods)[:10]):
            print(f"  {i+1}. {method}")
        if len(required_methods) > 10:
            print(f"  ... and {len(required_methods) - 10} more")
    
    except Exception as e:
        print(f"❌ Error during filtering: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        main_conn.close()
        test_conn.close()
        filtered_conn.close()


def verify_filtered_database():
    """Verify the filtered database contains the expected methods"""
    
    filtered_db = "filtered_pycatia_methods.db"
    test_db = "test_pycatia_methods.db"
    
    if not os.path.exists(filtered_db) or not os.path.exists(test_db):
        print("❌ Cannot verify - databases not found")
        return
    
    print("\n🔍 Verifying filtered database...")
    
    filtered_conn = sqlite3.connect(filtered_db)
    test_conn = sqlite3.connect(test_db)
    
    try:
        # Get required methods from test database
        test_cursor = test_conn.cursor()
        test_cursor.execute("""
            SELECT DISTINCT matched_full_signature 
            FROM final_steps_methods 
            WHERE matched_full_signature IS NOT NULL 
            AND matched_full_signature != ''
        """)
        required_methods = {row[0] for row in test_cursor.fetchall()}
        
        # Check each table in filtered database
        filtered_cursor = filtered_conn.cursor()
        filtered_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        found_methods = set()
        
        for table_row in filtered_cursor.fetchall():
            table_name = table_row[0]
            
            # Get column info
            filtered_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in filtered_cursor.fetchall()]
            
            # Look for signature-like columns
            for col in columns:
                if any(keyword in col.lower() for keyword in ['signature', 'full_name', 'method_name']):
                    filtered_cursor.execute(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL")
                    for method_row in filtered_cursor.fetchall():
                        method_sig = method_row[0]
                        if method_sig in required_methods:
                            found_methods.add(method_sig)
        
        # Report results
        missing_methods = required_methods - found_methods
        extra_methods = found_methods - required_methods
        
        print(f"✅ Required methods: {len(required_methods)}")
        print(f"✅ Found methods: {len(found_methods)}")
        print(f"✅ Match rate: {len(found_methods)/len(required_methods)*100:.1f}%")
        
        if missing_methods:
            print(f"⚠️ Missing methods ({len(missing_methods)}):")
            for method in sorted(missing_methods)[:5]:
                print(f"  - {method}")
            if len(missing_methods) > 5:
                print(f"  ... and {len(missing_methods) - 5} more")
        
        if extra_methods:
            print(f"ℹ️ Extra methods found ({len(extra_methods)}):")
            for method in sorted(extra_methods)[:3]:
                print(f"  + {method}")
            if len(extra_methods) > 3:
                print(f"  ... and {len(extra_methods) - 3} more")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
    
    finally:
        filtered_conn.close()
        test_conn.close()


if __name__ == "__main__":
    print("🎯 PyCATIA Methods Database Filter")
    print("=" * 50)
    
    # Create the filtered database
    create_filtered_pycatia_db()
    
    # Verify the results
    verify_filtered_database()
    
    print("\n🎉 Process complete!")