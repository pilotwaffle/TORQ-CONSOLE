"""TORQ Layer 17 - Agent Registry Service

This service manages the agent genome population with Supabase persistence.
"""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from ..models import AgentGenome, GenomeStatus


# =============================================================================
# AGENT REGISTRY SERVICE
# =============================================================================


class AgentRegistry:
    """Service for managing agent genome population.

    Handles:
    - Genome registration and storage
    - Population queries with filtering
    - Fitness updates
    - Agent retirement
    - Type distribution tracking
    """

    def __init__(self, supabase_client=None):
        """Initialize the agent registry.

        Args:
            supabase_client: Optional Supabase client for persistence
        """
        self._supabase = supabase_client
        self._genomes: dict[str, AgentGenome] = {}

    async def register_genome(
        self,
        genome: AgentGenome,
    ) -> str:
        """Register a new agent genome.

        Args:
            genome: Genome to register

        Returns:
            Genome ID

        Raises:
            ValueError: If genome_id already exists
        """
        if genome.genome_id in self._genomes:
            raise ValueError(f"Genome {genome.genome_id} already registered")

        self._genomes[genome.genome_id] = genome

        # Persist to Supabase if available
        if self._supabase:
            await self._persist_genome(genome)

        return genome.genome_id

    async def get_genome(
        self,
        genome_id: str,
    ) -> AgentGenome | None:
        """Get a genome by ID.

        Args:
            genome_id: Genome identifier

        Returns:
            AgentGenome if found, None otherwise
        """
        return self._genomes.get(genome_id)

    async def get_population(self) -> list[AgentGenome]:
        """Get all genomes in the population.

        Returns:
            List of all genomes
        """
        return list(self._genomes.values())

    async def get_active_population(
        self,
        status: GenomeStatus | None = None,
    ) -> list[AgentGenome]:
        """Get active genomes, optionally filtered by status.

        Args:
            status: Optional status filter (experimental/production)

        Returns:
            List of active genomes
        """
        genomes = list(self._genomes.values())

        # Filter out retired
        active = [g for g in genomes if g.status != GenomeStatus.RETIRED]

        # Filter by status if specified
        if status is not None:
            active = [g for g in active if g.status == status]

        return active

    async def update_fitness(
        self,
        genome_id: str,
        fitness: float,
    ) -> bool:
        """Update fitness score for a genome.

        Args:
            genome_id: Genome identifier
            fitness: New fitness score (0.0 to 1.0)

        Returns:
            True if updated, False if genome not found
        """
        genome = self._genomes.get(genome_id)
        if genome is None:
            return False

        genome.fitness_score = max(0.0, min(1.0, fitness))
        genome.updated_at = datetime.utcnow() if hasattr(datetime, 'utcnow') else None

        if self._supabase:
            await self._persist_genome(genome)

        return True

    async def retire_agent(self, genome_id: str) -> bool:
        """Retire an agent from the population.

        Args:
            genome_id: Genome identifier

        Returns:
            True if retired, False if genome not found
        """
        genome = self._genomes.get(genome_id)
        if genome is None:
            return False

        genome.status = GenomeStatus.RETIRED
        from datetime import datetime
        genome.retired_at = datetime.utcnow() if hasattr(datetime, 'utcnow') else None
        genome.updated_at = genome.retired_at

        if self._supabase:
            await self._persist_genome(genome)

        return True

    async def get_type_distribution(self) -> dict[str, int]:
        """Get distribution of agent types in population.

        Returns:
            Dictionary with counts for each agent type
            (experimental, production, retired)
        """
        distribution = {
            "experimental": 0,
            "production": 0,
            "retired": 0,
        }

        for genome in self._genomes.values():
            distribution[genome.status.value] += 1

        return distribution

    async def _persist_genome(self, genome: AgentGenome):
        """Persist genome to Supabase.

        Args:
            genome: Genome to persist
        """
        if not self._supabase:
            return

        # Convert to dict for Supabase
        data = {
            "genome_id": genome.genome_id,
            "parent_genome_id": genome.parent_genome_id,
            "generation": genome.generation,
            "status": genome.status.value,
            "toolset": genome.toolset,
            "min_toolset_size": genome.min_toolset_size,
            "max_toolset_size": genome.max_toolset_size,
            "llm_model": genome.llm_model,
            "llm_temperature": genome.llm_temperature,
            "llm_max_tokens": genome.llm_max_tokens,
            "missions_completed": genome.missions_completed,
            "missions_attempted": genome.missions_attempted,
            "total_value_generated": genome.total_value_generated,
            "total_cost_incurred": genome.total_cost_incurred,
            "fitness_score": genome.fitness_score,
            "completion_rate": genome.completion_rate,
            "efficiency_score": genome.efficiency_score,
            "reliability_score": genome.reliability_score,
            "benchmark_completion_score": genome.benchmark_completion_score,
            "benchmark_latency_score": genome.benchmark_latency_score,
            "benchmark_consistency_score": genome.benchmark_consistency_score,
            "benchmark_overall_score": genome.benchmark_overall_score,
            "benchmark_passed": genome.benchmark_passed,
            "created_at": genome.created_at.isoformat(),
            "updated_at": genome.updated_at.isoformat(),
            "retired_at": genome.retired_at.isoformat() if genome.retired_at else None,
        }

        await self._supabase.table("agent_genomes").upsert(data).execute()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_agent_registry(supabase_client=None) -> AgentRegistry:
    """Factory function to create an agent registry.

    Args:
        supabase_client: Optional Supabase client

    Returns:
        Configured AgentRegistry instance
    """
    return AgentRegistry(supabase_client=supabase_client)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "AgentRegistry",
    "create_agent_registry",
]
