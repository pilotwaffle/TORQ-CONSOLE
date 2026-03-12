"""
Memory Injection Experiments

Controlled experiments to prove strategic memory improves reasoning outcomes.

Two experiments:
- Experiment A: Memory vs No Memory (control vs top-5 injection)
- Experiment B: Sparse vs Dense Memory (top-3 vs top-5)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID

from ..strategic_memory.models import (
    MemoryType,
    MemoryScope,
    MemorySearchRequest,
    MemoryInjection,
)
from ..strategic_memory.retrieval import MemoryRetrievalEngine


logger = logging.getLogger(__name__)


# ============================================================================
# Experiment Configuration
# ============================================================================

class ExperimentType(str, Enum):
    """Types of memory injection experiments."""
    MEMORY_VS_NONE = "memory_vs_none"  # Experiment A
    SPARSE_VS_DENSE = "sparse_vs_dense"  # Experiment B


class ExperimentGroup(str, Enum):
    """Experiment group assignments."""
    CONTROL = "control"
    CANDIDATE = "candidate"


@dataclass
class ExperimentConfig:
    """Configuration for a memory injection experiment."""
    name: str
    description: str
    experiment_type: ExperimentType
    sample_size_target: int = 50
    min_sample_size: int = 20
    stratify_by_workflow_type: bool = True

    # Group configurations
    control_config: Dict[str, Any] = field(default_factory=dict)
    candidate_config: Dict[str, Any] = field(default_factory=dict)

    # Status
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: Literal["planning", "running", "completed", "cancelled"] = "planning"


# Default Experiment Configurations
EXPERIMENT_A_CONFIG = ExperimentConfig(
    name="Memory vs No Memory",
    description="Compare execution quality with and without strategic memory injection",
    experiment_type=ExperimentType.MEMORY_VS_NONE,
    sample_size_target=50,
    control_config={
        "inject_memory": False,
        "max_memories": 0
    },
    candidate_config={
        "inject_memory": True,
        "max_memories": 5,
        "include_warnings": True,
        "include_playbooks": True,
        "include_heuristics": True
    }
)

EXPERIMENT_B_CONFIG = ExperimentConfig(
    name="Sparse vs Dense Memory",
    description="Compare execution quality with top-3 vs top-5 strategic memories",
    experiment_type=ExperimentType.SPARSE_VS_DENSE,
    sample_size_target=50,
    control_config={
        "inject_memory": True,
        "max_memories": 3
    },
    candidate_config={
        "inject_memory": True,
        "max_memories": 5
    }
)


# ============================================================================
# Experiment Assignment
# ============================================================================

class ExperimentAssigner:
    """
    Assigns executions to experiment groups deterministically.

    Uses hash-based assignment for consistency:
    - Same execution always gets same group
    - Enables fair comparison across similar workloads
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def assign_to_group(
        self,
        experiment_id: str,
        execution_id: str,
        config: ExperimentConfig
    ) -> ExperimentGroup:
        """
        Assign an execution to control or candidate group.

        Uses deterministic hash-based assignment.
        """
        # Generate hash from experiment + execution
        hash_input = f"{experiment_id}:{execution_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Assign to group based on hash parity
        if config.experiment_type == ExperimentType.MEMORY_VS_NONE:
            # 50/50 split for memory vs none
            group = ExperimentGroup.CANDIDATE if hash_value % 2 == 0 else ExperimentGroup.CONTROL
        else:
            # 50/50 split for sparse vs dense
            group = ExperimentGroup.CANDIDATE if hash_value % 2 == 0 else ExperimentGroup.CONTROL

        # Record assignment
        await self._record_assignment(experiment_id, execution_id, group, config)

        logger.debug(f"Assigned execution {execution_id} to {group} in experiment {experiment_id}")

        return group

    async def get_memory_injection_config(
        self,
        experiment_id: str,
        execution_id: str,
        config: ExperimentConfig
    ) -> Dict[str, Any]:
        """
        Get the memory injection configuration for an execution.

        Returns config based on group assignment.
        """
        group = await self.assign_to_group(experiment_id, execution_id, config)

        if group == ExperimentGroup.CONTROL:
            return config.control_config
        else:
            return config.candidate_config

    async def _record_assignment(
        self,
        experiment_id: str,
        execution_id: str,
        group: ExperimentGroup,
        config: ExperimentConfig
    ):
        """Record experiment assignment for analysis."""
        try:
            # Check if experiment_assignments table has memory_ids column
            # If not, we'll add it via migration
            self.supabase.table("experiment_assignments").insert({
                "experiment_id": experiment_id,
                "execution_id": execution_id,
                "group_assignment": group.value,
                "experiment_type": config.experiment_type.value,
                "config_at_assignment": config.candidate_config if group == ExperimentGroup.CANDIDATE else config.control_config,
                "memory_ids": [],  # Will be populated when memories are injected
                "assigned_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error recording assignment: {e}")


# ============================================================================
# Injection Tracker
# ============================================================================

class MemoryInjectionTracker:
    """
    Tracks which memories were injected into each execution.

    Links injections to outcomes for effectiveness analysis.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def record_injection(
        self,
        execution_id: str,
        experiment_id: Optional[str],
        memory_ids: List[str],
        injection_config: Dict[str, Any]
    ):
        """Record which memories were injected into an execution."""
        try:
            # Update experiment assignment if exists
            if experiment_id:
                self.supabase.table("experiment_assignments").update({
                    "memory_ids": memory_ids,
                    "injected_at": datetime.now().isoformat()
                }).eq("execution_id", execution_id).eq("experiment_id", experiment_id).execute()

            # Record to memory_usage for each memory
            for memory_id in memory_ids:
                self.supabase.table("memory_usage").insert({
                    "memory_id": memory_id,
                    "execution_id": execution_id,
                    "experiment_id": experiment_id,
                    "injection_config": injection_config,
                    "used_at": datetime.now().isoformat()
                }).execute()

            logger.debug(f"Recorded injection of {len(memory_ids)} memories for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error recording injection: {e}")

    async def get_memories_for_execution(
        self,
        execution_id: str
    ) -> List[Dict[str, Any]]:
        """Get memories that were injected into an execution."""
        try:
            result = self.supabase.table("memory_usage").select("*").eq("execution_id", execution_id).execute()

            if not result.data:
                return []

            # Fetch full memory details
            memory_ids = [u["memory_id"] for u in result.data]
            memories_result = self.supabase.table("strategic_memories").select("*").in_("id", memory_ids).execute()

            return memories_result.data if memories_result.data else []

        except Exception as e:
            logger.error(f"Error getting memories for execution: {e}")
            return []


# ============================================================================
# Results Tracking
# ============================================================================

@dataclass
class ExperimentResult:
    """Result from a single execution in an experiment."""
    execution_id: str
    experiment_id: str
    group: ExperimentGroup
    memory_ids: List[str]

    # Evaluation metrics
    overall_score: Optional[float] = None
    reasoning_score: Optional[float] = None
    coherence_score: Optional[float] = None
    actionability_score: Optional[float] = None
    contradiction_count: Optional[int] = None

    # Performance metrics
    latency_seconds: Optional[float] = None
    token_count: Optional[int] = None

    # Metadata
    workflow_type: Optional[str] = None
    domain: Optional[str] = None
    evaluated_at: Optional[datetime] = None


class ExperimentResultsTracker:
    """
    Tracks experiment outcomes for analysis.

    Collects evaluation metrics, performance metrics, and metadata.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def record_result(
        self,
        result: ExperimentResult
    ):
        """Record experiment result for analysis."""
        try:
            self.supabase.table("memory_injection_results").insert({
                "experiment_id": result.experiment_id,
                "execution_id": result.execution_id,
                "group_assignment": result.group.value,
                "memory_ids": result.memory_ids,
                "overall_score": result.overall_score,
                "reasoning_score": result.reasoning_score,
                "coherence_score": result.coherence_score,
                "actionability_score": result.actionability_score,
                "contradiction_count": result.contradiction_count,
                "latency_seconds": result.latency_seconds,
                "token_count": result.token_count,
                "workflow_type": result.workflow_type,
                "domain": result.domain,
                "evaluated_at": result.evaluated_at or datetime.now().isoformat()
            }).execute()

            logger.debug(f"Recorded result for execution {result.execution_id}")

        except Exception as e:
            logger.error(f"Error recording result: {e}")

    async def record_from_evaluation(
        self,
        execution_id: str,
        experiment_id: str,
        group: ExperimentGroup,
        evaluation_data: Dict[str, Any],
        performance_data: Dict[str, Any]
    ):
        """Record result from evaluation and performance data."""
        # Get injected memories for this execution
        tracker = MemoryInjectionTracker(self.supabase)
        memories = await tracker.get_memories_for_execution(execution_id)
        memory_ids = [m["id"] for m in memories]

        result = ExperimentResult(
            execution_id=execution_id,
            experiment_id=experiment_id,
            group=group,
            memory_ids=memory_ids,
            overall_score=evaluation_data.get("overall_score"),
            reasoning_score=evaluation_data.get("reasoning_score"),
            coherence_score=evaluation_data.get("coherence_score"),
            actionability_score=evaluation_data.get("actionability_score"),
            contradiction_count=evaluation_data.get("contradiction_count"),
            latency_seconds=performance_data.get("latency_seconds"),
            token_count=performance_data.get("token_count"),
            workflow_type=evaluation_data.get("workflow_type"),
            domain=evaluation_data.get("domain"),
            evaluated_at=datetime.now()
        )

        await self.record_result(result)


# ============================================================================
# Experiment Analysis
# ============================================================================

@dataclass
class ExperimentAnalysis:
    """Analysis results from an experiment."""
    experiment_id: str
    experiment_type: ExperimentType
    sample_size: int
    control_size: int
    candidate_size: int

    # Primary outcome
    overall_score_improvement: float  # percentage
    overall_score_confidence: float  # statistical confidence

    # Secondary outcomes
    coherence_improvement: float
    actionability_improvement: float
    contradiction_reduction: float
    latency_increase_pct: float
    token_increase_pct: float

    # Significance tests
    is_significant: bool
    p_value: Optional[float] = None

    # Recommendation
    recommendation: str  # "adopt", "refine", "reject"


class ExperimentAnalyzer:
    """
    Analyzes experiment results to determine effectiveness.

    Performs statistical comparison between control and candidate groups.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def analyze_experiment(
        self,
        experiment_id: str
    ) -> ExperimentAnalysis:
        """
        Analyze experiment results.

        Compares control vs candidate across all metrics.
        """
        # Fetch all results for this experiment
        results = await self._fetch_results(experiment_id)

        if not results:
            return self._no_data_analysis(experiment_id)

        # Split by group
        control_results = [r for r in results if r["group_assignment"] == "control"]
        candidate_results = [r for r in results if r["group_assignment"] == "candidate"]

        # Calculate metrics
        overall_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "overall_score"
        )

        coherence_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "coherence_score"
        )

        actionability_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "actionability_score"
        )

        contradiction_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "contradiction_count",
            lower_is_better=True
        )

        latency_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "latency_seconds",
            lower_is_better=True
        )

        token_impact = self._calculate_metric_delta(
            control_results,
            candidate_results,
            "token_count",
            lower_is_better=True
        )

        # Determine significance
        is_significant = overall_impact >= 0.03  # At least 3% improvement

        # Generate recommendation
        if is_significant and latency_impact > -0.10:  # Significant improvement, acceptable latency
            recommendation = "adopt"
        elif overall_impact > 0 and latency_impact > -0.10:
            recommendation = "refine"  # Some improvement, needs tuning
        else:
            recommendation = "reject"  # No improvement or too costly

        return ExperimentAnalysis(
            experiment_id=experiment_id,
            experiment_type=ExperimentType.MEMORY_VS_NONE,  # Determine from results
            sample_size=len(results),
            control_size=len(control_results),
            candidate_size=len(candidate_results),
            overall_score_improvement=overall_impact,
            overall_score_confidence=0.95,  # Placeholder - calculate properly
            coherence_improvement=coherence_impact,
            actionability_improvement=actionability_impact,
            contradiction_reduction=contradiction_impact,
            latency_increase_pct=abs(latency_impact) if latency_impact < 0 else 0,
            token_increase_pct=abs(token_impact) if token_impact < 0 else 0,
            is_significant=is_significant,
            p_value=None,  # Calculate proper p-value
            recommendation=recommendation
        )

    async def _fetch_results(self, experiment_id: str) -> List[Dict[str, Any]]:
        """Fetch all results for an experiment."""
        try:
            result = self.supabase.table("memory_injection_results").select("*").eq("experiment_id", experiment_id).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            return []

    def _calculate_metric_delta(
        self,
        control: List[Dict[str, Any]],
        candidate: List[Dict[str, Any]],
        metric_key: str,
        lower_is_better: bool = False
    ) -> float:
        """
        Calculate percentage difference between groups.

        Returns positive if candidate improved the metric.
        """
        if not control or not candidate:
            return 0.0

        # Get values (filter out nulls)
        control_values = [c[metric_key] for c in control if c.get(metric_key) is not None]
        candidate_values = [c[metric_key] for c in candidate if c.get(metric_key) is not None]

        if not control_values or not candidate_values:
            return 0.0

        control_avg = sum(control_values) / len(control_values)
        candidate_avg = sum(candidate_values) / len(candidate_values)

        if control_avg == 0:
            return 0.0

        # Calculate percentage difference
        delta = (candidate_avg - control_avg) / control_avg

        # If lower is better, invert the sign
        if lower_is_better:
            delta = -delta

        return round(delta, 4)  # As percentage (e.g., 0.03 = 3%)

    def _no_data_analysis(self, experiment_id: str) -> ExperimentAnalysis:
        """Return analysis for experiment with no data."""
        return ExperimentAnalysis(
            experiment_id=experiment_id,
            experiment_type=ExperimentType.MEMORY_VS_NONE,
            sample_size=0,
            control_size=0,
            candidate_size=0,
            overall_score_improvement=0.0,
            overall_score_confidence=0.0,
            coherence_improvement=0.0,
            actionability_improvement=0.0,
            contradiction_reduction=0.0,
            latency_increase_pct=0.0,
            token_increase_pct=0.0,
            is_significant=False,
            p_value=None,
            recommendation="insufficient_data"
        )


# ============================================================================
# Experiment Manager
# ============================================================================

class MemoryInjectionExperimentManager:
    """
    Main interface for running memory injection experiments.

    Coordinates assignment, injection tracking, and results analysis.
    """

    def __init__(self, supabase_client, retrieval_engine: MemoryRetrievalEngine):
        self.supabase = supabase_client
        self.retrieval = retrieval_engine
        self.assigner = ExperimentAssigner(supabase_client)
        self.tracker = MemoryInjectionTracker(supabase_client)
        self.results_tracker = ExperimentResultsTracker(supabase_client)
        self.analyzer = ExperimentAnalyzer(supabase_client)

    async def create_experiment(
        self,
        config: ExperimentConfig
    ) -> str:
        """Create a new experiment."""
        # Generate experiment ID
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{config.experiment_type.value}"

        # Create experiment record
        self.supabase.table("memory_injection_experiments").insert({
            "experiment_id": experiment_id,
            "name": config.name,
            "description": config.description,
            "experiment_type": config.experiment_type.value,
            "sample_size_target": config.sample_size_target,
            "min_sample_size": config.min_sample_size,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "control_config": config.control_config,
            "candidate_config": config.candidate_config
        }).execute()

        logger.info(f"Created experiment {experiment_id}: {config.name}")

        return experiment_id

    async def prepare_execution(
        self,
        execution_id: str,
        experiment_id: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Prepare an execution for experiment.

        Returns list of memory IDs to inject (may be empty for control).
        """
        # Get experiment config
        experiment = await self._get_experiment(experiment_id)
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            return []

        config = self._config_from_dict(experiment)

        # Get injection config for this execution
        injection_config = await self.assigner.get_memory_injection_config(
            experiment_id,
            execution_id,
            config
        )

        # Get memories if injection enabled
        memory_ids = []
        if injection_config.get("inject_memory", False):
            max_memories = injection_config.get("max_memories", 5)

            # Build search request
            search_request = MemorySearchRequest(
                workflow_type=context.get("workflow_type"),
                domain=context.get("domain"),
                agent_type=context.get("agent_type"),
                max_results=max_memories,
                min_confidence=0.5
            )

            results = await self.retrieval.search(search_request)
            memory_ids = [r.memory.id for r in results]

        # Record injection
        await self.tracker.record_injection(
            execution_id,
            experiment_id,
            memory_ids,
            injection_config
        )

        return memory_ids

    async def record_evaluation(
        self,
        execution_id: str,
        evaluation_data: Dict[str, Any],
        performance_data: Dict[str, Any]
    ):
        """Record evaluation result for an execution in an experiment."""
        # Find experiment for this execution
        assignment = await self._get_assignment(execution_id)
        if not assignment:
            return

        await self.results_tracker.record_from_evaluation(
            execution_id,
            assignment["experiment_id"],
            ExperimentGroup(assignment["group_assignment"]),
            evaluation_data,
            performance_data
        )

    async def get_experiment_status(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """Get current status of an experiment."""
        results = await self.analyzer._fetch_results(experiment_id)

        control_count = len([r for r in results if r["group_assignment"] == "control"])
        candidate_count = len([r for r in results if r["group_assignment"] == "candidate"])

        return {
            "experiment_id": experiment_id,
            "total_results": len(results),
            "control_count": control_count,
            "candidate_count": candidate_count,
            "complete": len(results) >= 50  # Target sample size
        }

    async def analyze_and_finalize(
        self,
        experiment_id: str
    ) -> ExperimentAnalysis:
        """Analyze experiment and mark complete."""
        analysis = await self.analyzer.analyze_experiment(experiment_id)

        # Update experiment status
        self.supabase.table("memory_injection_experiments").update({
            "status": "completed",
            "ended_at": datetime.now().isoformat(),
            "analysis_result": {
                "recommendation": analysis.recommendation,
                "overall_improvement": analysis.overall_score_improvement,
                "is_significant": analysis.is_significant
            }
        }).eq("experiment_id", experiment_id).execute()

        return analysis

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID."""
        result = self.supabase.table("memory_injection_experiments").select("*").eq("experiment_id", experiment_id).execute()
        return result.data[0] if result.data else None

    async def _get_assignment(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get assignment for execution."""
        result = self.supabase.table("experiment_assignments").select("*").eq("execution_id", execution_id).execute()
        return result.data[0] if result.data else None

    def _config_from_dict(self, experiment: Dict[str, Any]) -> ExperimentConfig:
        """Reconstruct ExperimentConfig from dict."""
        return ExperimentConfig(
            name=experiment["name"],
            description=experiment["description"],
            experiment_type=ExperimentType(experiment["experiment_type"]),
            sample_size_target=experiment.get("sample_size_target", 50),
            min_sample_size=experiment.get("min_sample_size", 20),
            control_config=experiment.get("control_config", {}),
            candidate_config=experiment.get("candidate_config", {})
        )


# ============================================================================
# Quick Start Functions
# ============================================================================

async def start_memory_vs_none_experiment(
    supabase_client,
    retrieval_engine: MemoryRetrievalEngine
) -> str:
    """
    Quick start: Create Experiment A (Memory vs No Memory).

    Usage:
        experiment_id = await start_memory_vs_none_experiment(supabase, retrieval)
        memory_ids = await manager.prepare_execution(exec_id, experiment_id, context)
    """
    manager = MemoryInjectionExperimentManager(supabase_client, retrieval_engine)
    return await manager.create_experiment(EXPERIMENT_A_CONFIG)


async def start_sparse_vs_dense_experiment(
    supabase_client,
    retrieval_engine: MemoryRetrievalEngine
) -> str:
    """
    Quick start: Create Experiment B (Sparse vs Dense Memory).

    Usage:
        experiment_id = await start_sparse_vs_dense_experiment(supabase, retrieval)
        memory_ids = await manager.prepare_execution(exec_id, experiment_id, context)
    """
    manager = MemoryInjectionExperimentManager(supabase_client, retrieval_engine)
    return await manager.create_experiment(EXPERIMENT_B_CONFIG)
