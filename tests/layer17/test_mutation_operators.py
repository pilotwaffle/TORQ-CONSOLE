"""TORQ Layer 17 - Mutation Operator Tests

Tests for the MutationEngine.
"""

import pytest

from torq_console.layer17.models import AgentGenome, GenomeStatus
from torq_console.layer17.mutation import create_mutation_engine


# =============================================================================
# TESTS
# =============================================================================


class TestMutationEngine:
    """Test suite for MutationEngine."""

    def test_mutation_creates_new_genome_id(self, mutation_engine):
        """Test that mutation produces a new genome_id."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search"],
        )

        result = mutation_engine._rng  # Access RNG directly for sync test
        child = mutation_engine.mutate_genome.__wrapped__(mutation_engine, parent)

        assert child.genome_id != parent.genome_id
        assert child.parent_genome_id == "parent_001"

    @pytest.mark.asyncio
    async def test_mutation_increments_generation(self, mutation_engine):
        """Test that mutation increments generation number."""
        parent = AgentGenome(
            genome_id="parent_001",
            generation=5,
            toolset=["web_search"],
        )

        child = await mutation_engine.mutate_genome(parent)

        assert child.generation == 6

    @pytest.mark.asyncio
    async def test_mutation_sets_parent_genome_id(self, mutation_engine):
        """Test that mutation correctly sets parent_genome_id."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search"],
        )

        child = await mutation_engine.mutate_genome(parent)

        assert child.parent_genome_id == "parent_001"

    @pytest.mark.asyncio
    async def test_mutation_respects_min_toolset_size(self, mutation_engine):
        """Test that toolset never drops below min_toolset_size."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search", "code_executor", "file_read"],
            min_toolset_size=3,
            max_toolset_size=10,
        )

        child = await mutation_engine.mutate_genome(
            parent,
            mutation_rate=1.0,  # Max mutations
            max_mutations=10,
        )

        assert len(child.toolset) >= child.min_toolset_size

    @pytest.mark.asyncio
    async def test_mutation_respects_max_toolset_size(self, mutation_engine):
        """Test that toolset never exceeds max_toolset_size."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search"],
            min_toolset_size=1,
            max_toolset_size=5,
        )

        child = await mutation_engine.mutate_genome(
            parent,
            mutation_rate=1.0,  # Max mutations
            max_mutations=10,
        )

        assert len(child.toolset) <= child.max_toolset_size

    @pytest.mark.asyncio
    async def test_zero_mutation_rate_produces_identical_toolset(self, mutation_engine):
        """Test that mutation_rate of 0.0 produces identical toolset."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search", "code_executor", "file_read"],
        )

        child = await mutation_engine.mutate_genome(parent, mutation_rate=0.0)

        assert child.toolset == parent.toolset
        assert child.llm_model == parent.llm_model
        assert child.llm_temperature == parent.llm_temperature

    @pytest.mark.asyncio
    async def test_deterministic_mutation_with_fixed_seed(self, mutation_engine):
        """Test that fixed seed produces repeatable output."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search", "code_executor"],
            generation=0,
        )

        # Create two engines with same seed
        engine1 = create_mutation_engine(seed=42)
        engine2 = create_mutation_engine(seed=42)

        result1 = await engine1.mutate_genome(parent, mutation_rate=0.5)
        result2 = await engine2.mutate_genome(parent, mutation_rate=0.5)

        # Results should be identical
        assert result1.toolset == result2.toolset
        assert result1.llm_model == result2.llm_model
        # genome_id will differ but everything else should match

    @pytest.mark.asyncio
    async def test_different_seeds_produce_different_results(self, mutation_engine):
        """Test that different seeds produce different results."""
        parent = AgentGenome(
            genome_id="parent_001",
            toolset=["web_search", "code_executor"],
        )

        engine1 = create_mutation_engine(seed=42)
        engine2 = create_mutation_engine(seed=123)

        result1 = await engine1.mutate_genome(parent, mutation_rate=0.5)
        result2 = await engine2.mutate_genome(parent, mutation_rate=0.5)

        # At least one should differ (probabilistic but very likely)
        # We compare toolsets as that's most likely to differ
        results_differ = (
            result1.toolset != result2.toolset or
            result1.llm_model != result2.llm_model
        )
        assert results_differ, "Different seeds should produce different results"

    @pytest.mark.asyncio
    async def test_invalid_mutation_rate_raises_error(self, mutation_engine):
        """Test that invalid mutation_rate raises ValueError."""
        parent = AgentGenome(genome_id="parent_001")

        with pytest.raises(ValueError, match="mutation_rate must be 0.0 to 1.0"):
            await mutation_engine.mutate_genome(parent, mutation_rate=1.5)

        with pytest.raises(ValueError, match="mutation_rate must be 0.0 to 1.0"):
            await mutation_engine.mutate_genome(parent, mutation_rate=-0.1)

    @pytest.mark.asyncio
    async def test_child_starts_as_experimental(self, mutation_engine):
        """Test that mutated genome starts as experimental."""
        parent = AgentGenome(
            genome_id="parent_001",
            status=GenomeStatus.PRODUCTION,
        )

        child = await mutation_engine.mutate_genome(parent)

        assert child.status == GenomeStatus.EXPERIMENTAL

    def test_can_mutate_enforces_experiment_limit(self, mutation_engine):
        """Test that can_mutate enforces MAX_ACTIVE_EXPERIMENTS."""
        # At limit
        assert not mutation_engine.can_mutate(
            mutation_engine.MAX_ACTIVE_EXPERIMENTS
        )

        # Under limit
        assert mutation_engine.can_mutate(mutation_engine.MAX_ACTIVE_EXPERIMENTS - 1)

        # Over limit
        assert mutation_engine.can_mutate(0)
