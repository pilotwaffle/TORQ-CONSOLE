"""
TORQ Agent Cognitive Loop Telemetry Module

Implements OpenTelemetry observability for the cognitive loop with comprehensive
span tracking for all reasoning, retrieval, planning, action, evaluation, and learning steps.

Integrates with the existing infrastructure/tracing.py module for seamless
distributed tracing across the TORQ ecosystem.
"""

import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Union
from functools import wraps
import asyncio
import logging

# Import existing tracer
try:
    from infrastructure.tracing import (
        TORQTracer,
        TraceContext,
        Span,
        SpanKind,
        get_tracer,
        OTEL_AVAILABLE
    )
except ImportError:
    # Fallback for standalone usage
    OTEL_AVAILABLE = False
    TORQTracer = None
    TraceContext = None
    Span = None

logger = logging.getLogger(__name__)


# ============================================================================
# Span Definitions for Cognitive Loop
# ============================================================================

class CognitiveSpanKind(str, Enum):
    """Span types for cognitive loop steps."""

    # Core cognitive steps
    REASON_STEP = "cognitive.reason.step"
    RETRIEVE_STEP = "cognitive.retrieve.step"
    PLAN_STEP = "cognitive.plan.step"
    ACT_STEP = "cognitive.act.step"
    EVALUATE_STEP = "cognitive.evaluate.step"
    LEARN_STEP = "cognitive.learn.step"

    # Loop-level spans
    COGNITIVE_LOOP = "cognitive.loop"
    LOOP_ITERATION = "cognitive.loop.iteration"

    # Sub-operation spans
    TOOL_EXECUTION = "cognitive.tool.execution"
    KNOWLEDGE_SEARCH = "cognitive.knowledge.search"
    REASONING_CHAIN = "cognitive.reasoning.chain"
    PLAN_GENERATION = "cognitive.plan.generation"
    RESULT_VALIDATION = "cognitive.result.validation"


# ============================================================================
# Span Attribute Keys (Standardized)
# ============================================================================

class AttributeKey(str, Enum):
    """Standard attribute keys for cognitive spans."""

    # Core identifiers
    LOOP_ID = "cognitive.loop.id"
    ITERATION_ID = "cognitive.iteration.id"
    SESSION_ID = "cognitive.session.id"
    USER_QUERY = "cognitive.user.query"

    # Reasoning attributes
    REASONING_CONFIDENCE = "cognitive.reasoning.confidence"
    REASONING_STEPS = "cognitive.reasoning.steps"
    REASONING_MODEL = "cognitive.reasoning.model"

    # Retrieval attributes
    KNOWLEDGE_COUNT_RETRIEVED = "cognitive.retrieve.count"
    KNOWLEDGE_SOURCE = "cognitive.retrieve.source"
    RETRIEVAL_METHOD = "cognitive.retrieve.method"
    RETRIEVAL_QUERY = "cognitive.retrieve.query"

    # Planning attributes
    PLAN_STEPS_COUNT = "cognitive.plan.steps.count"
    PLAN_COMPLEXITY = "cognitive.plan.complexity"
    PLAN_ESTIMATED_DURATION = "cognitive.plan.estimated_duration"

    # Action attributes
    TOOLS_USED = "cognitive.act.tools"
    TOOL_SUCCESS_RATE = "cognitive.act.success_rate"
    ACTIONS_COUNT = "cognitive.act.count"
    TOOL_DURATION = "cognitive.act.tool_duration"

    # Evaluation attributes
    EVALUATION_CONFIDENCE = "cognitive.evaluate.confidence"
    EVALUATION_OUTCOME = "cognitive.evaluate.outcome"
    EVALUATION_METRICS = "cognitive.evaluate.metrics"
    RESULT_QUALITY = "cognitive.evaluate.quality"

    # Learning attributes
    LEARNING_STORED = "cognitive.learn.stored"
    LEARNING_TYPE = "cognitive.learn.type"
    MEMORY_UPDATED = "cognitive.learn.memory_updated"
    PATTERN_LEARNED = "cognitive.learn.pattern"

    # Performance attributes
    LOOP_LATENCY_MS = "cognitive.loop.latency_ms"
    STEP_LATENCY_MS = "cognitive.step.latency_ms"
    TOTAL_TOKENS = "cognitive.tokens.total"


# ============================================================================
# Cognitive Loop Telemetry Data Classes
# ============================================================================

@dataclass
class CognitiveLoopContext:
    """Context for tracking a complete cognitive loop execution."""

    loop_id: str
    session_id: str
    user_query: str
    start_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Tracking state
    iteration_count: int = 0
    tools_used: List[str] = field(default_factory=list)
    total_tokens: int = 0
    confidence_scores: List[float] = field(default_factory=list)

    # Step timing
    step_timings: Dict[str, float] = field(default_factory=dict)

    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def get_average_confidence(self) -> float:
        """Calculate average confidence across all steps."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)

    def get_total_latency(self) -> float:
        """Get total loop latency in milliseconds."""
        return (time.time() - self.start_time) * 1000

    def add_step_timing(self, step_name: str, duration_ms: float) -> None:
        """Record timing for a step."""
        self.step_timings[step_name] = duration_ms


@dataclass
class StepResult:
    """Result from a cognitive step execution."""

    step_name: str
    success: bool
    duration_ms: float
    confidence: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    output: Optional[Any] = None


# ============================================================================
# Main Telemetry Class
# ============================================================================

class CognitiveLoopTelemetry:
    """
    Manages OpenTelemetry telemetry for the TORQ Agent Cognitive Loop.

    Provides decorators, context managers, and direct methods for instrumenting
    each step of the cognitive reasoning process.
    """

    def __init__(
        self,
        service_name: str = "torq-cognitive-loop",
        tracer: Optional[TORQTracer] = None,
        enable_auto_instrumentation: bool = True
    ):
        """
        Initialize cognitive loop telemetry.

        Args:
            service_name: Service identifier for traces
            tracer: Existing TORQTracer instance (optional)
            enable_auto_instrumentation: Enable automatic span recording
        """
        self.service_name = service_name
        self._tracer = tracer or (get_tracer() if TORQTracer else None)
        self.enable_auto = enable_auto_instrumentation

        # Active contexts
        self._active_loops: Dict[str, CognitiveLoopContext] = {}
        self._active_spans: Dict[str, Any] = {}

        # Metrics aggregation
        self._loop_metrics: List[Dict[str, Any]] = []

        logger.info(f"Cognitive Loop Telemetry initialized: {service_name}")

    # ========================================================================
    # Context Managers for Span Creation
    # ========================================================================

    @asynccontextmanager
    async def observe_reason_step(
        self,
        loop_id: str,
        reasoning_prompt: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe a reasoning step with automatic span creation.

        Args:
            loop_id: Cognitive loop identifier
            reasoning_prompt: The reasoning prompt/chain
            attributes: Additional span attributes

        Yields:
            StepResult for recording outcomes
        """
        step_name = CognitiveSpanKind.REASON_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            AttributeKey.USER_QUERY: reasoning_prompt[:500],
            **(attributes or {})
        }

        # Start span
        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            # Update context timing
            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("reason", duration_ms)

            # End span
            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                confidence=result.confidence,
                **result.attributes
            )

    @asynccontextmanager
    async def observe_retrieve_step(
        self,
        loop_id: str,
        query: str,
        retrieval_method: str = "vector_search",
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe a knowledge retrieval step.

        Args:
            loop_id: Cognitive loop identifier
            query: Search query for retrieval
            retrieval_method: Method used (vector_search, keyword, hybrid)
            attributes: Additional span attributes

        Yields:
            StepResult for recording retrieval outcomes
        """
        step_name = CognitiveSpanKind.RETRIEVE_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            AttributeKey.RETRIEVAL_QUERY: query[:500],
            AttributeKey.RETRIEVAL_METHOD: retrieval_method,
            **(attributes or {})
        }

        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("retrieve", duration_ms)

            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                knowledge_count=result.attributes.get(AttributeKey.KNOWLEDGE_COUNT_RETRIEVED, 0),
                **result.attributes
            )

    @asynccontextmanager
    async def observe_plan_step(
        self,
        loop_id: str,
        plan_description: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe a planning step.

        Args:
            loop_id: Cognitive loop identifier
            plan_description: Description of the plan
            attributes: Additional span attributes

        Yields:
            StepResult for recording planning outcomes
        """
        step_name = CognitiveSpanKind.PLAN_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            "cognitive.plan.description": plan_description[:500],
            **(attributes or {})
        }

        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("plan", duration_ms)

            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                steps_count=result.attributes.get(AttributeKey.PLAN_STEPS_COUNT, 0),
                **result.attributes
            )

    @asynccontextmanager
    async def observe_act_step(
        self,
        loop_id: str,
        tool_names: List[str],
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe an action/tool execution step.

        Args:
            loop_id: Cognitive loop identifier
            tool_names: List of tools being executed
            attributes: Additional span attributes

        Yields:
            StepResult for recording action outcomes
        """
        step_name = CognitiveSpanKind.ACT_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            AttributeKey.TOOLS_USED: tool_names,
            **(attributes or {})
        }

        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            # Track tools used
            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("act", duration_ms)
                for tool in tool_names:
                    if tool not in self._active_loops[loop_id].tools_used:
                        self._active_loops[loop_id].tools_used.append(tool)

            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                tools=tool_names,
                success_rate=result.attributes.get(AttributeKey.TOOL_SUCCESS_RATE, 0.0),
                **result.attributes
            )

    @asynccontextmanager
    async def observe_evaluate_step(
        self,
        loop_id: str,
        evaluation_criteria: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe an evaluation step.

        Args:
            loop_id: Cognitive loop identifier
            evaluation_criteria: Criteria for evaluation
            attributes: Additional span attributes

        Yields:
            StepResult for recording evaluation outcomes
        """
        step_name = CognitiveSpanKind.EVALUATE_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            "cognitive.evaluate.criteria": evaluation_criteria[:500],
            **(attributes or {})
        }

        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("evaluate", duration_ms)
                self._active_loops[loop_id].confidence_scores.append(result.confidence)

            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                confidence=result.confidence,
                outcome=result.attributes.get(AttributeKey.EVALUATION_OUTCOME, ""),
                **result.attributes
            )

    @asynccontextmanager
    async def observe_learn_step(
        self,
        loop_id: str,
        learning_type: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe a learning step.

        Args:
            loop_id: Cognitive loop identifier
            learning_type: Type of learning (reinforcement, pattern, feedback)
            attributes: Additional span attributes

        Yields:
            StepResult for recording learning outcomes
        """
        step_name = CognitiveSpanKind.LEARN_STEP
        start_time = time.time()
        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            AttributeKey.LEARNING_TYPE: learning_type,
            **(attributes or {})
        }

        span = self._start_span(step_name, span_attrs)

        try:
            result = StepResult(
                step_name=step_name,
                success=False,
                duration_ms=0.0,
                attributes=span_attrs
            )
            yield result

        finally:
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            if loop_id in self._active_loops:
                self._active_loops[loop_id].add_step_timing("learn", duration_ms)

            self._end_span(
                span,
                status="ok" if result.success else "error",
                duration_ms=duration_ms,
                learning_stored=result.attributes.get(AttributeKey.LEARNING_STORED, False),
                memory_updated=result.attributes.get(AttributeKey.MEMORY_UPDATED, False),
                **result.attributes
            )

    # ========================================================================
    # Complete Loop Observation
    # ========================================================================

    @asynccontextmanager
    async def observe_cognitive_loop(
        self,
        user_query: str,
        session_id: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Observe a complete cognitive loop execution.

        Args:
            user_query: The user's query/request
            session_id: Session identifier
            attributes: Additional loop-level attributes

        Yields:
            CognitiveLoopContext for tracking the full loop
        """
        loop_id = str(uuid.uuid4())
        start_time = time.time()

        context = CognitiveLoopContext(
            loop_id=loop_id,
            session_id=session_id,
            user_query=user_query,
            start_time=start_time,
            metadata=attributes or {}
        )

        # Register active loop
        self._active_loops[loop_id] = context

        span_attrs = {
            AttributeKey.LOOP_ID: loop_id,
            AttributeKey.SESSION_ID: session_id,
            AttributeKey.USER_QUERY: user_query[:500],
            **(attributes or {})
        }

        span = self._start_span(
            CognitiveSpanKind.COGNITIVE_LOOP,
            span_attrs
        )

        try:
            logger.debug(f"Starting cognitive loop: {loop_id}")
            yield context

        finally:
            # Calculate final metrics
            total_latency = (time.time() - start_time) * 1000

            # End loop span with aggregated metrics
            self._end_span(
                span,
                status="ok",
                duration_ms=total_latency,
                iterations=context.iteration_count,
                tools_used=context.tools_used,
                avg_confidence=context.get_average_confidence(),
                total_tokens=context.total_tokens,
                step_timings=context.step_timings
            )

            # Store metrics
            self._store_loop_metrics(context, total_latency)

            # Cleanup
            del self._active_loops[loop_id]
            logger.debug(f"Completed cognitive loop: {loop_id} in {total_latency:.2f}ms")

    # ========================================================================
    # Decorators for Automatic Instrumentation
    # ========================================================================

    def trace_reasoning(self, loop_id_attr: str = "loop_id"):
        """
        Decorator to automatically trace reasoning functions.

        Args:
            loop_id_attr: Attribute name containing loop_id
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                loop_id = kwargs.get(loop_id_attr) or getattr(args[0], loop_id_attr, None)
                if not loop_id:
                    return await func(*args, **kwargs)

                async with self.observe_reason_step(
                    loop_id=loop_id,
                    reasoning_prompt=str(args)[:500]
                ) as result:
                    try:
                        output = await func(*args, **kwargs)
                        result.success = True
                        result.output = output
                        return output
                    except Exception as e:
                        result.success = False
                        result.error = str(e)
                        raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                loop_id = kwargs.get(loop_id_attr) or getattr(args[0], loop_id_attr, None)
                if not loop_id:
                    return func(*args, **kwargs)

                # For sync functions, run in context manager
                async def _run():
                    async with self.observe_reason_step(
                        loop_id=loop_id,
                        reasoning_prompt=str(args)[:500]
                    ) as result:
                        try:
                            output = func(*args, **kwargs)
                            result.success = True
                            result.output = output
                            return output
                        except Exception as e:
                            result.success = False
                            result.error = str(e)
                            raise

                return asyncio.run(_run())

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def trace_retrieval(self, loop_id_attr: str = "loop_id"):
        """Decorator to automatically trace knowledge retrieval functions."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                loop_id = kwargs.get(loop_id_attr) or getattr(args[0], loop_id_attr, None)
                query = args[1] if len(args) > 1 else str(args)[:500]

                if not loop_id:
                    return await func(*args, **kwargs)

                async with self.observe_retrieve_step(
                    loop_id=loop_id,
                    query=query
                ) as result:
                    try:
                        output = await func(*args, **kwargs)
                        result.success = True
                        result.output = output
                        # Extract knowledge count if available
                        if isinstance(output, (list, tuple)):
                            result.attributes[AttributeKey.KNOWLEDGE_COUNT_RETRIEVED] = len(output)
                        return output
                    except Exception as e:
                        result.success = False
                        result.error = str(e)
                        raise

            return async_wrapper

        return decorator

    def trace_action(self, loop_id_attr: str = "loop_id"):
        """Decorator to automatically trace action/tool execution functions."""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                loop_id = kwargs.get(loop_id_attr) or getattr(args[0], loop_id_attr, None)
                tool_name = kwargs.get("tool_name", func.__name__)

                if not loop_id:
                    return await func(*args, **kwargs)

                async with self.observe_act_step(
                    loop_id=loop_id,
                    tool_names=[tool_name]
                ) as result:
                    try:
                        output = await func(*args, **kwargs)
                        result.success = True
                        result.output = output
                        return output
                    except Exception as e:
                        result.success = False
                        result.error = str(e)
                        raise

            return async_wrapper

        return decorator

    # ========================================================================
    # Direct Span Methods
    # ========================================================================

    def _start_span(
        self,
        name: Union[str, CognitiveSpanKind],
        attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Start an OpenTelemetry span."""
        if not self._tracer:
            return None

        try:
            return self._tracer.start_span(
                name=str(name),
                attributes=attributes
            )
        except Exception as e:
            logger.warning(f"Failed to start span: {e}")
            return None

    def _end_span(
        self,
        span: Optional[Any],
        status: str = "ok",
        **attributes
    ) -> None:
        """End an OpenTelemetry span with attributes."""
        if not span or not self._tracer:
            return

        try:
            # Add final attributes
            for key, value in attributes.items():
                span.attributes[key] = value

            self._tracer.end_span(span, status=status)
        except Exception as e:
            logger.warning(f"Failed to end span: {e}")

    def _store_loop_metrics(self, context: CognitiveLoopContext, total_latency: float) -> None:
        """Store aggregated loop metrics."""
        metrics = {
            "loop_id": context.loop_id,
            "session_id": context.session_id,
            "user_query": context.user_query[:200],
            "timestamp": time.time(),
            "total_latency_ms": total_latency,
            "iterations": context.iteration_count,
            "tools_used": context.tools_used,
            "avg_confidence": context.get_average_confidence(),
            "total_tokens": context.total_tokens,
            "step_timings": context.step_timings,
            "error_count": len(context.errors)
        }
        self._loop_metrics.append(metrics)

        # Keep only recent metrics
        if len(self._loop_metrics) > 1000:
            self._loop_metrics = self._loop_metrics[-1000:]

    # ========================================================================
    # Metrics and Reporting
    # ========================================================================

    def get_loop_metrics(
        self,
        limit: int = 100,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stored loop metrics.

        Args:
            limit: Maximum number of metrics to return
            session_id: Filter by session ID

        Returns:
            List of loop metrics
        """
        metrics = self._loop_metrics

        if session_id:
            metrics = [m for m in metrics if m.get("session_id") == session_id]

        return metrics[-limit:]

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics across all loops.

        Returns:
            Dictionary with aggregated statistics
        """
        if not self._loop_metrics:
            return {
                "total_loops": 0,
                "avg_latency_ms": 0.0,
                "avg_confidence": 0.0,
                "success_rate": 0.0,
                "most_used_tools": {},
                "error_count": 0
            }

        total_loops = len(self._loop_metrics)
        avg_latency = sum(m["total_latency_ms"] for m in self._loop_metrics) / total_loops
        avg_confidence = sum(m.get("avg_confidence", 0) for m in self._loop_metrics) / total_loops
        error_loops = sum(1 for m in self._loop_metrics if m.get("error_count", 0) > 0)

        # Aggregate tool usage
        all_tools = []
        for m in self._loop_metrics:
            all_tools.extend(m.get("tools_used", []))

        from collections import Counter
        tool_counts = Counter(all_tools)

        return {
            "total_loops": total_loops,
            "avg_latency_ms": avg_latency,
            "avg_confidence": avg_confidence,
            "success_rate": (total_loops - error_loops) / total_loops if total_loops > 0 else 0.0,
            "most_used_tools": dict(tool_counts.most_common(10)),
            "error_count": error_loops
        }

    def export_metrics_for_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-format metrics string
        """
        agg = self.get_aggregated_metrics()

        lines = [
            "# TORQ Cognitive Loop Metrics",
            f"torq_cognitive_loops_total {agg['total_loops']}",
            f"torq_cognitive_latency_avg_ms {agg['avg_latency_ms']:.2f}",
            f"torq_cognitive_confidence_avg {agg['avg_confidence']:.3f}",
            f"torq_cognitive_success_rate {agg['success_rate']:.3f}",
            f"torq_cognitive_errors_total {agg['error_count']}",
            ""
        ]

        # Tool usage metrics
        for tool, count in agg.get("most_used_tools", {}).items():
            lines.append(f'torq_cognitive_tool_usage{{tool="{tool}"}} {count}')

        return "\n".join(lines)


# ============================================================================
# Singleton Instance
# ============================================================================

_global_telemetry: Optional[CognitiveLoopTelemetry] = None


def get_cognitive_telemetry(
    service_name: str = "torq-cognitive-loop",
    tracer: Optional[TORQTracer] = None
) -> CognitiveLoopTelemetry:
    """Get or create global cognitive telemetry instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = CognitiveLoopTelemetry(
            service_name=service_name,
            tracer=tracer
        )
    return _global_telemetry


# ============================================================================
# Convenience Functions
# ============================================================================

async def run_observed_loop(
    user_query: str,
    session_id: str,
    telemetry: Optional[CognitiveLoopTelemetry] = None,
    loop_func: Optional[Callable] = None
) -> CognitiveLoopContext:
    """
    Run a cognitive loop with full telemetry observation.

    Args:
        user_query: The user query
        session_id: Session identifier
        telemetry: Telemetry instance (uses global if not provided)
        loop_func: Async function implementing the loop

    Returns:
        CognitiveLoopContext with execution details
    """
    if telemetry is None:
        telemetry = get_cognitive_telemetry()

    async with telemetry.observe_cognitive_loop(
        user_query=user_query,
        session_id=session_id
    ) as context:
        if loop_func:
            await loop_func(context)

    return context


# ============================================================================
# Export Public API
# ============================================================================

__all__ = [
    # Main classes
    "CognitiveLoopTelemetry",
    "CognitiveLoopContext",
    "StepResult",

    # Enums
    "CognitiveSpanKind",
    "AttributeKey",

    # Functions
    "get_cognitive_telemetry",
    "run_observed_loop",
]
