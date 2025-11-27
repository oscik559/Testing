# Function Library Database - Two-Script Setup Guide

## Overview
This directory contains a streamlined two-script setup for creating and managing the function library database:

1. **create_schema.py** - Creates the complete database structure
2. **populate_database.py** - Populates the database with optimized function data

## Database Statistics
- **17 optimized functions** (consolidated from 30 original functions)
- **124 methods** with complete parameter extraction
- **173 parameters** (146 variables + 27 inputs)
- **Optimized schema** with merged parameter_type_flag column

## Usage Instructions

### Step 1: Create Database Schema
```bash
python create_schema.py
```

This will:
- Create a fresh `functions.db` database
- Set up all tables (functions, function_methods, parameters)
- Create performance indexes and foreign key constraints
- Display complete schema details

### Step 2: Populate Database
```bash
python populate_database.py
```

This will:
- Check if database already contains data (preserves existing optimized data)
- Extract functions from `uav_wing_design_2.py` using AST parsing
- Apply consolidation rules to merge similar functions
- Populate all tables with comprehensive method and parameter data
- Display final statistics and verification

## Key Features

### Smart Population Logic
- **Preservation Check**: Won't overwrite existing optimized database
- **AST Analysis**: Comprehensive extraction of functions, methods, and parameters
- **Consolidation Rules**: Merges similar functions into generic templates
- **Parameter Classification**: Distinguishes between variables (flag=1) and inputs (flag=0)

### Database Schema
```sql
-- Functions table
functions (function_id, function_name, function_description, category, timestamp)

-- Methods table  
function_methods (id, function_ref, method_name, step_order, object_chain, 
                 method_call, method_parameters, object_type, return_type, 
                 method_description, timestamp)

-- Parameters table
parameters (id, function_ref, method_ref, parameter_name, parameter_type,
           parameter_value, parameter_position, parameter_description, 
           parameter_type_flag)
```

### Parameter Type Flag
- **parameter_type_flag = 1**: Variables (objects, method outputs)
- **parameter_type_flag = 0**: Inputs (literal values, user inputs)

## File Structure
```
FUNCTION_LIBRARY/
├── create_schema.py          # Database schema creator
├── populate_database.py      # Database populator
├── uav_wing_design_2.py     # Source functions file
├── functions.db             # Generated database
└── exports/                 # Export files directory
```

## Export/Import Pipeline
After creating and populating the database, you can:

1. **Export to Excel/CSV**: Use existing export scripts
2. **Edit Data**: Modify exported CSV files
3. **Import Changes**: Use import scripts to update database

## Troubleshooting

### Database Already Populated
If you see "Database already contains X functions", the populate script is preserving your existing optimized data. This is normal and expected behavior.

### Starting Fresh
To create a completely new database:
1. Delete the existing `functions.db` file
2. Run `python create_schema.py`
3. Run `python populate_database.py`

### Verification
Check database contents:
```python
import sqlite3
conn = sqlite3.connect('functions.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM functions')
print(f'Functions: {cursor.fetchone()[0]}')
conn.close()
```

## Expected Output
- **Functions**: 17 (optimized/consolidated)
- **Methods**: 124 (all method calls extracted)
- **Parameters**: 173 (comprehensive parameter analysis)
- **Categories**: 7 distinct function categories
- **Performance**: Indexed tables with foreign key constraints

## Success Indicators
✅ Database schema created successfully  
✅ All tables and indexes in place  
✅ Foreign key constraints enabled  
✅ Consolidation rules applied for optimization  
✅ All functions, methods, and parameters populated  
✅ Parameter type classification complete  

## Next Steps
After successful creation and population:
1. Use export scripts to generate Excel/CSV files
2. Analyze function patterns and relationships
3. Integrate with CATIA automation workflows
4. Extend with additional function libraries as needed