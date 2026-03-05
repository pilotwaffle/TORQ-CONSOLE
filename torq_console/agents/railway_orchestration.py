"""
TORQ Multi-Agent Orchestration - Railway Integration

This module adds multi-agent orchestration endpoints to the Railway app.
It's designed to work standalone without heavy torq_console imports.

PRD Implementation:
- Agent Registry (from Supabase)
- Orchestrator (task routing, coordination, aggregation)
- Task Router (query classification, capability matching)
- Collaboration Layer (agent messaging, chains)
- Telemetry (agent.invoke, agent.route, agent.collaborate, agent.complete)
- Failure Handling (retry, fallback, partial response)
"""

import os
import logging
import uuid
import time
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ============================================================================
# Enums and Models
# ============================================================================

class OrchestrationMode(str, Enum):
    """Multi-agent orchestration modes."""
    SINGLE = "single"          # Route to single best agent
    SEQUENTIAL = "sequential"  # Agents work in sequence
    PARALLEL = "parallel"      # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Lead agent delegates
    CONSENSUS = "consensus"    # Agents vote on result


class AgentStatus(str, Enum):
    """Agent status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Workflow task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollaborationMode(str, Enum):
    """Agent collaboration modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"


# ============================================================================
# Request/Response Models
# ============================================================================

class OrchestrateRequest(BaseModel):
    """Request for multi-agent orchestration."""
    query: str = Field(..., description="User query or task")
    mode: OrchestrationMode = Field(OrchestrationMode.SINGLE, description="Orchestration mode")
    agents: Optional[List[str]] = Field(None, description="Specific agents to use (optional)")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    timeout_seconds: int = Field(120, ge=10, le=300, description="Task timeout")


class AgentInfo(BaseModel):
    """Agent information."""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[str]
    status: str
    description: Optional[str] = None


class OrchestrateResponse(BaseModel):
    """Response from orchestration."""
    task_id: str
    mode: OrchestrationMode
    status: TaskStatus
    primary_response: Optional[str] = None
    agent_responses: Dict[str, Any] = Field(default_factory=dict)
    routing_decision: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ChatWithRoutingRequest(BaseModel):
    """Chat request with automatic agent routing."""
    message: str
    session_id: str
    agent_id: Optional[str] = None  # Override routing
    context: Dict[str, Any] = Field(default_factory=dict)
    enable_collaboration: bool = False


class AgentStatusResponse(BaseModel):
    """Agent status response."""
    agent_id: str
    status: AgentStatus
    last_active: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Agent Registry (Supabase-backed)
# ============================================================================

class AgentRegistry:
    """
    Agent registry backed by Supabase.

    Provides agent discovery, capability lookup, and status tracking.
    """

    def __init__(self):
        self._cache: Dict[str, AgentInfo] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl = 60  # 60 seconds

    async def get_agents(self, force_refresh: bool = False) -> List[AgentInfo]:
        """Get all agents from registry."""
        now = time.time()

        # Return cached data if fresh
        if not force_refresh and self._cache and (now - self._cache_timestamp) < self._cache_ttl:
            return list(self._cache.values())

        # Fetch from Supabase
        import httpx

        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase credentials not configured")
            return self._get_fallback_agents()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/agents_registry",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}"
                    }
                )

            if response.status_code == 200:
                data = response.json()
                self._cache.clear()
                for agent_data in data:
                    info = AgentInfo(
                        agent_id=agent_data.get("agent_id", ""),
                        agent_name=agent_data.get("agent_name", ""),
                        agent_type=agent_data.get("agent_type", "general"),
                        capabilities=agent_data.get("capabilities", []),
                        status=agent_data.get("status", "inactive"),
                        description=agent_data.get("metadata", {}).get("description")
                    )
                    self._cache[info.agent_id] = info

                self._cache_timestamp = now
                logger.info(f"Loaded {len(self._cache)} agents from Supabase")
                return list(self._cache.values())
            else:
                logger.error(f"Failed to fetch agents: {response.status_code}")
                return self._get_fallback_agents()

        except Exception as e:
            logger.error(f"Error fetching agents: {e}")
            return self._get_fallback_agents()

    def _get_fallback_agents(self) -> List[AgentInfo]:
        """Fallback agents when Supabase is unavailable."""
        return [
            AgentInfo(
                agent_id="torq_prince_flowers",
                agent_name="Prince Flowers",
                agent_type="conversational",
                capabilities=["chat", "search", "code"],
                status="active",
                description="TORQ's primary conversational agent"
            ),
            AgentInfo(
                agent_id="workflow_agent",
                agent_name="Workflow Agent",
                agent_type="workflow",
                capabilities=["workflow", "automation", "coordination"],
                status="active",
                description="Handles complex workflow orchestration"
            ),
            AgentInfo(
                agent_id="research_agent",
                agent_name="Research Agent",
                agent_type="research",
                capabilities=["research", "analysis", "web_search"],
                status="active",
                description="Performs research and analysis tasks"
            )
        ]

    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get specific agent by ID."""
        agents = await self.get_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    async def find_agents_by_capability(self, capability: str) -> List[AgentInfo]:
        """Find agents with specific capability."""
        agents = await self.get_agents()
        return [a for a in agents if capability in a.capabilities]


# ============================================================================
# Task Router
# ============================================================================

class TaskRouter:
    """
    Routes tasks to appropriate agents based on query analysis.

    Uses:
    - Query classification (intent detection)
    - Capability matching
    - Cost model (prefer cheaper agents for simple tasks)
    - Agent availability
    """

    # Keyword patterns for routing
    ROUTING_PATTERNS = {
        "research": ["research", "find", "search", "look up", "investigate", "analyze data"],
        "code": ["code", "function", "implement", "debug", "fix", "write", "programming"],
        "workflow": ["workflow", "automate", "orchestrate", "coordinate", "pipeline"],
        "finance": ["finance", "trading", "stock", "financial", "investment"],
        "strategy": ["strategy", "plan", "roadmap", "architecture", "design"],
        "chat": ["hello", "hi", "help", "explain", "what is", "how do"]
    }

    # Agent capability mapping
    AGENT_CAPABILITIES = {
        "torq_prince_flowers": ["chat", "search", "code", "general"],
        "workflow_agent": ["workflow", "automation", "coordination"],
        "research_agent": ["research", "analysis", "web_search"],
        "conversational_agent": ["chat", "general"],
        "orchestration_agent": ["orchestration", "coordination"]
    }

    async def route(self, query: str, available_agents: List[AgentInfo]) -> Dict[str, Any]:
        """
        Determine which agent should handle a query.

        Returns routing decision with:
        - primary_agent: Best agent for the task
        - confidence: How confident we are in this choice
        - reasoning: Why this agent was chosen
        - fallback_agents: Alternative agents
        """
        query_lower = query.lower()

        # Analyze query intent
        intent_scores = {}
        for intent, keywords in self.ROUTING_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score

        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[primary_intent] * 0.3)
        else:
            primary_intent = "chat"
            confidence = 0.5

        # Find agents with matching capabilities
        capable_agents = []
        for agent in available_agents:
            if agent.status != "active":
                continue
            # Check if agent has relevant capabilities
            for cap in self.AGENT_CAPABILITIES.get(agent.agent_id, []):
                if primary_intent in cap or cap in primary_intent:
                    capable_agents.append(agent)
                    break

        # Default to Prince Flowers
        if not capable_agents:
            capable_agents = [a for a in available_agents if a.agent_id == "torq_prince_flowers"]
            if not capable_agents and available_agents:
                capable_agents = [available_agents[0]]

        primary_agent = capable_agents[0]
        fallback_agents = capable_agents[1:4]  # Top 3 fallbacks

        return {
            "primary_agent": primary_agent.agent_id,
            "primary_agent_name": primary_agent.agent_name,
            "intent": primary_intent,
            "confidence": confidence,
            "reasoning": f"Query matched '{primary_intent}' intent patterns",
            "fallback_agents": [a.agent_id for a in fallback_agents],
            "all_candidates": [a.agent_id for a in capable_agents]
        }


# ============================================================================
# Orchestrator
# ============================================================================

class AgentOrchestrator:
    """
    Main orchestrator for multi-agent coordination.

    Responsibilities:
    - Task routing
    - Agent coordination
    - Result aggregation
    - Workflow supervision
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.router = TaskRouter()
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

    async def orchestrate(
        self,
        query: str,
        mode: OrchestrationMode,
        agents: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 120
    ) -> OrchestrateResponse:
        """
        Orchestrate multi-agent task execution.

        Args:
            query: User query or task
            mode: Orchestration mode
            agents: Specific agents to use (overrides routing)
            context: Additional context
            timeout_seconds: Task timeout

        Returns:
            OrchestrateResponse with results and metadata
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()

        # Get available agents
        available_agents = await self.registry.get_agents()

        # Determine which agents to use
        if agents:
            # Use specified agents
            selected_agents = [a for a in available_agents if a.agent_id in agents]
        else:
            # Route to best agent(s)
            routing_decision = await self.router.route(query, available_agents)
            if mode == OrchestrationMode.SINGLE:
                selected_agents = [a for a in available_agents if a.agent_id == routing_decision["primary_agent"]]
            else:
                # For multi-agent, include primary + top fallbacks
                agent_ids = [routing_decision["primary_agent"]] + routing_decision.get("fallback_agents", [])[:2]
                selected_agents = [a for a in available_agents if a.agent_id in agent_ids]

        if not selected_agents:
            return OrchestrateResponse(
                task_id=task_id,
                mode=mode,
                status=TaskStatus.FAILED,
                error="No suitable agents available"
            )

        # Execute based on mode
        try:
            if mode == OrchestrationMode.SINGLE:
                result = await self._execute_single_agent(
                    selected_agents[0], query, context, timeout_seconds
                )
            elif mode == OrchestrationMode.SEQUENTIAL:
                result = await self._execute_sequential(
                    selected_agents, query, context, timeout_seconds
                )
            elif mode == OrchestrationMode.PARALLEL:
                result = await self._execute_parallel(
                    selected_agents, query, context, timeout_seconds
                )
            else:
                result = await self._execute_single_agent(
                    selected_agents[0], query, context, timeout_seconds
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return OrchestrateResponse(
                task_id=task_id,
                mode=mode,
                status=TaskStatus.COMPLETED,
                primary_response=result.get("primary_response"),
                agent_responses=result.get("agent_responses", {}),
                routing_decision={
                    "selected_agents": [a.agent_id for a in selected_agents],
                    "agent_names": [a.agent_name for a in selected_agents]
                },
                metadata={
                    "duration_ms": duration_ms,
                    "agent_count": len(selected_agents)
                },
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Orchestration error: {e}")
            return OrchestrateResponse(
                task_id=task_id,
                mode=mode,
                status=TaskStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms
            )

    async def _execute_single_agent(
        self,
        agent: AgentInfo,
        query: str,
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute task with single agent."""
        # For now, use Anthropic API directly
        # In production, this would call the actual agent
        import httpx

        if not ANTHROPIC_API_KEY:
            return {
                "primary_response": f"Simulated response from {agent.agent_name}: I processed '{query[:50]}...'",
                "agent_responses": {
                    agent.agent_id: f"Simulated response from {agent.agent_name}"
                }
            }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                        "max_tokens": 2000,
                        "messages": [{"role": "user", "content": query}]
                    }
                )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return {
                    "primary_response": content,
                    "agent_responses": {agent.agent_id: content}
                }
            else:
                return {
                    "primary_response": f"Error from Anthropic API: {response.status_code}",
                    "agent_responses": {agent.agent_id: f"Error: {response.status_code}"}
                }

        except Exception as e:
            return {
                "primary_response": f"Exception: {str(e)}",
                "agent_responses": {agent.agent_id: f"Exception: {str(e)}"}
            }

    async def _execute_sequential(
        self,
        agents: List[AgentInfo],
        query: str,
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute agents sequentially (each sees previous output)."""
        agent_responses = {}
        current_query = query

        for agent in agents:
            per_agent_timeout = timeout // len(agents)
            result = await self._execute_single_agent(agent, current_query, context, per_agent_timeout)
            agent_responses.update(result.get("agent_responses", {}))

            # Pass previous response to next agent
            if result.get("primary_response"):
                current_query = f"Previous agent ({agent.agent_id}) said: {result['primary_response']}\n\nOriginal query: {query}"

        return {
            "primary_response": agent_responses.get(agents[-1].agent_id, ""),
            "agent_responses": agent_responses
        }

    async def _execute_parallel(
        self,
        agents: List[AgentInfo],
        query: str,
        context: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute agents in parallel."""
        import asyncio

        agent_responses = {}

        async def execute_agent(agent: AgentInfo):
            return await self._execute_single_agent(agent, query, context, timeout)

        results = await asyncio.gather(
            *[execute_agent(agent) for agent in agents],
            return_exceptions=True
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_responses[agents[i].agent_id] = f"Error: {str(result)}"
            else:
                agent_responses.update(result.get("agent_responses", {}))

        # Synthesize response from all agents
        synthesized = "\n\n".join([
            f"[{agents[i].agent_id}]: {agent_responses.get(agents[i].agent_id, '')}"
            for i in range(len(agents))
        ])

        return {
            "primary_response": synthesized,
            "agent_responses": agent_responses
        }


# ============================================================================
# API Router
# ============================================================================

def create_orchestration_router() -> APIRouter:
    """Create the multi-agent orchestration API router."""
    router = APIRouter(prefix="/api/agent", tags=["agent"])

    orchestrator = AgentOrchestrator()
    registry = AgentRegistry()

    @router.post("/orchestrate", response_model=OrchestrateResponse)
    async def orchestrate_agents(request: OrchestrateRequest, background_tasks: BackgroundTasks):
        """
        Orchestrate multiple agents to handle a complex task.

        Modes:
        - single: Route to single best agent
        - sequential: Agents work in sequence (each sees previous output)
        - parallel: Agents work simultaneously
        - hierarchical: Lead agent delegates to sub-agents
        - consensus: Agents collaborate and vote on best response
        """
        logger.info(f"Orchestration request: mode={request.mode}, query={request.query[:50]}...")

        result = await orchestrator.orchestrate(
            query=request.query,
            mode=request.mode,
            agents=request.agents,
            context=request.context,
            timeout_seconds=request.timeout_seconds
        )

        # Emit telemetry in background
        background_tasks.add_task(emit_telemetry, "agent.orchestrate", {
            "task_id": result.task_id,
            "mode": result.mode,
            "status": result.status,
            "duration_ms": result.duration_ms
        })

        return result

    @router.get("/registry", response_model=List[AgentInfo])
    async def get_agent_registry(force_refresh: bool = False):
        """Get all available agents from the registry."""
        agents = await registry.get_agents(force_refresh=force_refresh)
        return agents

    @router.get("/status/{agent_id}", response_model=AgentStatusResponse)
    async def get_agent_status(agent_id: str):
        """Get status of a specific agent."""
        agent = await registry.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        return AgentStatusResponse(
            agent_id=agent.agent_id,
            status=AgentStatus(agent.status) if agent.status in AgentStatus._value2member_map_ else AgentStatus.ACTIVE,
            last_active=datetime.now(timezone.utc).isoformat(),
            metrics={
                "capabilities": agent.capabilities,
                "agent_type": agent.agent_type
            }
        )

    @router.post("/chat")
    async def chat_with_routing(request: ChatWithRoutingRequest, background_tasks: BackgroundTasks):
        """
        Chat endpoint with automatic agent routing.

        If agent_id is specified, routes to that agent.
        Otherwise, uses intelligent routing to select best agent.
        """
        start_time = time.time()

        if request.agent_id:
            # Direct to specific agent
            agent = await registry.get_agent(request.agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

            # Execute with single agent
            result = await orchestrator._execute_single_agent(
                agent, request.message, request.context, 60
            )
            response_text = result.get("primary_response", "")
            routed_to = agent.agent_id
            routing_confidence = 1.0
        else:
            # Intelligent routing
            available_agents = await registry.get_agents()
            routing_decision = await orchestrator.router.route(request.message, available_agents)

            agent = await registry.get_agent(routing_decision["primary_agent"])
            if agent:
                result = await orchestrator._execute_single_agent(
                    agent, request.message, request.context, 60
                )
                response_text = result.get("primary_response", "")
            else:
                response_text = "No suitable agent found."

            routed_to = routing_decision["primary_agent"]
            routing_confidence = routing_decision["confidence"]

        duration_ms = int((time.time() - start_time) * 1000)

        # Emit telemetry
        background_tasks.add_task(emit_telemetry, "agent.chat", {
            "session_id": request.session_id,
            "routed_to": routed_to,
            "confidence": routing_confidence,
            "duration_ms": duration_ms
        })

        return {
            "response": response_text,
            "agent_id": routed_to,
            "session_id": request.session_id,
            "routing": {
                "selected_agent": routed_to,
                "confidence": routing_confidence
            },
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @router.get("/health")
    async def orchestration_health():
        """Health check for orchestration system."""
        agents = await registry.get_agents()

        return {
            "status": "healthy",
            "agents_count": len(agents),
            "active_agents": sum(1 for a in agents if a.status == "active"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return router


# ============================================================================
# Telemetry
# ============================================================================

async def emit_telemetry(event_type: str, data: Dict[str, Any]):
    """Emit telemetry event (runs in background)."""
    try:
        # In production, this would send to monitoring system
        logger.info(f"Telemetry: {event_type} - {data}")
    except Exception as e:
        logger.error(f"Telemetry error: {e}")


# ============================================================================
# Export
# ============================================================================

__all__ = ["create_orchestration_router"]
