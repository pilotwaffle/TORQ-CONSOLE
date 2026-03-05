"""
TORQ Multi-Agent Orchestration System - Agent Registry Module

Provides interface to the agents_registry table in Supabase for managing
agent metadata, capabilities, and status.

This module is designed to work standalone without heavy torq_console imports.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Models
# ============================================================================

class AgentStatus(str, Enum):
    """Agent operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    TESTING = "testing"


class AgentCapability(str, Enum):
    """Standard agent capabilities."""
    WEB_SEARCH = "web_search"
    CODE_GENERATION = "code_generation"
    CODE_DEBUGGING = "code_debugging"
    DATA_ANALYSIS = "data_analysis"
    FINANCE = "finance"
    RESEARCH = "research"
    STRATEGY = "strategy"
    AUTOMATION = "automation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    WORKFLOW_DESIGN = "workflow_design"
    SEMANTIC_SEARCH = "semantic_search"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"


@dataclass
class AgentDefinition:
    """Definition of an AI agent with its capabilities."""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    model: str
    status: AgentStatus = AgentStatus.ACTIVE
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "model": self.model,
            "status": self.status.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDefinition":
        """Create from dictionary (e.g., from Supabase)."""
        # Handle both string and enum status
        status = data.get("status", "active")
        if isinstance(status, str):
            try:
                status = AgentStatus(status)
            except ValueError:
                status = AgentStatus.ACTIVE

        return cls(
            agent_id=data.get("agent_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            model=data.get("model", ""),
            status=status,
            max_tokens=data.get("max_tokens"),
            temperature=data.get("temperature", 0.7),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class AgentSelectionScore:
    """Score for agent selection."""
    agent_id: str
    score: float
    reasons: List[str]
    capability_match: float
    cost_efficiency: float


# ============================================================================
# Default Agent Definitions
# ============================================================================

DEFAULT_AGENTS = [
    AgentDefinition(
        agent_id="prince_flowers",
        name="Prince Flowers",
        description="General conversational agent with web search and knowledge retrieval capabilities",
        capabilities=[
            AgentCapability.WEB_SEARCH,
            AgentCapability.SEMANTIC_SEARCH,
            AgentCapability.KNOWLEDGE_RETRIEVAL,
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="research_agent",
        name="Research Agent",
        description="Specialized in deep research, information gathering, and analysis",
        capabilities=[
            AgentCapability.WEB_SEARCH,
            AgentCapability.RESEARCH,
            AgentCapability.DATA_ANALYSIS
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="finance_agent",
        name="Finance Agent",
        description="Financial analysis, market data, and trading strategy",
        capabilities=[
            AgentCapability.FINANCE,
            AgentCapability.DATA_ANALYSIS,
            AgentCapability.RESEARCH
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="strategy_agent",
        name="Strategy Agent",
        description="Strategic planning and business analysis",
        capabilities=[
            AgentCapability.STRATEGY,
            AgentCapability.RESEARCH,
            AgentCapability.DATA_ANALYSIS
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="automation_agent",
        name="Automation Agent",
        description="n8n workflow design and automation planning",
        capabilities=[
            AgentCapability.AUTOMATION,
            AgentCapability.WORKFLOW_DESIGN,
            AgentCapability.CODE_GENERATION
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="code_agent",
        name="Code Agent",
        description="Code generation, debugging, and technical implementation",
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_DEBUGGING,
            AgentCapability.TESTING,
            AgentCapability.ARCHITECTURE
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
    AgentDefinition(
        agent_id="data_analysis_agent",
        name="Data Analysis Agent",
        description="Data processing, analysis, and visualization",
        capabilities=[
            AgentCapability.DATA_ANALYSIS,
            AgentCapability.CODE_GENERATION,
            AgentCapability.RESEARCH
        ],
        model="claude-sonnet-4-20250514",
        status=AgentStatus.ACTIVE
    ),
]


# ============================================================================
# Agent Registry Class
# ============================================================================

class AgentRegistry:
    """
    Registry for managing AI agents with Supabase persistence.

    Features:
    - Query agents by capability
    - Check agent status
    - Register/unregister agents
    - Fallback to in-memory when Supabase unavailable
    """

    def __init__(self):
        """Initialize agent registry with default agents."""
        self._in_memory_agents: Dict[str, AgentDefinition] = {}
        self._supabase_available = False
        self._initialized = False

        # Initialize with default agents
        for agent in DEFAULT_AGENTS:
            self._in_memory_agents[agent.agent_id] = agent

        # Check Supabase availability
        self._check_supabase()

    def _check_supabase(self) -> bool:
        """Check if Supabase is configured."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._supabase_available = bool(supabase_url and supabase_key)
        return self._supabase_available

    async def initialize(self) -> None:
        """Initialize registry - load agents from Supabase if available."""
        if self._initialized:
            return

        self._check_supabase()

        if self._supabase_available:
            try:
                await self._load_from_supabase()
                logger.info("AgentRegistry initialized from Supabase")
            except Exception as e:
                logger.warning(f"Failed to load agents from Supabase: {e}. Using in-memory defaults.")
                self._supabase_available = False
        else:
            logger.info("AgentRegistry initialized with in-memory defaults")

        self._initialized = True

    async def _load_from_supabase(self) -> None:
        """Load agents from Supabase agents_registry table."""
        import httpx

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{supabase_url}/rest/v1/agents_registry",
                headers=headers
            )
            response.raise_for_status()
            agents_data = response.json()

            # Update in-memory cache
            for agent_data in agents_data:
                agent = AgentDefinition.from_dict(agent_data)
                self._in_memory_agents[agent.agent_id] = agent

            logger.info(f"Loaded {len(agents_data)} agents from Supabase")

    async def _save_to_supabase(self, agent: AgentDefinition) -> None:
        """Save or update agent in Supabase."""
        import httpx

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        agent_data = agent.to_dict()
        agent_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Upsert agent
            response = await client.post(
                f"{supabase_url}/rest/v1/agents_registry",
                headers=headers,
                json=agent_data,
                params={"on_conflict": "agent_id"}
            )
            response.raise_for_status()

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent by ID."""
        return self._in_memory_agents.get(agent_id)

    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentDefinition]:
        """List all agents, optionally filtered by status."""
        agents = list(self._in_memory_agents.values())

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    def list_active_agents(self) -> List[AgentDefinition]:
        """List only active agents."""
        return self.list_agents(status=AgentStatus.ACTIVE)

    def find_agents_by_capability(self, capability: str) -> List[AgentDefinition]:
        """Find agents that have a specific capability."""
        return [
            agent for agent in self._in_memory_agents.values()
            if capability in agent.capabilities and agent.status == AgentStatus.ACTIVE
        ]

    def get_agent_count(self) -> int:
        """Get total number of registered agents."""
        return len(self._in_memory_agents)

    def get_active_count(self) -> int:
        """Get number of active agents."""
        return len(self.list_active_agents())

    async def register_agent(self, agent: AgentDefinition) -> bool:
        """Register a new agent or update existing one."""
        try:
            # Add to in-memory cache
            self._in_memory_agents[agent.agent_id] = agent

            # Persist to Supabase if available
            if self._supabase_available:
                await self._save_to_supabase(agent)

            logger.info(f"Registered agent: {agent.agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        agent = self.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent not found: {agent_id}")
            return False

        agent.status = status
        agent.updated_at = datetime.now(timezone.utc).isoformat()

        if self._supabase_available:
            try:
                await self._save_to_supabase(agent)
            except Exception as e:
                logger.error(f"Failed to update agent status in Supabase: {e}")
                return False

        return True

    def get_capabilities_summary(self) -> Dict[str, List[str]]:
        """Get summary of all capabilities and agents that provide them."""
        summary: Dict[str, List[str]] = {}

        for agent in self._in_memory_agents.values():
            if agent.status != AgentStatus.ACTIVE:
                continue

            for capability in agent.capabilities:
                if capability not in summary:
                    summary[capability] = []
                summary[capability].append(agent.agent_id)

        return summary

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Export all agents as list of dicts."""
        return [agent.to_dict() for agent in self._in_memory_agents.values()]


# ============================================================================
# Global Registry Instance
# ============================================================================

_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


async def initialize_registry() -> AgentRegistry:
    """Initialize and return the global registry."""
    registry = get_agent_registry()
    await registry.initialize()
    return registry
