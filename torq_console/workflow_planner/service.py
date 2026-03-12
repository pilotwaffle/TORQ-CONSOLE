"""
Workflow planner service - Orchestrates the planning pipeline.

Planner → Normalize → Validate → (retry once on failure) → Write Reasoning
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .graph_drafter import normalize_raw_draft
from .models import WorkflowPlannerRequest, WorkflowPlannerResponse
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
    5. Write reasoning entries to workspace (if configured)
    """

    def __init__(self, anthropic_client: Any, workspace_service: Optional[Any] = None):
        """
        Initialize the service.

        Args:
            anthropic_client: Anthropic client for LLM calls
            workspace_service: Optional WorkspaceService for reasoning entries
        """
        self.planner = WorkflowPlanner(anthropic_client=anthropic_client)
        self.workspace_service = workspace_service

    async def draft_workflow(
        self,
        request: WorkflowPlannerRequest,
    ) -> WorkflowPlannerResponse:
        """
        Generate a workflow draft from a user prompt.

        Will retry once if generation or validation fails.
        Will write reasoning entries to workspace if configured.

        Args:
            request: Workflow planner request with prompt and optional workspace_id

        Returns:
            WorkflowPlannerResponse with draft or error
        """
        last_error = None

        for attempt in range(2):
            try:
                logger.info(f"Draft workflow attempt {attempt + 1}/2")

                # Step 1: Generate raw draft
                raw, generation_time_ms = self.planner.generate_raw_draft(request.prompt)

                # Step 2: Normalize
                draft = normalize_raw_draft(raw)

                # Step 3: Validate
                validate_workflow_draft(draft)

                # Success!
                logger.info(f"Successfully generated workflow: {draft.name}")

                response = WorkflowPlannerResponse(
                    success=True,
                    draft=draft,
                    generation_time_ms=generation_time_ms,
                )

                # Step 4: Write reasoning entries to workspace (async)
                if request.write_reasoning and self.workspace_service:
                    await self._write_planning_reasoning(request, draft, response)

                return response

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

    async def _write_planning_reasoning(
        self,
        request: WorkflowPlannerRequest,
        draft: Any,
        response: WorkflowPlannerResponse,
    ) -> None:
        """
        Write reasoning entries to the workspace after planning.

        Creates structured entries that explain:
        - What the user requested
        - What agents were selected and why
        - Any questions or decisions made during planning

        Args:
            request: Original planner request
            draft: Generated workflow draft
            response: Planner response
        """
        from torq_console.workspace.models import (
            WorkspaceEntryCreate,
            WorkspaceEntryType,
        )

        # Use workspace_id if provided, otherwise use session_id to lookup/create session workspace
        workspace_id = request.workspace_id

        if not workspace_id and self.workspace_service:
            # Try to get or create a session workspace
            try:
                if request.session_id:
                    workspace = await self.workspace_service.get_or_create_workspace(
                        scope_type="session",
                        scope_id=request.session_id,
                        title=f"Session: {request.session_id[:8]}",
                        description="Planning session workspace",
                    )
                    workspace_id = str(workspace.workspace_id)
            except Exception as e:
                logger.warning(f"Failed to get/create session workspace: {e}")

        if not workspace_id:
            logger.debug("No workspace available for planning reasoning")
            return

        try:
            # Entry 1: User request (Fact)
            self.workspace_service.add_entry(
                workspace_id=workspace_id,
                entry=WorkspaceEntryCreate(
                    entry_type=WorkspaceEntryType.FACT,
                    content={
                        "category": "user_request",
                        "prompt": request.prompt,
                        "session_id": request.session_id,
                    },
                    source_agent="workflow_planner",
                    confidence=1.0,
                ),
            )

            # Entry 2: Agent sequence decision (Decision)
            agent_sequence = " → ".join([node.agent_id for node in draft.nodes])
            self.workspace_service.add_entry(
                workspace_id=workspace_id,
                entry=WorkspaceEntryCreate(
                    entry_type=WorkspaceEntryType.DECISION,
                    content={
                        "category": "agent_selection",
                        "selected_sequence": agent_sequence,
                        "node_count": len(draft.nodes),
                        "rationale": draft.rationale or "No explicit rationale provided",
                    },
                    source_agent="workflow_planner",
                    confidence=0.9,
                ),
            )

            # Entry 3: Generated workflow artifact (Artifact)
            self.workspace_service.add_entry(
                workspace_id=workspace_id,
                entry=WorkspaceEntryCreate(
                    entry_type=WorkspaceEntryType.ARTIFACT,
                    content={
                        "category": "workflow_draft",
                        "workflow_name": draft.name,
                        "workflow_description": draft.description,
                        "nodes": [
                            {
                                "name": node.name,
                                "agent_id": node.agent_id,
                                "depends_on": node.depends_on,
                            }
                            for node in draft.nodes
                        ],
                    },
                    source_agent="workflow_planner",
                    confidence=0.95,
                ),
            )

            logger.info(
                f"Wrote planning reasoning to workspace {workspace_id}: "
                f"{len(draft.nodes)} nodes, sequence '{agent_sequence}'"
            )

        except Exception as e:
            # Non-blocking - don't fail planning if reasoning write fails
            logger.warning(f"Failed to write planning reasoning to workspace: {e}")
