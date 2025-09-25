"""
Enhanced Memory System for Advanced Swarm Intelligence.

This module provides persistent memory, cross-agent knowledge sharing,
and learning capabilities for the swarm orchestrator system.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
from collections import defaultdict, deque


class SwarmMemory:
    """
    Enhanced memory system for swarm intelligence with persistence and learning.

    Features:
    - Persistent agent memory across sessions
    - Cross-agent knowledge sharing
    - Task execution patterns learning
    - Performance optimization based on history
    - Dynamic agent routing based on past success
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the swarm memory system.

        Args:
            storage_path: Path to store persistent memory data
        """
        self.logger = logging.getLogger(__name__)

        # Storage configuration
        self.storage_path = Path(storage_path) if storage_path else Path.home() / '.torq_console' / 'swarm_memory'
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Memory components
        self.agent_memories = {}  # Per-agent persistent memory
        self.shared_knowledge = {}  # Cross-agent shared knowledge
        self.execution_patterns = defaultdict(list)  # Task execution patterns
        self.performance_history = defaultdict(list)  # Performance tracking
        self.routing_success = defaultdict(dict)  # Agent routing success rates

        # Memory limits and cleanup
        self.max_memory_entries = 10000
        self.max_pattern_history = 1000
        self.memory_cleanup_interval = 3600  # 1 hour
        self.last_cleanup = datetime.now()

        # Learning parameters
        self.learning_weight = 0.7  # Weight for recent vs historical data
        self.success_threshold = 0.8  # Minimum success rate for pattern learning
        self.pattern_confidence_threshold = 0.75

        # Initialize memory system
        self._load_persistent_memory()

        self.logger.info("SwarmMemory initialized with storage at: %s", self.storage_path)

    async def store_agent_memory(self, agent_id: str, memory_key: str, memory_data: Any) -> None:
        """
        Store memory data for a specific agent.

        Args:
            agent_id: The agent identifier
            memory_key: Key for the memory entry
            memory_data: Data to store
        """
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = {}

        self.agent_memories[agent_id][memory_key] = {
            'data': memory_data,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }

        # Trigger cleanup if needed
        await self._cleanup_if_needed()

        self.logger.debug(f"Stored memory for agent {agent_id}: {memory_key}")

    async def retrieve_agent_memory(self, agent_id: str, memory_key: str) -> Optional[Any]:
        """
        Retrieve memory data for a specific agent.

        Args:
            agent_id: The agent identifier
            memory_key: Key for the memory entry

        Returns:
            Stored memory data or None if not found
        """
        if agent_id in self.agent_memories and memory_key in self.agent_memories[agent_id]:
            memory_entry = self.agent_memories[agent_id][memory_key]
            memory_entry['access_count'] += 1
            memory_entry['last_accessed'] = datetime.now().isoformat()

            self.logger.debug(f"Retrieved memory for agent {agent_id}: {memory_key}")
            return memory_entry['data']

        return None

    async def share_knowledge(self, source_agent: str, target_agent: str, knowledge_key: str, knowledge_data: Any) -> None:
        """
        Share knowledge between agents.

        Args:
            source_agent: Agent sharing the knowledge
            target_agent: Agent receiving the knowledge
            knowledge_key: Key for the knowledge entry
            knowledge_data: Knowledge data to share
        """
        knowledge_id = f"{source_agent}_to_{target_agent}_{knowledge_key}"

        self.shared_knowledge[knowledge_id] = {
            'source_agent': source_agent,
            'target_agent': target_agent,
            'knowledge_key': knowledge_key,
            'data': knowledge_data,
            'timestamp': datetime.now().isoformat(),
            'usage_count': 0
        }

        self.logger.info(f"Knowledge shared: {source_agent} -> {target_agent} ({knowledge_key})")

    async def get_shared_knowledge(self, target_agent: str, knowledge_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get shared knowledge for a target agent.

        Args:
            target_agent: Agent requesting knowledge
            knowledge_key: Optional specific knowledge key

        Returns:
            List of shared knowledge entries
        """
        relevant_knowledge = []

        for knowledge_id, knowledge_entry in self.shared_knowledge.items():
            if knowledge_entry['target_agent'] == target_agent:
                if knowledge_key is None or knowledge_entry['knowledge_key'] == knowledge_key:
                    knowledge_entry['usage_count'] += 1
                    relevant_knowledge.append(knowledge_entry)

        return relevant_knowledge

    async def record_execution_pattern(self, task_type: str, agent_sequence: List[str],
                                     execution_time: float, success: bool, context: Dict[str, Any]) -> None:
        """
        Record a task execution pattern for learning.

        Args:
            task_type: Type of task executed
            agent_sequence: Sequence of agents that processed the task
            execution_time: Total execution time
            success: Whether the execution was successful
            context: Additional context about the execution
        """
        pattern = {
            'task_type': task_type,
            'agent_sequence': agent_sequence,
            'execution_time': execution_time,
            'success': success,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        self.execution_patterns[task_type].append(pattern)

        # Update routing success rates
        for i, agent in enumerate(agent_sequence):
            next_agent = agent_sequence[i + 1] if i + 1 < len(agent_sequence) else 'completed'

            if agent not in self.routing_success:
                self.routing_success[agent] = {}

            if next_agent not in self.routing_success[agent]:
                self.routing_success[agent][next_agent] = {'success': 0, 'total': 0}

            self.routing_success[agent][next_agent]['total'] += 1
            if success:
                self.routing_success[agent][next_agent]['success'] += 1

        # Limit pattern history size
        if len(self.execution_patterns[task_type]) > self.max_pattern_history:
            self.execution_patterns[task_type] = self.execution_patterns[task_type][-self.max_pattern_history:]

        self.logger.debug(f"Recorded execution pattern for {task_type}: {agent_sequence}")

    async def get_optimal_agent_sequence(self, task_type: str, context: Dict[str, Any]) -> List[str]:
        """
        Get optimal agent sequence based on historical patterns.

        Args:
            task_type: Type of task to execute
            context: Task context for pattern matching

        Returns:
            Recommended agent sequence
        """
        if task_type not in self.execution_patterns:
            return self._get_default_sequence(task_type)

        patterns = self.execution_patterns[task_type]

        # Filter successful patterns
        successful_patterns = [p for p in patterns if p['success']]

        if not successful_patterns:
            return self._get_default_sequence(task_type)

        # Score patterns based on recency, success rate, and context similarity
        scored_patterns = []

        for pattern in successful_patterns:
            score = self._score_pattern(pattern, context)
            scored_patterns.append((score, pattern))

        # Get the highest scoring pattern
        if scored_patterns:
            scored_patterns.sort(reverse=True)
            best_pattern = scored_patterns[0][1]

            self.logger.info(f"Optimal sequence for {task_type}: {best_pattern['agent_sequence']}")
            return best_pattern['agent_sequence']

        return self._get_default_sequence(task_type)

    async def get_agent_routing_recommendation(self, current_agent: str, task_context: Dict[str, Any]) -> Optional[str]:
        """
        Get next agent recommendation based on routing success history.

        Args:
            current_agent: Current agent making the routing decision
            task_context: Context of the current task

        Returns:
            Recommended next agent or None
        """
        if current_agent not in self.routing_success:
            return None

        routing_stats = self.routing_success[current_agent]

        # Calculate success rates
        success_rates = {}
        for next_agent, stats in routing_stats.items():
            if stats['total'] >= 3:  # Minimum sample size
                success_rate = stats['success'] / stats['total']
                success_rates[next_agent] = success_rate

        if not success_rates:
            return None

        # Get agent with highest success rate
        best_agent = max(success_rates.items(), key=lambda x: x[1])

        if best_agent[1] >= self.success_threshold:
            self.logger.debug(f"Routing recommendation for {current_agent}: {best_agent[0]} (success rate: {best_agent[1]:.2f})")
            return best_agent[0]

        return None

    async def record_performance_metric(self, agent_id: str, metric_name: str,
                                      metric_value: float, context: Dict[str, Any]) -> None:
        """
        Record performance metrics for agents.

        Args:
            agent_id: Agent identifier
            metric_name: Name of the performance metric
            metric_value: Value of the metric
            context: Additional context
        """
        performance_entry = {
            'metric_name': metric_name,
            'metric_value': metric_value,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        self.performance_history[agent_id].append(performance_entry)

        # Limit history size
        if len(self.performance_history[agent_id]) > self.max_pattern_history:
            self.performance_history[agent_id] = self.performance_history[agent_id][-self.max_pattern_history:]

    async def get_agent_performance_insights(self, agent_id: str, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance insights for an agent.

        Args:
            agent_id: Agent identifier
            metric_name: Optional specific metric name

        Returns:
            Performance insights
        """
        if agent_id not in self.performance_history:
            return {'insights': 'No performance data available'}

        metrics = self.performance_history[agent_id]

        if metric_name:
            metrics = [m for m in metrics if m['metric_name'] == metric_name]

        if not metrics:
            return {'insights': f'No data for metric: {metric_name}'}

        # Calculate basic statistics
        recent_metrics = metrics[-50:]  # Last 50 entries
        values = [m['metric_value'] for m in recent_metrics]

        insights = {
            'total_entries': len(metrics),
            'recent_entries': len(recent_metrics),
            'average_value': sum(values) / len(values) if values else 0,
            'min_value': min(values) if values else 0,
            'max_value': max(values) if values else 0,
            'trend': self._calculate_trend(values),
            'last_updated': recent_metrics[-1]['timestamp'] if recent_metrics else None
        }

        return insights

    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Optimize memory usage by cleaning up old or unused entries.

        Returns:
            Optimization report
        """
        report = {
            'entries_cleaned': 0,
            'memory_freed': 0,
            'optimization_time': datetime.now().isoformat()
        }

        # Clean up old agent memories
        cutoff_date = datetime.now() - timedelta(days=30)

        for agent_id in list(self.agent_memories.keys()):
            for memory_key in list(self.agent_memories[agent_id].keys()):
                memory_entry = self.agent_memories[agent_id][memory_key]
                entry_date = datetime.fromisoformat(memory_entry['timestamp'])

                # Remove if old and rarely accessed
                if entry_date < cutoff_date and memory_entry['access_count'] < 3:
                    del self.agent_memories[agent_id][memory_key]
                    report['entries_cleaned'] += 1

        # Clean up old shared knowledge
        for knowledge_id in list(self.shared_knowledge.keys()):
            knowledge_entry = self.shared_knowledge[knowledge_id]
            entry_date = datetime.fromisoformat(knowledge_entry['timestamp'])

            if entry_date < cutoff_date and knowledge_entry['usage_count'] < 2:
                del self.shared_knowledge[knowledge_id]
                report['entries_cleaned'] += 1

        self.logger.info(f"Memory optimization completed: {report['entries_cleaned']} entries cleaned")
        return report

    def _score_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Score a pattern based on recency, success, and context similarity."""
        # Recency score (more recent = higher score)
        pattern_time = datetime.fromisoformat(pattern['timestamp'])
        time_diff = datetime.now() - pattern_time
        recency_score = max(0, 1 - (time_diff.days / 30))  # Decay over 30 days

        # Success score
        success_score = 1.0 if pattern['success'] else 0.0

        # Context similarity score
        similarity_score = self._calculate_context_similarity(pattern['context'], context)

        # Weighted final score
        final_score = (recency_score * 0.3 + success_score * 0.5 + similarity_score * 0.2)

        return final_score

    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts."""
        if not context1 or not context2:
            return 0.5  # Neutral similarity for empty contexts

        common_keys = set(context1.keys()) & set(context2.keys())

        if not common_keys:
            return 0.3  # Low similarity for no common keys

        similarity_sum = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                similarity_sum += 1

        return similarity_sum / len(common_keys)

    def _get_default_sequence(self, task_type: str) -> List[str]:
        """Get default agent sequence for task type."""
        default_sequences = {
            'search': ['search_agent', 'analysis_agent', 'synthesis_agent', 'response_agent'],
            'code_analysis': ['code_agent', 'testing_agent', 'documentation_agent', 'response_agent'],
            'performance_optimization': ['performance_agent', 'code_agent', 'testing_agent', 'response_agent'],
            'api_documentation': ['documentation_agent', 'testing_agent', 'response_agent'],
            'general': ['search_agent', 'analysis_agent', 'synthesis_agent', 'response_agent']
        }

        return default_sequences.get(task_type, default_sequences['general'])

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a series of values."""
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg * 1.1:
            return 'improving'
        elif second_avg < first_avg * 0.9:
            return 'declining'
        else:
            return 'stable'

    async def _cleanup_if_needed(self) -> None:
        """Cleanup memory if needed based on time interval."""
        if datetime.now() - self.last_cleanup > timedelta(seconds=self.memory_cleanup_interval):
            await self.optimize_memory_usage()
            await self.save_persistent_memory()
            self.last_cleanup = datetime.now()

    def _load_persistent_memory(self) -> None:
        """Load persistent memory from storage."""
        try:
            # Load agent memories
            agent_memory_file = self.storage_path / 'agent_memories.json'
            if agent_memory_file.exists():
                with open(agent_memory_file, 'r') as f:
                    self.agent_memories = json.load(f)

            # Load shared knowledge
            shared_knowledge_file = self.storage_path / 'shared_knowledge.json'
            if shared_knowledge_file.exists():
                with open(shared_knowledge_file, 'r') as f:
                    self.shared_knowledge = json.load(f)

            # Load execution patterns
            patterns_file = self.storage_path / 'execution_patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.execution_patterns = defaultdict(list, data)

            # Load routing success
            routing_file = self.storage_path / 'routing_success.json'
            if routing_file.exists():
                with open(routing_file, 'r') as f:
                    data = json.load(f)
                    self.routing_success = defaultdict(dict, data)

            # Load performance history
            performance_file = self.storage_path / 'performance_history.json'
            if performance_file.exists():
                with open(performance_file, 'r') as f:
                    data = json.load(f)
                    self.performance_history = defaultdict(list, data)

            self.logger.info("Persistent memory loaded successfully")

        except Exception as e:
            self.logger.warning(f"Failed to load persistent memory: {e}")

    async def save_persistent_memory(self) -> None:
        """Save persistent memory to storage."""
        try:
            # Save agent memories
            with open(self.storage_path / 'agent_memories.json', 'w') as f:
                json.dump(self.agent_memories, f, indent=2)

            # Save shared knowledge
            with open(self.storage_path / 'shared_knowledge.json', 'w') as f:
                json.dump(self.shared_knowledge, f, indent=2)

            # Save execution patterns
            with open(self.storage_path / 'execution_patterns.json', 'w') as f:
                json.dump(dict(self.execution_patterns), f, indent=2)

            # Save routing success
            with open(self.storage_path / 'routing_success.json', 'w') as f:
                json.dump(dict(self.routing_success), f, indent=2)

            # Save performance history
            with open(self.storage_path / 'performance_history.json', 'w') as f:
                json.dump(dict(self.performance_history), f, indent=2)

            self.logger.info("Persistent memory saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save persistent memory: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            'agent_memories': len(self.agent_memories),
            'shared_knowledge_entries': len(self.shared_knowledge),
            'execution_patterns': sum(len(patterns) for patterns in self.execution_patterns.values()),
            'routing_success_entries': sum(len(routes) for routes in self.routing_success.values()),
            'performance_history_entries': sum(len(history) for history in self.performance_history.values()),
            'storage_path': str(self.storage_path),
            'last_cleanup': self.last_cleanup.isoformat(),
            'memory_limits': {
                'max_memory_entries': self.max_memory_entries,
                'max_pattern_history': self.max_pattern_history
            }
        }