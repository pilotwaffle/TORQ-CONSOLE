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

# Phase 2: Routing Override Import
from .routing.realtime_override import detect_routing_override, RoutingOverride

# Phase 3: Tool Policy Engine Import
from .tools.tool_policy_engine import ToolPolicyEngine, ToolPolicy

logger = logging.getLogger(__name__)

# ============================================================================
# Session Store Integration
# ============================================================================

try:
    from supabase import create_client
    from .session_store import SessionStore, get_session_store, set_session_store
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not available - session persistence disabled")

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
    RESEARCH = "research"      # Deep research with web search tools (Phase 2)


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
    Unified chat request contract.

    Supports both simple chat and multi-agent orchestration.
    """
    message: str = Field(..., description="User message or query", min_length=1)
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


class UnifiedChatResponse(BaseModel):
    """
    Canonical unified chat response v1.

    Field naming is consistent: agent_id_used (not agent), mode_used, routing_confidence.
    """
    # Core response - canonical field name
    text: str
    session_id: str
    # Agent info - canonical field name
    agent_id_used: str
    mode_used: ExecutionMode
    agents_involved: List[str] = Field(default_factory=list)
    # Routing - structured with confidence
    routing: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Routing info when agent was auto-selected: selected_agent, confidence, reasoning"
    )
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Timing
    latency_ms: int = Field(..., description="Response latency in milliseconds")
    # Errors
    error: Optional[str] = None

    # Legacy compatibility - deprecated, remove after frontend migrates
    response: Optional[str] = Field(None, deprecated=True, description="Legacy: use 'text' instead")
    agent_id: Optional[str] = Field(None, deprecated=True, description="Legacy: use 'agent_id_used' instead")
    duration_ms: Optional[int] = Field(None, deprecated=True, description="Legacy: use 'latency_ms' instead")


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

    def __init__(self, session_store: Optional["SessionStore"] = None):
        self.registry = EnhancedAgentRegistry()
        self.session_store = session_store

        # Initialize session store if not provided but Supabase is available
        if not self.session_store and SUPABASE_AVAILABLE:
            supabase_client = None
            try:
                if SUPABASE_URL and SUPABASE_KEY:
                    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                    self.session_store = SessionStore(supabase_client)
                    logger.info("Session store initialized with Supabase")
            except Exception as e:
                logger.warning(f"Failed to initialize session store: {e}")

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
        - agent_id provided → use that agent (routing override still applies for mode selection)
        - agent_id null → auto-route based on query
        - mode AUTO → system chooses best approach
        - mode multi-agent → orchestrate

        Phase 2 Enhancement:
        - Routing override runs FIRST, before agent selection
        - Forces RESEARCH mode for real-time queries (finance, news, lookups)
        - Ensures web search tools are available for override queries
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()

        # ======================================================================
        # PHASE 2: Routing Override Detection (HIGHEST PRIORITY)
        # ======================================================================
        # This runs BEFORE any agent selection or mode decision.
        # Real-time queries (finance, news, current events) get hard-routed
        # to RESEARCH mode with web search tools.
        routing_override: RoutingOverride = detect_routing_override(request.message)

        if routing_override.force_research:
            logger.info(
                f"Routing override triggered: query='{request.message[:100]}', "
                f"reason={routing_override.reason}, "
                f"matched_terms={routing_override.matched_terms}"
            )

        try:
            # Get available agents
            available_agents = await self.registry.get_agents()
            active_agents = [a for a in available_agents if a.status == "active"]

            if not active_agents:
                return UnifiedChatResponse(
                    text="No agents available",
                    response="No agents available",  # Legacy compatibility
                    session_id=request.session_id,
                    agent_id_used="system",
                    agent_id="system",  # Legacy compatibility
                    mode_used=request.mode,
                    error="No active agents",
                    latency_ms=0,
                    duration_ms=0  # Legacy compatibility
                )

            # Determine agent selection
            selected_agent = None
            routed_to = None
            routing_confidence = 0.0

            if request.agent_id:
                # Explicit agent selection (but override still affects mode/tools)
                selected_agent = await self.registry.get_agent(request.agent_id)
                if not selected_agent:
                    return UnifiedChatResponse(
                        text=f"Agent {request.agent_id} not found",
                        response=f"Agent {request.agent_id} not found",  # Legacy compatibility
                        session_id=request.session_id,
                        agent_id_used=request.agent_id,
                        agent_id=request.agent_id,  # Legacy compatibility
                        mode_used=request.mode,
                        error="Agent not found",
                        latency_ms=0,
                        duration_ms=0  # Legacy compatibility
                    )
                routed_to = request.agent_id
                routing_confidence = 1.0
            else:
                # Auto-routing
                # Phase 2: If override active, prioritize research-capable agents
                if routing_override.force_research:
                    # Prefer agents with web search capability
                    for agent in active_agents:
                        if "web search" in [t.lower() for t in agent.tools]:
                            selected_agent = agent
                            routed_to = agent.agent_id
                            routing_confidence = 1.0
                            logger.info(f"Routing override selected agent: {agent.agent_id} (has web_search)")
                            break

                # Fallback to normal routing if no agent matched or no override
                if not selected_agent:
                    routing = await self._route_request(request.message, active_agents)
                    selected_agent = await self.registry.get_agent(routing["agent_id"])
                    routed_to = routing["agent_id"]
                    routing_confidence = routing["confidence"]

            if not selected_agent:
                selected_agent = active_agents[0]
                routed_to = selected_agent.agent_id

            # Determine execution mode
            # Phase 2: Override forces RESEARCH mode
            mode_to_use = request.mode
            if routing_override.force_research:
                # Hard-route to RESEARCH mode
                mode_to_use = ExecutionMode.RESEARCH if hasattr(ExecutionMode, 'RESEARCH') else ExecutionMode.SINGLE
                logger.info(f"Routing override forced mode: {mode_to_use}")
            elif mode_to_use == ExecutionMode.AUTO:
                # System chooses based on query complexity
                mode_to_use = await self._select_mode(request.message, routing_confidence)

            # ======================================================================
            # PHASE 3: Tool Policy Enforcement
            # ======================================================================
            # When routing override is active, execute tools BEFORE LLM call
            # This ensures live data is retrieved and prevents "I don't have live data" responses
            tool_results = []
            tool_policy_engine = ToolPolicyEngine()
            tool_attempted = False
            tool_success = False

            if routing_override.force_research:
                # Determine tool policy based on routing override
                policy_decision = tool_policy_engine.decide_policy(
                    routing_override.reason,
                    request.message
                )

                logger.info(
                    f"Tool policy decision: policy={policy_decision.policy}, "
                    f"tools={policy_decision.tool_classes}, reason={policy_decision.reason}"
                )

                # Execute tools if policy requires it
                if policy_decision.policy == ToolPolicy.REQUIRED:
                    tool_attempted = True
                    tool_results = await tool_policy_engine.execute_tool_chain(
                        policy_decision,
                        request.message
                    )

                    # Check if any tool succeeded
                    tool_success = any(r.success for r in tool_results)

                    logger.info(
                        f"Tool execution results: attempted={tool_attempted}, "
                        f"success={tool_success}, results={len(tool_results)}"
                    )

                    # Format tool results for LLM context
                    if tool_results:
                        tool_context = tool_policy_engine.format_tool_results_for_llm(
                            tool_results,
                            request.message
                        )

                        if tool_context:
                            logger.info(f"Tool context for LLM: {tool_context[:200]}...")

            # Prepare context with routing override info
            enhanced_context = dict(request.context)

            if routing_override.force_research:
                override_info = {
                    "active": True,
                    "reason": routing_override.reason,
                    "force_tools": routing_override.force_tools,
                    "matched_terms": routing_override.matched_terms,
                    "tool_attempted": tool_attempted,
                    "tool_success": tool_success,
                }

                # Add tool results to context
                if tool_results:
                    successful_results = [r for r in tool_results if r.success]
                    if successful_results:
                        override_info["tool_results"] = [
                            {
                                "tool_class": r.tool_class,
                                "data": r.data,
                                "raw_response": r.raw_response
                            }
                            for r in successful_results
                        ]

                enhanced_context.update({"routing_override": override_info})

            # Execute based on mode
            if mode_to_use == ExecutionMode.SINGLE:
                result = await self._execute_single(
                    selected_agent,
                    request.message,
                    enhanced_context,
                    session_id=request.session_id
                )
                agents_involved = [selected_agent.agent_id]
            else:
                # Multi-agent orchestration
                result = await self._orchestrate_multi(
                    selected_agent,
                    active_agents,
                    request.message,
                    mode_to_use,
                    enhanced_context,
                    session_id=request.session_id
                )
                agents_involved = result.get("agents_involved", [selected_agent.agent_id])

            duration_ms = int((time.time() - start_time) * 1000)

            # Build routing metadata
            routing_metadata = {
                "selected_agent": routed_to,
                "confidence": routing_confidence,
                "override_active": routing_override.force_research,
            }

            # Phase 3: Add tool execution metadata
            if tool_attempted:
                routing_metadata["tool_attempted"] = True
                routing_metadata["tool_success"] = tool_success
                if tool_results:
                    successful_tools = [r.tool_class for r in tool_results if r.success]
                    if successful_tools:
                        routing_metadata["tools_used"] = successful_tools

            # Add override info to routing metadata
            if routing_override.force_research:
                routing_metadata.update({
                    "override_reason": routing_override.reason,
                    "override_matched_terms": routing_override.matched_terms,
                    "reasoning": f"Routing override: {routing_override.reason}"
                })
            else:
                routing_metadata["reasoning"] = "Explicit agent selection" if request.agent_id else "Agent selected based on query analysis"

            return UnifiedChatResponse(
                text=result.get("response", ""),
                response=result.get("response", ""),  # Legacy compatibility
                session_id=request.session_id,
                agent_id_used=routed_to,
                agent_id=routed_to,  # Legacy compatibility
                mode_used=mode_to_use,
                agents_involved=agents_involved,
                routing=routing_metadata,
                metadata={
                    "task_id": task_id,
                    "duration_ms": duration_ms,
                    "agent_count": len(agents_involved),
                    "routing_override": routing_override.force_research,
                    "tool_attempted": tool_attempted,
                    "tool_success": tool_success,
                },
                latency_ms=duration_ms,
                duration_ms=duration_ms  # Legacy compatibility
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Chat error: {e}")
            return UnifiedChatResponse(
                text=f"Error: {str(e)}",
                response=f"Error: {str(e)}",  # Legacy compatibility
                session_id=request.session_id,
                agent_id_used="system",
                agent_id="system",  # Legacy compatibility
                mode_used=request.mode,
                error=str(e),
                latency_ms=duration_ms,
                duration_ms=duration_ms  # Legacy compatibility
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
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute with single agent."""
        import httpx

        if not ANTHROPIC_API_KEY:
            return {
                "response": f"[Simulated] {agent.agent_name}: I processed '{query[:50]}...'",
                "agents_involved": [agent.agent_id]
            }

        # Use actual TORQ Prince Flowers agent with web search for research queries
        if agent.agent_id == "torq_prince_flowers":
            return await self._execute_with_torq_agent(query, context, session_id)

        # Build messages array with conversation history
        messages = []

        # Phase 3: Inject tool results into message context
        # This ensures the LLM has access to live data when tools were executed
        routing_override = context.get("routing_override", {})
        if routing_override.get("tool_results"):
            tool_context_parts = []
            for tool_result in routing_override["tool_results"]:
                tool_class = tool_result.get("tool_class")
                data = tool_result.get("data")

                if tool_class == "weather":
                    tool_context_parts.append(
                        f"Current weather data for {data.get('location')}: "
                        f"{data.get('temperature_f')}F ({data.get('temperature_c')}C), "
                        f"{data.get('condition')}, Humidity: {data.get('humidity')}%"
                    )
                elif tool_class == "finance":
                    if data.get("asset_type") == "crypto":
                        tool_context_parts.append(
                            f"Current {data.get('symbol')} price: ${data.get('price_us'):,.2f} "
                            f"({data.get('change_24h_percent'):+.2f}% change)"
                        )
                    else:
                        tool_context_parts.append(f"Finance data: {tool_result.get('raw_response')}")

            if tool_context_parts:
                # Add as system message with tool context
                tool_context = "\n".join(tool_context_parts)
                logger.info(f"Injecting tool results into conversation: {tool_context[:100]}...")

        # Load session history if session store is available
        if self.session_store and session_id:
            try:
                history = await self.session_store.get_session_history(session_id, max_messages=10)
                for msg in history:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                logger.info(f"Loaded {len(history)} messages from session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to load session history: {e}")

        # Phase 3: If tool results exist, prepend them to the user query
        user_content = query
        if routing_override.get("tool_results"):
            tool_context_parts = []
            for tool_result in routing_override["tool_results"]:
                tool_class = tool_result.get("tool_class")
                data = tool_result.get("data")

                if tool_class == "weather":
                    tool_context_parts.append(
                        f"[Current Data] The weather in {data.get('location')} is "
                        f"{data.get('temperature_f')}F and {data.get('condition')}."
                    )
                elif tool_class == "finance" and data.get("asset_type") == "crypto":
                    tool_context_parts.append(
                        f"[Current Data] {data.get('symbol')} is trading at "
                        f"${data.get('price_usd'):,.2f} ({data.get('change_24h_percent'):+.2f}%)."
                    )

            if tool_context_parts:
                user_content = "\n\n".join(tool_context_parts) + f"\n\nUser question: {query}"

        # Add current query (with tool context if available)
        messages.append({"role": "user", "content": user_content})

        # Get TORQ-native system context (as separate parameter for Anthropic API)
        system_context = self._get_system_context(agent)

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Build request payload
                payload = {
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                    "max_tokens": 2000,
                    "messages": messages
                }

                # Add system parameter if context exists
                if system_context:
                    payload["system"] = system_context

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")

                # Persist messages to session store
                if self.session_store and session_id:
                    try:
                        await self.session_store.add_message(
                            session_id=session_id,
                            role="user",
                            content=query,
                            agent_id=agent.agent_id
                        )
                        await self.session_store.add_message(
                            session_id=session_id,
                            role="assistant",
                            content=content,
                            agent_id=agent.agent_id
                        )
                        logger.info(f"Persisted messages to session {session_id}")
                    except Exception as e:
                        logger.warning(f"Failed to persist messages: {e}")

                return {"response": content, "agents_involved": [agent.agent_id]}
            else:
                return {
                    "response": f"API Error: {response.status_code}",
                    "agents_involved": [agent.agent_id]
                }

        except Exception as e:
            return {"response": f"Error: {str(e)}", "agents_involved": [agent.agent_id]}

    async def _execute_with_torq_agent(
        self,
        query: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute using actual TORQ Prince Flowers agent with web search."""
        try:
            # Import the actual TORQ agent and LLM provider
            from .torq_prince_flowers import TORQPrinceFlowers
            from ..llm.providers.claude import ClaudeProvider

            # Create LLM provider with API key from environment
            llm_provider = ClaudeProvider()

            # Create agent instance with LLM provider
            torq_agent = TORQPrinceFlowers(llm_provider=llm_provider)

            # Process query with full web search capabilities
            result = await torq_agent.process_query(
                query=query,
                context=context or {}
            )

            # Format response
            response_text = result.response if result.success else result.error_message

            # Persist to session store
            if self.session_store and session_id:
                try:
                    await self.session_store.add_message(
                        session_id=session_id,
                        role="user",
                        content=query,
                        agent_id="torq_prince_flowers"
                    )
                    await self.session_store.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=response_text,
                        agent_id="torq_prince_flowers"
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist messages: {e}")

            return {
                "response": response_text,
                "agents_involved": ["torq_prince_flowers"],
                "metadata": {
                    "search_performed": result.metadata.get("search_performed", False),
                    "search_results": result.metadata.get("search_results", []),
                    "reasoning_steps": result.metadata.get("reasoning_steps", [])
                }
            }

        except ImportError as e:
            logger.error(f"Failed to import TORQ agent: {e}")
            # Fallback to direct API call
            return await self._execute_single_fallback(query, session_id)
        except Exception as e:
            logger.error(f"TORQ agent execution failed: {e}")
            return {"response": f"Agent Error: {str(e)}", "agents_involved": ["torq_prince_flowers"]}

    async def _execute_single_fallback(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback to direct API call when TORQ agent is unavailable."""
        import httpx

        system_context = """You are TORQ Prince Flowers, an AI agent with web search capabilities.

When asked questions that require current information or research:
1. Acknowledge that you would search the web for this information
2. Provide your general knowledge on the topic
3. Mention that for the most accurate, up-to-date information, web search would be used"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                payload = {
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": query}],
                    "system": system_context
                }

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return {"response": content, "agents_involved": ["torq_prince_flowers"]}
            else:
                return {"response": f"API Error: {response.status_code}", "agents_involved": ["torq_prince_flowers"]}

        except Exception as e:
            return {"response": f"Error: {str(e)}", "agents_involved": ["torq_prince_flowers"]}

    def _get_system_context(self, agent: AgentCard) -> str:
        """Generate TORQ-native system context for agents."""
        return f"""You are {agent.agent_name}, an AI agent in TORQ Console.

**Your Identity:**
- Agent ID: {agent.agent_id}
- Name: {agent.agent_name}
- Type: {agent.agent_type}
- Description: {agent.description or agent.agent_name}

**Your Capabilities:**
{chr(10).join(f"- {cap}" for cap in agent.capabilities)}

**Tools You Can Use:**
{chr(10).join(f"- {tool}" for tool in agent.tools) if agent.tools else "- Standard conversation tools"}

**TORQ Console Context:**
- You are part of a multi-agent AI orchestration platform
- Other agents may be available for specialized tasks
- Users can switch between agents or use auto-routing
- Session continuity is enabled - you remember prior messages in the conversation

**Behavior Guidelines:**
- Be helpful, accurate, and concise
- Leverage your specific capabilities
- If a task would be better handled by another agent, mention it
- Remember context from earlier in this conversation
- Provide practical, actionable guidance"""

    async def _orchestrate_multi(
        self,
        primary_agent: AgentCard,
        all_agents: List[AgentCard],
        query: str,
        mode: ExecutionMode,
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrate multiple agents."""
        # For now, simple parallel execution
        agents_to_use = all_agents[:3]  # Top 3 agents

        async def execute_agent(agent: AgentCard):
            return await self._execute_single(agent, query, context, session_id)

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

def create_unified_router(session_store: Optional["SessionStore"] = None) -> APIRouter:
    """Create unified API router with consistent contract."""
    router = APIRouter(prefix="/api/chat", tags=["chat"])
    orchestrator = UnifiedOrchestrator(session_store=session_store)

    # Set global session store instance
    if session_store:
        set_session_store(session_store)
        logger.info("Global session store configured")

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
        # Phase 2: Sanity log for routing audit
        logger.info(
            f"/api/chat request - agent_id={request.agent_id or 'auto'}, "
            f"mode={request.mode}, message={request.message[:50]}..."
        )

        result = await orchestrator.chat(request)

        # Phase 2: Sanity log for routing result
        logger.info(
            f"/api/chat routing result - agent_id_used={result.agent_id_used}, "
            f"mode_used={result.mode_used}, "
            f"routing_override={result.metadata.get('routing_override', False)}"
        )

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
