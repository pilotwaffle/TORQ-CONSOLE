"""
Validation test for Enhanced Prince Flowers v2.1 improvements.

Tests the integration of:
1. Adaptive Quality Manager
2. Improved Debate Activation

Verifies:
- Systems initialize correctly
- Improved debate activation works with keywords
- Adaptive quality manager provides multi-metric scoring
- Stats include new systems
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_v2_improvements():
    """Test v2.1 improvements."""
    print("\n" + "="*70)
    print(" ENHANCED PRINCE FLOWERS V2.1 - IMPROVEMENTS VALIDATION")
    print("="*70)

    tests_passed = 0
    total_tests = 6

    # Test 1: Import and initialize v2.1
    print("\n" + "-"*70)
    print(" TEST 1: Import and Initialize v2.1")
    print("-"*70)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "enhanced_v2",
            "torq_console/agents/enhanced_prince_flowers_v2.py"
        )
        epf_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(epf_module)

        # Create instance
        prince = epf_module.EnhancedPrinceFlowers(
            memory_enabled=False,  # Disable Letta for testing
            enable_advanced_features=True,
            use_hierarchical_planning=True,
            use_multi_agent_debate=True,
            use_self_evaluation=True
        )

        # Check new systems initialized
        assert hasattr(prince, 'quality_manager'), "Quality manager should be initialized"
        assert hasattr(prince, 'debate_activator'), "Debate activator should be initialized"

        print("✅ v2.1 initialized with new systems")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Initialization failed: {e}")

    # Test 2: Test Improved Debate Activation
    print("\n" + "-"*70)
    print(" TEST 2: Improved Debate Activation")
    print("-"*70)

    try:
        # Test comparison query (should activate)
        decision1 = await prince.debate_activator.should_activate_debate(
            "What's better: Python or JavaScript?"
        )
        assert decision1.should_activate, "Comparison query should activate debate"
        assert decision1.debate_worthiness >= 0.5, "Should have high worthiness"
        print(f"  ✓ Comparison query activated: {decision1.protocol.value}")
        print(f"    Reasoning: {decision1.reasoning}")

        # Test decision query (should activate)
        decision2 = await prince.debate_activator.should_activate_debate(
            "Should I use Docker or Kubernetes?"
        )
        assert decision2.should_activate, "Decision query should activate debate"
        print(f"  ✓ Decision query activated: {decision2.protocol.value}")

        # Test simple query (should NOT activate)
        decision3 = await prince.debate_activator.should_activate_debate(
            "Hello, how are you?"
        )
        assert not decision3.should_activate, "Simple query should not activate"
        print(f"  ✓ Simple query correctly rejected")

        print("✅ Improved Debate Activation working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Debate activation failed: {e}")

    # Test 3: Test Adaptive Quality Manager
    print("\n" + "-"*70)
    print(" TEST 3: Adaptive Quality Manager")
    print("-"*70)

    try:
        # Test quality evaluation
        query = "How do I implement authentication?"
        response = "You can implement authentication using JWT tokens with bcrypt password hashing. First, create user registration and login endpoints. Then use middleware to verify tokens."

        metrics, meets_thresholds = await prince.quality_manager.evaluate_quality(
            query, response
        )

        assert 0 <= metrics.format_compliance <= 1, "Format score should be 0-1"
        assert 0 <= metrics.semantic_correctness <= 1, "Semantic score should be 0-1"
        assert 0 <= metrics.relevance <= 1, "Relevance score should be 0-1"
        assert 0 <= metrics.tone <= 1, "Tone score should be 0-1"
        assert 0 <= metrics.solution_quality <= 1, "Solution score should be 0-1"
        assert 0 <= metrics.overall_score() <= 1, "Overall score should be 0-1"

        print(f"  ✓ Format Compliance: {metrics.format_compliance:.2f}")
        print(f"  ✓ Semantic Correctness: {metrics.semantic_correctness:.2f}")
        print(f"  ✓ Relevance: {metrics.relevance:.2f}")
        print(f"  ✓ Tone: {metrics.tone:.2f}")
        print(f"  ✓ Solution Quality: {metrics.solution_quality:.2f}")
        print(f"  ✓ Overall Score: {metrics.overall_score():.2f}")
        print(f"  ✓ Meets Thresholds: {meets_thresholds}")

        print("✅ Adaptive Quality Manager working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Quality manager failed: {e}")

    # Test 4: Test Adaptive Threshold Updates
    print("\n" + "-"*70)
    print(" TEST 4: Adaptive Threshold Updates")
    print("-"*70)

    try:
        # Get initial threshold
        initial_threshold = prince.quality_manager.thresholds["overall"].current_value
        print(f"  Initial threshold: {initial_threshold:.3f}")

        # Evaluate multiple responses to trigger threshold update
        for i in range(25):  # Need 20+ for threshold update
            await prince.quality_manager.evaluate_quality(
                "Test query",
                "Test response with sufficient length and structure."
            )

        # Check if history accumulated
        history_size = len(prince.quality_manager.thresholds["overall"].history)
        assert history_size >= 20, "Should have accumulated 20+ evaluations"
        print(f"  ✓ Accumulated {history_size} evaluations")

        # Threshold should remain within bounds
        updated_threshold = prince.quality_manager.thresholds["overall"].current_value
        assert 0.5 <= updated_threshold <= 0.9, "Threshold should be within bounds"
        print(f"  Updated threshold: {updated_threshold:.3f}")

        print("✅ Adaptive threshold updates working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Threshold updates failed: {e}")

    # Test 5: Test Drift Detection
    print("\n" + "-"*70)
    print(" TEST 5: Drift Detection")
    print("-"*70)

    try:
        # Get performance history size
        perf_size = len(prince.quality_manager.performance_history)
        print(f"  Performance history size: {perf_size}")

        # Check drift status
        drift_status = prince.quality_manager.get_threshold_status()
        assert "drift_detected" in drift_status, "Should have drift status"
        print(f"  ✓ Drift detected: {drift_status['drift_detected']}")

        # Get recent performance
        recent_perf = prince.quality_manager.get_recent_performance(last_n=20)
        if recent_perf:
            print(f"  ✓ Average score: {recent_perf['average_score']:.2f}")
            print(f"  ✓ Pass rate: {recent_perf['pass_rate']:.2f}")

        print("✅ Drift detection working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Drift detection failed: {e}")

    # Test 6: Test Stats Integration
    print("\n" + "-"*70)
    print(" TEST 6: Stats Integration")
    print("-"*70)

    try:
        stats = prince.get_stats()

        assert "advanced_systems" in stats, "Should have advanced systems stats"
        advanced = stats["advanced_systems"]

        # Check new systems in stats
        assert "adaptive_quality_manager" in advanced, "Should have quality manager stats"
        assert "improved_debate_activation" in advanced, "Should have debate activator stats"

        quality_stats = advanced["adaptive_quality_manager"]
        assert "thresholds" in quality_stats, "Should have threshold info"
        assert "drift_detected" in quality_stats, "Should have drift status"

        activation_stats = advanced["improved_debate_activation"]
        assert "comparison_keywords" in activation_stats, "Should have keyword counts"

        print(f"  ✓ Quality Manager Stats: {len(quality_stats)} keys")
        print(f"  ✓ Debate Activation Stats: {len(activation_stats)} keys")
        print(f"  ✓ Thresholds tracked: {len(quality_stats['thresholds'])}")

        print("✅ Stats integration working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Stats integration failed: {e}")

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Tests Passed: {tests_passed}/{total_tests} ({100*tests_passed/total_tests:.0f}%)")

    if tests_passed == total_tests:
        print("\n🎉 ALL V2.1 IMPROVEMENTS WORKING!")
        print("\n📊 Verified Improvements:")
        print("   ✅ Adaptive Quality Manager integrated")
        print("   ✅ Improved Debate Activation integrated")
        print("   ✅ Multi-metric quality scoring operational")
        print("   ✅ Keyword-based debate triggers working")
        print("   ✅ Adaptive threshold updates functional")
        print("   ✅ Drift detection operational")
        print("   ✅ Stats include new systems")
        print("\n🚀 Ready for agentic testing!")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_v2_improvements())
    sys.exit(0 if success else 1)
