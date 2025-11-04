"""
Marvin Agent Orchestration System

Coordinates multiple Marvin-powered agents with intelligent routing,
context management, and workflow orchestration.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .marvin_query_router import (
    MarvinQueryRouter,
    QueryAnalysis,
    RoutingDecision,
    AgentCapability
)
from .marvin_prince_flowers import MarvinPrinceFlowers
from .marvin_workflow_agents import (
    WorkflowType,
    WorkflowResult,
    get_workflow_agent
)


class OrchestrationMode(str, Enum):
    """Orchestration execution modes."""
    SINGLE_AGENT = "single_agent"  # Route to single best agent
    MULTI_AGENT = "multi_agent"    # Coordinate multiple agents
    PIPELINE = "pipeline"          # Sequential agent pipeline
    PARALLEL = "parallel"          # Parallel agent execution


@dataclass
class OrchestrationResult:
    """Result from orchestrated agent execution."""
    mode: OrchestrationMode
    primary_response: Any
    agent_responses: Dict[str, Any] = field(default_factory=dict)
    routing_decision: Optional[RoutingDecision] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


class MarvinAgentOrchestrator:
    """
    Orchestrates multiple Marvin-powered agents with intelligent routing.

    Provides:
    - Automatic query routing
    - Multi-agent coordination
    - Context-aware agent selection
    - Workflow orchestration
    - Performance monitoring
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize agent orchestrator.

        Args:
            model: Optional LLM model override
        """
        self.logger = logging.getLogger("TORQ.Agents.Orchestrator")

        # Initialize components
        self.router = MarvinQueryRouter(model=model)
        self.prince_flowers = MarvinPrinceFlowers(model=model)

        # Agent registry
        self.agents = {
            'prince_flowers': self.prince_flowers,
            'router': self.router,
        }

        # Orchestration metrics
        self.metrics = {
            'total_requests': 0,
            'single_agent_requests': 0,
            'multi_agent_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
        }

        self.logger.info("Initialized Marvin Agent Orchestrator")

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        mode: OrchestrationMode = OrchestrationMode.SINGLE_AGENT
    ) -> OrchestrationResult:
        """
        Process a query through the orchestration system.

        Args:
            query: User query
            context: Optional context information
            mode: Orchestration mode

        Returns:
            OrchestrationResult with responses
        """
        try:
            self.metrics['total_requests'] += 1

            # Route the query
            routing = await self.router.route_query(query, context)

            # Execute based on mode
            if mode == OrchestrationMode.SINGLE_AGENT:
                result = await self._execute_single_agent(
                    query,
                    routing,
                    context
                )
                self.metrics['single_agent_requests'] += 1

            elif mode == OrchestrationMode.MULTI_AGENT:
                result = await self._execute_multi_agent(
                    query,
                    routing,
                    context
                )
                self.metrics['multi_agent_requests'] += 1

            elif mode == OrchestrationMode.PIPELINE:
                result = await self._execute_pipeline(
                    query,
                    routing,
                    context
                )

            elif mode == OrchestrationMode.PARALLEL:
                result = await self._execute_parallel(
                    query,
                    routing,
                    context
                )

            else:
                raise ValueError(f"Unknown orchestration mode: {mode}")

            self.metrics['successful_requests'] += 1
            return result

        except Exception as e:
            self.logger.error(f"Query processing failed: {e}", exc_info=True)
            self.metrics['failed_requests'] += 1

            return OrchestrationResult(
                mode=mode,
                primary_response=f"Error processing query: {str(e)}",
                success=False,
                metadata={'error': str(e)}
            )

    async def _execute_single_agent(
        self,
        query: str,
        routing: RoutingDecision,
        context: Optional[Dict[str, Any]]
    ) -> OrchestrationResult:
        """Execute using a single agent."""
        agent_name = routing.primary_agent

        # For now, route everything through Prince Flowers
        # In future, can route to specialized agents
        response = await self.prince_flowers.chat(query, context)

        return OrchestrationResult(
            mode=OrchestrationMode.SINGLE_AGENT,
            primary_response=response,
            routing_decision=routing,
            metadata={
                'agent_used': agent_name,
                'capabilities': [cap.value for cap in routing.capabilities_needed]
            }
        )

    async def _execute_multi_agent(
        self,
        query: str,
        routing: RoutingDecision,
        context: Optional[Dict[str, Any]]
    ) -> OrchestrationResult:
        """Execute using multiple coordinated agents."""
        responses = {}

        # Get primary agent response
        primary_response = await self.prince_flowers.chat(query, context)
        responses['prince_flowers'] = primary_response

        # If workflow agents are needed, invoke them
        if AgentCapability.CODE_GENERATION in routing.capabilities_needed:
            workflow_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
            if workflow_agent:
                workflow_result = await workflow_agent.generate_code(
                    query,
                    context=context
                )
                responses['code_generation'] = workflow_result

        if AgentCapability.CODE_REVIEW in routing.capabilities_needed:
            # Would invoke code review agent
            pass

        return OrchestrationResult(
            mode=OrchestrationMode.MULTI_AGENT,
            primary_response=primary_response,
            agent_responses=responses,
            routing_decision=routing,
            metadata={
                'agents_used': list(responses.keys()),
                'coordination_strategy': 'primary_with_specialists'
            }
        )

    async def _execute_pipeline(
        self,
        query: str,
        routing: RoutingDecision,
        context: Optional[Dict[str, Any]]
    ) -> OrchestrationResult:
        """Execute agents in a pipeline sequence."""
        pipeline_results = []

        # Example pipeline: analyze -> generate -> review
        # Step 1: Initial response
        response = await self.prince_flowers.chat(query, context)
        pipeline_results.append({
            'stage': 'initial_response',
            'agent': 'prince_flowers',
            'output': response
        })

        # Additional pipeline stages would go here

        return OrchestrationResult(
            mode=OrchestrationMode.PIPELINE,
            primary_response=response,
            agent_responses={'pipeline': pipeline_results},
            routing_decision=routing,
            metadata={
                'pipeline_stages': len(pipeline_results),
                'flow': 'sequential'
            }
        )

    async def _execute_parallel(
        self,
        query: str,
        routing: RoutingDecision,
        context: Optional[Dict[str, Any]]
    ) -> OrchestrationResult:
        """Execute multiple agents in parallel."""
        # For now, simplified implementation
        # In production, would use asyncio.gather for true parallelism

        responses = {}

        # Get response from Prince Flowers
        response = await self.prince_flowers.chat(query, context)
        responses['prince_flowers'] = response

        return OrchestrationResult(
            mode=OrchestrationMode.PARALLEL,
            primary_response=response,
            agent_responses=responses,
            routing_decision=routing,
            metadata={
                'execution_model': 'parallel',
                'agents_count': len(responses)
            }
        )

    async def handle_workflow_request(
        self,
        workflow_type: WorkflowType,
        request_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Handle a specific workflow request.

        Args:
            workflow_type: Type of workflow
            request_data: Workflow-specific request data
            context: Optional context

        Returns:
            WorkflowResult from specialized agent
        """
        try:
            workflow_agent = get_workflow_agent(workflow_type)

            if not workflow_agent:
                raise ValueError(f"No agent for workflow type: {workflow_type}")

            # Route to appropriate workflow method
            if workflow_type == WorkflowType.CODE_GENERATION:
                result = await workflow_agent.generate_code(
                    request_data.get('requirements', ''),
                    request_data.get('language', 'python'),
                    context
                )
            elif workflow_type == WorkflowType.DEBUGGING:
                result = await workflow_agent.debug_issue(
                    request_data.get('code', ''),
                    request_data.get('error_message', ''),
                    request_data.get('language', 'python'),
                    context
                )
            elif workflow_type == WorkflowType.DOCUMENTATION:
                result = await workflow_agent.generate_documentation(
                    request_data.get('code', ''),
                    request_data.get('doc_type', 'api'),
                    request_data.get('language', 'python'),
                    context
                )
            elif workflow_type == WorkflowType.TESTING:
                result = await workflow_agent.generate_tests(
                    request_data.get('code', ''),
                    request_data.get('test_framework', 'pytest'),
                    request_data.get('language', 'python'),
                    context
                )
            elif workflow_type == WorkflowType.ARCHITECTURE:
                result = await workflow_agent.design_architecture(
                    request_data.get('requirements', ''),
                    request_data.get('system_type', 'web_application'),
                    context
                )
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")

            return result

        except Exception as e:
            self.logger.error(f"Workflow request failed: {e}", exc_info=True)
            return WorkflowResult(
                workflow_type=workflow_type,
                success=False,
                output=None,
                metadata={'error': str(e)},
                recommendations=["Check request data", "Verify workflow type"]
            )

    def get_agent(self, agent_name: str):
        """Get a specific agent by name."""
        return self.agents.get(agent_name)

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all components."""
        return {
            'orchestrator': {
                **self.metrics,
                'success_rate': self._calculate_success_rate()
            },
            'router': self.router.get_metrics(),
            'prince_flowers': self.prince_flowers.get_metrics(),
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        total = self.metrics['total_requests']
        if total == 0:
            return 0.0

        return round(
            self.metrics['successful_requests'] / total,
            3
        )


# Global orchestrator instance
_global_orchestrator: Optional[MarvinAgentOrchestrator] = None


def get_orchestrator(model: Optional[str] = None) -> MarvinAgentOrchestrator:
    """
    Get global orchestrator instance (singleton).

    Args:
        model: Optional LLM model override

    Returns:
        MarvinAgentOrchestrator instance
    """
    global _global_orchestrator

    if _global_orchestrator is None:
        _global_orchestrator = MarvinAgentOrchestrator(model=model)

    return _global_orchestrator
