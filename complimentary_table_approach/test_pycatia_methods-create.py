#!/usr/bin/env python3
"""
Advanced PyCATIA Methods Extractor for UAV Wing Design

This script performs sophisticated analysis of uav_wing_design.py using:
- AST (Abstract Syntax Tree) parsing for accurate code analysis
- Hierarchical object mapping to track PyCATIA object inheritance
- Variable/object chaining to follow method call chains
- Context preservation to understand method relationships
- Intelligent matching with pycatia_methods.db for full signatures

The analysis creates test_pycatia_methods.db with comprehensive method mapping
that agents can use to understand which PyCATIA methods are needed for each
step of the UAV wing design workflow.

Author: Generated for Advanced PyCATIA UAV Wing Design Analysis
Date: October 2025
"""

import sqlite3
import ast
import re
import os
import inspect
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, deque


class AdvancedPyCATIAMethodExtractor:
    """
    Advanced PyCATIA method extractor using AST analysis and hierarchical mapping
    """
    
    def __init__(self, source_file: str = "uav_wing_design.py", pycatia_db: str = "pycatia_methods.db"):
        self.source_file = source_file
        self.pycatia_db = pycatia_db
        self.methods_found = []
        
        # AST analysis structures
        self.variable_types = {}  # Track variable -> type mappings
        self.object_hierarchy = {}  # Track object inheritance chains
        self.method_calls = []  # Store all method calls with context
        self.function_contexts = {}  # Track function definitions and their contexts
        
        # Dynamic type discovery from PyCATIA database
        self.discovered_types = {}  # Will be populated from database
        self.method_signatures_by_name = {}  # Method name -> all possible signatures
        self.return_type_mappings = {}  # Method -> return type mappings from DB
        
        # LLM-powered type inference context
        self.semantic_context = {
            "factory_methods": [],  # Methods that create objects
            "attribute_accessors": [],  # Properties that return typed objects  
            "method_chains": [],  # Common method call patterns
            "type_relationships": {}  # Parent-child type relationships
        }
        
        # Load PyCATIA database for method matching
        self.pycatia_methods = self.load_pycatia_methods()
        
    def load_pycatia_methods(self) -> Dict[str, Dict]:
        """Load PyCATIA methods database and build intelligent semantic mappings"""
        if not os.path.exists(self.pycatia_db):
            print(f"⚠️ PyCATIA database {self.pycatia_db} not found. Using semantic inference only.")
            return {}
        
        methods_db = {}
        try:
            conn = sqlite3.connect(self.pycatia_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, method_name, full_method_name, method_type, 
                       method_parameters, return_annotation, parameter_count
                FROM pycatia_methods
                WHERE full_method_name IS NOT NULL AND full_method_name != ''
            """)
            
            for row in cursor.fetchall():
                method_id, method_name, full_method_name, method_type, params, return_type, param_count = row
                
                # Parse the full method name
                parts = full_method_name.split('.')
                if len(parts) >= 3:
                    module_path = '.'.join(parts[:-2])
                    class_name = parts[-2]
                    method_name_clean = parts[-1]
                    
                    # Store by class.method for precise matching
                    key = f"{class_name}.{method_name_clean}"
                    methods_db[key] = {
                        'id': method_id,
                        'method_name': method_name_clean,
                        'full_method_name': full_method_name,
                        'class_name': class_name,
                        'module_path': module_path,
                        'method_type': method_type,
                        'parameters': params,
                        'return_annotation': return_type,
                        'parameter_count': param_count
                    }
                    
                    # Build semantic indexes for intelligent matching
                    
                    # 1. Index by method name only (for fuzzy matching)
                    if method_name_clean not in self.method_signatures_by_name:
                        self.method_signatures_by_name[method_name_clean] = []
                    self.method_signatures_by_name[method_name_clean].append({
                        'full_signature': full_method_name,
                        'class_name': class_name,
                        'module_path': module_path,
                        'return_type': return_type
                    })
                    
                    # 2. Discover type relationships from return annotations
                    if return_type and return_type != 'None':
                        # Map method -> return type
                        self.return_type_mappings[f"{class_name}.{method_name_clean}"] = return_type
                        
                        # Discover what types this class can create
                        if method_name_clean.startswith('add_new_') or method_name_clean.startswith('create_'):
                            if class_name not in self.semantic_context["factory_methods"]:
                                self.semantic_context["factory_methods"].append(class_name)
                    
                    # 3. Build type discovery index
                    if class_name not in self.discovered_types:
                        self.discovered_types[class_name] = {
                            'full_class_path': f"{module_path}.{class_name}",
                            'methods': [],
                            'creates': [],  # What types this class can create
                            'attributes': []  # Attributes that return typed objects
                        }
                    
                    self.discovered_types[class_name]['methods'].append(method_name_clean)
                    
                    # 4. Identify factory patterns
                    if 'factory' in class_name.lower():
                        factory_creates = self._extract_created_type_from_method(method_name_clean)
                        if factory_creates:
                            self.discovered_types[class_name]['creates'].append(factory_creates)
            
            conn.close()
            
            # Build intelligent type relationship mappings
            self._build_semantic_relationships()
            
            print(f"✅ Loaded {len(methods_db)} PyCATIA methods from database")
            print(f"🧠 Discovered {len(self.discovered_types)} types with semantic relationships")
            print(f"🔍 Indexed {len(self.method_signatures_by_name)} unique method names for fuzzy matching")
            
        except Exception as e:
            print(f"⚠️ Error loading PyCATIA database: {e}")
            
        return methods_db
    
    def _extract_created_type_from_method(self, method_name: str) -> str:
        """Extract what type a factory method creates from its name"""
        if method_name.startswith('add_new_'):
            # add_new_spline -> Spline, add_new_point_coord -> Point
            type_part = method_name[8:]  # Remove 'add_new_'
            if '_' in type_part:
                base_type = type_part.split('_')[0]
            else:
                base_type = type_part
            
            # Capitalize first letter for class name
            return base_type.capitalize()
        
        return ""
    
    def _build_semantic_relationships(self):
        """Build semantic understanding of type relationships"""
        # Analyze patterns in the discovered types
        for class_name, info in self.discovered_types.items():
            full_path = info['full_class_path']
            
            # Extract module hierarchy for semantic understanding
            path_parts = full_path.split('.')
            if len(path_parts) >= 3:
                domain = path_parts[1]  # e.g., 'hybrid_shape_interfaces'
                
                # Group types by domain for semantic relationships
                if domain not in self.semantic_context["type_relationships"]:
                    self.semantic_context["type_relationships"][domain] = []
                
                self.semantic_context["type_relationships"][domain].append({
                    'class_name': class_name,
                    'full_path': full_path,
                    'creates': info.get('creates', [])
                })
        
        print(f"🎯 Built semantic relationships for {len(self.semantic_context['type_relationships'])} domains")
    
    class ASTMethodCallVisitor(ast.NodeVisitor):
        """AST visitor to extract method calls with full context"""
        
        def __init__(self, extractor):
            self.extractor = extractor
            self.current_function = None
            self.current_step = 0
            self.method_calls = []
            
        def visit_FunctionDef(self, node):
            """Visit function definitions to track context"""
            old_function = self.current_function
            old_step = self.current_step
            
            self.current_function = node.name
            
            # Extract step number if it's a step function
            step_match = re.match(r'step_(\d+)_(.+)', node.name)
            if step_match:
                self.current_step = int(step_match.group(1))
            else:
                self.current_step = 0
                
            # Store function context
            self.extractor.function_contexts[node.name] = {
                'step_number': self.current_step,
                'line_number': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'returns': []
            }
            
            self.generic_visit(node)
            
            self.current_function = old_function
            self.current_step = old_step
            
        def visit_Assign(self, node):
            """Visit assignments to track variable types and object creation"""
            if isinstance(node.value, ast.Call):
                # Handle assignment from method calls
                self._handle_assignment_call(node)
            elif isinstance(node.value, ast.Attribute):
                # Handle assignment from attribute access
                self._handle_assignment_attribute(node)
                
            self.generic_visit(node)
            
        def visit_Call(self, node):
            """Visit function/method calls"""
            if isinstance(node.func, ast.Attribute):
                # Method call: object.method()
                method_call_info = self._extract_method_call(node)
                if method_call_info:
                    self.method_calls.append(method_call_info)
            elif isinstance(node.func, ast.Name):
                # Function call: function()
                if node.func.id == 'catia':
                    # Special case for catia() function
                    method_call_info = {
                        'step_number': self.current_step,
                        'function_name': self.current_function or 'global_scope',
                        'object_chain': '',
                        'method_name': 'catia',
                        'full_call': self._reconstruct_call(node),
                        'line_number': node.lineno,
                        'arguments': self._extract_arguments(node),
                        'object_type': 'function',
                        'return_type': 'Application'
                    }
                    self.method_calls.append(method_call_info)
                    
            self.generic_visit(node)
            
        def _extract_method_call(self, node):
            """Extract detailed information about a method call"""
            if not isinstance(node.func, ast.Attribute):
                return None
                
            # Get the object chain
            object_chain = self._get_object_chain(node.func.value)
            method_name = node.func.attr
            
            # Get object type from our tracking
            object_type = self._infer_object_type(object_chain)
            
            # Extract arguments
            arguments = self._extract_arguments(node)
            
            # Reconstruct the full call
            full_call = self._reconstruct_call(node)
            
            return {
                'step_number': self.current_step,
                'function_name': self.current_function or 'global_scope',
                'object_chain': object_chain,
                'method_name': method_name,
                'full_call': full_call,
                'line_number': node.lineno,
                'arguments': arguments,
                'object_type': object_type,
                'return_type': None  # Will be inferred later
            }
            
        def _get_object_chain(self, node):
            """Recursively build object chain from AST node"""
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_object_chain(node.value)}.{node.attr}"
            elif isinstance(node, ast.Call):
                return self._reconstruct_call(node)
            else:
                return str(node)
                
        def _infer_object_type(self, object_chain):
            """Infer the type of an object from our tracking"""
            # Try direct lookup first
            if object_chain in self.extractor.variable_types:
                return self.extractor.variable_types[object_chain]
                
            # Try to infer from chain
            parts = object_chain.split('.')
            base_var = parts[0]
            
            if base_var in self.extractor.variable_types:
                base_type = self.extractor.variable_types[base_var]
                # For now, return the base type; could be enhanced with property mapping
                return base_type
                
            return "unknown"
            
        def _extract_arguments(self, node):
            """Extract arguments from a method call"""
            args = []
            for arg in node.args:
                if isinstance(arg, ast.Constant):
                    args.append(repr(arg.value))
                elif isinstance(arg, ast.Name):
                    args.append(arg.id)
                elif isinstance(arg, ast.Attribute):
                    args.append(self._get_object_chain(arg))
                else:
                    args.append(ast.unparse(arg) if hasattr(ast, 'unparse') else str(arg))
            return args
            
        def _reconstruct_call(self, node):
            """Reconstruct the full method call as string"""
            try:
                if hasattr(ast, 'unparse'):
                    return ast.unparse(node)
                else:
                    # Fallback for older Python versions
                    if isinstance(node.func, ast.Attribute):
                        obj_chain = self._get_object_chain(node.func.value)
                        method = node.func.attr
                        args_str = ", ".join(self._extract_arguments(node))
                        return f"{obj_chain}.{method}({args_str})"
                    elif isinstance(node.func, ast.Name):
                        args_str = ", ".join(self._extract_arguments(node))
                        return f"{node.func.id}({args_str})"
            except:
                return f"<method_call_line_{node.lineno}>"
                
        def _handle_assignment_call(self, node):
            """Handle variable assignment from method calls"""
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                
                if isinstance(node.value, ast.Call):
                    # Infer return type from method call
                    if isinstance(node.value.func, ast.Attribute):
                        method_name = node.value.func.attr
                        object_chain = self._get_object_chain(node.value.func.value)
                        object_type = self._infer_object_type(object_chain)
                        
                        # Map known method return types
                        return_type = self._map_return_type(object_type, method_name)
                        self.extractor.variable_types[var_name] = return_type
                    elif isinstance(node.value.func, ast.Name):
                        if node.value.func.id == 'catia':
                            self.extractor.variable_types[var_name] = 'Application'
                            
        def _handle_assignment_attribute(self, node):
            """Handle variable assignment from attribute access"""
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                
                if isinstance(node.value, ast.Attribute):
                    object_chain = self._get_object_chain(node.value.value)
                    attr_name = node.value.attr
                    object_type = self._infer_object_type(object_chain)
                    
                    # Map known attribute types
                    attr_type = self._map_attribute_type(object_type, attr_name)
                    self.extractor.variable_types[var_name] = attr_type
                    
        def _map_return_type(self, object_type, method_name):
            """Intelligent return type mapping using database knowledge"""
            # First, try to get from database mappings
            lookup_key = f"{object_type}.{method_name}"
            if lookup_key in self.extractor.return_type_mappings:
                return self.extractor.return_type_mappings[lookup_key]
            
            # Semantic inference for factory methods
            if method_name.startswith('add_new_'):
                created_type = self.extractor._extract_created_type_from_method(method_name)
                if created_type:
                    # Look for the most likely full class name
                    for class_name in self.extractor.discovered_types:
                        if created_type.lower() in class_name.lower():
                            return class_name
                    return created_type
            
            # Attribute access patterns
            attribute_patterns = {
                'documents': 'Documents',
                'part': 'Part', 
                'hybrid_shape_factory': 'HybridShapeFactory',
                'shape_factory': 'ShapeFactory',
                'hybrid_bodies': 'HybridBodies',
                'origin_elements': 'OriginElements',
                'selection': 'Selection'
            }
            
            if method_name in attribute_patterns:
                return attribute_patterns[method_name]
            
            # Default to intelligent guess based on method name
            return self._infer_type_from_method_name(method_name)
            
        def _map_attribute_type(self, object_type, attr_name):
            """Intelligent attribute type mapping using semantic understanding"""
            # Try database first
            for class_name, info in self.extractor.discovered_types.items():
                if object_type == class_name:
                    # Check if this attribute is known to return a specific type
                    if attr_name in info.get('attributes', []):
                        return info['attributes'][attr_name]
            
            # Semantic patterns for common attributes
            semantic_patterns = {
                'documents': 'Documents',
                'active_document': 'Document', 
                'part': 'Part',
                'selection': 'Selection',
                'hybrid_shape_factory': 'HybridShapeFactory',
                'shape_factory': 'ShapeFactory',
                'hybrid_bodies': 'HybridBodies',
                'origin_elements': 'OriginElements',
                'plane_xy': 'Plane',
                'plane_yz': 'Plane', 
                'plane_zx': 'Plane',
                'hybrid_shapes': 'HybridShapes',
                'vis_properties': 'VisPropertySet'
            }
            
            if attr_name in semantic_patterns:
                return semantic_patterns[attr_name]
            
            # Try to infer from attribute name
            return self._infer_type_from_attribute_name(attr_name)
        
        def _infer_type_from_method_name(self, method_name):
            """Infer likely return type from method name semantics"""
            if 'create' in method_name or 'add_new' in method_name:
                # Extract what's being created
                if 'reference' in method_name:
                    return 'Reference'
                elif 'point' in method_name:
                    return 'Point'
                elif 'line' in method_name:
                    return 'Line'
                elif 'plane' in method_name:
                    return 'Plane'
                elif 'spline' in method_name:
                    return 'Spline'
            
            return 'unknown'
        
        def _infer_type_from_attribute_name(self, attr_name):
            """Infer type from attribute name patterns"""
            if 'factory' in attr_name:
                return attr_name.replace('_', '').title()
            elif 'plane' in attr_name:
                return 'Plane'
            elif 'point' in attr_name:
                return 'Point'
            elif 'bodies' in attr_name:
                return attr_name.replace('_', '').title()
            
            return 'unknown'
    
    def parse_source_file(self):
        """Parse source file using AST and extract method calls"""
        if not os.path.exists(self.source_file):
            raise FileNotFoundError(f"Source file {self.source_file} not found")
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"❌ Syntax error in {self.source_file}: {e}")
            return []
        
        # Visit the AST and extract method calls
        visitor = self.ASTMethodCallVisitor(self)
        visitor.visit(tree)
        
        return visitor.method_calls
    
    def match_with_pycatia_database(self, method_calls):
        """Intelligent semantic matching with PyCATIA database using LLM-like reasoning"""
        matched_methods = []
        
        for call in method_calls:
            object_type = call.get('object_type', 'unknown')
            method_name = call.get('method_name', '')
            object_chain = call.get('object_chain', '')
            
            # Multi-stage intelligent matching
            matched_signature, matched_method_id, return_annotation = self._intelligent_method_matching(
                object_type, method_name, object_chain, call
            )
            
            # Create enhanced method call record
            enhanced_call = call.copy()
            enhanced_call.update({
                'matched_full_signature': matched_signature,
                'matched_method_id': matched_method_id,
                'return_annotation': return_annotation,
                'method_parameters': ', '.join(call.get('arguments', []))
            })
            
            matched_methods.append(enhanced_call)
        
        return matched_methods
    
    def _intelligent_method_matching(self, object_type, method_name, object_chain, call_context):
        """
        LLM-like intelligent method matching using semantic reasoning
        """
        # Stage 1: Direct exact match
        lookup_key = f"{object_type}.{method_name}"
        if lookup_key in self.pycatia_methods:
            method_info = self.pycatia_methods[lookup_key]
            return method_info['full_method_name'], method_info['id'], method_info['return_annotation']
        
        # Stage 2: Semantic method name search across all signatures
        if method_name in self.method_signatures_by_name:
            candidates = self.method_signatures_by_name[method_name]
            
            # Use semantic scoring to find best match
            best_match = self._score_method_candidates(candidates, object_type, object_chain, call_context)
            if best_match:
                # Get full method info
                key = f"{best_match['class_name']}.{method_name}"
                if key in self.pycatia_methods:
                    method_info = self.pycatia_methods[key]
                    return method_info['full_method_name'], method_info['id'], method_info['return_annotation']
        
        # Stage 3: Fuzzy semantic matching based on context
        semantic_match = self._semantic_context_matching(object_type, method_name, object_chain, call_context)
        if semantic_match:
            return semantic_match
        
        # Stage 4: Pattern-based inference for unmatched methods
        inferred_match = self._pattern_based_inference(object_type, method_name, object_chain)
        if inferred_match:
            return inferred_match
        
        return "", None, None
    
    def _score_method_candidates(self, candidates, object_type, object_chain, call_context):
        """Score method candidates using semantic similarity"""
        if not candidates:
            return None
        
        scored_candidates = []
        
        for candidate in candidates:
            score = 0
            class_name = candidate['class_name']
            module_path = candidate['module_path']
            
            # Scoring factors:
            
            # 1. Exact object type match
            if object_type == class_name:
                score += 100
            
            # 2. Semantic similarity in naming
            if object_type.lower() in class_name.lower() or class_name.lower() in object_type.lower():
                score += 50
            
            # 3. Module domain relevance
            if 'hybrid_shape' in module_path and any(word in object_chain.lower() for word in ['hybrid', 'shape', 'factory']):
                score += 30
            
            # 4. Method context relevance (if it's a factory method creating the right type)
            step_number = call_context.get('step_number', 0)
            if step_number > 0:
                # Early steps (1-10) likely use basic factories
                if step_number <= 10 and 'factory' in class_name.lower():
                    score += 20
                # Later steps (20+) might use specialized classes
                elif step_number >= 20 and 'factory' not in class_name.lower():
                    score += 10
            
            # 5. Return type coherence (does the return type make sense for this method?)
            return_type = candidate.get('return_type', '')
            if return_type and self._return_type_makes_sense(call_context, return_type):
                score += 15
            
            scored_candidates.append((score, candidate))
        
        # Return the highest scoring candidate
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            return scored_candidates[0][1]
        
        return None
    
    def _semantic_context_matching(self, object_type, method_name, object_chain, call_context):
        """Use semantic context to infer the correct method signature"""
        # Look for patterns in the object chain and context
        
        # Pattern 1: Variable name hints
        # e.g., spline1.add_point -> likely HybridShapeSpline, not just Spline
        if object_chain:
            base_var = object_chain.split('.')[0]
            
            # Common variable naming patterns that hint at types
            type_hints = {
                'spline': ['HybridShapeSpline', 'Spline'],
                'loft': ['Loft', 'HybridShapeLoft'],
                'extrude': ['Extrude', 'HybridShapeExtrude'],
                'join': ['Join', 'HybridShapeJoin'],
                'plane': ['Plane', 'HybridShapePlane'],
                'point': ['Point', 'HybridShapePoint'],
                'line': ['Line', 'HybridShapeLine']
            }
            
            for hint, possible_types in type_hints.items():
                if hint in base_var.lower():
                    for possible_type in possible_types:
                        candidate_key = f"{possible_type}.{method_name}"
                        if candidate_key in self.pycatia_methods:
                            method_info = self.pycatia_methods[candidate_key]
                            return method_info['full_method_name'], method_info['id'], method_info['return_annotation']
        
        # Pattern 2: Context-based inference
        step_number = call_context.get('step_number', 0)
        function_name = call_context.get('function_name', '')
        
        # Analyze function context for hints
        if 'spline' in function_name and method_name in ['add_point', 'add_point_with_constraint_from_curve']:
            # This is likely a spline operation - try HybridShapeSpline first
            for spline_type in ['HybridShapeSpline', 'Spline']:
                candidate_key = f"{spline_type}.{method_name}"
                if candidate_key in self.pycatia_methods:
                    method_info = self.pycatia_methods[candidate_key]
                    return method_info['full_method_name'], method_info['id'], method_info['return_annotation']
        
        return None
    
    def _pattern_based_inference(self, object_type, method_name, object_chain):
        """Last resort: use pattern-based inference to guess the method signature"""
        
        # Common PyCATIA patterns
        patterns = [
            # HybridShape* classes for geometry operations
            f"pycatia.hybrid_shape_interfaces.hybrid_shape_{object_type.lower()}.HybridShape{object_type}.{method_name}",
            f"pycatia.hybrid_shape_interfaces.{object_type.lower()}.{object_type}.{method_name}",
            
            # Interface patterns
            f"pycatia.in_interfaces.{object_type.lower()}.{object_type}.{method_name}",
            
            # Mec mod interfaces  
            f"pycatia.mec_mod_interfaces.{object_type.lower()}.{object_type}.{method_name}",
        ]
        
        # Check if any of these patterns exist in our database
        for pattern in patterns:
            for key, method_info in self.pycatia_methods.items():
                if method_info['full_method_name'] == pattern:
                    return method_info['full_method_name'], method_info['id'], method_info['return_annotation']
        
        return None
    
    def _return_type_makes_sense(self, call_context, return_type):
        """Check if a return type makes sense in the given context"""
        # Simple heuristic: if the next line uses the returned object,
        # the type should be consistent
        # This could be enhanced with more sophisticated analysis
        return True  # For now, accept all return types
    
    def create_database(self, db_path: str = "test_pycatia_methods.db"):
        """Create SQLite database with extracted methods using advanced AST analysis"""
        
        # Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ Removed existing {db_path}")
        
        # Parse source file with AST
        print(f"� Performing advanced AST analysis of {self.source_file}...")
        method_calls = self.parse_source_file()
        
        if not method_calls:
            print("⚠️ No method calls found in source file")
            return
        
        print(f"✅ Found {len(method_calls)} method calls via AST analysis")
        
        # Match with PyCATIA database
        print(f"🔗 Matching with PyCATIA methods database...")
        matched_methods = self.match_with_pycatia_database(method_calls)
        
        # Create database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Create enhanced table with additional AST analysis fields
            cursor.execute('''
                CREATE TABLE final_steps_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_number INTEGER,
                    function_name TEXT,
                    object_chain TEXT,
                    method_name TEXT,
                    full_call TEXT,
                    line_number INTEGER,
                    matched_full_signature TEXT,
                    matched_method_id INTEGER,
                    method_parameters TEXT,
                    return_annotation TEXT,
                    object_type TEXT,
                    arguments_list TEXT,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert methods with enhanced information
            for method in matched_methods:
                cursor.execute('''
                    INSERT INTO final_steps_methods 
                    (step_number, function_name, object_chain, method_name, full_call, 
                     line_number, matched_full_signature, matched_method_id,
                     method_parameters, return_annotation, object_type, arguments_list)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    method.get('step_number', 0),
                    method.get('function_name', ''),
                    method.get('object_chain', ''),
                    method.get('method_name', ''),
                    method.get('full_call', ''),
                    method.get('line_number', 0),
                    method.get('matched_full_signature', ''),
                    method.get('matched_method_id'),
                    method.get('method_parameters', ''),
                    method.get('return_annotation'),
                    method.get('object_type', ''),
                    str(method.get('arguments', []))
                ))
            
            conn.commit()
            
            # Enhanced Verification
            cursor.execute("SELECT COUNT(*) FROM final_steps_methods")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT matched_full_signature) FROM final_steps_methods WHERE matched_full_signature != ''")
            unique_signatures = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM final_steps_methods WHERE matched_method_id IS NOT NULL")
            db_matched_count = cursor.fetchone()[0]
            
            print(f"✅ Created enhanced database: {db_path}")
            print(f"📊 Total method calls: {total_count}")
            print(f"🎯 Unique PyCATIA signatures: {unique_signatures}")
            print(f"🔗 Database matched: {db_matched_count} ({db_matched_count/total_count*100:.1f}%)")
            
            # Show step-by-step analysis
            cursor.execute("""
                SELECT step_number, COUNT(*) as method_count,
                       COUNT(CASE WHEN matched_full_signature != '' THEN 1 END) as matched_count
                FROM final_steps_methods 
                WHERE step_number > 0 
                GROUP BY step_number 
                ORDER BY step_number
            """)
            
            step_analysis = cursor.fetchall()
            if step_analysis:
                print(f"\n📊 Step-by-step method analysis:")
                for step, total, matched in step_analysis:
                    match_rate = matched/total*100 if total > 0 else 0
                    print(f"  Step {step:2d}: {total:2d} methods, {matched:2d} matched ({match_rate:.0f}%)")
            
            # Show sample of extracted methods with object types
            cursor.execute("""
                SELECT DISTINCT object_type, method_name, matched_full_signature 
                FROM final_steps_methods 
                WHERE matched_full_signature != '' 
                ORDER BY object_type, method_name 
                LIMIT 15
            """)
            
            sample_methods = cursor.fetchall()
            if sample_methods:
                print(f"\n📋 Sample matched methods with object types:")
                for obj_type, method_name, signature in sample_methods:
                    print(f"  {obj_type}.{method_name} → {signature}")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            conn.close()
    
    def verify_database(self, db_path: str = "test_pycatia_methods.db"):
        """Verify the created database contains expected data"""
        if not os.path.exists(db_path):
            print(f"❌ Database {db_path} not found")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            print(f"\n🔍 Verifying database: {db_path}")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(final_steps_methods)")
            columns = cursor.fetchall()
            print(f"📊 Table structure: {len(columns)} columns")
            
            # Check data distribution
            cursor.execute("SELECT COUNT(*) FROM final_steps_methods")
            total_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM final_steps_methods WHERE matched_full_signature != ''")
            matched_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT step_number) FROM final_steps_methods WHERE step_number > 0")
            unique_steps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT function_name) FROM final_steps_methods")
            unique_functions = cursor.fetchone()[0]
            
            print(f"📈 Data verification:")
            print(f"  Total rows: {total_rows}")
            print(f"  Matched signatures: {matched_rows}")
            print(f"  Unique steps: {unique_steps}")
            print(f"  Unique functions: {unique_functions}")
            print(f"  Match rate: {matched_rows/total_rows*100:.1f}%")
            
            # Show step distribution
            cursor.execute("""
                SELECT step_number, COUNT(*) as method_count 
                FROM final_steps_methods 
                WHERE step_number > 0 
                GROUP BY step_number 
                ORDER BY step_number 
                LIMIT 10
            """)
            
            step_distribution = cursor.fetchall()
            if step_distribution:
                print(f"\n📊 Methods per step (first 10):")
                for step, count in step_distribution:
                    print(f"  Step {step}: {count} methods")
            
        except Exception as e:
            print(f"❌ Error verifying database: {e}")
        
        finally:
            conn.close()


def main():
    """Main execution function"""
    print("🎯 Advanced PyCATIA Methods Extractor for UAV Wing Design")
    print("=" * 70)
    print("🔬 Using AST analysis, hierarchical mapping & database integration")
    
    # Check if source file exists
    source_file = "uav_wing_design.py"
    if not os.path.exists(source_file):
        print(f"❌ Source file {source_file} not found")
        print("Please ensure uav_wing_design.py is in the current directory")
        return
    
    # Check if PyCATIA database exists
    pycatia_db = "pycatia_methods.db"
    if not os.path.exists(pycatia_db):
        print(f"⚠️  PyCATIA database {pycatia_db} not found")
        print("   Analysis will use built-in type mappings only")
        print("   For best results, ensure pycatia_methods.db is available")
    
    # Create advanced extractor and process file
    extractor = AdvancedPyCATIAMethodExtractor(source_file, pycatia_db)
    
    # Create database with advanced analysis
    db_path = "test_pycatia_methods.db"
    extractor.create_database(db_path)
    
    # Verify results
    extractor.verify_database(db_path)
    
    print("\n🎉 Advanced PyCATIA method extraction complete!")
    print(f"📁 Enhanced database created: {db_path}")
    print("🔗 This database contains:")
    print("   • Hierarchical object type mapping")
    print("   • AST-based context preservation") 
    print("   • Intelligent PyCATIA database matching")
    print("   • Step-by-step workflow method cataloging")
    print("🚀 Ready for agent-based code generation!")


if __name__ == "__main__":
    main()
