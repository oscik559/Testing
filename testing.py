#!/usr/bin/env python3
"""
PyCATIA Methods Reference Extractor
Extracts PyCATIA API methods from UAV wing design code and database,
creates a reference database linking steps to methods with full method details.
"""

import sqlite3
import re
import ast
import inspect
from pathlib import Path


def extract_pycatia_methods_from_code(file_path):
    """Extract PyCATIA method calls from Python code"""
    methods = []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse the AST to find function definitions
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract step number from function name
            step_match = re.match(r"step_(\d+)_", node.name)
            if step_match:
                step_num = int(step_match.group(1))
                function_name = node.name

                # Get function source code
                func_lines = ast.get_source_segment(content, node)
                if func_lines:
                    # Find PyCATIA method calls
                    pycatia_calls = find_pycatia_calls(func_lines)

                    methods.append(
                        {
                            "step_number": step_num,
                            "function_name": function_name,
                            "pycatia_methods": pycatia_calls,
                            "source_type": "code",
                        }
                    )

    return methods


def find_pycatia_calls(code_text):
    """Find PyCATIA API method calls in code text"""
    pycatia_patterns = [
        r"\.add_new_(\w+)\(",
        r"\.create_reference_from_(\w+)\(",
        r"hybrid_shape_factory\.(\w+)\(",
        r"shape_factory\.(\w+)\(",
        r"part\.(\w+)\(",
        r"catia\(\)",
        r"documents\.(\w+)\(",
        r"\.start_workbench\(",
        r"\.update\(\)",
        r"\.append_hybrid_shape\(",
        r"selection\.(\w+)\(",
        r"vis_properties\.(\w+)\(",
    ]

    methods = []
    for pattern in pycatia_patterns:
        matches = re.findall(pattern, code_text)
        for match in matches:
            if isinstance(match, tuple):
                methods.extend(match)
            else:
                methods.append(match)

    # Clean up and deduplicate
    methods = list(set([m for m in methods if m and m != ""]))
    return methods


def extract_methods_from_database(db_path):
    """Extract PyCATIA methods from design database"""
    methods = []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT step_number, action_short, pycatia_method
            FROM design_steps
            ORDER BY step_number
        """
        )

        for row in cursor.fetchall():
            step_num, action_short, pycatia_method = row
            if pycatia_method:
                # Parse multiple methods separated by commas
                method_list = [m.strip() for m in pycatia_method.split(",")]
                methods.append(
                    {
                        "step_number": step_num,
                        "function_name": f'step_{step_num:02d}_{action_short.lower().replace(" ", "_")}',
                        "pycatia_methods": method_list,
                        "source_type": "database",
                    }
                )

        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

    return methods


def get_method_details_from_pycatia_db(method_name, pycatia_db_path):
    """Get method details from pycatia_methods.db"""
    try:
        conn = sqlite3.connect(pycatia_db_path)
        cursor = conn.cursor()

        # Try different search patterns for method name matching
        search_patterns = [
            f"%{method_name}%",
            f"%{method_name.lower()}%",
            f"%.{method_name}%",
            f"%{method_name}(%",
        ]

        for pattern in search_patterns:
            cursor.execute(
                """
                SELECT * FROM pycatia_methods
                WHERE method_name LIKE ? OR full_method_name LIKE ?
                LIMIT 1
            """,
                (pattern, pattern),
            )

            result = cursor.fetchone()
            if result:
                # Get column names
                cursor.execute("PRAGMA table_info(pycatia_methods)")
                columns = [col[1] for col in cursor.fetchall()]

                # Convert to dictionary
                method_details = dict(zip(columns, result))
                conn.close()
                return method_details

        conn.close()
        return None

    except sqlite3.Error as e:
        print(f"PyCATIA database error: {e}")
        return None


def create_reference_database(output_db_path):
    """Create the reference database with steps-methods table"""
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()

    # Drop existing table if it exists to ensure clean slate
    cursor.execute("DROP TABLE IF EXISTS `steps-methods`")

    # Create steps-methods table
    cursor.execute(
        """
        CREATE TABLE `steps-methods` (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_number INTEGER NOT NULL,
            function_name TEXT NOT NULL,
            method_name TEXT NOT NULL,
            source_type TEXT NOT NULL,  -- 'code' or 'database'

            -- PyCATIA method details (from pycatia_methods.db)
            method_id INTEGER,
            full_signature TEXT,
            class_name TEXT,
            module_name TEXT,
            description TEXT,
            parameters TEXT,
            return_type TEXT,
            example_usage TEXT,
            documentation_url TEXT,

            -- Metadata
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(step_number, function_name, method_name, source_type)
        )
    """
    )

    conn.commit()
    conn.close()
    print(f"✅ Created reference database: {output_db_path}")


def populate_reference_database(output_db_path, code_methods, pycatia_db_path):
    """Populate the reference database with extracted methods from code only"""
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()

    # Use only code methods
    all_methods = code_methods

    inserted_count = 0

    for method_data in all_methods:
        step_num = method_data["step_number"]
        func_name = method_data["function_name"]
        source_type = method_data["source_type"]

        for method_name in method_data["pycatia_methods"]:
            # Get method details from pycatia_methods.db
            method_details = get_method_details_from_pycatia_db(
                method_name, pycatia_db_path
            )

            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO `steps-methods` (
                        step_number, function_name, method_name, source_type,
                        method_id, full_signature, class_name, module_name,
                        description, parameters, return_type, example_usage,
                        documentation_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        step_num,
                        func_name,
                        method_name,
                        source_type,
                        method_details.get("id") if method_details else None,
                        (
                            method_details.get("full_method_name")
                            if method_details
                            else None
                        ),
                        None,  # class_name not available in new schema
                        None,  # module_name not available in new schema
                        None,  # description not available in new schema
                        (
                            method_details.get("method_parameters")
                            if method_details
                            else None
                        ),
                        (
                            method_details.get("return_annotation")
                            if method_details
                            else None
                        ),
                        None,  # example_usage not available in new schema
                        None,  # documentation_url not available in new schema
                    ),
                )

                if cursor.rowcount > 0:
                    inserted_count += 1

            except sqlite3.Error as e:
                print(f"Error inserting {method_name}: {e}")

    conn.commit()
    conn.close()

    print(f"✅ Inserted {inserted_count} method references")


def generate_summary_report(output_db_path):
    """Generate a summary report of extracted methods"""
    conn = sqlite3.connect(output_db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("📊 PYCATIA METHODS REFERENCE SUMMARY")
    print("=" * 80)

    # Total methods by source (only code methods)
    cursor.execute(
        """
        SELECT source_type, COUNT(*) as count
        FROM `steps-methods`
        WHERE source_type = 'code'
        GROUP BY source_type
    """
    )

    print("\n📈 Methods by Source:")
    for source_type, count in cursor.fetchall():
        print(f"  {source_type.upper():10}: {count:3} methods")

    # Methods per step (only code methods)
    cursor.execute(
        """
        SELECT step_number, COUNT(*) as method_count
        FROM `steps-methods`
        WHERE source_type = 'code'
        GROUP BY step_number
        ORDER BY step_number
    """
    )

    print("\n🔧 Methods per Step:")
    step_data = cursor.fetchall()
    for step_num, count in step_data:
        print(f"  Step {step_num:2}: {count:2} methods")

    # Most common methods (only code methods)
    cursor.execute(
        """
        SELECT method_name, COUNT(*) as usage_count
        FROM `steps-methods`
        WHERE source_type = 'code'
        GROUP BY method_name
        ORDER BY usage_count DESC
        LIMIT 10
    """
    )

    print("\n🏆 Most Used Methods:")
    for method_name, usage_count in cursor.fetchall():
        print(f"  {method_name:30}: {usage_count} times")

    # Methods with documentation (only code methods)
    cursor.execute(
        """
        SELECT
            COUNT(*) as total_methods,
            COUNT(full_signature) as with_signature,
            COUNT(description) as with_description,
            COUNT(documentation_url) as with_docs
        FROM `steps-methods`
        WHERE source_type = 'code'
    """
    )

    total, with_sig, with_desc, with_docs = cursor.fetchone()
    print(f"\n📚 Documentation Coverage:")
    print(f"  Total Methods:     {total}")
    print(f"  With Signature:    {with_sig} ({with_sig/total*100:.1f}%)")
    print(f"  With Description:  {with_desc} ({with_desc/total*100:.1f}%)")
    print(f"  With Docs URL:     {with_docs} ({with_docs/total*100:.1f}%)")

    conn.close()


def main():
    """Main execution function"""
    print("🚀 PyCATIA Methods Reference Extractor")
    print("=" * 50)

    # File paths
    code_file = "uav_wing_design.py"
    pycatia_db = "pycatia_methods.db"
    output_db = "ref_pycatia_methods.db"

    # Check if required files exist
    required_files = [code_file, pycatia_db]
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            return

    print("✅ All required files found")

    # Extract methods from code
    print("\n📝 Extracting methods from code...")
    code_methods = extract_pycatia_methods_from_code(code_file)
    print(f"✅ Found {len(code_methods)} step functions in code")

    # Create reference database
    print(f"\n🗄️ Creating reference database: {output_db}")
    create_reference_database(output_db)

    # Populate with method data (code methods only)
    print("\n📊 Populating reference database with code methods only...")
    populate_reference_database(output_db, code_methods, pycatia_db)

    # Generate summary report
    generate_summary_report(output_db)

    print(f"\n🎯 Reference database created successfully: {output_db}")
    print("   Table: steps-methods")
    print(
        "   Contains: Code-based Step-to-Method mappings with full PyCATIA reference details"
    )
    print(
        "   Note: Only methods extracted from code are included (database methods excluded)"
    )


if __name__ == "__main__":
    main()
