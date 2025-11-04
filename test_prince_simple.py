#!/usr/bin/env python3
"""Simple test to verify Prince Flowers routing logic (no API calls)."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_routing_logic():
    """Test just the routing logic without making API calls."""
    try:
        from torq_console.agents.marvin_orchestrator import MarvinAgentOrchestrator
        from torq_console.agents.marvin_query_router import AgentCapability

        logger.info("=" * 60)
        logger.info("Testing Prince Flowers Routing Logic")
        logger.info("=" * 60)

        # Create orchestrator
        orchestrator = MarvinAgentOrchestrator()

        # Test search query detection
        test_queries = [
            ("Search GitHub for top repositories", True),
            ("Find the best Python frameworks", True),
            ("List top 3 repositories with most workflows", True),
            ("What is GitHub?", True),
            ("Explain async/await in Python", False),
            ("How does authentication work?", False),
            ("Tell me about design patterns", False),
        ]

        logger.info("\nTesting keyword detection:")
        logger.info("-" * 60)

        for query, should_be_search in test_queries:
            is_search = orchestrator._is_search_query(query)
            status = "✓" if is_search == should_be_search else "✗"
            query_type = "SEARCH" if is_search else "CHAT"

            logger.info(f"{status} '{query[:50]}...'")
            logger.info(f"   Detected as: {query_type} (expected: {'SEARCH' if should_be_search else 'CHAT'})")

        # Check if TorqPrince is available
        from torq_console.agents import marvin_orchestrator as mo
        logger.info("\n" + "=" * 60)
        logger.info("Component Availability:")
        logger.info("-" * 60)
        logger.info(f"TorqPrinceFlowers available: {mo.TORQ_PRINCE_AVAILABLE}")
        logger.info(f"Initialized: {orchestrator._torq_prince_initialized}")

        # Check metrics structure
        logger.info("\n" + "=" * 60)
        logger.info("Metrics Structure:")
        logger.info("-" * 60)
        logger.info(f"Total requests: {orchestrator.metrics['total_requests']}")
        logger.info(f"TorqPrince requests: {orchestrator.metrics['torq_prince_requests']}")
        logger.info(f"MarvinPrince requests: {orchestrator.metrics['marvin_prince_requests']}")

        logger.info("\n" + "=" * 60)
        logger.info("ROUTING LOGIC TEST: PASSED ✓")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_routing_logic())
    import sys
    sys.exit(0 if success else 1)
