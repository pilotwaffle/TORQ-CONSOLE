"""
FastAPI router for Workflow Planning Copilot.

Provides POST /api/workflow-planner/draft endpoint.
Integrates with Shared Cognitive Workspace for reasoning entries.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from .models import WorkflowPlannerRequest, WorkflowPlannerResponse
from .service import WorkflowPlannerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow-planner", tags=["workflow-planner"])

# Optional workspace service for reasoning entries
_workspace_service: Optional[Any] = None


def set_workspace_service(workspace_service: Any) -> None:
    """Set the shared workspace service globally."""
    global _workspace_service
    _workspace_service = workspace_service


def get_anthropic_client() -> Any:
    """
    Get or create the Anthropic client.

    In production, this should use a shared client from the app state.
    For now, we create a simple client.

    TODO: Integrate with proper dependency injection.
    """
    try:
        from anthropic import Anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - workflow planner will fail")
            raise HTTPException(
                status_code=503,
                detail="Anthropic API key not configured"
            )

        return Anthropic(api_key=api_key)

    except ImportError:
        logger.error("anthropic package not installed")
        raise HTTPException(
            status_code=500,
            detail="Anthropic client not available"
        )


def get_workflow_planner_service() -> WorkflowPlannerService:
    """
    Get the workflow planner service instance.

    Creates a new service with an Anthropic client and optional workspace service.
    """
    client = get_anthropic_client()
    return WorkflowPlannerService(
        anthropic_client=client,
        workspace_service=_workspace_service,
    )


@router.post("/draft", response_model=WorkflowPlannerResponse)
async def generate_workflow_draft(
    request: WorkflowPlannerRequest,
    service: WorkflowPlannerService = Depends(get_workflow_planner_service),
) -> WorkflowPlannerResponse:
    """
    Generate a workflow draft from a natural language prompt.

    Example:
    ```
    POST /api/workflow-planner/draft
    {
      "prompt": "Research the AI market and create a strategic summary",
      "session_id": "optional-session-id",
      "write_reasoning": true
    }
    ```

    The response includes:
    - A valid workflow draft with nodes and edges
    - A rationale explaining the design choices
    - Generation time in milliseconds

    If session_id or workspace_id is provided and write_reasoning is true, the planner will write:
    - Fact: User's original request
    - Decision: Selected agent sequence with rationale
    - Artifact: Generated workflow structure

    The draft is NOT saved automatically - the user must review and save it.

    Raises:
        503: If Anthropic API key is not configured
        500: If generation fails after retries
    """
    logger.info(f"Generating workflow draft for prompt: {request.prompt[:100]}...")

    try:
        response = await service.draft_workflow(request)

        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=response.error_message or "Workflow draft generation failed"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in workflow draft generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check for the workflow planner module."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    return {
        "status": "healthy" if api_key else "degraded",
        "module": "workflow_planner",
        "anthropic_configured": "true" if api_key else "false",
    }
