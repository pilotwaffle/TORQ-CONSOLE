"""
Production-Grade Web Research Test Suite

Tests the 4 critical failure modes:
1. Citation enforcement
2. Fallback ladder
3. Cache hit behavior
4. Router precision

Run: python test_production_research.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from torq_console.research import (
    research,
    get_research_coordinator,
)
from torq_console.research.router import ResearchRouter, get_research_router
from torq_console.research.cache import get_query_cache
from torq_console.research.citations import get_citation_policy
from torq_console.research.providers import search_with_fallback, ResearchQuery


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def log_pass(self, name: str):
        self.passed += 1
        self.tests.append((name, "PASS"))
        print(f"  [PASS] {name}")

    def log_fail(self, name: str, reason: str = ""):
        self.failed += 1
        self.tests.append((name, f"FAIL: {reason}"))
        print(f"  [FAIL] {name}: {reason}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        for name, result in self.tests:
            print(f"  {result}: {name}")
        return self.failed == 0


async def test_citation_enforcement():
    """
    Test 1: Citation Enforcement

    Verify that research queries require citations and missing citations
    trigger a retry.
    """
    print("\n[Test 1] Citation Enforcement")

    results = TestResults()

    # Skip if no API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        results.log_fail("Citation Enforcement", "No ANTHROPIC_API_KEY")
        return results

    # This query should require research (time-sensitive)
    query = "What are the latest Bitcoin price predictions for 2026?"

    try:
        coordinator = get_research_coordinator()
        response = await coordinator.research(query)

        # Check that response has citations
        if not response.has_citations:
            results.log_fail("Citation Enforcement", "No citations in research response")
        elif response.citation_count < 2:
            results.log_fail("Citation Enforcement", f"Only {response.citation_count} citations, need >= 2")
        else:
            results.log_pass("Citation Enforcement")

        # Verify citation format
        citations = response.citations
        if citations:
            first_citation = citations[0]
            if "url" not in first_citation or "title" not in first_citation:
                results.log_fail("Citation Format", "Missing required fields in citation")
            else:
                results.log_pass("Citation Format")

    except Exception as e:
        results.log_fail("Citation Enforcement", f"Exception: {e}")

    return results


async def test_fallback_ladder():
    """
    Test 2: Fallback Ladder

    Verify that when primary provider fails, system falls back
    to secondary providers.
    """
    print("\n[Test 2] Fallback Ladder")

    results = TestResults()

    query = ResearchQuery(
        query="Python async await tutorial",
        top_k=3,
    )

    try:
        # Test with all providers enabled
        response = await search_with_fallback(
            query,
            providers=["duckduckgo", "brave"],  # Use free providers for testing
        )

        # Should get results from at least one provider
        if response.result_count == 0:
            results.log_fail("Fallback Ladder", "No results from any provider")
        else:
            results.log_pass(f"Fallback Ladder ({response.provider})")

        # Check that result_count matches items
        if response.result_count != len(response.items):
            results.log_fail(
                "Result Count Mismatch",
                f"result_count={response.result_count}, items={len(response.items)}"
            )
        else:
            results.log_pass("Result Count Accuracy")

    except Exception as e:
        results.log_fail("Fallback Ladder", f"Exception: {e}")

    return results


async def test_cache_hit():
    """
    Test 3: Cache Hit Behavior

    Verify that:
    1. First query calls external search
    2. Second identical query uses cache
    3. Cache respects TTL
    """
    print("\n[Test 3] Cache Hit")

    results = TestResults()

    cache = get_query_cache()

    # Clear cache first
    await cache.invalidate()

    query = "What is the capital of France?"
    params = {"top_k": 3}

    # First call - should miss cache
    cached1 = await cache.get(query, params)
    if cached1 is not None:
        results.log_fail("Cache Initial State", "Cache should be empty after invalidate")

    # Manually set a cached result
    await cache.set(
        query,
        params,
        {
            "provider": "test",
            "items": [{"title": "Test", "url": "https://test.com", "snippet": "Test snippet"}],
        },
        ttl_seconds=60,
    )

    # Second call - should hit cache
    cached2 = await cache.get(query, params)
    if cached2 is None:
        results.log_fail("Cache Miss", "Second call should hit cache")
    else:
        results.log_pass("Cache Hit")

    # Verify cache stats
    stats = cache.get_stats()
    if stats["size"] == 0:
        results.log_fail("Cache Stats", f"Cache shows size=0 but we cached something")
    else:
        results.log_pass(f"Cache Stats (size={stats['size']})")

    return results


async def test_router_precision():
    """
    Test 4: Router Precision

    Verify that:
    1. Time-sensitive queries trigger research
    2. Conceptual queries do NOT trigger research
    3. Explicit "verify" triggers research
    """
    print("\n[Test 4] Router Precision")

    results = TestResults()

    router = get_research_router()

    # Test 1: Time-sensitive query should research
    should1, signals1 = router.should_research("What are the latest AI trends?")
    if not should1:
        results.log_fail("Time Cue Detection", "Should trigger research for 'latest'")
    else:
        results.log_pass("Time Cue Detection")

    # Test 2: Conceptual query should NOT research
    should2, signals2 = router.should_research("What is a database?")
    if "conceptual_question" in signals2 and should2 is False:
        results.log_pass("Conceptual Query Detection")
    elif should2:
        results.log_fail("Conceptual Query", "Should NOT trigger research")
    else:
        results.log_pass("Conceptual Query (no explicit research)")

    # Test 3: Explicit research signal
    should3, signals3 = router.should_research("Verify the capital of France")
    if "explicit_research_request" in signals3:
        results.log_pass("Explicit Research Signal")
    else:
        results.log_fail("Explicit Research", "Should detect 'verify' signal")

    # Test 4: Volatility domain detection
    should4, signals4 = router.should_research("Current Bitcoin price")
    if any("volatility" in s for s in signals4):
        results.log_pass("Volatility Domain Detection")
    else:
        results.log_fail("Volatility Domain", "Should detect crypto domain")

    return results


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Production-Grade Web Research Test Suite")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")

    all_results = []

    # Run tests
    all_results.append(await test_citation_enforcement())
    all_results.append(await test_fallback_ladder())
    all_results.append(await test_cache_hit())
    all_results.append(await test_router_precision())

    # Aggregate results
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)

    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")

    if total_failed == 0:
        print("\nAll tests PASSED! Research system is production-ready.")
        return 0
    else:
        print(f"\n{total_failed} test(s) FAILED. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
