"""
Federation Health Index Calculator

Layer 12 Phase 2A — Federation Stability Validation Harness

Calculates the Federation Health Index (FHI) - a composite metric that
measures overall federation health across multiple dimensions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .metrics import SimulationMetrics

logger = logging.getLogger(__name__)


# ============================================================================
# Health Status Definitions
# ============================================================================

@dataclass
class HealthThresholds:
    """Health status thresholds for interpretation."""

    # Overall thresholds
    healthy_min: float = 0.85
    stable_min: float = 0.70
    degraded_min: float = 0.50

    # Category thresholds
    diversity_healthy: float = 0.80
    diversity_stable: float = 0.70

    influence_healthy: float = 0.75
    influence_stable: float = 0.65

    trust_healthy: float = 0.85
    trust_stable: float = 0.75

    quality_healthy: float = 0.80
    quality_stable: float = 0.70

    resilience_healthy: float = 0.80
    resilience_stable: float = 0.70


class HealthStatus(Enum):
    """Federation health status levels."""
    HEALTHY = "healthy"
    STABLE = "stable"
    DEGRADED = "degraded"
    FAILING = "failing"


# ============================================================================
# Health Index Calculator
# ============================================================================

class FederationHealthIndexCalculator:
    """Calculates and interprets the Federation Health Index."""

    def __init__(self, thresholds: Optional[HealthThresholds] = None):
        self.thresholds = thresholds or HealthThresholds()
        self.logger = logging.getLogger(__name__)

    def calculate_health_index(
        self,
        metrics: SimulationMetrics,
        round_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive health index with interpretation."""

        # Calculate raw scores
        scores = {
            "overall": metrics.overall_health_index,
            "diversity": metrics.diversity_health,
            "influence": metrics.influence_balance,
            "trust": metrics.trust_stability,
            "quality": metrics.quality_integrity,
            "resilience": metrics.resilience,
        }

        # Determine health status
        health_status = self._determine_health_status(scores["overall"])

        # Analyze trends if history provided
        trends = {}
        if round_history:
            trends = self._analyze_trends(round_history)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(scores)

        # Calculate expected outcomes comparison
        expected_outcomes = self._compare_with_expected_outcomes(metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(scores, risk_factors)

        # Build health report
        health_report = {
            # Overall health
            "status": health_status.value,
            "index": scores["overall"],
            "interpretation": self._interpret_health_index(scores["overall"]),

            # Category breakdown
            "categories": {
                "diversity": {
                    "score": scores["diversity"],
                    "status": self._determine_category_status(scores["diversity"]),
                    "interpretation": self._interpret_category_score("diversity", scores["diversity"]),
                },
                "influence": {
                    "score": scores["influence"],
                    "status": self._determine_category_status(scores["influence"]),
                    "interpretation": self._interpret_category_score("influence", scores["influence"]),
                },
                "trust": {
                    "score": scores["trust"],
                    "status": self._determine_category_status(scores["trust"]),
                    "interpretation": self._interpret_category_score("trust", scores["trust"]),
                },
                "quality": {
                    "score": scores["quality"],
                    "status": self._determine_category_status(scores["quality"]),
                    "interpretation": self._interpret_category_score("quality", scores["quality"]),
                },
                "resilience": {
                    "score": scores["resilience"],
                    "status": self._determine_category_status(scores["resilience"]),
                    "interpretation": self._interpret_category_score("resilience", scores["resilience"]),
                },
            },

            # Trend analysis
            "trends": trends,

            # Risk assessment
            "risk_factors": risk_factors,
            "risk_level": self._calculate_risk_level(risk_factors),

            # Expected outcomes
            "expected_outcomes": expected_outcomes,

            # Recommendations
            "recommendations": recommendations,

            # Timestamp
            "calculated_at": datetime.utcnow().isoformat(),
        }

        return health_report

    def _determine_health_status(self, overall_score: float) -> HealthStatus:
        """Determine overall health status."""
        if overall_score >= self.thresholds.healthy_min:
            return HealthStatus.HEALTHY
        elif overall_score >= self.thresholds.stable_min:
            return HealthStatus.STABLE
        elif overall_score >= self.thresholds.degraded_min:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.FAILING

    def _determine_category_status(self, score: float) -> str:
        """Determine status for a specific category."""
        if score >= self.thresholds.healthy_min:
            return "healthy"
        elif score >= self.thresholds.stable_min:
            return "stable"
        elif score >= self.thresholds.degraded_min:
            return "degraded"
        else:
            return "failing"

    def _interpret_health_index(self, index: float) -> str:
        """Provide interpretation of overall health index."""
        if index >= 0.90:
            return "Excellent - federation is operating optimally"
        elif index >= 0.85:
            return "Very Good - federation is healthy with minor concerns"
        elif index >= 0.80:
            return "Good - federation is stable but could be improved"
        elif index >= 0.70:
            return "Acceptable - federation is stable but watch for degradation"
        elif index >= 0.60:
            return "Marginal - federation is showing signs of stress"
        elif index >= 0.50:
            return "Poor - federation is degraded and needs attention"
        else:
            return "Critical - federation is at risk of collapse"

    def _interpret_category_score(self, category: str, score: float) -> str:
        """Provide interpretation for category scores."""
        interpretations = {
            "diversity": {
                0.90: "Exceptional epistemic diversity",
                0.80: "Good diversity with minor concerns",
                0.70: "Acceptable diversity but watch for monoculture",
                0.60: "Diversity at risk - clustering detected",
                0.0: "Poor diversity - significant monoculture risk",
            },
            "influence": {
                0.90: "Perfectly balanced influence distribution",
                0.80: "Good balance with slight concentration",
                0.70: "Moderate concentration but acceptable",
                0.60: "Noticeable concentration needs attention",
                0.0: "Severe concentration imbalance",
            },
            "trust": {
                0.90: "Trust system is very stable and accurate",
                0.80: "Trust system is stable with minor drift",
                0.70: "Trust system shows acceptable volatility",
                0.60: "Trust system is unstable - anomalies detected",
                0.0: "Trust system is severely compromised",
            },
            "quality": {
                0.90: "Excellent quality filtering and integrity",
                0.80: "Good quality management with few issues",
                0.70: "Acceptable quality but false positives possible",
                0.60: "Quality issues detected - needs calibration",
                0.0: "Severe quality problems - system failing",
            },
            "resilience": {
                0.90: "Exceptional resilience under all conditions",
                0.80: "Good recovery from stress events",
                0.70: "Adequate resilience with some recovery time",
                0.60: "Poor recovery - extended degradation",
                0.0: "System collapse - no resilience",
            },
        }

        thresholds = interpretations.get(category, {})
        for threshold, interpretation in sorted(thresholds.items(), reverse=True):
            if score >= threshold:
                return interpretation

        return "Critical issues detected"

    def _analyze_trends(self, round_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends across simulation rounds."""
        trends = {}

        if not round_history:
            return trends

        # Overall trend
        health_scores = [round.get("overall_health", 0.0) for round in round_history]
        if health_scores:
            trends["overall"] = self._calculate_trend(health_scores)

        # Category trends
        categories = ["diversity", "influence", "trust", "quality", "resilience"]
        for category in categories:
            scores = [round.get(category, {}).get("score", 0.0) for round in round_history]
            if scores:
                trends[category] = self._calculate_trend(scores)

        # Key indicators trends
        trends["acceptance_rate"] = self._calculate_trend([
            round.get("acceptance_rate", 0.0) for round in round_history
        ])

        trends["concentration"] = self._calculate_trend([
            round.get("concentration_metrics", {}).get("gini_coefficient", 0.0)
            for round in round_history
        ])

        return trends

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend from a list of values."""
        if len(values) < 2:
            return {"direction": "unknown", "strength": 0.0}

        # Simple linear regression for trend
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xx = sum(xi * xi for xi in x)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Determine trend direction and strength
        if abs(slope) < 0.01:
            direction = "stable"
            strength = 0.0
        elif slope > 0:
            direction = "improving"
            strength = min(abs(slope) * 10, 1.0)  # Normalize to 0-1
        else:
            direction = "declining"
            strength = min(abs(slope) * 10, 1.0)

        return {
            "direction": direction,
            "strength": strength,
            "current": values[-1],
            "change": values[-1] - values[0] if len(values) > 1 else 0.0,
        }

    def _identify_risk_factors(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify risk factors in the federation."""
        risk_factors = []

        # Check for critical categories
        for category, score in scores.items():
            if score < self.thresholds.degraded_min:
                risk_factors.append({
                    "category": category,
                    "score": score,
                    "severity": "critical",
                    "description": f"{category.title()} is severely degraded",
                })
            elif score < self.thresholds.stable_min:
                risk_factors.append({
                    "category": category,
                    "score": score,
                    "severity": "high",
                    "description": f"{category.title()} is below stable threshold",
                })

        # Check for specific metrics
        if scores["diversity"] < 0.6:
            risk_factors.append({
                "category": "diversity",
                "metric": "topic_entropy",
                "severity": "high",
                "description": "Epistemic monoculture detected - risk of context collapse",
            })

        if scores["influence"] < 0.6:
            risk_factors.append({
                "category": "influence",
                "metric": "gini_coefficient",
                "severity": "high",
                "description": "Authority concentration detected - risk of centralization",
            })

        if scores["trust"] < 0.6:
            risk_factors.append({
                "category": "trust",
                "metric": "trust_drift",
                "severity": "critical",
                "description": "Trust system instability detected - risk of gaming",
            })

        # Sort risk factors by severity
        severity_order = {"critical": 3, "high": 2, "medium": 1}
        risk_factors.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)

        return risk_factors

    def _calculate_risk_level(self, risk_factors: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level."""
        if not risk_factors:
            return "low"

        critical_risks = [r for r in risk_factors if r["severity"] == "critical"]
        high_risks = [r for r in risk_factors if r["severity"] == "high"]

        if critical_risks:
            return "critical"
        elif len(high_risks) >= 2:
            return "high"
        elif high_risks:
            return "medium"
        else:
            return "low"

    def _compare_with_expected_outcomes(self, metrics: SimulationMetrics) -> Dict[str, Any]:
        """Compare results with expected outcomes."""
        comparisons = {}

        # Diversity comparisons
        if metrics.topic_entropy < 0.6:
            comparisons["diversity"] = {
                "expected": "healthy",
                "actual": "low",
                "issue": "Topic diversity below expected threshold",
            }

        # Influence comparisons
        if metrics.gini_coefficient > 0.6:
            comparisons["influence"] = {
                "expected": "balanced",
                "actual": "concentrated",
                "issue": "Gini coefficient exceeds threshold",
            }

        # Trust comparisons
        if metrics.trust_volatility > 0.3:
            comparisons["trust"] = {
                "expected": "stable",
                "actual": "volatile",
                "issue": "Trust volatility too high",
            }

        return comparisons

    def _generate_recommendations(self, scores: Dict[str, float], risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Priority-based recommendations based on risk factors
        for risk in risk_factors:
            category = risk["category"]

            if category == "diversity":
                recommendations.append(
                    "Implement additional viewpoint diversity safeguards - consider adjusting PluralityPreservationRules thresholds"
                )
            elif category == "influence":
                recommendations.append(
                    "Review AllocativeBoundaryGuard settings - consider tightening concentration thresholds"
                )
            elif category == "trust":
                recommendations.append(
                    "Increase TrustDecayModel sensitivity - adjust anomaly detection thresholds"
                )
            elif category == "quality":
                recommendations.append(
                    "Calibrate FederationEligibilityFilter - review spam detection parameters"
                )
            elif category == "resilience":
                recommendations.append(
                    "Implement circuit breakers for high-volume scenarios - add rate limiting safeguards"
                )

        # General recommendations based on overall score
        if scores["overall"] < 0.70:
            recommendations.append("Consider federation throttling to prevent overload")
        if scores["overall"] < 0.60:
            recommendations.append("Initiate federation recovery protocol")
        if scores["overall"] >= 0.90:
            recommendations.append("Federation operating optimally - maintain current configuration")

        return recommendations


# ============================================================================
# Health Status Tracker
# ============================================================================

@dataclass
class FederationHealthTracker:
    """Tracks federation health over time."""

    history: List[Dict[str, Any]] = field(default_factory=list)
    calculator: FederationHealthIndexCalculator = field(
        default_factory=FederationHealthIndexCalculator
    )

    def record_health_state(
        self,
        metrics: SimulationMetrics,
        scenario_name: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record a health state for tracking."""
        health_report = self.calculator.calculate_health_index(metrics)

        record = {
            "timestamp": timestamp or datetime.utcnow(),
            "scenario": scenario_name,
            "health_index": health_report["index"],
            "status": health_report["status"],
            "risk_level": health_report["risk_level"],
            "categories": {
                cat: data["score"] for cat, data in health_report["categories"].items()
            },
            "risk_factors_count": len(health_report["risk_factors"]),
        }

        self.history.append(record)

    def get_health_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get health trend over specified days."""
        if not self.history:
            return {"trend": "unknown", "change": 0.0}

        # Filter recent history
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_history = [
            record for record in self.history
            if record["timestamp"] >= cutoff
        ]

        if not recent_history:
            return {"trend": "unknown", "change": 0.0}

        # Calculate trend
        first_index = recent_history[0]["health_index"]
        last_index = recent_history[-1]["health_index"]
        change = last_index - first_index

        if abs(change) < 0.05:
            trend = "stable"
        elif change > 0:
            trend = "improving"
        else:
            trend = "declining"

        return {
            "trend": trend,
            "change": change,
            "current": last_index,
            "average": sum(r["health_index"] for r in recent_history) / len(recent_history),
            "days_tracked": len(recent_history),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get health statistics across all tracked states."""
        if not self.history:
            return {"total_records": 0}

        health_indices = [record["health_index"] for record in self.history]
        statuses = [record["status"] for record in self.history]
        risk_levels = [record["risk_level"] for record in self.history]

        return {
            "total_records": len(self.history),
            "average_health_index": sum(health_indices) / len(health_indices),
            "min_health_index": min(health_indices),
            "max_health_index": max(health_indices),
            "status_distribution": {
                status: statuses.count(status) for status in set(statuses)
            },
            "risk_level_distribution": {
                level: risk_levels.count(level) for level in set(risk_levels)
            },
        }