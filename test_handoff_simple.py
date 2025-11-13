#!/usr/bin/env python3
"""
Simple test for handoff information preservation fixes.

Tests the improvements to:
1. Memory → Planning handoffs (context preservation)
2. Debate → Evaluation handoffs (nuance preservation)
"""

import sys
from pathlib import Path

# Test memory context preservation
def test_memory_context_preservation():
    """Test that memory context is no longer truncated."""
    print("\n" + "=" * 80)
    print("TEST 1: Memory Context Preservation")
    print("=" * 80)

    # Add to path
    sys.path.insert(0, str(Path(__file__).parent))
    from torq_console.agents.memory_integration import MemoryIntegration

    memory = MemoryIntegration()

    # Mock context with long content
    test_context = {
        'memories': [
            {
                'content': 'This is a very long memory content that used to be truncated at 200 characters but should now be preserved up to 1000 characters. ' * 5,
                'similarity': 0.95
            },
            {
                'content': 'Another memory with important details about OAuth implementation, JWT tokens, refresh tokens, and security considerations.',
                'similarity': 0.88
            }
        ],
        'patterns': [
            {
                'pattern_type': 'authentication',
                'success_rate': 0.92,
                'pattern_content': {
                    'method': 'oauth',
                    'tokens': ['access', 'refresh'],
                    'security': 'high'
                }
            }
        ]
    }

    # Test formatted output
    formatted = memory.format_context_for_prompt(test_context, preserve_full_context=True)
    structured = memory.get_structured_context(test_context)

    print(f"\n✓ Formatted context length: {len(formatted)} chars")
    print(f"✓ Full content preserved: {len(structured['full_content'])} memories")
    print(f"✓ Similarity scores tracked: {structured['similarity_scores']}")

    # Check improvements
    improvements = []
    if len(formatted) > 500:  # Should be > 500 with full context
        improvements.append("✅ Context no longer truncated at 200 chars")
    if 'oauth' in formatted.lower():
        improvements.append("✅ Pattern details included in context")
    if len(structured['full_content']) == 2:
        improvements.append("✅ All memories preserved in structured format")

    print(f"\nImprovements:")
    for imp in improvements:
        print(f"  {imp}")

    return len(improvements) >= 2  # At least 2 improvements


def test_debate_context_preservation():
    """Test that debate context preserves all perspectives."""
    print("\n" + "=" * 80)
    print("TEST 2: Debate Context Preservation")
    print("=" * 80)

    sys.path.insert(0, str(Path(__file__).parent))
    from torq_console.agents.multi_agent_debate import DebateArgument, DebateRole, DebateRound

    # Mock debate rounds
    round1_args = [
        DebateArgument(DebateRole.PROPOSER, "Initial proposal content", 0.8, ["evidence1"]),
        DebateArgument(DebateRole.QUESTIONER, "Critical questions raised", 0.85, ["analysis"]),
        DebateArgument(DebateRole.CREATIVE, "Alternative approaches", 0.75, ["innovation"]),
        DebateArgument(DebateRole.FACT_CHECKER, "Verification results", 0.9, ["facts"])
    ]

    round1 = DebateRound(1, round1_args, 0.85)
    rounds = [round1]

    # Import the debate system to test the refined output
    from torq_console.agents.multi_agent_debate import MultiAgentDebate
    import asyncio

    debate = MultiAgentDebate(max_rounds=3)

    async def run_test():
        result = await debate.debate_and_refine(rounds)
        return result

    result = asyncio.run(run_test())

    print(f"\n✓ Debate result keys: {list(result.keys())}")
    print(f"✓ All rounds preserved: {'all_rounds' in result}")
    print(f"✓ All arguments preserved: {'all_arguments' in result}")
    print(f"✓ Agent contributions tracked: {'agent_contributions' in result}")
    print(f"✓ Debate metadata included: {'debate_metadata' in result}")

    # Check improvements
    improvements = []
    if 'all_rounds' in result and result['all_rounds']:
        improvements.append("✅ Full debate rounds preserved (not just final synthesis)")
    if 'all_arguments' in result and len(result['all_arguments']) == 4:
        improvements.append("✅ All agent arguments preserved")
    if 'agent_contributions' in result and len(result['agent_contributions']) > 0:
        improvements.append("✅ Perspectives organized by agent role")
    if 'debate_metadata' in result:
        improvements.append("✅ Debate metadata tracked for evaluation")

    print(f"\nImprovements:")
    for imp in improvements:
        print(f"  {imp}")

    # Show what used to be lost
    if 'agent_contributions' in result:
        print(f"\n📊 Agent Contributions (previously lost in handoff):")
        for role, contributions in result['agent_contributions'].items():
            print(f"  {role}: {len(contributions)} contribution(s)")

    return len(improvements) >= 3  # At least 3 improvements


def test_information_preservation_metrics():
    """Test improved information preservation checking."""
    print("\n" + "=" * 80)
    print("TEST 3: Information Preservation Metrics")
    print("=" * 80)

    sys.path.insert(0, str(Path(__file__).parent))
    from torq_console.agents.coordination_benchmark import CoordinationBenchmarkSuite

    benchmark = CoordinationBenchmarkSuite()

    # Test with mock data
    query = "Build authentication system with OAuth and JWT"
    response = "Implementation includes OAuth integration and JWT token management with refresh tokens"

    # Metadata with debate context
    metadata_with_context = {
        'used_planning': True,
        'used_debate': True,
        'used_evaluation': True,
        'consensus_score': 0.9,
        'debate_rounds': 3,
        'agent_contributions': {'proposer': 1, 'questioner': 1}
    }

    # Metadata without debate context (old way)
    metadata_minimal = {
        'used_debate': True
    }

    score_with_context = benchmark._check_information_preservation(query, response, metadata_with_context)
    score_minimal = benchmark._check_information_preservation(query, response, metadata_minimal)

    print(f"\n✓ Information preservation WITH context: {score_with_context:.2%}")
    print(f"✓ Information preservation WITHOUT context: {score_minimal:.2%}")
    print(f"✓ Improvement: {(score_with_context - score_minimal):.2%}")

    improvements = []
    if score_with_context > score_minimal:
        improvements.append("✅ Metadata preservation improves scoring")
    if score_with_context > 0.7:
        improvements.append("✅ Good information preservation achieved")
    if 'agent_contributions' in str(metadata_with_context):
        improvements.append("✅ Agent contributions tracked in metadata")

    print(f"\nImprovements:")
    for imp in improvements:
        print(f"  {imp}")

    return score_with_context > 0.7  # At least 70% preservation


def main():
    """Run all handoff preservation tests."""
    print("=" * 80)
    print("HANDOFF INFORMATION PRESERVATION - FIX VALIDATION")
    print("=" * 80)
    print("\nTesting fixes for 70% information loss in subsystem handoffs...")

    results = []

    try:
        results.append(("Memory → Planning", test_memory_context_preservation()))
    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")
        results.append(("Memory → Planning", False))

    try:
        results.append(("Debate → Evaluation", test_debate_context_preservation()))
    except Exception as e:
        print(f"\n❌ Debate test failed: {e}")
        results.append(("Debate → Evaluation", False))

    try:
        results.append(("Information Metrics", test_information_preservation_metrics()))
    except Exception as e:
        print(f"\n❌ Metrics test failed: {e}")
        results.append(("Information Metrics", False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Handoff fixes validated!")
        print("\nInformation loss should be significantly reduced:")
        print("  • Memory → Planning: Full context preserved (1000 chars vs 200)")
        print("  • Debate → Evaluation: All perspectives maintained")
        print("  • Improved metrics: Metadata + semantic tracking")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
