"""
TORQ Console Marvin-Powered Agents
Phase 3: Agent Enhancement

Intelligent agents with Marvin integration for enhanced AI capabilities.
"""

# Query routing
from .marvin_query_router import (
    MarvinQueryRouter,
    create_query_router,
    QueryAnalysis,
    RoutingDecision,
    AgentCapability
)

# Enhanced Prince Flowers
from .marvin_prince_flowers import (
    MarvinPrinceFlowers,
    create_prince_flowers_agent,
    ConversationTurn,
    AgentState
)

# Specialized workflow agents
from .marvin_workflow_agents import (
    WorkflowType,
    WorkflowResult,
    CodeGenerationAgent,
    DebuggingAgent,
    DocumentationAgent,
    TestingAgent,
    ArchitectureAgent,
    get_workflow_agent,
    list_workflow_agents
)

# Agent orchestration
from .marvin_orchestrator import (
    MarvinAgentOrchestrator,
    get_orchestrator,
    OrchestrationMode,
    OrchestrationResult
)

# Agent memory and learning
from .marvin_memory import (
    MarvinAgentMemory,
    get_agent_memory,
    AgentInteraction,
    InteractionType,
    AgentMemorySnapshot
)

# CLI Commands
from .marvin_commands import (
    MarvinAgentCommands,
    create_marvin_commands
)


__all__ = [
    # Query Router
    'MarvinQueryRouter',
    'create_query_router',
    'QueryAnalysis',
    'RoutingDecision',
    'AgentCapability',

    # Prince Flowers
    'MarvinPrinceFlowers',
    'create_prince_flowers_agent',
    'ConversationTurn',
    'AgentState',

    # Workflow Agents
    'WorkflowType',
    'WorkflowResult',
    'CodeGenerationAgent',
    'DebuggingAgent',
    'DocumentationAgent',
    'TestingAgent',
    'ArchitectureAgent',
    'get_workflow_agent',
    'list_workflow_agents',

    # Orchestration
    'MarvinAgentOrchestrator',
    'get_orchestrator',
    'OrchestrationMode',
    'OrchestrationResult',

    # Memory & Learning
    'MarvinAgentMemory',
    'get_agent_memory',
    'AgentInteraction',
    'InteractionType',
    'AgentMemorySnapshot',

    # CLI Commands
    'MarvinAgentCommands',
    'create_marvin_commands',
]

__version__ = '0.3.0'  # Phase 3: Agent Enhancement
