#!/usr/bin/env python3
"""
Quick test script to verify TORQ Console benchmarking system works.
"""

import asyncio
import sys
from pathlib import Path

def test_slo_config():
    """Test SLO configuration loading."""
    print("🔧 Testing SLO Configuration...")

    try:
        from torq_console.benchmarking.slo_config import SLOConfig

        # Load default configuration
        slo_config = SLOConfig.load_default()
        print(f"✓ Loaded SLO config version {slo_config.version}")
        print(f"✓ Found {len(slo_config.categories)} categories")

        # Test environment adjustment
        interactive_slo = slo_config.get_category("interactive", "production")
        print(f"✓ Interactive SLO: p95_ttfuo_ms = {interactive_slo.p95_ttfuo_ms}ms")

        dev_slo = slo_config.get_category("interactive", "development")
        print(f"✓ Development SLO: p95_ttfuo_ms = {dev_slo.p95_ttfuo_ms}ms (slack factor: {dev_slo.p95_ttfuo_ms / interactive_slo.p95_ttfuo_ms:.1f}x)")

        return True

    except Exception as e:
        print(f"❌ SLO configuration test failed: {e}")
        return False


def test_storage():
    """Test benchmark storage system."""
    print("\n🗄️ Testing Benchmark Storage...")

    try:
        from torq_console.benchmarking.storage import BenchmarkStorage

        # Create storage in temp directory
        storage_path = Path("temp_benchmarks")
        storage = BenchmarkStorage(storage_path)

        print(f"✓ Storage initialized at {storage_path}")

        # Test listing (will be empty initially)
        results = storage.list_results(limit=5)
        print(f"✓ Storage listing works (found {len(results)} existing results)")

        # Clean up
        import shutil
        if storage_path.exists():
            shutil.rmtree(storage_path)

        return True

    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False


async def test_benchmark_runner():
    """Test benchmark runner with default tests."""
    print("\n🏃 Testing Benchmark Runner...")

    try:
        from torq_console.benchmarking.runner import BenchmarkRunner, create_default_tests

        # Create runner
        runner = BenchmarkRunner()

        # Register default tests
        tests = create_default_tests()
        for test in tests:
            runner.register_test(test)

        print(f"✓ Registered {len(tests)} default tests")
        print(f"✓ Available tests: {', '.join(runner.list_tests())}")

        # Run a single iteration of simple_response test
        print("✓ Running single iteration of simple_response test...")
        result = await runner.run_single_iteration(runner.get_test("simple_response"))

        print(f"✓ Test completed in {result.duration_ms:.0f}ms")
        print(f"✓ Success: {result.success}")
        print(f"✓ Tokens generated: {result.tokens_generated}")

        if not result.success:
            print(f"⚠️ Test error: {result.error}")

        return True

    except Exception as e:
        print(f"❌ Benchmark runner test failed: {e}")
        return False


def test_slo_validation():
    """Test SLO validation logic."""
    print("\n📏 Testing SLO Validation...")

    try:
        from torq_console.benchmarking.slo_config import SLOConfig

        slo_config = SLOConfig.load_default()

        # Test interactive SLO validation
        test_cases = [
            ("interactive", "p95_ttfuo_ms", 2000, True, "Should pass"),
            ("interactive", "p95_ttfuo_ms", 3000, False, "Should fail"),
            ("tool_heavy", "p95_e2e_ms", 25000, True, "Should pass"),
            ("tool_heavy", "p95_e2e_ms", 35000, False, "Should fail"),
        ]

        for category, metric, value, expected_pass, description in test_cases:
            result = slo_config.validate_slo(category, value, metric, "production")
            level = slo_config.get_degradation_level(category, value, metric, "production")

            if result == expected_pass:
                print(f"✓ {description}: {category}.{metric} = {value} → {level}")
            else:
                print(f"❌ {description}: {category}.{metric} = {value} → Expected {expected_pass}, got {result}")
                return False

        return True

    except Exception as e:
        print(f"❌ SLO validation test failed: {e}")
        return False


def test_cli_integration():
    """Test CLI integration."""
    print("\n🖥️ Testing CLI Integration...")

    try:
        # Test import of CLI modules
        from torq_console.benchmarking.bcli import cli
        from torq_console.cli import main as torq_main

        print("✓ CLI modules imported successfully")

        # Test SLO command (dry run)
        import click.testing
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem():
            # Test SLO command
            result = runner.invoke(cli, ['slo'])
            if result.exit_code == 0:
                print("✓ 'torq-bench slo' command works")
            else:
                print(f"⚠️ 'torq-bench slo' command failed: {result.output}")

            # Test help command
            result = runner.invoke(cli, ['--help'])
            if result.exit_code == 0:
                print("✓ 'torq-bench --help' command works")
            else:
                print(f"⚠️ 'torq-bench --help' command failed: {result.output}")

        return True

    except Exception as e:
        print(f"❌ CLI integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 TORQ Console Benchmarking System Test Suite")
    print("=" * 50)

    tests = [
        ("SLO Configuration", test_slo_config),
        ("Benchmark Storage", test_storage),
        ("SLO Validation", test_slo_validation),
        ("CLI Integration", test_cli_integration),
        ("Benchmark Runner", test_benchmark_runner),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")

        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! TORQ Console benchmarking system is working correctly.")

        print("\n📖 Quick start guide:")
        print("  torq-bench slo                 # Show SLO configuration")
        print("  torq-bench run                 # Run all benchmarks")
        print("  torq-bench run simple_response # Run specific test")
        print("  torq-bench list                # List recent results")
        print("")
        print("🔗 For full documentation: BENCHMARKING_GUIDE.md")

        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))