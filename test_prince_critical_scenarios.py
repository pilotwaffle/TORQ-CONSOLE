#!/usr/bin/env python3
"""
Critical Scenario Tests for Enhanced Prince Flowers

Tests the exact failure cases that were reported by the user:
1. "search for top 3 posts on x.com" → Should WebSearch ✅
2. "Search the latest AI news 11/08/25" → Should WebSearch (was generating TypeScript) ❌
3. "Research new updates coming to GLM-4.6" → Should WebSearch (was generating TypeScript) ❌
4. "No that's not right" → Should trigger behavior change ❌
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.agents.action_learning import EnhancedActionLearning


def test_critical_scenarios():
    """Test the exact scenarios that were failing."""

    print("="*80)
    print("ENHANCED PRINCE - CRITICAL SCENARIO TESTS")
    print("Testing User's Exact Failure Cases")
    print("="*80)
    print()

    learning = EnhancedActionLearning()

    # Define critical test cases (user's exact failures)
    critical_cases = [
        {
            'id': 1,
            'query': 'search for top 3 posts on x.com',
            'expected': 'IMMEDIATE_ACTION',
            'historical': 'WORKED CORRECTLY',
            'severity': 'PASS'
        },
        {
            'id': 2,
            'query': 'Search the latest AI news 11/08/25',
            'expected': 'IMMEDIATE_ACTION',
            'historical': 'Generated 500+ lines of TypeScript',
            'severity': 'CRITICAL'
        },
        {
            'id': 3,
            'query': 'Research new updates coming to GLM-4.6',
            'expected': 'IMMEDIATE_ACTION',
            'historical': 'Generated TypeScript application',
            'severity': 'CRITICAL'
        },
        {
            'id': 4,
            'query': 'No that\'s not right',
            'expected': 'IMPLICIT_FEEDBACK',  # Should be detected as feedback
            'historical': 'Generated MORE TypeScript (validation system)',
            'severity': 'CRITICAL'
        },
        {
            'id': 5,
            'query': 'I want the top AI news',
            'expected': 'IMMEDIATE_ACTION',
            'historical': 'Generated TypeScript news app',
            'severity': 'CRITICAL'
        },
    ]

    # Additional test cases for comprehensive coverage
    additional_cases = [
        ('under ideation: search for viral TikTok videos', 'IMMEDIATE_ACTION'),
        ('find trending AI tools', 'IMMEDIATE_ACTION'),
        ('research latest developments in quantum computing', 'IMMEDIATE_ACTION'),
        ('build a todo app', 'ASK_CLARIFICATION'),
        ('create a weather application', 'ASK_CLARIFICATION'),
        ('develop a chat system', 'ASK_CLARIFICATION'),
    ]

    print("PART 1: CRITICAL FAILURE CASES")
    print("-" * 80)
    print()

    critical_passed = 0
    critical_failed = 0

    for case in critical_cases:
        query = case['query']
        expected = case['expected']

        # Special handling for feedback detection
        if expected == 'IMPLICIT_FEEDBACK':
            # Check if it matches negative feedback patterns
            result = 'IMPLICIT_FEEDBACK' if learning._matches_implicit_feedback(query) else 'NOT_DETECTED'
        else:
            result = learning.classify_action(query)

        passed = (result == expected)
        status = '✅ PASS' if passed else '❌ FAIL'

        if passed:
            critical_passed += 1
        else:
            critical_failed += 1

        print(f"Test #{case['id']}: {status}")
        print(f"  Query: \"{query}\"")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print(f"  Historical Behavior: {case['historical']}")
        print(f"  Severity: {case['severity']}")
        print()

    print()
    print("PART 2: ADDITIONAL COVERAGE")
    print("-" * 80)
    print()

    additional_passed = 0
    additional_failed = 0

    for query, expected in additional_cases:
        result = learning.classify_action(query)
        passed = (result == expected)
        status = '✅' if passed else '❌'

        if passed:
            additional_passed += 1
        else:
            additional_failed += 1

        print(f"{status} \"{query}\"")
        print(f"   Expected: {expected}, Got: {result}")
        print()

    # Summary
    total_critical = len(critical_cases)
    total_additional = len(additional_cases)
    total_tests = total_critical + total_additional
    total_passed = critical_passed + additional_passed
    total_failed = critical_failed + additional_failed

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print(f"Critical Tests: {critical_passed}/{total_critical} passed ({100*critical_passed/total_critical:.1f}%)")
    print(f"Additional Tests: {additional_passed}/{total_additional} passed ({100*additional_passed/total_additional:.1f}%)")
    print(f"Overall: {total_passed}/{total_tests} passed ({100*total_passed/total_tests:.1f}%)")
    print()

    if critical_failed == 0:
        print("🎉 EXCELLENT! All critical failure cases now pass!")
    else:
        print(f"⚠️  WARNING: {critical_failed} critical test(s) still failing")

    print()
    print("="*80)

    return critical_passed, critical_failed, additional_passed, additional_failed


if __name__ == "__main__":
    test_critical_scenarios()
