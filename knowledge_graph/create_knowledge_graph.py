#!/usr/bin/env python3
"""
PyCATIA Live Knowledge Graph Creator

This script creates the knowledge graph JSON from the live PyCATIA library
by inspecting the installed PyCATIA module using Python's inspect capabilities.

This replaces the missing direct_pycatia_inspector.py script.
"""

import inspect
import json
import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Any, List
import sys
import warnings

# Suppress warnings during module inspection
warnings.filterwarnings('ignore')


def discover_pycatia_modules():
    """Discover all PyCATIA submodules"""
    
    print("🔍 Discovering PyCATIA modules...")
    
    try:
        import pycatia
    except ImportError:
        print("❌ PyCATIA not installed. Please install PyCATIA first.")
        return []
    
    modules = []
    
    # Walk through pycatia package
    for importer, modname, ispkg in pkgutil.walk_packages(
        pycatia.__path__, 
        pycatia.__name__ + "."
    ):
        modules.append(modname)
    
    print(f"📦 Found {len(modules)} PyCATIA modules")
    return modules


def inspect_class(cls, module_path: str) -> Dict[str, Any]:
    """Inspect a single class and extract its information"""
    
    class_info = {
        'full_name': f"{module_path}.{cls.__name__}",
        'module_path': module_path,
        'class_name': cls.__name__,
        'parent_classes': [base.__name__ for base in cls.__bases__ if base.__name__ != 'object'],
        'methods': {},
        'properties': {},
        'class_methods': [],
        'static_methods': [],
        'domain': module_path.split('.')[1] if len(module_path.split('.')) > 1 else 'unknown',
        'docstring': inspect.getdoc(cls) or '',
        'is_abstract': inspect.isabstract(cls),
        'is_factory': 'Factory' in cls.__name__,
        'is_collection': any(name in cls.__name__.lower() for name in ['collection', 'list', 'set']),
        'mro': [base.__name__ for base in cls.__mro__[1:]]  # Skip self
    }
    
    # Inspect methods and properties
    for name, member in inspect.getmembers(cls):
        if name.startswith('_'):
            continue
            
        try:
            if inspect.ismethod(member) or inspect.isfunction(member):
                full_method_name = f"{module_path}.{cls.__name__}.{name}"
                class_info['methods'][name] = full_method_name
                
                if isinstance(member, classmethod):
                    class_info['class_methods'].append(name)
                elif isinstance(member, staticmethod):
                    class_info['static_methods'].append(name)
                    
            elif inspect.isdatadescriptor(member):
                # Property
                prop_type = str(type(member).__name__)
                if hasattr(member, 'fget') and member.fget:
                    if hasattr(member.fget, '__annotations__'):
                        return_annotation = member.fget.__annotations__.get('return')
                        if return_annotation:
                            prop_type = str(return_annotation)
                
                class_info['properties'][name] = prop_type
                
        except Exception:
            # Skip problematic members
            continue
    
    return class_info


def create_live_knowledge_graph():
    """Create knowledge graph from live PyCATIA inspection"""
    
    print("🧠 Creating Live PyCATIA Knowledge Graph")
    print("=" * 50)
    
    # Discover modules
    modules = discover_pycatia_modules()
    if not modules:
        return None
    
    knowledge_graph = {
        'classes': {},
        'creation_info': {
            'method': 'live_library_inspection',
            'modules_inspected': len(modules),
            'timestamp': '2025-10-07'
        }
    }
    
    total_classes = 0
    total_methods = 0
    
    print("🔍 Inspecting classes...")
    
    for i, module_name in enumerate(modules):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(modules)} modules...")
        
        try:
            # Import module
            module = importlib.import_module(module_name)
            
            # Find classes in module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name:  # Only classes defined in this module
                    
                    class_info = inspect_class(obj, module_name)
                    knowledge_graph['classes'][name] = class_info
                    
                    total_classes += 1
                    total_methods += len(class_info['methods'])
                    
        except Exception as e:
            # Skip problematic modules
            continue
    
    # Add summary
    knowledge_graph['creation_info']['classes_found'] = total_classes
    knowledge_graph['creation_info']['methods_found'] = total_methods
    
    print(f"📊 Inspection Complete:")
    print(f"  📋 Classes: {total_classes}")
    print(f"  🔧 Methods: {total_methods}")
    print(f"  📦 Modules: {len(modules)}")
    
    return knowledge_graph


def save_knowledge_graph(kg_data: Dict[str, Any], output_file: str = 'knowledge_graph/pycatia_knowledge_graph.json'):
    """Save knowledge graph to JSON file"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(kg_data, f, indent=2, default=str)
    
    print(f"💾 Knowledge graph saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print("🚀 PyCATIA Live Knowledge Graph Creator")
    print("=" * 50)
    
    try:
        # Create knowledge graph
        kg_data = create_live_knowledge_graph()
        
        if kg_data:
            # Save to file
            output_file = save_knowledge_graph(kg_data)
            
            print(f"\n✅ Live knowledge graph created successfully!")
            print(f"📁 File: {output_file}")
            print(f"📊 Statistics:")
            print(f"  📋 Classes: {kg_data['creation_info']['classes_found']}")
            print(f"  🔧 Methods: {kg_data['creation_info']['methods_found']}")
            print(f"  📦 Modules: {kg_data['creation_info']['modules_inspected']}")
            
        else:
            print("❌ Failed to create knowledge graph")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()