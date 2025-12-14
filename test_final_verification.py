"""
Final Verification Test Suite for TORQ Console Fixes

Verifies that both critical fixes are working:
1. Content Safety Test fixture fix
2. Marvin Query Router variable scope fix

Author: TORQ Console Development Team
Version: 1.0.0 - Final Verification
"""

import sys
import os
import pytest
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_content_safety_fixture_fix():
    """Test that the Content Safety tests have proper pytest fixtures."""
    print("\n" + "="*60)
    print("TESTING: Content Safety Fixture Fix")
    print("="*60)

    try:
        # Import the fixed test file
        from tests.test_content_safety_fixed import TestResults, test_content_sanitizer

        # Test that TestResults class works properly
        results = TestResults()
        assert results.tests_run == 0
        assert results.tests_passed == 0
        assert results.tests_failed == 0

        # Test that we can record a pass
        results.record_pass("Test", "Success")
        assert results.tests_run == 1
        assert results.tests_passed == 1

        # Test that we can record a fail
        results.record_fail("TestFail", "Error")
        assert results.tests_run == 2
        assert results.tests_failed == 1

        print("✓ TestResults class working properly")

        # Test that the fixture is available
        try:
            import tests.test_content_safety_fixed as fixed_module
            assert hasattr(fixed_module, 'results')  # This should be the pytest fixture
            print("✓ Pytest fixture 'results' is defined")
        except Exception as e:
            print(f"✗ Fixture check failed: {e}")
            return False

        print("✓ Content Safety fixture fix VERIFIED")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_marvin_query_router_variable_scope_fix():
    """Test that the Marvin Query Router variable scope issue is fixed."""
    print("\n" + "="*60)
    print("TESTING: Marvin Query Router Variable Scope Fix")
    print("="*60)

    try:
        from torq_console.agents.marvin_query_router import MarvinQueryRouter
        from torq_console.marvin_integration import IntentClassification

        # Initialize router
        router = MarvinQueryRouter()
        print("✓ Router initialized successfully")

        # Test queries that would trigger the problematic code paths
        test_queries = [
            "use brave search to find python tutorials",  # Tests tool-based search detection
            "generate code for search application",        # Tests explicit code request vs search
            "with perplexity find information about AI",   # Tests 'with' pattern detection
            "create a function that sorts data",          # Tests code generation detection
            "what are the best practices for API design?" # Tests general chat fallback
        ]

        print("Testing variable scope in _infer_capabilities method...")
        for i, query in enumerate(test_queries):
            try:
                # This directly tests the _infer_capabilities method where query_lower is used
                capabilities = router._infer_capabilities(query, IntentClassification.CHAT)

                assert isinstance(capabilities, list)
                assert len(capabilities) > 0
                print(f"✓ Test {i+1}: '{query[:40]}...' -> {len(capabilities)} capabilities")

                # Verify query_lower was used correctly by checking the results
                for cap in capabilities:
                    assert hasattr(cap, 'value')  # Should be AgentCapability enum

            except NameError as e:
                if "query_lower" in str(e):
                    print(f"✗ Test {i+1}: query_lower not defined error: {e}")
                    return False
                else:
                    print(f"✗ Test {i+1}: Other NameError: {e}")
                    return False
            except Exception as e:
                print(f"✗ Test {i+1}: Unexpected error: {e}")
                return False

        print("✓ Variable scope fix VERIFIED")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_marvin_query_router_integration():
    """Test Marvin Query Router integration functionality."""
    print("\n" + "="*60)
    print("TESTING: Marvin Query Router Integration")
    print("="*60)

    try:
        from torq_console.agents.marvin_query_router import MarvinQueryRouter, create_query_router

        # Test factory function
        router = create_query_router()
        assert router is not None
        print("✓ Factory function works")

        # Test basic methods
        capabilities = router.get_agent_capabilities('prince_flowers')
        assert isinstance(capabilities, list)
        print("✓ get_agent_capabilities works")

        history = router.get_routing_history()
        assert isinstance(history, list)
        print("✓ get_routing_history works")

        metrics = router.get_metrics()
        assert isinstance(metrics, dict)
        assert 'total_routes' in metrics
        print("✓ get_metrics works")

        print("✓ Integration test VERIFIED")
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


async def test_async_functionality():
    """Test async functionality of the router."""
    print("\n" + "="*60)
    print("TESTING: Async Functionality")
    print("="*60)

    try:
        from torq_console.agents.marvin_query_router import MarvinQueryRouter

        router = MarvinQueryRouter()

        # Test async route_query method
        decision = await router.route_query("test query")
        assert decision is not None
        assert hasattr(decision, 'primary_agent')
        assert hasattr(decision, 'capabilities_needed')
        print("✓ Async route_query works")

        # Test async analyze_query method
        analysis = await router.analyze_query("test query")
        assert analysis is not None
        assert hasattr(analysis, 'suggested_agent')
        assert hasattr(analysis, 'required_capabilities')
        print("✓ Async analyze_query works")

        print("✓ Async functionality VERIFIED")
        return True

    except Exception as e:
        print(f"✗ Async test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("TORQ CONSOLE - FINAL VERIFICATION TEST SUITE")
    print("="*80)
    print("Verifying fixes for:")
    print("1. Content Safety Test fixture issues")
    print("2. Marvin Query Router variable scope issues")
    print("="*80)

    # Run all tests
    tests = [
        ("Content Safety Fixture Fix", test_content_safety_fixture_fix),
        ("Marvin Query Router Variable Scope Fix", test_marvin_query_router_variable_scope_fix),
        ("Marvin Query Router Integration", test_marvin_query_router_integration)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Run async test separately
    print(f"\n--- Async Functionality ---")
    try:
        result = asyncio.run(test_async_functionality())
        results.append(("Async Functionality", result))
    except Exception as e:
        print(f"✗ Async test crashed: {e}")
        results.append(("Async Functionality", False))

    # Final summary
    print("\n" + "="*80)
    print("FINAL VERIFICATION SUMMARY")
    print("="*80)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("\n✅ Content Safety fixture issues: FIXED")
        print("✅ Marvin Query Router variable scope issues: FIXED")
        print("✅ Integration functionality: WORKING")
        print("✅ Async functionality: WORKING")
        print("\nThe TORQ Console test failures have been resolved.")
        return True
    else:
        print(f"\n❌ {total - passed} FIXES NEED ATTENTION")
        print("Review the failed tests above for additional fixes needed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)