"""
TORQ Layer 10 - Risk Modeling System

L10-M1: Assesses and quantifies operational, governance, and strategic risks.

The RiskModelingSystem provides:
- Risk probability calculation
- Impact estimation
- Mitigation recommendations
- Aggregated risk reporting
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from collections import defaultdict

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    RiskAssessment,
    RiskModelReport,
    RiskCategory,
    RiskSeverity,
    RiskMitigation,
)


# ============================================================================
# Risk Modeling Context
# ============================================================================

@dataclass
class RiskContext:
    """Context data for risk modeling."""
    # Current system state
    total_capabilities: int = 100
    ready_capabilities: int = 70
    at_risk_capabilities: int = 15
    critical_capabilities: int = 10

    # Historical risk data
    historical_regression_rate: float = 0.05
    historical_failure_rate: float = 0.10

    # Environmental factors
    change_velocity: str = "medium"  # low, medium, high
    system_complexity: str = "medium"  # low, medium, high
    operational_stability: float = 0.80

    # Risk weights by category
    category_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.category_weights is None:
            self.category_weights = {
                "execution": 1.0,
                "governance": 0.8,
                "operational_complexity": 0.6,
                "readiness_instability": 0.9,
                "systemic_pattern_drift": 0.7,
                "capability_degradation": 0.8,
                "resource_constraint": 0.5,
                "strategic_misalignment": 0.6,
            }


# ============================================================================
# Risk Modeling Service
# ============================================================================

class RiskModelingService:
    """
    Assesses and models operational and strategic risks.

    Identifies, quantifies, and provides mitigation strategies for
    risks across the TORQ ecosystem.
    """

    def __init__(self):
        """Initialize the risk modeling service."""
        self._assessments: Dict[UUID, RiskAssessment] = {}
        self._reports: Dict[UUID, RiskModelReport] = {}
        self._context = RiskContext()

    def set_risk_context(self, context: RiskContext) -> None:
        """Set the risk modeling context."""
        self._context = context
        logger.debug(f"[RiskService] Updated risk context")

    async def assess_risk(
        self,
        title: str,
        description: str,
        risk_category: RiskCategory,
        probability: float = 0.5,
        impact: float = 0.5,
        affected_capabilities: Optional[List[str]] = None,
        context_override: Optional[RiskContext] = None,
    ) -> RiskAssessment:
        """
        Create a risk assessment.

        Args:
            title: Risk title
            description: Risk description
            risk_category: Category of risk
            probability: Probability of occurrence (0-1)
            impact: Impact if occurs (0-1)
            affected_capabilities: List of affected capabilities
            context_override: Optional context override

        Returns:
            RiskAssessment with calculated severity
        """
        context = context_override or self._context

        # Calculate risk score
        risk_score = probability * impact

        # Determine severity
        severity = self._calculate_severity(risk_score)

        # Generate mitigation options
        mitigation_options = self._generate_mitigations(
            risk_category,
            probability,
            impact,
        )

        assessment = RiskAssessment(
            title=title,
            description=description,
            risk_category=risk_category,
            probability=probability,
            impact=impact,
            severity=severity,
            risk_score=risk_score,
            affected_capabilities=affected_capabilities or [],
            mitigation_options=mitigation_options,
            monitoring_indicators=self._get_monitoring_indicators(risk_category),
            review_frequency=self._get_review_frequency(risk_category, severity),
        )

        self._assessments[assessment.risk_id] = assessment

        logger.info(
            f"[RiskService] Assessed risk '{title}': "
            f"{severity} severity (score: {risk_score:.2f})"
        )

        return assessment

    async def evaluate_scenario_risks(
        self,
        scenario_id: Optional[UUID],
        context_override: Optional[RiskContext] = None,
    ) -> RiskModelReport:
        """
        Generate a comprehensive risk model report.

        Args:
            scenario_id: Optional scenario ID to link to
            context_override: Optional context override

        Returns:
            RiskModelReport with aggregated risk analysis
        """
        context = context_override or self._context

        report = RiskModelReport(
            scenario_id=scenario_id,
        )

        # Generate risk assessments for each category
        assessments = []
        for category in RiskCategory:
            assessment = await self._assess_category_risk(category, context)
            if assessment:
                assessments.append(assessment)
                self._assessments[assessment.risk_id] = assessment

        # Calculate aggregate scores
        report.risk_by_category = {
            cat.risk_category.value if hasattr(cat.risk_category, 'value') else str(cat.risk_category): cat.risk_score
            for cat in assessments
        }

        # Count by severity
        severity_counts = defaultdict(int)
        for assessment in assessments:
            severity_key = assessment.severity.value if hasattr(assessment.severity, 'value') else str(assessment.severity)
            severity_counts[severity_key] += 1
        report.risk_by_severity = dict(severity_counts)

        # Calculate overall risk score
        if report.risk_by_category:
            weighted_scores = []
            for cat, score in report.risk_by_category.items():
                weight = context.category_weights.get(cat, 1.0)
                weighted_scores.append(score * weight)
            report.overall_risk_score = sum(weighted_scores) / len(weighted_scores)

        # Top risks
        sorted_assessments = sorted(assessments, key=lambda r: r.risk_score, reverse=True)
        report.top_risks = sorted_assessments[:5]
        report.critical_risk_count = severity_counts.get("critical", 0)
        report.high_risk_count = severity_counts.get("high", 0)

        # Determine trend
        report.risk_trend = self._assess_risk_trend(report, context)

        # Generate recommendations
        report.prioritized_mitigations = self._prioritize_mitigations(report.top_risks)
        report.strategic_recommendations = self._generate_strategic_recommendations(report)

        self._reports[report.report_id] = report

        logger.info(
            f"[RiskService] Risk report generated: "
            f"{report.overall_risk_score:.2f} overall risk score"
        )

        return report

    async def _assess_category_risk(
        self,
        category: RiskCategory,
        context: RiskContext,
    ) -> Optional[RiskAssessment]:
        """Assess risk for a specific category."""
        # Generate risk category-specific risk assessment
        category_configs = {
            RiskCategory.EXECUTION: {
                "title": "Mission Execution Risk",
                "description": "Risk of mission failures or degraded performance",
                "base_probability": context.historical_failure_rate,
                "base_impact": 0.7,
            },
            RiskCategory.GOVERNANCE: {
                "title": "Governance Risk",
                "description": "Risk of policy violations or governance failures",
                "base_probability": 0.15,
                "base_impact": 0.8,
            },
            RiskCategory.OPERATIONAL_COMPLEXITY: {
                "title": "Operational Complexity Risk",
                "description": "Risk from system complexity and interdependencies",
                "base_probability": 0.25 if context.system_complexity == "high" else 0.15,
                "base_impact": 0.6,
            },
            RiskCategory.READINESS_INSTABILITY: {
                "title": "Readiness Instability Risk",
                "description": "Risk of capability readiness fluctuations",
                "base_probability": context.historical_regression_rate * 2,
                "base_impact": 0.75,
            },
            RiskCategory.SYSTEMIC_PATTERN_DRIFT: {
                "title": "Systemic Pattern Drift Risk",
                "description": "Risk of patterns degrading over time",
                "base_probability": 0.20,
                "base_impact": 0.65,
            },
            RiskCategory.CAPABILITY_DEGRADATION: {
                "title": "Capability Degradation Risk",
                "description": "Risk of capability performance decline",
                "base_probability": 0.10,
                "base_impact": 0.70,
            },
            RiskCategory.RESOURCE_CONSTRAINT: {
                "title": "Resource Constraint Risk",
                "description": "Risk of insufficient resources for operations",
                "base_probability": 0.15,
                "base_impact": 0.80,
            },
            RiskCategory.STRATEGIC_MISALIGNMENT: {
                "title": "Strategic Misalignment Risk",
                "description": "Risk of operations misaligning with strategic goals",
                "base_probability": 0.12,
                "base_impact": 0.85,
            },
        }

        config = category_configs.get(category)
        if not config:
            return None

        # Adjust probability based on context
        probability = config["base_probability"]
        if context.change_velocity == "high":
            probability *= 1.5
        elif context.change_velocity == "low":
            probability *= 0.7

        probability = min(1.0, probability)

        return await self.assess_risk(
            title=config["title"],
            description=config["description"],
            risk_category=category,
            probability=probability,
            impact=config["base_impact"],
            context_override=context,
        )

    def _calculate_severity(self, risk_score: float) -> RiskSeverity:
        """Calculate severity from risk score."""
        if risk_score >= 0.6:
            return RiskSeverity.CRITICAL
        elif risk_score >= 0.4:
            return RiskSeverity.HIGH
        elif risk_score >= 0.2:
            return RiskSeverity.MEDIUM
        else:
            return RiskSeverity.LOW

    def _generate_mitigations(
        self,
        category: RiskCategory,
        probability: float,
        impact: float,
    ) -> List[RiskMitigation]:
        """Generate mitigation options for a risk."""
        mitigations = []

        # Category-specific mitigations
        category_mitigations = {
            RiskCategory.EXECUTION: [
                RiskMitigation(
                    mitigation_id="enhanced_validation",
                    strategy="Enhanced Validation",
                    description="Implement additional validation checks before mission execution",
                    effectiveness=0.7,
                ),
                RiskMitigation(
                    mitigation_id="rollback_plan",
                    strategy="Rollback Planning",
                    description="Maintain rollback plans for critical missions",
                    effectiveness=0.8,
                ),
            ],
            RiskCategory.GOVERNANCE: [
                RiskMitigation(
                    mitigation_id="policy_review",
                    strategy="Policy Review",
                    description="Conduct regular policy reviews and updates",
                    effectiveness=0.75,
                ),
                RiskMitigation(
                    mitigation_id="compliance_monitoring",
                    strategy="Compliance Monitoring",
                    description="Implement automated compliance monitoring",
                    effectiveness=0.85,
                ),
            ],
            RiskCategory.READINESS_INSTABILITY: [
                RiskMitigation(
                    mitigation_id="readiness_buffer",
                    strategy="Readiness Buffer",
                    description="Maintain buffer above readiness threshold",
                    effectiveness=0.8,
                ),
            ],
            RiskCategory.RESOURCE_CONSTRAINT: [
                RiskMitigation(
                    mitigation_id="resource_scaling",
                    strategy="Resource Scaling",
                    description="Implement auto-scaling for resources",
                    effectiveness=0.85,
                ),
            ],
        }

        # Get category-specific mitigations
        specific = category_mitigations.get(category, [])

        # Add generic mitigations
        generic = [
            RiskMitigation(
                mitigation_id="monitoring",
                strategy="Enhanced Monitoring",
                description="Increase monitoring frequency and granularity",
                effectiveness=0.6,
            ),
            RiskMitigation(
                mitigation_id="documentation",
                strategy="Documentation Update",
                description="Update documentation to reflect current state",
                effectiveness=0.4,
            ),
        ]

        return specific + generic

    def _get_monitoring_indicators(self, category: RiskCategory) -> List[str]:
        """Get monitoring indicators for a risk category."""
        indicators = {
            RiskCategory.EXECUTION: ["mission_success_rate", "avg_duration", "error_rate"],
            RiskCategory.GOVERNANCE: ["policy_violations", "compliance_rate"],
            RiskCategory.READINESS_INSTABILITY: ["readiness_volatility", "regression_rate"],
            RiskCategory.RESOURCE_CONSTRAINT: ["resource_utilization", "queue_depth"],
        }
        return indicators.get(category, ["general_risk_indicator"])

    def _get_review_frequency(self, category: RiskCategory, severity: RiskSeverity) -> str:
        """Get recommended review frequency."""
        if severity == RiskSeverity.CRITICAL:
            return "daily"
        elif severity == RiskSeverity.HIGH:
            return "weekly"
        elif severity == RiskSeverity.MEDIUM:
            return "monthly"
        else:
            return "quarterly"

    def _assess_risk_trend(self, report: RiskModelReport, context: RiskContext) -> str:
        """Assess overall risk trend."""
        if report.overall_risk_score > 0.6:
            return "increasing"
        elif report.overall_risk_score < 0.3:
            return "decreasing"
        else:
            return "stable"

    def _prioritize_mitigations(self, top_risks: List[RiskAssessment]) -> List[str]:
        """Prioritize mitigation recommendations."""
        prioritized = []

        for risk in top_risks[:3]:
            if risk.mitigation_options:
                best = max(risk.mitigation_options, key=lambda m: m.effectiveness)
                prioritized.append(f"{best.strategy}: {best.description}")

        return prioritized

    def _generate_strategic_recommendations(self, report: RiskModelReport) -> List[str]:
        """Generate strategic risk recommendations."""
        recommendations = []

        if report.overall_risk_score > 0.5:
            recommendations.append("Implement comprehensive risk reduction plan")

        if report.critical_risk_count > 0:
            recommendations.append(f"Address {report.critical_risk_count} critical risks immediately")

        if report.high_risk_count > 3:
            recommendations.append("Establish risk management working group")

        if report.risk_trend == "increasing":
            recommendations.append("Investigate root causes of rising risk levels")

        # Always include
        recommendations.append("Establish regular risk review cadence")
        recommendations.append("Update risk register quarterly")

        return recommendations

    def get_assessment(self, assessment_id: UUID) -> Optional[RiskAssessment]:
        """Get a risk assessment by ID."""
        return self._assessments.get(assessment_id)

    def get_report(self, report_id: UUID) -> Optional[RiskModelReport]:
        """Get a risk report by ID."""
        return self._reports.get(report_id)

    def list_assessments(self) -> List[RiskAssessment]:
        """List all risk assessments."""
        return list(self._assessments.values())

    def list_reports(self) -> List[RiskModelReport]:
        """List all risk reports."""
        return list(self._reports.values())


# Global risk modeling service instance
_service: Optional[RiskModelingService] = None


def get_risk_service() -> RiskModelingService:
    """Get the global risk modeling service instance."""
    global _service
    if _service is None:
        _service = RiskModelingService()
    return _service
