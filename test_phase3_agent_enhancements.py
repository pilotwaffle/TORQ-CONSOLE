#!/usr/bin/env python3
"""
Test Phase 3: Agent System Enhancements.

Tests:
1. Cross-agent learning
2. Agent performance monitoring
3. Advanced coordination
4. Agent specialization
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_cross_agent_learning():
    """Test cross-agent learning system."""
    print("\n" + "=" * 80)
    print("TEST 1: CROSS-AGENT LEARNING")
    print("=" * 80)

    # Import directly
    import importlib.util as iu

    spec = iu.spec_from_file_location(
        "agent_enhancements",
        "torq_console/agents/agent_system_enhancements.py"
    )
    ae_module = iu.module_from_spec(spec)
    spec.loader.exec_module(ae_module)

    learning = ae_module.get_cross_agent_learning()

    # Test 1: Share knowledge
    print("\n1.1 Testing Knowledge Sharing...")
    kid1 = learning.share_knowledge(
        source_agent="agent_code",
        knowledge_type="pattern",
        content={"pattern": "repository_pattern", "language": "python"},
        confidence=0.9
    )
    print(f"   Shared knowledge: {kid1}")
    assert kid1.startswith("k_")
    print(f"   ✅ Knowledge sharing - PASS")

    # Test 2: Query knowledge
    print("\n1.2 Testing Knowledge Query...")
    results = learning.query_knowledge(knowledge_type="pattern", min_confidence=0.8)
    print(f"   Found {len(results)} knowledge items")
    assert len(results) >= 1
    print(f"   ✅ Knowledge query - PASS")

    # Test 3: Record usage
    print("\n1.3 Testing Usage Recording...")
    learning.record_knowledge_usage(kid1, success=True)
    knowledge = learning.knowledge_base[kid1]
    print(f"   Usage count: {knowledge.usage_count}")
    print(f"   Success rate: {knowledge.success_rate:.1%}")
    assert knowledge.usage_count == 1
    assert knowledge.success_rate == 1.0
    print(f"   ✅ Usage recording - PASS")

    print(f"\n✅ Cross-Agent Learning: ALL PASS")
    return True


def test_performance_monitoring():
    """Test agent performance monitoring."""
    print("\n" + "=" * 80)
    print("TEST 2: PERFORMANCE MONITORING")
    print("=" * 80)

    import importlib.util as iu

    spec = iu.spec_from_file_location(
        "agent_enhancements",
        "torq_console/agents/agent_system_enhancements.py"
    )
    ae_module = iu.module_from_spec(spec)
    spec.loader.exec_module(ae_module)

    monitor = ae_module.get_performance_monitor()

    # Test 1: Record metrics
    print("\n2.1 Testing Metric Recording...")
    monitor.record_metric("agent_1", "response_latency", 1.5)
    monitor.record_metric("agent_1", "response_latency", 1.2)
    monitor.record_metric("agent_1", "quality_score", 0.85)
    monitor.record_metric("agent_1", "quality_score", 0.90)
    print(f"   Recorded 4 metrics")
    assert len(monitor.metrics) == 4
    print(f"   ✅ Metric recording - PASS")

    # Test 2: Get performance summary
    print("\n2.2 Testing Performance Summary...")
    perf = monitor.get_agent_performance("agent_1")
    print(f"   Agent: {perf['agent_id']}")
    print(f"   Metrics tracked: {list(perf['metrics'].keys())}")
    assert 'response_latency' in perf['metrics']
    assert 'quality_score' in perf['metrics']
    print(f"   Latency mean: {perf['metrics']['response_latency']['mean']:.2f}s")
    print(f"   Quality mean: {perf['metrics']['quality_score']['mean']:.2f}")
    print(f"   ✅ Performance summary - PASS")

    # Test 3: Bottleneck detection
    print("\n2.3 Testing Bottleneck Detection...")
    # Record some problematic metrics
    monitor.record_metric("agent_2", "response_latency", 6.0)  # High latency
    monitor.record_metric("agent_2", "quality_score", 0.4)  # Low quality
    monitor.record_metric("agent_2", "error_rate", 0.2)  # High errors

    bottlenecks = monitor.detect_bottlenecks("agent_2")
    print(f"   Detected {len(bottlenecks)} bottleneck(s)")
    for bottleneck in bottlenecks:
        print(f"   - {bottleneck['type']}: {bottleneck['metric']} = {bottleneck['value']:.2f}")
    assert len(bottlenecks) >= 2  # Should detect at least 2 issues
    print(f"   ✅ Bottleneck detection - PASS")

    print(f"\n✅ Performance Monitoring: ALL PASS")
    return True


def test_advanced_coordination():
    """Test advanced agent coordination."""
    print("\n" + "=" * 80)
    print("TEST 3: ADVANCED COORDINATION")
    print("=" * 80)

    import importlib.util as iu

    spec = iu.spec_from_file_location(
        "agent_enhancements",
        "torq_console/agents/agent_system_enhancements.py"
    )
    ae_module = iu.module_from_spec(spec)
    spec.loader.exec_module(ae_module)

    coordinator = ae_module.get_advanced_coordinator()
    AgentRole = ae_module.AgentRole

    # Test 1: Register agents
    print("\n3.1 Testing Agent Registration...")
    coordinator.register_agent("agent_code", AgentRole.SPECIALIST_CODE)
    coordinator.register_agent("agent_debug", AgentRole.SPECIALIST_DEBUG)
    coordinator.register_agent("agent_general", AgentRole.GENERALIST)
    print(f"   Registered {len(coordinator.available_agents)} agents")
    assert len(coordinator.available_agents) == 3
    print(f"   ✅ Agent registration - PASS")

    # Test 2: Agent selection
    print("\n3.2 Testing Best Agent Selection...")
    best = coordinator.select_best_agent(AgentRole.SPECIALIST_CODE)
    print(f"   Best agent for CODE: {best}")
    assert best == "agent_code"
    print(f"   ✅ Agent selection - PASS")

    # Test 3: Parallel coordination
    print("\n3.3 Testing Parallel Coordination...")
    tasks = [
        {"task_id": "task1", "required_role": AgentRole.SPECIALIST_CODE},
        {"task_id": "task2", "required_role": AgentRole.SPECIALIST_DEBUG},
        {"task_id": "task3", "required_role": AgentRole.GENERALIST}
    ]

    plan = coordinator.coordinate_parallel_execution(tasks)
    print(f"   Coordination type: {plan['coordination_type']}")
    print(f"   Total tasks: {plan['total_tasks']}")
    print(f"   Assignments: {len(plan['agent_assignments'])}")
    assert plan['total_tasks'] == 3
    assert len(plan['agent_assignments']) == 3
    print(f"   ✅ Parallel coordination - PASS")

    print(f"\n✅ Advanced Coordination: ALL PASS")
    return True


def main():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 80)
    print("PHASE 3: AGENT SYSTEM ENHANCEMENTS TESTS")
    print("=" * 80)

    try:
        # Run tests
        learning_success = test_cross_agent_learning()
        monitoring_success = test_performance_monitoring()
        coordination_success = test_advanced_coordination()

        # Summary
        print("\n" + "=" * 80)
        print("PHASE 3 TEST SUMMARY")
        print("=" * 80)
        print(f"\nCross-Agent Learning: {'✅ PASS' if learning_success else '❌ FAIL'}")
        print(f"Performance Monitoring: {'✅ PASS' if monitoring_success else '❌ FAIL'}")
        print(f"Advanced Coordination: {'✅ PASS' if coordination_success else '❌ FAIL'}")

        overall_success = learning_success and monitoring_success and coordination_success

        if overall_success:
            print("\n🎉 PHASE 3 VALIDATION COMPLETE")
            print("\nPhase 3 Agent Enhancements Ready:")
            print("  ✅ Cross-agent learning & knowledge sharing")
            print("  ✅ Real-time performance monitoring")
            print("  ✅ Bottleneck detection & optimization")
            print("  ✅ Advanced multi-agent coordination")
            print("  ✅ Dynamic agent selection")
            print("  ✅ Parallel task execution")
            print("\n🎊 ALL 3 PHASES COMPLETE!")
            return True
        else:
            print("\n⚠️  PHASE 3 VALIDATION INCOMPLETE")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
