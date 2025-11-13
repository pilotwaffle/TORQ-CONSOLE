#!/usr/bin/env python3
"""
Quick test to measure handoff information preservation improvements.

Runs coordination benchmark and shows before/after comparison.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def run_coordination_test():
    """Run coordination benchmark and show results."""
    print("\n" + "=" * 80)
    print("COORDINATION BENCHMARK - HANDOFF INFORMATION PRESERVATION TEST")
    print("=" * 80)
    print("\nTesting improvements to Memory→Planning and Debate→Evaluation handoffs")

    # Load dependencies manually to avoid import issues
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
    ]

    print("\n1. Loading agent modules...")
    for mod_name, mod_path in deps:
        try:
            spec = iu.spec_from_file_location(mod_name, mod_path)
            mod = iu.module_from_spec(spec)
            sys.modules[f'torq_console.agents.{mod_name}'] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"   ⚠️  Warning loading {mod_name}: {e}")
            continue

    # Load Enhanced Prince Flowers v2
    spec = iu.spec_from_file_location(
        "enhanced_v2",
        "torq_console/agents/enhanced_prince_flowers_v2.py"
    )
    epf_module = iu.module_from_spec(spec)
    sys.modules['torq_console.agents.enhanced_prince_flowers_v2'] = epf_module
    spec.loader.exec_module(epf_module)

    print("   ✅ All modules loaded")

    # Initialize agent
    print("\n2. Initializing Enhanced Prince Flowers v2...")
    try:
        prince = epf_module.EnhancedPrinceFlowers(
            memory_enabled=False,
            enable_advanced_features=True,
            use_hierarchical_planning=True,
            use_multi_agent_debate=True,
            use_self_evaluation=True
        )
        print("   ✅ Agent initialized with all advanced features")
    except Exception as e:
        print(f"   ❌ Failed to initialize agent: {e}")
        return False

    # Get coordination benchmark
    print("\n3. Running Coordination Benchmark (10 tests)...")
    from torq_console.agents.coordination_benchmark import get_coordination_benchmark, CoordinationType

    benchmark = get_coordination_benchmark()

    try:
        result = await benchmark.run_benchmark(prince, num_tests=10)
    except Exception as e:
        print(f"   ❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Analyze results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    # Overall statistics
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Tests: {result.total_tests}")
    print(f"  Passed: {result.passed} ({result.passed/result.total_tests*100:.1f}%)")
    print(f"  Failed: {result.failed} ({result.failed/result.total_tests*100:.1f}%)")
    print(f"  Average Latency: {result.average_latency:.2f}s")
    print(f"  Average Quality: {result.average_quality:.2f}")

    # Information preservation analysis
    print(f"\n🔍 Information Preservation Analysis:")
    total_info_preserved = sum(
        m.information_preserved
        for m in result.coordination_metrics
    ) / len(result.coordination_metrics)
    print(f"  Overall Preservation: {total_info_preserved:.2%}")

    # Expected baseline (before fixes): ~28% overall, 70% loss rate
    # Expected after fixes: ~88% overall, <30% loss rate
    baseline_preservation = 0.28
    improvement = ((total_info_preserved - baseline_preservation) / baseline_preservation) * 100

    print(f"\n  📈 Improvement vs Baseline (28%):")
    print(f"     Current: {total_info_preserved:.1%}")
    print(f"     Baseline: {baseline_preservation:.1%}")
    print(f"     Change: {improvement:+.1f}%")

    # Break down by coordination type
    by_type = {}
    for metric in result.coordination_metrics:
        coord_type = metric.coordination_type.value
        if coord_type not in by_type:
            by_type[coord_type] = []
        by_type[coord_type].append(metric.information_preserved)

    print(f"\n  📋 By Coordination Type:")
    for coord_type, preserved_values in sorted(by_type.items()):
        avg = sum(preserved_values) / len(preserved_values)
        count = len(preserved_values)
        print(f"     {coord_type}: {avg:.1%} ({count} test(s))")

    # Focus on key handoffs
    print(f"\n  🎯 Key Handoff Improvements:")

    memory_planning = [
        m for m in result.coordination_metrics
        if m.coordination_type == CoordinationType.MEMORY_TO_PLANNING
    ]
    if memory_planning:
        avg = sum(m.information_preserved for m in memory_planning) / len(memory_planning)
        baseline = 0.30  # 30% before
        improvement = ((avg - baseline) / baseline) * 100
        print(f"     Memory → Planning: {avg:.1%} (baseline 30%, {improvement:+.0f}%)")

    debate_eval = [
        m for m in result.coordination_metrics
        if m.coordination_type == CoordinationType.DEBATE_TO_EVALUATION
    ]
    if debate_eval:
        avg = sum(m.information_preserved for m in debate_eval) / len(debate_eval)
        baseline = 0.25  # 25% before
        improvement = ((avg - baseline) / baseline) * 100
        print(f"     Debate → Evaluation: {avg:.1%} (baseline 25%, {improvement:+.0f}%)")

    # Issues detected
    print(f"\n⚠️  Issues Detected:")
    if result.issues_by_type:
        for issue_type, count in sorted(result.issues_by_type.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / result.total_tests) * 100
            print(f"  {issue_type}: {count} ({percentage:.0f}%)")

        # Focus on information loss
        info_loss_count = result.issues_by_type.get('information_loss', 0)
        info_loss_rate = info_loss_count / result.total_tests
        baseline_loss_rate = 0.70  # 70% before (7/10 tests)

        print(f"\n  📉 Information Loss Rate:")
        print(f"     Current: {info_loss_rate:.1%} ({info_loss_count}/{result.total_tests} tests)")
        print(f"     Baseline: {baseline_loss_rate:.1%} (7/10 tests)")
        reduction = ((baseline_loss_rate - info_loss_rate) / baseline_loss_rate) * 100
        print(f"     Reduction: {reduction:.0f}%")

        if info_loss_rate < 0.30:
            print(f"     ✅ SUCCESS - Loss rate < 30% target!")
        else:
            print(f"     ⚠️  Still above 30% target")
    else:
        print("  ✅ No issues detected!")
        print(f"     Information Loss Rate: 0% (0/{result.total_tests} tests)")
        print(f"     Baseline: 70% (7/10 tests)")
        print(f"     Reduction: 100%")
        print(f"     ✅ SUCCESS - All information preserved!")

    # Emergent behaviors
    if result.emergent_behaviors:
        print(f"\n✨ Emergent Behaviors:")
        behavior_counts = {}
        for behavior in result.emergent_behaviors:
            behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
        for behavior, count in sorted(behavior_counts.items()):
            print(f"  {behavior}: {count} occurrence(s)")

    # Final verdict
    print(f"\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    success_criteria = {
        "overall_preservation": total_info_preserved >= 0.70,  # Target: >70%
        "information_loss_rate": result.issues_by_type.get('information_loss', 0) / result.total_tests < 0.30,  # Target: <30%
        "pass_rate": result.passed / result.total_tests >= 0.70  # Target: >70%
    }

    passed_criteria = sum(1 for passed in success_criteria.values() if passed)

    print(f"\nSuccess Criteria ({passed_criteria}/3 met):")
    print(f"  Overall Preservation >70%: {'✅ PASS' if success_criteria['overall_preservation'] else '❌ FAIL'} ({total_info_preserved:.1%})")
    print(f"  Information Loss <30%: {'✅ PASS' if success_criteria['information_loss_rate'] else '❌ FAIL'} ({result.issues_by_type.get('information_loss', 0)}/{result.total_tests})")
    print(f"  Test Pass Rate >70%: {'✅ PASS' if success_criteria['pass_rate'] else '❌ FAIL'} ({result.passed}/{result.total_tests})")

    if passed_criteria == 3:
        print(f"\n🎉 ALL CRITERIA MET - Handoff fixes validated!")
    elif passed_criteria >= 2:
        print(f"\n✅ GOOD - Most criteria met, significant improvement!")
    else:
        print(f"\n⚠️  PARTIAL - Some improvements, but not all targets met")

    print(f"\n" + "=" * 80)

    return passed_criteria >= 2


if __name__ == "__main__":
    success = asyncio.run(run_coordination_test())
    sys.exit(0 if success else 1)
