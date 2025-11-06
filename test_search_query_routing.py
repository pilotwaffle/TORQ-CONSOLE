#!/usr/bin/env python3
"""
Validation Test: Search Query Routing Fix

Validates that search queries (including "use X to search" patterns)
are correctly routed to WEB_SEARCH/RESEARCH capabilities instead of
CODE_GENERATION.

This test ensures the fix for the issue where queries like
"Use perplexity to search prince celebration 2026" incorrectly
triggered code generation.
"""

import asyncio
import sys
from torq_console.agents.marvin_query_router import (
    MarvinQueryRouter,
    AgentCapability
)


async def test_search_query_patterns():
    """Test that various search query patterns are correctly classified."""

    print("🧪 Testing Search Query Routing Fix")
    print("=" * 70)

    router = MarvinQueryRouter()

    # Test cases: (query, expected_capabilities, should_not_have)
    test_cases = [
        # Basic search queries
        (
            "search prince celebration 2026",
            [AgentCapability.WEB_SEARCH, AgentCapability.RESEARCH],
            [AgentCapability.CODE_GENERATION]
        ),
        # The problematic query that triggered code generation
        (
            "Use perplexity to search prince celebration 2026",
            [AgentCapability.WEB_SEARCH, AgentCapability.RESEARCH],
            [AgentCapability.CODE_GENERATION]
        ),
        # Similar patterns with tool names
        (
            "use google to find latest AI news",
            [AgentCapability.WEB_SEARCH, AgentCapability.RESEARCH],
            [AgentCapability.CODE_GENERATION]
        ),
        (
            "with brave search look up machine learning trends",
            [AgentCapability.WEB_SEARCH, AgentCapability.RESEARCH],
            [AgentCapability.CODE_GENERATION]
        ),
        # Make sure we still support code generation when explicitly requested
        (
            "write code that uses the Perplexity API",
            [AgentCapability.CODE_GENERATION],
            []
        ),
        (
            "generate code for a search application",
            [AgentCapability.CODE_GENERATION],
            []
        ),
        (
            "implement function to call Perplexity API",
            [AgentCapability.CODE_GENERATION],
            []
        ),
        # General chat (no search or code)
        (
            "what is the best way to structure a project?",
            [],  # Should get GENERAL_CHAT from intent, not from keywords
            [AgentCapability.CODE_GENERATION]
        ),
    ]

    passed = 0
    failed = 0

    for query, expected_caps, should_not_have in test_cases:
        print(f"\n📝 Testing: '{query}'")

        try:
            analysis = await router.analyze_query(query)
            capabilities = analysis.required_capabilities

            # Check expected capabilities
            missing = []
            for expected_cap in expected_caps:
                if expected_cap not in capabilities:
                    missing.append(expected_cap)

            # Check capabilities that should NOT be present
            unexpected = []
            for cap in should_not_have:
                if cap in capabilities:
                    unexpected.append(cap)

            # Determine pass/fail
            if not missing and not unexpected:
                print(f"   ✅ PASS")
                print(f"      Capabilities: {[c.value for c in capabilities]}")
                print(f"      Agent: {analysis.suggested_agent}")
                print(f"      Confidence: {analysis.confidence:.2f}")
                passed += 1
            else:
                print(f"   ❌ FAIL")
                if missing:
                    print(f"      Missing: {[c.value for c in missing]}")
                if unexpected:
                    print(f"      Unexpected: {[c.value for c in unexpected]}")
                print(f"      Got capabilities: {[c.value for c in capabilities]}")
                failed += 1

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 Test Results")
    print(f"=" * 70)
    print(f"   Passed: {passed}/{len(test_cases)}")
    print(f"   Failed: {failed}/{len(test_cases)}")
    print(f"   Success Rate: {passed/len(test_cases)*100:.1f}%")

    if failed == 0:
        print(f"\n✅ All tests passed! Search query routing is working correctly.")
        return True
    else:
        print(f"\n❌ Some tests failed. Please review the routing logic.")
        return False


async def test_specific_problematic_query():
    """Test the specific query mentioned in the bug report."""

    print(f"\n{'=' * 70}")
    print("🎯 Testing Specific Problematic Query")
    print(f"{'=' * 70}")

    router = MarvinQueryRouter()

    query = "Use perplexity to search prince celebration 2026"

    print(f"\nQuery: '{query}'")
    print(f"\nExpected Behavior:")
    print(f"   - Should route to WEB_SEARCH/RESEARCH capabilities")
    print(f"   - Should NOT trigger CODE_GENERATION")
    print(f"   - Should route to 'research_specialist' agent")
    print(f"\nActual Behavior:")

    analysis = await router.analyze_query(query)
    routing = await router.route_query(query)

    print(f"   Intent: {analysis.intent.value}")
    print(f"   Capabilities: {[c.value for c in analysis.required_capabilities]}")
    print(f"   Primary Agent: {routing.primary_agent}")
    print(f"   Fallback Agents: {routing.fallback_agents}")
    print(f"   Confidence: {analysis.confidence:.2f}")
    print(f"   Reasoning: {analysis.reasoning}")

    # Check if correct
    has_search = AgentCapability.WEB_SEARCH in analysis.required_capabilities
    has_research = AgentCapability.RESEARCH in analysis.required_capabilities
    no_code_gen = AgentCapability.CODE_GENERATION not in analysis.required_capabilities

    if has_search and has_research and no_code_gen:
        print(f"\n✅ CORRECT: Query properly routed to search/research!")
        return True
    else:
        print(f"\n❌ INCORRECT: Query routing still has issues:")
        if not has_search:
            print(f"   - Missing WEB_SEARCH capability")
        if not has_research:
            print(f"   - Missing RESEARCH capability")
        if not no_code_gen:
            print(f"   - Incorrectly has CODE_GENERATION capability")
        return False


async def main():
    """Run all validation tests."""

    print("🚀 Search Query Routing Validation Test Suite")
    print("=" * 70)
    print("This test validates the fix for search queries being misrouted")
    print("to code generation instead of web search/research.\n")

    # Run tests
    test1_passed = await test_search_query_patterns()
    test2_passed = await test_specific_problematic_query()

    # Final verdict
    print(f"\n{'=' * 70}")
    print("🏁 FINAL VERDICT")
    print(f"{'=' * 70}")

    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe fix successfully addresses the search query routing issue.")
        print("Prince Flowers will now correctly handle search queries instead of")
        print("generating code for search tools.")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nThe routing logic may need further adjustment.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
