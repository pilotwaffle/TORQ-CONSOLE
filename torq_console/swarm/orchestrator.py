"""
Swarm Orchestrator for TORQ CONSOLE.

This module coordinates the multi-agent swarm system, managing agent handoffs
and task delegation based on OpenAI Swarm principles and natural swarm intelligence.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .agents.search_agent import SearchAgent
from .agents.analysis_agent import AnalysisAgent
from .agents.synthesis_agent import SynthesisAgent
from .agents.response_agent import ResponseAgent


class SwarmOrchestrator:
    """
    Central orchestrator for the multi-agent swarm system.

    Coordinates agent handoffs and ensures smooth information flow between
    specialized agents following swarm intelligence principles.
    """

    def __init__(self, llm_manager=None, web_search_provider=None):
        """
        Initialize the swarm orchestrator.

        Args:
            llm_manager: LLM manager instance for agent AI capabilities
            web_search_provider: Web search provider for search operations
        """
        self.llm_manager = llm_manager
        self.web_search_provider = web_search_provider
        self.logger = logging.getLogger(__name__)

        # Initialize agents
        self.agents = self._initialize_agents()

        # Task execution history
        self.execution_history = []
        self.max_history = 50

        # Agent coordination settings
        self.max_handoffs = 10  # Prevent infinite loops
        self.execution_timeout = 300  # 5 minutes max per task

        self.logger.info("SwarmOrchestrator initialized with agents: " +
                        ", ".join(self.agents.keys()))

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all swarm agents."""
        # Get LLM provider for agents
        llm_provider = None
        if self.llm_manager:
            llm_provider = self.llm_manager.get_provider('deepseek')

        agents = {
            'search_agent': SearchAgent(
                web_search_provider=self.web_search_provider,
                llm_provider=llm_provider
            ),
            'analysis_agent': AnalysisAgent(
                llm_provider=llm_provider
            ),
            'synthesis_agent': SynthesisAgent(
                llm_provider=llm_provider
            ),
            'response_agent': ResponseAgent(
                llm_provider=llm_provider
            )
        }

        return agents

    async def execute_task(self, task: Dict[str, Any]) -> str:
        """
        Execute a task through the swarm system.

        Args:
            task: Task dictionary with type, query, and context

        Returns:
            Final response string from the swarm
        """
        task_id = task.get('id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        self.logger.info(f"Executing task {task_id}: {task.get('type', 'unknown')}")

        try:
            # Start task execution with timeout
            result = await asyncio.wait_for(
                self._execute_task_chain(task),
                timeout=self.execution_timeout
            )

            # Log successful completion
            self._log_execution(task_id, 'completed', result)

            return result

        except asyncio.TimeoutError:
            error_msg = f"Task {task_id} timed out after {self.execution_timeout} seconds"
            self.logger.error(error_msg)
            self._log_execution(task_id, 'timeout', error_msg)
            return f"I apologize, but the search operation took too long to complete. Please try a more specific query or try again later."

        except Exception as e:
            error_msg = f"Task {task_id} failed: {e}"
            self.logger.error(error_msg)
            self._log_execution(task_id, 'error', error_msg)
            return f"I apologize, but I encountered an error while processing your request: {e}"

    async def _execute_task_chain(self, task: Dict[str, Any]) -> str:
        """Execute the task through the agent chain."""
        current_task = task.copy()
        current_agent = 'search_agent'  # Always start with search
        handoff_count = 0

        while current_agent and handoff_count < self.max_handoffs:
            self.logger.debug(f"Handoff #{handoff_count + 1}: Processing with {current_agent}")

            # Get the current agent
            agent = self.agents.get(current_agent)
            if not agent:
                raise ValueError(f"Agent {current_agent} not found")

            # Process task with current agent
            result = await agent.process_task(current_task)

            # Check if this is the final result
            next_agent = result.get('next_agent')
            if not next_agent:
                # Final response from ResponseAgent
                final_response = result.get('final_response', '')
                if final_response:
                    return final_response
                else:
                    # Fallback if no final response
                    return self._create_fallback_response(current_task.get('query', ''))

            # Prepare for next agent handoff
            current_task = result
            current_agent = next_agent
            handoff_count += 1

        # If we exit the loop, we hit max handoffs
        self.logger.warning(f"Hit maximum handoffs ({self.max_handoffs}), returning current result")
        return self._create_fallback_response(task.get('query', ''))

    def _create_fallback_response(self, query: str) -> str:
        """Create a fallback response when the chain fails."""
        return f"""I attempted to search for information about "{query}" but encountered some technical difficulties in processing the results.

For the most current information, I recommend:
• Checking official websites and recent news sources
• Using search engines directly for real-time results
• Consulting relevant academic or industry publications
• Verifying information from multiple reliable sources

I apologize for not being able to provide more specific results at this time."""

    async def search_ai_news(self, query: str = "latest AI news") -> str:
        """
        Specialized method for AI news searches.

        Args:
            query: AI news search query

        Returns:
            Formatted AI news response
        """
        task = {
            'type': 'ai_news_search',
            'query': query,
            'context': {
                'search_type': 'ai_news',
                'priority': 'high',
                'max_results': 8
            }
        }

        return await self.execute_task(task)

    async def search_recent_developments(self, topic: str, days: int = 7) -> str:
        """
        Search for recent developments on a specific topic.

        Args:
            topic: Topic to search for
            days: Number of days to look back

        Returns:
            Formatted response about recent developments
        """
        task = {
            'type': 'recent_developments',
            'query': topic,
            'context': {
                'days_back': days,
                'search_type': 'news',
                'priority': 'high'
            }
        }

        return await self.execute_task(task)

    async def general_search(self, query: str) -> str:
        """
        Perform a general search query.

        Args:
            query: Search query

        Returns:
            Formatted search response
        """
        task = {
            'type': 'general_search',
            'query': query,
            'context': {
                'search_type': 'general',
                'priority': 'normal'
            }
        }

        return await self.execute_task(task)

    def _log_execution(self, task_id: str, status: str, result: Any):
        """Log task execution for history tracking."""
        execution_entry = {
            'task_id': task_id,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'result_length': len(str(result)) if result else 0
        }

        self.execution_history.append(execution_entry)

        # Trim history if too long
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of the entire swarm system."""
        agent_statuses = {}

        for agent_name, agent in self.agents.items():
            try:
                agent_statuses[agent_name] = await agent.get_status()
            except Exception as e:
                agent_statuses[agent_name] = {
                    'agent_id': agent_name,
                    'status': 'error',
                    'error': str(e)
                }

        return {
            'orchestrator_status': 'active',
            'agents': agent_statuses,
            'execution_history_count': len(self.execution_history),
            'llm_manager_available': self.llm_manager is not None,
            'web_search_available': self.web_search_provider is not None,
            'max_handoffs': self.max_handoffs,
            'execution_timeout': self.execution_timeout
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the swarm system."""
        try:
            # Test a simple task
            test_task = {
                'type': 'general_search',
                'query': 'test query',
                'context': {'test': True}
            }

            # Run with shorter timeout for health check
            result = await asyncio.wait_for(
                self._execute_task_chain(test_task),
                timeout=10  # 10 second timeout for health check
            )

            return {
                'status': 'healthy',
                'test_result': 'passed',
                'response_length': len(result) if result else 0
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'test_result': 'failed',
                'error': str(e)
            }