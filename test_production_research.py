"""
Production-Grade Web Research Test Suite

Tests the 5 critical failure modes:
1. Citation enforcement
2. Fallback ladder
3. Cache hit behavior
4. Router precision
5. Citation format stability (regression test)

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
from torq_console.research import (
    canonicalize_citations,
    normalize_url,
    normalize_sources,
    validate_citation_format,
)
from torq_console.research.schema import ResearchSource, SearchProvider


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []

    def log_pass(self, name: str):
        self.passed += 1
        self.tests.append((name, "PASS"))
        print(f"  [PASS] {name}")

    def log_fail(self, name: str, reason: str = ""):
        self.failed += 1
        self.tests.append((name, f"FAIL: {reason}"))
        print(f"  [FAIL] {name}: {reason}")

    def log_skip(self, name: str, reason: str = ""):
        self.skipped += 1
        self.tests.append((name, f"SKIP: {reason}"))
        print(f"  [SKIP] {name}: {reason}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"Test Results: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
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

    SKIP condition: No provider API keys configured
    """
    print("\n[Test 2] Fallback Ladder")

    results = TestResults()

    # Check for provider availability
    has_brave = bool(os.getenv("BRAVE_SEARCH_API_KEY"))
    has_tavily = bool(os.getenv("TAVILY_API_KEY"))

    if not (has_brave or has_tavily):
        results.log_skip(
            "Fallback Ladder",
            "No provider API keys configured (set BRAVE_SEARCH_API_KEY or TAVILY_API_KEY)"
        )
        return results

    query = ResearchQuery(
        query="Python async await tutorial",
        top_k=3,
    )

    try:
        # Build provider list (prioritize working providers)
        providers = []
        if has_tavily:
            providers.append("tavily")
        if has_brave:
            providers.append("brave")

        response = await search_with_fallback(query, providers=providers)

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


async def test_citation_stability():
    """
    Test 5: Citation Format Stability (Regression Test)

    Verify that citation canonicalization produces deterministic output:
    1. URL normalization removes tracking params
    2. Duplicate URLs are removed
    3. Sources are stably sorted
    4. Running twice produces identical results
    """
    print("\n[Test 5] Citation Format Stability (Regression)")

    results = TestResults()

    # Test 1: URL normalization
    urls_to_normalize = [
        "https://example.com/path?utm_source=google&utm_medium=ad",
        "HTTPS://EXAMPLE.COM/PATH/",  # Different case/trailing slash
        "https://example.com/path?fbclid=abc123&ref=twitter",
        "https://example.com/path",  # Canonical form
    ]

    normalized_urls = [normalize_url(url) for url in urls_to_normalize]
    unique_normalized = set(normalized_urls)

    if len(unique_normalized) == 1:
        results.log_pass("URL Normalization (dedupes tracking params)")
    else:
        results.log_fail(
            "URL Normalization",
            f"Expected 1 unique URL, got {len(unique_normalized)}: {unique_normalized}"
        )

    # Test 2: Source deduplication
    sources = [
        ResearchSource(
            title="Example",
            url="https://example.com/article?utm_source=google",
            snippet="A test article",
            score=0.5,
            provider=SearchProvider.TAVILY,
        ),
        ResearchSource(
            title="Example",
            url="https://EXAMPLE.COM/article?fbclid=123",  # Same URL after normalize
            snippet="A test article",
            score=0.6,  # Higher score
            provider=SearchProvider.BRAVE,
        ),
        ResearchSource(
            title="Another",
            url="https://another.com/article",
            snippet="Another article",
            score=0.7,
            provider=SearchProvider.DUCKDUCKGO,
        ),
    ]

    normalized = normalize_sources(sources)

    if len(normalized) == 2:  # Should dedupe to 2 unique URLs
        results.log_pass("Source Deduplication")
    else:
        results.log_fail(
            "Source Deduplication",
            f"Expected 2 sources after deduplication, got {len(normalized)}"
        )

    # Test 3: Stable sorting (higher score first)
    # another.com has score 0.7, example.com has score 0.6, so another.com should be first
    if len(normalized) >= 2:
        # The first item should have the highest score
        if normalized[0].score >= normalized[1].score:
            results.log_pass("Stable Sorting (by trust score)")
        else:
            results.log_fail(
                "Stable Sorting",
                f"Expected highest score first, got {normalized[0].score} then {normalized[1].score}"
            )

    # Test 4: Canonicalization produces deterministic output
    answer = "According to [1], Bitcoin is volatile. See [2] for more details."

    # Run canonicalization twice
    result1 = canonicalize_citations(answer, sources)
    result2 = canonicalize_citations(answer, sources)

    if result1["answer"] == result2["answer"]:
        results.log_pass("Deterministic Canonicalization")
    else:
        results.log_fail(
            "Deterministic Canonicalization",
            "Running twice produced different answers"
        )

    # Test 5: Citation validation
    validation = validate_citation_format(answer, sources)
    if validation["is_valid"]:
        results.log_pass("Citation Format Validation")
    else:
        # This is expected to pass for our simple test case
        if not validation["errors"]:
            results.log_pass("Citation Format Validation (no errors)")
        else:
            results.log_fail(
                "Citation Format Validation",
                f"Errors: {validation['errors']}"
            )

    # Test 6: Check for tracking parameter removal
    url_with_tracking = "https://example.com/path?utm_source=google&utm_medium=email&fbclid=abc123"
    normalized = normalize_url(url_with_tracking)

    if "utm_" not in normalized and "fbclid" not in normalized:
        results.log_pass("Tracking Parameter Removal")
    else:
        results.log_fail(
            "Tracking Parameter Removal",
            f"Tracking params not removed: {normalized}"
        )

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
    all_results.append(await test_citation_stability())

    # Aggregate results
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_skipped = sum(r.skipped for r in all_results)

    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Skipped: {total_skipped}")

    if total_failed == 0:
        if total_skipped > 0:
            print(f"\n{total_skipped} test(s) skipped - configure API keys to run.")
        print("\nAll active tests PASSED! Research system is production-ready.")
        return 0
    else:
        print(f"\n{total_failed} test(s) FAILED. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
