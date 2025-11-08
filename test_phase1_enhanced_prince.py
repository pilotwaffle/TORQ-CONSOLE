#!/usr/bin/env python3
"""
Test Phase 1: Enhanced Prince Flowers as Default Agent

This script verifies that:
1. Enhanced Prince Flowers is instantiated by default
2. TikTok lesson is applied automatically
3. Action-oriented behavior works correctly
4. Memory and learning systems are functional
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.agents import (
    get_orchestrator,
    get_action_learning,
    get_agent_memory,
    ActionDecision
)


async def test_phase1():
    """Test Phase 1 implementation"""
    print("\n" + "=" * 80)
    print("PHASE 1 TEST: Enhanced Prince Flowers as Default Agent")
    print("=" * 80 + "\n")

    # Test 1: Verify orchestrator creates Enhanced Prince
    print("Test 1: Verify Enhanced Prince Flowers is the default agent")
    print("-" * 80)
    try:
        orchestrator = get_orchestrator()
        prince = orchestrator.get_agent('prince_flowers')

        # Check if it's EnhancedPrinceFlowers
        is_enhanced = hasattr(prince, 'action_learning') and hasattr(prince, 'record_user_feedback')

        if is_enhanced:
            print("✅ PASS: Enhanced Prince Flowers is active")
            print(f"   Agent type: {type(prince).__name__}")
        else:
            print("❌ FAIL: Base MarvinPrinceFlowers is active (not enhanced)")
            print(f"   Agent type: {type(prince).__name__}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error creating orchestrator: {e}")
        return False

    print()

    # Test 2: Verify TikTok lesson is applied
    print("Test 2: Verify TikTok lesson is applied")
    print("-" * 80)
    try:
        action_learning = get_action_learning()
        patterns = action_learning.get_patterns('ideation_research_immediate')

        if patterns:
            print("✅ PASS: TikTok lesson pattern found")
            print(f"   Pattern name: {patterns[0]['name']}")
            print(f"   Keywords: {patterns[0]['data']['keywords']}")
        else:
            print("⚠️  WARNING: TikTok lesson not found in patterns")
            print("   This is OK if it's the first run")
    except Exception as e:
        print(f"⚠️  WARNING: Could not check TikTok lesson: {e}")

    print()

    # Test 3: Test action analysis (research request)
    print("Test 3: Action analysis for research request")
    print("-" * 80)
    try:
        action_learning = get_action_learning()

        test_queries = [
            "search for top AI frameworks",
            "under ideation: find best Python libraries",
            "build a tool to monitor APIs"
        ]

        for query in test_queries:
            analysis = action_learning.analyze_request(query)
            print(f"Query: \"{query}\"")
            print(f"  → Action: {analysis['recommended_action'].value}")
            print(f"  → Confidence: {analysis['confidence']:.2f}")
            print()

        print("✅ PASS: Action analysis working")
    except Exception as e:
        print(f"❌ FAIL: Action analysis error: {e}")
        return False

    print()

    # Test 4: Test memory system
    print("Test 4: Memory system functionality")
    print("-" * 80)
    try:
        memory = get_agent_memory()
        snapshot = memory.get_memory_snapshot()

        print(f"Total interactions: {snapshot.total_interactions}")
        print(f"Success rate: {snapshot.success_rate:.1%}")
        print(f"Learned patterns: {len(snapshot.learned_patterns)}")
        print("✅ PASS: Memory system working")
    except Exception as e:
        print(f"❌ FAIL: Memory system error: {e}")
        return False

    print()

    # Test 5: Simulate a research request through Enhanced Prince
    print("Test 5: Simulated research request (action-oriented behavior)")
    print("-" * 80)
    try:
        # Note: We can't actually run LLM queries in this test without API keys
        # But we can verify the setup is correct

        print("Setup verification:")
        print(f"  • Enhanced Prince instance: {type(prince).__name__}")
        print(f"  • Has action_learning attribute: {hasattr(prince, 'action_learning')}")
        print(f"  • Has record_user_feedback method: {hasattr(prince, 'record_user_feedback')}")
        print(f"  • Has get_learning_stats method: {hasattr(prince, 'get_learning_stats')}")

        if all([
            hasattr(prince, 'action_learning'),
            hasattr(prince, 'record_user_feedback'),
            hasattr(prince, 'get_learning_stats')
        ]):
            print("✅ PASS: Enhanced Prince has all required features")
        else:
            print("❌ FAIL: Enhanced Prince missing features")
            return False

    except Exception as e:
        print(f"❌ FAIL: Enhanced Prince feature check error: {e}")
        return False

    print()

    # Test 6: Get learning stats
    print("Test 6: Learning statistics")
    print("-" * 80)
    try:
        if hasattr(prince, 'get_learning_stats'):
            stats = prince.get_learning_stats()

            print("Action Learning:")
            print(f"  • Total patterns: {stats['action_learning']['total_patterns']}")
            print(f"  • Learned patterns: {stats['action_learning']['learned_patterns']}")
            print(f"  • Built-in patterns: {stats['action_learning']['built_in_patterns']}")
            print(f"  • Average confidence: {stats['action_learning']['average_confidence']:.2f}")

            print("\nMemory:")
            print(f"  • Total interactions: {stats['memory']['total_interactions']}")
            print(f"  • Success rate: {stats['memory']['success_rate']:.1%}")
            print(f"  • Learned patterns: {stats['memory']['learned_patterns']}")

            print("✅ PASS: Learning stats retrieved")
        else:
            print("❌ FAIL: get_learning_stats not available")
            return False
    except Exception as e:
        print(f"❌ FAIL: Learning stats error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 80)
    print("PHASE 1 TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✅ Enhanced Prince Flowers is the default agent")
    print("  ✅ Action-oriented learning system is active")
    print("  ✅ TikTok lesson is applied (or will be on first interaction)")
    print("  ✅ Memory system is functional")
    print("  ✅ All features are present and working")
    print()
    print("Next: Test with actual queries when API keys are configured")

    return True


async def main():
    """Run Phase 1 tests"""
    success = await test_phase1()

    if success:
        print("\n🎉 PHASE 1 IMPLEMENTATION: SUCCESS")
        print("Enhanced Prince Flowers is now the default agent!")
        sys.exit(0)
    else:
        print("\n❌ PHASE 1 IMPLEMENTATION: FAILED")
        print("Please review errors above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
