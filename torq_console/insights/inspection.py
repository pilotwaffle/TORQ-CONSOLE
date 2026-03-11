"""
Insight Inspection & Audit Layer - Phase Insight Publishing Milestone 4

Provides inspection, audit, and governance capabilities for published insights.

This module enables:
- Insight detail inspection with full lineage
- Lifecycle history tracking
- Usage and retrieval analytics
- Publication audit trails
- Governance controls (archive, supersede, disable)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightScope,
    InsightLifecycleState,
    InsightSourceType,
    InsightCreate,
    InsightUpdate,
)
from .persistence import (
    InsightPersistence,
    InsightRecord,
    RejectionRecord,
)
from .retrieval import (
    RetrievalAuditEntry,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Inspection Models
# ============================================================================

class InsightLineage(BaseModel):
    """
    Lineage information for an insight.
    """
    insight_id: str
    insight_type: str
    title: str

    # Source lineage
    source_memories: List[SourceMemoryRef] = Field(default_factory=list)
    source_artifacts: List[SourceArtifactRef] = Field(default_factory=list)
    source_insights: List[SourceInsightRef] = Field(default_factory=list)

    # Extraction path
    extraction_method: Optional[str] = None
    extraction_date: Optional[datetime] = None

    # Validation path
    validation_passed: bool = True
    validation_date: Optional[datetime] = None
    quality_scores: Dict[str, float] = Field(default_factory=dict)


class SourceMemoryRef(BaseModel):
    """Reference to a source memory."""
    memory_id: str
    memory_type: str
    title: str
    contribution_weight: float


class SourceArtifactRef(BaseModel):
    """Reference to a source artifact."""
    artifact_id: str
    artifact_type: str
    title: str
    contribution_weight: float


class SourceInsightRef(BaseModel):
    """Reference to a source insight."""
    insight_id: str
    insight_type: str
    title: str
    contribution_weight: float


class LifecycleEvent(BaseModel):
    """
    Event in the lifecycle of an insight.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str  # created, validated, published, superseded, archived, etc.
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    triggered_by: str
    reason: Optional[str] = None

    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageRecord(BaseModel):
    """
    Record of an insight being used/retrieved.
    """
    usage_id: str = Field(default_factory=lambda: str(uuid4()))
    insight_id: str
    retrieved_at: datetime = Field(default_factory=datetime.now)

    # Retrieval context
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    mission_type: Optional[str] = None
    domain: Optional[str] = None

    # Result context
    was_selected: bool = False  # Was the insight actually used (vs just retrieved)
    user_feedback: Optional[str] = None  # Optional feedback on quality


class InsightDetail(BaseModel):
    """
    Complete detail view of an insight.
    """
    # Core identification
    id: str
    insight_type: str
    title: str
    summary: str

    # Scope and content
    scope: str
    scope_key: Optional[str]
    domain: Optional[str]
    tags: List[str]
    content: Dict[str, Any]

    # Quality metrics
    confidence: float
    validation_score: float
    applicability: float
    execution_count: int
    success_rate: Optional[float]

    # Lifecycle
    lifecycle_state: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    expires_at: Optional[datetime]

    # Usage
    usage_count: int
    last_used_at: Optional[datetime]
    effectiveness_score: Optional[float]

    # Supersession
    superseded_by: Optional[str] = None
    superseded_at: Optional[datetime] = None

    # Provenance
    lineage: InsightLineage

    # Lifecycle events
    lifecycle_history: List[LifecycleEvent] = Field(default_factory=list)

    # Usage history (recent)
    recent_usage: List[UsageRecord] = Field(default_factory=list)


# ============================================================================
# Audit Models
# ============================================================================

class RetrievalAuditSummary(BaseModel):
    """
    Summary of retrieval activity for insights.
    """
    total_retrievals: int
    unique_insights_retrieved: int
    avg_retrieval_time_ms: float

    # By agent type
    retrievals_by_agent_type: Dict[str, int] = Field(default_factory=dict)

    # By mission type
    retrievals_by_mission_type: Dict[str, int] = Field(default_factory=dict)

    # By domain
    retrievals_by_domain: Dict[str, int] = Field(default_factory=dict)

    # Most retrieved insights
    top_retrieved_insights: List[Dict[str, Any]] = Field(default_factory=list)

    # Time period
    period_start: datetime
    period_end: datetime


class PublicationAuditTrail(BaseModel):
    """
    Audit trail for insight publication.
    """
    insight_id: str
    insight_type: str
    title: str

    # Publication path
    extraction_date: Optional[datetime] = None
    validation_date: Optional[datetime] = None
    publication_date: Optional[datetime] = None

    # Source details
    source_memory_ids: List[str] = Field(default_factory=list)
    source_artifact_ids: List[str] = Field(default_factory=list)

    # Validation details
    quality_gate_results: List[Dict[str, Any]] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)

    # Approval details
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None

    # Supersession
    has_superseded: bool = False
    superseded_insights: List[str] = Field(default_factory=list)
    superseded_by: Optional[str] = None


class RankingExplanation(BaseModel):
    """
    Explanation of why insights were ranked the way they were.
    """
    retrieval_id: str

    # Query context
    query_context: Dict[str, Any] = Field(default_factory=dict)

    # Ranking factors applied
    ranking_factors: List[str]
    ranking_weights: Dict[str, float] = Field(default_factory=dict)

    # Per-insight scores
    insight_scores: List[Dict[str, Any]] = Field(default_factory=list)

    # Suppression explanations
    suppressed_insights: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Governance Models
# ============================================================================

class GovernanceAction(BaseModel):
    """
    Result of a governance action on an insight.
    """
    success: bool
    action: str  # archive, supersede, disable, etc.
    insight_id: str

    # State changes
    previous_state: Optional[str] = None
    new_state: Optional[str] = None

    # Additional context
    message: str
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.now)

    # Validation
    validation_errors: List[str] = Field(default_factory=list)


class InsightTypeConfig(BaseModel):
    """
    Configuration for an insight type (can be disabled).
    """
    insight_type: str
    enabled: bool = True

    # Governance constraints
    require_explicit_approval: bool = False
    max_confidence: Optional[float] = None
    require_execution_evidence: bool = False

    # Metadata
    disabled_reason: Optional[str] = None
    disabled_by: Optional[str] = None
    disabled_at: Optional[datetime] = None


# ============================================================================
# Inspection Service
# ============================================================================

class InsightInspectionService:
    """
    Service for inspecting and auditing published insights.

    Provides detailed views, lineage tracing, and governance controls.
    """

    def __init__(
        self,
        persistence: InsightPersistence,
        retrieval_service=None,
    ):
        """
        Initialize the inspection service.

        Args:
            persistence: Insight persistence layer
            retrieval_service: Optional retrieval service for audit access
        """
        self.persistence = persistence
        self.retrieval_service = retrieval_service

        # In-memory lifecycle and usage tracking
        # (In production, these would be in dedicated tables)
        self._lifecycle_events: Dict[str, List[LifecycleEvent]] = {}
        self._usage_records: List[UsageRecord] = []

        # Insight type configurations
        self._insight_type_configs: Dict[str, InsightTypeConfig] = {}

    # ========================================================================
    # Insight Listing
    # ========================================================================

    async def list_published_insights(
        self,
        insight_type: Optional[InsightType] = None,
        scope: Optional[InsightScope] = None,
        domain: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List published insights with summary information.

        Args:
            insight_type: Optional type filter
            scope: Optional scope filter
            domain: Optional domain filter
            limit: Max results
            offset: Pagination offset

        Returns:
            List of insight summaries
        """
        insights = await self.persistence.list_insights(
            insight_type=insight_type,
            lifecycle_state=InsightLifecycleState.PUBLISHED,
            scope=scope,
            limit=limit + offset,  # Get extra for offset
        )

        # Apply offset and additional filters
        results = []
        for insight in insights:
            if domain and insight.domain != domain:
                continue
            results.append(insight)

        # Apply offset
        paginated = results[offset:offset + limit]

        # Convert to summary dicts
        summaries = []
        for insight in paginated:
            quality = self._extract_quality(insight)
            summaries.append({
                "id": str(insight.id),
                "insight_type": insight.insight_type.value,
                "title": insight.title,
                "summary": insight.summary,
                "scope": insight.scope.value,
                "domain": insight.domain,
                "confidence": quality.get("confidence_score", 0.0),
                "lifecycle_state": insight.lifecycle_state.value,
                "usage_count": insight.usage_count,
                "created_at": insight.created_at.isoformat(),
                "published_at": insight.published_at.isoformat() if insight.published_at else None,
            })

        return summaries

    # ========================================================================
    # Insight Detail
    # ========================================================================

    async def get_insight_detail(
        self,
        insight_id: UUID,
    ) -> Optional[InsightDetail]:
        """
        Get complete detail view of an insight.

        Args:
            insight_id: ID of insight to inspect

        Returns:
            InsightDetail with full information
        """
        record = await self.persistence.get_insight(insight_id)
        if not record:
            return None

        # Build lineage
        lineage = self._build_lineage(record)

        # Get lifecycle history
        history = self._lifecycle_events.get(str(insight_id), [])

        # Get recent usage
        recent_usage = [
            usage for usage in self._usage_records
            if usage.insight_id == str(insight_id)
        ][-100:]  # Last 100 uses

        quality = self._extract_quality(record)

        return InsightDetail(
            id=str(record.id),
            insight_type=record.insight_type.value,
            title=record.title,
            summary=record.summary,
            scope=record.scope.value,
            scope_key=record.scope_key,
            domain=record.domain,
            tags=record.tags,
            content=record.content,
            confidence=quality.get("confidence_score", 0.0),
            validation_score=quality.get("validation_score", 0.0),
            applicability=quality.get("applicability_score", 0.0),
            execution_count=quality.get("execution_count", 0),
            success_rate=quality.get("success_rate"),
            lifecycle_state=record.lifecycle_state.value,
            created_at=record.created_at,
            updated_at=record.updated_at,
            published_at=record.published_at,
            expires_at=None,
            usage_count=record.usage_count,
            last_used_at=record.last_used_at,
            effectiveness_score=record.effectiveness_score,
            superseded_by=str(record.superseded_by_id) if record.superseded_by_id else None,
            superseded_at=None,  # Could track this
            lineage=lineage,
            lifecycle_history=history,
            recent_usage=recent_usage,
        )

    async def get_insight_lineage(
        self,
        insight_id: UUID,
    ) -> Optional[InsightLineage]:
        """
        Get lineage information for an insight.

        Shows what memories, artifacts, or insights
        this insight was derived from.

        Args:
            insight_id: ID of insight

        Returns:
            InsightLineage with source references
        """
        record = await self.persistence.get_insight(insight_id)
        if not record:
            return None

        return self._build_lineage(record)

    def _build_lineage(self, record: InsightRecord) -> InsightLineage:
        """Build lineage from record."""
        source_refs = record.source_references if record.source_references else []

        source_memories = []
        source_artifacts = []
        source_insights = []

        for ref in source_refs:
            if isinstance(ref, dict):
                source_type = ref.get("source_type")
                source_id = ref.get("source_id")
                weight = ref.get("contribution_weight", 1.0)
            else:
                source_type = ref.source_type.value if hasattr(ref.source_type, "value") else ref.source_type
                source_id = ref.source_id
                weight = ref.contribution_weight

            if source_type == InsightSourceType.MEMORY.value:
                source_memories.append(SourceMemoryRef(
                    memory_id=source_id,
                    memory_type="memory",
                    title=f"Memory {source_id}",
                    contribution_weight=weight,
                ))
            elif source_type == InsightSourceType.ARTIFACT.value:
                source_artifacts.append(SourceArtifactRef(
                    artifact_id=source_id,
                    artifact_type="artifact",
                    title=f"Artifact {source_id}",
                    contribution_weight=weight,
                ))
            elif source_type == InsightSourceType.INSIGHT.value:
                source_insights.append(SourceInsightRef(
                    insight_id=source_id,
                    insight_type="insight",
                    title=f"Insight {source_id}",
                    contribution_weight=weight,
                ))

        quality = self._extract_quality(record)

        # Filter quality dict to only include float values for Pydantic validation
        quality_scores = {
            k: v for k, v in quality.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }

        return InsightLineage(
            insight_id=str(record.id),
            insight_type=record.insight_type.value,
            title=record.title,
            source_memories=source_memories,
            source_artifacts=source_artifacts,
            source_insights=source_insights,
            extraction_method="memory_to_insight_extraction",
            extraction_date=record.created_at,
            validation_passed=record.lifecycle_state in [
                InsightLifecycleState.VALIDATED,
                InsightLifecycleState.PUBLISHED,
            ],
            validation_date=record.updated_at,
            quality_scores=quality_scores,
        )

    async def get_insight_lifecycle_history(
        self,
        insight_id: UUID,
    ) -> List[LifecycleEvent]:
        """
        Get lifecycle history for an insight.

        Shows all state transitions and governance actions.

        Args:
            insight_id: ID of insight

        Returns:
            List of lifecycle events
        """
        return self._lifecycle_events.get(str(insight_id), [])

    async def get_insight_usage_history(
        self,
        insight_id: UUID,
        limit: int = 100,
    ) -> List[UsageRecord]:
        """
        Get usage history for an insight.

        Shows when and how the insight was retrieved/used.

        Args:
            insight_id: ID of insight
            limit: Max records

        Returns:
            List of usage records
        """
        all_usage = [
            usage for usage in self._usage_records
            if usage.insight_id == str(insight_id)
        ]

        # Sort by retrieved_at descending
        all_usage.sort(key=lambda u: u.retrieved_at, reverse=True)

        return all_usage[:limit]

    # ========================================================================
    # Retrieval Audit
    # ========================================================================

    async def get_retrieval_audit_log(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get retrieval audit log entries.

        Args:
            limit: Max entries
            agent_id: Optional agent filter
            agent_type: Optional agent type filter

        Returns:
            List of audit entries
        """
        if self.retrieval_service:
            raw_entries = self.retrieval_service.get_audit_log(limit)
        else:
            raw_entries = []

        # Filter by agent
        entries = []
        for entry in raw_entries:
            if agent_id and entry.agent_id != agent_id:
                continue
            if agent_type and entry.agent_type != agent_type:
                continue
            entries.append(entry)

        # Convert to dicts
        return [
            {
                "retrieval_id": entry.retrieval_id,
                "agent_id": entry.agent_id,
                "agent_type": entry.agent_type,
                "total_candidates": entry.total_candidates,
                "returned_count": entry.returned_count,
                "suppressed_count": entry.suppressed_count,
                "retrieval_time_ms": entry.retrieval_time_ms,
                "timestamp": entry.timestamp.isoformat(),
            }
            for entry in entries
        ]

    async def get_retrieval_audit_summary(
        self,
        period_days: int = 7,
    ) -> RetrievalAuditSummary:
        """
        Get summary statistics for retrieval activity.

        Args:
            period_days: Number of days to summarize

        Returns:
            RetrievalAuditSummary with statistics
        """
        # Calculate period boundaries
        period_end = datetime.now()
        period_start = period_end - timedelta(days=period_days)

        # Filter usage records by period first (needed for unique insights count)
        period_usage = [
            usage for usage in self._usage_records
            if usage.retrieved_at >= period_start
        ]

        if self.retrieval_service:
            stats = self.retrieval_service.get_audit_stats()
            audit_log = self.retrieval_service.get_audit_log(limit=1000)

            # Filter audit log by period
            period_audit = [
                entry for entry in audit_log
                if entry.timestamp >= period_start
            ]

            # Aggregate by various dimensions from audit log
            retrievals_by_agent_type: Dict[str, int] = {}
            retrievals_by_mission_type: Dict[str, int] = {}
            retrievals_by_domain: Dict[str, int] = {}

            for entry in period_audit:
                if entry.agent_type:
                    retrievals_by_agent_type[entry.agent_type] = \
                        retrievals_by_agent_type.get(entry.agent_type, 0) + 1

                # Access mission_type and domain from query_context
                mission_type = entry.query_context.mission_type if entry.query_context else None
                domain = entry.query_context.domain if entry.query_context else None

                if mission_type:
                    retrievals_by_mission_type[mission_type] = \
                        retrievals_by_mission_type.get(mission_type, 0) + 1

                if domain:
                    retrievals_by_domain[domain] = \
                        retrievals_by_domain.get(domain, 0) + 1

            # Use stats from retrieval service for aggregated counts
            total_retrievals = stats.get("total_retrievals", 0)

            # Unique insights retrieved comes from usage records, not audit entries
            # Audit entries track retrieval operations (queries), not specific insights
            unique_insights_retrieved = len(set(
                usage.insight_id for usage in period_usage
            )) if period_usage else 0
        else:
            stats = {"total_retrievals": 0, "avg_retrieval_time_ms": 0.0}
            retrievals_by_agent_type = {}
            retrievals_by_mission_type = {}
            retrievals_by_domain = {}
            total_retrievals = 0
            unique_insights_retrieved = 0

        # Top retrieved insights (from usage records which track specific insight usage)
        insight_retrieval_counts: Dict[str, int] = {}
        for usage in period_usage:
            insight_retrieval_counts[usage.insight_id] = \
                insight_retrieval_counts.get(usage.insight_id, 0) + 1

        top_retrieved = sorted(
            insight_retrieval_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return RetrievalAuditSummary(
            total_retrievals=total_retrievals,
            unique_insights_retrieved=unique_insights_retrieved,
            avg_retrieval_time_ms=stats.get("avg_retrieval_time_ms", 0.0),
            retrievals_by_agent_type=retrievals_by_agent_type,
            retrievals_by_mission_type=retrievals_by_mission_type,
            retrievals_by_domain=retrievals_by_domain,
            top_retrieved_insights=[
                {"insight_id": id, "retrieval_count": count}
                for id, count in top_retrieved
            ],
            period_start=period_start,
            period_end=period_end,
        )

    # ========================================================================
    # Publication Audit
    # ========================================================================

    async def get_publication_audit_trail(
        self,
        insight_id: UUID,
    ) -> Optional[PublicationAuditTrail]:
        """
        Get complete audit trail for an insight's publication.

        Shows extraction, validation, and approval path.

        Args:
            insight_id: ID of insight

        Returns:
            PublicationAuditTrail with full audit info
        """
        record = await self.persistence.get_insight(insight_id)
        if not record:
            return None

        # Get rejections if any (would need separate query in production)
        # For now, build from record
        quality = self._extract_quality(record)

        # Extract source IDs
        source_memory_ids = []
        source_artifact_ids = []

        for ref in record.source_references or []:
            if isinstance(ref, dict):
                source_type = ref.get("source_type")
                ref_id = ref.get("source_id")
            else:
                source_type = ref.source_type.value if hasattr(ref.source_type, "value") else ref.source_type
                ref_id = ref.source_id

            if source_type == InsightSourceType.MEMORY.value:
                source_memory_ids.append(ref_id)
            elif source_type == InsightSourceType.ARTIFACT.value:
                source_artifact_ids.append(ref_id)

        return PublicationAuditTrail(
            insight_id=str(record.id),
            insight_type=record.insight_type.value,
            title=record.title,
            extraction_date=record.created_at,
            validation_date=record.updated_at,
            publication_date=record.published_at,
            source_memory_ids=source_memory_ids,
            source_artifact_ids=source_artifact_ids,
            quality_gate_results=[
                {"gate": "quality", "score": quality.get("confidence_score", 0.0)}
            ],
            validation_errors=[],
            approved_by="system",
            approval_date=record.published_at,
            has_superseded=record.superseded_by_id is not None,
            superseded_insights=[],  # Could query for insights superseded by this one
            superseded_by=str(record.superseded_by_id) if record.superseded_by_id else None,
        )

    # ========================================================================
    # Governance Controls
    # ========================================================================

    async def archive_insight(
        self,
        insight_id: UUID,
        archived_by: str,
        reason: Optional[str] = None,
    ) -> GovernanceAction:
        """
        Archive an insight (mark as no longer relevant).

        Args:
            insight_id: ID of insight to archive
            archived_by: Who is archiving
            reason: Optional reason for archiving

        Returns:
            GovernanceAction with result
        """
        record = await self.persistence.get_insight(insight_id)
        if not record:
            return GovernanceAction(
                success=False,
                action="archive",
                insight_id=str(insight_id),
                message="Insight not found",
                performed_by=archived_by,
            )

        previous_state = record.lifecycle_state.value

        # Transition to ARCHIVED
        from .models import InsightUpdate
        update = InsightUpdate(lifecycle_state=InsightLifecycleState.ARCHIVED)
        updated = await self.persistence.update_insight(insight_id, update)

        # Log lifecycle event
        self._log_lifecycle_event(
            str(insight_id),
            "archived",
            previous_state,
            InsightLifecycleState.ARCHIVED.value,
            archived_by,
            reason,
        )

        return GovernanceAction(
            success=True,
            action="archive",
            insight_id=str(insight_id),
            previous_state=previous_state,
            new_state=InsightLifecycleState.ARCHIVED.value,
            message=f"Insight archived: {record.title}",
            performed_by=archived_by,
        )

    async def supersede_insight(
        self,
        old_insight_id: UUID,
        new_insight_id: UUID,
        superseded_by: str,
        reason: Optional[str] = None,
    ) -> GovernanceAction:
        """
        Mark an insight as superseded by a newer one.

        Args:
            old_insight_id: ID of insight to supersede
            new_insight_id: ID of replacement insight
            superseded_by: Who is performing the action
            reason: Optional reason

        Returns:
            GovernanceAction with result
        """
        old_record = await self.persistence.get_insight(old_insight_id)
        new_record = await self.persistence.get_insight(new_insight_id)

        if not old_record:
            return GovernanceAction(
                success=False,
                action="supersede",
                insight_id=str(old_insight_id),
                message="Old insight not found",
                performed_by=superseded_by,
            )

        previous_state = old_record.lifecycle_state.value

        # Transition old to SUPERSEDED (Milestone 5B: Set superseded_by_id)
        from .models import InsightUpdate
        update = InsightUpdate(
            lifecycle_state=InsightLifecycleState.SUPERSEDED,
            superseded_by_id=new_insight_id,  # Milestone 5B: Track superseding insight
        )
        await self.persistence.update_insight(old_insight_id, update)

        # Log lifecycle event (M5B: Handle None new_record safely)
        new_title = new_record.title if new_record else f"Insight {new_insight_id}"
        supersession_msg = f"Superseded by {new_title}. Reason: {reason or 'None'}"

        self._log_lifecycle_event(
            str(old_insight_id),
            "superseded",
            previous_state,
            InsightLifecycleState.SUPERSEDED.value,
            superseded_by,
            supersession_msg,
        )

        return GovernanceAction(
            success=True,
            action="supersede",
            insight_id=str(old_insight_id),
            previous_state=previous_state,
            new_state=InsightLifecycleState.SUPERSEDED.value,
            message=f"Insight superseded by {new_title}",
            performed_by=superseded_by,
        )

    async def disable_insight_type(
        self,
        insight_type: InsightType,
        disabled_by: str,
        reason: Optional[str] = None,
    ) -> GovernanceAction:
        """
        Disable an insight type (prevent new publications).

        Args:
            insight_type: Type to disable
            disabled_by: Who is disabling
            reason: Optional reason

        Returns:
            GovernanceAction with result
        """
        config = InsightTypeConfig(
            insight_type=insight_type.value,
            enabled=False,
            disabled_reason=reason,
            disabled_by=disabled_by,
            disabled_at=datetime.now(),
        )

        self._insight_type_configs[insight_type.value] = config

        return GovernanceAction(
            success=True,
            action="disable_type",
            insight_id=insight_type.value,
            message=f"Insight type {insight_type.value} disabled",
            performed_by=disabled_by,
        )

    async def enable_insight_type(
        self,
        insight_type: InsightType,
        enabled_by: str,
    ) -> GovernanceAction:
        """
        Re-enable a disabled insight type.

        Args:
            insight_type: Type to enable
            enabled_by: Who is enabling

        Returns:
            GovernanceAction with result
        """
        config = self._insight_type_configs.get(insight_type.value)
        if config:
            config.enabled = True
            config.disabled_reason = None
            config.disabled_by = None
            config.disabled_at = None
        else:
            config = InsightTypeConfig(
                insight_type=insight_type.value,
                enabled=True,
            )

        self._insight_type_configs[insight_type.value] = config

        return GovernanceAction(
            success=True,
            action="enable_type",
            insight_id=insight_type.value,
            message=f"Insight type {insight_type.value} enabled",
            performed_by=enabled_by,
        )

    def is_insight_type_enabled(self, insight_type: InsightType) -> bool:
        """Check if an insight type is enabled for publication."""
        config = self._insight_type_configs.get(insight_type.value)
        if config:
            return config.enabled
        return True  # Default to enabled

    def get_insight_type_config(self, insight_type) -> Optional[InsightTypeConfig]:
        """
        Get the configuration for an insight type.

        Milestone 5B: Added for retrieval service to check disabled types.

        Args:
            insight_type: InsightType enum or string value

        Returns:
            InsightTypeConfig if exists, None otherwise
        """
        # Handle both enum and string
        type_value = insight_type.value if hasattr(insight_type, 'value') else str(insight_type)
        return self._insight_type_configs.get(type_value)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_quality(self, record: InsightRecord) -> Dict[str, Any]:
        """Extract quality dict from record (handles dict or object)."""
        quality = getattr(record, 'quality', {})
        if isinstance(quality, dict):
            return quality
        # If it's a QualityMetrics object, convert to dict
        return {
            "confidence_score": getattr(quality, "confidence_score", 0.0),
            "validation_score": getattr(quality, "validation_score", 0.0),
            "applicability_score": getattr(quality, "applicability_score", 0.0),
            "source_count": getattr(quality, "source_count", 0),
            "execution_count": getattr(quality, "execution_count", 0),
            "success_rate": getattr(quality, "success_rate", None),
            "last_validated_at": getattr(quality, "last_validated_at", None),
        }

    def _log_lifecycle_event(
        self,
        insight_id: str,
        event_type: str,
        from_state: Optional[str],
        to_state: Optional[str],
        triggered_by: str,
        reason: Optional[str] = None,
    ):
        """Log a lifecycle event for an insight."""
        event = LifecycleEvent(
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            triggered_by=triggered_by,
            reason=reason,
        )

        if insight_id not in self._lifecycle_events:
            self._lifecycle_events[insight_id] = []

        self._lifecycle_events[insight_id].append(event)

    def log_usage(
        self,
        insight_id: str,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        mission_type: Optional[str] = None,
        domain: Optional[str] = None,
    ):
        """
        Log a usage/retrieval of an insight.

        Called by retrieval service when insights are retrieved.
        """
        usage = UsageRecord(
            insight_id=insight_id,
            agent_id=agent_id,
            agent_type=agent_type,
            mission_type=mission_type,
            domain=domain,
        )

        self._usage_records.append(usage)


# ============================================================================
# Helper Functions
# ============================================================================

def get_inspection_service(
    persistence: InsightPersistence,
    retrieval_service=None,
) -> InsightInspectionService:
    """
    Get the insight inspection service.

    Args:
        persistence: Insight persistence layer
        retrieval_service: Optional retrieval service for audit

    Returns:
        InsightInspectionService instance
    """
    return InsightInspectionService(persistence, retrieval_service)
