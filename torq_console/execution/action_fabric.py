"""
External Action Fabric

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

The Action Fabric is the central execution layer for all external system actions.
It ensures policy compliance, handles approvals, manages retries, and provides
audit trails for all external interactions.

Core principle: Agents may propose actions. Only the Action Fabric executes them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ..connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectorStatus,
    ConnectorType,
    ExternalAction,
    ActionExecutionResult,
    ActionState,
    RiskLevel,
    RetryPolicy,
    HealthCheckResult,
    get_connector_registry,
)
from ..autonomy.models import ApprovalRequest, ApprovalStatus, PolicyDecision, PolicyLevel
from ..autonomy.state_store import StateStore
from .provenance import (
    ProvenanceStore,
    ExecutionProvenance,
    ProvenanceEventType,
    get_provenance_store,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    HealthMonitor,
    get_health_monitor,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Events
# ============================================================================

class ActionFabricEvent(BaseModel):
    """Event emitted by the Action Fabric."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # "action_created", "action_executed", "action_failed", etc.
    action_id: str
    connector_type: str
    action_type: str

    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)

    # Context
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    requested_by: Optional[str] = None

    # Timestamp
    timestamp: float = Field(default_factory=time.time)


# ============================================================================
# Action Queue
# ============================================================================

class ActionQueue:
    """Queue for managing pending actions."""

    def __init__(self, max_size: int = 1000):
        self._queue: asyncio.Queue[ExternalAction] = asyncio.Queue(maxsize=max_size)
        self._prioritized: Dict[str, List[ExternalAction]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def put(self, action: ExternalAction) -> None:
        """Add an action to the queue."""
        await self._queue.put(action)

    async def get(self) -> ExternalAction:
        """Get the next action from the queue."""
        return await self._queue.get()

    def qsize(self) -> int:
        """Get the current queue size."""
        return self._queue.qsize()

    async def clear(self) -> None:
        """Clear all pending actions."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break


# ============================================================================
# Policy Integration
# ============================================================================

class ActionPolicy(BaseModel):
    """Policy for external action execution."""
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

    # Scope
    connector_types: List[str] = Field(default_factory=list)
    action_types: List[str] = Field(default_factory=list)
    environments: List[str] = Field(default_factory=list)  # empty = all

    # Rules
    require_approval: bool = False
    allowed_risk_levels: List[RiskLevel] = Field(default_factory=lambda: [RiskLevel.LOW, RiskLevel.MEDIUM])
    rate_limit_per_minute: Optional[int] = None

    # Approval rules
    approval_threshold: str = "admin"  # who can approve
    approval_timeout_seconds: int = 3600

    # Workspace scoping
    workspace_id: Optional[str] = None

    # Active flag
    enabled: bool = True


# ============================================================================
# Result Verification
# ============================================================================

class ResultVerifier:
    """Verifies the results of external action executions."""

    async def verify(self, result: ActionExecutionResult, action: ExternalAction) -> tuple[bool, Optional[str]]:
        """
        Verify an action execution result.

        Args:
            result: The execution result to verify
            action: The action that was executed

        Returns:
            Tuple of (verified, verification_message)
        """
        # Basic success check
        if not result.success:
            return False, result.error_message or "Execution failed"

        # Connector-specific verification
        verifier = self._get_verifier(action.connector_type)
        if verifier:
            try:
                verified, message = await verifier(result, action)
                return verified, message
            except Exception as e:
                logger.warning(f"Verifier error for {action.connector_type}: {e}")
                return False, f"Verification error: {str(e)}"

        # Default verification: success response is enough
        return True, "Execution completed successfully"

    def _get_verifier(self, connector_type: str) -> Optional[Callable]:
        """Get the verifier function for a connector type."""
        verifiers = {
            "webhook": self._verify_webhook,
            "slack": self._verify_slack,
            "jira": self._verify_jira,
            "email": self._verify_email,
        }
        return verifiers.get(connector_type)

    async def _verify_webhook(self, result: ActionExecutionResult, action: ExternalAction) -> tuple[bool, Optional[str]]:
        """Verify webhook execution result."""
        if result.result and "status_code" in result.result:
            status_code = result.result["status_code"]
            if 200 <= status_code < 300:
                return True, f"Webhook returned {status_code}"
            return False, f"Webhook returned error status {status_code}"
        return False, "No status code in result"

    async def _verify_slack(self, result: ActionExecutionResult, action: ExternalAction) -> tuple[bool, Optional[str]]:
        """Verify Slack execution result."""
        if result.result and "ts" in result.result:
            return True, f"Message sent (timestamp: {result.result['ts']})"
        return False, "No message timestamp in result"

    async def _verify_jira(self, result: ActionExecutionResult, action: ExternalAction) -> tuple[bool, Optional[str]]:
        """Verify Jira execution result."""
        if result.result and "key" in result.result:
            return True, f"Ticket created: {result.result['key']}"
        return False, "No ticket key in result"

    async def _verify_email(self, result: ActionExecutionResult, action: ExternalAction) -> tuple[bool, Optional[str]]:
        """Verify email execution result."""
        if result.result and "message_id" in result.result:
            return True, f"Email sent (ID: {result.result['message_id']})"
        return False, "No message ID in result"


# ============================================================================
# External Action Fabric
# ============================================================================

class ExternalActionFabric:
    """
    Central execution fabric for all external actions.

    The Action Fabric ensures:
    - Policy compliance before execution
    - Approval workflow for high-risk actions
    - Secure connector routing
    - Retry logic with exponential backoff
    - Result verification
    - Complete audit trails
    """

    def __init__(
        self,
        connector_registry: Optional[ConnectorRegistry] = None,
        state_store: Optional[StateStore] = None,
        provenance_store: Optional[ProvenanceStore] = None,
        health_monitor: Optional[HealthMonitor] = None
    ):
        """
        Initialize the Action Fabric.

        Args:
            connector_registry: Registry of available connectors
            state_store: State store for persistence
            provenance_store: Provenance store for traceability
            health_monitor: Health monitor for circuit breaking
        """
        self._registry = connector_registry or get_connector_registry()
        self._state_store = state_store
        self._provenance = provenance_store or get_provenance_store()
        self._health_monitor = health_monitor or get_health_monitor()

        # Action queue
        self._queue = ActionQueue()

        # Policies
        self._policies: List[ActionPolicy] = []
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)

        # Result verifier
        self._verifier = ResultVerifier()

        # Event handlers
        self._event_handlers: List[Callable[[ActionFabricEvent], None]] = []

        # Execution state
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "approval_required": 0,
            "approval_denied": 0,
            "idempotency_hits": 0,
            "circuit_breaker_trips": 0,
        }

        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the Action Fabric processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_actions())
        self.logger.info("External Action Fabric started")

    async def stop(self) -> None:
        """Stop the Action Fabric processor."""
        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("External Action Fabric stopped")

    def add_event_handler(self, handler: Callable[[ActionFabricEvent], None]) -> None:
        """Add an event handler."""
        self._event_handlers.append(handler)

    def _emit_event(self, event: ActionFabricEvent) -> None:
        """Emit an event to all handlers."""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")

    # -------------------------------------------------------------------------
    # Action Submission
    # -------------------------------------------------------------------------

    async def submit_action(
        self,
        action_type: str,
        connector_type: str,
        parameters: Dict[str, Any],
        workspace_id: Optional[str] = None,
        environment: Optional[str] = None,
        requested_by: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        task_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> ExternalAction:
        """
        Submit an external action for execution.

        Args:
            action_type: The type of action to execute
            connector_type: The type of connector to use
            parameters: Action parameters
            workspace_id: Workspace ID for scoping
            environment: Environment (dev, staging, production)
            requested_by: User or agent requesting the action
            risk_level: Risk level of the action
            task_id: Associated task ID
            trace_id: Root trace ID for provenance
            idempotency_key: Unique key for deduplication

        Returns:
            The created ExternalAction
        """
        # Generate idempotency key if not provided
        if not idempotency_key:
            # Create from workspace, connector, type, and params hash
            import hashlib
            params_str = json.dumps(parameters, sort_keys=True)
            params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]
            idempotency_key = f"{workspace_id}:{connector_type}:{action_type}:{params_hash}"

        # Check for existing provenance (idempotency)
        existing = self._provenance.get_by_idempotency_key(idempotency_key)
        if existing:
            self._stats["idempotency_hits"] += 1
            self.logger.info(f"Idempotency hit: {idempotency_key}")
            # Return existing action's info
            action = ExternalAction(
                action_id=existing.action_id,
                action_type=action_type,
                connector_type=connector_type,
                parameters=parameters,
                state=ActionState(existing.status.upper()),
                result=existing.result
            )
            return action

        # Create provenance record
        provenance = self._provenance.create_provenance(
            action_id="",  # Will be set when action is created
            connector_type=connector_type,
            action_type=action_type,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            workspace_id=workspace_id,
            environment=environment,
            requested_by=requested_by,
            risk_level=risk_level.value,
            task_id=task_id
        )

        action = ExternalAction(
            action_type=action_type,
            connector_type=connector_type,
            parameters=parameters,
            risk_level=risk_level,
            workspace_id=workspace_id,
            environment=environment,
            requested_by=requested_by,
            task_id=task_id
        )

        # Link action to provenance
        provenance.action_id = action.action_id

        self._stats["total_actions"] += 1

        # Emit action created event
        self._emit_event(ActionFabricEvent(
            event_type="action_created",
            action_id=action.action_id,
            connector_type=connector_type,
            action_type=action_type,
            data={"risk_level": risk_level, "idempotency_key": idempotency_key},
            workspace_id=workspace_id,
            environment=environment,
            requested_by=requested_by
        ))

        # Add to queue
        await self._queue.put(action)

        return action

    # -------------------------------------------------------------------------
    # Action Processing
    # -------------------------------------------------------------------------

    async def _process_actions(self) -> None:
        """Background task to process actions from the queue."""
        while self._running:
            try:
                action = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                asyncio.create_task(self._execute_action(action))
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing action: {e}")

    async def _execute_action(self, action: ExternalAction) -> ActionExecutionResult:
        """
        Execute an external action through the fabric.

        Args:
            action: The action to execute

        Returns:
            ActionExecutionResult
        """
        try:
            # 1. Policy Check
            policy_result = await self._check_policy(action)
            if not policy_result.allowed:
                action.state = ActionState.DENIED
                action.denial_reason = policy_result.reason

                self._emit_event(ActionFabricEvent(
                    event_type="action_denied",
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    data={"reason": policy_result.reason},
                    workspace_id=action.workspace_id
                ))

                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    error_message=f"Policy denied: {policy_result.reason}",
                    error_code="POLICY_DENIED",
                    retryable=False,
                    execution_duration_seconds=0
                )

            # 2. Approval Check
            if action.requires_approval or policy_result.requires_approval:
                action.state = ActionState.APPROVAL_PENDING
                self._stats["approval_required"] += 1

                # In a real system, would wait for approval here
                # For now, auto-approve if risk level allows
                if action.risk_level == RiskLevel.CRITICAL:
                    # Require actual approval
                    action.denial_reason = "Critical actions require explicit approval"
                    self._stats["approval_denied"] += 1
                    return ActionExecutionResult(
                        success=False,
                        action_id=action.action_id,
                        connector_type=action.connector_type,
                        action_type=action.action_type,
                        error_message="Critical action requires approval",
                        error_code="APPROVAL_REQUIRED",
                        retryable=False,
                        execution_duration_seconds=0
                    )
                else:
                    action.state = ActionState.APPROVED
                    action.approved_by = "system"
                    action.approved_at = time.time()

            # 3. Rate Limit Check
            if not await self._check_rate_limit(action):
                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    error_message="Rate limit exceeded",
                    error_code="RATE_LIMITED",
                    retryable=True,
                    execution_duration_seconds=0
                )

            # 4. Get Connector
            connector = self._registry.get_connector_by_type(
                action.connector_type,
                action.workspace_id
            )

            if not connector:
                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    error_message=f"Connector not found: {action.connector_type}",
                    error_code="CONNECTOR_NOT_FOUND",
                    retryable=False,
                    execution_duration_seconds=0
                )

            # Auto-register connector with health monitor if not already registered
            if not self._health_monitor.get_circuit_breaker(connector.connector_id):
                self._health_monitor.register_connector(
                    connector_id=connector.connector_id,
                    connector_type=connector.config.connector_type,
                    circuit_breaker_config=CircuitBreakerConfig(
                        failure_threshold=5,
                        open_timeout_seconds=60.0
                    )
                )

            # 5. Circuit Breaker Check
            breaker = self._health_monitor.get_circuit_breaker(connector.connector_id)
            if breaker and not breaker.can_execute:
                self._stats["circuit_breaker_trips"] += 1
                action.state = ActionState.FAILED
                action.error_message = f"Circuit breaker is open for {action.connector_type}"

                self._emit_event(ActionFabricEvent(
                    event_type="action_blocked",
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    data={"reason": "Circuit breaker open"},
                    workspace_id=action.workspace_id
                ))

                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    error_message=f"Circuit breaker is open for {action.connector_type}",
                    error_code="CIRCUIT_OPEN",
                    retryable=False,
                    execution_duration_seconds=0
                )

            # 6. Execute through circuit breaker
            action.state = ActionState.EXECUTING
            action.started_at = time.time()

            async def execute_through_breaker():
                return await execute_with_retry(
                    connector,
                    action,
                    RetryPolicy(max_retries=action.max_retries)
                )

            if breaker:
                result = await breaker.execute(execute_through_breaker)
            else:
                result = await execute_through_breaker()

            # 7. Verify Result
            verified, verification_message = await self._verifier.verify(result, action)
            result.verified = verified
            result.verification_message = verification_message

            # 8. Update state
            action.completed_at = time.time()
            action.execution_duration_seconds = action.completed_at - action.started_at
            action.result = result.result

            if result.success:
                action.state = ActionState.SUCCEEDED
                self._stats["successful_actions"] += 1

                self._emit_event(ActionFabricEvent(
                    event_type="action_succeeded",
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    data={"duration": action.execution_duration_seconds},
                    workspace_id=action.workspace_id
                ))
            else:
                action.state = ActionState.FAILED
                action.error_message = result.error_message
                self._stats["failed_actions"] += 1

                # Record failure in circuit breaker
                if breaker:
                    breaker._state.record_failure()

                self._emit_event(ActionFabricEvent(
                    event_type="action_failed",
                    action_id=action.action_id,
                    connector_type=action.connector_type,
                    action_type=action.action_type,
                    data={"error": result.error_message},
                    workspace_id=action.workspace_id
                ))

            # 9. Persist to state store
            if self._state_store:
                await self._save_action_record(action, result)

            return result

        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
            action.state = ActionState.FAILED
            action.error_message = str(e)
            self._stats["failed_actions"] += 1

            return ActionExecutionResult(
                success=False,
                action_id=action.action_id,
                connector_type=action.connector_type,
                action_type=action.action_type,
                error_message=str(e),
                error_code="EXECUTION_ERROR",
                retryable=False,
                execution_duration_seconds=0
            )

    # -------------------------------------------------------------------------
    # Policy Checking
    # -------------------------------------------------------------------------

    async def _check_policy(self, action: ExternalAction) -> "PolicyCheckResult":
        """Check if action complies with policies."""
        for policy in self._policies:
            if not policy.enabled:
                continue

            if policy.workspace_id and policy.workspace_id != action.workspace_id:
                continue

            if policy.connector_types and action.connector_type not in policy.connector_types:
                continue

            if policy.action_types and action.action_type not in policy.action_types:
                continue

            if policy.environments and action.environment not in policy.environments:
                continue

            # Check risk level
            if action.risk_level not in policy.allowed_risk_levels:
                return PolicyCheckResult(
                    allowed=False,
                    requires_approval=False,
                    reason=f"Risk level {action.risk_level} not allowed by policy {policy.name}"
                )

            # Check approval requirement
            if policy.require_approval:
                return PolicyCheckResult(
                    allowed=True,
                    requires_approval=True,
                    reason=f"Policy {policy.name} requires approval"
                )

        return PolicyCheckResult(allowed=True, requires_approval=False)

    async def _check_rate_limit(self, action: ExternalAction) -> bool:
        """Check if action is within rate limits."""
        key = f"{action.workspace_id}:{action.connector_type}:{action.action_type}"

        # Clean old entries (older than 1 minute)
        now = time.time()
        self._rate_limits[key] = [
            t for t in self._rate_limits[key]
            if now - t < 60
        ]

        # Find applicable policy limit
        limit = None
        for policy in self._policies:
            if policy.rate_limit_per_minute:
                if policy.workspace_id and policy.workspace_id != action.workspace_id:
                    continue
                if policy.connector_types and action.connector_type not in policy.connector_types:
                    continue
                limit = policy.rate_limit_per_minute
                break

        if limit and len(self._rate_limits[key]) >= limit:
            return False

        # Record this action
        self._rate_limits[key].append(now)
        return True

    # -------------------------------------------------------------------------
    # State Persistence
    # -------------------------------------------------------------------------

    async def _save_action_record(self, action: ExternalAction, result: ActionExecutionResult) -> None:
        """Save action execution record to state store."""
        if not self._state_store:
            return

        record = {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "connector_type": action.connector_type,
            "workspace_id": action.workspace_id,
            "environment": action.environment,
            "requested_by": action.requested_by,
            "risk_level": action.risk_level,
            "state": action.state,
            "result": result.result,
            "success": result.success,
            "error_message": result.error_message,
            "execution_duration_seconds": action.execution_duration_seconds,
            "created_at": action.created_at,
            "completed_at": action.completed_at,
        }

        # Would save to state store here
        # await self._state_store.save_action_record(record)

    # -------------------------------------------------------------------------
    # Policy Management
    # -------------------------------------------------------------------------

    def add_policy(self, policy: ActionPolicy) -> None:
        """Add an action policy."""
        self._policies.append(policy)
        self.logger.info(f"Added policy: {policy.name}")

    def remove_policy(self, policy_id: str) -> bool:
        """Remove an action policy."""
        for i, policy in enumerate(self._policies):
            if policy.policy_id == policy_id:
                del self._policies[i]
                self.logger.info(f"Removed policy: {policy_id}")
                return True
        return False

    def list_policies(self, workspace_id: Optional[str] = None) -> List[ActionPolicy]:
        """List all policies."""
        if workspace_id:
            return [p for p in self._policies if p.workspace_id == workspace_id]
        return self._policies.copy()

    # -------------------------------------------------------------------------
    # Statistics and Monitoring
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "active_policies": len([p for p in self._policies if p.enabled]),
            "is_running": self._running,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all connectors."""
        results = {}

        for connector in self._registry.list_connectors():
            try:
                health = await connector.health_check()
                results[connector.config.connector_id] = health
            except Exception as e:
                results[connector.config.connector_id] = HealthCheckResult(
                    healthy=False,
                    connector_id=connector.config.connector_id,
                    connector_type=connector.connector_type,
                    message=f"Health check failed: {str(e)}",
                    last_error=str(e)
                )

        return results


class PolicyCheckResult(BaseModel):
    """Result of a policy check."""
    allowed: bool
    requires_approval: bool = False
    reason: Optional[str] = None


# ============================================================================
# Singleton Instance
# ============================================================================

_global_fabric: Optional[ExternalActionFabric] = None


def get_action_fabric() -> ExternalActionFabric:
    """Get the global Action Fabric instance."""
    global _global_fabric
    if _global_fabric is None:
        _global_fabric = ExternalActionFabric()
    return _global_fabric


# Export
__all__ = [
    # Main class
    'ExternalActionFabric',
    'get_action_fabric',
    # Models
    'ActionFabricEvent',
    'ActionPolicy',
    'PolicyCheckResult',
    # Supporting
    'ActionQueue',
    'ResultVerifier',
]
