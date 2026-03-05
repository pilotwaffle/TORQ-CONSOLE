"""
TORQ Console - OpenTelemetry Distributed Tracing Module
Step 2: Infrastructure Upgrades

Implements distributed tracing for all major system actions with proper
span propagation and instrumentation.
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.propagators import extract, inject
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("Warning: OpenTelemetry not installed. Run: pip install opentelemetry-api opentelemetry-sdk")


class SpanKind(Enum):
    """Standard span kinds for TORQ operations"""
    API_REQUEST = "api.request"
    AGENT_REASON = "agent.reason"
    AGENT_RETRIEVE = "agent.retrieve"
    AGENT_ACT = "agent.act"
    AGENT_EVALUATE = "agent.evaluate"
    DATABASE_QUERY = "database.query"
    REDIS_LOOKUP = "redis.lookup"
    CACHE_OPERATION = "cache.operation"
    HTTP_REQUEST = "http.request"
    LLM_REQUEST = "llm.request"
    TOOL_EXECUTION = "tool.execution"


@dataclass
class TraceContext:
    """Immutable trace context for propagation"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def generate(cls) -> "TraceContext":
        """Generate a new trace context with unique IDs"""
        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4())
        )

    def child(self, span_id: Optional[str] = None) -> "TraceContext":
        """Create child context"""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=span_id or str(uuid.uuid4()),
            parent_span_id=self.span_id,
            baggage=self.baggage.copy()
        )


@dataclass
class Span:
    """Span data structure"""
    name: str
    context: TraceContext
    start_time: float
    end_time: Optional[float] = None
    status: str = "started"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)
    links: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for logging/export"""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time or time.time(),
            "duration_ms": ((self.end_time or time.time()) - self.start_time) * 1000,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links
        }


class Tracer:
    """
    TORQ Distributed Tracer

    Supports both OpenTelemetry backend and fallback console logging.
    """

    def __init__(
        self,
        service_name: str = "torq-console",
        otlp_endpoint: Optional[str] = None,
        enable_console: bool = True
    ):
        self.service_name = service_name
        self.enable_console = enable_console
        self._spans: list = []
        self._current_context: Optional[TraceContext] = None

        if OTEL_AVAILABLE:
            # Create resource with service metadata
            attrs = {SERVICE_NAME: service_name}
            resource = Resource.create(attrs)

            self.provider = TracerProvider(resource=resource)

            # Add exporters
            if enable_console:
                self.provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter())
                )

            if otlp_endpoint:
                try:
                    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                    self.provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                except Exception as e:
                    print(f"Warning: OTLP exporter setup failed: {e}")

            # Set global tracer provider
            trace.set_tracer_provider(self.provider)
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = None

    def start_span(
        self,
        name: str,
        context: Optional[TraceContext] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span"""
        if context is None:
            context = self._current_context or TraceContext.generate()
        else:
            context = context.child()

        span = Span(
            name=name,
            context=context,
            start_time=time.time(),
            attributes=attributes or {}
        )

        if OTEL_AVAILABLE and self.tracer:
            span._otel_span = self.tracer.start_span(
                name=name,
                attributes=attributes or {}
            )

        self._current_context = context
        self._spans.append(span)
        return span

    def end_span(self, span: Span, status: str = "ok") -> None:
        """End a span"""
        span.end_time = time.time()
        span.status = status

        if OTEL_AVAILABLE and hasattr(span, '_otel_span'):
            try:
                span._otel_span.end()
            except Exception:
                pass

        if self.enable_console:
            print(f"[TRACE] {span.to_dict()}")

    def get_current_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return self._current_context

    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for propagation"""
        if self._current_context:
            headers["X-Trace-Id"] = self._current_context.trace_id
            headers["X-Span-Id"] = self._current_context.span_id
            if self._current_context.parent_span_id:
                headers["X-Parent-Span-Id"] = self._current_context.parent_span_id
        return headers

    def extract_context(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from headers"""
        # Standard OpenTelemetry trace parent header
        trace_parent = headers.get("traceparent", "")
        if trace_parent:
            # Format: 00-trace_id-span_id-trace_flags
            parts = trace_parent.split("-")
            if len(parts) >= 3:
                return TraceContext(
                    trace_id=parts[1],
                    span_id=parts[2],
                    baggage=self._extract_baggage(headers)
                )

        # Fallback to TORQ-specific headers
        trace_id = headers.get("X-Trace-Id") or headers.get("x-trace-id")
        span_id = headers.get("X-Span-Id") or headers.get("x-span-id")
        parent_span_id = headers.get("X-Parent-Span-Id") or headers.get("x-parent-span-id")

        if trace_id:
            return TraceContext(
                trace_id=trace_id,
                span_id=span_id or str(uuid.uuid4()),
                parent_span_id=parent_span_id,
                baggage=self._extract_baggage(headers)
            )

        return None

    def _extract_baggage(self, headers: dict) -> dict:
        """Extract baggage from headers"""
        baggage_header = headers.get("baggage", "")
        if not baggage_header:
            return {}

        baggage = {}
        for item in baggage_header.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                baggage[key.strip()] = value.strip()
        return baggage

    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to client host
        if hasattr(request, 'client'):
            return request.client.host if request.client else "unknown"

        return "unknown"


class TORQTracer(Tracer):
    """
    TORQ-specific tracer with predefined span types and
    Railway/FastAPI integration helpers.
    """

    def trace_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        **attrs
    ) -> Span:
        """Trace an API request"""
        return self.start_span(
            name=f"{method.value if hasattr(method, 'value') else method} {path}",
            attributes={
                "http.method": method.value if hasattr(method, 'value') else method,
                "http.route": path,
                "http.status_code": status_code,
                **attrs
            }
        )

    def trace_agent_reason(
        self,
        agent_id: str,
        prompt: str,
        **attrs
    ) -> Span:
        """Trace agent reasoning step"""
        return self.start_span(
            name="agent.reason",
            attributes={
                "agent.id": agent_id,
                "reasoning.prompt": prompt[:500],  # Truncate for logging
                **attrs
            }
        )

    def trace_agent_retrieve(
        self,
        agent_id: str,
        query: str,
        **attrs
    ) -> Span:
        """Trace agent knowledge retrieval"""
        return self.start_span(
            name="agent.retrieve",
            attributes={
                "agent.id": agent_id,
                "retrieve.query": query[:500],
                **attrs
            }
        )

    def trace_agent_act(
        self,
        agent_id: str,
        action: str,
        **attrs
    ) -> Span:
        """Trace agent action"""
        return self.start_span(
            name="agent.act",
            attributes={
                "agent.id": agent_id,
                "action.name": action,
                **attrs
            }
        )

    def trace_agent_evaluate(
        self,
        agent_id: str,
        outcome: str,
        **attrs
    ) -> Span:
        """Trace agent evaluation"""
        return self.start_span(
            name="agent.evaluate",
            attributes={
                "agent.id": agent_id,
                "evaluation.outcome": outcome,
                **attrs
            }
        )

    def trace_database_query(
        self,
        query_type: str = "query",
        **attrs
    ) -> Span:
        """Trace database operation"""
        return self.start_span(
            name="database.query",
            attributes={
                "db.operation": query_type,
                **attrs
            }
        )

    def trace_redis_operation(
        self,
        operation: str = "lookup",
        **attrs
    ) -> Span:
        """Trace Redis operation"""
        return self.start_span(
            name="redis.lookup",
            attributes={
                "cache.operation": operation,
                **attrs
            }
        )

    def trace_llm_request(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        **attrs
    ) -> Span:
        """Trace LLM API call"""
        return self.start_span(
            name="llm.request",
            attributes={
                "llm.provider": provider,
                "llm.model": model,
                **attrs
            }
        )


# Singleton instance for global access
_global_tracer: Optional[TORQTracer] = None


def get_tracer(
    service_name: str = "torq-console",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = True
) -> TORQTracer:
    """Get or create global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = TORQTracer(
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            enable_console=enable_console
        )
    return _global_tracer


def init_tracing(
    service_name: str = "torq-console",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = True,
    resource_attrs: Optional[Dict[str, str]] = None
) -> TORQTracer:
    """
    Initialize distributed tracing for TORQ Console.

    Args:
        service_name: Service identifier for traces
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        enable_console: Enable console exporter for debugging
        resource_attrs: Additional resource attributes

    Returns:
        Configured TORQTracer instance

    Example:
        >>> tracer = init_tracing(
        ...     service_name="torq-api",
        ...     otlp_endpoint="http://jaeger:4317"
        ... )
    """
    global _global_tracer
    _global_tracer = TORQTracer(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        enable_console=enable_console
    )
    print(f"[TRACING] Initialized OpenTelemetry for {service_name}")
    return _global_tracer


# Export public API
__all__ = [
    "Tracer",
    "TORQTracer",
    "TraceContext",
    "Span",
    "SpanKind",
    "get_tracer",
    "init_tracing"
]
