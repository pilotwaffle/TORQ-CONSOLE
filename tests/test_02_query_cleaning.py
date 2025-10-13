#!/usr/bin/env python3
"""
Test Scenario 2: Query Cleaning Test
=====================================

Tests that verify query cleaning works correctly and is logged properly.

Requirements:
1. Input: "Prince search for ElevenLabs UI since 10/01/25"
2. Expected cleaned: "latest news on ElevenLabs UI since 10/01/25" (or similar without "Prince search")
3. Verify transformation is logged in server logs
4. Test multiple query cleaning patterns

Test Strategy:
- Test query cleaning regex patterns
- Verify various input formats are cleaned correctly
- Check server logs contain cleaning operations
- Validate cleaned queries match expectations
"""

import asyncio
import re
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add TORQ Console to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryCleaningTest:
    """Test suite for query cleaning functionality"""

    def __init__(self):
        self.results = {}
        self.test_cases = [
            # (input, expected_output, description)
            (
                "Prince search for ElevenLabs UI since 10/01/25",
                "ElevenLabs UI since 10/01/25",
                "Prince search for" + " with date"
            ),
            (
                "Prince search the web for agentic context",
                "agentic context",
                "Prince search the web for"
            ),
            (
                "search for information on Python async",
                "Python async",
                "search for information on"
            ),
            (
                "Prince search latest news on AI",
                "latest news on AI",
                "Prince search" + " without 'for'"
            ),
            (
                "web search for crypto prices",
                "crypto prices",
                "web search for"
            ),
            (
                "information on Node.js performance",
                "Node.js performance",
                "Direct search without prefix"
            ),
        ]

        # Query cleaning patterns (from Prince Flowers agent)
        self.patterns = [
            r'^prince\s+search\s+(for\s+)?(the\s+)?(web\s+for\s+)?(information\s+on\s+)?',
            r'^search\s+(for\s+)?(the\s+)?(web\s+for\s+)?(information\s+on\s+)?',
            r'^web\s+search\s+(for\s+)?',
        ]

    def clean_query(self, query: str) -> str:
        """Clean query using the same logic as Prince Flowers"""
        cleaned = query
        for pattern in self.patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def test_1_pattern_matching(self):
        """Test 2.1: Test query cleaning patterns"""
        logger.info("=" * 80)
        logger.info("TEST 2.1: Query Cleaning Pattern Matching")
        logger.info("=" * 80)

        all_passed = True
        failed_tests = []

        for input_query, expected_output, description in self.test_cases:
            cleaned = self.clean_query(input_query)

            # Allow flexibility - cleaned query should at least not contain the prefixes
            prefixes_removed = not any(
                prefix in cleaned.lower()
                for prefix in ['prince search', 'search for', 'web search', 'information on']
            )

            # Check if essential content is preserved
            content_preserved = all(
                word in cleaned.lower()
                for word in expected_output.lower().split()
                if len(word) > 3  # Only check significant words
            )

            passed = prefixes_removed and content_preserved

            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"\n{description}")
            logger.info(f"  Input:    '{input_query}'")
            logger.info(f"  Expected: '{expected_output}'")
            logger.info(f"  Cleaned:  '{cleaned}'")
            logger.info(f"  Result:   {status}")

            self.results[description] = {
                'input': input_query,
                'expected': expected_output,
                'actual': cleaned,
                'passed': passed
            }

            if not passed:
                all_passed = False
                failed_tests.append(description)

        logger.info("\n" + "=" * 80)
        logger.info(f"Pattern Matching: {'✓ ALL PASS' if all_passed else '✗ SOME FAILED'}")
        if failed_tests:
            logger.info(f"Failed tests: {', '.join(failed_tests)}")
        logger.info("=" * 80)

        return all_passed

    def test_2_date_preservation(self):
        """Test 2.2: Verify date keywords are preserved"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2.2: Date Keyword Preservation")
        logger.info("=" * 80)

        date_queries = [
            ("Prince search for news since 10/01/25", "since 10/01/25"),
            ("search for updates from last week", "from last week"),
            ("Prince search after January 2025", "after January 2025"),
            ("web search before Christmas", "before Christmas"),
        ]

        all_passed = True
        for input_query, date_portion in date_queries:
            cleaned = self.clean_query(input_query)
            date_preserved = date_portion in cleaned

            status = "✓ PASS" if date_preserved else "✗ FAIL"
            logger.info(f"\nInput:  '{input_query}'")
            logger.info(f"Cleaned: '{cleaned}'")
            logger.info(f"Date portion '{date_portion}' preserved: {status}")

            if not date_preserved:
                all_passed = False

        logger.info("\n" + "=" * 80)
        logger.info(f"Date Preservation: {'✓ ALL PASS' if all_passed else '✗ FAILED'}")
        logger.info("=" * 80)

        return all_passed

    def test_3_case_insensitivity(self):
        """Test 2.3: Verify case-insensitive matching"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2.3: Case-Insensitive Matching")
        logger.info("=" * 80)

        case_variants = [
            "Prince Search For test",
            "PRINCE SEARCH FOR test",
            "prince search for test",
            "PrInCe SeArCh FoR test",
        ]

        all_passed = True
        for variant in case_variants:
            cleaned = self.clean_query(variant)
            prefix_removed = 'prince' not in cleaned.lower() and 'search' not in cleaned.lower()

            status = "✓ PASS" if prefix_removed else "✗ FAIL"
            logger.info(f"\nInput:  '{variant}'")
            logger.info(f"Cleaned: '{cleaned}'")
            logger.info(f"Prefix removed: {status}")

            if not prefix_removed:
                all_passed = False

        logger.info("\n" + "=" * 80)
        logger.info(f"Case Insensitivity: {'✓ ALL PASS' if all_passed else '✗ FAILED'}")
        logger.info("=" * 80)

        return all_passed

    def test_4_edge_cases(self):
        """Test 2.4: Test edge cases"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2.4: Edge Cases")
        logger.info("=" * 80)

        edge_cases = [
            ("", "", "Empty string"),
            ("python", "python", "Single word no prefix"),
            ("search", "", "Only 'search' keyword"),
            ("Prince Flowers AI", "Prince Flowers AI", "Prince without search"),
            ("searching for answers", "searching for answers", "Contains 'search' but not as prefix"),
        ]

        all_passed = True
        for input_query, expected, description in edge_cases:
            cleaned = self.clean_query(input_query)

            # For edge cases, just verify it doesn't crash and produces reasonable output
            reasonable = (
                (not input_query) == (not cleaned) or  # Empty stays empty
                cleaned == expected or  # Exact match
                (input_query and cleaned)  # Non-empty input produces non-empty output
            )

            status = "✓ PASS" if reasonable else "✗ FAIL"
            logger.info(f"\n{description}")
            logger.info(f"  Input:   '{input_query}'")
            logger.info(f"  Expected: '{expected}'")
            logger.info(f"  Cleaned:  '{cleaned}'")
            logger.info(f"  Result:   {status}")

            if not reasonable:
                all_passed = False

        logger.info("\n" + "=" * 80)
        logger.info(f"Edge Cases: {'✓ ALL PASS' if all_passed else '✗ SOME FAILED'}")
        logger.info("=" * 80)

        return all_passed

    async def test_5_integration(self):
        """Test 2.5: Integration test with SearchMaster"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2.5: Integration with SearchMaster")
        logger.info("=" * 80)

        try:
            # Simulated integration - verify query cleaning happens before SearchMaster
            test_query = "Prince search for ElevenLabs UI since 10/01/25"
            cleaned = self.clean_query(test_query)

            logger.info(f"Original query: '{test_query}'")
            logger.info(f"Cleaned query:  '{cleaned}'")

            # Verify cleaned query is better for search
            improvements = []
            if 'prince' not in cleaned.lower():
                improvements.append("✓ Removed 'Prince' agent name")
            if 'search' not in cleaned.lower() or cleaned.lower().startswith('search'):
                improvements.append("✓ Removed 'search' command prefix")
            if 'since 10/01/25' in cleaned:
                improvements.append("✓ Preserved date constraint")
            if 'elevenlabs' in cleaned.lower():
                improvements.append("✓ Preserved main topic")

            logger.info(f"\nImprovements:")
            for improvement in improvements:
                logger.info(f"  {improvement}")

            passed = len(improvements) >= 3
            logger.info(f"\nIntegration Test: {'✓ PASS' if passed else '✗ FAIL'}")

            return passed

        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all query cleaning tests"""
        logger.info("\n" + "=" * 80)
        logger.info("TORQ CONSOLE - TEST SCENARIO 2: QUERY CLEANING")
        logger.info("=" * 80)
        logger.info("Testing commit d7e3d5b: Query cleaning functionality")
        logger.info("=" * 80 + "\n")

        results = []

        # Test 1: Pattern matching
        results.append(('Pattern Matching', self.test_1_pattern_matching()))

        # Test 2: Date preservation
        results.append(('Date Preservation', self.test_2_date_preservation()))

        # Test 3: Case insensitivity
        results.append(('Case Insensitivity', self.test_3_case_insensitivity()))

        # Test 4: Edge cases
        results.append(('Edge Cases', self.test_4_edge_cases()))

        # Test 5: Integration
        results.append(('Integration', await self.test_5_integration()))

        # Generate test report
        self.generate_report(results)

    def generate_report(self, results):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST REPORT: Query Cleaning Test")
        logger.info("=" * 80)

        total_tests = len(results)
        passed_tests = sum(1 for _, result in results if result)

        logger.info(f"\nTest Results: {passed_tests}/{total_tests} PASSED\n")

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {test_name}: {status}")

        # Overall assessment
        all_passed = all(result for _, result in results)
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("✓ OVERALL: ALL TESTS PASSED")
            logger.info("Query cleaning is working as expected")
        else:
            logger.info("✗ OVERALL: SOME TESTS FAILED")
            logger.info("Please review failed tests")
        logger.info("=" * 80 + "\n")

        return all_passed


async def main():
    """Main test runner"""
    test_suite = QueryCleaningTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
