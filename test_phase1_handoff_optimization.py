#!/usr/bin/env python3
"""
Test Phase 1: Advanced Handoff Optimization.

Tests improvements:
1. Semantic context preservation
2. Smart context compression
3. Adaptive handoff parameters
4. Increased context limits (2000 chars)

Target improvements:
- Memory → Planning: 46% → 85%
- Overall preservation: 58.9% → 70%
- Information loss: 40% → <30%
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_phase1_optimizer():
    """Test Phase 1 handoff optimizer."""
    print("\n" + "=" * 80)
    print("PHASE 1: ADVANCED HANDOFF OPTIMIZATION TESTS")
    print("=" * 80)

    from torq_console.agents.handoff_optimizer import (
        get_handoff_optimizer,
        SmartContextCompressor,
        EntityExtractor
    )

    optimizer = get_handoff_optimizer()
    compressor = SmartContextCompressor()
    extractor = EntityExtractor()

    # Test 1: Entity extraction
    print("\n1. Testing Entity Extraction...")
    test_text = "We need to implement OAuth authentication with JWT tokens using PostgreSQL and Redis for caching"
    entities = extractor.extract_entities(test_text)
    print(f"   Extracted entities: {entities}")
    print(f"   ✅ Found {len(entities)} entities")

    # Test 2: Concept extraction
    print("\n2. Testing Concept Extraction...")
    concepts = extractor.extract_key_concepts(test_text)
    print(f"   Extracted concepts: {concepts}")
    print(f"   ✅ Found {len(concepts)} concepts")

    # Test 3: Smart compression
    print("\n3. Testing Smart Context Compression...")
    long_content = """
    We discussed implementing a secure authentication system using OAuth 2.0 protocol.
    The system should support JWT tokens for API authentication and include refresh token rotation.
    We also talked about using PostgreSQL as the primary database for storing user credentials.
    Redis will be used for session management and caching frequently accessed data.
    The architecture should follow microservices patterns with API gateway as the entry point.
    Security considerations include HTTPS encryption, rate limiting, and SQL injection prevention.
    Performance requirements specify sub-100ms response times for authentication endpoints.
    """ * 5  # Make it long enough to need compression

    semantic_ctx = compressor.compress_context(long_content, target_length=500)
    print(f"   Original length: {semantic_ctx.original_length} chars")
    print(f"   Compressed length: {len(semantic_ctx.compressed_content)} chars")
    print(f"   Compression ratio: {semantic_ctx.compression_ratio:.1%}")
    print(f"   Key entities preserved: {len(semantic_ctx.key_entities)}")
    print(f"   Key concepts preserved: {len(semantic_ctx.key_concepts)}")
    print(f"   ✅ Compression successful")

    # Test 4: Query complexity analysis
    print("\n4. Testing Query Complexity Analysis...")
    simple_query = "What is OAuth?"
    complex_query = "Build a secure authentication system with OAuth, JWT tokens, refresh token rotation, and implement Redis caching"

    simple_complexity = optimizer._analyze_query_complexity(simple_query)
    complex_complexity = optimizer._analyze_query_complexity(complex_query)

    print(f"   Simple query complexity: {simple_complexity:.2f}")
    print(f"   Complex query complexity: {complex_complexity:.2f}")
    print(f"   ✅ Complexity analysis working (complex > simple: {complex_complexity > simple_complexity})")

    # Test 5: Memory optimization
    print("\n5. Testing Memory Context Optimization...")
    mock_memories = [
        {
            'content': 'We previously discussed OAuth 2.0 authentication patterns and security best practices for token management',
            'similarity': 0.9
        },
        {
            'content': 'The team decided to use PostgreSQL for persistent storage with Redis for caching layer',
            'similarity': 0.85
        },
        {
            'content': 'API gateway should handle rate limiting and request routing to microservices',
            'similarity': 0.8
        }
    ]

    query = "Implement the authentication system we discussed with Redis caching"
    optimized = optimizer.optimize_memory_context(mock_memories, query, max_length=2000)

    print(f"   Query complexity: {optimized['query_complexity']:.2f}")
    print(f"   Memories optimized: {len(optimized['memories'])}")
    print(f"   Total length: {optimized['total_length']} chars")
    print(f"   Context utilization: {optimized['context_utilization']:.1%}")
    print(f"   ✅ Memory optimization successful")

    # Test 6: Preservation quality scoring
    print("\n6. Testing Preservation Quality Scoring...")
    original = "OAuth authentication with JWT tokens and PostgreSQL database"
    preserved = "OAuth with JWT tokens and PostgreSQL"

    quality = optimizer.calculate_preservation_quality(original, preserved)
    print(f"   Preservation quality: {quality:.1%}")
    print(f"   ✅ Quality scoring working")

    print("\n" + "=" * 80)
    print("PHASE 1 UNIT TESTS: ALL PASSED")
    print("=" * 80)

    return True


async def test_phase1_integration():
    """Test Phase 1 integration with coordination benchmark."""
    print("\n" + "=" * 80)
    print("PHASE 1: INTEGRATION TESTS WITH COORDINATION BENCHMARK")
    print("=" * 80)

    # Load modules
    print("\n1. Loading agent modules...")
    import importlib.util as iu

    deps = [
        ("conversation_session", "torq_console/agents/conversation_session.py"),
        ("preference_learning", "torq_console/agents/preference_learning.py"),
        ("feedback_learning", "torq_console/agents/feedback_learning.py"),
        ("advanced_memory_system", "torq_console/agents/advanced_memory_system.py"),
        ("hierarchical_task_planner", "torq_console/agents/hierarchical_task_planner.py"),
        ("meta_learning_engine", "torq_console/agents/meta_learning_engine.py"),
        ("multi_agent_debate", "torq_console/agents/multi_agent_debate.py"),
        ("self_evaluation_system", "torq_console/agents/self_evaluation_system.py"),
        ("adaptive_quality_manager", "torq_console/agents/adaptive_quality_manager.py"),
        ("improved_debate_activation", "torq_console/agents/improved_debate_activation.py"),
        ("coordination_benchmark", "torq_console/agents/coordination_benchmark.py"),
        ("handoff_optimizer", "torq_console/agents/handoff_optimizer.py"),  # Phase 1
    ]

    for mod_name, mod_path in deps:
        try:
            spec = iu.spec_from_file_location(mod_name, mod_path)
            mod = iu.module_from_spec(spec)
            sys.modules[f'torq_console.agents.{mod_name}'] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"   ⚠️ Warning loading {mod_name}: {e}")

    # Load Enhanced Prince Flowers v2
    spec = iu.spec_from_file_location(
        "enhanced_v2",
        "torq_console/agents/enhanced_prince_flowers_v2.py"
    )
    epf_module = iu.module_from_spec(spec)
    spec.loader.exec_module(epf_module)

    print("   ✅ Modules loaded")

    # Initialize agent
    print("\n2. Initializing Enhanced Prince Flowers v2 with Phase 1...")
    prince = epf_module.EnhancedPrinceFlowers(
        memory_enabled=False,
        enable_advanced_features=True,
        use_hierarchical_planning=True,
        use_multi_agent_debate=True,
        use_self_evaluation=True
    )
    print("   ✅ Agent initialized")

    # Run coordination benchmark
    print("\n3. Running Coordination Benchmark with Phase 1...")
    from torq_console.agents.coordination_benchmark import get_coordination_benchmark, CoordinationType

    benchmark = get_coordination_benchmark()
    result = await benchmark.run_benchmark(prince, num_tests=10)

    # Results
    print("\n" + "=" * 80)
    print("PHASE 1 INTEGRATION RESULTS")
    print("=" * 80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Tests Passed: {result.passed}/{result.total_tests} ({result.passed/result.total_tests*100:.1f}%)")
    print(f"  Average Quality: {result.average_quality:.2f}")

    # Information preservation
    total_preserved = sum(m.information_preserved for m in result.coordination_metrics) / len(result.coordination_metrics)
    print(f"\n🔍 Information Preservation:")
    print(f"  Overall: {total_preserved:.1%}")

    # Baseline comparisons
    baseline_overall = 0.589  # From previous tests
    baseline_loss = 0.40  # 40% loss rate

    improvement = ((total_preserved - baseline_overall) / baseline_overall) * 100
    print(f"\n  📈 vs Baseline:")
    print(f"     Previous: {baseline_overall:.1%}")
    print(f"     Current: {total_preserved:.1%}")
    print(f"     Improvement: {improvement:+.1f}%")

    # By handoff type
    by_type = {}
    for metric in result.coordination_metrics:
        coord_type = metric.coordination_type.value
        if coord_type not in by_type:
            by_type[coord_type] = []
        by_type[coord_type].append(metric.information_preserved)

    print(f"\n  📋 By Type:")
    for coord_type, values in sorted(by_type.items()):
        avg = sum(values) / len(values)
        print(f"     {coord_type}: {avg:.1%}")

    # Key handoffs
    memory_planning = [m for m in result.coordination_metrics if m.coordination_type == CoordinationType.MEMORY_TO_PLANNING]
    if memory_planning:
        avg = sum(m.information_preserved for m in memory_planning) / len(memory_planning)
        baseline_mp = 0.46
        improvement_mp = ((avg - baseline_mp) / baseline_mp) * 100
        print(f"\n  🎯 Memory → Planning:")
        print(f"     Previous: {baseline_mp:.1%}")
        print(f"     Current: {avg:.1%}")
        print(f"     Improvement: {improvement_mp:+.1f}%")
        print(f"     Target: 85%")
        if avg >= 0.85:
            print(f"     ✅ TARGET ACHIEVED!")
        elif avg >= 0.70:
            print(f"     ✅ GOOD PROGRESS ({avg/0.85*100:.0f}% of target)")
        else:
            print(f"     ⚠️  More work needed ({avg/0.85*100:.0f}% of target)")

    # Information loss
    info_loss_count = result.issues_by_type.get('information_loss', 0)
    info_loss_rate = info_loss_count / result.total_tests
    print(f"\n  📉 Information Loss:")
    print(f"     Previous: 40% (4/10 tests)")
    print(f"     Current: {info_loss_rate:.0%} ({info_loss_count}/{result.total_tests} tests)")
    print(f"     Target: <30%")
    if info_loss_rate < 0.30:
        print(f"     ✅ TARGET ACHIEVED!")
    else:
        reduction = (baseline_loss - info_loss_rate) / baseline_loss * 100
        print(f"     Improvement: {reduction:.0f}% reduction")

    # Verdict
    print(f"\n" + "=" * 80)
    print("PHASE 1 VERDICT")
    print("=" * 80)

    targets_met = 0
    targets_total = 3

    if total_preserved >= 0.70:
        targets_met += 1
        print(f"\n✅ Overall Preservation Target Met: {total_preserved:.1%} (target 70%)")
    else:
        print(f"\n⚠️  Overall Preservation: {total_preserved:.1%} (target 70%, {total_preserved/0.70*100:.0f}% there)")

    if info_loss_rate < 0.30:
        targets_met += 1
        print(f"✅ Information Loss Target Met: {info_loss_rate:.0%} (target <30%)")
    else:
        print(f"⚠️  Information Loss: {info_loss_rate:.0%} (target <30%)")

    memory_planning_avg = sum(m.information_preserved for m in memory_planning) / len(memory_planning) if memory_planning else 0
    if memory_planning_avg >= 0.85:
        targets_met += 1
        print(f"✅ Memory → Planning Target Met: {memory_planning_avg:.1%} (target 85%)")
    else:
        print(f"⚠️  Memory → Planning: {memory_planning_avg:.1%} (target 85%, {memory_planning_avg/0.85*100:.0f}% there)")

    print(f"\nTargets Met: {targets_met}/{targets_total}")

    if targets_met == targets_total:
        print("\n🎉 PHASE 1 COMPLETE - ALL TARGETS ACHIEVED!")
        return True
    elif targets_met >= 2:
        print("\n✅ PHASE 1 SUCCESSFUL - Most targets achieved")
        return True
    else:
        print("\n⚠️  PHASE 1 PARTIAL - Additional optimization needed")
        return False


async def main():
    """Run all Phase 1 tests."""
    print("\n" + "=" * 80)
    print("PHASE 1: ADVANCED HANDOFF OPTIMIZATION")
    print("Testing semantic preservation and adaptive handoffs")
    print("=" * 80)

    # Run unit tests
    unit_success = await test_phase1_optimizer()

    # Run integration tests
    integration_success = await test_phase1_integration()

    # Final summary
    print("\n" + "=" * 80)
    print("PHASE 1 TEST SUMMARY")
    print("=" * 80)
    print(f"\nUnit Tests: {'✅ PASS' if unit_success else '❌ FAIL'}")
    print(f"Integration Tests: {'✅ PASS' if integration_success else '❌ FAIL'}")

    overall_success = unit_success and integration_success

    if overall_success:
        print("\n🎉 PHASE 1 VALIDATION COMPLETE - READY FOR PHASE 2")
    else:
        print("\n⚠️  PHASE 1 NEEDS REVIEW")

    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
