"""TORQ Layer 17 - Mutation Operators

This module implements genetic mutation operators for agent toolset evolution.
"""

import random
from datetime import datetime
from typing import Literal

from ..models import AgentGenome, GenomeStatus, generate_genome_id


# =============================================================================
# MUTATION OPERATORS
# =============================================================================


class MutationEngine:
    """Engine for mutating agent toolsets through genetic operations.

    Operators:
    - add_tool: Add a new tool to the toolset
    - remove_tool: Remove a tool from the toolset
    - replace_tool: Replace one tool with another
    - swap_llm: Change the LLM model
    - adjust_temperature: Mutate LLM temperature

    Enforces:
    - MAX_MUTATIONS_PER_CYCLE: Maximum mutations per mutate call
    - MAX_ACTIVE_EXPERIMENTS: Maximum experimental genomes allowed
    """

    # Mutation constraints
    MAX_MUTATIONS_PER_CYCLE = 3
    MAX_ACTIVE_EXPERIMENTS = 5

    # Verified tool names from TORQ ecosystem
    VERIFIED_TOOLS = [
        "web_search",
        "code_executor",
        "file_read",
        "file_write",
        "bash",
        "git",
        "database_query",
        "api_call",
        "web_scrape",
        "data_analyze",
        "text_process",
        "image_gen",
        "monitor",
        "validate",
        "test_runner",
        "documentation",
    ]

    # Verified LLM models
    VERIFIED_LLM_MODELS = [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "claude-haiku-4-5",
        "gpt-4o",
        "gpt-4o-mini",
        "o1-preview",
        "o1-mini",
    ]

    def __init__(self, seed: int | None = None):
        """Initialize the mutation engine.

        Args:
            seed: Optional random seed for deterministic testing
        """
        self._rng = random.Random(seed)
        self._seed = seed

    async def mutate_genome(
        self,
        genome: AgentGenome,
        mutation_rate: float = 0.1,
        max_mutations: int | None = None,
    ) -> AgentGenome:
        """Mutate a genome to create a new agent variant.

        Args:
            genome: Parent genome to mutate
            mutation_rate: Probability of each mutation occurring (0.0 to 1.0)
            max_mutations: Maximum mutations to apply (defaults to MAX_MUTATIONS_PER_CYCLE)

        Returns:
            New mutated AgentGenome with unique genome_id

        Raises:
            ValueError: If mutation parameters are invalid
        """
        if mutation_rate < 0.0 or mutation_rate > 1.0:
            raise ValueError(f"mutation_rate must be 0.0 to 1.0, got {mutation_rate}")

        if max_mutations is None:
            max_mutations = self.MAX_MUTATIONS_PER_CYCLE

        # Create child genome
        child_genome = AgentGenome(
            genome_id=generate_genome_id(),
            parent_genome_id=genome.genome_id,
            generation=genome.generation + 1,
            status=GenomeStatus.EXPERIMENTAL,
            toolset=genome.toolset.copy(),
            min_toolset_size=genome.min_toolset_size,
            max_toolset_size=genome.max_toolset_size,
            llm_model=genome.llm_model,
            llm_temperature=genome.llm_temperature,
            llm_max_tokens=genome.llm_max_tokens,
        )

        # Apply mutations based on rate
        mutations_applied = 0

        # Toolset mutations
        if self._rng.random() < mutation_rate and mutations_applied < max_mutations:
            if self._should_add_tool(child_genome):
                self._add_tool(child_genome)
                mutations_applied += 1

        if self._rng.random() < mutation_rate and mutations_applied < max_mutations:
            if self._should_remove_tool(child_genome):
                self._remove_tool(child_genome)
                mutations_applied += 1

        if self._rng.random() < mutation_rate and mutations_applied < max_mutations:
            if self._should_replace_tool(child_genome):
                self._replace_tool(child_genome)
                mutations_applied += 1

        # LLM mutations
        if self._rng.random() < mutation_rate and mutations_applied < max_mutations:
            self._swap_llm(child_genome)
            mutations_applied += 1

        if self._rng.random() < mutation_rate and mutations_applied < max_mutations:
            self._adjust_temperature(child_genome)
            mutations_applied += 1

        # Ensure toolset constraints
        self._enforce_toolset_bounds(child_genome)

        return child_genome

    def _should_add_tool(self, genome: AgentGenome) -> bool:
        """Check if tool should be added."""
        # Add if below max size and has room
        return len(genome.toolset) < genome.max_toolset_size

    def _add_tool(self, genome: AgentGenome):
        """Add a random new tool to the toolset."""
        available = [t for t in self.VERIFIED_TOOLS if t not in genome.toolset]
        if available:
            new_tool = self._rng.choice(available)
            genome.toolset.append(new_tool)

    def _should_remove_tool(self, genome: AgentGenome) -> bool:
        """Check if tool should be removed."""
        # Remove if above min size
        return len(genome.toolset) > genome.min_toolset_size

    def _remove_tool(self, genome: AgentGenome):
        """Remove a random tool from the toolset."""
        if genome.toolset:
            tool_to_remove = self._rng.choice(genome.toolset)
            genome.toolset.remove(tool_to_remove)

    def _should_replace_tool(self, genome: AgentGenome) -> bool:
        """Check if tool should be replaced."""
        # Replace if toolset not empty
        return len(genome.toolset) > 0

    def _replace_tool(self, genome: AgentGenome):
        """Replace one tool with another."""
        if not genome.toolset:
            return

        tool_to_replace = self._rng.choice(genome.toolset)
        available = [t for t in self.VERIFIED_TOOLS if t not in genome.toolset]

        if available:
            genome.toolset.remove(tool_to_replace)
            genome.toolset.append(self._rng.choice(available))

    def _swap_llm(self, genome: AgentGenome):
        """Swap to a different LLM model."""
        available = [m for m in self.VERIFIED_LLM_MODELS if m != genome.llm_model]
        if available:
            genome.llm_model = self._rng.choice(available)

    def _adjust_temperature(self, genome: AgentGenome):
        """Adjust LLM temperature slightly."""
        delta = self._rng.uniform(-0.1, 0.1)
        genome.llm_temperature = max(0.0, min(1.0, genome.llm_temperature + delta))

    def _enforce_toolset_bounds(self, genome: AgentGenome):
        """Enforce min/max toolset size constraints."""
        current_size = len(genome.toolset)

        if current_size < genome.min_toolset_size:
            # Add random tools to reach minimum
            needed = genome.min_toolset_size - current_size
            available = [t for t in self.VERIFIED_TOOLS if t not in genome.toolset]
            for _ in range(min(needed, len(available))):
                genome.toolset.append(self._rng.choice(available))

        if current_size > genome.max_toolset_size:
            # Remove tools to reach maximum
            excess = current_size - genome.max_toolset_size
            for _ in range(excess):
                if genome.toolset:
                    genome.toolset.pop()

    def can_mutate(self, experimental_count: int) -> bool:
        """Check if mutation is allowed given experiment constraints.

        Args:
            experimental_count: Current number of experimental genomes

        Returns:
            True if mutation allowed, False otherwise
        """
        return experimental_count < self.MAX_ACTIVE_EXPERIMENTS


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_mutation_engine(seed: int | None = None) -> MutationEngine:
    """Factory function to create a mutation engine.

    Args:
        seed: Optional random seed for deterministic testing

    Returns:
        Configured MutationEngine instance
    """
    return MutationEngine(seed=seed)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "MutationEngine",
    "create_mutation_engine",
]
