"""
TORQ Readiness Checker - Query Service

Milestone 4: Query interface for readiness objects.

Provides filtering, pagination, and retrieval of readiness candidates
and their evaluations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from .readiness_models import (
    ReadinessCandidate,
    ReadinessState,
    CandidateType,
    ReadinessEvaluation,
)
from .inspection_models import (
    CandidateListFilter,
    CandidateListItem,
    CandidateListResult,
)


logger = logging.getLogger(__name__)


# ============================================================================
# In-Memory Storage (would be database in production)
# ============================================================================

_candidates: Dict[UUID, ReadinessCandidate] = {}
_evaluations: Dict[UUID, List[ReadinessEvaluation]] = {}


def register_candidate(candidate: ReadinessCandidate) -> None:
    """Register a candidate for query."""
    _candidates[candidate.id] = candidate
    _evaluations[candidate.id] = []


def add_evaluation(candidate_id: UUID, evaluation: ReadinessEvaluation) -> None:
    """Add an evaluation for a candidate."""
    if candidate_id in _evaluations:
        _evaluations[candidate_id].append(evaluation)


def get_candidate_storage() -> Dict[UUID, ReadinessCandidate]:
    """Get all candidates (for testing)."""
    return _candidates.copy()


def clear_candidate_storage() -> None:
    """Clear all candidates (for testing)."""
    global _candidates, _evaluations
    _candidates = {}
    _evaluations = {}


def get_all_evaluations() -> Dict[UUID, List[ReadinessEvaluation]]:
    """Get all evaluations (for inspection service)."""
    return _evaluations.copy()


# ============================================================================
# Query Service
# ============================================================================

class ReadinessQueryService:
    """
    Query service for readiness candidates and evaluations.

    Provides filtering, pagination, and retrieval capabilities
    for the readiness system.
    """

    def get_candidate(self, candidate_id: UUID) -> Optional[ReadinessCandidate]:
        """
        Get a candidate by ID.

        Args:
            candidate_id: ID of the candidate

        Returns:
            ReadinessCandidate if found, None otherwise
        """
        return _candidates.get(candidate_id)

    def list_candidates(
        self,
        filters: Optional[CandidateListFilter] = None,
    ) -> CandidateListResult:
        """
        List candidates with optional filtering.

        Args:
            filters: Optional filter parameters

        Returns:
            CandidateListResult with matching candidates
        """
        if filters is None:
            filters = CandidateListFilter()

        # Start with all candidates
        candidates = list(_candidates.values())

        # Apply filters
        if filters.candidate_type:
            candidates = [
                c for c in candidates
                if c.candidate_type.value == filters.candidate_type
            ]

        if filters.state:
            candidates = [
                c for c in candidates
                if c.current_state.value == filters.state
            ]

        if filters.policy_profile:
            candidates = [
                c for c in candidates
                if c.policy_profile_id == filters.policy_profile
            ]

        if filters.min_score is not None:
            candidates = [
                c for c in candidates
                if self._get_latest_score(c.id) >= filters.min_score
            ]

        if filters.max_score is not None:
            candidates = [
                c for c in candidates
                if self._get_latest_score(c.id) <= filters.max_score
            ]

        if filters.created_after:
            candidates = [
                c for c in candidates
                if c.created_at >= filters.created_after
            ]

        if filters.updated_after:
            candidates = [
                c for c in candidates
                if c.updated_at >= filters.updated_after
            ]

        # Sort
        reverse = filters.sort_order.lower() == "desc"
        if filters.sort_by == "updated_at":
            candidates.sort(key=lambda c: c.updated_at, reverse=reverse)
        elif filters.sort_by == "created_at":
            candidates.sort(key=lambda c: c.created_at, reverse=reverse)
        elif filters.sort_by == "state":
            candidates.sort(key=lambda c: c.current_state.value, reverse=reverse)
        elif filters.sort_by == "score":
            candidates.sort(key=lambda c: self._get_latest_score(c.id), reverse=reverse)

        # Get total count before pagination
        total_count = len(candidates)

        # Paginate
        start = filters.offset
        end = start + filters.limit
        paginated_candidates = candidates[start:end]

        # Convert to list items
        items = [
            self._candidate_to_list_item(c)
            for c in paginated_candidates
        ]

        return CandidateListResult(
            candidates=items,
            total_count=total_count,
            limit=filters.limit,
            offset=filters.offset,
            has_more=end < total_count,
        )

    def list_ready_candidates(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> CandidateListResult:
        """
        List candidates in READY state.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            CandidateListResult with ready candidates
        """
        filters = CandidateListFilter(
            state=ReadinessState.READY.value,
            limit=limit,
            offset=offset,
            sort_by="score",
            sort_order="desc",
        )
        return self.list_candidates(filters)

    def list_blocked_candidates(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> CandidateListResult:
        """
        List candidates in BLOCKED state.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            CandidateListResult with blocked candidates
        """
        filters = CandidateListFilter(
            state=ReadinessState.BLOCKED.value,
            limit=limit,
            offset=offset,
            sort_by="updated_at",
            sort_order="desc",
        )
        return self.list_candidates(filters)

    def list_regressed_candidates(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> CandidateListResult:
        """
        List candidates in REGRESSED state.

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            CandidateListResult with regressed candidates
        """
        filters = CandidateListFilter(
            state=ReadinessState.REGRESSED.value,
            limit=limit,
            offset=offset,
            sort_by="updated_at",
            sort_order="desc",
        )
        return self.list_candidates(filters)

    def get_latest_evaluation(
        self,
        candidate_id: UUID,
    ) -> Optional[ReadinessEvaluation]:
        """
        Get the most recent evaluation for a candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Most recent ReadinessEvaluation if exists, None otherwise
        """
        evaluations = _evaluations.get(candidate_id, [])
        if not evaluations:
            return None

        # Sort by evaluated_at descending
        evaluations.sort(key=lambda e: e.evaluated_at, reverse=True)
        return evaluations[0]

    def get_evaluation_history(
        self,
        candidate_id: UUID,
        limit: int = 50,
    ) -> List[ReadinessEvaluation]:
        """
        Get evaluation history for a candidate.

        Args:
            candidate_id: ID of the candidate
            limit: Maximum number of evaluations to return

        Returns:
            List of ReadinessEvaluation, most recent first
        """
        evaluations = _evaluations.get(candidate_id, [])
        evaluations.sort(key=lambda e: e.evaluated_at, reverse=True)
        return evaluations[:limit]

    def count_by_state(self) -> Dict[str, int]:
        """
        Count candidates by readiness state.

        Returns:
            Dictionary mapping state names to counts
        """
        counts: Dict[str, int] = {}

        for candidate in _candidates.values():
            state = candidate.current_state.value
            counts[state] = counts.get(state, 0) + 1

        return counts

    def _get_latest_score(self, candidate_id: UUID) -> float:
        """Get the latest score for a candidate."""
        evaluation = self.get_latest_evaluation(candidate_id)
        if evaluation:
            return evaluation.score.overall_score
        return 0.0

    def _candidate_to_list_item(
        self,
        candidate: ReadinessCandidate,
    ) -> CandidateListItem:
        """Convert a candidate to a list item view."""
        evaluation = self.get_latest_evaluation(candidate.id)

        # Check governance status
        has_hard_blocks = False
        is_regressed = candidate.current_state == ReadinessState.REGRESSED

        if evaluation:
            has_hard_blocks = len(evaluation.score.hard_blocks) > 0

        return CandidateListItem(
            candidate_id=candidate.id,
            candidate_type=candidate.candidate_type.value,
            candidate_key=candidate.key if hasattr(candidate, 'key') else None,
            title=candidate.title,
            current_state=candidate.current_state.value,
            state_since=candidate.current_state_since,
            score=self._get_latest_score(candidate.id),
            confidence=evaluation.score.confidence if evaluation else 0.0,
            policy_profile=candidate.policy_profile_id,
            has_hard_blocks=has_hard_blocks,
            is_regressed=is_regressed,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            last_assessed_at=evaluation.evaluated_at if evaluation else None,
        )


# Global query service instance
_query_service: Optional[ReadinessQueryService] = None


def get_query_service() -> ReadinessQueryService:
    """Get the global query service instance."""
    global _query_service
    if _query_service is None:
        _query_service = ReadinessQueryService()
    return _query_service
