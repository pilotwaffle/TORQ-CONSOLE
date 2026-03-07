"""
TORQ Console Multi-Agent Orchestration System - Phase 4A

This module implements the executive orchestration layer where Prince Flowers
coordinates specialist agents for multi-agent operations.

Architecture:
    Prince Flowers (Executive) → Specialist Agents → Tools
                ↑
           Delegation & Coordination
"""

from .executive_controller import ExecutiveController
from .delegation import DelegationRequest, DelegationResult, DelegationPolicy
from .agent_coordinator import AgentCoordinator
from .execution_plan import ExecutionPlan, ExecutionMode

__all__ = [
    "ExecutiveController",
    "DelegationRequest",
    "DelegationResult",
    "DelegationPolicy",
    "AgentCoordinator",
    "ExecutionPlan",
    "ExecutionMode",
]
