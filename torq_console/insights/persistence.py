"""
Insight Persistence Layer - Phase Insight Publishing Milestone 2

Persists insights to storage with lineage tracking and rejection logging.

This module handles:
- Storing candidate and published insights
- Logging rejection reasons
- Preserving lineage back to source memory/artifacts
- Managing lifecycle state transitions
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightScope,
    InsightLifecycleState,
    InsightSourceType,
    Insight,
    InsightCreate,
    InsightUpdate,
    SourceReference,
    QualityMetrics,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Storage Models
# ============================================================================

class InsightRecord(BaseModel):
    """
    Record of an insight in storage.
    """
    id: UUID = Field(default_factory=uuid4)
    insight_type: InsightType
    title: str
    summary: str
    scope: InsightScope
    scope_key: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    content: Dict[str, Any]

    # Provenance
    source_references: List[Dict[str, Any]] = Field(default_factory=list)

    # Quality
    quality: Dict[str, Any] = Field(default_factory=dict)

    # Lifecycle
    lifecycle_state: InsightLifecycleState

    # Tracking
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Usage
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    effectiveness_score: Optional[float] = None

    # Supersession
    superseded_by_id: Optional[UUID] = None

    # Creator
    created_by: str = "system"


class RejectionRecord(BaseModel):
    """
    Record of a rejected insight candidate.
    """
    id: UUID = Field(default_factory=uuid4)
    insight_type: InsightType
    title: str
    summary: str

    # Rejection details
    rejection_reasons: List[str]
    quality_gate_results: List[Dict[str, Any]]

    # Candidate data (for review)
    candidate_data: Dict[str, Any]

    # Source info
    source_memory_ids: List[str]
    source_artifact_ids: List[str]

    # Metadata
    rejected_at: datetime = Field(default_factory=datetime.now)
    rejected_by: str = "system"


# ============================================================================
# Persistence Interface
# ============================================================================

class InsightPersistence(BaseModel):
    """
    Base interface for insight persistence.

    Implementations can use Supabase, PostgreSQL, or other storage.
    """

    async def create_insight(
        self,
        insight: InsightCreate
    ) -> InsightRecord:
        """Create a new insight record."""
        raise NotImplementedError

    async def get_insight(
        self,
        insight_id: UUID
    ) -> Optional[InsightRecord]:
        """Get an insight by ID."""
        raise NotImplementedError

    async def list_insights(
        self,
        insight_type: Optional[InsightType] = None,
        lifecycle_state: Optional[InsightLifecycleState] = None,
        scope: Optional[InsightScope] = None,
        limit: int = 100
    ) -> List[InsightRecord]:
        """List insights with optional filters."""
        raise NotImplementedError

    async def update_insight(
        self,
        insight_id: UUID,
        update: InsightUpdate
    ) -> Optional[InsightRecord]:
        """Update an insight."""
        raise NotImplementedError

    async def delete_insight(
        self,
        insight_id: UUID
    ) -> bool:
        """Delete an insight."""
        raise NotImplementedError

    async def log_rejection(
        self,
        candidate: InsightCreate,
        rejection_reasons: List[str],
        quality_gate_results: List[Dict]
    ) -> RejectionRecord:
        """Log a rejected candidate."""
        raise NotImplementedError

    async def get_rejections(
        self,
        limit: int = 100
    ) -> List[RejectionRecord]:
        """Get rejection records."""
        raise NotImplementedError


# ============================================================================
# Supabase Implementation
# ============================================================================

class SupabaseInsightPersistence(InsightPersistence):
    """
    Supabase-based insight persistence.

    Stores insights in Supabase with proper schema and lineage tracking.
    """

    def __init__(self, supabase_client):
        """
        Initialize with Supabase client.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client

    async def create_insight(
        self,
        insight: InsightCreate
    ) -> InsightRecord:
        """
        Create a new insight record.

        Args:
            insight: The insight to create

        Returns:
            The created insight record
        """
        now = datetime.now()

        # Serialize source references
        source_refs = [
            {
                "source_type": sr.source_type.value,
                "source_id": sr.source_id,
                "contribution_weight": sr.contribution_weight,
                "extraction_method": sr.extraction_method,
                "referenced_at": sr.referenced_at.isoformat(),
                "evidence_snippet": sr.evidence_snippet,
            }
            for sr in insight.source_references
        ]

        # Serialize quality metrics
        quality_dict = {
            "confidence_score": insight.quality.confidence_score,
            "validation_score": insight.quality.validation_score,
            "applicability_score": insight.quality.applicability_score,
            "source_count": insight.quality.source_count,
            "execution_count": insight.quality.execution_count,
            "success_rate": insight.quality.success_rate,
            "last_validated_at": insight.quality.last_validated_at.isoformat()
                if insight.quality.last_validated_at else None,
            "evidence_cutoff_at": insight.quality.evidence_cutoff_at.isoformat()
                if insight.quality.evidence_cutoff_at else None,
        }

        # Build record
        record = {
            "id": str(uuid4()),
            "insight_type": insight.insight_type.value,
            "title": insight.title,
            "summary": insight.summary,
            "scope": insight.scope.value,
            "scope_key": insight.scope_key,
            "domain": insight.domain,
            "tags": insight.tags,
            "content": insight.content,
            "source_references": source_refs,
            "quality": quality_dict,
            "lifecycle_state": insight.initial_state.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "published_at": None,
            "expires_at": (now + timedelta(days=90)).isoformat()
                if insight.expires_in_days else None,
            "usage_count": 0,
            "created_by": "system",
        }

        # Insert to Supabase
        result = self.supabase.table("insights").insert(record).execute()

        if result.data:
            row = result.data[0]
            return self._row_to_record(row)
        else:
            raise Exception(f"Failed to create insight: {result}")

    async def get_insight(
        self,
        insight_id: UUID
    ) -> Optional[InsightRecord]:
        """Get an insight by ID."""
        result = self.supabase.table("insights").select("*").eq("id", str(insight_id)).execute()

        if result.data:
            return self._row_to_record(result.data[0])
        return None

    async def list_insights(
        self,
        insight_type: Optional[InsightType] = None,
        lifecycle_state: Optional[InsightLifecycleState] = None,
        scope: Optional[InsightScope] = None,
        limit: int = 100
    ) -> List[InsightRecord]:
        """List insights with optional filters."""
        query = self.supabase.table("insights").select("*")

        if insight_type:
            query = query.eq("insight_type", insight_type.value)
        if lifecycle_state:
            query = query.eq("lifecycle_state", lifecycle_state.value)
        if scope:
            query = query.eq("scope", scope.value)

        result = query.limit(limit).execute()

        return [self._row_to_record(row) for row in result.data]

    async def update_insight(
        self,
        insight_id: UUID,
        update: InsightUpdate
    ) -> Optional[InsightRecord]:
        """Update an insight."""
        update_data = {"updated_at": datetime.now().isoformat()}

        if update.title:
            update_data["title"] = update.title
        if update.summary:
            update_data["summary"] = update.summary
        if update.content:
            update_data["content"] = update.content
        if update.tags:
            update_data["tags"] = update.tags
        if update.lifecycle_state:
            update_data["lifecycle_state"] = update.lifecycle_state.value
        if update.expires_at:
            update_data["expires_at"] = update.expires_at.isoformat()

        result = self.supabase.table("insights").update(update_data).eq("id", str(insight_id)).execute()

        if result.data:
            return self._row_to_record(result.data[0])
        return None

    async def delete_insight(
        self,
        insight_id: UUID
    ) -> bool:
        """Delete an insight."""
        result = self.supabase.table("insights").delete().eq("id", str(insight_id)).execute()
        return len(result.data) > 0

    async def log_rejection(
        self,
        candidate: InsightCreate,
        rejection_reasons: List[str],
        quality_gate_results: List[Dict]
    ) -> RejectionRecord:
        """Log a rejected candidate."""
        # Extract source IDs
        source_memory_ids = [
            sr.source_id
            for sr in candidate.source_references
            if sr.source_type == InsightSourceType.MEMORY
        ]
        source_artifact_ids = [
            sr.source_id
            for sr in candidate.source_references
            if sr.source_type == InsightSourceType.ARTIFACT
        ]

        record = {
            "id": str(uuid4()),
            "insight_type": candidate.insight_type.value,
            "title": candidate.title,
            "summary": candidate.summary,
            "rejection_reasons": rejection_reasons,
            "quality_gate_results": quality_gate_results,
            "candidate_data": candidate.model_dump(),
            "source_memory_ids": source_memory_ids,
            "source_artifact_ids": source_artifact_ids,
            "rejected_at": datetime.now().isoformat(),
            "rejected_by": "system",
        }

        result = self.supabase.table("insight_rejections").insert(record).execute()

        if result.data:
            row = result.data[0]
            return RejectionRecord(
                id=UUID(row["id"]),
                insight_type=InsightType(row["insight_type"]),
                title=row["title"],
                summary=row["summary"],
                rejection_reasons=row["rejection_reasons"],
                quality_gate_results=row["quality_gate_results"],
                candidate_data=row["candidate_data"],
                source_memory_ids=row["source_memory_ids"],
                source_artifact_ids=row["source_artifact_ids"],
                rejected_at=datetime.fromisoformat(row["rejected_at"]),
                rejected_by=row["rejected_by"],
            )
        else:
            raise Exception(f"Failed to log rejection: {result}")

    async def get_rejections(
        self,
        limit: int = 100
    ) -> List[RejectionRecord]:
        """Get rejection records."""
        result = self.supabase.table("insight_rejections").select("*").order("rejected_at", desc=True).limit(limit).execute()

        return [
            RejectionRecord(
                id=UUID(row["id"]),
                insight_type=InsightType(row["insight_type"]),
                title=row["title"],
                summary=row["summary"],
                rejection_reasons=row["rejection_reasons"],
                quality_gate_results=row["quality_gate_results"],
                candidate_data=row["candidate_data"],
                source_memory_ids=row["source_memory_ids"],
                source_artifact_ids=row["source_artifact_ids"],
                rejected_at=datetime.fromisoformat(row["rejected_at"]),
                rejected_by=row["rejected_by"],
            )
            for row in result.data
        ]

    def _row_to_record(self, row: Dict[str, Any]) -> InsightRecord:
        """Convert database row to InsightRecord."""
        return InsightRecord(
            id=UUID(row["id"]),
            insight_type=InsightType(row["insight_type"]),
            title=row["title"],
            summary=row["summary"],
            scope=InsightScope(row["scope"]),
            scope_key=row.get("scope_key"),
            domain=row.get("domain"),
            tags=row.get("tags", []),
            content=row["content"],
            source_references=row.get("source_references", []),
            quality=row.get("quality", {}),
            lifecycle_state=InsightLifecycleState(row["lifecycle_state"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            published_at=datetime.fromisoformat(row["published_at"]) if row.get("published_at") else None,
            expires_at=datetime.fromisoformat(row["expires_at"]) if row.get("expires_at") else None,
            usage_count=row.get("usage_count", 0),
            last_used_at=datetime.fromisoformat(row["last_used_at"]) if row.get("last_used_at") else None,
            effectiveness_score=row.get("effectiveness_score"),
            superseded_by_id=UUID(row["superseded_by_id"]) if row.get("superseded_by_id") else None,
            created_by=row.get("created_by", "system"),
        )


# ============================================================================
# In-Memory Implementation (for testing)
# ============================================================================

class MemoryInsightPersistence(InsightPersistence):
    """
    In-memory insight persistence for testing.

    Not production-ready but useful for development and testing.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._insights: Dict[UUID, InsightRecord] = {}
        self._rejections: List[RejectionRecord] = []

    async def create_insight(
        self,
        insight: InsightCreate
    ) -> InsightRecord:
        """Create a new insight record in memory."""
        id = uuid4()
        now = datetime.now()

        record = InsightRecord(
            id=id,
            insight_type=insight.insight_type,
            title=insight.title,
            summary=insight.summary,
            scope=insight.scope,
            scope_key=insight.scope_key,
            domain=insight.domain,
            tags=insight.tags,
            content=insight.content,
            source_references=[sr.model_dump() for sr in insight.source_references],
            quality=insight.quality.model_dump(),
            lifecycle_state=insight.initial_state,
            created_at=now,
            updated_at=now,
            published_at=None,
            expires_at=None,
            created_by="system",
        )

        self._insights[id] = record
        logger.info(f"Created insight {id}: {insight.title}")
        return record

    async def get_insight(
        self,
        insight_id: UUID
    ) -> Optional[InsightRecord]:
        """Get an insight by ID."""
        return self._insights.get(insight_id)

    async def list_insights(
        self,
        insight_type: Optional[InsightType] = None,
        lifecycle_state: Optional[InsightLifecycleState] = None,
        scope: Optional[InsightScope] = None,
        limit: int = 100
    ) -> List[InsightRecord]:
        """List insights with filters."""
        insights = list(self._insights.values())

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        if lifecycle_state:
            insights = [i for i in insights if i.lifecycle_state == lifecycle_state]
        if scope:
            insights = [i for i in insights if i.scope == scope]

        return insights[:limit]

    async def update_insight(
        self,
        insight_id: UUID,
        update: InsightUpdate
    ) -> Optional[InsightRecord]:
        """Update an insight."""
        record = self._insights.get(insight_id)
        if not record:
            return None

        if update.title:
            record.title = update.title
        if update.summary:
            record.summary = update.summary
        if update.content:
            record.content = update.content
        if update.tags:
            record.tags = update.tags
        if update.lifecycle_state:
            record.lifecycle_state = update.lifecycle_state
        if update.superseded_by_id:
            record.superseded_by_id = update.superseded_by_id  # Milestone 5B
        if update.expires_at:
            record.expires_at = update.expires_at

        record.updated_at = datetime.now()
        return record

    async def delete_insight(
        self,
        insight_id: UUID
    ) -> bool:
        """Delete an insight."""
        if insight_id in self._insights:
            del self._insights[insight_id]
            return True
        return False

    async def log_rejection(
        self,
        candidate: InsightCreate,
        rejection_reasons: List[str],
        quality_gate_results: List[Dict]
    ) -> RejectionRecord:
        """Log a rejected candidate."""
        source_memory_ids = [
            sr.source_id
            for sr in candidate.source_references
            if sr.source_type == InsightSourceType.MEMORY
        ]
        source_artifact_ids = [
            sr.source_id
            for sr in candidate.source_references
            if sr.source_type == InsightSourceType.ARTIFACT
        ]

        record = RejectionRecord(
            id=uuid4(),
            insight_type=candidate.insight_type,
            title=candidate.title,
            summary=candidate.summary,
            rejection_reasons=rejection_reasons,
            quality_gate_results=quality_gate_results,
            candidate_data=candidate.model_dump(),
            source_memory_ids=source_memory_ids,
            source_artifact_ids=source_artifact_ids,
            rejected_at=datetime.now(),
        )

        self._rejections.append(record)
        return record

    async def get_rejections(
        self,
        limit: int = 100
    ) -> List[RejectionRecord]:
        """Get rejection records."""
        return self._rejections[:limit]


# ============================================================================
# Helper Functions
# ============================================================================

def get_insight_persistence(supabase_client=None) -> InsightPersistence:
    """
    Get the appropriate insight persistence implementation.

    Args:
        supabase_client: Supabase client (uses in-memory if None)

    Returns:
        InsightPersistence instance
    """
    if supabase_client:
        return SupabaseInsightPersistence(supabase_client)
    return MemoryInsightPersistence()
