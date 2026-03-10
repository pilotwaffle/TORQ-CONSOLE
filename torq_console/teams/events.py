"""
Agent Teams - Event Streaming

Phase 5.2B: Observability + UI

This module provides SSE event streaming for real-time team execution observability.
DOES NOT modify runtime behavior - only exposes events for UI consumption.
"""

from __future__ import annotations

import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse

from .models import TeamExecutionStatus, TeamRole, MessageType, ValidatorStatus
from .persistence import TeamPersistence
from .orchestrator import AgentTeamOrchestrator


logger = logging.getLogger(__name__)


# ============================================================================
# Team Event Types (Read-Only)
# ============================================================================

class TeamEventType:
    """Team execution event types for observability."""

    TEAM_EXECUTION_STARTED = "team_execution_started"
    TEAM_EXECUTION_COMPLETED = "team_execution_completed"
    TEAM_EXECUTION_FAILED = "team_execution_failed"
    TEAM_ROUND_STARTED = "team_round_started"
    TEAM_ROUND_COMPLETED = "team_round_completed"
    ROLE_EXECUTED = "role_executed"
    CRITIQUE_SUBMITTED = "critique_submitted"
    VALIDATOR_DECISION = "validator_decision"
    TEAM_DECISION_FINALIZED = "team_decision_finalized"


# ============================================================================
# Team Event Emitter (Read-Only Interface)
# ============================================================================

class TeamEventEmitter:
    """
    Emits team execution events for SSE streaming.

    This is a READ-ONLY interface - it does not modify runtime behavior.
    Events are derived from persisted data and in-memory execution state.
    """

    def __init__(self, persistence: TeamPersistence):
        """
        Initialize event emitter.

        Args:
            persistence: Team persistence layer for reading events
        """
        self.persistence = persistence
        # Track active executions for real-time events
        self._active_executions: Dict[UUID, Dict[str, Any]] = {}

    def register_execution(self, execution_id: UUID, context: Dict[str, Any]):
        """
        Register an execution for real-time event tracking.

        Args:
            execution_id: Execution identifier
            context: Execution context (team_id, objective, etc.)
        """
        self._active_executions[execution_id] = {
            "registered_at": datetime.now(timezone.utc),
            "context": context,
        }
        logger.debug(f"Registered execution {execution_id} for event tracking")

    def unregister_execution(self, execution_id: UUID):
        """
        Unregister an execution from event tracking.

        Args:
            execution_id: Execution identifier
        """
        self._active_executions.pop(execution_id, None)
        logger.debug(f"Unregistered execution {execution_id}")

    async def stream_execution_events(
        self,
        execution_id: UUID,
        since: Optional[datetime] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream events for a team execution.

        This is a READ-ONLY operation - it queries persisted data
        and yields events in chronological order.

        Args:
            execution_id: Execution identifier
            since: Only yield events after this timestamp

        Yields:
            Event dictionaries with type, data, and timestamp
        """
        # Get execution record
        execution = await self.persistence.get_execution(execution_id)
        if not execution:
            yield {
                "type": "error",
                "data": {"message": f"Execution {execution_id} not found"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return

        # Yield execution started event
        if execution.started_at:
            yield {
                "type": TeamEventType.TEAM_EXECUTION_STARTED,
                "data": {
                    "execution_id": str(execution_id),
                    "team_id": str(execution.team_id),
                    "workspace_id": execution.workspace_id,
                    "objective": execution.objective,
                    "max_rounds": execution.max_rounds,
                },
                "timestamp": execution.started_at.isoformat(),
            }

        # Get all messages for this execution
        messages = await self.persistence.get_messages(execution_id)

        # Group by round for round events
        rounds: Dict[int, list] = {}
        for msg in messages:
            if since and msg.created_at and msg.created_at <= since:
                continue
            round_num = msg.round_number
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(msg)

        # Yield events in chronological order
        for round_num in sorted(rounds.keys()):
            round_messages = rounds[round_num]

            # Round started event (first message in round)
            if round_messages:
                yield {
                    "type": TeamEventType.TEAM_ROUND_STARTED,
                    "data": {
                        "execution_id": str(execution_id),
                        "round_number": round_num,
                    },
                    "timestamp": round_messages[0].created_at.isoformat() if round_messages[0].created_at else datetime.now(timezone.utc).isoformat(),
                }

            # Role executed events
            for msg in round_messages:
                if msg.message_type == MessageType.ROLE_TO_ROLE:
                    yield {
                        "type": TeamEventType.ROLE_EXECUTED,
                        "data": {
                            "execution_id": str(execution_id),
                            "round_number": msg.round_number,
                            "sender_role": msg.sender_role.value,
                            "receiver_role": msg.receiver_role.value,
                            "confidence": msg.confidence,
                            "text_content": msg.text_content[:200] if msg.text_content else "",  # Truncate for UI
                        },
                        "timestamp": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
                    }

                    # Check for critique
                    if msg.sender_role == TeamRole.CRITIC:
                        yield {
                            "type": TeamEventType.CRITIQUE_SUBMITTED,
                            "data": {
                                "execution_id": str(execution_id),
                                "round_number": msg.round_number,
                                "content_summary": msg.text_content[:100] if msg.text_content else "",
                            },
                            "timestamp": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
                        }

                elif msg.message_type == MessageType.VALIDATION_PASS:
                    yield {
                        "type": TeamEventType.VALIDATOR_DECISION,
                        "data": {
                            "execution_id": str(execution_id),
                            "round_number": msg.round_number,
                            "decision": "passed",
                            "notes": msg.content.get("notes", "") if msg.content else "",
                        },
                        "timestamp": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
                    }

                elif msg.message_type == MessageType.VALIDATION_BLOCK:
                    yield {
                        "type": TeamEventType.VALIDATOR_DECISION,
                        "data": {
                            "execution_id": str(execution_id),
                            "round_number": msg.round_number,
                            "decision": "blocked",
                            "issues": msg.content.get("issues", []) if msg.content else [],
                        },
                        "timestamp": msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
                    }

            # Round completed event
            yield {
                "type": TeamEventType.TEAM_ROUND_COMPLETED,
                "data": {
                    "execution_id": str(execution_id),
                    "round_number": round_num,
                    "message_count": len(round_messages),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Get decision for finalization event
        decision = await self.persistence.get_decision(execution_id)
        if decision:
            yield {
                "type": TeamEventType.TEAM_DECISION_FINALIZED,
                "data": {
                    "execution_id": str(execution_id),
                    "decision_policy": decision.decision_policy,
                    "validator_status": decision.validator_status.value,
                    "confidence_score": decision.confidence_score,
                    "revision_count": decision.revision_count,
                    "escalation_count": decision.escalation_count,
                    "has_dissent": decision.dissent_summary.get("has_dissent", False) if decision.dissent_summary else False,
                },
                "timestamp": decision.created_at.isoformat() if decision.created_at else datetime.now(timezone.utc).isoformat(),
            }

        # Final status event
        if execution.status == TeamExecutionStatus.COMPLETED:
            yield {
                "type": TeamEventType.TEAM_EXECUTION_COMPLETED,
                "data": {
                    "execution_id": str(execution_id),
                    "final_confidence": execution.final_confidence,
                    "rounds_completed": execution.current_round,
                },
                "timestamp": execution.completed_at.isoformat() if execution.completed_at else datetime.now(timezone.utc).isoformat(),
            }
        elif execution.status == TeamExecutionStatus.FAILED:
            yield {
                "type": TeamEventType.TEAM_EXECUTION_FAILED,
                "data": {
                    "execution_id": str(execution_id),
                },
                "timestamp": execution.completed_at.isoformat() if execution.completed_at else datetime.now(timezone.utc).isoformat(),
            }


# ============================================================================
# SSE Streaming Endpoint
# ============================================================================

async def stream_team_execution_events(
    execution_id: UUID,
    persistence: TeamPersistence,
) -> StreamingResponse:
    """
    Create SSE stream for team execution events.

    This is a READ-ONLY endpoint - queries persisted data and streams events.

    Args:
        execution_id: Team execution identifier
        persistence: Team persistence layer

    Returns:
        StreamingResponse with text/event-stream media type
    """
    emitter = TeamEventEmitter(persistence)

    async def event_generator():
        """Generate SSE events for team execution."""
        try:
            # Query existing events
            last_timestamp = None

            while True:
                # Stream events from persistence
                async for event in emitter.stream_execution_events(execution_id, last_timestamp):
                    # Format as SSE
                    event_json = json.dumps(event)
                    yield f"data: {event_json}\n\n"

                    # Update timestamp for next poll
                    if event.get("timestamp"):
                        try:
                            last_timestamp = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                        except:
                            pass

                # Check if execution is complete
                execution = await persistence.get_execution(execution_id)
                if execution and execution.status in (TeamExecutionStatus.COMPLETED, TeamExecutionStatus.FAILED):
                    # Send completion event and close
                    yield f"event: complete\ndata: {{\"execution_id\": \"{str(execution_id)}\"}}\n\n"
                    break

                # Wait before polling again (for live executions)
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info(f"SSE client disconnected for execution {execution_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream for execution {execution_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
