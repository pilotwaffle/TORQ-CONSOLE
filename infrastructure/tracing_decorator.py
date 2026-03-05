"""
TORQ Console - Tracing Decorators

Python decorators for automatic tracing of functions and methods.
Supports both sync and async functions.
"""

from functools import wraps
from typing import Callable, Optional, Any
import inspect

from .tracing import (
    TORQTracer,
    get_tracer,
    Span,
    TraceContext,
    SpanKind
)


def traced(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.API_REQUEST,
    attributes: Optional[dict] = None,
    tracer: Optional[TORQTracer] = None
):
    """
    Decorator to automatically trace function execution.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind from SpanKind enum
        attributes: Static attributes to include in span
        tracer: Tracer instance (defaults to global)

    Example:
        >>> @traced(name="user.login", kind=SpanKind.AGENT_ACT)
        >>> async def login(username: str):
        ...     ...  # Your login logic
    """
    def decorator(func: Callable) -> Callable:
        # Get tracer
        t = tracer or get_tracer()

        # Determine span name
        span_name = name or f"{func.__module__}.{func.__name__}"

        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract trace context from kwargs if available
                trace_context = kwargs.pop("trace_context", None)
                if not trace_context:
                    trace_context = TraceContext.generate()

                # Merge static and dynamic attributes
                span_attrs = (attributes or {}).copy()
                span_attrs.update({
                    "function.name": func.__name__,
                    "function.module": func.__module__
                })

                # Create and start span
                span = t.start_span(
                    name=span_name,
                    kind=kind,
                    context=trace_context,
                    attributes=span_attrs
                )

                # Store span in kwargs for downstream calls
                kwargs["trace_context"] = span.context

                try:
                    result = await func(*args, **kwargs)
                    t.end_span(span, status="ok")
                    return result

                except Exception as e:
                    t.end_span(span, status=f"error: {e}")
                    raise

            return async_wrapper

        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                trace_context = kwargs.pop("trace_context", None)
                if not trace_context:
                    trace_context = TraceContext.generate()

                span_attrs = (attributes or {}).copy()
                span_attrs.update({
                    "function.name": func.__name__,
                    "function.module": func.__module__
                })

                span = t.start_span(
                    name=span_name,
                    kind=kind,
                    context=trace_context,
                    attributes=span_attrs
                )

                kwargs["trace_context"] = span.context

                try:
                    result = func(*args, **kwargs)
                    t.end_span(span, status="ok")
                    return result

                except Exception as e:
                    t.end_span(span, status=f"error: {e}")
                    raise

            return sync_wrapper

    return decorator


def traced_agent(reason_name: Optional[str] = None):
    """
    Decorator for agent reasoning functions.

    Automatically creates spans with AGENT_REASON kind.
    """
    return traced(
        name=reason_name,
        kind=SpanKind.AGENT_REASON,
        attributes={"component": "agent", "phase": "reason"}
    )


def traced_retrieve(retrieve_name: Optional[str] = None):
    """
    Decorator for knowledge retrieval functions.
    """
    return traced(
        name=retrieve_name,
        kind=SpanKind.AGENT_RETRIEVE,
        attributes={"component": "agent", "phase": "retrieve"}
    )


def traced_act(act_name: Optional[str] = None):
    """
    Decorator for agent action functions.
    """
    return traced(
        name=act_name,
        kind=SpanKind.AGENT_ACT,
        attributes={"component": "agent", "phase": "act"}
    )


def traced_evaluate(eval_name: Optional[str] = None):
    """
    Decorator for agent evaluation functions.
    """
    return traced(
        name=eval_name,
        kind=SpanKind.AGENT_EVALUATE,
        attributes={"component": "agent", "phase": "evaluate"}
    )


def traced_db(operation: str = "query"):
    """
    Decorator for database operations.
    """
    return traced(
        kind=SpanKind.DATABASE_QUERY,
        attributes={"component": "database", "operation": operation}
    )


def traced_redis(operation: str = "lookup"):
    """
    Decorator for Redis operations.
    """
    return traced(
        kind=SpanKind.REDIS_LOOKUP,
        attributes={"component": "redis", "operation": operation}
    )


def traced_llm(provider: str = "openai", model: str = "gpt-4"):
    """
    Decorator for LLM API calls.
    """
    return traced(
        kind=SpanKind.LLM_REQUEST,
        attributes={
            "component": "llm",
            "llm.provider": provider,
            "llm.model": model
        }
    )


__all__ = [
    "traced",
    "traced_agent",
    "traced_retrieve",
    "traced_act",
    "traced_evaluate",
    "traced_db",
    "traced_redis",
    "traced_llm"
]
