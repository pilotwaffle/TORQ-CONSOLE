#!/usr/bin/env python3
"""
Basic Policy-Driven Routing System Test

Core functionality tests without Unicode characters for Windows compatibility.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_policy_loading():
    """Test policy loading and basic functionality."""
    print("=" * 50)
    print("TESTING POLICY LOADING")
    print("=" * 50)

    try:
        from torq_console.agents.policy_framework import PolicyFramework

        # Load policy
        policy_path = project_root / "policies" / "routing" / "v1.yaml"
        framework = PolicyFramework(str(policy_path))

        # Test policy loading
        assert framework.current_policy is not None
        assert framework.policy_version == "1.0.0"
        print("PASS: Policy loaded successfully")

        # Test intent mapping
        web_search_mapping = framework.get_intent_mapping("web_search")
        assert web_search_mapping is not None
        assert web_search_mapping.primary_agent == "research_specialist"
        print("PASS: Intent mapping works")

        # Test agent definition
        prince_def = framework.get_agent_definition("prince_flowers")
        assert prince_def is not None
        assert len(prince_def.capabilities) > 0
        print("PASS: Agent definition works")

        # Test cost estimation
        cost = framework.estimate_cost("prince_flowers", 1000)
        assert cost > 0
        print(f"PASS: Cost estimation works: ${cost:.6f}")

        print("SUCCESS: All basic policy tests passed")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_policy_validation():
    """Test policy compliance validation."""
    print("\n" + "=" * 50)
    print("TESTING POLICY VALIDATION")
    print("=" * 50)

    try:
        from torq_console.agents.policy_framework import PolicyFramework, PolicyComplianceStatus

        policy_path = project_root / "policies" / "routing" / "v1.yaml"
        framework = PolicyFramework(str(policy_path))

        # Test compliant decision
        status, violations = framework.validate_routing_decision(
            intent="web_search",
            selected_agent="research_specialist",
            confidence_score=0.8,
            estimated_cost=0.03,
            estimated_latency=3000
        )
        assert status == PolicyComplianceStatus.COMPLIANT
        assert len(violations) == 0
        print("PASS: Compliant routing validation works")

        # Test cost violation
        status, violations = framework.validate_routing_decision(
            intent="web_search",
            selected_agent="research_specialist",
            confidence_score=0.8,
            estimated_cost=0.10,  # Exceeds budget
            estimated_latency=3000
        )
        assert status == PolicyComplianceStatus.ESCALATION
        assert len(violations) > 0
        print("PASS: Cost violation detection works")

        # Test fallback agent selection
        fallbacks = framework.get_fallback_agents(
            intent="web_search",
            primary_agent="research_specialist",
            violations=["Estimated cost $0.10 exceeds budget $0.05"]
        )
        assert len(fallbacks) > 0
        assert "prince_flowers" in fallbacks
        print("PASS: Fallback agent selection works")

        print("SUCCESS: All validation tests passed")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_policy_structure():
    """Test policy file structure."""
    print("\n" + "=" * 50)
    print("TESTING POLICY STRUCTURE")
    print("=" * 50)

    try:
        import yaml

        policy_path = project_root / "policies" / "routing" / "v1.yaml"
        assert policy_path.exists(), "Policy file should exist"

        with open(policy_path, 'r') as f:
            policy_data = yaml.safe_load(f)

        # Check required sections
        required_sections = [
            'metadata', 'defaults', 'intent_mappings',
            'agent_definitions', 'escalation_rules', 'monitoring', 'compliance'
        ]

        for section in required_sections:
            assert section in policy_data, f"Missing section: {section}"

        # Check specific intents
        intents = policy_data['intent_mappings']
        required_intents = ['web_search', 'code_generation', 'debugging']

        for intent in required_intents:
            assert intent in intents, f"Missing intent mapping: {intent}"

        # Check agents
        agents = policy_data['agent_definitions']
        required_agents = ['research_specialist', 'prince_flowers']

        for agent in required_agents:
            assert agent in agents, f"Missing agent definition: {agent}"

        print("PASS: Policy file structure is correct")
        print("SUCCESS: All structure tests passed")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration with existing systems."""
    print("\n" + "=" * 50)
    print("TESTING INTEGRATION")
    print("=" * 50)

    try:
        from torq_console.agents import get_policy_framework, create_policy_driven_router

        # Test global policy framework
        global_policy = get_policy_framework()
        assert global_policy is not None
        assert global_policy.policy_version == "1.0.0"
        print("PASS: Global policy framework works")

        # Test factory function
        router = create_policy_driven_router()
        assert router is not None
        print("PASS: Factory function works")

        print("SUCCESS: All integration tests passed")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("POLICY-DRIVEN ROUTING SYSTEM - BASIC TESTS")
    print("=" * 60)

    test_results = []

    # Run individual tests
    test_results.append(test_policy_loading())
    test_results.append(test_policy_validation())
    test_results.append(test_policy_structure())
    test_results.append(test_integration())

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(test_results)
    total = len(test_results)

    test_names = [
        "Policy Loading",
        "Policy Validation",
        "Policy Structure",
        "Integration"
    ]

    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if passed == total:
        print("\nSUCCESS: ALL TESTS PASSED!")
        print("Policy-driven routing system is working correctly.")
        print("\nKey features verified:")
        print("- Policy loading and validation")
        print("- Intent-to-agent mappings")
        print("- Cost and latency estimation")
        print("- Compliance checking")
        print("- Fallback agent selection")
        print("- Integration with existing systems")
        return True
    else:
        print(f"\nWARNING: {total - passed} test(s) failed.")
        print("Check the implementation and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)