"""
TORQ Layer 10 - Policy Impact Simulator

L10-M1: Evaluates governance and readiness policy changes before deployment.

The PolicyImpactSimulator provides:
- Readiness threshold impact simulation
- Promotion criteria testing
- Regression threshold evaluation
- Governance rule impact analysis
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from dataclasses import dataclass
from collections import defaultdict

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    PolicyImpactReport,
    PolicySimulationConfig,
    PolicyChangeType,
    RiskCategory,
    RiskSeverity,
)


# ============================================================================
# Policy Simulation Context
# ============================================================================

@dataclass
class PolicyContext:
    """Context data for policy simulation."""
    total_capabilities: int = 100
    ready_capabilities: int = 70
    blocked_capabilities: int = 20
    watchlist_capabilities: int = 10

    # Current policy settings
    current_readiness_threshold: float = 0.70
    current_regression_threshold: float = 0.60
    current_validation_required: bool = True

    # Historical rates
    historical_promotion_rate: float = 0.15  # 15% per month
    historical_regression_rate: float = 0.05  # 5% per month

    # Capability readiness distribution (for simulation)
    readiness_distribution: Dict[str, int] = None

    def __post_init__(self):
        if self.readiness_distribution is None:
            # Distribution of capabilities by readiness range
            self.readiness_distribution = {
                "0.0-0.5": 5,
                "0.5-0.6": 10,
                "0.6-0.7": 15,  # Just below current threshold
                "0.7-0.8": 25,  # Just ready
                "0.8-0.9": 30,
                "0.9-1.0": 15,
            }


# ============================================================================
# Policy Impact Simulator
# ============================================================================

class PolicyImpactSimulator:
    """
    Simulates the impact of policy and governance changes.

    Evaluates how changes to readiness thresholds, promotion criteria,
    and governance rules will affect the capability pipeline.
    """

    def __init__(self):
        """Initialize the policy simulator."""
        self._reports: Dict[UUID, PolicyImpactReport] = {}
        self._context = PolicyContext()

    def set_policy_context(self, context: PolicyContext) -> None:
        """Set the policy simulation context."""
        self._context = context
        logger.debug(f"[PolicySimulator] Updated policy context")

    async def simulate_policy_change(
        self,
        config: PolicySimulationConfig,
        context_override: Optional[PolicyContext] = None,
    ) -> PolicyImpactReport:
        """
        Simulate the impact of a policy change.

        Args:
            config: Policy simulation configuration
            context_override: Optional context override

        Returns:
            PolicyImpactReport with impact analysis
        """
        context = context_override or self._context

        # Create report
        report = PolicyImpactReport(
            policy_id=config.policy_id,
            change_type=config.change_type,
            change_description=f"Change {config.change_type} from {config.current_value} to {config.proposed_value}",
            baseline_promotion_rate=context.historical_promotion_rate,
            baseline_regression_rate=context.historical_regression_rate,
            baseline_ready_count=context.ready_capabilities,
        )

        logger.info(
            f"[PolicySimulator] Simulating {config.change_type}: "
            f"{config.current_value} → {config.proposed_value}"
        )

        # Run simulation based on change type
        if config.change_type == PolicyChangeType.READINESS_THRESHOLD:
            await self._simulate_readiness_threshold_change(config, report, context)
        elif config.change_type == PolicyChangeType.PROMOTION_CRITERIA:
            await self._simulate_promotion_criteria_change(config, report, context)
        elif config.change_type == PolicyChangeType.REGRESSION_THRESHOLD:
            await self._simulate_regression_threshold_change(config, report, context)
        elif config.change_type == PolicyChangeType.VALIDATION_REQUIREMENT:
            await self._simulate_validation_requirement_change(config, report, context)
        else:
            await self._simulate_governance_rule_change(config, report, context)

        # Generate recommendations
        self._generate_recommendations(report)

        self._reports[report.report_id] = report

        logger.info(
            f"[PolicySimulator] Policy simulation complete: "
            f"promotion {'+' if report.promotion_rate_change >= 0 else ''}{report.promotion_rate_change:.1%}"
        )

        return report

    async def _simulate_readiness_threshold_change(
        self,
        config: PolicySimulationConfig,
        report: PolicyImpactReport,
        context: PolicyContext,
    ) -> None:
        """Simulate changing the readiness threshold."""
        old_threshold = float(config.current_value)
        new_threshold = float(config.proposed_value)

        # Calculate affected capabilities
        newly_ready = 0
        newly_blocked = 0
        at_risk = []

        # Using readiness distribution
        for range_str, count in context.readiness_distribution.items():
            low, high = map(float, range_str.split("-"))

            if low >= new_threshold:
                # Already above new threshold
                newly_ready += count
            elif high < new_threshold:
                # Below new threshold - at risk of blocking
                if high >= old_threshold:
                    # Was ready under old threshold
                    at_risk.extend([f"capability_{i}" for i in range(count)])
                    newly_blocked += count

        # Update predictions
        report.predicted_ready_count = context.ready_capabilities - newly_blocked + newly_ready
        report.ready_count_change = report.predicted_ready_count - context.ready_capabilities

        # Estimate promotion rate change
        threshold_delta = new_threshold - old_threshold
        report.promotion_rate_change = -threshold_delta * 0.5  # Rough estimate
        report.predicted_promotion_rate = context.historical_promotion_rate + report.promotion_rate_change

        # Regression rate typically increases with stricter thresholds
        # (capabilities may struggle to maintain higher standard)
        if new_threshold > old_threshold:
            report.regression_rate_change = threshold_delta * 0.2
        else:
            report.regression_rate_change = -threshold_delta * 0.1

        report.predicted_regression_rate = context.historical_regression_rate + report.regression_rate_change

        report.capabilities_at_risk = at_risk[:10]  # Top 10 at risk
        report.affected_capabilities = at_risk

        # Implementation timeline
        report.implementation_timeline = "Immediate effect on new promotions"
        report.stabilization_period = f"{abs(threshold_delta) * 30:.0f} days"

    async def _simulate_promotion_criteria_change(
        self,
        config: PolicySimulationConfig,
        report: PolicyImpactReport,
        context: PolicyContext,
    ) -> None:
        """Simulate changing promotion criteria."""
        # Extract criteria parameters
        old_min_validations = int(config.current_value)
        new_min_validations = int(config.proposed_value)

        # Simulate impact
        validation_delta = new_min_validations - old_min_validations

        # More validations = slower promotions but higher quality
        report.promotion_rate_change = -validation_delta * 0.03
        report.predicted_promotion_rate = context.historical_promotion_rate + report.promotion_rate_change

        # Stricter criteria may reduce regressions
        report.regression_rate_change = -validation_delta * 0.01
        report.predicted_regression_rate = context.historical_regression_rate + report.regression_rate_change

        # Ready count may decrease if criteria are retroactive
        if new_min_validations > old_min_validations:
            affected_pct = 0.1 * validation_delta  # 10% affected per additional validation
            report.ready_count_change = -int(context.ready_capabilities * affected_pct)
        else:
            report.ready_count_change = 0

        report.predicted_ready_count = context.ready_capabilities + report.ready_count_change

        report.implementation_timeline = "Effect on new promotions: immediate"
        report.stabilization_period = "2-4 weeks"

    async def _simulate_regression_threshold_change(
        self,
        config: PolicySimulationConfig,
        report: PolicyImpactReport,
        context: PolicyContext,
    ) -> None:
        """Simulate changing the regression threshold."""
        old_threshold = float(config.current_value)
        new_threshold = float(config.proposed_value)

        threshold_delta = new_threshold - old_threshold

        # Lower regression threshold = more aggressive detection
        # Higher regression threshold = more tolerance
        if new_threshold < old_threshold:
            # More aggressive - catch regressions earlier
            report.regression_rate_change = threshold_delta * 0.3  # Will appear to increase
            report.promotion_rate_change = -0.02  # May slow promotions
        else:
            # More lenient - fewer regressions detected
            report.regression_rate_change = threshold_delta * 0.2
            report.promotion_rate_change = 0.01  # May speed up promotions

        report.predicted_regression_rate = context.historical_regression_rate + report.regression_rate_change
        report.predicted_promotion_rate = context.historical_promotion_rate + report.promotion_rate_change

        # Ready count largely unaffected
        report.predicted_ready_count = context.ready_capabilities
        report.ready_count_change = 0

        report.implementation_timeline = "Immediate effect on regression monitoring"

    async def _simulate_validation_requirement_change(
        self,
        config: PolicySimulationConfig,
        report: PolicyImpactReport,
        context: PolicyContext,
    ) -> None:
        """Simulate changing validation requirements."""
        old_required = bool(config.current_value)
        new_required = bool(config.proposed_value)

        if new_required and not old_required:
            # Adding validation requirement
            report.promotion_rate_change = -0.15  # Significant slowdown
            report.regression_rate_change = -0.05  # Fewer regressions
            report.implementation_timeline = "Immediate for new validations"
        elif not new_required and old_required:
            # Removing validation requirement
            report.promotion_rate_change = 0.20  # Faster promotions
            report.regression_rate_change = 0.10  # More regressions
            report.implementation_timeline = "Immediate effect"
        else:
            report.promotion_rate_change = 0.0
            report.regression_rate_change = 0.0

        report.predicted_promotion_rate = context.historical_promotion_rate + report.promotion_rate_change
        report.predicted_regression_rate = context.historical_regression_rate + report.regression_rate_change
        report.predicted_ready_count = context.ready_capabilities
        report.ready_count_change = 0

    async def _simulate_governance_rule_change(
        self,
        config: PolicySimulationConfig,
        report: PolicyImpactReport,
        context: PolicyContext,
    ) -> None:
        """Simulate a generic governance rule change."""
        # Generic simulation with moderate impact
        rule_severity = config.parameters.get("severity", "medium")

        if rule_severity == "high":
            report.promotion_rate_change = -0.10
            report.regression_rate_change = -0.03
        elif rule_severity == "low":
            report.promotion_rate_change = 0.05
            report.regression_rate_change = 0.02
        else:
            report.promotion_rate_change = -0.02
            report.regression_rate_change = -0.01

        report.predicted_promotion_rate = context.historical_promotion_rate + report.promotion_rate_change
        report.predicted_regression_rate = context.historical_regression_rate + report.regression_rate_change
        report.predicted_ready_count = context.ready_capabilities
        report.ready_count_change = 0

        report.implementation_timeline = "1-2 weeks for full effect"

    def _generate_recommendations(self, report: PolicyImpactReport) -> None:
        """Generate recommendations based on policy impact."""
        report.recommendations = []
        report.risk_factors = []

        # Analyze promotion change
        if report.promotion_rate_change < -0.10:
            report.recommendations.append(
                "Consider gradual rollout to monitor impact on capability pipeline"
            )
            report.risk_factors.append(
                "Significant reduction in promotion rate may cause pipeline backup"
            )
        elif report.promotion_rate_change > 0.10:
            report.recommendations.append(
                "Increase monitoring for quality issues with faster promotions"
            )
            report.risk_factors.append(
                "Rapid promotion increase may reduce capability quality"
            )

        # Analyze regression change
        if report.regression_rate_change > 0.05:
            report.recommendations.append(
                "Implement additional safeguards to prevent instability"
            )
            report.risk_factors.append(
                "Increased regression risk may affect system stability"
            )

        # Analyze at-risk capabilities
        if len(report.capabilities_at_risk) > 5:
            report.recommendations.append(
                f"Proactively review {len(report.capabilities_at_risk)} at-risk capabilities"
            )

        # Always include these
        report.recommendations.append(
            "Monitor key metrics for 2 weeks post-implementation"
        )
        report.recommendations.append(
            "Prepare rollback plan in case of unexpected outcomes"
        )

        # Set confidence based on change magnitude
        change_magnitude = abs(report.promotion_rate_change) + abs(report.regression_rate_change)
        report.confidence = max(0.3, min(0.95, 0.9 - change_magnitude))

    def get_report(self, report_id: UUID) -> Optional[PolicyImpactReport]:
        """Get a policy impact report by ID."""
        return self._reports.get(report_id)

    def list_reports(self) -> List[PolicyImpactReport]:
        """List all policy impact reports."""
        return list(self._reports.values())


# Global policy simulator instance
_simulator: Optional[PolicyImpactSimulator] = None


def get_policy_simulator() -> PolicyImpactSimulator:
    """Get the global policy impact simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = PolicyImpactSimulator()
    return _simulator
