#!/usr/bin/env python3
"""
Hierarchical Tree Search System for PyKTR API Method Matching

This system implements a top-down hierarchical search that uses:
1. Knowledge graph structure for efficient tree traversal
2. LLM semantic analysis for step understanding
3. Database descriptions for context-aware matching
4. Rating system to progressively narrow down from classes to methods

The approach:
- Start with root classes from knowledge graph
- Use LLM to analyze tutorial steps and rate class relevance
- Navigate down the hierarchy based on ratings
- Continue until finding the most appropriate methods
"""

import json
import sqlite3
import requests
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, deque


@dataclass
class ClassNode:
    """Represents a class in the hierarchical tree"""
    name: str
    full_name: str
    domain: str
    parent_classes: List[str]
    child_classes: List[str]
    methods: Dict[str, str]
    description: str = ""
    relevance_score: float = 0.0


@dataclass
class TutorialStep:
    """Represents a step in the tutorial"""
    step_number: int
    title: str
    description: str
    expected_outcome: str
    keywords: List[str]


@dataclass
class ObjectContext:
    """Tracks objects created in previous steps for context awareness"""
    object_name: str
    object_type: str
    creation_step: int
    creation_method: str
    properties: Dict[str, any] = None
    

@dataclass
class MethodMatch:
    """Represents a matched method with confidence"""
    method_signature: str
    class_name: str
    method_name: str
    confidence: float
    reasoning: str
    step_number: int
    referenced_objects: List[str] = None  # Objects from previous steps this method might use
    
    # Backward compatibility
    @property
    def confidence_score(self):
        return self.confidence


class HierarchicalTreeNavigator:
    """
    Navigates the knowledge graph hierarchy efficiently
    """
    
    def __init__(self, knowledge_graph_path: str):
        self.graph_path = knowledge_graph_path
        self.classes = {}
        self.class_hierarchy = defaultdict(list)  # parent -> children
        self.root_classes = set()
        
        self._load_knowledge_graph()
        self._build_hierarchy()
    
    def _load_knowledge_graph(self):
        """Load the knowledge graph from JSON"""
        try:
            with open(self.graph_path, 'r') as f:
                graph_data = json.load(f)
            
            self.classes = graph_data.get('classes', {})
            print(f"📚 Loaded {len(self.classes)} classes from knowledge graph")
            
        except FileNotFoundError:
            print(f"❌ Knowledge graph not found: {self.graph_path}")
            raise
    
    def _build_hierarchy(self):
        """Build the hierarchical tree structure"""
        all_classes = set(self.classes.keys())
        has_parent = set()
        
        # Build parent -> children mapping
        for class_name, class_info in self.classes.items():
            parent_classes = class_info.get('parent_classes', [])
            
            for parent in parent_classes:
                if parent in all_classes:  # Ensure parent exists in our graph
                    self.class_hierarchy[parent].append(class_name)
                    has_parent.add(class_name)
        
        # Find root classes (classes with no parents in our graph)
        self.root_classes = all_classes - has_parent
        
        print(f"🌳 Built hierarchy: {len(self.root_classes)} root classes")
        print(f"   Root classes: {list(self.root_classes)[:5]}...")  # Show first 5
    
    def get_productive_starting_classes(self) -> List[ClassNode]:
        """
        ENHANCED INTELLIGENCE: Get diverse starting classes for comprehensive coverage
        
        This enhanced version includes more class types and uses smarter filtering
        to ensure we don't miss important classes that could be relevant.
        """
        productive_classes = []
        
        # EXPANDED productive class patterns for comprehensive PyCATIA coverage
        productive_patterns = [
            # Core CATIA functionality
            'Application',     # CATIA application entry point
            'Document',        # Document management  
            'Part',            # Part objects
            'Bodies',          # Geometric bodies
            'Body',            # Individual body objects
            
            # Factory classes (creation tools)
            'Factory',         # All factory classes
            'HybridShape',     # Hybrid shape operations
            'Shape',           # Shape operations
            'Sketcher',        # Sketching operations
            
            # Reference and coordinate systems
            'Reference',       # Reference elements
            'Plane',           # Plane objects
            'Axis',            # Axis objects
            'Point',           # Point objects
            'Coordinate',      # Coordinate systems
            'Origin',          # Origin elements
            
            # Managers and controllers
            'Manager',         # Various managers
            'Collection',      # Collection objects
            'Service',         # Service objects
            'Setting',         # Settings and configuration
            
            # Workbench specific
            'Workbench',       # Workbench objects
            'Environment',     # Environment objects
            'Infrastructure',  # Infrastructure components
            
            # Analysis and measurement
            'Measurable',      # Measurement objects
            'Analysis',        # Analysis tools
            'Validation',      # Validation tools
        ]
        
        # Find classes that match productive patterns with more flexible criteria
        for class_name, class_info in self.classes.items():
            methods = class_info.get('methods', {})
            domain = class_info.get('domain', '')
            
            # More flexible method count threshold
            if len(methods) < 2:  # Only skip classes with very few methods
                continue
            
            is_productive = False
            
            # Pattern matching for known productive classes
            for pattern in productive_patterns:
                if pattern.lower() in class_name.lower():
                    is_productive = True
                    break
            
            # ENHANCED domain relevance checks - include more domains
            important_domains = [
                'part_interfaces',           # Part modeling
                'hybrid_shape_interfaces',   # Hybrid shapes
                'mec_mod_interfaces',        # Mechanical modeling
                'sketcher_interfaces',       # Sketching
                'product_structure_interfaces',  # Product structure
                'drafting_interfaces',       # Drafting
                'assembly_interfaces',       # Assembly
                'analysis_interfaces',       # Analysis
            ]
            
            if any(important_domain in domain for important_domain in important_domains):
                if len(methods) >= 3:  # Lower threshold for domain-relevant classes
                    is_productive = True
            
            # Include classes with many methods regardless of pattern matching
            if len(methods) >= 15:  # Classes with substantial functionality
                is_productive = True
            
            # Include classes mentioned in method purposes (they're being used)
            if hasattr(self, 'class_purposes') and class_name in self.class_purposes:
                if len(self.class_purposes[class_name]) >= 2:  # Has documented purposes
                    is_productive = True
            
            if is_productive:
                node = ClassNode(
                    name=class_name,
                    full_name=class_info.get('full_name', class_name),
                    domain=domain,
                    parent_classes=class_info.get('parent_classes', []),
                    child_classes=self.class_hierarchy.get(class_name, []),
                    methods=methods,
                    description=class_info.get('docstring', '')
                )
                productive_classes.append(node)
        
        # Enhanced sorting: balance method count with purpose documentation
        def sort_key(cls):
            base_score = len(cls.methods)
            
            # Bonus for having documented purposes
            if hasattr(self, 'class_purposes') and cls.name in self.class_purposes:
                base_score += len(self.class_purposes[cls.name]) * 5
            
            # Bonus for being in key domains
            key_domains = ['hybrid_shape_interfaces', 'part_interfaces', 'mec_mod_interfaces']
            if any(domain in cls.domain for domain in key_domains):
                base_score += 20
            
            return base_score
        
        productive_classes.sort(key=sort_key, reverse=True)
        
        print(f"🎯 Found {len(productive_classes)} productive starting classes")
        print(f"   Top classes: {[cls.name for cls in productive_classes[:5]]}")
        print(f"   Domain diversity: {len(set(cls.domain for cls in productive_classes[:20]))} domains in top 20")
        
        return productive_classes
    
    def get_root_classes(self) -> List[ClassNode]:
        """Get all root classes as ClassNode objects (legacy method)"""
        root_nodes = []
        
        for class_name in self.root_classes:
            class_info = self.classes.get(class_name, {})
            
            node = ClassNode(
                name=class_name,
                full_name=class_info.get('full_name', class_name),
                domain=class_info.get('domain', ''),
                parent_classes=class_info.get('parent_classes', []),
                child_classes=self.class_hierarchy.get(class_name, []),
                methods=class_info.get('methods', {}),
                description=class_info.get('docstring', '')
            )
            root_nodes.append(node)
        
        return root_nodes
    
    def get_children(self, class_name: str) -> List[ClassNode]:
        """Get child classes of a given class"""
        child_nodes = []
        
        for child_name in self.class_hierarchy.get(class_name, []):
            class_info = self.classes.get(child_name, {})
            
            node = ClassNode(
                name=child_name,
                full_name=class_info.get('full_name', child_name),
                domain=class_info.get('domain', ''),
                parent_classes=class_info.get('parent_classes', []),
                child_classes=self.class_hierarchy.get(child_name, []),
                methods=class_info.get('methods', {}),
                description=class_info.get('docstring', '')
            )
            child_nodes.append(node)
        
        return child_nodes
    
    def find_path_to_class(self, target_class: str) -> List[str]:
        """Find the path from root to a specific class"""
        # BFS to find path
        queue = deque([(root, [root]) for root in self.root_classes])
        
        while queue:
            current_class, path = queue.popleft()
            
            if current_class == target_class:
                return path
            
            for child in self.class_hierarchy.get(current_class, []):
                queue.append((child, path + [child]))
        
        return []  # Not found
    
    def _comprehensive_semantic_analysis(self, step: TutorialStep, classes: List[ClassNode], max_classes: int = 30) -> List[ClassNode]:
        """
        ENHANCED COMPREHENSIVE SEMANTIC ANALYSIS: More inclusive and thorough approach
        
        This enhanced version includes more classes and uses improved scoring to ensure
        we don't miss potentially relevant matches.
        """
        
        print(f"   🧠 Enhanced semantic analysis: Understanding design step and examining {len(classes)} class purposes...")
        
        # Step 1: Understand the design step intent
        step_understanding = self._deep_understand_design_step(step)
        print(f"   📋 Step understanding: {step_understanding['primary_action']} - {step_understanding['catia_operation']}")
        
        # Step 2: Analyze each class with its purposes
        analyzed_classes = []
        
        for i, class_node in enumerate(classes):
            # Extract class purposes from method descriptions
            class_purposes = self._extract_class_purposes(class_node)
            
            # Calculate semantic alignment with enhanced scoring
            alignment_score = self._calculate_deep_semantic_alignment(step_understanding, class_node, class_purposes)
            
            # More inclusive threshold - include classes with even minimal relevance
            inclusion_threshold = 0.02  # Much lower threshold
            
            # Special bonuses for certain class types
            bonus_score = 0.0
            
            # Bonus for factory classes (they create things)
            if 'factory' in class_node.name.lower():
                bonus_score += 0.1
            
            # Bonus for classes with many methods (likely to be useful)
            if len(class_node.methods) > 20:
                bonus_score += 0.05
            
            # Bonus for classes with documented purposes
            if hasattr(self, 'class_purposes') and class_node.name in self.class_purposes:
                if len(self.class_purposes[class_node.name]) > 5:
                    bonus_score += 0.08
            
            # Bonus for key domains
            key_domains = ['hybrid_shape_interfaces', 'part_interfaces', 'mec_mod_interfaces']
            if any(domain in class_node.domain for domain in key_domains):
                bonus_score += 0.06
            
            final_score = alignment_score + bonus_score
            
            if final_score > inclusion_threshold:
                class_node.relevance_score = final_score
                class_node.extracted_purposes = class_purposes
                analyzed_classes.append(class_node)
                
                # Show purposes for verification (show more classes)
                if i < 15:  # Show more classes for verification
                    print(f"   📚 {class_node.name}: {class_purposes[:80]}... (score: {final_score:.3f})")
        
        # Sort by semantic alignment
        analyzed_classes.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"   🎯 Top semantic matches: {[f'{cls.name}({cls.relevance_score:.3f})' for cls in analyzed_classes[:8]]}")
        print(f"   📊 Total classes included: {len(analyzed_classes)} (from {len(classes)} candidates)")
        
        return analyzed_classes[:max_classes]
    
    def _deep_understand_design_step(self, step: TutorialStep) -> Dict:
        """Deep understanding of what the design step is trying to accomplish"""
        
        understanding = {
            'step_number': step.step_number,
            'primary_action': self._extract_primary_action(step),
            'catia_operation': self._identify_catia_operation_type(step),
            'modeling_intent': self._understand_modeling_intent(step),
            'required_capabilities': self._identify_required_capabilities(step)
        }
        
        return understanding
    
    def _extract_primary_action(self, step: TutorialStep) -> str:
        """Extract the primary action verb from the design step"""
        title_lower = step.title.lower()
        
        action_patterns = {
            'initialize': ['initialize', 'start', 'begin', 'setup'],
            'create': ['create', 'add', 'generate', 'build'],
            'define': ['define', 'set', 'establish', 'specify'],
            'configure': ['configure', 'setup', 'prepare', 'adjust'],
            'access': ['access', 'get', 'retrieve', 'obtain']
        }
        
        for action, patterns in action_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return action
        
        return 'execute'
    
    def _identify_catia_operation_type(self, step: TutorialStep) -> str:
        """Identify what type of CATIA operation this step represents"""
        
        desc_text = step.description.lower()
        
        if any(word in desc_text for word in ['catia', 'application', 'environment', 'workbench']):
            return 'application_control'
        elif any(word in desc_text for word in ['document', 'part', 'new']):
            return 'document_management'
        elif any(word in desc_text for word in ['plane', 'axis', 'reference', 'coordinate']):
            return 'reference_geometry'
        elif any(word in desc_text for word in ['hybrid', 'shape', 'factory', 'geometrical']):
            return 'geometry_factory'
        elif any(word in desc_text for word in ['spline', 'curve', 'surface', 'point']):
            return 'geometric_elements'
        else:
            return 'general_modeling'
    
    def _understand_modeling_intent(self, step: TutorialStep) -> str:
        """Understand the modeling intent behind the step"""
        
        desc_lower = step.description.lower()
        
        if 'initialize' in desc_lower:
            return 'setup_environment'
        elif 'configure' in desc_lower or 'set up' in desc_lower:
            return 'configure_workspace'
        elif 'create' in desc_lower and 'document' in desc_lower:
            return 'document_creation'
        elif 'access' in desc_lower or 'origin' in desc_lower:
            return 'access_references'
        else:
            return 'geometric_modeling'
    
    def _identify_required_capabilities(self, step: TutorialStep) -> List[str]:
        """Identify what capabilities are needed to execute this step"""
        
        desc_text = step.description.lower()
        capabilities = []
        
        if 'catia' in desc_text or 'application' in desc_text:
            capabilities.append('application_access')
        if 'document' in desc_text:
            capabilities.append('document_management')
        if 'factory' in desc_text or 'hybrid' in desc_text:
            capabilities.append('geometry_factory')
        if 'plane' in desc_text or 'reference' in desc_text:
            capabilities.append('reference_creation')
        
        return capabilities
    
    def _extract_class_purposes(self, class_node: ClassNode, method_descriptions: Dict = None) -> str:
        """Extract comprehensive purposes from class methods using proper database lookup"""
        
        purposes = []
        
        # Access class_purposes from navigator if available (passed from search engine)
        if hasattr(self, 'class_purposes') and class_node.name in self.class_purposes:
            class_method_purposes = self.class_purposes[class_node.name]
            for method_info in class_method_purposes:  # Get all available purposes
                purposes.append(method_info['purpose'])
        
        # Fallback: Get purposes from method descriptions
        elif method_descriptions:
            for method_name, method_sig in list(class_node.methods.items()):
                if method_sig in method_descriptions:
                    purpose = method_descriptions[method_sig].get('purpose', '')
                    if purpose and len(purpose) > 20:
                        purposes.append(purpose[:80])
        
        # Combine with class description if no specific purposes found
        if not purposes and class_node.description and len(class_node.description) > 50:
            purposes.append(class_node.description[:100])
        
        # Create comprehensive summary
        if purposes:
            return f"Domain: {class_node.domain}. ACTUAL PURPOSES: " + "; ".join(purposes[:2])
        else:
            return f"Domain: {class_node.domain}. Class with {len(class_node.methods)} methods (no specific purposes found)."
    
    def _calculate_deep_semantic_alignment(self, step_understanding: Dict, class_node: ClassNode, class_purposes: str) -> float:
        """Calculate deep semantic alignment between step understanding and class purposes"""
        
        score = 0.0
        
        # 1. Operation type alignment (40% weight)
        catia_operation = step_understanding['catia_operation']
        operation_score = self._score_operation_alignment(catia_operation, class_node.domain, class_purposes)
        score += operation_score * 0.4
        
        # 2. Required capabilities alignment (30% weight)
        capabilities_score = self._score_capabilities_alignment(step_understanding['required_capabilities'], class_purposes)
        score += capabilities_score * 0.3
        
        # 3. Modeling intent alignment (30% weight)
        intent_score = self._score_intent_alignment(step_understanding['modeling_intent'], class_purposes)
        score += intent_score * 0.3
        
        return min(score, 1.0)
    
    def _score_operation_alignment(self, catia_operation: str, class_domain: str, class_purposes: str) -> float:
        """Score alignment between CATIA operation type and class capabilities"""
        
        operation_mappings = {
            'application_control': ['application', 'catia', 'interface'],
            'document_management': ['document', 'part', 'create'],
            'reference_geometry': ['reference', 'plane', 'axis', 'coordinate'],
            'geometry_factory': ['factory', 'hybrid', 'shape'],
            'geometric_elements': ['spline', 'curve', 'point', 'surface']
        }
        
        relevant_terms = operation_mappings.get(catia_operation, [])
        desc_text = f"{class_domain} {class_purposes}".lower()
        
        matches = sum(1 for term in relevant_terms if term in desc_text)
        return min(matches / len(relevant_terms) if relevant_terms else 0, 1.0)
    
    def _score_capabilities_alignment(self, required_capabilities: List[str], class_purposes: str) -> float:
        """Score how well class purposes align with required capabilities"""
        
        if not required_capabilities:
            return 0.5  # Neutral score
        
        purposes_lower = class_purposes.lower()
        matching_capabilities = 0
        
        for capability in required_capabilities:
            capability_terms = capability.split('_')
            if any(term in purposes_lower for term in capability_terms):
                matching_capabilities += 1
        
        return matching_capabilities / len(required_capabilities)
    
    def _score_intent_alignment(self, modeling_intent: str, class_purposes: str) -> float:
        """Score alignment between modeling intent and class purposes"""
        
        intent_keywords = {
            'setup_environment': ['initialize', 'setup', 'environment'],
            'configure_workspace': ['configure', 'set', 'workspace'],
            'document_creation': ['document', 'create', 'new'],
            'access_references': ['access', 'reference', 'origin'],
            'geometric_modeling': ['geometry', 'shape', 'model']
        }
        
        keywords = intent_keywords.get(modeling_intent, [])
        purposes_lower = class_purposes.lower()
        
        matches = sum(1 for keyword in keywords if keyword in purposes_lower)
        return min(matches / len(keywords) if keywords else 0, 1.0)


class LLMStepAnalyzer:
    """
    Uses Ollama LLM with reasoning model to analyze tutorial steps and rate class relevance
    Enhanced with fine-grained rating system for better discrimination
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", method_descriptions: Dict = None):
        self.ollama_url = ollama_url
        self.model = "deepseek-r1:latest"  # Use deepseek-r1 for superior reasoning capabilities
        self.method_descriptions = method_descriptions or {}
        
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("🤖 LLM Analyzer connected successfully")
            else:
                print("⚠️  Could not connect to Ollama LLM")
        except Exception as e:
            print(f"⚠️  LLM connection failed: {e}")
    
    def analyze_step_for_classes(self, step: TutorialStep, classes: List[ClassNode]) -> List[Tuple[ClassNode, float, str]]:
        """
        Analyze a tutorial step and rate the relevance of classes
        
        Returns: List of (ClassNode, relevance_score, reasoning)
        """
        if not classes:
            return []
        
        # Create semantic understanding prompt
        prompt = self._create_semantic_understanding_prompt(step, classes)
        
        try:
            # Query LLM
            response = self._query_ollama(prompt)
            
            # Parse ratings from response
            ratings = self._parse_class_ratings(response, classes)
            
            return ratings
            
        except Exception as e:
            print(f"⚠️  LLM analysis failed: {e}")
            # Fallback to keyword matching
            return self._fallback_keyword_rating(step, classes)
    
    def analyze_step_for_methods(self, step: TutorialStep, class_node: ClassNode) -> List[Tuple[str, float, str]]:
        """
        Analyze a step to find the best methods within a specific class
        
        Returns: List of (method_signature, confidence, reasoning)
        """
        if not class_node.methods:
            return []
        
        prompt = self._create_method_rating_prompt(step, class_node)
        
        try:
            response = self._query_ollama(prompt)
            method_ratings = self._parse_method_ratings(response, class_node.methods)
            return method_ratings
            
        except Exception as e:
            print(f"⚠️  Method analysis failed: {e}")
            return self._fallback_method_rating(step, class_node)
    
    def _create_semantic_understanding_prompt(self, step: TutorialStep, classes: List[ClassNode]) -> str:
        """SEMANTIC ENHANCEMENT: Create deep understanding prompt for CATIA design steps"""
        
        prompt = f"""You are a CATIA V5 CAD modeling expert analyzing a design step for wing geometry creation.

DESIGN CONTEXT: This is a professional CATIA V5 modeling workflow for creating UAV wing geometry.

DESIGN STEP {step.step_number}: {step.title}

STEP UNDERSTANDING:
What needs to be accomplished: {step.description}
Expected modeling outcome: {step.expected_outcome}

AVAILABLE PYCATIA CLASSES WITH THEIR PURPOSES:
"""
        
        for i, class_node in enumerate(classes, 1):
            prompt += f"\n{i}. CLASS: {class_node.name}\n"
            prompt += f"   Domain: {class_node.domain}\n"
            
            # Show actual method purposes from database
            purposes_shown = 0
            for method_name, method_sig in list(class_node.methods.items()):  # Show all methods
                if hasattr(self, 'method_descriptions') and method_sig in self.method_descriptions:
                    purpose = self.method_descriptions[method_sig].get('purpose', '')
                    if purpose:  # Show all clear purposes
                        prompt += f"   Purpose {purposes_shown + 1}: {purpose[:150]}...\n"
                        purposes_shown += 1
            
            if purposes_shown == 0:
                prompt += f"   Description: {class_node.description[:150]}...\n"
            
            prompt += f"   Total methods: {len(class_node.methods)}\n"
        
        prompt += f"""

SEMANTIC ANALYSIS TASK:
1. First, understand what the design step is trying to accomplish in CATIA V5
2. Then, analyze each class's purposes to see which ones enable that accomplishment
3. Rate each class from 0.0 to 1.0 based on semantic alignment

CATIA V5 MODELING WORKFLOW UNDERSTANDING:
- Initialize/Setup steps: Need Application, Document, Workbench classes
- Reference creation: Need factory classes that create planes, axes, coordinate systems
- Geometry creation: Need HybridShape factories and geometric element classes
- Advanced operations: Need specialized geometric manipulation classes

FINE-GRAINED ANALYSIS APPROACH (Use decimal precision to 4 places for better discrimination):
- 0.9500-1.0000: PERFECT - Class purposes directly implement the exact design step requirement
- 0.8500-0.9499: EXCELLENT - Class is the primary tool for this type of design operation  
- 0.7000-0.8499: STRONG - Class has significant relevance and supports the design step
- 0.5500-0.6999: MODERATE - Class has some connection but not the primary tool
- 0.3000-0.5499: WEAK - Class has minimal relevance or indirect connection
- 0.1000-0.2999: VERY WEAK - Class barely relates to the design step
- 0.0000-0.0999: NO MATCH - Class purposes completely unrelated

REASONING REQUIREMENTS:
Analyze each class's ACTUAL PURPOSES from the database against the specific design step requirements.
Focus on what the class methods can DO, not just keyword matching.
Consider CATIA workflow context and the step's position in the modeling sequence.

RESPONSE FORMAT (use precise decimal ratings):
Class 1: 0.9287 - EXCELLENT match because [specific reasoning about how the actual method purposes enable this exact design step]
Class 2: 0.6843 - MODERATE relevance because [explain specific connections between purposes and step requirements]

Your semantic analysis:"""
        
        return prompt
    
    def _create_method_rating_prompt(self, step: TutorialStep, class_node: ClassNode) -> str:
        """Create prompt for rating method relevance within a class"""
        
        prompt = f"""You are analyzing methods within the {class_node.name} class for this tutorial step.

TUTORIAL STEP {step.step_number}:
Title: {step.title}
Description: {step.description}
Expected Outcome: {step.expected_outcome}

CLASS: {class_node.name}
Description: {class_node.description[:300]}

METHODS IN THIS CLASS:
"""
        
        for i, (method_name, method_sig) in enumerate(class_node.methods.items(), 1):
            prompt += f"{i}. {method_name}\n   Signature: {method_sig}\n\n"
        
        prompt += f"""
Rate each method from 0.0 to 1.0 based on how likely it is to be used in this tutorial step.

Format:
Method 1: 0.9 - Perfect match because...
Method 2: 0.1 - Unlikely because...

Your ratings:"""
        
        return prompt
    
    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama with the prompt"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            raise Exception(f"Ollama request failed: {response.status_code}")
    
    def _parse_class_ratings(self, response: str, classes: List[ClassNode]) -> List[Tuple[ClassNode, float, str]]:
        """Parse LLM response to extract class ratings"""
        ratings = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and any(char.isdigit() for char in line):
                try:
                    # Look for pattern "Class X: 0.Y - reasoning"
                    parts = line.split(':', 1)
                    if len(parts) >= 2:
                        class_part = parts[0].strip()
                        rest = parts[1].strip()
                        
                        # Extract class number
                        class_num = None
                        for word in class_part.split():
                            if word.isdigit():
                                class_num = int(word) - 1  # Convert to 0-based index
                                break
                        
                        if class_num is not None and 0 <= class_num < len(classes):
                            # Extract score
                            score_str = rest.split()[0]
                            score = float(score_str)
                            
                            # Extract reasoning
                            reasoning = rest.split('-', 1)[1].strip() if '-' in rest else "No reasoning provided"
                            
                            ratings.append((classes[class_num], score, reasoning))
                            
                except (ValueError, IndexError):
                    continue
        
        # Fallback if parsing failed
        if not ratings:
            return self._fallback_keyword_rating(None, classes)
        
        return ratings
    
    def _parse_method_ratings(self, response: str, methods: Dict[str, str]) -> List[Tuple[str, float, str]]:
        """Parse LLM response to extract method ratings"""
        ratings = []
        lines = response.split('\n')
        method_list = list(methods.items())
        
        for line in lines:
            line = line.strip()
            if ':' in line and any(char.isdigit() for char in line):
                try:
                    parts = line.split(':', 1)
                    if len(parts) >= 2:
                        method_part = parts[0].strip()
                        rest = parts[1].strip()
                        
                        # Extract method number
                        method_num = None
                        for word in method_part.split():
                            if word.isdigit():
                                method_num = int(word) - 1
                                break
                        
                        if method_num is not None and 0 <= method_num < len(method_list):
                            method_name, method_sig = method_list[method_num]
                            
                            # Extract score
                            score_str = rest.split()[0]
                            score = float(score_str)
                            
                            # Extract reasoning
                            reasoning = rest.split('-', 1)[1].strip() if '-' in rest else "No reasoning provided"
                            
                            ratings.append((method_sig, score, reasoning))
                            
                except (ValueError, IndexError):
                    continue
        
        return ratings
    
    def _fallback_keyword_rating(self, step: Optional[TutorialStep], classes: List[ClassNode]) -> List[Tuple[ClassNode, float, str]]:
        """Fallback keyword-based rating when LLM fails"""
        ratings = []
        
        if not step:
            # Equal rating for all classes
            for class_node in classes:
                ratings.append((class_node, 0.5, "Fallback equal rating"))
            return ratings
        
        # Simple keyword matching
        step_text = f"{step.description} {' '.join(step.keywords)}".lower()
        
        for class_node in classes:
            class_text = f"{class_node.name} {class_node.domain} {class_node.description}".lower()
            
            # Count keyword matches
            matches = sum(1 for word in step_text.split() if word in class_text)
            score = min(matches / 10.0, 1.0)  # Normalize
            
            ratings.append((class_node, score, f"Keyword matching: {matches} matches"))
        
        return ratings
    
    def _fallback_method_rating(self, step: TutorialStep, class_node: ClassNode) -> List[Tuple[str, float, str]]:
        """Fallback method rating using keyword matching"""
        ratings = []
        step_text = f"{step.description} {' '.join(step.keywords)}".lower()
        
        for method_name, method_sig in class_node.methods.items():
            method_text = f"{method_name} {method_sig}".lower()
            
            matches = sum(1 for word in step_text.split() if word in method_text)
            score = min(matches / 5.0, 1.0)
            
            ratings.append((method_sig, score, f"Keyword matching: {matches} matches"))
        
        return ratings


class HierarchicalSearchEngine:
    """
    Main engine that combines tree navigation with LLM analysis
    """
    
    def __init__(self, knowledge_graph_path: str, methods_database_path: str, design_database_path: str):
        self.navigator = HierarchicalTreeNavigator(knowledge_graph_path)
        self.methods_db_path = methods_database_path
        self.design_db_path = design_database_path
        
        # Object context tracking for understanding step relationships
        self.object_context: List[ObjectContext] = []
        self.step_objects = {}  # step_number -> list of created objects
        
        # Load method descriptions from database
        self._load_method_descriptions()
        
        # Pass method descriptions and class purposes to navigator for comprehensive semantic analysis  
        self.navigator.method_descriptions = self.method_descriptions
        self.navigator.class_purposes = self.class_purposes
        
        # Initialize analyzer with method descriptions for semantic understanding
        self.analyzer = LLMStepAnalyzer(method_descriptions=self.method_descriptions)
        
        print("🚀 Hierarchical Search Engine initialized")
    
    def _load_method_descriptions(self):
        """Load method descriptions and purposes from the methods database with proper class mapping"""
        self.method_descriptions = {}
        self.class_purposes = defaultdict(list)  # Track purposes by class name
        
        try:
            conn = sqlite3.connect(self.methods_db_path)
            cursor = conn.cursor()
            
            # Join methods with their purposes and extract class information
            cursor.execute("""
                SELECT pm.full_method_name, pm.method_name, mp.purpose, mp.docstring
                FROM pycatia_methods pm
                JOIN method_purposes mp ON pm.id = mp.method_id
                WHERE mp.purpose IS NOT NULL AND mp.purpose != ''
            """)
            
            for row in cursor.fetchall():
                full_method_name, method_name, purpose, docstring = row
                
                # Extract class name from full_method_name
                # e.g., 'pycatia.abq_automation_interfaces.abq_analysis_case.ABQAnalysisCase.method_name'
                class_name = self._extract_class_name_from_full_method(full_method_name)
                
                self.method_descriptions[full_method_name] = {
                    'purpose': purpose,
                    'docstring': docstring or '',
                    'class_name': class_name,
                    'method_name': method_name
                }
                
                # Group purposes by class for easier lookup
                if class_name and purpose:
                    self.class_purposes[class_name].append({
                        'method_name': method_name,
                        'purpose': purpose[:200],  # Limit length
                        'full_method': full_method_name
                    })
            
            conn.close()
            print(f"📚 Loaded descriptions for {len(self.method_descriptions)} methods")
            print(f"📚 Organized {len(self.class_purposes)} classes with purposes")
            
        except Exception as e:
            print(f"⚠️  Could not load method descriptions: {e}")
            self.method_descriptions = {}
            self.class_purposes = defaultdict(list)
    
    def _extract_class_name_from_full_method(self, full_method_name: str) -> str:
        """Extract class name from full method name like 'pycatia.module.ClassName.method_name'"""
        try:
            parts = full_method_name.split('.')
            if len(parts) >= 2:
                # The class name is typically the second-to-last part
                return parts[-2]
            return ""
        except:
            return ""
    
    def load_tutorial_steps_from_db(self, template_id: int = 1) -> List[TutorialStep]:
        """Load tutorial steps from the design database"""
        tutorial_steps = []
        
        try:
            conn = sqlite3.connect(self.design_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT step_number, action_short, details, action_type, target_object, 
                       parameters, purpose_notes, pycatia_method
                FROM design_steps 
                WHERE template_id = ?
                ORDER BY step_number
            """, (template_id,))
            
            for row in cursor.fetchall():
                step_number, action_short, details, action_type, target_object, parameters, purpose_notes, pycatia_method = row
                
                # Use correct detailed descriptions from database
                title = action_short or f"Step {step_number}"
                description = details or action_short  # Use detailed description
                expected_outcome = purpose_notes or f"Complete step {step_number}"
                
                # Extract keywords from various fields
                keywords = []
                if action_type:
                    keywords.append(action_type)
                if target_object:
                    keywords.append(target_object)
                if parameters:
                    # Parse JSON parameters to extract values
                    try:
                        import json
                        param_dict = json.loads(parameters)
                        keywords.extend(str(v) for v in param_dict.values() if isinstance(v, str))
                    except:
                        pass
                
                tutorial_step = TutorialStep(
                    step_number=step_number,
                    title=title,
                    description=description,
                    expected_outcome=expected_outcome,
                    keywords=keywords
                )
                tutorial_steps.append(tutorial_step)
            
            conn.close()
            print(f"📋 Loaded {len(tutorial_steps)} tutorial steps from database")
            
        except Exception as e:
            print(f"❌ Error loading tutorial steps: {e}")
            
        return tutorial_steps
    
    def _extract_objects_from_step(self, step: TutorialStep) -> List[str]:
        """Extract object names that might be created or referenced in this step"""
        desc_lower = step.description.lower()
        objects = []
        
        # Common CATIA object patterns
        object_patterns = [
            r'plane\.(\d+)', r'point\.(\d+)', r'line\.(\d+)', r'spline\.(\d+)',
            r'surface\.(\d+)', r'extrude\.(\d+)', r'join\.(\d+)', r'thicksurface\.(\d+)',
            r'plane', r'point', r'line', r'spline', r'surface', r'extrude', r'join'
        ]
        
        import re
        for pattern in object_patterns:
            matches = re.findall(pattern, desc_lower)
            objects.extend([f"plane.{m}" if 'plane' in pattern else f"object.{m}" for m in matches])
        
        return objects
    
    def _update_object_context(self, step: TutorialStep, matches: List[MethodMatch]):
        """Update object context based on step execution and matched methods"""
        created_objects = self._extract_objects_from_step(step)
        
        for obj_name in created_objects:
            # Determine object type from the best matching method
            obj_type = "geometric_element"
            creation_method = matches[0].method_name if matches else "unknown"
            
            if "plane" in obj_name.lower():
                obj_type = "reference_plane"
            elif "point" in obj_name.lower():
                obj_type = "reference_point"
            elif "spline" in obj_name.lower():
                obj_type = "curve"
            elif "surface" in obj_name.lower():
                obj_type = "surface"
            
            context = ObjectContext(
                object_name=obj_name,
                object_type=obj_type,
                creation_step=step.step_number,
                creation_method=creation_method,
                properties={"description": step.description}
            )
            
            self.object_context.append(context)
            
        # Track objects created in this step
        self.step_objects[step.step_number] = created_objects
    
    def _get_context_for_step(self, step: TutorialStep) -> str:
        """Get relevant context from previous steps for this step"""
        context_info = []
        
        # Get objects created in previous steps
        previous_objects = []
        for prev_step in range(1, step.step_number):
            if prev_step in self.step_objects:
                previous_objects.extend(self.step_objects[prev_step])
        
        if previous_objects:
            context_info.append(f"Available objects from previous steps: {', '.join(previous_objects[-5:])}")  # Last 5 objects
        
        # Find objects referenced in current step
        step_desc_lower = step.description.lower()
        referenced_objects = []
        for obj_context in self.object_context:
            if obj_context.object_name.lower() in step_desc_lower:
                referenced_objects.append(f"{obj_context.object_name} (created in step {obj_context.creation_step})")
        
        if referenced_objects:
            context_info.append(f"Referenced objects: {', '.join(referenced_objects)}")
        
        return " | ".join(context_info) if context_info else ""
    
    def find_methods_for_steps(self, tutorial_steps: List[TutorialStep], 
                              confidence_threshold: float = 0.6) -> Dict[int, List[MethodMatch]]:
        """
        Find matching methods for all tutorial steps using hierarchical search
        
        Returns: Dict mapping step_number to list of MethodMatch objects
        """
        results = {}
        
        for step in tutorial_steps:
            print(f"\n🔍 Processing Step {step.step_number}: {step.title}")
            
            matches = self._search_for_step(step, confidence_threshold)
            results[step.step_number] = matches
            
            # Update object context after finding matches
            self._update_object_context(step, matches)
            
            if matches:
                print(f"   ✅ Found {len(matches)} method matches")
                for match in matches[:3]:  # Show top 3
                    print(f"      {match.method_signature} (confidence: {match.confidence_score:.3f})")
            else:
                print(f"   ❌ No methods found above confidence threshold")
        
        return results
    
    def _search_for_step(self, step: TutorialStep, threshold: float) -> List[MethodMatch]:
        """
        INTELLIGENCE ENHANCEMENT: Perform semantic hierarchical search for a single step
        
        Uses productive starting classes and intelligent semantic filtering
        """
        # Get context from previous steps
        context = self._get_context_for_step(step)
        if context:
            print(f"   🔗 Context: {context}")
        
        # ENHANCEMENT: Start with productive classes instead of abstract roots
        current_level = self.navigator.get_productive_starting_classes()
        best_matches = []
        search_depth = 0
        max_depth = 3  # Shorter depth since we start at productive level
        
        while current_level and search_depth < max_depth:
            print(f"   🔍 Search depth {search_depth}: analyzing {len(current_level)} classes")
            
            # COMPREHENSIVE SEMANTIC ENHANCEMENT: Deep understanding approach
            if len(current_level) > 10:
                print(f"   🧠 Comprehensive semantic analysis: {len(current_level)} classes")
                current_level = self._comprehensive_semantic_analysis(step, current_level, max_classes=20)
                print(f"   🧠 After comprehensive analysis: {len(current_level)} classes")
            
            # ENHANCED: Use both comprehensive semantic analysis results AND LLM ratings
            # Current_level already has relevance_score from comprehensive analysis
            semantic_ratings = [(cls, cls.relevance_score, f"Semantic analysis: {cls.relevance_score:.3f}") 
                               for cls in current_level if hasattr(cls, 'relevance_score')]
            
            # Also get LLM ratings for comparison/supplementation
            llm_ratings = self.analyzer.analyze_step_for_classes(step, current_level)
            
            # Combine and use the best approach
            if semantic_ratings:
                class_ratings = semantic_ratings
                print(f"   🧠 Using comprehensive semantic analysis ratings")
            else:
                class_ratings = llm_ratings
                print(f"   🤖 Using LLM analysis ratings")
            
            # Sort by relevance score
            class_ratings.sort(key=lambda x: x[1], reverse=True)
            
            # ALWAYS analyze methods at this level since we're starting with productive classes
            print(f"   🎯 Analyzing methods in top {min(5, len(class_ratings))} classes")
            for class_node, score, reasoning in class_ratings[:15]:  # Show top 15 for better coverage
                if score >= 0.1:  # Very low threshold for method analysis
                    print(f"      ⚙️  Analyzing {class_node.name} (score: {score:.3f})")
                    method_matches = self._analyze_methods_in_class(step, class_node, threshold)
                    best_matches.extend(method_matches)
            break  # Always stop after method analysis since we start with productive classes
            
            # Continue deeper - get children of best classes
            next_level = []
            for class_node, score, reasoning in class_ratings[:15]:  # Show top 15 for better coverage  # Top 5 classes
                if score >= threshold * 0.5:  # Even lower threshold for traversal
                    children = self.navigator.get_children(class_node.name)
                    next_level.extend(children)
            
            current_level = next_level
            search_depth += 1
        
        # Sort final matches by confidence
        best_matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Filter by threshold
        return [match for match in best_matches if match.confidence_score >= threshold]
    
    def _analyze_methods_in_class(self, step: TutorialStep, class_node: ClassNode, threshold: float) -> List[MethodMatch]:
        """
        ENHANCED METHOD-LEVEL ANALYSIS: Deep dive into individual method purposes
        This is the bottom level of the tree where actual matching happens
        """
        print(f"         🔬 Deep method analysis in {class_node.name} ({len(class_node.methods)} methods)")
        
        # Get method purposes from database for this class
        if hasattr(self, 'class_purposes') and class_node.name in self.class_purposes:
            method_purposes = self.class_purposes[class_node.name]
            print(f"         📋 Found {len(method_purposes)} methods with purposes in database")
        else:
            method_purposes = []
            print(f"         ⚠️  No method purposes found in database for {class_node.name}")
        
        matches = []
        analyzed_methods = 0
        
        # Analyze each method individually with its specific purpose
        for method_info in method_purposes:
            method_name = method_info['method_name']
            purpose = method_info['purpose']
            full_method = method_info['full_method']
            
            # Calculate semantic alignment between step and method purpose
            alignment_score = self._calculate_method_step_alignment(step, method_name, purpose)
            
            if alignment_score > threshold * 0.3:  # Lower threshold for method level
                # Get detailed reasoning from LLM
                reasoning = self._generate_method_reasoning(step, method_name, purpose, alignment_score)
                
                match = MethodMatch(
                    method_signature=full_method,
                    class_name=class_node.name,
                    method_name=method_name,
                    confidence=alignment_score,
                    reasoning=reasoning,
                    step_number=step.step_number
                )
                matches.append(match)
                analyzed_methods += 1
                
                print(f"         ✅ {method_name}: {alignment_score:.4f} | {purpose[:80]}...")
            
        print(f"         📊 Analyzed {analyzed_methods} methods, found {len(matches)} potential matches")
        
        # Also use LLM for broader analysis if database methods are limited
        if len(method_purposes) < 5 and len(class_node.methods) > len(method_purposes):
            print(f"         🤖 Supplementing with LLM analysis for remaining methods...")
            enhanced_class_node = self._enhance_class_with_descriptions(class_node)
            llm_ratings = self.analyzer.analyze_step_for_methods(step, enhanced_class_node)
            
            for method_sig, confidence, reasoning in llm_ratings:
                if confidence >= threshold and not any(m.method_signature == method_sig for m in matches):
                    # Extract method name from signature
                    method_name = method_sig.split('.')[-1] if '.' in method_sig else method_sig
                    match = MethodMatch(
                        method_signature=method_sig,
                        class_name=class_node.name,
                        method_name=method_name,
                        confidence=confidence,
                        reasoning=reasoning,
                        step_number=step.step_number
                    )
                    matches.append(match)
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)
    
    def _calculate_method_step_alignment(self, step: TutorialStep, method_name: str, method_purpose: str) -> float:
        """
        ENHANCED SEMANTIC ALIGNMENT: Calculate improved alignment between design step and method purpose
        
        This enhanced version uses more sophisticated scoring with better weight distribution
        and expanded vocabulary matching for higher accuracy.
        """
        
        # Extract and normalize text
        step_text = step.description.lower()
        purpose_text = method_purpose.lower()
        method_name_lower = method_name.lower()
        
        alignment_score = 0.0
        
        # 1. ENHANCED Direct keyword matching (25% weight) - improved with stemming-like approach
        step_keywords = set(step.keywords + step.description.split())
        step_keywords = {kw.lower().strip('.,!?()[]') for kw in step_keywords if len(kw) > 2}
        
        # Add root words for better matching
        expanded_keywords = step_keywords.copy()
        for keyword in step_keywords:
            if keyword.endswith('s') and len(keyword) > 3:
                expanded_keywords.add(keyword[:-1])  # Remove plural 's'
            if keyword.endswith('ing') and len(keyword) > 4:
                expanded_keywords.add(keyword[:-3])  # Remove 'ing'
        
        keyword_matches = sum(1 for keyword in expanded_keywords if keyword in purpose_text or keyword in method_name_lower)
        keyword_score = min(keyword_matches / max(len(expanded_keywords), 1), 1.0) * 1.5  # Boost good matches
        alignment_score += min(keyword_score, 1.0) * 0.25
        
        # 2. ENHANCED Action verb alignment (30% weight) - expanded vocabulary
        action_verbs = {
            'create': ['create', 'add', 'new', 'generate', 'build', 'make'],
            'initialize': ['initialize', 'init', 'start', 'begin', 'setup', 'launch'],
            'access': ['access', 'get', 'retrieve', 'obtain', 'fetch'],
            'configure': ['configure', 'set', 'setup', 'adjust', 'modify'],
            'define': ['define', 'specify', 'establish', 'determine'],
            'connect': ['connect', 'join', 'link', 'attach'],
            'modify': ['modify', 'change', 'update', 'edit', 'alter']
        }
        
        step_action_categories = []
        purpose_action_categories = []
        
        for category, verbs in action_verbs.items():
            if any(verb in step_text for verb in verbs):
                step_action_categories.append(category)
            if any(verb in purpose_text or verb in method_name_lower for verb in verbs):
                purpose_action_categories.append(category)
        
        if step_action_categories and purpose_action_categories:
            action_overlap = len(set(step_action_categories) & set(purpose_action_categories))
            action_score = (action_overlap / max(len(step_action_categories), 1)) * 1.2  # Boost action matches
            alignment_score += min(action_score, 1.0) * 0.30
        
        # 3. ENHANCED Object/target alignment (30% weight) - expanded CATIA vocabulary
        catia_objects = {
            'geometry': ['plane', 'point', 'line', 'surface', 'curve', 'spline', 'axis', 'coordinate', 'vector'],
            'creation': ['factory', 'hybrid', 'shape', 'element', 'feature'],
            'structure': ['document', 'part', 'body', 'assembly', 'component'],
            'reference': ['reference', 'datum', 'origin', 'system', 'frame'],
            'operations': ['project', 'extrude', 'revolve', 'sweep', 'loft', 'blend']
        }
        
        step_object_categories = []
        purpose_object_categories = []
        
        for category, objects in catia_objects.items():
            if any(obj in step_text for obj in objects):
                step_object_categories.append(category)
            if any(obj in purpose_text or obj in method_name_lower for obj in objects):
                purpose_object_categories.append(category)
        
        if step_object_categories and purpose_object_categories:
            object_overlap = len(set(step_object_categories) & set(purpose_object_categories))
            object_score = (object_overlap / max(len(step_object_categories), 1)) * 1.3  # Boost object matches
            alignment_score += min(object_score, 1.0) * 0.30
        
        # 4. Context-aware bonus scoring (15% weight)
        context_bonuses = 0.0
        
        # Bonus for method name relevance
        if any(word in method_name_lower for word in expanded_keywords):
            context_bonuses += 0.3
        
        # Bonus for CATIA workflow coherence
        if 'initialize' in step_text and any(word in purpose_text for word in ['application', 'catia', 'environment']):
            context_bonuses += 0.4
        
        if 'reference' in step_text and any(word in purpose_text for word in ['plane', 'axis', 'coordinate', 'origin']):
            context_bonuses += 0.4
        
        if 'create' in step_text and any(word in purpose_text for word in ['new', 'add', 'generate']):
            context_bonuses += 0.3
        
        alignment_score += min(context_bonuses, 1.0) * 0.15
        
        # Apply final boost for high-quality matches
        if alignment_score > 0.6:
            alignment_score = min(alignment_score * 1.1, 1.0)
        
        return min(alignment_score, 1.0)
    
    def _generate_method_reasoning(self, step: TutorialStep, method_name: str, method_purpose: str, score: float) -> str:
        """Generate human-readable reasoning for method selection"""
        
        confidence_level = "HIGH" if score > 0.7 else "MEDIUM" if score > 0.4 else "LOW"
        
        return (f"{confidence_level} confidence match: Method '{method_name}' aligns with step "
                f"'{step.title}' because {method_purpose[:150]}... "
                f"(Semantic alignment: {score:.3f})")
    
    
    def _enhance_class_with_descriptions(self, class_node: ClassNode) -> ClassNode:
        """Enhance class node with method descriptions from database"""
        enhanced_methods = {}
        
        for method_name, method_sig in class_node.methods.items():
            enhanced_methods[method_name] = method_sig
            
            # Add description if available
            if method_sig in self.method_descriptions:
                desc_info = self.method_descriptions[method_sig]
                purpose = desc_info.get('purpose', '')
                if purpose:
                    enhanced_methods[method_name] = f"{method_sig} | Purpose: {purpose[:200]}..."
        
        # Create enhanced class node
        enhanced_node = ClassNode(
            name=class_node.name,
            full_name=class_node.full_name,
            domain=class_node.domain,
            parent_classes=class_node.parent_classes,
            child_classes=class_node.child_classes,
            methods=enhanced_methods,
            description=class_node.description,
            relevance_score=class_node.relevance_score
        )
        
        return enhanced_node
    
    def _comprehensive_semantic_analysis(self, step: TutorialStep, classes: List[ClassNode], max_classes: int = 20) -> List[ClassNode]:
        """
        COMPREHENSIVE SEMANTIC ENHANCEMENT: Full understanding approach
        
        1. Read and understand the design step completely
        2. Examine ALL class purposes from database
        3. Perform semantic mapping between step intent and class capabilities
        4. Show class purposes for verification
        """
        
        print(f"   🧠 Deep semantic analysis: Understanding design step and examining {len(classes)} class purposes...")
        
        # Step 1: Understand the design step intent
        step_understanding = self._deep_understand_design_step(step)
        print(f"   📋 Step understanding: {step_understanding['primary_action']} - {step_understanding['catia_operation']}")
        
        # Step 2: Analyze each class with its purposes
        analyzed_classes = []
        
        for i, class_node in enumerate(classes):
            # Extract class purposes from method descriptions
            class_purposes = self._extract_class_purposes(class_node)
            
            # Calculate semantic alignment
            alignment_score = self._calculate_deep_semantic_alignment(step_understanding, class_node, class_purposes)
            
            if alignment_score > 0.05:  # Include more classes for comprehensive analysis
                class_node.relevance_score = alignment_score
                class_node.extracted_purposes = class_purposes  # Store for display
                analyzed_classes.append(class_node)
                
                # Show purposes for verification
                if i < 10:  # Show first 10 for verification
                    print(f"   📚 {class_node.name}: {class_purposes[:100]}... (score: {alignment_score:.3f})")
        
        # Sort by semantic alignment
        analyzed_classes.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"   🎯 Top semantic matches: {[f'{cls.name}({cls.relevance_score:.3f})' for cls in analyzed_classes[:5]]}")
        
        return analyzed_classes[:max_classes]
    
    def _deep_understand_design_step(self, step: TutorialStep) -> Dict:
        """Deep understanding of what the design step is trying to accomplish"""
        
        understanding = {
            'step_number': step.step_number,
            'primary_action': self._extract_primary_action(step),
            'catia_operation': self._identify_catia_operation_type(step),
            'modeling_intent': self._understand_modeling_intent(step),
            'required_capabilities': self._identify_required_capabilities(step)
        }
        
        return understanding
    
    def _extract_primary_action(self, step: TutorialStep) -> str:
        """Extract the primary action verb from the design step"""
        title_lower = step.title.lower()
        
        action_patterns = {
            'initialize': ['initialize', 'start', 'begin', 'setup'],
            'create': ['create', 'add', 'generate', 'build'],
            'define': ['define', 'set', 'establish', 'specify'],
            'configure': ['configure', 'setup', 'prepare', 'adjust'],
            'access': ['access', 'get', 'retrieve', 'obtain']
        }
        
        for action, patterns in action_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return action
        
        return 'execute'
    
    def _identify_catia_operation_type(self, step: TutorialStep) -> str:
        """Identify what type of CATIA operation this step represents"""
        
        desc_text = step.description.lower()
        
        if any(word in desc_text for word in ['catia', 'application', 'environment', 'workbench']):
            return 'application_control'
        elif any(word in desc_text for word in ['document', 'part', 'new']):
            return 'document_management'
        elif any(word in desc_text for word in ['plane', 'axis', 'reference', 'coordinate']):
            return 'reference_geometry'
        elif any(word in desc_text for word in ['hybrid', 'shape', 'factory', 'geometrical']):
            return 'geometry_factory'
        elif any(word in desc_text for word in ['spline', 'curve', 'surface', 'point']):
            return 'geometric_elements'
        else:
            return 'general_modeling'
    
    def _understand_modeling_intent(self, step: TutorialStep) -> str:
        """Understand the modeling intent behind the step"""
        
        desc_lower = step.description.lower()
        
        if 'initialize' in desc_lower:
            return 'setup_environment'
        elif 'configure' in desc_lower or 'set up' in desc_lower:
            return 'configure_workspace'
        elif 'create' in desc_lower and 'document' in desc_lower:
            return 'document_creation'
        elif 'access' in desc_lower or 'origin' in desc_lower:
            return 'access_references'
        else:
            return 'geometric_modeling'
    
    def _identify_required_capabilities(self, step: TutorialStep) -> List[str]:
        """Identify what capabilities are needed to execute this step"""
        
        desc_text = step.description.lower()
        capabilities = []
        
        if 'catia' in desc_text or 'application' in desc_text:
            capabilities.append('application_access')
        if 'document' in desc_text:
            capabilities.append('document_management')
        if 'factory' in desc_text or 'hybrid' in desc_text:
            capabilities.append('geometry_factory')
        if 'plane' in desc_text or 'reference' in desc_text:
            capabilities.append('reference_creation')
        
        return capabilities
    
    def _extract_class_purposes(self, class_node: ClassNode) -> str:
        """Extract comprehensive purposes from class methods using database"""
        
        purposes = []
        
        # Get purposes from method descriptions
        for method_name, method_sig in class_node.methods.items():
            if method_sig in self.method_descriptions:
                purpose = self.method_descriptions[method_sig].get('purpose', '')
                if purpose and len(purpose) > 20:  # Only meaningful purposes
                    purposes.append(purpose[:100])  # Limit length
        
        # Combine with class description
        if class_node.description:
            purposes.append(class_node.description[:100])
        
        # Create summary
        if purposes:
            return f"Domain: {class_node.domain}. Purposes: " + "; ".join(purposes[:3])
        else:
            return f"Domain: {class_node.domain}. Class with {len(class_node.methods)} methods."
    
    def _calculate_deep_semantic_alignment(self, step_understanding: Dict, class_node: ClassNode, class_purposes: str) -> float:
        """Calculate deep semantic alignment between step understanding and class purposes"""
        
        score = 0.0
        
        # 1. Operation type alignment (40% weight)
        catia_operation = step_understanding['catia_operation']
        operation_score = self._score_operation_alignment(catia_operation, class_node.domain, class_purposes)
        score += operation_score * 0.4
        
        # 2. Required capabilities alignment (30% weight)
        capabilities_score = self._score_capabilities_alignment(step_understanding['required_capabilities'], class_purposes)
        score += capabilities_score * 0.3
        
        # 3. Modeling intent alignment (30% weight)
        intent_score = self._score_intent_alignment(step_understanding['modeling_intent'], class_purposes)
        score += intent_score * 0.3
        
        return min(score, 1.0)
    
    def _score_operation_alignment(self, catia_operation: str, class_domain: str, class_purposes: str) -> float:
        """Score alignment between CATIA operation type and class capabilities"""
        
        operation_mappings = {
            'application_control': ['application', 'catia', 'interface'],
            'document_management': ['document', 'part', 'create'],
            'reference_geometry': ['reference', 'plane', 'axis', 'coordinate'],
            'geometry_factory': ['factory', 'hybrid', 'shape'],
            'geometric_elements': ['spline', 'curve', 'point', 'surface']
        }
        
        relevant_terms = operation_mappings.get(catia_operation, [])
        desc_text = f"{class_domain} {class_purposes}".lower()
        
        matches = sum(1 for term in relevant_terms if term in desc_text)
        return min(matches / len(relevant_terms) if relevant_terms else 0, 1.0)
    
    def _score_capabilities_alignment(self, required_capabilities: List[str], class_purposes: str) -> float:
        """Score how well class purposes align with required capabilities"""
        
        if not required_capabilities:
            return 0.5  # Neutral score
        
        purposes_lower = class_purposes.lower()
        matching_capabilities = 0
        
        for capability in required_capabilities:
            capability_terms = capability.split('_')
            if any(term in purposes_lower for term in capability_terms):
                matching_capabilities += 1
        
        return matching_capabilities / len(required_capabilities)
    
    def _score_intent_alignment(self, modeling_intent: str, class_purposes: str) -> float:
        """Score alignment between modeling intent and class purposes"""
        
        intent_keywords = {
            'setup_environment': ['initialize', 'setup', 'environment'],
            'configure_workspace': ['configure', 'set', 'workspace'],
            'document_creation': ['document', 'create', 'new'],
            'access_references': ['access', 'reference', 'origin'],
            'geometric_modeling': ['geometry', 'shape', 'model']
        }
        
        keywords = intent_keywords.get(modeling_intent, [])
        purposes_lower = class_purposes.lower()
        
        matches = sum(1 for keyword in keywords if keyword in purposes_lower)
        return min(matches / len(keywords) if keywords else 0, 1.0)
    
    def _analyze_step_semantic_context(self, step: TutorialStep) -> Dict:
        """Analyze the semantic context of a tutorial step"""
        
        context = {
            'step_number': step.step_number,
            'workflow_phase': self._determine_workflow_phase(step),
            'primary_intent': self._extract_primary_intent(step),
            'technical_level': self._assess_technical_level(step),
            'catia_domain': self._identify_catia_domain(step)
        }
        
        return context
    
    def _determine_workflow_phase(self, step: TutorialStep) -> str:
        """Determine which phase of the workflow this step belongs to"""
        
        step_num = step.step_number
        title_lower = step.title.lower()
        desc_lower = step.description.lower()
        
        # Phase 1: Initialization (Steps 1-5)
        if step_num <= 5 or any(word in title_lower for word in ['initialize', 'setup', 'environment', 'catia']):
            return 'initialization'
        
        # Phase 2: Reference setup (Steps 6-10)
        elif step_num <= 10 or any(word in title_lower for word in ['reference', 'plane', 'axis', 'coordinate']):
            return 'reference_setup'
        
        # Phase 3: Geometry creation (Steps 11-20)
        elif step_num <= 20 or any(word in title_lower for word in ['create', 'geometry', 'shape', 'spline']):
            return 'geometry_creation'
        
        # Phase 4: Advanced operations (Steps 21+)
        else:
            return 'advanced_operations'
    
    def _extract_primary_intent(self, step: TutorialStep) -> str:
        """Extract the primary intent/action of the step"""
        
        title_lower = step.title.lower()
        
        if 'initialize' in title_lower or 'setup' in title_lower:
            return 'setup'
        elif 'create' in title_lower or 'add' in title_lower:
            return 'create'
        elif 'define' in title_lower or 'set' in title_lower:
            return 'define'
        elif 'configure' in title_lower or 'adjust' in title_lower:
            return 'configure'
        else:
            return 'execute'
    
    def _assess_technical_level(self, step: TutorialStep) -> str:
        """Assess the technical complexity level of the step"""
        
        desc_lower = step.description.lower()
        
        if any(word in desc_lower for word in ['initialize', 'basic', 'simple']):
            return 'basic'
        elif any(word in desc_lower for word in ['configure', 'setup', 'define']):
            return 'intermediate'
        else:
            return 'advanced'
    
    def _identify_catia_domain(self, step: TutorialStep) -> str:
        """Identify which CATIA domain this step primarily involves"""
        
        desc_text = step.description.lower()
        
        if any(word in desc_text for word in ['application', 'document', 'catia', 'environment']):
            return 'application_management'
        elif any(word in desc_text for word in ['hybrid', 'shape', 'geometry', 'spline', 'curve']):
            return 'hybrid_shape_design'
        elif any(word in desc_text for word in ['part', 'body', 'solid', 'feature']):
            return 'mechanical_design'
        elif any(word in desc_text for word in ['sketch', '2d', 'constraint']):
            return 'sketching'
        else:
            return 'general'
    
    def _calculate_semantic_relevance(self, step_context: Dict, class_node: ClassNode) -> float:
        """Calculate semantic relevance score based on context understanding"""
        
        score = 0.0
        
        # Domain alignment scoring
        domain_score = self._score_domain_alignment(step_context['catia_domain'], class_node.domain)
        score += domain_score * 0.4
        
        # Workflow phase alignment
        phase_score = self._score_phase_alignment(step_context['workflow_phase'], class_node)
        score += phase_score * 0.3
        
        # Method purpose alignment (using database descriptions)
        purpose_score = self._score_purpose_alignment(step_context, class_node)
        score += purpose_score * 0.3
        
        return min(score, 1.0)
    
    def _score_domain_alignment(self, step_domain: str, class_domain: str) -> float:
        """Score how well the class domain aligns with the step domain"""
        
        domain_mappings = {
            'application_management': ['part_interfaces', 'application_interfaces'],
            'hybrid_shape_design': ['hybrid_shape_interfaces', 'mec_mod_interfaces'],
            'mechanical_design': ['mec_mod_interfaces', 'part_interfaces'],
            'sketching': ['sketcher_interfaces']
        }
        
        relevant_domains = domain_mappings.get(step_domain, [])
        
        for relevant_domain in relevant_domains:
            if relevant_domain in class_domain.lower():
                return 1.0
        
        return 0.2  # Some base relevance for all classes
    
    def _score_phase_alignment(self, workflow_phase: str, class_node: ClassNode) -> float:
        """Score how well the class aligns with the workflow phase"""
        
        class_name_lower = class_node.name.lower()
        
        if workflow_phase == 'initialization':
            if any(word in class_name_lower for word in ['application', 'document', 'catia']):
                return 1.0
        elif workflow_phase == 'reference_setup':
            if any(word in class_name_lower for word in ['reference', 'plane', 'axis', 'factory']):
                return 1.0
        elif workflow_phase == 'geometry_creation':
            if any(word in class_name_lower for word in ['hybrid', 'shape', 'factory', 'geometry']):
                return 1.0
        
        return 0.3  # Base score
    
    def _score_purpose_alignment(self, step_context: Dict, class_node: ClassNode) -> float:
        """Score based on method purposes from database descriptions"""
        
        if not hasattr(self, 'method_descriptions') or not self.method_descriptions:
            return 0.5  # Neutral score if no descriptions available
        
        relevant_methods = 0
        total_methods = len(class_node.methods)
        
        if total_methods == 0:
            return 0.0
        
        for method_name, method_sig in class_node.methods.items():
            if method_sig in self.method_descriptions:
                purpose = self.method_descriptions[method_sig].get('purpose', '').lower()
                
                # Check if purpose aligns with step intent
                step_intent = step_context['primary_intent']
                
                if step_intent == 'setup' and any(word in purpose for word in ['initialize', 'create', 'setup']):
                    relevant_methods += 1
                elif step_intent == 'create' and any(word in purpose for word in ['add', 'create', 'generate']):
                    relevant_methods += 1
                elif step_intent == 'define' and any(word in purpose for word in ['define', 'set', 'configure']):
                    relevant_methods += 1
        
        return relevant_methods / total_methods
    
    def _ensure_domain_diversity(self, scored_classes: List[ClassNode], max_classes: int) -> List[ClassNode]:
        """Ensure diverse domain representation in final class selection"""
        
        final_classes = []
        domain_counts = defaultdict(int)
        max_per_domain = max(2, max_classes // 4)  # At least 2, or quarter of total
        
        for class_node in scored_classes:
            domain = class_node.domain
            
            if domain_counts[domain] < max_per_domain and len(final_classes) < max_classes:
                final_classes.append(class_node)
                domain_counts[domain] += 1
        
        # Fill remaining slots with highest scoring classes regardless of domain
        remaining_slots = max_classes - len(final_classes)
        for class_node in scored_classes:
            if remaining_slots <= 0:
                break
            if class_node not in final_classes:
                final_classes.append(class_node)
                remaining_slots -= 1
        
        return final_classes
    
    def generate_report(self, results: Dict[int, List[MethodMatch]]) -> str:
        """
        Generate a comprehensive report of the search results
        """
        report = ["🎯 Hierarchical Search Results", "=" * 50, ""]
        
        total_steps = len(results)
        successful_steps = sum(1 for matches in results.values() if matches)
        
        report.append(f"📊 Summary:")
        report.append(f"   Total Steps: {total_steps}")
        report.append(f"   Successfully Matched: {successful_steps}")
        report.append(f"   Success Rate: {successful_steps/total_steps*100:.1f}%")
        report.append("")
        
        for step_num, matches in results.items():
            report.append(f"Step {step_num}:")
            if matches:
                for i, match in enumerate(matches, 1):
                    report.append(f"   {i}. {match.method_signature}")
                    report.append(f"      Class: {match.class_name}")
                    report.append(f"      Confidence: {match.confidence_score:.3f}")
                    report.append(f"      Reasoning: {match.reasoning}")
                    report.append("")
            else:
                report.append("   No matches found")
                report.append("")
        
        return "\n".join(report)


def create_sample_tutorial_steps() -> List[TutorialStep]:
    """Create sample tutorial steps for testing (fallback if database loading fails)"""
    return [
        TutorialStep(
            step_number=1,
            title="Initialize the design environment",
            description="Set up the basic environment and create a new document for the path design",
            expected_outcome="A new document is created and ready for design work",
            keywords=["initialize", "document", "environment", "create", "new"]
        ),
        TutorialStep(
            step_number=2,
            title="Create basic geometric shapes",
            description="Add fundamental geometric elements like points, lines, and curves",
            expected_outcome="Basic geometric shapes are available for path construction",
            keywords=["geometry", "shapes", "points", "lines", "curves", "create"]
        ),
        TutorialStep(
            step_number=3,
            title="Define path constraints",
            description="Set up constraints and parameters that will guide the path design",
            expected_outcome="Path constraints are defined and ready to influence design",
            keywords=["constraints", "parameters", "path", "define", "guide"]
        ),
        TutorialStep(
            step_number=4,
            title="Generate the path",
            description="Use the defined shapes and constraints to generate the actual path",
            expected_outcome="A complete path is generated based on the specified parameters",
            keywords=["generate", "path", "create", "build", "construct"]
        ),
        TutorialStep(
            step_number=5,
            title="Validate and optimize",
            description="Check the generated path for correctness and optimize if needed",
            expected_outcome="Path is validated and optimized for the intended use",
            keywords=["validate", "check", "optimize", "verify", "improve"]
        )
    ]


def main():
    """Main function to demonstrate the hierarchical search system"""
    print("🌳 Hierarchical Tree Search System for PyCATIA")
    print("=" * 60)
    
    # Configuration - Using your actual database files
    knowledge_graph_path = "knowledge_graph/pycatia_knowledge_graph.json"
    methods_database_path = "pycatia_methods.db"
    design_database_path = "design.db"
    
    try:
        # Initialize the search engine
        search_engine = HierarchicalSearchEngine(
            knowledge_graph_path, 
            methods_database_path, 
            design_database_path
        )
        
        # Load tutorial steps from database
        tutorial_steps = search_engine.load_tutorial_steps_from_db(template_id=1)
        
        # Fallback to sample steps if database loading failed
        if not tutorial_steps:
            print("⚠️  Using sample tutorial steps as fallback")
            tutorial_steps = create_sample_tutorial_steps()
        
        print(f"\n📚 Tutorial Steps to Process: {len(tutorial_steps)}")
        for step in tutorial_steps[:5]:  # Show first 5
            print(f"   {step.step_number}. {step.title}")
        if len(tutorial_steps) > 5:
            print(f"   ... and {len(tutorial_steps) - 5} more steps")
        
        # Show sample step details
        if tutorial_steps:
            sample_step = tutorial_steps[0]
            print(f"\n📋 Sample Step Details:")
            print(f"   Title: {sample_step.title}")
            print(f"   Description: {sample_step.description[:100]}...")
            print(f"   Keywords: {sample_step.keywords}")
        
        # Perform hierarchical search on first few steps for testing
        test_steps = tutorial_steps[:3]  # Test with first 3 steps
        print(f"\n🔍 Starting Hierarchical Search on {len(test_steps)} test steps...")
        results = search_engine.find_methods_for_steps(test_steps, confidence_threshold=0.1)
        
        # Generate and display report
        report = search_engine.generate_report(results)
        print(f"\n{report}")
        
        # Save results to file
        with open("hierarchical_search_results.txt", "w", encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n💾 Results saved to: hierarchical_search_results.txt")
        
        # ENHANCEMENT: Debug first hierarchy purposes
        print(f"\n🔍 DEBUG: First Hierarchy Purpose Verification")
        debug_first_hierarchy_purposes(search_engine)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def debug_first_hierarchy_purposes(search_engine):
    """Debug function to verify purpose matching for first hierarchy level"""
    
    print("=" * 60)
    root_classes = search_engine.navigator.get_root_classes()[:5]  # First 5 root classes
    
    for i, class_node in enumerate(root_classes, 1):
        print(f"\n{i}. Class: {class_node.name}")
        print(f"   Domain: {class_node.domain}")
        print(f"   Methods count: {len(class_node.methods)}")
        
        # Show first few methods and their purposes
        method_count = 0
        for method_name, method_sig in list(class_node.methods.items()):
            method_count += 1
            if method_sig in search_engine.method_descriptions:
                purpose = search_engine.method_descriptions[method_sig].get('purpose', 'No purpose found')
                print(f"   Method {method_count}: {method_name}")
                print(f"      Purpose: {purpose[:100]}...")
            else:
                print(f"   Method {method_count}: {method_name} - No purpose in database")
        
        if len(class_node.methods) > 3:
            print(f"   ... and {len(class_node.methods) - 3} more methods")


if __name__ == "__main__":
    main()
