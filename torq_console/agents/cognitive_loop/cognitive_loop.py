"""
Cognitive Loop - Main Orchestrator for the TORQ Agent Cognitive Loop System.

Orchestrates the complete reasoning cycle: Reason -> Retrieve -> Plan -> Act -> Evaluate -> Learn
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .config import get_cognitive_config
from .models import (
    CognitiveLoopConfig,
    CognitiveLoopResult,
    CognitiveLoopStatus,
    IntentType,
    KnowledgeContext,
    LearningEvent,
    ReasoningPlan,
    SessionContext,
)
from .evaluator import Evaluator
from .knowledge_retriever import KnowledgeRetriever
from .learning_writer import LearningWriter
from .planner import Planner
from .reasoning_engine import ReasoningEngine
from .tool_executor import ToolExecutor


logger = logging.getLogger(__name__)


class CognitiveLoop:
    """
    Main orchestrator for the cognitive reasoning loop.

    Coordinates all phases:
    1. Reason - Interpret user intent
    2. Retrieve - Get relevant knowledge
    3. Plan - Create execution plan
    4. Act - Execute tools
    5. Evaluate - Assess results
    6. Learn - Record learning events
    """

    def __init__(
        self,
        agent_id: str = "torq_agent",
        reasoning_engine: Optional[ReasoningEngine] = None,
        knowledge_retriever: Optional[KnowledgeRetriever] = None,
        planner: Optional[Planner] = None,
        tool_executor: Optional[ToolExecutor] = None,
        evaluator: Optional[Evaluator] = None,
        learning_writer: Optional[LearningWriter] = None,
        config: Optional[CognitiveLoopConfig] = None,
    ):
        self.agent_id = agent_id
        self.config = config or get_cognitive_config()
        self.logger = logging.getLogger(f"{__name__}.CognitiveLoop.{agent_id}")

        # Initialize components
        self.reasoning_engine = reasoning_engine or ReasoningEngine(self.config)
        self.knowledge_retriever = knowledge_retriever or KnowledgeRetriever(self.config)
        self.planner = planner or Planner(self.config)
        self.tool_executor = tool_executor or ToolExecutor(self.config)
        self.evaluator = evaluator or Evaluator(self.config)
        self.learning_writer = learning_writer or LearningWriter(self.config)

        # Session management
        self._current_session: Optional[SessionContext] = None
        self._active_runs: Dict[str, CognitiveLoopResult] = {}

        # Statistics
        self._stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_retries": 0,
            "avg_latency_seconds": 0.0,
        }

    async def run(
        self,
        query: str,
        session_context: Optional[SessionContext] = None,
        **kwargs
    ) -> CognitiveLoopResult:
        """
        Execute the complete cognitive loop for a query.

        Args:
            query: The user's query
            session_context: Optional session context for continuity
            **kwargs: Additional context and parameters

        Returns:
            CognitiveLoopResult with all phases and final outcome
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()

        self.logger.info(f"Starting cognitive loop run {run_id} for query: {query[:100]}...")

        # Initialize result
        result = CognitiveLoopResult(
            query=query,
            status=CognitiveLoopStatus.IDLE,
            metadata={"run_id": run_id, "agent_id": self.agent_id}
        )

        # Store active run
        self._active_runs[run_id] = result

        try:
            # Phase 1: REASON
            result.status = CognitiveLoopStatus.REASONING
            result = await self._phase_reason(query, result, session_context)

            # Phase 2: RETRIEVE
            result.status = CognitiveLoopStatus.RETRIEVING
            result = await self._phase_retrieve(query, result, session_context)

            # Phase 3: PLAN
            result.status = CognitiveLoopStatus.PLANNING
            result = await self._phase_plan(query, result, session_context)

            # Execute with retry loop
            retry_count = 0
            max_retries = self.config.max_retries

            while retry_count <= max_retries:
                # Phase 4: ACT
                result.status = CognitiveLoopStatus.EXECUTING
                result = await self._phase_act(query, result, session_context)

                # Phase 5: EVALUATE
                result.status = CognitiveLoopStatus.EVALUATING
                result = await self._phase_evaluate(query, result, session_context)

                # Check if we need to retry
                if not result.evaluation_result.should_retry:
                    break

                retry_count += 1
                if retry_count <= max_retries:
                    self.logger.info(f"Retrying cognitive loop (attempt {retry_count}/{max_retries})")
                    result.status = CognitiveLoopStatus.RETRYING
                    await asyncio.sleep(self.config.retry_delay_seconds)
                    # Refine plan based on evaluation
                    result.execution_plan = await self.planner.refine_plan(
                        result.execution_plan,
                        result.evaluation_result.retry_reason
                    )
                else:
                    self.logger.warning(f"Max retries ({max_retries}) exceeded")

            result.retry_count = retry_count
            self._stats["total_retries"] += retry_count

            # Phase 6: LEARN
            result.status = CognitiveLoopStatus.LEARNING
            result = await self._phase_learn(query, result, session_context)

            # Finalize result
            result.status = CognitiveLoopStatus.COMPLETED
            result.success = (
                result.evaluation_result.task_completed if result.evaluation_result else False
            )

        except Exception as e:
            self.logger.error(f"Cognitive loop error: {e}", exc_info=True)
            result.status = CognitiveLoopStatus.FAILED
            result.success = False
            result.error = str(e)

        finally:
            # Calculate total time
            result.total_time_seconds = time.time() - start_time

            # Update statistics
            self._update_statistics(result)

            # Emit telemetry
            if self.config.telemetry_enabled:
                await self._emit_telemetry(run_id, result)

            # Clean up
            self._active_runs.pop(run_id, None)

        self.logger.info(
            f"Cognitive loop complete: success={result.success}, "
            f"time={result.total_time_seconds:.2f}s, "
            f"confidence={result.confidence:.2f}"
        )

        return result

    async def _phase_reason(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 1: Reason about the query."""
        phase_start = time.time()

        try:
            result.reasoning_plan = await self.reasoning_engine.reason(
                query=query,
                session_context=session_context,
                knowledge_contexts=result.knowledge_contexts,
            )

            result.phase_times_seconds["reason"] = time.time() - phase_start

            # Emit telemetry span
            if self.config.emit_detailed_spans:
                await self.reasoning_engine.emit_telemetry(
                    "reason",
                    {
                        "intent": result.reasoning_plan.intent.value,
                        "confidence": result.reasoning_plan.intent_confidence,
                        "complexity": result.reasoning_plan.complexity_estimate,
                    },
                    result.metadata.get("run_id")
                )

        except Exception as e:
            self.logger.error(f"Reasoning phase error: {e}")
            result.reasoning_plan = ReasoningPlan(
                intent=IntentType.UNKNOWN,
                intent_confidence=0.0,
                reasoning=f"Reasoning failed: {str(e)}"
            )

        return result

    async def _phase_retrieve(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 2: Retrieve relevant knowledge."""
        phase_start = time.time()

        try:
            result.knowledge_contexts = await self.knowledge_retriever.retrieve(
                query=query,
                session_context=session_context,
            )

            result.phase_times_seconds["retrieve"] = time.time() - phase_start

            # Emit telemetry span
            if self.config.emit_detailed_spans:
                await self.knowledge_retriever.emit_telemetry(
                    "retrieve",
                    {
                        "contexts_retrieved": len(result.knowledge_contexts),
                        "avg_similarity": sum(c.similarity for c in result.knowledge_contexts) / max(len(result.knowledge_contexts), 1),
                    },
                    result.metadata.get("run_id")
                )

        except Exception as e:
            self.logger.warning(f"Knowledge retrieval error: {e}")
            result.knowledge_contexts = []

        return result

    async def _phase_plan(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 3: Plan execution."""
        phase_start = time.time()

        try:
            result.execution_plan = await self.planner.plan(
                reasoning_plan=result.reasoning_plan,
                query=query,
                session_context=session_context,
            )

            result.phase_times_seconds["plan"] = time.time() - phase_start

            # Emit telemetry span
            if self.config.emit_detailed_spans:
                await self.planner.emit_telemetry(
                    "plan",
                    {
                        "steps": len(result.execution_plan.steps),
                        "estimated_duration": result.execution_plan.estimated_duration_seconds,
                    },
                    result.metadata.get("run_id")
                )

        except Exception as e:
            self.logger.error(f"Planning phase error: {e}")
            result.execution_plan = None

        return result

    async def _phase_act(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 4: Execute tools."""
        phase_start = time.time()

        try:
            if result.execution_plan:
                result.execution_result = await self.tool_executor.execute(
                    plan=result.execution_plan,
                    query=query,
                )

                result.phase_times_seconds["act"] = time.time() - phase_start

                # Emit telemetry span
                if self.config.emit_detailed_spans:
                    await self.tool_executor.emit_telemetry(
                        "act",
                        {
                            "tools_executed": len(result.execution_result.tool_results),
                            "success": result.execution_result.success,
                        },
                        result.metadata.get("run_id")
                    )
            else:
                self.logger.warning("No execution plan available for action phase")

        except Exception as e:
            self.logger.error(f"Execution phase error: {e}")
            result.execution_result = None

        return result

    async def _phase_evaluate(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 5: Evaluate results."""
        phase_start = time.time()

        try:
            if result.execution_result and result.execution_plan:
                result.evaluation_result = await self.evaluator.evaluate(
                    execution_result=result.execution_result,
                    execution_plan=result.execution_plan,
                    reasoning_plan=result.reasoning_plan,
                    query=query,
                )

                result.phase_times_seconds["evaluate"] = time.time() - phase_start

                # Emit telemetry span
                if self.config.emit_detailed_spans:
                    await self.evaluator.emit_telemetry(
                        "evaluate",
                        {
                            "confidence": result.evaluation_result.confidence_score,
                            "task_completed": result.evaluation_result.task_completed,
                            "should_retry": result.evaluation_result.should_retry,
                        },
                        result.metadata.get("run_id")
                    )
            else:
                # Default evaluation if no execution result
                result.evaluation_result = EvaluationResult(
                    task_completed=False,
                    confidence_score=0.0,
                    data_integrity_score=0.0,
                    quality_score=0.0,
                    reasoning="No execution results to evaluate",
                )

        except Exception as e:
            self.logger.error(f"Evaluation phase error: {e}")
            result.evaluation_result = None

        return result

    async def _phase_learn(
        self,
        query: str,
        result: CognitiveLoopResult,
        session_context: Optional[SessionContext]
    ) -> CognitiveLoopResult:
        """Phase 6: Learn from the execution."""
        phase_start = time.time()

        try:
            intent = result.reasoning_plan.intent if result.reasoning_plan else IntentType.UNKNOWN

            result.learning_event = await self.learning_writer.record(
                query=query,
                intent=intent,
                reasoning_plan=result.reasoning_plan or ReasoningPlan(),
                knowledge_contexts=result.knowledge_contexts,
                execution_plan=result.execution_plan,
                execution_result=result.execution_result,
                evaluation_result=result.evaluation_result,
                total_time_seconds=result.total_time_seconds,
                retry_count=result.retry_count,
                agent_id=self.agent_id,
            )

            result.phase_times_seconds["learn"] = time.time() - phase_start

            # Emit telemetry span
            if self.config.emit_detailed_spans:
                await self.learning_writer.emit_telemetry(
                    "learn",
                    {
                        "success": result.learning_event.success if result.learning_event else False,
                        "score": result.learning_event.success_score if result.learning_event else 0.0,
                    },
                    result.metadata.get("run_id")
                )

        except Exception as e:
            self.logger.warning(f"Learning phase error: {e}")

        return result

    async def _emit_telemetry(self, run_id: str, result: CognitiveLoopResult):
        """Emit complete telemetry for the run."""
        try:
            from torq_console.core.telemetry.event import AgentStatus
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()

            await integration.record_agent_run(
                agent_name=self.agent_id,
                agent_type="cognitive_loop",
                status=AgentStatus.COMPLETED if result.success else AgentStatus.FAILED,
                run_id=run_id,
                tools_used=result.execution_plan.required_tools if result.execution_plan else [],
                success=result.success,
                error_message=result.error,
            )

        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")

    def _update_statistics(self, result: CognitiveLoopResult):
        """Update cognitive loop statistics."""
        self._stats["total_runs"] += 1

        if result.success:
            self._stats["successful_runs"] += 1
        else:
            self._stats["failed_runs"] += 1

        # Update average latency
        n = self._stats["total_runs"]
        self._stats["avg_latency_seconds"] = (
            (self._stats["avg_latency_seconds"] * (n - 1) + result.total_time_seconds) / n
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get cognitive loop statistics."""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_runs"] / max(self._stats["total_runs"], 1)
            ),
            "active_runs": len(self._active_runs),
        }

    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        return await self.learning_writer.get_statistics()

    def create_session(
        self,
        user_id: Optional[str] = None,
        **metadata
    ) -> SessionContext:
        """Create a new session context."""
        session = SessionContext(
            agent_id=self.agent_id,
            user_id=user_id,
            metadata=metadata,
        )
        self._current_session = session
        return session

    async def shutdown(self):
        """Shutdown the cognitive loop and clean up resources."""
        await self.learning_writer.shutdown()
        self.logger.info(f"Cognitive loop {self.agent_id} shutdown complete")

    # Stream processing support
    async def run_stream(
        self,
        query: str,
        session_context: Optional[SessionContext] = None,
        phase_callback: Optional[Callable[[CognitiveLoopStatus, Dict[str, Any]], None]] = None,
    ) -> CognitiveLoopResult:
        """
        Execute cognitive loop with streaming updates via callback.

        Args:
            query: The user's query
            session_context: Optional session context
            phase_callback: Callback function for phase updates

        Returns:
            CognitiveLoopResult with all phases and final outcome
        """
        async def phase_wrapper(phase_name: str, coro):
            """Wrapper to emit phase updates."""
            if phase_callback:
                await phase_callback(CognitiveLoopStatus[phase_name.upper()], {"phase": phase_name})
            return await coro

        # For streaming, we'll modify the phases to call the callback
        # This is a simplified version - full implementation would inject callbacks into each phase
        return await self.run(query, session_context)
