#!/usr/bin/env python3
"""
Focused test for agent handoff scenarios.

Tests scenarios that specifically exercise the improved handoffs:
1. Complex queries requiring Memory → Planning
2. Decision queries requiring Debate → Evaluation
3. Multi-step queries exercising full pipeline
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))


class HandoffTest:
    """Test case for handoff scenarios."""
    def __init__(self, name: str, query: str, expects_planning: bool,
                 expects_debate: bool, expects_evaluation: bool):
        self.name = name
        self.query = query
        self.expects_planning = expects_planning
        self.expects_debate = expects_debate
        self.expects_evaluation = expects_evaluation
        self.passed = False
        self.metadata = {}


async def run_handoff_tests():
    """Run focused handoff tests."""
    print("\n" + "=" * 80)
    print("FOCUSED HANDOFF SCENARIO TESTS")
    print("=" * 80)
    print("\nTesting scenarios that specifically exercise handoff improvements")

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
    print("\n2. Initializing Enhanced Prince Flowers v2...")
    prince = epf_module.EnhancedPrinceFlowers(
        memory_enabled=False,
        enable_advanced_features=True,
        use_hierarchical_planning=True,
        use_multi_agent_debate=True,
        use_self_evaluation=True
    )
    print("   ✅ Agent initialized")

    # Define handoff-focused test scenarios
    tests = [
        # Memory → Planning scenarios
        HandoffTest(
            "Memory Context Preservation",
            "Build a secure authentication system with OAuth, JWT tokens, and refresh token rotation based on the security patterns we discussed earlier",
            expects_planning=True,
            expects_debate=False,
            expects_evaluation=True
        ),
        HandoffTest(
            "Complex Multi-Step Planning",
            "Create a comprehensive microservices architecture with API gateway, service mesh, and implement the caching strategy we talked about before",
            expects_planning=True,
            expects_debate=False,
            expects_evaluation=True
        ),

        # Debate → Evaluation scenarios
        HandoffTest(
            "Architectural Decision Debate",
            "Should I use microservices or monolithic architecture for a new e-commerce platform with 1000 concurrent users?",
            expects_planning=False,
            expects_debate=True,
            expects_evaluation=True
        ),
        HandoffTest(
            "Technology Comparison Debate",
            "Compare PostgreSQL versus MongoDB for a real-time analytics dashboard with complex queries",
            expects_planning=False,
            expects_debate=True,
            expects_evaluation=True
        ),
        HandoffTest(
            "Design Pattern Decision",
            "Should I use repository pattern or active record for a Django application with complex business logic?",
            expects_planning=False,
            expects_debate=True,
            expects_evaluation=True
        ),

        # Full pipeline scenarios
        HandoffTest(
            "Full Pipeline: Design → Debate → Evaluate",
            "Design a distributed caching system, compare Redis vs Memcached, evaluate the best approach, and recommend implementation strategy",
            expects_planning=True,
            expects_debate=True,
            expects_evaluation=True
        ),
        HandoffTest(
            "Full Pipeline: Build → Analyze → Decide",
            "Build a recommendation engine using collaborative filtering, analyze different similarity metrics, and recommend the best approach for a movie streaming platform",
            expects_planning=True,
            expects_debate=True,
            expects_evaluation=True
        ),
    ]

    print(f"\n3. Running {len(tests)} handoff-focused tests...")
    print("-" * 80)

    passed = 0
    info_preservation_scores = []
    quality_scores = []

    for idx, test in enumerate(tests, 1):
        print(f"\n[{idx}/{len(tests)}] {test.name}")
        print(f"Query: {test.query[:80]}...")

        try:
            result = await prince.chat_with_memory(
                user_message=test.query,
                session_id=f"handoff_test_{idx}",
                include_context=True,
                use_advanced_ai=True
            )

            metadata = result.get("metadata", {})

            # Check expectations
            expectations_met = 0
            expectations_total = 0

            if test.expects_planning:
                expectations_total += 1
                if metadata.get("used_planning"):
                    expectations_met += 1
                    print(f"  ✅ Planning activated")
                else:
                    print(f"  ⚠️  Planning expected but not activated")

            if test.expects_debate:
                expectations_total += 1
                if metadata.get("used_debate"):
                    expectations_met += 1
                    print(f"  ✅ Debate activated")
                    # Check if debate context was preserved
                    if 'debate_rounds' in str(metadata):
                        print(f"     • Debate rounds: {metadata.get('debate_rounds', 0)}")
                    if 'consensus_score' in str(metadata):
                        print(f"     • Consensus: {metadata.get('consensus_score', 0):.2f}")
                else:
                    print(f"  ⚠️  Debate expected but not activated")

            if test.expects_evaluation:
                expectations_total += 1
                if metadata.get("used_evaluation"):
                    expectations_met += 1
                    print(f"  ✅ Evaluation activated")
                    quality = metadata.get("overall_quality", metadata.get("quality_score", 0))
                    print(f"     • Quality: {quality:.2f}")
                    quality_scores.append(quality)
                else:
                    print(f"  ⚠️  Evaluation expected but not activated")

            # Check information preservation indicators
            info_score = 0.0
            info_checks = 0

            # Check for preserved metadata
            if metadata.get("used_debate"):
                info_checks += 1
                if 'consensus_score' in str(metadata):
                    info_score += 1.0
                if 'debate_rounds' in str(metadata):
                    info_score += 0.5
                if 'agent_contributions' in str(metadata):
                    info_score += 0.5
                    print(f"  ✅ Agent contributions preserved in metadata")

            if metadata.get("used_planning"):
                info_checks += 1
                if 'complexity' in str(metadata) or 'plan_steps' in str(metadata):
                    info_score += 1.0

            if info_checks > 0:
                info_preservation = info_score / (info_checks * 2.0)  # Normalize
                info_preservation_scores.append(info_preservation)
                print(f"  📊 Information preservation: {info_preservation:.1%}")

            # Overall pass/fail
            if expectations_met >= expectations_total * 0.7:  # 70% threshold
                test.passed = True
                passed += 1
                print(f"  ✅ PASS ({expectations_met}/{expectations_total} expectations met)")
            else:
                print(f"  ❌ FAIL ({expectations_met}/{expectations_total} expectations met)")

            test.metadata = metadata

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            test.passed = False

    # Results summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    pass_rate = (passed / len(tests)) * 100
    print(f"\n📊 Overall Performance:")
    print(f"  Tests Passed: {passed}/{len(tests)} ({pass_rate:.1f}%)")

    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        print(f"  Average Quality: {avg_quality:.2f}")

    if info_preservation_scores:
        avg_preservation = sum(info_preservation_scores) / len(info_preservation_scores)
        print(f"  Average Info Preservation: {avg_preservation:.1%}")

    # Break down by scenario type
    print(f"\n📋 By Scenario Type:")

    memory_planning_tests = [t for t in tests if t.expects_planning and not t.expects_debate]
    if memory_planning_tests:
        mp_passed = sum(1 for t in memory_planning_tests if t.passed)
        print(f"  Memory → Planning: {mp_passed}/{len(memory_planning_tests)} ({mp_passed/len(memory_planning_tests)*100:.0f}%)")

    debate_eval_tests = [t for t in tests if t.expects_debate and not t.expects_planning]
    if debate_eval_tests:
        de_passed = sum(1 for t in debate_eval_tests if t.passed)
        print(f"  Debate → Evaluation: {de_passed}/{len(debate_eval_tests)} ({de_passed/len(debate_eval_tests)*100:.0f}%)")

    full_pipeline_tests = [t for t in tests if t.expects_planning and t.expects_debate]
    if full_pipeline_tests:
        fp_passed = sum(1 for t in full_pipeline_tests if t.passed)
        print(f"  Full Pipeline: {fp_passed}/{len(full_pipeline_tests)} ({fp_passed/len(full_pipeline_tests)*100:.0f}%)")

    # Handoff quality analysis
    print(f"\n🔍 Handoff Quality Indicators:")

    tests_with_debate = [t for t in tests if t.metadata.get("used_debate")]
    if tests_with_debate:
        debate_with_context = sum(
            1 for t in tests_with_debate
            if 'consensus_score' in str(t.metadata) or 'agent_contributions' in str(t.metadata)
        )
        print(f"  Debate Context Preserved: {debate_with_context}/{len(tests_with_debate)} ({debate_with_context/len(tests_with_debate)*100:.0f}%)")

    tests_with_planning = [t for t in tests if t.metadata.get("used_planning")]
    if tests_with_planning:
        planning_with_context = sum(
            1 for t in tests_with_planning
            if 'complexity' in str(t.metadata) or 'plan_steps' in str(t.metadata)
        )
        print(f"  Planning Context Preserved: {planning_with_context}/{len(tests_with_planning)} ({planning_with_context/len(tests_with_planning)*100:.0f}%)")

    # Verdict
    print(f"\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if pass_rate >= 70:
        print(f"\n✅ EXCELLENT - {pass_rate:.0f}% pass rate")
        print("   Handoff improvements are working effectively!")
    elif pass_rate >= 60:
        print(f"\n✅ GOOD - {pass_rate:.0f}% pass rate")
        print("   Handoff improvements showing positive impact")
    else:
        print(f"\n⚠️  NEEDS WORK - {pass_rate:.0f}% pass rate")
        print("   Some handoff scenarios need optimization")

    if info_preservation_scores:
        avg = sum(info_preservation_scores) / len(info_preservation_scores)
        if avg >= 0.7:
            print(f"✅ Information preservation: {avg:.0%} (excellent)")
        elif avg >= 0.5:
            print(f"✅ Information preservation: {avg:.0%} (good)")
        else:
            print(f"⚠️  Information preservation: {avg:.0%} (needs improvement)")

    return pass_rate >= 60


if __name__ == "__main__":
    success = asyncio.run(run_handoff_tests())
    sys.exit(0 if success else 1)
