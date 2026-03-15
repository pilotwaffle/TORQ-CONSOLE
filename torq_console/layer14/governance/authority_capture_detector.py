"""TORQ Layer 14 - Authority Capture Detector

This module implements detection of authority capture - when
influence becomes excessively concentrated in a single agent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .models import (
    AuthorityLevel,
    GovernanceDecisionPacket,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# INFLUENCE METRICS
# =============================================================================


@dataclass
class InfluenceMetrics:
    """Metrics tracking an agent's influence in the system."""

    agent_id: str

    # Decision influence
    total_decisions: int = 0
    proposed_decisions: int = 0
    approved_decisions: int = 0

    # Approval influence
    approval_count: int = 0
    self_approvals: int = 0  # Approvals of own proposals

    # Resource control
    total_budget_controlled: float = 0.0
    resources_allocated: list[str] = field(default_factory=list)

    # Time window
    window_start: datetime = field(default_factory=datetime.utcnow)
    window_end: datetime | None = None

    @property
    def decision_share(self) -> float:
        """Share of total decisions this agent is involved in."""
        if self.total_decisions == 0:
            return 0.0
        return (
            self.proposed_decisions + self.approved_decisions
        ) / self.total_decisions

    @property
    def approval_share(self) -> float:
        """Share of total approvals this agent controls."""
        if self.total_decisions == 0:
            return 0.0
        return self.approval_count / self.total_decisions

    @property
    def self_approval_rate(self) -> float:
        """Rate of self-approvals (should be 0)."""
        if self.approved_decisions == 0:
            return 0.0
        return self.self_approvals / self.approved_decisions


@dataclass
class AuthorityRisk:
    """Authority capture risk assessment for an agent."""

    agent_id: str
    influence_score: float  # 0.0 to 1.0
    capture_risk_level: str  # "low", "medium", "high", "critical"

    # Risk factors
    decision_concentration: float = 0.0
    approval_concentration: float = 0.0
    resource_concentration: float = 0.0
    authority_exceedance: bool = False

    # Details
    warnings: list[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# AUTHORITY CAPTURE DETECTOR
# =============================================================================


class AuthorityCaptureDetector:
    """Engine for detecting authority capture in the system.

    Authority capture occurs when influence becomes excessively
    concentrated in a single agent or small group, undermining
    system governance.

    The detector tracks:
    - Decision share (proposals + approvals)
    - Approval control
    - Resource allocation
    - Authority level compliance
    """

    # Risk thresholds
    DEFAULT_THRESHOLDS = {
        "decision_share_high": 0.5,  # >50% of decisions
        "approval_share_high": 0.6,  # >60% of approvals
        "resource_concentration_high": 0.7,  # >70% of resources
        "influence_critical": 0.8,  # Overall influence score
    }

    def __init__(
        self,
        window_seconds: int = 3600,
        thresholds: dict | None = None,
    ):
        """Initialize the authority capture detector.

        Args:
            window_seconds: Time window for tracking influence (default 1 hour)
            thresholds: Custom risk thresholds
        """
        self.window_seconds = window_seconds
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.metrics: dict[str, InfluenceMetrics] = {}
        self.total_system_decisions = 0
        self.total_system_budget = 0.0

    def track_decision(self, decision: GovernanceDecisionPacket):
        """Track a decision for influence metrics.

        Args:
            decision: Decision packet to track
        """
        # Update system totals
        self.total_system_decisions += 1
        self.total_system_budget += decision.estimated_cost

        # Track proposing agent
        self._get_or_create_metrics(decision.proposing_agent_id)
        self.metrics[decision.proposing_agent_id].proposed_decisions += 1

        # Track approving agent
        if decision.approving_agent_id:
            self._get_or_create_metrics(decision.approving_agent_id)
            self.metrics[decision.approving_agent_id].approved_decisions += 1
            self.metrics[decision.approving_agent_id].approval_count += 1

            # Check for self-approval
            if decision.proposing_agent_id == decision.approving_agent_id:
                self.metrics[decision.approving_agent_id].self_approvals += 1

        # Update all metrics with new total
        for metrics in self.metrics.values():
            metrics.total_decisions = self.total_system_decisions

    def _get_or_create_metrics(self, agent_id: str) -> InfluenceMetrics:
        """Get or create influence metrics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            InfluenceMetrics for the agent
        """
        if agent_id not in self.metrics:
            self.metrics[agent_id] = InfluenceMetrics(agent_id=agent_id)
        return self.metrics[agent_id]

    async def assess_capture_risk(
        self,
        agent_id: str,
        authority_level: AuthorityLevel = AuthorityLevel.PROPOSE,
    ) -> AuthorityRisk:
        """Assess authority capture risk for an agent.

        Args:
            agent_id: Agent to assess
            authority_level: Agent's current authority level

        Returns:
            AuthorityRisk assessment
        """
        if agent_id not in self.metrics:
            return AuthorityRisk(
                agent_id=agent_id,
                influence_score=0.0,
                capture_risk_level="low",
            )

        metrics = self.metrics[agent_id]

        # Calculate risk factors
        decision_concentration = self._assess_decision_concentration(metrics)
        approval_concentration = self._assess_approval_concentration(metrics)
        resource_concentration = self._assess_resource_concentration(metrics)

        # Calculate overall influence score
        influence_score = (
            decision_concentration * 0.4
            + approval_concentration * 0.4
            + resource_concentration * 0.2
        )

        # Determine risk level
        risk_level = self._determine_risk_level(influence_score)

        # Generate warnings
        warnings = self._generate_warnings(metrics, influence_score)

        # Check for authority exceedance
        authority_exceedance = self._check_authority_exceedance(
            metrics, authority_level
        )

        return AuthorityRisk(
            agent_id=agent_id,
            influence_score=influence_score,
            capture_risk_level=risk_level,
            decision_concentration=decision_concentration,
            approval_concentration=approval_concentration,
            resource_concentration=resource_concentration,
            authority_exceedance=authority_exceedance,
            warnings=warnings,
        )

    async def assess_all_risks(
        self,
        authority_levels: dict[str, AuthorityLevel] | None = None,
    ) -> dict[str, AuthorityRisk]:
        """Assess capture risk for all tracked agents.

        Args:
            authority_levels: Optional mapping of agent_id to authority level

        Returns:
            Dictionary mapping agent_id to AuthorityRisk
        """
        risks = {}
        authority_levels = authority_levels or {}

        for agent_id in self.metrics:
            authority = authority_levels.get(agent_id, AuthorityLevel.PROPOSE)
            risk = await self.assess_capture_risk(agent_id, authority)
            risks[agent_id] = risk

        return risks

    def _assess_decision_concentration(
        self, metrics: InfluenceMetrics
    ) -> float:
        """Assess decision concentration risk.

        Args:
            metrics: Agent's influence metrics

        Returns:
            Concentration score (0.0 to 1.0)
        """
        share = metrics.decision_share
        threshold = self.thresholds["decision_share_high"]

        if share >= threshold:
            return min(1.0, share / threshold)
        return share / threshold

    def _assess_approval_concentration(
        self, metrics: InfluenceMetrics
    ) -> float:
        """Assess approval concentration risk.

        Args:
            metrics: Agent's influence metrics

        Returns:
            Concentration score (0.0 to 1.0)
        """
        share = metrics.approval_share
        threshold = self.thresholds["approval_share_high"]

        if share >= threshold:
            return min(1.0, share / threshold)
        return share / threshold

    def _assess_resource_concentration(
        self, metrics: InfluenceMetrics
    ) -> float:
        """Assess resource concentration risk.

        Args:
            metrics: Agent's influence metrics

        Returns:
            Concentration score (0.0 to 1.0)
        """
        if self.total_system_budget == 0:
            return 0.0

        share = metrics.total_budget_controlled / self.total_system_budget
        threshold = self.thresholds["resource_concentration_high"]

        if share >= threshold:
            return min(1.0, share / threshold)
        return share / threshold

    def _determine_risk_level(self, influence_score: float) -> str:
        """Determine risk level from influence score.

        Args:
            influence_score: Overall influence score (0.0 to 1.0)

        Returns:
            Risk level: "low", "medium", "high", or "critical"
        """
        if influence_score >= self.thresholds["influence_critical"]:
            return "critical"
        elif influence_score >= 0.6:
            return "high"
        elif influence_score >= 0.3:
            return "medium"
        else:
            return "low"

    def _generate_warnings(
        self, metrics: InfluenceMetrics, influence_score: float
    ) -> list[str]:
        """Generate warning messages based on metrics.

        Args:
            metrics: Agent's influence metrics
            influence_score: Overall influence score

        Returns:
            List of warning messages
        """
        warnings = []

        if metrics.decision_share > 0.4:
            warnings.append(
                f"Agent controls {metrics.decision_share:.1%} of decisions"
            )

        if metrics.approval_share > 0.5:
            warnings.append(
                f"Agent controls {metrics.approval_share:.1%} of approvals"
            )

        if metrics.self_approval_rate > 0:
            warnings.append(
                f"Agent has {metrics.self_approvals} self-approvals"
            )

        if influence_score > 0.6:
            warnings.append("High influence concentration detected")

        return warnings

    def _check_authority_exceedance(
        self, metrics: InfluenceMetrics, authority_level: AuthorityLevel
    ) -> bool:
        """Check if agent is exercising authority beyond their level.

        Args:
            metrics: Agent's influence metrics
            authority_level: Agent's granted authority level

        Returns:
            True if authority is being exceeded
        """
        # High influence with low authority is a red flag
        if metrics.decision_share > 0.5:
            if authority_level in (
                AuthorityLevel.PROPOSE,
                AuthorityLevel.ADVISE,
                AuthorityLevel.EXECUTE,
            ):
                return True

        # High approval control without APPROVE authority
        if metrics.approval_share > 0.5:
            if authority_level != AuthorityLevel.APPROVE:
                return True

        return False

    def reset_window(self):
        """Reset the tracking window."""
        self.metrics.clear()
        self.total_system_decisions = 0
        self.total_system_budget = 0.0

    def get_metrics(self, agent_id: str) -> InfluenceMetrics | None:
        """Get influence metrics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            InfluenceMetrics if found, None otherwise
        """
        return self.metrics.get(agent_id)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_authority_capture_detector(
    window_seconds: int = 3600,
    thresholds: dict | None = None,
) -> AuthorityCaptureDetector:
    """Factory function to create an authority capture detector.

    Args:
        window_seconds: Time window for tracking (default 1 hour)
        thresholds: Custom risk thresholds

    Returns:
        Configured AuthorityCaptureDetector instance
    """
    return AuthorityCaptureDetector(
        window_seconds=window_seconds,
        thresholds=thresholds,
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "AuthorityCaptureDetector",
    "AuthorityRisk",
    "InfluenceMetrics",
    "create_authority_capture_detector",
]
