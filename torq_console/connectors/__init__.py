"""
Connectors Module - External System Integration

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

This module provides connectors for integrating TORQ Console with external
systems and platforms.
"""

from .base import (
    # Enums
    ConnectorType,
    ConnectorStatus,
    ActionState,
    RiskLevel,
    # Models
    ConnectorConfig,
    ConnectorCapability,
    ExternalAction,
    ActionExecutionResult,
    RetryPolicy,
    HealthCheckResult,
    # Base class
    BaseConnector,
    # Registry
    ConnectorRegistry,
    get_connector_registry,
    # Helpers
    execute_with_retry,
)

# Import specific connectors when they are implemented
# from .slack import SlackConnector
# from .jira import JiraConnector
# from .webhook import WebhookConnector
# from .email import EmailConnector

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
