#!/usr/bin/env python3
"""
Simple test of Enhanced RL System
"""
import sys
sys.path.append('torq_console/agents')
sys.path.append('torq_console/agents/rl_modules')

import asyncio
import time

# Import the modules directly
from torq_console.agents.rl_learning_system import ARTISTRLSystem, Experience, RewardType
from torq_console.agents.rl_modules.modular_agent import create_production_agent, ModularRLAgent
from torq_console.agents.rl_modules.dynamic_actions import DynamicActionSpaceModule
from torq_console.agents.rl_modules.async_training import AsyncTrainingSystem


async def simple_test():
    print("🚀 Enhanced RL System Quick Test")
    print("=" * 40)

    # Test 1: Modular Agent
    print("\n1. Testing Modular Agent...")
    agent = create_production_agent("test_agent")
    result = await agent.select_action(
        "test_state",
        ["action_a", "action_b", "action_c"]
    )
    print(f"✅ Selected action: {result.get('action')}")
    print(f"   Confidence: {result.get('confidence', 0):.3f}")

    # Test 2: Dynamic Actions
    print("\n2. Testing Dynamic Actions...")
    config = {
        'base_actions': ['search', 'analyze', 'create'],
        'conditional_actions': {
            'capability_web': ['scrape', 'fetch'],
            'env_mode_research': ['deep_search', 'citations']
        }
    }

    dynamic_module = DynamicActionSpaceModule(config)
    context = {
        'agent_capabilities': ['web'],
        'environment_state': {'mode': 'research'}
    }

    action_space = await dynamic_module.process("research_state", context)
    print(f"✅ Available actions: {action_space.get('available_actions', [])}")
    print(f"   Space size: {action_space.get('space_size', 0)}")

    # Test 3: Async Training
    print("\n3. Testing Async Training...")
    async_config = {
        'rollout_workers': 2,
        'training_workers': 1,
        'batch_size': 5
    }

    async_system = AsyncTrainingSystem(async_config)
    await async_system.start()

    # Add some rollout tasks
    for i in range(3):
        await async_system.add_rollout_task({
            'state': f'async_state_{i}',
            'action': f'async_action_{i}',
            'reward': 0.8
        })

    # Wait a moment then stop
    await asyncio.sleep(1)
    await async_system.stop()

    stats = async_system.get_performance_stats()
    print(f"✅ Processed tasks: {stats.get('total_rollouts', 0)}")
    print(f"   Training batches: {stats.get('training_batches', 0)}")

    # Test 4: ARTIST RL System
    print("\n4. Testing ARTIST RL Learning...")
    artist_system = ARTISTRLSystem("test_artist")

    # Add some experiences
    experience1 = Experience(
        state="learning_test",
        action="learn_action",
        reward=0.8,
        next_state="success_state",
        reward_type=RewardType.SUCCESS
    )

    artist_system.add_experience(experience1)

    # Test prediction
    predicted_action = await artist_system.predict_best_action(
        "learning_test",
        ["learn_action", "other_action"]
    )

    print(f"✅ ARTIST predicted: {predicted_action}")
    print(f"   Experience count: {len(artist_system.experiences)}")

    print("\n🎉 All tests completed successfully!")
    print("\nTo test in TORQ Console:")
    print("1. Open http://127.0.0.1:8899 (or 8888, 8890, 8891, etc.)")
    print("2. Try complex queries that require learning")
    print("3. Notice improved responses over time")
    print("4. Test error scenarios to see recovery")


if __name__ == "__main__":
    asyncio.run(simple_test())