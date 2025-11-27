"""
Function Analysis and Merging Utility
Analyzes functions to identify duplicates and creates generic templates
"""

import sqlite3
import re
from collections import defaultdict
from typing import Dict, List, Tuple

def analyze_function_similarity(db_path: str = "functions.db"):
    """Analyze functions to find similar ones that can be merged"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all functions with their methods
    cursor.execute("""
        SELECT 
            f.function_id,
            f.function_name,
            f.function_description,
            f.category,
            fm.method_name,
            fm.step_order,
            fm.object_chain,
            fm.method_call
        FROM functions f
        JOIN function_methods fm ON f.function_id = fm.function_ref
        ORDER BY f.function_id, fm.step_order
    """)
    
    results = cursor.fetchall()
    
    # Group by function
    functions = defaultdict(list)
    function_info = {}
    
    for row in results:
        func_id, func_name, func_desc, category, method_name, step_order, object_chain, method_call = row
        
        if func_id not in function_info:
            function_info[func_id] = {
                'name': func_name,
                'description': func_desc,
                'category': category
            }
        
        functions[func_id].append({
            'method_name': method_name,
            'step_order': step_order,
            'object_chain': object_chain,
            'method_call': method_call
        })
    
    # Create method signatures for comparison
    function_signatures = {}
    for func_id, methods in functions.items():
        # Create a signature based on method sequence (ignoring parameters)
        signature = []
        for method in methods:
            # Extract just the method structure, ignore specific parameters
            generic_call = generalize_method_call(method['method_call'])
            signature.append(f"{method['object_chain']}.{method['method_name']}")
        
        function_signatures[func_id] = tuple(signature)
    
    # Find functions with identical signatures
    signature_groups = defaultdict(list)
    for func_id, signature in function_signatures.items():
        signature_groups[signature].append(func_id)
    
    # Identify duplicates
    duplicates = []
    for signature, func_ids in signature_groups.items():
        if len(func_ids) > 1:
            duplicate_group = []
            for func_id in func_ids:
                duplicate_group.append({
                    'id': func_id,
                    'name': function_info[func_id]['name'],
                    'description': function_info[func_id]['description'],
                    'category': function_info[func_id]['category']
                })
            duplicates.append({
                'signature': signature,
                'functions': duplicate_group,
                'method_count': len(signature)
            })
    
    conn.close()
    return duplicates

def generalize_method_call(method_call: str) -> str:
    """Convert specific method call to generic template"""
    
    # Extract method name and object chain
    if '(' in method_call:
        method_part, params_part = method_call.split('(', 1)
        params_part = params_part.rstrip(')')
        
        # Count parameters
        if params_part.strip():
            # Simple parameter counting (not perfect but good enough)
            param_count = len([p.strip() for p in params_part.split(',') if p.strip()])
            generic_params = ', '.join([f'param{i+1}' for i in range(param_count)])
        else:
            generic_params = ''
        
        return f"{method_part}({generic_params})"
    
    return method_call

def get_pycatia_method_signature(method_name: str, pycatia_db_path: str = "../pycatia_methods.db") -> Dict:
    """Get the proper method signature from pycatia database"""
    
    try:
        conn = sqlite3.connect(pycatia_db_path)
        cursor = conn.cursor()
        
        # Get method info
        cursor.execute("""
            SELECT pm.id, pm.method_name, pm.full_method_name, pm.method_type,
                   pm.return_annotation, pm.parameter_count
            FROM pycatia_methods pm
            WHERE pm.method_name = ?
            LIMIT 1
        """, (method_name,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        method_id, name, full_name, method_type, return_annotation, param_count = result
        
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
            'method_name': name,
            'full_method_name': full_name,
            'method_type': method_type,
            'return_annotation': return_annotation,
            'parameter_count': param_count,
            'parameters': parameters
        }
    
    except Exception as e:
        print(f"Error getting method signature for {method_name}: {e}")
        return None

def create_generic_function_template(duplicate_group: Dict) -> Dict:
    """Create a generic template from a group of duplicate functions"""
    
    functions = duplicate_group['functions']
    
    # Find common elements
    categories = set(f['category'] for f in functions)
    descriptions = [f['description'] for f in functions]
    
    # Create generic name by finding common parts
    names = [f['name'] for f in functions]
    generic_name = find_common_pattern(names)
    
    # Use most common category
    common_category = max(categories, key=lambda x: sum(1 for f in functions if f['category'] == x))
    
    # Create generic description
    generic_description = create_generic_description(descriptions)
    
    return {
        'generic_name': generic_name,
        'generic_description': generic_description,
        'category': common_category,
        'original_functions': [f['name'] for f in functions],
        'method_signature': duplicate_group['signature']
    }

def find_common_pattern(names: List[str]) -> str:
    """Find common pattern in function names"""
    
    # Remove numbers and common suffixes
    patterns = []
    for name in names:
        # Remove trailing numbers/digits
        clean_name = re.sub(r'\d+$', '', name)
        # Remove common suffixes
        clean_name = re.sub(r'_[34]$', '', clean_name)
        patterns.append(clean_name)
    
    # Find most common pattern
    from collections import Counter
    pattern_counts = Counter(patterns)
    return pattern_counts.most_common(1)[0][0] if pattern_counts else "Generic_Function"

def create_generic_description(descriptions: List[str]) -> str:
    """Create generic description from multiple descriptions"""
    
    # Find common words and create generic description
    if not descriptions:
        return "Generic function description"
    
    # Use the first non-empty description as base and make it generic
    base_desc = next((desc for desc in descriptions if desc.strip()), "Generic function")
    
    # Remove specific references
    generic_desc = re.sub(r'\d+', 'N', base_desc)  # Replace numbers with N
    generic_desc = re.sub(r'specific|particular', 'generic', generic_desc, flags=re.IGNORECASE)
    
    return generic_desc

def analyze_and_report():
    """Main analysis function"""
    
    print("Function Similarity Analysis")
    print("=" * 50)
    
    duplicates = analyze_function_similarity()
    
    if not duplicates:
        print("No duplicate functions found.")
        return
    
    print(f"Found {len(duplicates)} groups of similar functions:")
    
    generic_templates = []
    
    for i, group in enumerate(duplicates, 1):
        print(f"\n{i}. Group with {len(group['functions'])} similar functions:")
        print(f"   Method sequence: {' → '.join(group['signature'])}")
        
        for func in group['functions']:
            print(f"   • {func['name']} - {func['description'][:50]}...")
        
        # Create generic template
        template = create_generic_function_template(group)
        generic_templates.append(template)
        
        print(f"   → Suggested generic name: {template['generic_name']}")
        print(f"   → Generic description: {template['generic_description'][:50]}...")
    
    print(f"\n📊 Summary:")
    print(f"   • {len(duplicates)} duplicate groups found")
    print(f"   • {sum(len(g['functions']) for g in duplicates)} functions can be merged")
    print(f"   • {len(generic_templates)} generic templates created")
    
    return generic_templates

if __name__ == "__main__":
    templates = analyze_and_report()