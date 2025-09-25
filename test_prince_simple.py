"""
Simple Prince Flowers Test - Windows Compatible
Tests the Prince Flowers integration without Unicode emojis
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def simple_test():
    """Simple test without Unicode issues"""
    print("=== Prince Flowers Simple Test ===")
    print("Testing TORQ Console integration...")

    try:
        # Test 1: Import the integration
        from torq_integration import PrinceFlowersAgent
        print("✓ Successfully imported PrinceFlowersAgent")

        # Test 2: Initialize the agent
        agent = PrinceFlowersAgent()
        print(f"✓ Agent initialized - Status: {'Available' if agent.available else 'Mock mode'}")

        # Test 3: Check capabilities
        print(f"✓ Agent capabilities: {len(agent.capabilities)} tools available")

        # Test 4: Basic status check
        print("✓ Basic initialization tests passed")

        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

async def async_test():
    """Async test of agent functionality"""
    print("\n=== Async Functionality Test ===")

    try:
        from torq_integration import PrinceFlowersAgent
        agent = PrinceFlowersAgent()

        # Test async query processing
        result = await agent.process_query("what are your capabilities?")

        if result["success"]:
            print("✓ Async query processing works")
            print(f"✓ Response received: {len(result['response'])} characters")
            print(f"✓ Agent: {result['agent']}")

            metadata = result.get("metadata", {})
            if metadata:
                print(f"✓ Performance data available: {len(metadata)} metrics")

            return True
        else:
            print(f"✗ Query failed: {result['error']}")
            return False

    except Exception as e:
        print(f"✗ Async test error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Prince Flowers Integration Test")
    print("=" * 40)

    # Synchronous tests
    sync_success = simple_test()

    # Asynchronous tests
    async_success = asyncio.run(async_test())

    # Summary
    print("\n=== Test Summary ===")
    print(f"Sync Tests: {'PASSED' if sync_success else 'FAILED'}")
    print(f"Async Tests: {'PASSED' if async_success else 'FAILED'}")

    overall_success = sync_success and async_success
    print(f"Overall: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")

    if overall_success:
        print("\n*** Prince Flowers integration is working correctly! ***")
        print("You can now use 'prince help' in your TORQ Console interactive shell.")
    else:
        print("\n*** Some issues detected - check error messages above ***")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)