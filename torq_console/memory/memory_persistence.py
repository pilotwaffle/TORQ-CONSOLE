"""
Memory Persistence - Phase 4H.1 Milestone 2

Provides persistence for validated memory entries and rejected candidates.
Implements non-blocking write behavior and full auditability.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel

# Try to import Supabase client
try:
    from supabase import Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from .memory_models import (
    MemoryCandidate,
    ValidatedMemory,
    MemoryProvenance,
    MemoryMetadata,
    MemoryContent,
    MemoryType,
    ConfidenceLevel,
    ValidationDecision,
    RejectionReason,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Persistence Models
# ============================================================================

class MemoryRecord(BaseModel):
    """Database record for a validated memory entry."""

    # Identification
    id: UUID
    memory_id: str  # Human-readable identifier

    # Content (stored as JSON)
    content_json: Dict[str, Any]
    content_text: str

    # Metadata
    memory_type: str
    confidence_level: str
    confidence_score: float
    completeness_score: float
    status: str  # active, stale, superseded

    # Provenance
    artifact_id: UUID
    artifact_type: str
    workspace_id: UUID
    mission_id: Optional[UUID]
    node_id: Optional[UUID]
    execution_id: Optional[str]
    team_execution_id: Optional[UUID]
    role_name: Optional[str]
    round_number: Optional[int]

    # Temporal
    created_at: datetime
    validated_at: datetime
    last_accessed_at: Optional[datetime]
    access_count: int = 0

    # Freshness
    freshness_window_days: int
    expires_at: Optional[datetime]

    # Versioning
    version: int = 1
    supersedes_memory_id: Optional[UUID] = None
    superseded_by_memory_id: Optional[UUID] = None


class RejectionLog(BaseModel):
    """Database record for a rejected memory candidate."""

    # Identification
    id: UUID

    # Candidate information (what was rejected)
    artifact_id: UUID
    artifact_type: str
    workspace_id: UUID
    proposed_memory_type: str

    # Rejection details
    rejection_reason: str
    rejection_message: Optional[str]
    failing_rule: Optional[str]

    # Scores at time of rejection
    confidence_score: float
    completeness_score: float

    # Content summary
    title: str
    summary: str

    # Temporal
    rejected_at: datetime

    # Validator info
    validator_version: str = "1.0.0"


# ============================================================================
# Memory Persistence Service
# ============================================================================

class MemoryPersistenceService:
    """
    Service for persisting validated memory entries.

    This is the write path for governed memory.
    """

    def __init__(self, supabase_client: Optional[Any] = None):
        """
        Initialize the persistence service.

        Args:
            supabase_client: Optional Supabase client (uses env vars if None)
        """
        self.supabase = supabase_client
        self.table_name = "governed_memory"
        self.rejection_table_name = "memory_rejection_log"
        self._in_memory_storage: Optional[Dict[str, Any]] = None

    async def initialize_tables(self) -> bool:
        """
        Create database tables if they don't exist.

        Returns:
            True if tables are ready, False otherwise
        """
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available - using in-memory storage")
            self._in_memory_storage: Dict[str, Any] = {
                "memories": {},
                "rejections": {},
            }
            return True

        # Tables would be created via migrations
        # For now, return True to indicate ready
        return True

    async def store_memory(
        self,
        candidate: MemoryCandidate,
        memory_id: str,
    ) -> Tuple[bool, Optional[str], Optional[UUID]]:
        """
        Store a validated memory entry.

        Args:
            candidate: The validated memory candidate
            memory_id: Human-readable memory ID

        Returns:
            (success, error_message, memory_uuid)
        """
        try:
            memory_uuid = uuid4()

            # Build the memory record
            record = {
                "id": str(memory_uuid),
                "memory_id": memory_id,
                "content_json": candidate.content.model_dump(),
                "content_text": candidate.content.content_text,
                "memory_type": candidate.proposed_memory_type.value,
                "confidence_level": candidate.confidence_level.value,
                "confidence_score": candidate.confidence_score,
                "completeness_score": candidate.completeness_score,
                "status": "active",
                "artifact_id": str(candidate.provenance.artifact_id),
                "artifact_type": candidate.provenance.artifact_type,
                "workspace_id": str(candidate.provenance.workspace_id),
                "mission_id": str(candidate.provenance.mission_id) if candidate.provenance.mission_id else None,
                "node_id": str(candidate.provenance.node_id) if candidate.provenance.node_id else None,
                "execution_id": candidate.provenance.execution_id,
                "team_execution_id": str(candidate.provenance.team_execution_id) if candidate.provenance.team_execution_id else None,
                "role_name": candidate.provenance.role_name,
                "round_number": candidate.provenance.round_number,
                "created_at": datetime.utcnow().isoformat(),
                "validated_at": datetime.utcnow().isoformat(),
                "last_accessed_at": None,
                "access_count": 0,
                "freshness_window_days": self._get_freshness_days(candidate.proposed_memory_type),
                "expires_at": None,
                "version": 1,
                "supersedes_memory_id": None,
                "superseded_by_memory_id": None,
            }

            # Store in Supabase or in-memory
            if SUPABASE_AVAILABLE and self.supabase:
                result = self.supabase.table(self.table_name).insert(record).execute()
                logger.info(f"Stored memory {memory_id} ({memory_uuid})")
            else:
                # In-memory fallback
                if self._in_memory_storage is None:
                    self._in_memory_storage = {"memories": {}, "rejections": {}}
                self._in_memory_storage["memories"][str(memory_uuid)] = record
                logger.info(f"Stored memory {memory_id} ({memory_uuid}) in-memory")

            return True, None, memory_uuid

        except Exception as e:
            error_msg = f"Failed to store memory: {e}"
            logger.error(error_msg)
            return False, error_msg, None

    async def log_rejection(
        self,
        candidate: MemoryCandidate,
        rejection_reason: RejectionReason,
        rejection_message: Optional[str] = None,
        failing_rule: Optional[str] = None,
    ) -> bool:
        """
        Log a rejected memory candidate.

        Args:
            candidate: The rejected candidate
            rejection_reason: Why it was rejected
            rejection_message: Optional detailed message
            failing_rule: Optional rule that failed

        Returns:
            True if logged successfully
        """
        try:
            log_id = uuid4()
            log_entry = {
                "id": str(log_id),
                "artifact_id": str(candidate.artifact_id),
                "artifact_type": candidate.artifact_type,
                "workspace_id": str(candidate.provenance.workspace_id),
                "proposed_memory_type": candidate.proposed_memory_type.value,
                "rejection_reason": rejection_reason.value,
                "rejection_message": rejection_message,
                "failing_rule": failing_rule,
                "confidence_score": candidate.confidence_score,
                "completeness_score": candidate.completeness_score,
                "title": candidate.content.title,
                "summary": candidate.content.summary,
                "rejected_at": datetime.utcnow().isoformat(),
                "validator_version": "1.0.0",
            }

            # Store in Supabase or in-memory
            if SUPABASE_AVAILABLE and self.supabase:
                self.supabase.table(self.rejection_table_name).insert(log_entry).execute()
                logger.info(f"Logged rejection for artifact {candidate.artifact_id}: {rejection_reason.value}")
            else:
                # In-memory fallback
                if self._in_memory_storage is None:
                    self._in_memory_storage = {"memories": {}, "rejections": {}}
                self._in_memory_storage["rejections"][str(log_id)] = log_entry
                logger.info(f"Logged rejection for artifact {candidate.artifact_id} in-memory")

            return True

        except Exception as e:
            logger.error(f"Failed to log rejection: {e}")
            return False

    async def get_memory(
        self,
        memory_uuid: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by UUID.

        Args:
            memory_uuid: Memory UUID

        Returns:
            Memory record or None if not found
        """
        try:
            if SUPABASE_AVAILABLE and self.supabase:
                result = self.supabase.table(self.table_name).select("*").eq("id", str(memory_uuid)).execute()
                if result.data:
                    return result.data[0]
            else:
                # In-memory fallback
                if self._in_memory_storage:
                    return self._in_memory_storage["memories"].get(str(memory_uuid))

            return None

        except Exception as e:
            logger.error(f"Failed to get memory {memory_uuid}: {e}")
            return None

    async def get_rejections_by_artifact(
        self,
        artifact_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get rejection logs for a specific artifact.

        Args:
            artifact_id: Artifact ID

        Returns:
            List of rejection logs
        """
        try:
            if SUPABASE_AVAILABLE and self.supabase:
                result = self.supabase.table(self.rejection_table_name).select("*").eq("artifact_id", str(artifact_id)).execute()
                return result.data
            else:
                # In-memory fallback
                if self._in_memory_storage:
                    return [
                        log for log in self._in_memory_storage["rejections"].values()
                        if log["artifact_id"] == str(artifact_id)
                    ]

        except Exception as e:
            logger.error(f"Failed to get rejections for artifact {artifact_id}: {e}")
            return []

    def _get_freshness_days(self, memory_type: MemoryType) -> int:
        """Get freshness window for a memory type."""
        from .memory_models import get_freshness_window
        return get_freshness_window(memory_type)


# ============================================================================
# Memory Write Pipeline
# ============================================================================

class MemoryWritePipeline:
    """
    End-to-end write pipeline for governed memory.

    Flow:
    1. Extract candidate from artifact
    2. Validate candidate
    3. Accept or reject
    4. Log decision
    5. Persist if approved
    """

    def __init__(
        self,
        persistence: MemoryPersistenceService,
        strict_mode: bool = False,
    ):
        """
        Initialize the write pipeline.

        Args:
            persistence: Memory persistence service
            strict_mode: If True, be more restrictive
        """
        self.persistence = persistence
        self.strict_mode = strict_mode

        # Import eligibility engine
        from .eligibility_rules import get_eligibility_engine, get_conflict_detector
        self.eligibility_engine = get_eligibility_engine()
        self.conflict_detector = get_conflict_detector(strict_mode=strict_mode)

        # Statistics
        self._stats = {
            "processed": 0,
            "accepted": 0,
            "rejected": 0,
            "errors": 0,
        }

    async def process_artifact(
        self,
        artifact_data: Dict[str, Any],
        artifact_type: str,
        workspace_id: UUID,
        proposed_memory_type: MemoryType,
        confidence_score: float = 0.7,
        completeness_score: float = 0.7,
    ) -> Tuple[bool, Optional[str], Optional[UUID]]:
        """
        Process an artifact through the memory write pipeline.

        Args:
            artifact_data: The artifact content
            artifact_type: Type of artifact
            workspace_id: Workspace ID
            proposed_memory_type: What type of memory this would be
            confidence_score: Estimated confidence
            completeness_score: Estimated completeness

        Returns:
            (accepted, rejection_reason, memory_uuid)
        """
        self._stats["processed"] += 1

        try:
            # 1. Extract candidate from artifact
            candidate = self._extract_candidate(
                artifact_data,
                artifact_type,
                workspace_id,
                proposed_memory_type,
                confidence_score,
                completeness_score,
            )

            # 2. Validate candidate
            decision, reason, msg = self.eligibility_engine.check_candidate(candidate)

            # 3. Handle rejection
            if decision != ValidationDecision.ACCEPT:
                self._stats["rejected"] += 1
                await self.persistence.log_rejection(
                    candidate,
                    reason or RejectionReason.LOW_CONFIDENCE,
                    msg,
                )
                return False, msg, None

            # 4. Check for conflicts
            existing_memories = await self._get_existing_memories(workspace_id)
            has_conflict, conflict_msg = self.conflict_detector.check_conflict(candidate, existing_memories)
            if has_conflict:
                self._stats["rejected"] += 1
                await self.persistence.log_rejection(
                    candidate,
                    RejectionReason.CONFLICTING,
                    conflict_msg,
                )
                return False, conflict_msg, None

            # 5. Accept and store
            memory_id = self._generate_memory_id(proposed_memory_type)
            success, error, memory_uuid = await self.persistence.store_memory(candidate, memory_id)

            if success:
                self._stats["accepted"] += 1
                return True, None, memory_uuid
            else:
                self._stats["errors"] += 1
                await self.persistence.log_rejection(
                    candidate,
                    RejectionReason.INVALID_SOURCE_TYPE,
                    f"Storage error: {error}",
                )
                return False, error, None

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Error processing artifact: {e}")
            return False, str(e), None

    def _extract_candidate(
        self,
        artifact_data: Dict[str, Any],
        artifact_type: str,
        workspace_id: UUID,
        proposed_memory_type: MemoryType,
        confidence_score: float,
        completeness_score: float,
    ) -> MemoryCandidate:
        """Extract a memory candidate from artifact data."""
        from .memory_models import MemoryProvenance, MemoryContent

        # Build content
        content = MemoryContent(
            title=artifact_data.get("title", "Untitled"),
            summary=artifact_data.get("summary", ""),
            content_json=artifact_data.get("content_json", {}),
            content_text=artifact_data.get("content_text", ""),
            tags=artifact_data.get("tags", []),
        )

        # Build provenance
        provenance = MemoryProvenance(
            artifact_id=UUID(artifact_data.get("artifact_id", str(uuid4()))),
            artifact_type=artifact_type,
            workspace_id=workspace_id,
            mission_id=UUID(artifact_data["mission_id"]) if artifact_data.get("mission_id") else None,
            node_id=UUID(artifact_data["node_id"]) if artifact_data.get("node_id") else None,
            execution_id=artifact_data.get("execution_id"),
            team_execution_id=UUID(artifact_data["team_execution_id"]) if artifact_data.get("team_execution_id") else None,
            role_name=artifact_data.get("role_name"),
            round_number=artifact_data.get("round_number"),
            tool_name=artifact_data.get("tool_name"),
            artifact_created_at=datetime.fromisoformat(artifact_data.get("created_at", datetime.utcnow().isoformat())),
        )

        return MemoryCandidate(
            artifact_id=provenance.artifact_id,
            artifact_type=artifact_type,
            content=content,
            provenance=provenance,
            confidence_score=confidence_score,
            completeness_score=completeness_score,
            proposed_memory_type=proposed_memory_type,
        )

    async def _get_existing_memories(self, workspace_id: UUID) -> List[Any]:
        """Get existing memories for conflict detection."""
        # For now, return empty list
        # In full implementation, would query from persistence
        return []

    def _generate_memory_id(self, memory_type: MemoryType) -> str:
        """Generate a human-readable memory ID."""
        import time
        timestamp = int(time.time())
        return f"{memory_type.value[:3].upper()}_{timestamp}"

    def get_stats(self) -> Dict[str, int]:
        """Get pipeline statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset pipeline statistics."""
        self._stats = {
            "processed": 0,
            "accepted": 0,
            "rejected": 0,
            "errors": 0,
        }


# ============================================================================
# Factory Functions
# ============================================================================

def get_memory_persistence(supabase_client: Optional[Any] = None) -> MemoryPersistenceService:
    """
    Get a memory persistence service.

    Args:
        supabase_client: Optional Supabase client

    Returns:
        Configured persistence service
    """
    return MemoryPersistenceService(supabase_client)


def get_memory_write_pipeline(
    persistence: Optional[MemoryPersistenceService] = None,
    strict_mode: bool = False,
) -> MemoryWritePipeline:
    """
    Get a memory write pipeline.

    Args:
        persistence: Optional persistence service (creates default if None)
        strict_mode: Whether to use strict validation

    Returns:
        Configured write pipeline
    """
    if persistence is None:
        persistence = get_memory_persistence()
    return MemoryWritePipeline(persistence, strict_mode=strict_mode)
