"""
Main ControlFlow Integration for TORQ Console

Provides the primary interface for ControlFlow-based orchestration.
"""

import logging
from typing import Dict, Any, Optional, List
import controlflow as cf

logger = logging.getLogger(__name__)


class TorqControlFlowIntegration:
    """
    Main integration point for ControlFlow in TORQ Console.

    This class manages:
    - Agent registry
    - Flow execution
    - Integration with existing TORQ systems
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ControlFlow integration.

        Args:
            config: Configuration dictionary with:
                - default_model: LLM model to use (e.g., "anthropic/claude-sonnet-4")
                - api_keys: Dict of API keys for various providers
                - enable_monitoring: Whether to enable Prefect monitoring
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.TorqCF")

        # Agent registry
        self.agents: Dict[str, cf.Agent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}

        # Flow registry
        self.flows: Dict[str, Any] = {}

        # Performance metrics
        self.metrics = {
            'total_flows_executed': 0,
            'successful_flows': 0,
            'failed_flows': 0,
            'total_tasks_executed': 0,
            'avg_flow_execution_time': 0.0
        }

        self.logger.info("ControlFlow integration initialized")

    def register_agent(
        self,
        name: str,
        agent: cf.Agent,
        capabilities: List[str]
    ) -> None:
        """
        Register an agent with the integration system.

        Args:
            name: Unique agent name
            agent: ControlFlow Agent instance
            capabilities: List of capabilities this agent has
        """
        self.agents[name] = agent
        self.agent_capabilities[name] = capabilities
        self.logger.info(f"Registered agent: {name} with capabilities: {capabilities}")

    def get_agent(self, name: str) -> Optional[cf.Agent]:
        """Get an agent by name."""
        return self.agents.get(name)

    def get_agents_by_capability(self, capability: str) -> List[cf.Agent]:
        """Get all agents that have a specific capability."""
        return [
            agent for name, agent in self.agents.items()
            if capability in self.agent_capabilities.get(name, [])
        ]

    def register_flow(self, name: str, flow_func: Any) -> None:
        """Register a flow with the integration system."""
        self.flows[name] = flow_func
        self.logger.info(f"Registered flow: {name}")

    def get_flow(self, name: str) -> Optional[Any]:
        """Get a flow by name."""
        return self.flows.get(name)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.metrics.copy()

    def update_metrics(self, success: bool, execution_time: float, tasks_count: int = 1):
        """Update performance metrics after flow execution."""
        self.metrics['total_flows_executed'] += 1
        if success:
            self.metrics['successful_flows'] += 1
        else:
            self.metrics['failed_flows'] += 1

        self.metrics['total_tasks_executed'] += tasks_count

        # Update average execution time (exponential moving average)
        alpha = 0.1
        current_avg = self.metrics['avg_flow_execution_time']
        self.metrics['avg_flow_execution_time'] = (
            current_avg * (1 - alpha) + execution_time * alpha
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current integration status."""
        return {
            'agents_registered': len(self.agents),
            'flows_registered': len(self.flows),
            'metrics': self.get_metrics(),
            'agent_list': list(self.agents.keys()),
            'flow_list': list(self.flows.keys())
        }
