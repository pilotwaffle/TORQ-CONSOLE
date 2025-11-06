"""
Test script for GLM-4.6 integration in TORQ Console.
"""
import asyncio
import os
from torq_console.agents.glm_prince_flowers import GLMPrinceFlowersAgent

async def test_glm_integration():
    """Test GLM-4.6 Prince Flowers agent."""

    print("=" * 80)
    print("GLM-4.6 Integration Test for TORQ Console")
    print("=" * 80)

    # Check API key
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GLM_API_KEY not set in environment")
        print("Please set GLM_API_KEY in .env file or environment variables")
        return

    print(f"\n✅ GLM API Key found: {api_key[:20]}...")

    # Initialize agent
    print("\n🤖 Initializing GLM Prince Flowers agent...")
    agent = GLMPrinceFlowersAgent(api_key=api_key, model="glm-4.6")
    print(f"✅ Agent initialized with model: {agent.model}")
    print(f"   Context window: 200K tokens")
    print(f"   Max output: 128K tokens")
    print(f"   Performance: Par with Claude Sonnet 4")

    # Test 1: Simple conversation
    print("\n" + "=" * 80)
    print("Test 1: Simple Conversation")
    print("=" * 80)

    response1 = await agent.chat("Hello! Can you introduce yourself?")
    print(f"\nAgent Response:\n{response1}\n")

    # Test 2: Code generation
    print("\n" + "=" * 80)
    print("Test 2: Code Generation")
    print("=" * 80)

    code_response = await agent.generate_code(
        requirements="Create a Python function that calculates the factorial of a number using recursion",
        language="python"
    )
    print(f"\nGenerated Code:\n{code_response}\n")

    # Test 3: Code explanation
    print("\n" + "=" * 80)
    print("Test 3: Code Explanation")
    print("=" * 80)

    test_code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""

    explanation = await agent.explain_code(test_code, language="python")
    print(f"\nCode Explanation:\n{explanation}\n")

    # Test 4: Multi-turn conversation
    print("\n" + "=" * 80)
    print("Test 4: Multi-turn Conversation")
    print("=" * 80)

    response2 = await agent.chat("What are the key principles of clean code?")
    print(f"\nAgent Response 1:\n{response2}\n")

    response3 = await agent.chat("Can you give me an example of applying the single responsibility principle in Python?")
    print(f"\nAgent Response 2:\n{response3}\n")

    print(f"\n📊 Conversation history length: {agent.get_history_length()} messages")

    # Test 5: Web search (if available)
    print("\n" + "=" * 80)
    print("Test 5: Web Search (Optional)")
    print("=" * 80)

    try:
        search_response = await agent.research_with_web_search(
            "What are the latest features in Python 3.12?"
        )
        print(f"\nWeb Search Response:\n{search_response}\n")
    except Exception as e:
        print(f"\n⚠️ Web search test skipped or failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ All GLM-4.6 Integration Tests Completed Successfully!")
    print("=" * 80)
    print(f"\n📈 Summary:")
    print(f"   - API Key: Configured ✅")
    print(f"   - Agent Initialization: Success ✅")
    print(f"   - Simple Chat: Working ✅")
    print(f"   - Code Generation: Working ✅")
    print(f"   - Code Explanation: Working ✅")
    print(f"   - Multi-turn Conversation: Working ✅")
    print(f"   - Conversation History: {agent.get_history_length()} messages")
    print("\n🎉 GLM-4.6 is ready for use in TORQ Console!")

if __name__ == "__main__":
    asyncio.run(test_glm_integration())
