"""
Execution Fabric - Handoff Manager

Creates, validates, stores, and routes structured handoff packets.

A handoff packet is collaboration-centric (vs. node output which is artifact-centric).
It ensures coherent downstream work through explicit transfer of context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .models import NodeType, NodeStatus


logger = logging.getLogger(__name__)


# ============================================================================
# Handoff Models
# ============================================================================

class HandoffStatus(str, Enum):
    """Status of a handoff."""
    CREATED = "created"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


@dataclass
class HandoffPacket:
    """
    Structured handoff packet from one agent to another.

    Contains everything needed for the receiving agent to continue
    work coherently.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    mission_id: str = ""

    # Source information
    from_node_id: str = ""
    from_agent_type: str = ""
    completed_at: datetime = field(default_factory=datetime.now)

    # Objective
    objective_completed: str = ""
    objective_description: str = ""

    # Output summary
    output_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Quality assessment
    confidence_level: float = 0.0  # 0.0 to 1.0
    confidence_basis: str = ""  # Explanation of confidence

    # Unresolved items
    unresolved_questions: List[str] = field(default_factory=list)
    assumptions_made: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Risk flags
    known_risks: List[str] = field(default_factory=list)
    severity_indicators: List[str] = field(default_factory=list)

    # Artifacts
    artifacts_produced: List[Dict[str, Any]] = field(default_factory=list)
    workspace_entries: List[str] = field(default_factory=list)  # Entry IDs

    # Routing
    recommended_next_consumers: List[str] = field(default_factory=list)
    required_next_actions: List[str] = field(default_factory=list)

    # Metadata
    handoff_status: HandoffStatus = HandoffStatus.CREATED
    delivery_attempts: int = 0
    delivered_to: List[str] = field(default_factory=list)
    acknowledged_by: List[str] = field(default_factory=list)


@dataclass
class HandoffValidation:
    """Validation result for a handoff packet."""
    is_valid: bool
    missing_fields: List[str] = field(default_factory=list)
    quality_flags: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# Handoff Manager
# ============================================================================

class HandoffManager:
    """
    Manages structured handoffs between mission nodes.

    Responsibilities:
    - Create handoff packets from node outputs
    - Validate handoff completeness
    - Route handoffs to appropriate consumers
    - Track delivery and acknowledgment
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def create_handoff(
        self,
        mission_id: str,
        from_node_id: str,
        from_agent_type: str,
        node_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> HandoffPacket:
        """
        Create a handoff packet from node execution output.

        Transforms raw output into a structured handoff packet.
        """
        # Extract key information from node output
        objective_completed = context.get("node_title", "Task completed")

        # Build summary
        output_summary = node_output.get("summary", "")
        if not output_summary and node_output.get("content"):
            # Generate summary from content
            output_summary = self._generate_summary(node_output["content"])

        # Extract key findings
        key_findings = node_output.get("key_findings", [])

        # Generate recommendations if not provided
        recommendations = node_output.get("recommendations", [])
        if not recommendations and node_output.get("analysis"):
            recommendations = self._extract_recommendations(node_output.get("analysis", {}))

        # Assess confidence
        confidence_level = node_output.get("confidence_score", 0.5)
        confidence_basis = node_output.get("confidence_basis", "Agent assessment")

        # Identify unresolved items
        unresolved_questions = node_output.get("unresolved_questions", [])
        assumptions_made = node_output.get("assumptions", [])
        limitations = node_output.get("limitations", [])

        # Risk flags
        known_risks = node_output.get("risks", [])
        severity_indicators = node_output.get("severity_flags", [])

        # Artifacts
        artifacts = node_output.get("artifacts", [])

        # Determine recommended next consumers
        recommended_consumers = context.get("downstream_nodes", [])

        return HandoffPacket(
            mission_id=mission_id,
            from_node_id=from_node_id,
            from_agent_type=from_agent_type,
            objective_completed=objective_completed,
            objective_description=node_output.get("description", ""),
            output_summary=output_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            confidence_level=confidence_level,
            confidence_basis=confidence_basis,
            unresolved_questions=unresolved_questions,
            assumptions_made=assumptions_made,
            limitations=limitations,
            known_risks=known_risks,
            severity_indicators=severity_indicators,
            artifacts_produced=artifacts,
            recommended_next_consumers=recommended_consumers
        )

    async def validate_handoff(
        self,
        handoff: HandoffPacket
    ) -> HandoffValidation:
        """
        Validate a handoff packet for completeness.

        Checks that all required fields are present and reasonable.
        """
        errors = []
        warnings = []

        # Required fields
        if not handoff.objective_completed:
            errors.append("Missing objective_completed")

        if not handoff.output_summary:
            errors.append("Missing output_summary")

        if handoff.confidence_level < 0 or handoff.confidence_level > 1:
            errors.append("Invalid confidence_level")

        # Quality checks
        if handoff.confidence_level < 0.3:
            warnings.append("Low confidence - may require review")

        if handoff.known_risks and handoff.confidence_level > 0.7:
            warnings.append("High confidence but known risks present - contradictory")

        if not handoff.recommended_next_consumers:
            warnings.append("No recommended next consumers - may cause delays")

        # Check for critical items
        if handoff.severity_indicators:
            warnings.append(f"Severity indicators present: {handoff.severity_indicators}")

        return HandoffValidation(
            is_valid=len(errors) == 0,
            missing_fields=errors,
            quality_flags=warnings,
            recommendations=[]
        )

    async def deliver_handoff(
        self,
        handoff: HandoffPacket
    ) -> bool:
        """
        Deliver a handoff packet to its consumers.

        Routes the packet to recommended next consumers and tracks delivery.
        """
        validation = await self.validate_handoff(handoff)

        if not validation.is_valid:
            logger.warning(f"Handoff validation failed: {validation.missing_fields}")
            handoff.handoff_status = HandoffStatus.FAILED
            await self._persist_handoff(handoff)
            return False

        # Update status
        handoff.handoff_status = HandoffStatus.IN_TRANSIT
        handoff.delivery_attempts += 1

        # Persist
        await self._persist_handoff(handoff)

        # Deliver to consumers
        delivered = False
        for consumer_id in handoff.recommended_next_consumers:
            try:
                # This would notify the consumer agent
                # For now, track delivery
                handoff.delivered_to.append(consumer_id)
                delivered = True
            except Exception as e:
                logger.error(f"Error delivering handoff to {consumer_id}: {e}")

        if delivered:
            handoff.handoff_status = HandoffStatus.DELIVERED
        else:
            handoff.handoff_status = HandoffStatus.FAILED

        await self._persist_handoff(handoff)

        # Emit context bus event
        from .context_bus import ContextBusManager, MissionEventType
        bus = ContextBusManager.get_bus(handoff.mission_id)
        await bus.emit(MissionEvent(
            mission_id=handoff.mission_id,
            event_type=MissionEventType.ARTIFACT_PRODUCED,
            payload={"handoff_id": handoff.id},
            source_node_id=handoff.from_node_id
        ))

        return handoff.handoff_status == HandoffStatus.DELIVERED

    async def get_handoffs_for_node(
        self,
        node_id: str
    ) -> List[HandoffPacket]:
        """Get all handoffs from a specific node."""
        try:
            result = self.supabase.table("mission_handoffs").select("*").eq("from_node_id", node_id).execute()

            handoffs = []
            for h in result.data:
                handoffs.append(HandoffPacket(
                    id=h["id"],
                    mission_id=h["mission_id"],
                    from_node_id=h["from_node_id"],
                    from_agent_type=h["from_agent_type"],
                    completed_at=datetime.fromisoformat(h["created_at"]),
                    objective_completed=h["handoff_summary"]["objective_completed"],
                    output_summary=h["handoff_summary"]["output_summary"],
                    key_findings=h["handoff_summary"].get("key_findings", []),
                    recommendations=h["handoff_summary"].get("recommendations", []),
                    confidence_level=h["confidence"],
                    confidence_basis=h.get("confidence_basis", ""),
                    unresolved_questions=h.get("unresolved_questions", []),
                    assumptions_made=h.get("assumptions_made", []),
                    limitations=h.get("limitations", []),
                    known_risks=h.get("risks", []),
                    severity_indicators=h.get("severity_indicators", []),
                    artifacts_produced=h.get("artifacts", []),
                    recommended_next_consumers=h.get("recommended_consumers", []),
                    handoff_status=HandoffStatus(h.get("status", "created"))
                ))

            return handoffs

        except Exception as e:
            logger.error(f"Error getting handoffs for node {node_id}: {e}")
            return []

    async def get_pending_handoffs(
        self,
        workstream_id: str
    ) -> List[HandoffPacket]:
        """Get handoffs awaiting processing for a workstream."""
        try:
            # Find handoffs where this workstream is a recommended consumer
            result = self.supabase.table("mission_handoffs").select("*").contains("recommended_consumers", [workstream_id]).execute()

            handoffs = []
            for h in result.data:
                if h.get("status") in ["created", "in_transit"]:
                    handoffs.append(HandoffPacket(**h))

            return handoffs

        except Exception as e:
            logger.error(f"Error getting pending handoffs: {e}")
            return []

    # ========================================================================
    # Internal Methods
    # ========================================================================

    def _generate_summary(self, content: Any) -> str:
        """Generate a summary from content."""
        if isinstance(content, dict):
            return content.get("summary", content.get("title", str(content)))
        elif isinstance(content, str):
            # Truncate if too long
            return content[:500] + "..." if len(content) > 500 else content
        else:
            return str(content)

    def _extract_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis output."""
        recommendations = []

        if "recommendations" in analysis:
            return analysis["recommendations"]

        # Generate from other fields
        if "risks" in analysis:
            recommendations.extend([f"Review: {r}" for r in analysis["risks"][:3]])

        if "next_steps" in analysis:
            recommendations.extend(analysis["next_steps"][:3])

        return recommendations

    async def _persist_handoff(self, handoff: HandoffPacket):
        """Persist handoff to database."""
        try:
            self.supabase.table("mission_handoffs").insert({
                "id": handoff.id,
                "mission_id": handoff.mission_id,
                "from_node_id": handoff.from_node_id,
                "to_node_id": None,  # Will be set when consumed
                "from_agent_type": handoff.from_agent_type,
                "to_agent_type": None,  # Will be set when consumed
                "handoff_summary": {
                    "objective_completed": handoff.objective_completed,
                    "output_summary": handoff.output_summary,
                    "key_findings": handoff.key_findings,
                    "recommendations": handoff.recommendations
                },
                "confidence": handoff.confidence_level,
                "unresolved_questions": handoff.unresolved_questions,
                "risks": handoff.known_risks,
                "artifacts": handoff.artifacts_produced,
                "status": handoff.handoff_status.value,
                "created_at": handoff.completed_at.isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error persisting handoff: {e}")


# ============================================================================
# Quick Start Functions
# ============================================================================

async def create_and_deliver_handoff(
    mission_id: str,
    from_node_id: str,
    from_agent_type: str,
    node_output: Dict[str, Any],
    context: Dict[str, Any],
    supabase_client
) -> str:
    """
    Quick helper: Create and deliver a handoff packet.

    Returns handoff ID.
    """
    manager = HandoffManager(supabase_client)

    handoff = await manager.create_handoff(
        mission_id=mission_id,
        from_node_id=from_node_id,
        from_agent_type=from_agent_type,
        node_output=node_output,
        context=context
    )

    success = await manager.deliver_handoff(handoff)

    if success:
        return handoff.id
    else:
        raise ValueError("Handoff delivery failed")
