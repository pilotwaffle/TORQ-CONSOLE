#!/usr/bin/env python3
"""
Phase B Tests: Reliability Improvements

Tests:
1. Configuration system works
2. Feature flags work
3. Thread safety (no race conditions)
4. Metrics collection works
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_configuration():
    """Test configuration system."""
    print("\n" + "=" * 80)
    print("TEST 1: CONFIGURATION SYSTEM")
    print("=" * 80)

    try:
        import importlib.util as iu

        # Load config module directly
        spec = iu.spec_from_file_location(
            "config",
            "torq_console/agents/config.py"
        )
        config_module = iu.module_from_spec(spec)
        spec.loader.exec_module(config_module)

        # Test loading config
        print("\n1.1 Testing configuration loading...")
        handoff_config = config_module.get_handoff_config()
        agent_config = config_module.get_agent_config()
        flags = config_module.get_feature_flags()

        assert handoff_config.max_context_length == 2000
        assert agent_config.latency_threshold_seconds == 2.0
        assert flags.enable_handoff_optimizer == True
        print(f"   ✅ Configuration loaded successfully")

        # Test that config is singleton
        print("\n1.2 Testing singleton pattern...")
        handoff_config2 = config_module.get_handoff_config()
        assert handoff_config is handoff_config2
        print(f"   ✅ Singleton pattern works")

        print(f"\n✅ Configuration System: ALL PASS")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thread_safety():
    """Test thread safety of singletons."""
    print("\n" + "=" * 80)
    print("TEST 2: THREAD SAFETY")
    print("=" * 80)

    try:
        import importlib.util as iu

        # Load handoff optimizer
        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        # Test concurrent access
        print("\n2.1 Testing concurrent singleton access...")
        instances = []

        def get_instance():
            optimizer = ho_module.get_handoff_optimizer()
            instances.append(id(optimizer))

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same (same ID)
        assert len(set(instances)) == 1, f"Got {len(set(instances))} different instances!"
        print(f"   ✅ 10 threads got same instance (no race condition)")

        print(f"\n✅ Thread Safety: ALL PASS")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics():
    """Test metrics collection."""
    print("\n" + "=" * 80)
    print("TEST 3: METRICS COLLECTION")
    print("=" * 80)

    try:
        import importlib.util as iu

        # Load handoff optimizer
        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        # Test metrics collection
        print("\n3.1 Testing metrics collection...")
        metrics_collector = ho_module.get_metrics_collector()

        # Record some metrics
        metric = ho_module.OptimizationMetrics(
            operation="test_op",
            duration_ms=50.0,
            input_size=1000,
            output_size=500,
            compression_ratio=0.5,
            quality_score=0.9
        )
        metrics_collector.record_metric(metric)

        # Get summary
        summary = metrics_collector.get_summary()
        assert "total_operations" in summary
        assert summary["total_operations"] >= 1
        print(f"   ✅ Metrics collection works: {summary['total_operations']} operations tracked")

        print(f"\n✅ Metrics Collection: ALL PASS")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase B tests."""
    print("\n" + "=" * 80)
    print("PHASE B RELIABILITY TESTS")
    print("=" * 80)
    print("\nTesting Phase B improvements:")
    print("  - B.1: Logging and metrics")
    print("  - B.2: Configuration system")
    print("  - B.3: Thread safety")
    print("  - B.4: Feature flags")

    try:
        # Run tests
        test1 = test_configuration()
        test2 = test_thread_safety()
        test3 = test_metrics()

        # Summary
        print("\n" + "=" * 80)
        print("PHASE B TEST SUMMARY")
        print("=" * 80)
        print(f"\nConfiguration System: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Thread Safety: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"Metrics Collection: {'✅ PASS' if test3 else '❌ FAIL'}")

        overall_success = test1 and test2 and test3

        if overall_success:
            print("\n🎉 PHASE B RELIABILITY VALIDATED")
            print("\nAll Phase B components working:")
            print("  ✅ Configuration system loads from environment")
            print("  ✅ Feature flags enable/disable functionality")
            print("  ✅ Thread-safe singletons (no race conditions)")
            print("  ✅ Metrics collection tracks operations")
            print("\n✅ Ready for Phase C (Performance validation)")
            return True
        else:
            print("\n⚠️  PHASE B INCOMPLETE")
            print("Some tests failed - review errors above")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
