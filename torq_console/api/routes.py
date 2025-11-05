"""
TORQ Console API Routes

RESTful API endpoints for agent management, chat sessions,
and system status.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from torq_console.agents.marvin_prince_flowers import (
    MarvinPrinceFlowers,
    create_prince_flowers_agent,
)
from torq_console.agents.marvin_orchestrator import (
    MarvinAgentOrchestrator,
    OrchestrationMode,
    get_orchestrator,
)
from torq_console.agents.marvin_query_router import (
    MarvinQueryRouter,
    create_query_router,
)

# Configure logging
logger = logging.getLogger("TORQ.API.Routes")

# Create router
router = APIRouter(tags=["TORQ Console API"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================


class AgentInfo(BaseModel):
    """Information about an available agent."""

    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="Agent description")
    capabilities: list[str] = Field(..., description="Agent capabilities")
    status: str = Field(default="active", description="Agent status")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent performance metrics",
    )


class ChatMessage(BaseModel):
    """Chat message request."""

    message: str = Field(..., description="User message text", min_length=1)
    context: Optional[dict[str, Any]] = Field(
        None,
        description="Optional context information",
    )
    mode: Optional[str] = Field(
        "single_agent",
        description="Orchestration mode (single_agent, multi_agent, pipeline, parallel)",
    )


class ChatResponse(BaseModel):
    """Chat message response."""

    response: str = Field(..., description="Agent response text")
    agent_id: str = Field(..., description="Agent that generated response")
    timestamp: str = Field(..., description="Response timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata",
    )


class SessionInfo(BaseModel):
    """Chat session information."""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: str = Field(..., description="Session creation timestamp")
    agent_id: str = Field(..., description="Associated agent ID")
    message_count: int = Field(default=0, description="Number of messages in session")
    status: str = Field(default="active", description="Session status")


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    agent_id: str = Field(..., description="Agent ID for the session")
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Optional session metadata",
    )


class SystemStatus(BaseModel):
    """System status information."""

    status: str = Field(..., description="Overall system status")
    agents_active: int = Field(..., description="Number of active agents")
    sessions_active: int = Field(..., description="Number of active sessions")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="System metrics",
    )


# ============================================================================
# Global State Management
# ============================================================================


class AgentManager:
    """Manages agent instances and sessions."""

    def __init__(self) -> None:
        """Initialize agent manager."""
        self.orchestrator: MarvinAgentOrchestrator = get_orchestrator()
        self.router: MarvinQueryRouter = create_query_router()
        self.prince_flowers: MarvinPrinceFlowers = create_prince_flowers_agent()

        self.sessions: dict[str, dict[str, Any]] = {}
        self.startup_time = datetime.now()

        logger.info("Agent manager initialized")

    async def get_agent_info(self, agent_id: str) -> AgentInfo:
        """
        Get information about a specific agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            AgentInfo with agent details.

        Raises:
            HTTPException: If agent not found.
        """
        agents_map = {
            "prince_flowers": {
                "name": "Prince Flowers",
                "description": "Enhanced conversational AI assistant with code, task, and general chat capabilities",
                "capabilities": [
                    "general_chat",
                    "code_generation",
                    "task_planning",
                    "documentation",
                ],
            },
            "orchestrator": {
                "name": "Agent Orchestrator",
                "description": "Coordinates multiple agents for complex tasks",
                "capabilities": [
                    "multi_agent_coordination",
                    "workflow_orchestration",
                    "intelligent_routing",
                ],
            },
            "query_router": {
                "name": "Query Router",
                "description": "Intelligently routes queries to appropriate agents",
                "capabilities": [
                    "intent_classification",
                    "query_analysis",
                    "agent_selection",
                ],
            },
        }

        if agent_id not in agents_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found",
            )

        agent_data = agents_map[agent_id]

        # Get metrics based on agent type
        if agent_id == "prince_flowers":
            metrics = self.prince_flowers.get_metrics()
        elif agent_id == "orchestrator":
            metrics = self.orchestrator.get_comprehensive_metrics()
        elif agent_id == "query_router":
            metrics = self.router.get_metrics()
        else:
            metrics = {}

        return AgentInfo(
            id=agent_id,
            name=agent_data["name"],
            description=agent_data["description"],
            capabilities=agent_data["capabilities"],
            status="active",
            metrics=metrics,
        )

    async def process_chat(
        self,
        agent_id: str,
        message: str,
        context: Optional[dict[str, Any]] = None,
        mode: str = "single_agent",
    ) -> ChatResponse:
        """
        Process a chat message with the specified agent.

        Args:
            agent_id: Agent to use for processing.
            message: User message.
            context: Optional context information.
            mode: Orchestration mode.

        Returns:
            ChatResponse with agent's reply.

        Raises:
            HTTPException: If processing fails.
        """
        try:
            # Map mode string to OrchestrationMode enum
            orchestration_modes = {
                "single_agent": OrchestrationMode.SINGLE_AGENT,
                "multi_agent": OrchestrationMode.MULTI_AGENT,
                "pipeline": OrchestrationMode.PIPELINE,
                "parallel": OrchestrationMode.PARALLEL,
            }

            selected_mode = orchestration_modes.get(
                mode,
                OrchestrationMode.SINGLE_AGENT,
            )

            # Process through orchestrator for intelligent routing
            result = await self.orchestrator.process_query(
                message,
                context=context,
                mode=selected_mode,
            )

            # Extract response based on result type
            if isinstance(result.primary_response, str):
                response_text = result.primary_response
            else:
                response_text = str(result.primary_response)

            return ChatResponse(
                response=response_text,
                agent_id=agent_id,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "mode": mode,
                    "routing_decision": (
                        {
                            "primary_agent": result.routing_decision.primary_agent,
                            "capabilities": [
                                cap.value
                                for cap in result.routing_decision.capabilities_needed
                            ],
                        }
                        if result.routing_decision
                        else None
                    ),
                    "success": result.success,
                    **result.metadata,
                },
            )

        except Exception as e:
            logger.error(f"Failed to process chat message: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process message: {str(e)}",
            ) from e

    def create_session(
        self,
        agent_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SessionInfo:
        """
        Create a new chat session.

        Args:
            agent_id: Agent ID for the session.
            metadata: Optional session metadata.

        Returns:
            SessionInfo with session details.
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "status": "active",
            "metadata": metadata or {},
        }

        self.sessions[session_id] = session_data
        logger.info(f"Created session {session_id} for agent {agent_id}")

        return SessionInfo(**session_data)

    def get_session(self, session_id: str) -> SessionInfo:
        """
        Get session information.

        Args:
            session_id: Session identifier.

        Returns:
            SessionInfo with session details.

        Raises:
            HTTPException: If session not found.
        """
        session_data = self.sessions.get(session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found",
            )

        return SessionInfo(**session_data)

    def list_sessions(self) -> list[SessionInfo]:
        """
        List all active sessions.

        Returns:
            List of SessionInfo objects.
        """
        return [SessionInfo(**session) for session in self.sessions.values()]

    def get_system_status(self) -> SystemStatus:
        """
        Get overall system status.

        Returns:
            SystemStatus with system information.
        """
        uptime = (datetime.now() - self.startup_time).total_seconds()

        return SystemStatus(
            status="healthy",
            agents_active=3,  # prince_flowers, orchestrator, query_router
            sessions_active=len(self.sessions),
            uptime_seconds=uptime,
            metrics=self.orchestrator.get_comprehensive_metrics(),
        )


# Global agent manager instance
agent_manager = AgentManager()


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """
    List all available agents.

    Returns:
        List of AgentInfo objects with agent details.

    Example:
        >>> response = requests.get("http://localhost:8899/api/agents")
        >>> agents = response.json()
    """
    agent_ids = ["prince_flowers", "orchestrator", "query_router"]

    agents = []
    for agent_id in agent_ids:
        try:
            agent_info = await agent_manager.get_agent_info(agent_id)
            agents.append(agent_info)
        except Exception as e:
            logger.error(f"Failed to get info for agent {agent_id}: {e}")

    return agents


@router.get("/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str) -> AgentInfo:
    """
    Get information about a specific agent.

    Args:
        agent_id: Unique agent identifier.

    Returns:
        AgentInfo with agent details.

    Raises:
        HTTPException: If agent not found (404).

    Example:
        >>> response = requests.get("http://localhost:8899/api/agents/prince_flowers")
        >>> agent = response.json()
    """
    return await agent_manager.get_agent_info(agent_id)


@router.post("/agents/{agent_id}/chat", response_model=ChatResponse)
async def send_message(agent_id: str, message: ChatMessage) -> ChatResponse:
    """
    Send a message to an agent and get a response.

    Args:
        agent_id: Agent to send message to.
        message: ChatMessage with user message and optional context.

    Returns:
        ChatResponse with agent's reply.

    Raises:
        HTTPException: If agent not found (404) or processing fails (500).

    Example:
        >>> response = requests.post(
        ...     "http://localhost:8899/api/agents/prince_flowers/chat",
        ...     json={"message": "How do I implement JWT auth?"}
        ... )
        >>> chat_response = response.json()
    """
    # Verify agent exists
    await agent_manager.get_agent_info(agent_id)

    return await agent_manager.process_chat(
        agent_id,
        message.message,
        context=message.context,
        mode=message.mode or "single_agent",
    )


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions() -> list[SessionInfo]:
    """
    List all chat sessions.

    Returns:
        List of SessionInfo objects.

    Example:
        >>> response = requests.get("http://localhost:8899/api/sessions")
        >>> sessions = response.json()
    """
    return agent_manager.list_sessions()


@router.post("/sessions", response_model=SessionInfo, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest) -> SessionInfo:
    """
    Create a new chat session.

    Args:
        request: CreateSessionRequest with agent_id and optional metadata.

    Returns:
        SessionInfo for the newly created session.

    Raises:
        HTTPException: If agent not found (404).

    Example:
        >>> response = requests.post(
        ...     "http://localhost:8899/api/sessions",
        ...     json={"agent_id": "prince_flowers"}
        ... )
        >>> session = response.json()
    """
    # Verify agent exists
    await agent_manager.get_agent_info(request.agent_id)

    return agent_manager.create_session(
        request.agent_id,
        metadata=request.metadata,
    )


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str) -> SessionInfo:
    """
    Get information about a specific session.

    Args:
        session_id: Unique session identifier.

    Returns:
        SessionInfo with session details.

    Raises:
        HTTPException: If session not found (404).

    Example:
        >>> response = requests.get("http://localhost:8899/api/sessions/{session_id}")
        >>> session = response.json()
    """
    return agent_manager.get_session(session_id)


@router.get("/status", response_model=SystemStatus)
async def get_status() -> SystemStatus:
    """
    Get system status and metrics.

    Returns:
        SystemStatus with overall system health and metrics.

    Example:
        >>> response = requests.get("http://localhost:8899/api/status")
        >>> status = response.json()
    """
    return agent_manager.get_system_status()
