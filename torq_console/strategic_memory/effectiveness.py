"""
Memory Effectiveness Scoring

Track whether injected memories actually improve downstream outcomes.

Effectiveness score components:
- Evaluation delta (30%): Score improvement vs baseline
- Experiment success rate (25%): Led to successful adaptations
- Workflow performance boost (25%): Workflow-level improvement
- Contradiction reduction (20%): Reduced contradictions
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import StrategicMemory


logger = logging.getLogger(__name__)


# ============================================================================
# Effectiveness Models
# ============================================================================

@dataclass
class MemoryEffectivenessComponents:
    """Component scores for memory effectiveness."""
    evaluation_delta_impact: float  # -1.0 to 1.0 (normalized)
    experiment_success_rate: float  # 0.0 to 1.0
    workflow_performance_boost: float  # -1.0 to 1.0 (normalized)
    contradiction_reduction: float  # 0.0 to 1.0


@dataclass
class MemoryEffectivenessRecord:
    """Full effectiveness record for a memory."""
    memory_id: str
    usage_count: int
    last_updated: datetime

    # Components
    components: MemoryEffectivenessComponents

    # Overall score
    effectiveness_score: float  # 0.0 to 1.0

    # Trends
    score_trend: str  # "improving", "stable", "declining"
    trend_window_days: int = 30

    # Breakdown
    avg_evaluation_delta: float
    avg_contradiction_reduction: float
    success_rate: float


# ============================================================================
# Effectiveness Calculator
# ============================================================================

class MemoryEffectivenessCalculator:
    """
    Calculate effectiveness scores for strategic memories.

    Aggregates usage data and computes multi-dimensional effectiveness.
    """

    # Weightings for effectiveness components
    WEIGHTS = {
        "evaluation_delta": 0.30,
        "experiment_success": 0.25,
        "workflow_performance": 0.25,
        "contradiction_reduction": 0.20,
    }

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def calculate_effectiveness(
        self,
        memory_id: str,
        days_back: int = 90
    ) -> Optional[MemoryEffectivenessRecord]:
        """
        Calculate full effectiveness record for a memory.

        Aggregates all usage data over the period.
        """
        since = datetime.now() - timedelta(days=days_back)

        # Fetch usage data
        usage_data = await self._fetch_usage_data(memory_id, since)
        if not usage_data:
            return None

        # Calculate components
        components = await self._calculate_components(memory_id, usage_data, days_back)

        # Calculate overall score
        effectiveness_score = self._calculate_overall_score(components)

        # Determine trend
        trend = await self._calculate_trend(memory_id, days_back)

        return MemoryEffectivenessRecord(
            memory_id=memory_id,
            usage_count=len(usage_data),
            last_updated=datetime.now(),
            components=components,
            effectiveness_score=effectiveness_score,
            score_trend=trend,
            avg_evaluation_delta=components.evaluation_delta_impact,
            avg_contradiction_reduction=components.contradiction_reduction,
            success_rate=components.experiment_success_rate
        )

    async def recalculate_all(
        self,
        days_back: int = 90
    ) -> List[MemoryEffectivenessRecord]:
        """
        Recalculate effectiveness for all active memories.

        Called periodically by governance job.
        """
        # Get all active memories
        result = self.supabase.table("strategic_memories").select("id").eq("status", "active").execute()

        if not result.data:
            return []

        records = []
        for memory in result.data:
            record = await self.calculate_effectiveness(memory["id"], days_back)
            if record:
                records.append(record)
                # Update database
                await self._update_effectiveness_in_db(record)

        logger.info(f"Recalculated effectiveness for {len(records)} memories")

        return records

    async def _calculate_components(
        self,
        memory_id: str,
        usage_data: List[Dict[str, Any]],
        days_back: int
    ) -> MemoryEffectivenessComponents:
        """Calculate each effectiveness component."""

        # 1. Evaluation Delta Impact
        eval_delta = await self._calculate_evaluation_delta(memory_id, usage_data)

        # 2. Experiment Success Rate
        exp_success = await self._calculate_experiment_success(memory_id)

        # 3. Workflow Performance Boost
        workflow_boost = await self._calculate_workflow_boost(memory_id, usage_data, days_back)

        # 4. Contradiction Reduction
        contradiction_reduction = await self._calculate_contradiction_reduction(memory_id, usage_data)

        return MemoryEffectivenessComponents(
            evaluation_delta_impact=eval_delta,
            experiment_success_rate=exp_success,
            workflow_performance_boost=workflow_boost,
            contradiction_reduction=contradiction_reduction
        )

    async def _calculate_evaluation_delta(
        self,
        memory_id: str,
        usage_data: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate evaluation score delta when memory was used.

        Compares execution scores to workflow type baseline.
        """
        if not usage_data:
            return 0.0

        # Get evaluation deltas from usage records
        deltas = []
        for usage in usage_data:
            delta = usage.get("evaluation_delta")
            if delta is not None:
                deltas.append(delta)

        if not deltas:
            return 0.0

        avg_delta = sum(deltas) / len(deltas)

        # Normalize to -1.0 to 1.0 range
        # Assuming typical delta range is -0.2 to +0.2
        normalized = max(-1.0, min(1.0, avg_delta * 5))

        return normalized

    async def _calculate_experiment_success(
        self,
        memory_id: str
    ) -> float:
        """
        Calculate success rate of adaptations this memory contributed to.

        If memory led to successful proposals/promotions, it's effective.
        """
        # Find adaptations that used this memory
        try:
            result = self.supabase.table("adaptation_proposals").select("*").contains("injected_memory_ids", [memory_id]).execute()

            if not result.data:
                return 0.0

            # Count successful outcomes
            successful = len([p for p in result.data if p.get("status") == "promoted"])
            total = len(result.data)

            if total == 0:
                return 0.0

            return successful / total

        except Exception as e:
            logger.error(f"Error calculating experiment success: {e}")
            return 0.0

    async def _calculate_workflow_boost(
        self,
        memory_id: str,
        usage_data: List[Dict[str, Any]],
        days_back: int
    ) -> float:
        """
        Calculate workflow-level performance boost.

        Compares evaluations for workflows using vs not using this memory.
        """
        if not usage_data:
            return 0.0

        # Group by workflow type
        workflow_scores = {}
        workflow_baselines = {}

        for usage in usage_data:
            workflow = usage.get("workflow_type")
            score = usage.get("outcome_score")

            if workflow and score is not None:
                if workflow not in workflow_scores:
                    workflow_scores[workflow] = []
                workflow_scores[workflow].append(score)

        # Calculate boost for each workflow type
        boosts = []
        for workflow, scores in workflow_scores.items():
            # Get baseline for this workflow (executions without this memory)
            baseline = await self._get_workflow_baseline(workflow, days_back)

            if baseline:
                avg_with_memory = sum(scores) / len(scores)
                boost = (avg_with_memory - baseline) / baseline if baseline > 0 else 0
                boosts.append(boost)

        if not boosts:
            return 0.0

        avg_boost = sum(boosts) / len(boosts)

        # Normalize to -1.0 to 1.0
        return max(-1.0, min(1.0, avg_boost * 3))

    async def _get_workflow_baseline(
        self,
        workflow_type: str,
        days_back: int
    ) -> Optional[float]:
        """Get baseline evaluation score for a workflow type."""
        since = datetime.now() - timedelta(days=days_back)

        try:
            # Get executions for this workflow
            result = self.supabase.table("task_executions").select("id").eq("workflow_type", workflow_type).gte("created_at", since.isoformat()).execute()

            if not result.data:
                return None

            # Get average evaluation score
            exec_ids = [e["id"] for e in result.data[:100]]  # Limit for performance

            eval_result = self.supabase.table("execution_evaluations").select("overall_score").in_("execution_id", exec_ids).execute()

            if not eval_result.data:
                return None

            scores = [e["overall_score"] for e in eval_result.data if e.get("overall_score") is not None]

            return sum(scores) / len(scores) if scores else None

        except Exception as e:
            logger.error(f"Error getting workflow baseline: {e}")
            return None

    async def _calculate_contradiction_reduction(
        self,
        memory_id: str,
        usage_data: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate contradiction rate reduction when memory is used.

        Lower contradictions = more effective.
        """
        if not usage_data:
            return 0.0

        # Get contradiction counts
        counts = []
        for usage in usage_data:
            count = usage.get("contradiction_count")
            if count is not None:
                counts.append(count)

        if not counts:
            return 0.0

        avg_contradictions = sum(counts) / len(counts)

        # Normalize: 0 contradictions = 1.0, 5+ contradictions = 0.0
        reduction = max(0.0, 1.0 - (avg_contradictions / 5.0))

        return reduction

    def _calculate_overall_score(
        self,
        components: MemoryEffectivenessComponents
    ) -> float:
        """Calculate overall effectiveness score from components."""
        score = (
            components.evaluation_delta_impact * self.WEIGHTS["evaluation_delta"] +
            components.experiment_success_rate * self.WEIGHTS["experiment_success"] +
            components.workflow_performance_boost * self.WEIGHTS["workflow_performance"] +
            components.contradiction_reduction * self.WEIGHTS["contradiction_reduction"]
        )

        # Normalize to 0-1 range (handling negative components)
        # -1 to 1 -> 0 to 1: (score + 1) / 2
        normalized = (score + 1) / 2

        return max(0.0, min(1.0, normalized))

    async def _calculate_trend(
        self,
        memory_id: str,
        days_back: int
    ) -> str:
        """
        Determine if effectiveness is trending up, stable, or down.

        Compares recent performance to older performance.
        """
        mid_point = days_back // 2

        # Recent period
        recent_record = await self.calculate_effectiveness(
            memory_id,
            days_back=mid_point
        )

        # Older period
        older_record = await self.calculate_effectiveness(
            memory_id,
            days_back=days_back
        )

        if not recent_record or not older_record:
            return "stable"

        recent_score = recent_record.effectiveness_score
        older_score = older_record.effectiveness_score

        delta = recent_score - older_score

        if delta > 0.05:
            return "improving"
        elif delta < -0.05:
            return "declining"
        else:
            return "stable"

    async def _fetch_usage_data(
        self,
        memory_id: str,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch usage data for a memory since a date."""
        try:
            result = self.supabase.table("memory_usage").select("*").eq("memory_id", memory_id).gte("used_at", since.isoformat()).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching usage data: {e}")
            return []

    async def _update_effectiveness_in_db(
        self,
        record: MemoryEffectivenessRecord
    ):
        """Update effectiveness score in strategic_memories table."""
        try:
            self.supabase.table("strategic_memories").update({
                "effectiveness_score": record.effectiveness_score,
                "last_validated_at": datetime.now().isoformat()
            }).eq("id", record.memory_id).execute()

        except Exception as e:
            logger.error(f"Error updating effectiveness in DB: {e}")


# ============================================================================
# Effectiveness Tracker (Real-time)
# ============================================================================

class EffectivenessTracker:
    """
    Track effectiveness contributions in real-time during execution.

    Updates effectiveness records as executions complete.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def record_execution_outcome(
        self,
        execution_id: str,
        memory_ids: List[str],
        evaluation_score: float,
        contradiction_count: int,
        workflow_type: Optional[str] = None
    ):
        """
        Record execution outcome for effectiveness tracking.

        Called when an execution with injected memories completes.
        """
        if not memory_ids:
            return

        # Get baseline for workflow type
        baseline = await self._get_baseline_score(workflow_type)

        # Calculate evaluation delta
        eval_delta = evaluation_score - baseline if baseline else 0

        for memory_id in memory_ids:
            try:
                # Update memory_usage with outcome data
                self.supabase.table("memory_usage").update({
                    "outcome_score": evaluation_score,
                    "evaluation_delta": eval_delta,
                    "contradiction_count": contradiction_count,
                    "helpful": eval_delta > 0  # Simple heuristic
                }).eq("execution_id", execution_id).eq("memory_id", memory_id).execute()

            except Exception as e:
                logger.error(f"Error recording outcome for memory {memory_id}: {e}")

    async def record_adaptation_outcome(
        self,
        proposal_id: str,
        memory_ids: List[str],
        succeeded: bool
    ):
        """
        Record adaptation proposal outcome.

        Contributes to experiment_success_rate component.
        """
        if not memory_ids:
            return

        for memory_id in memory_ids:
            try:
                # Update memory_usage records linked to this proposal
                self.supabase.table("memory_usage").update({
                    "led_to_proposal": True,
                    "proposal_succeeded": succeeded
                }).eq("memory_id", memory_id).is_("proposal_id", proposal_id).execute()

            except Exception as e:
                logger.error(f"Error recording adaptation outcome for memory {memory_id}: {e}")

    async def _get_baseline_score(
        self,
        workflow_type: Optional[str]
    ) -> Optional[float]:
        """Get baseline evaluation score for comparison."""
        if not workflow_type:
            return 0.75  # Default baseline

        # Use a cached baseline or compute
        # For now, return a simple default
        return 0.75


# ============================================================================
# Periodic Recalculation Job
# ============================================================================

async def recalculate_effectiveness_job(supabase_client):
    """
    Background job to recalculate all memory effectiveness scores.

    Should run daily or weekly via cron/scheduler.
    """
    calculator = MemoryEffectivenessCalculator(supabase_client)

    records = await calculator.recalculate_all(days_back=90)

    # Log summary
    if records:
        avg_score = sum(r.effectiveness_score for r in records) / len(records)
        logger.info(f"Effectiveness recalculation complete. "
                   f"Updated {len(records)} memories. "
                   f"Average effectiveness: {avg_score:.2f}")

        # Count by trend
        improving = len([r for r in records if r.score_trend == "improving"])
        declining = len([r for r in records if r.score_trend == "declining"])
        stable = len([r for r in records if r.score_trend == "stable"])

        logger.info(f"Trends: {improving} improving, {stable} stable, {declining} declining")

    return records
