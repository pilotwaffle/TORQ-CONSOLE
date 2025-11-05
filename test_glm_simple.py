"""Simple GLM-4.6 test without emoji characters."""
import asyncio
import os
from torq_console.agents.glm_prince_flowers import GLMPrinceFlowersAgent

async def test():
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        print("ERROR: GLM_API_KEY not set")
        return

    print("Initializing GLM-4.6 agent...")
    agent = GLMPrinceFlowersAgent(model="glm-4.6")

    print("\nTest 1: Simple greeting")
    result1 = await agent.chat("Hello! Please introduce yourself briefly.")
    print(f"Response: {result1[:200]}...")

    print("\nTest 2: Code generation")
    result2 = await agent.generate_code(
        requirements="Create a Python function that adds two numbers",
        language="python"
    )
    print(f"Generated code:\n{result2}")

    print("\nGLM-4.6 integration working!")

if __name__ == "__main__":
    asyncio.run(test())
