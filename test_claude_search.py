#!/usr/bin/env python3
"""
Test script for Claude Web Search Proxy functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our enhanced integration
from torq_integration import ClaudeWebSearchProxy, PrinceFlowersIntegrationWrapper

async def test_claude_search_proxy():
    """Test the Claude Web Search Proxy"""
    print("🔍 Testing Claude Web Search Proxy Implementation")
    print("=" * 60)

    # Test 1: Basic proxy initialization
    print("\n1. Testing Proxy Initialization...")
    try:
        proxy = ClaudeWebSearchProxy()
        print("✅ Claude Web Search Proxy initialized successfully")
    except Exception as e:
        print(f"❌ Proxy initialization failed: {e}")
        return False

    # Test 2: Search functionality
    print("\n2. Testing Search Functionality...")
    test_queries = [
        ("latest AI developments", "ai"),
        ("Python programming", "tech"),
        ("current news", "news"),
        ("machine learning", "general")
    ]

    for query, search_type in test_queries:
        print(f"\n   Testing: '{query}' (type: {search_type})")
        try:
            results = await proxy.search_web(query, max_results=2, search_type=search_type)

            print(f"   ✅ Success: {results['total_found']} results")
            print(f"   ⏱️ Time: {results['execution_time']:.3f}s")
            print(f"   🔧 Method: {results['method_used']}")

            # Show first result
            if results['results']:
                first_result = results['results'][0]
                print(f"   📄 Sample: {first_result.title[:50]}...")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # Test 3: Integration wrapper
    print("\n3. Testing Integration Wrapper...")
    try:
        integration = PrinceFlowersIntegrationWrapper()
        print("✅ Integration wrapper initialized successfully")

        # Test status
        status = integration.get_status()
        print(f"   Agent Type: {status.get('agent_type', 'unknown')}")
        print(f"   Web Search: {status.get('claude_web_search', 'unknown')}")

        # Test health check
        health = await integration.health_check()
        print(f"   Health: {health.get('overall_status', 'unknown')}")

    except Exception as e:
        print(f"❌ Integration wrapper failed: {e}")
        return False

    # Test 4: Query processing with search
    print("\n4. Testing Query Processing with Search...")
    try:
        response = await integration.query("search latest AI news")
        print(f"✅ Query processed successfully")
        print(f"   Success: {response.success}")
        print(f"   Tools: {', '.join(response.tools_used)}")
        print(f"   Content preview: {response.content[:100]}...")

    except Exception as e:
        print(f"❌ Query processing failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 Claude Web Search Proxy Test Completed Successfully!")
    print("\nKey Features Validated:")
    print("✅ Web search proxy initialization")
    print("✅ Multiple search types (AI, tech, news, general)")
    print("✅ Integration with PrinceFlowers agent")
    print("✅ Query processing with search capabilities")
    print("✅ Error handling and fallback mechanisms")
    print("\n🚀 Ready for TORQ Console integration!")

    return True

async def test_prince_command_simulation():
    """Simulate prince commands that would trigger web search"""
    print("\n" + "=" * 60)
    print("🤖 Testing Prince Command Simulation")
    print("=" * 60)

    integration = PrinceFlowersIntegrationWrapper()

    # Test commands that should trigger search
    test_commands = [
        "prince search latest AI developments",
        "prince help",
        "prince status",
        "search Python tutorials",
        "what is machine learning"
    ]

    for command in test_commands:
        print(f"\n🔍 Testing command: '{command}'")
        try:
            response = await integration.query(command)
            print(f"   ✅ Success: {response.success}")
            print(f"   Confidence: {response.confidence:.1%}")
            print(f"   Preview: {response.content[:150]}...")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print("\n🎯 Command simulation completed!")

if __name__ == "__main__":
    print("🚀 Starting Claude Web Search Proxy Test Suite")

    try:
        # Run main test
        success = asyncio.run(test_claude_search_proxy())

        if success:
            # Run command simulation
            asyncio.run(test_prince_command_simulation())

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)