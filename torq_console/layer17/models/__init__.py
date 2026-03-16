"""TORQ Layer 17 - Core Data Models

This module defines the core data structures for agent genome evolution.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def datetime_utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def generate_genome_id() -> str:
    """Generate a unique genome ID."""
    return f"genome_{uuid4().hex[:12]}"


# =============================================================================
# GENOME STATUS
# =============================================================================


class GenomeStatus(str, Enum):
    """Status of an agent genome in the population."""
    EXPERIMENTAL = "experimental"
    PRODUCTION = "production"
    RETIRED = "retired"


# =============================================================================
# AGENT GENOME MODEL
# =============================================================================


class AgentGenome(BaseModel):
    """A TORQ agent genome defining toolset and configuration.

    This represents the evolvable "DNA" of a TORQ agent - its available
    tools, LLM model, and learned parameters from ecosystem interaction.
    """

    # Identity
    genome_id: str = Field(default_factory=generate_genome_id, description="Unique genome identifier")
    parent_genome_id: str | None = Field(default=None, description="Parent genome ID if mutated")
    generation: int = Field(default=0, ge=0, description="Generation number (0 = founder)")

    # Status
    status: GenomeStatus = Field(default=GenomeStatus.EXPERIMENTAL, description="Genome status")

    # Toolset (evolvable)
    toolset: list[str] = Field(
        default_factory=list,
        description="Available tools for this agent",
    )
    min_toolset_size: int = Field(default=3, ge=1, description="Minimum tools required")
    max_toolset_size: int = Field(default=15, ge=1, description="Maximum tools allowed")

    # LLM Configuration
    llm_model: str = Field(default="claude-sonnet-4-6", description="Primary LLM model")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature")
    llm_max_tokens: int = Field(default=4096, ge=1, description="Max tokens per response")

    # Performance Metrics (from ecosystem interaction)
    missions_completed: int = Field(default=0, ge=0, description="Total missions completed")
    missions_attempted: int = Field(default=0, ge=0, description="Total missions attempted")
    total_value_generated: float = Field(default=0.0, ge=0.0, description="Total value from missions")
    total_cost_incurred: float = Field(default=0.0, ge=0.0, description="Total cost from missions")

    # Fitness Scores
    fitness_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Overall fitness score")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Mission completion rate")
    efficiency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Resource efficiency score")
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Reliability score")

    # Benchmark Results (from evaluation harness)
    benchmark_completion_score: float | None = Field(default=None, ge=0.0, le=1.0)
    benchmark_latency_score: float | None = Field(default=None, ge=0.0, le=1.0)
    benchmark_consistency_score: float | None = Field(default=None, ge=0.0, le=1.0)
    benchmark_overall_score: float | None = Field(default=None, ge=0.0, le=1.0)
    benchmark_passed: bool = Field(default=False, description="Whether benchmarks passed")

    # Metadata
    created_at: datetime = Field(default_factory=datetime_utcnow, description="When genome was created")
    updated_at: datetime = Field(default_factory=datetime_utcnow, description="When genome was last updated")
    retired_at: datetime | None = Field(default=None, description="When genome was retired")

    @property
    def completion_rate_calculated(self) -> float:
        """Calculate completion rate from missions."""
        if self.missions_attempted == 0:
            return 0.0
        return self.missions_completed / self.missions_attempted

    @property
    def is_production_ready(self) -> bool:
        """Check if genome meets production readiness criteria."""
        return (
            self.status == GenomeStatus.PRODUCTION
            and self.benchmark_passed is True
            and self.completion_rate_calculated >= 0.8
        )


# =============================================================================
# L16 ECOSYSTEM SIGNAL
# =============================================================================


class L16EcosystemSignal(BaseModel):
    """Signal collected from Layer 16 economic coordination system.

    This represents the ecosystem state that drives evolution -
    which tools are in demand, which agents are winning bids,
    and where the market has gaps.
    """

    signal_id: str = Field(default_factory=lambda: f"signal_{uuid4().hex[:12]}", description="Unique signal identifier")
    collected_at: datetime = Field(default_factory=datetime_utcnow, description="When signal was collected")

    # Market State (verified from L16)
    total_agents: int = Field(default=0, ge=0, description="Total agents in market")
    active_agents: int = Field(default=0, ge=0, description="Active agents")
    market_health: float = Field(default=0.8, ge=0.0, le=1.0, description="Overall market health")

    # Resource Supply/Demand (verified from L16)
    resource_supply: dict[str, float] = Field(default_factory=dict, description="Supply per resource type")
    resource_demand: dict[str, float] = Field(default_factory=dict, description="Demand per resource type")
    supply_demand_gap: float = Field(default=0.0, description="Supply minus demand")

    # Mission Allocation Data (verified from L16)
    total_missions_processed: int = Field(default=0, ge=0, description="Missions processed in period")
    total_missions_allocated: int = Field(default=0, ge=0, description="Missions successfully allocated")
    allocation_success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Successful allocation rate")

    # Recent Winning Allocations (verified from L16)
    recent_allocations: list[str] = Field(
        default_factory=list,
        description="Recent winning agent IDs",
        max_length=100,
    )

    # Price Information (verified from L16)
    equilibrium_prices: dict[str, float] = Field(default_factory=dict, description="Price per resource")

    # Equilibrium State (verified from L16)
    market_stable: bool = Field(default=False, description="Whether market is in equilibrium")
    equilibrium_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Equilibrium confidence")

    # Incentive Data (verified from L16)
    active_adjustments: int = Field(default=0, ge=0, description="Number of active incentive adjustments")

    # PROPOSED FIELDS (not yet in L16, for future use)
    tool_demand: dict[str, float] = Field(
        default_factory=dict,
        description="# PROPOSED: Demand score per tool",
    )
    agent_type_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="# PROPOSED: Count of agents by type",
    )


# =============================================================================
# BENCHMARK EVALUATION RESULT
# =============================================================================


class BenchmarkEvaluationResult(BaseModel):
    """Result from running benchmark suite on a genome.

    This is NOT final ecosystem fitness - just benchmark results.
    Phase 4 does not claim evolutionary fitness.
    """

    genome_id: str = Field(description="Genome being evaluated")
    benchmark_count: int = Field(default=0, ge=0, description="Number of benchmarks run")

    # Individual Scores
    completion_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Task completion score")
    latency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Latency performance score")
    consistency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Result consistency score")

    # Overall
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Weighted overall score")

    # Pass/Fail
    passed: bool = Field(default=False, description="Whether benchmarks passed threshold")

    # Details
    evaluated_at: datetime = Field(default_factory=datetime_utcnow, description="When evaluation was performed")
    evaluation_duration_ms: float = Field(default=0.0, ge=0.0, description="Evaluation duration")

    # Per-Benchmark Details
    benchmark_details: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Individual benchmark results",
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Utility
    "datetime_utcnow",
    "generate_genome_id",
    # Enum
    "GenomeStatus",
    # Models
    "AgentGenome",
    "L16EcosystemSignal",
    "BenchmarkEvaluationResult",
]
