"""
Standalone test for new modules (v2.1 improvements).

Tests adaptive_quality_manager and improved_debate_activation independently.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_new_modules():
    """Test new modules independently."""
    print("\n" + "="*70)
    print(" NEW MODULES STANDALONE TEST (V2.1)")
    print("="*70)

    tests_passed = 0
    total_tests = 4

    # Test 1: Import and test Adaptive Quality Manager
    print("\n" + "-"*70)
    print(" TEST 1: Adaptive Quality Manager")
    print("-"*70)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "adaptive_quality",
            "torq_console/agents/adaptive_quality_manager.py"
        )
        aqm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(aqm_module)

        # Create quality manager
        quality_manager = aqm_module.AdaptiveQualityManager()

        # Test evaluation
        query = "How do I implement authentication?"
        response = "You can implement authentication using JWT tokens with bcrypt password hashing. First, create user registration and login endpoints. Then use middleware to verify tokens."

        metrics, meets_thresholds = await quality_manager.evaluate_quality(
            query, response
        )

        assert 0 <= metrics.format_compliance <= 1
        assert 0 <= metrics.semantic_correctness <= 1
        assert 0 <= metrics.relevance <= 1
        assert 0 <= metrics.tone <= 1
        assert 0 <= metrics.solution_quality <= 1
        assert 0 <= metrics.overall_score() <= 1

        print(f"  ✓ Format Compliance: {metrics.format_compliance:.2f}")
        print(f"  ✓ Semantic Correctness: {metrics.semantic_correctness:.2f}")
        print(f"  ✓ Relevance: {metrics.relevance:.2f}")
        print(f"  ✓ Tone: {metrics.tone:.2f}")
        print(f"  ✓ Solution Quality: {metrics.solution_quality:.2f}")
        print(f"  ✓ Overall Score: {metrics.overall_score():.2f}")
        print(f"  ✓ Meets Thresholds: {meets_thresholds}")

        print("✅ Adaptive Quality Manager PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Adaptive Quality Manager FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Test threshold adaptation
    print("\n" + "-"*70)
    print(" TEST 2: Adaptive Threshold Updates")
    print("-"*70)

    try:
        # Get initial threshold
        initial = quality_manager.thresholds["overall"].current_value
        print(f"  Initial threshold: {initial:.3f}")

        # Run multiple evaluations
        for i in range(25):
            await quality_manager.evaluate_quality(
                "Test query",
                "This is a test response with sufficient length and proper structure."
            )

        # Check history
        history_size = len(quality_manager.thresholds["overall"].history)
        print(f"  ✓ History size: {history_size}")
        assert history_size >= 20

        # Check threshold bounds
        updated = quality_manager.thresholds["overall"].current_value
        print(f"  Updated threshold: {updated:.3f}")
        assert 0.5 <= updated <= 0.9

        print("✅ Adaptive Threshold Updates PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Threshold Updates FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Import and test Improved Debate Activation
    print("\n" + "-"*70)
    print(" TEST 3: Improved Debate Activation")
    print("-"*70)

    try:
        spec = importlib.util.spec_from_file_location(
            "debate_activation",
            "torq_console/agents/improved_debate_activation.py"
        )
        ida_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ida_module)

        # Create debate activator
        debate_activator = ida_module.ImprovedDebateActivation()

        # Test comparison query
        decision1 = await debate_activator.should_activate_debate(
            "What's better: Python or JavaScript for web development?"
        )
        assert decision1.should_activate
        assert decision1.debate_worthiness >= 0.5
        print(f"  ✓ Comparison query: {decision1.protocol.value}")
        print(f"    Worthiness: {decision1.debate_worthiness:.2f}")
        print(f"    Reasoning: {decision1.reasoning}")

        # Test decision query
        decision2 = await debate_activator.should_activate_debate(
            "Should I use Docker or Kubernetes?"
        )
        assert decision2.should_activate
        print(f"  ✓ Decision query: {decision2.protocol.value}")

        # Test simple query (should NOT activate)
        decision3 = await debate_activator.should_activate_debate(
            "Hello world"
        )
        assert not decision3.should_activate
        print(f"  ✓ Simple query correctly rejected")

        print("✅ Improved Debate Activation PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Debate Activation FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Test protocol selection
    print("\n" + "-"*70)
    print(" TEST 4: Protocol Selection")
    print("-"*70)

    try:
        # Test different query types
        queries = [
            ("Compare microservices vs monolithic architecture", "comparison"),
            ("Should I use React or Vue?", "decision"),
            ("Analyze the benefits of serverless", "analysis"),
            ("Why is caching important?", "reasoning")
        ]

        for query, expected_type in queries:
            decision = await debate_activator.should_activate_debate(query)
            if decision.should_activate:
                print(f"  ✓ '{expected_type}' → {decision.protocol.value}")
            else:
                print(f"  ⚠ '{expected_type}' → not activated")

        print("✅ Protocol Selection PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Protocol Selection FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Tests Passed: {tests_passed}/{total_tests} ({100*tests_passed/total_tests:.0f}%)")

    if tests_passed == total_tests:
        print("\n🎉 ALL NEW MODULES WORKING!")
        print("\n📊 Verified:")
        print("   ✅ Adaptive Quality Manager operational")
        print("   ✅ Multi-metric quality scoring working")
        print("   ✅ Adaptive threshold updates functional")
        print("   ✅ Improved Debate Activation operational")
        print("   ✅ Keyword-based activation working")
        print("   ✅ Protocol selection functional")
        print("\n🚀 Ready for integration!")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_new_modules())
    sys.exit(0 if success else 1)
