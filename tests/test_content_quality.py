"""
Test Content Quality Assertions for TORQ Console

These tests verify that response content matches user intent:
- Simple explanations don't return code
- Code generation prompts DO return code
- No placeholder/stub patterns

Run: pytest tests/test_content_quality.py -v
"""

import pytest
import requests
from torq_console.content_quality import validate_simple_explanation, validate_no_placeholders


class TestContentQuality:
    """Validate response content matches user intent."""

    @pytest.fixture(scope="module")
    def base_url(self):
        return "http://127.0.0.1:8899"

    def test_simple_math_explanation_no_code(self, base_url):
        """
        Test: Simple math explanation doesn't return code.

        This is the "mode correct but content wrong" check.
        Semantic metadata can be perfect, but content should still match intent.
        """
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "Explain why 2+2=4 in one sentence."},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success", True) is True

        # Check content quality
        error = validate_simple_explanation(
            "Explain why 2+2=4 in one sentence.",
            data.get("response", "")
        )

        # This will FAIL if the LLM returns code (like the TypeScript project we saw)
        # If it fails, it means routing/intent detection is biased toward code
        if error:
            pytest.fail(f"Content quality check failed: {error}")

    def test_simple_question_no_code(self, base_url):
        """Test: Simple factual question doesn't return code."""
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "What is the capital of France? Answer in one sentence."},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success", True) is True

        error = validate_simple_explanation(
            "What is the capital of France?",
            data.get("response", "")
        )

        if error:
            pytest.fail(f"Content quality check failed: {error}")

    def test_no_placeholder_patterns(self, base_url):
        """Test: Responses don't contain placeholder/stub patterns."""
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "What is 3+3?"},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        error = validate_no_placeholders(data.get("response", ""))
        if error:
            pytest.fail(f"Placeholder check failed: {error}")

    def test_code_generation_prompt_returns_code(self, base_url):
        """
        Test: Code generation prompt DOES return code.

        This is the inverse check - when user explicitly asks for code,
        the system should return code.
        """
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": "Write a Python function to add two numbers."},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("success", True) is True

        # Look for code indicators in response
        response_text = data.get("response", "")

        # Should have code fence or "def " or "class " etc.
        has_code = (
            "```" in response_text or
            "def " in response_text or
            "class " in response_text or
            "function " in response_text
        )

        if not has_code:
            pytest.fail("Code generation prompt didn't return code content")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
