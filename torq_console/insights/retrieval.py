"""
Insight Retrieval Service - Phase Insight Publishing Milestone 3

Provides agents with context-aware access to published insights.

This module enables:
- Mission-aware retrieval by context, domain, agent type
- Ranking by relevance, freshness, confidence
- Filtering of invalid/stale/superseded insights
- Audit logging for all retrieval operations
- Clean agent-facing payloads (not raw persistence)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightScope,
    InsightLifecycleState,
    InsightSourceType,
    Insight,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Retrieval Request Models
# ============================================================================

class RetrievalContext(BaseModel):
    """
    Context for insight retrieval.

    Describes the mission, agent, and execution context
    to enable context-aware retrieval.
    """
    # Mission context
    mission_type: Optional[str] = Field(
        None,
        description="Type of mission (e.g., 'planning', 'execution', 'review')"
    )
    mission_phase: Optional[str] = Field(
        None,
        description="Current mission phase"
    )

    # Agent context
    agent_type: Optional[str] = Field(
        None,
        description="Type of agent making the request"
    )
    agent_id: Optional[str] = Field(
        None,
        description="Specific agent ID"
    )

    # Domain context
    domain: Optional[str] = Field(
        None,
        description="Domain filter (e.g., 'financial', 'legal', 'technical')"
    )

    # Scope context
    scope: Optional[InsightScope] = Field(
        None,
        description="Requested scope filter"
    )
    scope_key: Optional[str] = Field(
        None,
        description="Specific scope key (e.g., workflow type name)"
    )

    # Insight type preference
    insight_types: Optional[List[InsightType]] = Field(
        None,
        description="Preferred insight types"
    )

    # Quality constraints
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score"
    )
    min_validation_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum validation score"
    )

    # Freshness constraints
    max_age_days: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum age of insight in days"
    )
    require_recent_validation: bool = Field(
        default=False,
        description="Require validation within validation window"
    )

    # Provenance constraints
    require_memory_source: bool = Field(
        default=False,
        description="Require source to be memory (not just artifacts)"
    )
    require_execution_evidence: bool = Field(
        default=False,
        description="Require execution evidence in provenance"
    )

    # Pagination
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum results to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination"
    )


class RetrievalResult(BaseModel):
    """
    Result of an insight retrieval operation.
    """
    # Retrieved insights
    insights: List[InsightPayload]

    # Retrieval metadata
    total_count: int
    returned_count: int
    filtered_count: int

    # Suppressed insights (for audit)
    suppressed: List[SuppressedInsight] = Field(default_factory=list)

    # Query context
    query_context: RetrievalContext

    # Ranking rationale
    ranking_factors: List[str] = Field(default_factory=list)

    # Performance
    retrieval_time_ms: int

    # Metadata
    retrieved_at: datetime = Field(default_factory=datetime.now)
    retrieval_id: str = Field(default_factory=lambda: f"retrieval_{datetime.now().isoformat()}")


# ============================================================================
# Agent-Facing Payload
# ============================================================================

class ProvenanceSummary(BaseModel):
    """
    Simplified provenance summary for agent consumption.
    """
    source_count: int
    source_types: List[str]
    has_memory_source: bool
    has_artifact_source: bool
    earliest_source_date: Optional[datetime]
    extraction_methods: List[str]


class InsightPayload(BaseModel):
    """
    Clean agent-facing insight payload.

    Does not expose raw persistence internals.
    """
    # Core identification
    id: str
    insight_type: str
    title: str
    summary: str

    # Content
    content: Dict[str, Any]

    # Scope
    scope: str
    scope_key: Optional[str]
    domain: Optional[str]
    tags: List[str]

    # Quality metrics
    confidence: float
    validation_score: float
    applicability: float

    # Status
    lifecycle_state: str
    published_at: Optional[datetime]
    last_validated_at: Optional[datetime]

    # Provenance (simplified)
    provenance: ProvenanceSummary

    # Usage stats
    usage_count: int
    effectiveness_score: Optional[float]

    # Relevance (computed for this retrieval)
    relevance_score: float
    match_reasons: List[str]

    # Traceability
    trace_id: str


class SuppressedInsight(BaseModel):
    """
    Record of a suppressed insight for audit purposes.
    """
    id: str
    insight_type: str
    title: str
    suppression_reason: str
    lifecycle_state: str
    confidence: float


# ============================================================================
# Retrieval Audit Log
# ============================================================================

class RetrievalAuditEntry(BaseModel):
    """
    Audit log entry for retrieval operations.
    """
    retrieval_id: str

    # Query
    query_context: RetrievalContext

    # Results
    total_candidates: int
    returned_count: int
    suppressed_count: int

    # Performance
    retrieval_time_ms: int

    # Ranking
    ranking_factors: List[str]

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None


# ============================================================================
# Ranking Configuration
# ============================================================================

class RankingConfig(BaseModel):
    """
    Configuration for insight ranking.
    """
    # Weight factors (sum should approach 1.0)
    scope_match_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    freshness_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    confidence_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    relevance_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    provenance_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    usage_weight: float = Field(default=0.05, ge=0.0, le=1.0)

    # Freshness scoring
    fresh_days_threshold: int = Field(default=30, ge=1)
    stale_days_threshold: int = Field(default=90, ge=1)

    # Lifecycle preference
    lifecycle_preference: List[InsightLifecycleState] = Field(
        default_factory=lambda: [
            InsightLifecycleState.PUBLISHED,
            InsightLifecycleState.VALIDATED,
        ]
    )


# ============================================================================
# Retrieval Service
# ============================================================================

class InsightRetrievalService:
    """
    Service for retrieving insights for agent consumption.

    Provides context-aware retrieval with ranking and filtering.
    """

    def __init__(
        self,
        persistence,
        ranking_config: Optional[RankingConfig] = None,
    ):
        """
        Initialize the retrieval service.

        Args:
            persistence: Insight persistence layer
            ranking_config: Optional ranking configuration
        """
        self.persistence = persistence
        self.ranking_config = ranking_config or RankingConfig()
        self._audit_log: List[RetrievalAuditEntry] = []

    async def retrieve(
        self,
        context: RetrievalContext
    ) -> RetrievalResult:
        """
        Retrieve insights based on context.

        Args:
            context: Retrieval context with filters and preferences

        Returns:
            RetrievalResult with ranked insights and metadata
        """
        start_time = datetime.now()

        # Get all published insights (base query)
        all_insights = await self.persistence.list_insights(
            insight_type=None,
            lifecycle_state=InsightLifecycleState.PUBLISHED,
            scope=context.scope,
            limit=1000  # Get more than we need for filtering
        )

        # Also include VALIDATED for some contexts
        if context.mission_type in ["planning", "review"]:
            validated = await self.persistence.list_insights(
                insight_type=None,
                lifecycle_state=InsightLifecycleState.VALIDATED,
                scope=context.scope,
                limit=500
            )
            all_insights.extend(validated)

        # Filter insights
        filtered, suppressed = self._filter_insights(all_insights, context)

        # Rank insights
        ranked = self._rank_insights(filtered, context)

        # Convert to payloads
        payloads = [
            self._to_payload(insight, context)
            for insight in ranked[:context.limit]
        ]

        # Calculate timing
        retrieval_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        # Build result
        result = RetrievalResult(
            insights=payloads,
            total_count=len(all_insights),
            returned_count=len(payloads),
            filtered_count=len(suppressed),
            suppressed=suppressed,
            query_context=context,
            ranking_factors=self._get_ranking_factors(),
            retrieval_time_ms=retrieval_time_ms,
        )

        # Audit log
        self._audit_retrieval(result)

        logger.info(
            f"Retrieved {len(payloads)} insights from {len(all_insights)} total, "
            f"{len(suppressed)} suppressed in {retrieval_time_ms}ms"
        )

        return result

    async def retrieve_by_mission(
        self,
        mission_type: str,
        agent_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> RetrievalResult:
        """
        Convenience method for mission-based retrieval.

        Args:
            mission_type: Type of mission
            agent_type: Optional agent type filter
            domain: Optional domain filter
            limit: Max results

        Returns:
            RetrievalResult
        """
        context = RetrievalContext(
            mission_type=mission_type,
            agent_type=agent_type,
            domain=domain,
            limit=limit,
        )
        return await self.retrieve(context)

    async def retrieve_by_domain(
        self,
        domain: str,
        insight_types: Optional[List[InsightType]] = None,
        min_confidence: float = 0.70,
        limit: int = 50
    ) -> RetrievalResult:
        """
        Convenience method for domain-based retrieval.

        Args:
            domain: Domain to filter by
            insight_types: Optional insight type filters
            min_confidence: Minimum confidence
            limit: Max results

        Returns:
            RetrievalResult
        """
        context = RetrievalContext(
            domain=domain,
            insight_types=insight_types,
            min_confidence=min_confidence,
            limit=limit,
        )
        return await self.retrieve(context)

    async def retrieve_by_agent_type(
        self,
        agent_type: str,
        mission_type: Optional[str] = None,
        scope: Optional[InsightScope] = None,
        limit: int = 50
    ) -> RetrievalResult:
        """
        Convenience method for agent-type-based retrieval.

        Args:
            agent_type: Type of agent
            mission_type: Optional mission type
            scope: Optional scope filter
            limit: Max results

        Returns:
            RetrievalResult
        """
        context = RetrievalContext(
            agent_type=agent_type,
            mission_type=mission_type,
            scope=scope,
            limit=limit,
        )
        return await self.retrieve(context)

    async def retrieve_by_insight_type(
        self,
        insight_type: InsightType,
        scope: Optional[InsightScope] = None,
        min_validation_score: float = 0.70,
        limit: int = 50
    ) -> RetrievalResult:
        """
        Convenience method for insight-type-based retrieval.

        Args:
            insight_type: Type of insight
            scope: Optional scope filter
            min_validation_score: Minimum validation score
            limit: Max results

        Returns:
            RetrievalResult
        """
        context = RetrievalContext(
            insight_types=[insight_type],
            scope=scope,
            min_validation_score=min_validation_score,
            limit=limit,
        )
        return await self.retrieve(context)

    async def retrieve_by_source_lineage(
        self,
        source_id: str,
        source_type: Optional[InsightSourceType] = None,
        limit: int = 50
    ) -> RetrievalResult:
        """
        Retrieve insights that trace back to a specific source.

        Useful for understanding what insights were derived from
        a particular memory or artifact.

        Args:
            source_id: Source ID to trace
            source_type: Optional source type filter
            limit: Max results

        Returns:
            RetrievalResult
        """
        # Get all insights and filter by lineage
        all_insights = await self.persistence.list_insights(
            lifecycle_state=InsightLifecycleState.PUBLISHED,
            limit=1000
        )

        matching = []
        for insight in all_insights:
            source_refs = self._get_source_references(insight)
            for ref in source_refs:
                ref_id = self._get_source_id(ref)
                if ref_id == source_id:
                    if source_type is None or self._get_source_type(ref) == source_type:
                        matching.append(insight)
                        break

        # Convert to payloads with minimal context
        context = RetrievalContext(limit=limit)
        payloads = [
            self._to_payload(insight, context)
            for insight in matching[:limit]
        ]

        return RetrievalResult(
            insights=payloads,
            total_count=len(matching),
            returned_count=len(payloads),
            filtered_count=0,
            query_context=context,
            ranking_factors=["source_lineage_match"],
            retrieval_time_ms=0,
        )

    # ========================================================================
    # Helper Methods for InsightRecord / Insight compatibility
    # ========================================================================

    def _get_confidence(self, insight) -> float:
        """Extract confidence score from insight (handles dict or object)."""
        quality = getattr(insight, 'quality', {})
        if isinstance(quality, dict):
            return quality.get('confidence_score', 0.0)
        return getattr(quality, 'confidence_score', 0.0)

    def _get_validation_score(self, insight) -> float:
        """Extract validation score from insight (handles dict or object)."""
        quality = getattr(insight, 'quality', {})
        if isinstance(quality, dict):
            return quality.get('validation_score', 0.0)
        return getattr(quality, 'validation_score', 0.0)

    def _get_applicability_score(self, insight) -> float:
        """Extract applicability score from insight (handles dict or object)."""
        quality = getattr(insight, 'quality', {})
        if isinstance(quality, dict):
            return quality.get('applicability_score', 0.0)
        return getattr(quality, 'applicability_score', 0.0)

    def _get_execution_count(self, insight) -> int:
        """Extract execution count from insight (handles dict or object)."""
        quality = getattr(insight, 'quality', {})
        if isinstance(quality, dict):
            return quality.get('execution_count', 0)
        return getattr(quality, 'execution_count', 0)

    def _get_last_validated_at(self, insight) -> Optional[datetime]:
        """Extract last_validated_at from insight (handles dict or object)."""
        quality = getattr(insight, 'quality', {})
        if isinstance(quality, dict):
            val = quality.get('last_validated_at')
            return datetime.fromisoformat(val) if isinstance(val, str) else val
        return getattr(quality, 'last_validated_at', None)

    def _get_source_references(self, insight) -> List:
        """Extract source references from insight (handles list of dict or list of objects)."""
        refs = getattr(insight, 'source_references', [])
        if not refs:
            return []
        # If first element is a dict, all are dicts
        if isinstance(refs[0], dict):
            return refs
        return refs

    def _get_source_type(self, ref) -> Optional[str]:
        """Extract source_type from reference (handles dict or object)."""
        if isinstance(ref, dict):
            return ref.get('source_type')
        return getattr(ref, 'source_type', None)

    def _get_source_id(self, ref) -> Optional[str]:
        """Extract source_id from reference (handles dict or object)."""
        if isinstance(ref, dict):
            return ref.get('source_id')
        return getattr(ref, 'source_id', None)

    # ========================================================================
    # Filtering
    # ========================================================================

    def _filter_insights(
        self,
        insights: List,
        context: RetrievalContext
    ) -> tuple[List, List[SuppressedInsight]]:
        """
        Filter insights based on context constraints.

        Returns:
            Tuple of (filtered_insights, suppressed_insights)
        """
        filtered = []
        suppressed = []

        for insight in insights:
            # Check against all filters
            reasons = self._get_suppression_reasons(insight, context)

            if reasons:
                suppressed.append(SuppressedInsight(
                    id=str(insight.id),
                    insight_type=insight.insight_type.value,
                    title=insight.title,
                    suppression_reason="; ".join(reasons),
                    lifecycle_state=insight.lifecycle_state.value,
                    confidence=self._get_confidence(insight),
                ))
            else:
                filtered.append(insight)

        return filtered, suppressed

    def _get_suppression_reasons(
        self,
        insight,
        context: RetrievalContext
    ) -> List[str]:
        """
        Get list of reasons why an insight should be suppressed.

        Returns empty list if insight should not be suppressed.
        """
        reasons = []

        # Lifecycle state filtering
        if insight.lifecycle_state in [
            InsightLifecycleState.DRAFT,
            InsightLifecycleState.CANDIDATE,
            InsightLifecycleState.SUPERSEDED,
            InsightLifecycleState.ARCHIVED,
        ]:
            reasons.append(f"lifecycle_state={insight.lifecycle_state.value}")
            return reasons  # Early return - these are hard filters

        # Insight type filtering
        if context.insight_types:
            if insight.insight_type not in context.insight_types:
                reasons.append(f"insight_type_not_requested")

        # Domain filtering
        if context.domain and insight.domain != context.domain:
            reasons.append(f"domain_mismatch")

        # Scope filtering
        if context.scope and insight.scope != context.scope:
            reasons.append(f"scope_mismatch")

        # Scope key filtering
        if context.scope_key and insight.scope_key != context.scope_key:
            reasons.append(f"scope_key_mismatch")

        # Quality filtering
        if context.min_confidence:
            if self._get_confidence(insight) < context.min_confidence:
                reasons.append(f"confidence_below_threshold")

        if context.min_validation_score:
            if self._get_validation_score(insight) < context.min_validation_score:
                reasons.append(f"validation_below_threshold")

        # Freshness filtering
        if context.max_age_days:
            age_days = (datetime.now() - insight.created_at).days
            if age_days > context.max_age_days:
                reasons.append(f"stale_exceeds_max_age")

        if context.require_recent_validation:
            last_validated = self._get_last_validated_at(insight)
            if last_validated:
                validation_age = (datetime.now() - last_validated).days
                if validation_age > 30:  # 30-day validation window
                    reasons.append(f"validation_not_recent")
            else:
                reasons.append(f"no_validation_date")

        # Provenance filtering
        if context.require_memory_source:
            source_refs = self._get_source_references(insight)
            has_memory = any(
                self._get_source_type(sr) == InsightSourceType.MEMORY
                for sr in source_refs
            )
            if not has_memory:
                reasons.append(f"no_memory_source")

        if context.require_execution_evidence:
            if self._get_execution_count(insight) == 0:
                reasons.append(f"no_execution_evidence")

        return reasons

    # ========================================================================
    # Ranking
    # ========================================================================

    def _rank_insights(
        self,
        insights: List,
        context: RetrievalContext
    ) -> List:
        """
        Rank insights by relevance to context.

        Returns sorted list (highest relevance first).
        """
        # Calculate scores
        scored = []
        for insight in insights:
            score = self._calculate_relevance_score(insight, context)
            scored.append((insight, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return [insight for insight, score in scored]

    def _calculate_relevance_score(
        self,
        insight,
        context: RetrievalContext
    ) -> float:
        """
        Calculate relevance score for an insight.

        Returns score between 0.0 and 1.0.
        """
        config = self.ranking_config

        # Scope match
        scope_score = 0.0
        if context.scope and insight.scope == context.scope:
            scope_score = 1.0
        elif context.scope_key and insight.scope_key == context.scope_key:
            scope_score = 0.8
        else:
            scope_score = 0.5

        # Freshness score
        age_days = (datetime.now() - insight.created_at).days
        if age_days <= config.fresh_days_threshold:
            freshness_score = 1.0
        elif age_days <= config.stale_days_threshold:
            # Linear decay
            ratio = (age_days - config.fresh_days_threshold) / (
                config.stale_days_threshold - config.fresh_days_threshold
            )
            freshness_score = 1.0 - (ratio * 0.5)
        else:
            freshness_score = 0.3  # Still somewhat relevant

        # Confidence score
        confidence_score = self._get_confidence(insight)

        # Relevance to mission/agent type
        relevance_score = 0.5  # Base
        if context.domain and insight.domain == context.domain:
            relevance_score += 0.3
        if context.insight_types and insight.insight_type in context.insight_types:
            relevance_score += 0.2
        relevance_score = min(relevance_score, 1.0)

        # Provenance quality
        provenance_score = min(self._get_validation_score(insight), 1.0)

        # Usage score
        usage_score = min(insight.usage_count / 100.0, 1.0)  # Cap at 100 uses

        # Weighted combination
        total_score = (
            scope_score * config.scope_match_weight +
            freshness_score * config.freshness_weight +
            confidence_score * config.confidence_weight +
            relevance_score * config.relevance_weight +
            provenance_score * config.provenance_weight +
            usage_score * config.usage_weight
        )

        return total_score

    def _get_ranking_factors(self) -> List[str]:
        """Get list of ranking factors used."""
        config = self.ranking_config
        factors = []

        if config.scope_match_weight > 0:
            factors.append("scope_match")
        if config.freshness_weight > 0:
            factors.append("freshness")
        if config.confidence_weight > 0:
            factors.append("confidence")
        if config.relevance_weight > 0:
            factors.append("relevance")
        if config.provenance_weight > 0:
            factors.append("provenance")
        if config.usage_weight > 0:
            factors.append("usage")

        return factors

    # ========================================================================
    # Payload Conversion
    # ========================================================================

    def _to_payload(
        self,
        insight,
        context: RetrievalContext
    ) -> InsightPayload:
        """
        Convert internal insight to agent-facing payload.
        """
        # Get source references
        source_refs = self._get_source_references(insight)

        # Build provenance summary
        source_types_set = set()
        for sr in source_refs:
            source_type = self._get_source_type(sr)
            if source_type:
                if isinstance(source_type, str):
                    source_types_set.add(source_type)
                else:
                    source_types_set.add(source_type.value)

        has_memory = InsightSourceType.MEMORY.value in source_types_set
        has_artifact = InsightSourceType.ARTIFACT.value in source_types_set

        extraction_methods = []
        for sr in source_refs:
            if isinstance(sr, dict):
                method = sr.get('extraction_method')
            else:
                method = getattr(sr, 'extraction_method', None)
            if method:
                extraction_methods.append(method)
        extraction_methods = list(set(extraction_methods))

        # Get last_validated_at
        last_validated = self._get_last_validated_at(insight)

        provenance = ProvenanceSummary(
            source_count=len(source_refs),
            source_types=list(source_types_set),
            has_memory_source=has_memory,
            has_artifact_source=has_artifact,
            earliest_source_date=None,  # Could compute from refs
            extraction_methods=extraction_methods,
        )

        # Compute match reasons
        match_reasons = []
        if context.scope and insight.scope == context.scope:
            match_reasons.append("scope_match")
        if context.domain and insight.domain == context.domain:
            match_reasons.append("domain_match")
        if context.insight_types and insight.insight_type in context.insight_types:
            match_reasons.append("requested_type")

        # Calculate relevance score
        relevance = self._calculate_relevance_score(insight, context)

        return InsightPayload(
            id=str(insight.id),
            insight_type=insight.insight_type.value,
            title=insight.title,
            summary=insight.summary,
            content=insight.content,
            scope=insight.scope.value,
            scope_key=insight.scope_key,
            domain=insight.domain,
            tags=insight.tags,
            confidence=self._get_confidence(insight),
            validation_score=self._get_validation_score(insight),
            applicability=self._get_applicability_score(insight),
            lifecycle_state=insight.lifecycle_state.value,
            published_at=insight.published_at,
            last_validated_at=last_validated,
            provenance=provenance,
            usage_count=insight.usage_count,
            effectiveness_score=insight.effectiveness_score,
            relevance_score=relevance,
            match_reasons=match_reasons,
            trace_id=str(insight.id),
        )

    # ========================================================================
    # Audit
    # ========================================================================

    def _audit_retrieval(self, result: RetrievalResult):
        """Log retrieval operation for audit."""
        entry = RetrievalAuditEntry(
            retrieval_id=result.retrieval_id,
            query_context=result.query_context,
            total_candidates=result.total_count,
            returned_count=result.returned_count,
            suppressed_count=result.filtered_count,
            retrieval_time_ms=result.retrieval_time_ms,
            ranking_factors=result.ranking_factors,
            agent_id=result.query_context.agent_id,
            agent_type=result.query_context.agent_type,
        )
        self._audit_log.append(entry)

    def get_audit_log(
        self,
        limit: int = 100
    ) -> List[RetrievalAuditEntry]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]

    def get_audit_stats(self) -> Dict[str, Any]:
        """Get statistics from audit log."""
        if not self._audit_log:
            return {"total_retrievals": 0}

        total = len(self._audit_log)
        avg_time = sum(e.retrieval_time_ms for e in self._audit_log) / total
        avg_results = sum(e.returned_count for e in self._audit_log) / total

        # By agent type
        by_agent = {}
        for entry in self._audit_log:
            if entry.agent_type:
                by_agent[entry.agent_type] = by_agent.get(entry.agent_type, 0) + 1

        return {
            "total_retrievals": total,
            "avg_retrieval_time_ms": avg_time,
            "avg_results_per_query": avg_results,
            "retrievals_by_agent_type": by_agent,
        }


# ============================================================================
# Helper Functions
# ============================================================================

def get_retrieval_service(
    persistence,
    ranking_config: Optional[RankingConfig] = None
) -> InsightRetrievalService:
    """
    Get the insight retrieval service.

    Args:
        persistence: Insight persistence layer
        ranking_config: Optional ranking configuration

    Returns:
        InsightRetrievalService instance
    """
    return InsightRetrievalService(persistence, ranking_config)
