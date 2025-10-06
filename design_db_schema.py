# Script to create the design database for agentic CAD automation
# This script creates three tables: design_templates, design_steps, design_parameters
# Each table includes comments and foreign key constraints as specified

import os
import sqlite3
from uav_wing import (
    get_uav_flying_wing_template,
    get_uav_flying_wing_steps,
    get_uav_flying_wing_parameters,
)

# Database path
DESIGN_DB_PATH = "design.db"

SCHEMA_SQL = """
-- Table: design_templates
-- Stores design templates for UAV wing creation workflows
CREATE TABLE IF NOT EXISTS design_templates (
    id INTEGER PRIMARY KEY,
    part_type TEXT UNIQUE NOT NULL,     -- Name of the design (e.g., 'uav_wing', 'flying_wing')
    description TEXT,                   -- Human-readable description of the design
    domain TEXT,                        -- CATIA workbench (e.g., 'Generative Shape Design')
    complexity TEXT,                    -- Complexity level (e.g., 'basic', 'intermediate', 'advanced')
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: design_steps
-- Stores ordered steps for UAV wing design, including instructions and parameters from steps.xlsx
CREATE TABLE IF NOT EXISTS design_steps (
    id INTEGER PRIMARY KEY,
    template_id INTEGER NOT NULL,       -- References design_templates.id
    step_number INTEGER NOT NULL,       -- Order of execution (from Excel Step column)
    action_short TEXT NOT NULL,         -- Short description of action (from Excel)
    details TEXT,                       -- Detailed how-to instructions (from Excel)
    action_type TEXT,                   -- Type of action (CreatePoint, CreateSpline, etc.)
    target_object TEXT,                 -- Object being created/modified
    parameters TEXT,                    -- JSON parameters for the action
    dependencies TEXT,                  -- References to prerequisite steps
    purpose_notes TEXT,                 -- Purpose/Notes from Excel
    pycatia_method TEXT,                -- Corresponding PyCATIA method name
    FOREIGN KEY (template_id) REFERENCES design_templates(id) ON DELETE CASCADE
);

-- Table: design_parameters
-- Stores parameterizable values for the UAV wing design
CREATE TABLE IF NOT EXISTS design_parameters (
    id INTEGER PRIMARY KEY,
    template_id INTEGER NOT NULL,       -- References design_templates.id
    parameter_name TEXT NOT NULL,       -- Name of the parameter
    parameter_value TEXT,               -- Default value
    parameter_type TEXT,                -- Type (REAL, INTEGER, TEXT, BOOLEAN)
    parameter_unit TEXT,                -- Unit of measurement (mm, deg, etc.)
    description TEXT,                   -- Description of what this parameter controls
    min_value REAL,                     -- Minimum allowed value
    max_value REAL,                     -- Maximum allowed value
    is_required BOOLEAN DEFAULT TRUE,   -- Whether this parameter is required
    FOREIGN KEY (template_id) REFERENCES design_templates(id) ON DELETE CASCADE
);
"""


def create_design_db(db_path=DESIGN_DB_PATH):
    """
    Creates the design database and tables for UAV wing design automation.
    """
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"Design database schema created at: {db_path}")
    except Exception as e:
        print(f"Error creating database schema: {e}")
        conn.rollback()
    finally:
        conn.close()


def insert_uav_template(cursor):
    """Insert UAV template and return template_id"""
    template_data = get_uav_flying_wing_template()

    # Check if template exists
    cursor.execute(
        "SELECT id FROM design_templates WHERE part_type = ?",
        (template_data["part_type"],),
    )
    existing = cursor.fetchone()

    if existing:
        print(f"✅ UAV Flying Wing template already exists (ID: {existing[0]})")
        return existing[0]
    else:
        cursor.execute(
            "INSERT INTO design_templates (part_type, description, domain, complexity) VALUES (?, ?, ?, ?)",
            (
                template_data["part_type"],
                template_data["description"],
                template_data["domain"],
                template_data["complexity"],
            ),
        )
        template_id = cursor.lastrowid
        print(f"✅ Created UAV Flying Wing template (ID: {template_id})")
        return template_id


def insert_uav_steps(cursor, template_id):
    """Insert UAV design steps for given template_id"""
    print("\n📋 Inserting UAV Flying Wing Design Steps...")

    # Clear existing steps and insert new ones
    cursor.execute("DELETE FROM design_steps WHERE template_id = ?", (template_id,))
    uav_steps = get_uav_flying_wing_steps(template_id)

    cursor.executemany(
        """INSERT INTO design_steps (
            template_id, step_number, action_short, details, action_type,
            target_object, parameters, dependencies, purpose_notes, pycatia_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        uav_steps,
    )

    print(f"✅ Inserted {len(uav_steps)} UAV Flying Wing design steps")
    return len(uav_steps)


def insert_uav_parameters(cursor, template_id):
    """Insert UAV design parameters for given template_id"""
    print("\n🔧 Inserting UAV Flying Wing Design Parameters...")

    # Clear existing parameters and insert new ones
    cursor.execute(
        "DELETE FROM design_parameters WHERE template_id = ?", (template_id,)
    )
    uav_parameters = get_uav_flying_wing_parameters(template_id)

    cursor.executemany(
        """INSERT INTO design_parameters (
            template_id, parameter_name, parameter_value, parameter_type,
            parameter_unit, description, min_value, max_value, is_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        uav_parameters,
    )

    print(f"✅ Inserted {len(uav_parameters)} UAV Flying Wing design parameters")
    return len(uav_parameters)


def populate_uav_design_data(db_path=DESIGN_DB_PATH):
    """
    Populate the design database with UAV flying wing design data.
    """
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found. Please run create_design_db() first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🛩️  Populating UAV Flying Wing Design Data")
    print("=" * 50)

    try:
        # Insert template, steps, and parameters
        template_id = insert_uav_template(cursor)
        step_count = insert_uav_steps(cursor, template_id)
        param_count = insert_uav_parameters(cursor, template_id)

        # Commit all changes
        conn.commit()

        print("\n🎯 UAV Flying Wing Design Data Successfully Populated!")
        print(f"   📋 Template ID: {template_id}")
        print(f"   📐 Design Steps: {step_count}")
        print(f"   🔧 Parameters: {param_count}")

    except Exception as e:
        print(f"❌ Error populating UAV design data: {e}")
        conn.rollback()
    finally:
        conn.close()
    """Query the design database schema to show table information"""

    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return

    conn = sqlite3.connect(db_path)

    print("\n=== DESIGN DATABASE SCHEMA ===")

    try:
        # Show table schemas
        print("\n--- Table Schemas ---")
        cursor = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        for name, sql in cursor.fetchall():
            print(f"\nTable: {name}")
            if sql:
                # Extract column info from CREATE statement
                lines = sql.split("\n")
                for line in lines[1:-1]:  # Skip CREATE TABLE and closing )
                    line = line.strip()
                    if (
                        line
                        and not line.startswith("--")
                        and not line.startswith("FOREIGN KEY")
                    ):
                        print(f"  {line}")

        # Show table counts
        tables = ["design_templates", "design_steps", "design_parameters"]
        print("\n--- Table Counts ---")
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
            except sqlite3.OperationalError:
                print(f"{table}: table does not exist")

    except Exception as e:
        print(f"Error querying database schema: {e}")
    finally:
        conn.close()


def query_design_db_schema(db_path=DESIGN_DB_PATH):
    """Query the design database schema to show table information"""

    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return

    conn = sqlite3.connect(db_path)

    print("\n=== DESIGN DATABASE SCHEMA ===")

    try:
        # Show table schemas
        print("\n--- Table Schemas ---")
        cursor = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        for name, sql in cursor.fetchall():
            print(f"\nTable: {name}")
            if sql:
                # Extract column info from CREATE statement
                lines = sql.split("\n")
                for line in lines[1:-1]:  # Skip CREATE TABLE and closing )
                    line = line.strip()
                    if (
                        line
                        and not line.startswith("--")
                        and not line.startswith("FOREIGN KEY")
                    ):
                        print(f"  {line}")

        # Show table counts
        tables = ["design_templates", "design_steps", "design_parameters"]
        print("\n--- Table Counts ---")
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
            except sqlite3.OperationalError:
                print(f"{table}: table does not exist")

    except Exception as e:
        print(f"Error querying database schema: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("Design Database Schema Creator")
    print("=" * 40)

    # Create the database schema
    create_design_db()

    # Populate with UAV design data
    populate_uav_design_data()

    # Query and display schema information
    query_design_db_schema()

    print(f"\n✅ Design database with UAV data ready!")
    print(f"📍 Database: {DESIGN_DB_PATH}")
    print("🚀 Ready for UAV design automation!")
