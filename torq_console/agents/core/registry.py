"""
Agent Registry - Centralized agent discovery and management.

Replaces scattered agent instantiation with a unified registry system.
Provides dynamic agent discovery, capability-based routing, and lifecycle management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

from .base_agent import (
    BaseAgent, AgentCapability, AgentStatus,
    AgentContext, AgentResult, IAgent
)


class RegistrationStatus(str, Enum):
    """Agent registration status."""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent_class: Type[BaseAgent]
    agent_id: str
    agent_name: str
    capabilities: List[AgentCapability]
    status: RegistrationStatus = RegistrationStatus.REGISTERED
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    instance: Optional[BaseAgent] = None
    last_health_check: Optional[float] = None


class AgentRegistry:
    """
    Central registry for all TORQ Console agents.

    Provides:
    - Agent registration and discovery
    - Capability-based agent lookup
    - Instance lifecycle management
    - Health monitoring
    - Dependency resolution
    """

    def __init__(self):
        """Initialize agent registry."""
        self._agents: Dict[str, AgentRegistration] = {}
        self._capability_index: Dict[AgentCapability, Set[str]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self._lock = Lock()
        self.logger = logging.getLogger("AgentRegistry")

        # Registry statistics
        self._total_registrations = 0
        self._active_instances = 0

    def register(
        self,
        agent_class: Type[BaseAgent],
        agent_id: str,
        agent_name: str,
        capabilities: List[AgentCapability],
        config: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_activate: bool = True
    ) -> bool:
        """
        Register an agent class with the registry.

        Args:
            agent_class: Agent class to register
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name
            capabilities: List of agent capabilities
            config: Agent configuration
            dependencies: List of required agent IDs
            metadata: Additional metadata
            auto_activate: Whether to auto-activate the agent

        Returns:
            True if registration successful, False otherwise
        """
        with self._lock:
            # Check for existing registration
            if agent_id in self._agents:
                self.logger.warning(f"Agent {agent_id} already registered")
                return False

            # Validate capabilities
            if not capabilities:
                self.logger.error(f"Agent {agent_id} must have at least one capability")
                return False

            # Validate dependencies
            if dependencies:
                for dep_id in dependencies:
                    if dep_id not in self._agents:
                        self.logger.error(
                            f"Agent {agent_id} depends on unregistered agent {dep_id}"
                        )
                        return False

            # Create registration
            registration = AgentRegistration(
                agent_class=agent_class,
                agent_id=agent_id,
                agent_name=agent_name,
                capabilities=capabilities,
                config=config or {},
                dependencies=dependencies or [],
                metadata=metadata or {},
                status=RegistrationStatus.ACTIVE if auto_activate else RegistrationStatus.REGISTERED
            )

            # Add to registry
            self._agents[agent_id] = registration

            # Update capability index
            for capability in capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent_id)

            self._total_registrations += 1
            self.logger.info(f"Registered agent: {agent_name} ({agent_id}) with capabilities: {capabilities}")

            return True

    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_id: ID of agent to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        with self._lock:
            if agent_id not in self._agents:
                self.logger.warning(f"Agent {agent_id} not found in registry")
                return False

            registration = self._agents[agent_id]

            # Check for dependent agents
            dependents = self._get_dependent_agents(agent_id)
            if dependents:
                self.logger.error(
                    f"Cannot unregister {agent_id}: has dependent agents: {dependents}"
                )
                return False

            # Deactivate and cleanup instance
            if registration.instance:
                self._deactivate_instance(agent_id)

            # Remove from capability index
            for capability in registration.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(agent_id)

            # Remove from registry
            del self._agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")

            return True

    def activate_agent(self, agent_id: str) -> bool:
        """
        Activate a registered agent.

        Args:
            agent_id: ID of agent to activate

        Returns:
            True if activation successful, False otherwise
        """
        with self._lock:
            if agent_id not in self._agents:
                self.logger.error(f"Agent {agent_id} not found in registry")
                return False

            registration = self._agents[agent_id]

            if registration.status == RegistrationStatus.ACTIVE:
                return True

            if registration.status not in [RegistrationStatus.REGISTERED, RegistrationStatus.INACTIVE]:
                self.logger.error(f"Cannot activate agent {agent_id} in status: {registration.status}")
                return False

            # Activate dependencies first
            for dep_id in registration.dependencies:
                if not self.activate_agent(dep_id):
                    self.logger.error(f"Failed to activate dependency {dep_id} for {agent_id}")
                    return False

            registration.status = RegistrationStatus.ACTIVE
            self.logger.info(f"Activated agent: {agent_id}")
            return True

    def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent.

        Args:
            agent_id: ID of agent to deactivate

        Returns:
            True if deactivation successful, False otherwise
        """
        with self._lock:
            if agent_id not in self._agents:
                return False

            registration = self._agents[agent_id]

            if registration.status != RegistrationStatus.ACTIVE:
                return True

            # Check for dependent active agents
            dependents = self._get_dependent_agents(agent_id)
            active_dependents = [
                dep_id for dep_id in dependents
                if self._agents[dep_id].status == RegistrationStatus.ACTIVE
            ]

            if active_dependents:
                self.logger.error(
                    f"Cannot deactivate {agent_id}: has active dependents: {active_dependents}"
                )
                return False

            # Cleanup instance
            if registration.instance:
                self._deactivate_instance(agent_id)

            registration.status = RegistrationStatus.INACTIVE
            self.logger.info(f"Deactivated agent: {agent_id}")
            return True

    async def get_agent_instance(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get or create an agent instance.

        Args:
            agent_id: ID of agent

        Returns:
            Agent instance or None if not available
        """
        if agent_id not in self._agents:
            return None

        registration = self._agents[agent_id]

        if registration.status != RegistrationStatus.ACTIVE:
            return None

        # Return existing instance
        if registration.instance:
            return registration.instance

        # Create new instance
        try:
            instance = await self._create_instance(registration)
            if instance:
                registration.instance = instance
                registration.last_health_check = asyncio.get_event_loop().time()
                self._active_instances += 1
                self.logger.info(f"Created instance for agent: {agent_id}")
            return instance

        except Exception as e:
            self.logger.error(f"Failed to create instance for {agent_id}: {e}")
            registration.status = RegistrationStatus.ERROR
            return None

    async def _create_instance(self, registration: AgentRegistration) -> BaseAgent:
        """Create a new agent instance."""
        # Import LLM provider if needed
        llm_provider = None
        if registration.config.get("use_llm"):
            try:
                from torq_console.llm.providers import get_default_provider
                llm_provider = await get_default_provider()
            except Exception as e:
                self.logger.warning(f"Failed to get LLM provider for {registration.agent_id}: {e}")

        # Create instance
        instance = registration.agent_class(
            agent_id=registration.agent_id,
            agent_name=registration.agent_name,
            capabilities=registration.capabilities,
            llm_provider=llm_provider,
            config=registration.config
        )

        return instance

    def _deactivate_instance(self, agent_id: str) -> None:
        """Deactivate and cleanup agent instance."""
        if agent_id in self._agents:
            registration = self._agents[agent_id]
            if registration.instance:
                # Cleanup instance
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(registration.instance.reset())
                    else:
                        loop.run_until_complete(registration.instance.reset())
                except Exception as e:
                    self.logger.error(f"Error cleaning up instance {agent_id}: {e}")

                registration.instance = None
                self._active_instances = max(0, self._active_instances - 1)

    def find_agents_by_capability(self, capability: AgentCapability) -> List[str]:
        """
        Find agent IDs that have a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agent IDs with the capability
        """
        if capability not in self._capability_index:
            return []

        # Filter by active agents
        active_agents = []
        for agent_id in self._capability_index[capability]:
            if (agent_id in self._agents and
                self._agents[agent_id].status == RegistrationStatus.ACTIVE):
                active_agents.append(agent_id)

        return active_agents

    def find_agents_by_capabilities(self, capabilities: List[AgentCapability]) -> List[str]:
        """
        Find agent IDs that have ALL specified capabilities.

        Args:
            capabilities: List of required capabilities

        Returns:
            List of agent IDs with all capabilities
        """
        if not capabilities:
            return []

        # Get agents with first capability
        candidates = set(self.find_agents_by_capability(capabilities[0]))

        # Filter by remaining capabilities
        for capability in capabilities[1:]:
            capability_agents = set(self.find_agents_by_capability(capability))
            candidates &= capability_agents

        return list(candidates)

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an agent.

        Args:
            agent_id: ID of agent

        Returns:
            Agent information dictionary or None
        """
        if agent_id not in self._agents:
            return None

        registration = self._agents[agent_id]

        info = {
            "agent_id": registration.agent_id,
            "agent_name": registration.agent_name,
            "capabilities": registration.capabilities,
            "status": registration.status,
            "dependencies": registration.dependencies,
            "metadata": registration.metadata,
            "created_at": registration.created_at,
            "has_instance": registration.instance is not None,
            "last_health_check": registration.last_health_check,
        }

        # Add instance metrics if available
        if registration.instance:
            info["metrics"] = registration.instance.get_metrics()
            info["current_status"] = registration.instance.status

        return info

    def list_agents(self, status_filter: Optional[RegistrationStatus] = None) -> List[Dict[str, Any]]:
        """
        List all registered agents.

        Args:
            status_filter: Optional status filter

        Returns:
            List of agent information dictionaries
        """
        agents = []

        for agent_id, registration in self._agents.items():
            if status_filter and registration.status != status_filter:
                continue

            agents.append(self.get_agent_info(agent_id))

        return agents

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        status_counts = {}
        for registration in self._agents.values():
            status_counts[registration.status] = status_counts.get(registration.status, 0) + 1

        return {
            "total_agents": len(self._agents),
            "total_registrations": self._total_registrations,
            "active_instances": self._active_instances,
            "capability_counts": {
                cap: len(agents) for cap, agents in self._capability_index.items()
            },
            "status_counts": status_counts,
        }

    def _get_dependent_agents(self, agent_id: str) -> List[str]:
        """Get list of agents that depend on the specified agent."""
        dependents = []
        for other_id, registration in self._agents.items():
            if agent_id in registration.dependencies:
                dependents.append(other_id)
        return dependents

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health checks on all active agent instances.

        Returns:
            Dictionary mapping agent IDs to health status
        """
        health_status = {}

        for agent_id, registration in self._agents.items():
            if registration.status != RegistrationStatus.ACTIVE:
                continue

            if registration.instance:
                try:
                    is_healthy = await registration.instance.health_check()
                    health_status[agent_id] = is_healthy
                    registration.last_health_check = asyncio.get_event_loop().time()

                    if not is_healthy:
                        self.logger.warning(f"Health check failed for agent: {agent_id}")

                except Exception as e:
                    self.logger.error(f"Health check error for {agent_id}: {e}")
                    health_status[agent_id] = False

        return health_status

    async def cleanup(self) -> None:
        """Cleanup all agent instances and resources."""
        self.logger.info("Cleaning up agent registry")

        for agent_id in list(self._agents.keys()):
            self._deactivate_instance(agent_id)

        self._agents.clear()
        self._capability_index.clear()
        self._instances.clear()
        self._active_instances = 0

        self.logger.info("Agent registry cleanup completed")


# Global registry instance
_global_registry: Optional[AgentRegistry] = None
_registry_lock = Lock()


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _global_registry

    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = AgentRegistry()

    return _global_registry


def register_agent(
    agent_class: Type[BaseAgent],
    agent_id: str,
    agent_name: str,
    capabilities: List[AgentCapability],
    config: Optional[Dict[str, Any]] = None,
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Convenience function to register an agent."""
    registry = get_agent_registry()
    return registry.register(
        agent_class=agent_class,
        agent_id=agent_id,
        agent_name=agent_name,
        capabilities=capabilities,
        config=config,
        dependencies=dependencies,
        metadata=metadata
    )


async def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Convenience function to get an agent instance."""
    registry = get_agent_registry()
    return await registry.get_agent_instance(agent_id)


def find_agents(capability: AgentCapability) -> List[str]:
    """Convenience function to find agents by capability."""
    registry = get_agent_registry()
    return registry.find_agents_by_capability(capability)