"""
TORQ Layer 8 - Pattern Validator

L8-M1: Validates pattern predictions and tracks accuracy.

The PatternValidator evaluates whether discovered patterns
accurately predict outcomes and adjusts confidence accordingly.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from ..autonomous_models import (
    PatternValidation,
    PatternValidationStatus,
    PatternAccuracyMetrics,
    PatternDriftDetection,
)


# ============================================================================
# Prediction Record
# ============================================================================

class PatternPrediction(BaseModel):
    """A prediction made by a pattern."""
    prediction_id: str
    pattern_id: str
    mission_id: str
    predicted_outcome: str
    confidence: float
    made_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Pattern Validator
# ============================================================================

class PatternValidator:
    """
    Validates pattern predictions and tracks accuracy.

    Maintains accuracy metrics for each pattern and detects
    drift over time.
    """

    def __init__(self):
        """Initialize the pattern validator."""
        # Pattern validations
        self._validations: Dict[str, PatternValidation] = {}

        # Prediction records
        self._predictions: List[PatternPrediction] = []

        # Pattern accuracy tracking
        self._pattern_accuracy: Dict[str, List[bool]] = defaultdict(list)

        # Drift tracking
        self._baseline_accuracy: Dict[str, float] = {}
        self._accuracy_history: Dict[str, List[float]] = defaultdict(list)

    async def record_prediction(
        self,
        pattern_id: str,
        mission_id: str,
        predicted_outcome: str,
        confidence: float,
    ) -> PatternPrediction:
        """
        Record a pattern prediction.

        Args:
            pattern_id: ID of the pattern making the prediction
            mission_id: ID of the mission being predicted
            predicted_outcome: The predicted outcome
            confidence: Prediction confidence (0-1)

        Returns:
            PatternPrediction record
        """
        prediction = PatternPrediction(
            prediction_id=str(uuid4()),
            pattern_id=pattern_id,
            mission_id=mission_id,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
        )

        self._predictions.append(prediction)
        logger.debug(
            f"[PatternValidator] Recorded prediction: {pattern_id} -> {predicted_outcome}"
        )

        return prediction

    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: str,
    ) -> PatternValidation:
        """
        Validate a prediction against actual outcome.

        Args:
            prediction_id: ID of the prediction to validate
            actual_outcome: The actual outcome that occurred

        Returns:
            PatternValidation with updated metrics
        """
        # Find the prediction
        prediction = None
        for p in self._predictions:
            if p.prediction_id == prediction_id:
                prediction = p
                break

        if not prediction:
            raise ValueError(f"Prediction not found: {prediction_id}")

        # Check if correct
        is_correct = (prediction.predicted_outcome == actual_outcome)

        # Track accuracy
        self._pattern_accuracy[prediction.pattern_id].append(is_correct)

        # Get or create validation
        validation = self._validations.get(prediction.pattern_id)
        if not validation:
            validation = PatternValidation(
                pattern_id=prediction.pattern_id,
                validation_status=PatternValidationStatus.PENDING,
                original_confidence=prediction.confidence,
                current_confidence=prediction.confidence,
            )
            self._validations[prediction.pattern_id] = validation

        # Update accuracy metrics
        metrics = validation.accuracy_metrics
        metrics.total_predictions += 1
        if is_correct:
            metrics.correct_predictions += 1
            validation.supporting_outcomes.append(prediction.mission_id)
        else:
            validation.false_positives += 1
            validation.contradicting_outcomes.append(prediction.mission_id)

        metrics.calculate_derived_metrics()

        # Update validation status based on accuracy
        validation = self._update_validation_status(validation, metrics)

        # Set next review time
        validation.next_review_at = datetime.now() + timedelta(hours=24)

        logger.info(
            f"[PatternValidator] Validated {prediction.pattern_id}: "
            f"correct={is_correct}, accuracy={metrics.accuracy:.2f}"
        )

        return validation

    async def validate_pattern(
        self,
        pattern_id: str,
        supporting_outcomes: List[str],
        contradicting_outcomes: List[str],
        current_confidence: float,
    ) -> PatternValidation:
        """
        Create or update a pattern validation.

        Args:
            pattern_id: ID of the pattern
            supporting_outcomes: Outcomes that support the pattern
            contradicting_outcomes: Outcomes that contradict the pattern
            current_confidence: Current confidence in the pattern

        Returns:
            PatternValidation
        """
        # Get or create validation
        validation = self._validations.get(pattern_id)
        if not validation:
            validation = PatternValidation(
                pattern_id=pattern_id,
                validation_status=PatternValidationStatus.PENDING,
                original_confidence=current_confidence,
                current_confidence=current_confidence,
            )

        # Update outcomes
        validation.supporting_outcomes = supporting_outcomes
        validation.contradicting_outcomes = contradicting_outcomes

        # Calculate metrics
        metrics = validation.accuracy_metrics
        metrics.total_predictions = len(supporting_outcomes) + len(contradicting_outcomes)
        metrics.correct_predictions = len(supporting_outcomes)
        metrics.false_positives = len(contradicting_outcomes)
        metrics.false_negatives = 0  # Not tracked in this mode

        metrics.calculate_derived_metrics()

        # Update confidence based on accuracy
        validation.current_confidence = max(0.0, min(1.0, metrics.accuracy))

        # Calculate confidence adjustment
        validation.confidence_adjustment = (
            validation.current_confidence - validation.original_confidence
        )

        # Update validation status
        validation = self._update_validation_status(validation, metrics)

        # Check for drift
        if pattern_id in self._baseline_accuracy:
            validation.drift_detection = self._detect_drift(
                pattern_id,
                validation.current_confidence,
            )

        self._validations[pattern_id] = validation

        logger.info(
            f"[PatternValidator] Validated {pattern_id}: "
            f"status={validation.validation_status.value}, "
            f"accuracy={metrics.accuracy:.2f}"
        )

        return validation

    def _update_validation_status(
        self,
        validation: PatternValidation,
        metrics: PatternAccuracyMetrics,
    ) -> PatternValidation:
        """Update validation status based on accuracy metrics."""
        if metrics.f1_score >= 0.8:
            validation.validation_status = PatternValidationStatus.VALIDATED
        elif metrics.f1_score >= 0.6:
            validation.validation_status = PatternValidationStatus.STRENGTHENED
        elif metrics.f1_score >= 0.4:
            validation.validation_status = PatternValidationStatus.WEAKENED
        elif metrics.f1_score < 0.2:
            validation.validation_status = PatternValidationStatus.DISPROVEN
        else:
            validation.validation_status = PatternValidationStatus.PENDING

        return validation

    def _detect_drift(
        self,
        pattern_id: str,
        current_accuracy: float,
    ) -> PatternDriftDetection:
        """Detect if a pattern's accuracy has drifted."""
        baseline = self._baseline_accuracy.get(pattern_id, current_accuracy)

        # Track history
        self._accuracy_history[pattern_id].append(current_accuracy)
        history = self._accuracy_history[pattern_id]

        # Calculate drift magnitude
        drift_magnitude = abs(current_accuracy - baseline)

        # Determine trend
        if len(history) >= 3:
            recent = history[-3:]
            if recent[-1] > recent[0] + 0.1:
                trend = "improving"
            elif recent[-1] < recent[0] - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine severity
        if drift_magnitude > 0.3:
            severity = "high"
        elif drift_magnitude > 0.15:
            severity = "medium"
        elif drift_magnitude > 0.05:
            severity = "low"
        else:
            severity = "none"

        return PatternDriftDetection(
            pattern_id=pattern_id,
            current_accuracy=current_accuracy,
            baseline_accuracy=baseline,
            drift_magnitude=drift_magnitude,
            accuracy_trend=trend,
            trend_confidence=min(1.0, len(history) / 10),
            drift_detected=(severity != "none"),
            drift_severity=severity,
            recommendation=self._get_drift_recommendation(severity, trend),
        )

    def _get_drift_recommendation(self, severity: str, trend: str) -> Optional[str]:
        """Get recommendation for drift."""
        if severity == "high":
            if trend == "declining":
                return "Pattern degrading - consider retirement or retraining"
            else:
                return "Significant accuracy change - review pattern"
        elif severity == "medium":
            return "Monitor pattern accuracy closely"
        else:
            return None

    async def get_validation(
        self,
        pattern_id: str,
    ) -> Optional[PatternValidation]:
        """Get validation for a specific pattern."""
        return self._validations.get(pattern_id)

    async def get_all_validations(
        self,
        status: Optional[PatternValidationStatus] = None,
    ) -> List[PatternValidation]:
        """
        Get all pattern validations.

        Args:
            status: Optional filter by validation status

        Returns:
            List of validations
        """
        validations = list(self._validations.values())

        if status:
            validations = [v for v in validations if v.validation_status == status]

        return validations

    async def get_drifted_patterns(
        self,
        min_severity: str = "low",
    ) -> List[PatternDriftDetection]:
        """
        Get patterns that have drifted.

        Args:
            min_severity: Minimum severity level (low, medium, high)

        Returns:
            List of drift detections
        """
        severity_levels = {"low": 1, "medium": 2, "high": 3}
        min_level = severity_levels.get(min_severity, 1)

        drifted = []
        for validation in self._validations.values():
            if validation.drift_detection:
                level = severity_levels.get(
                    validation.drift_detection.drift_severity,
                    0
                )
                if level >= min_level:
                    drifted.append(validation.drift_detection)

        return drifted

    async def set_baseline(
        self,
        pattern_id: str,
        baseline_accuracy: float,
    ):
        """Set the baseline accuracy for drift detection."""
        self._baseline_accuracy[pattern_id] = baseline_accuracy

    async def get_accuracy_summary(self) -> Dict[str, Any]:
        """Get summary of pattern accuracy across all patterns."""
        if not self._validations:
            return {
                "total_patterns": 0,
                "avg_accuracy": 0.0,
                "high_confidence_patterns": 0,
                "by_status": {},
            }

        accuracies = [
            v.current_confidence
            for v in self._validations.values()
        ]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

        high_confidence = sum(
            1 for v in self._validations.values()
            if v.current_confidence >= 0.8
        )

        by_status = defaultdict(int)
        for v in self._validations.values():
            by_status[v.validation_status.value] += 1

        return {
            "total_patterns": len(self._validations),
            "avg_accuracy": avg_accuracy,
            "high_confidence_patterns": high_confidence,
            "by_status": dict(by_status),
        }


# Global pattern validator instance
_validator: Optional[PatternValidator] = None


def get_pattern_validator() -> PatternValidator:
    """Get the global pattern validator instance."""
    global _validator
    if _validator is None:
        _validator = PatternValidator()
    return _validator
