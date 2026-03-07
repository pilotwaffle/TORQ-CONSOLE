"""
Base Connector Interface and Models

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

This module provides the base connector interface and common models for all
external system connectors.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class ConnectorType(str, Enum):
    """Types of connectors."""
    SAAS = "saas"                    # Slack, Notion, HubSpot, etc.
    INFRASTRUCTURE = "infrastructure" # AWS, Railway, Kubernetes, etc.
    DATA_PLATFORM = "data_platform"   # Snowflake, BigQuery, Supabase, etc.
    COMMUNICATION = "communication"   # Email, SMS, Webhooks, Discord, etc.
    CUSTOM = "custom"                 # Custom connectors


class ConnectorStatus(str, Enum):
    """Status of a connector."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"
    DISABLED = "disabled"


class ActionState(str, Enum):
    """States of an external action execution."""
    CREATED = "created"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class RiskLevel(str, Enum):
    """Risk levels for external actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Models
# ============================================================================

class ConnectorConfig(BaseModel):
    """Configuration for a connector."""
    connector_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connector_type: str
    name: str
    description: Optional[str] = None

    # Authentication
    auth_type: str = "none"  # "api_key", "oauth", "basic", "token", "none"
    credentials_ref: Optional[str] = None  # Reference to secure storage

    # Configuration
    base_url: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3

    # Scoping
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Status
    status: ConnectorStatus = ConnectorStatus.INACTIVE
    last_health_check: Optional[float] = None
    last_error: Optional[str] = None

    # Timestamp
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class ConnectorCapability(BaseModel):
    """Describes a connector's capability."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_params: List[str] = Field(default_factory=list)
    optional_params: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_approval: bool = False


class ExternalAction(BaseModel):
    """Definition of an external action to execute."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Action identification
    action_type: str  # e.g., "create_ticket", "send_message"
    connector_type: str  # e.g., "jira", "slack"
    connector_id: Optional[str] = None

    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Risk and approval
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_approval: bool = False

    # Execution context
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    requested_by: Optional[str] = None  # User or agent ID
    task_id: Optional[str] = None

    # State tracking
    state: ActionState = ActionState.CREATED
    current_retry: int = 0
    max_retries: int = 3

    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_duration_seconds: Optional[float] = None

    # Timestamps
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Approval
    approval_id: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    denial_reason: Optional[str] = None


class ActionExecutionResult(BaseModel):
    """Result of an action execution."""
    success: bool
    action_id: str
    connector_type: str
    action_type: str

    # Output
    result: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None

    # Error handling
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retryable: bool = False

    # Performance
    execution_duration_seconds: float
    retry_count: int = 0

    # Verification
    verified: bool = False
    verification_message: Optional[str] = None

    # Timestamp
    completed_at: float = Field(default_factory=time.time)


class RetryPolicy(BaseModel):
    """Retry policy for actions."""
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0

    # Conditions for retry
    retry_on_timeout: bool = True
    retry_on_5xx_errors: bool = True
    retry_on_network_errors: bool = True
    retry_on_specific_errors: List[str] = Field(default_factory=list)

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        delay = self.retry_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)


class HealthCheckResult(BaseModel):
    """Result of a connector health check."""
    healthy: bool
    connector_id: str
    connector_type: str

    # Details
    message: str
    response_time_ms: Optional[float] = None
    last_error: Optional[str] = None

    # Timestamp
    checked_at: float = Field(default_factory=time.time)


# ============================================================================
# Base Connector Interface
# ============================================================================

class BaseConnector(ABC):
    """
    Abstract base class for all connectors.

    All connectors must implement this interface to work with the
    External Action Fabric.
    """

    connector_type: str
    connector_name: str
    connector_category: ConnectorType

    def __init__(self, config: ConnectorConfig):
        """
        Initialize the connector.

        Args:
            config: Connector configuration
        """
        self.config = config
        self._status = ConnectorStatus.INACTIVE
        self._last_health_check: Optional[float] = None
        self.logger = logging.getLogger(f"{__name__}.{self.connector_type}")

    @abstractmethod
    async def execute(self, action: ExternalAction) -> ActionExecutionResult:
        """
        Execute an external action.

        Args:
            action: The action to execute

        Returns:
            ActionExecutionResult with execution details
        """
        pass

    @abstractmethod
    async def validate_parameters(self, action_type: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters for an action.

        Args:
            action_type: The type of action to validate
            parameters: The parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ConnectorCapability]:
        """
        Get the capabilities of this connector.

        Returns:
            List of ConnectorCapability objects
        """
        pass

    async def health_check(self) -> HealthCheckResult:
        """
        Check the health of the connector connection.

        Returns:
            HealthCheckResult with health status
        """
        start_time = time.time()

        try:
            # Default implementation - subclasses should override
            await self._test_connection()
            response_time = (time.time() - start_time) * 1000

            self._status = ConnectorStatus.ACTIVE
            self._last_health_check = time.time()
            self.config.last_health_check = self._last_health_check

            return HealthCheckResult(
                healthy=True,
                connector_id=self.config.connector_id,
                connector_type=self.connector_type,
                message="Connector is healthy",
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._status = ConnectorStatus.ERROR
            self.config.last_error = str(e)

            return HealthCheckResult(
                healthy=False,
                connector_id=self.config.connector_id,
                connector_type=self.connector_type,
                message=f"Health check failed: {str(e)}",
                last_error=str(e),
                response_time_ms=response_time
            )

    async def _test_connection(self) -> None:
        """
        Test the connection to the external service.

        Subclasses should override this method.
        """
        raise NotImplementedError(f"{self.connector_type} must implement _test_connection")

    async def setup(self) -> None:
        """
        Set up the connector connection.

        Called before the connector is used for the first time.
        """
        self.logger.info(f"Setting up {self.connector_type} connector")
        # Subclasses can override for initialization logic
        self._status = ConnectorStatus.ACTIVE

    async def teardown(self) -> None:
        """
        Tear down the connector connection.

        Called when the connector is being disabled or removed.
        """
        self.logger.info(f"Tearing down {self.connector_type} connector")
        # Subclasses can override for cleanup logic
        self._status = ConnectorStatus.INACTIVE

    @property
    def status(self) -> ConnectorStatus:
        """Get the current connector status."""
        return self._status

    @property
    def is_healthy(self) -> bool:
        """Check if the connector is healthy."""
        return self._status == ConnectorStatus.ACTIVE


# ============================================================================
# Connector Registry
# ============================================================================

class ConnectorRegistry:
    """
    Registry for managing connector instances.

    The registry maintains a mapping of connector types to their
    implementations and manages connector lifecycles.
    """

    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._connector_classes: Dict[str, type[BaseConnector]] = {}
        self.logger = logging.getLogger(__name__)

    def register_connector_class(self, connector_type: str, connector_class: type[BaseConnector]) -> None:
        """
        Register a connector class.

        Args:
            connector_type: The type identifier for the connector
            connector_class: The connector class to register
        """
        self._connector_classes[connector_type] = connector_class
        self.logger.info(f"Registered connector class: {connector_type}")

    def create_connector(self, config: ConnectorConfig) -> BaseConnector:
        """
        Create a connector instance from configuration.

        Args:
            config: Connector configuration

        Returns:
            Connector instance

        Raises:
            ValueError: If connector type is not registered
        """
        connector_class = self._connector_classes.get(config.connector_type)
        if connector_class is None:
            raise ValueError(f"Unknown connector type: {config.connector_type}")

        connector = connector_class(config)
        self._connectors[config.connector_id] = connector
        return connector

    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """
        Get a connector by ID.

        Args:
            connector_id: The connector ID

        Returns:
            Connector instance or None
        """
        return self._connectors.get(connector_id)

    def get_connector_by_type(self, connector_type: str, workspace_id: Optional[str] = None) -> Optional[BaseConnector]:
        """
        Get a connector by type.

        Args:
            connector_type: The connector type
            workspace_id: Optional workspace ID for scoping

        Returns:
            First matching connector or None
        """
        for connector in self._connectors.values():
            if connector.config.connector_type == connector_type:
                if workspace_id is None or connector.config.workspace_id == workspace_id:
                    return connector
        return None

    def list_connectors(self, workspace_id: Optional[str] = None, status: Optional[ConnectorStatus] = None) -> List[BaseConnector]:
        """
        List all connectors.

        Args:
            workspace_id: Optional workspace filter
            status: Optional status filter

        Returns:
            List of connectors matching filters
        """
        connectors = list(self._connectors.values())

        if workspace_id:
            connectors = [c for c in connectors if c.config.workspace_id == workspace_id]

        if status:
            connectors = [c for c in connectors if c.status == status]

        return connectors

    async def remove_connector(self, connector_id: str) -> bool:
        """
        Remove a connector.

        Args:
            connector_id: The connector ID to remove

        Returns:
            True if removed, False if not found
        """
        connector = self._connectors.get(connector_id)
        if connector:
            await connector.teardown()
            del self._connectors[connector_id]
            self.logger.info(f"Removed connector: {connector_id}")
            return True
        return False

    def get_registered_types(self) -> List[str]:
        """
        Get all registered connector types.

        Returns:
            List of connector type identifiers
        """
        return list(self._connector_classes.keys())


# Global registry instance
_global_registry: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    """Get the global connector registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ConnectorRegistry()
    return _global_registry


# ============================================================================
# Helper Functions
# ============================================================================

async def execute_with_retry(
    connector: BaseConnector,
    action: ExternalAction,
    retry_policy: Optional[RetryPolicy] = None
) -> ActionExecutionResult:
    """
    Execute an action with retry logic.

    Args:
        connector: The connector to use
        action: The action to execute
        retry_policy: Optional retry policy

    Returns:
        ActionExecutionResult from the final execution attempt
    """
    policy = retry_policy or RetryPolicy()
    last_result: Optional[ActionExecutionResult] = None

    for attempt in range(policy.max_retries + 1):
        if attempt > 0:
            action.current_retry = attempt
            action.state = ActionState.RETRYING

            delay = policy.get_retry_delay(attempt - 1)
            await asyncio.sleep(delay)

        try:
            result = await connector.execute(action)

            if result.success or not result.retryable:
                return result

            last_result = result

            # Check if we should retry based on error
            if not _should_retry(result, policy):
                return result

        except asyncio.TimeoutError:
            if not policy.retry_on_timeout or attempt >= policy.max_retries:
                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=connector.connector_type,
                    action_type=action.action_type,
                    error_message="Execution timeout",
                    error_code="TIMEOUT",
                    retryable=policy.retry_on_timeout,
                    execution_duration_seconds=0,
                    retry_count=attempt
                )
        except Exception as e:
            if attempt >= policy.max_retries:
                return ActionExecutionResult(
                    success=False,
                    action_id=action.action_id,
                    connector_type=connector.connector_type,
                    action_type=action.action_type,
                    error_message=str(e),
                    error_code="UNKNOWN",
                    retryable=False,
                    execution_duration_seconds=0,
                    retry_count=attempt
                )

    # Return the last result if all retries exhausted
    return last_result or ActionExecutionResult(
        success=False,
        action_id=action.action_id,
        connector_type=connector.connector_type,
        action_type=action.action_type,
        error_message="Max retries exceeded",
        error_code="MAX_RETRIES",
        retryable=False,
        execution_duration_seconds=0,
        retry_count=policy.max_retries
    )


def _should_retry(result: ActionExecutionResult, policy: RetryPolicy) -> bool:
    """Determine if an execution result should trigger a retry."""
    if not result.retryable:
        return False

    if result.error_code:
        # Check specific error codes
        if result.error_code in policy.retry_on_specific_errors:
            return True
        if result.error_code.startswith("5") and policy.retry_on_5xx_errors:
            return True

    return False


# Export all public items
__all__ = [
    # Enums
    'ConnectorType',
    'ConnectorStatus',
    'ActionState',
    'RiskLevel',
    # Models
    'ConnectorConfig',
    'ConnectorCapability',
    'ExternalAction',
    'ActionExecutionResult',
    'RetryPolicy',
    'HealthCheckResult',
    # Base class
    'BaseConnector',
    # Registry
    'ConnectorRegistry',
    'get_connector_registry',
    # Helpers
    'execute_with_retry',
]
