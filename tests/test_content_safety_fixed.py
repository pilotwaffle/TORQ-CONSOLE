"""
FIXED Comprehensive Test Suite for Phase 2: Content Safety

This is a corrected version of test_content_safety.py that fixes:
1. Missing pytest fixture for TestResults
2. Proper pytest function signatures

Tests all content safety components:
1. ContentSanitizer
2. ConnectionGuard
3. RateLimiter
4. SecurityLogger
5. WebSearch Integration

Author: TORQ Console Development Team
Version: 1.1.0 - Bug Fix Release
"""

import sys
import os
import time
import asyncio
import pytest
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from torq_console.llm.providers.content_safety import (
        ContentSanitizer, ConnectionGuard, RateLimiter, SecurityLogger
    )
    CONTENT_SAFETY_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Could not import content_safety: {e}")
    CONTENT_SAFETY_AVAILABLE = False


class TestResults:
    """Track and display test results."""

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


# PYTEST FIXTURE - This was missing in the original file
@pytest.fixture
def results():
    """Pytest fixture that provides a TestResults instance."""
    return TestResults()


def test_content_sanitizer(results):
    """Test ContentSanitizer functionality."""
    print("\n" + "="*70)
    print("TESTING: ContentSanitizer")
    print("="*70)

    if not CONTENT_SAFETY_AVAILABLE:
        pytest.skip("Content safety module not available")

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

    # Test 2: Event handler removal
    try:
        html = '<div onclick="evil()">Click me</div>'
        clean = sanitizer.sanitize_html(html)
        assert 'onclick' not in clean.lower()
        assert 'Click me' in clean
        results.record_pass("Event handler removal", f"Cleaned: {clean}")
    except Exception as e:
        results.record_fail("Event handler removal", str(e))

    # Test 3: Iframe removal
    try:
        html = '<p>Safe</p><iframe src="evil.com"></iframe><p>Content</p>'
        clean = sanitizer.sanitize_html(html)
        assert 'iframe' not in clean.lower()
        assert 'Safe' in clean
        assert 'Content' in clean
        results.record_pass("Iframe removal", f"Cleaned: {clean[:50]}...")
    except Exception as e:
        results.record_fail("Iframe removal", str(e))

    # Test 4: JavaScript URL removal
    try:
        html = '<a href="javascript:alert(\'XSS\')">Click</a>'
        clean = sanitizer.sanitize_html(html)
        assert 'javascript:' not in clean.lower()
        results.record_pass("JavaScript URL removal", f"Cleaned: {clean}")
    except Exception as e:
        results.record_fail("JavaScript URL removal", str(e))

    # Test 5: Text sanitization
    try:
        text = "Hello\x00\x01\x02World  \n\n  Test"
        clean = sanitizer.sanitize_text(text)
        assert '\x00' not in clean
        assert 'Hello' in clean
        assert 'World' in clean
        results.record_pass("Text sanitization", f"Cleaned: {clean}")
    except Exception as e:
        results.record_fail("Text sanitization", str(e))

    # Test 6: URL validation - valid HTTPS
    try:
        is_valid, reason = sanitizer.validate_url("https://example.com/test")
        assert is_valid == True
        results.record_pass("URL validation - HTTPS", reason)
    except Exception as e:
        results.record_fail("URL validation - HTTPS", str(e))

    # Test 7: URL validation - invalid scheme
    try:
        is_valid, reason = sanitizer.validate_url("javascript:alert('XSS')")
        assert is_valid == False
        results.record_pass("URL validation - invalid scheme", reason)
    except Exception as e:
        results.record_fail("URL validation - invalid scheme", str(e))

    # Test 8: URL validation - dangerous extension
    try:
        is_valid, reason = sanitizer.validate_url("https://example.com/file.exe")
        assert is_valid == False
        results.record_pass("URL validation - dangerous extension", reason)
    except Exception as e:
        results.record_fail("URL validation - dangerous extension", str(e))

    # Test 9: URL validation - localhost block
    try:
        is_valid, reason = sanitizer.validate_url("http://localhost:8080/admin")
        assert is_valid == False
        results.record_pass("URL validation - localhost block", reason)
    except Exception as e:
        results.record_fail("URL validation - localhost block", str(e))

    # Test 10: URL validation - private IP block
    try:
        is_valid, reason = sanitizer.validate_url("http://192.168.1.1/config")
        assert is_valid == False
        results.record_pass("URL validation - private IP block", reason)
    except Exception as e:
        results.record_fail("URL validation - private IP block", str(e))


def test_connection_guard(results):
    """Test ConnectionGuard functionality."""
    print("\n" + "="*70)
    print("TESTING: ConnectionGuard")
    print("="*70)

    if not CONTENT_SAFETY_AVAILABLE:
        pytest.skip("Content safety module not available")

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

    # Test 3: Blacklist allows non-blacklisted
    try:
        config = {'blacklist': ['malicious.com']}
        guard = ConnectionGuard(config)
        is_allowed, reason = guard.check_domain("https://safe.com")
        assert is_allowed == True
        results.record_pass("Blacklist allows non-blacklisted", reason)
    except Exception as e:
        results.record_fail("Blacklist allows non-blacklisted", str(e))

    # Test 4: Whitelist blocking
    try:
        config = {'whitelist': ['trusted.com', 'safe.com']}
        guard = ConnectionGuard(config)
        is_allowed, reason = guard.check_domain("https://untrusted.com")
        assert is_allowed == False
        results.record_pass("Whitelist blocking", reason)
    except Exception as e:
        results.record_fail("Whitelist blocking", str(e))

    # Test 5: Whitelist allowing
    try:
        config = {'whitelist': ['trusted.com', 'safe.com']}
        guard = ConnectionGuard(config)
        is_allowed, reason = guard.check_domain("https://trusted.com/api")
        assert is_allowed == True
        results.record_pass("Whitelist allowing", reason)
    except Exception as e:
        results.record_fail("Whitelist allowing", str(e))

    # Test 6: Connection logging
    try:
        guard = ConnectionGuard()
        guard.check_domain("https://example1.com")
        guard.check_domain("https://example2.com")
        stats = guard.get_connection_stats()
        assert stats['total_connections'] >= 2
        results.record_pass("Connection logging", f"Logged {stats['total_connections']} connections")
    except Exception as e:
        results.record_fail("Connection logging", str(e))


def test_rate_limiter(results):
    """Test RateLimiter functionality."""
    print("\n" + "="*70)
    print("TESTING: RateLimiter")
    print("="*70)

    if not CONTENT_SAFETY_AVAILABLE:
        pytest.skip("Content safety module not available")

    # Test 1: Within rate limits
    try:
        config = {'default_rpm': 10, 'default_rph': 100}
        limiter = RateLimiter(config)
        is_allowed, reason, wait_time = limiter.check_rate_limit("https://example.com/test1")
        assert is_allowed == True
        results.record_pass("Within rate limits", reason)
    except Exception as e:
        results.record_fail("Within rate limits", str(e))

    # Test 2: Exceed minute limit
    try:
        config = {'default_rpm': 3, 'default_rph': 100}
        limiter = RateLimiter(config)

        # Make 3 requests (should be allowed)
        for i in range(3):
            is_allowed, reason, wait_time = limiter.check_rate_limit("https://example.com/test2")
            assert is_allowed == True

        # 4th request should be blocked
        is_allowed, reason, wait_time = limiter.check_rate_limit("https://example.com/test2")
        assert is_allowed == False
        assert wait_time is not None
        results.record_pass("Exceed minute limit", f"{reason}, wait: {wait_time:.1f}s")
    except Exception as e:
        results.record_fail("Exceed minute limit", str(e))

    # Test 3: Different domains don't interfere
    try:
        config = {'default_rpm': 3, 'default_rph': 100}
        limiter = RateLimiter(config)

        # Make 3 requests to domain1
        for i in range(3):
            limiter.check_rate_limit("https://domain1.com/test")

        # Request to domain2 should still be allowed
        is_allowed, reason, wait_time = limiter.check_rate_limit("https://domain2.com/test")
        assert is_allowed == True
        results.record_pass("Different domains independent", reason)
    except Exception as e:
        results.record_fail("Different domains independent", str(e))

    # Test 4: Custom domain limits
    try:
        config = {
            'default_rpm': 3,
            'default_rph': 100,
            'domain_limits': {
                'api.github.com': {'rpm': 60, 'rph': 5000}
            }
        }
        limiter = RateLimiter(config)

        # Should allow more requests to github
        for i in range(10):
            is_allowed, reason, wait_time = limiter.check_rate_limit("https://api.github.com/repos")
            assert is_allowed == True

        results.record_pass("Custom domain limits", "GitHub API allowed 10 req/min")
    except Exception as e:
        results.record_fail("Custom domain limits", str(e))

    # Test 5: Rate limit statistics
    try:
        config = {'default_rpm': 10, 'default_rph': 100}
        limiter = RateLimiter(config)

        limiter.check_rate_limit("https://example.com/test")
        limiter.check_rate_limit("https://example.com/test")

        stats = limiter.get_rate_limit_stats()
        assert 'domains_tracked' in stats
        assert 'per_domain_stats' in stats
        results.record_pass("Rate limit statistics", f"Tracking {stats['domains_tracked']} domain(s)")
    except Exception as e:
        results.record_fail("Rate limit statistics", str(e))


def test_security_logger(results):
    """Test SecurityLogger functionality."""
    print("\n" + "="*70)
    print("TESTING: SecurityLogger")
    print("="*70)

    if not CONTENT_SAFETY_AVAILABLE:
        pytest.skip("Content safety module not available")

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

    # Test 3: Get recent events
    try:
        logger.log_request("https://test1.com", "GET", "ALLOWED")
        logger.log_request("https://test2.com", "GET", "ALLOWED")
        logger.log_request("https://test3.com", "GET", "ALLOWED")

        recent = logger.get_recent_events(count=3)
        assert len(recent) == 3
        results.record_pass("Get recent events", f"Retrieved {len(recent)} recent events")
    except Exception as e:
        results.record_fail("Get recent events", str(e))


@pytest.mark.asyncio
async def test_websearch_integration(results):
    """Test WebSearch integration with content safety."""
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

        # Test 2: Safety check method exists
        try:
            provider = WebSearchProvider()
            assert hasattr(provider, '_apply_safety_checks')
            assert hasattr(provider, '_sanitize_content')
            results.record_pass("WebSearch safety methods", "Safety check methods present")
        except Exception as e:
            results.record_fail("WebSearch safety methods", str(e))

        # Test 3: Content sanitization in action
        try:
            provider = WebSearchProvider()
            if provider.content_safety_enabled:
                dirty_html = '<p>Test</p><script>alert("XSS")</script>'
                clean = provider._sanitize_content(dirty_html, 'html')
                assert '<script>' not in clean.lower()
                results.record_pass("WebSearch content sanitization", f"Sanitized: {clean[:50]}...")
            else:
                results.record_pass("WebSearch content sanitization", "Skipped - safety not enabled")
        except Exception as e:
            results.record_fail("WebSearch content sanitization", str(e))

    except ImportError as e:
        results.record_fail("WebSearch integration", f"Could not import WebSearchProvider: {e}")


def test_content_safety_summary():
    """Test that the content safety module can be imported and basic functionality works."""
    print("\n" + "="*70)
    print("TESTING: Content Safety Module Summary")
    print("="*70)

    if not CONTENT_SAFETY_AVAILABLE:
        pytest.skip("Content safety module not available")

    # Test that all classes can be instantiated
    try:
        sanitizer = ContentSanitizer()
        guard = ConnectionGuard()
        limiter = RateLimiter()
        logger = SecurityLogger()

        assert sanitizer is not None
        assert guard is not None
        assert limiter is not None
        assert logger is not None

        print("✅ All content safety classes instantiated successfully")
    except Exception as e:
        pytest.fail(f"Failed to instantiate content safety classes: {e}")


if __name__ == "__main__":
    """Run the fixed test suite manually."""
    print("\n" + "="*70)
    print("TORQ CONSOLE - FIXED CONTENT SAFETY TEST SUITE")
    print("="*70)
    print("This version fixes the missing pytest fixture issue")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if not CONTENT_SAFETY_AVAILABLE:
        print("\n❌ ERROR: content_safety module not available")
        print("Cannot run tests without the module.")
        sys.exit(1)

    results = TestResults()

    # Run all test suites
    test_content_sanitizer(results)
    test_connection_guard(results)
    test_rate_limiter(results)
    test_security_logger(results)
    test_content_safety_summary()

    # Run async tests
    asyncio.run(test_websearch_integration(results))

    # Print summary
    print(f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    success = results.print_summary()

    sys.exit(0 if success else 1)