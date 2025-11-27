"""
Function Library Query Examples
Demonstrates how to query the function library database for automated code generation.
"""

import sqlite3
from typing import List, Dict, Any

class FunctionLibraryQuery:
    def __init__(self, db_path: str = "functions.db"):
        self.db_path = db_path
    
    def get_function_by_name(self, function_name: str) -> Dict[str, Any]:
        """Get complete function information including methods and parameters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get function info
        cursor.execute("""
            SELECT function_id, function_name, function_description, category, timestamp
            FROM functions 
            WHERE function_name = ?
        """, (function_name,))
        
        function_data = cursor.fetchone()
        if not function_data:
            conn.close()
            return None
        
        func_id, name, description, category, timestamp = function_data
        
        # Get methods for this function
        cursor.execute("""
            SELECT id, method_name, step_order, method_description, 
                   object_chain, method_call, object_type, return_type
            FROM function_methods 
            WHERE function_ref = ?
            ORDER BY step_order
        """, (func_id,))
        
        methods = []
        for method_data in cursor.fetchall():
            method_id, method_name, step_order, method_desc, object_chain, method_call, object_type, return_type = method_data
            
            # Get parameters for this method
            cursor.execute("""
                SELECT parameter_name, parameter_type, parameter_value, 
                       parameter_position, parameter_description
                FROM parameters
                WHERE method_ref = ?
                ORDER BY parameter_position
            """, (method_id,))
            
            parameters = [
                {
                    'name': param[0],
                    'type': param[1],
                    'value': param[2],
                    'position': param[3],
                    'description': param[4]
                } for param in cursor.fetchall()
            ]
            
            methods.append({
                'id': method_id,
                'name': method_name,
                'step_order': step_order,
                'description': method_desc,
                'object_chain': object_chain,
                'method_call': method_call,
                'object_type': object_type,
                'return_type': return_type,
                'parameters': parameters
            })
        
        conn.close()
        
        return {
            'function_id': func_id,
            'name': name,
            'description': description,
            'category': category,
            'timestamp': timestamp,
            'methods': methods
        }
    
    def get_functions_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get all functions in a specific category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT function_name, function_description
            FROM functions 
            WHERE category = ?
            ORDER BY function_name
        """, (category,))
        
        functions = [
            {'name': row[0], 'description': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return functions
    
    def get_methods_using_pycatia_method(self, pycatia_method: str) -> List[Dict[str, str]]:
        """Find all functions that use a specific PyCATIA method"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT f.function_name, fm.method_call, fm.step_order
            FROM functions f
            JOIN function_methods fm ON f.function_id = fm.function_ref
            WHERE fm.method_name = ?
            ORDER BY f.function_name, fm.step_order
        """, (pycatia_method,))
        
        results = [
            {
                'function_name': row[0],
                'method_call': row[1],
                'step_order': row[2]
            } for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
    
    def generate_function_code_template(self, function_name: str) -> str:
        """Generate a Python code template for a function"""
        function_data = self.get_function_by_name(function_name)
        if not function_data:
            return f"# Function '{function_name}' not found in database"
        
        code = f'def {function_data["name"]}():\n'
        code += f'    """{function_data["description"]}"""\n\n'
        
        for method in function_data['methods']:
            code += f'    # Step {method["step_order"]}: {method.get("description", method["name"])}\n'
            code += f'    # {method["method_call"]}\n'
            if method['parameters']:
                code += f'    # Parameters: {", ".join([p["name"] for p in method["parameters"]])}\n'
            code += '\n'
        
        return code

# Example usage and demonstrations
if __name__ == "__main__":
    query = FunctionLibraryQuery()
    
    print("Function Library Query Examples")
    print("=" * 50)
    
    # Example 1: Get a specific function
    print("1. Getting function details for 'Initialize_CATIA_app':")
    func_data = query.get_function_by_name("Initialize_CATIA_app")
    if func_data:
        print(f"   Function: {func_data['name']}")
        print(f"   Category: {func_data['category']}")
        print(f"   Methods: {len(func_data['methods'])}")
        for method in func_data['methods'][:3]:  # Show first 3 methods
            print(f"     - Step {method['step_order']}: {method['name']}")
    
    print()
    
    # Example 2: Get functions by category
    print("2. Functions in 'Initialisation' category:")
    step_functions = query.get_functions_by_category("Initialisation")
    for func in step_functions[:5]:  # Show first 5
        print(f"   - {func['name']}")
    print(f"   ... and {len(step_functions) - 5} more")
    
    print()
    
    # Example 3: Find functions using specific PyCATIA method
    print("3. Functions using 'add_new_point_coord' method:")
    method_usage = query.get_methods_using_pycatia_method("add_new_point_coord")
    for usage in method_usage:
        print(f"   - {usage['function_name']} (step {usage['step_order']})")
    
    print()
    
    # Example 4: Generate code template
    print("4. Code template for 'Create_Construction_Plane':")
    template = query.generate_function_code_template("Create_Construction_Plane")
    print(template)