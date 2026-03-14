"""
Test script to validate Phase 2B executor functionality.

Tests the executor milestones:
1. initialize 3-node network
2. route one claim across nodes
3. confirm each node processes through real Phase 2A path
4. aggregate network metrics for one epoch
5. run 10 epochs
6. generate report
7. then add scenario loader
"""

import asyncio
import logging
import sys

# Add parent directory to path
sys.path.insert(0, "/e/TORQ-CONSOLE")

from torq_console.layer12.federation.simulator.phase2b.executor_network import (
    NetworkSimulationConfig,
    NetworkSimulationExecutor,
    run_network_simulation,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_milestone_1_initialize():
    """Milestone 1: Initialize 3-node network."""
    from torq_console.layer12.federation.federation_identity_guard import (
        FederationIdentityGuard,
    )
    from torq_console.layer12.federation.inbound_claim_processor import (
        InboundFederatedClaimProcessor,
        ProcessorConfig,
    )
    from torq_console.layer12.federation.safeguards.federation_eligibility_filter import (
        create_eligibility_filter,
    )
    from torq_console.layer12.federation.safeguards.context_similarity_engine import (
        create_context_similarity_engine,
    )
    from torq_console.layer12.federation.safeguards.plurality_preservation_rules import (
        create_plurality_preservation_rules,
    )
    from torq_console.layer12.federation.safeguards.allocative_boundary_guard import (
        create_allocative_boundary_guard,
    )
    from torq_console.layer12.federation.safeguards.trust_decay_model import (
        create_trust_decay_model,
    )

    logger.info("=" * 60)
    logger.info("Milestone 1: Initialize 3-node network")
    logger.info("=" * 60)

    config = NetworkSimulationConfig(
        node_count=3,
        topology_type="small_world",
        epochs=1,
        claims_per_epoch=5,
        verbose=True,
    )

    identity_guard = FederationIdentityGuard()

    # Create processor with all safeguards enabled
    processor_config = ProcessorConfig(
        enable_eligibility_filter=True,
        enable_similarity_engine=True,
        enable_plurality_preservation=True,
        enable_allocative_boundaries=True,
        enable_trust_decay=True,
    )

    processor = InboundFederatedClaimProcessor(
        identity_guard=identity_guard,
        config=processor_config,
        eligibility_filter=create_eligibility_filter(),
        similarity_engine=create_context_similarity_engine(),
        plurality_rules=create_plurality_preservation_rules(),
        allocative_guard=create_allocative_boundary_guard(),
        trust_decay=create_trust_decay_model(),
    )

    executor = NetworkSimulationExecutor(config, processor, identity_guard)

    try:
        await executor.initialize()

        assert executor.registry.get_node_count() == 3, "Should have 3 nodes"
        assert executor.controller.topology is not None, "Should have topology"
        assert executor.scheduler is not None, "Should have scheduler"
        assert executor.metrics_calculator is not None, "Should have metrics calculator"

        logger.info("  ✓ Network initialized successfully")
        logger.info(f"    - Nodes: {executor.registry.get_node_count()}")
        logger.info(f"    - Topology: {executor.controller.topology.topology_type}")
        logger.info(f"    - Edges: {executor.controller.topology.edge_count}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Initialization failed: {e}", exc_info=True)
        return False


async def test_milestone_5_run_10_epochs():
    """Milestone 5: Run 10 epochs."""
    from torq_console.layer12.federation.federation_identity_guard import (
        FederationIdentityGuard,
    )
    from torq_console.layer12.federation.inbound_claim_processor import (
        InboundFederatedClaimProcessor,
        ProcessorConfig,
    )
    from torq_console.layer12.federation.safeguards.federation_eligibility_filter import (
        create_eligibility_filter,
    )
    from torq_console.layer12.federation.safeguards.context_similarity_engine import (
        create_context_similarity_engine,
    )
    from torq_console.layer12.federation.safeguards.plurality_preservation_rules import (
        create_plurality_preservation_rules,
    )
    from torq_console.layer12.federation.safeguards.allocative_boundary_guard import (
        create_allocative_boundary_guard,
    )
    from torq_console.layer12.federation.safeguards.trust_decay_model import (
        create_trust_decay_model,
    )

    logger.info("=" * 60)
    logger.info("Milestone 5: Run 10 epochs")
    logger.info("=" * 60)

    config = NetworkSimulationConfig(
        node_count=5,
        topology_type="small_world",
        epochs=10,
        claims_per_epoch=20,
        verbose=True,
    )

    identity_guard = FederationIdentityGuard()

    processor_config = ProcessorConfig(
        enable_eligibility_filter=True,
        enable_similarity_engine=True,
        enable_plurality_preservation=True,
        enable_allocative_boundaries=True,
        enable_trust_decay=True,
    )

    processor = InboundFederatedClaimProcessor(
        identity_guard=identity_guard,
        config=processor_config,
        eligibility_filter=create_eligibility_filter(),
        similarity_engine=create_context_similarity_engine(),
        plurality_rules=create_plurality_preservation_rules(),
        allocative_guard=create_allocative_boundary_guard(),
        trust_decay=create_trust_decay_model(),
    )

    executor = NetworkSimulationExecutor(config, processor, identity_guard)

    try:
        report = await executor.run_simulation()

        assert report.success, f"Simulation should succeed: {report.error}"
        assert report.epochs_completed == 10, f"Should complete 10 epochs, got {report.epochs_completed}"
        assert len(report.epoch_reports) == 10, "Should have 10 epoch reports"

        logger.info("  ✓ 10 epochs completed successfully")
        logger.info(f"    - Total claims processed: {report.total_claims_processed}")
        logger.info(f"    - Acceptance rate: {report.overall_acceptance_rate:.1%}")
        logger.info(f"    - Final network health: {report.final_network_health:.2f}")
        logger.info(f"    - Collapse risk: {report.final_collapse_risk}")

        # Show epoch progression
        logger.info("\n  Epoch Progression:")
        for er in report.epoch_reports[::3]:  # Show every 3rd epoch
            logger.info(
                f"    Epoch {er.epoch_number}: "
                f"{er.claims_accepted}/{er.claims_processed} accepted, "
                f"trust={er.avg_trust:.3f}"
            )

        return True

    except Exception as e:
        logger.error(f"  ✗ Simulation failed: {e}", exc_info=True)
        return False


async def test_milestone_6_generate_report():
    """Milestone 6: Generate and validate report."""
    from torq_console.layer12.federation.federation_identity_guard import (
        FederationIdentityGuard,
    )
    from torq_console.layer12.federation.inbound_claim_processor import (
        InboundFederatedClaimProcessor,
        ProcessorConfig,
    )
    from torq_console.layer12.federation.safeguards.federation_eligibility_filter import (
        create_eligibility_filter,
    )
    from torq_console.layer12.federation.safeguards.context_similarity_engine import (
        create_context_similarity_engine,
    )
    from torq_console.layer12.federation.safeguards.plurality_preservation_rules import (
        create_plurality_preservation_rules,
    )
    from torq_console.layer12.federation.safeguards.allocative_boundary_guard import (
        create_allocative_boundary_guard,
    )
    from torq_console.layer12.federation.safeguards.trust_decay_model import (
        create_trust_decay_model,
    )

    logger.info("=" * 60)
    logger.info("Milestone 6: Generate comprehensive report")
    logger.info("=" * 60)

    config = NetworkSimulationConfig(
        node_count=10,
        topology_type="small_world",
        epochs=5,
        claims_per_epoch=30,
        verbose=True,
    )

    identity_guard = FederationIdentityGuard()

    processor_config = ProcessorConfig(
        enable_eligibility_filter=True,
        enable_similarity_engine=True,
        enable_plurality_preservation=True,
        enable_allocative_boundaries=True,
        enable_trust_decay=True,
    )

    processor = InboundFederatedClaimProcessor(
        identity_guard=identity_guard,
        config=processor_config,
        eligibility_filter=create_eligibility_filter(),
        similarity_engine=create_context_similarity_engine(),
        plurality_rules=create_plurality_preservation_rules(),
        allocative_guard=create_allocative_boundary_guard(),
        trust_decay=create_trust_decay_model(),
    )

    executor = NetworkSimulationExecutor(config, processor, identity_guard)

    try:
        report = await executor.run_simulation()

        # Validate report structure
        assert report.scenario_name == "network_simulation"
        assert report.initial_node_count == 10
        assert report.execution_time.total_seconds() > 0
        assert len(report.epoch_reports) == 5

        # Validate summary
        summary = report.get_summary()
        assert "epochs" in summary
        assert "nodes" in summary
        assert "acceptance_rate" in summary
        assert "collapse_risk" in summary

        logger.info("  ✓ Report generated successfully")
        logger.info(f"\n  Summary:")
        for key, value in summary.items():
            logger.info(f"    {key}: {value}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Report generation failed: {e}", exc_info=True)
        return False


async def test_quick_start_function():
    """Test the quick-start run_network_simulation function."""
    logger.info("=" * 60)
    logger.info("Quick Start Test")
    logger.info("=" * 60)

    try:
        report = await run_network_simulation(
            node_count=5,
            topology_type="small_world",
            epochs=5,
            claims_per_epoch=20,
            verbose=True,
        )

        assert report.success, f"Quick start failed: {report.error}"

        logger.info("  ✓ Quick start function works")
        logger.info(f"    - {report.total_claims_processed} claims processed")
        logger.info(f"    - {report.overall_acceptance_rate:.1%} acceptance rate")
        logger.info(f"    - Health: {report.final_network_health:.2f}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Quick start failed: {e}", exc_info=True)
        return False


async def main():
    """Run all executor milestone tests."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Phase 2B Executor Validation Tests")
    logger.info("=" * 60)
    logger.info("")

    tests = [
        ("Milestone 1: Initialize 3-node network", test_milestone_1_initialize),
        ("Milestone 5: Run 10 epochs", test_milestone_5_run_10_epochs),
        ("Milestone 6: Generate report", test_milestone_6_generate_report),
        ("Quick Start Function", test_quick_start_function),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if await test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            logger.error(f"Test '{name}' crashed: {e}", exc_info=True)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
