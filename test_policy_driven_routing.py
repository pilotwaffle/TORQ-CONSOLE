#!/usr/bin/env python3
"""
Policy-Driven Routing System Test Suite

Comprehensive tests for the policy-driven routing implementation.
Validates policy loading, routing decisions, compliance checking, and telemetry.
"""

import asyncio
import logging
import os
import sys
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from torq_console.agents.policy_framework import (
    PolicyFramework,
    PolicyComplianceStatus,
    IntentMapping,
    AgentDefinition,
    EscalationRule,
    PolicyError
)
from torq_console.agents.policy_driven_router import (
    PolicyDrivenRouter,
    PolicyRoutingDecision,
    create_policy_driven_router
)
from torq_console.agents.marvin_query_router import AgentCapability, ComplexityLevel


# Test configuration
TEST_SESSION_ID = "test_session_001"
TEST_QUERIES = {
    "web_search": "search for latest AI news",
    "code_generation": "write a Python function to sort a list",
    "debugging": "fix this error: TypeError in my code",
    "general_chat": "how are you today?",
    "cost_violation": "generate a very large and complex application"
}


class TestPolicyFramework:
    """Test suite for PolicyFramework."""

    def setup_method(self):
        """Set up test environment."""
        self.logger = logging.getLogger("TestPolicyFramework")
        logging.basicConfig(level=logging.INFO)

        # Use the actual policy file from the project
        policy_path = project_root / "policies" / "routing" / "v1.yaml"
        self.framework = PolicyFramework(str(policy_path))

    def test_policy_loading(self):
        """Test policy loading and validation."""
        print("Testing policy loading...")

        # Check policy loaded successfully
        assert self.framework.current_policy is not None
        assert self.framework.policy_version is not None

        # Check metadata
        metadata = self.framework.current_policy.metadata
        assert "name" in metadata
        assert "version" in metadata
        assert "description" in metadata

        # Check intent mappings
        intent_mappings = self.framework.current_policy.intent_mappings
        assert len(intent_mappings) > 0
        assert "web_search" in intent_mappings
        assert "code_generation" in intent_mappings

        # Check agent definitions
        agent_definitions = self.framework.current_policy.agent_definitions
        assert len(agent_definitions) > 0
        assert "prince_flowers" in agent_definitions
        assert "research_specialist" in agent_definitions

        print(f"PASS: Policy loaded successfully - Version: {self.framework.policy_version}")
        print(f"PASS: Found {len(intent_mappings)} intent mappings")
        print(f"PASS: Found {len(agent_definitions)} agent definitions")

    def test_intent_mapping_retrieval(self):
        """Test intent mapping retrieval."""
        print("Testing intent mapping retrieval...")

        # Test valid intent
        web_search_mapping = self.framework.get_intent_mapping("web_search")
        assert web_search_mapping is not None
        assert isinstance(web_search_mapping, IntentMapping)
        assert web_search_mapping.primary_agent == "research_specialist"
        assert "prince_flowers" in web_search_mapping.fallback_agents
        assert web_search_mapping.confidence_threshold > 0

        # Test invalid intent
        invalid_mapping = self.framework.get_intent_mapping("nonexistent_intent")
        assert invalid_mapping is None

        print("PASS: Intent mapping retrieval works correctly")

    def test_agent_definition_retrieval(self):
        """Test agent definition retrieval."""
        print("Testing agent definition retrieval...")

        # Test valid agent
        prince_def = self.framework.get_agent_definition("prince_flowers")
        assert prince_def is not None
        assert isinstance(prince_def, AgentDefinition)
        assert len(prince_def.capabilities) > 0
        assert prince_def.cost_per_token > 0
        assert prince_def.max_concurrent_requests > 0

        # Test invalid agent
        invalid_def = self.framework.get_agent_definition("nonexistent_agent")
        assert invalid_def is None

        print("PASS: Agent definition retrieval works correctly")

    def test_routing_decision_validation(self):
        """Test routing decision validation."""
        print("Testing routing decision validation...")

        # Test compliant decision
        status, violations = self.framework.validate_routing_decision(
            intent="web_search",
            selected_agent="research_specialist",
            confidence_score=0.8,
            estimated_cost=0.03,
            estimated_latency=3000
        )
        assert status == PolicyComplianceStatus.COMPLIANT
        assert len(violations) == 0

        # Test non-compliant decision (wrong agent)
        status, violations = self.framework.validate_routing_decision(
            intent="web_search",
            selected_agent="prince_flowers",  # Not primary agent
            confidence_score=0.8,
            estimated_cost=0.03,
            estimated_latency=3000
        )
        assert status == PolicyComplianceStatus.FALLBACK
        assert len(violations) > 0

        # Test cost violation
        status, violations = self.framework.validate_routing_decision(
            intent="web_search",
            selected_agent="research_specialist",
            confidence_score=0.8,
            estimated_cost=0.10,  # Exceeds budget
            estimated_latency=3000
        )
        assert status == PolicyComplianceStatus.ESCALATION
        assert len(violations) > 0
        assert any("cost" in v.lower() for v in violations)

        print("PASS: Routing decision validation works correctly")

    def test_cost_estimation(self):
        """Test cost estimation."""
        print("Testing cost estimation...")

        # Test cost estimation for different agents
        prince_cost = self.framework.estimate_cost("prince_flowers", 1000)
        research_cost = self.framework.estimate_cost("research_specialist", 1000)

        assert prince_cost > 0
        assert research_cost > 0
        # Research specialist should be more expensive than prince_flowers
        assert research_cost > prince_cost

        # Test with complexity multiplier
        complex_cost = self.framework.estimate_cost("prince_flowers", 1000, 2.0)
        simple_cost = self.framework.estimate_cost("prince_flowers", 1000, 0.5)
        assert complex_cost > simple_cost

        print(f"PASS: Cost estimation works - Prince: ${prince_cost:.6f}, Research: ${research_cost:.6f}")

    def test_latency_estimation(self):
        """Test latency estimation."""
        print("Testing latency estimation...")

        # Test latency estimation for different complexities
        simple_latency = self.framework.estimate_latency("prince_flowers", "simple")
        complex_latency = self.framework.estimate_latency("prince_flowers", "complex")

        assert simple_latency > 0
        assert complex_latency > 0
        assert complex_latency > simple_latency

        print(f"PASS: Latency estimation works - Simple: {simple_latency}ms, Complex: {complex_latency}ms")

    def test_fallback_agent_selection(self):
        """Test fallback agent selection."""
        print("Testing fallback agent selection...")

        # Test cost violation fallback
        fallbacks = self.framework.get_fallback_agents(
            intent="web_search",
            primary_agent="research_specialist",
            violations=["Estimated cost $0.10 exceeds budget $0.05"]
        )
        assert len(fallbacks) > 0
        assert "prince_flowers" in fallbacks

        # Test confidence violation fallback
        fallbacks = self.framework.get_fallback_agents(
            intent="code_generation",
            primary_agent="code_generation_agent",
            violations=["Confidence 0.5 below threshold 0.8"]
        )
        assert len(fallbacks) > 0
        assert "prince_flowers" in fallbacks

        print("PASS: Fallback agent selection works correctly")

    def test_policy_metrics(self):
        """Test policy metrics collection."""
        print("Testing policy metrics...")

        metrics = self.framework.get_policy_metrics()

        assert "policy_version" in metrics
        assert "policy_name" in metrics
        assert "total_intents" in metrics
        assert "total_agents" in metrics
        assert "compliance_requirements" in metrics

        assert metrics["policy_version"] == self.framework.policy_version
        assert metrics["total_intents"] > 0
        assert metrics["total_agents"] > 0

        print(f"PASS: Policy metrics collected - Version: {metrics['policy_version']}")


class TestPolicyDrivenRouter:
    """Test suite for PolicyDrivenRouter."""

    def setup_method(self):
        """Set up test environment."""
        self.logger = logging.getLogger("TestPolicyDrivenRouter")

        # Create policy framework
        policy_path = project_root / "policies" / "routing" / "v1.yaml"
        self.framework = PolicyFramework(str(policy_path))

        # Mock Marvin integration to avoid API calls during tests
        with patch('torq_console.agents.marvin_query_router.TorqMarvinIntegration'):
            self.router = PolicyDrivenRouter(policy_framework=self.framework)

    async def test_compliant_routing(self):
        """Test routing with compliant decisions."""
        print("Testing compliant routing...")

        # Mock the base router to return a compliant decision
        mock_decision = Mock()
        mock_decision.primary_agent = "research_specialist"
        mock_decision.fallback_agents = ["prince_flowers"]
        mock_decision.capabilities_needed = [AgentCapability.WEB_SEARCH]
        mock_decision.estimated_complexity = ComplexityLevel.MODERATE
        mock_decision.confidence = 0.8
        mock_decision.reasoning = "Standard web search query"

        self.router.base_router.route_query = Mock(return_value=mock_decision)

        # Test routing
        result = await self.router.route_query(
            query=TEST_QUERIES["web_search"],
            session_id=TEST_SESSION_ID
        )

        assert isinstance(result, PolicyRoutingDecision)
        assert result.compliance_status == PolicyComplianceStatus.COMPLIANT
        assert len(result.policy_violations) == 0
        assert not result.escalation_triggered
        assert result.base_decision.primary_agent == "research_specialist"

        print("PASS: Compliant routing works correctly")

    async def test_cost_violation_routing(self):
        """Test routing with cost violations."""
        print("Testing cost violation routing...")

        # Mock a decision that violates cost constraints
        mock_decision = Mock()
        mock_decision.primary_agent = "code_generation_agent"
        mock_decision.fallback_agents = ["prince_flowers"]
        mock_decision.capabilities_needed = [AgentCapability.CODE_GENERATION]
        mock_decision.estimated_complexity = ComplexityLevel.VERY_COMPLEX
        mock_decision.confidence = 0.9
        mock_decision.reasoning = "Complex code generation request"

        self.router.base_router.route_query = Mock(return_value=mock_decision)

        # Test routing
        result = await self.router.route_query(
            query=TEST_QUERIES["cost_violation"],
            session_id=TEST_SESSION_ID
        )

        assert isinstance(result, PolicyRoutingDecision)
        assert result.compliance_status != PolicyComplianceStatus.COMPLIANT
        assert result.escalation_triggered
        assert len(result.policy_violations) > 0

        # Should escalate to lower-cost agent
        assert result.base_decision.primary_agent != "code_generation_agent" or len(result.fallback_path) > 0

        print("PASS: Cost violation routing works correctly")

    async def test_fallback_routing(self):
        """Test routing with fallback agents."""
        print("Testing fallback routing...")

        # Mock a decision that requires fallback
        mock_decision = Mock()
        mock_decision.primary_agent = "nonexistent_agent"
        mock_decision.fallback_agents = ["prince_flowers"]
        mock_decision.capabilities_needed = [AgentCapability.GENERAL_CHAT]
        mock_decision.estimated_complexity = ComplexityLevel.MODERATE
        mock_decision.confidence = 0.6
        mock_decision.reasoning = "General chat query"

        self.router.base_router.route_query = Mock(return_value=mock_decision)

        # Test routing
        result = await self.router.route_query(
            query=TEST_QUERIES["general_chat"],
            session_id=TEST_SESSION_ID
        )

        assert isinstance(result, PolicyRoutingDecision)
        # Should have escalated to a valid agent
        assert result.base_decision.primary_agent in self.framework.current_policy.agent_definitions

        print("PASS: Fallback routing works correctly")

    async def test_metrics_collection(self):
        """Test routing metrics collection."""
        print("Testing metrics collection...")

        # Mock a compliant decision
        mock_decision = Mock()
        mock_decision.primary_agent = "prince_flowers"
        mock_decision.fallback_agents = []
        mock_decision.capabilities_needed = [AgentCapability.GENERAL_CHAT]
        mock_decision.estimated_complexity = ComplexityLevel.MODERATE
        mock_decision.confidence = 0.7
        mock_decision.reasoning = "General query"

        self.router.base_router.route_query = Mock(return_value=mock_decision)

        # Make multiple routing calls
        for query in [TEST_QUERIES["general_chat"], TEST_QUERIES["web_search"]]:
            await self.router.route_query(query, TEST_SESSION_ID)

        # Check metrics
        metrics = self.router.get_policy_metrics()
        assert "policy_version" in metrics
        assert "routing_metrics" in metrics
        assert "compliance_rate" in metrics
        assert metrics["routing_metrics"]["total_routes"] == 2

        print(f"PASS: Metrics collection works - Total routes: {metrics['routing_metrics']['total_routes']}")

    async def test_policy_version_tracking(self):
        """Test policy version tracking in routing decisions."""
        print("Testing policy version tracking...")

        # Mock a compliant decision
        mock_decision = Mock()
        mock_decision.primary_agent = "prince_flowers"
        mock_decision.fallback_agents = []
        mock_decision.capabilities_needed = [AgentCapability.GENERAL_CHAT]
        mock_decision.estimated_complexity = ComplexityLevel.MODERATE
        mock_decision.confidence = 0.7
        mock_decision.reasoning = "General query"

        self.router.base_router.route_query = Mock(return_value=mock_decision)

        # Test routing
        result = await self.router.route_query(
            query=TEST_QUERIES["general_chat"],
            session_id=TEST_SESSION_ID
        )

        assert result.policy_version == self.framework.get_policy_version()
        assert "policy_version" in result.policy_metadata

        print(f"PASS: Policy version tracking works - Version: {result.policy_version}")


class TestPolicyIntegration:
    """Test suite for policy integration with existing systems."""

    def setup_method(self):
        """Set up test environment."""
        self.logger = logging.getLogger("TestPolicyIntegration")

    def test_policy_file_structure(self):
        """Test that the policy file has the correct structure."""
        print("Testing policy file structure...")

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

        # Check specific intent mappings
        intents = policy_data['intent_mappings']
        required_intents = [
            'web_search', 'code_generation', 'debugging',
            'documentation', 'testing', 'research', 'general_chat'
        ]

        for intent in required_intents:
            assert intent in intents, f"Missing intent mapping: {intent}"

        # Check agent definitions
        agents = policy_data['agent_definitions']
        required_agents = [
            'research_specialist', 'code_generation_agent',
            'debugging_agent', 'documentation_agent',
            'testing_agent', 'prince_flowers'
        ]

        for agent in required_agents:
            assert agent in agents, f"Missing agent definition: {agent}"

        print("PASS: Policy file structure is correct")

    def test_factory_functions(self):
        """Test factory functions for creating components."""
        print("Testing factory functions...")

        # Test policy-driven router factory
        router = create_policy_driven_router()
        assert router is not None
        assert isinstance(router, PolicyDrivenRouter)
        assert router.policy_framework is not None

        print("PASS: Factory functions work correctly")


async def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("POLICY-DRIVEN ROUTING SYSTEM TEST SUITE")
    print("=" * 60)

    test_results = []

    # Test PolicyFramework
    print("\n" + "=" * 40)
    print("TESTING POLICY FRAMEWORK")
    print("=" * 40)

    try:
        framework_tests = TestPolicyFramework()
        framework_tests.setup_method()

        framework_tests.test_policy_loading()
        framework_tests.test_intent_mapping_retrieval()
        framework_tests.test_agent_definition_retrieval()
        framework_tests.test_routing_decision_validation()
        framework_tests.test_cost_estimation()
        framework_tests.test_latency_estimation()
        framework_tests.test_fallback_agent_selection()
        framework_tests.test_policy_metrics()

        test_results.append(("PolicyFramework", "PASSED"))
        print("PASS: PolicyFramework tests PASSED")

    except Exception as e:
        test_results.append(("PolicyFramework", f"FAILED: {e}"))
        print(f"FAIL: PolicyFramework tests FAILED: {e}")

    # Test PolicyDrivenRouter
    print("\n" + "=" * 40)
    print("TESTING POLICY-DRIVEN ROUTER")
    print("=" * 40)

    try:
        router_tests = TestPolicyDrivenRouter()
        router_tests.setup_method()

        await router_tests.test_compliant_routing()
        await router_tests.test_cost_violation_routing()
        await router_tests.test_fallback_routing()
        await router_tests.test_metrics_collection()
        await router_tests.test_policy_version_tracking()

        test_results.append(("PolicyDrivenRouter", "PASSED"))
        print("PASS: PolicyDrivenRouter tests PASSED")

    except Exception as e:
        test_results.append(("PolicyDrivenRouter", f"FAILED: {e}"))
        print(f"FAIL: PolicyDrivenRouter tests FAILED: {e}")

    # Test PolicyIntegration
    print("\n" + "=" * 40)
    print("TESTING POLICY INTEGRATION")
    print("=" * 40)

    try:
        integration_tests = TestPolicyIntegration()
        integration_tests.setup_method()

        integration_tests.test_policy_file_structure()
        integration_tests.test_factory_functions()

        test_results.append(("PolicyIntegration", "PASSED"))
        print("PASS: PolicyIntegration tests PASSED")

    except Exception as e:
        test_results.append(("PolicyIntegration", f"FAILED: {e}"))
        print(f"FAIL: PolicyIntegration tests FAILED: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result == "PASSED")
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result == "PASSED" else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if passed == total:
        print("SUCCESS: ALL TESTS PASSED! Policy-driven routing system is working correctly.")
        return True
    else:
        print("WARNING: Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)