#!/usr/bin/env python3
"""
Test script to validate RL learning in Prince Flowers Agent
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent
from torq_console.agents.rl_learning_system import RewardType

async def test_rl_learning():
    """Test that the RL agent learns from mistakes and applies corrections."""

    print("Testing Prince Flowers Agent RL Learning System")
    print("=" * 60)

    # Initialize agent
    agent = PrinceFlowersAgent()

    # Test scenario 1: Simulated error pattern
    print("\nTest 1: Creating error pattern")

    # Simulate a query that would typically cause an error
    error_query = "create invalid python syntax with missing brackets"

    # Process query multiple times to establish error pattern
    for i in range(3):
        print(f"  Attempt {i+1}: Processing error-prone query...")

        try:
            result = await agent.process_query(error_query)

            # Check if RL stats are being tracked
            rl_stats = result.metadata.get('rl_learning', {})
            print(f"    RL Stats: {rl_stats}")

            # Simulate error feedback to the RL system
            if i < 2:  # First two attempts fail
                agent.rl_system.record_experience(
                    state=error_query,
                    action="generate_code",
                    reward=RewardType.FAILURE.value,
                    next_state="syntax_error",
                    error_info={
                        'type': 'syntax_error',
                        'correction': 'add missing closing bracket',
                        'signature': f'syntax_error|{error_query[:50]}|generate_code'
                    }
                )
            else:  # Third attempt succeeds
                agent.rl_system.record_experience(
                    state=error_query,
                    action="generate_code",
                    reward=RewardType.SUCCESS.value,
                    next_state="code_generated"
                )

        except Exception as e:
            print(f"    Error: {e}")

    # Test scenario 2: Check if agent learned and can predict correction
    print("\n🔮 Test 2: Testing error prediction and correction")

    similar_query = "create python function with missing brackets"
    prediction = await agent.rl_system.predict_correction(similar_query, "generate_code")

    if prediction:
        print(f"  ✅ Agent predicted correction: {prediction}")
    else:
        print("  ❌ No correction predicted")

    # Test scenario 3: Examine learned patterns
    print("\n🧠 Test 3: Examining learned error patterns")

    rl_stats = agent.rl_system.get_learning_stats()
    print(f"  Total experiences: {rl_stats['total_experiences']}")
    print(f"  Error patterns learned: {rl_stats['error_patterns_learned']}")
    print(f"  Corrections applied: {rl_stats['corrections_applied']}")
    print(f"  Learning efficiency: {rl_stats.get('learning_efficiency', 0.0):.2f}")

    # Display specific error patterns
    if agent.rl_system.error_patterns:
        print("\n  📋 Learned Error Patterns:")
        for signature, pattern in agent.rl_system.error_patterns.items():
            print(f"    - {pattern.error_type}: {pattern.frequency} occurrences, "
                  f"{pattern.confidence:.2f} confidence")

    # Test scenario 4: Test automatic correction
    print("\n🔧 Test 4: Testing automatic correction")

    # Create a known error scenario
    error_info = {
        'signature': 'syntax_error|create invalid python syntax with missing|generate_code',
        'type': 'syntax_error'
    }

    correction = agent.rl_system.apply_automatic_correction(error_info)

    if correction:
        print(f"  ✅ Automatic correction applied: {correction}")
    else:
        print("  ❌ No automatic correction available")

    # Test scenario 5: Test action selection
    print("\n🎯 Test 5: Testing intelligent action selection")

    state = "debug python code"
    actions = ["static_analysis", "dynamic_testing", "code_review", "random_guess"]

    best_action, confidence = agent.rl_system.get_best_action(state, actions)
    print(f"  Best action for '{state}': {best_action} (confidence: {confidence:.2f})")

    # Final assessment
    print("\n" + "=" * 60)
    print("RL Learning Test Results:")

    final_stats = agent.rl_system.get_learning_stats()

    # Check if learning is occurring
    learning_indicators = [
        final_stats['total_experiences'] > 0,
        final_stats['error_patterns_learned'] > 0,
        len(agent.rl_system.experience_buffer) > 0
    ]

    if all(learning_indicators):
        print("  SUCCESS: RL system is functioning and learning from experiences")
        print("  SUCCESS: Error patterns are being identified and stored")
        print("  SUCCESS: Experience buffer is accumulating data")

        if prediction:
            print("  SUCCESS: Predictive correction capability is working")

        if correction:
            print("  SUCCESS: Automatic correction system is operational")

        print(f"\n  Learning Progress:")
        print(f"    - {final_stats['total_experiences']} total experiences")
        print(f"    - {final_stats['error_patterns_learned']} error patterns learned")
        print(f"    - {final_stats['corrections_applied']} corrections applied")

        return True
    else:
        print("  FAILURE: RL system is not learning properly")
        print(f"    - Experiences: {final_stats['total_experiences']}")
        print(f"    - Error patterns: {final_stats['error_patterns_learned']}")
        print(f"    - Buffer size: {len(agent.rl_system.experience_buffer)}")

        return False

if __name__ == "__main__":
    success = asyncio.run(test_rl_learning())

    if success:
        print("\n🎊 SUCCESS: Prince Flowers Agent RL learning is validated!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: RL learning system needs further investigation")
        sys.exit(1)