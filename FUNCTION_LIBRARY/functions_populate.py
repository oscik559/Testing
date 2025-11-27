"""
Function Library Database Population Script
Extracts function and method data from uav_wing_design_2.py and pycatia_methods.db
to populate the functions.db database.
"""

import sqlite3
import ast
import inspect
import re
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add the current directory to Python path to import the UAV wing design module
sys.path.append(os.path.abspath('.'))

def clean_function_name(original_name: str) -> str:
    """Clean function name by removing step prefixes"""
    # Remove step_XX_ pattern
    import re
    cleaned = re.sub(r'^step_\d+_', '', original_name)
    
    # Convert to title case with proper formatting
    # Replace underscores with spaces, capitalize properly
    words = cleaned.split('_')
    cleaned_words = []
    
    for word in words:
        if word.lower() in ['catia', 'uav', 'gsd']:
            cleaned_words.append(word.upper())
        elif word.lower() in ['app', 'db']:
            cleaned_words.append(word.lower())
        else:
            cleaned_words.append(word.capitalize())
    
    return '_'.join(cleaned_words)

def clean_function_description(original_description: str) -> str:
    """Clean function description by removing step prefixes"""
    if not original_description:
        return ""
    
    # Remove step patterns like "Step 1:", "PDF Step 2:", etc.
    import re
    cleaned = re.sub(r'^(PDF\s+)?Step\s+\d+:\s*', '', original_description.strip())
    
    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned

def determine_category(function_name: str, description: str) -> str:
    """Determine better category based on function name and description"""
    name_lower = function_name.lower()
    desc_lower = description.lower()
    
    # Initialize/Setup functions
    if any(keyword in name_lower for keyword in ['initialize', 'setup', 'start']):
        return "Initialisation"
    elif any(keyword in name_lower for keyword in ['define', 'reference', 'plane', 'axes']):
        return "Reference_Definition"
    elif any(keyword in name_lower for keyword in ['create', 'construct']) and any(keyword in name_lower for keyword in ['point', 'plane']):
        return "Construction_Geometry"
    elif any(keyword in name_lower for keyword in ['create', 'construct']) and any(keyword in name_lower for keyword in ['spline', 'line', 'curve']):
        return "Curve_Creation"
    elif any(keyword in name_lower for keyword in ['extrude', 'loft', 'surface']):
        return "Surface_Creation"
    elif any(keyword in name_lower for keyword in ['join', 'mirror', 'thickness']):
        return "Feature_Operations"
    elif any(keyword in name_lower for keyword in ['visibility', 'control', 'hide']):
        return "Display_Control"
    else:
        return "General"

def extract_functions_from_py_file(file_path: str) -> List[Dict[str, Any]]:
    """Extract function information from Python file"""
    functions = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip private functions and main execution
            if node.name.startswith('_') or node.name in ['create_flying_wing']:
                continue
            
            # Extract and clean docstring
            original_docstring = ast.get_docstring(node) or ""
            cleaned_description = clean_function_description(original_docstring)
            
            # Clean function name
            cleaned_name = clean_function_name(node.name)
            
            # Determine better category
            category = determine_category(cleaned_name, cleaned_description)
            
            function_info = {
                'name': cleaned_name,
                'original_name': node.name,  # Keep original for reference
                'description': cleaned_description,
                'category': category,
                'lineno': node.lineno,
                'parameters': [arg.arg for arg in node.args.args],
                'ast_node': node
            }
            functions.append(function_info)
    
    return functions

def extract_method_calls_from_function(func_ast_node: ast.FunctionDef) -> List[Dict[str, Any]]:
    """Extract method calls from a function's AST node"""
    method_calls = []
    step_order = 1
    
    class MethodCallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.calls = []
            self.step_counter = 1
        
        def visit_Call(self, node):
            # Extract method call information
            call_info = self.extract_call_info(node)
            if call_info:
                call_info['step_order'] = self.step_counter
                self.calls.append(call_info)
                self.step_counter += 1
            self.generic_visit(node)
        
        def visit_Assign(self, node):
            # Handle assignments - both method calls and property assignments
            if isinstance(node.value, ast.Call):
                # Assignment from method call (e.g., extrude1 = hybrid_shape_factory.add_new_extrude(...))
                call_info = self.extract_call_info(node.value)
                if call_info and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        call_info['assigned_to'] = target.id
                        call_info['step_order'] = self.step_counter
                        self.calls.append(call_info)
                        self.step_counter += 1
            elif isinstance(node.value, (ast.Constant, ast.Str)) and len(node.targets) == 1:
                # Property assignment (e.g., extrude1.name = "Extrude.1")
                target = node.targets[0]
                if isinstance(target, ast.Attribute):
                    method_name = target.attr
                    object_chain = self.get_object_chain(target.value)
                    value = self.get_arg_value(node.value)
                    
                    property_info = {
                        'method_name': method_name,
                        'object_chain': object_chain,
                        'args': [value],
                        'kwargs': {},
                        'method_call': f"{object_chain}.{method_name} = {value}",
                        'step_order': self.step_counter,
                        'is_property_assignment': True
                    }
                    self.calls.append(property_info)
                    self.step_counter += 1
            
            self.generic_visit(node)
        
        def extract_call_info(self, node: ast.Call) -> Dict[str, Any]:
            """Extract information from a method call"""
            if not isinstance(node, ast.Call):
                return None
            
            # Extract method name and object chain
            method_name = ""
            object_chain = ""
            
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                object_chain = self.get_object_chain(node.func.value)
            elif isinstance(node.func, ast.Name):
                method_name = node.func.id
                object_chain = ""
            
            # Skip if this looks like a built-in function or import
            if not object_chain and method_name in ['print', 'len', 'str', 'int', 'float', 'dict', 'list']:
                return None
            
            # Extract arguments
            args = []
            for arg in node.args:
                args.append(self.get_arg_value(arg))
            
            # Extract keyword arguments
            kwargs = {}
            for keyword in node.keywords:
                kwargs[keyword.arg] = self.get_arg_value(keyword.value)
            
            return {
                'method_name': method_name,
                'object_chain': object_chain,
                'args': args,
                'kwargs': kwargs,
                'method_call': self.reconstruct_call(method_name, object_chain, args, kwargs),
                'is_property_assignment': False
            }
        
        def get_object_chain(self, node) -> str:
            """Reconstruct the object chain for a method call"""
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self.get_object_chain(node.value)}.{node.attr}"
            elif isinstance(node, ast.Call):
                return f"{self.get_object_chain(node.func)}()"
            return str(node)
        
        def get_arg_value(self, node) -> str:
            """Get string representation of an argument"""
            if isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.Str):  # For older Python versions
                return repr(node.s)
            elif isinstance(node, ast.Num):  # For older Python versions
                return str(node.n)
            elif isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return self.get_object_chain(node)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return f"-{self.get_arg_value(node.operand)}"
            elif isinstance(node, ast.List):
                elements = [self.get_arg_value(el) for el in node.elts]
                return f"[{', '.join(elements)}]"
            elif isinstance(node, ast.BoolOp):
                return "BooleanExpression"
            try:
                return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
            except:
                return "ComplexExpression"
        
        def reconstruct_call(self, method_name: str, object_chain: str, args: List, kwargs: Dict) -> str:
            """Reconstruct the method call string"""
            call_str = f"{object_chain}.{method_name}" if object_chain else method_name
            
            arg_strs = [str(arg) for arg in args]
            kwarg_strs = [f"{k}={v}" for k, v in kwargs.items()]
            all_args = arg_strs + kwarg_strs
            
            return f"{call_str}({', '.join(all_args)})"
    
    visitor = MethodCallVisitor()
    visitor.visit(func_ast_node)
    
    # Remove consecutive duplicates but preserve order
    deduplicated_calls = []
    prev_call = None
    
    for call in visitor.calls:
        # Create a signature for comparison (ignore step_order)
        call_signature = (call['method_name'], call['object_chain'], call['method_call'])
        prev_signature = (prev_call['method_name'], prev_call['object_chain'], prev_call['method_call']) if prev_call else None
        
        if call_signature != prev_signature:
            # Re-number the step order after deduplication
            call['step_order'] = len(deduplicated_calls) + 1
            deduplicated_calls.append(call)
            prev_call = call
    
    return deduplicated_calls

def get_pycatia_method_info(method_name: str, pycatia_db_path: str) -> Dict[str, Any]:
    """Get method information from pycatia_methods.db"""
    conn = sqlite3.connect(pycatia_db_path)
    cursor = conn.cursor()
    
    # Search for method by name
    cursor.execute("""
        SELECT pm.id, pm.method_name, pm.full_method_name, pm.method_type, 
               pm.return_annotation, pm.parameter_count,
               mp.purpose
        FROM pycatia_methods pm
        LEFT JOIN method_purposes mp ON pm.id = mp.method_id
        WHERE pm.method_name = ? OR pm.full_method_name LIKE ?
        LIMIT 1
    """, (method_name, f"%{method_name}%"))
    
    result = cursor.fetchone()
    if result:
        method_id, name, full_name, method_type, return_annotation, param_count, purpose = result
        
        # Get parameters
        cursor.execute("""
            SELECT parameter_position, parameter_name, parameter_annotation, 
                   has_default, default_value_repr
            FROM method_parameters
            WHERE method_id = ?
            ORDER BY parameter_position
        """, (method_id,))
        
        parameters = cursor.fetchall()
        
        conn.close()
        return {
            'method_id': method_id,
            'method_name': name,
            'full_method_name': full_name,
            'method_type': method_type,
            'return_annotation': return_annotation,
            'parameter_count': param_count,
            'purpose': purpose,
            'parameters': parameters
        }
    
    conn.close()
    return None

def populate_functions_database():
    """Main function to populate the functions database"""
    
    # Paths - handle both running from FUNCTION_LIBRARY and parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    uav_wing_file = os.path.join(script_dir, "uav_wing_design_2.py")
    pycatia_db = os.path.join(os.path.dirname(script_dir), "pycatia_methods.db")
    functions_db = os.path.join(script_dir, "functions.db")
    
    # Check if source files exist
    if not os.path.exists(uav_wing_file):
        print(f"Error: {uav_wing_file} not found!")
        return False
    
    if not os.path.exists(pycatia_db):
        print(f"Error: {pycatia_db} not found!")
        return False
    
    if not os.path.exists(functions_db):
        print(f"Error: {functions_db} not found! Run functions_schema.py first.")
        return False
    
    print("Extracting functions from uav_wing_design_2.py...")
    functions = extract_functions_from_py_file(uav_wing_file)
    print(f"Found {len(functions)} functions")
    
    # Connect to functions database
    conn = sqlite3.connect(functions_db)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM parameters")
    cursor.execute("DELETE FROM function_methods")
    cursor.execute("DELETE FROM functions")
    conn.commit()
    
    print("Populating database...")
    
    for func_info in functions:
        print(f"Processing function: {func_info['name']}")
        
        # Insert function
        cursor.execute("""
            INSERT INTO functions (function_name, function_description, category)
            VALUES (?, ?, ?)
        """, (func_info['name'], func_info['description'], func_info['category']))
        
        function_id = cursor.lastrowid
        
        # Extract method calls from function
        method_calls = extract_method_calls_from_function(func_info['ast_node'])
        
        for method_call in method_calls:
            # Get additional info from pycatia database
            pycatia_info = get_pycatia_method_info(method_call['method_name'], pycatia_db)
            
            method_description = ""
            object_type = ""
            return_type = ""
            
            if pycatia_info:
                method_description = pycatia_info.get('purpose', '')[:500]  # Limit description length
                return_type = pycatia_info.get('return_annotation', '')
                object_type = pycatia_info.get('method_type', '')
            
            # Insert function method
            cursor.execute("""
                INSERT INTO function_methods (
                    function_ref, method_name, step_order, object_chain,
                    method_call, method_parameters, object_type, return_type, method_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                function_id,
                method_call['method_name'],
                method_call['step_order'],
                method_call['object_chain'],
                method_call['method_call'],
                str(method_call.get('args', [])),
                object_type,
                return_type,
                method_description
            ))
            
            method_id = cursor.lastrowid
            
            # Insert parameters
            if pycatia_info and pycatia_info['parameters']:
                for param_pos, param_name, param_annotation, has_default, default_value in pycatia_info['parameters']:
                    cursor.execute("""
                        INSERT INTO parameters (
                            method_ref, parameter_name, parameter_type, 
                            parameter_value, parameter_position, parameter_description
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        method_id,
                        param_name,
                        param_annotation or 'Unknown',
                        default_value if has_default else None,
                        param_pos,
                        f"Parameter for {method_call['method_name']}"
                    ))
    
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM functions")
    func_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM function_methods")
    method_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parameters")
    param_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\nDatabase population completed!")
    print(f"Functions inserted: {func_count}")
    print(f"Methods inserted: {method_count}")
    print(f"Parameters inserted: {param_count}")
    
    return True

def verify_population():
    """Verify the database was populated correctly"""
    functions_db = os.path.join("FUNCTION_LIBRARY", "functions.db")
    
    conn = sqlite3.connect(functions_db)
    cursor = conn.cursor()
    
    print("\nDatabase Contents Summary:")
    print("=" * 40)
    
    # Show functions
    cursor.execute("SELECT function_name, category FROM functions ORDER BY function_name")
    functions = cursor.fetchall()
    print(f"Functions ({len(functions)}):")
    for func_name, category in functions[:10]:  # Show first 10
        print(f"  - {func_name} [{category}]")
    if len(functions) > 10:
        print(f"  ... and {len(functions) - 10} more")
    
    # Show sample methods
    cursor.execute("""
        SELECT fm.method_name, fm.object_chain, f.function_name
        FROM function_methods fm
        JOIN functions f ON fm.function_ref = f.function_id
        ORDER BY fm.step_order
        LIMIT 10
    """)
    methods = cursor.fetchall()
    print(f"\nSample Methods ({len(methods)}):")
    for method_name, object_chain, func_name in methods:
        print(f"  - {object_chain}.{method_name} (from {func_name})")
    
    conn.close()

if __name__ == "__main__":
    print("Populating Function Library Database")
    print("=" * 50)
    
    if populate_functions_database():
        verify_population()
        print("\n✓ Database population successful!")
    else:
        print("\n✗ Database population failed!")