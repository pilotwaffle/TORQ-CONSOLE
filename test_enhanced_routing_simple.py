"""
Simple standalone test for enhanced query routing.
Tests the core routing logic without requiring full TORQ Console environment.
"""

import re


class SimpleEnhancedRouter:
    """Simplified version of enhanced query router for testing."""

    def __init__(self):
        # Priority 1: Explicit code request patterns
        self.explicit_code_patterns = [
            'write code', 'generate code', 'create code', 'implement code',
            'code for', 'write a script', 'generate a script', 'create a script',
            'write application', 'generate application', 'build application'
        ]

        # Priority 2: Search intent patterns
        self.search_patterns = [
            'search', 'find', 'look up', 'lookup', 'research', 'investigate',
            'what is', 'who is', 'where is', 'when is', 'how to', 'why does',
            'tell me about', 'information about', 'details on'
        ]

        # Tool-based search patterns
        self.tool_based_search_patterns = [
            r'use .* to (search|find|lookup|look up)',
            r'with .* (search|find|lookup|look up)',
            r'via .* (search|find|lookup|look up)',
            r'through .* (search|find|lookup|look up)'
        ]

    def route_query(self, query: str) -> dict:
        """Route query based on priority patterns."""
        query_lower = query.lower()

        # Priority 1: Explicit code generation request?
        for pattern in self.explicit_code_patterns:
            if query_lower.startswith(pattern) or f" {pattern} " in query_lower:
                return {
                    'intent': 'CODE_GENERATION',
                    'confidence': 0.95,
                    'reasoning': f'Explicit code request: "{pattern}"'
                }

        # Check for "generate X functionality" pattern
        if query_lower.startswith('generate ') and 'functionality' in query_lower:
            return {
                'intent': 'CODE_GENERATION',
                'confidence': 0.85,
                'reasoning': 'Generate functionality pattern'
            }

        # Priority 2: Tool-based search pattern?
        for pattern in self.tool_based_search_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'WEB_SEARCH',
                    'confidence': 0.9,
                    'reasoning': f'Tool-based search pattern: "{pattern}"'
                }

        # Priority 3: General search intent?
        search_score = 0
        matched = []
        for pattern in self.search_patterns:
            if pattern in query_lower:
                search_score += 1
                matched.append(pattern)

        if search_score > 0:
            return {
                'intent': 'WEB_SEARCH',
                'confidence': min(0.7 + (search_score * 0.1), 0.95),
                'reasoning': f'Search patterns: {matched}'
            }

        # Default: Research
        return {
            'intent': 'RESEARCH',
            'confidence': 0.5,
            'reasoning': 'Default routing'
        }


def run_tests():
    """Run comprehensive test cases."""
    router = SimpleEnhancedRouter()

    print("="*80)
    print("Prince Flowers Enhanced - Query Routing Test Suite")
    print("="*80)

    test_cases = [
        # Explicit code requests (should be CODE_GENERATION)
        ("write code for authentication", "CODE_GENERATION", "Explicit code request"),
        ("generate code using Perplexity API", "CODE_GENERATION", "Explicit code with API mention"),
        ("create code for search app", "CODE_GENERATION", "Explicit code with search mention"),
        ("implement code for database", "CODE_GENERATION", "Explicit implementation request"),

        # Tool-based search (should be WEB_SEARCH, NOT code generation!)
        ("use perplexity to search prince celebration 2026", "WEB_SEARCH", "Problematic query from bug report"),
        ("use google to find AI news", "WEB_SEARCH", "Tool-based search with 'use'"),
        ("with duckduckgo search quantum computing", "WEB_SEARCH", "Tool-based search with 'with'"),
        ("via bing lookup historical events", "WEB_SEARCH", "Tool-based search with 'via'"),

        # General search (should be WEB_SEARCH)
        ("search prince celebration 2026", "WEB_SEARCH", "Direct search query"),
        ("find information about AI", "WEB_SEARCH", "Find query"),
        ("research quantum computing", "WEB_SEARCH", "Research query"),
        ("what is machine learning", "WEB_SEARCH", "Question query"),

        # Edge cases
        ("write code to search database", "CODE_GENERATION", "Code request with search mention"),
        ("generate search functionality", "CODE_GENERATION", "Generate with search"),
        ("tell me about Python", "WEB_SEARCH", "Information request"),
    ]

    passed = 0
    failed = 0
    results = []

    print("\nTest Results:")
    print("-"*80)

    for query, expected, description in test_cases:
        result = router.route_query(query)
        actual = result['intent']
        confidence = result['confidence']
        reasoning = result['reasoning']

        if actual == expected:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        results.append((status, query, expected, actual, confidence, reasoning, description))

    # Print results
    for status, query, expected, actual, confidence, reasoning, description in results:
        print(f"\n{status}")
        print(f"  Description: {description}")
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Actual: {actual}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Reasoning: {reasoning}")

    # Summary
    print("\n" + "="*80)
    print(f"Test Summary: {passed} passed, {failed} failed out of {len(test_cases)} total")
    print("="*80)

    if failed == 0:
        print("\n[SUCCESS] All tests passed! Enhanced routing working correctly.")
        print("\nKey fixes validated:")
        print("  [OK] 'use X to search' patterns route to WEB_SEARCH (not CODE_GENERATION)")
        print("  [OK] Explicit code requests correctly detected")
        print("  [OK] General search patterns working")
        print("  [OK] Priority ordering working correctly")
    else:
        print(f"\n[ERROR] {failed} test(s) failed. Review routing logic.")

    return passed == len(test_cases)


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
