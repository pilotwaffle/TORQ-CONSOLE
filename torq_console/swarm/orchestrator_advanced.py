"""
Advanced Swarm Orchestrator for TORQ CONSOLE with Parallel Execution and Dynamic Routing.

This module coordinates a multi-agent swarm system with enhanced capabilities including:
- 8 specialized agents with distinct expertise
- Parallel execution using asyncio.gather()
- Dynamic task routing based on AI and learning
- Persistent memory system with cross-agent knowledge sharing
- Autonomous task distribution and optimization
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .agents.search_agent import SearchAgent
from .agents.analysis_agent import AnalysisAgent
from .agents.synthesis_agent import SynthesisAgent
from .agents.response_agent import ResponseAgent
from .agents.code_agent import CodeAgent
from .agents.documentation_agent import DocumentationAgent
from .agents.testing_agent import TestingAgent
from .agents.performance_agent import PerformanceAgent
from .memory_system import SwarmMemory
from .communication_tools import communication_tools
from .communication_parser import communication_parser


class AdvancedSwarmOrchestrator:
    """
    Advanced Swarm Orchestrator with Dynamic Routing and Parallel Execution.

    Features:
    - 8 specialized agents with distinct expertise
    - Parallel execution with asyncio.gather()
    - Dynamic task routing based on context and learning
    - Persistent memory system with cross-agent knowledge sharing
    - Directional communication flows with '>' operator (Agency Swarm compatible)
    - Inter-agent messaging with send_message tool
    - Autonomous task distribution and optimization
    """

    def __init__(self, llm_manager=None, web_search_provider=None, memory_storage_path=None):
        """
        Initialize the advanced swarm orchestrator.

        Args:
            llm_manager: LLM manager instance for agent AI capabilities
            web_search_provider: Web search provider for search operations
            memory_storage_path: Path for persistent memory storage
        """
        self.llm_manager = llm_manager
        self.web_search_provider = web_search_provider
        self.logger = logging.getLogger(__name__)

        # Initialize enhanced memory system
        self.memory = SwarmMemory(memory_storage_path)

        # Initialize all 8 specialized agents
        self.agents = self._initialize_agents()

        # Advanced coordination settings
        self.max_parallel_agents = 4  # Maximum agents running in parallel
        self.max_handoffs = 15  # Increased for complex tasks
        self.execution_timeout = 600  # 10 minutes for complex tasks
        self.dynamic_routing = True  # Enable AI-driven routing
        self.parallel_execution = True  # Enable parallel processing
        self.communication_enabled = True  # Enable directional communication

        # Task execution tracking
        self.execution_history = []
        self.max_history = 100
        self.active_tasks = {}

        self.logger.info("Advanced SwarmOrchestrator initialized with %d agents: %s",
                        len(self.agents), ", ".join(self.agents.keys()))

        if self.communication_enabled:
            self.logger.info("Agency Swarm compatible directional communication enabled")

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all 8 specialized swarm agents."""
        # Get LLM provider for agents
        llm_provider = None
        if self.llm_manager:
            llm_provider = self.llm_manager.get_provider('deepseek')

        agents = {
            # Original 4 agents
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
            ),
            # New 4 specialized agents
            'code_agent': CodeAgent(
                llm_provider=llm_provider
            ),
            'documentation_agent': DocumentationAgent(
                llm_provider=llm_provider
            ),
            'testing_agent': TestingAgent(
                llm_provider=llm_provider
            ),
            'performance_agent': PerformanceAgent(
                llm_provider=llm_provider
            )
        }

        return agents

    async def execute_task(self, task: Dict[str, Any]) -> str:
        """
        Execute a task through the advanced swarm system with parallel execution.

        Args:
            task: Task dictionary with type, query, and context

        Returns:
            Final response string from the swarm
        """
        task_id = task.get('id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        task_type = task.get('type', 'general')

        self.logger.info(f"Executing advanced task {task_id}: {task_type}")

        # Track active task
        start_time = datetime.now()
        self.active_tasks[task_id] = {
            'start_time': start_time,
            'task_type': task_type,
            'status': 'running'
        }

        try:
            # Handle directional communication if present
            query = task.get('query', '')
            if self.communication_enabled and communication_parser.has_directional_syntax(query):
                self.logger.info(f"Task {task_id}: Processing directional communication syntax")

                # Parse and execute directional messages
                comm_result = await communication_tools.parse_directional_command(query, 'orchestrator')

                if comm_result['success'] and comm_result['messages_sent'] > 0:
                    self.logger.info(f"Task {task_id}: Sent {comm_result['messages_sent']} directional messages")

                    # Update task with base query (without directional syntax)
                    task['query'] = comm_result['base_query']
                    task['communication_context'] = {
                        'directional_messages_sent': comm_result['messages_sent'],
                        'send_results': comm_result['send_results']
                    }
            # Determine execution strategy based on task complexity
            if self.parallel_execution and self._can_parallelize_task(task):
                result = await asyncio.wait_for(
                    self._execute_parallel_task(task),
                    timeout=self.execution_timeout
                )
            else:
                result = await asyncio.wait_for(
                    self._execute_dynamic_task_chain(task),
                    timeout=self.execution_timeout
                )

            # Include communication context in result if present
            if 'communication_context' in task:
                comm_context = task['communication_context']
                if comm_context['directional_messages_sent'] > 0:
                    result += f"\n\n---\n**Communication Summary**: Sent {comm_context['directional_messages_sent']} inter-agent messages via directional communication flows."

            # Record successful execution in memory
            execution_time = (datetime.now() - start_time).total_seconds()
            agent_sequence = self.active_tasks[task_id].get('agent_sequence', [])

            await self.memory.record_execution_pattern(
                task_type=task_type,
                agent_sequence=agent_sequence,
                execution_time=execution_time,
                success=True,
                context=task.get('context', {})
            )

            # Update task status
            self.active_tasks[task_id]['status'] = 'completed'
            self.active_tasks[task_id]['result'] = result

            # Log successful completion
            self._log_execution(task_id, 'completed', result)

            return result

        except asyncio.TimeoutError:
            error_msg = f"Task {task_id} timed out after {self.execution_timeout} seconds"
            self.logger.error(error_msg)
            self.active_tasks[task_id]['status'] = 'timeout'
            self._log_execution(task_id, 'timeout', error_msg)
            return f"The task took too long to complete. Please try a more specific query or break down the request into smaller parts."

        except Exception as e:
            error_msg = f"Task {task_id} failed: {e}"
            self.logger.error(error_msg)
            self.active_tasks[task_id]['status'] = 'error'
            self.active_tasks[task_id]['error'] = str(e)

            # Record failed execution
            execution_time = (datetime.now() - start_time).total_seconds()
            agent_sequence = self.active_tasks[task_id].get('agent_sequence', [])

            await self.memory.record_execution_pattern(
                task_type=task_type,
                agent_sequence=agent_sequence,
                execution_time=execution_time,
                success=False,
                context=task.get('context', {})
            )

            self._log_execution(task_id, 'error', error_msg)
            return f"I encountered an error while processing your request. Please try rephrasing your query or contact support if the issue persists."

        finally:
            # Cleanup completed task
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def _execute_dynamic_task_chain(self, task: Dict[str, Any]) -> str:
        """Execute task through dynamic agent chain with AI-driven routing."""
        task_id = task.get('id', 'unknown')
        task_type = task.get('type', 'general')
        current_task = task.copy()

        # Get optimal agent sequence from memory system
        if self.dynamic_routing:
            agent_sequence = await self.memory.get_optimal_agent_sequence(
                task_type, task.get('context', {})
            )
            start_agent = agent_sequence[0] if agent_sequence else 'search_agent'
        else:
            start_agent = self._determine_start_agent(task)
            agent_sequence = []

        current_agent = start_agent
        handoff_count = 0
        executed_agents = []

        self.logger.info(f"Task {task_id}: Starting with {current_agent}, sequence: {agent_sequence}")

        while current_agent and handoff_count < self.max_handoffs:
            self.logger.debug(f"Task {task_id} Handoff #{handoff_count + 1}: Processing with {current_agent}")

            # Get the current agent
            agent = self.agents.get(current_agent)
            if not agent:
                self.logger.error(f"Agent {current_agent} not found")
                break

            executed_agents.append(current_agent)

            # Store agent memory before processing
            await self.memory.store_agent_memory(
                current_agent,
                f"task_{task_id}_context",
                {
                    'task_type': task_type,
                    'context': current_task.get('context', {}),
                    'handoff_count': handoff_count
                }
            )

            # Process task with current agent
            agent_start_time = datetime.now()
            result = await agent.process_task(current_task)
            agent_processing_time = (datetime.now() - agent_start_time).total_seconds()

            # Record agent performance
            await self.memory.record_performance_metric(
                current_agent,
                'processing_time',
                agent_processing_time,
                {'task_type': task_type, 'handoff_count': handoff_count}
            )

            # Determine next agent using AI routing or sequence
            if self.dynamic_routing and handoff_count < len(agent_sequence) - 1:
                # Use pre-determined sequence
                next_agent = agent_sequence[handoff_count + 1]
            else:
                # Use agent recommendation or memory-based routing
                suggested_next = result.get('next_agent')
                memory_recommendation = await self.memory.get_agent_routing_recommendation(
                    current_agent, current_task.get('context', {})
                )

                next_agent = memory_recommendation or suggested_next

            # Check if this is the final result
            if not next_agent or next_agent == 'response_agent':
                # Ensure we end with response_agent if not already there
                if current_agent != 'response_agent' and 'response_agent' in self.agents:
                    current_task.update(result)
                    final_agent = self.agents['response_agent']
                    final_result = await final_agent.process_task(current_task)
                    executed_agents.append('response_agent')
                    final_response = final_result.get('final_response', final_result.get('results', ''))
                else:
                    final_response = result.get('final_response', result.get('results', ''))

                # Store agent sequence in active task for tracking
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]['agent_sequence'] = executed_agents

                return str(final_response) if final_response else self._create_fallback_response(task.get('query', ''))

            # Share knowledge between agents
            if result.get('results') and next_agent in self.agents:
                await self.memory.share_knowledge(
                    current_agent,
                    next_agent,
                    f"task_{task_id}_results",
                    result.get('results')
                )

            # Prepare for next agent handoff
            current_task.update(result)
            current_agent = next_agent
            handoff_count += 1

        # Store agent sequence for tracking
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['agent_sequence'] = executed_agents

        # If we exit the loop, we hit max handoffs
        self.logger.warning(f"Task {task_id}: Hit maximum handoffs ({self.max_handoffs}), executed: {executed_agents}")
        return self._create_fallback_response(task.get('query', ''))

    async def _execute_parallel_task(self, task: Dict[str, Any]) -> str:
        """Execute task using parallel agent processing where applicable."""
        task_id = task.get('id', 'unknown')
        task_type = task.get('type', 'general')

        # Determine which agents can run in parallel for this task type
        parallel_agents = self._get_parallel_agents(task_type)

        if len(parallel_agents) <= 1:
            # Fall back to sequential processing
            return await self._execute_dynamic_task_chain(task)

        self.logger.info(f"Task {task_id}: Executing in parallel with agents: {parallel_agents}")

        # Create parallel tasks
        parallel_tasks = []
        for agent_id in parallel_agents:
            if agent_id in self.agents:
                agent_task = task.copy()
                agent_task['parallel_mode'] = True
                agent_task['agent_focus'] = self._get_agent_focus(agent_id, task_type)
                parallel_tasks.append(self._execute_agent_task(agent_id, agent_task))

        # Execute agents in parallel
        try:
            parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

            # Process parallel results
            successful_results = []
            agent_sequence = []

            for i, result in enumerate(parallel_results):
                agent_id = parallel_agents[i]
                agent_sequence.append(agent_id)

                if isinstance(result, Exception):
                    self.logger.warning(f"Agent {agent_id} failed in parallel execution: {result}")
                else:
                    successful_results.append({
                        'agent_id': agent_id,
                        'result': result
                    })

            # Store agent sequence
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['agent_sequence'] = agent_sequence

            # Synthesize parallel results
            if successful_results:
                return await self._synthesize_parallel_results(successful_results, task)
            else:
                return self._create_fallback_response(task.get('query', ''))

        except Exception as e:
            self.logger.error(f"Parallel execution failed for task {task_id}: {e}")
            # Fall back to sequential processing
            return await self._execute_dynamic_task_chain(task)

    async def _execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Record start time
        start_time = datetime.now()

        # Process task
        result = await agent.process_task(task)

        # Record performance
        processing_time = (datetime.now() - start_time).total_seconds()
        await self.memory.record_performance_metric(
            agent_id,
            'processing_time',
            processing_time,
            {'task_type': task.get('type', 'general'), 'parallel_mode': True}
        )

        return result

    async def _synthesize_parallel_results(self, results: List[Dict[str, Any]], original_task: Dict[str, Any]) -> str:
        """Synthesize results from parallel agent execution."""
        # Use synthesis agent to combine parallel results
        synthesis_agent = self.agents.get('synthesis_agent')
        if not synthesis_agent:
            # Fallback: simple concatenation
            combined_results = "\n\n".join(
                f"**{r['agent_id'].replace('_', ' ').title()}:**\n{r['result'].get('results', str(r['result']))}"
                for r in results
            )
            return combined_results

        # Create synthesis task
        synthesis_task = {
            'type': 'parallel_synthesis',
            'parallel_results': results,
            'original_query': original_task.get('query', ''),
            'context': original_task.get('context', {})
        }

        synthesis_result = await synthesis_agent.process_task(synthesis_task)

        # Use response agent for final formatting
        response_agent = self.agents.get('response_agent')
        if response_agent:
            final_task = {
                'type': 'final_response',
                'synthesis_result': synthesis_result,
                'original_query': original_task.get('query', ''),
                'context': original_task.get('context', {})
            }
            final_result = await response_agent.process_task(final_task)
            return final_result.get('final_response', str(synthesis_result))

        return str(synthesis_result.get('results', synthesis_result))

    def _can_parallelize_task(self, task: Dict[str, Any]) -> bool:
        """Determine if a task can benefit from parallel execution."""
        task_type = task.get('type', 'general')
        query = task.get('query', '').lower()

        # Tasks that benefit from parallel execution
        parallel_task_types = ['code_analysis', 'comprehensive_research', 'multi_domain_search']
        parallel_keywords = ['analyze', 'research', 'compare', 'evaluate', 'comprehensive']

        if task_type in parallel_task_types:
            return True

        if any(keyword in query for keyword in parallel_keywords):
            return True

        return False

    def _get_parallel_agents(self, task_type: str) -> List[str]:
        """Get list of agents that can run in parallel for given task type."""
        parallel_configurations = {
            'code_analysis': ['code_agent', 'testing_agent', 'performance_agent'],
            'research': ['search_agent', 'analysis_agent'],
            'documentation': ['documentation_agent', 'code_agent'],
            'comprehensive_search': ['search_agent', 'analysis_agent', 'synthesis_agent'],
            'general': ['search_agent', 'analysis_agent']
        }

        return parallel_configurations.get(task_type, parallel_configurations['general'])

    def _get_agent_focus(self, agent_id: str, task_type: str) -> str:
        """Get specific focus area for agent in parallel execution."""
        focus_mapping = {
            'code_agent': 'code_quality_and_structure',
            'testing_agent': 'test_coverage_and_validation',
            'performance_agent': 'performance_optimization',
            'search_agent': 'information_gathering',
            'analysis_agent': 'deep_analysis',
            'documentation_agent': 'documentation_quality'
        }

        return focus_mapping.get(agent_id, 'general_analysis')

    def _determine_start_agent(self, task: Dict[str, Any]) -> str:
        """Determine the best starting agent based on task characteristics."""
        task_type = task.get('type', 'general')
        query = task.get('query', '').lower()

        # Agent selection based on task type and keywords
        if task_type == 'code_analysis' or 'code' in query:
            return 'code_agent'
        elif task_type == 'documentation' or 'document' in query:
            return 'documentation_agent'
        elif task_type == 'testing' or 'test' in query:
            return 'testing_agent'
        elif task_type == 'performance' or 'performance' in query or 'optimize' in query:
            return 'performance_agent'
        else:
            return 'search_agent'  # Default starting agent

    def _create_fallback_response(self, query: str) -> str:
        """Create a fallback response when the chain fails."""
        return f"""I attempted to process your request about "{query}" but encountered some difficulties in the swarm processing.

The advanced agent system tried multiple approaches but couldn't complete the full analysis. Here are some suggestions:

• Try rephrasing your query with more specific details
• Break down complex requests into smaller, focused questions
• Check if you're requesting information that requires specific expertise areas
• Verify that all required context and parameters are provided

The swarm learning system will use this feedback to improve future responses."""

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

    # Legacy API compatibility methods
    async def search_ai_news(self, query: str = "latest AI news") -> str:
        """Specialized method for AI news searches."""
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
        """Search for recent developments on a specific topic."""
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
        """Perform a general search query."""
        task = {
            'type': 'general_search',
            'query': query,
            'context': {
                'search_type': 'general',
                'priority': 'normal'
            }
        }
        return await self.execute_task(task)

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the swarm system."""
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

        # Get memory system stats
        memory_stats = await self.memory.get_memory_stats()

        return {
            'orchestrator_status': 'active',
            'orchestrator_type': 'advanced',
            'agents': agent_statuses,
            'memory_system': memory_stats,
            'execution_history_count': len(self.execution_history),
            'active_tasks_count': len(self.active_tasks),
            'llm_manager_available': self.llm_manager is not None,
            'web_search_available': self.web_search_provider is not None,
            'configuration': {
                'max_handoffs': self.max_handoffs,
                'execution_timeout': self.execution_timeout,
                'max_parallel_agents': self.max_parallel_agents,
                'dynamic_routing': self.dynamic_routing,
                'parallel_execution': self.parallel_execution
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on the swarm system."""
        try:
            # Test a simple task
            test_task = {
                'type': 'health_check',
                'query': 'system health test',
                'context': {'test': True}
            }

            # Run with shorter timeout for health check
            result = await asyncio.wait_for(
                self._execute_dynamic_task_chain(test_task),
                timeout=30  # 30 second timeout for health check
            )

            # Check memory system
            memory_stats = await self.memory.get_memory_stats()

            return {
                'status': 'healthy',
                'test_result': 'passed',
                'response_length': len(result) if result else 0,
                'agents_count': len(self.agents),
                'memory_system_status': 'operational',
                'memory_entries': memory_stats.get('agent_memories', 0),
                'parallel_execution': self.parallel_execution,
                'dynamic_routing': self.dynamic_routing
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'test_result': 'failed',
                'error': str(e),
                'agents_count': len(self.agents),
                'memory_system_status': 'unknown'
            }