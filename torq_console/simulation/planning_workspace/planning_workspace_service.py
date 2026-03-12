"""
TORQ Layer 10 - Planning Workspace Service

L10-M1: Provides collaborative scenario planning and comparison environment.

The PlanningWorkspaceService provides:
- Planning session management
- Scenario comparison
- Decision tracking
- Action item management
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    PlanningSession,
    PlanningSessionStatus,
    ScenarioComparison,
)


# ============================================================================
# Planning Workspace Service
# ============================================================================

class PlanningWorkspaceService:
    """
    Manages collaborative planning sessions and scenario comparison.

    Provides a workspace for teams to compare simulation scenarios,
    track decisions, and manage action items.
    """

    def __init__(self):
        """Initialize the planning workspace service."""
        self._sessions: Dict[UUID, PlanningSession] = {}
        self._comparisons: Dict[UUID, ScenarioComparison] = {}

    async def create_session(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        **kwargs
    ) -> PlanningSession:
        """
        Create a new planning session.

        Args:
            title: Session title
            description: Session description
            owner: Session owner
            **kwargs: Additional session parameters

        Returns:
            Created PlanningSession
        """
        session = PlanningSession(
            title=title,
            description=description,
            status=PlanningSessionStatus.DRAFT,
            owner=owner,
            participants=[owner] if owner else [],
            **kwargs
        )

        self._sessions[session.session_id] = session

        logger.info(
            f"[PlanningWorkspace] Created session '{title}' "
            f"(owner: {owner})"
        )

        return session

    async def update_session(
        self,
        session_id: UUID,
        **updates
    ) -> Optional[PlanningSession]:
        """
        Update a planning session.

        Args:
            session_id: ID of session to update
            **updates: Fields to update

        Returns:
            Updated session or None
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.now()

        logger.debug(f"[PlanningWorkspace] Updated session {session_id}")

        return session

    async def add_scenario_to_session(
        self,
        session_id: UUID,
        scenario_id: UUID,
    ) -> bool:
        """
        Add a scenario to a planning session.

        Args:
            session_id: Session ID
            scenario_id: Scenario ID to add

        Returns:
            True if added successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if scenario_id not in session.scenario_ids:
            session.scenario_ids.append(scenario_id)
            session.updated_at = datetime.now()

        logger.debug(f"[PlanningWorkspace] Added scenario {scenario_id} to session {session_id}")

        return True

    async def compare_scenarios(
        self,
        scenario_ids: List[UUID],
        title: str = "Scenario Comparison",
    ) -> ScenarioComparison:
        """
        Compare multiple simulation scenarios.

        Args:
            scenario_ids: List of scenario IDs to compare
            title: Comparison title

        Returns:
            ScenarioComparison with analysis
        """
        comparison = ScenarioComparison(
            scenario_ids=scenario_ids,
        )

        # Compare metrics (placeholder - would integrate with actual results)
        comparison.metric_comparisons = {
            "success_rate": {str(sid): 0.75 + i * 0.05 for i, sid in enumerate(scenario_ids)},
            "avg_duration": {str(sid): 120 - i * 10 for i, sid in enumerate(scenario_ids)},
            "avg_quality": {str(sid): 0.8 + i * 0.03 for i, sid in enumerate(scenario_ids)},
        }

        # Determine winner by each metric
        for metric, values in comparison.metric_comparisons.items():
            if metric in ["success_rate", "avg_quality"]:
                # Higher is better
                winner_sid = max(values.items(), key=lambda x: x[1])[0]
            else:
                # Lower is better
                winner_sid = min(values.items(), key=lambda x: x[1])[0]
            comparison.winner_by_metric[metric] = UUID(winner_sid)

        # Overall recommendation (simple: most wins)
        wins = defaultdict(int)
        for winner in comparison.winner_by_metric.values():
            wins[str(winner)] += 1

        if wins:
            best_sid = max(wins.items(), key=lambda x: x[1])[0]
            comparison.recommended_scenario = UUID(best_sid)
            comparison.recommendation_rationale = (
                f"Scenario {best_sid} wins on {len([w for w in comparison.winner_by_metric.values() if str(w) == best_sid])} "
                f"of {len(comparison.winner_by_metric)} key metrics"
            )

        # Trade-offs
        comparison.trade_offs = [
            "Scenario with highest success rate has longer duration",
            "Quality improvements correlate with increased execution time",
        ]
        comparison.considerations = [
            "Consider operational constraints when selecting scenario",
            "Validate assumptions with historical data",
            "Monitor actual performance against predictions",
        ]

        self._comparisons[comparison.comparison_id] = comparison

        logger.info(
            f"[PlanningWorkspace] Created comparison: {len(scenario_ids)} scenarios"
        )

        return comparison

    async def set_session_comparison(
        self,
        session_id: UUID,
        comparison_id: UUID,
    ) -> bool:
        """Link a comparison to a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if comparison_id not in self._comparisons:
            return False

        session.comparison_id = comparison_id
        session.updated_at = datetime.now()

        return True

    async def add_decision(
        self,
        session_id: UUID,
        decision: str,
    ) -> bool:
        """Add a decision to a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.decisions.append(decision)
        session.updated_at = datetime.now()

        logger.debug(f"[PlanningWorkspace] Added decision to session {session_id}")

        return True

    async def add_action_item(
        self,
        session_id: UUID,
        action_item: str,
    ) -> bool:
        """Add an action item to a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.action_items.append(action_item)
        session.updated_at = datetime.now()

        logger.debug(f"[PlanningWorkspace] Added action item to session {session_id}")

        return True

    async def set_session_status(
        self,
        session_id: UUID,
        status: PlanningSessionStatus,
    ) -> bool:
        """Set the status of a planning session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.status = status
        session.updated_at = datetime.now()

        if status == PlanningSessionStatus.APPROVED:
            session.completed_at = datetime.now()

        logger.info(f"[PlanningWorkspace] Session {session_id} status: {status}")

        return True

    async def add_participant(
        self,
        session_id: UUID,
        participant: str,
    ) -> bool:
        """Add a participant to a planning session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if participant not in session.participants:
            session.participants.append(participant)
            session.updated_at = datetime.now()

        return True

    def get_session(self, session_id: UUID) -> Optional[PlanningSession]:
        """Get a planning session by ID."""
        return self._sessions.get(session_id)

    def get_comparison(self, comparison_id: UUID) -> Optional[ScenarioComparison]:
        """Get a scenario comparison by ID."""
        return self._comparisons.get(comparison_id)

    def list_sessions(
        self,
        status: Optional[PlanningSessionStatus] = None,
        owner: Optional[str] = None,
    ) -> List[PlanningSession]:
        """List planning sessions with optional filters."""
        sessions = list(self._sessions.values())

        if status:
            sessions = [s for s in sessions if s.status == status]

        if owner:
            sessions = [s for s in sessions if s.owner == owner]

        return sessions

    def list_comparisons(self) -> List[ScenarioComparison]:
        """List all scenario comparisons."""
        return list(self._comparisons.values())


# Global planning workspace service instance
_service: Optional[PlanningWorkspaceService] = None


def get_planning_workspace() -> PlanningWorkspaceService:
    """Get the global planning workspace service instance."""
    global _service
    if _service is None:
        _service = PlanningWorkspaceService()
    return _service
