TO DO

Hierarchical Tree Search System for PyKTR API Method Matching

Implements a top-down hierarchical search that uses:
1. Knowledge graph structure for efficient tree traversal
2. LLM semantic analysis for step understanding
3. Database descriptions for context-aware matching
4. Rating system to progressively narrow down from classes to methods

The approach:
- Start with root classes from knowledge graph
- Use LLM to analyze tutorial steps and rate class relevance
- Navigate down the hierarchy based on ratings
- Continue until finding the most appropriate methods

