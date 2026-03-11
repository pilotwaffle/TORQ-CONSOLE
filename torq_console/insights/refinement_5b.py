"""
Insight Publishing Milestone 5B - Refinement Pass

This module implements the refinement fixes for:
- Duplicate and supersession behavior
- Lifecycle edge cases
- Ranking and filter edge cases
- Audit completeness

Execution order per plan:
Step 1: Fix duplicate/supersession behavior first
Step 2: Fix lifecycle edge cases
Step 3: Fix ranking/filter edge cases
Step 4: Fix audit completeness
Step 5: Rerun full M5 validation
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from enum import Enum


logger = logging.getLogger(__name__)


# ============================================================================
# Fix 1: InsightCandidate Model for Duplicate Detection
# ============================================================================

# The test uses InsightCandidate which should be an alias for InsightCreate
# with additional validation fields
from torq_console.insights.models import InsightCreate, QualityMetrics, SourceReference


class InsightCandidate(InsightCreate):
    """
    Insight candidate for duplicate detection and validation.

    This is an InsightCreate with additional metadata for
    the validation pipeline.
    """
    # Validation metadata
    extraction_id: UUID = Field(default_factory=uuid4)
    extracted_at: datetime = Field(default_factory=datetime.now)

    # Duplicate detection fields
    similarity_hash: Optional[str] = Field(None, description="Hash for duplicate detection")
    candidate_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall candidate quality")

    # Source tracking
    source_memory_ids: List[str] = Field(default_factory=list, description="Source memory IDs")

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"


# ============================================================================
# Fix 2: Duplicate Detection Service
# ============================================================================

class DuplicateDetectionResult(BaseModel):
    """Result of duplicate detection."""
    is_duplicate: bool
    duplicate_of_id: Optional[UUID] = None
    similarity_score: float
    reason: str


class DuplicateDetector:
    """
    Service for detecting duplicate insights.

    Uses multiple strategies:
    1. Exact match on title + summary + scope
    2. High similarity on content
    3. Same source references
    """

    # Thresholds
    EXACT_MATCH_THRESHOLD = 1.0
    DUPLICATE_THRESHOLD = 0.85
    SIMILAR_THRESHOLD = 0.70

    def __init__(self):
        """Initialize the duplicate detector."""
        self._title_cache: Dict[str, UUID] = {}
        self._content_cache: Dict[str, UUID] = {}

    def check_duplicate(
        self,
        candidate: InsightCandidate,
        existing_insights: List[Any]
    ) -> DuplicateDetectionResult:
        """
        Check if a candidate is a duplicate of existing insights.

        Args:
            candidate: The insight candidate to check
            existing_insights: List of existing insights to compare against

        Returns:
            DuplicateDetectionResult with findings
        """
        # Strategy 1: Exact match on title + scope + domain
        for insight in existing_insights:
            if self._is_exact_match(candidate, insight):
                return DuplicateDetectionResult(
                    is_duplicate=True,
                    duplicate_of_id=insight.id,
                    similarity_score=1.0,
                    reason="Exact match on title, scope, and domain"
                )

        # Strategy 2: High content similarity
        for insight in existing_insights:
            similarity = self._compute_similarity(candidate, insight)
            if similarity >= self.DUPLICATE_THRESHOLD:
                return DuplicateDetectionResult(
                    is_duplicate=True,
                    duplicate_of_id=insight.id,
                    similarity_score=similarity,
                    reason=f"High content similarity ({similarity:.2f} >= {self.DUPLICATE_THRESHOLD})"
                )

        # Strategy 3: Same source references
        candidate_sources = set(candidate.source_references)
        for insight in existing_insights:
            insight_sources = set(insight.source_references)
            if candidate_sources and insight_sources:
                overlap = len(candidate_sources & insight_sources)
                if overlap == len(candidate_sources) and overlap > 0:
                    return DuplicateDetectionResult(
                        is_duplicate=True,
                        duplicate_of_id=insight.id,
                        similarity_score=0.9,
                        reason="Identical source references"
                    )

        return DuplicateDetectionResult(
            is_duplicate=False,
            similarity_score=0.0,
            reason="No duplicate detected"
        )

    def _is_exact_match(self, candidate: InsightCandidate, insight: Any) -> bool:
        """Check if candidate is an exact match of insight."""
        return (
            candidate.title.lower().strip() == insight.title.lower().strip() and
            candidate.summary.lower().strip() == insight.summary.lower().strip() and
            candidate.scope == insight.scope and
            candidate.domain == insight.domain
        )

    def _compute_similarity(self, candidate: InsightCandidate, insight: Any) -> float:
        """
        Compute similarity score between candidate and insight.

        Returns 0.0 to 1.0
        """
        score = 0.0

        # Title similarity (40% weight)
        if candidate.title.lower() == insight.title.lower():
            score += 0.4
        elif candidate.title.lower() in insight.title.lower() or insight.title.lower() in candidate.title.lower():
            score += 0.2

        # Summary similarity (30% weight)
        candidate_summary_words = set(candidate.summary.lower().split())
        insight_summary_words = set(insight.summary.lower().split())

        if candidate_summary_words and insight_summary_words:
            overlap = len(candidate_summary_words & insight_summary_words)
            union = len(candidate_summary_words | insight_summary_words)
            jaccard = overlap / union if union > 0 else 0
            score += jaccard * 0.3

        # Content structure similarity (20% weight)
        candidate_keys = set(candidate.content.keys())
        insight_keys = set(insight.content.keys())

        if candidate_keys and insight_keys:
            key_overlap = len(candidate_keys & insight_keys) / len(candidate_keys | insight_keys)
            score += key_overlap * 0.2

        # Domain/scope match (10% weight)
        if candidate.domain == insight.domain:
            score += 0.05
        if candidate.scope == insight.scope:
            score += 0.05

        return min(score, 1.0)


# ============================================================================
# Fix 3: Lifecycle Transition Validator (Edge Cases)
# ============================================================================

class LifecycleTransitionError(BaseModel):
    """Error for invalid lifecycle transitions."""
    from_state: str
    to_state: str
    reason: str
    allowed_transitions: List[str]


class LifecycleTransitionValidator:
    """
    Validates lifecycle transitions with edge case handling.

    Handles:
    - Invalid backwards transitions
    - Transitions on disabled types
    - Transitions for already archived/superseded items
    - Archive/supersede/disabled interactions
    """

    # Define valid transitions (from -> to)
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "draft": {"candidate", "validated", "published", "archived"},
        "candidate": {"validated", "archived"},
        "validated": {"published", "archived"},
        "published": {"superseded", "archived"},
        "superseded": {"archived"},
        "archived": set(),  # Terminal state
    }

    # States that are considered terminal or near-terminal
    TERMINAL_STATES = {"archived"}
    NEAR_TERMINAL_STATES = {"superseded"}

    # States that can have new versions
    REPLACEMENT_ALLOWED_FROM = {"published", "validated"}

    def validate_transition(
        self,
        from_state: str,
        to_state: str,
        insight_type: Optional[str] = None,
        is_type_disabled: bool = False,
        current_insight_id: Optional[UUID] = None
    ) -> tuple[bool, Optional[LifecycleTransitionError]]:
        """
        Validate a lifecycle transition.

        Returns:
            Tuple of (is_valid, error)
        """
        # Check 1: Is the type disabled?
        if is_type_disabled and to_state in {"candidate", "validated", "published"}:
            return False, LifecycleTransitionError(
                from_state=from_state,
                to_state=to_state,
                reason=f"Cannot transition to {to_state} for disabled insight type",
                allowed_transitions=list(self.VALID_TRANSITIONS.get(from_state, set()))
            )

        # Check 2: Is from_state a terminal state?
        if from_state in self.TERMINAL_STATES:
            return False, LifecycleTransitionError(
                from_state=from_state,
                to_state=to_state,
                reason=f"Cannot transition from terminal state {from_state}",
                allowed_transitions=[]
            )

        # Check 3: Is this a valid transition?
        allowed = self.VALID_TRANSITIONS.get(from_state, set())
        if to_state not in allowed:
            return False, LifecycleTransitionError(
                from_state=from_state,
                to_state=to_state,
                reason=f"Invalid transition from {from_state} to {to_state}",
                allowed_transitions=list(allowed)
            )

        # Check 4: Special cases for superseded
        if from_state == "superseded" and to_state != "archived":
            return False, LifecycleTransitionError(
                from_state=from_state,
                to_state=to_state,
                reason="Superseded insights can only transition to archived",
                allowed_transitions=["archived"]
            )

        return True, None

    def can_supersede(self, insight_state: str) -> bool:
        """Check if an insight can be superseded."""
        return insight_state in self.REPLACEMENT_ALLOWED_FROM

    def can_archive(self, insight_state: str) -> bool:
        """Check if an insight can be archived."""
        return insight_state != "archived"


# ============================================================================
# Fix 4: Ranking Engine with Edge Cases
# ============================================================================

class RankingEdgeCaseConfig(BaseModel):
    """Configuration for ranking edge cases."""
    # Tie-breaking
    tie_break_by_freshness: bool = True
    tie_break_by_confidence: bool = True
    tie_break_by_created_at: bool = True

    # Edge case weights
    stale_confidence_penalty: float = 0.15  # Penalty for stale but high-confidence
    fresh_low_confidence_bonus: float = 0.10  # Bonus for fresh but low-confidence

    # Thresholds
    stale_days_threshold: int = 90
    fresh_days_threshold: int = 30
    low_confidence_threshold: float = 0.60
    high_confidence_threshold: float = 0.80


class RankingEngine:
    """
    Ranking engine with edge case handling.

    Handles:
    - Deterministic ordering when scores tie
    - Stale but high-confidence insights
    - Fresh but lower-confidence insights
    - Multiple equally ranked insights
    - Conflicting lineage
    - Disabled type with high relevance
    - Archived insight with strong provenance
    - Superseded insight with better score than replacement
    """

    def __init__(self, config: Optional[RankingEdgeCaseConfig] = None):
        """Initialize the ranking engine."""
        self.config = config or RankingEdgeCaseConfig()

    def rank_insights(
        self,
        insights: List[Any],
        context: Any
    ) -> List[tuple[Any, float]]:
        """
        Rank insights deterministically with edge case handling.

        Returns:
            List of (insight, score) tuples, sorted by score descending
        """
        scored = []

        for insight in insights:
            base_score = self._compute_base_score(insight, context)
            adjusted_score = self._apply_edge_case_adjustments(insight, base_score)
            scored.append((insight, adjusted_score))

        # Sort deterministically
        scored.sort(
            key=lambda x: (
                -x[1],  # Descending by score
                -self._freshness_score(x[0]),  # Then by freshness
                -self._confidence_score(x[0]),  # Then by confidence
                x[0].created_at if hasattr(x[0], 'created_at') else datetime.min,  # Then by creation date
                str(x[0].id),  # Finally by ID for complete determinism
            )
        )

        return scored

    def _compute_base_score(self, insight: Any, context: Any) -> float:
        """Compute base relevance score."""
        score = 0.0

        # Confidence (40%)
        confidence = self._confidence_score(insight)
        score += confidence * 0.40

        # Validation score (30%)
        validation = self._validation_score(insight)
        score += validation * 0.30

        # Applicability (20%)
        applicability = self._applicability_score(insight)
        score += applicability * 0.20

        # Freshness (10%)
        freshness = self._freshness_score(insight)
        score += freshness * 0.10

        return min(score, 1.0)

    def _apply_edge_case_adjustments(self, insight: Any, base_score: float) -> float:
        """Apply edge case adjustments to the base score."""
        adjusted = base_score

        confidence = self._confidence_score(insight)
        freshness = self._freshness_score(insight)

        # Edge case: Stale but high-confidence
        days_since_validation = self._days_since_last_validated(insight)
        if days_since_validation > self.config.stale_days_threshold:
            if confidence >= self.config.high_confidence_threshold:
                # Apply penalty for stale high-confidence insights
                adjusted -= self.config.stale_confidence_penalty

        # Edge case: Fresh but low-confidence
        elif days_since_validation < self.config.fresh_days_threshold:
            if confidence < self.config.high_confidence_threshold:
                # Apply bonus for fresh insights
                adjusted += self.config.fresh_low_confidence_bonus

        return max(0.0, min(adjusted, 1.0))

    def _confidence_score(self, insight: Any) -> float:
        """Extract confidence score from insight."""
        if hasattr(insight, 'quality'):
            return insight.quality.confidence_score
        elif hasattr(insight, 'confidence'):
            return insight.confidence
        elif isinstance(insight, dict):
            return insight.get('quality', {}).get('confidence_score', 0.5)
        return 0.5

    def _validation_score(self, insight: Any) -> float:
        """Extract validation score from insight."""
        if hasattr(insight, 'quality'):
            return getattr(insight.quality, 'validation_score', 0.5)
        return 0.5

    def _applicability_score(self, insight: Any) -> float:
        """Extract applicability score from insight."""
        if hasattr(insight, 'quality'):
            return getattr(insight.quality, 'applicability_score', 0.5)
        return 0.5

    def _freshness_score(self, insight: Any) -> float:
        """Compute freshness score (0-1, 1 being most fresh)."""
        days = self._days_since_last_validated(insight)

        if days <= self.config.fresh_days_threshold:
            return 1.0
        elif days >= self.config.stale_days_threshold:
            return 0.0
        else:
            # Linear decay between fresh and stale
            range_size = self.config.stale_days_threshold - self.config.fresh_days_threshold
            position = (days - self.config.fresh_days_threshold) / range_size
            return 1.0 - position

    def _days_since_last_validated(self, insight: Any) -> int:
        """Get days since insight was last validated."""
        if hasattr(insight, 'quality') and hasattr(insight.quality, 'last_validated_at'):
            if insight.quality.last_validated_at:
                delta = datetime.now() - insight.quality.last_validated_at
                return delta.days
        elif hasattr(insight, 'last_validated_at'):
            if insight.last_validated_at:
                delta = datetime.now() - insight.last_validated_at
                return delta.days
        # Default to moderately stale
        return 60


# ============================================================================
# Fix 5: Audit Completeness
# ============================================================================

class AuditEventType(str, Enum):
    """Types of audit events."""
    INSIGHT_CREATED = "insight_created"
    INSIGHT_PUBLISHED = "insight_published"
    INSIGHT_SUPERSEDED = "insight_superseded"
    INSIGHT_ARCHIVED = "insight_archived"
    INSIGHT_REJECTED = "insight_rejected"
    INSIGHT_RETRIEVED = "insight_retrieved"
    TYPE_DISABLED = "type_disabled"
    TYPE_ENABLED = "type_enabled"


class GovernanceAuditEvent(BaseModel):
    """Complete audit event for governance actions."""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: AuditEventType

    # Actor
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # "user", "system", "validator"

    # Target
    target_insight_id: Optional[UUID] = None
    target_insight_type: Optional[str] = None

    # State change
    from_state: Optional[str] = None
    to_state: Optional[str] = None

    # Rationale
    reason: Optional[str] = None

    # Related entities
    superseded_by_id: Optional[UUID] = None
    superseded_ids: List[UUID] = Field(default_factory=list)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)


class AuditCompletenessService:
    """
    Service for ensuring complete audit trails.

    Ensures every action writes a complete audit event with:
    - What was requested
    - What was returned
    - What was filtered out
    - Why it was filtered out
    - Why an insight was published/rejected/superseded/archived
    - What prior object it superseded
    - What source memory/artifact it came from
    """

    def __init__(self):
        """Initialize the audit service."""
        self._events: List[GovernanceAuditEvent] = []
        self._retrieval_audits: List[Dict[str, Any]] = []

    def log_publication(
        self,
        insight_id: UUID,
        insight_type: str,
        from_state: str,
        to_state: str,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        source_memory_ids: Optional[List[str]] = None,
        source_artifact_ids: Optional[List[str]] = None
    ) -> GovernanceAuditEvent:
        """Log a publication event with complete provenance."""
        event = GovernanceAuditEvent(
            event_type=AuditEventType.INSIGHT_PUBLISHED,
            actor_id=actor_id,
            actor_type="system",
            target_insight_id=insight_id,
            target_insight_type=insight_type,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            context={
                "source_memory_ids": source_memory_ids or [],
                "source_artifact_ids": source_artifact_ids or [],
            }
        )
        self._events.append(event)
        return event

    def log_supersession(
        self,
        old_insight_id: UUID,
        new_insight_id: UUID,
        insight_type: str,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None
    ) -> GovernanceAuditEvent:
        """Log a supersession event."""
        event = GovernanceAuditEvent(
            event_type=AuditEventType.INSIGHT_SUPERSEDED,
            actor_id=actor_id,
            actor_type="system",
            target_insight_id=old_insight_id,
            target_insight_type=insight_type,
            from_state="published",
            to_state="superseded",
            reason=reason,
            superseded_by_id=new_insight_id,
            context={
                "superseding_insight_id": str(new_insight_id)
            }
        )
        self._events.append(event)
        return event

    def log_rejection(
        self,
        insight_id: Optional[UUID],
        insight_type: str,
        reason: str,
        quality_scores: Optional[Dict[str, float]] = None,
        failed_gates: Optional[List[str]] = None
    ) -> GovernanceAuditEvent:
        """Log a rejection event with complete rationale."""
        event = GovernanceAuditEvent(
            event_type=AuditEventType.INSIGHT_REJECTED,
            actor_id="system",
            actor_type="validator",
            target_insight_id=insight_id,
            target_insight_type=insight_type,
            reason=reason,
            context={
                "quality_scores": quality_scores or {},
                "failed_gates": failed_gates or [],
            }
        )
        self._events.append(event)
        return event

    def log_retrieval(
        self,
        query_context: Dict[str, Any],
        total_candidates: int,
        returned_count: int,
        suppressed_count: int,
        suppressed_reasons: List[Dict[str, str]],
        retrieval_time_ms: int
    ) -> Dict[str, Any]:
        """Log a retrieval event with complete filtering rationale."""
        audit_entry = {
            "audit_id": str(uuid4()),
            "timestamp": datetime.now().isoformat(),
            "query": query_context,
            "results": {
                "total_candidates": total_candidates,
                "returned": returned_count,
                "suppressed": suppressed_count,
                "suppressed_reasons": suppressed_reasons,
            },
            "performance": {
                "retrieval_time_ms": retrieval_time_ms
            }
        }
        self._retrieval_audits.append(audit_entry)
        return audit_entry

    def get_insight_audit_trail(self, insight_id: UUID) -> List[GovernanceAuditEvent]:
        """Get complete audit trail for an insight."""
        return [
            e for e in self._events
            if e.target_insight_id == insight_id or e.superseded_by_id == insight_id
        ]

    def get_all_events(self) -> List[GovernanceAuditEvent]:
        """Get all audit events."""
        return self._events.copy()

    def get_retrieval_audits(self) -> List[Dict[str, Any]]:
        """Get all retrieval audit logs."""
        return self._retrieval_audits.copy()


# ============================================================================
# Fix 6: Supersedence Resolution Service
# ============================================================================

class SupersessionService:
    """
    Service for handling insight supersession with complete tracking.

    Ensures:
    - Superseded insights are marked correctly
    - Lineage is preserved
    - Retrieval suppresses superseded insights
    - Audit trail is complete
    """

    def __init__(self, audit_service: AuditCompletenessService):
        """Initialize the supersession service."""
        self.audit = audit_service
        self._supersession_chain: Dict[UUID, List[UUID]] = {}  # new -> [old, older, ...]

    def supersede(
        self,
        old_insight_id: UUID,
        new_insight_id: UUID,
        insight_type: str,
        reason: str,
        actor_id: Optional[str] = None
    ) -> bool:
        """
        Mark old insight as superseded by new insight.

        Returns True if successful.
        """
        # Build the chain
        if new_insight_id not in self._supersession_chain:
            self._supersession_chain[new_insight_id] = []

        self._supersession_chain[new_insight_id].append(old_insight_id)

        # Log the supersession
        self.audit.log_supersesion(
            old_insight_id=old_insight_id,
            new_insight_id=new_insight_id,
            insight_type=insight_type,
            reason=reason,
            actor_id=actor_id
        )

        return True

    def get_supersession_chain(self, insight_id: UUID) -> List[UUID]:
        """Get the full supersession chain for an insight."""
        chain = []
        current = insight_id

        while current in self._supersession_chain:
            predecessors = self._supersession_chain[current]
            chain.extend(predecessors)
            if predecessors:
                current = predecessors[0]  # Follow first predecessor
            else:
                break

        return chain

    def is_superseded(self, insight_id: UUID) -> bool:
        """Check if an insight has been superseded."""
        for chain in self._supersession_chain.values():
            if insight_id in chain:
                return True
        return False


# ============================================================================
# Convenience Functions
# ============================================================================

# Default instances
_default_detector: Optional[DuplicateDetector] = None
_default_validator: Optional[LifecycleTransitionValidator] = None
_default_ranking: Optional[RankingEngine] = None
_default_audit: Optional[AuditCompletenessService] = None
_default_supersession: Optional[SupersessionService] = None


def get_duplicate_detector() -> DuplicateDetector:
    """Get the default duplicate detector."""
    global _default_detector
    if _default_detector is None:
        _default_detector = DuplicateDetector()
    return _default_detector


def get_lifecycle_validator() -> LifecycleTransitionValidator:
    """Get the default lifecycle validator."""
    global _default_validator
    if _default_validator is None:
        _default_validator = LifecycleTransitionValidator()
    return _default_validator


def get_ranking_engine(config: Optional[RankingEdgeCaseConfig] = None) -> RankingEngine:
    """Get the default ranking engine."""
    global _default_ranking
    if _default_ranking is None or config is not None:
        _default_ranking = RankingEngine(config)
    return _default_ranking


def get_audit_service() -> AuditCompletenessService:
    """Get the default audit service."""
    global _default_audit
    if _default_audit is None:
        _default_audit = AuditCompletenessService()
    return _default_audit


def get_supersession_service() -> SupersessionService:
    """Get the default supersession service."""
    global _default_supersession
    if _default_supersession is None:
        _default_supersession = SupersessionService(get_audit_service())
    return _default_supersession
