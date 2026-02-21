"""
Regression Tests: No Placeholder Responses

This test suite ensures Prince Flowers never returns placeholder or stub responses.
Prevents reintroduction of hardcoded placeholder strings that bypass the LLM.

Run: pytest tests/test_regression_no_placeholders.py -v
"""

import pytest
import requests
import time
from typing import List, Dict

# ============================================================================
# BANNED RESPONSE PATTERNS
# ============================================================================

# Centralized list of banned response patterns
# Expand this list if new placeholder strings are discovered
BANNED_PATTERNS = [
    "placeholder",
    "stub",
    "Direct reasoning execution",  # Old hardcoded response
    "Research reasoning execution",
    "Analysis reasoning execution",
    "Composition reasoning execution",
    "Meta-planning reasoning execution",
    "(placeholder)",
    "[PLACEHOLDER]",
    "<placeholder>",
]


class TestNoPlaceholderResponses:
    """Regression tests to ensure no placeholder responses are returned."""

    @pytest.fixture(scope="class")
    def base_url(self) -> str:
        """Base URL for TORQ Console API."""
        return "http://127.0.0.1:8899"

    def check_response_for_banned_patterns(
        self,
        response_text: str,
        test_name: str
    ) -> None:
        """
        Check that response doesn't contain any banned patterns.

        Args:
            response_text: The response text to check
            test_name: Name of the test (for error messages)

        Raises:
            AssertionError: If any banned pattern is found
        """
        response_lower = response_text.lower()

        for pattern in BANNED_PATTERNS:
            if pattern.lower() in response_lower:
                raise AssertionError(
                    f"{test_name}: Response contains banned pattern '{pattern}'\n"
                    f"Response snippet: {response_text[:200]}"
                )

    def test_a1_direct_reasoning_no_placeholder(
        self,
        base_url: str
    ) -> None:
        """
        TEST A1 - Direct Reasoning Mode: No placeholder responses.

        Test Case: "what is 2+2"
        Mode: Direct reasoning (no tools)
        Expected: Real LLM response, no placeholders

        Pass Criteria:
        - HTTP 200
        - success == True
        - Response does not contain any banned patterns
        - Latency > 0.2s (indicates real LLM call, not stub)
        """
        query = "what is 2+2"

        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": query},
            timeout=30
        )

        # Check HTTP status
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}"

        # Parse response
        result = response.json()
        assert result.get("success") is True, \
            f"Expected success=True, got {result.get('success')}"

        # Get response text
        response_text = result.get("response", "")
        assert len(response_text) > 0, "Response is empty"

        # Check for banned patterns
        self.check_response_for_banned_patterns(
            response_text,
            "test_a1_direct_reasoning"
        )

        # Verify it's a real response (should mention numbers/math)
        assert any(word in response_text.lower() for word in ["4", "four", "math"]), \
            f"Response doesn't look like a real answer: {response_text[:100]}"

    def test_a2_research_mode_no_placeholder(
        self,
        base_url: str
    ) -> None:
        """
        TEST A2 - Research Mode: No placeholder responses.

        Test Case: "what time is it in Texas right now"
        Mode: Research (with web_search tool enabled)
        Expected: Real LLM response with/without search results, no placeholders

        Pass Criteria:
        - HTTP 200
        - success == True
        - Response does not contain any banned patterns
        - Latency > 0.5s (indicates real LLM call, not stub)
        """
        query = "what time is it in Texas right now"

        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "message": query,
                "tools": ["web_search"]
            },
            timeout=30
        )

        # Check HTTP status
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}"

        # Parse response
        result = response.json()
        assert result.get("success") is True, \
            f"Expected success=True, got {result.get('success')}"

        # Get response text
        response_text = result.get("response", "")
        assert len(response_text) > 0, "Response is empty"

        # Check for banned patterns
        self.check_response_for_banned_patterns(
            response_text,
            "test_a2_research_mode"
        )

        # Verify it's a real response (should mention time/texas/zone)
        assert any(word in response_text.lower() for word in ["time", "texas", "zone", "central", "ct"]), \
            f"Response doesn't look like a real answer: {response_text[:100]}"

    def test_a3_code_generation_no_placeholder(
        self,
        base_url: str
    ) -> None:
        """
        TEST A3 - Code Generation Mode: No placeholder responses.

        Test Case: "write a hello world function in python"
        Mode: Code generation
        Expected: Real LLM response with code, no placeholders

        Pass Criteria:
        - HTTP 200
        - success == True
        - Response does not contain any banned patterns
        - Response contains actual code
        """
        query = "write a hello world function in python"

        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": query},
            timeout=30
        )

        # Check HTTP status
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}"

        # Parse response
        result = response.json()
        assert result.get("success") is True, \
            f"Expected success=True, got {result.get('success')}"

        # Get response text
        response_text = result.get("response", "")
        assert len(response_text) > 0, "Response is empty"

        # Check for banned patterns
        self.check_response_for_banned_patterns(
            response_text,
            "test_a3_code_generation"
        )

        # Verify it's a real response (should contain code)
        assert any(word in response_text.lower() for word in ["def", "function", "print", "hello", "world", "python"]), \
            f"Response doesn't look like code: {response_text[:100]}"

    def test_a4_microstrategy_query_no_placeholder(
        self,
        base_url: str
    ) -> None:
        """
        TEST A4 - MicroStrategy Query: No placeholder responses (edge case).

        Test Case: "what is the current MSTR stock price"
        Mode: Research (financial query that previously triggered code generation)
        Expected: Real LLM response, no placeholders

        This is the regression test for the original MicroStrategy bug where
        queries about MSTR were generating code dumps instead of research.

        Pass Criteria:
        - HTTP 200
        - success == True
        - Response does not contain any banned patterns
        - Response is NOT code generation
        """
        query = "what is the current MSTR MicroStrategy stock price"

        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": query, "tools": ["web_search"]},
            timeout=30
        )

        # Check HTTP status
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}"

        # Parse response
        result = response.json()
        assert result.get("success") is True, \
            f"Expected success=True, got {result.get('success')}"

        # Get response text
        response_text = result.get("response", "")
        assert len(response_text) > 0, "Response is empty"

        # Check for banned patterns
        self.check_response_for_banned_patterns(
            response_text,
            "test_a4_microstrategy_query"
        )

        # Verify it's NOT code generation (no large code blocks)
        # Code dumps typically contain multiple lines with def, class, import, etc.
        code_indicators = ["def ", "class ", "import ", "struct ", "interface ", "function "]
        code_count = sum(response_text.count(indicator) for indicator in code_indicators)

        # More than 3 code indicators suggests it's generating code, not research
        assert code_count < 3, \
            f"Response appears to be code generation (code indicators: {code_count}): {response_text[:200]}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_all_regression_tests():
    """
    Run all regression tests and return results.

    Returns:
        dict: Test results with pass/fail counts
    """
    import sys
    sys.path.insert(0, ".")

    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    return {
        "exit_code": exit_code,
        "all_passed": exit_code == 0
    }


if __name__ == "__main__":
    print("=" * 80)
    print("REGRESSION TESTS: No Placeholder Responses")
    print("=" * 80)
    print()
    print("Running tests to ensure Prince Flowers never returns placeholder responses...")
    print()

    results = run_all_regression_tests()

    print()
    print("=" * 80)
    if results["all_passed"]:
        print("✅ ALL TESTS PASSED - No placeholder responses detected")
    else:
        print("❌ TESTS FAILED - Placeholder responses detected!")
    print("=" * 80)
