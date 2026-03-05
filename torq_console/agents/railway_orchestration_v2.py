"""
TORQ Multi-Agent Orchestration - Railway Integration v2

UNIFIED API CONTRACT per user feedback:
- Single endpoint for all chat/orchestration
- Consistent request contract
- Explicit agent selection OR auto-routing
- Mode-based orchestration when not single

Frontend → Backend Contract:

{
  "message": "...",
  "session_id": "...",
  "agent_id": "research_agent",  // Optional: if provided, use it (no routing)
  "mode": "single",              // Optional: single | auto | sequential | parallel | consensus | hierarchical
  "context": {}                  // Optional: additional context
}

Rules:
- If agent_id is provided → use that agent (no routing)
- If agent_id is null → auto-route based on query
- If mode is "single" or "auto" → single agent response
- If mode is multi-agent mode → orchestrate multiple agents

Default behavior:
- agent_id: null (auto-route)
- mode: "auto" (system chooses best approach)
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

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# ============================================================================
# Enums
# ============================================================================

class ExecutionMode(str, Enum):
    """Execution mode for agent requests."""
    AUTO = "auto"              # System chooses best approach
    SINGLE = "single"          # One agent (use specified or auto-routed)
    SEQUENTIAL = "sequential"  # Agents work in sequence
    PARALLEL = "parallel"      # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Lead agent delegates
    CONSENSUS = "consensus"    # Agents collaborate and vote


class AgentSpeed(str, Enum):
    """Agent speed characterization."""
    FAST = "fast"      # Quick responses, less depth
    BALANCED = "balanced"
    DEEP = "deep"      # More thorough, slower


# ============================================================================
# Unified Request/Response Models
# ============================================================================

class UnifiedChatRequest(BaseModel):
    """
    Unified chat request contract v1.

    Version 1 contract - all fields are optional except message.
    Frontend should include v field for contract validation.
    """
    v: int = Field(1, description="Contract version", ge=1, le=1)
    message: str = Field(..., description="User message or query", min_length=1, max_length=10000)
    session_id: str = Field(..., description="Session ID for conversation tracking")
    agent_id: Optional[str] = Field(
        None,
        description="Specific agent to use. If null, system auto-routes."
    )
    mode: ExecutionMode = Field(
        ExecutionMode.AUTO,
        description="Execution mode. AUTO lets system decide based on query complexity."
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the request"
    )
    timeout_seconds: int = Field(
        120,
        ge=10,
        le=300,
        description="Maximum time for execution"
    )
    # Trace continuity
    trace_id: Optional[str] = Field(None, description="External trace ID for observability")
    request_id: Optional[str] = Field(None, description="Unique request ID")


class UnifiedChatResponse(BaseModel):
    """
    Unified chat response v1.

    Version 1 response contract with structured routing and evaluation confidence.
    """
    v: int = Field(1, description="Contract version")
    # Core response
    text: str = Field(..., description="The assistant's response text")
    session_id: str
    # Agent info
    agent_id_used: str = Field(..., description="Agent that handled the request")
    mode_used: ExecutionMode
    agents_involved: List[str] = Field(default_factory=list)
    # Routing (only meaningful when agent_id was null)
    routing: Optional[Dict[str, Any]] = Field(
        None,
        description="Routing decision when agent was auto-selected. Contains: selected_agent, confidence, reasoning"
    )
    # Evaluation (optional, when quality evaluation is enabled)
    evaluation: Optional[Dict[str, Any]] = Field(
        None,
        description="Quality evaluation when enabled. Contains: confidence, checks, score"
    )
    # Trace continuity
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    # Timing
    duration_ms: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Errors
    error: Optional[str] = None


class AgentCard(BaseModel):
    """Agent card for UI display with extended info."""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[str]
    status: str
    description: Optional[str] = None
    speed: AgentSpeed = Field(AgentSpeed.BALANCED, description="Response speed characteristic")
    best_for: List[str] = Field(default_factory=list, description="Recommended use cases")
    tools: List[str] = Field(default_factory=list, description="Tools this agent can use")


# ============================================================================
# Enhanced Agent Registry with UI Metadata
# ============================================================================

class EnhancedAgentRegistry:
    """
    Agent registry with UI-friendly metadata.
    """

    def __init__(self):
        self._cache: Dict[str, AgentCard] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl = 60

        # Extended metadata for agents (matches Supabase IDs)
        self._agent_metadata: Dict[str, Dict[str, Any]] = {
            "torq_prince_flowers": {
                "speed": AgentSpeed.BALANCED,
                "best_for": ["General chat", "Complex questions", "Multi-step reasoning"],
                "tools": ["Web Search", "Code Execution", "File Access"],
                "description": "TORQ's primary agent with enhanced capabilities"
            },
            "conversational_agent": {
                "speed": AgentSpeed.FAST,
                "best_for": ["Quick answers", "Conversation", "Follow-up questions"],
                "tools": ["Memory", "Learning"],
                "description": "Fast conversational agent with context memory"
            },
            "workflow_agent": {
                "speed": AgentSpeed.DEEP,
                "best_for": ["Code generation", "Debugging", "Testing", "Architecture"],
                "tools": ["Code Editor", "Test Runner", "Linter", "Documentation"],
                "description": "Comprehensive workflow agent for coding tasks"
            },
            "research_agent": {
                "speed": AgentSpeed.DEEP,
                "best_for": ["Research", "Analysis", "Information gathering"],
                "tools": ["Web Search", "Document Analysis", "Data Extraction"],
                "description": "Deep research and analysis agent"
            },
            "orchestration_agent": {
                "speed": AgentSpeed.BALANCED,
                "best_for": ["Multi-agent coordination", "Complex workflows", "Planning"],
                "tools": ["Agent Router", "Task Planner", "Result Aggregator"],
                "description": "Orchestrates multiple agents for complex tasks"
            }
        }

    async def get_agents(self, force_refresh: bool = False) -> List[AgentCard]:
        """Get all agents with UI metadata."""
        now = time.time()

        if not force_refresh and self._cache and (now - self._cache_timestamp) < self._cache_ttl:
            return list(self._cache.values())

        import httpx

        if not SUPABASE_URL or not SUPABASE_KEY:
            return self._get_fallback_cards()

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
                    agent_id = agent_data.get("agent_id", "")
                    metadata = self._agent_metadata.get(agent_id, {})

                    card = AgentCard(
                        agent_id=agent_id,
                        agent_name=agent_data.get("agent_name", ""),
                        agent_type=agent_data.get("agent_type", "general"),
                        capabilities=agent_data.get("capabilities", []),
                        status=agent_data.get("status", "inactive"),
                        description=agent_data.get("metadata", {}).get("description") or metadata.get("description"),
                        speed=metadata.get("speed", AgentSpeed.BALANCED),
                        best_for=metadata.get("best_for", []),
                        tools=metadata.get("tools", [])
                    )
                    self._cache[agent_id] = card

                self._cache_timestamp = now
                logger.info(f"Loaded {len(self._cache)} agent cards from Supabase")
                return list(self._cache.values())
            else:
                return self._get_fallback_cards()

        except Exception as e:
            logger.error(f"Error fetching agents: {e}")
            return self._get_fallback_cards()

    def _get_fallback_cards(self) -> List[AgentCard]:
        """Fallback agent cards when Supabase is unavailable."""
        cards = []
        for agent_id, metadata in self._agent_metadata.items():
            cards.append(AgentCard(
                agent_id=agent_id,
                agent_name=metadata["description"].split('.')[0] if metadata.get("description") else agent_id.replace("_", " ").title(),
                agent_type="general",
                capabilities=metadata.get("tools", []),
                status="active",
                description=metadata.get("description", ""),
                speed=metadata["speed"],
                best_for=metadata["best_for"],
                tools=metadata["tools"]
            ))
        return cards

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get specific agent by ID."""
        agents = await self.get_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                return agent
        return None


# ============================================================================
# Unified Orchestrator
# ============================================================================

class UnifiedOrchestrator:
    """
    Unified orchestrator with consistent contract.
    """

    def __init__(self):
        self.registry = EnhancedAgentRegistry()

        # Routing patterns
        self.routing_patterns = {
            "research": ["research", "find", "search", "look up", "investigate", "analyze data"],
            "code": ["code", "function", "implement", "debug", "fix", "write", "programming", "refactor"],
            "workflow": ["workflow", "automate", "orchestrate", "coordinate", "pipeline"],
            "chat": ["hello", "hi", "help", "explain", "what is", "how do", "can you"],
            "complex": ["analyze", "design", "plan", "architecture", "strategy"]
        }

    async def chat(self, request: UnifiedChatRequest) -> UnifiedChatResponse:
        """
        Unified chat endpoint.

        Contract:
        - agent_id provided → use that agent
        - agent_id null → auto-route based on query
        - mode AUTO → system chooses best approach
        - mode multi-agent → orchestrate
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Get available agents
            available_agents = await self.registry.get_agents()
            active_agents = [a for a in available_agents if a.status == "active"]

            if not active_agents:
                return UnifiedChatResponse(
                    v=1,
                    text="No agents available",
                    session_id=request.session_id,
                    agent_id_used="system",
                    mode_used=request.mode,
                    error="No active agents",
                    duration_ms=0
                )

            # Determine agent selection
            selected_agent = None
            routed_to = None
            routing_confidence = 0.0

            if request.agent_id:
                # Explicit agent selection
                selected_agent = await self.registry.get_agent(request.agent_id)
                if not selected_agent:
                    return UnifiedChatResponse(
                        v=1,
                        text=f"Agent {request.agent_id} not found",
                        session_id=request.session_id,
                        agent_id_used=request.agent_id,
                        mode_used=request.mode,
                        error="Agent not found",
                        duration_ms=0
                    )
                routed_to = request.agent_id
                routing_confidence = 1.0
            else:
                # Auto-routing
                routing = await self._route_request(request.message, active_agents)
                selected_agent = await self.registry.get_agent(routing["agent_id"])
                routed_to = routing["agent_id"]
                routing_confidence = routing["confidence"]

            if not selected_agent:
                selected_agent = active_agents[0]
                routed_to = selected_agent.agent_id

            # Determine execution mode
            mode_to_use = request.mode
            if mode_to_use == ExecutionMode.AUTO:
                # System chooses based on query complexity
                mode_to_use = await self._select_mode(request.message, routing_confidence)

            # Execute based on mode
            if mode_to_use == ExecutionMode.SINGLE:
                result = await self._execute_single(selected_agent, request.message, request.context)
                agents_involved = [selected_agent.agent_id]
            else:
                # Multi-agent orchestration
                result = await self._orchestrate_multi(
                    selected_agent,
                    active_agents,
                    request.message,
                    mode_to_use,
                    request.context
                )
                agents_involved = result.get("agents_involved", [selected_agent.agent_id])

            duration_ms = int((time.time() - start_time) * 1000)

            return UnifiedChatResponse(
                v=1,
                text=result.get("response", ""),
                session_id=request.session_id,
                agent_id_used=routed_to,
                mode_used=mode_to_use,
                agents_involved=agents_involved,
                routing={
                    "selected_agent": routed_to,
                    "confidence": routing_confidence,
                    "reasoning": "Explicit agent selection" if request.agent_id else "Agent selected based on query analysis"
                },
                trace_id=request.trace_id,
                request_id=request.request_id,
                metadata={
                    "task_id": task_id,
                    "duration_ms": duration_ms,
                    "agent_count": len(agents_involved)
                },
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Chat error: {e}")
            return UnifiedChatResponse(
                v=1,
                text=f"Error: {str(e)}",
                session_id=request.session_id,
                agent_id_used="system",
                mode_used=request.mode,
                error=str(e),
                duration_ms=duration_ms
            )

    async def _route_request(self, query: str, agents: List[AgentCard]) -> Dict[str, Any]:
        """Route request to best agent."""
        query_lower = query.lower()

        # Score each intent
        intent_scores = {}
        for intent, keywords in self.routing_patterns.items():
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

        # Find agent with matching capabilities
        for agent in agents:
            if primary_intent in agent.capabilities:
                return {"agent_id": agent.agent_id, "confidence": confidence}

        # Default to first active agent
        return {"agent_id": agents[0].agent_id, "confidence": 0.5}

    async def _select_mode(self, query: str, confidence: float) -> ExecutionMode:
        """Select execution mode based on query and routing confidence."""
        # Simple heuristics
        query_lower = query.lower()

        # Multi-agent indicators
        multi_agent_keywords = ["and then", "also", "additionally", "furthermore", "analyze from multiple"]
        if any(kw in query_lower for kw in multi_agent_keywords):
            return ExecutionMode.SEQUENTIAL

        # Complex task indicators
        complex_keywords = ["design", "plan", "architecture", "comprehensive", "detailed analysis"]
        if any(kw in query_lower for kw in complex_keywords):
            return ExecutionMode.PARALLEL

        # Default to single
        return ExecutionMode.SINGLE

    async def _execute_single(
        self,
        agent: AgentCard,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute with single agent."""
        import httpx

        if not ANTHROPIC_API_KEY:
            return {
                "response": f"[Simulated] {agent.agent_name}: I processed '{query[:50]}...'",
                "agents_involved": [agent.agent_id]
            }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
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
                return {"response": content, "agents_involved": [agent.agent_id]}
            else:
                return {
                    "response": f"API Error: {response.status_code}",
                    "agents_involved": [agent.agent_id]
                }

        except Exception as e:
            return {"response": f"Error: {str(e)}", "agents_involved": [agent.agent_id]}

    async def _orchestrate_multi(
        self,
        primary_agent: AgentCard,
        all_agents: List[AgentCard],
        query: str,
        mode: ExecutionMode,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate multiple agents."""
        # For now, simple parallel execution
        agents_to_use = all_agents[:3]  # Top 3 agents

        async def execute_agent(agent: AgentCard):
            return await self._execute_single(agent, query, context)

        results = await asyncio.gather(
            *[execute_agent(a) for a in agents_to_use],
            return_exceptions=True
        )

        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(f"{agents_to_use[i].agent_name}: Error")
            else:
                responses.append(result.get("response", ""))

        synthesized = "\n\n".join([
            f"**{agents_to_use[i].agent_name}**:\n{responses[i]}"
            for i in range(len(agents_to_use))
        ])

        return {
            "response": synthesized,
            "agents_involved": [a.agent_id for a in agents_to_use]
        }


# ============================================================================
# API Router - Unified Endpoints
# ============================================================================

def create_unified_router() -> APIRouter:
    """Create unified API router with consistent contract."""
    router = APIRouter(prefix="/api/chat", tags=["chat"])
    orchestrator = UnifiedOrchestrator()

    @router.post("", response_model=UnifiedChatResponse)
    async def unified_chat(request: UnifiedChatRequest, background_tasks: BackgroundTasks):
        """
        Unified chat endpoint.

        Contract:
        ```json
        {
          "message": "Your question",
          "session_id": "session-123",
          "agent_id": "research_agent",  // Optional - if null, auto-route
          "mode": "auto"                 // Optional - auto|single|sequential|parallel|consensus|hierarchical
        }
        ```

        Behavior:
        - agent_id provided → use that agent
        - agent_id null → auto-route based on query
        - mode "auto" → system chooses best approach
        - mode multi-agent → orchestrate multiple agents
        """
        logger.info(
            f"Chat request: agent={request.agent_id}, mode={request.mode}, "
            f"message={request.message[:50]}..."
        )

        result = await orchestrator.chat(request)

        # Emit telemetry
        background_tasks.add_task(emit_telemetry, "chat.unified", {
            "session_id": result.session_id,
            "agent_id": result.agent_id,
            "mode_used": result.mode_used.value,
            "agents_count": len(result.agents_involved),
            "duration_ms": result.duration_ms
        })

        return result

    @router.get("/agents", response_model=List[AgentCard])
    async def list_agents(force_refresh: bool = False):
        """
        List all available agents with UI metadata.

        Returns agent cards with:
        - capabilities
        - speed (fast/balanced/deep)
        - best_for (recommended use cases)
        - tools (available tools)
        """
        agents = await orchestrator.registry.get_agents(force_refresh=force_refresh)
        return agents

    @router.get("/agents/{agent_id}", response_model=AgentCard)
    async def get_agent_details(agent_id: str):
        """Get detailed information about a specific agent."""
        agent = await orchestrator.registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return agent

    @router.get("/health")
    async def health_check():
        """Health check for the unified chat system."""
        agents = await orchestrator.registry.get_agents()
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
    """Emit telemetry event."""
    logger.info(f"Telemetry: {event_type} - {data}")


# ============================================================================
# Export
# ============================================================================

__all__ = ["create_unified_router", "UnifiedChatRequest", "UnifiedChatResponse", "AgentCard"]
