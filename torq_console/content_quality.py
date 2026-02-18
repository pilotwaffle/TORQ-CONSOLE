"""
Content Quality Assertions for TORQ Console

This module provides utilities to detect when responses are off-task
(e.g., returning code when user asked for simple explanations).

These are "mode correct but content wrong" checks.
"""

import re
from typing import Optional, List


class ContentQualityChecker:
    """Checks if response content matches user intent."""

    # Patterns that suggest code generation
    CODE_PATTERNS = [
        r"```",           # Code fence
        r"package\.json", # npm package file
        r"<\?php",        # PHP tags
        r"import ",       # Import statements (with space to avoid word boundaries)
        r"from .* import", # Python imports
        r"interface ",    # TypeScript/Java interfaces
        r"class \w+\s*{", # Class definitions
        r"function\s+\w+\s*\(", # Function definitions
    ]

    # Patterns that are NOT code but look technical
    CODE_FALSE_POSITIVES = [
        r"import(?:ant)?\s+(?:to|for|the|that|this)",  # "important", "import" as verb
        r"(?:the\s+)?class\s*(?:of|is|was)",           # "the class of", "class is"
        r"function\s*(?:of|as|when)",                  # "function of", "function as"
    ]

    def __init__(self):
        # Compile regex patterns
        self.code_patterns = [re.compile(p, re.IGNORECASE) for p in self.CODE_PATTERNS]
        self.false_positives = [re.compile(p, re.IGNORECASE) for p in self.CODE_FALSE_POSITIVES]

    def has_code_indicators(self, text: str) -> bool:
        """
        Check if text contains code indicators.

        Returns True if text looks like code (excluding false positives).
        """
        text_lower = text.lower()

        # First check for false positives (non-code uses of technical words)
        for pattern in self.false_positives:
            if pattern.search(text):
                return False

        # Then check for actual code patterns
        for pattern in self.code_patterns:
            if pattern.search(text):
                return True

        return False

    def assert_simple_explanation(
        self,
        prompt: str,
        response: str,
        max_sentences: int = 5
    ) -> Optional[str]:
        """
        Assert that a "simple explanation" prompt doesn't return code.

        Use this for prompts like:
        - "Explain why 2+2=4"
        - "What is the capital of France?"
        - "How does photosynthesis work?"

        Args:
            prompt: The user's prompt
            response: The LLM's response
            max_sentences: Maximum expected sentences (for length check)

        Returns:
            Error message if assertion fails, None if passes
        """
        # Check for code when user asked for simple explanation
        simple_keywords = ["explain", "what is", "how does", "why is", "describe"]
        is_simple_prompt = any(kw in prompt.lower() for kw in simple_keywords)

        if is_simple_prompt and self.has_code_indicators(response):
            return f"Simple explanation prompt returned code content. Prompt: '{prompt[:50]}...'"

        # Check response length (simple explanations shouldn't be massive)
        # Rough heuristic: count sentences by periods
        sentence_count = response.count('.')
        if sentence_count > max_sentences:
            # Only warn if response is very long (might be legitimate detailed explanation)
            if len(response) > 2000:  # 2000+ chars with many sentences = probably wrong
                return f"Simple explanation prompt returned very long response ({len(response)} chars, {sentence_count} sentences)"

        return None

    def assert_code_generation(
        self,
        prompt: str,
        response: str
    ) -> Optional[str]:
        """
        Assert that a code generation prompt DOES return code.

        Use this for prompts like:
        - "Write a function that..."
        - "Create a class for..."
        - "Generate code to..."

        Args:
            prompt: The user's prompt
            response: The LLM's response

        Returns:
            Error message if assertion fails, None if passes
        """
        code_keywords = ["write", "create", "generate", "implement", "code", "function", "class"]
        is_code_prompt = any(kw in prompt.lower() for kw in code_keywords)

        if is_code_prompt and not self.has_code_indicators(response):
            return f"Code generation prompt returned no code. Prompt: '{prompt[:50]}...'"

        return None

    def assert_no_placeholders(
        self,
        response: str
    ) -> Optional[str]:
        """
        Assert that response doesn't contain placeholder/stub patterns.

        Args:
            response: The LLM's response

        Returns:
            Error message if assertion fails, None if passes
        """
        banned_patterns = [
            "placeholder",
            "stub",
            "todo",
            "not implemented",
            "coming soon",
            "your code here",
            "implement this",
        ]

        response_lower = response.lower()
        for pattern in banned_patterns:
            if pattern in response_lower:
                return f"Response contains placeholder/stub pattern: '{pattern}'"

        return None


# Singleton instance
_checker = None

def get_content_checker() -> ContentQualityChecker:
    """Get the singleton content quality checker."""
    global _checker
    if _checker is None:
        _checker = ContentQualityChecker()
    return _checker


def validate_simple_explanation(prompt: str, response: str) -> Optional[str]:
    """Convenience function to validate simple explanation responses."""
    return get_content_checker().assert_simple_explanation(prompt, response)


def validate_code_generation(prompt: str, response: str) -> Optional[str]:
    """Convenience function to validate code generation responses."""
    return get_content_checker().assert_code_generation(prompt, response)


def validate_no_placeholders(response: str) -> Optional[str]:
    """Convenience function to validate no placeholder/stub patterns."""
    return get_content_checker().assert_no_placeholders(response)
