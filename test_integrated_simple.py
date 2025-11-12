"""
Simple integration test for Enhanced Prince Flowers v2 core features.
Tests the 5 new advanced AI systems without Letta dependencies.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_simple_integration():
    """Test core advanced features."""
    print("\n" + "="*70)
    print(" ENHANCED PRINCE FLOWERS V2 - CORE FEATURES TEST")
    print("="*70)

    # Test each system independently first
    tests_passed = 0
    total_tests = 5

    # Test 1: Advanced Memory
    print("\n" + "-"*70)
    print(" TEST 1: Advanced Memory System")
    print("-"*70)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "advanced_memory",
            "torq_console/agents/advanced_memory_system.py"
        )
        ams = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ams)

        memory = ams.EnhancedMemorySystem()
        mem_id = await memory.add_memory(
            "Test message",
            ams.MemoryType.EPISODIC,
            0.8
        )
        assert mem_id, "Memory ID should not be empty"
        print("✅ Advanced Memory: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Advanced Memory: FAILED - {e}")

    # Test 2: Hierarchical Planner
    print("\n" + "-"*70)
    print(" TEST 2: Hierarchical Task Planner")
    print("-"*70)

    try:
        spec = importlib.util.spec_from_file_location(
            "hierarchical",
            "torq_console/agents/hierarchical_task_planner.py"
        )
        htp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(htp)

        planner = htp.HierarchicalTaskPlanner()
        result = await planner.execute_hierarchical_task("test query")
        assert result['status'] == 'success', "Should return success"
        print("✅ Hierarchical Planner: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Hierarchical Planner: FAILED - {e}")

    # Test 3: Meta-Learning
    print("\n" + "-"*70)
    print(" TEST 3: Meta-Learning Engine")
    print("-"*70)

    try:
        spec = importlib.util.spec_from_file_location(
            "meta_learning",
            "torq_console/agents/meta_learning_engine.py"
        )
        mle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mle)

        meta = mle.MetaLearningEngine()
        await meta.add_experience("t1", "search", "in", "out", 0.8)
        stats = await meta.get_stats()
        assert stats['experience_buffer_size'] == 1, "Should have 1 experience"
        print("✅ Meta-Learning: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Meta-Learning: FAILED - {e}")

    # Test 4: Multi-Agent Debate
    print("\n" + "-"*70)
    print(" TEST 4: Multi-Agent Debate System")
    print("-"*70)

    try:
        spec = importlib.util.spec_from_file_location(
            "debate",
            "torq_console/agents/multi_agent_debate.py"
        )
        mad = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mad)

        debate = mad.MultiAgentDebate(max_rounds=2)
        result = await debate.collaborative_reasoning("test query")
        assert result['status'] == 'success', "Should return success"
        print("✅ Multi-Agent Debate: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Multi-Agent Debate: FAILED - {e}")

    # Test 5: Self-Evaluation
    print("\n" + "-"*70)
    print(" TEST 5: Self-Evaluation System")
    print("-"*70)

    try:
        spec = importlib.util.spec_from_file_location(
            "self_eval",
            "torq_console/agents/self_evaluation_system.py"
        )
        ses = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ses)

        eval_sys = ses.SelfEvaluationSystem()
        result = await eval_sys.evaluate_response("query", "response")
        assert 0 <= result.confidence <= 1, "Confidence should be in [0,1]"
        assert 0 <= result.quality_score <= 1, "Quality should be in [0,1]"
        print("✅ Self-Evaluation: PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Self-Evaluation: FAILED - {e}")

    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Tests Passed: {tests_passed}/{total_tests} ({100*tests_passed/total_tests:.0f}%)")

    if tests_passed == total_tests:
        print("\n🎉 ALL CORE SYSTEMS OPERATIONAL!")
        print("\n📊 Verified Systems:")
        print("   ✅ Advanced Memory Integration")
        print("   ✅ Hierarchical Task Planning")
        print("   ✅ Meta-Learning Engine")
        print("   ✅ Multi-Agent Debate System")
        print("   ✅ Self-Evaluation System")
        print("\n🚀 Ready for full integration!")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_integration())
    sys.exit(0 if success else 1)
