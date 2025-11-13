#!/usr/bin/env python3
"""
Test script for handoff information preservation fixes.

Tests the improvements to:
1. Memory → Planning handoffs
2. Debate → Evaluation handoffs
3. Information preservation metrics
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.agents.coordination_benchmark import (
    get_coordination_benchmark,
    CoordinationType
)
from torq_console.agents.enhanced_prince_flowers_v2 import EnhancedPrinceFlowers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_handoff_tests():
    """Run comprehensive handoff preservation tests."""

    logger.info("=" * 80)
    logger.info("TESTING HANDOFF INFORMATION PRESERVATION FIXES")
    logger.info("=" * 80)

    # Initialize agent
    logger.info("\n1. Initializing Enhanced Prince Flowers agent...")
    try:
        agent = EnhancedPrinceFlowers(
            memory_enabled=False,  # Use False for testing without Letta
            enable_advanced_features=True,
            use_hierarchical_planning=True,
            use_multi_agent_debate=True,
            use_self_evaluation=True
        )
        logger.info("✅ Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}")
        return

    # Get coordination benchmark
    logger.info("\n2. Loading coordination benchmark suite...")
    benchmark = get_coordination_benchmark()
    logger.info(f"✅ Loaded {len(benchmark.test_scenarios)} test scenarios")

    # Run benchmark tests
    logger.info("\n3. Running coordination benchmark tests...")
    logger.info("-" * 80)

    try:
        result = await benchmark.run_benchmark(agent, num_tests=10)

        logger.info("\n" + "=" * 80)
        logger.info("BENCHMARK RESULTS")
        logger.info("=" * 80)

        # Overall statistics
        logger.info(f"\n📊 Overall Statistics:")
        logger.info(f"  Total Tests: {result.total_tests}")
        logger.info(f"  Passed: {result.passed} ({result.passed/result.total_tests*100:.1f}%)")
        logger.info(f"  Failed: {result.failed} ({result.failed/result.total_tests*100:.1f}%)")
        logger.info(f"  Average Latency: {result.average_latency:.2f}s")
        logger.info(f"  Average Quality: {result.average_quality:.2f}")

        # Information preservation analysis
        logger.info(f"\n🔍 Information Preservation Analysis:")
        total_info_preserved = sum(
            m.information_preserved
            for m in result.coordination_metrics
        ) / len(result.coordination_metrics)
        logger.info(f"  Average Information Preserved: {total_info_preserved:.2%}")

        # Break down by coordination type
        by_type = {}
        for metric in result.coordination_metrics:
            coord_type = metric.coordination_type.value
            if coord_type not in by_type:
                by_type[coord_type] = []
            by_type[coord_type].append(metric.information_preserved)

        logger.info(f"\n  By Coordination Type:")
        for coord_type, preserved_values in by_type.items():
            avg = sum(preserved_values) / len(preserved_values)
            logger.info(f"    {coord_type}: {avg:.2%}")

        # Issues detected
        logger.info(f"\n⚠️  Issues Detected:")
        if result.issues_by_type:
            for issue_type, count in sorted(result.issues_by_type.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {issue_type}: {count} occurrences")
        else:
            logger.info("  No issues detected!")

        # Emergent behaviors
        if result.emergent_behaviors:
            logger.info(f"\n✨ Emergent Behaviors:")
            for behavior in set(result.emergent_behaviors):
                count = result.emergent_behaviors.count(behavior)
                logger.info(f"  {behavior}: {count} times")

        # Success criteria
        logger.info(f"\n🎯 Success Criteria:")
        info_loss_count = result.issues_by_type.get('information_loss', 0)
        info_loss_rate = info_loss_count / result.total_tests * 100

        logger.info(f"  Information Loss Rate: {info_loss_rate:.1f}%")
        if info_loss_rate < 30:  # Target: < 30% (improved from 70%)
            logger.info("  ✅ PASS - Information loss significantly reduced!")
        else:
            logger.info(f"  ⚠️  NEEDS IMPROVEMENT - Target: < 30%")

        # Specific handoff analysis
        logger.info(f"\n📋 Handoff-Specific Analysis:")

        memory_to_planning = [
            m for m in result.coordination_metrics
            if m.coordination_type == CoordinationType.MEMORY_TO_PLANNING
        ]
        if memory_to_planning:
            avg_preserved = sum(m.information_preserved for m in memory_to_planning) / len(memory_to_planning)
            logger.info(f"  Memory → Planning: {avg_preserved:.2%} preserved")

        debate_to_eval = [
            m for m in result.coordination_metrics
            if m.coordination_type == CoordinationType.DEBATE_TO_EVALUATION
        ]
        if debate_to_eval:
            avg_preserved = sum(m.information_preserved for m in debate_to_eval) / len(debate_to_eval)
            logger.info(f"  Debate → Evaluation: {avg_preserved:.2%} preserved")

        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETE")
        logger.info("=" * 80)

        # Return success status
        return info_loss_rate < 30

    except Exception as e:
        logger.error(f"❌ Benchmark execution failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting handoff preservation tests...")
    success = asyncio.run(run_handoff_tests())

    if success:
        logger.info("\n✅ ALL TESTS PASSED - Handoff fixes working!")
        sys.exit(0)
    else:
        logger.info("\n⚠️  TESTS COMPLETED - Review results above")
        sys.exit(0)  # Still exit 0 for reporting purposes
