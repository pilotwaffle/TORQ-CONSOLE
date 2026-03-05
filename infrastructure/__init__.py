"""
TORQ Console - Infrastructure Package

Provides distributed tracing, caching, and observability
for the TORQ Console platform.
"""

from .tracing import (
    Tracer,
    TORQTracer,
    TraceContext,
    Span,
    SpanKind,
    get_tracer,
    init_tracing
)

from .tracing_middleware import (
    TracingMiddleware,
    add_tracing_middleware
)

from .tracing_decorator import (
    traced,
    traced_agent,
    traced_retrieve,
    traced_act,
    traced_evaluate,
    traced_db,
    traced_redis,
    traced_llm
)

__all__ = [
    # Core tracing
    "Tracer",
    "TORQTracer",
    "TraceContext",
    "Span",
    "SpanKind",
    "get_tracer",
    "init_tracing",
    # Middleware
    "TracingMiddleware",
    "add_tracing_middleware",
    # Decorators
    "traced",
    "traced_agent",
    "traced_retrieve",
    "traced_act",
    "traced_evaluate",
    "traced_db",
    "traced_redis",
    "traced_llm"
]

__version__ = "1.0.0"
