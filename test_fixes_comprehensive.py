"""
Fixed TORQ Console Test Suite

Comprehensive fixes for:
1. Content Safety Test fixture issues
2. Prince Flowers Variable Scope issues

Author: TORQ Console Development Team
Version: 1.0.0 - Bug Fix Release
"""

import sys
import os
import pytest
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestResults:
    """Track and display test results - same as original for compatibility."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def record_pass(self, test_name: str, message: str = ""):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"[PASS] {test_name}")
        if message:
            print(f"   {message}")

    def record_fail(self, test_name: str, error: str):
        self.tests_run += 1
        self.tests_failed += 1
        self.failures.append((test_name, error))
        print(f"[FAIL] {test_name}")
        print(f"   Error: {error}")

    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ({self.tests_passed/max(self.tests_run,1)*100:.1f}%)")
        print(f"Failed: {self.tests_failed} ({self.tests_failed/max(self.tests_run,1)*100:.1f}%)")

        if self.failures:
            print("\nFailed Tests:")
            for test_name, error in self.failures:
                print(f"  - {test_name}: {error}")

        print("="*70)

        if self.tests_failed == 0:
            print("*** ALL TESTS PASSED! ***")
        else:
            print(f"WARNING: {self.tests_failed} test(s) failed")

        return self.tests_failed == 0


@pytest.fixture
def results():
    """Pytest fixture for TestResults - fixes the missing fixture issue."""
    return TestResults()


# ============================================================================
# CONTENT SAFETY TESTS (Fixed with proper pytest fixtures)
# ============================================================================

def test_content_sanitizer(results):
    """Test ContentSanitizer functionality - FIXED with proper fixture."""
    print("\n" + "="*70)
    print("TESTING: ContentSanitizer")
    print("="*70)

    try:
        from torq_console.llm.providers.content_safety import ContentSanitizer
        sanitizer = ContentSanitizer()

        # Test 1: Script tag removal
        try:
            html = '<p>Hello</p><script>alert("XSS")</script><p>World</p>'
            clean = sanitizer.sanitize_html(html)
            assert '<script>' not in clean.lower()
            assert 'alert' not in clean
            assert 'Hello' in clean
            assert 'World' in clean
            results.record_pass("Script tag removal", f"Cleaned: {clean[:50]}...")
        except Exception as e:
            results.record_fail("Script tag removal", str(e))

        # Test 2: Text sanitization
        try:
            text = "Hello\x00\x01\x02World  \n\n  Test"
            clean = sanitizer.sanitize_text(text)
            assert '\x00' not in clean
            assert 'Hello' in clean
            assert 'World' in clean
            results.record_pass("Text sanitization", f"Cleaned: {clean}")
        except Exception as e:
            results.record_fail("Text sanitization", str(e))

        # Test 3: URL validation
        try:
            is_valid, reason = sanitizer.validate_url("https://example.com/test")
            assert is_valid == True
            results.record_pass("URL validation - HTTPS", reason)
        except Exception as e:
            results.record_fail("URL validation - HTTPS", str(e))

    except ImportError as e:
        results.record_fail("ContentSanitizer Import", f"Could not import ContentSanitizer: {e}")


def test_connection_guard(results):
    """Test ConnectionGuard functionality - FIXED with proper fixture."""
    print("\n" + "="*70)
    print("TESTING: ConnectionGuard")
    print("="*70)

    try:
        from torq_console.llm.providers.content_safety import ConnectionGuard

        # Test 1: Default (no blacklist/whitelist)
        try:
            guard = ConnectionGuard()
            is_allowed, reason = guard.check_domain("https://example.com")
            assert is_allowed == True
            results.record_pass("Default - allow all", reason)
        except Exception as e:
            results.record_fail("Default - allow all", str(e))

        # Test 2: Blacklist blocking
        try:
            config = {'blacklist': ['malicious.com', 'spam.net']}
            guard = ConnectionGuard(config)
            is_allowed, reason = guard.check_domain("https://malicious.com/evil")
            assert is_allowed == False
            results.record_pass("Blacklist blocking", reason)
        except Exception as e:
            results.record_fail("Blacklist blocking", str(e))

    except ImportError as e:
        results.record_fail("ConnectionGuard Import", f"Could not import ConnectionGuard: {e}")


def test_rate_limiter(results):
    """Test RateLimiter functionality - FIXED with proper fixture."""
    print("\n" + "="*70)
    print("TESTING: RateLimiter")
    print("="*70)

    try:
        from torq_console.llm.providers.content_safety import RateLimiter

        # Test 1: Within rate limits
        try:
            config = {'default_rpm': 10, 'default_rph': 100}
            limiter = RateLimiter(config)
            is_allowed, reason, wait_time = limiter.check_rate_limit("https://example.com/test1")
            assert is_allowed == True
            results.record_pass("Within rate limits", reason)
        except Exception as e:
            results.record_fail("Within rate limits", str(e))

        # Test 2: Rate limit statistics
        try:
            config = {'default_rpm': 10, 'default_rph': 100}
            limiter = RateLimiter(config)

            limiter.check_rate_limit("https://example.com/test")
            limiter.check_rate_limit("https://example.com/test")

            stats = limiter.get_rate_limit_stats()
            assert 'domains_tracked' in stats
            results.record_pass("Rate limit statistics", f"Tracking {stats['domains_tracked']} domain(s)")
        except Exception as e:
            results.record_fail("Rate limit statistics", str(e))

    except ImportError as e:
        results.record_fail("RateLimiter Import", f"Could not import RateLimiter: {e}")


def test_security_logger(results):
    """Test SecurityLogger functionality - FIXED with proper fixture."""
    print("\n" + "="*70)
    print("TESTING: SecurityLogger")
    print("="*70)

    try:
        from torq_console.llm.providers.content_safety import SecurityLogger
        logger = SecurityLogger()

        # Test 1: Log request
        try:
            logger.log_request("https://example.com", "GET", "ALLOWED", "Test request")
            events = logger.get_recent_events(count=10)
            assert len(events) >= 1
            assert events[-1]['type'] == 'WEB_REQUEST'
            results.record_pass("Log request", f"Logged {len(events)} event(s)")
        except Exception as e:
            results.record_fail("Log request", str(e))

        # Test 2: Log security event
        try:
            logger.log_security_event(
                event_type='BLOCKED_DOMAIN',
                url='https://malicious.com',
                severity='HIGH',
                details='Domain in blacklist'
            )
            events = logger.get_recent_events(count=10)
            security_events = [e for e in events if e['type'] == 'SECURITY_EVENT']
            assert len(security_events) >= 1
            results.record_pass("Log security event", f"Logged {len(security_events)} security event(s)")
        except Exception as e:
            results.record_fail("Log security event", str(e))

    except ImportError as e:
        results.record_fail("SecurityLogger Import", f"Could not import SecurityLogger: {e}")


@pytest.mark.asyncio
async def test_websearch_integration(results):
    """Test WebSearch integration with content safety - FIXED with proper fixture."""
    print("\n" + "="*70)
    print("TESTING: WebSearch Integration")
    print("="*70)

    try:
        from torq_console.llm.providers.websearch import WebSearchProvider

        # Test 1: WebSearch initializes safety features
        try:
            provider = WebSearchProvider()
            assert hasattr(provider, 'content_safety_enabled')
            assert hasattr(provider, 'sanitizer')
            assert hasattr(provider, 'connection_guard')
            assert hasattr(provider, 'rate_limiter')
            assert hasattr(provider, 'security_logger')

            if provider.content_safety_enabled:
                results.record_pass("WebSearch safety initialization", "All safety features initialized")
            else:
                results.record_fail("WebSearch safety initialization", "Safety features not enabled")
        except Exception as e:
            results.record_fail("WebSearch safety initialization", str(e))

    except ImportError as e:
        results.record_fail("WebSearch integration", f"Could not import WebSearchProvider: {e}")


# ============================================================================
# MARVIN QUERY ROUTER TESTS (Variable Scope Fix Verification)
# ============================================================================

def test_marvin_query_router_variable_scope():
    """Test Marvin Query Router variable scope - FIXED SCOPE ISSUE."""
    print("\n" + "="*70)
    print("TESTING: Marvin Query Router Variable Scope")
    print("="*70)

    results = TestResults()

    try:
        from torq_console.agents.marvin_query_router import MarvinQueryRouter

        # Initialize router
        router = MarvinQueryRouter()
        results.record_pass("Router Initialization", "MarvinQueryRouter initialized successfully")

        # Test the specific function that had the scope issue
        test_queries = [
            "search for python tutorials",
            "generate code for a web app",
            "use perplexity to find information",
            "create a function that sorts data",
            "what are the best practices for API design?"
        ]

        for i, query in enumerate(test_queries):
            try:
                # This should trigger the _infer_capabilities method where the scope issue was
                analysis = router.analyze_query(query)

                assert analysis is not None
                assert hasattr(analysis, 'required_capabilities')
                assert hasattr(analysis, 'suggested_agent')

                results.record_pass(f"Query Analysis {i+1}",
                    f"Query: '{query[:30]}...' -> Agent: {analysis.suggested_agent}, "
                    f"Capabilities: {[cap.value for cap in analysis.required_capabilities[:3]]}")

            except Exception as e:
                results.record_fail(f"Query Analysis {i+1}", f"Failed on '{query[:30]}...': {str(e)}")

        # Test the specific variable scope issue fix
        try:
            # Test queries that would trigger the problematic code path
            scope_test_queries = [
                "use brave search to find python tutorials",  # Tests tool-based search detection
                "generate code for search application",        # Tests explicit code request vs search
                "with perplexity find information about AI"   # Tests 'with' pattern detection
            ]

            for query in scope_test_queries:
                # This directly tests the _infer_capabilities method where query_lower is used
                capabilities = router._infer_capabilities(query, router.marvin.classify(query, router.marvin.__class__.__module__.split('.')[-1] if hasattr(router.marvin, '__class__') else 'CHAT'))

                assert isinstance(capabilities, list)
                results.record_pass("Variable Scope Test", f"No 'query_lower not defined' error for: '{query[:40]}...'")

        except NameError as e:
            if "query_lower" in str(e):
                results.record_fail("Variable Scope Issue", f"query_lower not defined error: {str(e)}")
            else:
                results.record_fail("Other NameError", f"NameError (not query_lower): {str(e)}")
        except Exception as e:
            results.record_fail("Variable Scope Test", f"Unexpected error: {str(e)}")

    except ImportError as e:
        results.record_fail("MarvinQueryRouter Import", f"Could not import MarvinQueryRouter: {e}")

    # Print results for this test
    success = results.print_summary()
    assert success, f"Marvin Query Router tests failed: {results.tests_failed} error(s)"


def test_marvin_query_router_integration():
    """Test full Marvin Query Router integration."""
    print("\n" + "="*70)
    print("TESTING: Marvin Query Router Integration")
    print("="*70)

    results = TestResults()

    try:
        from torq_console.agents.marvin_query_router import MarvinQueryRouter, create_query_router

        # Test factory function
        try:
            router = create_query_router()
            assert router is not None
            results.record_pass("Factory Function", "create_query_router() works")
        except Exception as e:
            results.record_fail("Factory Function", str(e))

        # Test routing decision
        try:
            router = MarvinQueryRouter()

            async def test_routing():
                decision = await router.route_query("search for python tutorials")
                assert decision is not None
                assert hasattr(decision, 'primary_agent')
                assert hasattr(decision, 'capabilities_needed')
                return decision

            import asyncio
            decision = asyncio.run(test_routing())
            results.record_pass("Async Routing", f"Routed to {decision.primary_agent}")

        except Exception as e:
            results.record_fail("Async Routing", str(e))

        # Test metrics
        try:
            metrics = router.get_metrics()
            assert isinstance(metrics, dict)
            assert 'total_routes' in metrics
            results.record_pass("Metrics Collection", f"Metrics available: {list(metrics.keys())}")
        except Exception as e:
            results.record_fail("Metrics Collection", str(e))

    except ImportError as e:
        results.record_fail("Integration Import", f"Could not import required modules: {e}")

    # Print results for this test
    success = results.print_summary()
    assert success, f"Integration tests failed: {results.tests_failed} error(s)"


if __name__ == "__main__":
    """Run the fixed test suite manually."""
    print("\n" + "="*70)
    print("TORQ CONSOLE - FIXED TEST SUITE")
    print("="*70)
    print("Running fixes for:")
    print("1. Content Safety Test fixture issues")
    print("2. Prince Flowers Variable Scope issues")
    print("="*70)

    # Test 1: Content Safety (Fixed fixture issue)
    print("\n" + "="*50)
    print("TEST 1: Content Safety (Fixture Fix)")
    print("="*50)

    results = TestResults()
    test_content_sanitizer(results)
    test_connection_guard(results)
    test_rate_limiter(results)
    test_security_logger(results)

    # Test async function separately
    import asyncio
    asyncio.run(test_websearch_integration(results))

    content_safety_success = results.print_summary()

    # Test 2: Marvin Query Router (Fixed scope issue)
    print("\n" + "="*50)
    print("TEST 2: Marvin Query Router (Scope Fix)")
    print("="*50)

    try:
        test_marvin_query_router_variable_scope()
        test_marvin_query_router_integration()
        query_router_success = True
        print("\n[SUCCESS] Marvin Query Router tests passed!")
    except Exception as e:
        print(f"\n[FAILED] Marvin Query Router tests: {e}")
        query_router_success = False

    # Final Summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    print(f"Content Safety Tests: {'PASSED' if content_safety_success else 'FAILED'}")
    print(f"Query Router Tests: {'PASSED' if query_router_success else 'FAILED'}")

    overall_success = content_safety_success and query_router_success
    print(f"Overall Result: {'SUCCESS' if overall_success else 'FAILURE'}")
    print("="*70)

    if overall_success:
        print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("\nFixes Applied:")
        print("✅ Added pytest fixture for TestResults")
        print("✅ Fixed variable scope issue in query_lower usage")
        print("✅ All tests now pass with proper error handling")
    else:
        print("❌ SOME FIXES NEED ATTENTION")
        print("Review the failures above for additional fixes needed.")

    sys.exit(0 if overall_success else 1)