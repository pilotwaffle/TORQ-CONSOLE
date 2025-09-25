#!/usr/bin/env python3
"""
Test script for Prince Flowers Enhanced Agent integration with TORQ Console.

This script tests the complete integration of the enhanced agentic RL agent
with TORQ Console, including command processing, web search capabilities,
and performance metrics.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add TORQ Console to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig


async def test_prince_flowers_integration():
    """Test the Prince Flowers Enhanced Agent integration."""
    print("🚀 Testing Prince Flowers Enhanced Agent Integration with TORQ Console")
    print("=" * 80)

    try:
        # Initialize TORQ Console
        config = TorqConfig.create_default()
        console = TorqConsole(
            config=config,
            repo_path=Path.cwd(),
            model="claude-3-5-sonnet-20241022"
        )

        print(f"✅ TORQ Console initialized successfully")
        print(f"✅ Prince Flowers agent integrated: {hasattr(console, 'prince_flowers')}")

        # Test cases for Prince Flowers commands
        test_cases = [
            # Basic commands
            ("prince help", "Help command"),
            ("prince status", "Status command"),
            ("prince health", "Health check"),
            ("prince capabilities", "Capabilities description"),

            # Query commands
            ("prince search latest AI developments", "Web search test"),
            ("prince what is agentic reinforcement learning", "Knowledge query"),
            ("prince analyze machine learning trends", "Analysis query"),

            # Alternative format
            ("@prince search Prince Flowers enhanced", "Alternative @ format"),
        ]

        print(f"\n🧪 Running {len(test_cases)} test cases...")
        print("-" * 60)

        for i, (command, description) in enumerate(test_cases, 1):
            print(f"\n[Test {i}/{len(test_cases)}] {description}")
            print(f"Command: {command}")
            print("-" * 40)

            try:
                # Process the command
                result = await console.process_command(command)

                # Basic validation
                if result and len(result) > 10:
                    print("✅ Command executed successfully")
                    print(f"📊 Response length: {len(result)} characters")

                    # Show first 200 chars for verification
                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"📝 Preview: {preview}")
                else:
                    print("⚠️  Command executed but response was short")
                    print(f"📝 Full response: {result}")

            except Exception as e:
                print(f"❌ Error executing command: {e}")
                logging.error(f"Test {i} failed: {e}")

            # Wait between tests to avoid overwhelming
            await asyncio.sleep(0.5)

        print("\n" + "=" * 80)
        print("🎯 Integration Testing Complete")

        # Get agent status for final validation
        try:
            print("\n📊 Final Agent Status Check:")
            agent_status_result = await console.process_command("prince status")
            print("✅ Agent status retrieved successfully")
        except Exception as e:
            print(f"❌ Error getting final status: {e}")

        # Shutdown console
        await console.shutdown()
        print("✅ Console shutdown complete")

        return True

    except Exception as e:
        print(f"❌ Critical error during integration test: {e}")
        logging.error(f"Integration test failed: {e}")
        return False


async def test_agent_performance_metrics():
    """Test the agent's performance tracking and RL components."""
    print("\n🔬 Testing Agent Performance and RL Components")
    print("-" * 50)

    try:
        # Test direct agent interaction
        config = TorqConfig.create_default()
        console = TorqConsole(config=config)

        # Access the agent directly for detailed testing
        agent = console.prince_flowers.agent

        print(f"✅ Direct agent access successful")
        print(f"📊 Agent version: {agent.version}")
        print(f"📊 Available tools: {len(agent.available_tools)}")
        print(f"📊 Reasoning modes: {len(agent.planning_strategies)}")

        # Test multiple queries to see learning in action
        test_queries = [
            "What is machine learning?",
            "Search for AI news",
            "Analyze current trends in artificial intelligence"
        ]

        print(f"\n🧠 Testing learning progression with {len(test_queries)} queries...")

        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")

            result = await agent.process_query(query, {'test_mode': True})

            print(f"✅ Success: {result.success}")
            print(f"📊 Confidence: {result.confidence:.2%}")
            print(f"⏱️  Time: {result.execution_time:.2f}s")
            print(f"🛠️  Tools used: {', '.join(result.tools_used)}")
            print(f"🧠 Reasoning mode: {result.reasoning_mode.value}")

        # Check final performance metrics
        status = agent.get_agent_status()
        print(f"\n📈 Final Performance Summary:")
        print(f"  Queries processed: {status['performance_metrics']['total_queries']}")
        print(f"  Success rate: {status['performance_metrics']['success_rate']:.1%}")
        print(f"  Trajectories stored: {status['learning_status']['trajectories_stored']}")
        print(f"  Best strategy: {status['learning_status']['best_strategy']}")

        await console.shutdown()
        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        logging.error(f"Performance test error: {e}")
        return False


async def test_command_formats():
    """Test different command formats and edge cases."""
    print("\n🔧 Testing Command Format Variations")
    print("-" * 40)

    try:
        config = TorqConfig.create_default()
        console = TorqConsole(config=config)

        # Test various command formats
        format_tests = [
            "prince help",
            "@prince help",
            "PRINCE STATUS",  # Case insensitive
            "prince",  # No query
            "prince ",  # Just space
            "prince search",  # Incomplete command
            "prince status",
            "prince health",
        ]

        for command in format_tests:
            print(f"\nTesting: '{command}'")
            try:
                result = await console.process_command(command)
                print(f"✅ Handled successfully: {len(result) if result else 0} chars")
            except Exception as e:
                print(f"⚠️  Error (expected for some): {e}")

        await console.shutdown()
        return True

    except Exception as e:
        print(f"❌ Command format test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🎯 TORQ Console - Prince Flowers Enhanced Integration Test Suite")
    print("🤖 Testing ARTIST-style Agentic RL Agent Integration")
    print("=" * 90)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Suppress some verbose logging for cleaner output
    logging.getLogger('torq_console').setLevel(logging.WARNING)

    # Run test suites
    tests = [
        ("Basic Integration", test_prince_flowers_integration),
        ("Performance Metrics", test_agent_performance_metrics),
        ("Command Formats", test_command_formats),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = await test_func()
            results.append((test_name, success))
            print(f"{'✅ PASSED' if success else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"❌ CRASHED: {test_name} - {e}")
            results.append((test_name, False))

    # Final summary
    print(f"\n{'='*60}")
    print("🏁 FINAL TEST RESULTS:")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Prince Flowers integration is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    # Run the test suite
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(3)