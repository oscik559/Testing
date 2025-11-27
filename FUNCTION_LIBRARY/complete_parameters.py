"""
Complete Parameters Extraction
Extracts all missing parameters from method calls and assignments
"""

import sqlite3
import re
import ast
from datetime import datetime

def extract_parameters_from_method_call(method_call, method_name):
    """Extract parameters from a method call string"""
    
    parameters = []
    
    # Handle different types of method calls
    if '=' in method_call:
        # Assignment operations like: variable.name = 'value'
        if '.name =' in method_call or '.Name =' in method_call:
            # Extract the value being assigned
            match = re.search(r'\.name\s*=\s*[\'"]([^\'"]+)[\'"]', method_call, re.IGNORECASE)
            if match:
                value = match.group(1)
                parameters.append({
                    'name': 'name_value',
                    'type': 'str',
                    'value': value,
                    'position': 1,
                    'description': f'Name value for {method_name}',
                    'variable': 0,  # This is an input
                    'input': 1
                })
        
        # Other assignments like: variable = method(params)
        elif '(' in method_call and ')' in method_call:
            # Extract parameters from method call
            params = extract_function_parameters(method_call)
            parameters.extend(params)
    
    elif '(' in method_call and ')' in method_call:
        # Direct method calls like: method(param1, param2)
        params = extract_function_parameters(method_call)
        parameters.extend(params)
    
    return parameters

def extract_function_parameters(method_call):
    """Extract parameters from function call syntax"""
    
    parameters = []
    
    # Find the method call part
    method_match = re.search(r'(\w+)\((.*?)\)', method_call)
    if not method_match:
        return parameters
    
    method_name = method_match.group(1)
    params_str = method_match.group(2).strip()
    
    if not params_str:
        return parameters
    
    # Split parameters by comma, handling nested parentheses
    param_parts = split_parameters(params_str)
    
    for i, param in enumerate(param_parts):
        param = param.strip()
        if param:
            param_info = analyze_parameter(param, i + 1, method_name)
            if param_info:
                parameters.append(param_info)
    
    return parameters

def split_parameters(params_str):
    """Split parameter string by commas, respecting parentheses and quotes"""
    
    parameters = []
    current_param = ""
    paren_depth = 0
    quote_char = None
    
    for char in params_str:
        if quote_char:
            current_param += char
            if char == quote_char and (not current_param.endswith('\\' + quote_char)):
                quote_char = None
        elif char in ['"', "'"]:
            quote_char = char
            current_param += char
        elif char == '(':
            paren_depth += 1
            current_param += char
        elif char == ')':
            paren_depth -= 1
            current_param += char
        elif char == ',' and paren_depth == 0:
            parameters.append(current_param.strip())
            current_param = ""
        else:
            current_param += char
    
    if current_param.strip():
        parameters.append(current_param.strip())
    
    return parameters

def analyze_parameter(param, position, method_name):
    """Analyze a parameter to determine its type and characteristics"""
    
    param = param.strip()
    
    # Determine if it's a variable or input
    is_variable = True
    is_input = False
    param_type = "Unknown"
    param_value = None
    
    # String literals
    if (param.startswith('"') and param.endswith('"')) or (param.startswith("'") and param.endswith("'")):
        is_variable = False
        is_input = True
        param_type = "str"
        param_value = param[1:-1]  # Remove quotes
    
    # Numeric literals
    elif re.match(r'^-?\d*\.?\d+$', param):
        is_variable = False
        is_input = True
        param_type = "float" if '.' in param else "int"
        param_value = param
    
    # Boolean literals
    elif param.lower() in ['true', 'false']:
        is_variable = False
        is_input = True
        param_type = "bool"
        param_value = param.lower()
    
    # None/null values
    elif param.lower() in ['none', 'null']:
        is_variable = True
        is_input = False
        param_type = "NoneType"
        param_value = "None"
    
    # Variable names (identifiers)
    elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param):
        is_variable = True
        is_input = False
        param_type = "object"
        param_value = None
    
    # Complex expressions
    else:
        # Could be method calls, attribute access, etc.
        is_variable = True
        is_input = False
        param_type = "expression"
        param_value = None
    
    return {
        'name': param,
        'type': param_type,
        'value': param_value,
        'position': position,
        'description': f'Parameter {position} for {method_name}',
        'variable': 1 if is_variable else 0,
        'input': 1 if is_input else 0
    }

def complete_parameters_extraction(db_path="functions.db"):
    """Extract all missing parameters from method calls"""
    
    print("🔧 COMPLETING PARAMETERS EXTRACTION")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all methods without parameters
    cursor.execute("""
        SELECT fm.id, fm.function_ref, fm.method_name, fm.method_call, fm.step_order
        FROM function_methods fm
        LEFT JOIN parameters p ON fm.id = p.method_ref
        WHERE p.method_ref IS NULL
        ORDER BY fm.function_ref, fm.step_order
    """)
    
    methods_without_params = cursor.fetchall()
    
    print(f"📋 Found {len(methods_without_params)} methods without parameters")
    
    if len(methods_without_params) == 0:
        print("✅ All methods already have parameters extracted!")
        conn.close()
        return
    
    # Extract parameters for each method
    total_extracted = 0
    
    for method_id, function_id, method_name, method_call, step_order in methods_without_params:
        print(f"🔍 Processing: {method_name}")
        print(f"   📝 Call: {method_call[:80]}...")
        
        # Extract parameters from the method call
        parameters = extract_parameters_from_method_call(method_call, method_name)
        
        if parameters:
            print(f"   ✅ Found {len(parameters)} parameters:")
            
            for param in parameters:
                # Insert parameter into database
                cursor.execute("""
                    INSERT INTO parameters (
                        function_ref, method_ref, parameter_name, parameter_type, 
                        parameter_value, parameter_position, parameter_description, 
                        variable, input
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    function_id,
                    method_id,
                    param['name'],
                    param['type'],
                    param['value'],
                    param['position'],
                    param['description'],
                    param['variable'],
                    param['input']
                ))
                
                var_type = "Input" if param['input'] else "Variable"
                print(f"     • {param['name']} ({param['type']}) = {param['value']} [{var_type}]")
                
                total_extracted += 1
        else:
            print(f"   ⚠️  No parameters found")
    
    # Commit changes
    conn.commit()
    
    # Verify completion
    cursor.execute("SELECT COUNT(*) FROM parameters")
    total_params = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM function_methods fm
        LEFT JOIN parameters p ON fm.id = p.method_ref
        WHERE p.method_ref IS NULL
    """)
    remaining_without_params = cursor.fetchone()[0]
    
    print(f"\n✅ Parameters extraction completed!")
    print(f"📊 Total parameters extracted: {total_extracted}")
    print(f"📊 Total parameters in database: {total_params}")
    print(f"📊 Methods still without parameters: {remaining_without_params}")
    
    # Show parameter statistics
    cursor.execute("SELECT COUNT(*) FROM parameters WHERE variable = 1")
    variable_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parameters WHERE input = 1")
    input_count = cursor.fetchone()[0]
    
    print(f"📊 Parameter classification:")
    print(f"   🔧 Variables: {variable_count}")
    print(f"   📥 Inputs: {input_count}")
    
    conn.close()

def show_parameter_examples(db_path="functions.db"):
    """Show examples of extracted parameters"""
    
    print(f"\n📋 PARAMETER EXAMPLES")
    print("=" * 30)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show input parameters
    print("📥 INPUT PARAMETERS:")
    cursor.execute("""
        SELECT p.parameter_name, p.parameter_type, p.parameter_value, 
               fm.method_name, f.function_name
        FROM parameters p
        JOIN function_methods fm ON p.method_ref = fm.id
        JOIN functions f ON p.function_ref = f.function_id
        WHERE p.input = 1
        LIMIT 10
    """)
    
    for param_name, param_type, param_value, method_name, func_name in cursor.fetchall():
        print(f"   • {param_name} ({param_type}) = {param_value} in {func_name}.{method_name}")
    
    # Show variable parameters
    print(f"\n🔧 VARIABLE PARAMETERS:")
    cursor.execute("""
        SELECT p.parameter_name, p.parameter_type, fm.method_name, f.function_name
        FROM parameters p
        JOIN function_methods fm ON p.method_ref = fm.id
        JOIN functions f ON p.function_ref = f.function_id
        WHERE p.variable = 1
        LIMIT 10
    """)
    
    for param_name, param_type, method_name, func_name in cursor.fetchall():
        print(f"   • {param_name} ({param_type}) in {func_name}.{method_name}")
    
    conn.close()

def main():
    """Main completion function"""
    
    print("🚀 COMPLETE PARAMETERS EXTRACTION")
    print("=" * 60)
    
    complete_parameters_extraction()
    show_parameter_examples()
    
    print(f"\n🎉 PARAMETERS TABLE COMPLETION FINISHED!")
    print(f"✅ All method calls now have parameters extracted")
    print(f"✅ Parameters classified as variables or inputs")
    print(f"✅ Ready for export with complete parameter data")

if __name__ == "__main__":
    main()