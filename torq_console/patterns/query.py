"""
Phase 4G: Pattern Query, Inspection, and Audit Layer (Milestone 4)

This module provides pattern retrieval, inspection, and governance capabilities for TORQ Console.

Key Components:
- PatternQueryService: Query patterns by multiple criteria
- PatternInspectionView: Rich inspection of pattern details
- PatternAuditView: Audit trail and decision history
- PatternGovernanceService: Governance and control operations
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
from enum import Enum

from .pattern_models import (
    PatternType,
    PatternLifecycleState,
    PatternSourceType,
    Pattern,
    PatternSourceReference,
    PatternQualityMetrics,
)
from .extraction import (
    PatternCandidate,
    PatternEvidence,
)
from .validation import (
    ValidationResult,
    PromotionResult,
    PatternAuditRecord,
    ValidationOutcome,
    RejectionReason,
)


# ============================================================================
# Query Filters and Criteria
# ============================================================================

class PatternQueryFilter:
    """
    Filter criteria for pattern queries.

    Supports filtering by:
    - Pattern type
    - Lifecycle state
    - Domain/scope
    - Confidence range
    - Recurrence range
    - Time range (first/last observed)
    - Source type
    - Validation status
    """

    def __init__(
        self,
        pattern_types: Optional[List[PatternType]] = None,
        lifecycle_states: Optional[List[PatternLifecycleState]] = None,
        domains: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        min_recurrence: Optional[float] = None,
        max_recurrence: Optional[float] = None,
        min_observation_count: Optional[int] = None,
        max_observation_count: Optional[int] = None,
        observed_after: Optional[datetime] = None,
        observed_before: Optional[datetime] = None,
        source_types: Optional[List[PatternSourceType]] = None,
        source_ids: Optional[List[str]] = None,
        validated_after: Optional[datetime] = None,
        validated_before: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        search_text: Optional[str] = None,
    ):
        """Initialize query filter."""
        self.pattern_types = pattern_types
        self.lifecycle_states = lifecycle_states
        self.domains = domains
        self.scopes = scopes
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.min_recurrence = min_recurrence
        self.max_recurrence = max_recurrence
        self.min_observation_count = min_observation_count
        self.max_observation_count = max_observation_count
        self.observed_after = observed_after
        self.observed_before = observed_before
        self.source_types = source_types
        self.source_ids = source_ids
        self.validated_after = validated_after
        self.validated_before = validated_before
        self.tags = tags
        self.search_text = search_text

    def matches(self, pattern: Pattern) -> bool:
        """
        Check if a pattern matches this filter.

        Args:
            pattern: Pattern to check

        Returns:
            True if pattern matches all filter criteria
        """
        # Pattern type filter
        if self.pattern_types and pattern.pattern_type not in self.pattern_types:
            return False

        # Lifecycle state filter
        if self.lifecycle_states and pattern.lifecycle_state not in self.lifecycle_states:
            return False

        # Domain filter
        if self.domains and pattern.domain not in self.domains:
            return False

        # Scope filter
        if self.scopes and pattern.scope not in self.scopes:
            return False

        # Confidence range
        conf = pattern.quality.confidence_score
        if self.min_confidence is not None and conf < self.min_confidence:
            return False
        if self.max_confidence is not None and conf > self.max_confidence:
            return False

        # Observation count range
        obs_count = pattern.quality.observation_count
        if self.min_observation_count is not None and obs_count < self.min_observation_count:
            return False
        if self.max_observation_count is not None and obs_count > self.max_observation_count:
            return False

        # Time range
        if self.observed_after and pattern.quality.first_observed_at < self.observed_after:
            return False
        if self.observed_before and pattern.quality.last_observed_at > self.observed_before:
            return False

        # Source type filter
        if self.source_types:
            pattern_source_types = {ref.source_type for ref in pattern.source_references}
            if not any(st in pattern_source_types for st in self.source_types):
                return False

        # Source ID filter
        if self.source_ids:
            pattern_source_ids = {ref.source_id for ref in pattern.source_references}
            if not any(sid in pattern_source_ids for sid in self.source_ids):
                return False

        # Tag filter
        if self.tags:
            pattern_tags = set(pattern.tags or [])
            if not any(tag in pattern_tags for tag in self.tags):
                return False

        # Text search (name, description, characteristics)
        if self.search_text:
            search_lower = self.search_text.lower()
            searchable_text = (
                pattern.name.lower() + " " +
                (pattern.description or "").lower() + " " +
                " ".join(str(v) for v in (pattern.characteristics or {}).values()).lower()
            )
            if search_lower not in searchable_text:
                return False

        return True


class PatternQuerySort(Enum):
    """Sort options for pattern queries."""
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    CONFIDENCE_ASC = "confidence_asc"
    CONFIDENCE_DESC = "confidence_desc"
    RECURRENCE_ASC = "recurrence_asc"
    RECURRENCE_DESC = "recurrence_desc"
    OBSERVED_ASC = "observed_asc"
    OBSERVED_DESC = "observed_desc"
    CREATED_ASC = "created_asc"
    CREATED_DESC = "created_desc"


class PatternQueryResult:
    """
    Result of a pattern query.

    Contains matched patterns, pagination info, and query metadata.
    """

    def __init__(
        self,
        patterns: List[Pattern],
        total_count: int,
        page: int = 1,
        page_size: int = 50,
        filter_applied: Optional[PatternQueryFilter] = None,
    ):
        """Initialize query result."""
        self.patterns = patterns
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.filter_applied = filter_applied
        self.total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        self.has_next = page < self.total_pages
        self.has_prev = page > 1

    @property
    def count(self) -> int:
        """Number of patterns in this page."""
        return len(self.patterns)


# ============================================================================
# Pattern Query Service
# ============================================================================

class PatternQueryService:
    """
    Service for querying and retrieving patterns.

    In-memory implementation for now. Can be extended to use
    persistent storage (database) for production.
    """

    def __init__(self):
        """Initialize the query service with in-memory storage."""
        self._patterns: Dict[UUID, Pattern] = {}
        self._audit_records: List[PatternAuditRecord] = []

    def add_pattern(self, pattern: Pattern) -> None:
        """Add a pattern to the query store."""
        self._patterns[pattern.id] = pattern

    def remove_pattern(self, pattern_id: UUID) -> bool:
        """Remove a pattern from the query store."""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            return True
        return False

    def add_audit_record(self, record: PatternAuditRecord) -> None:
        """Add an audit record."""
        self._audit_records.append(record)

    def get_by_id(self, pattern_id: UUID) -> Optional[Pattern]:
        """
        Get a pattern by its ID.

        Args:
            pattern_id: UUID of the pattern

        Returns:
            Pattern if found, None otherwise
        """
        return self._patterns.get(pattern_id)

    def get_by_ids(self, pattern_ids: List[UUID]) -> List[Pattern]:
        """
        Get multiple patterns by their IDs.

        Args:
            pattern_ids: List of pattern UUIDs

        Returns:
            List of found patterns (in same order as requested, missing IDs skipped)
        """
        patterns = []
        for pid in pattern_ids:
            if pid in self._patterns:
                patterns.append(self._patterns[pid])
        return patterns

    def query(
        self,
        filter: Optional[PatternQueryFilter] = None,
        sort: PatternQuerySort = PatternQuerySort.NAME_ASC,
        page: int = 1,
        page_size: int = 50,
    ) -> PatternQueryResult:
        """
        Query patterns with filtering and pagination.

        Args:
            filter: Query filter criteria
            sort: Sort order
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            PatternQueryResult with matched patterns
        """
        # Start with all patterns
        all_patterns = list(self._patterns.values())

        # Apply filter
        if filter:
            matched = [p for p in all_patterns if filter.matches(p)]
        else:
            matched = all_patterns

        # Sort
        matched = self._sort_patterns(matched, sort)

        # Get total count before pagination
        total_count = len(matched)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_patterns = matched[start_idx:end_idx]

        return PatternQueryResult(
            patterns=page_patterns,
            total_count=total_count,
            page=page,
            page_size=page_size,
            filter_applied=filter,
        )

    def query_by_type(
        self,
        pattern_type: PatternType,
        lifecycle_state: Optional[PatternLifecycleState] = None,
    ) -> List[Pattern]:
        """
        Query patterns by type.

        Args:
            pattern_type: Pattern type to filter by
            lifecycle_state: Optional lifecycle state filter

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(
            pattern_types=[pattern_type],
            lifecycle_states=[lifecycle_state] if lifecycle_state else None,
        )
        result = self.query(filter, page_size=1000)  # Get all
        return result.patterns

    def query_by_lifecycle_state(
        self,
        lifecycle_state: PatternLifecycleState,
    ) -> List[Pattern]:
        """
        Query patterns by lifecycle state.

        Args:
            lifecycle_state: Lifecycle state to filter by

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(lifecycle_states=[lifecycle_state])
        result = self.query(filter, page_size=1000)
        return result.patterns

    def query_by_domain(
        self,
        domain: str,
        pattern_type: Optional[PatternType] = None,
    ) -> List[Pattern]:
        """
        Query patterns by domain.

        Args:
            domain: Domain to filter by
            pattern_type: Optional pattern type filter

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(
            domains=[domain],
            pattern_types=[pattern_type] if pattern_type else None,
        )
        result = self.query(filter, page_size=1000)
        return result.patterns

    def query_by_source(
        self,
        source_type: PatternSourceType,
        source_id: Optional[str] = None,
    ) -> List[Pattern]:
        """
        Query patterns that reference a specific source.

        Args:
            source_type: Source type to filter by
            source_id: Optional specific source ID

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(
            source_types=[source_type],
            source_ids=[source_id] if source_id else None,
        )
        result = self.query(filter, page_size=1000)
        return result.patterns

    def query_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float = 1.0,
    ) -> List[Pattern]:
        """
        Query patterns within a confidence range.

        Args:
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(
            min_confidence=min_confidence,
            max_confidence=max_confidence,
        )
        result = self.query(filter, page_size=1000)
        return result.patterns

    def query_stale_patterns(
        self,
        days_threshold: int = 30,
    ) -> List[Pattern]:
        """
        Query patterns that haven't been observed recently.

        Args:
            days_threshold: Number of days since last observation

        Returns:
            List of stale patterns
        """
        threshold = datetime.now() - timedelta(days=days_threshold)
        filter = PatternQueryFilter(observed_before=threshold)
        result = self.query(filter, page_size=1000)
        return result.patterns

    def query_weak_patterns(
        self,
        confidence_threshold: float = 0.5,
        observation_threshold: int = 3,
    ) -> List[Pattern]:
        """
        Query patterns below quality thresholds.

        Args:
            confidence_threshold: Maximum confidence score
            observation_threshold: Maximum observation count

        Returns:
            List of weak patterns
        """
        filter = PatternQueryFilter(
            max_confidence=confidence_threshold,
            max_observation_count=observation_threshold,
        )
        result = self.query(filter, page_size=1000)
        return result.patterns

    def search(
        self,
        search_text: str,
        pattern_types: Optional[List[PatternType]] = None,
    ) -> List[Pattern]:
        """
        Full-text search across patterns.

        Args:
            search_text: Text to search for
            pattern_types: Optional pattern types to limit search

        Returns:
            List of matching patterns
        """
        filter = PatternQueryFilter(
            search_text=search_text,
            pattern_types=pattern_types,
        )
        result = self.query(filter, page_size=1000)
        return result.patterns

    def _sort_patterns(
        self,
        patterns: List[Pattern],
        sort: PatternQuerySort,
    ) -> List[Pattern]:
        """Sort patterns by the specified criteria."""
        reverse_map = {
            PatternQuerySort.NAME_DESC: True,
            PatternQuerySort.CONFIDENCE_DESC: True,
            PatternQuerySort.RECURRENCE_DESC: True,
            PatternQuerySort.OBSERVED_DESC: True,
            PatternQuerySort.CREATED_DESC: True,
        }

        reverse = reverse_map.get(sort, False)

        if sort in (PatternQuerySort.NAME_ASC, PatternQuerySort.NAME_DESC):
            return sorted(patterns, key=lambda p: p.name.lower(), reverse=reverse)

        elif sort in (PatternQuerySort.CONFIDENCE_ASC, PatternQuerySort.CONFIDENCE_DESC):
            return sorted(patterns, key=lambda p: p.quality.confidence_score, reverse=reverse)

        elif sort in (PatternQuerySort.RECURRENCE_ASC, PatternQuerySort.RECURRENCE_DESC):
            # Use observation count as recurrence proxy
            return sorted(patterns, key=lambda p: p.quality.observation_count, reverse=reverse)

        elif sort in (PatternQuerySort.OBSERVED_ASC, PatternQuerySort.OBSERVED_DESC):
            return sorted(patterns, key=lambda p: p.quality.last_observed_at, reverse=reverse)

        elif sort in (PatternQuerySort.CREATED_ASC, PatternQuerySort.CREATED_DESC):
            return sorted(patterns, key=lambda p: p.quality.first_observed_at, reverse=reverse)

        return patterns

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored patterns.

        Returns:
            Dict with pattern counts by type, state, etc.
        """
        patterns = list(self._patterns.values())

        if not patterns:
            return {
                "total_patterns": 0,
                "by_type": {},
                "by_lifecycle_state": {},
                "by_domain": {},
                "average_confidence": 0.0,
                "average_observations": 0.0,
            }

        # Count by type
        by_type: Dict[PatternType, int] = {}
        for p in patterns:
            by_type[p.pattern_type] = by_type.get(p.pattern_type, 0) + 1

        # Count by lifecycle state
        by_state: Dict[PatternLifecycleState, int] = {}
        for p in patterns:
            by_state[p.lifecycle_state] = by_state.get(p.lifecycle_state, 0) + 1

        # Count by domain
        by_domain: Dict[str, int] = {}
        for p in patterns:
            by_domain[p.domain] = by_domain.get(p.domain, 0) + 1

        # Calculate averages
        avg_confidence = sum(p.quality.confidence_score for p in patterns) / len(patterns)
        avg_observations = sum(p.quality.observation_count for p in patterns) / len(patterns)

        return {
            "total_patterns": len(patterns),
            "by_type": {pt.value: count for pt, count in by_type.items()},
            "by_lifecycle_state": {state.value: count for state, count in by_state.items()},
            "by_domain": by_domain,
            "average_confidence": round(avg_confidence, 3),
            "average_observations": round(avg_observations, 1),
        }


# ============================================================================
# Pattern Inspection View
# ============================================================================

class PatternEvidenceSummary:
    """Summary of evidence contributing to a pattern."""

    def __init__(
        self,
        total_count: int,
        by_source_type: Dict[str, int],
        by_execution_id: Dict[str, int],
        time_span: timedelta,
        earliest_observation: datetime,
        latest_observation: datetime,
    ):
        """Initialize evidence summary."""
        self.total_count = total_count
        self.by_source_type = {st.value: count for st, count in by_source_type.items()}
        self.by_execution_id = by_execution_id
        self.time_span_days = time_span.days
        self.earliest_observation = earliest_observation
        self.latest_observation = latest_observation


class PatternScoreBreakdown:
    """Breakdown of a pattern's quality scores."""

    def __init__(
        self,
        recurrence_score: float,
        confidence_score: float,
        stability_score: float,
        source_diversity_score: float,
        temporal_consistency_score: float,
        relevance_score: float,
    ):
        """Initialize score breakdown."""
        self.recurrence_score = recurrence_score
        self.confidence_score = confidence_score
        self.stability_score = stability_score
        self.source_diversity_score = source_diversity_score
        self.temporal_consistency_score = temporal_consistency_score
        self.relevance_score = relevance_score

    @property
    def overall_score(self) -> float:
        """Calculate overall score as average of all dimensions."""
        scores = [
            self.recurrence_score,
            self.confidence_score,
            self.stability_score,
            self.source_diversity_score,
            self.temporal_consistency_score,
        ]
        return sum(scores) / len(scores)


class PatternLifecycleHistoryEntry:
    """Single entry in pattern lifecycle history."""

    def __init__(
        self,
        timestamp: datetime,
        from_state: Optional[PatternLifecycleState],
        to_state: PatternLifecycleState,
        reason: str,
        triggered_by: Optional[str] = None,
    ):
        """Initialize history entry."""
        self.timestamp = timestamp
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.triggered_by = triggered_by


class PatternSupersessionInfo:
    """Information about pattern supersession."""

    def __init__(
        self,
        is_superseded: bool,
        superseded_by: Optional[Pattern] = None,
        superseded_at: Optional[datetime] = None,
        superseded_by_name: Optional[str] = None,
        superseded_by_id: Optional[UUID] = None,
    ):
        """Initialize supersession info."""
        self.is_superseded = is_superseded
        self.superseded_by = superseded_by
        self.superseded_at = superseded_at
        self.superseded_by_name = superseded_by_name
        self.superseded_by_id = superseded_by_id


class PatternInspectionView:
    """
    Rich inspection view for a pattern.

    Provides comprehensive details including:
    - Full pattern information
    - Evidence summary
    - Score breakdown
    - Lifecycle history
    - Supersession chain
    - Source references
    """

    def __init__(
        self,
        pattern: Pattern,
        evidence_summary: PatternEvidenceSummary,
        score_breakdown: PatternScoreBreakdown,
        lifecycle_history: List[PatternLifecycleHistoryEntry],
        supersession_info: PatternSupersessionInfo,
        source_references: List[PatternSourceReference],
        validation_history: List[PatternAuditRecord],
        characteristics: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """Initialize inspection view."""
        self.pattern = pattern
        self.evidence_summary = evidence_summary
        self.score_breakdown = score_breakdown
        self.lifecycle_history = lifecycle_history
        self.supersession_info = supersession_info
        self.source_references = source_references
        self.validation_history = validation_history
        self.characteristics = characteristics or {}
        self.tags = tags or []

    @property
    def id(self) -> UUID:
        """Pattern ID."""
        return self.pattern.id

    @property
    def pattern_id(self) -> UUID:
        """Pattern ID (alias for compatibility)."""
        return self.pattern.id

    @property
    def name(self) -> str:
        """Pattern name."""
        return self.pattern.name

    @property
    def pattern_type(self) -> PatternType:
        """Pattern type."""
        return self.pattern.pattern_type

    @property
    def lifecycle_state(self) -> PatternLifecycleState:
        """Current lifecycle state."""
        return self.pattern.lifecycle_state

    @property
    def domain(self) -> str:
        """Pattern domain."""
        return self.pattern.domain

    @property
    def scope(self) -> str:
        """Pattern scope."""
        return self.pattern.scope

    def to_dict(self) -> Dict[str, Any]:
        """Convert inspection view to dictionary."""
        return {
            "pattern": {
                "id": str(self.pattern.id),
                "name": self.pattern.name,
                "description": self.pattern.description,
                "pattern_type": self.pattern.pattern_type.value,
                "lifecycle_state": self.pattern.lifecycle_state.value,
                "domain": self.pattern.domain,
                "scope": self.pattern.scope,
                "characteristics": self.characteristics,
                "tags": self.tags,
                "created_at": self.pattern.quality.first_observed_at.isoformat(),
                "updated_at": self.pattern.quality.last_observed_at.isoformat(),
            },
            "evidence_summary": {
                "total_count": self.evidence_summary.total_count,
                "by_source_type": self.evidence_summary.by_source_type,
                "time_span_days": self.evidence_summary.time_span_days,
                "earliest_observation": self.evidence_summary.earliest_observation.isoformat(),
                "latest_observation": self.evidence_summary.latest_observation.isoformat(),
            },
            "score_breakdown": {
                "recurrence_score": self.score_breakdown.recurrence_score,
                "confidence_score": self.score_breakdown.confidence_score,
                "stability_score": self.score_breakdown.stability_score,
                "source_diversity_score": self.score_breakdown.source_diversity_score,
                "temporal_consistency_score": self.score_breakdown.temporal_consistency_score,
                "relevance_score": self.score_breakdown.relevance_score,
                "overall_score": self.score_breakdown.overall_score,
            },
            "lifecycle_history": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "from_state": entry.from_state.value if entry.from_state else None,
                    "to_state": entry.to_state.value,
                    "reason": entry.reason,
                    "triggered_by": entry.triggered_by,
                }
                for entry in self.lifecycle_history
            ],
            "supersession_info": {
                "is_superseded": self.supersession_info.is_superseded,
                "superseded_by": str(self.supersession_info.superseded_by_id) if self.supersession_info.superseded_by_id else None,
                "superseded_by_name": self.supersession_info.superseded_by_name,
                "superseded_at": self.supersession_info.superseded_at.isoformat() if self.supersession_info.superseded_at else None,
            },
            "source_references": [
                {
                    "source_type": ref.source_type.value,
                    "source_id": ref.source_id,
                    "observed_at": ref.observed_at.isoformat(),
                }
                for ref in self.source_references
            ],
            "validation_history": [
                {
                    "timestamp": record.decided_at.isoformat(),
                    "action": record.action,
                    "decision": record.decision_reasoning,
                }
                for record in self.validation_history
            ],
        }


# ============================================================================
# Pattern Inspection Service
# ============================================================================

class PatternInspectionService:
    """
    Service for creating rich inspection views of patterns.

    Builds comprehensive views including evidence, scores,
    lifecycle history, and supersession information.
    """

    def __init__(
        self,
        query_service: Optional[PatternQueryService] = None,
    ):
        """Initialize the inspection service."""
        self.query_service = query_service or PatternQueryService()

    def inspect(
        self,
        pattern: Pattern,
        audit_records: Optional[List[PatternAuditRecord]] = None,
    ) -> PatternInspectionView:
        """
        Create a rich inspection view for a pattern.

        Args:
            pattern: Pattern to inspect
            audit_records: Optional audit records for history

        Returns:
            PatternInspectionView with full details
        """
        # Build evidence summary
        evidence_summary = self._build_evidence_summary(pattern)

        # Build score breakdown
        score_breakdown = self._build_score_breakdown(pattern)

        # Build lifecycle history from audit records
        lifecycle_history = self._build_lifecycle_history(pattern, audit_records or [])

        # Build supersession info
        supersession_info = self._build_supersession_info(pattern)

        return PatternInspectionView(
            pattern=pattern,
            evidence_summary=evidence_summary,
            score_breakdown=score_breakdown,
            lifecycle_history=lifecycle_history,
            supersession_info=supersession_info,
            source_references=pattern.source_references,
            validation_history=audit_records or [],
            characteristics=pattern.characteristics,
            tags=pattern.tags,
        )

    def _build_evidence_summary(self, pattern: Pattern) -> PatternEvidenceSummary:
        """Build evidence summary from source references."""
        # Count by source type
        by_source_type: Dict[PatternSourceType, int] = {}
        for ref in pattern.source_references:
            by_source_type[ref.source_type] = by_source_type.get(ref.source_type, 0) + 1

        # Count by execution ID (from source references that might have it)
        by_execution_id: Dict[str, int] = {}
        for ref in pattern.source_references:
            # Use source_id as a proxy for execution grouping
            by_execution_id[ref.source_id] = by_execution_id.get(ref.source_id, 0) + 1

        # Time span
        earliest = pattern.quality.first_observed_at
        latest = pattern.quality.last_observed_at
        time_span = latest - earliest if latest > earliest else timedelta(0)

        return PatternEvidenceSummary(
            total_count=len(pattern.source_references),
            by_source_type=by_source_type,
            by_execution_id=by_execution_id,
            time_span=time_span,
            earliest_observation=earliest,
            latest_observation=latest,
        )

    def _build_score_breakdown(self, pattern: Pattern) -> PatternScoreBreakdown:
        """Build score breakdown from pattern quality metrics."""
        # Use pattern quality metrics directly
        # For patterns without full breakdown, infer from available metrics
        quality = pattern.quality

        return PatternScoreBreakdown(
            recurrence_score=min(quality.observation_count / 10.0, 1.0),  # Normalize to 0-1
            confidence_score=quality.confidence_score,
            stability_score=quality.stability_score,
            source_diversity_score=min(quality.distinct_source_count / 5.0, 1.0),  # Normalize
            temporal_consistency_score=quality.consistency_score,
            relevance_score=0.7,  # Default, could be computed from characteristics
        )

    def _build_lifecycle_history(
        self,
        pattern: Pattern,
        audit_records: List[PatternAuditRecord],
    ) -> List[PatternLifecycleHistoryEntry]:
        """Build lifecycle history from audit records."""
        # Filter records for this pattern
        pattern_records = [
            r for r in audit_records
            if r.pattern_id == pattern.id
        ]

        # Sort by timestamp
        pattern_records.sort(key=lambda r: r.timestamp)

        # Build history entries
        history = []
        for record in pattern_records:
            # Parse from_state and to_state from record details if available
            from_state = None
            to_state = None

            if record.from_state and record.to_state:
                from_state = record.from_state
                to_state = record.to_state

            history.append(PatternLifecycleHistoryEntry(
                timestamp=record.decided_at,
                from_state=from_state,
                to_state=to_state or pattern.lifecycle_state,
                reason=record.decision_reasoning,
                triggered_by=record.decided_by,
            ))

        return history

    def _build_supersession_info(self, pattern: Pattern) -> PatternSupersessionInfo:
        """Build supersession info from pattern."""
        is_superseded = pattern.lifecycle_state == PatternLifecycleState.SUPERSEDED

        superseded_by_id = None
        superseded_at = None
        superseded_by_name = None

        if is_superseded:
            # Extract supersession info from characteristics or metadata
            if pattern.characteristics:
                superseded_by_id = pattern.characteristics.get("superseded_by_id")
                superseded_at_str = pattern.characteristics.get("superseded_at")
                if superseded_at_str:
                    try:
                        superseded_at = datetime.fromisoformat(superseded_at_str)
                    except (ValueError, TypeError):
                        pass

            # Fetch superseding pattern if we have the ID
            if superseded_by_id:
                try:
                    if isinstance(superseded_by_id, str):
                        superseded_by_id = UUID(superseded_by_id)
                    superseding_pattern = self.query_service.get_by_id(superseded_by_id)
                    if superseding_pattern:
                        superseded_by_name = superseding_pattern.name
                except (ValueError, AttributeError):
                    pass

        return PatternSupersessionInfo(
            is_superseded=is_superseded,
            superseded_by=None,  # Could fetch full pattern if needed
            superseded_at=superseded_at,
            superseded_by_name=superseded_by_name,
            superseded_by_id=superseded_by_id,
        )


# ============================================================================
# Pattern Audit View
# ============================================================================

class PatternDecisionRecord:
    """Record of a pattern validation/promotion decision."""

    def __init__(
        self,
        decision_id: UUID,
        pattern_id: UUID,
        pattern_name: str,
        pattern_type: PatternType,
        decision: ValidationOutcome,
        timestamp: datetime,
        reasoning: str,
        passed_rules: List[str],
        failed_rules: List[str],
        triggered_by: Optional[str] = None,
    ):
        """Initialize decision record."""
        self.decision_id = decision_id
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.pattern_type = pattern_type
        self.decision = decision
        self.timestamp = timestamp
        self.reasoning = reasoning
        self.passed_rules = passed_rules
        self.failed_rules = failed_rules
        self.triggered_by = triggered_by


class PatternPromotionRecord:
    """Record of a pattern promotion event."""

    def __init__(
        self,
        promotion_id: UUID,
        pattern_id: UUID,
        pattern_name: str,
        from_state: PatternLifecycleState,
        to_state: PatternLifecycleState,
        timestamp: datetime,
        reason: str,
        forced: bool = False,
        triggered_by: Optional[str] = None,
    ):
        """Initialize promotion record."""
        self.promotion_id = promotion_id
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = timestamp
        self.reason = reason
        self.forced = forced
        self.triggered_by = triggered_by


class PatternSupersessionRecord:
    """Record of a pattern supersession event."""

    def __init__(
        self,
        supersession_id: UUID,
        superseded_pattern_id: UUID,
        superseded_pattern_name: str,
        superseding_pattern_id: UUID,
        superseding_pattern_name: str,
        timestamp: datetime,
        similarity_score: float,
        reason: str,
    ):
        """Initialize supersession record."""
        self.supersession_id = supersession_id
        self.superseded_pattern_id = superseded_pattern_id
        self.superseded_pattern_name = superseded_pattern_name
        self.superseding_pattern_id = superseding_pattern_id
        self.superseding_pattern_name = superseding_pattern_name
        self.timestamp = timestamp
        self.similarity_score = similarity_score
        self.reason = reason


class PatternAuditView:
    """
    Audit view for pattern governance and compliance.

    Provides visibility into:
    - Why patterns were promoted/rejected/held
    - What evidence contributed to decisions
    - What validator rules passed/failed
    - Supersession and merge logic
    """

    def __init__(
        self,
        pattern_id: UUID,
        pattern_name: str,
        decisions: List[PatternDecisionRecord],
        promotions: List[PatternPromotionRecord],
        supersessions: List[PatternSupersessionRecord],
        all_audit_records: List[PatternAuditRecord],
    ):
        """Initialize audit view."""
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.decisions = decisions
        self.promotions = promotions
        self.supersessions = supersessions
        self.all_audit_records = all_audit_records

    def get_decision_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of all decisions."""
        events = []

        for decision in self.decisions:
            events.append({
                "timestamp": decision.timestamp,
                "type": "decision",
                "outcome": decision.decision.value,
                "reasoning": decision.reasoning,
                "passed_rules": len(decision.passed_rules),
                "failed_rules": len(decision.failed_rules),
            })

        for promotion in self.promotions:
            events.append({
                "timestamp": promotion.timestamp,
                "type": "promotion",
                "from_state": promotion.from_state.value,
                "to_state": promotion.to_state.value,
                "reason": promotion.reason,
                "forced": promotion.forced,
            })

        for supersession in self.supersessions:
            events.append({
                "timestamp": supersession.timestamp,
                "type": "supersession",
                "superseded_by": supersession.superseding_pattern_name,
                "similarity": supersession.similarity_score,
                "reason": supersession.reason,
            })

        events.sort(key=lambda e: e["timestamp"])
        return events

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation outcomes."""
        total_decisions = len(self.decisions)

        if not total_decisions:
            return {
                "total_decisions": 0,
                "promoted": 0,
                "rejected": 0,
                "held": 0,
                "superseded": 0,
                "promotion_rate": 0.0,
            }

        promoted = sum(1 for d in self.decisions if d.decision == ValidationOutcome.PROMOTE)
        rejected = sum(1 for d in self.decisions if d.decision == ValidationOutcome.REJECT)
        held = sum(1 for d in self.decisions if d.decision == ValidationOutcome.HOLD)
        superseded = sum(1 for d in self.decisions if d.decision == ValidationOutcome.SUPERSEDED)

        return {
            "total_decisions": total_decisions,
            "promoted": promoted,
            "rejected": rejected,
            "held": held,
            "superseded": superseded,
            "promotion_rate": promoted / total_decisions if total_decisions > 0 else 0.0,
        }

    def get_failed_rules_summary(self) -> Dict[str, int]:
        """Get summary of most frequently failed rules."""
        rule_counts: Dict[str, int] = {}

        for decision in self.decisions:
            for rule in decision.failed_rules:
                rule_counts[rule] = rule_counts.get(rule, 0) + 1

        return dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True))


# ============================================================================
# Pattern Audit Service
# ============================================================================

class PatternAuditService:
    """
    Service for accessing and analyzing pattern audit trails.

    Provides audit views for compliance, governance, and analysis.
    """

    def __init__(
        self,
        query_service: Optional[PatternQueryService] = None,
    ):
        """Initialize the audit service."""
        self.query_service = query_service or PatternQueryService()

    def get_audit_view(
        self,
        pattern_id: UUID,
    ) -> Optional[PatternAuditView]:
        """
        Get audit view for a specific pattern.

        Args:
            pattern_id: Pattern ID

        Returns:
            PatternAuditView if found, None otherwise
        """
        pattern = self.query_service.get_by_id(pattern_id)
        if not pattern:
            return None

        # Extract records from query service's audit storage
        audit_records = getattr(self.query_service, "_audit_records", [])

        # Filter records for this pattern
        pattern_records = [
            r for r in audit_records
            if r.pattern_id == pattern_id
        ]

        # Build decision records
        decisions = []
        promotions = []
        supersessions = []

        for record in pattern_records:
            action_str = record.action if isinstance(record.action, str) else record.action.value

            if action_str in ("validated_promote", "validated_reject", "validated_hold"):
                # Parse decision from record
                decision = self._parse_decision_record(record, pattern)
                if decision:
                    decisions.append(decision)

            elif action_str.startswith("promoted_to_"):
                promotion = self._parse_promotion_record(record, pattern)
                if promotion:
                    promotions.append(promotion)

            elif action_str == "superseded":
                supersession = self._parse_supersession_record(record, pattern)
                if supersession:
                    supersessions.append(supersession)

        return PatternAuditView(
            pattern_id=pattern_id,
            pattern_name=pattern.name,
            decisions=decisions,
            promotions=promotions,
            supersessions=supersessions,
            all_audit_records=pattern_records,
        )

    def _parse_decision_record(
        self,
        record: PatternAuditRecord,
        pattern: Pattern,
    ) -> Optional[PatternDecisionRecord]:
        """Parse a decision record from an audit record."""
        # Determine outcome from action
        action_str = record.action if isinstance(record.action, str) else record.action.value

        outcome_map = {
            "validated_promote": ValidationOutcome.PROMOTE,
            "validated_reject": ValidationOutcome.REJECT,
            "validated_hold": ValidationOutcome.HOLD,
        }

        outcome = outcome_map.get(action_str)

        if not outcome:
            return None

        # Parse passed/failed rules from decision if available
        passed_rules = []
        failed_rules = []

        # This would be stored in the record details in a real implementation
        # For now, use placeholder
        if outcome == ValidationOutcome.PROMOTE:
            passed_rules = ["All validation rules passed"]
        else:
            failed_rules = [record.decision_reasoning]

        return PatternDecisionRecord(
            decision_id=record.id,
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            decision=outcome,
            timestamp=record.decided_at,
            reasoning=record.decision_reasoning,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            triggered_by=record.decided_by,
        )

    def _parse_promotion_record(
        self,
        record: PatternAuditRecord,
        pattern: Pattern,
    ) -> Optional[PatternPromotionRecord]:
        """Parse a promotion record from an audit record."""
        if not record.from_state or not record.to_state:
            return None

        return PatternPromotionRecord(
            promotion_id=record.id,
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            from_state=record.from_state,
            to_state=record.to_state,
            timestamp=record.decided_at,
            reason=record.decision_reasoning,
            forced=False,  # Would be stored in record details
            triggered_by=record.decided_by,
        )

    def _parse_supersession_record(
        self,
        record: PatternAuditRecord,
        pattern: Pattern,
    ) -> Optional[PatternSupersessionRecord]:
        """Parse a supersession record from an audit record."""
        # This would be stored in record details in a real implementation
        # For now, skip
        return None

    def get_compliance_report(
        self,
        pattern_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for patterns.

        Args:
            pattern_ids: Optional list of pattern IDs to include

        Returns:
            Compliance report with decision statistics
        """
        if pattern_ids:
            patterns = self.query_service.get_by_ids(pattern_ids)
        else:
            # Get all patterns
            all_results = self.query_service.query(page_size=10000)
            patterns = all_results.patterns

        audit_records = getattr(self.query_service, "_audit_records", [])

        # Filter records for specified patterns
        pattern_ids_set = {p.id for p in patterns}
        filtered_records = [
            r for r in audit_records
            if r.pattern_id in pattern_ids_set
        ]

        # Count outcomes
        promoted = sum(1 for r in filtered_records if "promote" in r.action)
        rejected = sum(1 for r in filtered_records if "reject" in r.action)
        held = sum(1 for r in filtered_records if "hold" in r.action)

        total = len(filtered_records)

        return {
            "total_patterns": len(patterns),
            "total_decisions": total,
            "promoted": promoted,
            "rejected": rejected,
            "held": held,
            "promotion_rate": promoted / total if total > 0 else 0.0,
            "rejection_rate": rejected / total if total > 0 else 0.0,
            "hold_rate": held / total if total > 0 else 0.0,
        }

    def get_audit_trail(
        self,
        limit: int = 100,
    ) -> List[PatternAuditRecord]:
        """
        Get the recent audit trail.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent audit records
        """
        audit_records = getattr(self.query_service, "_audit_records", [])

        # Sort by timestamp descending
        sorted_records = sorted(audit_records, key=lambda r: r.timestamp, reverse=True)

        return sorted_records[:limit]


# ============================================================================
# Pattern Governance Service
# ============================================================================

class GovernanceAction:
    """Types of governance actions."""

    ARCHIVE = "archive"
    SUPPERSEDE = "supersede"
    REVALIDATE = "revalidate"
    DISABLE_TYPE = "disable_type"
    ENABLE_TYPE = "enable_type"


class GovernanceActionResult:
    """Result of a governance action."""

    def __init__(
        self,
        success: bool,
        action: str,
        pattern_id: Optional[UUID] = None,
        pattern_name: Optional[str] = None,
        message: str = "",
        previous_state: Optional[PatternLifecycleState] = None,
        new_state: Optional[PatternLifecycleState] = None,
    ):
        """Initialize action result."""
        self.success = success
        self.action = action
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.message = message
        self.previous_state = previous_state
        self.new_state = new_state


class PatternGovernanceService:
    """
    Service for pattern governance and control operations.

    Provides:
    - Archive patterns
    - Supersede patterns
    - Revalidate patterns
    - Disable/enable pattern types
    - Inspect stale/weak patterns
    """

    def __init__(
        self,
        query_service: Optional[PatternQueryService] = None,
        audit_service: Optional[PatternAuditService] = None,
    ):
        """Initialize the governance service."""
        self.query_service = query_service or PatternQueryService()
        self.audit_service = audit_service or PatternAuditService(self.query_service)
        self._disabled_pattern_types: Set[PatternType] = set()

    def archive_pattern(
        self,
        pattern_id: UUID,
        reason: str,
        triggered_by: Optional[str] = None,
    ) -> GovernanceActionResult:
        """
        Archive a pattern.

        Args:
            pattern_id: Pattern ID to archive
            reason: Reason for archiving
            triggered_by: Optional user/system that triggered the action

        Returns:
            GovernanceActionResult with outcome
        """
        pattern = self.query_service.get_by_id(pattern_id)

        if not pattern:
            return GovernanceActionResult(
                success=False,
                action=GovernanceAction.ARCHIVE,
                pattern_id=pattern_id,
                message=f"Pattern {pattern_id} not found",
            )

        if pattern.lifecycle_state == PatternLifecycleState.ARCHIVED:
            return GovernanceActionResult(
                success=False,
                action=GovernanceAction.ARCHIVE,
                pattern_id=pattern_id,
                pattern_name=pattern.name,
                message="Pattern is already archived",
                previous_state=PatternLifecycleState.ARCHIVED,
                new_state=PatternLifecycleState.ARCHIVED,
            )

        # Create archived version
        archived_pattern = Pattern(
            id=pattern.id,
            pattern_type=pattern.pattern_type,
            name=pattern.name,
            description=pattern.description,
            domain=pattern.domain,
            scope=pattern.scope,
            structure=pattern.structure,
            characteristics={
                **(pattern.characteristics or {}),
                "archived_at": datetime.now().isoformat(),
                "archived_reason": reason,
            },
            tags=pattern.tags,
            source_references=pattern.source_references,
            quality=pattern.quality,
            lifecycle_state=PatternLifecycleState.ARCHIVED,
            superseded_by_id=pattern.superseded_by_id,
            superseded_at=pattern.superseded_at,
        )

        # Update in query service
        self.query_service.add_pattern(archived_pattern)

        # Log audit record
        audit_record = PatternAuditRecord(
            id=uuid4(),
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            action="archived",
            decision_reasoning=f"Archived: {reason}",
            decided_at=datetime.now(),
            decided_by=triggered_by or "governance_service",
        )
        self.query_service.add_audit_record(audit_record)

        return GovernanceActionResult(
            success=True,
            action=GovernanceAction.ARCHIVE,
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            message=f"Pattern archived: {reason}",
            previous_state=pattern.lifecycle_state,
            new_state=PatternLifecycleState.ARCHIVED,
        )

    def supersede_pattern(
        self,
        old_pattern_id: UUID,
        new_pattern_id: UUID,
        reason: str,
        triggered_by: Optional[str] = None,
    ) -> GovernanceActionResult:
        """
        Mark a pattern as superseded by a newer pattern.

        Args:
            old_pattern_id: Pattern ID to supersede
            new_pattern_id: Pattern ID that supersedes
            reason: Reason for supersession
            triggered_by: Optional user/system that triggered the action

        Returns:
            GovernanceActionResult with outcome
        """
        old_pattern = self.query_service.get_by_id(old_pattern_id)
        new_pattern = self.query_service.get_by_id(new_pattern_id)

        if not old_pattern:
            return GovernanceActionResult(
                success=False,
                action=GovernanceAction.SUPPERSEDE,
                pattern_id=old_pattern_id,
                message=f"Old pattern {old_pattern_id} not found",
            )

        if not new_pattern:
            return GovernanceActionResult(
                success=False,
                action=GovernanceAction.SUPPERSEDE,
                pattern_id=old_pattern_id,
                message=f"New pattern {new_pattern_id} not found",
            )

        # Create superseded version
        superseded_pattern = Pattern(
            id=old_pattern.id,
            pattern_type=old_pattern.pattern_type,
            name=old_pattern.name,
            description=old_pattern.description,
            domain=old_pattern.domain,
            scope=old_pattern.scope,
            structure=old_pattern.structure,
            characteristics={
                **(old_pattern.characteristics or {}),
                "superseded_by_id": str(new_pattern.id),
                "superseded_at": datetime.now().isoformat(),
                "superseded_reason": reason,
            },
            tags=old_pattern.tags,
            source_references=old_pattern.source_references,
            quality=old_pattern.quality,
            lifecycle_state=PatternLifecycleState.SUPERSEDED,
            superseded_by_id=new_pattern.id,
            superseded_at=datetime.now(),
        )

        # Update in query service
        self.query_service.add_pattern(superseded_pattern)

        # Log audit record for old pattern
        audit_record = PatternAuditRecord(
            id=uuid4(),
            pattern_id=old_pattern.id,
            pattern_name=old_pattern.name,
            pattern_type=old_pattern.pattern_type,
            action="superseded",
            decision_reasoning=f"Superseded by {new_pattern.name}: {reason}",
            decided_at=datetime.now(),
            decided_by=triggered_by or "governance_service",
        )
        self.query_service.add_audit_record(audit_record)

        return GovernanceActionResult(
            success=True,
            action=GovernanceAction.SUPPERSEDE,
            pattern_id=old_pattern.id,
            pattern_name=old_pattern.name,
            message=f"Pattern superseded by {new_pattern.name}: {reason}",
            previous_state=old_pattern.lifecycle_state,
            new_state=PatternLifecycleState.SUPERSEDED,
        )

    def revalidate_pattern(
        self,
        pattern_id: UUID,
        triggered_by: Optional[str] = None,
    ) -> Tuple[GovernanceActionResult, Optional[ValidationResult]]:
        """
        Revalidate a pattern against current governance rules.

        Args:
            pattern_id: Pattern ID to revalidate
            triggered_by: Optional user/system that triggered the action

        Returns:
            Tuple of (GovernanceActionResult, ValidationResult)
        """
        from .validation import PatternValidationService

        pattern = self.query_service.get_by_id(pattern_id)

        if not pattern:
            return (
                GovernanceActionResult(
                    success=False,
                    action=GovernanceAction.REVALIDATE,
                    pattern_id=pattern_id,
                    message=f"Pattern {pattern_id} not found",
                ),
                None,
            )

        # Create a candidate from the pattern for revalidation
        candidate = PatternCandidate(
            id=pattern.id,
            pattern_type=pattern.pattern_type,
            name=pattern.name,
            description=pattern.description,
            domain=pattern.domain,
            scope=pattern.scope,
            structure=pattern.structure,
            characteristics=pattern.characteristics or {},
            tags=pattern.tags or [],
            evidence=[],  # Evidence would need to be reconstructed
            source_references=pattern.source_references,
            lifecycle_state=pattern.lifecycle_state,
            quality=pattern.quality,
        )

        # Revalidate
        validation_service = PatternValidationService()
        result = validation_service.validate_candidate(candidate)

        # Log audit record
        audit_record = PatternAuditRecord(
            id=uuid4(),
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            action="revalidated",
            decision_reasoning=result.reasoning,
            decided_at=datetime.now(),
            decided_by=triggered_by or "governance_service",
        )
        self.query_service.add_audit_record(audit_record)

        return (
            GovernanceActionResult(
                success=True,
                action=GovernanceAction.REVALIDATE,
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                message=f"Revalidation complete: {result.outcome.value}",
            ),
            result,
        )

    def disable_pattern_type(
        self,
        pattern_type: PatternType,
        reason: str,
    ) -> GovernanceActionResult:
        """
        Disable a pattern type from being promoted.

        Args:
            pattern_type: Pattern type to disable
            reason: Reason for disabling

        Returns:
            GovernanceActionResult with outcome
        """
        self._disabled_pattern_types.add(pattern_type)

        return GovernanceActionResult(
            success=True,
            action=GovernanceAction.DISABLE_TYPE,
            message=f"Pattern type {pattern_type.value} disabled: {reason}",
        )

    def enable_pattern_type(
        self,
        pattern_type: PatternType,
    ) -> GovernanceActionResult:
        """
        Re-enable a disabled pattern type.

        Args:
            pattern_type: Pattern type to enable

        Returns:
            GovernanceActionResult with outcome
        """
        if pattern_type in self._disabled_pattern_types:
            self._disabled_pattern_types.remove(pattern_type)

        return GovernanceActionResult(
            success=True,
            action=GovernanceAction.ENABLE_TYPE,
            message=f"Pattern type {pattern_type.value} enabled",
        )

    def is_pattern_type_disabled(self, pattern_type: PatternType) -> bool:
        """Check if a pattern type is disabled."""
        return pattern_type in self._disabled_pattern_types

    def inspect_stale_patterns(
        self,
        days_threshold: int = 30,
        min_confidence: Optional[float] = None,
    ) -> List[Pattern]:
        """
        Get patterns that haven't been observed recently.

        Args:
            days_threshold: Days since last observation
            min_confidence: Optional minimum confidence filter

        Returns:
            List of stale patterns
        """
        stale_patterns = self.query_service.query_stale_patterns(days_threshold)

        if min_confidence is not None:
            stale_patterns = [
                p for p in stale_patterns
                if p.quality.confidence_score >= min_confidence
            ]

        return stale_patterns

    def inspect_weak_patterns(
        self,
        confidence_threshold: float = 0.5,
        observation_threshold: int = 3,
        lifecycle_states: Optional[List[PatternLifecycleState]] = None,
    ) -> List[Pattern]:
        """
        Get patterns below quality thresholds.

        Args:
            confidence_threshold: Maximum confidence score
            observation_threshold: Maximum observation count
            lifecycle_states: Optional lifecycle states to filter

        Returns:
            List of weak patterns
        """
        weak_patterns = self.query_service.query_weak_patterns(
            confidence_threshold,
            observation_threshold,
        )

        if lifecycle_states:
            weak_patterns = [
                p for p in weak_patterns
                if p.lifecycle_state in lifecycle_states
            ]

        return weak_patterns


# ============================================================================
# Convenience Functions
# ============================================================================

def create_pattern_query_service() -> PatternQueryService:
    """Create a new pattern query service."""
    return PatternQueryService()


def create_pattern_inspection_service(
    query_service: Optional[PatternQueryService] = None,
) -> PatternInspectionService:
    """Create a new pattern inspection service."""
    return PatternInspectionService(query_service)


def create_pattern_audit_service(
    query_service: Optional[PatternQueryService] = None,
) -> PatternAuditService:
    """Create a new pattern audit service."""
    return PatternAuditService(query_service)


def create_pattern_governance_service(
    query_service: Optional[PatternQueryService] = None,
    audit_service: Optional[PatternAuditService] = None,
) -> PatternGovernanceService:
    """Create a new pattern governance service."""
    return PatternGovernanceService(query_service, audit_service)


# Export all public classes and functions
__all__ = [
    # Query
    "PatternQueryFilter",
    "PatternQuerySort",
    "PatternQueryResult",
    "PatternQueryService",

    # Inspection
    "PatternEvidenceSummary",
    "PatternScoreBreakdown",
    "PatternLifecycleHistoryEntry",
    "PatternSupersessionInfo",
    "PatternInspectionView",
    "PatternInspectionService",

    # Audit
    "PatternDecisionRecord",
    "PatternPromotionRecord",
    "PatternSupersessionRecord",
    "PatternAuditView",
    "PatternAuditService",

    # Governance
    "GovernanceAction",
    "GovernanceActionResult",
    "PatternGovernanceService",

    # Convenience Functions
    "create_pattern_query_service",
    "create_pattern_inspection_service",
    "create_pattern_audit_service",
    "create_pattern_governance_service",
]
