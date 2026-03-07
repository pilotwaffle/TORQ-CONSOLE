"""
Learning Engine - Self-improvement and capability evolution.

Phase 7: Governed Self-Improvement, Capability Evolution & Agent Generation

This module provides:
- Learning from execution outcomes
- Performance metrics tracking
- Improvement suggestion generation
- Model feedback collection
- Long-term memory integration
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import defaultdict

from pydantic import BaseModel, Field, field_validator, model_validator

from .models import AutonomousTask, TaskState, ExecutionMode
from .state_store import StateStore
from .execution import ExecutionResult, ExecutionStatus


logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class OutcomeCategory(str, Enum):
    """Categories of task outcomes."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ERROR = "error"


class ImprovementType(str, Enum):
    """Types of improvements."""
    PERFORMANCE = "performance"           # Speed/efficiency improvements
    ACCURACY = "accuracy"                 # Result quality improvements
    COST = "cost"                        # Cost/reduction improvements
    RELIABILITY = "reliability"           # Reduce failures
    CAPABILITY = "capability"             # New capabilities/tools
    PROMPT = "prompt"                     # Prompt optimization
    WORKFLOW = "workflow"                 # Process improvements


class LearningSourceType(str, Enum):
    """Sources of learning data."""
    TASK_OUTCOME = "task_outcome"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_METRICS = "system_metrics"
    AGENT_OBSERVATION = "agent_observation"
    EXTERNAL_BENCHMARK = "external_benchmark"
    PATTERN_ANALYSIS = "pattern_analysis"


class FeedbackType(str, Enum):
    """Types of user/system feedback."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"


# ============================================================================
# Models
# ============================================================================

class TaskOutcome(BaseModel):
    """Record of a task execution outcome for learning."""
    outcome_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Task reference
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    plan_id: Optional[str] = None

    # Classification
    category: OutcomeCategory
    success: bool

    # Metrics
    duration_seconds: float
    cost_estimate: float = 0.0
    token_usage: int = 0

    # Quality assessment
    quality_score: Optional[float] = None  # 0.0 to 1.0, defaults based on success
    user_satisfaction: Optional[float] = None  # If user provided feedback

    # Context
    task_type: Optional[str] = None
    agents_used: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)

    # Failure analysis (if applicable)
    failure_reason: Optional[str] = None
    failure_category: Optional[str] = None
    error_message: Optional[str] = None

    # Workspace/tenant
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Timestamp
    timestamp: float = Field(default_factory=time.time)

    @model_validator(mode='before')
    @classmethod
    def set_default_quality_score(cls, data: Any) -> Any:
        """Set default quality_score based on success if not provided."""
        if isinstance(data, dict):
            if 'quality_score' not in data or data['quality_score'] is None:
                data['quality_score'] = 1.0 if data.get('success', True) else 0.0
        return data

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics for tracking agent/plan effectiveness."""
    metrics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Scope
    scope_type: str  # "agent", "plan_type", "tool", "workflow"
    scope_id: str

    # Performance stats
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    # Timing
    avg_duration_seconds: float = 0.0
    min_duration_seconds: float = float('inf')
    max_duration_seconds: float = 0.0

    # Quality
    avg_quality_score: float = 0.0
    avg_user_satisfaction: float = 0.0

    # Cost
    total_cost: float = 0.0
    avg_cost: float = 0.0

    # Trends (last N executions)
    recent_success_rate: float = 0.0
    trend: str = "stable"  # "improving", "declining", "stable"

    # Timestamp
    last_updated: float = Field(default_factory=time.time)

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    def record_execution(self, outcome: TaskOutcome) -> None:
        """Record an execution outcome."""
        self.total_executions += 1

        if outcome.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update timing
        self.avg_duration_seconds = (
            (self.avg_duration_seconds * (self.total_executions - 1) + outcome.duration_seconds)
            / self.total_executions
        )
        self.min_duration_seconds = min(self.min_duration_seconds, outcome.duration_seconds)
        self.max_duration_seconds = max(self.max_duration_seconds, outcome.duration_seconds)

        # Update quality
        if outcome.quality_score > 0:
            self.avg_quality_score = (
                (self.avg_quality_score * (self.total_executions - 1) + outcome.quality_score)
                / self.total_executions
            )

        # Update cost
        self.total_cost += outcome.cost_estimate
        self.avg_cost = self.total_cost / self.total_executions

        # Update success rate trend
        self.recent_success_rate = self.success_rate
        self.last_updated = time.time()


class ImprovementSuggestion(BaseModel):
    """A suggested improvement generated by the learning engine."""
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Type and priority
    improvement_type: ImprovementType
    priority: str  # "low", "medium", "high", "critical"

    # Scope
    target_type: str  # "agent", "workflow", "policy", "tool"
    target_id: Optional[str] = None

    # Description
    title: str
    description: str
    current_state: str
    proposed_state: str

    # Evidence
    evidence: List[str] = Field(default_factory=list)
    expected_impact: str

    # Implementation
    implementation_complexity: str  # "simple", "moderate", "complex"
    estimated_effort: Optional[str] = None

    # Status
    status: str = "pending"  # pending, reviewed, approved, implemented, rejected
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None

    # Context
    workspace_id: Optional[str] = None
    generated_by: str = "learning_engine"

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class ModelFeedback(BaseModel):
    """Feedback on model/agent performance."""
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Target
    agent_id: Optional[str] = None
    plan_type: Optional[str] = None
    tool_name: Optional[str] = None

    # Feedback
    feedback_type: FeedbackType
    rating: Optional[float] = None  # 0.0 to 1.0
    comment: Optional[str] = None

    # Context
    task_id: Optional[str] = None
    execution_id: Optional[str] = None

    # Source
    source_type: str  # "user", "system", "auto_evaluation"
    source_id: Optional[str] = None

    # Metrics at time of feedback
    metrics_at_time: Optional[Dict[str, Any]] = None

    # Timestamp
    timestamp: float = Field(default_factory=time.time)

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class ObservationRecord(BaseModel):
    """An observation about agent/system behavior."""
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # What was observed
    agent_id: Optional[str] = None
    behavior_type: str  # "task_execution", "decision_making", "tool_usage", etc.
    observation: str

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)

    # Classification
    pattern_type: Optional[str] = None  # "success_pattern", "failure_pattern", etc.
    confidence: float = 0.0  # 0.0 to 1.0

    # Timestamp
    timestamp: float = Field(default_factory=time.time)

    # Source
    source: str = "system"

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


# ============================================================================
# Learning Engine
# ============================================================================

class LearningEngine:
    """
    Engine for learning from execution outcomes and generating improvements.

    Responsibilities:
    - Track task outcomes and patterns
    - Maintain performance metrics
    - Generate improvement suggestions
    - Collect and process feedback
    - Detect patterns in success/failure
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None
    ):
        self.state_store = state_store
        self.logger = logging.getLogger(__name__)

        # Storage
        self._outcomes: List[TaskOutcome] = []
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._suggestions: List[ImprovementSuggestion] = []
        self._feedback: List[ModelFeedback] = []
        self._observations: List[ObservationRecord] = []

        # Pattern detection
        self._patterns: Dict[str, List[ObservationRecord]] = defaultdict(list)

        # Background processing
        self._running = False
        self._analysis_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the learning engine."""
        if self._running:
            return

        self._running = True
        self._analysis_task = asyncio.create_task(self._periodic_analysis())
        self.logger.info("Learning engine started")

    async def stop(self) -> None:
        """Stop the learning engine."""
        self._running = False

        if self._analysis_task:
            self._analysis_task.cancel()

        try:
            await self._analysis_task
        except asyncio.CancelledError:
            pass

        self.logger.info("Learning engine stopped")

    # ========================================================================
    # Outcome Tracking
    # ========================================================================

    async def record_execution(
        self,
        execution: ExecutionResult,
        quality_score: Optional[float] = None,
        user_satisfaction: Optional[float] = None,
        cost_estimate: float = 0.0
    ) -> TaskOutcome:
        """
        Record an execution outcome for learning.

        Args:
            execution: The execution result
            quality_score: Assessed quality (0.0 to 1.0)
            user_satisfaction: User satisfaction if provided
            cost_estimate: Estimated cost of execution

        Returns:
            TaskOutcome record
        """
        outcome = TaskOutcome(
            task_id=execution.task_id,
            execution_id=execution.execution_id,
            plan_id=execution.plan_id,
            category=OutcomeCategory.SUCCESS if execution.success else OutcomeCategory.FAILURE,
            success=execution.success,
            duration_seconds=execution.duration_seconds,
            cost_estimate=cost_estimate,
            quality_score=quality_score or (1.0 if execution.success else 0.0),
            user_satisfaction=user_satisfaction,
            task_type=execution.task_id,  # Would use task type from task
            agents_used=execution.agent_ids,
            tools_used=execution.tools_used,
            failure_reason=execution.error if not execution.success else None,
            workspace_id=execution.workspace_id,
            environment=execution.environment
        )

        self._outcomes.append(outcome)

        # Update performance metrics
        await self._update_metrics(outcome)

        # Store outcome
        await self._save_outcome(outcome)

        return outcome

    async def _update_metrics(self, outcome: TaskOutcome) -> None:
        """Update performance metrics based on outcome."""
        # Determine scope key
        if outcome.agents_used:
            # Track per-agent metrics
            for agent_id in outcome.agents_used:
                scope_id = f"agent_{agent_id}"
                self._get_or_create_metrics("agent", scope_id).record_execution(outcome)

        if outcome.task_type:
            scope_id = f"task_type_{outcome.task_type}"
            self._get_or_create_metrics("task_type", scope_id).record_execution(outcome)

    def _get_or_create_metrics(
        self,
        scope_type: str,
        scope_id: str
    ) -> PerformanceMetrics:
        """Get or create performance metrics for a scope."""
        key = f"{scope_type}:{scope_id}"
        if key not in self._metrics:
            self._metrics[key] = PerformanceMetrics(
                scope_type=scope_type,
                scope_id=scope_id
            )
        return self._metrics[key]

    # ========================================================================
    # Feedback Collection
    # ========================================================================

    async def collect_feedback(
        self,
        feedback_type: FeedbackType,
        rating: Optional[float] = None,
        comment: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        source_type: str = "user"
    ) -> ModelFeedback:
        """
        Collect user/system feedback on performance.

        Args:
            feedback_type: Type of feedback
            rating: Rating from 0.0 to 1.0
            comment: Optional comment
            agent_id: Target agent
            task_id: Related task
            execution_id: Related execution
            source_type: Who provided feedback

        Returns:
            ModelFeedback record
        """
        feedback = ModelFeedback(
            agent_id=agent_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            task_id=task_id,
            execution_id=execution_id,
            source_type=source_type
        )

        self._feedback.append(feedback)

        # Process feedback for insights
        await self._process_feedback(feedback)

        return feedback

    async def _process_feedback(self, feedback: ModelFeedback) -> None:
        """Process feedback for patterns and insights."""
        if feedback.rating is not None:
            if feedback.rating < 0.3:
                # Poor feedback - create observation
                observation = ObservationRecord(
                    agent_id=feedback.agent_id,
                    behavior_type="poor_performance",
                    observation=f"Low rating ({feedback.rating}): {feedback.comment}",
                    pattern_type="failure_pattern",
                    confidence=0.8
                )
                self._observations.append(observation)
                self._add_to_pattern("poor_performance", observation)

            elif feedback.rating > 0.8:
                # Good feedback - create observation
                observation = ObservationRecord(
                    agent_id=feedback.agent_id,
                    behavior_type="excellent_performance",
                    observation=f"High rating ({feedback.rating}): {feedback.comment}",
                    pattern_type="success_pattern",
                    confidence=0.8
                )
                self._observations.append(observation)
                self._add_to_pattern("excellent_performance", observation)

    # ========================================================================
    # Pattern Detection
    # ========================================================================

    def _add_to_pattern(self, pattern_type: str, observation: ObservationRecord) -> None:
        """Add observation to a pattern bucket."""
        self._patterns[pattern_type].append(observation)

    async def detect_patterns(self) -> List[ImprovementSuggestion]:
        """
        Analyze outcomes and observations for patterns.

        Returns:
            List of improvement suggestions based on detected patterns
        """
        suggestions = []

        # Pattern 1: Agent consistently fails on certain tasks
        agent_failure_rates = self._analyze_agent_failure_rates()
        for agent_id, failure_rate in agent_failure_rates.items():
            if failure_rate > 0.5:  # More than 50% failure rate
                suggestions.append(ImprovementSuggestion(
                    improvement_type=ImprovementType.RELIABILITY,
                    priority="high",
                    target_type="agent",
                    target_id=agent_id,
                    title=f"Agent {agent_id} has high failure rate",
                    description=f"Agent {agent_id} fails on {failure_rate*100:.1f}% of tasks",
                    current_state=f"Failure rate: {failure_rate*100:.1f}%",
                    proposed_state="Investigate agent capabilities and configuration",
                    evidence=[f"Analyzed {self._count_agent_executions(agent_id)} executions"],
                    expected_impact="Reduce failures, improve success rate",
                    implementation_complexity="moderate"
                ))

        # Pattern 2: Tasks taking too long
        slow_tasks = self._identify_slow_tasks()
        for task_type, avg_duration in slow_tasks.items():
            suggestions.append(ImprovementSuggestion(
                improvement_type=ImprovementType.PERFORMANCE,
                priority="medium",
                target_type="task_type",
                target_id=task_type,
                title=f"{task_type} tasks are slow",
                description=f"Average duration: {avg_duration:.1f}s",
                current_state=f"Average: {avg_duration:.1f}s",
                proposed_state="Optimize execution or break into smaller steps",
                expected_impact="Faster execution, better user experience",
                implementation_complexity="moderate"
            ))

        # Pattern 3: Poor user satisfaction
        if self._feedback:
            negative_feedback = [f for f in self._feedback if f.rating and f.rating < 0.5]
            if len(negative_feedback) > 5:
                suggestions.append(ImprovementSuggestion(
                    improvement_type=ImprovementType.CAPABILITY,
                    priority="high",
                    target_type="system",
                    title="High rate of negative user feedback",
                    description=f"{len(negative_feedback)} negative feedback records collected",
                    current_state="Low user satisfaction",
                    proposed_state="Review and improve agent responses",
                    expected_impact="Better user experience, higher satisfaction",
                    implementation_complexity="complex"
                ))

        return suggestions

    def _analyze_agent_failure_rates(self) -> Dict[str, float]:
        """Analyze failure rates by agent."""
        agent_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "failed": 0})

        for outcome in self._outcomes:
            for agent_id in outcome.agents_used:
                agent_stats[agent_id]["total"] += 1
                if not outcome.success:
                    agent_stats[agent_id]["failed"] += 1

        failure_rates = {}
        for agent_id, stats in agent_stats.items():
            if stats["total"] > 0:
                failure_rates[agent_id] = stats["failed"] / stats["total"]

        return failure_rates

    def _count_agent_executions(self, agent_id: str) -> int:
        """Count executions for an agent."""
        count = 0
        for outcome in self._outcomes:
            if agent_id in outcome.agents_used:
                count += 1
        return count

    def _identify_slow_tasks(self) -> Dict[str, float]:
        """Identify task types with slow execution."""
        task_durations: Dict[str, List[float]] = defaultdict(list)

        for outcome in self._outcomes:
            if outcome.task_type and outcome.duration_seconds > 0:
                task_durations[outcome.task_type].append(outcome.duration_seconds)

        slow_tasks = {}
        for task_type, durations in task_durations.items():
            if len(durations) >= 3:  # At least 3 samples
                avg = sum(durations) / len(durations)
                if avg > 60:  # More than 1 minute
                    slow_tasks[task_type] = avg

        return slow_tasks

    # ========================================================================
    # Improvement Suggestions
    # ========================================================================

    async def generate_suggestions(
        self,
        min_priority: Optional[str] = None
    ) -> List[ImprovementSuggestion]:
        """
        Generate improvement suggestions.

        Args:
            min_priority: Minimum priority level to return

        Returns:
            List of suggestions
        """
        # Detect patterns and generate suggestions
        detected = await self.detect_patterns()

        # Add to suggestions list
        for suggestion in detected:
            # Avoid duplicates
            if not any(s.title == suggestion.title for s in self._suggestions):
                self._suggestions.append(suggestion)

        # Filter by priority
        if min_priority:
            priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            min_level = priority_order.get(min_priority, 0)
            suggestions = [
                s for s in self._suggestions
                if priority_order.get(s.priority, 0) >= min_level
            ]
        else:
            suggestions = self._suggestions

        # Sort by priority (highest first) and date (newest first)
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        suggestions.sort(
            key=lambda s: (priority_order.get(s.priority, 0), s.created_at),
            reverse=True
        )

        return suggestions

    async def implement_suggestion(
        self,
        suggestion_id: str,
        implemented_by: str
    ) -> bool:
        """
        Mark a suggestion as implemented.

        Args:
            suggestion_id: Suggestion to implement
            implemented_by: Who implemented it

        Returns:
            True if successful
        """
        for suggestion in self._suggestions:
            if suggestion.suggestion_id == suggestion_id:
                suggestion.status = "implemented"
                # Create observation
                observation = ObservationRecord(
                    behavior_type="implementation",
                    observation=f"Suggestion implemented: {suggestion.title}",
                    pattern_type="improvement",
                    confidence=1.0,
                    context={"suggestion_id": suggestion_id, "implemented_by": implemented_by}
                )
                self._observations.append(observation)
                return True
        return False

    # ========================================================================
    # Metrics and Analytics
    # ========================================================================

    def get_metrics(
        self,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None
    ) -> List[PerformanceMetrics]:
        """Get performance metrics."""
        metrics = list(self._metrics.values())

        if scope_type:
            metrics = [m for m in metrics if m.scope_type == scope_type]
        if scope_id:
            metrics = [m for m in metrics if m.scope_id == scope_id]

        return metrics

    def get_top_performers(
        self,
        scope_type: str,
        limit: int = 10
    ) -> List[tuple[str, float]]:
        """
        Get top performers by success rate.

        Returns:
            List of (scope_id, success_rate) tuples
        """
        metrics = [m for m in self._metrics.values() if m.scope_type == scope_type]

        # Sort by success rate
        sorted_metrics = sorted(
            metrics,
            key=lambda m: m.success_rate,
            reverse=True
        )

        return [(m.scope_id, m.success_rate) for m in sorted_metrics[:limit]]

    def get_underperformers(
        self,
        scope_type: str,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[tuple[str, float]]:
        """
        Get underperforming scopes.

        Args:
            scope_type: Type of scope to check
            threshold: Success rate threshold
            limit: Max results

        Returns:
            List of (scope_id, success_rate) tuples
        """
        metrics = [m for m in self._metrics.values() if m.scope_type == scope_type]

        # Filter by below threshold
        underperformers = [
            (m.scope_id, m.success_rate)
            for m in metrics
            if m.success_rate < threshold and m.total_executions >= 3
        ]

        # Sort by success rate (lowest first)
        underperformers.sort(key=lambda x: x[1])

        return underperformers[:limit]

    # ========================================================================
    # Persistence
    # ========================================================================

    async def _save_outcome(self, outcome: TaskOutcome) -> bool:
        """Save outcome to storage."""
        if self.state_store:
            try:
                from .models import TaskStateRecord, TaskState
                record = TaskStateRecord(
                    task_id=f"outcome_{outcome.outcome_id}",
                    state=TaskState.SUCCEEDED if outcome.success else TaskState.FAILED,
                    timestamp=time.time(),
                    data={"outcome": outcome.model_dump()}
                )
                await self.state_store.save_task_state(record)
                return True
            except Exception as e:
                self.logger.error(f"Error saving outcome: {e}")
        return False

    async def _periodic_analysis(self) -> None:
        """Background task for periodic analysis."""
        while self._running:
            try:
                # Generate suggestions every 5 minutes
                await asyncio.sleep(300)
                await self.generate_suggestions()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(60)

    # ========================================================================
    # Learning Analytics
    # ========================================================================

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning statistics."""
        return {
            "total_outcomes": len(self._outcomes),
            "success_rate": (
                sum(1 for o in self._outcomes if o.success) / len(self._outcomes)
                if self._outcomes else 0
            ),
            "total_suggestions": len(self._suggestions),
            "pending_suggestions": sum(1 for s in self._suggestions if s.status == "pending"),
            "implemented_suggestions": sum(1 for s in self._suggestions if s.status == "implemented"),
            "total_feedback": len(self._feedback),
            "total_observations": len(self._observations),
            "tracked_metrics": len(self._metrics),
            "is_running": self._running
        }


# Singleton instance
_learning_engine: Optional[LearningEngine] = None


def get_learning_engine(
    state_store: Optional[StateStore] = None
) -> LearningEngine:
    """Get the singleton learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine(state_store=state_store)
    return _learning_engine
