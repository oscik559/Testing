#!/usr/bin/env python3
"""
Comprehensive Test Script for Full Design Steps Analysis

Tests the enhanced hierarchical search system on all 29 design steps
and provides detailed analytics on:
1. Method matching performance
2. Confidence score distributions
3. Processing times
4. Coverage analysis
5. Improvement areas identification
"""

import time
import json
from collections import defaultdict, Counter
from statistics import mean, median
from testing_tree_hierachical_search import HierarchicalSearchEngine, TutorialStep

def analyze_full_system_performance():
    """Run comprehensive analysis on all design steps"""
    
    print("🚀 COMPREHENSIVE SYSTEM TEST - All Design Steps")
    print("=" * 60)
    
    # Initialize the search engine
    knowledge_graph_path = "knowledge_graph/pycatia_knowledge_graph.json"
    methods_db_path = "pycatia_methods.db"
    design_db_path = "design.db"
    
    search_engine = HierarchicalSearchEngine(
        knowledge_graph_path=knowledge_graph_path,
        methods_database_path=methods_db_path,
        design_database_path=design_db_path
    )
    
    # Load all tutorial steps
    tutorial_steps = search_engine.load_tutorial_steps_from_db(template_id=1)
    print(f"📋 Loaded {len(tutorial_steps)} design steps for analysis")
    
    # Test configuration
    confidence_thresholds = [0.3, 0.4, 0.5, 0.6]  # Test multiple thresholds
    
    # Performance tracking
    results = {}
    processing_times = []
    total_matches = 0
    
    print("\n🔍 DETAILED STEP-BY-STEP ANALYSIS")
    print("-" * 40)
    
    for i, step in enumerate(tutorial_steps, 1):
        print(f"\n📍 STEP {step.step_number}: {step.title}")
        print(f"   Description: {step.description[:100]}...")
        
        # Time the search
        start_time = time.time()
        
        # Find matches with default threshold
        matches = search_engine._search_for_step(step, threshold=0.4)
        
        end_time = time.time()
        processing_time = end_time - start_time
        processing_times.append(processing_time)
        
        # Analyze results
        result_analysis = {
            'step_number': step.step_number,
            'title': step.title,
            'description': step.description,
            'match_count': len(matches),
            'processing_time': processing_time,
            'top_matches': [],
            'confidence_range': {},
            'classes_involved': set(),
            'domains_covered': set()
        }
        
        if matches:
            # Analyze top matches
            for match in matches[:5]:  # Top 5 matches
                result_analysis['top_matches'].append({
                    'method': match.method_name,
                    'class': match.class_name,
                    'confidence': match.confidence,
                    'reasoning': match.reasoning[:100] + "..." if len(match.reasoning) > 100 else match.reasoning
                })
                result_analysis['classes_involved'].add(match.class_name)
            
            # Confidence distribution
            confidences = [m.confidence for m in matches]
            result_analysis['confidence_range'] = {
                'min': min(confidences),
                'max': max(confidences),
                'mean': mean(confidences),
                'median': median(confidences)
            }
            
            # Show results
            print(f"   ✅ Found {len(matches)} method matches (processed in {processing_time:.2f}s)")
            print(f"   🎯 Top matches:")
            for j, match in enumerate(matches[:3], 1):
                print(f"      {j}. {match.class_name}.{match.method_name} (confidence: {match.confidence:.4f})")
                print(f"         Reasoning: {match.reasoning[:80]}...")
            
            print(f"   📊 Confidence range: {result_analysis['confidence_range']['min']:.3f} - {result_analysis['confidence_range']['max']:.3f}")
            print(f"   🏛️  Classes involved: {len(result_analysis['classes_involved'])}")
            
        else:
            print(f"   ❌ No matches found (processed in {processing_time:.2f}s)")
            print(f"   🔍 This step may need improvement in:")
            print(f"      - Semantic understanding")
            print(f"      - Database coverage")
            print(f"      - Confidence threshold adjustment")
        
        results[step.step_number] = result_analysis
        total_matches += len(matches)
        
        # Show progress
        if i % 5 == 0:
            print(f"\n⏱️  Progress: {i}/{len(tutorial_steps)} steps completed")
    
    # COMPREHENSIVE ANALYSIS
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE ANALYSIS RESULTS")
    print("=" * 60)
    
    # Overall performance metrics
    steps_with_matches = sum(1 for r in results.values() if r['match_count'] > 0)
    steps_without_matches = len(results) - steps_with_matches
    avg_processing_time = mean(processing_times)
    total_processing_time = sum(processing_times)
    
    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"   Total steps analyzed: {len(tutorial_steps)}")
    print(f"   Steps with matches: {steps_with_matches} ({steps_with_matches/len(tutorial_steps)*100:.1f}%)")
    print(f"   Steps without matches: {steps_without_matches} ({steps_without_matches/len(tutorial_steps)*100:.1f}%)")
    print(f"   Total method matches found: {total_matches}")
    print(f"   Average matches per step: {total_matches/len(tutorial_steps):.1f}")
    print(f"   Average processing time: {avg_processing_time:.2f}s")
    print(f"   Total processing time: {total_processing_time:.2f}s")
    
    # Steps needing improvement
    no_match_steps = [r for r in results.values() if r['match_count'] == 0]
    low_match_steps = [r for r in results.values() if 0 < r['match_count'] < 5]
    
    print(f"\n🚨 STEPS NEEDING IMPROVEMENT:")
    if no_match_steps:
        print(f"   Steps with NO matches ({len(no_match_steps)}):")
        for step in no_match_steps:
            print(f"      Step {step['step_number']}: {step['title']}")
    
    if low_match_steps:
        print(f"   Steps with LOW matches (1-4) ({len(low_match_steps)}):")
        for step in low_match_steps:
            print(f"      Step {step['step_number']}: {step['title']} ({step['match_count']} matches)")
    
    # Confidence analysis
    all_confidences = []
    for r in results.values():
        if r['match_count'] > 0:
            matches = search_engine._search_for_step(
                TutorialStep(r['step_number'], r['title'], r['description'], "", []), 
                threshold=0.0  # Get all matches for analysis
            )
            all_confidences.extend([m.confidence for m in matches])
    
    if all_confidences:
        print(f"\n📈 CONFIDENCE SCORE ANALYSIS:")
        print(f"   Total matches across all steps: {len(all_confidences)}")
        print(f"   Confidence range: {min(all_confidences):.4f} - {max(all_confidences):.4f}")
        print(f"   Average confidence: {mean(all_confidences):.4f}")
        print(f"   Median confidence: {median(all_confidences):.4f}")
        
        # Confidence distribution
        high_conf = sum(1 for c in all_confidences if c >= 0.7)
        med_conf = sum(1 for c in all_confidences if 0.4 <= c < 0.7)
        low_conf = sum(1 for c in all_confidences if c < 0.4)
        
        print(f"   High confidence (≥0.7): {high_conf} ({high_conf/len(all_confidences)*100:.1f}%)")
        print(f"   Medium confidence (0.4-0.7): {med_conf} ({med_conf/len(all_confidences)*100:.1f}%)")
        print(f"   Low confidence (<0.4): {low_conf} ({low_conf/len(all_confidences)*100:.1f}%)")
    
    # Class usage analysis
    all_classes = set()
    class_usage = Counter()
    for r in results.values():
        all_classes.update(r['classes_involved'])
        for cls in r['classes_involved']:
            class_usage[cls] += 1
    
    print(f"\n🏛️  CLASS COVERAGE ANALYSIS:")
    print(f"   Total unique classes found: {len(all_classes)}")
    print(f"   Most frequently matched classes:")
    for cls, count in class_usage.most_common(10):
        print(f"      {cls}: {count} steps")
    
    # Processing time analysis
    slow_steps = [r for r in results.values() if r['processing_time'] > avg_processing_time * 2]
    if slow_steps:
        print(f"\n⏱️  PERFORMANCE ISSUES:")
        print(f"   Steps with slow processing (>{avg_processing_time*2:.2f}s):")
        for step in slow_steps:
            print(f"      Step {step['step_number']}: {step['processing_time']:.2f}s - {step['title']}")
    
    # IMPROVEMENT RECOMMENDATIONS
    print(f"\n💡 IMPROVEMENT RECOMMENDATIONS:")
    
    if no_match_steps:
        print(f"   1. CRITICAL: {len(no_match_steps)} steps have no matches")
        print(f"      - Review semantic analysis for these steps")
        print(f"      - Check if database has relevant methods")
        print(f"      - Consider lowering confidence thresholds")
    
    if low_match_steps:
        print(f"   2. MODERATE: {len(low_match_steps)} steps have few matches")
        print(f"      - Enhance method purpose descriptions")
        print(f"      - Improve semantic alignment algorithms")
    
    if slow_steps:
        print(f"   3. PERFORMANCE: {len(slow_steps)} steps are slow")
        print(f"      - Optimize class filtering")
        print(f"      - Cache LLM responses")
        print(f"      - Reduce search space earlier")
    
    low_confidence_ratio = low_conf / len(all_confidences) if all_confidences else 0
    if low_confidence_ratio > 0.3:
        print(f"   4. CONFIDENCE: {low_confidence_ratio*100:.1f}% of matches have low confidence")
        print(f"      - Improve semantic alignment scoring")
        print(f"      - Enhance step understanding algorithms")
        print(f"      - Add more contextual information")
    
    print(f"\n✅ SYSTEM STATUS: {'GOOD' if steps_with_matches/len(tutorial_steps) > 0.8 else 'NEEDS IMPROVEMENT'}")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    try:
        results = analyze_full_system_performance()
        
        # Save results for further analysis
        with open('comprehensive_test_results.json', 'w') as f:
            # Convert sets to lists for JSON serialization
            json_results = {}
            for step_num, result in results.items():
                json_result = result.copy()
                json_result['classes_involved'] = list(json_result['classes_involved'])
                json_result['domains_covered'] = list(json_result['domains_covered'])
                json_results[str(step_num)] = json_result
            
            json.dump(json_results, f, indent=2)
        
        print(f"\n💾 Results saved to: comprehensive_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()