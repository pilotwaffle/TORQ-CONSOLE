"""
Policy Engine - Enforces governance rules for autonomous actions.

The Policy Engine is responsible for:
- Classifying action risk
- Determining allowed behavior
- Requiring approval when needed
- Recording approval decisions
- Blocking actions outside policy
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    AutonomousTask, ExecutionMode, ActionRisk,
    PolicyLevel, PolicyDecision
)


logger = logging.getLogger(__name__)


class PolicyRule:
    """
    A rule that determines whether an action is allowed.

    Rules are evaluated in order; first matching rule wins.
    """

    def __init__(
        self,
        name: str,
        condition: callable,
        policy_level: PolicyLevel,
        risk_level: ActionRisk = ActionRisk.LOW,
        reason: str = ""
    ):
        self.name = name
        self.condition = condition
        self.policy_level = policy_level
        self.risk_level = risk_level
        self.reason = reason

    def evaluate(self, task: AutonomousTask, context: Dict[str, Any]) -> Optional[PolicyDecision]:
        """
        Evaluate if this rule applies to the task.

        Returns:
            PolicyDecision if rule applies, None otherwise
        """
        try:
            if self.condition(task, context):
                return PolicyDecision(
                    allowed=self.policy_level != PolicyLevel.DENY,
                    policy_level=self.policy_level,
                    reason=self.reason,
                    requires_approval=self.policy_level == PolicyLevel.REQUIRE_APPROVAL,
                    risk_level=self.risk_level,
                    policy_rules_matched=[self.name]
                )
        except Exception as e:
            logger.error(f"Error evaluating rule {self.name}: {e}")

        return None


class PolicyEngine:
    """
    Engine for evaluating policies and making governance decisions.

    Responsibilities:
    - Evaluate tasks against policy rules
    - Determine if approval is required
    - Classify action risk levels
    - Maintain policy audit trail
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._rules = self._get_default_rules()

    def _get_default_rules(self) -> List[PolicyRule]:
        """Get default policy rules."""
        return [
            # Destructive actions - always denied
            PolicyRule(
                name="destructive_actions_denied",
                condition=lambda t, c: self._is_destructive_action(t),
                policy_level=PolicyLevel.DENY,
                risk_level=ActionRisk.CRITICAL,
                reason="Destructive actions are not allowed in autonomous mode"
            ),

            # Production write operations - require approval
            PolicyRule(
                name="prod_write_requires_approval",
                condition=lambda t, c: self._is_prod_write_operation(t, c),
                policy_level=PolicyLevel.REQUIRE_APPROVAL,
                risk_level=ActionRisk.HIGH,
                reason="Production write operations require approval"
            ),

            # External actions with side effects - require approval
            PolicyRule(
                name="external_side_effects_require_approval",
                condition=lambda t, c: self._has_external_side_effects(t),
                policy_level=PolicyLevel.REQUIRE_APPROVAL,
                risk_level=ActionRisk.HIGH,
                reason="Actions with external side effects require approval"
            ),

            # Execute mode - require approval unless observe
            PolicyRule(
                name="execute_mode_requires_approval",
                condition=lambda t, c: t.execution_mode == ExecutionMode.EXECUTE,
                policy_level=PolicyLevel.REQUIRE_APPROVAL,
                risk_level=ActionRisk.MEDIUM,
                reason="Execute mode actions require approval"
            ),

            # Prepare mode - allow with log
            PolicyRule(
                name="prepare_mode_allow_with_log",
                condition=lambda t, c: t.execution_mode == ExecutionMode.PREPARE,
                policy_level=PolicyLevel.ALLOW_WITH_LOG,
                risk_level=ActionRisk.LOW,
                reason="Prepare mode is allowed with logging"
            ),

            # Observe mode - auto-allow
            PolicyRule(
                name="observe_mode_auto_allow",
                condition=lambda t, c: t.execution_mode == ExecutionMode.OBSERVE,
                policy_level=PolicyLevel.ALLOW,
                risk_level=ActionRisk.LOW,
                reason="Observe mode is auto-allowed"
            ),

            # Default fallback - allow with log
            PolicyRule(
                name="default_allow_with_log",
                condition=lambda t, c: True,  # Always matches as fallback
                policy_level=PolicyLevel.ALLOW_WITH_LOG,
                risk_level=ActionRisk.LOW,
                reason="Default policy: allow with logging"
            ),
        ]

    def evaluate(
        self,
        task: AutonomousTask,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyDecision:
        """
        Evaluate a task against policy rules.

        Args:
            task: The autonomous task to evaluate
            context: Additional context (environment, workspace, etc.)

        Returns:
            PolicyDecision with the governance result
        """
        context = context or {}

        self.logger.debug(f"Evaluating policy for task {task.task_id}")

        # Evaluate rules in order
        for rule in self._rules:
            decision = rule.evaluate(task, context)
            if decision:
                self.logger.info(
                    f"Policy rule '{rule.name}' matched for task {task.task_id}: "
                    f"{decision.policy_level.value}"
                )
                return decision

        # Should never reach here due to default rule
        return PolicyDecision(
            allowed=True,
            policy_level=PolicyLevel.ALLOW_WITH_LOG,
            reason="No policy rules matched"
        )

    def _is_destructive_action(self, task: AutonomousTask) -> bool:
        """Check if task is a destructive action."""
        destructive_keywords = [
            "delete", "destroy", "drop", "remove", "truncate",
            "overwrite", "format", "erase", "purge"
        ]

        prompt_lower = (task.prompt_template or "").lower()
        name_lower = task.name.lower()

        for keyword in destructive_keywords:
            if keyword in prompt_lower or keyword in name_lower:
                return True

        return False

    def _is_prod_write_operation(self, task: AutonomousTask, context: Dict[str, Any]) -> bool:
        """Check if task is a production write operation."""
        # Check environment
        environment = context.get("environment", task.environment)
        if environment == "production":
            # Check if it's a write operation
            write_keywords = ["create", "update", "modify", "change", "write"]
            prompt_lower = (task.prompt_template or "").lower()

            for keyword in write_keywords:
                if keyword in prompt_lower:
                    return True

        return False

    def _has_external_side_effects(self, task: AutonomousTask) -> bool:
        """Check if task has external side effects."""
        side_effect_keywords = [
            "send", "email", "notify", "deploy", "publish",
            "post", "tweet", "message", "alert", "call"
        ]

        prompt_lower = (task.prompt_template or "").lower()
        name_lower = task.name.lower()

        for keyword in side_effect_keywords:
            if keyword in prompt_lower or keyword in name_lower:
                return True

        return False

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a custom policy rule."""
        # Insert before default rule
        default_idx = next(
            (i for i, r in enumerate(self._rules) if r.name == "default_allow_with_log"),
            len(self._rules)
        )
        self._rules.insert(default_idx, rule)
        self.logger.info(f"Added policy rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a policy rule by name."""
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                self._rules.pop(i)
                self.logger.info(f"Removed policy rule: {rule_name}")
                return True
        return False

    def list_rules(self) -> List[str]:
        """List all policy rule names."""
        return [rule.name for rule in self._rules]


# Singleton instance
_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """Get the singleton policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
