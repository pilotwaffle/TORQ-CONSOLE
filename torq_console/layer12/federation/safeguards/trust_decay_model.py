"""
Trust Decay Model

Phase 1B Hardening - Detect trust drift and anomalous patterns.

This model tracks trust score evolution over time to detect:
- Sudden trust spikes (possible gaming or collusion)
- Gradual trust erosion (quality decline or node degradation)
- Anomalous trust patterns (suspicious behavior)
- Prediction of future trust trajectory

Without this safeguard, compromised or degraded nodes could maintain
elevated trust scores beyond their warranted level, or malicious actors
could artificially inflate trust through collusion or gaming.
"""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedArtifactPayload

logger = logging.getLogger(__name__)


# ============================================================================
# Trust Tracking Types
# ============================================================================

class TrustObservation(BaseModel):
    """A single observation of a node's trust score."""

    timestamp: datetime = Field(..., description="When observed")
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Trust score")
    claim_count: int = Field(default=0, description="Claims contributing to score")
    accepted_count: int = Field(default=0, description="Claims accepted")
    rejected_count: int = Field(default=0, description="Claims rejected")
    trigger_event: str | None = Field(
        None,
        description="Event that triggered this observation"
    )


class TrustTrajectory(BaseModel):
    """
    Analysis of a node's trust trajectory.
    """

    node_id: str = Field(..., description="Node identifier")

    # Current state
    current_trust: float = Field(..., ge=0.0, le=1.0, description="Current trust score")
    observation_count: int = Field(default=0, description="Number of observations")

    # Trend analysis
    trend_direction: Literal["increasing", "stable", "decreasing", "volatile"] = Field(
        ...,
        description="Overall trend direction"
    )
    trend_strength: float = Field(
        ...,
        ge=0.0,
        description="Strength of trend (0 = no trend, 1 = strong trend)"
    )
    velocity: float = Field(
        ...,
        description="Rate of change per observation (positive = gaining trust)"
    )

    # Anomaly detection
    is_anomalous: bool = Field(default=False, description="Trust pattern is anomalous")
    anomaly_type: Literal["sudden_spike", "sudden_drop", "volatility", "none"] = Field(
        default="none",
        description="Type of anomaly detected"
    )
    anomaly_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence that this is an anomaly (1.0 = certain)"
    )

    # Prediction
    predicted_trust: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Predicted trust score at next observation"
    )
    prediction_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in prediction"
    )

    # Risk assessment
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        default="low",
        description="Risk level based on trust trajectory"
    )


class TrustDecayAssessment(BaseModel):
    """Assessment of trust decay for a claim submission."""

    artifact_id: str = Field(..., description="Artifact being assessed")
    node_id: str = Field(..., description="Submitting node")

    # Trust status
    current_trust: float = Field(..., ge=0.0, le=1.0, description="Current trust score")
    trajectory: TrustTrajectory | None = Field(None, description="Trust trajectory analysis")

    # Decay detection
    is_decaying: bool = Field(default=False, description="Trust is decaying")
    decay_rate: float = Field(
        default=0.0,
        description="Rate of decay per day (negative = gaining trust)"
    )

    # Action recommendation
    recommendation: Literal["allow", "caution", "reject"] = Field(
        ...,
        description="Recommended action"
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for recommendation"
    )

    # Adjusted trust (for this submission)
    adjusted_trust: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Trust score adjusted for trajectory"
    )

    # Assessment timestamp
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Trust Decay Configuration
# ============================================================================

class TrustDecayConfig(BaseModel):
    """Configuration for trust decay modeling."""

    # Observation tracking
    max_observations: int = Field(
        100,
        ge=10,
        description="Maximum observations to keep per node"
    )
    min_observations_for_analysis: int = Field(
        5,
        ge=3,
        description="Minimum observations required for trajectory analysis"
    )

    # Anomaly thresholds
    sudden_change_threshold: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Change threshold for sudden spike/drop detection"
    )
    volatility_threshold: float = Field(
        0.2,
        ge=0.0,
        description="Std dev threshold for volatility detection"
    )

    # Decay thresholds
    decay_rate_threshold: float = Field(
        -0.05,
        description="Decay rate below which node is considered decaying per day"
    )
    critical_trust_threshold: float = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Trust below which node is critical"
    )

    # Adjustment factors
    decaying_node_discount: float = Field(
        0.8,
        ge=0.0,
        le=1.0,
        description="Discount factor for decaying nodes"
    )
    anomalous_node_discount: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Discount factor for anomalous nodes"
    )

    # Analysis window
    analysis_window_hours: int = Field(
        24,
        ge=1,
        description="Hours to look back for trust history"
    )


# ============================================================================
# Trust Decay Model
# ============================================================================

class TrustDecayModel:
    """
    Models trust score evolution and detects anomalous patterns.

    This safeguard operates AFTER trust evaluation but
    INFLUENCES the effective trust used for decisions.

    It does not replace the trust evaluation system but
    provides temporal context and anomaly detection.
    """

    def __init__(
        self,
        config: TrustDecayConfig | None = None,
    ):
        """
        Initialize the trust decay model.

        Args:
            config: Model configuration
        """
        self.config = config or TrustDecayConfig()
        self.logger = logging.getLogger(__name__)

        # Trust history per node (deque for efficient popping)
        self._trust_history: dict[str, deque[TrustObservation]] = {}

        # Statistics
        self._total_assessments = 0
        self._total_decaying_detected = 0
        self._total_anomalies_detected = 0

    def assess_trust_decay(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        source_node_id: str,
        current_trust: float,
        claim_accepted: bool = True,
    ) -> TrustDecayAssessment:
        """
        Assess trust decay for a claim submission.

        Args:
            artifact: The artifact payload being submitted
            envelope_id: Envelope ID
            source_node_id: Source node ID
            current_trust: Node's current trust score
            claim_accepted: Whether this claim was accepted

        Returns:
            TrustDecayAssessment with trajectory analysis
        """
        self._total_assessments += 1

        # Record observation
        self._record_observation(
            source_node_id,
            current_trust,
            accepted=claim_accepted,
        )

        # Analyze trajectory
        trajectory = self._analyze_trajectory(source_node_id)

        # Detect decay
        is_decaying, decay_rate = self._detect_decay(source_node_id)

        # Determine recommendation
        recommendation, reasons, adjusted_trust = self._make_recommendation(
            current_trust,
            trajectory,
            is_decaying,
            decay_rate,
        )

        # Update statistics
        if is_decaying:
            self._total_decaying_detected += 1
        if trajectory and trajectory.is_anomalous:
            self._total_anomalies_detected += 1

        assessment = TrustDecayAssessment(
            artifact_id=artifact.artifact_id,
            node_id=source_node_id,
            current_trust=current_trust,
            trajectory=trajectory,
            is_decaying=is_decaying,
            decay_rate=decay_rate,
            recommendation=recommendation,  # type: ignore
            reasons=reasons,
            adjusted_trust=adjusted_trust,
        )

        self.logger.info(
            f"Trust decay assessment for {artifact.artifact_id}: "
            f"node={source_node_id}, trust={current_trust:.2f}, "
            f"adjusted={adjusted_trust:.2f}, recommendation={recommendation}"
        )

        return assessment

    def _record_observation(
        self,
        node_id: str,
        trust_score: float,
        accepted: bool = True,
        trigger_event: str | None = None,
    ) -> None:
        """
        Record a trust observation for a node.

        Args:
            node_id: Node identifier
            trust_score: Current trust score
            accepted: Whether claim was accepted
            trigger_event: Optional trigger event
        """
        if node_id not in self._trust_history:
            self._trust_history[node_id] = deque(maxlen=self.config.max_observations)

        # Get current counts
        history = self._trust_history[node_id]
        claim_count = history[-1].claim_count + 1 if history else 1

        accepted_count = history[-1].accepted_count + (1 if accepted else 0) if history else (1 if accepted else 0)
        rejected_count = history[-1].rejected_count + (0 if accepted else 1) if history else (0 if accepted else 1)

        observation = TrustObservation(
            timestamp=datetime.utcnow(),
            trust_score=trust_score,
            claim_count=claim_count,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            trigger_event=trigger_event,
        )

        self._trust_history[node_id].append(observation)

    def _analyze_trajectory(self, node_id: str) -> TrustTrajectory | None:
        """
        Analyze a node's trust trajectory.

        Args:
            node_id: Node to analyze

        Returns:
            TrustTrajectory with trend analysis, or None if insufficient data
        """
        history = self._trust_history.get(node_id)

        if not history or len(history) < self.config.min_observations_for_analysis:
            return None

        observations = list(history)
        current_trust = observations[-1].trust_score

        # Calculate trend using linear regression
        n = len(observations)
        x = list(range(n))
        y = [obs.trust_score for obs in observations]

        # Simple linear regression
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xx = sum(xi * xi for xi in x)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Determine trend direction
        if abs(slope) < 0.01:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

        # Calculate trend strength (R-squared approximation)
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((y[i] - (slope * x[i] + (sum_y - slope * sum_x) / n)) ** 2 for i in range(n))
        trend_strength = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate velocity (change per observation)
        velocity = slope

        # Detect anomalies
        is_anomalous, anomaly_type, anomaly_score = self._detect_anomalies(observations)

        # Predict next trust score
        predicted_trust = current_trust + slope
        predicted_trust = max(0.0, min(1.0, predicted_trust))
        prediction_confidence = trend_strength

        # Determine risk level
        risk_level: Literal["low", "medium", "high", "critical"] = "low"
        if is_anomalous and anomaly_type == "sudden_drop":
            risk_level = "critical"
        elif is_decaying := slope < self.config.decay_rate_threshold:
            risk_level = "high" if slope < self.config.decay_rate_threshold * 2 else "medium"
        elif current_trust < self.config.critical_trust_threshold:
            risk_level = "high"
        elif is_anomalous:
            risk_level = "medium"

        return TrustTrajectory(
            node_id=node_id,
            current_trust=current_trust,
            observation_count=n,
            trend_direction=trend_direction,  # type: ignore
            trend_strength=trend_strength,
            velocity=velocity,
            is_anomalous=is_anomalous,
            anomaly_type=anomaly_type,  # type: ignore
            anomaly_score=anomaly_score,
            predicted_trust=predicted_trust,
            prediction_confidence=prediction_confidence,
            risk_level=risk_level,  # type: ignore
        )

    def _detect_anomalies(
        self,
        observations: list[TrustObservation],
    ) -> tuple[bool, Literal["sudden_spike", "sudden_drop", "volatility", "none"], float]:
        """
        Detect anomalous trust patterns.

        Args:
            observations: Trust observations to analyze

        Returns:
            Tuple of (is_anomalous, anomaly_type, anomaly_score)
        """
        if len(observations) < 3:
            return False, "none", 0.0

        # Check for sudden spike/drop
        recent = observations[-1].trust_score
        previous = observations[-2].trust_score if len(observations) >= 2 else recent

        change = abs(recent - previous)

        if change > self.config.sudden_change_threshold:
            anomaly_type: Literal["sudden_spike", "sudden_drop", "volatility", "none"]
            if recent > previous:
                anomaly_type = "sudden_spike"
            else:
                anomaly_type = "sudden_drop"
            return True, anomaly_type, min(1.0, change / self.config.sudden_change_threshold)

        # Check for volatility
        scores = [obs.trust_score for obs in observations]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        if std_dev > self.config.volatility_threshold:
            return True, "volatility", min(1.0, std_dev / self.config.volatility_threshold)

        return False, "none", 0.0

    def _detect_decay(self, node_id: str) -> tuple[bool, float]:
        """
        Detect if a node's trust is decaying.

        Args:
            node_id: Node to check

        Returns:
            Tuple of (is_decaying, decay_rate_per_day)
        """
        history = self._trust_history.get(node_id)

        if not history or len(history) < 3:
            return False, 0.0

        observations = list(history)

        # Calculate decay rate over time
        first = observations[0]
        last = observations[-1]

        time_delta_hours = (last.timestamp - first.timestamp).total_seconds() / 3600
        time_delta_days = time_delta_hours / 24

        if time_delta_days < 0.01:  # Less than ~15 minutes
            return False, 0.0

        trust_delta = last.trust_score - first.trust_score
        decay_rate = trust_delta / time_delta_days

        return decay_rate < self.config.decay_rate_threshold, decay_rate

    def _make_recommendation(
        self,
        current_trust: float,
        trajectory: TrustTrajectory | None,
        is_decaying: bool,
        decay_rate: float,
    ) -> tuple[Literal["allow", "caution", "reject"], list[str], float]:
        """
        Make a recommendation based on trust decay analysis.

        Args:
            current_trust: Current trust score
            trajectory: Trust trajectory analysis
            is_decaying: Whether trust is decaying
            decay_rate: Rate of decay

        Returns:
            Tuple of (recommendation, reasons, adjusted_trust)
        """
        reasons: list[str] = []
        adjusted_trust = current_trust
        recommendation: Literal["allow", "caution", "reject"] = "allow"

        # Check for critical trust
        if current_trust < self.config.critical_trust_threshold:
            recommendation = "reject"
            adjusted_trust = current_trust * 0.5
            reasons.append(
                f"Critical trust level: {current_trust:.2f} < {self.config.critical_trust_threshold:.2f}"
            )

        # Check for anomalies
        elif trajectory and trajectory.is_anomalous:
            if trajectory.anomaly_type == "sudden_drop":
                recommendation = "reject"
                adjusted_trust = current_trust * self.config.anomalous_node_discount
                reasons.append(f"Sudden trust drop detected: {trajectory.velocity:.3f} per observation")
            elif trajectory.anomaly_type == "sudden_spike":
                recommendation = "caution"
                adjusted_trust = current_trust * 0.8
                reasons.append("Sudden trust spike detected - possible gaming or collusion")
            else:  # volatility
                recommendation = "caution"
                adjusted_trust = current_trust * 0.9
                reasons.append("High trust volatility detected")

        # Check for decay
        elif is_decaying:
            if decay_rate < self.config.decay_rate_threshold * 2:
                recommendation = "caution"
                adjusted_trust = current_trust * self.config.decaying_node_discount
                reasons.append(f"Trust decaying at {decay_rate:.3f} per day")
            else:
                recommendation = "allow"
                reasons.append("Mild trust decay detected")

        # Check trend direction
        elif trajectory and trajectory.trend_direction == "decreasing":
            if trajectory.risk_level in ("high", "critical"):
                recommendation = "caution"
                adjusted_trust = current_trust * 0.9
                reasons.append("Downward trust trend detected")

        # Positive feedback for healthy nodes
        if recommendation == "allow":
            if trajectory and trajectory.trend_direction == "increasing":
                reasons.append("Trust trending upward - healthy node")
            else:
                reasons.append("Trust stable - no concerns")

        return recommendation, reasons, max(0.0, min(1.0, adjusted_trust))

    def get_statistics(self) -> dict:
        """Get model statistics."""
        # Clean old observations
        self._cleanup_old_observations()

        node_trajectories = []
        for node_id, history in self._trust_history.items():
            if len(history) >= self.config.min_observations_for_analysis:
                trajectory = self._analyze_trajectory(node_id)
                if trajectory:
                    node_trajectories.append({
                        "nodeId": node_id,
                        "currentTrust": trajectory.current_trust,
                        "trend": trajectory.trend_direction,
                        "velocity": trajectory.velocity,
                        "isAnomalous": trajectory.is_anomalous,
                        "riskLevel": trajectory.risk_level,
                    })

        return {
            "totalAssessments": self._total_assessments,
            "decayingDetected": self._total_decaying_detected,
            "anomaliesDetected": self._total_anomalies_detected,
            "trackedNodes": len(self._trust_history),
            "nodeTrajectories": node_trajectories[:50],  # Top 50
        }

    def _cleanup_old_observations(self) -> None:
        """Remove observations outside the analysis window."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.analysis_window_hours)

        for node_id in list(self._trust_history.keys()):
            history = self._trust_history[node_id]

            # Remove old observations
            while history and history[0].timestamp < cutoff:
                history.popleft()

            # Remove empty histories
            if not history:
                del self._trust_history[node_id]

    def get_node_trust_report(self, node_id: str) -> dict:
        """
        Get detailed trust report for a specific node.

        Args:
            node_id: Node to report on

        Returns:
            Detailed trust report
        """
        history = self._trust_history.get(node_id)

        if not history:
            return {
                "nodeId": node_id,
                "error": "No trust history found",
            }

        trajectory = self._analyze_trajectory(node_id)
        is_decaying, decay_rate = self._detect_decay(node_id)

        return {
            "nodeId": node_id,
            "currentTrust": history[-1].trust_score,
            "observationCount": len(history),
            "oldestObservation": history[0].timestamp.isoformat(),
            "newestObservation": history[-1].timestamp.isoformat(),
            "trajectory": {
                "trend": trajectory.trend_direction if trajectory else "unknown",
                "velocity": trajectory.velocity if trajectory else 0.0,
                "isAnomalous": trajectory.is_anomalous if trajectory else False,
                "anomalyType": trajectory.anomaly_type if trajectory else "none",
                "predictedTrust": trajectory.predicted_trust if trajectory else history[-1].trust_score,
                "riskLevel": trajectory.risk_level if trajectory else "low",
            },
            "decay": {
                "isDecaying": is_decaying,
                "decayRate": decay_rate,
            },
            "recentObservations": [
                {
                    "timestamp": obs.timestamp.isoformat(),
                    "trustScore": obs.trust_score,
                    "claimCount": obs.claim_count,
                }
                for obs in list(history)[-10:]  # Last 10
            ],
        }


def create_trust_decay_model(
    config: TrustDecayConfig | None = None,
) -> TrustDecayModel:
    """
    Factory function to create a TrustDecayModel.

    Args:
        config: Model configuration

    Returns:
        Configured TrustDecayModel instance
    """
    return TrustDecayModel(config=config)
