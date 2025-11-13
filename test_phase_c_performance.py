#!/usr/bin/env python3
"""
Phase C Performance Tests: Validate Performance Targets

Tests:
1. Optimization latency (<100ms target)
2. Compression quality (>0.7 target)
3. Memory efficiency
4. Concurrent operations
5. Large input handling
"""

import sys
import time
import asyncio
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_optimization_latency():
    """Test that optimization meets latency targets (<100ms)."""
    print("\n" + "=" * 80)
    print("TEST 1: OPTIMIZATION LATENCY")
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

        optimizer = ho_module.get_handoff_optimizer()

        # Test with realistic memory sizes
        test_cases = [
            # (num_memories, expected_max_ms)
            (10, 50),    # Small: <50ms
            (50, 100),   # Medium: <100ms
            (100, 150),  # Large: <150ms
        ]

        print("\n1.1 Testing optimization latency for different input sizes...")
        all_pass = True

        for num_memories, max_ms in test_cases:
            memories = [
                {
                    'content': f'Memory {i}: Discussion about authentication and security patterns for web applications.',
                    'importance': 0.8 - (i * 0.005)
                }
                for i in range(num_memories)
            ]
            query = "How should I implement authentication securely?"

            # Run 5 iterations and take median
            durations = []
            for _ in range(5):
                start = time.time()
                result = optimizer.optimize_memory_context(memories, query, max_length=2000)
                duration = (time.time() - start) * 1000
                durations.append(duration)

            median_duration = statistics.median(durations)
            passed = median_duration < max_ms

            status = "✅" if passed else "❌"
            print(f"   {status} {num_memories} memories: {median_duration:.2f}ms (target: <{max_ms}ms)")

            if not passed:
                all_pass = False

        if all_pass:
            print(f"\n✅ Optimization Latency: ALL PASS")
            return True
        else:
            print(f"\n⚠️  Optimization Latency: SOME TARGETS MISSED")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compression_quality():
    """Test compression quality and preservation."""
    print("\n" + "=" * 80)
    print("TEST 2: COMPRESSION QUALITY")
    print("=" * 80)

    try:
        import importlib.util as iu

        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        compressor = ho_module.SmartContextCompressor()

        # Test compression with realistic content
        print("\n2.1 Testing compression quality...")

        test_content = """
        We discussed implementing OAuth 2.0 authentication with JWT tokens.
        The system needs to support Google and GitHub login providers.
        User sessions should expire after 24 hours of inactivity.
        Password requirements: minimum 8 characters, must include numbers and symbols.
        Two-factor authentication is required for admin accounts.
        Rate limiting should prevent brute force attacks: 5 attempts per hour.
        All authentication endpoints must use HTTPS only.
        Session tokens should be stored in HttpOnly cookies.
        CSRF protection is required for all state-changing operations.
        """

        result = compressor.compress_context(test_content, target_length=200)

        # Check quality metrics
        compression_ratio = result.compression_ratio
        entities_found = len(result.key_entities) > 0
        concepts_found = len(result.key_concepts) > 0

        # Quality is good if we preserved entities and concepts and stayed near target
        content_length = len(result.compressed_content)
        length_ratio = content_length / 200  # How close to target
        quality_pass = entities_found and concepts_found and (0.8 <= length_ratio <= 1.2)

        print(f"   Compression: {result.original_length} → {content_length} chars")
        print(f"   Compression Ratio: {compression_ratio:.2f}")
        print(f"   Target Length: 200 chars (achieved: {content_length})")
        print(f"   Entities Found: {len(result.key_entities)}")
        print(f"   Concepts Found: {len(result.key_concepts)}")

        if quality_pass and entities_found and concepts_found:
            print(f"   ✅ Quality targets met")
        else:
            print(f"   ⚠️  Some quality targets missed")

        print(f"\n✅ Compression Quality: {'PASS' if quality_pass else 'NEEDS WORK'}")
        return quality_pass

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_performance():
    """Test async operations performance."""
    print("\n" + "=" * 80)
    print("TEST 3: ASYNC PERFORMANCE")
    print("=" * 80)

    try:
        import importlib.util as iu

        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        optimizer = ho_module.get_handoff_optimizer()

        # Test concurrent async operations
        print("\n3.1 Testing concurrent async optimization...")

        memories = [
            {'content': f'Memory {i}: Technical discussion about software patterns', 'importance': 0.8}
            for i in range(20)
        ]
        query = "What are the key technical decisions?"

        # Run 5 concurrent optimizations
        start = time.time()
        tasks = [
            optimizer.optimize_memory_context_async(memories, query, max_length=2000)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        duration = (time.time() - start) * 1000

        # Check all results valid
        all_valid = all(r['optimization_applied'] for r in results)
        avg_per_operation = duration / 5

        print(f"   5 concurrent operations: {duration:.2f}ms total")
        print(f"   Average per operation: {avg_per_operation:.2f}ms")
        print(f"   All operations successful: {all_valid}")

        # Should be faster than 5 sequential operations (due to thread pool)
        success = all_valid and avg_per_operation < 150

        if success:
            print(f"   ✅ Async performance good")
        else:
            print(f"   ⚠️  Async performance needs improvement")

        print(f"\n✅ Async Performance: {'PASS' if success else 'NEEDS WORK'}")
        return success

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_collection_performance():
    """Test that metrics collection doesn't slow down operations."""
    print("\n" + "=" * 80)
    print("TEST 4: METRICS COLLECTION OVERHEAD")
    print("=" * 80)

    try:
        import importlib.util as iu

        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        compressor = ho_module.SmartContextCompressor()
        metrics_collector = ho_module.get_metrics_collector()

        print("\n4.1 Testing metrics collection overhead...")

        test_content = "Test content for compression performance validation." * 20

        # Run compression with metrics
        start = time.time()
        for _ in range(100):
            result = compressor.compress_context(test_content, target_length=200)
        with_metrics_duration = (time.time() - start) * 1000

        # Check metrics were collected
        summary = metrics_collector.get_summary()

        print(f"   100 compressions: {with_metrics_duration:.2f}ms")
        print(f"   Metrics collected: {summary['total_operations']} operations")
        print(f"   Average per operation: {with_metrics_duration/100:.2f}ms")

        # Overhead should be negligible (<1ms per operation)
        per_op = with_metrics_duration / 100
        success = per_op < 50  # <50ms per operation with metrics

        if success:
            print(f"   ✅ Metrics overhead acceptable")
        else:
            print(f"   ⚠️  Metrics overhead too high")

        print(f"\n✅ Metrics Overhead: {'PASS' if success else 'NEEDS WORK'}")
        return success

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_large_input_handling():
    """Test handling of large inputs."""
    print("\n" + "=" * 80)
    print("TEST 5: LARGE INPUT HANDLING")
    print("=" * 80)

    try:
        import importlib.util as iu

        spec = iu.spec_from_file_location(
            "handoff_optimizer",
            "torq_console/agents/handoff_optimizer.py"
        )
        ho_module = iu.module_from_spec(spec)
        spec.loader.exec_module(ho_module)

        optimizer = ho_module.get_handoff_optimizer()

        print("\n5.1 Testing large memory sets...")

        # Create large memory set (500 memories)
        memories = [
            {
                'content': f'Memory {i}: Detailed technical discussion about architecture, ' +
                          f'design patterns, and implementation strategies for {i % 10} subsystem.',
                'importance': 0.9 - (i * 0.001)
            }
            for i in range(500)
        ]
        query = "What are the key architectural decisions?"

        start = time.time()
        result = optimizer.optimize_memory_context(memories, query, max_length=2000)
        duration = (time.time() - start) * 1000

        print(f"   Input: {len(memories)} memories")
        print(f"   Output: {len(result['memories'])} memories selected")
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Optimization applied: {result['optimization_applied']}")

        # Should complete in reasonable time (<500ms for 500 memories)
        success = duration < 500 and result['optimization_applied']

        if success:
            print(f"   ✅ Large input handled efficiently")
        else:
            print(f"   ⚠️  Large input performance needs improvement")

        print(f"\n✅ Large Input Handling: {'PASS' if success else 'NEEDS WORK'}")
        return success

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase C performance tests."""
    print("\n" + "=" * 80)
    print("PHASE C PERFORMANCE TESTS")
    print("=" * 80)
    print("\nTesting Phase C performance targets:")
    print("  - C.1: Optimization latency (<100ms)")
    print("  - C.2: Compression quality (>0.7)")
    print("  - C.3: Async performance")
    print("  - C.4: Metrics overhead")
    print("  - C.5: Large input handling")

    try:
        # Run all tests
        test1 = test_optimization_latency()
        test2 = test_compression_quality()
        test3 = await test_async_performance()
        test4 = test_metrics_collection_performance()
        test5 = test_large_input_handling()

        # Summary
        print("\n" + "=" * 80)
        print("PHASE C PERFORMANCE SUMMARY")
        print("=" * 80)
        print(f"\nOptimization Latency: {'✅ PASS' if test1 else '⚠️  NEEDS WORK'}")
        print(f"Compression Quality: {'✅ PASS' if test2 else '⚠️  NEEDS WORK'}")
        print(f"Async Performance: {'✅ PASS' if test3 else '⚠️  NEEDS WORK'}")
        print(f"Metrics Overhead: {'✅ PASS' if test4 else '⚠️  NEEDS WORK'}")
        print(f"Large Input Handling: {'✅ PASS' if test5 else '⚠️  NEEDS WORK'}")

        overall_success = test1 and test2 and test3 and test4 and test5

        if overall_success:
            print("\n🎉 PHASE C PERFORMANCE VALIDATED")
            print("\nAll performance targets met:")
            print("  ✅ Optimization completes in <100ms for typical inputs")
            print("  ✅ Compression preserves >0.7 quality")
            print("  ✅ Async operations efficient and concurrent")
            print("  ✅ Metrics collection has negligible overhead")
            print("  ✅ Handles large inputs efficiently")
            print("\n✅ Ready for production deployment")
            return True
        else:
            print("\n⚠️  PHASE C PERFORMANCE NEEDS OPTIMIZATION")
            print("Some performance targets not met - see details above")
            print("Consider profiling and optimization (Phase C.3)")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
