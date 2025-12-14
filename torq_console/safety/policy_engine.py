"""
Policy Engine for Tool Safety

Enforces deny-by-default rules with comprehensive policy evaluation
"""

import os
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging

from .models import (
    PolicyConfig, ToolRequest, PolicyDecision, Decision,
    RiskLevel, OperationType, SecurityContext
)

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Policy engine for tool safety enforcement"""

    def __init__(self, policies_dir: Optional[str] = None):
        """
        Initialize policy engine

        Args:
            policies_dir: Directory containing tool policy YAML files
        """
        self.policies_dir = Path(policies_dir) if policies_dir else None
        self.policies: Dict[str, PolicyConfig] = {}
        self.global_forbidden_paths = {
            "/etc/passwd", "/etc/shadow", "/etc/hosts",
            "C:\\Windows\\System32\\config",
            "C:\\boot.ini", "/boot/grub/",
            "/proc/", "/sys/", "/dev/",
            "~/.ssh/", "~/.aws/", "~/.gnupg/",
        }
        self.global_forbidden_operations = {
            OperationType.SYSTEM,
            OperationType.EXECUTE,
        }

        # Dangerous patterns to block
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'del\s+.*\*.*',
            r'format\s+c:',
            r'fdisk\s+',
            r'mkfs\s+',
            r'sudo\s+rm',
            r'chmod\s+777',
            r'chown\s+root',
            r'wget\s+.*\|.*sh',
            r'curl\s+.*\|.*bash',
            r'eval\s*\$',
            r'\$\([^)]*\)',
            r'`[^`]*`',
        ]

        # Load policies
        self._load_policies()

    def _load_policies(self):
        """Load all tool policies from directory"""
        if not self.policies_dir or not self.policies_dir.exists():
            logger.warning(f"Policies directory not found: {self.policies_dir}")
            return

        for policy_file in self.policies_dir.glob("*.yaml"):
            try:
                policy = self._load_policy_file(policy_file)
                if policy:
                    self.policies[policy.tool_name] = policy
                    logger.info(f"Loaded policy for tool: {policy.tool_name}")
            except Exception as e:
                logger.error(f"Failed to load policy {policy_file}: {e}")

    def _load_policy_file(self, policy_file: Path) -> Optional[PolicyConfig]:
        """Load a single policy file"""
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty policy file: {policy_file}")
                return None

            return PolicyConfig(**data)

        except Exception as e:
            logger.error(f"Error loading policy file {policy_file}: {e}")
            return None

    def evaluate_request(
        self,
        request: ToolRequest,
        security_context: Optional[SecurityContext] = None
    ) -> PolicyDecision:
        """
        Evaluate a tool request against policies

        Args:
            request: Tool request to evaluate
            security_context: Security context for the request

        Returns:
            PolicyDecision with the evaluation result
        """
        # Get policy for the tool
        policy = self.policies.get(request.tool_name)

        if not policy:
            # Default deny for unknown tools
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=RiskLevel.HIGH,
                reason=f"No policy found for tool: {request.tool_name}",
                policy_name="default_deny",
                denied_operations=[request.operation]
            )

        # Check for prompt injection patterns
        injection_detected = self._check_prompt_injection(request.parameters)
        if injection_detected:
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=RiskLevel.CRITICAL,
                reason=f"Prompt injection detected: {injection_detected}",
                policy_name="prompt_injection_protection",
                denied_operations=[request.operation]
            )

        # Check global forbidden paths
        if request.target_path and self._is_forbidden_path(request.target_path):
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=RiskLevel.CRITICAL,
                reason=f"Access to forbidden path: {request.target_path}",
                policy_name="global_path_protection",
                denied_operations=[request.operation]
            )

        # Check operation permissions
        if request.operation in self.global_forbidden_operations:
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=RiskLevel.HIGH,
                reason=f"Operation globally forbidden: {request.operation}",
                policy_name="global_operation_protection",
                denied_operations=[request.operation]
            )

        # Check tool-specific forbidden operations
        if request.operation in policy.forbidden_operations:
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=policy.risk_level,
                reason=f"Operation forbidden by tool policy: {request.operation}",
                policy_name=policy.tool_name,
                denied_operations=[request.operation]
            )

        # Check allowed operations
        if policy.allowed_operations and request.operation not in policy.allowed_operations:
            return PolicyDecision(
                decision=Decision.DENY,
                risk_level=RiskLevel.MEDIUM,
                reason=f"Operation not in allowed list: {request.operation}",
                policy_name=policy.tool_name,
                allowed_operations=policy.allowed_operations,
                denied_operations=[request.operation]
            )

        # Check path permissions
        if request.target_path:
            path_decision = self._check_path_permissions(request.target_path, policy)
            if path_decision.decision != Decision.ALLOW:
                return path_decision

        # Check user context requirements
        if policy.require_user_context and not security_context:
            return PolicyDecision(
                decision=Decision.REQUIRE_CONFIRMATION,
                risk_level=RiskLevel.MEDIUM,
                reason="Tool requires user context for security validation",
                policy_name=policy.tool_name
            )

        # Determine if confirmation is required
        if policy.requires_confirmation or policy.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            confirmation_msg = self._generate_confirmation_message(request, policy)
            return PolicyDecision(
                decision=Decision.REQUIRE_CONFIRMATION,
                risk_level=policy.risk_level,
                reason="High-risk operation requires user confirmation",
                policy_name=policy.tool_name,
                confirmation_required=True,
                confirmation_message=confirmation_msg,
                allowed_operations=policy.allowed_operations
            )

        # Allow the operation
        return PolicyDecision(
            decision=Decision.ALLOW,
            risk_level=policy.risk_level,
            reason="Operation allowed by policy",
            policy_name=policy.tool_name,
            allowed_operations=policy.allowed_operations
        )

    def _check_prompt_injection(self, parameters: Dict[str, Any]) -> Optional[str]:
        """Check for prompt injection patterns in parameters"""
        if not isinstance(parameters, dict):
            return None

        # Convert all parameters to strings and check for dangerous patterns
        for key, value in parameters.items():
            if isinstance(value, str):
                for pattern in self.dangerous_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return f"Dangerous pattern detected in parameter '{key}': {pattern}"

            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, str):
                        for pattern in self.dangerous_patterns:
                            if re.search(pattern, item, re.IGNORECASE):
                                return f"Dangerous pattern detected in list '{key}': {pattern}"

            elif isinstance(value, dict):
                # Recursively check nested dictionaries
                nested_result = self._check_prompt_injection(value)
                if nested_result:
                    return f"Nested parameter injection: {nested_result}"

        return None

    def _is_forbidden_path(self, path: str) -> bool:
        """Check if path is in global forbidden list"""
        normalized_path = str(path).replace('\\', '/')

        for forbidden in self.global_forbidden_paths:
            forbidden_normalized = forbidden.replace('\\', '/')
            if normalized_path.startswith(forbidden_normalized):
                return True

        return False

    def _check_path_permissions(self, path: str, policy: PolicyConfig) -> PolicyDecision:
        """Check if path access is allowed by policy"""
        normalized_path = str(path).replace('\\', '/')

        # Check forbidden paths first
        for forbidden in policy.forbidden_paths:
            if normalized_path.startswith(forbidden):
                return PolicyDecision(
                    decision=Decision.DENY,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Path forbidden by policy: {path}",
                    policy_name=policy.tool_name,
                    denied_operations=[OperationType.FILE_SYSTEM]
                )

        # If no allowed paths specified, allow any (except forbidden)
        if not policy.allowed_paths:
            return PolicyDecision(
                decision=Decision.ALLOW,
                risk_level=policy.risk_level,
                reason="Path access allowed (no restrictions in policy)",
                policy_name=policy.tool_name
            )

        # Check if path is in allowed paths
        for allowed in policy.allowed_paths:
            if normalized_path.startswith(allowed):
                return PolicyDecision(
                    decision=Decision.ALLOW,
                    risk_level=policy.risk_level,
                    reason=f"Path access allowed: {path}",
                    policy_name=policy.tool_name
                )

        # Path not in allowed list
        return PolicyDecision(
            decision=Decision.DENY,
            risk_level=RiskLevel.MEDIUM,
            reason=f"Path not in allowed list: {path}",
            policy_name=policy.tool_name,
            denied_operations=[OperationType.FILE_SYSTEM]
        )

    def _generate_confirmation_message(self, request: ToolRequest, policy: PolicyConfig) -> str:
        """Generate confirmation message for high-risk operations"""
        risk_descriptions = {
            RiskLevel.LOW: "This is a low-risk operation.",
            RiskLevel.MEDIUM: "This operation has medium risk.",
            RiskLevel.HIGH: "⚠️ This is a HIGH-RISK operation that could have significant impact.",
            RiskLevel.CRITICAL: "🚨 This is a CRITICAL operation that could cause serious damage."
        }

        msg = f"{risk_descriptions[policy.risk_level]}\n\n"
        msg += f"Tool: {request.tool_name}\n"
        msg += f"Operation: {request.operation.value}\n"

        if request.target_path:
            msg += f"Target: {request.target_path}\n"

        if request.parameters:
            msg += "Parameters:\n"
            for key, value in request.parameters.items():
                # Truncate long values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                msg += f"  {key}: {value_str}\n"

        msg += "\nAre you sure you want to proceed?"

        return msg

    def get_policy(self, tool_name: str) -> Optional[PolicyConfig]:
        """Get policy for a specific tool"""
        return self.policies.get(tool_name)

    def list_policies(self) -> List[str]:
        """List all available tool policies"""
        return list(self.policies.keys())

    def reload_policies(self):
        """Reload all policies from disk"""
        self.policies.clear()
        self._load_policies()
        logger.info("Policies reloaded")

    def validate_policy(self, policy_data: Dict[str, Any]) -> List[str]:
        """
        Validate policy data structure

        Args:
            policy_data: Policy data to validate

        Returns:
            List of validation errors
        """
        errors = []

        required_fields = ['tool_name']
        for field in required_fields:
            if field not in policy_data:
                errors.append(f"Missing required field: {field}")

        # Validate risk level
        if 'risk_level' in policy_data:
            valid_risks = [r.value for r in RiskLevel]
            if policy_data['risk_level'] not in valid_risks:
                errors.append(f"Invalid risk_level: {policy_data['risk_level']}")

        # Validate operations
        operation_fields = ['allowed_operations', 'forbidden_operations']
        for field in operation_fields:
            if field in policy_data:
                valid_ops = [op.value for op in OperationType]
                for op in policy_data[field]:
                    if op not in valid_ops:
                        errors.append(f"Invalid operation in {field}: {op}")

        return errors