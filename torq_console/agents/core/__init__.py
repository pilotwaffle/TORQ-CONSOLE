"""
TORQ Console Core Agent Architecture

Consolidated agent system providing unified interfaces for all agent capabilities.
Replaces scattered agent files with focused, composable modules.

This architecture reduces 75+ agent files to 15-20 core modules while preserving
all functionality and eliminating code duplication.
"""

# Core Components
from .base_agent import BaseAgent, AgentCapability, AgentStatus
from .registry import AgentRegistry, get_agent_registry
from .interfaces import (
    IAgent,
    IConversationAgent,
    IWorkflowAgent,
    IResearchAgent,
    ICodeAgent
)

# Capability Modules
from .capabilities import (
    ConversationCapability,
    ResearchCapability,
    CodeGenerationCapability,
    DebuggingCapability,
    DocumentationCapability,
    TestingCapability,
    ArchitectureCapability
)

# Core Agent Implementations
from .conversational_agent import ConversationalAgent
from .workflow_agent import WorkflowAgent
from .research_agent import ResearchAgent
from .orchestration_agent import OrchestrationAgent

__all__ = [
    # Core Architecture
    'BaseAgent',
    'AgentCapability',
    'AgentStatus',
    'AgentRegistry',
    'get_agent_registry',

    # Interfaces
    'IAgent',
    'IConversationAgent',
    'IWorkflowAgent',
    'IResearchAgent',
    'ICodeAgent',

    # Capabilities
    'ConversationCapability',
    'ResearchCapability',
    'CodeGenerationCapability',
    'DebuggingCapability',
    'DocumentationCapability',
    'TestingCapability',
    'ArchitectureCapability',

    # Core Agents
    'ConversationalAgent',
    'WorkflowAgent',
    'ResearchAgent',
    'OrchestrationAgent',
]

__version__ = '1.0.0'