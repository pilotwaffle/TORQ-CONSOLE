"""TORQ Layer 17 - Signal Collector Tests

Tests for the L16SignalCollector.
"""

import pytest

from torq_console.layer17.services import create_signal_collector
from torq_console.layer16 import create_economic_coordination_service, AgentRegistration, AgentCapabilities
from torq_console.layer16.models import ResourceOffer


# =============================================================================
# TESTS
# =============================================================================


class TestL16SignalCollector:
    """Test suite for L16SignalCollector."""

    @pytest.mark.asyncio
    async def test_collect_returns_valid_signal(self):
        """Test that collect returns a valid L16EcosystemSignal."""
        # Create L16 service and register some agents
        l16_service = create_economic_coordination_service()

        # Register a test agent
        capabilities = AgentCapabilities(
            agent_id="test_agent_1",
            agent_type="specialist",
            cpu_capacity=100.0,
            memory_capacity=8.0,
            can_execute=True,
            current_load=0.5,
        )
        registration = AgentRegistration(
            agent_id="test_agent_1",
            agent_type="specialist",
            capabilities=capabilities,
        )
        await l16_service.register_agent(registration)

        # Create collector and collect signal
        collector = create_signal_collector(l16_service)
        signal = await collector.collect()

        # Verify signal structure
        assert signal.signal_id is not None
        assert signal.collected_at is not None
        assert signal.total_agents == 1
        assert signal.market_health >= 0.0
        assert signal.market_health <= 1.0
        assert isinstance(signal.resource_supply, dict)
        assert isinstance(signal.resource_demand, dict)
        assert isinstance(signal.equilibrium_prices, dict)

    @pytest.mark.asyncio
    async def test_collect_uses_verified_l16_fields(self):
        """Test that collect only uses verified L16 producer fields."""
        l16_service = create_economic_coordination_service()
        collector = create_signal_collector(l16_service)

        signal = await collector.collect()

        # All these fields come from verified L16 sources
        verified_fields = [
            "total_agents",
            "active_agents",
            "market_health",
            "resource_supply",
            "resource_demand",
            "supply_demand_gap",
            "equilibrium_prices",
            "market_stable",
            "equilibrium_confidence",
            "active_adjustments",
        ]

        for field in verified_fields:
            assert hasattr(signal, field), f"Missing verified field: {field}"

    @pytest.mark.asyncio
    async def test_collect_with_resource_offers(self):
        """Test collecting signal when resources are being traded."""
        l16_service = create_economic_coordination_service()
        collector = create_signal_collector(l16_service)

        # Register agent first
        capabilities = AgentCapabilities(
            agent_id="seller_1",
            agent_type="specialist",
            cpu_capacity=100.0,
            memory_capacity=8.0,
            can_execute=True,
            current_load=0.2,
        )
        registration = AgentRegistration(
            agent_id="seller_1",
            agent_type="specialist",
            capabilities=capabilities,
        )
        await l16_service.register_agent(registration)

        # Submit a resource offer
        offer = ResourceOffer(
            offer_id="offer_1",
            agent_id="seller_1",
            resource_type="cpu",
            quantity=50.0,
            asking_price=10.0,
        )
        await l16_service.submit_resource_offer(offer)

        # Collect signal
        signal = await collector.collect()

        # Should see the offer reflected in supply
        assert "cpu" in signal.resource_supply
        assert signal.resource_supply["cpu"] > 0


class TestL16EcosystemSignal:
    """Test suite for L16EcosystemSignal model."""

    def test_signal_initializes_with_defaults(self):
        """Test that signal initializes with proper defaults."""
        from torq_console.layer17.models import L16EcosystemSignal

        signal = L16EcosystemSignal()

        assert signal.total_agents == 0
        assert signal.active_agents == 0
        assert signal.market_health == 0.8
        assert signal.resource_supply == {}
        assert signal.resource_demand == {}
        assert signal.supply_demand_gap == 0.0
        assert signal.recent_allocations == []
        assert signal.equilibrium_prices == {}
        assert signal.market_stable is False
        assert signal.equilibrium_confidence == 0.5
        assert signal.active_adjustments == 0

    def test_proposed_fields_marked_in_source(self):
        """Test that proposed fields are marked with comments."""
        from torq_console.layer17.models import L16EcosystemSignal
        import inspect

        # Get the source code
        source = inspect.getsource(L16EcosystemSignal)

        # Check that proposed fields have comments
        assert "# PROPOSED" in source
        assert "tool_demand" in source
        assert "agent_type_distribution" in source
