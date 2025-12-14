"""
Policy-Driven Routing Framework for TORQ Console

Provides policy loading, validation, and enforcement for routing decisions.
Ensures all routing decisions are policy-driven and versioned with full telemetry.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

from ..core.telemetry.event import (
    TorqEvent,
    TorqEventType,
    EventSeverity,
    RoutingDecisionEvent,
    RoutingStrategy,
    create_routing_decision_event
)


class PolicyError(Exception):
    """Policy-related errors."""
    pass


class PolicyComplianceStatus(str, Enum):
    """Policy compliance status."""
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    ESCALATION = "escalation"
    FALLBACK = "fallback"


@dataclass
class IntentMapping:
    """Intent to agent mapping configuration."""
    primary_agent: str
    fallback_agents: List[str]
    confidence_threshold: float
    max_cost: float
    max_latency: int
    capabilities_required: List[str]


@dataclass
class AgentDefinition:
    """Agent definition with constraints."""
    capabilities: List[str]
    cost_per_token: float
    max_concurrent_requests: int
    preferred_models: List[str]
    timeout_ms: int


@dataclass
class EscalationRule:
    """Escalation rule configuration."""
    condition: str
    action: str
    fallback_order: List[str] or str
    max_retries: Optional[int] = None
    final_fallback: Optional[str] = None


@dataclass
class RoutingPolicy:
    """Complete routing policy configuration."""
    metadata: Dict[str, Any]
    defaults: Dict[str, Any]
    intent_mappings: Dict[str, IntentMapping]
    agent_definitions: Dict[str, AgentDefinition]
    escalation_rules: Dict[str, EscalationRule]
    performance_constraints: Dict[str, Any]
    monitoring: Dict[str, Any]
    compliance: Dict[str, Any]


class PolicyFramework:
    """
    Policy-driven routing framework.

    Loads, validates, and enforces routing policies with full telemetry integration.
    """

    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize policy framework.

        Args:
            policy_path: Path to policy YAML file (defaults to policies/routing/v1.yaml)
        """
        self.logger = logging.getLogger("TORQ.Agents.PolicyFramework")

        # Set default policy path
        if policy_path is None:
            # Get the directory containing this file
            current_dir = Path(__file__).parent
            # Navigate to policies/routing/v1.yaml
            policy_path = current_dir.parent.parent / "policies" / "routing" / "v1.yaml"

        self.policy_path = Path(policy_path)
        self.current_policy: Optional[RoutingPolicy] = None
        self.policy_version: Optional[str] = None

        # Load and validate policy
        self._load_policy()

        self.logger.info(f"Policy Framework initialized with policy v{self.policy_version}")

    def _load_policy(self) -> None:
        """Load and validate the routing policy."""
        try:
            if not self.policy_path.exists():
                raise PolicyError(f"Policy file not found: {self.policy_path}")

            # Load YAML policy
            with open(self.policy_path, 'r', encoding='utf-8') as f:
                policy_data = yaml.safe_load(f)

            # Validate policy structure
            self._validate_policy_structure(policy_data)

            # Parse policy into structured objects
            self.current_policy = self._parse_policy(policy_data)
            self.policy_version = policy_data['metadata']['version']

            self.logger.info(f"Successfully loaded policy v{self.policy_version}: {self.current_policy.metadata['name']}")

        except Exception as e:
            self.logger.error(f"Failed to load policy: {e}", exc_info=True)
            raise PolicyError(f"Policy loading failed: {e}")

    def _validate_policy_structure(self, policy_data: Dict[str, Any]) -> None:
        """Validate the policy YAML structure."""
        required_sections = [
            'metadata', 'defaults', 'intent_mappings',
            'agent_definitions', 'escalation_rules'
        ]

        for section in required_sections:
            if section not in policy_data:
                raise PolicyError(f"Missing required policy section: {section}")

        # Validate metadata
        metadata = policy_data['metadata']
        required_metadata = ['name', 'version', 'description']
        for field in required_metadata:
            if field not in metadata:
                raise PolicyError(f"Missing required metadata field: {field}")

        # Validate intent mappings
        intent_mappings = policy_data['intent_mappings']
        if not intent_mappings:
            raise PolicyError("Intent mappings cannot be empty")

        for intent, mapping in intent_mappings.items():
            required_mapping_fields = [
                'primary_agent', 'fallback_agents', 'confidence_threshold',
                'max_cost', 'max_latency', 'capabilities_required'
            ]
            for field in required_mapping_fields:
                if field not in mapping:
                    raise PolicyError(f"Intent '{intent}' missing field: {field}")

        # Validate agent definitions
        agent_definitions = policy_data['agent_definitions']
        for agent, definition in agent_definitions.items():
            required_agent_fields = [
                'capabilities', 'cost_per_token', 'max_concurrent_requests',
                'preferred_models', 'timeout_ms'
            ]
            for field in required_agent_fields:
                if field not in definition:
                    raise PolicyError(f"Agent '{agent}' missing field: {field}")

        self.logger.debug("Policy structure validation passed")

    def _parse_policy(self, policy_data: Dict[str, Any]) -> RoutingPolicy:
        """Parse raw policy data into structured objects."""
        # Parse intent mappings
        intent_mappings = {}
        for intent, mapping in policy_data['intent_mappings'].items():
            intent_mappings[intent] = IntentMapping(
                primary_agent=mapping['primary_agent'],
                fallback_agents=mapping['fallback_agents'],
                confidence_threshold=mapping['confidence_threshold'],
                max_cost=mapping['max_cost'],
                max_latency=mapping['max_latency'],
                capabilities_required=mapping['capabilities_required']
            )

        # Parse agent definitions
        agent_definitions = {}
        for agent, definition in policy_data['agent_definitions'].items():
            agent_definitions[agent] = AgentDefinition(
                capabilities=definition['capabilities'],
                cost_per_token=definition['cost_per_token'],
                max_concurrent_requests=definition['max_concurrent_requests'],
                preferred_models=definition['preferred_models'],
                timeout_ms=definition['timeout_ms']
            )

        # Parse escalation rules
        escalation_rules = {}
        for rule_name, rule in policy_data['escalation_rules'].items():
            escalation_rules[rule_name] = EscalationRule(
                condition=rule['condition'],
                action=rule['action'],
                fallback_order=rule['fallback_order'],
                max_retries=rule.get('max_retries'),
                final_fallback=rule.get('final_fallback')
            )

        return RoutingPolicy(
            metadata=policy_data['metadata'],
            defaults=policy_data['defaults'],
            intent_mappings=intent_mappings,
            agent_definitions=agent_definitions,
            escalation_rules=escalation_rules,
            performance_constraints=policy_data.get('performance_constraints', {}),
            monitoring=policy_data.get('monitoring', {}),
            compliance=policy_data.get('compliance', {})
        )

    def get_policy_version(self) -> str:
        """Get current policy version."""
        if not self.policy_version:
            raise PolicyError("No policy loaded")
        return self.policy_version

    def get_intent_mapping(self, intent: str) -> Optional[IntentMapping]:
        """Get intent mapping for a specific intent."""
        if not self.current_policy:
            raise PolicyError("No policy loaded")
        return self.current_policy.intent_mappings.get(intent)

    def get_agent_definition(self, agent_name: str) -> Optional[AgentDefinition]:
        """Get agent definition."""
        if not self.current_policy:
            raise PolicyError("No policy loaded")
        return self.current_policy.agent_definitions.get(agent_name)

    def validate_routing_decision(
        self,
        intent: str,
        selected_agent: str,
        confidence_score: float,
        estimated_cost: float,
        estimated_latency: int
    ) -> Tuple[PolicyComplianceStatus, List[str]]:
        """
        Validate a routing decision against policy.

        Args:
            intent: Classified user intent
            selected_agent: Agent selected for routing
            confidence_score: Confidence in routing decision
            estimated_cost: Estimated cost in USD
            estimated_latency: Estimated latency in ms

        Returns:
            Tuple of (compliance_status, violations_list)
        """
        violations = []
        status = PolicyComplianceStatus.COMPLIANT

        # Get intent mapping
        intent_mapping = self.get_intent_mapping(intent)
        if not intent_mapping:
            violations.append(f"No intent mapping found for: {intent}")
            status = PolicyComplianceStatus.VIOLATION
            return status, violations

        # Check primary agent match
        if selected_agent != intent_mapping.primary_agent:
            # Check if selected agent is in fallback list
            if selected_agent not in intent_mapping.fallback_agents:
                violations.append(f"Selected agent {selected_agent} not in policy for intent {intent}")
                status = PolicyComplianceStatus.VIOLATION
            else:
                status = PolicyComplianceStatus.FALLBACK

        # Check confidence threshold
        if confidence_score < intent_mapping.confidence_threshold:
            violations.append(f"Confidence {confidence_score} below threshold {intent_mapping.confidence_threshold}")
            if status == PolicyComplianceStatus.COMPLIANT:
                status = PolicyComplianceStatus.ESCALATION

        # Check cost budget
        if estimated_cost > intent_mapping.max_cost:
            violations.append(f"Cost ${estimated_cost:.4f} exceeds budget ${intent_mapping.max_cost:.4f}")
            if status == PolicyComplianceStatus.COMPLIANT:
                status = PolicyComplianceStatus.ESCALATION

        # Check latency budget
        if estimated_latency > intent_mapping.max_latency:
            violations.append(f"Latency {estimated_latency}ms exceeds budget {intent_mapping.max_latency}ms")
            if status == PolicyComplianceStatus.COMPLIANT:
                status = PolicyComplianceStatus.ESCALATION

        return status, violations

    def get_fallback_agents(
        self,
        intent: str,
        primary_agent: str,
        violations: List[str]
    ) -> List[str]:
        """
        Get appropriate fallback agents based on policy violations.

        Args:
            intent: Original intent
            primary_agent: Agent that was selected
            violations: List of policy violations

        Returns:
            List of fallback agents in priority order
        """
        intent_mapping = self.get_intent_mapping(intent)
        if not intent_mapping:
            return ['prince_flowers']  # Ultimate fallback

        fallback_agents = []

        # Check violation types and determine escalation path
        violation_str = ' '.join(violations).lower()

        # Cost-based escalation
        if 'cost' in violation_str:
            cost_escalation = self.current_policy.escalation_rules.get('cost_over_threshold')
            if cost_escalation:
                fallback_agents.extend(cost_escalation.fallback_order)

        # Latency-based escalation
        elif 'latency' in violation_str:
            latency_escalation = self.current_policy.escalation_rules.get('latency_over_threshold')
            if latency_escalation:
                fallback_agents.extend(latency_escalation.fallback_order)

        # Confidence-based escalation
        elif 'confidence' in violation_str:
            confidence_escalation = self.current_policy.escalation_rules.get('low_confidence')
            if confidence_escalation:
                fallback_agents.extend(confidence_escalation.fallback_order)

        # Agent unavailable or other violations
        else:
            # Use intent mapping fallbacks
            fallback_agents.extend(intent_mapping.fallback_agents)

        # Remove primary agent if it's in the list
        fallback_agents = [agent for agent in fallback_agents if agent != primary_agent]

        # Ensure prince_flowers is always included as final fallback
        if 'prince_flowers' not in fallback_agents:
            fallback_agents.append('prince_flowers')

        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for agent in fallback_agents:
            if agent not in seen:
                seen.add(agent)
                unique_fallbacks.append(agent)

        return unique_fallbacks[:3]  # Limit to 3 fallbacks

    def estimate_cost(
        self,
        agent_name: str,
        estimated_tokens: int,
        complexity_multiplier: float = 1.0
    ) -> float:
        """
        Estimate cost for routing to an agent.

        Args:
            agent_name: Target agent
            estimated_tokens: Estimated token count
            complexity_multiplier: Complexity-based cost multiplier

        Returns:
            Estimated cost in USD
        """
        agent_def = self.get_agent_definition(agent_name)
        if not agent_def:
            return 0.05  # Default cost estimate

        base_cost = estimated_tokens * agent_def.cost_per_token
        return base_cost * complexity_multiplier

    def estimate_latency(
        self,
        agent_name: str,
        query_complexity: str = "moderate"
    ) -> int:
        """
        Estimate latency for routing to an agent.

        Args:
            agent_name: Target agent
            query_complexity: Complexity level (simple, moderate, complex)

        Returns:
            Estimated latency in milliseconds
        """
        agent_def = self.get_agent_definition(agent_name)
        if not agent_def:
            return 5000  # Default latency estimate

        base_latency = agent_def.timeout_ms * 0.5  # Use 50% of timeout as estimate

        # Apply complexity multiplier
        complexity_multipliers = {
            "simple": 0.5,
            "moderate": 1.0,
            "complex": 2.0,
            "very_complex": 3.0
        }

        multiplier = complexity_multipliers.get(query_complexity, 1.0)
        return int(base_latency * multiplier)

    def log_routing_decision(
        self,
        session_id: str,
        query: str,
        intent: str,
        selected_agent: str,
        confidence_score: float,
        estimated_cost: float,
        estimated_latency: int,
        routing_time_ms: int,
        candidate_agents: List[str],
        agent_scores: Dict[str, float],
        compliance_status: PolicyComplianceStatus,
        violations: List[str],
        fallback_path: List[str] = None
    ) -> RoutingDecisionEvent:
        """
        Log routing decision with policy compliance information.

        Args:
            session_id: Session identifier
            query: User query
            intent: Classified intent
            selected_agent: Agent selected for routing
            confidence_score: Confidence in decision
            estimated_cost: Estimated cost
            estimated_latency: Estimated latency
            routing_time_ms: Time taken for routing decision
            candidate_agents: All considered agents
            agent_scores: Scores for each candidate
            compliance_status: Policy compliance status
            violations: Any policy violations
            fallback_path: Fallback agents used (if any)

        Returns:
            RoutingDecisionEvent with full policy context
        """
        # Create routing decision event
        event = create_routing_decision_event(
            session_id=session_id,
            query=query,
            selected_agent=selected_agent,
            routing_strategy=RoutingStrategy.INTENT_BASED,
            confidence_score=confidence_score,
            routing_time_ms=routing_time_ms
        )

        # Add policy-specific information
        event.query_type = intent
        event.user_intent = intent
        event.candidate_agents = candidate_agents
        event.agent_scores = agent_scores
        event.expected_performance = {
            "estimated_cost_usd": estimated_cost,
            "estimated_latency_ms": estimated_latency
        }
        event.cost_estimate_usd = estimated_cost

        # Add policy compliance information
        event.data.update({
            "policy_version": self.policy_version,
            "policy_compliance_status": compliance_status.value,
            "policy_violations": violations,
            "fallback_path": fallback_path or [],
            "primary_agent_violation": selected_agent != self.get_intent_mapping(intent).primary_agent if self.get_intent_mapping(intent) else False
        })

        # Add tags for policy tracking
        event.tags.update({
            "policy_version": self.policy_version,
            "intent": intent,
            "compliance_status": compliance_status.value,
            "escalation_triggered": compliance_status in [PolicyComplianceStatus.ESCALATION, PolicyComplianceStatus.FALLBACK]
        })

        self.logger.info(
            f"Routing decision logged - Policy: {self.policy_version}, "
            f"Agent: {selected_agent}, Compliance: {compliance_status.value}, "
            f"Violations: {len(violations)}"
        )

        return event

    def reload_policy(self) -> None:
        """Reload the current policy from disk."""
        self.logger.info("Reloading routing policy...")
        self._load_policy()
        self.logger.info(f"Policy reloaded successfully - Version: {self.policy_version}")

    def get_policy_metrics(self) -> Dict[str, Any]:
        """Get policy metrics and status."""
        if not self.current_policy:
            return {"error": "No policy loaded"}

        return {
            "policy_version": self.policy_version,
            "policy_name": self.current_policy.metadata["name"],
            "policy_environment": self.current_policy.metadata.get("environment", "unknown"),
            "total_intents": len(self.current_policy.intent_mappings),
            "total_agents": len(self.current_policy.agent_definitions),
            "total_escalation_rules": len(self.current_policy.escalation_rules),
            "policy_created_date": self.current_policy.metadata.get("created_date"),
            "policy_author": self.current_policy.metadata.get("author"),
            "compliance_requirements": {
                "require_policy_version_in_telemetry": self.current_policy.compliance.get("require_policy_version_in_telemetry", False),
                "require_intent_classification": self.current_policy.compliance.get("require_intent_classification", False),
                "require_cost_estimation": self.current_policy.compliance.get("require_cost_estimation", False),
                "require_latency_estimation": self.current_policy.compliance.get("require_latency_estimation", False),
                "require_fallback_logging": self.current_policy.compliance.get("require_fallback_logging", False)
            },
            "monitoring_config": {
                "log_policy_version": self.current_policy.monitoring.get("log_policy_version", False),
                "log_candidate_scoring": self.current_policy.monitoring.get("log_candidate_scoring", False),
                "log_fallback_paths": self.current_policy.monitoring.get("log_fallback_paths", False),
                "log_performance_metrics": self.current_policy.monitoring.get("log_performance_metrics", False)
            }
        }


# Global policy instance
_policy_framework: Optional[PolicyFramework] = None


def get_policy_framework() -> PolicyFramework:
    """Get the global policy framework instance."""
    global _policy_framework
    if _policy_framework is None:
        _policy_framework = PolicyFramework()
    return _policy_framework


def reload_policy() -> None:
    """Reload the global policy framework."""
    global _policy_framework
    if _policy_framework is not None:
        _policy_framework.reload_policy()
    else:
        _policy_framework = PolicyFramework()