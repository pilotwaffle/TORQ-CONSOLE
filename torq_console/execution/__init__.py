"""
Execution Module - External Action Fabric

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

This module provides the External Action Fabric for safe execution of
external system actions.
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
