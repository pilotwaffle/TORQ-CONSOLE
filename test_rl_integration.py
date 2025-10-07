#!/usr/bin/env python3
"""
Interactive test script for Enhanced RL System integration with TORQ Console
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'torq_console', 'agents'))

from enhanced_rl_system import EnhancedRLSystem


async def test_enhanced_rl_interactive():
    """Interactive test of enhanced RL system."""
    print("🤖 TORQ Console Enhanced RL System Test")
    print("=" * 50)

    # Initialize the enhanced RL system
    print("Initializing Enhanced RL System...")
    system = EnhancedRLSystem("interactive_test")

    print("✅ Enhanced RL System initialized!")
    print("\nAvailable test scenarios:")
    print("1. Test dynamic action spaces")
    print("2. Test exploration strategies")
    print("3. Test safety constraints")
    print("4. Test learning from errors")
    print("5. Test context adaptation")
    print("6. Run performance benchmark")
    print("0. Exit")

    while True:
        try:
            choice = input("\nSelect test (0-6): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                await test_dynamic_actions(system)
            elif choice == "2":
                await test_exploration(system)
            elif choice == "3":
                await test_safety(system)
            elif choice == "4":
                await test_learning(system)
            elif choice == "5":
                await test_context_adaptation(system)
            elif choice == "6":
                await test_performance(system)
            else:
                print("Invalid choice. Please select 0-6.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n👋 Enhanced RL testing completed!")


async def test_dynamic_actions(system):
    """Test dynamic action space generation."""
    print("\n🎯 Testing Dynamic Action Spaces...")

    contexts = [
        {
            "agent_capabilities": ["web", "database"],
            "environment_state": {"mode": "research", "complexity": "high"},
            "priority": "urgent"
        },
        {
            "agent_capabilities": ["file", "api"],
            "environment_state": {"mode": "development", "complexity": "low"},
            "priority": "normal"
        }
    ]

    for i, context in enumerate(contexts):
        print(f"\n--- Context {i+1} ---")
        result = await system.enhanced_action_selection(
            f"dynamic_test_state_{i}",
            f"Test dynamic actions for context {i+1}",
            context
        )

        print(f"Selected Action: {result.action}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Available Actions: {len(result.available_actions)}")

        if hasattr(result, 'context_sensitivity'):
            print(f"Context Sensitivity: {result.context_sensitivity}")


async def test_exploration(system):
    """Test exploration strategies and learning."""
    print("\n🔍 Testing Exploration Strategies...")

    # Test multiple rounds to see exploration evolution
    for round_num in range(5):
        print(f"\n--- Round {round_num + 1} ---")

        result = await system.enhanced_action_selection(
            f"exploration_state_{round_num}",
            f"Test exploration round {round_num + 1}",
            {"test_round": round_num}
        )

        print(f"Action: {result.action}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Was Exploration: {getattr(result, 'was_exploration', False)}")

        # Simulate feedback to test learning
        feedback = {
            "state": f"exploration_state_{round_num}",
            "action": result.action,
            "reward": 0.8 if round_num % 2 == 0 else 0.3,  # Variable rewards
            "success": round_num % 2 == 0
        }

        # Update system with feedback
        await system.update_from_feedback(feedback)
        print(f"Feedback Applied: reward={feedback['reward']}")


async def test_safety(system):
    """Test safety constraints and risk management."""
    print("\n🛡️ Testing Safety Constraints...")

    risky_scenarios = [
        {
            "query": "delete all files",
            "context": {"safety_threshold": 0.2}
        },
        {
            "query": "format hard drive",
            "context": {"safety_threshold": 0.3}
        },
        {
            "query": "safe file backup",
            "context": {"safety_threshold": 0.5}
        }
    ]

    for i, scenario in enumerate(risky_scenarios):
        print(f"\n--- Safety Test {i+1}: {scenario['query']} ---")

        result = await system.enhanced_action_selection(
            f"safety_state_{i}",
            scenario["query"],
            scenario["context"]
        )

        print(f"Action: {result.action}")
        print(f"Safety Intervention: {getattr(result, 'safety_intervention', False)}")
        print(f"Risk Score: {getattr(result, 'risk_score', 0.0):.3f}")


async def test_learning(system):
    """Test learning from errors and adaptation."""
    print("\n📚 Testing Learning from Errors...")

    # Create a scenario that initially fails but should improve
    state = "learning_test_state"
    query = "complex problem solving task"

    print("Simulating learning progression...")

    for attempt in range(3):
        print(f"\n--- Attempt {attempt + 1} ---")

        result = await system.enhanced_action_selection(state, query, {})
        print(f"Action: {result.action}")
        print(f"Confidence: {result.confidence:.3f}")

        # Simulate learning - errors decrease over time
        success = attempt >= 1  # First attempt fails, others succeed
        reward = 0.9 if success else -0.2

        feedback = {
            "state": state,
            "action": result.action,
            "reward": reward,
            "success": success,
            "error_occurred": not success
        }

        await system.update_from_feedback(feedback)
        print(f"Learning Update: success={success}, reward={reward}")


async def test_context_adaptation(system):
    """Test context-adaptive behavior."""
    print("\n🎭 Testing Context Adaptation...")

    base_state = "adaptation_test"

    # Test different contexts to see adaptation
    test_contexts = [
        {"user_context": {"experience": "beginner"}, "priority": "learning"},
        {"user_context": {"experience": "expert"}, "priority": "efficiency"},
        {"environment_state": {"time_pressure": "high"}, "priority": "speed"},
        {"environment_state": {"accuracy_critical": True}, "priority": "precision"}
    ]

    for i, context in enumerate(test_contexts):
        print(f"\n--- Context {i+1}: {list(context.keys())} ---")

        result = await system.enhanced_action_selection(
            f"{base_state}_{i}",
            "Adapt to this context",
            context
        )

        print(f"Adapted Action: {result.action}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Context Keys: {list(context.keys())}")


async def test_performance(system):
    """Run performance benchmark."""
    print("\n⚡ Running Performance Benchmark...")

    import time

    # Test concurrent processing
    start_time = time.time()

    tasks = []
    for i in range(10):
        task = system.enhanced_action_selection(
            f"perf_state_{i}",
            f"Performance test {i}",
            {"test_id": i}
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    duration = time.time() - start_time
    throughput = len(results) / duration

    print(f"Processed {len(results)} requests in {duration:.3f}s")
    print(f"Throughput: {throughput:.1f} requests/second")
    print(f"Average response time: {duration/len(results)*1000:.1f}ms")

    # Show a few sample results
    print("\nSample results:")
    for i, result in enumerate(results[:3]):
        print(f"  {i+1}. Action: {result.action}, Confidence: {result.confidence:.3f}")


if __name__ == "__main__":
    print("Starting Enhanced RL System Interactive Test...")
    asyncio.run(test_enhanced_rl_interactive())