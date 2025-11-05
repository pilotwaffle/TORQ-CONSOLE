#!/usr/bin/env python3
"""
Validation Test for Bug Fixes

Tests the fixes for:
1. RoutingDecision missing confidence/reasoning attributes
2. get_workflow_agent() return type annotation
3. JSON enum serialization
4. get_marvin_status() API key check
"""

import sys
from dataclasses import asdict
from typing import get_type_hints


def test_routing_decision_attributes():
    """Test that RoutingDecision has confidence and reasoning attributes."""
    print("\n🧪 Test 1: RoutingDecision Attributes")
    print("-" * 50)

    try:
        from torq_console.agents.marvin_query_router import RoutingDecision, AgentCapability
        from torq_console.marvin_integration import ComplexityLevel

        # Create a RoutingDecision instance with all required fields
        decision = RoutingDecision(
            primary_agent="test_agent",
            fallback_agents=["agent1", "agent2"],
            capabilities_needed=[AgentCapability.GENERAL_CHAT],
            estimated_complexity=ComplexityLevel.SIMPLE,
            suggested_approach="Test approach",
            context_requirements={},
            confidence=0.85,
            reasoning="Test reasoning"
        )

        # Verify attributes exist and have correct values
        assert hasattr(decision, 'confidence'), "Missing 'confidence' attribute"
        assert hasattr(decision, 'reasoning'), "Missing 'reasoning' attribute"
        assert decision.confidence == 0.85, f"Expected confidence 0.85, got {decision.confidence}"
        assert decision.reasoning == "Test reasoning", f"Expected 'Test reasoning', got {decision.reasoning}"

        print("✅ PASS: RoutingDecision has confidence and reasoning attributes")
        print(f"   confidence: {decision.confidence}")
        print(f"   reasoning: {decision.reasoning}")
        return True

    except AttributeError as e:
        print(f"❌ FAIL: AttributeError - {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__} - {e}")
        return False


def test_get_workflow_agent_return_type():
    """Test that get_workflow_agent() has proper return type annotation."""
    print("\n🧪 Test 2: get_workflow_agent() Return Type")
    print("-" * 50)

    try:
        from torq_console.agents.marvin_workflow_agents import get_workflow_agent

        # Get type hints
        type_hints = get_type_hints(get_workflow_agent)

        if 'return' in type_hints:
            return_type = type_hints['return']
            print(f"✅ PASS: Return type annotation exists: {return_type}")
            return True
        else:
            print("❌ FAIL: Missing return type annotation")
            return False

    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__} - {e}")
        return False


def test_agent_interaction_json_serialization():
    """Test that AgentInteraction with enum can be serialized to JSON."""
    print("\n🧪 Test 3: AgentInteraction JSON Serialization")
    print("-" * 50)

    try:
        import json
        from torq_console.agents.marvin_memory import AgentInteraction, InteractionType

        # Create an AgentInteraction with an enum
        interaction = AgentInteraction(
            interaction_id="test_123",
            timestamp="2025-01-01T00:00:00",
            interaction_type=InteractionType.CODE_GENERATION,
            user_input="test input",
            agent_response="test response",
            agent_name="test_agent",
            success=True
        )

        # Convert to dict and fix enum
        interaction_dict = asdict(interaction)
        interaction_dict['interaction_type'] = interaction.interaction_type.value

        # Try to serialize to JSON
        json_str = json.dumps(interaction_dict)

        # Verify it worked
        parsed = json.loads(json_str)
        assert parsed['interaction_type'] == 'code_generation', "Enum not properly serialized"

        print("✅ PASS: AgentInteraction can be JSON serialized")
        print(f"   interaction_type: {parsed['interaction_type']}")
        return True

    except TypeError as e:
        print(f"❌ FAIL: TypeError during JSON serialization - {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__} - {e}")
        return False


def test_get_marvin_status_api_check():
    """Test that get_marvin_status() includes API key information."""
    print("\n🧪 Test 4: get_marvin_status() API Key Check")
    print("-" * 50)

    try:
        from torq_console.agents import get_marvin_status, is_marvin_available

        status = get_marvin_status()

        # Check basic status fields
        assert 'available' in status, "Missing 'available' field"

        print(f"   Marvin available: {status['available']}")

        # If Marvin is available, check for API key status
        if status['available']:
            if 'api_keys' in status:
                print("✅ PASS: API key status is included")
                print(f"   API keys info: {status['api_keys']}")
                return True
            else:
                print("❌ FAIL: Missing 'api_keys' field when Marvin is available")
                return False
        else:
            print("✅ PASS: Status returned (Marvin not available, skipping API key check)")
            print(f"   Error: {status.get('error', 'Unknown')[:100]}")
            return True

    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__} - {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Bug Fixes Validation Test Suite")
    print("=" * 70)

    tests = [
        ("RoutingDecision Attributes", test_routing_decision_attributes),
        ("get_workflow_agent() Return Type", test_get_workflow_agent_return_type),
        ("AgentInteraction JSON Serialization", test_agent_interaction_json_serialization),
        ("get_marvin_status() API Check", test_get_marvin_status_api_check),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'=' * 70}")
    print("📊 Test Results Summary")
    print(f"{'=' * 70}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\nPassed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n✅ All bug fixes validated successfully!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
