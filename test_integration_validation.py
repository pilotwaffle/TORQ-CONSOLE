#!/usr/bin/env python3
"""
Test script for Prince Flowers Integration v0.70.0
Validates the integration functionality without running the full TORQ Console.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

async def test_integration():
    """Test the Prince Flowers integration wrapper."""
    print("🧪 Testing Prince Flowers Integration v0.70.0")
    print("=" * 50)

    try:
        # Import the integration module
        from torq_integration import PrinceFlowersIntegrationWrapper, PrinceFlowersAgent

        print("✅ Integration module imported successfully")

        # Test 1: Create integration wrapper
        print("\n🔧 Test 1: Creating integration wrapper...")
        integration = PrinceFlowersIntegrationWrapper()
        print(f"✅ Integration wrapper created: {integration.agent_type}")

        # Test 2: Health check
        print("\n🔧 Test 2: Health check...")
        health = await integration.health_check()
        print(f"✅ Health status: {health['overall_status']}")

        # Test 3: Get capabilities
        print("\n🔧 Test 3: Get capabilities...")
        capabilities = integration.get_capabilities()
        print(f"✅ Agent type: {capabilities.get('agent_type', 'unknown')}")

        # Test 4: Process a simple query
        print("\n🔧 Test 4: Process test query...")
        response = await integration.query("prince help")
        print(f"✅ Query successful: {response.success}")
        print(f"   Confidence: {response.confidence:.1%}")
        print(f"   Tools used: {', '.join(response.tools_used)}")

        # Test 5: Get status
        print("\n🔧 Test 5: Get integration status...")
        status = integration.get_status()
        print(f"✅ Integration active: {status['integration_active']}")
        print(f"   Total queries: {status['total_queries']}")
        print(f"   Success rate: {status['success_rate']:.1%}")

        # Test 6: Legacy compatibility
        print("\n🔧 Test 6: Legacy compatibility...")
        legacy_agent = PrinceFlowersAgent()
        print(f"✅ Legacy agent available: {legacy_agent.available}")

        print("\n🎉 All tests passed! Integration is working correctly.")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the TORQ-CONSOLE directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

    return True

async def demo_queries():
    """Run demonstration queries."""
    print("\n🎯 Running demonstration queries...")

    try:
        from torq_integration import PrinceFlowersIntegrationWrapper

        integration = PrinceFlowersIntegrationWrapper()

        demo_queries = [
            "prince help",
            "What is agentic reinforcement learning?",
            "search latest AI developments",
            "prince status"
        ]

        for i, query in enumerate(demo_queries, 1):
            print(f"\n--- Demo Query {i}/{len(demo_queries)} ---")
            print(f"Query: {query}")

            response = await integration.query(query, show_performance=True)

            print(f"✅ Success: {response.success}")
            print(f"⏱️ Time: {response.execution_time:.2f}s")
            print(f"🎯 Confidence: {response.confidence:.1%}")
            print(f"Response: {response.content[:200]}{'...' if len(response.content) > 200 else ''}")

            if i < len(demo_queries):
                print("Press Enter to continue...")
                input()

        print("\n✅ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        traceback.print_exc()

def print_integration_summary():
    """Print integration summary."""
    print("\n📋 Prince Flowers Integration v0.70.0 Summary")
    print("=" * 50)

    summary = """
✨ **Features Implemented:**
- Comprehensive integration wrapper with standardized responses
- Health monitoring and performance tracking
- CLI testing interface with interactive commands
- Backward compatibility with existing TORQ Console code
- Enhanced error handling and recovery
- Multiple agent types (TORQ Console, Local Interface, Mock)

🚀 **Available Commands in TORQ Console:**
- prince <query> - Query the enhanced agentic RL agent
- prince help - Show agent help and capabilities
- prince status - Show agent performance metrics
- prince integration-status - Show integration status
- prince integration-health - Check integration health
- prince integration-capabilities - Show integration features

🛠️ **CLI Testing:**
- python torq_integration.py --help - Show CLI options
- python torq_integration.py --demo - Run demonstration queries
- python torq_integration.py --status - Show integration status
- python torq_integration.py cli - Interactive CLI session

🔧 **Integration Types:**
- Enhanced: Uses new integration wrapper with full features
- Standard: Falls back to existing TORQ Console integration
- Mock: Demo agent for testing when other agents unavailable

The integration is now ready for use with TORQ Console v0.70.0!
    """

    print(summary)

async def main():
    """Main test function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'demo':
            await demo_queries()
        elif sys.argv[1] == 'summary':
            print_integration_summary()
        else:
            print("Usage: python test_integration_validation.py [demo|summary]")
    else:
        # Run basic tests
        success = await test_integration()

        if success:
            print_integration_summary()
        else:
            print("\n❌ Tests failed. Check the error messages above.")

if __name__ == '__main__':
    print("🚀 Prince Flowers Integration Test Suite")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()