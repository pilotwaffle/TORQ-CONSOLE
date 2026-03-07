"""
Workflow planner service - Orchestrates the planning pipeline.

Planner → Normalize → Validate → (retry once on failure)
"""

from __future__ import annotations

import logging
from typing import Any

from .graph_drafter import normalize_raw_draft
from .models import WorkflowPlannerResponse
from .planner import WorkflowPlanner, WorkflowPlannerLLMError
from .validator import WorkflowDraftValidationError, validate_workflow_draft

logger = logging.getLogger(__name__)


class WorkflowPlannerService:
    """
    Orchestrates workflow draft generation.

    Pipeline:
    1. LLM generates raw draft
    2. Draft is normalized
    3. Draft is validated
    4. On failure, retry once
    """

    def __init__(self, anthropic_client: Any):
        """
        Initialize the service.

        Args:
            anthropic_client: Anthropic client for LLM calls
        """
        self.planner = WorkflowPlanner(anthropic_client=anthropic_client)

    def draft_workflow(self, prompt: str) -> WorkflowPlannerResponse:
        """
        Generate a workflow draft from a user prompt.

        Will retry once if generation or validation fails.

        Args:
            prompt: User's natural language workflow description

        Returns:
            WorkflowPlannerResponse with draft or error
        """
        last_error = None

        for attempt in range(2):
            try:
                logger.info(f"Draft workflow attempt {attempt + 1}/2")

                # Step 1: Generate raw draft
                raw, generation_time_ms = self.planner.generate_raw_draft(prompt)

                # Step 2: Normalize
                draft = normalize_raw_draft(raw)

                # Step 3: Validate
                validate_workflow_draft(draft)

                # Success!
                logger.info(f"Successfully generated workflow: {draft.name}")
                return WorkflowPlannerResponse(
                    success=True,
                    draft=draft,
                    generation_time_ms=generation_time_ms,
                )

            except (WorkflowPlannerLLMError, WorkflowDraftValidationError, ValueError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

        # Both attempts failed
        error_msg = str(last_error) if last_error else "Unknown draft generation failure."
        logger.error(f"Workflow draft generation failed after 2 attempts: {error_msg}")

        return WorkflowPlannerResponse(
            success=False,
            error_code="draft_generation_failed",
            error_message=error_msg,
        )
