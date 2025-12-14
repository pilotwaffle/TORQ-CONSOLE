"""
Agent Interfaces - Standardized contracts for different agent types.

Defines clear interfaces for various agent specializations to ensure
consistent behavior and enable proper type checking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any, Dict, List, Optional, Union, AsyncGenerator,
    Tuple
)
from enum import Enum

from .base_agent import (
    BaseAgent, AgentCapability, AgentContext, AgentResult
)


class WorkflowType(str, Enum):
    """Types of workflows agents can handle."""
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"


class ConversationMode(str, Enum):
    """Conversation interaction modes."""
    SINGLE_TURN = "single_turn"
    MULTI_TURN = "multi_turn"
    STREAMING = "streaming"
    ASYNC = "async"


class SearchScope(str, Enum):
    """Search scopes for research agents."""
    WEB = "web"
    LOCAL = "local"
    CODEBASE = "codebase"
    DOCUMENTATION = "documentation"
    SPECIFIC = "specific"


@dataclass
class CodeContext:
    """Context for code-related operations."""
    language: str
    framework: Optional[str] = None
    libraries: List[str] = None
    codebase_path: Optional[str] = None
    existing_code: Optional[str] = None
    style_guide: Optional[str] = None


@dataclass
class DocumentationRequest:
    """Request for documentation generation."""
    content: str
    doc_type: str  # api, guide, reference, tutorial
    audience: str  # developers, users, administrators
    format: str = "markdown"
    include_examples: bool = True
    detail_level: str = "medium"  # low, medium, high


@dataclass
class TestRequest:
    """Request for test generation."""
    code: str
    test_framework: str
    test_types: List[str] = None  # unit, integration, e2e
    coverage_target: float = 0.8
    mocking_required: bool = False


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    user_input: str
    agent_response: str
    timestamp: float
    context: Dict[str, Any]
    confidence: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class ResearchQuery:
    """Query for research operations."""
    query: str
    scope: SearchScope
    max_results: int = 10
    time_range: Optional[Tuple[str, str]] = None
    sources: Optional[List[str]] = None
    filters: Dict[str, Any] = None


@dataclass
class ArchitectureRequest:
    """Request for architecture design."""
    requirements: str
    constraints: List[str] = None
    scale: str = "medium"  # small, medium, large, enterprise
    domains: List[str] = None  # web, mobile, api, data, ml
    preferences: Dict[str, Any] = None


# Interface Definitions
class IAgent(ABC):
    """Base agent interface."""

    @abstractmethod
    async def process_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Process a generic request."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check agent health."""
        pass


class IConversationAgent(IAgent):
    """Interface for conversation-capable agents."""

    @abstractmethod
    async def start_conversation(
        self,
        initial_message: str,
        mode: ConversationMode = ConversationMode.MULTI_TURN,
        context: Optional[AgentContext] = None
    ) -> str:
        """Start a new conversation session."""
        pass

    @abstractmethod
    async def continue_conversation(
        self,
        session_id: str,
        message: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Continue an existing conversation."""
        pass

    @abstractmethod
    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Get conversation history for a session."""
        pass

    @abstractmethod
    async def end_conversation(self, session_id: str) -> bool:
        """End a conversation session."""
        pass


class IWorkflowAgent(IAgent):
    """Interface for workflow-capable agents."""

    @abstractmethod
    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        parameters: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute a specific workflow."""
        pass

    @abstractmethod
    def get_supported_workflows(self) -> List[WorkflowType]:
        """Get list of supported workflow types."""
        pass

    @abstractmethod
    async def get_workflow_template(
        self,
        workflow_type: WorkflowType
    ) -> Optional[Dict[str, Any]]:
        """Get template for a workflow type."""
        pass


class IResearchAgent(IAgent):
    """Interface for research-capable agents."""

    @abstractmethod
    async def search(
        self,
        query: ResearchQuery,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Perform a search operation."""
        pass

    @abstractmethod
    async def summarize_results(
        self,
        results: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Summarize search results."""
        pass

    @abstractmethod
    async def extract_insights(
        self,
        data: Union[str, List[Dict[str, Any]]],
        insights_type: str = "general"
    ) -> List[str]:
        """Extract insights from data."""
        pass


class ICodeAgent(IWorkflowAgent):
    """Interface for code-focused agents."""

    @abstractmethod
    async def generate_code(
        self,
        requirements: str,
        code_context: Optional[CodeContext] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Generate code from requirements."""
        pass

    @abstractmethod
    async def analyze_code(
        self,
        code: str,
        analysis_type: str = "general",  # security, performance, quality
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Analyze existing code."""
        pass

    @abstractmethod
    async def refactor_code(
        self,
        code: str,
        refactoring_goals: List[str],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Refactor existing code."""
        pass


class IDocumentationAgent(IWorkflowAgent):
    """Interface for documentation-focused agents."""

    @abstractmethod
    async def generate_documentation(
        self,
        request: DocumentationRequest,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Generate documentation."""
        pass

    @abstractmethod
    async def improve_documentation(
        self,
        existing_docs: str,
        improvement_areas: List[str],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Improve existing documentation."""
        pass


class ITestingAgent(IWorkflowAgent):
    """Interface for testing-focused agents."""

    @abstractmethod
    async def generate_tests(
        self,
        request: TestRequest,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Generate tests for code."""
        pass

    @abstractmethod
    async def analyze_coverage(
        self,
        code_path: str,
        test_results: Optional[Dict[str, Any]] = None,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Analyze test coverage."""
        pass


class IDebuggingAgent(IWorkflowAgent):
    """Interface for debugging-focused agents."""

    @abstractmethod
    async def debug_issue(
        self,
        code: str,
        error_message: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Debug a code issue."""
        pass

    @abstractmethod
    async def suggest_fixes(
        self,
        issue_analysis: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Suggest fixes for identified issues."""
        pass


class IArchitectureAgent(IWorkflowAgent):
    """Interface for architecture-focused agents."""

    @abstractmethod
    async def design_architecture(
        self,
        request: ArchitectureRequest,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Design system architecture."""
        pass

    @abstractmethod
    async def review_architecture(
        self,
        architecture_description: str,
        review_criteria: List[str],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Review existing architecture."""
        pass


class IOrchestrationAgent(IAgent):
    """Interface for orchestration agents."""

    @abstractmethod
    async def orchestrate_agents(
        self,
        agents: List[str],
        workflow: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Orchestrate multiple agents in a workflow."""
        pass

    @abstractmethod
    async def coordinate_workflow(
        self,
        workflow_definition: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Coordinate a complex workflow."""
        pass


class IMemoryAgent(IAgent):
    """Interface for memory-capable agents."""

    @abstractmethod
    async def store_memory(
        self,
        key: str,
        value: Any,
        category: str = "general",
        context: Optional[AgentContext] = None
    ) -> bool:
        """Store information in memory."""
        pass

    @abstractmethod
    async def retrieve_memory(
        self,
        key: str,
        category: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> Optional[Any]:
        """Retrieve information from memory."""
        pass

    @abstractmethod
    async def search_memories(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        limit: int = 10,
        context: Optional[AgentContext] = None
    ) -> List[Dict[str, Any]]:
        """Search stored memories."""
        pass

    @abstractmethod
    async def clear_memories(
        self,
        category: Optional[str] = None,
        older_than: Optional[float] = None
    ) -> int:
        """Clear stored memories."""
        pass


# Composite interfaces for common agent types
class ICodingAgent(ICodeAgent, IDebuggingAgent, ITestingAgent):
    """Complete coding agent interface."""
    pass


class IDevelopmentAgent(ICodingAgent, IDocumentationAgent, IArchitectureAgent):
    """Full development lifecycle agent interface."""
    pass


class IAssistantAgent(IConversationAgent, IResearchAgent, ICodeAgent):
    """General assistant agent interface."""
    pass