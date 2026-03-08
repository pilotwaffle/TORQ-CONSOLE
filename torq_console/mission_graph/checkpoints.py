"""
Execution Fabric - Checkpoint Manager

Persists recoverable mission snapshots for rollback and recovery.

Checkpoints capture:
- Complete graph state (nodes, edges, status)
- All node outputs and artifacts
- Workstream states
- Handoffs in progress
- Active blockers and risks
- Context bus events since last checkpoint
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


logger = logging.getLogger(__name__)


# ============================================================================
# Checkpoint Models
# ============================================================================

class CheckpointType(str, Enum):
    """Types of checkpoints."""
    AUTOMATIC = "automatic"  # Periodic automatic snapshots
    MANUAL = "manual"  # User-initiated checkpoints
    PRE_PHASE = "pre_phase"  # Before major phase transitions
    POST_PHASE = "post_phase"  # After major phase transitions
    CRITICAL = "critical"  # Before risky operations
    RECOVERY = "recovery"  # During recovery procedures


class CheckpointStatus(str, Enum):
    """Status of a checkpoint."""
    CREATING = "creating"
    READY = "ready"
    CORRUPTED = "corrupted"
    EXPIRED = "expired"
    DELETING = "deleting"


@dataclass
class CheckpointMetadata:
    """Metadata about a checkpoint."""
    checkpoint_id: str = ""
    mission_id: str = ""
    graph_id: str = ""

    # Type and status
    checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC
    status: CheckpointStatus = CheckpointStatus.CREATING

    # Content summary
    node_count: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    workstream_count: int = 0
    artifact_count: int = 0
    handoff_count: int = 0

    # Size tracking
    estimated_size_bytes: int = 0

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Creator
    created_by: str = "system"  # agent_type or "human"

    # Description
    description: str = ""
    tags: List[str] = field(default_factory=list)

    # Statistics
    mission_duration_seconds: float = 0.0
    average_confidence: float = 0.0
    open_blockers: int = 0
    open_risks: int = 0


@dataclass
class CheckpointData:
    """Complete checkpoint data for recovery."""
    metadata: CheckpointMetadata

    # Graph state
    graph_state: Dict[str, Any] = field(default_factory=dict)

    # Node states
    node_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Node outputs
    node_outputs: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # Workstream states
    workstream_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Active handoffs
    active_handoffs: List[Dict[str, Any]] = field(default_factory=list)

    # Blockers and risks
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)

    # Context bus events (since last checkpoint)
    events: List[Dict[str, Any]] = field(default_factory=list)

    # Decision outcomes
    decision_outcomes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RestoreResult:
    """Result of a checkpoint restore operation."""
    success: bool
    checkpoint_id: str = ""
    restored_nodes: int = 0
    restored_workstreams: int = 0
    restored_handoffs: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# Checkpoint Manager
# ============================================================================

class CheckpointManager:
    """
    Manages mission checkpoints for rollback and recovery.

    Responsibilities:
    - Create periodic and manual checkpoints
    - Restore mission state from checkpoints
    - Manage checkpoint retention and expiration
    - Verify checkpoint integrity
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

        # Configuration
        self.retention_days = 30
        self.max_checkpoints_per_mission = 50
        self.automatic_checkpoint_interval_minutes = 15

    async def create_checkpoint(
        self,
        mission_id: str,
        graph_state: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
        description: str = "",
        created_by: str = "system",
        tags: Optional[List[str]] = None
    ) -> CheckpointData:
        """
        Create a checkpoint of the current mission state.

        Captures graph, nodes, workstreams, handoffs, and events.
        """
        checkpoint_id = str(uuid4())
        graph_id = graph_state.get("id", "")

        logger.info(f"Creating checkpoint {checkpoint_id} for mission {mission_id}")

        # Build checkpoint data
        data = await self._build_checkpoint_data(
            checkpoint_id,
            mission_id,
            graph_id,
            graph_state
        )

        # Set metadata
        data.metadata.checkpoint_id = checkpoint_id
        data.metadata.mission_id = mission_id
        data.metadata.graph_id = graph_id
        data.metadata.checkpoint_type = checkpoint_type
        data.metadata.created_by = created_by
        data.metadata.description = description
        data.metadata.tags = tags or []

        # Calculate size
        data.metadata.estimated_size_bytes = self._estimate_size(data)

        # Persist checkpoint
        await self._persist_checkpoint(data)

        # Update status to ready
        data.metadata.status = CheckpointStatus.READY
        await self._update_checkpoint_status(checkpoint_id, CheckpointStatus.READY)

        # Clean up old checkpoints if needed
        await self._cleanup_old_checkpoints(mission_id)

        logger.info(f"Checkpoint {checkpoint_id} created successfully")

        return data

    async def restore_checkpoint(
        self,
        checkpoint_id: str,
        target_mission_id: Optional[str] = None
    ) -> RestoreResult:
        """
        Restore a mission from a checkpoint.

        If target_mission_id is provided, restores to that mission (for recovery).
        Otherwise, restores to the original mission (rollback).
        """
        # Load checkpoint
        data = await self._load_checkpoint(checkpoint_id)

        if not data:
            return RestoreResult(
                success=False,
                errors=[f"Checkpoint {checkpoint_id} not found or corrupted"]
            )

        logger.info(f"Restoring from checkpoint {checkpoint_id}")

        result = RestoreResult(
            success=True,
            checkpoint_id=checkpoint_id
        )

        target_mission = target_mission_id or data.metadata.mission_id

        try:
            # Restore node states
            for node_id, node_state in data.node_states.items():
                await self._restore_node_state(target_mission, node_id, node_state)
                result.restored_nodes += 1

            # Restore workstream states
            for ws_id, ws_state in data.workstream_states.items():
                await self._restore_workstream_state(target_mission, ws_id, ws_state)
                result.restored_workstreams += 1

            # Restore handoffs
            for handoff in data.active_handoffs:
                await self._restore_handoff(target_mission, handoff)
                result.restored_handoffs += 1

            # Log restore event
            await self._log_restore_event(checkpoint_id, target_mission, result)

            logger.info(f"Checkpoint restore complete: {result.restored_nodes} nodes, {result.restored_workstreams} workstreams")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Error restoring checkpoint: {e}")

        return result

    async def list_checkpoints(
        self,
        mission_id: str,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: int = 50
    ) -> List[CheckpointMetadata]:
        """List checkpoints for a mission."""
        try:
            query = self.supabase.table("mission_checkpoints").select("*").eq(
                "mission_id", mission_id
            )

            if checkpoint_type:
                query = query.eq("checkpoint_type", checkpoint_type.value)

            result = query.order("created_at", desc=True).limit(limit).execute()

            checkpoints = []
            for record in result.data:
                checkpoints.append(CheckpointMetadata(
                    checkpoint_id=record["id"],
                    mission_id=record["mission_id"],
                    graph_id=record["graph_id"],
                    checkpoint_type=CheckpointType(record["checkpoint_type"]),
                    status=CheckpointStatus(record["status"]),
                    node_count=record.get("node_count", 0),
                    completed_nodes=record.get("completed_nodes", 0),
                    failed_nodes=record.get("failed_nodes", 0),
                    workstream_count=record.get("workstream_count", 0),
                    artifact_count=record.get("artifact_count", 0),
                    handoff_count=record.get("handoff_count", 0),
                    estimated_size_bytes=record.get("estimated_size_bytes", 0),
                    created_at=datetime.fromisoformat(record["created_at"]),
                    expires_at=datetime.fromisoformat(record["expires_at"]) if record.get("expires_at") else None,
                    created_by=record.get("created_by", "system"),
                    description=record.get("description", ""),
                    tags=record.get("tags", []),
                    mission_duration_seconds=record.get("mission_duration_seconds", 0.0),
                    average_confidence=record.get("average_confidence", 0.0),
                    open_blockers=record.get("open_blockers", 0),
                    open_risks=record.get("open_risks", 0)
                ))

            return checkpoints

        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return []

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        try:
            self.supabase.table("mission_checkpoints").delete().eq(
                "id", checkpoint_id
            ).execute()

            # Delete associated data
            self.supabase.table("checkpoint_data").delete().eq(
                "checkpoint_id", checkpoint_id
            ).execute()

            logger.info(f"Deleted checkpoint {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting checkpoint: {e}")
            return False

    async def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify checkpoint integrity."""
        try:
            # Load checkpoint
            data = await self._load_checkpoint(checkpoint_id)

            if not data:
                return False

            # Basic validation
            if not data.metadata.mission_id:
                return False

            if data.metadata.node_count != len(data.node_states):
                logger.warning(f"Checkpoint {checkpoint_id}: node count mismatch")
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying checkpoint: {e}")
            return False

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _build_checkpoint_data(
        self,
        checkpoint_id: str,
        mission_id: str,
        graph_id: str,
        graph_state: Dict[str, Any]
    ) -> CheckpointData:
        """Build complete checkpoint data from current mission state."""
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            mission_id=mission_id,
            graph_id=graph_id
        )

        data = CheckpointData(metadata=metadata)

        # Get graph state
        data.graph_state = graph_state

        # Get node states
        nodes_result = self.supabase.table("mission_nodes").select("*").eq(
            "mission_id", mission_id
        ).execute()

        for node in nodes_result.data:
            data.node_states[node["id"]] = node
            metadata.node_count += 1

            if node["status"] == "completed":
                metadata.completed_nodes += 1
            elif node["status"] == "failed":
                metadata.failed_nodes += 1

        # Get node outputs
        outputs_result = self.supabase.table("mission_node_outputs").select("*").eq(
            "mission_id", mission_id
        ).execute()

        for output in outputs_result.data:
            node_id = output["node_id"]
            if node_id not in data.node_outputs:
                data.node_outputs[node_id] = []
            data.node_outputs[node_id].append(output)

        # Get workstream states
        ws_result = self.supabase.table("workstream_states").select("*").eq(
            "mission_id", mission_id
        ).execute()

        for ws in ws_result.data:
            data.workstream_states[ws["workstream_id"]] = ws
            metadata.workstream_count += 1

        # Get active handoffs
        handoffs_result = self.supabase.table("mission_handoffs").select("*").eq(
            "mission_id", mission_id
        ).in_("status", ["created", "in_transit"]).execute()

        data.active_handoffs = handoffs_result.data
        metadata.handoff_count = len(data.active_handoffs)

        # Get blockers from workstream states
        for ws_state in data.workstream_states.values():
            for blocker in ws_state.get("blockers", []):
                if blocker.get("resolved_at") is None:
                    data.blockers.append({
                        "workstream_id": ws_state["workstream_id"],
                        **blocker
                    })

        metadata.open_blockers = len(data.blockers)

        # Get recent events
        events_result = self.supabase.table("mission_events").select("*").eq(
            "mission_id", mission_id
        ).order("created_at", desc=True).limit(100).execute()

        data.events = events_result.data

        # Get decision outcomes
        decisions_result = self.supabase.table("decision_outcomes").select("*").eq(
            "mission_id", mission_id
        ).execute()

        data.decision_outcomes = decisions_result.data

        # Calculate statistics
        await self._calculate_statistics(data)

        return data

    async def _calculate_statistics(self, data: CheckpointData):
        """Calculate checkpoint statistics."""
        metadata = data.metadata

        # Calculate average confidence
        confidences = []
        for node_state in data.node_states.values():
            if "confidence_score" in node_state:
                confidences.append(node_state["confidence_score"])

        if confidences:
            metadata.average_confidence = sum(confidences) / len(confidences)

        # Count risks
        for ws_state in data.workstream_states.values():
            risks = ws_state.get("known_risks", [])
            metadata.open_risks += len(risks)

        # Calculate mission duration
        if metadata.completed_nodes > 0:
            mission_result = self.supabase.table("missions").select("created_at").eq(
                "id", metadata.mission_id
            ).execute()

            if mission_result.data:
                started = datetime.fromisoformat(mission_result.data[0]["created_at"])
                metadata.mission_duration_seconds = (datetime.now() - started).total_seconds()

    def _estimate_size(self, data: CheckpointData) -> int:
        """Estimate checkpoint size in bytes."""
        # Rough JSON serialization size
        try:
            serialized = json.dumps({
                "graph_state": data.graph_state,
                "node_states": data.node_states,
                "node_outputs": data.node_outputs,
                "workstream_states": data.workstream_states,
                "active_handoffs": data.active_handoffs,
                "blockers": data.blockers,
                "events": data.events,
                "decision_outcomes": data.decision_outcomes
            }, default=str)
            return len(serialized.encode('utf-8'))
        except Exception:
            return 0

    async def _persist_checkpoint(self, data: CheckpointData):
        """Persist checkpoint to database."""
        try:
            # Insert metadata
            self.supabase.table("mission_checkpoints").insert({
                "id": data.metadata.checkpoint_id,
                "mission_id": data.metadata.mission_id,
                "graph_id": data.metadata.graph_id,
                "checkpoint_type": data.metadata.checkpoint_type.value,
                "status": data.metadata.status.value,
                "node_count": data.metadata.node_count,
                "completed_nodes": data.metadata.completed_nodes,
                "failed_nodes": data.metadata.failed_nodes,
                "workstream_count": data.metadata.workstream_count,
                "artifact_count": data.metadata.artifact_count,
                "handoff_count": data.metadata.handoff_count,
                "estimated_size_bytes": data.metadata.estimated_size_bytes,
                "created_by": data.metadata.created_by,
                "description": data.metadata.description,
                "tags": data.metadata.tags,
                "mission_duration_seconds": data.metadata.mission_duration_seconds,
                "average_confidence": data.metadata.average_confidence,
                "open_blockers": data.metadata.open_blockers,
                "open_risks": data.metadata.open_risks,
                "expires_at": (datetime.now() + __import__('datetime').timedelta(days=self.retention_days)).isoformat()
            }).execute()

            # Insert data (compressed as JSONB)
            self.supabase.table("checkpoint_data").insert({
                "checkpoint_id": data.metadata.checkpoint_id,
                "graph_state": data.graph_state,
                "node_states": data.node_states,
                "node_outputs": data.node_outputs,
                "workstream_states": data.workstream_states,
                "active_handoffs": data.active_handoffs,
                "blockers": data.blockers,
                "risks": data.risks,
                "events": data.events,
                "decision_outcomes": data.decision_outcomes
            }).execute()

        except Exception as e:
            logger.error(f"Error persisting checkpoint: {e}")
            raise

    async def _update_checkpoint_status(
        self,
        checkpoint_id: str,
        status: CheckpointStatus
    ):
        """Update checkpoint status."""
        try:
            self.supabase.table("mission_checkpoints").update({
                "status": status.value
            }).eq("id", checkpoint_id).execute()

        except Exception as e:
            logger.error(f"Error updating checkpoint status: {e}")

    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """Load checkpoint from database."""
        try:
            # Get metadata
            metadata_result = self.supabase.table("mission_checkpoints").select("*").eq(
                "id", checkpoint_id
            ).execute()

            if not metadata_result.data:
                return None

            metadata_record = metadata_result.data[0]

            # Get data
            data_result = self.supabase.table("checkpoint_data").select("*").eq(
                "checkpoint_id", checkpoint_id
            ).execute()

            if not data_result.data:
                return None

            data_record = data_result.data[0]

            # Build metadata
            metadata = CheckpointMetadata(
                checkpoint_id=metadata_record["id"],
                mission_id=metadata_record["mission_id"],
                graph_id=metadata_record["graph_id"],
                checkpoint_type=CheckpointType(metadata_record["checkpoint_type"]),
                status=CheckpointStatus(metadata_record["status"]),
                node_count=metadata_record.get("node_count", 0),
                completed_nodes=metadata_record.get("completed_nodes", 0),
                failed_nodes=metadata_record.get("failed_nodes", 0),
                workstream_count=metadata_record.get("workstream_count", 0),
                artifact_count=metadata_record.get("artifact_count", 0),
                handoff_count=metadata_record.get("handoff_count", 0),
                estimated_size_bytes=metadata_record.get("estimated_size_bytes", 0),
                created_at=datetime.fromisoformat(metadata_record["created_at"]),
                expires_at=datetime.fromisoformat(metadata_record["expires_at"]) if metadata_record.get("expires_at") else None,
                created_by=metadata_record.get("created_by", "system"),
                description=metadata_record.get("description", ""),
                tags=metadata_record.get("tags", []),
                mission_duration_seconds=metadata_record.get("mission_duration_seconds", 0.0),
                average_confidence=metadata_record.get("average_confidence", 0.0),
                open_blockers=metadata_record.get("open_blockers", 0),
                open_risks=metadata_record.get("open_risks", 0)
            )

            # Build data
            return CheckpointData(
                metadata=metadata,
                graph_state=data_record.get("graph_state", {}),
                node_states=data_record.get("node_states", {}),
                node_outputs=data_record.get("node_outputs", {}),
                workstream_states=data_record.get("workstream_states", {}),
                active_handoffs=data_record.get("active_handoffs", []),
                blockers=data_record.get("blockers", []),
                risks=data_record.get("risks", []),
                events=data_record.get("events", []),
                decision_outcomes=data_record.get("decision_outcomes", [])
            )

        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return None

    async def _restore_node_state(
        self,
        mission_id: str,
        node_id: str,
        node_state: Dict[str, Any]
    ):
        """Restore a single node's state."""
        # Update node status and other fields
        update_data = {
            k: v for k, v in node_state.items()
            if k in ["status", "priority", "error_message", "output_count"]
        }

        if update_data:
            self.supabase.table("mission_nodes").update(update_data).eq(
                "mission_id", mission_id
            ).eq("id", node_id).execute()

    async def _restore_workstream_state(
        self,
        mission_id: str,
        workstream_id: str,
        ws_state: Dict[str, Any]
    ):
        """Restore a single workstream's state."""
        # Update workstream state
        update_data = {
            k: v for k, v in ws_state.items()
            if k in [
                "phase", "health", "status", "progress_percent",
                "confidence_score", "quality_score", "contradiction_count"
            ]
        }

        if update_data:
            self.supabase.table("workstream_states").update(update_data).eq(
                "mission_id", mission_id
            ).eq("workstream_id", workstream_id).execute()

    async def _restore_handoff(
        self,
        mission_id: str,
        handoff: Dict[str, Any]
    ):
        """Restore a single handoff."""
        # Re-insert handoff if not exists
        self.supabase.table("mission_handoffs").insert({
            **handoff,
            "mission_id": mission_id
        }).execute()

    async def _log_restore_event(
        self,
        checkpoint_id: str,
        target_mission_id: str,
        result: RestoreResult
    ):
        """Log checkpoint restore event."""
        try:
            self.supabase.table("mission_events").insert({
                "mission_id": target_mission_id,
                "event_type": "checkpoint.restored",
                "event_payload": {
                    "checkpoint_id": checkpoint_id,
                    "restored_nodes": result.restored_nodes,
                    "restored_workstreams": result.restored_workstreams,
                    "restored_handoffs": result.restored_handoffs,
                    "success": result.success,
                    "errors": result.errors
                },
                "created_at": datetime.now().isoformat()
            }).execute()

        except Exception as e:
            logger.error(f"Error logging restore event: {e}")

    async def _cleanup_old_checkpoints(self, mission_id: str):
        """Clean up old/ excess checkpoints for a mission."""
        try:
            # Get all checkpoints for mission
            result = self.supabase.table("mission_checkpoints").select("id, created_at").eq(
                "mission_id", mission_id
            ).order("created_at", desc=True).execute()

            checkpoints = result.data

            # Delete excess checkpoints (keep most recent N)
            if len(checkpoints) > self.max_checkpoints_per_mission:
                excess = checkpoints[self.max_checkpoints_per_mission:]
                for cp in excess:
                    await self.delete_checkpoint(cp["id"])

            # Delete expired checkpoints
            now = datetime.now()
            for cp in checkpoints:
                expires_at = cp.get("expires_at")
                if expires_at:
                    expiry = datetime.fromisoformat(expires_at)
                    if now > expiry:
                        await self.delete_checkpoint(cp["id"])

        except Exception as e:
            logger.error(f"Error cleaning up checkpoints: {e}")


# ============================================================================
# Quick Start Functions
# ============================================================================

async def create_mission_checkpoint(
    mission_id: str,
    graph_state: Dict[str, Any],
    supabase_client,
    description: str = "",
    checkpoint_type: str = "automatic"
) -> str:
    """
    Quick helper: Create a checkpoint for a mission.

    Returns checkpoint ID.
    """
    manager = CheckpointManager(supabase_client)

    data = await manager.create_checkpoint(
        mission_id=mission_id,
        graph_state=graph_state,
        checkpoint_type=CheckpointType(checkpoint_type),
        description=description
    )

    return data.metadata.checkpoint_id


async def restore_mission_checkpoint(
    checkpoint_id: str,
    supabase_client,
    target_mission_id: Optional[str] = None
) -> RestoreResult:
    """Quick helper: Restore a mission from checkpoint."""
    manager = CheckpointManager(supabase_client)
    return await manager.restore_checkpoint(checkpoint_id, target_mission_id)


async def list_mission_checkpoints(
    mission_id: str,
    supabase_client,
    limit: int = 50
) -> List[CheckpointMetadata]:
    """Quick helper: List checkpoints for a mission."""
    manager = CheckpointManager(supabase_client)
    return await manager.list_checkpoints(mission_id, limit=limit)
