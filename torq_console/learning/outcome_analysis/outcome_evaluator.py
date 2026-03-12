"""
TORQ Layer 8 - Outcome Evaluator

L8-M1: Evaluates mission outcomes and generates improvement candidates.

Analyzes execution results to measure success, detect patterns,
and identify operational improvements.
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
    OutcomeEvaluation,
    OutcomeCategory,
    PerformanceMetrics,
    ImprovementCandidate,
)


# ============================================================================
# Mission Result Model
# ============================================================================

class MissionResult(BaseModel):
    """Raw result from a mission execution."""
    mission_id: str
    execution_id: str

    # Outcome
    status: str  # "completed", "failed", "timeout", "cancelled"
    result_data: Dict[str, Any] = Field(default_factory=dict)

    # Performance
    duration_seconds: float = 0.0
    token_count: int = 0
    tool_calls: int = 0
    error_count: int = 0

    # Quality
    output_quality_score: Optional[float] = None

    # Timing
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime = Field(default_factory=datetime.now)

    # Context
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    predicted_outcome: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Outcome Analyzer
# ============================================================================

class OutcomeAnalyzer:
    """
    Analyzes mission execution outcomes.

    Evaluates success, compares predictions, detects patterns,
    and generates improvement candidates.
    """

    def __init__(self):
        """Initialize the outcome analyzer."""
        # Storage for evaluations
        self._evaluations: Dict[str, OutcomeEvaluation] = {}

        # Pattern detection
        self._outcome_patterns: Dict[str, List[str]] = defaultdict(list)
        self._failure_patterns: Dict[str, List[str]] = defaultdict(list)

        # Statistics
        self._total_evaluated = 0
        self._success_count = 0
        self._failure_count = 0

    async def evaluate_outcome(
        self,
        result: MissionResult,
    ) -> OutcomeEvaluation:
        """
        Evaluate a mission execution outcome.

        Args:
            result: Mission execution result

        Returns:
            OutcomeEvaluation with analysis
        """
        # Determine outcome category
        category = self._classify_outcome(result)

        # Calculate success score
        success_score = self._calculate_success_score(result, category)

        # Build performance metrics
        metrics = PerformanceMetrics(
            duration_seconds=result.duration_seconds,
            token_count=result.token_count,
            tool_calls=result.tool_calls,
            error_count=result.error_count,
            output_quality_score=result.output_quality_score or 0.0,
            tasks_completed=len(result.result_data.get("tasks", [])),
        )

        # Calculate tasks per minute
        if metrics.duration_seconds > 0:
            metrics.tasks_per_minute = (metrics.tasks_completed / metrics.duration_seconds) * 60

        # Get actual outcome
        actual_outcome = result.status

        # Check prediction match
        predicted_outcome = result.predicted_outcome or "unknown"
        prediction_match = (predicted_outcome == actual_outcome)
        prediction_accuracy = 1.0 if prediction_match else 0.0

        # Detect patterns
        detected_patterns = await self._detect_patterns(result, category)

        # Generate improvement candidates
        improvement_candidates = await self._generate_improvements(
            result, category, success_score, detected_patterns
        )

        # Create evaluation
        evaluation = OutcomeEvaluation(
            mission_id=result.mission_id,
            execution_id=result.execution_id,
            predicted_outcome=predicted_outcome,
            actual_outcome=actual_outcome,
            outcome_category=category,
            success_score=success_score,
            performance_metrics=metrics,
            predicted_vs_actual_match=prediction_match,
            prediction_accuracy=prediction_accuracy,
            detected_patterns=detected_patterns,
            improvement_candidates=improvement_candidates,
            mission_completed_at=result.completed_at,
            agent_id=result.agent_id,
            workflow_id=result.workflow_id,
        )

        # Store evaluation
        self._evaluations[str(evaluation.evaluation_id)] = evaluation
        self._total_evaluated += 1

        if success_score >= 0.5:
            self._success_count += 1
        else:
            self._failure_count += 1

        # Track patterns
        for pattern in detected_patterns:
            self._outcome_patterns[pattern].append(result.execution_id)

        logger.info(
            f"[OutcomeAnalyzer] Evaluated {result.execution_id}: "
            f"score={success_score:.2f}, category={category.value}"
        )

        return evaluation

    def _classify_outcome(self, result: MissionResult) -> OutcomeCategory:
        """Classify the outcome category."""
        if result.status == "completed" and result.error_count == 0:
            return OutcomeCategory.SUCCESS
        elif result.status == "completed" and result.error_count > 0:
            return OutcomeCategory.PARTIAL_SUCCESS
        elif result.status == "timeout":
            return OutcomeCategory.TIMEOUT
        elif result.status == "cancelled":
            return OutcomeCategory.CANCELLED
        elif result.status == "failed":
            return OutcomeCategory.FAILURE
        else:
            return OutcomeCategory.ERROR

    def _calculate_success_score(
        self,
        result: MissionResult,
        category: OutcomeCategory,
    ) -> float:
        """
        Calculate a success score (0.0 to 1.0).

        Combines status, errors, and quality indicators.
        """
        score = 0.0

        # Base score from category
        category_scores = {
            OutcomeCategory.SUCCESS: 1.0,
            OutcomeCategory.PARTIAL_SUCCESS: 0.6,
            OutcomeCategory.FAILURE: 0.2,
            OutcomeCategory.TIMEOUT: 0.3,
            OutcomeCategory.ERROR: 0.1,
            OutcomeCategory.CANCELLED: 0.0,
        }
        score = category_scores.get(category, 0.0)

        # Penalize errors
        error_penalty = min(result.error_count * 0.1, 0.5)
        score -= error_penalty

        # Quality bonus
        if result.output_quality_score is not None:
            quality_bonus = (result.output_quality_score - 0.5) * 0.3
            score += quality_bonus

        # Ensure bounds
        return max(0.0, min(1.0, score))

    async def _detect_patterns(
        self,
        result: MissionResult,
        category: OutcomeCategory,
    ) -> List[str]:
        """Detect patterns in the outcome."""
        patterns = []

        # Error patterns
        if result.error_count > 3:
            patterns.append("high_error_rate")

        # Timeout patterns
        if category == OutcomeCategory.TIMEOUT:
            patterns.append("timeout_pattern")

        # Long duration patterns
        if result.duration_seconds > 300:  # 5 minutes
            patterns.append("long_execution_time")

        # High token usage
        if result.token_count > 10000:
            patterns.append("high_token_usage")

        # Tool efficiency
        if result.tool_calls > 20:
            patterns.append("excessive_tool_calls")

        # Agent-specific patterns
        if result.agent_id:
            agent_evals = [
                e for e in self._evaluations.values()
                if e.agent_id == result.agent_id
            ]
            if agent_evals:
                recent_scores = [e.success_score for e in agent_evals[-5:]]
                avg_score = sum(recent_scores) / len(recent_scores)
                if avg_score < 0.5:
                    patterns.append(f"agent_{result.agent_id}_underperforming")

        return patterns

    async def _generate_improvements(
        self,
        result: MissionResult,
        category: OutcomeCategory,
        success_score: float,
        patterns: List[str],
    ) -> List[ImprovementCandidate]:
        """Generate improvement candidates from the analysis."""
        candidates = []

        # Error handling improvements
        if result.error_count > 2:
            candidates.append(ImprovementCandidate(
                category="workflow",
                description=f"High error rate ({result.error_count} errors) detected",
                current_impact=0.5,
                confidence=0.8,
                suggested_action="Add error handling checkpoints and retry logic",
            ))

        # Timeout improvements
        if category == OutcomeCategory.TIMEOUT:
            candidates.append(ImprovementCandidate(
                category="workflow",
                description="Mission execution timeout",
                current_impact=0.7,
                confidence=0.9,
                suggested_action="Break into smaller tasks or increase timeout limits",
            ))

        # Token efficiency
        if result.token_count > 10000:
            candidates.append(ImprovementCandidate(
                category="resource_allocation",
                description=f"High token usage ({result.token_count} tokens)",
                current_impact=0.3,
                confidence=0.7,
                suggested_action="Optimize prompts or use token-efficient models",
            ))

        # Tool call optimization
        if result.tool_calls > 20:
            candidates.append(ImprovementCandidate(
                category="tool_usage",
                description=f"Excessive tool calls ({result.tool_calls} calls)",
                current_impact=0.4,
                confidence=0.8,
                suggested_action="Batch similar operations or cache results",
            ))

        # Routing improvements
        if success_score < 0.4 and result.agent_id:
            candidates.append(ImprovementCandidate(
                category="routing",
                description=f"Agent {result.agent_id} underperforming (score: {success_score:.2f})",
                current_impact=0.6,
                confidence=0.7,
                suggested_action="Consider alternative agent for this task type",
            ))

        return candidates

    async def get_evaluations(
        self,
        mission_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[OutcomeEvaluation]:
        """
        Get outcome evaluations.

        Args:
            mission_id: Optional mission filter
            limit: Maximum results

        Returns:
            List of evaluations
        """
        evaluations = list(self._evaluations.values())

        if mission_id:
            evaluations = [e for e in evaluations if e.mission_id == mission_id]

        # Sort by evaluation time (newest first)
        evaluations.sort(key=lambda e: e.evaluated_at, reverse=True)

        return evaluations[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get outcome analysis statistics."""
        success_rate = (
            self._success_count / self._total_evaluated
            if self._total_evaluated > 0
            else 0.0
        )

        return {
            "total_evaluated": self._total_evaluated,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": success_rate,
            "patterns_detected": len(self._outcome_patterns),
            "pattern_counts": {
                pattern: len(executions)
                for pattern, executions in self._outcome_patterns.items()
            },
        }

    async def get_recent_patterns(
        self,
        hours: int = 24,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get recently detected patterns.

        Args:
            hours: Lookback period in hours
            limit: Maximum results

        Returns:
            List of pattern summaries
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        recent_evaluations = [
            e for e in self._evaluations.values()
            if e.evaluated_at >= cutoff
        ]

        pattern_counts = defaultdict(int)
        pattern_impacts = defaultdict(list)

        for eval in recent_evaluations:
            for pattern in eval.detected_patterns:
                pattern_counts[pattern] += 1
                pattern_impacts[pattern].append(1.0 - eval.success_score)

        # Build summaries
        summaries = []
        for pattern, count in pattern_counts.items():
            if count >= 2:  # Only show patterns seen multiple times
                avg_impact = sum(pattern_impacts[pattern]) / len(pattern_impacts[pattern])
                summaries.append({
                    "pattern": pattern,
                    "occurrences": count,
                    "avg_impact": avg_impact,
                })

        # Sort by occurrence count
        summaries.sort(key=lambda p: p["occurrences"], reverse=True)

        return summaries[:limit]


# Global outcome analyzer instance
_analyzer: Optional[OutcomeAnalyzer] = None


def get_outcome_analyzer() -> OutcomeAnalyzer:
    """Get the global outcome analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = OutcomeAnalyzer()
    return _analyzer
