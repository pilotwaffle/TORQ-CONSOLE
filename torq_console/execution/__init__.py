"""
Execution Module - External Action Fabric

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

This module provides the External Action Fabric for safe execution of
external system actions with idempotency, provenance tracking, and
circuit breaking.
"""

from .action_fabric import (
    # Main class
    ExternalActionFabric,
    get_action_fabric,
    # Models
    ActionFabricEvent,
    ActionPolicy,
    PolicyCheckResult,
    # Supporting
    ActionQueue,
    ResultVerifier,
)

from .provenance import (
    ProvenanceEventType,
    ExecutionProvenance,
    ProvenanceEvent,
    ProvenanceStore,
    get_provenance_store,
)

from .circuit_breaker import (
    CircuitState,
    HealthStatus,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitOpenError,
    ConnectorHealthMonitor,
    HealthMonitor,
    get_health_monitor,
)

__all__ = [
    # Action Fabric
    'ExternalActionFabric',
    'get_action_fabric',
    'ActionFabricEvent',
    'ActionPolicy',
    'PolicyCheckResult',
    'ActionQueue',
    'ResultVerifier',
    # Provenance
    'ProvenanceEventType',
    'ExecutionProvenance',
    'ProvenanceEvent',
    'ProvenanceStore',
    'get_provenance_store',
    # Circuit Breaker
    'CircuitState',
    'HealthStatus',
    'CircuitBreakerConfig',
    'CircuitBreaker',
    'CircuitOpenError',
    'ConnectorHealthMonitor',
    'HealthMonitor',
    'get_health_monitor',
]
