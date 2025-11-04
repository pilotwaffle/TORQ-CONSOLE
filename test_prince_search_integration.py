#!/usr/bin/env python3
"""
Test script for Prince Flowers search integration.

This script tests the enhanced orchestrator's ability to route search queries
to TorqPrinceFlowers (with SearchMaster tools) vs conversational queries
to MarvinPrinceFlowers.
"""

import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_search_routing():
    """Test that search queries are routed to TorqPrinceFlowers."""
    try:
        from torq_console.agents.marvin_orchestrator import get_orchestrator

        logger.info("=" * 80)
        logger.info("TESTING PRINCE FLOWERS SEARCH INTEGRATION")
        logger.info("=" * 80)

        # Initialize orchestrator
        orchestrator = get_orchestrator()

        # Test 1: Search query (should route to TorqPrinceFlowers)
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Search Query - 'Search GitHub for repositories with most workflows'")
        logger.info("=" * 80)

        search_query = "Search GitHub and list top 3 repository links with the most workflows"
        result1 = await orchestrator.process_query(search_query)

        logger.info(f"\nAgent Used: {result1.metadata.get('agent_used', 'unknown')}")
        logger.info(f"Used Tools: {result1.metadata.get('used_tools', False)}")
        logger.info(f"Success: {result1.success}")
        logger.info(f"\nResponse Preview:\n{str(result1.primary_response)[:500]}...")

        # Test 2: Conversational query (should route to MarvinPrinceFlowers)
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Conversational Query - 'Explain async/await in Python'")
        logger.info("=" * 80)

        conv_query = "Can you explain how async/await works in Python?"
        result2 = await orchestrator.process_query(conv_query)

        logger.info(f"\nAgent Used: {result2.metadata.get('agent_used', 'unknown')}")
        logger.info(f"Used Tools: {result2.metadata.get('used_tools', False)}")
        logger.info(f"Success: {result2.success}")
        logger.info(f"\nResponse Preview:\n{str(result2.primary_response)[:500]}...")

        # Test 3: Another search query
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Search Query - 'Find latest Python frameworks'")
        logger.info("=" * 80)

        search_query2 = "Find the top 5 latest Python web frameworks with their GitHub stars"
        result3 = await orchestrator.process_query(search_query2)

        logger.info(f"\nAgent Used: {result3.metadata.get('agent_used', 'unknown')}")
        logger.info(f"Used Tools: {result3.metadata.get('used_tools', False)}")
        logger.info(f"Success: {result3.success}")
        logger.info(f"\nResponse Preview:\n{str(result3.primary_response)[:500]}...")

        # Display metrics
        logger.info("\n" + "=" * 80)
        logger.info("ORCHESTRATOR METRICS")
        logger.info("=" * 80)

        metrics = orchestrator.get_comprehensive_metrics()
        logger.info(f"\nTotal Requests: {metrics['orchestrator']['total_requests']}")
        logger.info(f"TorqPrince Requests: {metrics['orchestrator']['torq_prince_requests']}")
        logger.info(f"MarvinPrince Requests: {metrics['orchestrator']['marvin_prince_requests']}")
        logger.info(f"Success Rate: {metrics['orchestrator']['success_rate']:.2%}")

        # Validation
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 80)

        # Check if search queries used TorqPrince
        search_used_torq = (
            'torq_prince_flowers' in result1.metadata.get('agent_used', '') or
            result1.metadata.get('used_tools', False)
        )

        conv_used_marvin = 'marvin_prince_flowers' in result2.metadata.get('agent_used', '')

        if search_used_torq:
            logger.info("✓ PASS: Search queries routed to TorqPrinceFlowers (with tools)")
        else:
            logger.warning("✗ FAIL: Search queries not routed to TorqPrinceFlowers")

        if conv_used_marvin:
            logger.info("✓ PASS: Conversational queries routed to MarvinPrinceFlowers")
        else:
            logger.warning("✗ FAIL: Conversational queries not routed correctly")

        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETE")
        logger.info("=" * 80)

        return search_used_torq and conv_used_marvin

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


async def test_direct_search():
    """Test direct search with TorqPrinceFlowers."""
    try:
        from torq_console.agents.torq_prince_flowers import TorqPrinceFlowers
        from torq_console.llm.providers import create_anthropic_provider, create_openai_provider

        logger.info("\n" + "=" * 80)
        logger.info("DIRECT TORQ PRINCE FLOWERS TEST")
        logger.info("=" * 80)

        # Initialize TorqPrinceFlowers directly
        llm_provider = None
        try:
            llm_provider = create_anthropic_provider()
            logger.info("Using Anthropic provider")
        except Exception:
            try:
                llm_provider = create_openai_provider()
                logger.info("Using OpenAI provider")
            except Exception as e:
                logger.error(f"Could not create LLM provider: {e}")
                return False

        if not llm_provider:
            logger.error("No LLM provider available")
            return False

        prince = TorqPrinceFlowers(llm_provider=llm_provider)

        # Test search
        query = "Search GitHub for top 3 repositories with most workflows"
        logger.info(f"\nQuery: {query}")

        response = await prince.process_query(query)

        logger.info(f"\nResponse:\n{response}")

        return True

    except Exception as e:
        logger.error(f"Direct test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("Starting Prince Flowers Search Integration Tests\n")

    # Check environment
    has_anthropic = os.getenv('ANTHROPIC_API_KEY') is not None
    has_openai = os.getenv('OPENAI_API_KEY') is not None

    if not (has_anthropic or has_openai):
        logger.warning("No API keys found in environment!")
        logger.warning("Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run tests")
        return False

    # Run tests
    test1_passed = await test_search_routing()

    # Uncomment to test direct TorqPrinceFlowers
    # test2_passed = await test_direct_search()

    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 80)

    return test1_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
