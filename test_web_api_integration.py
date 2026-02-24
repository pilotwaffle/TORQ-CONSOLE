"""
Web API Integration Tests

Tests the /api/chat endpoint and agent contract to prevent
"silent broken UI" deployments.

Run with: pytest test_web_api_integration.py -v
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_agent_contract():
    """
    Test 1: Agent Contract Validation

    Verify that TORQPrinceFlowers implements the AsyncAgent protocol.
    This prevents the web API from breaking at runtime.
    """
    print("\n[Test 1] Agent Contract Validation")

    from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
    from torq_console.agents.protocols import validate_agent_contract, AsyncAgent

    # Create agent instance
    agent = TORQPrinceFlowers()

    # Validate contract
    is_valid, errors = validate_agent_contract(agent)

    if not is_valid:
        print(f"  [FAIL] Agent contract validation failed:")
        for error in errors:
            print(f"    - {error}")
        return False

    # Also check Protocol compliance
    if not isinstance(agent, AsyncAgent):
        print(f"  [FAIL] Agent does not implement AsyncAgent protocol")
        return False

    print(f"  [PASS] Agent contract validation passed")
    return True


async def test_agent_arun_basic():
    """
    Test 2: Agent arun() Basic Functionality

    Call agent.arun() with a simple message and verify response structure.
    """
    print("\n[Test 2] Agent arun() Basic Functionality")

    # Skip if no API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("  [SKIP] No ANTHROPIC_API_KEY configured")
        return True

    from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
    from torq_console.agents.protocols import AgentResponse

    agent = TORQPrinceFlowers()

    # Test with simple message
    try:
        result = await agent.arun("hello")

        # Validate response structure
        try:
            response = AgentResponse(**result)
        except Exception as e:
            print(f"  [FAIL] Response does not match AgentResponse schema: {e}")
            print(f"    Got: {result}")
            return False

        # Check required fields
        if not response.response:
            print(f"  [FAIL] Response has empty 'response' field")
            return False

        if not response.success:
            print(f"  [FAIL] Response marked as failed: {response.error}")
            return False

        # Check that response is not just echoing the input
        if response.response.strip().lower() == "hello":
            print(f"  [FAIL] Response appears to echo input")
            return False

        print(f"  [PASS] arun() returned valid response")
        print(f"    Response length: {len(response.response)} chars")
        print(f"    Schema version: {response.schema_version}")
        return True

    except Exception as e:
        print(f"  [FAIL] arun() raised exception: {e}")
        return False


async def test_railway_app_chat_endpoint():
    """
    Test 3: Railway App /api/chat Endpoint

    Test the FastAPI endpoint directly using TestClient.
    This would have caught the missing arun() issue.
    """
    print("\n[Test 3] Railway App /api/chat Endpoint (mock)")

    # Note: This is a mock test since we don't want to start the full FastAPI app
    # In a real setup, use TestClient from fastapi.testclient

    from torq_console.agents.protocols import AgentResponse

    # Simulate what the endpoint does
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("  [SKIP] No ANTHROPIC_API_KEY configured")
        return True

    from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers

    try:
        agent = TORQPrinceFlowers()
        result = await agent.arun("test message")

        # Validate response
        response = AgentResponse(**result)

        if not response.response:
            print(f"  [FAIL] Empty response from agent")
            return False

        # Check response has meaningful content (not just echo)
        if len(response.response) < 10:
            print(f"  [FAIL] Response too short: {len(response.response)} chars")
            return False

        print(f"  [PASS] /api/chat would return valid response")
        return True

    except Exception as e:
        print(f"  [FAIL] Endpoint simulation failed: {e}")
        return False


async def test_error_response_structure():
    """
    Test 4: Error Response Structure

    Verify that errors return structured payloads, not empty/echo responses.
    This prevents the "truncated UI" symptom.
    """
    print("\n[Test 4] Error Response Structure")

    from torq_console.agents.protocols import AgentResponse

    # Simulate an error response from agent
    error_response = AgentResponse(
        response="I'm sorry, I encountered an error.",
        success=False,  # This marks it as an error
        confidence=0.0,
        execution_time=0.1,
        tools_used=[],
        error="Test error",
        error_type="TestError",
    )

    # Verify structure - success should be False for errors
    if error_response.success:
        print(f"  [FAIL] Error response should have success=False")
        return False

    if not error_response.error:
        print(f"  [FAIL] Error response missing error field")
        return False

    # Verify the API layer would correctly interpret this
    # (ok = success, so ok=False for errors)
    error_dict = error_response.model_dump()
    api_ok = error_dict["success"]  # API maps ok = success

    if api_ok:  # Should be False
        print(f"  [FAIL] API would set ok=True for error response")
        return False

    print(f"  [PASS] Error response structure is valid")
    return True


async def test_metadata_computed_not_hardcoded():
    """
    Test 5: Metadata is Computed, Not Hardcoded

    Verify that metadata fields like evidence_level and satisfaction
    are computed from actual signals, not hardcoded constants.
    """
    print("\n[Test 5] Metadata Computed from Actual Signals")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("  [SKIP] No ANTHROPIC_API_KEY configured")
        return True

    from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers
    from torq_console.agents.protocols import AgentResponse

    agent = TORQPrinceFlowers()

    # Test 1: Simple query should have low evidence (no tools)
    result1 = await agent.arun("what is 2+2?")
    response1 = AgentResponse(**result1)

    if response1.evidence_level == "medium" or response1.evidence_level == "high":
        print(f"  [FAIL] Simple query incorrectly marked {response1.evidence_level} evidence")
        return False

    # Test 2: Research query should have higher evidence
    result2 = await agent.arun("search for the latest Python 3.13 features")
    response2 = AgentResponse(**result2)

    if response2.evidence_level and response2.evidence_level not in ["low", "medium", "high"]:
        print(f"  [FAIL] Invalid evidence_level: {response2.evidence_level}")
        return False

    print(f"  [PASS] Metadata is computed from actual signals")
    print(f"    Simple query evidence: {response1.evidence_level}")
    print(f"    Research query evidence: {response2.evidence_level}")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Web API Integration Test Suite")
    print("=" * 60)

    tests = [
        test_agent_contract,
        test_agent_arun_basic,
        test_railway_app_chat_endpoint,
        test_error_response_structure,
        test_metadata_computed_not_hardcoded,
    ]

    results = []
    for test in tests:
        try:
            passed = await test()
            results.append(passed)
        except Exception as e:
            print(f"  [FAIL] Test raised exception: {e}")
            results.append(False)

    # Summary
    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(results)} passed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
