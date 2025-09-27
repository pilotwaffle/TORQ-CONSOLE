#!/usr/bin/env python3
"""
TORQ Console Chain-of-Thought (CoT) Reasoning Enhancers

This module provides integration enhancers that add CoT reasoning capabilities
to existing TORQ Console components like Perplexity search, Prince Flowers agent,
and GitHub Spec-Kit workflows.

Classes:
    CoTEnhancer: Base class for CoT integration enhancers
    PerplexityCoTEnhancer: CoT-enhanced Perplexity search
    AgentCoTEnhancer: CoT-enhanced agent interactions
    SpecKitCoTEnhancer: CoT-enhanced GitHub Spec-Kit workflows
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import json

from .core import CoTReasoning, ReasoningChain, ReasoningStep, ReasoningType
from .templates import ResearchTemplate, AnalysisTemplate, DecisionTemplate, Phase1SpecTemplate
from .validator import CoTValidator

logger = logging.getLogger(__name__)


class CoTEnhancer(ABC):
    """
    Base class for Chain-of-Thought enhancement integrations.

    Enhancers add CoT reasoning capabilities to existing TORQ Console components,
    making them more transparent and methodical in their approach.
    """

    def __init__(self, enhancer_name: str, cot_framework: Optional[CoTReasoning] = None):
        """
        Initialize the CoT enhancer.

        Args:
            enhancer_name: Name of the enhancer
            cot_framework: CoT reasoning framework (creates new if None)
        """
        self.enhancer_name = enhancer_name
        self.cot_framework = cot_framework or CoTReasoning()
        self.validator = CoTValidator()
        self.logger = logging.getLogger(__name__)
        self.active_chains: Dict[str, ReasoningChain] = {}

    @abstractmethod
    async def enhance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a request with CoT reasoning.

        Args:
            request: The original request to enhance

        Returns:
            Enhanced result with CoT reasoning trace
        """
        pass

    async def create_reasoning_chain(
        self,
        chain_id: str,
        title: str,
        reasoning_type: ReasoningType,
        context: Dict[str, Any]
    ) -> ReasoningChain:
        """Create and register a reasoning chain."""
        chain = await self.cot_framework.create_chain(
            chain_id=chain_id,
            title=title,
            reasoning_type=reasoning_type,
            context=context
        )
        self.active_chains[chain_id] = chain
        return chain

    async def execute_and_validate_chain(self, chain_id: str) -> Dict[str, Any]:
        """Execute a reasoning chain and validate the results."""
        if chain_id not in self.active_chains:
            raise ValueError(f"Chain {chain_id} not found")

        chain = self.active_chains[chain_id]

        # Execute the chain
        success = await chain.execute()

        # Validate the results
        validation_result = await self.validator.validate_chain(chain)

        # Compile results
        result = {
            "execution_success": success,
            "validation_result": validation_result,
            "chain_summary": chain.get_execution_summary(),
            "reasoning_trace": self._create_reasoning_trace(chain),
            "confidence": chain.total_confidence,
            "quality_score": validation_result.quality_score
        }

        self.logger.info(f"Chain {chain_id} executed: success={success}, quality={validation_result.quality_score:.2f}")
        return result

    def _create_reasoning_trace(self, chain: ReasoningChain) -> List[Dict[str, Any]]:
        """Create a human-readable reasoning trace."""
        trace = []
        for step in chain.steps:
            trace.append({
                "step_id": step.step_id,
                "description": step.description,
                "reasoning": step.reasoning,
                "status": step.status.value,
                "confidence": step.confidence,
                "execution_time": step.execution_time,
                "outputs": step.outputs if step.outputs else {}
            })
        return trace


class PerplexityCoTEnhancer(CoTEnhancer):
    """
    CoT-enhanced Perplexity search that adds transparent reasoning
    to information gathering and analysis processes.
    """

    def __init__(self, perplexity_client=None, cot_framework: Optional[CoTReasoning] = None):
        """
        Initialize the Perplexity CoT enhancer.

        Args:
            perplexity_client: Perplexity API client instance
            cot_framework: CoT reasoning framework
        """
        super().__init__("Perplexity CoT Enhancer", cot_framework)
        self.perplexity_client = perplexity_client
        self.research_template = ResearchTemplate()

    async def enhance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance Perplexity search with CoT reasoning.

        Args:
            request: Search request containing query, filters, etc.

        Returns:
            Enhanced search results with reasoning trace
        """
        query = request.get("query", "")
        search_type = request.get("search_type", "web")
        max_results = request.get("max_results", 10)

        # Create unique chain ID
        chain_id = f"perplexity_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Create reasoning chain using research template
            chain = await self.research_template.create_chain(
                cot_framework=self.cot_framework,
                chain_id=chain_id,
                context={
                    "query": query,
                    "search_type": search_type,
                    "max_results": max_results,
                    "perplexity_client": self.perplexity_client
                }
            )

            # Register chain in enhancer tracking
            self.active_chains[chain_id] = chain

            # Enhance research steps with Perplexity-specific actions
            await self._enhance_research_steps(chain, request)

            # Execute the enhanced chain
            execution_result = await self.execute_and_validate_chain(chain_id)

            # Extract search results from the reasoning chain
            search_results = await self._extract_search_results(chain)

            return {
                "search_results": search_results,
                "reasoning": execution_result,
                "query": query,
                "metadata": {
                    "search_type": search_type,
                    "max_results": max_results,
                    "reasoning_quality": execution_result.get("quality_score", 0.0),
                    "search_confidence": execution_result.get("confidence", 0.0)
                }
            }

        except Exception as e:
            self.logger.error(f"Perplexity CoT enhancement failed: {e}")
            return {
                "search_results": [],
                "reasoning": {"error": str(e)},
                "query": query,
                "metadata": {"error": True}
            }

    async def _enhance_research_steps(self, chain: ReasoningChain, request: Dict[str, Any]):
        """Enhance research steps with Perplexity-specific functionality."""
        # Find the information gathering step and enhance it
        for step in chain.steps:
            if step.step_id == "gather_information":
                step.action = self._perplexity_search_action
                step.inputs.update(request)

    async def _perplexity_search_action(self, **kwargs) -> Dict[str, Any]:
        """Enhanced Perplexity search action with CoT reasoning."""
        query = kwargs.get("query", "")
        search_type = kwargs.get("search_type", "web")
        max_results = kwargs.get("max_results", 10)

        self.logger.info(f"Executing Perplexity search: {query}")

        try:
            # Simulate Perplexity API call (replace with actual client when available)
            if self.perplexity_client:
                # Use actual Perplexity client
                search_results = await self._call_perplexity_api(query, search_type, max_results)
            else:
                # Simulate search results for testing
                search_results = self._simulate_perplexity_results(query, max_results)

            return {
                "search_results": search_results,
                "query_processed": query,
                "results_count": len(search_results),
                "search_quality": "high",
                "sources_diversity": "good"
            }

        except Exception as e:
            self.logger.error(f"Perplexity search failed: {e}")
            return {
                "search_results": [],
                "error": str(e),
                "search_quality": "failed"
            }

    async def _call_perplexity_api(self, query: str, search_type: str, max_results: int) -> List[Dict[str, Any]]:
        """Call the actual Perplexity API."""
        # This would integrate with the actual Perplexity client
        # For now, return simulated results
        return self._simulate_perplexity_results(query, max_results)

    def _simulate_perplexity_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Simulate Perplexity search results for testing."""
        results = []
        for i in range(min(max_results, 5)):
            results.append({
                "title": f"Result {i+1} for {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a detailed snippet about {query} from source {i+1}",
                "relevance_score": 0.9 - (i * 0.1),
                "source_type": "web",
                "timestamp": datetime.now().isoformat()
            })
        return results

    async def _extract_search_results(self, chain: ReasoningChain) -> List[Dict[str, Any]]:
        """Extract search results from the reasoning chain outputs."""
        search_results = []

        for step in chain.steps:
            if step.step_id == "gather_information" and step.outputs:
                results = step.outputs.get("search_results", [])
                search_results.extend(results)

        return search_results


class AgentCoTEnhancer(CoTEnhancer):
    """
    CoT-enhanced agent interactions that add transparent reasoning
    to agent decision-making and task execution.
    """

    def __init__(self, agent_manager=None, cot_framework: Optional[CoTReasoning] = None):
        """
        Initialize the Agent CoT enhancer.

        Args:
            agent_manager: Agent management system
            cot_framework: CoT reasoning framework
        """
        super().__init__("Agent CoT Enhancer", cot_framework)
        self.agent_manager = agent_manager
        self.decision_template = DecisionTemplate()

    async def enhance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance agent interaction with CoT reasoning.

        Args:
            request: Agent task request

        Returns:
            Enhanced agent response with reasoning trace
        """
        task = request.get("task", "")
        agent_type = request.get("agent_type", "general")
        context = request.get("context", {})

        chain_id = f"agent_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Create reasoning chain for agent decision-making
            chain = await self.decision_template.create_chain(
                cot_framework=self.cot_framework,
                chain_id=chain_id,
                context={
                    "decision": f"How to execute task: {task}",
                    "agent_type": agent_type,
                    "task_context": context
                }
            )

            # Register chain in enhancer tracking
            self.active_chains[chain_id] = chain

            # Enhance decision steps with agent-specific actions
            await self._enhance_agent_steps(chain, request)

            # Execute the enhanced chain
            execution_result = await self.execute_and_validate_chain(chain_id)

            # Extract agent response
            agent_response = await self._extract_agent_response(chain)

            return {
                "agent_response": agent_response,
                "reasoning": execution_result,
                "task": task,
                "metadata": {
                    "agent_type": agent_type,
                    "reasoning_quality": execution_result.get("quality_score", 0.0),
                    "decision_confidence": execution_result.get("confidence", 0.0)
                }
            }

        except Exception as e:
            self.logger.error(f"Agent CoT enhancement failed: {e}")
            return {
                "agent_response": {"error": str(e)},
                "reasoning": {"error": str(e)},
                "task": task,
                "metadata": {"error": True}
            }

    async def _enhance_agent_steps(self, chain: ReasoningChain, request: Dict[str, Any]):
        """Enhance decision steps with agent-specific functionality."""
        # Find the recommendation step and enhance it
        for step in chain.steps:
            if step.step_id == "make_recommendation":
                step.action = self._agent_decision_action
                step.inputs.update(request)

    async def _agent_decision_action(self, **kwargs) -> Dict[str, Any]:
        """Enhanced agent decision action with CoT reasoning."""
        task = kwargs.get("task", "")
        agent_type = kwargs.get("agent_type", "general")
        context = kwargs.get("context", {})

        self.logger.info(f"Agent {agent_type} processing task: {task}")

        try:
            # Simulate agent processing (replace with actual agent when available)
            if self.agent_manager:
                response = await self._call_agent_manager(task, agent_type, context)
            else:
                response = self._simulate_agent_response(task, agent_type)

            return {
                "recommended_option": response.get("action", "execute_task"),
                "reasoning": response.get("reasoning", "Based on task analysis"),
                "confidence": response.get("confidence", 0.8),
                "next_steps": response.get("next_steps", ["Execute task", "Monitor progress"])
            }

        except Exception as e:
            self.logger.error(f"Agent decision failed: {e}")
            return {
                "recommended_option": "error_handling",
                "reasoning": f"Error occurred: {str(e)}",
                "confidence": 0.1,
                "next_steps": ["Review error", "Retry task"]
            }

    async def _call_agent_manager(self, task: str, agent_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call the actual agent manager."""
        # This would integrate with the actual agent system
        return self._simulate_agent_response(task, agent_type)

    def _simulate_agent_response(self, task: str, agent_type: str) -> Dict[str, Any]:
        """Simulate agent response for testing."""
        return {
            "action": "execute_task",
            "reasoning": f"Task '{task}' is suitable for {agent_type} agent",
            "confidence": 0.85,
            "next_steps": ["Parse task requirements", "Execute task", "Validate results"],
            "estimated_time": "5 minutes"
        }

    async def _extract_agent_response(self, chain: ReasoningChain) -> Dict[str, Any]:
        """Extract agent response from the reasoning chain outputs."""
        response = {}

        for step in chain.steps:
            if step.step_id == "make_recommendation" and step.outputs:
                response = step.outputs
                break

        return response


class SpecKitCoTEnhancer(CoTEnhancer):
    """
    CoT-enhanced GitHub Spec-Kit workflows that add transparent reasoning
    to specification creation and analysis processes.
    """

    def __init__(self, spec_kit_manager=None, cot_framework: Optional[CoTReasoning] = None):
        """
        Initialize the SpecKit CoT enhancer.

        Args:
            spec_kit_manager: Spec-Kit management system
            cot_framework: CoT reasoning framework
        """
        super().__init__("SpecKit CoT Enhancer", cot_framework)
        self.spec_kit_manager = spec_kit_manager
        self.phase1_template = Phase1SpecTemplate()
        self.analysis_template = AnalysisTemplate()

    async def enhance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance Spec-Kit workflow with CoT reasoning.

        Args:
            request: Spec-Kit operation request

        Returns:
            Enhanced spec result with reasoning trace
        """
        operation = request.get("operation", "create")
        spec_type = request.get("type", "specification")
        content = request.get("content", {})

        chain_id = f"speckit_{operation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if operation in ["create", "update"]:
                # Use Phase 1 template for creation/update
                chain = await self.phase1_template.create_chain(
                    cot_framework=self.cot_framework,
                    chain_id=chain_id,
                    context={
                        "type": spec_type,
                        "content": content,
                        "operation": operation
                    }
                )
            else:
                # Use analysis template for other operations
                chain = await self.analysis_template.create_chain(
                    cot_framework=self.cot_framework,
                    chain_id=chain_id,
                    context={
                        "subject": f"Spec-Kit {operation}",
                        "type": "specification_analysis",
                        "content": content
                    }
                )

            # Register chain in enhancer tracking
            self.active_chains[chain_id] = chain

            # Enhance spec steps with SpecKit-specific actions
            await self._enhance_spec_steps(chain, request)

            # Execute the enhanced chain
            execution_result = await self.execute_and_validate_chain(chain_id)

            # Extract spec results
            spec_result = await self._extract_spec_result(chain)

            return {
                "spec_result": spec_result,
                "reasoning": execution_result,
                "operation": operation,
                "metadata": {
                    "spec_type": spec_type,
                    "reasoning_quality": execution_result.get("quality_score", 0.0),
                    "spec_confidence": execution_result.get("confidence", 0.0)
                }
            }

        except Exception as e:
            self.logger.error(f"SpecKit CoT enhancement failed: {e}")
            return {
                "spec_result": {"error": str(e)},
                "reasoning": {"error": str(e)},
                "operation": operation,
                "metadata": {"error": True}
            }

    async def _enhance_spec_steps(self, chain: ReasoningChain, request: Dict[str, Any]):
        """Enhance spec steps with SpecKit-specific functionality."""
        operation = request.get("operation", "create")

        # Find relevant steps based on operation
        if operation == "create":
            target_step = "validate_specification"
        elif operation == "analyze":
            target_step = "validate_analysis"
        else:
            target_step = None

        if target_step:
            for step in chain.steps:
                if step.step_id == target_step:
                    step.action = self._spec_kit_action
                    step.inputs.update(request)

    async def _spec_kit_action(self, **kwargs) -> Dict[str, Any]:
        """Enhanced SpecKit action with CoT reasoning."""
        operation = kwargs.get("operation", "create")
        spec_type = kwargs.get("type", "specification")
        content = kwargs.get("content", {})

        self.logger.info(f"SpecKit {operation} for {spec_type}")

        try:
            # Simulate SpecKit processing (replace with actual manager when available)
            if self.spec_kit_manager:
                result = await self._call_spec_kit_manager(operation, spec_type, content)
            else:
                result = self._simulate_spec_kit_result(operation, spec_type, content)

            return {
                "validation": result.get("status", "passed"),
                "quality_score": result.get("quality_score", 0.85),
                "spec_output": result.get("output", {}),
                "recommendations": result.get("recommendations", [])
            }

        except Exception as e:
            self.logger.error(f"SpecKit action failed: {e}")
            return {
                "validation": "failed",
                "quality_score": 0.0,
                "error": str(e),
                "recommendations": ["Review specification content", "Check SpecKit configuration"]
            }

    async def _call_spec_kit_manager(self, operation: str, spec_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Call the actual SpecKit manager."""
        # This would integrate with the actual SpecKit system
        return self._simulate_spec_kit_result(operation, spec_type, content)

    def _simulate_spec_kit_result(self, operation: str, spec_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate SpecKit result for testing."""
        return {
            "status": "passed",
            "quality_score": 0.88,
            "output": {
                "spec_id": f"spec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": spec_type,
                "operation": operation,
                "validation_passed": True
            },
            "recommendations": [
                "Consider adding more detailed acceptance criteria",
                "Review technical dependencies"
            ]
        }

    async def _extract_spec_result(self, chain: ReasoningChain) -> Dict[str, Any]:
        """Extract spec result from the reasoning chain outputs."""
        result = {}

        # Look for validation or analysis output
        for step in chain.steps:
            if step.step_id in ["validate_specification", "validate_analysis"] and step.outputs:
                result = step.outputs
                break

        return result


# Utility functions for easy integration

async def enhance_perplexity_search(query: str, search_type: str = "web", max_results: int = 10) -> Dict[str, Any]:
    """
    Quick function to enhance a Perplexity search with CoT reasoning.

    Args:
        query: Search query
        search_type: Type of search (web, academic, etc.)
        max_results: Maximum number of results

    Returns:
        Enhanced search results with reasoning trace
    """
    enhancer = PerplexityCoTEnhancer()
    return await enhancer.enhance({
        "query": query,
        "search_type": search_type,
        "max_results": max_results
    })


async def enhance_agent_task(task: str, agent_type: str = "general", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quick function to enhance an agent task with CoT reasoning.

    Args:
        task: Task description
        agent_type: Type of agent to use
        context: Additional context for the task

    Returns:
        Enhanced agent response with reasoning trace
    """
    enhancer = AgentCoTEnhancer()
    return await enhancer.enhance({
        "task": task,
        "agent_type": agent_type,
        "context": context or {}
    })


async def enhance_spec_kit_operation(operation: str, spec_type: str = "specification", content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Quick function to enhance a SpecKit operation with CoT reasoning.

    Args:
        operation: SpecKit operation (create, analyze, etc.)
        spec_type: Type of specification
        content: Specification content

    Returns:
        Enhanced spec result with reasoning trace
    """
    enhancer = SpecKitCoTEnhancer()
    return await enhancer.enhance({
        "operation": operation,
        "type": spec_type,
        "content": content or {}
    })