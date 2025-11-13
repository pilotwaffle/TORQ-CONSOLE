"""
Phase 3: Agent System Enhancements.

Advanced agent capabilities:
1. Cross-agent learning and knowledge sharing
2. Agent performance monitoring
3. Advanced coordination patterns
4. Agent specialization framework
5. Distributed agent execution

These enhancements build on the existing Prince Flowers agent system.

Phase A.4: Error handling and logging for production reliability
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import statistics

# Logger for error handling
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles."""
    GENERALIST = "generalist"  # General-purpose
    SPECIALIST_CODE = "specialist_code"  # Code generation expert
    SPECIALIST_DEBUG = "specialist_debug"  # Debugging expert
    SPECIALIST_ARCH = "specialist_arch"  # Architecture expert
    SPECIALIST_TEST = "specialist_test"  # Testing expert
    COORDINATOR = "coordinator"  # Multi-agent coordinator
    MONITOR = "monitor"  # Performance monitoring


@dataclass
class AgentPerformanceMetric:
    """Performance metrics for an agent."""
    agent_id: str
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    """Shared knowledge item between agents."""
    knowledge_id: str
    source_agent: str
    knowledge_type: str  # pattern, solution, best_practice, lesson
    content: Any
    confidence: float
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationPattern:
    """Advanced coordination pattern."""
    pattern_id: str
    pattern_type: str  # sequential, parallel, hierarchical, collaborative
    participating_agents: List[str]
    coordination_rules: Dict[str, Any]
    success_rate: float = 0.0
    usage_count: int = 0


class CrossAgentLearning:
    """
    Enable agents to learn from each other's experiences.

    Features:
    - Knowledge sharing across agents
    - Pattern recognition and propagation
    - Collective intelligence
    """

    def __init__(self, storage_dir: str = ".torq/agent_learning"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_file = self.storage_dir / "shared_knowledge.json"

        # In-memory knowledge base
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """Load shared knowledge from storage."""
        # Phase A.4: Error handling for file operations
        if not self.knowledge_file.exists():
            logger.info(f"Knowledge file does not exist yet: {self.knowledge_file}")
            return

        try:
            with open(self.knowledge_file, 'r') as f:
                data = json.load(f)
                for kid, kdata in data.items():
                    try:
                        self.knowledge_base[kid] = KnowledgeItem(
                            knowledge_id=kid,
                            source_agent=kdata['source_agent'],
                            knowledge_type=kdata['knowledge_type'],
                            content=kdata['content'],
                            confidence=kdata['confidence'],
                            usage_count=kdata.get('usage_count', 0),
                            success_rate=kdata.get('success_rate', 0.0),
                            created_at=datetime.fromisoformat(kdata['created_at']),
                            metadata=kdata.get('metadata', {})
                        )
                    except Exception as e:
                        logger.error(f"Failed to load knowledge item {kid}: {e}")
                        # Continue loading other items
                        continue

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in knowledge file: {e}")
            # Start with empty knowledge base
            self.knowledge_base = {}
        except Exception as e:
            logger.error(f"Failed to load knowledge: {e}", exc_info=True)
            # Start with empty knowledge base
            self.knowledge_base = {}

    def _save_knowledge(self):
        """Save shared knowledge to storage."""
        # Phase A.4: Error handling for file operations
        try:
            data = {}
            for kid, knowledge in self.knowledge_base.items():
                try:
                    data[kid] = {
                        'source_agent': knowledge.source_agent,
                        'knowledge_type': knowledge.knowledge_type,
                        'content': knowledge.content,
                        'confidence': knowledge.confidence,
                        'usage_count': knowledge.usage_count,
                        'success_rate': knowledge.success_rate,
                        'created_at': knowledge.created_at.isoformat(),
                        'metadata': knowledge.metadata
                    }
                except Exception as e:
                    logger.error(f"Failed to serialize knowledge item {kid}: {e}")
                    # Continue saving other items
                    continue

            with open(self.knowledge_file, 'w') as f:
                json.dump(data, f, indent=2)

        except IOError as e:
            logger.error(f"Failed to write knowledge file: {e}")
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}", exc_info=True)

    def share_knowledge(
        self,
        source_agent: str,
        knowledge_type: str,
        content: Any,
        confidence: float
    ) -> str:
        """
        Share knowledge from one agent to the collective.

        Args:
            source_agent: Agent sharing the knowledge
            knowledge_type: Type of knowledge
            content: Knowledge content
            confidence: Confidence in this knowledge

        Returns:
            Knowledge ID
        """
        knowledge_id = f"k_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self.knowledge_base[knowledge_id] = KnowledgeItem(
            knowledge_id=knowledge_id,
            source_agent=source_agent,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence
        )

        self._save_knowledge()
        return knowledge_id

    def query_knowledge(
        self,
        knowledge_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[KnowledgeItem]:
        """
        Query shared knowledge base.

        Args:
            knowledge_type: Filter by type
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching knowledge items
        """
        results = []

        for knowledge in self.knowledge_base.values():
            if knowledge.confidence < min_confidence:
                continue

            if knowledge_type and knowledge.knowledge_type != knowledge_type:
                continue

            results.append(knowledge)

        # Sort by confidence and usage
        results.sort(
            key=lambda k: (k.success_rate, k.confidence, k.usage_count),
            reverse=True
        )

        return results

    def record_knowledge_usage(
        self,
        knowledge_id: str,
        success: bool
    ):
        """
        Record usage of shared knowledge.

        Args:
            knowledge_id: Knowledge identifier
            success: Whether usage was successful
        """
        if knowledge_id not in self.knowledge_base:
            return

        knowledge = self.knowledge_base[knowledge_id]
        knowledge.usage_count += 1

        # Update success rate (running average)
        if knowledge.usage_count == 1:
            knowledge.success_rate = 1.0 if success else 0.0
        else:
            # Weighted average favoring recent results
            weight = 0.3  # Weight for new result
            knowledge.success_rate = (
                (1 - weight) * knowledge.success_rate +
                weight * (1.0 if success else 0.0)
            )

        self._save_knowledge()


class AgentPerformanceMonitor:
    """
    Monitor and optimize agent performance.

    Features:
    - Real-time performance tracking
    - Bottleneck detection
    - Optimization suggestions
    """

    def __init__(self):
        self.metrics: List[AgentPerformanceMetric] = []
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}

    def record_metric(
        self,
        agent_id: str,
        metric_name: str,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric."""
        self.metrics.append(AgentPerformanceMetric(
            agent_id=agent_id,
            metric_name=metric_name,
            value=value,
            context=context or {}
        ))

        # Keep last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

    def get_agent_performance(
        self,
        agent_id: str,
        time_window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get performance summary for an agent.

        Args:
            agent_id: Agent identifier
            time_window_seconds: Optional time window

        Returns:
            Performance summary dictionary
        """
        # Filter metrics for this agent
        agent_metrics = [m for m in self.metrics if m.agent_id == agent_id]

        # Apply time window if specified
        if time_window_seconds:
            cutoff = datetime.now().timestamp() - time_window_seconds
            agent_metrics = [
                m for m in agent_metrics
                if m.timestamp.timestamp() >= cutoff
            ]

        if not agent_metrics:
            return {"agent_id": agent_id, "no_data": True}

        # Group by metric name
        by_metric = {}
        for metric in agent_metrics:
            if metric.metric_name not in by_metric:
                by_metric[metric.metric_name] = []
            by_metric[metric.metric_name].append(metric.value)

        # Calculate statistics
        summary = {"agent_id": agent_id, "metrics": {}}

        for metric_name, values in by_metric.items():
            summary["metrics"][metric_name] = {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0.0
            }

        return summary

    def detect_bottlenecks(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect performance bottlenecks.

        Args:
            agent_id: Agent identifier

        Returns:
            List of detected bottlenecks
        """
        performance = self.get_agent_performance(agent_id)

        if performance.get('no_data'):
            return []

        bottlenecks = []

        # Check each metric
        for metric_name, stats in performance.get('metrics', {}).items():
            # High latency
            if 'latency' in metric_name.lower() and stats['mean'] > 2.0:
                bottlenecks.append({
                    "type": "high_latency",
                    "metric": metric_name,
                    "value": stats['mean'],
                    "threshold": 2.0,
                    "severity": "high" if stats['mean'] > 5.0 else "medium"
                })

            # Low quality
            if 'quality' in metric_name.lower() and stats['mean'] < 0.7:
                bottlenecks.append({
                    "type": "low_quality",
                    "metric": metric_name,
                    "value": stats['mean'],
                    "threshold": 0.7,
                    "severity": "high" if stats['mean'] < 0.5 else "medium"
                })

            # High error rate
            if 'error' in metric_name.lower() and stats['mean'] > 0.1:
                bottlenecks.append({
                    "type": "high_error_rate",
                    "metric": metric_name,
                    "value": stats['mean'],
                    "threshold": 0.1,
                    "severity": "critical"
                })

        return bottlenecks


class AdvancedCoordinator:
    """
    Advanced multi-agent coordination patterns.

    Features:
    - Dynamic agent selection
    - Load balancing
    - Fault tolerance
    - Parallel execution
    """

    def __init__(self):
        self.available_agents: Dict[str, AgentRole] = {}
        self.coordination_patterns: Dict[str, CoordinationPattern] = {}
        self.performance_monitor = AgentPerformanceMonitor()

    def register_agent(
        self,
        agent_id: str,
        role: AgentRole
    ):
        """Register an agent with the coordinator."""
        self.available_agents[agent_id] = role

    def select_best_agent(
        self,
        required_role: AgentRole,
        task_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Select the best agent for a task.

        Args:
            required_role: Required agent role
            task_context: Task context for selection

        Returns:
            Agent ID or None
        """
        # Find agents with required role
        candidates = [
            aid for aid, role in self.available_agents.items()
            if role == required_role or role == AgentRole.GENERALIST
        ]

        if not candidates:
            return None

        # If only one candidate, return it
        if len(candidates) == 1:
            return candidates[0]

        # Select based on performance
        best_agent = None
        best_score = -1.0

        for agent_id in candidates:
            perf = self.performance_monitor.get_agent_performance(agent_id)

            if perf.get('no_data'):
                score = 0.5  # Default score for agents without data
            else:
                # Calculate composite score
                quality = perf['metrics'].get('quality_score', {}).get('mean', 0.5)
                latency = perf['metrics'].get('response_latency', {}).get('mean', 1.0)

                # Higher quality, lower latency = better score
                score = quality / (1 + latency / 10.0)

            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    def coordinate_parallel_execution(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Coordinate parallel execution of tasks.

        Args:
            tasks: List of tasks to execute

        Returns:
            Coordination plan
        """
        plan = {
            "coordination_type": "parallel",
            "total_tasks": len(tasks),
            "agent_assignments": []
        }

        # Assign tasks to agents
        for task in tasks:
            required_role = task.get('required_role', AgentRole.GENERALIST)
            agent_id = self.select_best_agent(required_role, task)

            if agent_id:
                plan["agent_assignments"].append({
                    "task_id": task.get('task_id', 'unknown'),
                    "agent_id": agent_id,
                    "estimated_duration": task.get('estimated_duration', 1.0)
                })

        return plan


# Global instances
_cross_agent_learning: Optional[CrossAgentLearning] = None
_performance_monitor: Optional[AgentPerformanceMonitor] = None
_advanced_coordinator: Optional[AdvancedCoordinator] = None


def get_cross_agent_learning() -> CrossAgentLearning:
    """Get or create global cross-agent learning instance."""
    global _cross_agent_learning
    if _cross_agent_learning is None:
        _cross_agent_learning = CrossAgentLearning()
    return _cross_agent_learning


def get_performance_monitor() -> AgentPerformanceMonitor:
    """Get or create global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = AgentPerformanceMonitor()
    return _performance_monitor


def get_advanced_coordinator() -> AdvancedCoordinator:
    """Get or create global advanced coordinator."""
    global _advanced_coordinator
    if _advanced_coordinator is None:
        _advanced_coordinator = AdvancedCoordinator()
    return _advanced_coordinator
