"""
Base Agent Class - Foundation for all TORQ Console agents.

Provides common functionality, interfaces, and patterns for all agent implementations.
Consolidates duplicate code found across 75+ agent files.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Callable, Union,
    Type, Coroutine, Protocol, runtime_checkable
)
from contextlib import asynccontextmanager

from torq_console.llm.providers.base import BaseLLMProvider


class AgentCapability(str, Enum):
    """Standardized agent capabilities."""

    # Core Capabilities
    CONVERSATION = "conversation"
    RESEARCH = "research"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"

    # Specialized Capabilities
    WEB_SEARCH = "web_search"
    DATA_ANALYSIS = "data_analysis"
    WORKFLOW_AUTOMATION = "workflow_automation"
    MEMORY_MANAGEMENT = "memory_management"
    LEARNING = "learning"
    ORCHESTRATION = "orchestration"

    # Domain-Specific Capabilities
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentContext:
    """Execution context for agent operations."""
    session_id: str
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Standard result structure for all agent operations."""
    success: bool
    content: str
    confidence: float = 0.0
    execution_time: float = 0.0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class AgentMetrics:
    """Performance and usage metrics for agents."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_execution_time: float = 0.0
    total_tokens_used: int = 0
    last_request_time: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


@runtime_checkable
class IAgent(Protocol):
    """Protocol for agent interfaces."""

    agent_id: str
    agent_name: str
    capabilities: List[AgentCapability]
    status: AgentStatus

    async def process_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Process a user request."""
        ...

    async def health_check(self) -> bool:
        """Check agent health."""
        ...


class BaseAgent(ABC):
    """
    Base class for all TORQ Console agents.

    Provides common functionality including:
    - Standardized initialization and lifecycle management
    - Request processing pipeline with error handling
    - Metrics collection and monitoring
    - Capability management
    - Context-aware execution
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: List[AgentCapability],
        llm_provider: Optional[BaseLLMProvider] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize base agent."""
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.llm_provider = llm_provider
        self.config = config or {}

        # State management
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Agent.{self.agent_id}")

        # Metrics and monitoring
        self.metrics = AgentMetrics()
        self._request_history: List[AgentResult] = []
        self._max_history_size = self.config.get("max_history_size", 100)

        # Runtime state
        self._current_context: Optional[AgentContext] = None
        self._request_id_counter = 0

        self.logger.info(f"Initialized agent: {self.agent_name} ({self.agent_id})")

    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy and ready."""
        return self.status in [AgentStatus.IDLE, AgentStatus.PROCESSING]

    @property
    def can_process_requests(self) -> bool:
        """Check if agent can accept new requests."""
        return self.status == AgentStatus.IDLE

    @asynccontextmanager
    async def _request_context(self, request: str):
        """Context manager for request processing."""
        self.status = AgentStatus.PROCESSING
        start_time = time.time()

        try:
            yield
        except Exception as e:
            self.status = AgentStatus.ERROR
            raise
        finally:
            execution_time = time.time() - start_time
            self.status = AgentStatus.IDLE
            self.metrics.last_request_time = time.time()
            self.logger.debug(f"Request processed in {execution_time:.2f}s")

    async def process_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Process a user request with standardized pipeline.

        Args:
            request: User request string
            context: Optional execution context

        Returns:
            AgentResult with standardized structure
        """
        if not self.can_process_requests:
            return AgentResult(
                success=False,
                content="Agent is currently busy and cannot process requests",
                error=f"Agent status: {self.status}"
            )

        async with self._request_context(request):
            self._current_context = context
            request_id = self._generate_request_id()

            try:
                self.logger.info(f"Processing request {request_id}: {request[:100]}...")

                # Pre-processing hook
                await self._before_process(request, context)

                # Execute main processing
                result = await self._execute_request(request, context)

                # Post-processing hook
                result = await self._after_process(request, result, context)

                # Update metrics
                self._update_metrics(result, execution_time=result.execution_time)

                # Store in history
                self._add_to_history(result)

                self.logger.info(f"Request {request_id} completed: {result.success}")
                return result

            except Exception as e:
                error_msg = f"Request {request_id} failed: {str(e)}"
                self.logger.error(error_msg, exc_info=True)

                result = AgentResult(
                    success=False,
                    content="An error occurred while processing your request",
                    error=error_msg,
                    execution_time=time.time() - start_time
                )

                self._update_metrics(result, execution_time=result.execution_time)
                self._add_to_history(result)
                return result

    @abstractmethod
    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Execute the main request processing logic.

        Must be implemented by concrete agents.
        """
        pass

    async def _before_process(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> None:
        """Pre-processing hook. Override in subclasses."""
        pass

    async def _after_process(
        self,
        request: str,
        result: AgentResult,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Post-processing hook. Override in subclasses."""
        return result

    async def health_check(self) -> bool:
        """Perform comprehensive health check."""
        try:
            # Check basic state
            if not self.is_healthy:
                return False

            # Check LLM provider if available
            if self.llm_provider:
                try:
                    # Simple test call
                    await self.llm_provider.generate_response("Health check")
                except Exception:
                    return False

            # Agent-specific health check
            return await self._health_check_impl()

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def _health_check_impl(self) -> bool:
        """Agent-specific health check. Override in subclasses."""
        return True

    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities."""
        return self.capabilities.copy()

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability."""
        return capability in self.capabilities

    def get_metrics(self) -> AgentMetrics:
        """Get current agent metrics."""
        return self.metrics

    def get_request_history(
        self,
        limit: Optional[int] = None
    ) -> List[AgentResult]:
        """Get request history."""
        history = self._request_history.copy()
        if limit:
            return history[-limit:]
        return history

    def clear_history(self) -> None:
        """Clear request history."""
        self._request_history.clear()
        self.logger.info("Request history cleared")

    async def reset(self) -> None:
        """Reset agent state."""
        self.status = AgentStatus.IDLE
        self._current_context = None
        self.clear_history()

        # Agent-specific reset
        await self._reset_impl()

        self.logger.info("Agent reset completed")

    async def _reset_impl(self) -> None:
        """Agent-specific reset implementation. Override in subclasses."""
        pass

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_id_counter += 1
        return f"{self.agent_id}_{self._request_id_counter}_{int(time.time())}"

    def _update_metrics(self, result: AgentResult, execution_time: float) -> None:
        """Update agent metrics."""
        self.metrics.total_requests += 1

        if result.success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        # Update average execution time
        total_time = (
            self.metrics.average_execution_time * (self.metrics.total_requests - 1) +
            execution_time
        )
        self.metrics.average_execution_time = total_time / self.metrics.total_requests

        # Update token usage
        if hasattr(result, 'tokens_used') and result.tokens_used:
            self.metrics.total_tokens_used += result.tokens_used

    def _add_to_history(self, result: AgentResult) -> None:
        """Add result to request history."""
        self._request_history.append(result)

        # Maintain history size limit
        if len(self._request_history) > self._max_history_size:
            self._request_history = self._request_history[-self._max_history_size:]

    def __str__(self) -> str:
        return f"{self.agent_name} ({self.agent_id})"

    def __repr__(self) -> str:
        return (
            f"BaseAgent(id='{self.agent_id}', name='{self.agent_name}', "
            f"capabilities={self.capabilities}, status={self.status})"
        )