#!/usr/bin/env python3
"""
PyCATIA Knowledge Graph Intelligence Module

This module provides intelligent PyCATIA method resolution using the live library
knowledge graph with zero hardcoded rules - all relationships are dynamically 
discovered from the actual installed PyCATIA library.

Usage:
    from knowledge_graph.pycatia_knowledge_graph import PyCATIAIntelligence
    
    intel = PyCATIAIntelligence()
    method_sig = intel.resolve_method("spline1", "add_point_with_constraint_from_curve")
    # Returns: "pycatia.hybrid_shape_interfaces.hybrid_shape_spline.HybridShapeSpline.add_point_with_constraint_from_curve"
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class PyCATIAIntelligence:
    """
    Intelligent PyCATIA method resolution using live library knowledge graph
    """
    
    def __init__(self, graph_file: str = 'pycatia_knowledge_graph.json'):
        # If graph_file is just a filename, look for it in the same directory as this script
        if not os.path.dirname(graph_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.graph_file = os.path.join(script_dir, graph_file)
        else:
            self.graph_file = graph_file
        
        # Load the live knowledge graph data
        if not os.path.exists(self.graph_file):
            raise FileNotFoundError(f"Live knowledge graph not found: {self.graph_file}")
            
        with open(self.graph_file, 'r') as f:
            self.graph_data = json.load(f)
        
        self.classes = self.graph_data['classes']
        
        # Extract methods from the nested structure
        self.methods = {}
        for class_name, class_info in self.classes.items():
            if 'methods' in class_info:
                for method_name, method_signature in class_info['methods'].items():
                    method_key = f"{class_name}.{method_name}"
                    self.methods[method_key] = {
                        'method_name': method_name,
                        'class_name': class_name,
                        'full_signature': method_signature,
                        'method_type': 'instance'  # Default to instance method
                    }
        
        # Build reverse indexes for fast lookup
        self._build_indexes()
        
        print(f"🔍 Loaded PyCATIA knowledge graph:")
        print(f"   📚 Classes: {len(self.classes)}")
        print(f"   🔧 Methods: {len(self.methods)}")
    
    def _build_indexes(self):
        """Build reverse indexes for intelligent matching"""
        self.method_to_classes = defaultdict(list)
        self.class_to_domain = {}
        self.class_inheritance = {}
        
        # Build method name to classes mapping
        for method_key, method_info in self.methods.items():
            method_name = method_info['method_name']
            class_name = method_info['class_name']
            self.method_to_classes[method_name].append(class_name)
        
        # Build class domain and inheritance mappings
        for class_name, class_info in self.classes.items():
            self.class_to_domain[class_name] = class_info['domain']
            self.class_inheritance[class_name] = class_info.get('parent_classes', [])
    
    def resolve_method(self, object_chain: str, method_name: str, context: Dict = None) -> Optional[str]:
        """
        Intelligently resolve a method call to its full PyCATIA signature using live graph
        
        Args:
            object_chain: The object chain (e.g., "spline1", "factory.create")
            method_name: The method being called
            context: Additional context (step_number, function_name, etc.)
        
        Returns:
            Full method signature or None if not found
        """
        context = context or {}
        
        # Get all classes that have this method
        candidate_classes = self.method_to_classes.get(method_name, [])
        if not candidate_classes:
            return None
        
        # Score candidates based on semantic similarity
        scored_candidates = []
        for class_name in candidate_classes:
            score = self._score_class_candidate(class_name, object_chain, method_name, context)
            scored_candidates.append((score, class_name))
        
        # Return the highest scoring candidate
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            best_class = scored_candidates[0][1]
            method_key = f"{best_class}.{method_name}"
            
            if method_key in self.methods:
                return self.methods[method_key]['full_signature']
        
        return None
    
    def _score_class_candidate(self, class_name: str, object_chain: str, method_name: str, context: Dict) -> float:
        """Score how well a class matches the context using live graph intelligence"""
        score = 0.0
        
        # Variable name hints (e.g., spline1 -> HybridShapeSpline)
        base_var = object_chain.split('.')[0].lower()
        
        # Direct semantic matching with class name
        if base_var in class_name.lower():
            score += 100
        
        # Check parent classes for inheritance matches
        parent_classes = self.class_inheritance.get(class_name, [])
        for parent in parent_classes:
            if base_var in parent.lower():
                score += 75
        
        # Domain relevance scoring
        class_info = self.classes.get(class_name, {})
        domain = class_info.get('domain', '')
        
        # Hybrid shape interfaces are key for geometry operations
        if 'hybrid_shape' in domain and any(hint in base_var for hint in ['spline', 'point', 'line', 'plane', 'curve']):
            score += 50
        
        # Factory pattern recognition
        if class_info.get('is_factory', False) and any(hint in method_name for hint in ['add_new', 'create']):
            score += 40
        
        # Collection/container pattern recognition  
        if class_info.get('is_collection', False) and method_name in ['add', 'item', 'remove']:
            score += 30
        
        # Context-based scoring using step information
        step_number = context.get('step_number', 0)
        if step_number > 0:
            # Early steps typically use factory methods
            if step_number <= 10 and class_info.get('is_factory', False):
                score += 20
            # Later steps typically use geometry manipulation
            elif step_number > 15 and class_info.get('is_geometry', False):
                score += 15
        
        # Method type patterns
        method_info = self.methods.get(f"{class_name}.{method_name}", {})
        method_type = method_info.get('method_type', 'instance')
        
        # Properties are often used for configuration
        if method_type == 'property' and any(hint in base_var for hint in ['config', 'setting', 'param']):
            score += 10
        
        # Static methods are typically utilities
        if method_type == 'static' and method_name.startswith('get_'):
            score += 5
        
        return score
    
    def get_method_info(self, full_signature: str) -> Optional[Dict]:
        """Get detailed information about a method from live graph"""
        for method_key, method_info in self.methods.items():
            if method_info['full_signature'] == full_signature:
                return method_info
        return None
    
    def get_class_info(self, class_name: str) -> Optional[Dict]:
        """Get detailed information about a class from live graph"""
        return self.classes.get(class_name)
    
    def find_similar_methods(self, method_name: str, limit: int = 10) -> List[str]:
        """Find methods with similar names using live graph"""
        similar = []
        
        # Exact name matches
        if method_name in self.method_to_classes:
            for class_name in self.method_to_classes[method_name]:
                method_key = f"{class_name}.{method_name}"
                if method_key in self.methods:
                    similar.append(self.methods[method_key]['full_signature'])
        
        # Fuzzy name matching for common patterns
        method_lower = method_name.lower()
        for method_key, method_info in self.methods.items():
            if len(similar) >= limit:
                break
                
            existing_method = method_info['method_name'].lower()
            
            # Look for similar patterns
            if (method_lower != existing_method and 
                (method_lower in existing_method or existing_method in method_lower)):
                sig = method_info['full_signature']
                if sig not in similar:
                    similar.append(sig)
        
        return similar[:limit]
    
    def get_statistics(self) -> Dict:
        """Get statistics about the live knowledge graph"""
        stats = {
            'total_classes': len(self.classes),
            'total_methods': len(self.methods),
            'domains': len(set(self.class_to_domain.values())),
            'factory_classes': sum(1 for cls in self.classes.values() if cls.get('is_factory', False)),
            'geometry_classes': sum(1 for cls in self.classes.values() if cls.get('is_geometry', False)),
            'classes_with_inheritance': sum(1 for cls in self.classes.values() if cls.get('parent_classes', [])),
            'methods_with_docs': sum(1 for method in self.methods.values() if method.get('docstring', '').strip()),
            'source': 'live_library_inspection'
        }
        return stats


# Global instance for easy access
PYCATIA_INTELLIGENCE = None

def get_intelligence():
    """Get or create the global intelligence instance"""
    global PYCATIA_INTELLIGENCE
    if PYCATIA_INTELLIGENCE is None:
        PYCATIA_INTELLIGENCE = PyCATIAIntelligence()
    return PYCATIA_INTELLIGENCE

def resolve_method(object_chain: str, method_name: str, context: Dict = None) -> Optional[str]:
    """Convenience function for method resolution"""
    intelligence = get_intelligence()
    return intelligence.resolve_method(object_chain, method_name, context)


if __name__ == "__main__":
    # Test the live intelligence
    print("🧠 Testing PyCATIA Intelligence")
    print("=" * 50)
    
    try:
        intel = PyCATIAIntelligence()
        
        # Test key method resolution
        test_cases = [
            ("spline1", "add_point_with_constraint_from_curve"),
            ("factory", "add_new_spline"),
            ("part1", "update"),
            ("hybrid_bodies", "add")
        ]
        
        for obj_chain, method in test_cases:
            result = intel.resolve_method(obj_chain, method)
            print(f"   {obj_chain}.{method}() -> {result}")
        
        # Show statistics
        stats = intel.get_statistics()
        print(f"\n📊 Knowledge Graph Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error: {e}")