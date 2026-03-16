"""TORQ Layer 17 - Agent Registry Tests

Tests for the AgentRegistry service.
"""

import pytest

from torq_console.layer17.models import AgentGenome, GenomeStatus
from torq_console.layer17.services import create_agent_registry


# =============================================================================
# TESTS
# =============================================================================


class TestAgentRegistry:
    """Test suite for AgentRegistry."""

    @pytest.mark.asyncio
    async def test_register_and_retrieve_genome(self, agent_registry):
        """Test registering and retrieving a genome."""
        genome = AgentGenome(
            genome_id="test_001",
            status=GenomeStatus.EXPERIMENTAL,
            toolset=["web_search"],
        )

        genome_id = await agent_registry.register_genome(genome)
        retrieved = await agent_registry.get_genome("test_001")

        assert genome_id == "test_001"
        assert retrieved is not None
        assert retrieved.genome_id == "test_001"
        assert retrieved.toolset == ["web_search"]

    @pytest.mark.asyncio
    async def test_register_duplicate_raises_error(self, agent_registry):
        """Test that registering duplicate genome raises error."""
        genome = AgentGenome(genome_id="test_001")

        await agent_registry.register_genome(genome)

        with pytest.raises(ValueError, match="already registered"):
            await agent_registry.register_genome(genome)

    @pytest.mark.asyncio
    async def test_get_genome_returns_none_for_unknown(self, agent_registry):
        """Test get_genome returns None for unknown genome."""
        result = await agent_registry.get_genome("unknown_genome")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_population_returns_all_genomes(self, agent_registry):
        """Test get_population returns all registered genomes."""
        genomes = [
            AgentGenome(genome_id=f"test_{i:03d}", status=GenomeStatus.EXPERIMENTAL)
            for i in range(3)
        ]

        for genome in genomes:
            await agent_registry.register_genome(genome)

        population = await agent_registry.get_population()

        assert len(population) == 3
        assert all(g.status != GenomeStatus.RETIRED for g in population)

    @pytest.mark.asyncio
    async def test_get_active_population_filters_by_status(self, agent_registry):
        """Test get_active_population filters by status correctly."""
        # Register genomes with different statuses
        await agent_registry.register_genome(AgentGenome(
            genome_id="exp_1",
            status=GenomeStatus.EXPERIMENTAL,
        ))
        await agent_registry.register_genome(AgentGenome(
            genome_id="prod_1",
            status=GenomeStatus.PRODUCTION,
        ))
        await agent_registry.register_genome(AgentGenome(
            genome_id="retired_1",
            status=GenomeStatus.RETIRED,
        ))

        # Get experimental only
        experimental = await agent_registry.get_active_population(status=GenomeStatus.EXPERIMENTAL)
        assert len(experimental) == 1
        assert experimental[0].genome_id == "exp_1"

        # Get production only
        production = await agent_registry.get_active_population(status=GenomeStatus.PRODUCTION)
        assert len(production) == 1
        assert production[0].genome_id == "prod_1"

        # Get all active (excludes retired)
        all_active = await agent_registry.get_active_population()
        assert len(all_active) == 2

    @pytest.mark.asyncio
    async def test_update_fitness(self, agent_registry):
        """Test updating fitness score."""
        genome = AgentGenome(genome_id="test_001")
        await agent_registry.register_genome(genome)

        result = await agent_registry.update_fitness("test_001", 0.85)

        assert result is True
        retrieved = await agent_registry.get_genome("test_001")
        assert retrieved.fitness_score == 0.85

    @pytest.mark.asyncio
    async def test_update_fitness_clamps_to_valid_range(self, agent_registry):
        """Test fitness score is clamped to 0.0-1.0 range."""
        genome = AgentGenome(genome_id="test_001")
        await agent_registry.register_genome(genome)

        await agent_registry.update_fitness("test_001", 1.5)
        retrieved = await agent_registry.get_genome("test_001")
        assert retrieved.fitness_score == 1.0

        await agent_registry.update_fitness("test_001", -0.5)
        retrieved = await agent_registry.get_genome("test_001")
        assert retrieved.fitness_score == 0.0

    @pytest.mark.asyncio
    async def test_update_fitness_returns_false_for_unknown(self, agent_registry):
        """Test update_fitness returns False for unknown genome."""
        result = await agent_registry.update_fitness("unknown", 0.5)
        assert result is False

    @pytest.mark.asyncio
    async def test_retire_agent(self, agent_registry):
        """Test retiring an agent."""
        genome = AgentGenome(
            genome_id="test_001",
            status=GenomeStatus.PRODUCTION,
        )
        await agent_registry.register_genome(genome)

        result = await agent_registry.retire_agent("test_001")

        assert result is True
        retrieved = await agent_registry.get_genome("test_001")
        assert retrieved.status == GenomeStatus.RETIRED
        assert retrieved.retired_at is not None

    @pytest.mark.asyncio
    async def test_retire_agent_returns_false_for_unknown(self, agent_registry):
        """Test retire_agent returns False for unknown genome."""
        result = await agent_registry.retire_agent("unknown")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_type_distribution(self, agent_registry):
        """Test getting type distribution."""
        # Register mixed population
        await agent_registry.register_genome(AgentGenome(
            genome_id="exp_1", status=GenomeStatus.EXPERIMENTAL
        ))
        await agent_registry.register_genome(AgentGenome(
            genome_id="exp_2", status=GenomeStatus.EXPERIMENTAL
        ))
        await agent_registry.register_genome(AgentGenome(
            genome_id="prod_1", status=GenomeStatus.PRODUCTION
        ))
        await agent_registry.register_genome(AgentGenome(
            genome_id="retired_1", status=GenomeStatus.RETIRED
        ))

        distribution = await agent_registry.get_type_distribution()

        assert distribution["experimental"] == 2
        assert distribution["production"] == 1
        assert distribution["retired"] == 1

    @pytest.mark.asyncio
    async def test_get_type_distribution_empty_population(self, agent_registry):
        """Test type distribution with empty population."""
        distribution = await agent_registry.get_type_distribution()

        assert distribution["experimental"] == 0
        assert distribution["production"] == 0
        assert distribution["retired"] == 0
