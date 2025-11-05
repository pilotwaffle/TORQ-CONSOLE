"""
TORQ Console Marvin-Powered Agents
Phase 3: Agent Enhancement

Intelligent agents with Marvin integration for enhanced AI capabilities.
"""

# Try to import Marvin components, but make them optional
_MARVIN_AVAILABLE = False
_MARVIN_IMPORT_ERROR = None

__all__ = []

try:
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

    _MARVIN_AVAILABLE = True

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

except ImportError as e:
    _MARVIN_IMPORT_ERROR = str(e)
    # Marvin not available - agents module will have no exports
    pass


# Always export these status indicators
__all__.extend(['is_marvin_available', 'get_marvin_status'])


def is_marvin_available() -> bool:
    """Check if Marvin integration is available."""
    return _MARVIN_AVAILABLE


def get_marvin_status() -> dict:
    """Get Marvin integration status and any import errors."""
    return {
        'available': _MARVIN_AVAILABLE,
        'error': _MARVIN_IMPORT_ERROR if not _MARVIN_AVAILABLE else None
    }


__version__ = '0.3.0'  # Phase 3: Agent Enhancement
