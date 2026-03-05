"""
Learning Writer for the TORQ Agent Cognitive Loop.

Records learning events to the learning system for continuous improvement.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    CognitiveLoopConfig,
    EvaluationResult,
    ExecutionPlan,
    ExecutionResult,
    IntentType,
    KnowledgeContext,
    LearningEvent,
    ReasoningPlan,
)


logger = logging.getLogger(__name__)


class LearningWriter:
    """
    Records learning events from cognitive loop executions.

    Stores query, actions, tools, success scores, and execution times
    to populate reinforcement learning training datasets.
    """

    def __init__(self, config: CognitiveLoopConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.LearningWriter")

        # Storage paths
        self._storage_path = Path(config.learning_storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Learning buffer for batch writes
        self._learning_buffer: List[LearningEvent] = []
        self._buffer_size = 10

        # Statistics
        self._stats = {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "avg_confidence": 0.0,
            "avg_execution_time": 0.0,
        }

    async def record(
        self,
        query: str,
        intent: IntentType,
        reasoning_plan: ReasoningPlan,
        knowledge_contexts: List[KnowledgeContext],
        execution_plan: ExecutionPlan,
        execution_result: Optional[ExecutionResult],
        evaluation_result: Optional[EvaluationResult],
        total_time_seconds: float,
        retry_count: int = 0,
        agent_id: str = "torq_agent",
        **metadata
    ) -> LearningEvent:
        """
        Record a learning event from a cognitive loop execution.

        Args:
            query: The original query
            intent: Detected intent
            reasoning_plan: Reasoning plan output
            knowledge_contexts: Retrieved knowledge contexts
            execution_plan: Execution plan
            execution_result: Tool execution results
            evaluation_result: Evaluation results
            total_time_seconds: Total execution time
            retry_count: Number of retries performed
            agent_id: Agent identifier
            **metadata: Additional metadata

        Returns:
            LearningEvent that was recorded
        """
        if not self.config.learning_enabled:
            return None

        # Determine success and calculate scores
        success, success_score = self._calculate_success_metrics(
            execution_result, evaluation_result
        )

        # Extract tools used
        tools_used = execution_plan.required_tools if execution_plan else []

        # Generate learned insights
        learned_insights = self._generate_insights(
            reasoning_plan, execution_result, evaluation_result
        )

        # Create learning event
        event = LearningEvent(
            agent_id=agent_id,
            query=query,
            intent=intent,
            reasoning_plan=reasoning_plan,
            execution_plan=execution_plan,
            tools_used=tools_used,
            execution_result=execution_result,
            evaluation_result=evaluation_result,
            success=success,
            success_score=success_score,
            execution_time_seconds=total_time_seconds,
            retry_count=retry_count,
            learned_insights=learned_insights,
            metadata=metadata,
        )

        # Store the event
        await self._store_event(event)

        # Update statistics
        self._update_stats(event)

        # Check if we should store novel insights in knowledge plane
        if success and success_score > self.config.min_confidence_for_learning:
            await self._store_novel_insights(event, knowledge_contexts)

        self.logger.debug(
            f"Recorded learning event: success={success}, "
            f"score={success_score:.2f}, intent={intent.value}"
        )

        return event

    def _calculate_success_metrics(
        self,
        execution_result: Optional[ExecutionResult],
        evaluation_result: Optional[EvaluationResult]
    ) -> tuple[bool, float]:
        """Calculate success metrics for the learning event."""
        if evaluation_result:
            success = evaluation_result.task_completed
            success_score = evaluation_result.confidence_score
        elif execution_result:
            success = execution_result.success or execution_result.partial_results
            success_score = 0.7 if execution_result.partial_results else (
                1.0 if execution_result.success else 0.3
            )
        else:
            success = False
            success_score = 0.0

        return success, success_score

    def _generate_insights(
        self,
        reasoning_plan: ReasoningPlan,
        execution_result: Optional[ExecutionResult],
        evaluation_result: Optional[EvaluationResult]
    ) -> List[str]:
        """Generate insights from the execution."""
        insights = []

        # Intent-based insights
        if reasoning_plan.intent_confidence > 0.8:
            insights.append(f"High confidence in {reasoning_plan.intent.value} intent detection")

        # Tool effectiveness insights
        if execution_result:
            successful_tools = [
                r.tool_name for r in execution_result.tool_results if r.success
            ]
            if successful_tools:
                insights.append(f"Effective tools: {', '.join(successful_tools)}")

            failed_tools = [
                r.tool_name for r in execution_result.tool_results if not r.success
            ]
            if failed_tools:
                insights.append(f"Ineffective tools: {', '.join(failed_tools)}")

        # Quality insights
        if evaluation_result:
            if evaluation_result.confidence_score > 0.9:
                insights.append("High-quality result achieved")
            elif evaluation_result.confidence_score < 0.5:
                insights.append("Result quality below acceptable threshold")

        return insights

    async def _store_event(self, event: LearningEvent):
        """Store a learning event to persistent storage."""
        # Add to buffer for batch writes
        self._learning_buffer.append(event)

        # Write buffer if full
        if len(self._learning_buffer) >= self._buffer_size:
            await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush the learning buffer to disk."""
        if not self._learning_buffer:
            return

        # Append to daily log file
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self._storage_path / f"learning_{today}.jsonl"

        try:
            with open(log_file, "a") as f:
                for event in self._learning_buffer:
                    f.write(json.dumps(event.to_dict()) + "\n")

            self.logger.debug(f"Wrote {len(self._learning_buffer)} events to {log_file}")
            self._learning_buffer.clear()

        except Exception as e:
            self.logger.error(f"Failed to write learning events: {e}")

    async def _store_novel_insights(
        self,
        event: LearningEvent,
        knowledge_contexts: List[KnowledgeContext]
    ):
        """Store novel insights in the knowledge plane."""
        try:
            # Import here to avoid circular dependency
            from .knowledge_retriever import KnowledgeRetriever

            retriever = KnowledgeRetriever(self.config)

            # Check if insights are novel (not already in knowledge)
            for insight in event.learned_insights:
                # Simple check: is this insight already in our contexts?
                is_novel = True
                for context in knowledge_contexts:
                    if insight.lower() in context.content.lower():
                        is_novel = False
                        break

                if is_novel:
                    # Store as new knowledge
                    await retriever.store_knowledge(
                        content=insight,
                        source=f"learning_event_{event.id}",
                        metadata={
                            "intent": event.intent.value,
                            "success_score": event.success_score,
                            "tools_used": event.tools_used,
                        }
                    )
                    self.logger.debug(f"Stored novel insight: {insight}")

        except Exception as e:
            self.logger.warning(f"Failed to store novel insights: {e}")

    def _update_stats(self, event: LearningEvent):
        """Update learning statistics."""
        self._stats["total_events"] += 1

        if event.success:
            self._stats["successful_events"] += 1
        else:
            self._stats["failed_events"] += 1

        # Update averages
        n = self._stats["total_events"]
        self._stats["avg_confidence"] = (
            (self._stats["avg_confidence"] * (n - 1) + event.success_score) / n
        )
        self._stats["avg_execution_time"] = (
            (self._stats["avg_execution_time"] * (n - 1) + event.execution_time_seconds) / n
        )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        await self._flush_buffer()  # Ensure all events are written

        return {
            **self._stats,
            "storage_path": str(self._storage_path),
            "buffer_size": len(self._learning_buffer),
            "success_rate": (
                self._stats["successful_events"] / max(self._stats["total_events"], 1)
            ),
        }

    async def get_recent_events(self, limit: int = 10) -> List[LearningEvent]:
        """Get recent learning events."""
        await self._flush_buffer()

        events = []
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self._storage_path / f"learning_{today}.jsonl"

        if log_file.exists():
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if len(events) >= limit:
                            break
                        data = json.loads(line.strip())
                        # Reconstruct LearningEvent (simplified)
                        events.append(LearningEvent(**data))
            except Exception as e:
                self.logger.warning(f"Failed to read recent events: {e}")

        return events

    async def get_learning_data_for_training(
        self,
        min_success_score: float = 0.7,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get learning data suitable for RL training.

        Returns events that meet minimum quality thresholds.
        """
        await self._flush_buffer()

        training_data = []

        # Read from recent log files
        for log_file in sorted(self._storage_path.glob("learning_*.jsonl"), reverse=True)[:7]:
            if len(training_data) >= limit:
                break

            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if len(training_data) >= limit:
                            break

                        data = json.loads(line.strip())
                        if data.get("success_score", 0) >= min_success_score:
                            training_data.append(data)
            except Exception as e:
                self.logger.warning(f"Failed to read {log_file}: {e}")

        return training_data

    async def shutdown(self):
        """Shutdown the learning writer and flush buffers."""
        await self._flush_buffer()
        self.logger.info("Learning writer shutdown complete")

    async def emit_telemetry(
        self,
        phase: str,
        data: Dict[str, Any],
        run_id: Optional[str] = None
    ):
        """Emit telemetry for the learning phase."""
        if not self.config.telemetry_enabled:
            return

        try:
            from torq_console.core.telemetry.event import create_system_event
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()
            await integration.record_agent_run(
                agent_name="learning_writer",
                agent_type="cognitive_loop",
                status="started",
                run_id=run_id,
                **{f"learn.{k}": v for k, v in data.items()}
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")
