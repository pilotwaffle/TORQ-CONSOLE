"""
Quick sanity test for Phase 2B components.

Tests basic functionality of NodeRegistry, NetworkController,
EventScheduler, and NetworkMetrics.
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_node_registry():
    """Test NodeRegistry basic functionality."""
    from torq_console.layer12.federation.simulator.phase2b import (
        NodeRegistry,
        create_node,
        create_nodes_with_distribution,
    )
    from torq_console.layer12.federation.simulator.models import Domain

    logger.info("Testing NodeRegistry...")

    # Create registry
    registry = NodeRegistry()

    # Create a single node
    node = create_node(
        node_id="test_node",
        display_name="Test Node",
        domain=Domain.TECHNICAL,
        initial_trust=0.7,
    )

    registry.register_node(node)

    # Verify registration
    assert registry.get_node_count() == 1
    assert registry.get_active_count() == 1

    # Test trust update
    registry.update_trust("test_node", 0.1, "Good behavior")
    retrieved = registry.get_node("test_node")
    assert abs(retrieved.current_trust - 0.8) < 0.01

    # Test batch node creation
    nodes = create_nodes_with_distribution(
        count=10,
        trust_distribution="normal",
        adversarial_ratio=0.2,
    )

    for n in nodes:
        registry.register_node(n)

    # Verify
    assert registry.get_node_count() == 11  # 1 + 10
    assert len(registry.get_adversarial_nodes()) > 0

    # Test summary
    summary = registry.get_network_summary()
    assert summary["total_nodes"] == 11

    logger.info(f"  ✓ NodeRegistry: {summary['total_nodes']} nodes, "
                f"{summary['avg_trust']:.2f} avg trust")

    return True


def test_network_controller():
    """Test NetworkController topology building."""
    from torq_console.layer12.federation.simulator.phase2b import (
        NodeRegistry,
        NetworkController,
        NetworkConfig,
    )
    from torq_console.layer12.federation.simulator.models import Domain

    logger.info("Testing NetworkController...")

    # Create registry and controller
    registry = NodeRegistry()
    config = NetworkConfig(
        node_count=10,
        topology_type="small_world",
        adversarial_ratio=0.1,
    )
    controller = NetworkController(registry, config)

    # Build topology
    topology = controller.build_topology()

    # Verify topology
    assert topology is not None
    assert topology.node_count == 10
    assert len(topology.adjacency_list) == 10

    # Verify nodes were created
    assert registry.get_node_count() == 10

    # Test topology analysis
    summary = topology.get_summary()
    assert summary["node_count"] == 10
    assert summary["average_degree"] > 0

    # Test broadcasting
    node_ids = list(registry.nodes.keys())
    recipients = controller.broadcast_claim(
        claim_envelope=None,  # Not needed for this test
        source=node_ids[0],
        radius=1,
    )

    logger.info(f"  ✓ NetworkController: {topology.node_count} nodes, "
                f"{summary['edge_count']} edges, "
                f"{summary['topology_type']} topology")

    return True


def test_event_scheduler():
    """Test EventScheduler basic functionality."""
    from torq_console.layer12.federation.simulator.phase2b import (
        NodeRegistry,
        NetworkController,
        NetworkConfig,
        EventScheduler,
    )

    logger.info("Testing EventScheduler...")

    # Setup
    registry = NodeRegistry()
    config = NetworkConfig(node_count=5, topology_type="small_world")
    controller = NetworkController(registry, config)
    controller.build_topology()

    scheduler = EventScheduler(controller, registry)

    # Schedule some events
    scheduler.schedule_trust_adjustment("node_0000", 0.1, "Test", delay=0.0)
    scheduler.schedule_trust_adjustment("node_0001", -0.05, "Test", delay=0.5)
    scheduler.schedule_epoch_end(1, delay=1.0)

    # Process events
    processed = 0
    while scheduler.has_more_events() and scheduler.current_time < 2.0:
        scheduler.step()
        processed += 1

    stats = scheduler.get_statistics()

    logger.info(f"  ✓ EventScheduler: {stats['events_processed']} events processed, "
                f"{stats['events_pending']} pending")

    return True


def test_network_metrics():
    """Test NetworkMetricsCalculator."""
    from torq_console.layer12.federation.simulator.phase2b import (
        NodeRegistry,
        NetworkController,
        NetworkConfig,
        NetworkMetricsCalculator,
    )

    logger.info("Testing NetworkMetricsCalculator...")

    # Setup
    registry = NodeRegistry()
    config = NetworkConfig(
        node_count=10,
        topology_type="small_world",
        adversarial_ratio=0.2,
    )
    controller = NetworkController(registry, config)
    controller.build_topology()

    calculator = NetworkMetricsCalculator(controller, registry)

    # Calculate metrics
    centrality = calculator.calculate_centrality()
    health = calculator.calculate_network_health()
    influence = calculator.calculate_influence_distribution()
    collapse = calculator.calculate_collapse_indicators()

    # Verify
    assert len(centrality.degree_centrality) == 10
    assert health.density > 0
    assert 0 <= influence.gini_coefficient <= 1

    # Get summary
    summary = calculator.get_network_summary()
    assert "health_score" in summary
    assert "collapse_risk" in summary

    logger.info(f"  ✓ NetworkMetrics: health={summary['health_score']:.2f}, "
                f"risk={summary['collapse_risk']['level']}, "
                f"gini={influence.gini_coefficient:.2f}")

    return True


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Phase 2B Component Sanity Tests")
    logger.info("=" * 60)

    tests = [
        test_node_registry,
        test_network_controller,
        test_event_scheduler,
        test_network_metrics,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                logger.error(f"  ✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            logger.error(f"  ✗ {test.__name__} error: {e}", exc_info=True)

    logger.info("=" * 60)
    logger.info(f"Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
