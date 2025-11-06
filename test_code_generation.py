"""
Test script to verify Prince Flowers agent can generate Python code.
"""
import asyncio
import os
from torq_console.agents.marvin_prince_flowers import MarvinPrinceFlowers

async def test_code_generation():
    """Test Python code generation through Prince Flowers agent."""

    # Initialize agent
    print("Initializing Prince Flowers agent...")
    agent = MarvinPrinceFlowers(model="anthropic/claude-sonnet-4-20250514")

    # Test 1: Simple function generation
    print("\n=== Test 1: Generate a simple sorting function ===")
    test1_query = "Write a Python function that implements bubble sort algorithm. Include docstring and type hints."

    response1 = await agent.chat(test1_query)
    print(f"Response:\n{response1}")

    # Test 2: Class generation
    print("\n=== Test 2: Generate a simple class ===")
    test2_query = "Create a Python class called 'Calculator' with methods for add, subtract, multiply, and divide."

    response2 = await agent.chat(test2_query)
    print(f"Response:\n{response2}")

    # Test 3: Explain code
    print("\n=== Test 3: Explain code ===")
    test3_query = """
    Explain what this code does:

    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    """

    response3 = await agent.chat(test3_query)
    print(f"Response:\n{response3}")

    print("\n=== All tests completed successfully! ===")

if __name__ == "__main__":
    # Set API key if not already set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Tests may fail.")

    asyncio.run(test_code_generation())
