#!/usr/bin/env python3
"""
Test all improvements together on sample steps
"""

import sys
sys.path.append('.')

from testing_tree_hierachical_search import HierarchicalSearchEngine, TutorialStep
import time

def test_all_improvements():
    """Test the enhanced system with all improvements"""
    
    print("🧪 TESTING ALL IMPROVEMENTS")
    print("=" * 50)
    
    # Initialize the enhanced search engine
    search_engine = HierarchicalSearchEngine(
        knowledge_graph_path="knowledge_graph/pycatia_knowledge_graph.json",
        methods_database_path="pycatia_methods.db", 
        design_database_path="design.db"
    )
    
    # Test on key steps that showed problems before
    test_steps = [
        TutorialStep(8, "Create an offset plane","Create a plane of type (offset from plane) with reference to the zx plane, and offset by 20mm", "", []),
        TutorialStep(10, "Create reference line", "Create a Line - Point-Direction type using Plane.1 as Direction", "", []),
    ]
    
    print(f"📋 Testing {len(test_steps)} key steps with all improvements")
    
    results = {}
    total_matches = 0
    high_confidence_matches = 0
    
    for step in test_steps:
        print(f"\n📍 STEP {step.step_number}: {step.title}")
        print(f"   Description: {step.description}")
        
        start_time = time.time()
        matches = search_engine._search_for_step(step, threshold=0.4)
        end_time = time.time()
        
        results[step.step_number] = matches
        total_matches += len(matches)
        
        if matches:
            confidences = [m.confidence for m in matches]
            high_conf = sum(1 for c in confidences if c >= 0.6)
            high_confidence_matches += high_conf
            
            print(f"   ✅ Found {len(matches)} matches in {end_time-start_time:.2f}s")
            print(f"   📊 Confidence: min={min(confidences):.3f}, max={max(confidences):.3f}, avg={sum(confidences)/len(confidences):.3f}")
            print(f"   🎯 High confidence (≥0.6): {high_conf}/{len(matches)} ({high_conf/len(matches)*100:.1f}%)")
            
            print("   Top matches:")
            for i, match in enumerate(matches[:3], 1):
                print(f"      {i}. {match.class_name}.{match.method_name} - {match.confidence:.3f}")
        else:
            print(f"   ❌ No matches found")
    
    # Summary
    print(f"\n🎯 ENHANCED SYSTEM PERFORMANCE SUMMARY")
    print("=" * 50)
    print(f"   Total steps tested: {len(test_steps)}")
    print(f"   Steps with matches: {len([r for r in results.values() if r])}/{len(test_steps)} ({len([r for r in results.values() if r])/len(test_steps)*100:.1f}%)")
    print(f"   Total matches found: {total_matches}")
    print(f"   High confidence matches: {high_confidence_matches}/{total_matches} ({high_confidence_matches/total_matches*100:.1f}%)" if total_matches > 0 else "   No matches for confidence analysis")
    print(f"   Average matches per step: {total_matches/len(test_steps):.1f}")
    
    # Check object context tracking
    print(f"\n🔗 OBJECT CONTEXT TRACKING")
    print(f"   Objects tracked: {len(search_engine.object_context)}")
    for obj in search_engine.object_context[-5:]:  # Show last 5
        print(f"      {obj.object_name} ({obj.object_type}) - created in step {obj.creation_step}")
    
    return results

if __name__ == "__main__":
    test_all_improvements()