"""
Main Safety Manager

Integrates all safety components into a comprehensive tool safety system
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

from .models import (
    ToolRequest, PolicyDecision, Decision, RiskLevel,
    SecurityContext, SandboxConfig, ConfirmationRequest
)
from .policy_engine import PolicyEngine
from .sandbox import SandboxManager
from .confirmation import ConfirmationManager
from .audit_logger import AuditLogger
from .rate_limiter import RateLimiter
from .security import SecurityManager

logger = logging.getLogger(__name__)


class SafetyManager:
    """
    Comprehensive tool safety manager

    Integrates policy enforcement, sandboxing, confirmation workflows,
    rate limiting, audit logging, and security protections.
    """

    def __init__(
        self,
        policies_dir: Optional[str] = None,
        audit_log_dir: Optional[str] = None,
        sandbox_config: Optional[SandboxConfig] = None
    ):
        """
        Initialize safety manager

        Args:
            policies_dir: Directory containing tool policies
            audit_log_dir: Directory for audit logs
            sandbox_config: Default sandbox configuration
        """
        # Initialize all safety components
        self.policy_engine = PolicyEngine(policies_dir)
        self.sandbox_manager = SandboxManager(sandbox_config)
        self.confirmation_manager = ConfirmationManager()
        self.audit_logger = AuditLogger(audit_log_dir)
        self.rate_limiter = RateLimiter()
        self.security_manager = SecurityManager()

        # Safety statistics
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "confirmations_requested": 0,
            "security_violations": 0,
            "sandboxes_used": 0
        }

        # Safety configuration
        self.config = {
            "enable_sandboxing": True,
            "enable_confirmations": True,
            "enable_rate_limiting": True,
            "enable_audit_logging": True,
            "strict_mode": False,  # When True, denies on uncertainty
            "default_confirmation_timeout": 300,
            "max_execution_time": 600,  # 10 minutes
        }

        logger.info("Safety Manager initialized with all components")

    def evaluate_and_execute_tool(
        self,
        request: ToolRequest,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[SecurityContext] = None,
        bypass_confirmation: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive tool request evaluation and execution

        Args:
            request: Tool request to process
            user_id: User identifier
            session_id: Session identifier
            context: Security context
            bypass_confirmation: Skip confirmation requirements

        Returns:
            Execution result with safety information
        """
        start_time = time.time()
        execution_id = f"exec_{request.request_id}_{int(start_time)}"

        try:
            self.stats["total_requests"] += 1

            # Step 1: Security validation
            security_result = self._validate_security(request, context)
            if not security_result["valid"]:
                return self._create_denial_response(
                    execution_id, request, "Security validation failed",
                    security_result["threats"], RiskLevel.CRITICAL, user_id, session_id
                )

            # Step 2: Policy evaluation
            policy_decision = self.policy_engine.evaluate_request(request, context)
            self.audit_logger.log_tool_request(
                request, policy_decision, user_id, session_id
            )

            # Step 3: Rate limiting check
            if self.config["enable_rate_limiting"]:
                is_allowed, rate_info = self.rate_limiter.check_rate_limit(
                    request, user_id, session_id
                )
                if not is_allowed:
                    return self._create_denial_response(
                        execution_id, request, "Rate limit exceeded",
                        [f"Rate limit: {rate_info}"], RiskLevel.MEDIUM,
                        user_id, session_id, rate_limit_info=rate_info.dict()
                    )

            # Step 4: Handle policy decisions
            if policy_decision.decision == Decision.DENY:
                self.stats["denied_requests"] += 1
                return self._create_denial_response(
                    execution_id, request, policy_decision.reason,
                    [policy_decision.reason], policy_decision.risk_level,
                    user_id, session_id
                )

            elif policy_decision.decision == Decision.REQUIRE_CONFIRMATION:
                if not bypass_confirmation and self.config["enable_confirmations"]:
                    return self._handle_confirmation_required(
                        execution_id, request, policy_decision, user_id, session_id
                    )

            # Step 5: Execute tool with sandboxing
            result = self._execute_tool_safely(
                execution_id, request, policy_decision, user_id, session_id
            )

            # Step 6: Update statistics
            if result.get("success", False):
                self.stats["allowed_requests"] += 1

            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            result["execution_time_ms"] = execution_time

            # Log completion
            self.audit_logger.log_tool_request(
                request, policy_decision, user_id, session_id,
                execution_time_ms=execution_time,
                error_message=result.get("error"),
                additional_data={"execution_id": execution_id}
            )

            return result

        except Exception as e:
            logger.error(f"Error in safety evaluation: {e}")
            self.audit_logger.log_security_violation(
                "safety_system_error", RiskLevel.HIGH, request.tool_name,
                f"Safety system error: {str(e)}", user_id, session_id
            )

            return {
                "success": False,
                "error": f"Safety system error: {str(e)}",
                "execution_id": execution_id,
                "risk_level": RiskLevel.HIGH.value,
                "denied_reason": "Internal safety system error"
            }

    def _validate_security(
        self,
        request: ToolRequest,
        context: Optional[SecurityContext]
    ) -> Dict[str, Any]:
        """Validate request for security threats"""
        threats = []
        max_risk = RiskLevel.LOW

        # Validate each parameter
        for param_name, param_value in request.parameters.items():
            is_valid, param_threats, risk_level = self.security_manager.validate_input(
                param_value, param_name
            )
            if not is_valid:
                threats.extend([f"{param_name}: {threat}" for threat in param_threats])
                max_risk = max(max_risk, risk_level, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        # Check for prompt injection
        prompt_text = " ".join(str(v) for v in request.parameters.values())
        has_injection, injection_indicators = self.security_manager.detect_prompt_injection(prompt_text)
        if has_injection:
            threats.extend(injection_indicators)
            max_risk = RiskLevel.CRITICAL

        # Assess overall request risk
        assessed_risk = self.security_manager.assess_request_risk(request, context)
        max_risk = max(max_risk, assessed_risk, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))

        return {
            "valid": len(threats) == 0,
            "threats": threats,
            "risk_level": max_risk
        }

    def _handle_confirmation_required(
        self,
        execution_id: str,
        request: ToolRequest,
        policy_decision: PolicyDecision,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle confirmation requirement"""
        self.stats["confirmations_requested"] += 1

        # Request confirmation
        confirmation = self.confirmation_manager.request_confirmation(
            request,
            policy_decision.risk_level,
            policy_decision.confirmation_message or "High-risk operation requires confirmation",
            details={
                "tool_name": request.tool_name,
                "operation": request.operation.value,
                "parameters": request.parameters,
                "risk_level": policy_decision.risk_level.value
            },
            timeout=self.config["default_confirmation_timeout"],
            user_id=user_id
        )

        return {
            "success": False,
            "requires_confirmation": True,
            "confirmation_id": confirmation.request_id,
            "confirmation_message": confirmation.message,
            "execution_id": execution_id,
            "expires_at": confirmation.expires_at.isoformat(),
            "tool_name": request.tool_name,
            "risk_level": policy_decision.risk_level.value
        }

    def _execute_tool_safely(
        self,
        execution_id: str,
        request: ToolRequest,
        policy_decision: PolicyDecision,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute tool with safety measures"""
        sandbox_id = None

        try:
            # Create sandbox if enabled
            if self.config["enable_sandboxing"]:
                sandbox_config = SandboxConfig(
                    working_directory=f"/tmp/torq_exec/{execution_id}",
                    temp_directory=f"/tmp/torq_temp/{execution_id}",
                    filesystem_isolated=True,
                    network_isolated=policy_decision.risk_level == RiskLevel.HIGH,
                    max_cpu_time_seconds=self.config["max_execution_time"]
                )

                sandbox_info = self.sandbox_manager.create_sandbox(request, sandbox_config)
                sandbox_id = sandbox_info["id"]
                self.stats["sandboxes_used"] += 1

                # Log sandbox creation
                self.audit_logger.log_sandbox_event(
                    "created", sandbox_id, request.tool_name,
                    {"execution_id": execution_id}, user_id
                )

            # Execute the tool (this would integrate with actual tool execution)
            # For now, simulate execution
            execution_result = self._simulate_tool_execution(request, sandbox_id)

            # Clean up sandbox
            if sandbox_id:
                self.sandbox_manager.cleanup_sandbox(sandbox_id)
                self.audit_logger.log_sandbox_event(
                    "destroyed", sandbox_id, request.tool_name,
                    {"execution_id": execution_id}, user_id
                )

            return {
                "success": True,
                "result": execution_result,
                "execution_id": execution_id,
                "sandbox_id": sandbox_id,
                "risk_level": policy_decision.risk_level.value,
                "policy_applied": policy_decision.policy_name
            }

        except Exception as e:
            # Clean up sandbox on error
            if sandbox_id:
                try:
                    self.sandbox_manager.cleanup_sandbox(sandbox_id)
                    self.audit_logger.log_sandbox_event(
                        "error_cleanup", sandbox_id, request.tool_name,
                        {"error": str(e)}, user_id
                    )
                except:
                    pass

            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id,
                "sandbox_id": sandbox_id,
                "risk_level": policy_decision.risk_level.value
            }

    def _simulate_tool_execution(self, request: ToolRequest, sandbox_id: Optional[str]) -> Dict[str, Any]:
        """Simulate tool execution (replace with actual tool integration)"""
        # This is a placeholder - integrate with actual tool execution
        return {
            "status": "completed",
            "output": f"Simulated execution of {request.tool_name} with operation {request.operation.value}",
            "parameters_used": request.parameters,
            "execution_method": "sandbox" if sandbox_id else "direct"
        }

    def _create_denial_response(
        self,
        execution_id: str,
        request: ToolRequest,
        reason: str,
        threats: List[str],
        risk_level: RiskLevel,
        user_id: Optional[str],
        session_id: Optional[str],
        rate_limit_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized denial response"""
        # Log security violation if high risk
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.audit_logger.log_security_violation(
                "tool_access_denied", risk_level, request.tool_name,
                f"Access denied: {reason}", user_id, session_id,
                blocked=True, details={"threats": threats}
            )
            self.stats["security_violations"] += 1

        response = {
            "success": False,
            "denied": True,
            "execution_id": execution_id,
            "tool_name": request.tool_name,
            "operation": request.operation.value,
            "denied_reason": reason,
            "risk_level": risk_level.value,
            "threats_detected": threats
        }

        if rate_limit_info:
            response["rate_limit_info"] = rate_limit_info

        return response

    def confirm_operation(
        self,
        confirmation_id: str,
        confirmed: bool,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Process user confirmation response

        Args:
            confirmation_id: Confirmation request ID
            confirmed: Whether user confirmed
            user_id: User identifier

        Returns:
            True if confirmation was processed
        """
        return self.confirmation_manager.confirm_operation(confirmation_id, confirmed, user_id)

    def get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety system status"""
        return {
            "statistics": self.stats.copy(),
            "configuration": self.config.copy(),
            "policy_engine": {
                "loaded_policies": self.policy_engine.list_policies(),
                "total_policies": len(self.policy_engine.list_policies())
            },
            "sandbox_manager": {
                "active_sandboxes": self.sandbox_manager.list_active_sandboxes(),
                "total_created": self.stats["sandboxes_used"]
            },
            "confirmation_manager": {
                "pending_confirmations": len(self.confirmation_manager.get_pending_confirmations()),
                "statistics": self.confirmation_manager.get_confirmation_statistics()
            },
            "rate_limiter": self.rate_limiter.get_statistics(),
            "audit_logger": self.audit_logger.get_statistics(),
            "security_manager": self.security_manager.get_security_report()
        }

    def reload_policies(self):
        """Reload all safety policies"""
        self.policy_engine.reload_policies()
        self.audit_logger.log_configuration_change(
            "policy_engine", "reload_policies", "old", "new", None, "Policy reload requested"
        )

    def update_configuration(self, config_updates: Dict[str, Any]):
        """Update safety configuration"""
        old_config = self.config.copy()
        self.config.update(config_updates)

        self.audit_logger.log_configuration_change(
            "safety_manager", "config_update", old_config, self.config, None
        )

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.confirmation_manager.cleanup_expired_confirmations()
            self.sandbox_manager.cleanup_all_sandboxes()
            self.security_manager.cleanup_old_sessions()
            logger.info("Safety manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during safety manager cleanup: {e}")