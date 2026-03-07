"""
LLM-based workflow planner.

Calls Claude to generate workflow drafts from user prompts.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Tuple

from .prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class WorkflowPlannerLLMError(Exception):
    """Raised when the LLM call fails or returns invalid data."""

    pass


class WorkflowPlanner:
    """
    Generates workflow drafts using Claude.

    Responsibilities:
    - Interpret user goals
    - Select appropriate workflow pattern
    - Choose agents
    - Infer dependencies
    - Output valid graph schema
    """

    def __init__(self, anthropic_client: Any, model: str = "claude-sonnet-4-6"):
        """
        Initialize the workflow planner.

        Args:
            anthropic_client: Anthropic client instance
            model: Model to use for generation
        """
        self.anthropic_client = anthropic_client
        self.model = model

    def generate_raw_draft(self, prompt: str) -> Tuple[Dict[str, Any], int]:
        """
        Generate a raw workflow draft from a user prompt.

        Args:
            prompt: User's natural language workflow description

        Returns:
            Tuple of (raw draft dict, generation time in ms)

        Raises:
            WorkflowPlannerLLMError: If generation fails or returns invalid JSON
        """
        started = time.perf_counter()

        try:
            logger.info(f"Generating workflow draft for prompt: {prompt[:100]}...")

            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.2,  # Low temperature for consistent structure
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": build_user_prompt(prompt),
                    }
                ],
            )

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise WorkflowPlannerLLMError(f"planner_request_failed: {e}") from e

        elapsed_ms = int((time.perf_counter() - started) * 1000)

        try:
            # Extract text from response blocks
            text = "".join(
                block.text
                for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip()

            # Parse JSON
            data = json.loads(text)

            logger.info(f"Generated draft with {len(data.get('nodes', []))} nodes in {elapsed_ms}ms")
            return data, elapsed_ms

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {text[:500]}")
            raise WorkflowPlannerLLMError(f"planner_invalid_json: {e}") from e
        except Exception as e:
            logger.error(f"Failed to process LLM response: {e}")
            raise WorkflowPlannerLLMError(f"planner_processing_error: {e}") from e
